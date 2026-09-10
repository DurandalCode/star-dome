"""The fabric cover: what it rests on, how much of it there is, how it is cut.

A Star Dome's cover is not a design decision so much as a consequence. The
rods are already a sphere, so the fabric is a sphere too -- pulled over the
outside of the lattice, resting on whichever rod sits furthest out.

## What the fabric rests on

Not the nominal sphere. In the layered weave a rod leaves its great circle by
up to a rod diameter and a half, and the fabric rides on the *outermost rod
surface*: `max_diameter_incl_rod / 2`, which the model already derives. For D6
that is 3075 mm against a nominal 3000: 2.5% more radius, and so **5.1% more
fabric** than the naive figure -- three square metres on a sixty square metre
cover, and 5.1% more sail area to hold down.

## Why a sphere is awkward fabric

A sphere is not developable: no piece of it flattens without stretching. So a
spherical cover is sewn from **gores** -- tapered strips between two meridians,
each of which *is* developable to the accuracy anyone cuts fabric to. The
classic construction, and the one used here:

    a gore runs pole to equator, length      pi * R / 2
    its HALF width at polar angle theta      pi * R * sin(theta) / n
    so it is widest at the equator, across   2 * pi * R / n

That last line is the equator's circumference divided between the gores,
which is the only thing it could be. Halving it by mistake halves the gore
count too, and the cover comes back saying it sews from seven strips when it
needs thirteen.

That last line is the one that decides everything: the gore has to fit across
the roll of fabric you can actually buy, and that fixes the gore count. It is
why a bigger dome is not simply more fabric -- it is more *seams*, and every
seam is labour and a leak path.

## What this does not do

- No stretch, no sag, no catenary between rods. The fabric is taken as lying
  on the sphere, which is the optimistic case: real fabric dips between the
  rods and picks up a little area doing it.
- No seam allowance, no hem, no overlap at the base. Those are cutting-room
  numbers and they depend on the machine and the material.
- The mesh exported for drawing is closed. The doorway is exported separately,
  as an outline, by ``doorway`` -- see ``opening`` below for its area.

None of that is a structural claim. Load paths, wind pressure and attachment
are milestones 5 and 8; this module knows only shape and area.
"""

from __future__ import annotations

import math

# A gore has to cross the roll of fabric being cut from. This is an input, not
# a fact about the world: change it to whatever the supplier actually sells.
DEFAULT_ROLL_WIDTH_MM = 1500.0

# Drawing resolution for the exported mesh. 60 meridians divides by 5, so the
# dome's own symmetry lands on mesh edges rather than across them.
MESH_MERIDIANS = 60
MESH_PARALLELS = 24


def radius(data: dict) -> float:
    """The sphere the fabric lies on: the outermost rod's outer surface.

    ``max_diameter_woven`` rather than ``max_diameter_incl_rod``, because the
    weave is a fact about the built dome and not a drawing convention. A model
    built in flat mode reports every rod on the nominal sphere; the fabric
    still has to go over the real one.
    """
    meta = data["meta"]
    return meta.get("max_diameter_woven", meta["max_diameter_incl_rod"]) / 2.0


def areas(data: dict) -> dict:
    """Fabric area, split by what part of the structure it covers.

    The dome is a hemisphere zone (2*pi*R^2) and the skirt, when there is one,
    a cylinder under it. The doorway is subtracted because it is cut out, and
    reported separately because it is also the piece you have to make a door
    out of.
    """
    meta = data["meta"]
    r = radius(data)
    skirt = meta.get("skirt_height", 0.0) or 0.0

    dome = 2.0 * math.pi * r * r
    barrel = 2.0 * math.pi * r * skirt
    door = opening(data)["area_mm2"]

    return {
        "radius_mm": round(r, 1),
        "dome_m2": round(dome / 1e6, 2),
        "skirt_m2": round(barrel / 1e6, 2),
        "doorway_m2": round(door / 1e6, 2),
        "total_m2": round((dome + barrel - door) / 1e6, 2),
        "gross_m2": round((dome + barrel) / 1e6, 2),
    }


def opening(data: dict) -> dict:
    """The hole the doorway makes in the cover.

    The bay's open area is what the fabric loses; the outline is what it is
    cut to. Both come from ``doorway`` -- this module does not rediscover
    which bay the door is in.
    """
    door = data.get("doorway")
    if not door:
        return {"area_mm2": 0.0, "present": False, "note": "no doorway on this variant"}
    bay = door["bay"]
    outline = door.get("outline") or {}
    return {
        "present": True,
        "area_mm2": bay["open_area_m2"] * 1e6,
        "area_m2": bay["open_area_m2"],
        "centre_azimuth_deg": bay["centre_azimuth_deg"],
        "span_deg": bay["span_deg"],
        "outline_points": outline.get("point_count", 0),
        "note": (
            "Cut to the doorway outline, which traces the two framing bows and "
            "the ground. The cover loses this area; the door panel is made of it."
        ),
    }


