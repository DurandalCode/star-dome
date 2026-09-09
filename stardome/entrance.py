"""Where a doorway fits, and how big it can be.

The Star Dome has no door. It has fifteen rods and whatever gaps they leave,
and an entrance has to live in one of those gaps without cutting a member. This
answers that by measurement rather than by eye, which is what Milestone 2's
entrance-clearance item asks for.

## The method

Unroll the dome. Every rod is a curve on a sphere; map each of its points to
``(azimuth, z)`` and the whole structure becomes a flat elevation, 360 degrees
wide. In that picture a ground-standing doorway is an axis-aligned rectangle
with its bottom edge on z = 0.

For each azimuth, the height available from the ground is the lowest a rod
reaches at that azimuth, less the rod's own radius. That gives a **door
envelope**: a histogram of free height against azimuth. The widest doorway of
a given height is then the longest run of the histogram at or above it, and the
largest doorway by area is the classic largest-rectangle-under-a-histogram
problem, solved exactly rather than sampled.

Widths are reported as arc length along the base circle, because that is what
a door frame and a cover panel are cut to.

## What this does and does not tell you

It is the opening in the *structure*, measured to the rod surface. It says
nothing about the cover, which has to be cut and hemmed around the same gap, or
about what happens to the load paths when a bay is left unbraced by fabric, or
about a door frame's own stiffness.
"""

from __future__ import annotations

import math

from . import geometry

# Doorway heights worth reporting: a low crawl-through, a duck-under, a
# comfortable pass, and a clear pass for someone tall in costume.
STANDARD_HEIGHTS_MM = (1200.0, 1600.0, 1800.0, 2000.0)

DEFAULT_BINS = 1440  # a quarter of a degree
SAMPLES_PER_BOW = 2000


def door_envelope(
    data: dict,
    bins: int = DEFAULT_BINS,
    clearance_mm: float = 0.0,
    removed: dict | None = None,
) -> dict:
    """Free height from the ground, per azimuth bin.

    ``clearance_mm`` is kept clear of every rod surface on top of the rod's own
    radius -- knuckles, a cover hem, a door frame.

    ``removed`` maps a bow name to spans of its parameter t that are not there:
    ``{"G1": [(0.0, 36.0)]}`` measures the dome as if that piece of that bow
    had been cut out. Every bow is divided by its crossings into pieces, and
    cutting one out is the obvious way to enlarge a doorway -- so the obvious
    question is what that buys, and answering it needs an envelope that can be
    computed with pieces missing.
    """
    removed = removed or {}
    meta = data["meta"]
    radius = meta["dome_radius"]
    rod_radius = meta["rod_diameter"] / 2.0
    keep_out = rod_radius + clearance_mm

    step = 360.0 / bins
    # A rod of finite thickness blocks a spread of azimuth, not a single line.
    # At the base the spread is widest in angle terms, so use the base radius:
    # that is conservative higher up, where the horizontal radius is smaller
    # and the same rod covers more degrees -- so widen by the larger of the two.
    spread_bins = max(1, int(math.ceil(math.degrees(keep_out / radius) / step)) + 1)

    ceiling = meta.get("dome_height_measured", radius)
    envelope = [ceiling] * bins

    for bow in geometry.build_bows():
        gaps = removed.get(bow.name, ())
        for i in range(SAMPLES_PER_BOW + 1):
            t = 180.0 * i / SAMPLES_PER_BOW
            if any(lo <= t <= hi for lo, hi in gaps):
                continue
            x, y, z = bow.point(t, radius)
            if z < 0.0:
                continue
            blocked = max(0.0, z - keep_out)
            centre = int((math.degrees(math.atan2(y, x)) % 360.0) / step)
            for d in range(-spread_bins, spread_bins + 1):
                b = (centre + d) % bins
                if blocked < envelope[b]:
                    envelope[b] = blocked

    return {
        "bins": bins,
        "bin_width_deg": step,
        "radius_mm": radius,
        "clearance_mm": clearance_mm,
        "keep_out_mm": keep_out,
        "envelope_mm": envelope,
    }


