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


# --------------------------------------------------------------------------
# the timber portal
# --------------------------------------------------------------------------
# A second kind of corridor, not a replacement for the hoop. Two posts, a
# header across them, a knee brace in each top corner: a P-frame in boards.
# It buys width the bent hoop cannot -- 1.5 to 2 m instead of 900 mm -- at the
# cost of being timber rather than the rod stock already on site.
DEFAULT_PORTAL_WIDTH_MM = 1800.0
DEFAULT_PORTAL_HEIGHT_MM = 2100.0
DEFAULT_PORTAL_PITCH_MM = 1200.0

# A knee brace at 45 degrees across each top corner. Without one the frame is
# three boards pinned at two corners, which is a mechanism: it folds sideways
# under any wind along the corridor. With one, each corner is a triangle.
DEFAULT_BRACE_LEG_MM = 300.0

# Nominal sawn board, mm. Thickness is across the frame, width is in its plane
# -- boards resist bending the way they are turned, and a portal frame bends
# in its own plane.
DEFAULT_BOARD_THICKNESS_MM = 45.0
DEFAULT_BOARD_WIDTH_MM = 145.0


def portal_section(
    width: float,
    height: float,
    brace_leg: float = DEFAULT_BRACE_LEG_MM,
) -> list:
    """The clear opening of a portal frame as ``(height, half_width)``.

    Not a rectangle. The knee braces cut both top corners at 45 degrees, so
    what is actually clear is a trapezoid: full width up to ``height -
    brace_leg``, then chamfered in.

    That turns out to suit the traffic better than the hoop does. A person is
    wide at the shoulders and narrower at the head, and so is this; the hoop's
    semicircular roof starts narrowing at shoulder height and keeps going.
    """
    half = width / 2.0
    if brace_leg < 0:
        raise ValueError("brace leg cannot be negative")
    if brace_leg > half:
        raise ValueError(
            f"brace leg {brace_leg:g} is more than half the width {width:g}: "
            "the two braces would meet in the middle of the opening"
        )
    if height <= brace_leg:
        raise ValueError(
            f"height {height:g} is not more than the brace leg {brace_leg:g}"
        )
    return [
        (0.0, half),
        (height - brace_leg, half),
        (height, half - brace_leg),
    ]


def portal_frame(
    width: float,
    height: float,
    brace_leg: float = DEFAULT_BRACE_LEG_MM,
    thickness: float = DEFAULT_BOARD_THICKNESS_MM,
    board: float = DEFAULT_BOARD_WIDTH_MM,
) -> dict:
    """One frame, as a cut list. Boards, so it is lengths rather than a bend.

    ``width`` and ``height`` are the CLEAR opening -- what you walk through --
    so the posts stand outside it and the header sits above it.
    """
    post = height
    header = width + 2.0 * board
    brace = brace_leg * math.sqrt(2.0)
    total = 2.0 * post + header + 2.0 * brace
    return {
        "clear_width_mm": round(width, 1),
        "clear_height_mm": round(height, 1),
        "overall_width_mm": round(header, 1),
        "overall_height_mm": round(height + board, 1),
        "board": f"{thickness:g} x {board:g}",
        "members": [
            {"name": "post", "count": 2, "length_mm": round(post, 1)},
            {"name": "header", "count": 1, "length_mm": round(header, 1)},
            {"name": "knee brace", "count": 2, "length_mm": round(brace, 1),
             "note": "cut both ends at 45 deg"},
        ],
        "board_length_mm": round(total, 1),
        "note": (
            "Clear opening given; posts stand outside it, header above it. "
            "The braces are what stop the frame racking -- three boards pinned "
            "at two corners is a mechanism, not a frame."
        ),
    }


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
          samples: int = ARC_SAMPLES, kind: str = "hoop",
          brace_leg: float = DEFAULT_BRACE_LEG_MM) -> dict:
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

    outline = section_for(kind, width, height, samples, brace_leg)
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


