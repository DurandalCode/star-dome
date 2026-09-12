"""The door: one bay of the star, opened to the ground.

A Star Dome has no door. It has fifteen rods and whatever gaps they leave, so
a doorway is not designed, it is *chosen* -- and then measured. ``entrance``
answers "how big an opening will fit anywhere". This module answers the next
question: **which opening, bounded by what, and what is its outline in space**,
which is what a cover panel and a door frame are actually cut to.

## What the star leaves you

Unrolled (see ``entrance``), the dome has ten ground-standing openings in two
sizes: five tall ones and five low ones, alternating. The tall one is the door.
Its proportions are fixed by the shape, not by the size:

    span          34.5 deg of azimuth, at every diameter
    head height   0.26287 * D, exactly -- the head is a node on a
                  self-similar shape, so it scales with nothing else
    clear height  about 0.254 * D, being the head less the rod. Not
                  quite self-similar, because a rod is a fixed thickness
                  taking a shrinking bite out of a growing dome: 0.2541
                  of D on D3, 0.2549 on D12
    open area     about 0.042 * D^2

It is a **lancet**: two bows of family G spring from adjacent base points and
meet overhead at a lashed four-rod node. So the doorway is framed, top and
bottom, by joints that already exist -- two base points and one of the ten
strongest nodes in the structure. It costs nothing to have.

## Why not simply cut a rod

Because every bow is one continuous semicircle carrying load the whole way
round. Shortening one to widen a hole does not remove a piece of a member, it
removes the member -- and with it one fifteenth of the structure, at the exact
place where the structure has just been opened. The lancet is free; a cut bow
is the most expensive possible way to gain a few hundred millimetres.

## What is measured here

Clearances come from ``entrance.door_envelope``, which works to the rod
*surface* and so reads a little tighter than the rod centrelines: the head
node sits at 0.26287 * D while the free height under it is about 0.254 * D,
the difference being the rod. Outlines, by contrast, are exact rod
centrelines, because a centreline is what gets drawn.
"""

from __future__ import annotations

import math

from . import entrance, geometry

# The doorway is sized to a person carrying something through it -- a chest, a
# table end, a stretcher -- because that is what an event actually does with a
# door. See entrance.TEMPLATES.
DEFAULT_TEMPLATE = "carry"

# A bay counts as tall if it reaches this fraction of the tallest bay. The two
# families sit at roughly 0.254*D and 0.110*D, so anything above half separates
# them cleanly without either number being written down here.
TALL_BAY_FRACTION = 0.5


def bays(data: dict, env: dict | None = None, clearance_mm: float = 0.0) -> list:
    """Every ground-standing opening, tall and low, around the dome.

    A bay is a run of azimuth where the free height is above zero, bounded at
    each end by a rod coming down to the base ring.
    """
    env = env or entrance.door_envelope(data, clearance_mm=clearance_mm)
    envelope = env["envelope_mm"]
    n = len(envelope)
    step = env["bin_width_deg"]
    arc_per_bin = math.radians(step) * env["radius_mm"]
    tallest = max(envelope)

    out = []
    for start, count in entrance._runs_at_least(envelope, 1e-9):
        idx = [(start + k) % n for k in range(count)]
        heights = [envelope[i] for i in idx]
        peak = max(heights)
        apex_bin = idx[heights.index(peak)]
        out.append(
            {
                "kind": "tall" if peak >= TALL_BAY_FRACTION * tallest else "low",
                "centre_azimuth_deg": round(((start + count / 2.0) % n) * step, 3),
                "apex_azimuth_deg": round(apex_bin * step, 3),
                "span_deg": round(count * step, 3),
                "base_width_mm": round(count * arc_per_bin, 1),
                "clear_height_mm": round(peak, 1),
                "open_area_m2": round(sum(heights) * arc_per_bin / 1e6, 3),
            }
        )
    out.sort(key=lambda b: b["centre_azimuth_deg"])
    return out


def bay_clearance(env: dict, bay: dict) -> dict:
    """Free height and widths inside one bay, and nowhere else.

    ``max(envelope)`` is a fact about the whole dome. Once a cut is anything
    but symmetric it can raise some *other* bay, and reading that number as
    the doorway's is how a cut that does nothing for the door gets reported as
    opening it up. Everything about a door has to be measured in its own bay.
    """
    envelope = env["envelope_mm"]
    step = env["bin_width_deg"]
    radius = env["radius_mm"]
    half = bay["span_deg"] / 2.0 + step
    centre = bay["centre_azimuth_deg"]

    inside = [
        i
        for i in range(len(envelope))
        if abs((i * step - centre + 180.0) % 360.0 - 180.0) <= half
    ]
    widths = {}
    for height in (1200.0, 1400.0, 1800.0, 2000.0, 2200.0):
        run = best = 0
        for i in inside:
            run = run + 1 if envelope[i] >= height else 0
            best = max(best, run)
        widths[str(int(height))] = round(
            best * math.radians(step) * radius, 1
        )
    return {
        "clear_height_mm": round(max(envelope[i] for i in inside), 1),
        "widths_mm": widths,
    }


def tall_bays(data: dict, env: dict | None = None, clearance_mm: float = 0.0) -> list:
    return [b for b in bays(data, env, clearance_mm) if b["kind"] == "tall"]


def _azimuth(x: float, y: float) -> float:
    return math.degrees(math.atan2(y, x)) % 360.0


