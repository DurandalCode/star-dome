"""Connector schedule: what parts the dome actually needs.

This turns "how many connector types does the Star Dome need" from an argument
into a derivation. It reads the built model and groups every crossing into the
part that would serve it.

The answer for the baseline topology is uncomfortable and worth stating plainly:

- The 30 unlashed crossings are all two-rod contacts at exactly one angle,
  ``acos(1/3)`` = 70.5288 deg. One part type covers every one of them.
- The 10 lashed nodes each join FOUR rods at a single point, with six pairwise
  angles between them. A two-rod clamp cannot serve them at all.

The reference lashes the second group and leaves the first alone, so the
two-rod clamp solves the crossings the original design does not tie, and does
not solve the ones it does. See docs/roadmap.md milestone 3.
"""

from __future__ import annotations

import math

from . import SCHEMA_VERSION, doorway, weave

SCHEMA = f"star_dome_connectors/{SCHEMA_VERSION}"

# How many rods a two-piece crossing clamp of the V1 architecture can hold.
TWO_ROD_CLAMP_CAPACITY = 2

ANGLE_DP = 4

# How long a splice ferrule has to be, in rod diameters.
#
# A bow is bent everywhere -- to the dome radius, the whole way round -- so a
# splice is not a butt joint with a collar over it: it is a sleeve that has to
# carry that bending across itself, five diameters of engagement each side of
# the butt. Too short and it is a hinge at the one place a continuous member
# was carrying moment. Ten diameters is the working assumption the geometry
# uses to keep splices clear of the crossings; the generator owns the real
# number, and if it moves, this moves with it.
SPLICE_SLEEVE_DIAMETERS = 10.0

# What still has to be *made*, against what merely has to be chosen.
#
# A driven steel angle takes the ground anchorage at every point that touches
# the earth: it resists uplift and, through the soil, the horizontal thrust.
# That is hardware -- a size and a length to specify, not a shape to design --
# and it removes a whole column from the list of things this project has to
# draw. What it does not do is gather three bow ends arriving at three
# different inclinations and hold them to each other; that is still a part, or
# a lashing, and calling the stake an answer to it would be wishful.
GENERATED = "generated"      # a script produces the geometry today
HARDWARE = "hardware"        # bought or cut to length; specify, do not design
UNDESIGNED = "undesigned"    # nothing exists and something must


def _part_id(kind: str, rod_diameter: float, angle: float) -> str:
    return f"{kind}-{rod_diameter:g}-{angle:.{ANGLE_DP}f}"


