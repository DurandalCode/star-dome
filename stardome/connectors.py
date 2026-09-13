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

# How many cut lengths one dome is allowed. See `_section_kit` and decision
# 0024.
#
# Two, and it is a logistics number rather than a geometric one: the sections
# are a kit somebody packs, carries and hands out, and lengths that differ by
# 80 mm are lengths that get confused. The solver takes one where one will do.
#
# This is a policy statement, not a dial. Raising it would need `_section_kit`
# rewritten -- it solves a 2x2 system, and three lengths is a different
# problem -- so it is here to be asserted against and quoted, not turned up.
SECTION_LENGTH_KINDS = 2

# How many sections past the minimum a stretch may be cut into while the kit
# is being searched for. A bow that needs a third piece to clear a crossing
# should get one; a bow that needs a fourth is telling us the sleeve and the
# transport length disagree, and that should be an error, not a longer search.
_COUNT_SLACK = 2

# What counts as the same length, in mm. Sections are metres of rod cut with a
# saw; a micron of arithmetic drift is not a different part.
_SECTION_TOL = 0.5

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


# --------------------------------------------------------------------------
# the fastener schedule
# --------------------------------------------------------------------------
# How many fasteners a part takes, and -- the half nobody had written down --
# **where it is worked**. Both are properties of the drawn part, and the part
# is drawn in FreeCAD, so this is the same kind of entry as
# ``SPLICE_SLEEVE_DIAMETERS`` above: the generator owns the real number and if
# a bolt pattern moves, this moves with it.
#
# FIELD and SHOP are not a tidy-up. Every generator already states its field
# sequence, and they do not agree about the bolt:
#
#   base_hub_v1   "the stack is assembled once, on the ground or at home, and
#                  the bow ends go in afterwards" -- its bolts are done up
#                  before the dome leaves the workshop and are never touched
#                  again. What happens at the dome is a pin per arm.
#   fan_node_v2   "open the stack -> lay rod 1 -> ... -> tighten two bolts" --
#                  its bolts are undone and done up at head height.
#   crossing_clamp_v1, term_clamp_v1
#                 the cap comes off to admit the rods, so both bolts and both
#                 nuts are loose objects in somebody's hand, up a ladder.
#
# Only the FIELD row costs assembly time, and rule 1 of this project is that
# assembly time is a requirement of the first class. Counting the two together
# hides the number that matters.
FIELD = "field"              # undone or done up while the dome goes up
SHOP = "shop"                # done up once, at home, and never touched again

BOLT = "bolt"                # a bolt, a nut and a tool at each end
PIN = "pin"                  # a cross pin: pushed in, not turned

# The two ways a two-piece clamp can be closed, and they are a choice made
# per dome rather than per part. `bolt` is the V1 joint. `hinge` hangs the
# cap to the bottom half on one side, which turns one of the two bolts into a
# pin that is fitted once and never touched again, and leaves the other
# standing in an open-ended slot so the cap comes off it sideways. See
# docs/quick-release.md and connectors/closure.py.
BOLTED = "bolt"
HINGED = "hinge"
CLOSURES = (BOLTED, HINGED)

# Fasteners per ONE of each part, by kind and by closure. A callable takes the
# part and returns the count, for the parts whose pattern follows their
# members. A kind with no entry for a closure keeps its bolted one: a splice
# has no bolts to save and a base hub's are already done up at home.
_FASTENERS = {
    "two_rod_clamp":   [(BOLT, 2, FIELD)],
    "cut_termination": [(BOLT, 2, FIELD)],
    "four_rod_fan":    [(BOLT, 2, FIELD)],
    # Two bolts through the plate stack, done up at home; then one cross pin
    # per arm, because a slide-fit channel locates the rod and holds it
    # against nothing.
    "base_hub":        [(BOLT, 2, SHOP),
                        (PIN, lambda part: part.get("bow_ends", 0), FIELD)],
    # Two pinching the post, and one per member end: two ring chords and two
    # braces, each on its own bolt through a lug.
    "skirt_collar":    [(BOLT, 2, FIELD),
                        (BOLT, lambda part: 2 * part.get("ends_per_post", 0),
                         FIELD)],
    # A sleeve over a butt joint. Decision: V2 dropped the bolts entirely.
    "rod_splice":      [],
    "ground_stake":    [],
    "header_clamp":    [],   # nothing is drawn yet; see milestone 5
}

