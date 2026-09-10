"""A covered corridor on the doorway, and whether it actually fits there.

The dome has one good opening per bay and five of them, and a corridor is how
two domes become a camp rather than two tents. This module puts one on the
chosen doorway and then measures the thing everybody assumes: **that the
corridor fits through the hole it is attached to.**

## What the corridor is

A hooped tunnel -- a polytunnel. Straight legs to shoulder height, a
semicircular roof over them, fabric across the lot:

    height H = leg + W/2          the roof is a semicircle of radius W/2
    hoop rod = 2*leg + pi*W/2     one bent rod per hoop

Hoops rather than a little star dome, for the reason the whole project keeps:
a repeated part beats a clever one. A hoop is one rod, bent one way, and
every hoop in the corridor is the same hoop.

## The finding that matters

**The corridor bends rod far harder than the dome does.** Every bow in the
dome is bent to the dome radius -- 3000 mm on D6, and minimum bend radius is
already a live constraint on rod selection (roadmap, milestone 1). A corridor
900 mm wide bends its hoops to **450 mm**, six to seven times tighter. The
corridor cannot be made of dome stock; it wants thinner rod, and that is a
purchasing decision, not a drawing one. The report says so in as many words
and refuses to pretend otherwise.

## Where it meets the dome

The mouth is the curve where the tunnel surface meets the cover, and the
cover is a sphere above the base ring and a cylinder through the skirt. For a
point of the tunnel section at ``(v, z)``, the outward distance to that
surface is exact:

    z >= 0    u = sqrt(Rc^2 - v^2 - z^2)      the sphere
    z <  0    u = sqrt(Rc^2 - v^2)            the skirt cylinder

So the mouth is not a plane cut, and a corridor butted flat against the dome
leaves a gap at the crown of nearly half a metre on D6. It is exported as a
closed 3D curve for whatever has to be cut to it.

## What is checked, and how

The tunnel's own cross-section is fed to ``doorway.fit_shape`` as a
silhouette -- the same routine, the same envelope and the same rules that
decide whether a person gets through the door. A corridor is just a very
wide, very square person. That is the whole point of measuring it this way:
there is one definition of "fits through the doorway" in this project, and
the corridor is held to it rather than to a new one invented here.

Nothing here is structural. Wind on a tunnel, hoop footings and the joint at
the dome are milestones 5 and 8.
"""

from __future__ import annotations

import math

from . import doorway, entrance

# A corridor you can carry a chest along, matching the doorway's own default
# silhouette. The height is not free: a semicircular roof pinches over the
# middle, so 900 mm wide needs 1915 mm of height before the "carry" shoulders
# and head both clear it -- 1900 admits only "walk". 1950 keeps a little
# margin over that threshold. All in mm.
DEFAULT_WIDTH_MM = 900.0
DEFAULT_HEIGHT_MM = 1950.0
DEFAULT_LENGTH_MM = 3000.0
DEFAULT_PITCH_MM = 750.0

# How finely the roof arc is sampled for the section outline and the mouth.
ARC_SAMPLES = 12


def section(width: float, height: float, samples: int = ARC_SAMPLES) -> list:
    """The tunnel cross-section as ``(height, half_width)``, ground upward.

    The same shape ``entrance.TEMPLATES`` uses, so it can be measured against
    the doorway by exactly the routine that measures people.
    """
    half = width / 2.0
    leg = height - half
    if leg < 0:
        raise ValueError(
            f"height {height:g} is less than half the width {width:g}: "
            "a semicircular roof alone is that tall, so the tunnel cannot be "
            "shorter than its own arch"
        )
    out = [(0.0, half), (leg, half)]
    for i in range(1, samples + 1):
        a = (math.pi / 2.0) * i / samples
        out.append((leg + half * math.sin(a), half * math.cos(a)))
    return out


def hoop(width: float, height: float, rod_diameter: float, dome_radius: float) -> dict:
    """One bent hoop: how much rod, and how hard it is bent."""
    half = width / 2.0
    leg = height - half
    arc = math.pi * half
    return {
        "bend_radius_mm": round(half, 1),
        "leg_height_mm": round(leg, 1),
        "arc_length_mm": round(arc, 1),
        "rod_length_mm": round(2.0 * leg + arc, 1),
        "dome_bend_radius_mm": round(dome_radius, 1),
        "times_tighter_than_dome": round(dome_radius / half, 2) if half else None,
        "note": (
            "The dome bends every bow to the dome radius; this bends a rod "
            f"{dome_radius / half:.1f}x tighter. Corridor hoops are a different "
            "rod from dome bows -- confirm the stock's minimum bend radius "
            "before assuming one rod serves both."
        ) if half else "",
    }