def _runs_at_least(envelope: list, height: float) -> list:
    """Circular runs of bins whose free height reaches ``height``."""
    n = len(envelope)
    if all(v >= height for v in envelope):
        return [(0, n)]
    runs = []
    start = None
    # Rotate so the scan starts on a blocked bin: then no run wraps except one,
    # and that one is stitched below.
    offset = next(i for i, v in enumerate(envelope) if v < height)
    for k in range(n):
        i = (offset + k) % n
        if envelope[i] >= height:
            if start is None:
                start = k
        elif start is not None:
            runs.append(((offset + start) % n, k - start))
            start = None
    if start is not None:
        runs.append(((offset + start) % n, n - start))
    return runs


def widest_at_height(data: dict, height_mm: float, env: dict | None = None) -> dict:
    """The widest ground-standing opening that clears ``height_mm``."""
    env = env or door_envelope(data)
    envelope = env["envelope_mm"]
    radius = env["radius_mm"]
    arc_per_bin = math.radians(env["bin_width_deg"]) * radius

    runs = _runs_at_least(envelope, height_mm)
    openings = []
    for start, count in runs:
        centre_bin = (start + count / 2.0) % len(envelope)
        openings.append(
            {
                "width_mm": round(count * arc_per_bin, 1),
                "centre_azimuth_deg": round(centre_bin * env["bin_width_deg"], 3),
                "start_azimuth_deg": round(start * env["bin_width_deg"], 3),
                "bins": count,
            }
        )
    openings.sort(key=lambda o: -o["width_mm"])
    return {
        "height_mm": height_mm,
        "opening_count": len(openings),
        "widest_mm": openings[0]["width_mm"] if openings else 0.0,
        "openings": openings,
    }


def largest_doorway(data: dict, env: dict | None = None) -> dict:
    """The biggest ground-standing rectangle by area, exactly.

    Largest rectangle under a histogram, on a circular histogram: the array is
    doubled and any candidate wider than one turn is discarded.
    """
    env = env or door_envelope(data)
    envelope = env["envelope_mm"]
    n = len(envelope)
    radius = env["radius_mm"]
    arc_per_bin = math.radians(env["bin_width_deg"]) * radius

    doubled = envelope + envelope
    best = {"area_mm2": 0.0}
    stack: list = []
    for i in range(len(doubled) + 1):
        h = 0.0 if i == len(doubled) else doubled[i]
        while stack and doubled[stack[-1]] >= h:
            top = stack.pop()
            left = stack[-1] + 1 if stack else 0
            count = i - left
            if count > n:
                count = n
                left = i - n
            height = doubled[top]
            area = count * arc_per_bin * height
            if area > best["area_mm2"]:
                best = {
                    "area_mm2": round(area, 1),
                    "width_mm": round(count * arc_per_bin, 1),
                    "height_mm": round(height, 1),
                    "centre_azimuth_deg": round(
                        ((left + count / 2.0) % n) * env["bin_width_deg"], 3
                    ),
                }
        stack.append(i)
    return best


# A person is not a rectangle, and neither is a doorway that follows the rods.
# These silhouettes are half-widths at a height: widest at the shoulders,
# narrower at the head, which is exactly the trapezoid you get under a pair of
# crossing bows. Testing a rectangle instead understates every opening.
#
# Each entry is (height_mm, half_width_mm). The template must fit at every
# listed height.
TEMPLATES = {
    "crawl": [(0.0, 350.0), (700.0, 350.0), (900.0, 250.0)],
    "stoop": [(0.0, 300.0), (1200.0, 300.0), (1400.0, 200.0)],
    "walk": [(0.0, 300.0), (1450.0, 300.0), (1800.0, 180.0)],
    "walk_wide": [(0.0, 400.0), (1450.0, 400.0), (1900.0, 220.0)],
    "carry": [(0.0, 450.0), (1450.0, 450.0), (1800.0, 300.0)],
    # Not a person. An event has costumed characters on stilts, in horned
    # helmets, in frames -- and whether one of those gets through the door is
    # a real question that a 1.8 m silhouette never asks.
    "tall": [(0.0, 350.0), (1800.0, 350.0), (2200.0, 220.0)],
}


