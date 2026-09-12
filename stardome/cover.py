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
# How many rods meet at a lashed node, and how close two vertices must be to
# the base chord to count as an edge of the face cut.
FOUR_ROD = 4
EDGE_TOL = 1.0

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
    """The holes the doorways make in the cover.

    Each bay's open area is what the fabric loses there; each outline is what
    it is cut to. Both come from ``doorway`` -- this module does not
    rediscover which bay a door is in. A dome may have several, so the totals
    are sums and ``each`` carries them one by one.
    """
    from . import doorway as _doorway

    doors = _doorway.doors_on(data)
    if not doors:
        return {
            "area_mm2": 0.0,
            "area_m2": 0.0,
            "count": 0,
            "each": [],
            "present": False,
            "note": "no doorway on this variant",
        }
    each = []
    for door in doors:
        bay = door["bay"]
        outline = door.get("outline") or {}
        each.append(
            {
                "area_m2": bay["open_area_m2"],
                "centre_azimuth_deg": bay["centre_azimuth_deg"],
                "span_deg": bay["span_deg"],
                "outline_points": outline.get("point_count", 0),
            }
        )
    total = sum(e["area_m2"] for e in each)
    first = each[0]
    return {
        "present": True,
        "count": len(each),
        "each": each,
        "area_mm2": total * 1e6,
        "area_m2": round(total, 6),
        # The first door is what "the doorway" means to anything that was
        # written before a dome could have two -- the seam phase above all.
        "centre_azimuth_deg": first["centre_azimuth_deg"],
        "span_deg": first["span_deg"],
        "outline_points": first["outline_points"],
        "note": (
            "Cut to each doorway outline, which traces the two framing bows "
            "and the ground. The cover loses this area; the door panels are "
            "made of it."
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


def panel_faces(data: dict) -> dict:
    """The cover cut to the dome's own faces, instead of to meridian strips.

    This dome is not a smooth sphere with a lattice drawn on it. Its ten feet
    and its ten lashed nodes are the twenty vertices of an **icosidodecahedron
    hemisphere** -- the edge is the base chord, R/phi, 1854.1 mm on M -- and
    its faces are six pentagons and ten triangles, every edge the same length.

    That is the cover the reference cuts, and it took going back to the source
    to notice: `gores` is the answer for a sphere, and this is not one.

    What it buys is that **25 of the 35 edges lie along the G bows**. The other
    ten are the base ring, where there is no rod and no second panel -- that
    edge is the hem. So a seam here is not merely a join in cloth: it lands on
    a member, and the panel corners land on the two connectors that already
    exist, the base hub and the four-rod fan.

    Derived, not asserted: the vertices come from the model, the edges from
    the distances between them, and the faces from walking the rotation system
    of the graph. If the topology ever stopped being an icosidodecahedron this
    would return something other than 6 and 10, and the tests say so.
    """
    from . import vec

    edge = data["meta"]["base_edge_chord"]
    points = {
        n["name"]: (n["x"], n["y"], n["z"])
        for n in data["nodes"]
        if n["rod_count"] == FOUR_ROD
    }
    points.update(
        {b["name"]: (b["x"], b["y"], b["z"]) for b in data["base_nodes"]}
    )
    names = sorted(points)

    neighbours: dict = {name: [] for name in names}
    edges = []
    for i, one in enumerate(names):
        for other in names[i + 1:]:
            if abs(_distance(points[one], points[other]) - edge) < EDGE_TOL:
                neighbours[one].append(other)
                neighbours[other].append(one)
                edges.append((one, other))

    # Sort each vertex's neighbours by angle in its own tangent plane, which
    # turns the graph into a surface and lets the faces be walked off it.
    for name in names:
        normal = vec.unit(points[name])
        ref = (0.0, 0.0, 1.0) if abs(normal[2]) < 0.9 else (1.0, 0.0, 0.0)
        e1 = vec.unit(vec.cross(ref, normal))
        e2 = vec.cross(normal, e1)

        def angle(other, here=name, u=e1, v=e2):
            delta = tuple(
                points[other][k] - points[here][k] for k in range(3)
            )
            return math.atan2(vec.dot(delta, v), vec.dot(delta, u))

        neighbours[name].sort(key=angle)

    following = {}
    for name in names:
        ring = neighbours[name]
        for i, other in enumerate(ring):
            following[(other, name)] = ring[(i - 1) % len(ring)]

    seen: set = set()
    walked = []
    for start in list(following):
        if start in seen:
            continue
        face, step = [], start
        while step not in seen:
            seen.add(step)
            face.append(step[0])
            step = (step[1], following[step])
        walked.append(face)

    # The longest walk is the outside of the hemisphere -- the base ring. It
    # is not a panel; it is the hole the dome stands in, and the hem.
    walked.sort(key=len)
    boundary = walked[-1]
    faces = walked[:-1]

    by_size: dict = {}
    for face in faces:
        by_size.setdefault(len(face), []).append(sorted(face))

    on_bow = 0
    rods_at = {n["name"]: set(n["rods"]) for n in data["nodes"]}
    rods_at.update({b["name"]: set(b["rods"]) for b in data["base_nodes"]})
    for one, other in edges:
        if rods_at[one] & rods_at[other]:
            on_bow += 1

    return {
        "vertices": len(names),
        "edge_mm": round(edge, 3),
        "edges": len(edges),
        "edges_on_a_bow": on_bow,
        "edges_on_the_base_ring": len(edges) - on_bow,
        "faces": len(faces),
        "by_sides": {k: len(v) for k, v in sorted(by_size.items())},
        "panels": {k: v for k, v in sorted(by_size.items())},
        "boundary": sorted(boundary),
        "note": (
            "An icosidodecahedron hemisphere: 20 vertices, 35 edges all of "
            "R/phi, 6 pentagons and 10 triangles. Every seam but the base "
            "ring lies on a bow of family G."
        ),
    }


def _distance(one, other) -> float:
    return math.sqrt(sum((one[k] - other[k]) ** 2 for k in range(3)))


def _regular(sides: int, edge: float) -> list:
    """A regular polygon of this many sides, turned so its narrowest way across
    lies along x -- which is the way it has to lie on a roll."""
    circum = edge / (2.0 * math.sin(math.pi / sides))
    # The narrowest direction is across a flat. Put that on x by starting the
    # first vertex a half-step round.
    start = math.pi / 2.0 + (math.pi / sides if sides % 2 else 0.0)
    return [
        (
            circum * math.cos(2.0 * math.pi * k / sides + start),
            circum * math.sin(2.0 * math.pi * k / sides + start),
        )
        for k in range(sides)
    ]


def _min_width(sides: int, edge: float) -> float:
    """Narrowest strip a regular polygon fits in.

    Across the flats for an even count, flat-to-vertex for an odd one -- which
    is why a pentagon's 2853 mm and not the 3154 mm of its long diagonal. Get
    that wrong and the pentagon looks like it needs three strips of a 1500 mm
    roll when it needs two.
    """
    circum = edge / (2.0 * math.sin(math.pi / sides))
    if sides % 2 == 0:
        return 2.0 * circum * math.cos(math.pi / sides)
    return circum * (1.0 + math.cos(math.pi / sides))


def _chord(polygon: list, x: float) -> float:
    """How long a straight cut across the polygon at this x is.

    Measured rather than approximated by the circumdiameter, which overstates
    a pentagon's mid-cut by 13% -- and that difference is metres of seam on a
    cover with six of them.
    """
    ys = []
    for i in range(len(polygon)):
        one, other = polygon[i], polygon[(i + 1) % len(polygon)]
        if (one[0] - x) * (other[0] - x) < 0.0:
            t = (x - one[0]) / (other[0] - one[0])
            ys.append(one[1] + t * (other[1] - one[1]))
    return max(ys) - min(ys) if len(ys) >= 2 else 0.0


def panels(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM) -> dict:
    """The face cut, priced against a roll: pieces, strips and seam length.

    A panel wider than the roll is cut in strips and sewn back together, which
    is cheap -- a pentagon on a 1500 mm roll is one extra seam of 2.8 m -- but
    those seams land nowhere, unlike the 25 that lie on bows.
    """
    faces = panel_faces(data)
    edge = faces["edge_mm"]

    pieces = 0
    internal_mm = 0.0
    breakdown = {}
    for sides, count in faces["by_sides"].items():
        width = _min_width(sides, edge)
        strips = max(1, math.ceil(width / roll_width_mm))
        seam_each = 0.0
        if strips > 1:
            shape = _regular(sides, edge)
            left = min(point[0] for point in shape)
            for k in range(1, strips):
                seam_each += _chord(shape, left + width * k / strips)
        pieces += strips * count
        internal_mm += seam_each * count
        breakdown[sides] = {
            "count": count,
            "min_width_mm": round(width, 1),
            "strips": strips,
            "pieces": strips * count,
            "internal_seam_each_mm": round(seam_each, 1),
        }

    seam_mm = faces["edges_on_a_bow"] * edge
    return {
        "roll_width_mm": round(roll_width_mm, 1),
        "faces": faces["faces"],
        "by_sides": faces["by_sides"],
        "pieces": pieces,
        "edge_mm": edge,
        "panel_seam_mm": round(seam_mm, 1),
        "internal_seam_mm": round(internal_mm, 1),
        "seam_length_mm": round(seam_mm + internal_mm, 1),
        "seams_on_a_bow": faces["edges_on_a_bow"],
        "hem_mm": round(faces["edges_on_the_base_ring"] * edge, 1),
        "shapes": breakdown,
        "note": (
            "Seams that land on a member, and panel corners that land on the "
            "base hub and the four-rod fan. Flat faces come to less area than "
            "the sphere they cover, so a panel wants easing -- the reference "
            "says 10% -- and that is not in these numbers."
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


def layouts(data: dict, roll_width_mm: float = DEFAULT_ROLL_WIDTH_MM) -> dict:
    """The two ways to cut this cover, side by side on one roll.

    Kept together because the choice is not obvious and the numbers move with
    the roll. Gores are the answer for a sphere; faces are the answer for this
    dome, which is an icosidodecahedron with bows on its edges. On a narrow
    roll the faces cost more seam, on a wide one they cost less, and the
    crossover is close enough to standard fabric to be worth recomputing
    rather than remembering.
    """
    strips = gores(data, roll_width_mm)
    faces = panels(data, roll_width_mm)
    hem = 2.0 * math.pi * radius(data)
    return {
        "roll_width_mm": round(roll_width_mm, 1),
        "gores": {
            "pieces": strips["count"],
            "shapes": 1,
            "seam_mm": strips["seam_length_mm"],
            "seams_on_a_bow": 0,
            "hem_mm": round(hem, 1),
            "piece_mm": [strips["gore_width_mm"], strips["gore_length_mm"]],
            "crown": (
                f"{strips['count']} seams meet at a point; wants a crown patch"
            ),
        },
        "faces": {
            "pieces": faces["pieces"],
            "shapes": len(faces["by_sides"]),
            "seam_mm": faces["seam_length_mm"],
            "seams_on_a_bow": faces["seams_on_a_bow"],
            "hem_mm": faces["hem_mm"],
            "piece_mm": [faces["edge_mm"]] * 2,
            "crown": "a pentagon; nothing converges",
        },
        "note": (
            "Seam totals exclude the hem, which both need and which is the "
            "same length either way. Neither includes seam allowance, and "
            "the face cut's flat panels want easing onto the sphere."
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
        "panels": panels(data, roll_width_mm),
        "layouts": layouts(data, roll_width_mm),
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
        f"  two ways to cut it, on a {roll_width_mm:.0f} mm roll:",
        "",
        "                  pieces  shapes   seam    on a bow   crown",
    ]
    for label, cut in (("gores", a["layouts"]["gores"]),
                       ("faces", a["layouts"]["faces"])):
        lines.append(
            f"  {label:<14}{cut['pieces']:>5}{cut['shapes']:>8}"
            f"{cut['seam_mm'] / 1000.0:>8.1f} m{cut['seams_on_a_bow']:>9}"
            f"   {cut['crown']}"
        )
    faces = a["panels"]
    lines += [
        "",
        f"  gore            {g['gore_width_mm']:.0f} x {g['gore_length_mm']:.0f} mm, "
        f"tapered, every section a different width",
        f"  face            {faces['edge_mm']:.1f} mm every edge; "
        + ", ".join(
            f"{v['count']}x{k}-sided in {v['strips']} strip(s)"
            for k, v in faces["shapes"].items()
        ),
        f"  hem             {a['layouts']['gores']['hem_mm'] / 1000.0:.1f} m, "
        "the same either way",
        "",
        "  Shape and area only. No sag, no seam allowance, no load claim.",
    ]
    return "\n".join(lines)
