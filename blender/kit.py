"""Shared Blender helpers for the scene builders.

`build_scene.py` draws one dome for inspecting it; `build_site.py` lines several
up for comparing them. They are different pictures, but they draw the same
things out of the same `model.json`, and these five helpers were byte-identical
in both files.

Everything here is drawing. No dome geometry is computed in this directory --
rod centrelines, cut spans and door outlines all arrive from the model, which
is the rule in docs/architecture.md.

What stays in each builder is its own picture: the palette, the camera, the
figures, and how the scene is laid out.
"""

import math

import bpy
from mathutils import Vector

MM = 0.001  # model units (mm) -> Blender units (m)


def material(name, rgba):
    """A solid-colour material that reads the same in render and solid view."""
    mat = bpy.data.materials.new(name)
    # Materials come with a node tree already. Touching use_nodes at all --
    # even reading it -- raises a DeprecationWarning on Blender 5.2, so go
    # through node_tree and only fall back if some build gives us none.
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = rgba
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.45
    mat.diffuse_color = rgba  # solid-view colour
    return mat


def make_transparent(mat, alpha):
    """Make a material see-through on whichever EEVEE this Blender ships.

    4.2 replaced `blend_method` with `surface_render_method`, and 5.x still
    accepts the old name silently without doing anything -- which is how the
    door panel came out looking like a solid tent.
    """
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
    if bsdf is not None:
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        # Flat and unlit. A glazed panel picks up the sun and reads as a solid
        # tent flap, which is the opposite of "this is a hole".
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 1.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.0
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = 0.0
    colour = mat.diffuse_color
    mat.diffuse_color = (colour[0], colour[1], colour[2], alpha)
    return mat


def new_collection(name, parent):
    coll = bpy.data.collections.new(name)
    parent.children.link(coll)
    return coll


def move_to(obj, collection):
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def rod_runs(rod):
    """Split a rod's polyline into the pieces that are there and the pieces gone.

    A cut is recorded on the rod as spans of the bow parameter t, and the
    polyline samples t evenly from 0 to 180 -- so the index gives t back. The
    removed piece is still worth drawing, as a ghost: a door you cannot see the
    price of is a door that looks free.
    """
    points = rod["points"]
    spans = rod.get("cut_spans_deg") or []
    if not spans:
        return [(points, True)]

    last = len(points) - 1
    runs = []
    current = []
    state = None
    for i, point in enumerate(points):
        t = 180.0 * i / last
        present = not any(lo - 1e-6 <= t <= hi + 1e-6 for lo, hi in spans)
        if state is None:
            state = present
        if present != state:
            # The boundary point belongs to both runs, so the ghost meets the
            # rod instead of leaving a gap at the joint.
            current.append(point)
            runs.append((current, state))
            current = [points[i - 1]]
            state = present
        current.append(point)
    runs.append((current, state))
    return [(pts, keep) for pts, keep in runs if len(pts) > 1]


def segment(name, a, b, radius_m, material, collection, place, lift=0.0):
    """One straight member between two model-space points.

    ``place`` maps a model (x, y) to scene metres, so the same drawing works
    in a single-dome scene and in a row where each dome is offset and spun.
    """
    ax, ay = place(a[0], a[1])
    bx, by = place(b[0], b[1])
    az = a[2] * MM + lift
    bz = b[2] * MM + lift
    mid = ((ax + bx) / 2.0, (ay + by) / 2.0, (az + bz) / 2.0)
    length = math.dist((ax, ay, az), (bx, by, bz))
    if length < 1e-9:
        return None
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_m, depth=length,
                                        location=mid, vertices=12)
    obj = bpy.context.active_object
    obj.name = name
    direction = Vector((bx - ax, by - ay, bz - az))
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(material)
    return move_to(obj, collection)
