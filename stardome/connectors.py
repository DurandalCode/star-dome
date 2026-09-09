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

from . import SCHEMA_VERSION

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
                    "reason": (
                        f"{rod_count} rods meet at one point; the V1 two-piece clamp "
                        f"holds {TWO_ROD_CLAMP_CAPACITY}. Needs a different "
                        f"architecture, and the radial stacking order is a build "
                        f"decision that has not been made (see model meta, "
                        f"above_convention)."
                    ),
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

    part_list = sorted(parts.values(), key=lambda p: p["crossing_angle"])
    unsupported_list = sorted(unsupported.values(), key=lambda e: -e["rod_count"])

    covered = sum(p["count"] for p in part_list)
    uncovered = sum(e["count"] for e in unsupported_list)

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
            "covered_nodes": covered,
            "uncovered_nodes": uncovered,
            "distinct_part_types": len(part_list),
            "parts_per_dome": covered,
        },
    }


def format_schedule(sched: dict) -> str:
    """Human-readable schedule, for the CLI."""
    lines = []
    meta = sched["meta"]
    lines.append(f"--- {meta['variant']} connector schedule  (rod {meta['rod_diameter']:g} mm)")

    if sched["parts"]:
        lines.append("  parts that can be generated:")
        for p in sched["parts"]:
            tied = "lashed" if p["tied"] else "unlashed"
            lines.append(
                f"    {p['id']:<16} {p['count']:>3} x  "
                f"{p['crossing_angle']:.4f} deg  ({tied}, "
                f"classes {'/'.join(p['crossing_types'])})"
            )
    else:
        lines.append("  no generatable parts")

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
        f"{t['parts_per_dome']} parts per dome, "
        f"{t['uncovered_nodes']} node(s) uncovered"
    )
    return "\n".join(lines)
