"""A camp: several domes, joined by corridors, laid out from a plan.

[`corridor.py`](corridor.py) opens with the sentence this module finishes -- *a
corridor is how two domes become a camp rather than two tents* -- and then does
the half that fits in one dome: it puts a tunnel on a doorway and measures
whether it fits the hole it is attached to. A corridor between two domes has
two ends, and its length is not a parameter at all.

## What is written down, and what is derived

``configs/camps.toml`` says which domes stand where and which pairs are
joined. That is all it says. Everything else follows:

- the **bearing** from each dome to its neighbour, from the two positions;
- the **door** that bearing wants, and whether the dome, as turned, has one
  facing that way. A dome is not re-drilled to face a neighbour, it is turned
  on the ground: `turn` rotates the whole dome and its doors with it, and the
  plan reports what turn each link would want if the written one does not
  suit. A dome with two neighbours needs two doors, and no turn substitutes
  for the second -- that is a change to `configs/variants.toml`, and the plan
  says so rather than pretending otherwise;
- the **length** of the corridor, which is the gap between the two covers
  along that bearing, not a number anybody chose;
- the two **mouths**, one on each dome's cover.

A bearing typed into both files is a bearing that stops agreeing with itself,
so it is typed into neither. Move a dome and everything moves with it.

## The length is what is left between two covers

A dome's cover reaches further out at the crown of a tunnel's section than at
its floor, so the joint is not a plane cut -- `corridor.mouth` already reports
how far from flat it is. What a corridor has to span is therefore measured
from the furthest point of each mouth, not from either centre:

    length = distance between centres - reach of A - reach of B

which is the free run between the two fabrics. It comes out negative when two
domes are close enough that their covers would touch, and that is reported as
the overlap it is rather than as a corridor of negative length.

```bash
python3 -m stardome camp yard
python3 -m stardome camp --all --json
```

Nothing here is structural, and one thing in particular is not a claim: a
corridor that does not fit the doorway it lands on is **reported and drawn
anyway**. Whether it fits is `corridor`'s question and it answers it; a plan is
allowed to be wrong on paper, which is the point of drawing it before building
it. See docs/camp.md.
"""

from __future__ import annotations

import math
import tomllib
from pathlib import Path

from . import config, corridor, cover, doorway

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "camps.toml"

# How close two bearings have to be before a door counts as facing a
# neighbour. A door sits in a bay and the bays are 36 degrees apart, so half a
# bay is the widest a door could be off and still be the right one.
FACING_TOLERANCE_DEG = 18.0


def load_all(path=None) -> dict:
    """Every named camp in the file, as plain dicts."""
    path = Path(path) if path is not None else DEFAULT_CONFIG
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)
    camps = raw.get("camps") or {}
    if not camps:
        raise ValueError(f"no [camps.*] tables found in {path}")
    for name, camp in camps.items():
        _check(name, camp)
    return camps


def _check(name: str, camp: dict) -> None:
    domes = camp.get("domes") or []
    if not domes:
        raise ValueError(f"camp {name!r} has no domes")
    seen = set()
    for dome in domes:
        for key in ("name", "variant", "at"):
            if key not in dome:
                raise ValueError(f"camp {name!r}: a dome has no {key!r}")
        if dome["name"] in seen:
            raise ValueError(
                f"camp {name!r} has two domes called {dome['name']!r}; "
                "a camp can hold two of one variant, but not two of one name"
            )
        seen.add(dome["name"])
        if len(dome["at"]) != 2:
            raise ValueError(
                f"camp {name!r}: {dome['name']!r} sits at {dome['at']!r}; "
                "a position is [x, y] on the ground, in mm"
            )
    for link in camp.get("links") or []:
        pair = link.get("between")
        if not pair or len(pair) != 2:
            raise ValueError(f"camp {name!r}: a link joins exactly two domes")
        for end in pair:
            if end not in seen:
                raise ValueError(
                    f"camp {name!r}: link to {end!r}, which is not in this camp"
                )
        if pair[0] == pair[1]:
            raise ValueError(
                f"camp {name!r}: {pair[0]!r} is linked to itself"
            )