def mouth(data: dict, azimuth_deg: float, width: float, height: float,
          samples: int = ARC_SAMPLES) -> dict:
    """Where the tunnel meets the cover, as a closed 3D curve.

    Exact, not a plane cut: above the base ring the cover is a sphere, through
    the skirt it is a cylinder, and the tunnel meets each differently.
    """
    from . import cover

    meta = data["meta"]
    rc = cover.radius(data)
    ground = meta.get("ground_z", 0.0) or 0.0

    a = math.radians(azimuth_deg)
    eu = (math.cos(a), math.sin(a))
    ev = (-math.sin(a), math.cos(a))

    outline = section(width, height, samples)
    # Up one side and down the other: a closed loop round the section.
    loop = [(z, +w) for z, w in outline] + [(z, -w) for z, w in reversed(outline)]

    points = []
    reach = []
    for z_rel, v in loop:
        z = ground + z_rel
        if z >= 0.0:
            inside = rc * rc - v * v - z * z
        else:
            inside = rc * rc - v * v
        if inside <= 0.0:
            # The section pokes outside the dome's silhouette entirely.
            return {
                "fits_on_dome": False,
                "point_count": 0,
                "points": [],
                "note": (
                    "The tunnel section reaches past the cover's own silhouette; "
                    "it cannot meet the dome at all at this size."
                ),
            }
        u = math.sqrt(inside)
        reach.append(u)
        points.append([
            round(eu[0] * u + ev[0] * v, 3),
            round(eu[1] * u + ev[1] * v, 3),
            round(z, 3),
        ])

    return {
        "fits_on_dome": True,
        "point_count": len(points),
        "closed": True,
        "min_reach_mm": round(min(reach), 1),
        "max_reach_mm": round(max(reach), 1),
        "step_mm": round(max(reach) - min(reach), 1),
        "points": points,
        "note": (
            "Closed curve on the cover surface. max_reach - min_reach is how "
            "far from flat the joint is: a corridor butted square against the "
            "dome leaves that much gap at the crown."
        ),
    }


def _profile(width: float, height: float, samples: int) -> list:
    """The hoop's own curve as ``(v, z)``: up one leg, over, down the other.

    Continuous, and in that order. Running one side crown-downward instead
    makes the curve jump across the floor, which draws a hoop as a bow tie.
    """
    outline = section(width, height, samples)
    left = [(-w, z) for z, w in outline]            # ground up to the crown
    right = [(w, z) for z, w in reversed(outline)]  # crown back down
    return left + right[1:]                         # the crown is in both


def _frame(azimuth_deg: float):
    a = math.radians(azimuth_deg)
    return (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))


def _reach(rc: float, v: float, z: float) -> float:
    """Outward distance to the cover at this point of the section."""
    inside = rc * rc - v * v - (z * z if z >= 0.0 else 0.0)
    return math.sqrt(inside) if inside > 0.0 else 0.0


