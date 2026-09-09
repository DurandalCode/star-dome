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


CROSSING_KINDS = ("four_rod_fan", "two_rod_clamp")


def _crossing_parts(sched):
    return [p for p in sched["parts"] if p["kind"] in CROSSING_KINDS]


def test_the_lattice_needs_two_connector_geometries(sched):
    """Two parts serve all forty rod-to-rod crossings.

    That was once the whole schedule. It is now the easy half of it: the
    joints where the dome meets the ground, the skirt and itself lengthwise
    outnumber the crossings and have no design at all.
    """
    assert len(_crossing_parts(sched)) == 2
    kinds = sorted(p["kind"] for p in _crossing_parts(sched))
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


def test_every_crossing_part_has_a_generator(sched):
    """The whole connector set is buildable from the model.

    This test previously asserted the opposite -- that the fan had no
    generator -- so that landing one could not pass unnoticed. It landed;
    `connectors/fan_node_v1.py` builds it.
    """
    assert _part(sched, "four_rod_fan")["generator"] == "fan_node_v2"
    assert _part(sched, "two_rod_clamp")["generator"] == "crossing_clamp_v1"
    totals = sched["totals"]
    assert totals["generatable_now"] == 40
    # And everything that is not a crossing is waiting for one.
    assert totals["awaiting_a_generator"] == sum(
        p["count"] for p in sched["parts"] if p["kind"] not in CROSSING_KINDS
    )
    assert totals["awaiting_a_generator"] > 0


def test_every_crossing_point_is_accounted_for(sched):
    """The forty crossings are covered. The rest of the schedule is not a
    crossing and is counted separately."""
    totals = sched["totals"]
    assert totals["crossing_points"] == 40
    assert sum(p["count"] for p in _crossing_parts(sched)) == 40
    assert totals["parts_per_dome"] > 40
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


def test_the_base_point_is_the_busiest_joint_in_the_structure():
    """Eight members at one point on a skirted dome, and nothing designed.

    Three bow ends arrive at three different inclinations, the post head from
    below, two ring chords pulling sideways and two brace heads pulling
    diagonally. That is twice the four-rod fan, which does have a part.
    """
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("S")))
    hubs = [p for p in sched["parts"] if p["kind"] == "base_hub"]
    assert hubs
    assert max(h["members"] for h in hubs) == 8
    assert sum(h["count"] for h in hubs) == 10
    assert all(h["generator"] is None for h in hubs)

    fan = _part(sched, "four_rod_fan")
    assert max(h["members"] for h in hubs) > fan["count"] // 2  # 8 > 5


def test_a_bare_dome_anchors_its_feet_with_a_stake_and_still_needs_a_hub():
    """Without a skirt the base point is three rod ends over a driven angle.

    The stake is what resists the dome spreading -- through soil, the way a
    tent peg does -- and it is hardware, a size to specify rather than a shape
    to design. What it does not do is gather three bow ends arriving at three
    different inclinations, so the hub is still undesigned. Splitting those
    two is the whole point of the state field.
    """
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("M")))
    hubs = [p for p in sched["parts"] if p["kind"] == "base_hub"]
    assert len(hubs) == 1
    assert hubs[0]["members"] == 3
    assert hubs[0]["count"] == 10
    assert hubs[0]["state"] == connectors.UNDESIGNED
    assert hubs[0]["anchored_by_stake"] is True

    stake = _part(sched, "ground_stake")
    assert stake["count"] == 10
    assert stake["state"] == connectors.HARDWARE


def test_the_skirted_base_point_is_out_of_a_stake_s_reach():
    """S's busiest joint sits 1.35 m up on top of a post.

    That is the one place the stake argument does not reach, and it is also
    the joint with the most members in the structure.
    """
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("S")))
    hubs = [p for p in sched["parts"] if p["kind"] == "base_hub"]
    assert max(h["members"] for h in hubs) == 8
    assert all(h["state"] == connectors.UNDESIGNED for h in hubs)
    assert all(h["anchored_by_stake"] is False for h in hubs)

    # The post feet below them, by contrast, are hardware.
    feet = [p for p in sched["parts"] if p["kind"] == "post_foot"]
    assert feet
    assert all(f["state"] == connectors.HARDWARE for f in feet)


def test_splices_are_the_largest_part_count_on_any_real_size(sched):
    """A bow is far longer than a transportable section, so it is spliced.

    On the smaller domes a bow still fits in three sections and there are
    fewer of these than crossings; from D6 up they outnumber everything else
    in the schedule, and nothing generates them.
    """
    splice = _part(sched, "rod_splice")
    assert splice["generator"] is None
    others = max(
        p["count"] for p in sched["parts"] if p["kind"] != "rod_splice"
    )
    if sched["meta"]["variant"] in ("D3", "D4"):
        assert splice["count"] <= others
    else:
        assert splice["count"] > others


def test_the_portal_cut_leaves_terminations_that_are_not_crossings():
    """A bow that starts at a crossing needs a different clamp from one that
    passes through it, and there are two of them per cut door."""
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("M")))
    term = _part(sched, "cut_termination")
    assert term["count"] == 2
    assert term["generator"] is None
