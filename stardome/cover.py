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


def gores(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM,
          radius_mm: float | None = None) -> dict:
    """How few tapered strips the hemisphere can be sewn from.

    The gore is widest at the equator, where the gores between them share the
    equator's whole circumference: ``2 * pi * R / n`` each. That is what has
    to cross the roll, so the roll width sets the minimum count. Fewer gores
    means fewer seams, so the answer wanted is always the smallest ``n`` that
    fits.
    """
    r = radius(data) if radius_mm is None else radius_mm
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


# --------------------------------------------------------------------------
# cutting patterns
# --------------------------------------------------------------------------
# Three ways to make the same skin, and they are not equivalent. Two come
# from the reference (see docs/references.md); the third is what you get if
# you insist every panel is one piece.
PATTERNS = ("faceted", "leaf", "gore")

# Takekawa's own figure, quoted by the reference: make the cover 10% larger if
# it goes over the outside of the structure.
DEFAULT_OVERSIZE = 0.10

# Overlap between horizontal lanes within a leaf. A shingled lap sheds water
# without the joint having to be watertight, which is the whole reason the
# reference prefers leaves for rain. An input, not a derived figure.
DEFAULT_LAP_MM = 80.0

# Regular polygon areas, as multiples of side^2.
PENTAGON_AREA = 1.720477400588967   # (1/4) sqrt(5(5+2 sqrt5))
TRIANGLE_AREA = 0.4330127018922193  # sqrt(3)/4
# A regular pentagon of side s is s*phi across and s*sqrt((5+2sqrt5))/2 tall.
PENTAGON_WIDTH = 1.618033988749895
PENTAGON_HEIGHT = 1.5388417685876268


def facet_side(data: dict) -> float:
    """The side of every cover facet, which the model already carries.

    Half an icosidodecahedron is 6 pentagons and 10 triangles, and its
    equatorial decagons are the G family bows -- so the facet side IS the
    base edge chord, and that is ``R / phi`` exactly.
    """
    return data["meta"]["base_edge_chord"]


def faceted(data: dict, oversize: float = DEFAULT_OVERSIZE,
            roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM) -> dict:
    """The reference's first pattern: 6 pentagons and 10 triangles of side s.

    Every panel is flat, so it develops with no distortion at all -- there is
    no spherical approximation anywhere in it. What it costs is seams, and on
    a narrow roll it costs more than it looks: a pentagon is 1.618*s across,
    which on anything but a small dome is wider than the fabric.

    The reference does not recommend it for weather. Quoted in
    docs/references.md.
    """
    s = facet_side(data) * (1.0 + oversize)
    pent = PENTAGON_AREA * s * s
    tri = TRIANGLE_AREA * s * s
    area = 6.0 * pent + 10.0 * tri

    width = PENTAGON_WIDTH * s
    strips = max(1, math.ceil(width / roll_width_mm))

    return {
        "pattern": "faceted",
        "side_mm": round(s, 1),
        "panels": {"pentagons": 6, "triangles": 10},
        "panel_count": 16,
        "area_m2": round(area / 1e6, 2),
        # 25 internal edges in half an icosidodecahedron: 60 edges, 10 on the
        # equator, the other 50 shared between the two halves.
        "seam_count": 25,
        "seam_length_m": round(25.0 * s / 1000.0, 1),
        "hem_length_m": round(10.0 * s / 1000.0, 1),
        "pentagon_width_mm": round(width, 1),
        "pentagon_fits_roll": width <= roll_width_mm,
        "pentagon_strips": strips,
        "roll_floor_m": round(area / 1e6 / (roll_width_mm / 1000.0), 1),
        "baseline": "inscribed polyhedron, not the sphere",
        "note": (
            "Flat panels, no distortion, and genuinely LESS fabric than the "
            "other two -- it wraps the inscribed polyhedron rather than the "
            "sphere, so it is a different surface and not a like-for-like "
            "saving. The reference calls it interior or "
            "sun-shade only -- too many seams to sew leak-free. And a "
            f"pentagon is {width:.0f} mm across against a "
            f"{roll_width_mm:.0f} mm roll, so it needs piecing too unless the "
            "fabric is wide."
        ),
    }


