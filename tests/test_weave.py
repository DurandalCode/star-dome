"""The four-rod node: coplanarity, the single fan, and the stacking order.

The coplanarity test is the important one. It is what turns the lashed node
from a four-rod puzzle in three dimensions into a flat fan, and it is a
consequence of the geometry rather than a modelling choice -- so if it ever
stops holding, something upstream is wrong.
"""

from __future__ import annotations

import pytest

from stardome import config, geometry, model, weave

VARIANTS = ["D4", "D6", "D8", "D12"]

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
    """The cost of fan order: rods change level between nodes. Quantified, it is small."""
    mig = weave.migration(built)
    assert mig["worst_slope"] < 0.02
    # Family U never leaves the middle of the fan.
    u_rods = [r for r in mig["rods"] if r["family"] == "U"]
    assert u_rods and all(r["level_span"] <= 1 for r in u_rods)


def test_every_rod_has_a_level_at_every_node_it_passes(built):
    levels = weave.rod_levels(built)
    counts = {name: len(v) for name, v in levels.items()}
    for rod in built["rods"]:
        expected = 4 if rod["family"] == "G" else 2
        assert counts[rod["name"]] == expected
