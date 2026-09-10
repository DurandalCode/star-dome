"""What the section ferrule should be made of.

The result worth locking in is the one that inverts the intuition: the metals
cannot be made thin enough to share the bow's curve, and printed plastic can,
because its modulus is low.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, geometry, model, rod, splice

VARIANTS = sorted(config.load_all())


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param), weave_mode="layered")


# --- the moment the bow already carries -----------------------------------
def test_the_shape_moment_is_E_I_over_R(built):
    meta = built["meta"]
    s = splice.shape_moment(built)
    inertia = math.pi * meta["rod_diameter"] ** 4 / 64.0
    assert s["second_moment_mm4"] == pytest.approx(inertia, abs=0.05)
    assert s["moment_Nmm"] == pytest.approx(
        splice.ROD_MODULUS_MPA * inertia / meta["dome_radius"], abs=0.5
    )


def test_the_rod_is_not_close_to_its_own_limit(built):
    """Bending to shape costs the rod well under a GFRP pultrusion's strength."""
    assert splice.shape_moment(built)["rod_stress_mpa"] < 120.0


def test_a_bigger_dome_bends_its_rod_less_hard():
    small = splice.shape_moment(model.build(config.load("D4")))
    large = splice.shape_moment(model.build(config.load("D12")))
    assert large["rod_stress_mpa"] < small["rod_stress_mpa"]


# --- the finding ----------------------------------------------------------
def test_steel_cannot_be_made_thin_enough_to_share_the_curve(built):
    """0.2 mm of wall is what it would take, and nobody sells that."""
    s = splice.sleeve(built, "steel_mild")
    assert s["wall_for_stiffness_mm"] < s["min_wall_mm"]
    assert s["governed_by"] == "what can be made"
    assert s["stiffness_ratio"] > 3.0


def test_printed_plastic_matches_the_rod_by_construction(built):
    for material in ("printed_pla", "printed_petg", "printed_nylon_cf"):
        s = splice.sleeve(built, material)
        assert s["governed_by"] == "stiffness"
        assert s["stiffness_ratio"] == pytest.approx(1.0, abs=0.02)
        # And the wall it wants is one a printer can lay down.
        assert s["wall_mm"] >= s["min_wall_mm"]


def test_aluminium_is_the_closest_metal(built):
    metals = ("aluminium_6061", "steel_mild", "stainless_304",
              "cast_aluminium", "cast_bronze")
    ratios = {m: splice.sleeve(built, m)["stiffness_ratio"] for m in metals}
    assert min(ratios, key=ratios.get) == "aluminium_6061"


def test_casting_is_stiffer_still_because_of_its_minimum_wall(built):
    cast = splice.sleeve(built, "cast_aluminium")
    drawn = splice.sleeve(built, "aluminium_6061")
    assert cast["min_wall_mm"] > drawn["min_wall_mm"]
    assert cast["stiffness_ratio"] > drawn["stiffness_ratio"]


def test_strength_never_decides_it(built):
    """Every material survives the shape moment at a makeable wall."""
    for material in splice.MATERIALS:
        s = splice.sleeve(built, material)
        assert s["utilisation"] < 1.0


def test_the_comparison_is_sorted_by_how_well_it_matches(built):
    rows = splice.compare(built)
    scores = [abs(math.log(r["stiffness_ratio"])) for r in rows]
    assert scores == sorted(scores)
    assert rows[0]["material"].startswith("printed")


def test_an_unknown_material_is_refused(built):
    with pytest.raises(ValueError):
        splice.sleeve(built, "unobtainium")


# --- the sleeve as an object ----------------------------------------------
def test_a_thicker_sleeve_weighs_more(built):
    light = splice.sleeve(built, "printed_nylon_cf")
    heavy = splice.sleeve(built, "printed_petg")
    assert heavy["wall_mm"] > light["wall_mm"]
    assert heavy["mass_g"] > light["mass_g"]


def test_the_bore_clears_the_rod(built):
    s = splice.sleeve(built, "aluminium_6061", clearance_mm=0.4)
    assert s["bore_mm"] == pytest.approx(
        built["meta"]["rod_diameter"] + 0.4, abs=1e-6
    )
    assert s["od_mm"] > s["bore_mm"]
    assert s["over_rod_mm"] > 0


