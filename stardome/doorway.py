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


def fit(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    env: dict | None = None,
    clearance_mm: float = 0.0,
    skirt_mm: float | None = None,
) -> dict:
    """Does the chosen person-shape pass, and with how much room to spare.

    ``spare_mm`` is how much taller the same silhouette could be and still
    get through -- the difference between "it fits" and "it fits, and you can
    put a hat on".
    """
    env = env or entrance.door_envelope(data, clearance_mm=clearance_mm)
    template = entrance.TEMPLATES[template_name]
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
        "template": template_name,
        "height_mm": max(h for h, _ in template),
        "width_mm": max(w for _, w in template) * 2.0,
        "skirt_mm": skirt,
        "fits": bool(centres),
        "place_count": len(_places(env, centres)) if centres else 0,
        "places": _places(env, centres) if centres else [],
        "spare_mm": round(spare, 1),
    }


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


def place(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    clearance_mm: float = 0.0,
    samples: int = 32,
) -> dict:
    """The chosen doorway, ready to serialise into the model."""
    env = entrance.door_envelope(data, clearance_mm=clearance_mm)
    tall = tall_bays(data, env, clearance_mm)
    if not tall:
        raise ValueError("no tall bay found; this dome has nowhere to put a door")
    bay = tall[0]
    info = frame(data, bay["apex_azimuth_deg"])
    skirt = data["meta"].get("skirt_height", 0.0)
    return {
        "bay": bay,
        "bay_count": len(tall),
        "frame": info,
        "outline": outline(data, bay["apex_azimuth_deg"], samples, info),
        "clearance_mm": clearance_mm,
        "skirt_height_mm": skirt,
        "opening_height_mm": round(bay["clear_height_mm"] + skirt, 1),
        "door": fit(data, template_name, env, clearance_mm),
        "note": (
            "One of five identical tall bays; any of them can be the door, and "
            "a second one opposite gives a through-draught without changing "
            "anything structurally."
        ),
    }


def analyse(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    clearance_mm: float = 0.0,
) -> dict:
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
        "doorway": place(data, template_name, clearance_mm),
    }


def format_analysis(
    data: dict,
    template_name: str = DEFAULT_TEMPLATE,
    clearance_mm: float = 0.0,
) -> str:
    a = analyse(data, template_name, clearance_mm)
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
        f"  door bay at azimuth {bay['apex_azimuth_deg']:.1f} deg, "
        f"{bay['span_deg']:.1f} deg wide "
        f"({bay['base_width_mm']:.0f} mm along the base ring)",
        f"  clear height {bay['clear_height_mm']:.0f} mm dome "
        f"+ {a['skirt_height_mm']:.0f} mm skirt "
        f"= {d['opening_height_mm']:.0f} mm",
        f"  open area {bay['open_area_m2']:.2f} m2  "
        f"({bay['clear_height_mm'] / diameter:.4f} of D high, "
        f"{bay['open_area_m2'] * 1e6 / diameter ** 2:.4f} of D^2 in area)",
        f"  framed by rods {info['jamb_rods'][0]} and {info['jamb_rods'][1]}, "
        f"meeting at lashed node {info['apex_node']}; "
        f"feet at {info['feet'][0]} and {info['feet'][1]}",
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