def drawing(
    data: dict,
    azimuth_deg: float,
    width: float,
    height: float,
    length: float,
    pitch: float,
    samples: int = ARC_SAMPLES,
) -> dict:
    """Hoop centrelines and the fabric skin, as geometry a consumer can draw.

    Exported rather than described, the same contract the rod polylines keep:
    a scene builder should never work out where a hoop goes.
    """
    from . import cover

    meta = data["meta"]
    rc = cover.radius(data)
    ground = meta.get("ground_z", 0.0) or 0.0
    eu, ev = _frame(azimuth_deg)
    profile = _profile(width, height, samples)

    def place3(u: float, v: float, z_rel: float) -> list:
        return [
            round(eu[0] * u + ev[0] * v, 3),
            round(eu[1] * u + ev[1] * v, 3),
            round(ground + z_rel, 3),
        ]

    starts = [_reach(rc, v, ground + z) for v, z in profile]
    u_first = max(starts)
    u_far = u_first + length
    count = int(length // pitch) + 1

    hoops = []
    for i in range(count):
        u = u_far - i * pitch
        if u < u_first - 1e-9:
            break
        hoops.append([place3(u, v, z) for v, z in profile])

    verts = []
    near = []
    far = []
    for (v, z), u0 in zip(profile, starts):
        near.append(len(verts))
        verts.append(place3(u0, v, z))
    for v, z in profile:
        far.append(len(verts))
        verts.append(place3(u_far, v, z))

    faces = [
        [near[i], near[i + 1], far[i + 1], far[i]]
        for i in range(len(profile) - 1)
    ]

    return {
        "hoop_count": len(hoops),
        "hoops": hoops,
        "skin": {
            "vertex_count": len(verts),
            "face_count": len(faces),
            "vertices": verts,
            "faces": faces,
        },
        "note": (
            "The skin is ruled from the mouth curve to the far end, so it "
            "follows the dome at the near end and is square at the far one. "
            "Open at both ends: a corridor joins two things."
        ),
    }


def admits(width: float, height: float) -> list:
    """Which standard silhouettes fit inside the tunnel itself, smallest first.

    Containment only -- this asks whether the corridor is big enough, not
    whether it is attached to anything.
    """
    half = width / 2.0
    leg = height - half
    passing = []
    for name, template in entrance.TEMPLATES.items():
        ok = True
        for h, w in template:
            if h > height:
                ok = False
                break
            avail = half if h <= leg else math.sqrt(max(0.0, half * half - (h - leg) ** 2))
            if w > avail:
                ok = False
                break
        if ok:
            passing.append(name)
    return sorted(passing, key=lambda k: max(h for h, _ in entrance.TEMPLATES[k]))


def place(
    data: dict,
    width: float = DEFAULT_WIDTH_MM,
    height: float = DEFAULT_HEIGHT_MM,
    length: float = DEFAULT_LENGTH_MM,
    pitch: float = DEFAULT_PITCH_MM,
    samples: int = ARC_SAMPLES,
    include_geometry: bool = False,
) -> dict:
    """Put a corridor on the chosen doorway and measure everything about it."""
    meta = data["meta"]
    door = data.get("doorway")
    if not door:
        return {
            "present": False,
            "note": "this variant has no doorway, so there is nothing to attach to",
        }

    bay = door["bay"]
    azimuth = bay["centre_azimuth_deg"]
    half = width / 2.0
    leg = height - half

    shape = section(width, height, samples)
    env = entrance.door_envelope(data)
    through = doorway.fit_shape(data, shape, "corridor", env)

    m = mouth(data, azimuth, width, height, samples)
    hoops = hoop(width, height, meta["rod_diameter"], meta["dome_radius"])

    count = int(length // pitch) + 1
    skin_perimeter = 2.0 * leg + math.pi * half
    skin_area = skin_perimeter * length
    floor_area = width * length
    section_area = width * leg + math.pi * half * half / 2.0

    out = {
        "present": True,
        "attaches_to_bay_azimuth_deg": azimuth,
        "width_mm": round(width, 1),
        "height_mm": round(height, 1),
        "length_mm": round(length, 1),
        "hoop_pitch_mm": round(pitch, 1),
        "hoop_count": count,
        "hoop": hoops,
        "rod_total_mm": round(count * hoops["rod_length_mm"], 1),
        "mouth": m,
        "through_doorway": {
            "fits": through["fits"],
            "spare_mm": through["spare_mm"],
            # The bay's own clear height is measured from the base ring; a
            # skirt lifts the whole dome and adds to it. Reporting only the
            # first number is how a skirted dome gets called too short.
            "bay_clear_height_mm": door["in_bay"]["clear_height_mm"],
            "skirt_mm": meta.get("skirt_height", 0.0) or 0.0,
            "available_height_mm": round(
                (meta.get("skirt_height", 0.0) or 0.0)
                + door["in_bay"]["clear_height_mm"], 1
            ),
            "bay_widths_mm": door["in_bay"]["widths_mm"],
        },
        "admits": admits(width, height),
        "cover_m2": round(skin_area / 1e6, 2),
        "floor_m2": round(floor_area / 1e6, 2),
        "section_m2": round(section_area / 1e6, 3),
        "note": (
            "Shape, fit and quantities only. The joint at the dome, hoop "
            "footings and wind on a tunnel are milestones 5 and 8. "
            "See docs/corridor.md."
        ),
    }
    if include_geometry and m["fits_on_dome"]:
        out["drawing"] = drawing(
            data, azimuth, width, height, length, pitch, samples
        )
    return out


def widest_that_fits(
    data: dict,
    height: float = DEFAULT_HEIGHT_MM,
    step: float = 25.0,
) -> dict:
    """The widest corridor of this height the doorway will pass.

    Answers the question the failing case immediately raises: not "does 900
    fit" but "then what does".
    """
    env = entrance.door_envelope(data)
    best = 0.0
    width = 2.0 * step
    while width <= 3000.0:
        if height < width / 2.0:
            break
        try:
            shape = section(width, height)
        except ValueError:
            break
        if doorway.fit_shape(data, shape, "corridor", env)["fits"]:
            best = width
        width += step
    return {
        "height_mm": round(height, 1),
        "widest_mm": round(best, 1),
        "admits": admits(best, height) if best else [],
    }


def tallest_that_fits(data: dict, width: float = DEFAULT_WIDTH_MM,
                      step: float = 25.0) -> dict:
    """The tallest corridor of this width the doorway will pass.

    When no width at all fits, height is the binding constraint, and this is
    the number that says what to do about it.
    """
    env = entrance.door_envelope(data)
    best = 0.0
    height = width / 2.0
    while height <= 3000.0:
        shape = section(width, height)
        if doorway.fit_shape(data, shape, "corridor", env)["fits"]:
            best = height
        else:
            break
        height += step
    return {
        "width_mm": round(width, 1),
        "tallest_mm": round(best, 1),
        "admits": admits(width, best) if best else [],
    }


def fitted_spec(
    data: dict,
    width: float = DEFAULT_WIDTH_MM,
    max_height: float = DEFAULT_HEIGHT_MM,
    length: float = DEFAULT_LENGTH_MM,
    pitch: float = DEFAULT_PITCH_MM,
) -> dict | None:
    """The biggest corridor of this width that this dome's doorway will pass.

    A camp cannot give every dome the same corridor, because the domes do not
    have the same door. Sizing each one to what its own bay admits is what
    makes a row of five read as five different-sized buildings rather than as
    one design drawn wrong four times.

    Returns ``None`` when the dome has no doorway at all.
    """
    if not data.get("doorway"):
        return None
    best = tallest_that_fits(data, width)["tallest_mm"]
    if not best:
        return None
    return {
        "width": width,
        "height": min(best, max_height),
        "length": length,
        "pitch": pitch,
    }


def format_analysis(
    data: dict,
    width: float = DEFAULT_WIDTH_MM,
    height: float = DEFAULT_HEIGHT_MM,
    length: float = DEFAULT_LENGTH_MM,
    pitch: float = DEFAULT_PITCH_MM,
) -> str:
    """The corridor, as a page for a person."""
    meta = data["meta"]
    c = place(data, width, height, length, pitch)
    if not c["present"]:
        return f"--- {meta['variant']} corridor: {c['note']}"

    h = c["hoop"]
    t = c["through_doorway"]
    lines = [
        f"--- {meta['variant']} corridor  {c['width_mm']:.0f} x {c['height_mm']:.0f} mm, "
        f"{c['length_mm'] / 1000.0:.1f} m long, on the bay at "
        f"{c['attaches_to_bay_azimuth_deg']:.1f} deg",
        f"  hoops           {c['hoop_count']} at {c['hoop_pitch_mm']:.0f} mm, "
        f"{h['rod_length_mm']:.0f} mm of rod each, {c['rod_total_mm'] / 1000.0:.1f} m total",
        f"  bend radius     {h['bend_radius_mm']:.0f} mm, "
        f"{h['times_tighter_than_dome']:.1f}x tighter than the dome's "
        f"{h['dome_bend_radius_mm']:.0f} mm",
        f"  cover           {c['cover_m2']:.2f} m2 skin over {c['floor_m2']:.2f} m2 of floor",
        f"  admits          {', '.join(c['admits']) or 'nothing'}",
        "",
    ]

    if c["mouth"]["fits_on_dome"]:
        lines.append(
            f"  mouth           reaches {c['mouth']['min_reach_mm']:.0f}"
            f"-{c['mouth']['max_reach_mm']:.0f} mm from centre, so the joint is "
            f"{c['mouth']['step_mm']:.0f} mm from flat"
        )
    else:
        lines.append(f"  mouth           {c['mouth']['note']}")

    if t["fits"]:
        lines.append(
            f"  through the bay YES, with {t['spare_mm']:.0f} mm of headroom to spare"
        )
    else:
        w = widest_that_fits(data, height)
        if w["widest_mm"]:
            lines.append(
                f"  through the bay NO, too wide. Widest at {c['height_mm']:.0f} mm "
                f"of height is {w['widest_mm']:.0f} mm"
                + (f", which admits {', '.join(w['admits'])}" if w["admits"] else
                   ", which admits nothing")
            )
        else:
            # Nothing of this height fits at any width, so the height is what
            # is wrong, not the width -- say that instead of reporting a zero.
            tall = tallest_that_fits(data, width)
            where = (
                f" ({t['bay_clear_height_mm']:.0f} mm of bay over "
                f"{t['skirt_mm']:.0f} mm of skirt)" if t["skirt_mm"] else ""
            )
            lines.append(
                f"  through the bay NO, too tall. There is only "
                f"{t['available_height_mm']:.0f} mm{where}, so no corridor "
                f"{c['height_mm']:.0f} mm high fits at any width."
            )
            lines.append(
                f"                  At {c['width_mm']:.0f} mm wide the tallest "
                f"that passes is {tall['tallest_mm']:.0f} mm"
                + (f", admitting {', '.join(tall['admits'])}." if tall["admits"] else
                   ", which admits nothing.")
            )
        lines.append(
            "                  A corridor cannot be bigger than the hole it "
            "attaches to. Raise the dome on a skirt, or shrink the corridor."
        )

    lines += ["", "  Shape and fit only. No structural claim."]
    return "\n".join(lines)