def template_fits(
    data: dict,
    template: list,
    env: dict | None = None,
    clearance_mm: float = 0.0,
) -> dict:
    """Where a person-shaped opening fits, rather than a rectangle.

    A doorway under two crossing bows is a trapezoid, and so is a person: wide
    at the shoulders, narrower at the head. Fitting that shape finds openings a
    rectangle misses -- which is the difference between "no door fits" and
    "you can walk in here".
    """
    env = env or door_envelope(data, clearance_mm=clearance_mm)
    envelope = env["envelope_mm"]
    n = len(envelope)
    radius = env["radius_mm"]
    arc_per_bin = math.radians(env["bin_width_deg"]) * radius

    def fits_at(centre: int) -> bool:
        for height, half_width in template:
            reach = int(math.ceil(half_width / arc_per_bin))
            for d in range(-reach, reach + 1):
                if envelope[(centre + d) % n] < height:
                    return False
        return True

    centres = [c for c in range(n) if fits_at(c)]
    # Group the acceptable centres into contiguous arcs, so the answer is
    # "five places, each this wide" rather than a list of bins.
    places = []
    if centres:
        runs = _runs_at_least(
            [1.0 if c in set(centres) else 0.0 for c in range(n)], 0.5
        )
        for start, count in runs:
            places.append(
                {
                    "centre_azimuth_deg": round(
                        ((start + count / 2.0) % n) * env["bin_width_deg"], 2
                    ),
                    "slide_mm": round(count * arc_per_bin, 1),
                }
            )
    top = max(h for h, _ in template)
    widest = max(w for _, w in template) * 2.0
    return {
        "height_mm": top,
        "width_mm": widest,
        "place_count": len(places),
        "places": places,
        "fits": bool(places),
    }


def skirt_bay(data: dict, clearance_mm: float = 0.0) -> dict | None:
    """The opening in one bay of the skirt, if there is a skirt.

    The skirt is a vertical wall between two posts, so unlike the dome it has
    no ceiling curving in: the bay is its full height by the chord between
    adjacent posts, less the posts themselves. On a small dome this is the only
    place a standing door fits at all.
    """
    skirt = data.get("skirt")
    if not skirt:
        return None
    meta = data["meta"]
    chord = meta["base_edge_chord"]
    post_diameter = meta["rod_diameter"]
    width = chord - post_diameter - 2.0 * clearance_mm
    return {
        "height_mm": round(skirt["height"], 1),
        "width_mm": round(max(0.0, width), 1),
        "bay_count": skirt["post_count"],
        "note": (
            "Full bay height by the post-to-post chord. Unbraced as drawn -- "
            "and taking a bay out for a door removes whatever bracing that bay "
            "would have carried. See docs/skirt.md."
        ),
    }


def combined_door(data: dict, height_mm: float, env: dict | None = None,
                  clearance_mm: float = 0.0) -> dict:
    """The widest door of a given height, through the skirt and into the dome.

    Below the skirt's height the bay is a plain rectangle. Above it the door
    also has to clear the dome, so the width is whichever of the two is
    narrower.
    """
    bay = skirt_bay(data, clearance_mm)
    skirt_height = bay["height_mm"] if bay else 0.0
    bay_width = bay["width_mm"] if bay else None

    if height_mm <= skirt_height:
        return {
            "height_mm": height_mm,
            "width_mm": bay_width,
            "limited_by": "skirt bay",
        }

    needed_above = height_mm - skirt_height
    dome = widest_at_height(data, needed_above, env)
    dome_width = dome["widest_mm"]
    if bay_width is None:
        return {
            "height_mm": height_mm,
            "width_mm": dome_width,
            "limited_by": "dome" if dome_width else "nothing fits",
        }
    width = min(bay_width, dome_width)
    return {
        "height_mm": height_mm,
        "width_mm": round(width, 1),
        "dome_needs_mm": round(needed_above, 1),
        "dome_allows_mm": dome_width,
        "skirt_bay_mm": bay_width,
        "limited_by": (
            "nothing fits"
            if width <= 0.0
            else ("dome" if dome_width < bay_width else "skirt bay")
        ),
    }


