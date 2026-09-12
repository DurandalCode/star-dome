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


def _part(sched, kind, part_id=None):
    hits = [p for p in sched["parts"] if p["kind"] == kind]
    if part_id is not None:
        hits = [p for p in hits if p["id"] == part_id]
        assert len(hits) == 1, f"expected exactly one {part_id}, got {len(hits)}"
        return hits[0]
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
    assert totals["generatable_now"] >= 40
    # Everything without a generator is waiting for one, whatever kind it is.
    assert totals["awaiting_a_generator"] == sum(
        p["count"] for p in sched["parts"] if not p.get("generator")
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


def test_a_skirt_does_not_make_the_base_point_a_different_joint():
    """It used to be eight members and nothing designed. It is three.

    The old reading put the post head, two ring chords and two brace heads on
    the hub, which made the busiest joint in the structure the one place no
    part existed for. None of them has to go there. The hub already carries a
    through slot for a driven steel angle; a post is that same angle made
    longer, so it is no more a member of this joint than a stake is, and the
    skirt's own members land on a collar clamped to the post below the hub.

    What that buys is that a skirted dome and a bare one use the SAME base
    hub -- see docs/decisions/0017.
    """
    from stardome import connectors, model

    skirted = connectors.schedule(model.build(config.load("S")))
    bare = connectors.schedule(model.build(config.load("M")))

    def hubs(sched):
        return {p["id"].split("-")[0]: p for p in sched["parts"]
                if p["kind"] == "base_hub"}

    with_skirt, without = hubs(skirted), hubs(bare)
    assert set(with_skirt) == set(without) == {"BASE3", "BASE2"}
    for key in with_skirt:
        assert with_skirt[key]["members"] == without[key]["members"]
        assert with_skirt[key]["count"] == without[key]["count"]
        assert with_skirt[key]["generator"] == "base_hub_v1"
        assert with_skirt[key]["state"] == connectors.GENERATED
        # The angle in the slot reaches the ground either way.
        assert with_skirt[key]["anchored_by_stake"] is True

    assert sum(h["count"] for h in with_skirt.values()) == 10


def test_the_post_and_the_stake_are_one_member():
    """A post and a stake at one point would be two things in one place."""
    from stardome import connectors, model

    skirted = connectors.schedule(model.build(config.load("S")))
    bare = connectors.schedule(model.build(config.load("M")))

    here = _part(skirted, "ground_stake")
    there = _part(bare, "ground_stake")
    assert here["count"] == there["count"] == 10
    assert here["state"] == there["state"] == connectors.HARDWARE
    assert there["standing_mm"] == 0.0
    assert here["standing_mm"] == config.load("S").skirt_height
    assert here["is_the_post"] is True
    assert there["is_the_post"] is False


def test_the_skirt_joins_on_one_collar_used_at_both_ends_of_every_post():
    """Two ring chords and two brace ends, at each end of each post.

    The two ends are the same shape: the chords leave level on both and the
    braces leave at the same angle, down at the head and up at the foot. So it
    is one geometry turned over, not two parts -- twenty of one thing.
    """
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("S")))
    collar = _part(sched, "skirt_collar")
    data = model.build(config.load("S"))
    posts = data["skirt"]["post_count"]

    assert collar["count"] == 2 * posts
    assert collar["ends_per_post"] == 2
    assert collar["generator"] == "skirt_collar_v1"
    assert collar["state"] == connectors.GENERATED

    # Derived from the post count, not typed in: the chord to the next post
    # round a regular decagon leaves at 90 + 180/10 from the outward radius.
    assert collar["chord_azimuths_deg"][0] == pytest.approx(90.0 + 180.0 / posts)
    assert sum(collar["chord_azimuths_deg"]) == pytest.approx(360.0)
    assert collar["brace_rise_deg"] == pytest.approx(
        data["skirt"]["brace_angle_deg"]
    )

    # The two posts beside the doorway carry one empty side, at both ends.
    assert len(collar["one_side_unused"]) == 2 * len(data["skirt"]["open_bays"])