def bearing_deg(frm, to) -> float:
    """Compass-free bearing: the azimuth of ``to`` seen from ``frm``."""
    return math.degrees(math.atan2(to[1] - frm[1], to[0] - frm[0])) % 360.0


def _gap(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def door_azimuths(data: dict, turn_deg: float = 0.0) -> list:
    """Where this dome's doors point once it has been turned on the ground."""
    return [
        (door["bay"]["centre_azimuth_deg"] + turn_deg) % 360.0
        for door in doorway.doors_on(data)
    ]


def door_facing(data: dict, azimuth_deg: float, turn_deg: float = 0.0) -> dict:
    """The dome's door nearest a bearing, as turned, and how far off it is.

    Doors live in `configs/variants.toml` and are aimed there. This does not
    move one -- it says which is nearest and by how much, and what turn would
    bring it round, so a camp that wants a door where there is none says so in
    as many words instead of quietly drawing one.
    """
    doors = doorway.doors_on(data)
    if not doors:
        return {"has_door": False, "off_by_deg": None, "note": "no door at all"}
    here = door_azimuths(data, turn_deg)
    at = min(here, key=lambda a: _gap(a, azimuth_deg))
    off = _gap(at, azimuth_deg)
    # What the dome would have to be turned to, for this door to face it.
    own = (at - turn_deg) % 360.0
    return {
        "has_door": True,
        "at_deg": round(at, 3),
        "off_by_deg": round(off, 3),
        "facing_it": off <= FACING_TOLERANCE_DEG,
        "turn_for_it_deg": round((azimuth_deg - own) % 360.0, 3),
        "door_count": len(doors),
    }


def _to_camp(points: list, dome: dict) -> list:
    """One dome's own points, put where that dome stands in the camp.

    Turn about its own axis, slide to its position, and lift it so every
    dome's GROUND is the camp's z = 0 -- a dome with a skirt keeps its base
    ring at zero in its own frame and hangs the skirt below, so a camp that
    ignored the lift would bury it.
    """
    a = math.radians(dome["turn"])
    ca, sa = math.cos(a), math.sin(a)
    lift = dome["data"]["meta"].get("skirt_height", 0.0) or 0.0
    x0, y0 = dome["at"]
    return [
        [
            round(px * ca - py * sa + x0, 3),
            round(px * sa + py * ca + y0, 3),
            round(pz + lift, 3),
        ]
        for px, py, pz in points
    ]


def _tube(loop_a: list, loop_b: list, hoops: int) -> dict:
    """The corridor as geometry: two mouths, the rings between, and a skin.

    Every ring is the same section, so a ring part way along is the two mouths
    interpolated -- which is also why the skin is a quad strip between them
    and needs nothing solved.
    """
    rings = []
    for k in range(1, max(0, hoops) + 1):
        f = k / (hoops + 1.0)
        rings.append(
            [
                [
                    round(pa[i] + (pb[i] - pa[i]) * f, 3)
                    for i in range(3)
                ]
                for pa, pb in zip(loop_a, loop_b)
            ]
        )
    return {
        "mouths": [loop_a, loop_b],
        "rings": rings,
        "skin_note": (
            "A quad strip between the two mouths: matching points joined in "
            "order, both loops closed and equally sampled."
        ),
    }


def link(a: dict, b: dict, width: float, height: float,
         pitch: float = corridor.DEFAULT_PITCH_MM,
         samples: int = corridor.ARC_SAMPLES) -> dict:
    """One corridor between two domes, measured on both of them.

    ``a`` and ``b`` are ``{"name", "at", "data"}``. Nothing about the corridor
    is chosen here beyond its section: where it runs and how long it is are
    read off the two positions.
    """
    to_b = bearing_deg(a["at"], b["at"])
    to_a = (to_b + 180.0) % 360.0
    centres = math.dist(a["at"], b["at"])

    # The mouth is cut on the dome's own surface, so the bearing has to be
    # expressed in the dome's own frame -- turning the dome turns the wall the
    # corridor lands on with it.
    mouth_a = corridor.mouth(
        a["data"], (to_b - a["turn"]) % 360.0, width, height, samples
    )
    mouth_b = corridor.mouth(
        b["data"], (to_a - b["turn"]) % 360.0, width, height, samples
    )
    on_both = mouth_a.get("fits_on_dome") and mouth_b.get("fits_on_dome")

    reach_a = mouth_a.get("max_reach_mm", 0.0) if on_both else 0.0
    reach_b = mouth_b.get("max_reach_mm", 0.0) if on_both else 0.0
    free = centres - reach_a - reach_b

    covers = cover.radius(a["data"]) + cover.radius(b["data"])
    hoops = int(free // pitch) + 1 if free > 0 else 0

    return {
        "between": [a["name"], b["name"]],
        "bearing_deg": round(to_b, 3),
        "centres_mm": round(centres, 1),
        "length_mm": round(free, 1),
        "section": {"width_mm": width, "height_mm": height},
        "meets_the_cover": bool(on_both),
        "reach_mm": [round(reach_a, 1), round(reach_b, 1)],
        "joint_off_flat_mm": [
            mouth_a.get("step_mm"), mouth_b.get("step_mm")
        ],
        "mouths": [mouth_a, mouth_b],
        "hoops": hoops,
        "hoop": corridor.hoop(
            width, height, a["data"]["meta"]["rod_diameter"],
            a["data"]["meta"]["dome_radius"],
        ),
        "rod_mm": round(
            hoops * corridor.hoop(
                width, height, a["data"]["meta"]["rod_diameter"],
                a["data"]["meta"]["dome_radius"],
            )["rod_length_mm"],
            1,
        ),
        "doors": [
            door_facing(a["data"], to_b, a["turn"]),
            door_facing(b["data"], to_a, b["turn"]),
        ],
        # Two covers that touch is a layout mistake, and it shows up here as a
        # corridor with no length to it.
        "covers_overlap": centres < covers,
        "covers_clear_mm": round(centres - covers, 1),
        "drawing": (
            _tube(
                _to_camp(mouth_a["points"], a),
                _to_camp(mouth_b["points"], b),
                hoops,
            )
            if on_both
            else None
        ),
    }


def analyse(camp: dict, models: dict, width: float = corridor.DEFAULT_WIDTH_MM,
            height: float = corridor.DEFAULT_HEIGHT_MM,
            pitch: float = corridor.DEFAULT_PITCH_MM) -> dict:
    """The whole plan: where everything stands and what joins it."""
    by_name = {}
    for dome in camp["domes"]:
        canonical = config.resolve(dome["variant"])
        by_name[dome["name"]] = {
            "name": dome["name"],
            "variant": canonical,
            "at": [float(dome["at"][0]), float(dome["at"][1])],
            "turn": float(dome.get("turn", 0.0)) % 360.0,
            "data": models[canonical],
        }

    links = []
    for spec in camp.get("links") or []:
        a, b = (by_name[end] for end in spec["between"])
        links.append(
            link(
                a, b,
                float(spec.get("width", width)),
                float(spec.get("height", height)),
                float(spec.get("pitch", pitch)),
            )
        )

    xs = [d["at"][0] for d in by_name.values()]
    ys = [d["at"][1] for d in by_name.values()]
    reach = max(cover.radius(d["data"]) for d in by_name.values())
    return {
        "note": camp.get("note", ""),
        "domes": [
            {
                "name": d["name"],
                "variant": d["variant"],
                "at": d["at"],
                "diameter_mm": d["data"]["meta"]["dome_diameter"],
                "cover_radius_mm": round(cover.radius(d["data"]), 1),
                "turn_deg": d["turn"],
                "doors": [round(az, 2) for az in door_azimuths(d["data"], d["turn"])],
            }
            for d in by_name.values()
        ],
        "links": links,
        "footprint_mm": [
            round(max(xs) - min(xs) + 2 * reach, 1),
            round(max(ys) - min(ys) + 2 * reach, 1),
        ],
        "corridor_rod_m": round(
            sum(l["rod_mm"] for l in links) / 1000.0, 2
        ),
        "problems": _problems(by_name, links),
    }


def _problems(by_name: dict, links: list) -> list:
    """Everything about this plan that will not build as drawn.

    Reported, never enforced. A plan is allowed to be wrong on paper -- that
    is what drawing it before building it is for.
    """
    out = []
    names = list(by_name)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = by_name[names[i]], by_name[names[j]]
            apart = math.dist(a["at"], b["at"])
            covers = cover.radius(a["data"]) + cover.radius(b["data"])
            if apart < covers:
                out.append(
                    f"{a['name']} and {b['name']} overlap: {apart:.0f} mm "
                    f"between centres against {covers:.0f} mm of cover"
                )
    for one in links:
        a, b = one["between"]
        for end, door in zip((a, b), one["doors"]):
            if not door["has_door"]:
                out.append(f"{end} has no door at all to put a corridor on")
            elif not door["facing_it"]:
                fix = (
                    f"turn {end} to {door['turn_for_it_deg']:.0f} deg"
                    if door["door_count"] == 1
                    else f"give {end} a door facing it, or turn it to "
                         f"{door['turn_for_it_deg']:.0f} deg"
                )
                out.append(
                    f"{end}'s nearest door is {door['off_by_deg']:.0f} deg off "
                    f"the bearing to its neighbour -- {fix}"
                )
        if not one["meets_the_cover"]:
            out.append(
                f"the corridor {a}-{b} is too big to meet either cover at all"
            )
        elif one["length_mm"] <= 0:
            out.append(
                f"the corridor {a}-{b} has no length: the covers are "
                f"{-one['length_mm']:.0f} mm into each other"
            )
    return out


def format_analysis(name: str, camp: dict, models: dict, **kwargs) -> str:
    a = analyse(camp, models, **kwargs)
    out = [f"--- camp {name}" + (f"  -- {a['note']}" if a["note"] else "")]
    out.append(
        f"  {len(a['domes'])} domes over "
        f"{a['footprint_mm'][0] / 1000.0:.1f} x "
        f"{a['footprint_mm'][1] / 1000.0:.1f} m"
    )
    for dome in a["domes"]:
        doors = ", ".join(f"{d:g}" for d in dome["doors"]) or "none"
        out.append(
            f"    {dome['name']:<10} {dome['variant']:<4} at "
            f"{dome['at'][0] / 1000.0:6.1f}, {dome['at'][1] / 1000.0:6.1f} m"
            f", turned {dome['turn_deg']:5.1f}   doors at {doors} deg"
        )
    out.append("")
    for one in a["links"]:
        a_name, b_name = one["between"]
        out.append(
            f"  {a_name} - {b_name}  bearing {one['bearing_deg']:.1f} deg, "
            f"{one['centres_mm'] / 1000.0:.2f} m between centres"
        )
        if one["meets_the_cover"]:
            out.append(
                f"    corridor    {one['length_mm']:.0f} mm of free run, "
                f"{one['hoops']} hoops, {one['rod_mm'] / 1000.0:.1f} m of rod"
            )
            out.append(
                f"    joint       {one['joint_off_flat_mm'][0]:.0f} and "
                f"{one['joint_off_flat_mm'][1]:.0f} mm from flat at the two ends"
            )
        else:
            out.append("    corridor    does not meet the covers at this size")
        for end, door in zip(one["between"], one["doors"]):
            if not door["has_door"]:
                out.append(f"    {end:<11} no door")
            else:
                out.append(
                    f"    {end:<11} door at {door['at_deg']:.1f} deg, "
                    f"{door['off_by_deg']:.1f} off the bearing"
                    + (
                        ""
                        if door["facing_it"]
                        else f"  -- turn to {door['turn_for_it_deg']:.0f} deg"
                    )
                )
        out.append("")
    if a["problems"]:
        out.append("  will not build as drawn:")
        for problem in a["problems"]:
            out.append(f"    - {problem}")
    else:
        out.append("  nothing in this plan contradicts itself")
    out.append("")
    out.append(
        "  Layout and fit only. A corridor that does not fit its doorway is "
        "reported and drawn anyway -- a plan is allowed to be wrong on paper."
    )
    return "\n".join(out)