def _angular_gap(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def frame(data: dict, apex_azimuth_deg: float) -> dict:
    """The joints and rods that bound one tall bay.

    Found rather than assumed: the apex is the lowest four-rod node on that
    azimuth, the feet are the two base points either side of it, and each jamb
    is the single rod the apex and one foot have in common.
    """
    apex = None
    for node in data["nodes"]:
        if node["rod_count"] != 4:
            continue
        if _angular_gap(_azimuth(node["x"], node["y"]), apex_azimuth_deg) > 1.0:
            continue
        if apex is None or node["z"] < apex["z"]:
            apex = node
    if apex is None:
        raise ValueError(f"no four-rod node on azimuth {apex_azimuth_deg}")

    feet = sorted(
        data["base_nodes"],
        key=lambda b: _angular_gap(_azimuth(b["x"], b["y"]), apex_azimuth_deg),
    )[:2]
    feet.sort(key=lambda b: _azimuth(b["x"], b["y"]))

    jambs = []
    for foot in feet:
        shared = [r for r in foot["rods"] if r in apex["rods"]]
        if len(shared) != 1:
            raise ValueError(
                f"foot {foot['name']} and node {apex['name']} share {shared}, "
                "expected exactly one rod"
            )
        jambs.append(shared[0])

    return {
        "apex_node": apex["name"],
        "apex_point": [apex["x"], apex["y"], apex["z"]],
        "apex_rods": list(apex["rods"]),
        "feet": [f["name"] for f in feet],
        "foot_points": [[f["x"], f["y"], f["z"]] for f in feet],
        "jamb_rods": jambs,
        "note": (
            "The head of the door is a lashed four-rod node and both feet are "
            "base points, so the opening is framed entirely by joints the "
            "structure already has. No rod is cut."
        ),
    }


def _jamb_polyline(bow, radius: float, start, end, samples: int) -> list:
    """Sample one bow between two points on it, the short way round.

    ``Bow.t_of`` wraps to [0, 360), so a point that sits exactly at t = 0 can
    come back as 359.999... depending on which side of zero the arithmetic
    lands -- and it does, for the base points of some variants. Sweeping from
    the smaller value to the larger would then go the long way round, under
    the ground and over the top. Stepping by the signed short-way difference
    is immune to that, and a jamb is only 36 degrees of arc, so the short way
    is always the right one.
    """
    t0 = bow.t_of(start)
    delta = (bow.t_of(end) - t0 + 180.0) % 360.0 - 180.0
    return [
        list(bow.point(t0 + delta * i / samples, radius))
        for i in range(samples + 1)
    ]


def outline(
    data: dict,
    apex_azimuth_deg: float,
    samples: int = 32,
    frame_info: dict | None = None,
) -> dict:
    """The closed 3D outline of the opening, as rod centrelines.

    Traversed from the left foot up the left jamb to the apex, down the right
    jamb to the right foot, and back along the ground. With a skirt the two
    ends drop straight down by the skirt height first, so the outline is the
    whole hole a person walks through and not just its arched top.
    """
    info = frame_info or frame(data, apex_azimuth_deg)
    radius = data["meta"]["dome_radius"]
    ground_z = data["meta"].get("ground_z", 0.0)
    bows = {b.name: b for b in geometry.build_bows()}

    apex = tuple(info["apex_point"])
    left_foot, right_foot = (tuple(p) for p in info["foot_points"])
    left_rod, right_rod = info["jamb_rods"]

    left = _jamb_polyline(bows[left_rod], radius, left_foot, apex, samples)
    right = _jamb_polyline(bows[right_rod], radius, apex, right_foot, samples)
    # Orient each run so the walk reads left foot -> apex -> right foot.
    if left[0][2] > left[-1][2]:
        left.reverse()
    if right[0][2] < right[-1][2]:
        right.reverse()

    loop = left + right[1:]
    if ground_z < 0.0:
        loop = (
            [[loop[0][0], loop[0][1], ground_z]]
            + loop
            + [[loop[-1][0], loop[-1][1], ground_z]]
        )

    return {
        "apex_azimuth_deg": round(apex_azimuth_deg, 3),
        "point_count": len(loop),
        "closed": True,
        "ground_z": ground_z,
        "points": [[round(c, 6) for c in p] for p in loop],
        "note": (
            "Rod centrelines, not the clear opening: the cover and the frame "
            "sit inside this line by a rod radius. Clearances come from the "
            "envelope instead -- see entrance."
        ),
    }


def _bay_width(meta: dict, clearance_mm: float) -> float:
    """Clear width between two adjacent skirt posts."""
    return meta["base_edge_chord"] - meta["rod_diameter"] - 2.0 * clearance_mm


def _fit_centres(env: dict, bay_width: float, template: list, skirt: float) -> list:
    """Azimuth bins where the template passes, given a skirt of this height.

    ``entrance.template_fits`` deliberately knows nothing about the skirt --
    its envelope starts at the base ring. A doorway through a skirted dome is
    two problems stacked: below the skirt the opening is the straight
    post-to-post bay, above it the dome envelope shifted down by the skirt.
    """
    envelope = env["envelope_mm"]
    n = len(envelope)
    arc_per_bin = math.radians(env["bin_width_deg"]) * env["radius_mm"]

    centres = []
    for centre in range(n):
        ok = True
        for height, half_width in template:
            if height <= skirt:
                if 2.0 * half_width > bay_width:
                    return []  # too wide for the bay at any skirt height
                continue
            reach = int(math.ceil(half_width / arc_per_bin))
            for d in range(-reach, reach + 1):
                if envelope[(centre + d) % n] < height - skirt:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            centres.append(centre)
    return centres


def _places(env: dict, centres: list) -> list:
    """Group acceptable centres into arcs: 'five places, each this wide'."""
    n = len(env["envelope_mm"])
    arc_per_bin = math.radians(env["bin_width_deg"]) * env["radius_mm"]
    wanted = set(centres)
    flags = [1.0 if c in wanted else 0.0 for c in range(n)]
    return [
        {
            "centre_azimuth_deg": round(
                ((start + count / 2.0) % n) * env["bin_width_deg"], 2
            ),
            "slide_mm": round(count * arc_per_bin, 1),
        }
        for start, count in entrance._runs_at_least(flags, 0.5)
    ]



def opening_outline(
    data: dict,
    env: dict,
    bay: dict,
    samples: int = 96,
) -> dict:
    """The clear opening of one bay, traced from the envelope itself.

    ``outline`` follows the two rod centrelines that frame an untouched
    lancet, which is exact but only works while the opening *is* a lancet.
    Once pieces have been cut out the boundary is made of whatever rods are
    left -- on a cut M bay that is a U rod, then L1, then L5, then another U --
    so the general answer is to trace the envelope: at each azimuth take the
    free height, and put the point on the sphere at that height.

    The result is the *clear* opening rather than a centreline, which is what
    a door frame wants anyway.
    """
    radius = data["meta"]["dome_radius"]
    ground_z = data["meta"].get("ground_z", 0.0)
    envelope = env["envelope_mm"]
    count = len(envelope)
    step = env["bin_width_deg"]

    start = bay["centre_azimuth_deg"] - bay["span_deg"] / 2.0
    points = []
    for i in range(samples + 1):
        azimuth = start + bay["span_deg"] * i / samples
        z = envelope[int(round(azimuth / step)) % count]
        # Horizontal radius of the sphere at that height; the two ends sit on
        # the base ring where z is zero.
        horizontal = math.sqrt(max(0.0, radius * radius - z * z))
        a = math.radians(azimuth)
        points.append([horizontal * math.cos(a), horizontal * math.sin(a), z])

    # Close it down to the ground at both ends. The envelope's outermost bins
    # sit just above zero rather than on it, and with a skirt the opening
    # continues below the base ring, so neither end closes itself.
    def foot(point):
        a = math.atan2(point[1], point[0])
        return [radius * math.cos(a), radius * math.sin(a), ground_z]

    points = [foot(points[0])] + points + [foot(points[-1])]

    return {
        "apex_azimuth_deg": bay["apex_azimuth_deg"],
        "point_count": len(points),
        "closed": True,
        "ground_z": ground_z,
        "traced_from": "envelope",
        "points": [[round(c, 6) for c in p] for p in points],
        "note": (
            "The clear opening, to the rod surface -- not a centreline. Traced "
            "from the door envelope, so it stays right whatever is left of the "
            "rods around it."
        ),
    }


def fit_shape(
    data: dict,
    template: list,
    label: str = "shape",
    env: dict | None = None,
    clearance_mm: float = 0.0,
    skirt_mm: float | None = None,
) -> dict:
    """Does this cross-section pass, and with how much room to spare.

    ``template`` is a silhouette as ``(height, half_width)`` pairs, the same
    shape ``entrance.TEMPLATES`` holds. Taking the list rather than a name is
    what lets something that is not a person -- a corridor's tunnel section,
    say -- be measured against the same opening by the same rules.

    ``spare_mm`` is how much taller the same silhouette could be and still
    get through -- the difference between "it fits" and "it fits, and you can
    put a hat on".
    """
    env = env or entrance.door_envelope(data, clearance_mm=clearance_mm)
    meta = data["meta"]
    skirt = meta.get("skirt_height", 0.0) if skirt_mm is None else skirt_mm
    bay_width = _bay_width(meta, clearance_mm)

    centres = _fit_centres(env, bay_width, template, skirt)
    spare = 0.0
    if centres:
        # How much taller the same silhouette could be and still pass. Fitting
        # is monotone in the lift, so bisect rather than march: the scan is the
        # expensive part and this keeps it to a handful of passes.
        lo, hi = 0.0, 2000.0
        while hi - lo > 5.0:
            mid = (lo + hi) / 2.0
            lifted = [(h + mid, w) for h, w in template]
            if _fit_centres(env, bay_width, lifted, skirt):
                lo = mid
            else:
                hi = mid
        spare = lo

    return {
        "template": label,
        "height_mm": max(h for h, _ in template),
        "width_mm": max(w for _, w in template) * 2.0,
        "skirt_mm": skirt,
        "fits": bool(centres),
        "place_count": len(_places(env, centres)) if centres else 0,
        "places": _places(env, centres) if centres else [],
        "spare_mm": round(spare, 1),
    }


def fit(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    env: dict | None = None,
    clearance_mm: float = 0.0,
    skirt_mm: float | None = None,
) -> dict:
    """Does the chosen person-shape pass, and with how much room to spare."""
    return fit_shape(
        data,
        entrance.TEMPLATES[template_name],
        template_name,
        env,
        clearance_mm,
        skirt_mm,
    )


def skirt_for_template(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    clearance_mm: float = 0.0,
    step_mm: float = 10.0,
    limit_mm: float = 3000.0,
) -> float:
    """The shortest skirt that lets ``template_name`` walk in.

    One envelope answers every trial height, so this does not rebuild the
    model per step. Returns 0.0 when the dome already takes the door, and NaN
    when no skirt within ``limit_mm`` is enough.
    """
    env = entrance.door_envelope(data, clearance_mm=clearance_mm)
    template = entrance.TEMPLATES[template_name]
    bay_width = _bay_width(data["meta"], clearance_mm)

    skirt = 0.0
    while skirt <= limit_mm:
        if _fit_centres(env, bay_width, template, skirt):
            return skirt
        skirt += step_mm
    return float("nan")


def admits_env(
    data: dict,
    env: dict,
    clearance_mm: float = 0.0,
    skirt_mm: float | None = None,
) -> list:
    """Which silhouettes get through a given envelope, smallest first."""
    passing = [
        name
        for name in entrance.TEMPLATES
        if fit(data, name, env, clearance_mm, skirt_mm)["fits"]
    ]
    return sorted(passing, key=lambda k: max(h for h, _ in entrance.TEMPLATES[k]))


def admits(
    data: dict,
    env: dict | None = None,
    clearance_mm: float = 0.0,
    skirt_mm: float | None = None,
) -> list:
    """Which of the standard silhouettes get through, smallest first."""
    env = env or entrance.door_envelope(data, clearance_mm=clearance_mm)
    return admits_env(data, env, clearance_mm, skirt_mm)


def _eligible_bays(data, env, level, clearance_mm):
    """The bays a door of this cut level can go in.

    A portal is a low bay opened up; everything else is a tall bay. That is
    not a preference -- the cuts are different cuts, and each only makes sense
    against the bay it was worked out for.
    """
    if level == "portal":
        return low_bays(data, env, clearance_mm)
    return tall_bays(data, env, clearance_mm)


def _aim(candidates: list, facing: float | None) -> dict:
    """The bay a door asked for: nearest to ``facing``, else the first.

    ``None`` keeps the behaviour every variant had before a dome could have
    two doors -- take the first eligible bay by azimuth.
    """
    if not candidates:
        raise ValueError("no eligible bay found; this dome has nowhere to put a door")
    if facing is None:
        return candidates[0]
    return min(
        candidates, key=lambda b: _angular_gap(b["centre_azimuth_deg"], facing)
    )


def cuts_for(data: dict, level: str, target: dict) -> dict:
    """The spans one door takes out, at the bay it was aimed at."""
    if level == "none":
        return {}
    if level == "portal":
        return portal_cut(data, target)
    info = frame(data, target["apex_azimuth_deg"])
    return CUT_LEVELS[level](data, info) or {}


def merge_cuts(every: list) -> dict:
    """Every door's cuts, as one set of removed spans per rod.

    Two doors on one dome are not two independent questions. A cut takes rod
    out of the envelope everywhere, not only in front of the door that asked
    for it, so the opening each one leaves has to be measured after all of
    them are made.
    """
    out: dict = {}
    for cuts in every:
        for rod, spans in cuts.items():
            out.setdefault(rod, []).extend(tuple(s) for s in spans)
    for rod, spans in out.items():
        spans.sort()
        merged = [list(spans[0])]
        for lo, hi in spans[1:]:
            if lo <= merged[-1][1] + 1e-9:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        out[rod] = [tuple(s) for s in merged]
    return out


def removed_spans(data: dict) -> dict:
    """Every span any doorway took out of any bow, keyed by rod.

    Read off the rods rather than off the doors, because a rod carries the
    union and a door carries only its own share -- and once a dome has more
    than one door those stop being the same thing.
    """
    out = {}
    for rod in data.get("rods", []):
        spans = rod.get("cut_spans_deg")
        if spans:
            out[rod["name"]] = [tuple(s) for s in spans]
    return out


def landless_bows(data: dict) -> list:
    """Bows that no longer reach the ground, because cuts took both ends.

    One door cannot do this -- its two jamb pieces come off two different
    bows. Two doors can, and the result is a bow that is still continuous and
    still carries load but stands on nothing: it hangs in the lattice between
    its crossings. Not an error, and not something a reader should have to
    notice for themselves.
    """
    out = []
    for rod in data.get("rods", []):
        spans = rod.get("cut_spans_deg") or []
        starts = any(lo <= 1e-6 for lo, _ in spans)
        ends = any(hi >= 180.0 - 1e-6 for _, hi in spans)
        if starts and ends:
            out.append(rod["name"])
    return out


def doors_on(data: dict) -> list:
    """Every doorway on a built model, however old the model is."""
    doors = data.get("doorways")
    if doors:
        return doors
    one = data.get("doorway")
    return [one] if one else []


def place_all(
    data: dict,
    doors,
    clearance_mm: float = 0.0,
    samples: int = 32,
) -> list:
    """Every doorway on one dome, each measured on the dome all of them leave.

    Doors are aimed rather than placed: a door can only sit in a bay, there
    are ten of them, and the eligible ones depend on the cut. Each door takes
    the eligible bay nearest the azimuth it asked for, and the record says
    where it actually landed.
    """
    plain = entrance.door_envelope(data, clearance_mm=clearance_mm)

    resolved = []
    for index, door in enumerate(doors):
        level = door.cut
        if level not in CUT_LEVELS:
            raise ValueError(f"unknown cut level {level!r}; know {sorted(CUT_LEVELS)}")
        target = _aim(_eligible_bays(data, plain, level, clearance_mm), door.facing)
        resolved.append((door, level, target))

    # Two doors in one bay is a configuration mistake rather than a very wide
    # door, and it would quietly cut the same rod twice.
    taken: dict = {}
    for index, (door, level, target) in enumerate(resolved):
        key = round(target["centre_azimuth_deg"], 3)
        if key in taken:
            raise ValueError(
                f"doors {taken[key]} and {index} both land in the bay at "
                f"{key} deg; a dome has ten bays and each holds one door"
            )
        taken[key] = index

    plain_tall = len(tall_bays(data, plain, clearance_mm))
    every = [cuts_for(data, level, target) for _, level, target in resolved]
    union = merge_cuts(every)
    env = (
        entrance.door_envelope(data, clearance_mm=clearance_mm, removed=union)
        if union
        else plain
    )

    out = []
    for (door, level, target), cuts in zip(resolved, every):
        out.append(
            _record(
                data, door, level, target, cuts or None, env, clearance_mm,
                samples, plain_tall,
            )
        )
    return out


def _record(data, door, level, target, cuts, env, clearance_mm, samples,
            bay_count) -> dict:
    """One doorway, measured on the finished dome."""
    wanted = target["centre_azimuth_deg"]
    if level == "portal":
        bay = min(
            bays(data, env, clearance_mm),
            key=lambda b: _angular_gap(b["centre_azimuth_deg"], wanted),
        )
        info = None
    else:
        info = frame(data, target["apex_azimuth_deg"])
        if cuts:
            # A cut can change where the bays fall, so pick the one still
            # centred on this door rather than whichever comes first.
            bay = min(
                tall_bays(data, env, clearance_mm),
                key=lambda b: _angular_gap(b["centre_azimuth_deg"], wanted),
            )
        else:
            bay = target

    skirt = data["meta"].get("skirt_height", 0.0)
    return {
        "bay": bay,
        "bay_count": bay_count,
        "facing_deg": door.facing,
        "landed_deg": bay["centre_azimuth_deg"],
        "template": door.template,
        "frame": info,
        "cut": (
            {
                "level": level,
                "spans": {r: [list(s) for s in v] for r, v in cuts.items()},
                "cost": cut_pieces(data, cuts),
                "note": (
                    "The head node stops being a crossing and becomes a place "
                    "where rod ends meet, which is a different connector from "
                    "the one in docs/fan-node-v2.md. At level 'head' nothing "
                    "passes through it at all: four bows converge there and "
                    "every one of them terminates, so the node is held by no "
                    "continuous member and wants a lintel or a tie. Whether "
                    "it stands without one is statics, not geometry."
                ),
            }
            if cuts
            else None
        ),
        "outline": (
            opening_outline(data, env, bay)
            if cuts
            else outline(data, bay["apex_azimuth_deg"], samples, info)
        ),
        "clearance_mm": clearance_mm,
        "skirt_height_mm": skirt,
        "opening_height_mm": round(bay["clear_height_mm"] + skirt, 1),
        "in_bay": bay_clearance(env, bay),
        "door": fit(data, door.template, env, clearance_mm),
        # Everything that gets through, largest last. Naming only the chosen
        # silhouette hides both failures and headroom: it cannot show that a
        # dome admits nothing, nor that it would take much more.
        "admits": admits_env(data, env, clearance_mm),
        "note": (
            "One of five identical tall bays; any of them can be the door, and "
            "a second one opposite gives a through-draught without changing "
            "anything structurally."
        ),
    }


def place(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    clearance_mm: float = 0.0,
    samples: int = 32,
    cut: str = "none",
) -> dict:
    """The chosen doorway, ready to serialise into the model.

    One door, placed where this dome puts its first one -- which is what every
    variant asked for before a dome could have several. ``place_all`` is the
    general form; this is it with a single unaimed door, and returns the same
    record.

    With ``cut`` the two jamb pieces are taken out and everything reported
    afterwards describes the opening that leaves. The uncut lancet is still
    reported as ``frame``, because that is what was cut, and the cut itself
    is reported as ``cut`` with its cost.
    """
    from .config import Door

    level = "none" if cut in (None, False) else ("jambs" if cut is True else cut)
    if level not in CUT_LEVELS:
        raise ValueError(f"unknown cut level {cut!r}; know {sorted(CUT_LEVELS)}")
    doors = (Door(cut=level, facing=None, template=template_name),)
    return place_all(data, doors, clearance_mm, samples)[0]


# ---------------------------------------------------------------------------
# Cutting the door open
#
# Every bow is divided by its crossings into pieces, and each piece ends at a
# lashed node -- so a cut is made at a joint, not in the middle of a span. That
# makes enlarging the doorway by removing pieces a real option rather than
# vandalism, but the pieces are not equal:
#
#   an END piece   the bow gets shorter and still runs unbroken from one
#                  base point to a node. Nothing is severed.
#   a MIDDLE piece the bow becomes two disconnected bows. That is a different
#                  structure, not a modified one.
#
# The doorway's own jambs are end pieces. That is the whole reason this is
# worth measuring: the obvious cut is also the cheap one.
# ---------------------------------------------------------------------------


def jamb_cut(data: dict, frame_info: dict | None = None) -> dict:
    """The two end pieces that form the doorway's jambs.

    Removing these opens the lancet out to the full bay below its head node.
    Both are end pieces, so neither bow is severed: each simply starts at the
    head node instead of at a base point, a fifth shorter.
    """
    bay = tall_bays(data)[0]
    info = frame_info or frame(data, bay["apex_azimuth_deg"])
    bows = {b.name: b for b in geometry.build_bows()}
    apex = tuple(info["apex_point"])

    spans = {}
    for rod, foot in zip(info["jamb_rods"], info["foot_points"]):
        bow = bows[rod]
        t_foot = bow.t_of(tuple(foot))
        t_apex = bow.t_of(apex)
        # t_of wraps, and a base point can read as 360 rather than 0; snap it.
        t_foot = 0.0 if min(t_foot, 360.0 - t_foot) < 1e-3 else t_foot
        spans[rod] = [(min(t_foot, t_apex), max(t_foot, t_apex))]
    return spans


def _crossing_ts(data: dict, rod: str) -> list:
    """Where the crossings fall along one bow, in its own parameter."""
    bows = {b.name: b for b in geometry.build_bows()}
    bow = bows[rod]
    ts = []
    for node in data["nodes"]:
        if rod not in node["rods"]:
            continue
        t = bow.t_of((node["x"], node["y"], node["z"])) % 360.0
        if t > 180.0 + 1e-6:
            t -= 360.0
        ts.append(round(t, 4))
    return sorted(set(ts))


def head_cut(data: dict, frame_info: dict | None = None) -> dict:
    """The jambs, plus the two pieces that still cross the opening above them.

    Once the jambs are gone the bay is bounded by the *other* two rods through
    the head node -- the L pair -- sloping down across the opening. Removing
    their pieces is the only way further, and it is a different kind of cut:
    those are middle pieces, so each of those two bows becomes two bows.

    Worse, it leaves the head node with nothing passing through it. All four
    rods then terminate there, and a node that was a crossing becomes the
    converging apex of four bows with no continuous member holding it. That
    is a structural question this file cannot answer -- see cut_pieces for
    what it can say.
    """
    bay = tall_bays(data)[0]
    info = frame_info or frame(data, bay["apex_azimuth_deg"])
    spans = jamb_cut(data, info)

    bows = {b.name: b for b in geometry.build_bows()}
    radius = data["meta"]["dome_radius"]
    apex = tuple(info["apex_point"])
    half = bay["span_deg"] / 2.0
    centre = bay["centre_azimuth_deg"]

    def clearance(cuts):
        env = entrance.door_envelope(data, removed=cuts)
        return bay_clearance(env, bay)["clear_height_mm"]

    baseline = clearance(spans)
    for rod in info["apex_rods"]:
        if rod in spans:
            continue
        bow = bows[rod]
        t_apex = bow.t_of(apex) % 360.0
        if t_apex > 180.0 + 1e-6:
            t_apex -= 360.0
        ts = [0.0] + _crossing_ts(data, rod) + [180.0]
        # Two pieces meet the head node. Only one of them lies across this
        # doorway; the other runs away over the dome, and removing it would
        # cost rod and open a bay nobody asked about. Decide by measurement --
        # keep the piece whose removal actually raises *this* bay.
        best = None
        for lo, hi in zip(ts, ts[1:]):
            if abs(lo - t_apex) > 1e-3 and abs(hi - t_apex) > 1e-3:
                continue
            trial = {r: list(v) for r, v in spans.items()}
            trial.setdefault(rod, []).append((lo, hi))
            gain = clearance(trial) - baseline
            if gain > 1e-6 and (best is None or gain > best[0]):
                best = (gain, (lo, hi))
        if best is not None:
            spans.setdefault(rod, []).append(best[1])
    return spans


# How far to open the door, by name. The order is the order of cost:
# "jambs" severs nothing, "head" severs two bows and strands the head node.
CUT_LEVELS = {
    "none": lambda data, info=None: {},
    "jambs": jamb_cut,
    "head": head_cut,
    # A door in a low bay instead of a tall one: two U jambs and a level L
    # lintel, cleared of the crossing that fills it. Costs what the jamb cut
    # costs and severs nothing, and gives a taller opening.
    "portal": lambda data, info=None: portal_cut(data),
}


def low_bays(data: dict, env: dict | None = None, clearance_mm: float = 0.0) -> list:
    return [b for b in bays(data, env, clearance_mm) if b["kind"] == "low"]


def portal_cut(data: dict, bay: dict | None = None) -> dict:
    """Open a low bay into a portal, by clearing the crossing that fills it.

    The five *low* bays are shaped quite differently from the tall ones. Each
    is bounded by two U bows rising from adjacent base points and, across the
    top, one L bow running nearly level between two crossings at the same
    height. That is a doorway with a **lintel** rather than a pointed arch --
    b8 - N18 - N19 - b9 on M -- and its head sits at 0.3009 * D, above the tall
    bay's 0.2629 and high enough to walk under on a bare 6 m dome.

    What fills it is a second pair of L bows crossing low in the middle. Each
    gives up its end piece **and the piece past that crossing**: stopping at
    the crossing leaves the next piece still slanting across the opening,
    which is exactly why removing only its legs changes nothing. Both spans
    run contiguously to a bow end, so neither bow is severed -- each simply
    starts higher up, the same bargain the jamb cut makes.
    """
    env = entrance.door_envelope(data)
    bay = bay or low_bays(data, env)[0]
    centre = bay["centre_azimuth_deg"]

    # The crossing that fills the bay: the lowest node on the bay's azimuth.
    filler = None
    for node in data["nodes"]:
        if _angular_gap(_azimuth(node["x"], node["y"]), centre) > 1.0:
            continue
        if filler is None or node["z"] < filler["z"]:
            filler = node
    if filler is None:
        raise ValueError(f"no crossing fills the low bay at {centre} deg")

    bows = {b.name: b for b in geometry.build_bows()}
    point = (filler["x"], filler["y"], filler["z"])

    spans: dict = {}
    for rod in filler["rods"]:
        bow = bows[rod]
        t_node = bow.t_of(point) % 360.0
        if t_node > 180.0 + 1e-6:
            t_node -= 360.0
        ts = _crossing_ts(data, rod)
        # _crossing_ts rounds, so the node's own entry can land a whisker above
        # the unrounded parameter it came from. A degree of slack is far below
        # the 15-22 degree spacing of real crossings and well above that.
        if t_node <= 90.0:
            beyond = [t for t in ts if t > t_node + 1.0]
            spans[rod] = [(0.0, beyond[0])]
        else:
            beyond = [t for t in ts if t < t_node - 1.0]
            spans[rod] = [(beyond[-1], 180.0)]
    return spans


def cut_pieces(data: dict, cuts: dict) -> dict:
    """What a set of cuts costs: rod removed, and what it severs."""
    radius = data["meta"]["dome_radius"]
    ends = []
    severed = []
    removed = 0.0
    for rod, spans in cuts.items():
        for lo, hi in spans:
            removed += (hi - lo) / 180.0 * math.pi * radius
            if lo <= 1e-6 or hi >= 180.0 - 1e-6:
                ends.append(rod)
            else:
                severed.append(rod)
    # A severed bow is not debris: each half still runs from a base point to a
    # node, exactly like a bow whose end piece was removed. What is lost is
    # continuity *through* the node in the middle, and that is the thing worth
    # naming rather than the word "severed".
    orphaned = _nodes_with_nothing_through(data, cuts)
    return {
        "rod_removed_mm": round(removed, 1),
        "rod_removed_fraction": round(removed / data["meta"]["total_rod_length"], 4),
        "end_pieces": sorted(ends),
        "severed_bows": sorted(set(severed)),
        "severs_nothing": not severed,
        "nodes_with_nothing_through": orphaned,
        "note": (
            "Each half of a severed bow still runs from a base point to a "
            "node. What the cut costs is continuity through the node between "
            "them -- and a node where every rod terminates is held by no "
            "continuous member at all. Whether that stands up is statics, not "
            "geometry."
        ),
    }


def feet_released(data: dict, cuts: dict) -> dict:
    """Which base points lose a bow end to a cut, and which bow.

    A bow runs foot to foot, so a removed piece that reaches ``t = 0`` takes
    its end off ``foot_a`` and one reaching ``t = 180`` off ``foot_b``. Those
    base points now gather one fewer arm than the other eight, and a base hub
    drawn for three of them does not fit two.

    On the portal cut this is never incidental: the two feet it frees are the
    two the doorway stands between, which is the whole point of cutting there.
    """
    feet = {b["index"]: b["name"] for b in data["base_nodes"]}
    out: dict = {}
    for rod in data["rods"]:
        for lo, hi in cuts.get(rod["name"], ()):
            if lo <= 1e-6:
                out.setdefault(feet[rod["foot_a"]], []).append(rod["name"])
            if hi >= 180.0 - 1e-6:
                out.setdefault(feet[rod["foot_b"]], []).append(rod["name"])
    return {name: sorted(set(rods)) for name, rods in sorted(out.items())}


def terminations(data: dict, cuts: dict) -> list:
    """Where each cut bow now begins: the crossing it stops at, and against what.

    A bow that used to run through a crossing now ends in it. The joint there
    holds a rod END against a rod, which is a different part from the clamp
    that holds two rods against each other, and it needs to know which of the
    two is the one that stops.

    ``approach`` says which way the surviving bow arrives in the bow's own
    parameter: ``+`` means it runs on towards 180, ``-`` back towards 0. That
    is what tells the part which side of the channel is open and which is the
    wall the rod end bears on.
    """
    out = []
    for rod, spans in sorted(cuts.items()):
        for lo, hi in spans:
            if lo <= 1e-6:
                t_end, approach = hi, "+"
            elif hi >= 180.0 - 1e-6:
                t_end, approach = lo, "-"
            else:
                # A span in the middle of a bow severs it and leaves two ends,
                # neither of which is what the portal cut makes. No level in
                # CUT_LEVELS produces one today; if one ever does, it wants
                # its own answer rather than a guess from this one.
                continue
            match = None
            for c in data["crossings"]:
                for side in ("a", "b"):
                    if c[f"rod_{side}"] != rod:
                        continue
                    if abs(c[f"t_{side}_deg"] - t_end) > 1e-3:
                        continue
                    match = (c, side)
            if match is None:
                raise ValueError(
                    f"{rod} is cut to t={t_end}, which is not a crossing; "
                    "a bow end in mid-span has nothing to be clamped to"
                )
            crossing, side = match
            other = "b" if side == "a" else "a"
            out.append(
                {
                    "node": crossing["node"],
                    "rod": rod,
                    "other_rod": crossing[f"rod_{other}"],
                    "t_deg": round(t_end, 6),
                    "approach": approach,
                    "crossing_angle_deg": crossing["angle_deg"],
                    "ends_above": crossing["rod_above"] == rod,
                    "x": crossing["x"],
                    "y": crossing["y"],
                    "z": crossing["z"],
                }
            )
    return out


def _nodes_with_nothing_through(data: dict, cuts: dict) -> list:
    """Nodes left with every rod terminating on them and none passing through.

    A crossing is held by the members that run through it. Cut enough away and
    it stops being a crossing and becomes a free apex where four rod ends meet,
    which is a different structural object and a different connector.
    """
    bows = {b.name: b for b in geometry.build_bows()}
    stranded = []
    for node in data["nodes"]:
        point = (node["x"], node["y"], node["z"])
        through = 0
        for rod in node["rods"]:
            bow = bows[rod]
            t = bow.t_of(point) % 360.0
            if t > 180.0 + 1e-6:
                t -= 360.0
            spans = cuts.get(rod, ())
            # The rod passes through unless a removed piece stops at this point
            # or the node is an end of the bow itself.
            ends_here = t <= 1e-3 or t >= 180.0 - 1e-3
            for lo, hi in spans:
                if abs(lo - t) < 1e-3 or abs(hi - t) < 1e-3:
                    ends_here = True
            if not ends_here:
                through += 1
        if node["rods"] and through == 0:
            stranded.append(node["name"])
    return stranded


def with_cut(
    data: dict,
    cuts: dict,
    template_name: str = DEFAULT_TEMPLATE,
    clearance_mm: float = 0.0,
) -> dict:
    """What the doorway becomes once those pieces are gone."""
    env = entrance.door_envelope(data, clearance_mm=clearance_mm, removed=cuts)
    return {
        "cuts": {rod: [list(s) for s in spans] for rod, spans in cuts.items()},
        "cost": cut_pieces(data, cuts),
        "clear_height_mm": round(max(env["envelope_mm"]), 1),
        "widths_mm": {
            str(h): entrance.widest_at_height(data, float(h), env)["widest_mm"]
            for h in (1200, 1400, 1800, 2000, 2200)
        },
        "admits": admits_env(data, env, clearance_mm),
        "door": fit(data, template_name, env, clearance_mm),
    }


def analyse(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    clearance_mm: float = 0.0,
    cut: str | None = None,
) -> dict:
    """``cut`` defaults to whatever the variant asked for, so the report and
    the serialised model can never disagree about which dome they describe."""
    if cut is None:
        cut = data["meta"].get("door_cut", "none")
    env = entrance.door_envelope(data, clearance_mm=clearance_mm)
    meta = data["meta"]
    all_bays = bays(data, env, clearance_mm)
    return {
        "variant": meta["variant"],
        "diameter_mm": meta["dome_diameter"],
        "skirt_height_mm": meta.get("skirt_height", 0.0),
        "bay_count": len(all_bays),
        "tall_bay_count": sum(1 for b in all_bays if b["kind"] == "tall"),
        "bays": all_bays,
        "doorway": place(data, template_name, clearance_mm, cut=cut),
    }


def format_doors(data: dict) -> str:
    """Every door on a built dome, and where each one landed.

    The single-door report says everything about one opening; this says which
    openings a dome has, which way each faces, and what each one cost. A door
    that asked for an azimuth and got a bay two degrees away is worth seeing,
    because a bay is where a door can go and the wish is only a wish.
    """
    doors = doors_on(data)
    meta = data["meta"]
    lines = [
        f"--- {meta['variant']} doors  ({len(doors)} on a dome with "
        f"{len(bays(data))} bays)"
    ]
    for i, d in enumerate(doors):
        bay = d["bay"]
        cut = d.get("cut") or {}
        asked = d.get("facing_deg")
        aim = (
            f"asked {asked:.0f} deg, landed {bay['centre_azimuth_deg']:.1f}"
            if asked is not None
            else f"placed at {bay['centre_azimuth_deg']:.1f} deg"
        )
        lines.append(
            f"  {i}  {aim}  --  {bay['kind']} bay, clear "
            f"{bay['clear_height_mm']:.0f} mm, {bay['open_area_m2']:.2f} m2"
        )
        lines.append(
            f"     cut {cut.get('level', 'none')}"
            + (
                f", {cut['cost']['rod_removed_mm'] / 1000.0:.1f} m of rod "
                f"({cut['cost']['rod_removed_fraction'] * 100:.1f}%), "
                + (
                    "severs nothing"
                    if cut["cost"]["severs_nothing"]
                    else "SEVERS " + ", ".join(cut["cost"]["severed_bows"])
                )
                if cut
                else " -- nothing removed, the bay is the opening"
            )
        )
        lines.append(
            f"     sized to {d.get('template') or DEFAULT_TEMPLATE}; "
            f"admits {', '.join(d['admits']) or 'nothing'}"
        )
    landless = landless_bows(data)
    if landless:
        lines.append(
            "  no longer standing on the ground: "
            + ", ".join(landless)
            + " -- cut at both ends, so still continuous and still loaded, "
            "but held only by its crossings"
        )
    removed = removed_spans(data)
    if removed:
        lines.append(
            "  rod taken out, all doors together: "
            + ", ".join(
                f"{rod} " + " ".join(f"{lo:.0f}-{hi:.0f}" for lo, hi in spans)
                for rod, spans in sorted(removed.items())
            )
        )
    return "\n".join(lines)


def format_analysis(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    clearance_mm: float = 0.0,
    cut: str | None = None,
) -> str:
    a = analyse(data, template_name, clearance_mm, cut)
    d = a["doorway"]
    bay = d["bay"]
    info = d["frame"]
    door = d["door"]
    diameter = a["diameter_mm"]
    low = a["bay_count"] - a["tall_bay_count"]
    lines = [
        f"--- {a['variant']} doorway  "
        f"(diameter {diameter:.0f} mm, skirt {a['skirt_height_mm']:.0f} mm)",
        f"  {a['bay_count']} ground openings: {a['tall_bay_count']} tall, {low} low",
        f"  door bay centred {bay['centre_azimuth_deg']:.1f} deg, "
        f"{bay['span_deg']:.1f} deg wide "
        f"({bay['base_width_mm']:.0f} mm along the base ring), "
        f"highest at {bay['apex_azimuth_deg']:.1f} deg",
        f"  clear height {bay['clear_height_mm']:.0f} mm dome "
        f"+ {a['skirt_height_mm']:.0f} mm skirt "
        f"= {d['opening_height_mm']:.0f} mm",
        f"  open area {bay['open_area_m2']:.2f} m2  "
        f"({bay['clear_height_mm'] / diameter:.4f} of D high, "
        f"{bay['open_area_m2'] * 1e6 / diameter ** 2:.4f} of D^2 in area)",
        (
            f"  framed by rods {info['jamb_rods'][0]} and {info['jamb_rods'][1]}, "
            f"meeting at lashed node {info['apex_node']}; "
            f"feet at {info['feet'][0]} and {info['feet'][1]}"
            if info
            else "  a portal in a low bay: two U jambs and an L bow lying "
                 "level across the top, no pointed head"
        ),
        *(
            [
                f"  CUT ({d['cut']['level']}): "
                + ", ".join(
                    f"{rod} {lo:.0f}-{hi:.0f} deg"
                    for rod, spans in d["cut"]["spans"].items()
                    for lo, hi in spans
                )
                + f"  ({d['cut']['cost']['rod_removed_mm'] / 1000:.1f} m, "
                + f"{d['cut']['cost']['rod_removed_fraction'] * 100:.1f}% of rod, "
                + (
                    "severs nothing)"
                    if d["cut"]["cost"]["severs_nothing"]
                    else "SEVERS " + ", ".join(d["cut"]["cost"]["severed_bows"]) + ")"
                )
                + (
                    "\n  NOTHING PASSES THROUGH "
                    + ", ".join(d["cut"]["cost"]["nodes_with_nothing_through"])
                    + " -- the head is held by no continuous member"
                    if d["cut"]["cost"]["nodes_with_nothing_through"]
                    else ""
                )
            ]
            if d.get("cut")
            else []
        ),
        "  clear width in the bay: "
        + ", ".join(
            f"{h} mm high: {w:.0f}" for h, w in d["in_bay"]["widths_mm"].items()
        ),
        "  admits: " + (", ".join(d["admits"]) if d["admits"] else "nothing"),
        f"  {door['template']} template "
        f"({door['width_mm']:.0f} x {door['height_mm']:.0f} mm): "
        + (
            f"fits in {door['place_count']} places, "
            f"slide {max(p['slide_mm'] for p in door['places']):.0f} mm"
            if door["fits"]
            else "DOES NOT FIT -- needs a taller skirt"
        ),
    ]
    return "\n".join(lines)