KINDS = ("hoop", "portal")


def section_for(
    kind: str,
    width: float,
    height: float,
    samples: int = ARC_SAMPLES,
    brace_leg: float = DEFAULT_BRACE_LEG_MM,
) -> list:
    """The clear cross-section of either kind of corridor, as a silhouette."""
    if kind == "hoop":
        return section(width, height, samples)
    if kind == "portal":
        return portal_section(width, height, brace_leg)
    raise ValueError(f"unknown corridor kind {kind!r}; expected one of {KINDS}")


def _portal_members(width: float, height: float, brace_leg: float,
                    thickness: float, board: float) -> list:
    """Each board as a centreline in the frame's own ``(v, z)`` plane."""
    outer = width / 2.0 + board / 2.0
    inner = width / 2.0 + board
    return [
        ("post_left", (-outer, 0.0), (-outer, height)),
        ("post_right", (outer, 0.0), (outer, height)),
        ("header", (-inner, height + board / 2.0), (inner, height + board / 2.0)),
        ("brace_left", (-outer, height - brace_leg),
         (-(width / 2.0 - brace_leg), height)),
        ("brace_right", (outer, height - brace_leg),
         (width / 2.0 - brace_leg, height)),
    ]


def _profile(width: float, height: float, samples: int,
             kind: str = "hoop", brace_leg: float = DEFAULT_BRACE_LEG_MM) -> list:
    """The clear opening's own curve as ``(v, z)``: up one side and down the other.

    Continuous, and in that order. Running one side crown-downward instead
    makes the curve jump across the floor, which draws a hoop as a bow tie.
    """
    outline = section_for(kind, width, height, samples, brace_leg)
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


def _board_box(a2, b2, eu, ev, u, ground, thickness, board):
    """One board as eight corners: a member from a2 to b2 in the frame plane."""
    (v0, z0), (v1, z1) = a2, b2
    dv, dz = v1 - v0, z1 - z0
    span = math.hypot(dv, dz)
    if span < 1e-9:
        return [], []
    # In-plane normal to the member, so the board's WIDTH lies in the frame.
    nv, nz = -dz / span, dv / span
    hb, ht = board / 2.0, thickness / 2.0

    verts = []
    for v_end, z_end in ((v0, z0), (v1, z1)):
        for sn in (-1.0, 1.0):
            for st in (-1.0, 1.0):
                v = v_end + nv * hb * sn
                z = z_end + nz * hb * sn
                du = ht * st
                verts.append([
                    round(eu[0] * (u + du) + ev[0] * v, 3),
                    round(eu[1] * (u + du) + ev[1] * v, 3),
                    round(ground + z, 3),
                ])
    faces = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 2, 6, 4],
             [1, 5, 7, 3], [0, 4, 5, 1], [2, 3, 7, 6]]
    return verts, faces


def drawing(
    data: dict,
    azimuth_deg: float,
    width: float,
    height: float,
    length: float,
    pitch: float,
    samples: int = ARC_SAMPLES,
    kind: str = "hoop",
    brace_leg: float = DEFAULT_BRACE_LEG_MM,
) -> dict:
    """Rib centrelines and the fabric skin, as geometry a consumer can draw.

    Exported rather than described, the same contract the rod polylines keep:
    a scene builder should never work out where a hoop goes.
    """
    from . import cover

    meta = data["meta"]
    rc = cover.radius(data)
    ground = meta.get("ground_z", 0.0) or 0.0
    eu, ev = _frame(azimuth_deg)
    profile = _profile(width, height, samples, kind, brace_leg)

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
    frames = []
    members = (
        _portal_members(width, height, brace_leg,
                        DEFAULT_BOARD_THICKNESS_MM, DEFAULT_BOARD_WIDTH_MM)
        if kind == "portal" else []
    )
    for i in range(count):
        u = u_far - i * pitch
        if u < u_first - 1e-9:
            break
        if kind == "portal":
            fverts, ffaces = [], []
            for _name, a2, b2 in members:
                bv, bf = _board_box(
                    a2, b2, eu, ev, u, ground,
                    DEFAULT_BOARD_THICKNESS_MM, DEFAULT_BOARD_WIDTH_MM,
                )
                base = len(fverts)
                fverts.extend(bv)
                ffaces.extend([[k + base for k in face] for face in bf])
            frames.append({"vertices": fverts, "faces": ffaces})
        else:
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
        "kind": kind,
        "hoop_count": len(hoops) or len(frames),
        "hoops": hoops,
        "frames": frames,
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


