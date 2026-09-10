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


def test_even_division_runs_out_on_the_biggest_dome():
    """Which is the argument for not dividing evenly at all.

    D12 has to reach 23 equal sections before the joints clear a ferrule AND
    a connector, and 23 sections is 22 splices per bow. The room was never
    missing -- even division just does not aim at it.
    """
    d12 = model.build(config.load("D12"), weave_mode="layered")
    chosen = splice.choose_sections(d12)
    assert chosen["sections"] > 20


def test_placing_in_the_gaps_solves_every_variant(built):
    """The right question: the crossings leave gaps, so put the joints there."""
    for limit in (3000.0, 3500.0):
        plan = splice.place_splices(built, limit)
        for fam, info in plan["by_family"].items():
            assert info["longest_section_mm"] <= limit + 0.5
            assert info["sections"] >= 1


def test_placement_reaches_the_fewest_sections_possible(built):
    """Greedy from the foot is optimal: ceil(bow / limit) and no more."""
    limit = 3500.0
    plan = splice.place_splices(built, limit)
    floor = math.ceil(rod.bows(built)["length_mm"] / limit)
    for info in plan["by_family"].values():
        assert info["sections"] == floor


def test_every_placed_joint_keeps_its_margin_from_a_crossing(built):
    """The whole point: room for the ferrule AND the connector beside it."""
    plan = splice.place_splices(built, 3500.0)
    radius = built["meta"]["dome_radius"]
    spans = splice.free_spans(built, plan["margin_mm"])
    for fam, info in plan["by_family"].items():
        for cut in info["cuts_deg"]:
            inside = any(lo - 1e-6 <= cut <= hi + 1e-6
                         for lo, hi in spans[fam]["usable_deg"])
            assert inside, (fam, cut)


def test_the_sections_come_out_unequal_and_the_families_differ(built):
    """The price of aiming at the room, and worth reporting rather than hiding."""
    plan = splice.place_splices(built, 3500.0)
    assert plan["margin_mm"] > 0
    lengths = {tuple(v["section_lengths_mm"]) for v in plan["by_family"].values()}
    # G is crossed in fifths and U/L in an alternating rhythm, so at least two
    # different cut lists come out of it on any dome that needs a splice.
    if any(v["splices_per_bow"] for v in plan["by_family"].values()):
        assert plan["cut_lists"] == len(lengths)


def test_a_section_limit_nothing_can_meet_is_refused(built):
    with pytest.raises(ValueError):
        splice.place_splices(built, 50.0)


def test_clearing_costs_sections_and_the_report_says_how_many():
    d4 = model.build(config.load("D4"), weave_mode="layered")
    chosen = splice.choose_sections(d4)
    assert chosen["extra_sections"] >= 1
    assert chosen["extra_splices_total"] == chosen["extra_sections"] * 15


def test_the_free_spans_are_what_the_families_make_them(built):
    """G is crossed in fifths, U and L in an alternating pair of gaps."""
    spans = splice.free_spans(built, 0.0)
    assert len(spans["G"]["crossings_deg"]) == 4
    assert len(spans["U"]["crossings_deg"]) == 8
    assert spans["G"]["widest_gap_deg"] == pytest.approx(
        spans["G"]["narrowest_gap_deg"], abs=1e-6
    )
    assert spans["U"]["widest_gap_deg"] > spans["U"]["narrowest_gap_deg"]


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
