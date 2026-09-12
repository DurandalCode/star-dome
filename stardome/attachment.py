"""How the cover is held on.

The dome has no purlins and no ring beam. It is fifteen continuous bows and
ten feet, and the fabric lies over the lot -- so the question is not "what does
the cover bolt to" but "what already resists uplift, and can the cover reach
it".

The answer is the **driven steel angle at each foot**. It is the one thing in
the structure whose whole job is holding the dome down, through soil; the
cover's job is the same job, and giving it a separate anchor would be a second
system to get wrong. Nothing new is printed, and that is the point: milestone
5 asks for an attachment that does not concentrate load on one printed part,
and the way to satisfy that is not a better lug but no lug.

Three pieces:

**A bolt rope in a hem, all the way round the base.** A continuous line in a
sewn sleeve rather than a row of eyelets. Fabric tears from a point and does
not tear from a line, and the hem turns the whole base edge into one member.

**Ten loops, one per foot.** The hem's line is picked up at each foot and
dropped over the angle. Between feet the hem carries its own tension, and the
sag it takes is reported below rather than assumed away.

**Five straps over the crown, following the U bows.** A cover held only at its
edge lifts in the middle, which is where a dome's uplift is worst. Each bow
runs foot to foot, so a strap laid along one needs no anchor of its own -- it
ends on the two angles the bow already stands on. The U family is the one to
use: all three families touch every foot exactly once, and U is the family
that goes over the top, reaching the dome's own height.

That last is the whole reason this is a geometry question and not a hardware
one. Five straps, ten ends, ten feet, one end each.

```bash
python3 -m stardome attachment M
python3 -m stardome attachment --all
```

Nothing here is a load calculation. What it gives is lengths, counts and where
things land; whether webbing of a given strength holds a cover of a given area
in a given wind is milestone 8.
"""

from __future__ import annotations

import math

from . import cover

# The bow family the retaining straps follow. All three families touch every
# foot exactly once; this is the one that crosses the crown.
STRAP_FAMILY = "U"

# How much a strap is pulled down past the foot to tension it, and how much
# hem is turned under. Both are workshop numbers rather than results.
DEFAULT_HEM_MM = 60.0
DEFAULT_STRAP_TAIL_MM = 300.0


def hem(data: dict, hem_mm: float = DEFAULT_HEM_MM) -> dict:
    """The base edge: its length, what interrupts it, and how it sags.

    The hem is a sleeve with a line in it, so its length is the cover's own
    circumference less whatever the doorway takes out of it. The sag is the
    catenary-ish droop between two feet if the line is pulled to a given
    tension -- reported as the geometric shape only, because the tension is
    not known.
    """
    from . import doorway as _doorway

    r = cover.radius(data)
    feet = data["base_nodes"]
    doors = _doorway.doors_on(data)

    circumference = 2.0 * math.pi * r
    # Every door breaks the hem, not just the first: the rope dead-ends at
    # both feet of each opening and the run between two doors is its own line.
    gaps = [
        circumference * door["bay"]["span_deg"] / 360.0 for door in doors
    ]
    interrupted = sum(gaps)
    spacing = circumference / len(feet)

    return {
        "cover_radius_mm": round(r, 1),
        "circumference_mm": round(circumference, 1),
        "doorway_gap_mm": round(interrupted, 1),
        "doorway_count": len(doors),
        "doorway_gaps_mm": [round(g, 1) for g in gaps],
        "rope_runs": max(1, len(doors)),
        "rope_length_mm": round(circumference - interrupted, 1),
        "loops": len(feet),
        "loop_spacing_mm": round(spacing, 1),
        "hem_allowance_mm": hem_mm,
        "hem_fabric_m2": round(circumference * hem_mm * 2.0 / 1e6, 3),
        "note": (
            "A line in a sleeve, not a row of eyelets: fabric tears from a "
            "point and does not tear from a line. The doorway interrupts it, "
            "so the rope is dead-ended at the two feet the door stands "
            "between rather than run through."
        ),
    }