def _clear_half_width(outline: list, h: float) -> float:
    """Half width of a section at height ``h``, interpolated between samples."""
    if h > outline[-1][0]:
        return -1.0
    prev_h, prev_w = outline[0]
    for point_h, point_w in outline:
        if h <= point_h:
            if point_h == prev_h:
                return min(prev_w, point_w)
            t = (h - prev_h) / (point_h - prev_h)
            return prev_w + t * (point_w - prev_w)
        prev_h, prev_w = point_h, point_w
    return prev_w


def admits(width: float, height: float, kind: str = "hoop",
           brace_leg: float = DEFAULT_BRACE_LEG_MM) -> list:
    """Which standard silhouettes fit inside the tunnel itself, smallest first.

    Containment only -- this asks whether the corridor is big enough, not
    whether it is attached to anything.
    """
    outline = section_for(kind, width, height, ARC_SAMPLES, brace_leg)
    passing = []
    for name, template in entrance.TEMPLATES.items():
        if all(_clear_half_width(outline, h) >= w for h, w in template):
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
    kind: str = "hoop",
    brace_leg: float = DEFAULT_BRACE_LEG_MM,
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

    shape = section_for(kind, width, height, samples, brace_leg)
    env = entrance.door_envelope(data)
    through = doorway.fit_shape(data, shape, "corridor", env)

    m = mouth(data, azimuth, width, height, samples, kind, brace_leg)

    if kind == "portal":
        rib = portal_frame(width, height, brace_leg)
    else:
        rib = hoop(width, height, meta["rod_diameter"], meta["dome_radius"])

    count = int(length // pitch) + 1
    # Perimeter and area straight off the outline, so both kinds are measured
    # by one rule rather than by two formulas that can drift apart.
    profile = _profile(width, height, samples, kind, brace_leg)
    skin_perimeter = sum(
        math.dist(profile[i], profile[i + 1]) for i in range(len(profile) - 1)
    )
    skin_area = skin_perimeter * length
    floor_area = width * length
    section_area = 0.0
    for i in range(len(shape) - 1):
        h0, w0 = shape[i]
        h1, w1 = shape[i + 1]
        section_area += (w0 + w1) * (h1 - h0)  # trapezoid, both halves

    out = {
        "present": True,
        "kind": kind,
        "attaches_to_bay_azimuth_deg": azimuth,
        "width_mm": round(width, 1),
        "height_mm": round(height, 1),
        "length_mm": round(length, 1),
        "hoop_pitch_mm": round(pitch, 1),
        "hoop_count": count,
        "rib": rib,
        "material_total_mm": round(
            count * rib.get("rod_length_mm", rib.get("board_length_mm", 0.0)), 1
        ),
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
        "admits": admits(width, height, kind, brace_leg),
        # A corridor wider than its door is a normal building, not a mistake:
        # you walk from the corridor through the doorway. `fits` asks the
        # strict question -- does the whole section pass unobstructed -- and
        # this says what still gets through when the answer is no.
        "bottleneck": {
            "at": None if through["fits"] else "the dome's doorway",
            "doorway_admits": door.get("admits", []),
            "note": (
                "None -- the whole section passes."
                if through["fits"] else
                "The corridor is bigger than the opening it meets, so its "
                "posts land on the bows rather than inside the bay. Walking "
                "through is unaffected -- the door still admits a person -- "
                "but the junction needs a detail that does not exist yet: "
                "trim the corridor to the bay, or raise the dome on a skirt. "
                "See roadmap milestone 5, entrance/corridor interface."
            ),
        },
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
            data, azimuth, width, height, length, pitch, samples, kind, brace_leg
        )
    return out


def widest_that_fits(
    data: dict,
    height: float = DEFAULT_HEIGHT_MM,
    step: float = 25.0,
    kind: str = "hoop",
    brace_leg: float = DEFAULT_BRACE_LEG_MM,
) -> dict:
    """The widest corridor of this height the doorway will pass.

    Answers the question the failing case immediately raises: not "does 900
    fit" but "then what does".
    """
    env = entrance.door_envelope(data)
    best = 0.0
    width = 2.0 * step
    while width <= 3000.0:
        try:
            shape = section_for(kind, width, height, ARC_SAMPLES, brace_leg)
        except ValueError:
            width += step
            continue
        if doorway.fit_shape(data, shape, "corridor", env)["fits"]:
            best = width
        width += step
    return {
        "height_mm": round(height, 1),
        "widest_mm": round(best, 1),
        "admits": admits(best, height, kind, brace_leg) if best else [],
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
    kind: str = "hoop",
    brace_leg: float = DEFAULT_BRACE_LEG_MM,
) -> str:
    """The corridor, as a page for a person."""
    meta = data["meta"]
    c = place(data, width, height, length, pitch, kind=kind, brace_leg=brace_leg)
    if not c["present"]:
        return f"--- {meta['variant']} corridor: {c['note']}"

    rib = c["rib"]
    t = c["through_doorway"]
    lines = [
        f"--- {meta['variant']} {c['kind']} corridor  "
        f"{c['width_mm']:.0f} x {c['height_mm']:.0f} mm, "
        f"{c['length_mm'] / 1000.0:.1f} m long, on the bay at "
        f"{c['attaches_to_bay_azimuth_deg']:.1f} deg",
    ]
    if c["kind"] == "portal":
        cuts = ", ".join(
            f"{m['count']}x {m['length_mm']:.0f}" for m in rib["members"]
        )
        lines += [
            f"  frames          {c['hoop_count']} at {c['hoop_pitch_mm']:.0f} mm, "
            f"board {rib['board']}",
            f"  cut list        {cuts} mm  "
            f"({rib['board_length_mm'] / 1000.0:.1f} m per frame, "
            f"{c['material_total_mm'] / 1000.0:.1f} m total)",
            f"  clear opening   {rib['clear_width_mm']:.0f} wide, "
            f"{rib['clear_height_mm']:.0f} high, corners cut back "
            f"{brace_leg:.0f} mm by the braces",
        ]
    else:
        lines += [
            f"  hoops           {c['hoop_count']} at {c['hoop_pitch_mm']:.0f} mm, "
            f"{rib['rod_length_mm']:.0f} mm of rod each, "
            f"{c['material_total_mm'] / 1000.0:.1f} m total",
            f"  bend radius     {rib['bend_radius_mm']:.0f} mm, "
            f"{rib['times_tighter_than_dome']:.1f}x tighter than the dome's "
            f"{rib['dome_bend_radius_mm']:.0f} mm",
        ]
    lines += [
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
    elif c["kind"] == "portal":
        w = widest_that_fits(data, height, 25.0, kind, brace_leg)
        lines.append(
            f"  through the bay NO -- the corridor is wider than the door. "
            f"Widest portal that passes whole is {w['widest_mm']:.0f} mm."
        )
        lines.append(
            "                  So its posts land on the bows rather than "
            "inside the bay. A person is unaffected -- the door still admits "
            + (", ".join(c["bottleneck"]["doorway_admits"]) or "nothing")
            + " -- but the junction needs a detail that does not exist yet."
        )
        lines.append(
            "                  Trim the corridor to the bay, or raise the "
            "dome: 1800 mm of skirt on D6, 1300 on D8, 700 on D10."
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