def test_a_foot_collar_is_a_head_collar_turned_over():
    """The claim the part rests on, checked in the placements rather than in
    the drawing: the two bases differ by a half turn about the outward radius,
    which is what makes one printed geometry serve both ends."""
    from stardome import connectors, model

    data = model.build(config.load("S"), weave_mode="woven")
    spots = [
        s for s in connectors.schedule(data)["placements"]
        if s["kind"] == "skirt_collar"
    ]
    assert len(spots) == 2 * data["skirt"]["post_count"]

    by_post = {}
    for spot in spots:
        post, end = spot["at"].rsplit("_", 1)
        by_post.setdefault(post, {})[end] = spot

    for post, ends in by_post.items():
        head, foot = ends["head"], ends["foot"]
        assert head["turned_over"] is False
        assert foot["turned_over"] is True
        # Same outward radius, opposite axis, and a right-handed frame either
        # way -- exactly a half turn about local +X.
        assert head["basis"][0] == foot["basis"][0], post
        assert head["basis"][1] == [-c for c in foot["basis"][1]], post
        assert head["basis"][2] == [-c for c in foot["basis"][2]], post
        assert head["origin_mm"][2] == 0.0
        assert foot["origin_mm"][2] == pytest.approx(
            -data["skirt"]["height"]
        )


def test_nothing_in_the_skirt_is_left_without_a_part_except_the_header():
    """The skirt used to contribute twelve parts with nothing at all."""
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("S")))
    nothing = [
        p for p in sched["parts"] if p.get("state") == connectors.UNDESIGNED
    ]
    assert [p["kind"] for p in nothing] == ["header_clamp"]


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
    hubs = {p["id"]: p for p in sched["parts"] if p["kind"] == "base_hub"}
    assert sum(h["count"] for h in hubs.values()) == 10
    for hub in hubs.values():
        # The hub itself is drawn now -- it is the node's fan with one arm
        # fewer -- and every foot on a bare dome sits over a driven angle.
        assert hub["state"] == connectors.GENERATED
        assert hub["generator"] == "base_hub_v1"
        assert hub["anchored_by_stake"] is True

    assert hubs["BASE3-10"]["members"] == 3
    assert hubs["BASE3-10"]["count"] == 8

    stake = _part(sched, "ground_stake")
    assert stake["count"] == 10
    assert stake["state"] == connectors.HARDWARE


def test_the_doorway_takes_a_bow_off_the_two_feet_it_stands_between():
    """The portal cut is not free at the ground, and this is what it costs.

    The cut frees a bow end at each of the two feet the door stands between,
    so those two gather two arms and the other eight gather three. A schedule
    that still asked for ten identical hubs would be asking for a part that
    does not fit at the one place anybody stands.

    What it does not cost is a second geometry. Both jambs keep the same pair
    of arms -- the U bow and the G bow -- at the same 37.3774 deg the node fan
    already uses, and the two are mirror images, so one printed part turned
    over serves both.
    """
    from stardome import connectors, doorway, model

    data = model.build(config.load("M"))
    cuts = {r: [tuple(s) for s in v]
            for r, v in data["doorway"]["cut"]["spans"].items()}
    assert doorway.feet_released(data, cuts) == {"b0": ["L1"], "b1": ["L4"]}

    sched = connectors.schedule(data)
    jamb = _part(sched, "base_hub", "BASE2-10")
    assert jamb["count"] == 2
    assert jamb["members"] == 2
    assert jamb["bow_ends"] == 2
    assert jamb["families_in_fan_order"] == ["U", "G"]
    assert jamb["fan_gaps_deg"] == [37.377368]
    assert jamb["handed"] is True
    assert jamb["generator"] == "base_hub_v1"


def test_a_cut_bow_ends_in_a_crossing_and_wants_a_part_that_knows_it():
    """TERM is a rod END against a rod, which CL2 is not.

    The portal cut stops two L bows at crossings rather than at their feet.
    The clamp there holds one rod that stops and one that carries on, so it
    has a closed channel and an open one -- and the part has to be told which
    crossing, at what angle, and which way the surviving bow runs.

    Both land on the same 70.5288 deg every unlashed crossing uses, and in
    both the terminating bow is the outer of the two, so this is one part.
    """
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("M")))
    term = _part(sched, "cut_termination")
    assert term["count"] == 2
    assert term["nodes"] == ["N25", "N26"]
    assert term["crossing_angle"] == 70.5288

    ends = term["terminations"]
    assert {e["rod"] for e in ends} == {"L1", "L4"}
    assert {e["other_rod"] for e in ends} == {"U1", "U4"}
    assert {e["approach"] for e in ends} == {"+", "-"}
    assert all(e["ends_above"] for e in ends)