def _joint_parts(data: dict, rod_diameter: float) -> list:
    """Every joint that is not a rod-to-rod crossing.

    The crossing schedule above answers "how many clamp types does the lattice
    need". It says nothing about the places where the dome meets the ground,
    the skirt, or itself lengthwise -- and those are most of the joints, and
    include the busiest one in the whole structure.
    """
    meta = data["meta"]
    skirt = data.get("skirt")
    door = data.get("doorway")
    parts = []

    # --- base points ---------------------------------------------------------
    #
    # Three rod ends meet here in any case. With a skirt they are joined by the
    # post head, two ring chords and two brace heads: eight members at one
    # point, which is more than the four-rod fan and has no design at all.
    at_base = {b["name"]: 3 for b in data["base_nodes"]}

    # A doorway cut takes a bow end off the two feet the door stands between,
    # so those two gather two arms and not three. Eight identical hubs and two
    # different ones is the truth; ten identical hubs is a part that does not
    # fit where it matters most.
    cuts = {}
    if door and door.get("cut"):
        cuts = {r: [tuple(s) for s in v] for r, v in door["cut"]["spans"].items()}
    released = doorway.feet_released(data, cuts) if cuts else {}
    for name, rods in released.items():
        at_base[name] -= len(rods)

    if skirt:
        for post in skirt["posts"]:
            at_base[post["base_node"]] += 1
        for seg in skirt["top_ring"]:
            at_base[seg["from"]] += 1
            at_base[seg["to"]] += 1
        by_point = {
            (round(post["x"]), round(post["y"])): post for post in skirt["posts"]
        }
        for brace in skirt["braces"]:
            head = by_point[(round(brace["b"][0]), round(brace["b"][1]))]
            at_base[head["base_node"]] += 1

    fan = weave.base_fan(data, removed=released)

    grouped: dict = {}
    for name, count in at_base.items():
        grouped.setdefault(count, []).append(name)
    for count, names in sorted(grouped.items(), reverse=True):
        on_ground = not skirt
        # Every point in a group has the same member count, and the fan is
        # the same shape at all of them up to the mirror, so one of them
        # describes the part. Take the first by name so the answer does not
        # depend on dict order.
        here = fan["by_base"][sorted(names)[0]]
        bows_here = len(here["arms"])
        # The generator draws a flat fan of bow ends, however many. What it
        # cannot draw is the skirted hub, where the post head, two ring chords
        # and the brace heads arrive on top of the bows: that is a different
        # problem and still has nothing.
        drawable = count == bows_here
        parts.append(
            {
                "id": f"BASE{count}-{rod_diameter:g}",
                "kind": "base_hub",
                "rod_diameter": rod_diameter,
                "count": len(names),
                "nodes": sorted(names),
                "tied": True,
                "members": count,
                "bow_ends": bows_here,
                "generator": "base_hub_v1" if drawable else None,
                "state": GENERATED if drawable else UNDESIGNED,
                "anchored_by_stake": on_ground,
                "coplanar": fan["coplanar"],
                "fan_gaps_deg": here["gaps_deg"],
                "fan_spread_deg": here["spread_deg"],
                # In the plane the part is drawn in, measured from horizontal
                # along the base ring. NOT the same as the rises below: an arm
                # past 90 deg is coming back DOWN, so BASE2's outer arm sits at
                # 116.5651 deg and rises 63.4349. The generator wants the
                # azimuth, and asking it to work one out from the other is how
                # a hub comes out mirrored.
                "arm_azimuths_deg": [a["in_plane_deg"] for a in here["arms"]],
                "families_in_fan_order": [a["family"] for a in here["arms"]],
                "rises_deg": [a["rise_deg"] for a in here["arms"]],
                "handed": fan["mirror_pairs"],
                "note": (
                    f"{bows_here} bow ends"
                    + (
                        ", the post head, two ring chords and the brace heads"
                        if count > bows_here
                        else ""
                    )
                    + ". They arrive at "
                    + ("two" if bows_here == 2 else "three")
                    + " different inclinations and have to be held to each "
                    "other"
                    + (
                        ", 1.35 m in the air on top of a post, where no stake "
                        "can reach."
                        if count > bows_here
                        else " and to the stake under them."
                    )
                    + (
                        "  This is a doorway jamb: the cut took its third bow "
                        "away, so it holds two, and the missing arm is the "
                        "one that used to run across the opening."
                        if bows_here < 3
                        else ""
                    )
                ),
            }
        )

    if not skirt:
        parts.append(
            {
                "id": "STAKE-BASE",
                "kind": "ground_stake",
                "rod_diameter": rod_diameter,
                "count": len(data["base_nodes"]),
                "nodes": sorted(b["name"] for b in data["base_nodes"]),
                "tied": False,
                "members": 1,
                "generator": None,
                "state": HARDWARE,
                "note": (
                    "A driven steel angle at each base point. This is what "
                    "resists the dome spreading at its feet -- through soil, "
                    "the way a tent peg does -- and it is a size and a length "
                    "to specify rather than a shape to design. It does not "
                    "gather the three bow ends; that is BASE3."
                ),
            }
        )

    # --- post feet -----------------------------------------------------------
    if skirt:
        at_foot = {post["name"]: 1 for post in skirt["posts"]}  # the post itself
        for seg in skirt["bottom_ring"]:
            at_foot[seg["from"]] += 1
            at_foot[seg["to"]] += 1
        by_point = {
            (round(post["x"]), round(post["y"])): post for post in skirt["posts"]
        }
        for brace in skirt["braces"]:
            foot = by_point[(round(brace["a"][0]), round(brace["a"][1]))]
            at_foot[foot["name"]] += 1

        grouped = {}
        for name, count in at_foot.items():
            grouped.setdefault(count, []).append(name)
        for count, names in sorted(grouped.items(), reverse=True):
            parts.append(
                {
                    "id": f"FOOT{count}-{rod_diameter:g}",
                    "kind": "post_foot",
                    "rod_diameter": rod_diameter,
                    "count": len(names),
                    "nodes": sorted(names),
                    "tied": True,
                    "members": count,
                    "generator": None,
                    "state": HARDWARE,
                    "anchored_by_stake": True,
                    "note": (
                        "Post foot, two ring chords and the brace feet, all "
                        "gathered on the driven steel angle that anchors this "
                        "point anyway. Hardware rather than a part: what has "
                        "to be decided is the stake and whether the post is "
                        "pinned or fixed to it, which is what turns racking "
                        "into a bending problem at the feet. See "
                        "docs/skirt.md."
                    ),
                }
            )

        header = skirt.get("header")
        if header:
            parts.append(
                {
                    "id": f"HDR-{rod_diameter:g}",
                    "state": UNDESIGNED,
                    "kind": "header_clamp",
                    "rod_diameter": rod_diameter,
                    "count": len(header["rods"]),
                    "nodes": list(header["rods"]),
                    "tied": True,
                    "members": 2,
                    "generator": None,
                    "note": (
                        "Clamps the header to a bow part-way up its length, "
                        "where there is no crossing to hang it on. It carries "
                        "the top ring's hoop force round the doorway, so it "
                        "is a tension joint on a curved member."
                    ),
                }
            )

    # --- rod terminations left by a cut --------------------------------------
    if cuts:
        ends = doorway.terminations(data, cuts)
        angles = sorted({round(e["crossing_angle_deg"], ANGLE_DP) for e in ends})
        # One angle means one part. If a future cut level ever produced two,
        # the id would have to carry the angle the way CL2's does, so say so
        # rather than quietly averaging them.
        if len(angles) != 1:
            raise ValueError(
                f"terminations land on {len(angles)} different crossing "
                f"angles {angles}; TERM is one part per angle, so this wants "
                "one id per angle rather than one part"
            )
        parts.append(
            {
                "id": _part_id("TERM", rod_diameter, angles[0]),
                "state": GENERATED,
                "kind": "cut_termination",
                "rod_diameter": rod_diameter,
                "count": len(ends),
                "nodes": sorted({e["node"] for e in ends}),
                "tied": True,
                "members": 2,
                "crossing_angle": angles[0],
                "terminations": ends,
                "generator": "term_clamp_v1",
                "note": (
                    "A bow now starts at a crossing instead of passing "
                    "through it. The clamp there holds a rod end against a "
                    "rod, not two rods against each other, and it is the end "
                    "of a member that used to be continuous."
                ),
            }
        )

    # --- splices along each bow ----------------------------------------------
    section = meta.get("section_length") or 0.0
    if section > 0:
        sleeve = SPLICE_SLEEVE_DIAMETERS * rod_diameter
        joints = splice_joints(data, section, sleeve)
        if joints:
            clear = min(j["clear_of_crossing_mm"] for j in joints)
            moved = max(abs(j["moved_mm"]) for j in joints)
            longest = max(max(j["sections_mm"]) for j in joints)
            parts.append(
                {
                    "id": f"SPLICE-{rod_diameter:g}",
                    "state": GENERATED,
                    "kind": "rod_splice",
                    "rod_diameter": rod_diameter,
                    "count": len(joints),
                    "nodes": [],
                    "tied": False,
                    "members": 2,
                    "bend_radius": meta["dome_radius"],
                    "sleeve_length": round(sleeve, 3),
                    "section_length": section,
                    "tightest_clearance_mm": round(clear, 1),
                    "longest_section_mm": round(longest, 1),
                    "worst_move_mm": round(moved, 1),
                    "joints": joints,
                    "generator": "rod_splice_v2",
                    "note": (
                        f"A bow is {meta['rod_length_nominal']:.0f} mm long and "
                        f"transports in {section:.0f} mm sections, so it is "
                        "spliced along its length. A ferrule: the sections "
                        "slide in from the ends, the way a tent pole joins, "
                        "because a splice is the one joint here that never "
                        "has to close around anything. The joint still has to "
                        "carry bending, and the bow is bent to "
                        f"{meta['dome_radius']:.0f} mm radius afterwards, so "
                        "the ferrule's middle is relieved rather than "
                        "close-fitting -- it bears at its two ends and lets "
                        "the bow curve through it. Joints sit at the even "
                        "division of each bow where that clears the crossings "
                        f"and up to {moved:.0f} mm off it where it does not; "
                        f"longest section {longest:.0f} mm, tightest crossing "
                        f"clearance {clear:.0f} mm."
                    ),
                }
            )

    return parts


