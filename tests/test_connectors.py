"""The connector schedule derived from the dome model.

These lock in the finding that drives connector design: the whole dome needs
two connector geometries, not the twelve its symmetry classes might suggest.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, connectors, model

# Every named variant, so adding one to the config puts it under test.
VARIANTS = sorted(config.load_all())

TETRAHEDRAL = round(math.degrees(math.acos(1 / 3)), 4)


@pytest.fixture(scope="module", params=VARIANTS)
def sched(request):
    return connectors.schedule(model.build(config.load(request.param)))


def _part(sched, kind):
    hits = [p for p in sched["parts"] if p["kind"] == kind]
    assert len(hits) == 1, f"expected exactly one {kind}, got {len(hits)}"
    return hits[0]


def test_the_dome_needs_two_connector_geometries(sched):
    assert sched["totals"]["distinct_part_types"] == 2
    kinds = sorted(p["kind"] for p in sched["parts"])
    assert kinds == ["four_rod_fan", "two_rod_clamp"]


def test_one_two_rod_clamp_geometry(sched):
    """All 30 unlashed crossings share a single angle, so one part serves them."""
    part = _part(sched, "two_rod_clamp")
    assert part["count"] == 30
    assert part["crossing_angle"] == pytest.approx(TETRAHEDRAL, abs=1e-4)
    assert part["tied"] is False
    assert part["generator"] == "crossing_clamp_v1"


def test_one_four_rod_fan_serves_every_lashed_node(sched):
    part = _part(sched, "four_rod_fan")
    assert part["count"] == 10
    assert part["tied"] is True
    assert part["coplanar"] is True
    assert part["fan_gaps_deg"] == pytest.approx(
        [37.377368, 41.810315, 37.377368, 63.434949], abs=1e-5
    )
    assert sum(part["fan_gaps_deg"]) == pytest.approx(180.0, abs=1e-6)


def test_every_part_has_a_generator(sched):
    """The whole connector set is buildable from the model.

    This test previously asserted the opposite -- that the fan had no
    generator -- so that landing one could not pass unnoticed. It landed;
    `connectors/fan_node_v1.py` builds it.
    """
    assert _part(sched, "four_rod_fan")["generator"] == "fan_node_v2"
    assert _part(sched, "two_rod_clamp")["generator"] == "crossing_clamp_v1"
    totals = sched["totals"]
    assert totals["generatable_now"] == 40
    assert totals["awaiting_a_generator"] == 0


def test_every_crossing_point_is_accounted_for(sched):
    totals = sched["totals"]
    assert totals["crossing_points"] == 40
    assert totals["parts_per_dome"] == 40
    assert totals["uncovered_nodes"] == 0
    assert sched["unsupported"] == []


def test_the_clamp_covers_only_crossings_the_reference_leaves_untied(sched):
    """V1 solves the crossings the original design does not tie, and vice versa."""
    assert _part(sched, "two_rod_clamp")["tied"] is False
    assert _part(sched, "four_rod_fan")["tied"] is True


def test_schedule_scales_only_in_rod_diameter():
    """Crossing angles are topology; only the rod stock changes per variant."""
    angles = set()
    diameters = set()
    heights = set()
    for name in VARIANTS:
        s = connectors.schedule(model.build(config.load(name)))
        angles.add(_part(s, "two_rod_clamp")["crossing_angle"])
        diameters.add(_part(s, "two_rod_clamp")["rod_diameter"])
        heights.add(_part(s, "four_rod_fan")["stack_height"])
    assert len(angles) == 1
    assert len(diameters) > 1
    # Stack height is three rod diameters, so it tracks the rod, not the dome.
    assert len(heights) == len(diameters)