def test_splices_are_the_largest_part_count_on_any_real_size(sched):
    """A bow is far longer than a transportable section, so it is spliced.

    On the smaller domes a bow still fits in three sections and there are
    fewer of these than crossings; from D6 up they outnumber everything else
    in the schedule put together, which is what makes the sleeve the part
    worth getting right before any of the others.
    """
    splice = _part(sched, "rod_splice")
    assert splice["generator"] == "rod_splice_v2"
    # The sleeve is drawn on the dome radius, because the bow is bent to it
    # everywhere; a splice does not get a straight piece of rod to sit on.
    assert splice["bend_radius"] == sched_radius(sched)
    others = max(
        p["count"] for p in sched["parts"] if p["kind"] != "rod_splice"
    )
    if sched["meta"]["variant"] in ("D3", "D4"):
        assert splice["count"] <= others
    else:
        assert splice["count"] > others


def sched_radius(sched):
    """The dome radius the schedule was derived from."""
    return config.load(sched["meta"]["variant"]).radius


def test_the_portal_cut_leaves_terminations_that_are_not_crossings():
    """A bow that starts at a crossing needs a different clamp from one that
    passes through it, and there are two of them per cut door."""
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("M")))
    term = _part(sched, "cut_termination")
    assert term["count"] == 2
    assert term["generator"] == "term_clamp_v1"


def test_the_base_point_is_a_flat_fan_like_the_node(sched):
    """The result that decides what the base hub is.

    A great circle through a point on the sphere's equator has its tangent
    there in the surface, and the surface at the equator is the vertical plane
    tangent to the base ring. So all three bows leave a base point in one
    plane, with no radial component at all -- the same reason the four bows at
    a lashed node are coplanar.

    That makes the base hub the node's part with one arm fewer, rather than
    some new kind of thing, and it shares two of the node's gap angles.
    """
    from stardome import model, weave

    data = model.build(config.load(sched["meta"]["variant"], skirt_height=0.0))
    fan = weave.base_fan(data)

    assert fan["coplanar"]
    assert fan["coplanarity_residual"] < 1e-12
    assert fan["gaps_deg"] == pytest.approx([41.8103, 37.3774], abs=1e-4)
    assert fan["spread_deg"] == pytest.approx(79.1877, abs=1e-4)


def test_the_base_fan_shares_the_node_fan_s_gaps(sched):
    """41.8103 and 37.3774 appear in both, which is why one architecture
    serves both parts."""
    node = _part(sched, "four_rod_fan")
    hub = [p for p in sched["parts"] if p["kind"] == "base_hub"][0]
    assert set(round(g, 4) for g in hub["fan_gaps_deg"]) <= set(
        round(g, 4) for g in node["fan_gaps_deg"]
    )


def test_the_bows_rise_at_their_own_family_tilts(sched):
    """Each bow leaves the ground at exactly its family's tilt.

    Not a coincidence: at the equator the tangent's rise *is* the tilt, so the
    base hub's three arm angles are the three numbers the whole dome is built
    from.
    """
    from stardome import geometry, model, weave

    data = model.build(config.load(sched["meta"]["variant"], skirt_height=0.0))
    fan = weave.base_fan(data)
    tilts = geometry.family_tilts()
    tilts["G"] = geometry.TILT_G

    for arm in fan["arms"]:
        assert arm["rise_deg"] == pytest.approx(tilts[arm["family"]], abs=1e-4)


def test_the_ten_base_points_are_two_mirror_sets_of_five(sched):
    """So one geometry still serves them all, turned over for the other half."""
    from stardome import model, weave

    data = model.build(config.load(sched["meta"]["variant"], skirt_height=0.0))
    fan = weave.base_fan(data)
    assert fan["distinct_fans"] == 1 or fan["mirror_pairs"]
    assert fan["base_points"] == 10


def _woven(name):
    from stardome import model

    return model.build(config.load(name), weave_mode="woven", include_polylines=True)