def gores(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM) -> dict:
    """How few tapered strips the hemisphere can be sewn from.

    The gore is widest at the equator, where the gores between them share the
    equator's whole circumference: ``2 * pi * R / n`` each. That is what has
    to cross the roll, so the roll width sets the minimum count. Fewer gores
    means fewer seams, so the answer wanted is always the smallest ``n`` that
    fits.
    """
    r = radius(data)
    if roll_width_mm <= 0:
        raise ValueError("roll width must be positive")

    # Widest gore is 2*pi*R/n across -- the equator shared out -- and it must
    # fit the roll.
    count = max(3, math.ceil(2.0 * math.pi * r / roll_width_mm))
    width = 2.0 * math.pi * r / count
    length = math.pi * r / 2.0

    return {
        "count": count,
        "roll_width_mm": round(roll_width_mm, 1),
        "gore_width_mm": round(width, 1),
        "gore_length_mm": round(length, 1),
        "seam_count": count,
        "seam_length_mm": round(count * length, 1),
        "note": (
            "Hemisphere only, no seam allowance and no hem. The skirt, where "
            "there is one, is a cylinder and cuts flat from the same roll."
        ),
    }


def gore_outline(data: dict, count: int, samples: int = 24) -> list:
    """One gore as a flat pattern: (along, half_width) in mm from the pole.

    Developed along the meridian, which is exact for the meridian itself and
    the standard approximation everywhere else. ``along`` is arc length from
    the pole, so the piece is cut ``pi*R/2`` long.
    """
    r = radius(data)
    out = []
    for i in range(samples + 1):
        theta = (math.pi / 2.0) * i / samples
        along = r * theta
        half = math.pi * r * math.sin(theta) / count
        out.append((round(along, 1), round(half, 1)))
    return out


def mesh(
    data: dict,
    meridians: int = MESH_MERIDIANS,
    parallels: int = MESH_PARALLELS,
) -> dict:
    """The cover as vertices and quad faces, for a consumer to draw.

    Exported rather than described so no consumer has to rebuild it, the same
    contract the rod polylines keep. The skirt, when present, is the first
    ring of quads below the base ring.
    """
    meta = data["meta"]
    r = radius(data)
    skirt = meta.get("skirt_height", 0.0) or 0.0
    ground = meta.get("ground_z", 0.0)

    verts = []
    rings = []

    if skirt > 0:
        ring = []
        for j in range(meridians):
            a = 2.0 * math.pi * j / meridians
            ring.append(len(verts))
            verts.append([round(r * math.cos(a), 3), round(r * math.sin(a), 3),
                          round(ground, 3)])
        rings.append(ring)

    # Base ring up to just below the pole, then a single apex vertex.
    for i in range(parallels):
        theta = (math.pi / 2.0) * i / parallels  # 0 at the equator
        z = r * math.sin(theta)
        rr = r * math.cos(theta)
        ring = []
        for j in range(meridians):
            a = 2.0 * math.pi * j / meridians
            ring.append(len(verts))
            verts.append([round(rr * math.cos(a), 3), round(rr * math.sin(a), 3),
                          round(z, 3)])
        rings.append(ring)

    apex = len(verts)
    verts.append([0.0, 0.0, round(r, 3)])

    faces = []
    for a_ring, b_ring in zip(rings, rings[1:]):
        for j in range(meridians):
            k = (j + 1) % meridians
            faces.append([a_ring[j], a_ring[k], b_ring[k], b_ring[j]])
    top = rings[-1]
    for j in range(meridians):
        k = (j + 1) % meridians
        faces.append([top[j], top[k], apex])

    return {
        "vertex_count": len(verts),
        "face_count": len(faces),
        "vertices": verts,
        "faces": faces,
        "note": (
            "Closed surface on the outermost rod radius. The doorway is NOT "
            "cut out of it -- draw doorway.outline over it."
        ),
    }


def analyse(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM) -> dict:
    """Everything about the cover that is shape rather than structure."""
    meta = data["meta"]
    r = radius(data)
    nominal = meta["dome_radius"]
    area = areas(data)
    g = gores(data, roll_width_mm)

    return {
        "radius_mm": round(r, 1),
        "over_nominal_mm": round(r - nominal, 1),
        "over_nominal_pct": round(100.0 * (r * r - nominal * nominal) / (nominal * nominal), 2),
        "areas": area,
        "gores": g,
        "opening": opening(data),
        "note": (
            "Fabric taken as lying on the sphere: no sag between rods, no seam "
            "allowance, no hem. Shape and area only -- nothing here is a wind "
            "or load statement. See docs/cover.md."
        ),
    }


def format_analysis(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM) -> str:
    """The cover, as a page for a person."""
    meta = data["meta"]
    a = analyse(data, roll_width_mm)
    area = a["areas"]
    g = a["gores"]
    lines = [
        f"--- {meta['variant']} cover  (rests at r = {a['radius_mm']:.0f} mm, "
        f"{a['over_nominal_mm']:+.0f} on nominal, {a['over_nominal_pct']:+.1f}% area)",
        f"  dome            {area['dome_m2']:8.2f} m2",
    ]
    if area["skirt_m2"]:
        lines.append(f"  skirt           {area['skirt_m2']:8.2f} m2")
    if a["opening"]["present"]:
        lines.append(f"  less doorway    {-area['doorway_m2']:8.2f} m2")
    lines += [
        f"  total           {area['total_m2']:8.2f} m2",
        "",
        f"  gores           {g['count']} of {g['gore_width_mm']:.0f} x "
        f"{g['gore_length_mm']:.0f} mm, on a {g['roll_width_mm']:.0f} mm roll",
        f"  seams           {g['seam_count']}, {g['seam_length_mm'] / 1000.0:.1f} m total",
        "",
        "  Shape and area only. No sag, no seam allowance, no load claim.",
    ]
    return "\n".join(lines)
