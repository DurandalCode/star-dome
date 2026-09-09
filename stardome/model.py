"""Assemble the whole-dome model and serialise it.

The output dict is schema ``star_dome_geometry/1`` -- the same schema the
OpenSCAD model emits, so the two producers are interchangeable and can be
diffed against each other. See docs/architecture.md.

This module is the only place that knows the wire format. Geometry lives in
``geometry`` and ``topology``; consumers (OpenSCAD, FreeCAD, Blender) read the
serialised file and never recompute any of it.
"""

from __future__ import annotations

import math

from . import SCHEMA_VERSION, __version__, geometry, topology
from .config import Variant

SCHEMA = f"star_dome_geometry/{SCHEMA_VERSION}"

DP = 6


def _r(x: float) -> float:
    return round(x, DP)


def _skirt(variant, base_pts: list, radius: float) -> dict:
    """Posts, two rings and the diagonals that stop the thing racking.

    A ring of pin-ended verticals is a mechanism: every bay is a parallelogram
    and the whole skirt folds over under any sideways load. Three things fix
    that, and all three are members the earlier drawing did not have.

    **The top ring** is not only the skirt's. A dome pushes *outward* at its
    feet, and the ten base points of a bare Star Dome are ten free rod ends
    with nothing tying them to each other. Something has to take that thrust
    in hoop tension whether there is a skirt underneath or not; putting it at
    the top of the skirt is just where it happens to live here.

    **The bottom ring** closes the other end of every post so the bay is a
    quadrilateral rather than two free-standing legs.

    **The diagonals** triangulate each bay. They are declared as *tension*
    members rather than rod, because the one member in this structure that
    can buckle is a 1.8 m diagonal in compression, and a strap cannot buckle.
    Two per bay, so that whichever way the skirt is pushed one of them is in
    tension and the other simply goes slack.

    Both rings are chords between adjacent posts, not hoops: a hoop would have
    to be bent to the base radius, and the posts already define a polygon.
    """
    height = variant.skirt_height
    ground_z = -height
    count = len(base_pts)

    posts = [
        {
            "name": f"s{i}",
            "base_node": f"b{i}",
            "x": _r(p[0]),
            "y": _r(p[1]),
            "z_bottom": _r(ground_z),
            "z_top": _r(p[2]),
            "length": _r(height),
        }
        for i, p in enumerate(base_pts)
    ]

    def ring(z: float, tag: str) -> list:
        out = []
        for i, p in enumerate(base_pts):
            q = base_pts[(i + 1) % count]
            out.append(
                {
                    "name": f"{tag}{i}",
                    "bay": i,
                    "from": f"b{i}" if z == 0.0 else f"s{i}",
                    "to": f"b{(i + 1) % count}" if z == 0.0 else f"s{(i + 1) % count}",
                    "a": [_r(p[0]), _r(p[1]), _r(z)],
                    "b": [_r(q[0]), _r(q[1]), _r(z)],
                    "length": _r(math.dist(p[:2], q[:2])),
                }
            )
        return out

    top_ring = ring(0.0, "tr")
    bottom_ring = ring(ground_z, "br")

    braces = []
    for i, p in enumerate(base_pts):
        q = base_pts[(i + 1) % count]
        span = math.dist(p[:2], q[:2])
        length = math.hypot(span, height)
        for sense, (lo, hi) in enumerate(((p, q), (q, p))):
            braces.append(
                {
                    "name": f"d{i}{'ab'[sense]}",
                    "bay": i,
                    "a": [_r(lo[0]), _r(lo[1]), _r(ground_z)],
                    "b": [_r(hi[0]), _r(hi[1]), _r(0.0)],
                    "length": _r(length),
                    "angle_deg": _r(math.degrees(math.atan2(height, span))),
                    "member": "tension",
                }
            )

    return {
        "height": _r(height),
        "ground_z": _r(ground_z),
        "post_count": count,
        "bay_count": count,
        "posts": posts,
        "top_ring": top_ring,
        "bottom_ring": bottom_ring,
        "braces": braces,
        "open_bays": [],
        "post_total_length": _r(height * count),
        "top_ring_length": _r(sum(seg["length"] for seg in top_ring)),
        "bottom_ring_length": _r(sum(seg["length"] for seg in bottom_ring)),
        "brace_total_length": _r(sum(b["length"] for b in braces)),
        "brace_angle_deg": _r(braces[0]["angle_deg"]) if braces else 0.0,
        # Kept for consumers that read the old field; it is the hoop, which is
        # not what gets built -- the ring is chords.
        "ground_ring_length": _r(2.0 * math.pi * radius),
        "note": (
            "Posts, a ring at each end and two tension diagonals per bay. The "
            "top ring also takes the dome's outward thrust at its feet, which "
            "nothing else in this model does. The diagonals are declared as "
            "tension members: the only thing here that can buckle is a "
            "diagonal in compression, and a strap cannot. See docs/skirt.md."
        ),
    }