def test_every_part_the_schedule_asks_for_has_somewhere_to_go():
    """A part counted but not placed is a part that quietly went missing."""
    from stardome import connectors

    sched = connectors.schedule(_woven("M"))
    assert sched["placements_note"] is None
    placed = {}
    for spot in sched["placements"]:
        placed[spot["part"]] = placed.get(spot["part"], 0) + 1
    for part in sched["parts"]:
        assert placed.get(part["id"]) == part["count"], part["id"]
    assert len(sched["placements"]) == sched["totals"]["parts_per_dome"]


def test_a_flat_model_cannot_say_where_a_part_goes():
    """Which rod runs outside is what fixes a part's stack, and flat has none."""
    from stardome import connectors, model

    sched = connectors.schedule(model.build(config.load("M")))
    assert sched["placements"] == []
    assert "woven" in sched["placements_note"]


def test_every_connector_lands_on_the_rods_it_holds():
    """The frames are read off the generators, so check them against the dome.

    Each part is flat: arms in local XY, stack along local Z. Put the
    generator's own arm azimuths and stack levels through the placement's
    basis and they have to come out on the real rods, at the real radial
    offsets the weave gives them. A millimetre here is a connector floating
    off its rod in the scene.
    """
    import math

    from stardome import connectors, geometry, vec

    data = _woven("M")
    sched = connectors.schedule(data)
    bows = {b.name: b for b in geometry.build_bows()}
    parts = {p["id"]: p for p in sched["parts"]}
    offset_at = connectors._rod_offset_sampler(data)
    rod_d = data["meta"]["rod_diameter"]
    nodes = {n["name"]: n for n in data["nodes"]}
    crossings = {c["node"]: c for c in data["crossings"]}

    def to_world(basis, local):
        return tuple(
            sum(local[k] * basis[k][i] for k in range(3)) for i in range(3)
        )

    checked = 0
    for spot in sched["placements"]:
        part = parts[spot["part"]]
        basis, origin = spot["basis"], spot["origin_mm"]

        # Right-handed, or the part is mirrored and would not print as drawn.
        det = sum(
            basis[0][i] * vec.cross(basis[1], basis[2])[i] for i in range(3)
        )
        assert abs(det - 1.0) < 1e-6, spot["at"]

        if spot["kind"] == "four_rod_fan":
            point = tuple(nodes[spot["at"]][k] for k in "xyz")
            azimuths = connectors._azimuths(part["fan_gaps_deg"][:-1], 0.0)
            pitch = part["stack_height"] / 3.0
            arms = spot["arms"]
            # Arm k sits at stack level k, innermost first.
            levels = [(k - 1.5) * pitch for k in range(4)]
        elif spot["kind"] in ("two_rod_clamp", "cut_termination"):
            contact = crossings[spot["at"]]
            point = (contact["x"], contact["y"], contact["z"])
            half = part["crossing_angle"] / 2.0
            if spot["hand"] == "mirrored":
                half = -half
            azimuths = [half, -half]
            arms = [spot["rod_above"], spot["rod_below"]]
            # The cap is outside, so the upper rod is the one at +v/2.
            levels = [+rod_d / 2.0, -rod_d / 2.0]
        else:
            continue

        normal = vec.unit(point)
        for k, rod in enumerate(arms):
            t = bows[rod].t_of(point)
            angle = math.radians(azimuths[k])
            placed = to_world(basis, (math.cos(angle), math.sin(angle), 0.0))
            real = vec.unit(bows[rod].tangent(t))
            # Rods are lines, so compare them as lines.
            assert abs(abs(vec.dot(placed, real)) - 1.0) < 1e-9, (spot["at"], rod)

            axis = tuple(origin[i] + levels[k] * basis[2][i] for i in range(3))
            want = tuple(
                point[i] + offset_at(rod, t) * normal[i] for i in range(3)
            )
            assert vec.dist(axis, want) < 1e-6, (spot["at"], rod)
            checked += 1
    assert checked == 10 * 4 + 30 * 2 + 2 * 2