def leaf(data: dict, leaves: int = 10, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM,
         lap_mm: float = DEFAULT_LAP_MM,
         oversize: float = DEFAULT_OVERSIZE) -> dict:
    """The reference's preferred pattern: 5 or 10 leaves of shingled lanes.

    A leaf is a gore spanning 360/leaves of azimuth, and it is far wider than
    any roll -- so it is built up from horizontal lanes laid overlapping,
    upper over lower, and rain sheds down the slope without the joint having
    to be watertight.

    Roll length is computed rather than assumed: a lane is cut with its
    height across the roll and its width along it, so the roll it eats is the
    leaf's width at that lane, summed.
    """
    if leaves < 3:
        raise ValueError("a leaf cover wants at least three leaves")
    r = radius(data) * (1.0 + oversize)
    slant = math.pi * r / 2.0

    if roll_width_mm - lap_mm <= 0:
        raise ValueError("the lap cannot be as wide as the roll")
    lanes = max(1, math.ceil((slant - lap_mm) / (roll_width_mm - lap_mm)))
    # Divide the slant evenly rather than packing lanes at full roll width and
    # letting the last one hang off the end. Same lane count, no overhang, and
    # every lane is the same piece -- which is also easier to cut.
    step = (slant - lap_mm) / lanes

    def leaf_width(arc):
        return 2.0 * math.pi * r * math.sin(min(arc / r, math.pi / 2.0)) / leaves

    # Each lane is very nearly a trapezoid: narrow at the top, wide at the
    # bottom. Cut one per rectangle and the taper is waste; turn every other
    # one end for end and two lanes share a rectangle, so each costs its MEAN
    # width instead of its widest. That is exact for a straight-sided
    # trapezoid and slightly optimistic here, because the sides are sine
    # curves rather than lines.
    roll_plain = 0.0
    roll_nested = 0.0
    widths = []
    for i in range(lanes):
        s_top = i * step
        s_low = min(slant, (i + 1) * step + lap_mm)
        w_top = leaf_width(s_top)
        w_low = leaf_width(s_low)
        widths.append(round(w_low, 1))
        roll_plain += w_low
        roll_nested += 0.5 * (w_top + w_low)
    roll_plain *= leaves
    roll_nested *= leaves
    roll_mm = roll_nested

    return {
        "pattern": "leaf",
        "leaves": leaves,
        "lanes_per_leaf": lanes,
        "lane_height_mm": round(step + lap_mm, 1),
        # The lane rarely fills the roll's width exactly, and what is left is
        # a continuous strip down the whole run -- the entry triangle and
        # every patch come out of it.
        "offcut_strip_mm": round(roll_width_mm - (step + lap_mm), 1),
        "piece_count": leaves * lanes,
        "lane_widths_mm": widths,
        "lap_mm": lap_mm,
        "area_m2": round(2.0 * math.pi * r * r / 1e6, 2),
        "roll_length_m": round(roll_mm / 1000.0, 1),
        "roll_unnested_m": round(roll_plain / 1000.0, 1),
        "roll_floor_m": round(
            2.0 * math.pi * r * r / 1e6 / (roll_width_mm / 1000.0), 1
        ),
        "leaf_seam_length_m": round(leaves * slant / 1000.0, 1),
        "lap_length_m": round(leaves * sum(widths[:-1]) / 1000.0, 1),
        "note": (
            "Vertical seams run down the slope, where water leaves; the "
            "horizontal joints are laps, not seams. One larger triangle at "
            "the base is the entry, per the reference. Roll length assumes "
            "alternate lanes are turned end for end so two share a "
            "rectangle; cut them all the same way round and it is "
            f"{roll_plain / 1000.0:.1f} m instead."
        ),
    }


def gore_plan(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM,
              oversize: float = DEFAULT_OVERSIZE) -> dict:
    """Every gore in one piece, pole to equator. No horizontal joints at all.

    The clean-looking option, and the expensive one. **A gore fills exactly
    2/pi = 63.66% of its own bounding rectangle**, whatever the radius and
    whatever the gore count, and no nesting recovers it: at the equator the
    gore is already the full width of its strip, so a flipped neighbour has
    nowhere to go. Raising the gore count does not help either -- it only
    leaves more of the roll's width unused.
    """
    r = radius(data) * (1.0 + oversize)
    g = gores(data, roll_width_mm, radius_mm=r)
    slant = math.pi * r / 2.0
    roll_mm = g["count"] * slant
    area = 2.0 * math.pi * r * r
    return {
        "pattern": "gore",
        "count": g["count"],
        "piece_count": g["count"],
        "gore_width_mm": g["gore_width_mm"],
        "gore_length_mm": round(slant, 1),
        "area_m2": round(area / 1e6, 2),
        "roll_length_m": round(roll_mm / 1000.0, 1),
        "seam_length_m": round(g["count"] * slant / 1000.0, 1),
        "fill_of_bounding_box": round(2.0 / math.pi, 6),
        "roll_floor_m": round(area / 1e6 / (roll_width_mm / 1000.0), 1),
        "note": (
            "No horizontal joints. A gore fills 2/pi of its bounding "
            "rectangle exactly, and nesting cannot beat it -- at the equator "
            "the gore is already the full strip width."
        ),
    }