def _present_spans(rod: dict, cuts: dict) -> list:
    """The stretches of a bow that are still there, in bow parameter.

    A cut is recorded as the pieces REMOVED, so this is the complement inside
    0..180. The portal cut only ever takes an end piece, which leaves one
    stretch; a cut in mid-span would leave two, and each is spliced on its own
    because they travel as separate members.
    """
    spans = sorted(cuts.get(rod["name"], ()))
    out = []
    at = 0.0
    for lo, hi in spans:
        if lo > at + 1e-6:
            out.append((at, lo))
        at = max(at, hi)
    if at < 180.0 - 1e-6:
        out.append((at, 180.0))
    return out


def _allowed_windows(blockers: list, keep_out: float, lo: float, hi: float) -> list:
    """What is left of ``[lo, hi]`` once every blocker keeps its distance."""
    forbidden = []
    for b in blockers:
        a, z = b - keep_out, b + keep_out
        if z <= lo or a >= hi:
            continue
        forbidden.append((max(a, lo), min(z, hi)))
    forbidden.sort()

    windows = []
    at = lo
    for a, z in forbidden:
        if a > at + 1e-9:
            windows.append((at, a))
        at = max(at, z)
    if at < hi - 1e-9:
        windows.append((at, hi))
    return windows


def _nearest_allowed(target: float, windows: list):
    """The point in ``windows`` closest to ``target``; None if there is none."""
    best = None
    for a, z in windows:
        here = min(max(target, a), z)
        if best is None or abs(here - target) < abs(best - target):
            best = here
    return best


def _place_joints(length: float, section: float, keep_out: float,
                  blockers: list) -> list:
    """Joint positions along one stretch: even if that works, nudged if not."""
    sections = max(1, math.ceil(length / section))
    # One extra section is always enough in this geometry -- crossings on a
    # bow are hundreds of millimetres apart and a sleeve is tens -- but the
    # loop is bounded rather than trusting that, so a change of proportions
    # gives an error instead of hanging.
    for extra in range(4):
        n = sections + extra
        joints = [length * i / n for i in range(1, n)]
        ok = True
        for i, target in enumerate(joints):
            before = joints[i - 1] if i else 0.0
            after = joints[i + 1] if i + 1 < len(joints) else length
            windows = _allowed_windows(
                blockers, keep_out,
                max(0.0, after - section), min(length, before + section),
            )
            here = _nearest_allowed(target, windows)
            if here is None:
                ok = False
                break
            joints[i] = here
        if not ok:
            continue
        edges = [0.0] + joints + [length]
        if max(b - a for a, b in zip(edges, edges[1:])) <= section + 1e-6:
            return joints
    raise ValueError(
        f"a {length:.0f} mm bow will not divide into sections of "
        f"{section:.0f} mm with every joint {keep_out:.0f} mm clear of a "
        "crossing; the transport length and the sleeve length disagree"
    )


