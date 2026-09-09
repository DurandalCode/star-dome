"""The four-rod node: its plane, its fan, and the radial stacking order.

The ten lashed nodes are where the Star Dome actually needs a connector, and
for a long time they looked like the hard case: four rods meeting at a point
with six pairwise angles between them. They are not hard, for one reason.

**The four tangents are coplanar.** Every bow is a great circle, and a great
circle's tangent at a point lies in the sphere's tangent plane there. So all
four rods leave the node in one plane, perpendicular to the radius. The node
is a flat four-armed fan, and the rods stack along the radius, across that
plane.

Two consequences follow, and both are computed here rather than asserted:

- All ten lashed nodes are the *same* fan. The five high nodes read G-U-U-G
  around the fan and the five low ones read L-G-G-L, but as geometry the two
  are the same cyclic sequence of gaps. One part serves all ten.
- Only rods adjacent in the stack touch, so choosing the stacking order is
  choosing which three of the fan's angles become rod-on-rod contacts.

The stacking order is a build decision, not a geometric fact. This module
enumerates the options with their consequences; ``STACK_ORDER`` records the
one the project has chosen and why.
"""

from __future__ import annotations

import itertools
import math

from . import geometry, vec

# Chosen stacking order, as indices into the fan read in angular order.
#
# Fan order: each rod lies immediately outside its angular neighbour. Picked
# over the alternatives because it puts the three shallowest angles the fan
# offers into contact (37.38 / 41.81 / 37.38), needs only two distinct saddle
# angles rather than three, is palindromic so the stack reads the same from
# either side, and states as one sentence in the field: stack them in the
# order they fan out.
#
# Its cost is that family G and L rods change level between nodes. That was
# checked and is negligible: three levels is 3 rod diameters, spread over the
# arc between two tie marks, which is a slope near 1.5% on a rod already bent
# to the dome radius. See docs/tied-node.md.
STACK_ORDER = (0, 1, 2, 3)

# Angular tolerance for calling two fans the same, in degrees.
ANGLE_TOL = 1e-6


def node_frame(point) -> tuple:
    """Right-handed basis with the radius as normal: the node's tangent plane."""
    n = vec.unit(point)
    ref = (0.0, 0.0, 1.0) if abs(n[2]) < 0.9 else (1.0, 0.0, 0.0)
    e1 = vec.unit(vec.cross(ref, n))
    e2 = vec.unit(vec.cross(n, e1))
    return n, e1, e2


def node_fan(node: dict, bows: dict) -> list:
    """The node's rods in angular order around the fan.

    Returns ``(in_plane_deg, rod_name, family, out_of_plane)`` per rod, sorted
    by angle. ``out_of_plane`` is the tangent's component along the radius and
    is the evidence for coplanarity -- it should be zero to machine precision.
    """
    point = (node["x"], node["y"], node["z"])
    n, e1, e2 = node_frame(point)
    rows = []
    for name in node["rods"]:
        bow = bows[name]
        t = bow.t_of(point)
        d = vec.unit(bow.tangent(t))
        angle = math.degrees(math.atan2(vec.dot(d, e2), vec.dot(d, e1))) % 180.0
        rows.append((angle, name, bow.family, vec.dot(d, n)))
    rows.sort()
    return rows


def fan_gaps(angles: list) -> list:
    """Angles between angular neighbours, going once around. Sums to 180."""
    a = sorted(angles)
    out = [a[i + 1] - a[i] for i in range(len(a) - 1)]
    out.append(a[0] + 180.0 - a[-1])
    return out


def canonical_gaps(gaps: list, dp: int = 6) -> tuple:
    """Cyclic gap sequence up to rotation and reflection.

    Two fans are congruent exactly when their canonical sequences match, so
    this is what decides how many distinct parts the nodes need.
    """
    n = len(gaps)
    best = None
    for seq in (list(gaps), list(reversed(gaps))):
        for i in range(n):
            cand = tuple(round(x, dp) for x in seq[i:] + seq[:i])
            if best is None or cand < best:
                best = cand
    return best


def acute(a: float, b: float) -> float:
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def stacking_options(fan_angles: list) -> list:
    """Every distinct radial stacking order, with the contacts it creates.

    Only rods adjacent in the stack touch. Reversals are collapsed: turning
    the stack inside out gives the same three contacts.
    """
    seen = set()
    out = []
    for perm in itertools.permutations(range(len(fan_angles))):
        if perm[::-1] in seen:
            continue
        seen.add(perm)
        contacts = [
            acute(fan_angles[perm[k]], fan_angles[perm[k + 1]])
            for k in range(len(perm) - 1)
        ]
        out.append(
            {
                "order": [i + 1 for i in perm],
                "contacts": [round(c, 6) for c in contacts],
                "distinct_contacts": len({round(c, 6) for c in contacts}),
                "sharpest_contact": round(max(contacts), 6),
                "chosen": perm == STACK_ORDER,
            }
        )
    out.sort(key=lambda o: (o["distinct_contacts"], o["sharpest_contact"]))
    return out


