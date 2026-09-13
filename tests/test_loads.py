"""The wind, and the partition of the cover it arrives on.

Two things here are worth guarding. The first is that the tributary strips are
a **partition**: every square millimetre of cover belongs to exactly one bow,
so the strips sum to the shell with no residue and no double counting. If that
identity ever breaks, every line load in `strength.py` is wrong by an unknown
factor and nothing else would notice.

The second is the shape of the pressure field. The finding that decides what
this whole calculation is *about* -- that a bare dome lifts rather than tips --
falls straight out of pressure being normal to a sphere, and it would be
reversed by a sign error nobody would see in a table of newtons.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, cover, loads, material, model

VARIANTS = ["D3", "D4", "D6", "D8", "D10", "D12"]
BARE = ["D6", "D8", "D10", "D12"]
SKIRTED = ["D3", "D4"]


@pytest.fixture(scope="module")
def built():
    return {
        name: model.build(
            config.load(name), weave_mode="woven", include_polylines=True
        )
        for name in VARIANTS
    }


@pytest.fixture(scope="module")
def cfg():
    return loads.load()


# --- pressure ---------------------------------------------------------------


def test_velocity_pressure_goes_as_the_square_of_the_speed(cfg):
    """The identity that makes a limiting speed solvable in closed form: the
    whole load field is built once and scaled, rather than re-integrated at
    every speed a bisection tries."""
    assert loads.velocity_pressure(20.0, cfg) == pytest.approx(
        4.0 * loads.velocity_pressure(10.0, cfg), rel=1e-12
    )
    assert loads.velocity_pressure(0.0, cfg) == 0.0


def test_the_shape_coefficient_hits_its_tabulated_points(cfg):
    """0, 90 and 180 degrees are EN 1991-1-4 figure 7.12's A, B and C, read at
    f/d = 0.5. Everything between them is interpolation, and if the endpoints
    drift the config and the code have stopped agreeing."""
    assert loads.shape_coefficient(0.0, cfg) == pytest.approx(cfg.cp_windward)
    assert loads.shape_coefficient(90.0, cfg) == pytest.approx(cfg.cp_crown)
    assert loads.shape_coefficient(180.0, cfg) == pytest.approx(cfg.cp_lee)


def test_most_of_the_shell_is_in_suction(cfg):
    """The premise of the whole result. If a majority of the dome were in
    positive pressure the governing action would be drag, the answer would be
    about overturning, and the field rule would be a different rule."""
    sampled = [loads.shape_coefficient(t, cfg) for t in range(0, 181, 5)]
    assert sum(1 for c in sampled if c < 0) > 0.6 * len(sampled)


def test_an_open_door_makes_the_uplift_worse(built, cfg):
    """Internal pressure pushes out everywhere the outside is already sucking.
    It is the one mitigation in this calculation that is free, so the sign of
    it had better be right."""
    for name in VARIANTS:
        shut = loads.resultants(built[name], 20.0, cfg, door="shut")
        opened = loads.resultants(built[name], 20.0, cfg, door="open")
        assert opened["lift_n"] > shut["lift_n"], name


def test_lift_and_drag_both_scale_as_the_square_of_the_speed(built, cfg):
    one = loads.resultants(built["D6"], 10.0, cfg)
    two = loads.resultants(built["D6"], 20.0, cfg)
    # abs rather than rel: `resultants` rounds its newtons to three decimals
    # for the report, so the identity is exact underneath and the last digit
    # is display. A milli-newton on three kilonewtons is not a disagreement.
    assert two["lift_n"] == pytest.approx(4.0 * one["lift_n"], abs=0.01)
    assert two["drag_n"] == pytest.approx(4.0 * one["drag_n"], abs=0.01)


# --- the dome lifts, it does not tip ----------------------------------------


@pytest.mark.parametrize("name", BARE)
def test_a_bare_dome_has_no_overturning_couple(built, cfg, name):
    """Pressure acts normal to the shell; every normal of a sphere is radial;
    so every facet force passes through the sphere's centre -- which for a
    bare dome sits in the ground plane. The resultant is a pure force and the
    rigid-body failure mode is uplift, not tipping.

    `interior.md` ranks variants on a `tip_index` and says, correctly, that it
    "proves nothing about safety". This is the answer it declined to give.

    Not asserted as exactly zero: the cover is a faceted mesh, so what is left
    is discretisation. Four orders of magnitude below drag times the radius is
    the scale a real couple would be on.
    """
    r = loads.resultants(built[name], 20.0, cfg)
    scale = r["drag_n"] * built[name]["meta"]["dome_radius"]
    assert r["overturning_nmm"] / scale < 1e-3, name


@pytest.mark.parametrize("name", SKIRTED)
def test_a_skirt_puts_the_centre_up_and_a_real_couple_appears(built, cfg, name):
    """The other half of the argument above. A skirt raises the sphere's
    centre off the ground, the forces no longer pass through a point on the
    base plane, and the dome acquires a genuine overturning moment -- which is
    a cost of a skirt nobody had priced."""
    r = loads.resultants(built[name], 20.0, cfg)
    scale = r["drag_n"] * built[name]["meta"]["dome_radius"]
    assert r["overturning_nmm"] / scale > 0.1, name


# --- the tributary strips are a partition -----------------------------------


@pytest.mark.parametrize("name", VARIANTS)
def test_the_strips_tile_the_cover_with_no_residue(built, cfg, name):
    """The identity the line loads rest on. Every facet is assigned to exactly
    one bow, so the areas sum to the meshed shell exactly -- not nearly. A
    smearing scheme, or a facet counted twice, shows up here and nowhere
    else."""
    data = built[name]
    facets = loads._facets(data, loads.LOAD_MERIDIANS, loads.LOAD_PARALLELS)
    meshed_dome = sum(a for _, a, _, is_skirt in facets if not is_skirt)
    t = loads.tributary(data)
    assert t["dome_area_mm2"] == pytest.approx(meshed_dome, rel=1e-9), name


@pytest.mark.parametrize("name", VARIANTS)
def test_the_partition_converges_on_the_analytic_hemisphere(built, cfg, name):
    """The meshed shell under-measures the true one, because a faceted sphere
    is inscribed in it. Within a tenth of a per cent at the resolution used,
    which is well inside everything else's uncertainty -- but it is a
    discretisation and is checked rather than assumed."""
    data = built[name]
    t = loads.tributary(data)
    analytic = cover.areas(data)["dome_m2"] * 1e6
    assert t["dome_area_mm2"] == pytest.approx(analytic, rel=2e-3), name
    assert t["dome_area_mm2"] <= analytic


def test_an_average_strip_width_is_wrong_everywhere_in_particular(built, cfg):
    """Why the partition is computed rather than estimated as cover area over
    rod length. The per-bow averages alone spread by half again, and that is
    before the variation along one bow."""
    t = loads.tributary(built["D6"])
    widths = [v["width_mm"] for v in t["per_rod"].values()]
    assert max(widths) / min(widths) > 1.3


def test_a_bare_dome_has_no_skirt_to_carry(built, cfg):
    for name in BARE:
        assert loads.tributary(built[name])["skirt_area_mm2"] == 0.0
    for name in SKIRTED:
        assert loads.tributary(built[name])["skirt_area_mm2"] > 0.0


def test_the_scattered_forces_sum_to_the_independent_resultant(built, cfg):
    """Two routes to the same newtons: scatter every facet onto a bow and add
    the pieces up, or integrate over the shell without a structural model at
    all. They are separate code paths and must agree exactly."""
    data = built["D6"]
    facets = loads.facet_loads(data, 20.0, cfg)
    spread = loads.scatter(data, facets)
    total = [0.0, 0.0, 0.0]
    for items in spread["by_rod"].values():
        for _, facet in items:
            total = [total[i] + facet["force_n"][i] for i in range(3)]
    total = [total[i] + spread["skirt_force_n"][i] for i in range(3)]
    r = loads.resultants(data, 20.0, cfg)
    assert total[2] == pytest.approx(r["lift_n"], abs=0.01)
    assert math.hypot(total[0], total[1]) == pytest.approx(r["drag_n"], abs=0.01)


# --- weight -----------------------------------------------------------------


@pytest.mark.parametrize("name", VARIANTS)
def test_the_rod_mass_is_its_length_times_its_linear_mass(built, cfg, name):
    """The first density in this repository. `docs/bom.md` closes with "Money,
    and mass. Both want a supplier and a material, and this project has
    neither yet" -- the mass half is answered by this line."""
    data = built[name]
    m = material.load()
    w = loads.self_weight(data, m, cfg)
    expected = (data["meta"]["total_rod_length"] / 1000.0) \
        * m.linear_mass(data["meta"]["rod_diameter"])
    assert w["rod_kg"] == pytest.approx(expected, abs=1e-3), name


def test_the_wind_lifts_far_more_than_the_dome_weighs(built, cfg):
    """The sentence this whole module exists to be able to say. At 20 m/s a
    bare D6 weighs about a tenth of what the wind pulls up, so what holds it
    down is the ten driven angles and nothing else."""
    data = built["D6"]
    w = loads.self_weight(data, material.load(), cfg)
    r = loads.resultants(data, 20.0, cfg)
    assert r["lift_n"] > 5.0 * w["total_n"]