def splice_joints(data: dict, section: float, sleeve: float) -> list:
    """Where each bow is joined along its length, and how clear of a crossing.

    Two things decide this, and they pull against each other.

    **No section may be longer than the transport length.** That is what puts
    the dome in a car, and it is the reason splices exist at all. It fixes how
    many joints a bow needs: ``ceil(length / section)`` sections, one fewer
    joints than sections.

    **No joint may sit on a crossing.** A sleeve there cannot be clamped and
    cannot be woven past, and the crossing already carries a part of its own.
    So the sleeve clears the crossing by its own length, which leaves room for
    that part as well as for itself.

    Even sections satisfy the first and, on M, happen to satisfy the second.
    They do not in general: the bigger domes cut a bow into more sections, the
    divisions fall closer together, and some land on a crossing. So sections
    start even and each joint is then moved the shortest distance that clears,
    staying inside the window where both of its own sections are still short
    enough to travel. If nothing in that window is clear, the bow takes one
    more section -- shorter ones, more slack, more room to move -- and it is
    tried again.

    Deterministic, and it prefers even sections: a bow that does not need the
    help does not get any.
    """
    from . import geometry

    radius = data["meta"]["dome_radius"]
    mm_per_deg = math.pi * radius / 180.0
    keep_out = sleeve
    door = data.get("doorway")
    cuts = {}
    if door and door.get("cut"):
        cuts = {r: [tuple(sp) for sp in v] for r, v in door["cut"]["spans"].items()}

    crossing_ts: dict = {}
    for c in data["crossings"]:
        for side in ("a", "b"):
            crossing_ts.setdefault(c[f"rod_{side}"], []).append(c[f"t_{side}_deg"])

    bows = {b.name: b for b in geometry.build_bows()}
    out = []
    for rod in data["rods"]:
        bow = bows[rod["name"]]
        ts = sorted(set(crossing_ts.get(rod["name"], [])))
        for lo, hi in _present_spans(rod, cuts):
            length = (hi - lo) * mm_per_deg
            # Arc length from the start of this stretch: the frame both
            # constraints are naturally stated in.
            blockers = [(t - lo) * mm_per_deg for t in ts if lo <= t <= hi]
            placed = _place_joints(length, section, keep_out, blockers)
            edges = [0.0] + list(placed) + [length]
            for i, s_mm in enumerate(placed):
                t = lo + s_mm / mm_per_deg
                clear = min(
                    (abs(s_mm - b) for b in blockers), default=float("inf")
                )
                even = length * (i + 1) / (len(placed) + 1)
                x, y, z = bow.point(t, radius)
                out.append(
                    {
                        "rod": rod["name"],
                        "t_deg": round(t, 6),
                        "s_mm": round(s_mm, 3),
                        "clear_of_crossing_mm": round(clear, 3),
                        "moved_mm": round(s_mm - even, 3),
                        "sections_mm": [
                            round(edges[i + 1] - edges[i], 1),
                            round(edges[i + 2] - edges[i + 1], 1),
                        ],
                        "x": round(x, 6),
                        "y": round(y, 6),
                        "z": round(z, 6),
                    }
                )
    return out

