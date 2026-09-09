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
        posts = []
        for i, p in enumerate(base_pts):
            posts.append(
                {
                    "name": f"s{i}",
                    "base_node": f"b{i}",
                    "x": _r(p[0]),
                    "y": _r(p[1]),
                    "z_bottom": _r(-variant.skirt_height),
                    "z_top": _r(p[2]),
                    "length": _r(variant.skirt_height),
                    "rods": topology.rods_at_base_point(bows, i),
                }
            )
        skirt = {
            "height": _r(variant.skirt_height),
            "ground_z": _r(-variant.skirt_height),
            "post_count": len(posts),
            "posts": posts,
            "post_total_length": _r(variant.skirt_height * len(posts)),
            "ground_ring_length": _r(2.0 * math.pi * radius),
            "note": (
                "Vertical posts and a ground ring, nothing more. An unbraced "
                "ring of verticals racks under any sideways load; diagonal "
                "bracing or a tension belt is required before this is built. "
                "See docs/skirt.md."
            ),
        }

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
