"""The connector schedule derived from the dome model.

These lock in the finding that drives connector design: the baseline topology
needs exactly one two-rod clamp geometry, and it does not cover the nodes the
reference actually lashes.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, connectors, model

VARIANTS = ["D4", "D6", "D8", "D12"]

TETRAHEDRAL = round(math.degrees(math.acos(1 / 3)), 4)


@pytest.fixture(scope="module", params=VARIANTS)
def sched(request):
    return connectors.schedule(model.build(config.load(request.param)))


def test_one_two_rod_clamp_geometry(sched):
    """All 30 unlashed crossings share a single angle, so one part serves them."""
    assert len(sched["parts"]) == 1
    part = sched["parts"][0]
    assert part["kind"] == "two_rod_clamp"
    assert part["count"] == 30
    assert part["crossing_angle"] == pytest.approx(TETRAHEDRAL, abs=1e-4)
    assert part["tied"] is False


def test_four_rod_nodes_are_reported_not_silently_skipped(sched):
    assert len(sched["unsupported"]) == 1
    entry = sched["unsupported"][0]
    assert entry["rod_count"] == 4
    assert entry["count"] == 10
    assert entry["pair_angles"] == pytest.approx(
        [37.3774, 41.8103, 63.4349, 79.1877], abs=1e-4
    )


def test_every_crossing_point_is_accounted_for(sched):
    totals = sched["totals"]
    assert totals["covered_nodes"] + totals["uncovered_nodes"] == totals["crossing_points"]
    assert totals["crossing_points"] == 40


def test_the_clamp_covers_only_crossings_the_reference_leaves_untied(sched):
    """V1 solves the crossings the original design does not tie, and vice versa.

    Worth a test rather than a comment: if a future change makes the two-rod
    clamp cover a lashed crossing, that is a real design shift and should not
    pass silently.
    """
    assert all(part["tied"] is False for part in sched["parts"])


def test_part_id_encodes_rod_diameter_and_angle(sched):
    part = sched["parts"][0]
    assert str(int(part["rod_diameter"])) in part["id"]
    assert f"{part['crossing_angle']:.4f}" in part["id"]


def test_schedule_scales_only_in_rod_diameter():
    """Crossing angles are topology; only the rod stock changes per variant."""
    angles = set()
    diameters = set()
    for name in VARIANTS:
        s = connectors.schedule(model.build(config.load(name)))
        angles.add(s["parts"][0]["crossing_angle"])
        diameters.add(s["parts"][0]["rod_diameter"])
    assert len(angles) == 1
    assert len(diameters) > 1