def _on_bow_at_height(bow, radius: float, foot, z_target: float, steps: int = 4000):
    """The point on a bow at a given height, on the branch leaving ``foot``.

    A bow crosses any height twice; the one that matters for a door header is
    the leg that starts at the base point beside the doorway.
    """
    t0 = bow.t_of(tuple(foot))
    direction = 1.0 if t0 < 90.0 else -1.0
    best = None
    for i in range(steps + 1):
        t = t0 + direction * 180.0 * i / steps
        p = bow.point(t, radius)
        if p[2] < 0.0:
            continue
        if best is None or abs(p[2] - z_target) < abs(best[2] - z_target):
            best = p
        if p[2] > z_target + 0.1 * radius:
            break
    return best


def _open_door_bay(skirt: dict, data: dict, radius: float, head_room: float = 150.0):
    """Take the ring segments out of the door bay and put a header over it.

    Removing the diagonals is not enough to make a doorway: both rings still
    run straight across the bay, one along the ground to trip on and one at
    the top of the skirt, right at head height. Neither is a hole.

    So the bay loses both chords, and the hoop force that the top ring was
    carrying takes a detour over the opening: post head -> the U bow rising
    from that base point -> a header between the two U bows -> down the other
    side. That is a portal frame, and it puts bending into the two U bows near
    their feet, which is a statics question this model does not answer.

    The header sits above the tallest silhouette the opening actually
    **admits**, not above the one it is nominally sized for. Those are not the
    same: S is sized for someone carrying something at 1800 mm but its portal
    passes a 2.2 m character, and a header placed on the nominal figure takes
    that back -- a lintel that blocks what the doorway was letting through.
    It is still never put above the dome's own opening, where it would be
    carrying nothing over anything.
    """
    from . import geometry

    door = data.get("doorway")
    if not door or not skirt["open_bays"]:
        return
    bay = skirt["open_bays"][0]
    count = skirt["bay_count"]

    skirt["top_ring"] = [seg for seg in skirt["top_ring"] if seg["bay"] != bay]
    skirt["bottom_ring"] = [seg for seg in skirt["bottom_ring"] if seg["bay"] != bay]
    skirt["top_ring_length"] = _r(sum(seg["length"] for seg in skirt["top_ring"]))
    skirt["bottom_ring_length"] = _r(
        sum(seg["length"] for seg in skirt["bottom_ring"])
    )

    base = {b["name"]: b for b in data["base_nodes"]}
    feet = [
        base[skirt["posts"][bay]["base_node"]],
        base[skirt["posts"][(bay + 1) % count]["base_node"]],
    ]
    jambs = []
    for foot in feet:
        u = [r for r in foot["rods"] if r.startswith("U")]
        if len(u) != 1:
            return
        jambs.append(u[0])

    # How high the header has to be, measured from the ground, and how high it
    # is allowed to be before it stops being over the doorway at all.
    from . import entrance

    admitted = door.get("admits") or []
    if admitted:
        wanted = max(
            max(z for z, _ in entrance.TEMPLATES[name]) for name in admitted
        )
    else:
        template = data["meta"].get("door_template", "")
        wanted = (
            max(z for z, _ in entrance.TEMPLATES[template]) if template else 1800.0
        )
    # Keep it under the dome's own lintel rather than in it.
    ceiling = (
        door["in_bay"]["clear_height_mm"]
        + skirt["height"]
        - data["meta"]["rod_diameter"]
    )
    above_ground = min(wanted + head_room, ceiling)
    z = above_ground - skirt["height"]  # back into base-ring coordinates

    bows = {b.name: b for b in geometry.build_bows()}
    ends = [
        _on_bow_at_height(bows[rod], radius, (f["x"], f["y"], f["z"]), z)
        for rod, f in zip(jambs, feet)
    ]
    if any(e is None for e in ends):
        return

    skirt["header"] = {
        "name": "hd",
        "bay": bay,
        "rods": jambs,
        "a": [_r(c) for c in ends[0]],
        "b": [_r(c) for c in ends[1]],
        "length": _r(math.dist(ends[0], ends[1])),
        "height_above_ground": _r(above_ground),
        "clears_mm": _r(wanted),
        "note": (
            "Carries the top ring's hoop force over the doorway: post head, up "
            "the U bow, across, and down the other side. A portal frame, so it "
            "bends the two U bows near their feet -- unchecked here."
        ),
    }