def roll_cost(roll_length_m: float, price_per_m: float) -> dict:
    """What that much roll costs. The price is yours, not the module's."""
    return {
        "roll_length_m": round(roll_length_m, 1),
        "price_per_m": price_per_m,
        "total": round(roll_length_m * price_per_m, 2),
    }


def patterns(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM,
             lap_mm: float = DEFAULT_LAP_MM,
             oversize: float = DEFAULT_OVERSIZE,
             price_per_m: float | None = None) -> dict:
    """All three patterns side by side, so the trade is visible."""
    out = {
        "roll_width_mm": roll_width_mm,
        "oversize": oversize,
        "faceted": faceted(data, oversize, roll_width_mm),
        "leaf_10": leaf(data, 10, roll_width_mm, lap_mm, oversize),
        "leaf_5": leaf(data, 5, roll_width_mm, lap_mm, oversize),
        "gore": gore_plan(data, roll_width_mm, oversize),
    }
    if price_per_m is not None:
        for key in ("leaf_10", "leaf_5", "gore"):
            out[key]["cost"] = roll_cost(out[key]["roll_length_m"], price_per_m)
    return out


def format_patterns(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM,
                    lap_mm: float = DEFAULT_LAP_MM,
                    oversize: float = DEFAULT_OVERSIZE,
                    price_per_m: float | None = None) -> str:
    """The cutting patterns, as a page for a person."""
    meta = data["meta"]
    p = patterns(data, roll_width_mm, lap_mm, oversize, price_per_m)
    f, l10, l5, g = p["faceted"], p["leaf_10"], p["leaf_5"], p["gore"]

    alias = meta.get("alias")
    name = f"{alias} ({meta['variant']})" if alias else meta["variant"]
    lines = [
        f"--- {name} cover patterns  "
        f"({roll_width_mm:.0f} mm roll, +{oversize * 100:.0f}% oversize)",
        "",
        f"  {'':<10}{'pieces':>8}{'area m2':>10}{'roll m':>9}{'floor':>8}"
        f"{'seam m':>9}{'cost':>10}",
    ]

    def row(name, pieces, area, roll, seam, plan):
        cost = plan.get("cost")
        money = f"{cost['total']:.0f}" if cost else "--"
        roll_s = f"{roll:.1f}" if roll else "--"
        floor = f"{plan['roll_floor_m']:.1f}"
        return (f"  {name:<10}{pieces:>8}{area:>10.2f}{roll_s:>9}{floor:>8}"
                f"{seam:>9.1f}{money:>10}")

    lines.append(row("faceted", f["panel_count"], f["area_m2"], None,
                     f["seam_length_m"], f))
    lines.append(row("leaf x10", l10["piece_count"], l10["area_m2"],
                     l10["roll_length_m"], l10["leaf_seam_length_m"], l10))
    lines.append(row("leaf x5", l5["piece_count"], l5["area_m2"],
                     l5["roll_length_m"], l5["leaf_seam_length_m"], l5))
    lines.append(row("gore", g["piece_count"], g["area_m2"],
                     g["roll_length_m"], g["seam_length_m"], g))

    lines += [
        "",
        f"  faceted   6 pentagons + 10 triangles, side {f['side_mm']:.0f} mm "
        f"(= R/phi, the model's own base edge)",
        f"            flat panels, no distortion -- but a pentagon is "
        f"{f['pentagon_width_mm']:.0f} mm across, so on this roll it needs "
        f"{f['pentagon_strips']} strip(s) of its own.",
        "            The reference calls this interior / sun-shade only: too "
        "many seams to sew leak-free.",
        "",
        f"  leaf      the reference's choice for rain. {l10['lanes_per_leaf']} "
        f"lanes per leaf, lapped {l10['lap_mm']:.0f} mm.",
        "            Vertical seams run down the slope where water leaves; "
        "the horizontal joints are laps, not seams.",
        f"            Lanes are nested end for end, two to a rectangle. Cut "
        f"them all one way round and it is {l10['roll_unnested_m']:.1f} m.",
        "",
        f"  gore      one piece per gore, no horizontal joints -- and "
        f"{g['fill_of_bounding_box'] * 100:.1f}% of the roll used.",
        "            A gore fills 2/pi of its bounding rectangle exactly, at "
        "any radius and any count, and",
        "            nesting cannot beat it: at the equator the gore is "
        "already the full strip width.",
    ]
    lines += [
        "",
        "  floor is area / roll width: the roll you would buy if fabric came "
        "in the shape you wanted.",
        "  faceted's area is measured against the INSCRIBED polyhedron, not "
        "the sphere -- a different",
        "  surface, so its smaller figure is not a like-for-like saving.",
    ]
    if price_per_m is None:
        lines += ["", "  Pass --price to cost it; the price per metre is yours, not mine."]
    return "\n".join(lines)