def test_the_two_rod_clamp_is_chiral_and_the_dome_needs_both_hands():
    """The cap goes outside, and that is what makes the part handed.

    Turning a two-piece clamp over to make its angles agree puts the cap on
    the inside, under the rod it is meant to hold down. So the mirror-image
    crossings need the mirror-image part, and the schedule says how many.
    """
    from stardome import connectors

    sched = connectors.schedule(_woven("M"))
    clamp = _part(sched, "two_rod_clamp")
    assert clamp["hands"] == {"as-drawn": 17, "mirrored": 13}
    assert sum(clamp["hands"].values()) == clamp["count"]


def test_the_four_rod_fan_never_has_to_be_turned_over():
    """Unlike the base hub, the fan sits stack-outward at all ten nodes.

    That matters because the stack is five different plates: turned over, the
    Cap would be on the inside. It works out because the fan is cut at its
    widest gap, which makes the ten nodes one part in the same orientation.
    """
    from stardome import connectors

    sched = connectors.schedule(_woven("M"))
    fans = [p for p in sched["placements"] if p["kind"] == "four_rod_fan"]
    assert len(fans) == 10
    assert not any(f["turned_over"] for f in fans)

    feet = [p for p in sched["placements"] if p["kind"] == "base_hub"]
    turned = sum(1 for f in feet if f["turned_over"])
    assert turned == 5, "the base hubs are two mirror sets of five"


def test_the_splice_is_a_ferrule_and_not_a_clamp():
    """A splice joins two sections, and before assembly those are two objects.

    So it is the one joint in the dome that never has to close around
    anything: the sections slide in from the ends, the way a tent pole joins.
    V1 was the crossing clamp's two-piece bolted architecture copied into a
    place that does not need it -- the clamp has bolts beside the rod because
    two rods cross there and nothing can sit on the axis -- and it cost
    48.4 mm of width on a 10 mm rod.

    This does not check the solid, which needs FreeCAD. It checks that the
    schedule still describes the joint the ferrule was drawn for: one rod, a
    known bend radius to relieve the middle against, and a sleeve long enough
    not to be a hinge.
    """
    from stardome import connectors

    sched = connectors.schedule(_woven("M"))
    splice = _part(sched, "rod_splice")
    assert splice["generator"] == "rod_splice_v2"
    assert splice["members"] == 2
    assert splice["sleeve_length"] == connectors.SPLICE_SLEEVE_DIAMETERS * 10.0
    assert splice["bend_radius"] == 3000.0
    # Five rod diameters of engagement each side of the butt.
    assert splice["sleeve_length"] / 2.0 / 10.0 == 5.0


def test_no_splice_lands_on_a_crossing():
    """A sleeve on a crossing cannot be clamped and cannot be woven past, and
    the crossing already carries a part of its own. So every joint clears the
    nearest crossing by at least the sleeve's own length."""
    from stardome import connectors

    for name in ("S", "M", "L", "XL"):
        sched = connectors.schedule(_woven(name))
        splice = _part(sched, "rod_splice")
        sleeve = splice["sleeve_length"]
        assert splice["joints"]
        for joint in splice["joints"]:
            assert joint["clear_of_crossing_mm"] >= sleeve - 1e-6, (
                name, joint["rod"], joint["clear_of_crossing_mm"], sleeve
            )


def test_the_stake_knows_which_way_is_out_and_which_way_is_down():
    """The driven angle is hardware, but where it stands is not arbitrary.

    It goes in vertically -- you hammer it, and the ground is down -- and it
    passes through a slot the hub carries UNDER the bow bundle, offset towards
    the dome centre. So the frame has to say which way is outward, or a
    consumer cannot put the angle on the correct side, and the two mirror sets
    of feet would get it on opposite ones.
    """
    from stardome import connectors, vec

    sched = connectors.schedule(_woven("M"))
    stakes = [p for p in sched["placements"] if p["kind"] == "ground_stake"]
    assert len(stakes) == 10

    for spot in stakes:
        ex, ey, ez = (tuple(row) for row in spot["basis"])
        # Driven: local +Z is straight down, at every foot.
        assert ez == (0.0, 0.0, -1.0), spot["at"]
        # Local +Y is outward from the dome axis, so an inboard offset is
        # negative along it wherever the foot happens to be.
        radial = vec.unit((spot["origin_mm"][0], spot["origin_mm"][1], 0.0))
        assert vec.dot(ey, radial) > 0.999, spot["at"]
        # Right-handed, like every other placement.
        det = sum(ex[i] * vec.cross(ey, ez)[i] for i in range(3))
        assert abs(det - 1.0) < 1e-9, spot["at"]


