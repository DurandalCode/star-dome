"""The material catalogue, and the duplication it exists to prevent.

The bug this file guards against was real: the same rod's density was typed
in two modules and its modulus in a third, so measuring the actual stock
would have meant editing three places and the mass figures could drift apart
without anything noticing.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from stardome import config, materials, rod, splice, wind

PACKAGE = pathlib.Path(materials.__file__).parent


def test_the_rod_has_one_density_and_every_module_uses_it():
    """The bug, pinned."""
    catalogue = materials.ROD[materials.DEFAULT_ROD]["density_kgm3"]
    assert rod.GFRP_DENSITY == catalogue
    assert wind.GFRP_DENSITY == catalogue


def test_the_rod_has_one_modulus_and_it_is_the_catalogue_s():
    assert splice.ROD_MODULUS_MPA == (
        materials.ROD[materials.DEFAULT_ROD]["modulus_mpa"]
    )


PROPERTY_NAMES = ("DENSITY", "MODULUS", "GSM", "ALLOWABLE", "GRAVITY")


def test_no_module_types_a_material_property_of_its_own():
    """A material property may be NAMED elsewhere, but not typed elsewhere.

    Matching bare numbers was too crude -- 1900 is also a doorway height in
    millimetres. This looks for a module-level constant whose name says it is
    a material property and whose value is a literal rather than a lookup.
    """
    offenders = []
    for path in sorted(PACKAGE.glob("*.py")):
        if path.name == "materials.py":
            continue
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if not any(word in target.id for word in PROPERTY_NAMES):
                    continue
                if isinstance(node.value, ast.Constant):
                    offenders.append(f"{path.name}: {target.id}")
    assert not offenders, offenders


def test_every_catalogue_entry_says_whether_it_was_measured():
    for catalogue in materials.CATALOGUES.values():
        for entry in catalogue.values():
            assert "measured" in entry


def test_nothing_has_been_measured_yet_and_the_module_admits_it():
    """When this starts failing, someone has weighed something. Update it."""
    unmeasured = materials.unmeasured()
    assert len(unmeasured) == sum(
        len(c) for c in materials.CATALOGUES.values()
    )
    assert "rod.gfrp_pultruded" in unmeasured


def test_an_unknown_material_names_the_ones_that_exist():
    with pytest.raises(ValueError, match="oxford_210d"):
        materials.get("fabric", "hessian")
    with pytest.raises(ValueError, match="fabric"):
        materials.get("upholstery", "hessian")


# --- a variant chooses, it does not define -------------------------------
def test_every_variant_names_materials_that_exist():
    for name in sorted(config.load_all()):
        variant = config.load(name)
        materials.get("rod", variant.rod_material)
        materials.get("fabric", variant.cover_fabric)
        materials.get("sleeve", variant.sleeve_material)


def test_the_recorded_sleeve_decision_is_the_default():
    """Steel, male-female, threaded stud. See docs/transport.md."""
    assert materials.DEFAULT_SLEEVE == "steel_mild"
    assert config.load("M").sleeve_material == "steel_mild"


def test_a_typo_in_the_config_fails_at_load_not_in_a_report():
    with pytest.raises(ValueError):
        config._material("fabric", {"cover_fabric": "oxford_900d"}, {},
                         "oxford_600d", key="cover_fabric")


def test_domes_on_different_rod_diameters_share_one_material():
    """Which is the point of naming the material instead of its properties."""
    small = config.load("D4")   # 8 mm
    large = config.load("D12")  # 12 mm
    assert small.rod_diameter != large.rod_diameter
    assert small.rod_material == large.rod_material


def test_mass_follows_the_chosen_material(built_m=None):
    from stardome import model

    data = model.build(config.load("M"))
    assert rod.mass(data)["material"] == materials.DEFAULT_ROD
    assert rod.mass(data)["measured"] is False


def test_the_catalogue_is_the_only_place_with_a_sleeve_property():
    """splice.MATERIALS is a view, not a second copy."""
    for name, entry in materials.SLEEVE.items():
        modulus, allowable, density, wall, made = splice.MATERIALS[name]
        assert modulus == entry["modulus_mpa"]
        assert allowable == entry["allowable_mpa"]
        assert density == entry["density_kgm3"]
        assert wall == entry["min_wall_mm"]
        assert made == entry["made_by"]


def test_air_and_gravity_are_physical_not_assumptions():
    assert wind.AIR_DENSITY == materials.AIR_DENSITY
    assert wind.GRAVITY == materials.GRAVITY
    assert materials.AIR_CONDITION
