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


def _part_id(kind: str, rod_diameter: float, angle: float) -> str:
    return f"{kind}-{rod_diameter:g}-{angle:.{ANGLE_DP}f}"


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

    # Four-rod fans first: they are the nodes the reference actually lashes.
    part_list = sorted(
        parts.values(),
        key=lambda p: (p["kind"] != "four_rod_fan", p.get("crossing_angle", 0.0)),
    )
    unsupported_list = sorted(unsupported.values(), key=lambda e: -e["rod_count"])

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
        },
    }


def format_schedule(sched: dict) -> str:
    """Human-readable schedule, for the CLI."""
    lines = []
    meta = sched["meta"]
    lines.append(f"--- {meta['variant']} connector schedule  (rod {meta['rod_diameter']:g} mm)")

    for p in sched["parts"]:
        tied = "lashed" if p["tied"] else "unlashed"
        state = p["generator"] or "NO GENERATOR YET"
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
        else:
            lines.append(
                f"      two rods at {p['crossing_angle']:.4f} deg, "
                f"classes {'/'.join(p['crossing_types'])}"
            )
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
    return "\n".join(lines)