_HINGED = {
    "two_rod_clamp":   [(BOLT, 1, FIELD), (PIN, 1, SHOP)],
    "cut_termination": [(BOLT, 1, FIELD), (PIN, 1, SHOP)],
}

BOLT_SIZES = (3, 4, 5, 6, 8)


def fastener_for(rod_diameter: float) -> str:
    """Which metric bolt a rod of this size gets: half it, snapped.

    Decision 0013. The table itself lives in ``connectors/kit.py``, which only
    imports inside FreeCAD; the *rule* is small enough to state here so that
    anything counting fasteners does not have to guess at it.
    """
    want = rod_diameter / 2.0
    size = min(BOLT_SIZES, key=lambda m: (abs(m - want), m))
    return f"M{size}"


def _fasteners_for(part: dict, closure: str = BOLTED) -> list:
    """The fastener rows of one part, counts resolved against the part."""
    table = _FASTENERS
    if closure == HINGED and part["kind"] in _HINGED:
        table = _HINGED
    rows = []
    for kind, count, when in table.get(part["kind"], []):
        if callable(count):
            count = count(part)
        if count:
            rows.append({"type": kind, "count": int(count), "worked": when})
    return rows


def fastener_tally(parts: list, rod_diameter: float,
                   closure: str = BOLTED) -> dict:
    """Every fastener in the dome, split by where it is worked.

    The split is the point. A dome's bolts are not one number: some are done
    up in a workshop with a bench and a cup of tea, and some are done up at
    head height in the wind, and only the second kind is an assembly cost.
    """
    out = {
        "closure": closure,
        "size": fastener_for(rod_diameter),
        "field": {BOLT: 0, PIN: 0},
        "shop": {BOLT: 0, PIN: 0},
        "by_part": [],
    }
    for part in parts:
        rows = _fasteners_for(part, closure)
        if not rows:
            continue
        total = 0
        for row in rows:
            n = row["count"] * part["count"]
            out[row["worked"]][row["type"]] += n
            total += n
        out["by_part"].append(
            {
                "id": part["id"],
                "count": part["count"],
                "per_part": sum(r["count"] for r in rows),
                "total": total,
                "rows": rows,
            }
        )
    out["field_total"] = sum(out["field"].values())
    out["shop_total"] = sum(out["shop"].values())
    out["total"] = out["field_total"] + out["shop_total"]
    return out