def skirt_for_door(
    data: dict,
    height_mm: float,
    width_mm: float,
    env: dict | None = None,
    clearance_mm: float = 0.0,
    step_mm: float = 10.0,
) -> dict:
    """How tall a skirt a given doorway needs, if the dome cannot take it.

    The dome's own opening narrows as it gets taller, so a door of a fixed
    width can only reach so far above the base ring. Whatever is left has to
    come from the skirt. Reported as the answer to "I want a 1.8 m door" rather
    than as a table to read backwards.
    """
    env = env or door_envelope(data, clearance_mm=clearance_mm)
    meta = data["meta"]
    bay = skirt_bay(data, clearance_mm)
    bay_width = bay["width_mm"] if bay else meta["base_edge_chord"] - meta["rod_diameter"]

    if width_mm > bay_width:
        return {
            "height_mm": height_mm,
            "width_mm": width_mm,
            "possible": False,
            "why": (
                f"a {width_mm:g} mm door will not fit between skirt posts "
                f"{bay_width:.0f} mm apart"
            ),
        }

    # The tallest the dome alone can carry this width.
    reach = 0.0
    h = 0.0
    ceiling = max(env["envelope_mm"])
    while h <= ceiling:
        if widest_at_height(data, h, env)["widest_mm"] >= width_mm:
            reach = h
        else:
            break
        h += step_mm

    needed = max(0.0, height_mm - reach)
    return {
        "height_mm": height_mm,
        "width_mm": width_mm,
        "possible": True,
        "dome_reach_mm": round(reach, 1),
        "skirt_needed_mm": round(needed, 1),
        "skirt_present_mm": bay["height_mm"] if bay else 0.0,
        "overall_height_mm": round(needed + meta["dome_height_nominal"], 1),
    }


def analyse(data: dict, clearance_mm: float = 0.0) -> dict:
    """Door envelope, the largest doorway, and widths at the standard heights."""
    env = door_envelope(data, clearance_mm=clearance_mm)
    envelope = env["envelope_mm"]
    return {
        "variant": data["meta"]["variant"],
        "clearance_mm": clearance_mm,
        "free_height_max_mm": round(max(envelope), 1),
        "free_height_min_mm": round(min(envelope), 1),
        "free_height_over_diameter": round(
            max(envelope) / data["meta"]["dome_diameter"], 4
        ),
        "largest_doorway": largest_doorway(data, env),
        "by_height": [
            widest_at_height(data, h, env) for h in STANDARD_HEIGHTS_MM
        ],
        "skirt_bay": skirt_bay(data, clearance_mm),
        "combined_by_height": [
            combined_door(data, h, env, clearance_mm) for h in STANDARD_HEIGHTS_MM
        ],
    }


def format_analysis(data: dict, clearance_mm: float = 0.0) -> str:
    a = analyse(data, clearance_mm)
    meta = data["meta"]
    lines = [
        f"--- {a['variant']} entrances  "
        f"(rod {meta['rod_diameter']:g} mm, clearance {clearance_mm:g} mm)",
        f"  free height at the base ring: "
        f"{a['free_height_min_mm']:.0f} to {a['free_height_max_mm']:.0f} mm",
    ]
    big = a["largest_doorway"]
    if big.get("width_mm"):
        lines.append(
            f"  largest opening by area: {big['width_mm']:.0f} wide x "
            f"{big['height_mm']:.0f} high at azimuth "
            f"{big['centre_azimuth_deg']:.1f} deg"
        )
    lines.append("  widest opening at a given height:")
    for entry in a["by_height"]:
        if entry["widest_mm"] <= 0.0:
            lines.append(
                f"    {entry['height_mm']:>5.0f} mm high:  nothing fits"
            )
            continue
        first = entry["openings"][0]
        lines.append(
            f"    {entry['height_mm']:>5.0f} mm high:  {entry['widest_mm']:>6.0f} mm "
            f"wide at azimuth {first['centre_azimuth_deg']:>6.1f} deg"
            f"   ({entry['opening_count']} such opening"
            f"{'s' if entry['opening_count'] != 1 else ''} around the dome)"
        )

    bay = a["skirt_bay"]
    if bay:
        lines.append(
            f"  skirt: {bay['bay_count']} bays of {bay['width_mm']:.0f} x "
            f"{bay['height_mm']:.0f} mm -- a vertical wall, no ceiling curving in"
        )
        lines.append("  door through skirt and dome together:")
        for entry in a["combined_by_height"]:
            width = entry["width_mm"] or 0.0
            if width <= 0.0:
                lines.append(
                    f"    {entry['height_mm']:>5.0f} mm high:  nothing fits "
                    f"({entry['limited_by']})"
                )
            else:
                lines.append(
                    f"    {entry['height_mm']:>5.0f} mm high:  {width:>6.0f} mm "
                    f"wide, limited by the {entry['limited_by']}"
                )
    return "\n".join(lines)