def straps(data: dict, tail_mm: float = DEFAULT_STRAP_TAIL_MM) -> dict:
    """The over-the-crown retaining straps, one per bow of the strap family.

    A strap lies along a bow, on the outside of the cover, and ends on the two
    driven angles that bow already stands on. So the count, the anchors and
    the paths are all the dome's, not a choice: five bows, ten ends, ten feet.
    """
    r = cover.radius(data)
    feet = {b["index"]: b["name"] for b in data["base_nodes"]}
    rods = [rod for rod in data["rods"] if rod["family"] == STRAP_FAMILY]

    ends = []
    for rod in rods:
        ends.extend((feet[rod["foot_a"]], feet[rod["foot_b"]]))
    per_foot = {name: ends.count(name) for name in sorted(set(ends))}

    over = math.pi * r
    return {
        "family": STRAP_FAMILY,
        "count": len(rods),
        "bows": sorted(rod["name"] for rod in rods),
        "over_cover_mm": round(over, 1),
        "tail_each_end_mm": tail_mm,
        "strap_length_mm": round(over + 2.0 * tail_mm, 1),
        "total_webbing_mm": round(len(rods) * (over + 2.0 * tail_mm), 1),
        "ends_per_foot": per_foot,
        "one_end_per_foot": set(per_foot.values()) == {1},
        "note": (
            "Laid along a bow, outside the cover, ending on the angles that "
            "bow already stands on. The U family is used because all three "
            "touch every foot exactly once and U is the one that crosses the "
            "crown."
        ),
    }


def analyse(data: dict, hem_mm: float = DEFAULT_HEM_MM,
            tail_mm: float = DEFAULT_STRAP_TAIL_MM) -> dict:
    """Everything the cover needs to be held on, as lengths and counts."""
    edge = hem(data, hem_mm)
    lines = straps(data, tail_mm)
    return {
        "variant": data["meta"]["variant"],
        "hem": edge,
        "straps": lines,
        "anchors": {
            "count": len(data["base_nodes"]),
            "what": "the driven steel angle already at each foot",
            "per_anchor": "one hem loop and one strap end",
            "new_printed_parts": 0,
        },
        "webbing_total_m": round(
            (edge["rope_length_mm"] + lines["total_webbing_mm"]) / 1000.0, 1
        ),
        "note": (
            "Lengths, counts and where things land. No load, no tension, no "
            "claim that any of it holds -- that is milestone 8."
        ),
    }


def format_analysis(data: dict, hem_mm: float = DEFAULT_HEM_MM,
                    tail_mm: float = DEFAULT_STRAP_TAIL_MM) -> str:
    a = analyse(data, hem_mm, tail_mm)
    edge, lines = a["hem"], a["straps"]
    out = [
        f"--- {a['variant']} cover attachment  "
        f"(fabric at r = {edge['cover_radius_mm']:.0f} mm)",
        f"  hem rope        {edge['rope_length_mm'] / 1000.0:.2f} m in a sleeve, "
        f"{edge['loops']} loops at {edge['loop_spacing_mm']:.0f} mm",
        (
            f"  doorway gap     {edge['doorway_gap_mm']:.0f} mm, dead-ended "
            "either side"
            if edge["doorway_gap_mm"]
            else "  doorway gap     none: the rope closes on itself"
        ),
        f"  hem allowance   {edge['hem_allowance_mm']:.0f} mm turned under, "
        f"{edge['hem_fabric_m2']:.2f} m2 of fabric",
        f"  straps          {lines['count']} over the crown on family "
        f"{lines['family']} ({', '.join(lines['bows'])})",
        f"                  {lines['strap_length_mm'] / 1000.0:.2f} m each, "
        f"{lines['total_webbing_mm'] / 1000.0:.1f} m total",
        f"  anchors         {a['anchors']['count']} driven angles, "
        f"{a['anchors']['per_anchor']}",
        f"  webbing         {a['webbing_total_m']:.1f} m all in",
        f"  new printed parts: {a['anchors']['new_printed_parts']}",
        "",
        "  " + a["note"],
    ]
    return "\n".join(out)
