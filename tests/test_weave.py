"""The four-rod node: coplanarity, the single fan, and the stacking order.

The coplanarity test is the important one. It is what turns the lashed node
from a four-rod puzzle in three dimensions into a flat fan, and it is a
consequence of the geometry rather than a modelling choice -- so if it ever
stops holding, something upstream is wrong.
"""

from __future__ import annotations

import pytest

from stardome import config, geometry, model, weave

# Every named variant, so adding one to the config puts it under test.
VARIANTS = sorted(config.load_all())

EXPECTED_GAPS = [37.377368, 41.810315, 37.377368, 63.434949]


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param))


def test_all_four_tangents_are_coplanar(built):
    """A great circle's tangent lies in the sphere's tangent plane."""
    analysis = weave.analyse(built)
    assert analysis["coplanarity_residual"] < 1e-12


def test_one_fan_serves_every_lashed_node(built):
    analysis = weave.analyse(built)
    assert analysis["tied_node_count"] == 10
    assert analysis["distinct_fans"] == 1
    assert analysis["groups"][0]["node_count"] == 10


def test_fan_gaps_close_the_half_turn(built):
    group = weave.analyse(built)["groups"][0]
    assert group["gaps_deg"] == pytest.approx(EXPECTED_GAPS, abs=1e-5)
    assert sum(group["gaps_deg"]) == pytest.approx(180.0, abs=1e-9)


def test_high_and_low_nodes_are_the_same_fan_with_families_swapped(built):
    """Five nodes read G-U-U-G and five read L-G-G-L, but the fan is one shape."""
    bows = {b.name: b for b in geometry.build_bows()}
    tied = [n for n in built["nodes"] if n["rod_count"] == 4]
    highs = [n for n in tied if n["z"] > built["meta"]["dome_radius"] * 0.7]
    lows = [n for n in tied if n["z"] < built["meta"]["dome_radius"] * 0.7]
    assert len(highs) == 5 and len(lows) == 5

    def families(node):
        return [row[2] for row in weave.node_fan(node, bows)]

    def canon(node):
        return weave.canonical_gaps(
            weave.fan_gaps([row[0] for row in weave.node_fan(node, bows)])
        )

    assert families(highs[0]) == ["G", "U", "U", "G"]
    assert families(lows[0]) == ["L", "G", "G", "L"]
    assert canon(highs[0]) == canon(lows[0])


def test_chosen_stack_uses_the_shallowest_contacts(built):
    """Fan order was chosen because its three contacts are the shallowest available."""
    analysis = weave.analyse(built)
    assert analysis["stack_order"] == [0, 1, 2, 3]
    assert analysis["stack_contacts"] == pytest.approx(
        [37.377368, 41.810315, 37.377368], abs=1e-5
    )
    options = analysis["groups"][0]["stacking_options"]
    chosen = [o for o in options if o["chosen"]]
    assert len(chosen) == 1
    sharpest = min(o["sharpest_contact"] for o in options)
    assert chosen[0]["sharpest_contact"] == pytest.approx(sharpest, abs=1e-9)


def test_stack_height_is_three_rod_diameters(built):
    analysis = weave.analyse(built)
    assert analysis["stack_height"] == pytest.approx(
        3.0 * built["meta"]["rod_diameter"], abs=1e-9
    )


def test_radial_migration_is_negligible(built):
    """The cost of fan order: rods change level between nodes.

    Measured across the family: 0.95% at D12 up to 2.55% at D3 -- the smaller
    the dome, the shorter the arc between nodes and the steeper the ramp, so
    D3 is the tight case. 2.55% is 1.46 deg on a rod already bent to a 1500 mm
    radius. The threshold is a regression guard, not a limit anyone is near.
    """
    mig = weave.migration(built)
    assert mig["worst_slope"] < 0.035
    # Family U never leaves the middle of the fan.
    u_rods = [r for r in mig["rods"] if r["family"] == "U"]
    assert u_rods and all(r["level_span"] <= 1 for r in u_rods)


def test_every_rod_has_a_level_at_every_node_it_passes(built):
    levels = weave.rod_levels(built)
    counts = {name: len(v) for name, v in levels.items()}
    for rod in built["rods"]:
        expected = 4 if rod["family"] == "G" else 2
        assert counts[rod["name"]] == expected


def test_linear_interpolation_between_nodes_does_not_work(built):
    """The obvious guess fails, which is why global_profile exists.

    Routing each rod straight between the offsets its lashed nodes dictate
    leaves half the unlashed crossings with the two rods sharing space.
    """
    violations = weave.linear_profile_violations(built)
    assert len(violations) == 15
    assert all(not v["tied"] for v in violations)
    worst = min(v["separation_mm"] for v in violations)
    assert worst < 0.2 * built["meta"]["rod_diameter"]


def test_a_globally_consistent_weave_exists(built):
    g = weave.global_profile(built)
    assert g["feasible"]
    assert g["violations"] == []
    assert g["crossings_checked"] == 90
    assert g["tightest_separation_mm"] >= built["meta"]["rod_diameter"] - 1e-6


def test_the_weave_needs_no_room_beyond_the_stack(built):
    """The rods stay inside the band the four-rod stack already requires."""
    g = weave.global_profile(built)
    assert g["band_mm"] <= g["stack_half_height_mm"] + 1e-6


def test_the_route_is_gentle(built):
    """A rod leaving its great circle by about a degree is not a constraint.

    The measured range is 0.59 deg at D12 up to 1.57 deg at D3 -- the weave
    gets easier as the dome grows, because the arc between nodes grows faster
    than the rod. D3 is the tight case. The threshold here is a regression
    guard, not a limit anyone is near.
    """
    g = weave.global_profile(built)
    assert g["worst_slope"] < 0.035
    assert g["worst_slope_deg"] < 2.0


def test_lashed_offsets_are_untouched_by_the_solver(built):
    g = weave.global_profile(built)
    d = built["meta"]["rod_diameter"]
    allowed = {round((lvl - 2.5) * d, 6) for lvl in (1, 2, 3, 4)}
    lashed = [s for stops in g["routes"].values() for s in stops if s["lashed"]]
    assert len(lashed) == 40
    assert all(round(s["offset_mm"], 6) in allowed for s in lashed)


def test_the_solver_is_deterministic(built):
    a = weave.global_profile(built)
    b = weave.global_profile(built)
    assert a["routes"] == b["routes"]
    assert a["tightest_separation_mm"] == b["tightest_separation_mm"]


def test_every_stacking_order_admits_a_consistent_weave(built):
    """Feasibility does not depend on the order chosen -- only its cost does."""
    import itertools

    seen = set()
    for perm in itertools.permutations(range(4)):
        if perm[::-1] in seen:
            continue
        seen.add(perm)
        assert weave.global_profile(built, perm)["feasible"], perm