def summary_row(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM,
                lap_mm: float = DEFAULT_LAP_MM,
                oversize: float = DEFAULT_OVERSIZE,
                price_per_m: float | None = None,
                leaves: int = 5) -> dict:
    """One size, one line: what the recommended pattern actually costs.

    The leaf at five is the pattern the reference prefers and the numbers
    agree with, so that is what a summary quotes. The gore is carried
    alongside because the difference between them is the point.
    """
    meta = data["meta"]
    l = leaf(data, leaves, roll_width_mm, lap_mm, oversize)
    g = gore_plan(data, roll_width_mm, oversize)
    row = {
        "variant": meta["variant"],
        "alias": meta.get("alias"),
        "diameter_mm": meta["dome_diameter"],
        "skirt_mm": meta.get("skirt_height", 0.0) or 0.0,
        "area_m2": l["area_m2"],
        "leaves": leaves,
        "pieces": l["piece_count"],
        "roll_m": l["roll_length_m"],
        "seam_m": l["leaf_seam_length_m"],
        "gore_roll_m": g["roll_length_m"],
        "gore_seam_m": g["seam_length_m"],
        # What you actually buy. Running metres are only comparable within one
        # roll width; area is comparable across widths, and a wider roll does
        # not cost the same per metre as a narrow one.
        "bought_m2": round(l["roll_length_m"] * roll_width_mm / 1000.0, 1),
        "waste_m2": round(
            l["roll_length_m"] * roll_width_mm / 1000.0 - l["area_m2"], 1
        ),
    }
    if price_per_m is not None:
        row["cost"] = round(l["roll_length_m"] * price_per_m, 2)
        row["gore_cost"] = round(g["roll_length_m"] * price_per_m, 2)
        row["saved"] = round(row["gore_cost"] - row["cost"], 2)
    return row


def format_summary(rows: list, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM,
                   oversize: float = DEFAULT_OVERSIZE,
                   price_per_m: float | None = None) -> str:
    """Several sizes on one page, for choosing between them."""
    priced = price_per_m is not None
    head = (
        f"--- cover, leaf pattern  ({roll_width_mm:.0f} mm roll, "
        f"+{oversize * 100:.0f}% oversize"
        + (f", {price_per_m:g} per metre)" if priced else ")")
    )
    lines = [
        head,
        "",
        f"  {'size':<10}{'across':>9}{'area m2':>10}{'bought':>9}{'pieces':>8}"
        f"{'roll m':>9}{'seam m':>9}" + (f"{'cost':>10}{'vs gore':>10}" if priced else ""),
    ]
    for r in rows:
        name = r["alias"] or r["variant"]
        if r["alias"]:
            name = f"{r['alias']} {r['variant']}"
        across = f"{r['diameter_mm'] / 1000.0:.0f} m"
        if r["skirt_mm"]:
            across += f"+{r['skirt_mm'] / 1000.0:.2f}"
        money = ""
        if priced:
            money = f"{r['cost']:>10.0f}{r['saved']:>+10.0f}"
        lines.append(
            f"  {name:<10}{across:>9}{r['area_m2']:>10.2f}{r['bought_m2']:>9.1f}"
            f"{r['pieces']:>8}{r['roll_m']:>9.1f}{r['seam_m']:>9.1f}{money}"
        )
    lines += [
        "",
        f"  Leaf of {rows[0]['leaves']} if any, lanes lapped and nested end for end.",
        "  'vs gore' is what the one-piece gore pattern would add.",
        "  'bought' is roll m x roll width -- the fabric you pay for, waste "
        "included.",
        "  Most of that waste is one continuous strip down the run, where the "
        "lane is shorter than the",
        "  roll is wide. The entry triangle and every patch come out of it.",
        "  Running metres compare only WITHIN one roll width: a wider roll is "
        "not the same price",
        "  per metre. To compare widths, price the bought area instead.",
        "  Price per metre is yours; area includes the oversize, not seam "
        "allowance or hem.",
    ]
    return "\n".join(lines)
