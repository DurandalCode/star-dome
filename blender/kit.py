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
from mathutils import Matrix, Vector

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


def import_stl(path):
    """Load one STL and return its object, or None if the file is not there.

    Blender 4.2 replaced ``import_mesh.stl`` with ``wm.stl_import`` and the old
    name is gone in 5.x, so both are tried. The file arrives in millimetres,
    which is what every generator in this project writes, and the object is
    left at millimetre scale: the caller places it with a matrix that carries
    the mm -> m conversion, so scaling twice is the mistake to avoid here.
    """
    import os

    if not os.path.exists(path):
        return None
    before = set(bpy.data.objects)
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=path, global_scale=1.0)
    else:  # pragma: no cover - Blender 4.1 and earlier
        bpy.ops.import_mesh.stl(filepath=path, global_scale=1.0)
    fresh = [o for o in bpy.data.objects if o not in before]
    if not fresh:
        return None
    if len(fresh) > 1:
        # One solid per file is what export_solid writes; anything else means
        # the file is not what this thinks it is.
        raise RuntimeError(f"{path} holds {len(fresh)} objects, expected 1")
    return fresh[0]


def part_pieces(part_id, directory):
    """Every printed piece of one part, in the order the generator wrote them.

    A connector is not one solid: the fan is five plates, the base hub four,
    the clamp a bottom and a cap. They are exported as separate STLs because
    they are separate prints, and a scene wants all of them in place.

    ``ref-`` files are reference rods and whole-node assemblies, drawn for
    looking at inside FreeCAD. Importing them would double every rod.
    """
    import os

    if not os.path.isdir(directory):
        return []
    prefix = f"{part_id}_"
    names = [
        f for f in sorted(os.listdir(directory))
        if f.startswith(prefix) and f.endswith(".stl")
        and not f[len(prefix):].startswith("ref-")
    ]
    return [os.path.join(directory, f) for f in names]


def place_instance(name, mesh, origin_mm, basis, collection,
                   lift=0.0, place=None, spin_deg=0.0):
    """One connector, sharing its mesh with every other copy of the same part.

    A dome carries 107 connectors and several hundred printed pieces, so each
    piece is imported once and every instance after that is a new object over
    the SAME mesh data. Blender treats that as one mesh with many transforms,
    which is the difference between a scene that opens and one that does not.

    ``basis`` maps the part's own axes onto the dome, as the connector
    schedule derived them: rows are where local +X, +Y and +Z point. The
    matrix is built by columns because that is what transforms a local vector.

    ``spin_deg`` turns the whole dome about its own axis, which a site scene
    does to aim a doorway. The basis has to turn with it: ``place`` moves where
    a part sits and would leave it facing the way the unspun dome faced.

    Colour rides on the mesh, not the object, because the mesh is the shared
    thing: one material per printed piece, set once when it is imported.
    """
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    ex, ey, ez = (Vector(row) for row in basis)
    if spin_deg:
        turn = Matrix.Rotation(math.radians(spin_deg), 3, "Z")
        ex, ey, ez = (turn @ ex, turn @ ey, turn @ ez)
    x, y = (place(origin_mm[0], origin_mm[1]) if place
            else (origin_mm[0] * MM, origin_mm[1] * MM))
    obj.matrix_world = Matrix((
        (ex.x * MM, ey.x * MM, ez.x * MM, x),
        (ex.y * MM, ey.y * MM, ez.y * MM, y),
        (ex.z * MM, ey.z * MM, ez.z * MM, origin_mm[2] * MM + lift),
        (0.0, 0.0, 0.0, 1.0),
    ))
    return obj


def mirror_mesh(mesh, name):
    """A mesh reflected in its own XZ plane: the other hand of a chiral part.

    The two-rod clamp is handed -- its cap goes outside, over the rod that
    runs outside, so it cannot be turned over to make the angles agree -- and
    the dome needs both. Reflecting the mesh keeps the placement a rotation,
    which is what lets every instance share one transform convention.
    """
    copy = mesh.copy()
    copy.name = name
    for vertex in copy.vertices:
        vertex.co.y = -vertex.co.y
    for polygon in copy.polygons:
        polygon.flip()
    copy.update()
    return copy