def _rod_offset_sampler(data: dict):
    """A rod's radial offset anywhere along it, read back from a built model.

    Under ``flat`` and ``layered`` this is the rod's one constant. Under
    ``woven`` the rod carries the route it was drawn on, and reading it back
    here is what keeps a connector on the rod rather than near it: the two
    would disagree by up to seven rod diameters otherwise.
    """
    profiles = {}
    for rod in data["rods"]:
        profiles[rod["name"]] = (
            [tuple(stop) for stop in rod.get("radial_profile", [])],
            rod.get("radial_offset", 0.0),
        )

    def at(rod: str, t: float) -> float:
        stops, constant = profiles.get(rod, ([], 0.0))
        if not stops:
            return constant
        if t <= stops[0][0]:
            return stops[0][1]
        if t >= stops[-1][0]:
            return stops[-1][1]
        for (t0, v0), (t1, v1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                span = t1 - t0
                return v0 if span < 1e-9 else v0 + (t - t0) / span * (v1 - v0)
        return stops[-1][1]

    return at


def _basis(ex, ey, ez) -> list:
    return [[_p(c) for c in ex], [_p(c) for c in ey], [_p(c) for c in ez]]


def _p(x: float) -> float:
    return round(x, 9)


def placements(data: dict, parts: list) -> list:
    """Where every connector sits and which way round it goes.

    A part's geometry comes out of its generator in the generator's own frame.
    Putting it on the dome needs that frame expressed in dome coordinates, and
    the frames are not guesses -- each is read off the generator that draws
    the part:

    - ``fan_node_v2`` stacks its plates along local +Z and lays the arms out
      in local XY, the first at azimuth zero. So +Z is the outward radius and
      +X is the first arm of the fan, in the angular order ``weave.node_fan``
      already sorts them into.
    - ``crossing_clamp_v1`` puts the upper rod at ``+angle/2`` and ``z=+v/2``
      and the lower at ``-angle/2``, ``z=-v/2``. So +Z is outward again, and
      +X is the bisector, oriented so the rod on the outside is the one at the
      positive angle.
    - ``base_hub_v1`` draws the part in the frame it stands in: arm azimuths
      ARE their rises above horizontal, +X horizontal and -Y straight down.
      So +X runs along the base ring, +Y is world up and +Z is outward.

    The ten base points come in two mirror sets. Turning the planar part over
    about its own vertical axis is a rotation, not a reflection -- it maps a
    local azimuth to 180 minus itself, which is exactly the difference between
    the two sets -- so both sets are the same print and the basis says so by
    flipping +X and +Z together.

    Origins sit at the middle of the rods the part holds, which is where every
    one of these generators centres its stack.
    """
    from . import geometry

    bows = {b.name: b for b in geometry.build_bows()}
    nodes = {n["name"]: n for n in data["nodes"]}
    bases = {b["name"]: b for b in data["base_nodes"]}
    crossings_by_node: dict = {}
    for c in data["crossings"]:
        crossings_by_node.setdefault(c["node"], []).append(c)
    offset_at = _rod_offset_sampler(data)
    fan = weave.base_fan(data, removed=_released(data))

    if data["meta"].get("weave_mode") != "woven":
        # Not an error: the parts list is true of any model. Only where they
        # go is not, because which rod runs outside at a crossing is what
        # fixes a part's stack and neither flat nor layered answers it.
        return []

    out: list = []
    for part in parts:
        kind = part["kind"]
        if kind == "four_rod_fan":
            for name in part["nodes"]:
                out.append(_fan_placement(part, nodes[name], bows, offset_at))
        elif kind == "two_rod_clamp":
            for name in part["nodes"]:
                contact = crossings_by_node[name][0]
                out.append(_clamp_placement(part, contact, bows, offset_at))
        elif kind == "cut_termination":
            for end in part["terminations"]:
                contact = crossings_by_node[end["node"]][0]
                spot = _clamp_placement(part, contact, bows, offset_at)
                spot["terminating_rod"] = end["rod"]
                spot["approach"] = end["approach"]
                out.append(spot)
        elif kind == "base_hub":
            for name in part["nodes"]:
                out.append(_base_placement(part, bases[name], fan, bows))
        elif kind == "ground_stake":
            for name in part["nodes"]:
                out.append(_stake_placement(part, bases[name], fan))
        elif kind == "rod_splice":
            for joint in part["joints"]:
                out.append(_splice_placement(part, joint, bows, offset_at))
    return out


def _released(data: dict) -> dict:
    door = data.get("doorway")
    if not door or not door.get("cut"):
        return {}
    cuts = {r: [tuple(s) for s in v] for r, v in door["cut"]["spans"].items()}
    return doorway.feet_released(data, cuts)


def _line_gap_deg(a, b) -> float:
    """Angle between two RODS, which are lines: direction along them is free."""
    from . import vec

    c = abs(vec.dot(vec.unit(a), vec.unit(b)))
    return math.degrees(math.acos(min(1.0, c)))


def _orient(normal, want: list, candidates: list, what: str,
            levels: list | None = None, signs=(1.0, -1.0)) -> tuple:
    """The frame that puts a planar part's arms on the rods they hold.

    Every one of these parts is flat: its arms lie in local XY and its stack
    runs along local Z, which on the dome is the outward radius. So an
    orientation is two choices -- which way local +X points in the tangent
    plane, and whether the part is the right way up or turned over. Turning it
    over is a rotation, not a reflection, so the basis is
    ``(ex, s * (n x ex), s * n)`` and ``s = -1`` means turned over.

    Two things are checked, and the second is the one that matters.

    ``want`` pairs each arm's local azimuth with the rod LINE it has to land
    on. Lines have no direction, so this alone is weak: a part turned over
    lands on the same lines while holding the wrong rod on the outside.

    ``levels`` pairs each arm's local height in the stack with how far out the
    rod actually runs. That is what pins the part the right way up, and it is
    why a clamp whose cap belongs outside cannot be quietly flipped to make
    the angles work.
    """
    from . import vec

    best = None
    for ex in candidates:
        ex = vec.unit(ex)
        side = vec.unit(vec.cross(normal, ex))
        for s in signs:
            worst = 0.0
            for azimuth, rod_dir in want:
                a = math.radians(s * azimuth)
                placed = tuple(
                    math.cos(a) * ex[i] + math.sin(a) * side[i] for i in range(3)
                )
                worst = max(worst, _line_gap_deg(placed, rod_dir))
            for local_z, out_mm in levels or ():
                # A tenth of a millimetre: far under the clearance any of
                # these channels is drawn with, and far over the rounding.
                worst = max(worst, abs(s * local_z - out_mm) * 10.0)
            if best is None or worst < best[0]:
                ey = tuple(s * c for c in side)
                ez = tuple(s * c for c in normal)
                best = (worst, ex, ey, ez, s < 0)
    if best is None or best[0] > 1e-3:
        raise ValueError(
            f"no orientation puts {what} on its rods: the closest is "
            f"{best[0]:.6f} out, which is a part that does not fit"
        )
    return best[1], best[2], best[3], best[4]


def _fan_placement(part: dict, node: dict, bows: dict, offset_at) -> dict:
    from . import vec

    point = (node["x"], node["y"], node["z"])
    normal = vec.unit(point)
    arms = weave.node_fan_in_part_order(node, bows)
    azimuths = _azimuths(part["fan_gaps_deg"][:-1], 0.0)
    pitch = part["stack_height"] / (len(arms) - 1)
    mid = sum(
        offset_at(name, bows[name].t_of(point)) for _a, name, _f, _o in arms
    ) / len(arms)

    # ``node_fan_in_part_order`` already cut the fan where the part cuts it,
    # so arm k is arm k. Both directions are still tried: reading the fan the
    # other way round is the same part turned over, and the stack levels are
    # what decide whether it has to be.
    for direction in (1, -1):
        for _once in (0,):
            order = [
                arms[(direction * k) % len(arms)][1] for k in range(len(arms))
            ]
            want = [
                (azimuths[k], vec.unit(bows[r].tangent(bows[r].t_of(point))))
                for k, r in enumerate(order)
            ]
            levels = [
                ((k - (len(order) - 1) / 2.0) * pitch,
                 offset_at(r, bows[r].t_of(point)) - mid)
                for k, r in enumerate(order)
            ]
            try:
                ex, ey, ez, turned = _orient(
                    normal, want,
                    [_in_plane(bows[order[0]], point, normal)],
                    f"the fan at {node['name']}", levels=levels,
                )
            except ValueError:
                continue
            return {
                "part": part["id"],
                "kind": part["kind"],
                "at": node["name"],
                "origin_mm": [_p(c + mid * d) for c, d in zip(point, normal)],
                "basis": _basis(ex, ey, ez),
                "turned_over": turned,
                "arms": order,
            }
    raise ValueError(
        f"the fan at {node['name']} matches no arm order of {part['id']}"
    )


def _in_plane(bow, point, normal):
    """A rod's direction at a point, with the radial component taken out."""
    from . import vec

    d = vec.unit(bow.tangent(bow.t_of(point)))
    return vec.unit(tuple(c - vec.dot(d, normal) * m for c, m in zip(d, normal)))


def _azimuths(gaps: list, start: float) -> list:
    """``kit.azimuths_from_gaps``: n gaps lay out n+1 arms."""
    out = [start]
    for gap in gaps:
        out.append(out[-1] + gap)
    return out


def _clamp_placement(part: dict, contact: dict, bows: dict, offset_at) -> dict:
    """A two-rod clamp on its crossing, and which hand of it.

    The clamp is chiral and its two pieces are not interchangeable: the cap
    goes on the outside, over the rod that runs outside. That fixes the stack,
    and with the stack fixed the crossing either matches the part as drawn or
    matches its mirror image. Both occur on the dome -- see the ``hand`` count
    on the part -- so this reports which rather than flipping the part over to
    make the angles agree and putting the cap on the inside.
    """
    from . import vec

    point = (contact["x"], contact["y"], contact["z"])
    normal = vec.unit(point)
    above, below = contact["rod_above"], contact["rod_below"]
    t_above, t_below = bows[above].t_of(point), bows[below].t_of(point)

    da = _in_plane(bows[above], point, normal)
    db = _in_plane(bows[below], point, normal)
    if vec.dot(da, db) < 0.0:
        db = tuple(-c for c in db)
    angle = part["crossing_angle"]
    bisector = vec.unit(tuple(a + b for a, b in zip(da, db)))
    candidates = [bisector, tuple(-c for c in bisector)]

    mid = (offset_at(above, t_above) + offset_at(below, t_below)) / 2.0
    gap = offset_at(above, t_above) - offset_at(below, t_below)
    levels = [(+gap / 2.0, +gap / 2.0), (-gap / 2.0, -gap / 2.0)]

    for hand, (az_above, az_below) in (
        ("as-drawn", (+angle / 2.0, -angle / 2.0)),
        ("mirrored", (-angle / 2.0, +angle / 2.0)),
    ):
        try:
            ex, ey, ez, turned = _orient(
                normal, [(az_above, da), (az_below, db)], candidates,
                f"the clamp at {contact['node']}", levels=levels, signs=(1.0,),
            )
        except ValueError:
            continue
        return {
            "part": part["id"],
            "kind": part["kind"],
            "at": contact["node"],
            "origin_mm": [_p(c + mid * d) for c, d in zip(point, normal)],
            "basis": _basis(ex, ey, ez),
            "hand": hand,
            "rod_above": above,
            "rod_below": below,
        }
    raise ValueError(
        f"neither hand of {part['id']} fits the crossing at {contact['node']}"
    )


def _base_placement(part: dict, base: dict, fan: dict, bows: dict) -> dict:
    from . import vec

    here = fan["by_base"][base["name"]]
    point = (base["x"], base["y"], base["z"])
    normal = tuple(here["outward"])
    canonical = fan["by_base"][part["nodes"][0]]
    first = min(a["in_plane_deg"] for a in canonical["arms"])
    azimuths = _azimuths(part["fan_gaps_deg"], first)
    along = tuple(here["along"])

    # A base fan is open rather than cyclic, so the only question is which end
    # of it the generator's first arm sits at -- and the two mirror sets of
    # feet answer it the other way round. The bow ends all stop at the hub, so
    # there is no weave here to pin the stack: the part is turned over, which
    # is what the two mirror sets have always meant.
    for order in (
        [a["rod"] for a in here["arms"]],
        [a["rod"] for a in reversed(here["arms"])],
    ):
        want = [
            (azimuths[k], _foot_direction(bows[r], point))
            for k, r in enumerate(order)
        ]
        try:
            ex, ey, ez, turned = _orient(
                normal, want, [along, tuple(-c for c in along)],
                f"the base hub at {base['name']}",
            )
        except ValueError:
            continue
        return {
            "part": part["id"],
            "kind": part["kind"],
            "at": base["name"],
            "origin_mm": [base["x"], base["y"], base["z"]],
            "basis": _basis(ex, ey, ez),
            "turned_over": turned,
            "first_arm_rise_deg": round(first, 6),
            "arms": order,
        }
    raise ValueError(
        f"base point {base['name']} matches neither arm order of "
        f"{part['id']}; it is a third geometry and wants a part of its own"
    )


def _stake_placement(part: dict, base: dict, fan: dict) -> dict:
    """The driven angle at one foot, in the frame it is driven in.

    It is vertical whatever the hub above it is doing -- you hammer it, and the
    ground is down -- so local +Z points down the way it goes in. What the foot
    decides is the other two axes, and they matter: the hub carries its slot
    UNDER the bow bundle, offset towards the dome centre, so a consumer needs
    to know which way that is. Local +Y is outward, so the offset is negative
    along it, and the two mirror sets of feet get it on the correct side
    without anyone working out which set they are in.

    How far in, this does not say. That is a dimension of the hub, and the hub
    is `base_hub_v1`'s business; this is the ground's frame, not the part's.
    """
    from . import vec

    here = fan["by_base"][base["name"]]
    along = tuple(here["along"])
    outward = tuple(here["outward"])
    down = (0.0, 0.0, -1.0)
    return {
        "part": part["id"],
        "kind": part["kind"],
        "at": base["name"],
        "origin_mm": [base["x"], base["y"], base["z"]],
        "basis": _basis(along, outward, down),
        "driven": True,
    }


def _foot_direction(bow, point):
    """Which way a bow leaves a base point: away from the ground, always."""
    from . import vec

    t = bow.t_of(point) % 360.0
    if t > 180.0 + 1e-6:
        t -= 360.0
    d = vec.unit(bow.tangent(t))
    return d if d[2] >= 0.0 else tuple(-c for c in d)


def _splice_placement(part: dict, joint: dict, bows: dict, offset_at) -> dict:
    from . import vec

    bow = bows[joint["rod"]]
    t = joint["t_deg"]
    point = (joint["x"], joint["y"], joint["z"])
    n = vec.unit(point)
    ex = vec.unit(bow.tangent(t))
    ey = vec.unit(vec.cross(n, ex))
    ez = vec.unit(vec.cross(ex, ey))
    off = offset_at(joint["rod"], t)
    return {
        "part": part["id"],
        "kind": part["kind"],
        "at": f"{joint['rod']}@{t:.3f}",
        "origin_mm": [_p(c * (1.0 + off / vec.norm(point))) for c in point],
        "basis": _basis(ex, ey, ez),
        "rod": joint["rod"],
    }


def schedule(data: dict) -> dict:
    """Derive the connector schedule for a built model."""
    rod_diameter = data["meta"]["rod_diameter"]
    by_node = {}
    for c in data["crossings"]:
        by_node.setdefault(c["node"], []).append(c)

    node_rods = {n["name"]: n for n in data["nodes"]}

    parts: dict = {}
    unsupported: dict = {}

    for node_name, contacts in sorted(by_node.items()):
        node = node_rods[node_name]
        rod_count = node["rod_count"]

        if rod_count == TWO_ROD_CLAMP_CAPACITY:
            contact = contacts[0]
            angle = round(contact["angle_deg"], ANGLE_DP)
            key = _part_id("CL2", rod_diameter, angle)
            part = parts.setdefault(
                key,
                {
                    "id": key,
                    "kind": "two_rod_clamp",
                    "rod_diameter": rod_diameter,
                    "crossing_angle": angle,
                    "count": 0,
                    "nodes": [],
                    "tied": bool(contact["tied"]),
                    "crossing_types": [],
                    "generator": "crossing_clamp_v1",
                },
            )
            part["count"] += 1
            part["nodes"].append(node_name)
            if contact["type"] not in part["crossing_types"]:
                part["crossing_types"].append(contact["type"])
        else:
            key = f"N{rod_count}"
            entry = unsupported.setdefault(
                key,
                {
                    "kind": f"{rod_count}_rod_node",
                    "rod_count": rod_count,
                    "rod_diameter": rod_diameter,
                    "count": 0,
                    "nodes": [],
                    "pair_angles": [],
                    "crossing_types": [],
                },
            )
            entry["count"] += 1
            entry["nodes"].append(node_name)
            for c in contacts:
                angle = round(c["angle_deg"], ANGLE_DP)
                if angle not in entry["pair_angles"]:
                    entry["pair_angles"].append(angle)
                if c["type"] not in entry["crossing_types"]:
                    entry["crossing_types"].append(c["type"])

    for entry in unsupported.values():
        entry["pair_angles"].sort()
        entry["crossing_types"].sort()

    # Fold in what the fan analysis knows about the four-rod nodes. Their
    # geometry is settled -- one planar fan serves all ten -- so they belong in
    # `parts` as a specified part, not in a list of things we cannot describe.
    # What they still lack is a generator.
    fan = weave.analyse(data)
    four_rod = [e for e in unsupported.values() if e["rod_count"] == 4]
    for entry in four_rod:
        if fan["distinct_fans"] != 1:
            continue
        group = fan["groups"][0]
        key = _part_id("FAN4", rod_diameter, group["gaps_deg"][0])
        parts[key] = {
            "id": key,
            "kind": "four_rod_fan",
            "rod_diameter": rod_diameter,
            "count": entry["count"],
            "nodes": entry["nodes"],
            "tied": True,
            "crossing_types": entry["crossing_types"],
            "generator": "fan_node_v2",
            "fan_gaps_deg": group["gaps_deg"],
            "families_in_fan_order": group["families_in_fan_order"],
            "stack_order": fan["stack_order"],
            "stack_contacts_deg": fan["stack_contacts"],
            "stack_height": fan["stack_height"],
            "coplanar": fan["coplanarity_residual"] < 1e-9,
            "note": (
                "All four rods are coplanar -- a great circle's tangent lies in "
                "the sphere's tangent plane -- so this is a flat four-armed fan "
                "with the rods stacked along the radius. One part serves every "
                "one of these nodes. See docs/tied-node.md."
            ),
        }
    unsupported = {k: v for k, v in unsupported.items() if v["rod_count"] != 4 or fan["distinct_fans"] != 1}

    joint_parts = _joint_parts(data, rod_diameter)

    # Four-rod fans first: they are the nodes the reference actually lashes.
    part_list = sorted(
        parts.values(),
        key=lambda p: (p["kind"] != "four_rod_fan", p.get("crossing_angle", 0.0)),
    )
    unsupported_list = sorted(unsupported.values(), key=lambda e: -e["rod_count"])

    part_list = part_list + joint_parts
    covered = sum(p["count"] for p in part_list)
    uncovered = sum(e["count"] for e in unsupported_list)
    buildable = sum(p["count"] for p in part_list if p.get("generator"))

    spots = placements(data, part_list)
    woven = data["meta"].get("weave_mode") == "woven"

    # A part that comes in two hands is two prints, not one, and the count
    # that matters on a build day is how many of each. Only the placement
    # knows: it is the first thing that puts the part on a rod the right way
    # up, and handedness does not show until something does.
    for part in part_list:
        hands: dict = {}
        for spot in spots:
            if spot["part"] == part["id"] and "hand" in spot:
                hands[spot["hand"]] = hands.get(spot["hand"], 0) + 1
        if len(hands) > 1:
            part["hands"] = dict(sorted(hands.items()))
            part["note"] = part.get("note", "") + (
                "  It comes in two hands: "
                + ", ".join(f"{n} {h}" for h, n in sorted(hands.items()))
                + ". The cap goes outside, over the rod that runs outside, "
                "so the part cannot be turned over to make the angles agree "
                "-- the mirror image is a second print."
            )

    return {
        "schema": SCHEMA,
        "meta": {
            "variant": data["meta"]["variant"],
            "rod_diameter": rod_diameter,
            "units": "mm",
        },
        "parts": part_list,
        "placements": spots,
        "placements_note": (
            None
            if woven
            else (
                "no placements: this model was built "
                f"weave_mode={data['meta'].get('weave_mode')!r}, and where a "
                "part goes depends on which rod runs outside at each "
                "crossing. Build with weave_mode='woven'."
            )
        ),
        "unsupported": unsupported_list,
        "totals": {
            "crossing_points": len(data["nodes"]),
            "specified_nodes": covered,
            "uncovered_nodes": uncovered,
            "distinct_part_types": len(part_list),
            "parts_per_dome": covered,
            "generatable_now": buildable,
            "awaiting_a_generator": covered - buildable,
            "hardware": sum(
                p["count"] for p in part_list if p.get("state") == HARDWARE
            ),
            "undesigned": sum(
                p["count"] for p in part_list if p.get("state") == UNDESIGNED
            ),
            "undesigned_types": sorted(
                p["id"] for p in part_list if p.get("state") == UNDESIGNED
            ),
        },
    }


def format_schedule(sched: dict) -> str:
    """Human-readable schedule, for the CLI."""
    lines = []
    meta = sched["meta"]
    lines.append(f"--- {meta['variant']} connector schedule  (rod {meta['rod_diameter']:g} mm)")

    for p in sched["parts"]:
        tied = "lashed" if p["tied"] else "unlashed"
        state = p["generator"] or {
            HARDWARE: "hardware -- specify it",
            UNDESIGNED: "NOTHING EXISTS",
        }.get(p.get("state"), "NO GENERATOR YET")
        lines.append(f"    {p['id']:<20} {p['count']:>3} x   {tied}   [{state}]")
        if p["kind"] == "four_rod_fan":
            gaps = ", ".join(f"{g:.4f}" for g in p["fan_gaps_deg"])
            contacts = ", ".join(f"{c:.4f}" for c in p["stack_contacts_deg"])
            lines.append(
                f"      planar fan, gaps {gaps} deg; "
                f"families {'-'.join(p['families_in_fan_order'])}"
            )
            lines.append(
                f"      stack {'-'.join(str(i + 1) for i in p['stack_order'])}: "
                f"contacts {contacts} deg, height {p['stack_height']:g} mm"
            )
        elif p["kind"] == "two_rod_clamp":
            lines.append(
                f"      two rods at {p['crossing_angle']:.4f} deg, "
                f"classes {'/'.join(p['crossing_types'])}"
            )
            if p.get("hands"):
                lines.append(
                    "      two hands: "
                    + ", ".join(f"{n} {h}" for h, n in p["hands"].items())
                    + " -- the cap goes outside, so the mirror is a second print"
                )
        elif p["kind"] == "base_hub":
            gaps = ", ".join(f"{g:.4f}" for g in p["fan_gaps_deg"])
            rises = ", ".join(f"{r:.4f}" for r in p["rises_deg"])
            lines.append(
                f"      planar fan of {p['bow_ends']}, gaps {gaps} deg, "
                f"spread {p['fan_spread_deg']:.4f}; families "
                f"{'-'.join(p['families_in_fan_order'])}"
            )
            lines.append(
                f"      rods rise {rises} deg above horizontal; "
                + (f"two mirror sets of {p['count'] // 2}, so one part "
                   "turned over" if p["handed"] else "one orientation")
            )
            lines.append(f"      {p['members']} members;  {p['note']}")
        else:
            lines.append(f"      {p['members']} members;  {p['note']}")
    if not sched["parts"]:
        lines.append("  no parts")

    for e in sched["unsupported"]:
        lines.append(
            f"  NOT COVERED: {e['count']} x {e['rod_count']}-rod node "
            f"({'/'.join(e['crossing_types'])})"
        )
        angles = ", ".join(f"{a:.4f}" for a in e["pair_angles"])
        lines.append(f"    pairwise angles: {angles} deg")
        lines.append(f"    {e['reason']}")

    t = sched["totals"]
    lines.append(
        f"  totals: {t['distinct_part_types']} distinct part type(s), "
        f"{t['parts_per_dome']} parts per dome "
        f"({t['generatable_now']} generatable now, "
        f"{t['awaiting_a_generator']} awaiting a generator), "
        f"{t['uncovered_nodes']} node(s) unspecified"
    )
    lines.append(
        f"  of those: {t['generatable_now']} generated, "
        f"{t['hardware']} hardware to specify, "
        f"{t['undesigned']} with nothing at all "
        f"({', '.join(t['undesigned_types'])})"
    )
    return "\n".join(lines)
