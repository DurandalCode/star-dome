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
- **how many doors each dome has, and which way each points.** A dome in a
  camp needs one door per neighbour, and where they point is where the
  neighbours are -- both facts about the site rather than about the dome, so
  both are derived here. `configs/variants.toml` keeps describing a dome
  standing on its own, which is what it is for;
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


def bay_azimuths(data: dict, level: str = "none") -> list:
    """Where a door can go on this dome: the eligible bays, in its own frame.

    Five of them, 72 degrees apart -- a portal goes in a low bay and anything
    else in a tall one, and each family is five. That spacing is the whole
    reason a camp has to be laid out with the lattice in mind rather than
    wherever the domes happen to look good.
    """
    kind = "low" if level == "portal" else "tall"
    return sorted(
        bay["centre_azimuth_deg"]
        for bay in doorway.bays(data)
        if bay["kind"] == kind
    )


def best_turn(bearings, bays, step: float = 0.25) -> dict:
    """How far to turn a dome so its bays best suit the neighbours it has.

    A door cannot go anywhere: there are five places for it, 72 degrees apart.
    So a dome joined to two neighbours 100 degrees apart cannot face both, and
    what it can do is share the error between them. This finds the turn that
    makes the WORST of its doors the least bad, by scanning -- the objective
    is a max of absolute differences and has corners everywhere, which is
    exactly the shape that defeats anything cleverer.

    **Two domes that face each other want their lattices half a bay apart.**
    A bearing and its reverse differ by 180, and 180 is not a multiple of 72,
    so two domes turned the same way can never both have a door on the line
    between them. Turn one of them by 36 and both can. A camp whose links form
    a tree can always be coloured that way.
    """
    if not bearings or not bays:
        return {"turn_deg": 0.0, "worst_off_deg": None}
    best = None
    steps = int(round(72.0 / step))
    for k in range(steps):
        turn = k * step
        worst = max(
            min(_gap(bay + turn, bearing) for bay in bays)
            for bearing in bearings
        )
        if best is None or worst < best[0] - 1e-9:
            best = (worst, turn)
    return {"turn_deg": round(best[1] % 360.0, 4), "worst_off_deg": round(best[0], 4)}


def doors_needed(camp: dict) -> dict:
    """``dome name -> [bearing to each neighbour]``, from the links alone.

    A dome joined to three others needs three doors, and they point at the
    three. Neither the count nor the directions are written anywhere: writing
    them would be writing down something the links already determine, and the
    first time a dome moved the two would stop agreeing.

    A dome joined to nothing keeps whatever door its variant gives it -- it is
    a dome standing on its own, which is the case `variants.toml` describes.
    """
    at = {dome["name"]: dome["at"] for dome in camp["domes"]}
    out = {name: [] for name in at}
    for link_spec in camp.get("links") or []:
        a, b = link_spec["between"]
        out[a].append(round(bearing_deg(at[a], at[b]), 6))
        out[b].append(round(bearing_deg(at[b], at[a]), 6))
    return {name: sorted(bearings) for name, bearings in out.items()}


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


def _junction(data: dict, name: str, shape: list) -> dict:
    """Does this corridor's section pass the bay it lands on?"""
    fit = doorway.fit_shape(data, shape, "corridor")
    return {
        "end": name,
        "passes": bool(fit["fits"]),
        "spare_mm": fit.get("spare_mm"),
        "door_admits": list((data.get("doorway") or {}).get("admits", [])),
    }