def fastener_closures(parts: list, rod_diameter: float) -> dict:
    """Both closures, counted the same way, so the choice has a number.

    Rule 1 of this project is that fast assembly is a first-class
    requirement, and until now nothing in it counted the work. This does: the
    same schedule, closed two different ways, and the difference is bolts
    nobody has to turn at head height.
    """
    return {name: fastener_tally(parts, rod_diameter, name)
            for name in CLOSURES}


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
    nominal = meta["rod_diameter"]
    skirt = data.get("skirt")
    door = data.get("doorway")
    parts = []

    # --- base points ---------------------------------------------------------
    #
    # Three rod ends meet here, and that is all that meets here -- with a skirt
    # as well as without one.
    #
    # The hub already carries a pad and a bolt for a driven steel angle. A
    # skirt post is that same angle, longer: driven at the bottom, bolted to
    # the pad at the top, one member doing both jobs. So the post is not an
    # extra member at this point any more than the stake is, and the skirt's
    # own members -- two ring chords and two brace heads -- land on a collar
    # clamped to the post below the hub rather than on the hub. See COLLAR
    # below and docs/skirt.md.
    at_base = {b["name"]: 3 for b in data["base_nodes"]}

    # A doorway cut takes a bow end off the two feet the door stands between,
    # so those two gather two arms and not three. Eight identical hubs and two
    # different ones is the truth; ten identical hubs is a part that does not
    # fit where it matters most.
    # Every door's cuts, not the first one's: a dome with two doors releases
    # bow ends at four feet, and a schedule that saw one door would ask for
    # two hubs that do not fit.
    cuts = doorway.removed_spans(data)
    released = doorway.feet_released(data, cuts) if cuts else {}
    for name, rods in released.items():
        at_base[name] -= len(rods)

    fan = weave.base_fan(data, removed=released)

    grouped: dict = {}
    for name, count in at_base.items():
        grouped.setdefault(count, []).append(name)
    for count, names in sorted(grouped.items(), reverse=True):
        # Whether the angle on the hub's pad is driven straight into the
        # ground or is a post with the ground a skirt-height further down
        # changes its length and nothing else about this part. Either way the
        # hub is held down by the thing it is bolted to.
        on_ground = True
        # Every point in a group has the same member count, and the fan is
        # the same shape at all of them up to the mirror, so one of them
        # describes the part. Take the first by name so the answer does not
        # depend on dict order.
        here = fan["by_base"][sorted(names)[0]]
        bows_here = len(here["arms"])
        # The generator draws a flat fan of bow ends, however many, plus the
        # pad the angle bolts to. Nothing else arrives here.
        drawable = count == bows_here
        parts.append(
            {
                "id": f"BASE{count}-{rod_diameter:g}",
                "kind": "base_hub",
                "rod_diameter": rod_diameter,
                "rod_nominal_diameter": nominal,
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
                    + ". They arrive at "
                    + ("two" if bows_here == 2 else "three")
                    + " different inclinations and have to be held to each "
                    "other and to the angle bolted to the pad under them"
                    + (
                        " -- which on a skirted dome is the post, not a short "
                        "stake, and reaches the ground a skirt-height below."
                        if skirt
                        else "."
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

    # The angle on the hub's pad. On a bare dome it is a stake and nothing
    # else; under a skirt the same member keeps going down to the ground and
    # is the post as well. One item on the list either way, and the only thing
    # that changes is how much of it stands above the soil.
    standing = skirt["height"] if skirt else 0.0
    parts.append(
        {
            "id": "STAKE-BASE",
            "kind": "ground_stake",
            "rod_diameter": rod_diameter,
            "rod_nominal_diameter": nominal,
            "count": len(data["base_nodes"]),
            "nodes": sorted(b["name"] for b in data["base_nodes"]),
            "tied": False,
            "members": 1,
            "generator": None,
            "state": HARDWARE,
            "standing_mm": round(standing, 3),
            "is_the_post": bool(skirt),
            "note": (
                "A driven steel angle at each base point. This is what "
                "resists the dome spreading at its feet -- through soil, "
                "the way a tent peg does -- and it is a size and a length "
                "to specify rather than a shape to design. It does not "
                "gather the three bow ends; that is BASE3."
                + (
                    f"  Under a skirt it is also the post: the same angle, "
                    f"{standing:.0f} mm of it standing, carrying the collars "
                    "and running on into the ground. A post and a stake at the "
                    "same point would be two members competing for one place."
                    if skirt
                    else ""
                )
                + "  How far it is driven is the ground's answer, not this "
                "project's."
            ),
        }
    )

    # --- the skirt's own joints ---------------------------------------------
    #
    # Everything the skirt adds at a post -- two ring chords and two brace
    # ends -- lands on a collar clamped to the post, at both ends of it. The
    # two are the same shape: the chords leave level on both, and the braces
    # leave at the same angle, downward at the head and upward at the foot.
    # Turn the part over about the outward radius and one serves the other.
    if skirt:
        posts = skirt["posts"]
        count_posts = len(posts)
        # The chord to the next post round a regular polygon, measured from
        # the outward radius. Derived from the post count, not typed in.
        chord_azimuth = 90.0 + 180.0 / count_posts
        rise = skirt["brace_angle_deg"]

        # A doorway bay has neither ring chord nor brace, so the two posts
        # beside it carry a collar with one side unused -- at both ends.
        beside_a_door = set()
        for bay in skirt.get("open_bays") or []:
            beside_a_door.add(posts[bay % count_posts]["name"])
            beside_a_door.add(posts[(bay + 1) % count_posts]["name"])

        parts.append(
            {
                "id": f"COLLAR-{rod_diameter:g}",
                "kind": "skirt_collar",
                "rod_diameter": rod_diameter,
                "rod_nominal_diameter": nominal,
                "count": 2 * count_posts,
                "nodes": sorted(post["name"] for post in posts),
                "tied": True,
                "members": 5,
                "generator": "skirt_collar_v1",
                "state": GENERATED,
                "ends_per_post": 2,
                "chord_azimuths_deg": [
                    round(chord_azimuth, 6),
                    round(360.0 - chord_azimuth, 6),
                ],
                "brace_rise_deg": round(rise, 6),
                "chord_length_mm": round(skirt["top_ring"][0]["length"], 3),
                "brace_length_mm": round(skirt["braces"][0]["length"], 3),
                "post_length_mm": round(skirt["height"], 3),
                "one_side_unused": sorted(beside_a_door),
                "note": (
                    f"Two ring chords and two brace ends, at {chord_azimuth:.4f} "
                    f"deg either side of the outward radius -- the chords level "
                    f"and the braces at {rise:.4f} deg, down at the head and up "
                    f"at the foot. One geometry serves both ends: turned over "
                    f"about the radius, a head collar is a foot collar. "
                    + (
                        f"{len(beside_a_door) * 2} of them stand beside a "
                        "doorway and carry nothing on the door side."
                        if beside_a_door
                        else ""
                    )
                    + " What the collar does NOT do is decide what the ring "
                    "chord is made of. A GFRP rod of the dome's own diameter "
                    "buckles at well under a hundred newtons over this span, "
                    "so the ring is a section to specify -- milestone 8. See "
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
                "rod_nominal_diameter": nominal,
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
                "rod_nominal_diameter": nominal,
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
            kit = section_kit(data, section, sleeve)
            clear = min(j["clear_of_crossing_mm"] for j in joints)
            moved = max(abs(j["moved_mm"]) for j in joints)
            longest = max(kit)
            parts.append(
                {
                    "id": f"SPLICE-{rod_diameter:g}",
                    "state": GENERATED,
                    "kind": "rod_splice",
                    "rod_diameter": rod_diameter,
                "rod_nominal_diameter": nominal,
                    "count": len(joints),
                    "nodes": [],
                    "tied": False,
                    "members": 2,
                    "bend_radius": meta["dome_radius"],
                    "sleeve_length": round(sleeve, 3),
                    "section_length": section,
                    "section_kit_mm": [round(x, 1) for x in kit],
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
                        "the bow curve through it. The whole dome is cut "
                        f"into {len(kit)} "
                        f"length{'s' if len(kit) > 1 else ''} -- "
                        + ", ".join(f"{x:.0f} mm" for x in kit)
                        + " -- because a bag of sections is sorted by hand; "
                        "which lengths go where is the bow's own business. "
                        f"Joints sit up to {moved:.0f} mm off the even "
                        f"division, tightest crossing clearance {clear:.0f} "
                        "mm."
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


def _clears(at: float, blockers: list, keep_out: float) -> bool:
    """Is a joint at ``at`` far enough from every crossing on this stretch?"""
    return all(abs(at - b) >= keep_out - 1e-9 for b in blockers)


def _orders(length: float, blockers: list, keep_out: float, kit: tuple,
            count: int) -> list:
    """Every way to lay ``count`` pieces from ``kit`` end to end along a bow.

    The pieces come from the kit, so this is not a division of the bow: it is
    a choice of ORDER. A stretch of 12566 mm built from four 2149 mm sections
    and two 1986 mm ones can put the short pair anywhere, and the orders
    differ only in where the joints land -- which is the whole question, since
    a joint on a crossing is not a joint.
    """
    out = []
    ladder = sorted(set(kit), reverse=True)
    shortest, longest = ladder[-1], ladder[0]

    def walk(at: float, left: int, run: list):
        if left == 0:
            if abs(length - at) <= _SECTION_TOL:
                out.append(tuple(run))
            return
        if not (left * shortest - _SECTION_TOL
                <= length - at
                <= left * longest + _SECTION_TOL):
            return
        for piece in ladder:
            end = at + piece
            if left > 1 and not _clears(end, blockers, keep_out):
                continue
            run.append(piece)
            walk(end, left - 1, run)
            run.pop()

    walk(0.0, count, [])
    return out


def _evenness(order: tuple, length: float) -> float:
    """How far this order's joints sit from the even division, squared.

    The tie-break between orders that are all legal. Joints near the even
    division are the ones a tape measure finds easiest and the ones with the
    most room either side, so of two legal orders the more even one wins.
    """
    n = len(order)
    at = 0.0
    cost = 0.0
    for i, piece in enumerate(order[:-1]):
        at += piece
        cost += (at - length * (i + 1) / n) ** 2
    return cost


def _fit(length: float, blockers: list, keep_out: float, kit: tuple,
         count: int):
    """The best legal order of ``count`` kit pieces along a stretch, or None."""
    orders = _orders(length, blockers, keep_out, kit, count)
    if not orders:
        return None
    return min(orders, key=lambda o: (_evenness(o, length),
                                      tuple(-x for x in o)))


def _schedule_kit(kinds: list, section: float, keep_out: float, kit: tuple):
    """Lay every stretch out from ``kit``, at the fewest pieces each.

    Returns ``(orders, pieces)`` -- one order per kind and the total number of
    sections the dome is then cut into -- or ``None`` if any kind cannot be
    built from this kit at all.
    """
    orders = []
    pieces = 0
    for length, blockers, rods in kinds:
        floor = max(1, math.ceil(length / section - 1e-9))
        best = None
        for count in range(floor, floor + _COUNT_SLACK + 1):
            best = _fit(length, blockers, keep_out, kit, count)
            if best:
                break
        if not best:
            return None
        orders.append(best)
        pieces += rods * len(best)
    return orders, pieces


def _splits(length: float, section: float) -> list:
    """``(count, long_pieces)`` ways a stretch could be made of two lengths.

    One split is one linear equation in the two kit lengths: ``length = a*A +
    (n - a)*B``. Two splits are two equations, and two equations fix the kit.
    """
    floor = max(1, math.ceil(length / section - 1e-9))
    return [
        (n, a)
        for n in range(floor, floor + _COUNT_SLACK + 1)
        for a in range(n + 1)
    ]


def _candidate_kits(kinds: list, section: float, keep_out: float) -> list:
    """Every two-length kit worth trying, deduplicated.

    A kit is not searched for by moving joints around: it is SOLVED for. Pick
    how many pieces of each length two stretches are made of, and the two
    lengths follow from the two sums -- exactly, by 2x2 elimination. Every kit
    that could possibly close a bow is reachable this way, and almost nothing
    else is.
    """
    lengths = sorted({length for length, _, _ in kinds})
    equations = [
        (length, n, a)
        for length in lengths
        for n, a in _splits(length, section)
    ]

    seen = {}
    for i, (l1, n1, a1) in enumerate(equations):
        for l2, n2, a2 in equations[i + 1:]:
            det = a1 * (n2 - a2) - a2 * (n1 - a1)
            if det == 0:
                continue
            long_mm = (l1 * (n2 - a2) - l2 * (n1 - a1)) / det
            short_mm = (a1 * l2 - a2 * l1) / det
            if long_mm < short_mm:
                long_mm, short_mm = short_mm, long_mm
            if not keep_out <= short_mm <= long_mm <= section + _SECTION_TOL:
                continue
            key = (round(long_mm, 3), round(short_mm, 3))
            seen.setdefault(key, (long_mm, short_mm))
    return list(seen.values())


def _section_kit(kinds: list, section: float, keep_out: float):
    """The one or two lengths this whole dome is cut into, and how they lie.

    **A dome is built from at most two cut lengths.** Not because the geometry
    wants it -- dividing each bow evenly and nudging the joints that land on a
    crossing is geometrically freer, and it is what this used to do -- but
    because the sections are a kit that a person packs, carries, counts and
    hands out. Four lengths within 180 mm of each other, which is what even
    division and a nudge produced on S and L, is four lengths to tell apart
    in a bag on wet grass, and getting it wrong is a bow that will not close.
    So the constraint is logistical and it is hard: two, dome-wide, including
    the two bows a doorway shortens.

    The search is exact rather than heuristic:

    1. **One length, if one will do.** A single length has to divide every
       distinct stretch a whole number of times, so there is very little of it
       to try: the divisors of the longest stretch that are short enough to
       travel. A dome with an uncut door would take this branch.
    2. **Otherwise two, solved rather than sought.** Choosing how many pieces
       of each length two stretches are made of gives two linear equations in
       the two lengths, which fix them exactly -- see `_candidate_kits`. Each
       candidate kit is then laid out against every stretch, joints checked
       against every crossing.

    Of the kits that work, the one that cuts the dome into the fewest sections
    wins; ties go to the kit whose two lengths are closest together, because
    two lengths 160 mm apart are harder to confuse than two 700 mm apart only
    in the sense that they are more nearly one length.
    """
    lengths = sorted({length for length, _, _ in kinds})
    longest = lengths[-1]

    floor = max(1, math.ceil(longest / section - 1e-9))
    for count in range(floor, floor + _COUNT_SLACK + 1):
        one = (longest / count,)
        fitted = _schedule_kit(kinds, section, keep_out, one)
        if fitted:
            return one, fitted[0]

    best = None
    for kit in _candidate_kits(kinds, section, keep_out):
        fitted = _schedule_kit(kinds, section, keep_out, kit)
        if not fitted:
            continue
        orders, pieces = fitted
        rank = (pieces, round(kit[0] - kit[1], 6), -round(kit[1], 6))
        if best is None or rank < best[0]:
            best = (rank, kit, orders)
    if best:
        return best[1], best[2]

    raise ValueError(
        f"no kit of {SECTION_LENGTH_KINDS} cut lengths of at most "
        f"{section:.0f} mm builds every bow of this dome with each joint "
        f"{keep_out:.0f} mm clear of a crossing; the transport length and "
        "the sleeve length disagree"
    )


def _stretches(data: dict, mm_per_deg: float):
    """Every stretch of every bow, and the distinct kinds among them.

    A stretch is what survives of one bow after a doorway cut -- usually the
    whole bow. Two things decide how it is cut and nothing else does: how long
    it is, and where the crossings along it are. So stretches are grouped by
    that pair, and a dome has only a handful of groups -- the two bow families,
    plus whatever the doorway leaves of the two bows it shortens.

    Arc length from the start of the stretch is the frame both constraints are
    naturally stated in, so everything here is in millimetres along the bow.
    """
    cuts = doorway.removed_spans(data)
    crossing_ts: dict = {}
    for c in data["crossings"]:
        for side in ("a", "b"):
            crossing_ts.setdefault(c[f"rod_{side}"], []).append(c[f"t_{side}_deg"])

    spans = []
    kinds: dict = {}
    for rod in data["rods"]:
        ts = sorted(set(crossing_ts.get(rod["name"], [])))
        for lo, hi in _present_spans(rod, cuts):
            length = (hi - lo) * mm_per_deg
            blockers = tuple((t - lo) * mm_per_deg for t in ts if lo <= t <= hi)
            key = (round(length, 3), tuple(round(b, 3) for b in blockers))
            if key not in kinds:
                kinds[key] = [length, blockers, 0]
            kinds[key][2] += 1
            spans.append((rod["name"], lo, length, blockers, key))
    return spans, kinds


def section_kit(data: dict, section: float, sleeve: float) -> tuple:
    """The cut lengths this dome is built from, longest first.

    One or two numbers, and they are the cut list: what a saw is set to, and
    what the sections in the bag get sorted into. See `_section_kit`.
    """
    mm_per_deg = math.pi * data["meta"]["dome_radius"] / 180.0
    _, kinds = _stretches(data, mm_per_deg)
    kit, _ = _section_kit(
        [tuple(k) for k in kinds.values()], section, sleeve
    )
    return tuple(kit)


def splice_joints(data: dict, section: float, sleeve: float) -> list:
    """Where each bow is joined along its length, and how clear of a crossing.

    Three things decide this, and they pull against each other.

    **No section may be longer than the transport length.** That is what puts
    the dome in a car, and it is the reason splices exist at all. It fixes the
    fewest sections a bow can be cut into: ``ceil(length / section)``.

    **No joint may sit on a crossing.** A sleeve there cannot be clamped and
    cannot be woven past, and the crossing already carries a part of its own.
    So the sleeve clears the crossing by its own length, which leaves room for
    that part as well as for itself.

    **The whole dome is cut into at most two lengths.** A bag of sections is
    sorted by hand, so a dome with four lengths 80 mm apart is a dome that
    gets assembled wrong. See `_section_kit`, which owns this one.

    The first two used to be met bow by bow: divide evenly, then nudge each
    joint that lands on a crossing the shortest distance that clears. That is
    geometrically freer and logistically worse -- on S and L it produced four
    cut lengths within 180 mm of each other. The kit is now solved once for
    the whole dome and every stretch is laid out from it.
    """
    from . import geometry

    radius = data["meta"]["dome_radius"]
    mm_per_deg = math.pi * radius / 180.0
    spans, kinds = _stretches(data, mm_per_deg)
    _, orders = _section_kit(
        [tuple(k) for k in kinds.values()], section, sleeve
    )
    order_of = dict(zip(kinds, orders))

    bows = {b.name: b for b in geometry.build_bows()}
    out = []
    for name, lo, length, blockers, key in spans:
        bow = bows[name]
        order = order_of[key]
        at = 0.0
        for i, piece in enumerate(order[:-1]):
            at += piece
            t = lo + at / mm_per_deg
            clear = min((abs(at - b) for b in blockers), default=float("inf"))
            even = length * (i + 1) / len(order)
            x, y, z = bow.point(t, radius)
            out.append(
                {
                    "rod": name,
                    "t_deg": round(t, 6),
                    "s_mm": round(at, 3),
                    "clear_of_crossing_mm": round(clear, 3),
                    "moved_mm": round(at - even, 3),
                    "sections_mm": [round(order[i], 1), round(order[i + 1], 1)],
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
        elif kind == "skirt_collar":
            out.extend(_collar_placements(data, part))
        elif kind == "ground_stake":
            for name in part["nodes"]:
                out.append(_stake_placement(part, bases[name], fan))
        elif kind == "rod_splice":
            for joint in part["joints"]:
                out.append(_splice_placement(part, joint, bows, offset_at))
    return out


def _released(data: dict) -> dict:
    """Bow ends every doorway took off a foot, not just the first door's."""
    cuts = doorway.removed_spans(data)
    return doorway.feet_released(data, cuts) if cuts else {}


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
    decides is the other two axes, and they matter: the hub meets the angle on
    a pad offset from the bow bundle along the stack axis, so a consumer needs
    to know which way that axis runs. Local +Y is outward.

    Which SIDE the angle ends up on is not settled here, and saying that it was
    is the one thing this frame used to get wrong. The pad is on the outer face
    of the hub's bottom plate, and five of the ten feet take that hub turned
    over -- that is what the two mirror sets have always meant -- so five
    angles stand inboard of the bundle and five outboard. It was true of the
    through slot before the pad and nobody had noticed. See decision 0025.

    How far off, this does not say either. That is a dimension of the hub, and
    the hub is `base_hub_v1`'s business; this is the ground's frame.
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


def _collar_placements(data: dict, part: dict) -> list:
    """Both collars on every post: one at the head, one at the foot.

    ``skirt_collar_v1`` bores along local +Z and puts its lug arms at the
    chord azimuth either side of local +X, with the brace arms below them. So
    +X is the outward radius and +Z is up at a head -- and DOWN at a foot,
    which is the whole point of the part: turned over about the outward
    radius, a head collar is a foot collar.
    """
    import math

    from . import vec

    skirt = data.get("skirt") or {}
    out = []
    for post in skirt.get("posts", []):
        azimuth = math.atan2(post["y"], post["x"])
        outward = (math.cos(azimuth), math.sin(azimuth), 0.0)
        for where, z, up in (
            ("head", post["z_top"], (0.0, 0.0, 1.0)),
            ("foot", post["z_bottom"], (0.0, 0.0, -1.0)),
        ):
            # Right-handed, with +X outward and +Z along the post's axis as
            # this end sees it.
            ey = vec.cross(up, outward)
            out.append(
                {
                    "part": part["id"],
                    "kind": part["kind"],
                    "at": f"{post['name']}_{where}",
                    "origin_mm": [post["x"], post["y"], _p(z)],
                    "basis": _basis(outward, ey, up),
                    "end": where,
                    "turned_over": where == "foot",
                }
            )
    return out


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
    meta = data["meta"]
    # The part is named and sized by the rod it HOLDS, so that is the caliper
    # figure: a channel cut to a composite rod's nominal 10 mm does not admit
    # the 11-and-a-bit its winding actually measures. Strength still follows
    # the nominal, and the generators are handed both.
    rod_diameter = meta.get("rod_fit_diameter", meta["rod_diameter"])
    nominal = meta["rod_diameter"]
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
                "rod_nominal_diameter": nominal,
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
                "rod_nominal_diameter": nominal,
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

    # What each part is held together by, and where that work is done. See
    # the fastener schedule at the top of this module.
    for part in part_list:
        rows = _fasteners_for(part)
        if rows:
            part["fasteners"] = rows

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
        "fasteners": fastener_tally(part_list, nominal),
        "closures": fastener_closures(part_list, nominal),
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
