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

from . import SCHEMA_VERSION, weave

SCHEMA = f"star_dome_connectors/{SCHEMA_VERSION}"

# How many rods a two-piece crossing clamp of the V1 architecture can hold.
TWO_ROD_CLAMP_CAPACITY = 2

ANGLE_DP = 4

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
    import math

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

    fan = weave.base_fan(data)

    grouped: dict = {}
    for name, count in at_base.items():
        grouped.setdefault(count, []).append(name)
    for count, names in sorted(grouped.items(), reverse=True):
        on_ground = not skirt
        parts.append(
            {
                "id": f"BASE{count}-{rod_diameter:g}",
                "kind": "base_hub",
                "rod_diameter": rod_diameter,
                "count": len(names),
                "nodes": sorted(names),
                "tied": True,
                "members": count,
                # Three arms is the fan the generator draws; the skirted
                # eight-member hub on top of a post is a different problem and
                # still has nothing.
                "generator": "base_hub_v1" if count == 3 else None,
                "state": GENERATED if count == 3 else UNDESIGNED,
                "anchored_by_stake": on_ground,
                "coplanar": fan["coplanar"],
                "fan_gaps_deg": fan["gaps_deg"],
                "fan_spread_deg": fan["spread_deg"],
                "families_in_fan_order": [a["family"] for a in fan["arms"]],
                "rises_deg": [a["rise_deg"] for a in fan["arms"]],
                "handed": fan["mirror_pairs"],
                "note": (
                    "Three bow ends"
                    + (
                        ", the post head, two ring chords and the brace heads"
                        if count > 3
                        else ""
                    )
                    + ". They arrive at three different inclinations and have "
                    "to be held to each other"
                    + (
                        ", 1.35 m in the air on top of a post, where no stake "
                        "can reach."
                        if count > 3
                        else " and to the stake under them."
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
    if door and door.get("cut"):
        ends = sum(len(spans) for spans in door["cut"]["spans"].values())
        parts.append(
            {
                "id": f"TERM-{rod_diameter:g}",
                    "state": UNDESIGNED,
                "kind": "cut_termination",
                "rod_diameter": rod_diameter,
                "count": ends,
                "nodes": sorted(door["cut"]["spans"]),
                "tied": True,
                "members": 2,
                "generator": None,
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
        cut_spans = {}
        if door and door.get("cut"):
            cut_spans = door["cut"]["spans"]
        from . import rod as _rod

        total = 0
        for rod in data["rods"]:
            # The NOMINAL length: length_drawn is the layered drawing's, and
            # fifteen bows come out fifteen slightly different lengths there.
            length = meta["rod_length_nominal"]
            cut = cut_spans.get(rod["name"], ())
            for lo, hi in cut:
                length -= (hi - lo) / 180.0 * math.pi * meta["dome_radius"]
            count = max(1, math.ceil(length / section))
            if not cut:
                # A whole bow's joints land on the rod marks unless the count
                # dodges them; a cut one is no longer a full 180 degrees, so
                # the rule does not apply and the ceil stands.
                while not _rod.misses_the_marks(count):
                    count += 1
            total += count - 1
        if total:
            parts.append(
                {
                    "id": f"SPLICE-{rod_diameter:g}",
                    "state": GENERATED,
                    "kind": "rod_splice",
                    "rod_diameter": rod_diameter,
                    "count": total,
                    "nodes": [],
                    "tied": False,
                    # One tube per joint, so the count of PARTS to make and
                    # the count of joints are the same number.
                    "members": 1,
                    "sleeves": total,
                    "generator": "splice_v1",
                    "note": (
                        f"A bow is {meta['rod_length_nominal']:.0f} mm long and "
                        f"transports in {section:.0f} mm sections, so it is "
                        "spliced along its length. One steel sleeve per "
                        "joint, the rods butting inside it and a cross "
                        "fastener each side; the joint carries bending, "
                        "because the bow is bent everywhere, and it sits in "
                        "a gap between crossings. See docs/transport.md and "
                        "docs/splice.md."
                    ),
                }
            )

    return parts


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

    return {
        "schema": SCHEMA,
        "meta": {
            "variant": data["meta"]["variant"],
            "rod_diameter": rod_diameter,
            "units": "mm",
        },
        "parts": part_list,
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
        elif p["kind"] == "base_hub":
            gaps = ", ".join(f"{g:.4f}" for g in p["fan_gaps_deg"])
            rises = ", ".join(f"{r:.4f}" for r in p["rises_deg"])
            lines.append(
                f"      planar fan of 3, gaps {gaps} deg, spread "
                f"{p['fan_spread_deg']:.4f}; families "
                f"{'-'.join(p['families_in_fan_order'])}"
            )
            lines.append(
                f"      rods rise {rises} deg above horizontal; "
                + ("two mirror sets of five, so one part turned over"
                   if p["handed"] else "one orientation")
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