def stations(free: float, pitch: float) -> list:
    """Where the ribs stand along a corridor, as fractions of the free run.

    At the SPACING ASKED FOR, and centred. An earlier version spread the ribs
    evenly over the run instead, which quietly made the pitch a rib count and
    not a distance: 4 ribs over 4234 mm came out at 847 mm centres when the
    pitch said 1200. At least one rib, because a corridor shorter than its own
    pitch still wants a frame in it.
    """
    if free <= 0.0 or pitch <= 0.0:
        return []
    # As many as fit at this spacing without either end one overhanging the
    # run, and never fewer than one: a corridor shorter than its own pitch
    # still wants a frame in it.
    count = max(1, int(free // pitch) + 1)
    while count > 1 and (count - 1) * pitch > free:
        count -= 1
    first = (free - (count - 1) * pitch) / 2.0
    return [(first + k * pitch) / free for k in range(count)]


def _frames(at: list, bearing: float, reach: float, free: float, at_f: list,
            width: float, height: float, brace_leg: float) -> list:
    """The portal frames along one corridor, as boards in camp coordinates.

    A hoop is a curve and interpolating the two mouths gives it for nothing. A
    frame is five boards with thickness, so it is placed rather than
    interpolated: every frame is the same frame, square to the run, standing
    on the camp's own ground at z = 0.
    """
    a = math.radians(bearing)
    along = (math.cos(a), math.sin(a))
    across = (-math.sin(a), math.cos(a))
    out = []
    for f in at_f:
        d = reach + free * f
        origin = (at[0] + along[0] * d, at[1] + along[1] * d, 0.0)
        out.append(
            corridor.frame_boards(origin, along, across, width, height, brace_leg)
        )
    return out


def _tube(loop_a: list, loop_b: list, at_f: list, kind: str = "hoop",
          frames: list | None = None) -> dict:
    """The corridor as geometry: two mouths, the ribs between, and a skin.

    Every rib is the same section, so a hoop part way along is the two mouths
    interpolated -- which is also why the skin is a quad strip between them
    and needs nothing solved. A timber frame is not a curve and does not
    interpolate; it arrives already placed, in ``frames``.

    THE FAR MOUTH RUNS THE OTHER WAY ROUND, and that is not a detail. Each
    mouth is built in its own dome's frame, up the +v side of the section and
    down the -v side -- but the two domes face each other, so one dome's +v is
    the other's -v in the camp. Joining them index for index therefore pairs
    the left of one end with the RIGHT of the other, and the skin comes out
    crossed: a corridor with a half-turn in it. Reversing the far loop is what
    puts each point against the point on its own side.
    """
    far = list(reversed(loop_b))
    rings = []
    if kind != "portal":
        for f in at_f:
            rings.append(
                [
                    [
                        round(pa[i] + (pb[i] - pa[i]) * f, 3)
                        for i in range(3)
                    ]
                    for pa, pb in zip(loop_a, far)
                ]
            )
    return {
        "kind": kind,
        "mouths": [loop_a, far],
        "rings": rings,
        "frames": list(frames or ()),
        "skin_note": (
            "A quad strip between the two mouths: matching points joined in "
            "order, both loops closed, equally sampled and already wound the "
            "same way round the corridor."
        ),
    }


def link(a: dict, b: dict, width: float, height: float,
         pitch: float = corridor.DEFAULT_PITCH_MM,
         samples: int = corridor.ARC_SAMPLES,
         kind: str = "hoop",
         brace_leg: float = corridor.DEFAULT_BRACE_LEG_MM) -> dict:
    """One corridor between two domes, measured on both of them.

    ``a`` and ``b`` are ``{"name", "at", "data"}``. Nothing about the corridor
    is chosen here beyond its section: where it runs and how long it is are
    read off the two positions.

    ``kind`` picks which corridor this is -- a bent rod hoop or a timber
    portal frame. It changes the section, and the section is what the mouth is
    cut to, so the two kinds do not merely look different: a wider mouth
    reaches less far up the sphere and leaves a longer run between the covers.
    """
    to_b = bearing_deg(a["at"], b["at"])
    to_a = (to_b + 180.0) % 360.0
    centres = math.dist(a["at"], b["at"])

    # The mouth is cut on the dome's own surface, so the bearing has to be
    # expressed in the dome's own frame -- turning the dome turns the wall the
    # corridor lands on with it.
    mouth_a = corridor.mouth(
        a["data"], (to_b - a["turn"]) % 360.0, width, height, samples,
        kind, brace_leg,
    )
    mouth_b = corridor.mouth(
        b["data"], (to_a - b["turn"]) % 360.0, width, height, samples,
        kind, brace_leg,
    )
    on_both = mouth_a.get("fits_on_dome") and mouth_b.get("fits_on_dome")

    reach_a = mouth_a.get("max_reach_mm", 0.0) if on_both else 0.0
    reach_b = mouth_b.get("max_reach_mm", 0.0) if on_both else 0.0
    free = centres - reach_a - reach_b

    covers = cover.radius(a["data"]) + cover.radius(b["data"])
    at_f = stations(free, pitch)
    ribs = len(at_f)

    if kind == "portal":
        rib = corridor.portal_frame(width, height, brace_leg)
        material = "board"
        per_rib = rib["board_length_mm"]
    else:
        rib = corridor.hoop(
            width, height, a["data"]["meta"]["rod_diameter"],
            a["data"]["meta"]["dome_radius"],
        )
        material = "rod"
        per_rib = rib["rod_length_mm"]

    # Landing on a bay's AZIMUTH is what the layout solves. Whether the
    # section also passes THROUGH that bay is a separate question, and for a
    # wide timber portal the answer is usually no: its posts come down on the
    # bows rather than inside the opening. Saying only the first would be true
    # and misleading in the same breath.
    shape = corridor.section_for(kind, width, height, samples, brace_leg)
    through = [
        _junction(a["data"], a["name"], shape),
        _junction(b["data"], b["name"], shape),
    ]

    return {
        "between": [a["name"], b["name"]],
        "bearing_deg": round(to_b, 3),
        "centres_mm": round(centres, 1),
        "length_mm": round(free, 1),
        "section": {
            "kind": kind,
            "width_mm": width,
            "height_mm": height,
            "brace_leg_mm": brace_leg if kind == "portal" else None,
        },
        "meets_the_cover": bool(on_both),
        "reach_mm": [round(reach_a, 1), round(reach_b, 1)],
        "joint_off_flat_mm": [
            mouth_a.get("step_mm"), mouth_b.get("step_mm")
        ],
        "mouths": [mouth_a, mouth_b],
        "ribs": ribs,
        "rib": rib,
        "material": material,
        "rib_material_mm": round(ribs * per_rib, 1),
        "through_the_bay": through,
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
                at_f,
                kind=kind,
                frames=(
                    _frames(a["at"], to_b, reach_a, free, at_f,
                            width, height, brace_leg)
                    if kind == "portal"
                    else []
                ),
            )
            if on_both
            else None
        ),
    }