# --------------------------------------------------------------------------
# the fastener schedule
# --------------------------------------------------------------------------
# What this guards is not arithmetic -- it is the distinction the schedule
# was missing entirely until decision 0020: a bolt done up on a bench and a
# bolt done up at head height are not the same item, and rule 1 of this
# project only cares about the second. See docs/quick-release.md.
def test_every_part_says_what_holds_it_together(sched):
    """No part is silently left without a fastener row.

    A kind with no entry reads exactly like a kind with nothing to fasten,
    and the two are very different: the splice genuinely has no bolts, and a
    part somebody forgot to list would quietly stop being counted.
    """
    known = set(connectors._FASTENERS)
    kinds = {p["kind"] for p in sched["parts"]}
    assert kinds <= known, f"no fastener row for {sorted(kinds - known)}"


def test_the_tally_is_the_parts_added_up(sched):
    """The totals are the rows, not a second count that can drift."""
    tally = sched["fasteners"]
    by_hand = 0
    for part in sched["parts"]:
        for row in part.get("fasteners") or []:
            by_hand += row["count"] * part["count"]
    assert tally["total"] == by_hand
    assert tally["field_total"] + tally["shop_total"] == tally["total"]


def test_the_base_hub_does_its_bolts_at_home(sched):
    """Where each generator says the work happens.

    `base_hub_v1`: "the stack is assembled once, on the ground or at home,
    and the bow ends go in afterwards" -- so its bolts are shop work and its
    pins are field work. `fan_node_v2` opens its stack at the dome, so its
    are not. If a generator's field sequence ever changes, this is what
    notices.
    """
    hub = [p for p in sched["parts"] if p["kind"] == "base_hub"]
    assert hub, "every dome has base points"
    for part in hub:
        rows = {(r["type"], r["worked"]): r["count"] for r in part["fasteners"]}
        assert rows[(connectors.BOLT, connectors.SHOP)] == 2
        assert rows[(connectors.PIN, connectors.FIELD)] == part["bow_ends"]

    fan = _part(sched, "four_rod_fan")
    assert all(r["worked"] == connectors.FIELD for r in fan["fasteners"])


def test_the_field_bolts_are_most_of_the_bolts(sched):
    """The number the whole quick-release argument rests on.

    On a bare dome it is 84 against 20 -- and it is the same 84 at every
    size, because the topology is. A skirt adds its collars on top.
    """
    tally = sched["fasteners"]
    assert tally["field"][connectors.BOLT] > tally["shop"][connectors.BOLT]
    if not any(p["kind"] == "skirt_collar" for p in sched["parts"]):
        assert tally["field"][connectors.BOLT] == 84
    assert tally["shop"][connectors.BOLT] == 20


def test_hinging_the_clamp_moves_work_out_of_the_field(sched):
    """Decision 0020, counted rather than claimed.

    The hinged closure turns one of a clamp's two bolts into a pin that is
    fitted once, so every clamp and every termination gives up exactly one
    field bolt -- and nothing anywhere gets more field work than it had.
    """
    bolted = sched["closures"][connectors.BOLTED]
    hinged = sched["closures"][connectors.HINGED]

    hinged_kinds = ("two_rod_clamp", "cut_termination")
    moved = sum(p["count"] for p in sched["parts"] if p["kind"] in hinged_kinds)
    # Thirty untied crossings at every size, plus one termination per bow the
    # doorway cuts -- which is two on a dome with a door and none on D3,
    # where the schedule carries no doorway at all.
    assert moved >= 30

    assert hinged["field"][connectors.BOLT] == bolted["field"][connectors.BOLT] - moved
    assert hinged["shop"][connectors.PIN] == moved
    assert hinged["total"] == bolted["total"], "same joints, closed differently"
    for kind in (connectors.BOLT, connectors.PIN):
        assert hinged["field"][kind] <= bolted["field"][kind]


def test_the_bolt_is_the_one_decision_0013_chose(sched):
    """One rule for the bolt size, and the schedule reads it from source."""
    rod = _part(sched, "four_rod_fan")["rod_diameter"]
    assert sched["fasteners"]["size"] == connectors.fastener_for(rod)