def test_a_whole_dome_of_them(built):
    row = splice.sleeve(built, "printed_pla")
    total = splice.per_dome(built, row)
    assert total["splices"] == rod.sections(built)["splices_total"]
    assert total["mass_kg"] == pytest.approx(
        total["splices"] * row["mass_g"] / 1000.0, abs=0.01
    )


# --- and it must miss the crossings ---------------------------------------
def test_the_collision_is_with_the_thirds_marking_itself():
    """Not bad luck: a third of 180 degrees is where U and L are marked.

    Dividing a bow into three puts joints at the third points, and the
    reference marks the U and L bows at exactly those points -- so the
    crossings are there because the marks are there. Any section count that
    is a multiple of three collides by definition.
    """
    data = model.build(config.load("D4"), weave_mode="layered")
    on_bow = set()
    for crossing in data["crossings"]:
        for family_key, t_key in (("family_a", "t_a_deg"),
                                  ("family_b", "t_b_deg")):
            if crossing[family_key] in ("U", "L"):
                on_bow.add(round(crossing[t_key], 6))

    for mark in geometry.MARKS_THIRDS:
        assert mark in on_bow

    for count in (3, 6):
        joints = {round(180.0 * i / count, 6) for i in range(1, count)}
        assert set(geometry.MARKS_THIRDS) <= joints
        assert not splice.joint_clearance(
            data, limit_mm=180.0 / count * 0.99999
        )["clears"]


def test_divisible_by_three_or_five_hits_and_nothing_else_does():
    """The rule, exactly: thirds mark U and L, fifths mark G."""
    data = model.build(config.load("D4"), weave_mode="layered")
    bow = rod.bows(data)["length_mm"]
    for count in range(2, 15):
        clear = splice.joint_clearance(
            data, sleeve_length_mm=1.0, limit_mm=bow / count + 1e-9
        )
        assert clear["joints_per_bow"] == count - 1
        collides = count % 3 == 0 or count % 5 == 0
        assert (clear["closest_deg"] < 1e-6) is collides, count


def test_the_transport_minimum_can_land_a_joint_on_a_crossing():
    """The finding. Dividing a bow into three puts joints at 60 and 120 deg,
    and the star has crossings at exactly 60 and 120."""
    hits = []
    for name in VARIANTS:
        data = model.build(config.load(name), weave_mode="layered")
        if not splice.joint_clearance(data)["clears"]:
            hits.append(name)
    assert hits, "the whole point of choose_sections is that this happens"
    assert "D4" in hits and "D8" in hits


def test_the_chosen_section_count_always_clears(built):
    """The project has required this from the start; this is what checks it."""
    chosen = splice.choose_sections(built)
    clear = splice.joint_clearance(
        built, limit_mm=chosen["length_mm"] + 1e-9
    )
    assert clear["clears"]
    assert clear["spare_mm"] > 0
    assert chosen["sections"] >= chosen["transport_minimum"]


def test_clearing_costs_sections_and_the_report_says_how_many():
    d4 = model.build(config.load("D4"), weave_mode="layered")
    chosen = splice.choose_sections(d4)
    assert chosen["extra_sections"] >= 1
    assert chosen["extra_splices_total"] == chosen["extra_sections"] * 15


def test_the_biggest_dome_pays_the_most_to_clear():
    """D12 has to go from 8 sections to 13, which is 75 extra splices."""
    d12 = model.build(config.load("D12"), weave_mode="layered")
    chosen = splice.choose_sections(d12)
    assert chosen["extra_sections"] >= 4


def test_the_joints_sit_at_even_fractions_of_the_bow(built):
    clear = splice.joint_clearance(built)
    per_bow = rod.sections(built)["per_bow"]
    assert clear["joints_per_bow"] == per_bow - 1
    for i, joint in enumerate(clear["joints_deg"], start=1):
        assert joint == pytest.approx(180.0 * i / per_bow, abs=0.01)


def test_a_long_enough_sleeve_would_stop_clearing(built):
    """The check has teeth: make the ferrule absurd and it fails."""
    assert not splice.joint_clearance(built, sleeve_length_mm=6000.0)["clears"]


def test_a_bow_that_travels_whole_has_no_joint_to_clear(built):
    clear = splice.joint_clearance(built, limit_mm=0.0)
    assert clear["joints_per_bow"] == 0
    assert clear["clears"]