def prepare(camp: dict, config_path=None, weave_mode: str = "flat",
            include_polylines: bool = False) -> dict:
    """Build the model of every dome in a camp, as that camp needs it.

    A dome in a camp is not the plain variant: it carries a door per
    neighbour, pointed at it, and it is set down at whatever turn suits its
    bays best. Both depend on where it stands, so the model does too -- and
    two domes that come out identical are built once and shared, because
    building them twice is two chances to differ.

    Returns the models keyed by dome name and the plan with every derived
    turn filled in, so what is analysed and what is drawn agree.
    """
    from . import model as _model

    wanted = doors_needed(camp)
    models, cache, bays, built = {}, {}, {}, {}
    domes = []
    for dome in camp["domes"]:
        variant = config.load(dome["variant"], config_path)
        bearings = tuple(wanted[dome["name"]])
        if variant.name not in bays:
            bays[variant.name] = bay_azimuths(
                _model.build(variant, weave_mode="flat"), variant.door_cut
            )
        # A door can only go in one of five bays, 72 degrees apart, so which
        # way the dome is set down decides how near its doors get to its
        # neighbours. Derived unless the plan insists on a turn of its own.
        turn = dome.get("turn")
        if turn is None:
            turn = best_turn(bearings, bays[variant.name])["turn_deg"]
        turn = float(turn)

        key = (variant.name, bearings, turn)
        if key not in cache:
            doors = tuple(
                config.Door(
                    cut=variant.door_cut,
                    facing=bearing - turn,
                    template=variant.door or doorway.DEFAULT_TEMPLATE,
                )
                for bearing in bearings
            )
            spec = (
                config.load(dome["variant"], config_path, doors=doors)
                if doors
                else variant
            )
            cache[key] = _model.build(
                spec, weave_mode=weave_mode, include_polylines=include_polylines
            )
            built[key] = spec
        models[dome["name"]] = cache[key]
        domes.append(dict(dome, turn=turn))

    return {
        "models": models,
        "plan": dict(camp, domes=domes),
    }