def build(
    variant: Variant,
    weave_mode: str = "flat",
    include_polylines: bool = False,
) -> dict:
    """Compute the complete model for one variant.

    ``weave_mode="flat"`` puts every centreline on the nominal sphere and is
    the basis for all exported coordinates. ``"layered"`` only changes the
    reported per-rod offsets and radial gaps.
    """
    radius = variant.radius
    bows = geometry.build_bows()

    xs = topology.crossings(
        bows,
        radius,
        rod_diameter=variant.rod_diameter,
        weave_mode=weave_mode,
        weave_gap=variant.weave_gap,
    )
    node_points = topology.nodes(xs)
    topology.assign_nodes(xs, node_points)
    class_sigs = topology.classes(xs)

    offsets = topology._radial_offsets(
        bows, variant.rod_diameter, weave_mode, variant.weave_gap
    )

    rods = []
    for b in bows:
        drawn_radius = radius + offsets[b.name]
        marks = b.tie_marks_deg()
        rod = {
            "number": b.number,
            "name": b.name,
            "family": b.family,
            "foot_a": b.foot_a,
            "foot_b": b.foot_b,
            "azimuth_deg": _r(b.azimuth_deg),
            "tilt_deg": _r(b.tilt_deg),
            "length_nominal": _r(math.pi * radius),
            "length_drawn": _r(math.pi * drawn_radius),
            "layer": b.layer,
            "radial_offset": _r(offsets[b.name]),
            "tie_marks_deg": [_r(m) for m in marks],
            "tie_marks_mm": [_r(radius * math.radians(m)) for m in marks],
        }
        if include_polylines:
            rod["points"] = [
                [_r(c) for c in p]
                for p in b.polyline(drawn_radius, variant.rod_segments)
            ]
        rods.append(rod)

    base_pts = geometry.base_points(radius)
    base_nodes = [
        {
            "index": i,
            "name": f"b{i}",
            "x": _r(p[0]),
            "y": _r(p[1]),
            "z": _r(p[2]),
            "rods": topology.rods_at_base_point(bows, i),
        }
        for i, p in enumerate(base_pts)
    ]

    nodes = []
    for i, p in enumerate(node_points):
        names = topology.rods_at_node(xs, i, bows)
        nodes.append(
            {
                "index": i,
                "name": topology.node_name(i),
                "x": _r(p[0]),
                "y": _r(p[1]),
                "z": _r(p[2]),
                "rod_count": len(names),
                "rods": names,
            }
        )

    crossings = []
    for c in xs:
        crossings.append(
            {
                "index": c.index,
                "node": topology.node_name(c.node),
                "rod_a": c.bow_a.name,
                "rod_b": c.bow_b.name,
                "family_a": c.bow_a.family,
                "family_b": c.bow_b.family,
                "x": _r(c.point[0]),
                "y": _r(c.point[1]),
                "z": _r(c.point[2]),
                "t_a_deg": _r(c.t_a),
                "t_b_deg": _r(c.t_b),
                "s_a_mm": _r(c.bow_a.arclength(c.t_a, radius)),
                "s_b_mm": _r(c.bow_b.arclength(c.t_b, radius)),
                "tan_a_x": _r(c.tangent_a[0]),
                "tan_a_y": _r(c.tangent_a[1]),
                "tan_a_z": _r(c.tangent_a[2]),
                "tan_b_x": _r(c.tangent_b[0]),
                "tan_b_y": _r(c.tangent_b[1]),
                "tan_b_z": _r(c.tangent_b[2]),
                "angle_deg": _r(c.angle),
                "incl_a_deg": _r(c.incl_a),
                "incl_b_deg": _r(c.incl_b),
                "rod_above": c.rod_above,
                "rod_below": c.rod_below,
                "radial_gap": _r(c.radial_gap),
                "tied": c.tied,
                "type": topology.type_name(c.type_index),
            }
        )

    crossing_types = []
    for i in range(len(class_sigs)):
        members = [c for c in xs if c.type_index == i]
        rep = members[0]
        # Every per-rod field in this record -- family, inclination, arc
        # position -- refers to the representative crossing in its own rod
        # order, the same order example_rods names. The signature sorts the
        # family pair for grouping only; using that sorted order here would
        # label the "a" columns with one rod's family and another rod's
        # angles. See docs/architecture.md, "Divergences from the OpenSCAD
        # exporter".
        crossing_types.append(
            {
                "index": i,
                "name": topology.type_name(i),
                "count": len(members),
                "family_a": rep.bow_a.family,
                "family_b": rep.bow_b.family,
                "z": _r(rep.point[2]),
                "angle_deg": _r(rep.angle),
                "incl_a_deg": _r(rep.incl_a),
                "incl_b_deg": _r(rep.incl_b),
                "t_a_deg": _r(rep.t_a),
                "t_b_deg": _r(rep.t_b),
                "tied": rep.tied,
                "example_rods": [rep.bow_a.name, rep.bow_b.name],
            }
        )

    # The skirt. The dome frame keeps its base ring at z = 0, so the skirt
    # hangs below it and the ground is at negative z. That deliberately leaves
    # every crossing, node and tangent in the frame the geometry was derived
    # in, where the sphere is centred on the origin -- offsetting the dome
    # instead would quietly break the node-frame maths in weave.py, which
    # takes the radius vector to be the position vector.
    skirt = None
    if variant.skirt_height > 0:
        skirt = _skirt(variant, base_pts, radius)

    length_classes = sorted({r["length_drawn"] for r in rods})
    max_drawn_radius = max(radius + o for o in offsets.values())
    tilt_u = geometry.family_tilts()["U"]
    height_measured = max(
        (radius + offsets[b.name]) * math.sin(math.radians(b.tilt_deg)) for b in bows
    )

    meta = {
        "variant": variant.name,
        "variant_note": variant.note,
        "units": "mm",
        "dome_diameter": _r(variant.diameter),
        "dome_radius": _r(radius),
        "rod_diameter": _r(variant.rod_diameter),
        "weave_mode": weave_mode,
        "weave_gap": _r(variant.weave_gap),
        "rod_segments": variant.rod_segments,
        "rod_count": len(rods),
        "base_node_count": len(base_nodes),
        "crossing_point_count": len(nodes),
        "crossing_pair_count": len(crossings),
        "crossing_type_count": len(crossing_types),
        "rod_length_nominal": _r(math.pi * radius),
        "rod_length_class_count": len(length_classes),
        "rod_length_classes": length_classes,
        "total_rod_length": _r(sum(r["length_drawn"] for r in rods)),
        "base_ring_length": _r(2.0 * math.pi * radius),
        "dome_height_nominal": _r(radius * math.sin(math.radians(tilt_u))),
        "dome_height_measured": _r(height_measured),
        "max_diameter_measured": _r(2.0 * max_drawn_radius),
        "max_diameter_incl_rod": _r(2.0 * max_drawn_radius + variant.rod_diameter),
        "base_edge_arc": _r(2.0 * math.pi * radius / geometry.BASE_POINT_COUNT),
        "base_edge_chord": _r(2.0 * radius * math.sin(math.radians(18.0))),
        "alias": variant.alias,
        "skirt_height": _r(variant.skirt_height),
        "ground_z": _r(-variant.skirt_height),
        "overall_height": _r(variant.overall_height),
        "door_template": variant.door,
        "door_cut": variant.door_cut,
        "coordinate_basis": (
            "nominal centreline on the sphere (same as weaveMode=flat); "
            "weave offsets are reported per crossing as radial_gap"
        ),
        "inclination_convention": (
            "unsigned angle of the rod tangent above horizontal, 0..90 deg"
        ),
        "above_convention": (
            "the rod on the outer weave shell (higher layer index); "
            "a drawing convention, not a build decision"
        ),
    }

    out = {
        "meta": meta,
        "rods": rods,
        "base_nodes": base_nodes,
        "nodes": nodes,
        "crossings": crossings,
        "crossing_types": crossing_types,
        "schema": SCHEMA,
        "source": f"stardome/{__version__}",
    }
    if skirt is not None:
        out["skirt"] = skirt
    if variant.door:
        # Computed last, because choosing the doorway means reading the model
        # back: which bay is tall, which node heads it, which rods frame it.
        # Consumers get the opening as finished geometry and never rediscover
        # it -- the same contract the rest of this file keeps.
        from . import doorway

        out["doorway"] = doorway.place(out, variant.door, cut=variant.door_cut)

        if skirt is not None:
            # The bay under the door cannot be braced: a diagonal across the
            # doorway is a doorway with a diagonal across it. The rings still
            # close round it, so the rest of the skirt holds this bay square.
            centre = out["doorway"]["bay"]["centre_azimuth_deg"]
            best = None
            for i, post in enumerate(skirt["posts"]):
                nxt = skirt["posts"][(i + 1) % skirt["bay_count"]]
                mid = math.degrees(
                    math.atan2(
                        post["y"] + nxt["y"], post["x"] + nxt["x"]
                    )
                ) % 360.0
                gap = abs((mid - centre + 180.0) % 360.0 - 180.0)
                if best is None or gap < best[0]:
                    best = (gap, i)
            open_bay = best[1]
            skirt["open_bays"] = [open_bay]
            skirt["braces"] = [b for b in skirt["braces"] if b["bay"] != open_bay]
            skirt["brace_total_length"] = _r(
                sum(b["length"] for b in skirt["braces"])
            )
            _open_door_bay(skirt, out, radius)
            skirt["note"] += (
                f" Bay {open_bay} is left open for the door: no diagonal, and "
                "neither ring runs across it. A header over the opening takes "
                "the hoop force round."
            )

        cut = out["doorway"].get("cut")
        if cut:
            # Carry the removed spans on the rods themselves so a consumer can
            # draw what is actually there without re-deriving the cut. The
            # rod's own length fields stay nominal: the dome underneath is
            # still the whole Takekawa dome, and the cut is a modification of
            # it that verify checks separately.
            for rod in out["rods"]:
                spans = cut["spans"].get(rod["name"])
                if spans:
                    rod["cut_spans_deg"] = spans
    return out
