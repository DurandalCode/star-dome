"""The material inputs, guarded against the mistakes that move an answer 1000x.

Every other test in this suite checks a calculation. This one checks the
*numbers going into* one, because a strength result is only as good as the
megapascal it was typed in, and a units slip in `configs/materials.toml` would
propagate silently into every wind speed this project ever quotes.

One of these tests exists because the bug it catches was written, here, on the
first attempt: the shear modulus was derived from a Poisson's ratio, which is
an isotropic formula applied to a unidirectional composite and overstates
torsional stiffness about fivefold.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, material, span

CANDIDATES = ["gost31938", "pultruded_rod", "gfrp_tube"]
VARIANTS = ["D3", "D4", "D6", "D8", "D10", "D12"]


@pytest.fixture(scope="module")
def materials():
    return material.load_all()


# --- the inputs are physically possible -------------------------------------


def test_every_candidate_states_where_its_numbers_came_from(materials):
    """A number without a source is a guess wearing a standard's clothes.

    The loader refuses to build a Material without one, so this is really a
    test that nobody has weakened the loader -- which is the only thing
    keeping `configs/materials.toml` honest.
    """
    for name, m in materials.items():
        assert m.source.strip(), f"{name} has no source"


@pytest.mark.parametrize("name", CANDIDATES)
def test_the_numbers_are_in_the_units_they_claim(materials, name):
    """The GPa-for-MPa catch, which is the cheapest 1000x error to make."""
    m = materials[name]
    assert 20_000 <= m.modulus_mpa <= 100_000, m.modulus_mpa
    assert 100 <= m.tensile_strength_mpa <= 2_000, m.tensile_strength_mpa
    assert 50 <= m.compressive_strength_mpa <= 1_000, m.compressive_strength_mpa
    assert 1_000 <= m.density_kg_m3 <= 3_000, m.density_kg_m3


@pytest.mark.parametrize("name", CANDIDATES)
def test_the_shear_modulus_was_not_derived_from_a_poisson_ratio(materials, name):
    """The bug that was actually written here, and the reason this file exists.

    `G = E / 2(1 + nu)` is isotropic. A pultruded rod is glass running one way
    in a soft matrix: stiff along the fibres, floppy across them, with G/E
    around 0.06-0.09 against an isotropic 0.4. Anything above 0.2 means
    somebody reached for the isotropic formula, and the effect is to stiffen a
    curved member against exactly the action the wind applies.
    """
    m = materials[name]
    assert m.shear_ratio < 0.2, (
        f"{name}: G/E = {m.shear_ratio:.3f}. That is an isotropic value for a "
        "unidirectional composite."
    )


@pytest.mark.parametrize("name", CANDIDATES)
def test_glass_composite_is_weaker_in_compression_than_in_tension(materials, name):
    """True of every glass composite, and the reason the two fibres of a bent
    rod are checked separately. A candidate that failed this would make the
    compression check silently slack."""
    m = materials[name]
    assert m.compressive_strength_mpa < m.tensile_strength_mpa


# --- the allowables mean what they say --------------------------------------


@pytest.mark.parametrize("name", CANDIDATES)
def test_a_permanent_stress_is_allowed_less_than_a_gust(materials, name):
    """Creep rupture is the governing limit state for glass composite and has
    no equivalent in steel. If these two ever came out equal, the duration
    distinction has been lost and the bend check has stopped meaning
    anything."""
    m = materials[name]
    assert m.allowable("sustained", "tension") < m.allowable("short_term", "tension")


@pytest.mark.parametrize("name", CANDIDATES)
def test_an_allowable_strain_is_just_an_allowable_stress_over_the_modulus(
    materials, name
):
    """`docs/span.md` prints four guesses at this number and says nobody has
    measured one. This is the identity that lets a material supply it."""
    m = materials[name]
    for term in material.TERMS:
        for fibre in material.FIBRES:
            assert m.allowable_strain(term, fibre) == pytest.approx(
                m.allowable(term, fibre) / m.modulus_mpa, rel=1e-12
            )


def test_legacy_reference_is_named_but_minimum_modulus_is_not_conservative(materials):
    from dataclasses import replace
    m = materials["gost31938"]
    assert material.REFERENCE_MATERIAL == "gost31938"
    stiffer = replace(m, modulus_mpa=60000)
    # D4 at R=2 m, d=8 mm: both E values satisfy the old 50 GPa minimum.
    assert m.bend_stress(8, 2000) == pytest.approx(100)
    assert stiffer.bend_stress(8, 2000) == pytest.approx(120)
    assert m.bend_utilisation(8,2000) < 1 < stiffer.bend_utilisation(8,2000)


@pytest.mark.parametrize("field,value", [("modulus_mpa",0), ("modulus_mpa",math.nan),
    ("density_kg_m3",-1), ("wall_ratio",.5), ("environmental_factor",1.1),
    ("sustained_stress_ratio",0), ("shear_modulus_mpa",math.inf)])
def test_invalid_material_parameters_rejected(field, value):
    from dataclasses import replace
    with pytest.raises(ValueError):
        replace(material.load(), **{field:value})


# --- a rod of it ------------------------------------------------------------


def test_a_solid_bar_is_solid(materials):
    """`wall_ratio = 0` has to mean a solid bar, not a shell of zero
    thickness. Written because the first version got it wrong: the tube
    formula `d(1 - 2t/d)` returns `d` at `t = 0`, which is a bore the full
    diameter of the rod and a section area of exactly nothing."""
    for name in ("gost31938", "pultruded_rod"):
        m = materials[name]
        assert not m.is_hollow
        assert m.inner_diameter(10.0) == 0.0
        assert m.area(10.0) == pytest.approx(math.pi * 100.0 / 4.0, rel=1e-12)
        assert m.second_moment(10.0) == pytest.approx(
            math.pi * 10.0 ** 4 / 64.0, rel=1e-12
        )


def test_a_tube_trades_area_away_and_keeps_the_stiffness(materials):
    """The whole reason milestone 7 lists a tube: hollowing takes 36% of the
    section away and only 13% of the second moment, so stiffness per unit mass
    goes up. Decision 0015 still says it cannot move the family's ceiling,
    because it puts no support in the middle of a bow."""
    solid = materials["pultruded_rod"]
    tube = materials["gfrp_tube"]
    assert tube.area(10.0) < solid.area(10.0)
    assert tube.second_moment(10.0) < solid.second_moment(10.0)
    assert (tube.second_moment(10.0) / tube.area(10.0)
            > solid.second_moment(10.0) / solid.area(10.0))


def test_the_section_modulus_is_the_second_moment_over_the_outer_fibre(materials):
    for name in CANDIDATES:
        m = materials[name]
        assert m.section_modulus(12.0) == pytest.approx(
            m.second_moment(12.0) / 6.0, rel=1e-12
        )


# --- agreement with the module that already knew half of this ---------------


@pytest.mark.parametrize("variant", VARIANTS)
def test_bend_stress_is_the_strain_span_already_computes_times_the_modulus(variant):
    """`span.bend_strain` is pure geometry -- `d / 2R`, no material in it --
    and has been tested since before there was a material. This is the same
    quantity in megapascals, and the two must never drift apart, because
    `docs/span.md` and `docs/strength.md` each quote one of them."""
    v = config.load(variant)
    m = material.load()
    assert m.bend_stress(v.rod_diameter, v.radius) == pytest.approx(
        m.modulus_mpa * span.bend_strain(v.rod_diameter, v.radius), rel=1e-12
    )


def test_the_thickest_bendable_rod_inverts_the_bend_stress(materials):
    """`bendable_diameter` is the `d <= 2Re` constraint `span.ceiling` is built
    on, with a real allowable strain instead of one of its four samples. A rod
    exactly that thick must land exactly on the allowable."""
    m = materials["gost31938"]
    for radius in (1500.0, 3000.0, 6000.0):
        d = m.bendable_diameter(radius)
        assert m.bend_stress(d, radius) == pytest.approx(
            m.allowable("sustained", "tension"), rel=1e-12
        )