# Each kind of corridor has its own sensible size. An unset one therefore
# means "this kind's default" rather than "the hoop's default applied to a
# timber frame", which would draw a 900 mm portal nobody asked for.
KIND_DEFAULTS = {
    "hoop": (corridor.DEFAULT_WIDTH_MM, corridor.DEFAULT_HEIGHT_MM,
             corridor.DEFAULT_PITCH_MM),
    "portal": (corridor.DEFAULT_PORTAL_WIDTH_MM,
               corridor.DEFAULT_PORTAL_HEIGHT_MM,
               corridor.DEFAULT_PORTAL_PITCH_MM),
}


def analyse(camp: dict, models: dict, width: float | None = None,
            height: float | None = None,
            pitch: float | None = None,
            kind: str = "hoop",
            brace_leg: float = corridor.DEFAULT_BRACE_LEG_MM) -> dict:
    """The whole plan: where everything stands and what joins it."""
    if kind not in KIND_DEFAULTS:
        raise ValueError(
            f"unknown corridor kind {kind!r}; know "
            + ", ".join(sorted(KIND_DEFAULTS))
        )
    default_w, default_h, default_p = KIND_DEFAULTS[kind]
    width = default_w if width is None else width
    height = default_h if height is None else height
    pitch = default_p if pitch is None else pitch
    by_name = {}
    for dome in camp["domes"]:
        canonical = config.resolve(dome["variant"])
        by_name[dome["name"]] = {
            "name": dome["name"],
            "variant": canonical,
            "at": [float(dome["at"][0]), float(dome["at"][1])],
            # A door is placed at a bearing, so nothing has to be turned to
            # face anything. `turn` stays for aiming a dome that is joined to
            # nothing, or for turning one for reasons of its own.
            "turn": float(dome.get("turn", 0.0)) % 360.0,
            "data": models[dome["name"]] if dome["name"] in models
            else models[canonical],
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
                corridor.ARC_SAMPLES,
                str(spec.get("kind", kind)),
                float(spec.get("brace", brace_leg)),
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
        # Kind-neutral: a hoop is metres of rod and a portal is metres of
        # board, and a camp can hold one of each if a link asks for it.
        "corridor_material_m": {
            material: round(
                sum(l["rib_material_mm"] for l in links
                    if l["material"] == material) / 1000.0,
                2,
            )
            for material in sorted({l["material"] for l in links})
        },
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
                f"{one['ribs']} "
                + ("frames" if one["section"]["kind"] == "portal" else "hoops")
                + f", {one['rib_material_mm'] / 1000.0:.1f} m of "
                + one["material"]
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
    joints = [(one, end) for one in a["links"] for end in one["through_the_bay"]]
    bad = [(one, end) for one, end in joints if not end["passes"]]
    if bad:
        out.append(
            f"  {len(bad)} of {len(joints)} junctions do NOT pass: the section "
            "is bigger than the bay it lands"
        )
        out.append(
            "  on, so its sides come down on the bows rather than inside the "
            "opening. Each needs the"
        )
        out.append(
            "  entrance/corridor interface (milestone 5), or a narrower "
            "corridor. The door itself is"
        )
        out.append("  not the problem -- a person still walks through it:")
        for one, end in bad:
            admits = ", ".join(end["door_admits"]) or "nothing"
            out.append(
                f"    {' - '.join(one['between']):<26} at {end['end']:<12} "
                f"(that door admits {admits})"
            )
        out.append("")
    else:
        out.append(
            f"  all {len(joints)} junctions pass: the section goes through the "
            "bay at every end"
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