def analyse(data: dict) -> dict:
    """Full four-rod node analysis for a built model."""
    bows = {b.name: b for b in geometry.build_bows()}
    rod_diameter = data["meta"]["rod_diameter"]
    tied = [n for n in data["nodes"] if n["rod_count"] == 4]

    fans = {n["name"]: node_fan(n, bows) for n in tied}
    coplanarity = max(
        abs(row[3]) for rows in fans.values() for row in rows
    ) if fans else 0.0

    canon = {}
    for name, rows in fans.items():
        canon.setdefault(canonical_gaps(fan_gaps([r[0] for r in rows])), []).append(name)

    groups = []
    for gaps, names in canon.items():
        rows = fans[names[0]]
        groups.append(
            {
                "gaps_deg": list(gaps),
                "node_count": len(names),
                "nodes": sorted(names),
                "example": names[0],
                "families_in_fan_order": [r[2] for r in rows],
                "stacking_options": stacking_options([r[0] for r in rows]),
            }
        )
    groups.sort(key=lambda g: -g["node_count"])

    chosen = None
    for group in groups:
        for option in group["stacking_options"]:
            if option["chosen"]:
                chosen = option
                break
        if chosen:
            break

    return {
        "tied_node_count": len(tied),
        "coplanarity_residual": coplanarity,
        "distinct_fans": len(groups),
        "groups": groups,
        "stack_order": list(STACK_ORDER),
        "stack_contacts": chosen["contacts"] if chosen else [],
        "stack_height": round(3.0 * rod_diameter, 6),
        "rod_diameter": rod_diameter,
    }


def rod_levels(data: dict) -> dict:
    """Radial level of each rod at each lashed node, under ``STACK_ORDER``.

    Level 1 is the innermost. A rod that takes different levels at different
    nodes migrates radially between them; ``migration`` puts a number on how
    steep that is.
    """
    bows = {b.name: b for b in geometry.build_bows()}
    tied = [n for n in data["nodes"] if n["rod_count"] == 4]
    order = {fan_index: level for level, fan_index in enumerate(STACK_ORDER)}

    out: dict = {}
    for node in tied:
        rows = node_fan(node, bows)
        for fan_index, (_a, name, _f, _o) in enumerate(rows):
            out.setdefault(name, []).append(
                {"node": node["name"], "level": order[fan_index] + 1, "z": node["z"]}
            )
    for visits in out.values():
        visits.sort(key=lambda v: -v["z"])
    return out


def migration(data: dict) -> dict:
    """How steeply a rod has to change level between the nodes it passes.

    The worry with a fan-order stack is that a rod is innermost at one node
    and outermost at the next. It is not a real worry, and this is the
    calculation that settles it: the slope is a small fraction of a percent
    of the arc between tie marks.
    """
    radius = data["meta"]["dome_radius"]
    rod_diameter = data["meta"]["rod_diameter"]
    levels = rod_levels(data)
    marks = {r["name"]: r["tie_marks_deg"] for r in data["rods"]}

    rows = []
    worst = 0.0
    for name, visits in sorted(levels.items()):
        seen = [v["level"] for v in visits]
        span = max(seen) - min(seen)
        # Arc between consecutive tie marks on this rod.
        rod_marks = marks[name]
        step_deg = min(
            rod_marks[i + 1] - rod_marks[i] for i in range(len(rod_marks) - 1)
        ) if len(rod_marks) > 1 else 180.0
        arc_mm = radius * math.radians(step_deg)
        slope = (span * rod_diameter) / arc_mm if arc_mm else 0.0
        worst = max(worst, slope)
        rows.append(
            {
                "rod": name,
                "family": name[0],
                "levels": sorted(set(seen)),
                "level_span": span,
                "radial_shift_mm": round(span * rod_diameter, 3),
                "arc_between_nodes_mm": round(arc_mm, 3),
                "slope": round(slope, 6),
            }
        )
    return {"rods": rows, "worst_slope": round(worst, 6)}


def format_analysis(data: dict) -> str:
    """Human-readable summary, for the CLI."""
    a = analyse(data)
    mig = migration(data)
    lines = [
        f"--- {data['meta']['variant']} four-rod nodes  "
        f"(rod {a['rod_diameter']:g} mm)",
        f"  {a['tied_node_count']} lashed nodes, all four rods coplanar "
        f"(worst out-of-plane component {a['coplanarity_residual']:.1e})",
        f"  distinct fan geometries: {a['distinct_fans']}",
    ]
    for group in a["groups"]:
        gaps = ", ".join(f"{g:.4f}" for g in group["gaps_deg"])
        lines.append(
            f"    {group['node_count']} nodes, gaps around the fan: {gaps} deg"
        )
        lines.append(
            f"      families in fan order: "
            f"{'-'.join(group['families_in_fan_order'])} (example {group['example']})"
        )
    lines.append(
        f"  chosen stack {'-'.join(str(i + 1) for i in a['stack_order'])}: contacts "
        + ", ".join(f"{c:.4f}" for c in a["stack_contacts"])
        + f" deg;  stack height {a['stack_height']:g} mm"
    )
    lines.append(
        f"  worst radial migration slope: {mig['worst_slope'] * 100:.2f}% "
        f"of the arc between nodes"
    )
    lines.append("  alternatives considered:")
    for option in a["groups"][0]["stacking_options"][:4]:
        mark = " <- chosen" if option["chosen"] else ""
        contacts = " ".join(f"{c:7.4f}" for c in option["contacts"])
        lines.append(
            f"    {'-'.join(str(i) for i in option['order'])}  {contacts}  "
            f"distinct={option['distinct_contacts']}{mark}"
        )
    return "\n".join(lines)
