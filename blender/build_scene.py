"""Build a 1:1 Blender scene from the dome model.

A consumer, not a source of geometry. Every coordinate comes from
``model.json``; this script computes no dome geometry of its own. See
docs/architecture.md.

    python3 -m stardome build D6 --polylines --weave-mode layered
    blender --background --factory-startup \
        --python blender/build_scene.py -- \
        --model exports/model/star_dome_d6.json \
        --out exports/blender/star_dome_d6.blend \
        --render exports/blender/star_dome_d6.png

Use ``--weave-mode layered`` when generating the model. In ``flat`` mode all
15 centrelines lie on one sphere and every crossing has two rods occupying the
same space, which looks wrong and makes clearance checks meaningless. Layered
gives each bow its own shell so crossings read as real over/under -- it is a
drawing convention, not a build instruction.

The model is in millimetres. The scene is built in metres at 1:1 so that a
1.8 m doorway and a human figure measure correctly against the rods, which is
the entire point of doing this in Blender.

Objects are named by their model IDs (``Rod_G1``, ``Node_N07``, ``Base_b0``)
so a regenerated variant can be matched against an existing scene.
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

MM = 0.001  # model units (mm) -> Blender units (m)

# Family colours, chosen to be distinguishable in both solid and rendered view.
FAMILY_COLOUR = {
    "G": (0.15, 0.55, 0.95, 1.0),   # the icosidodecahedral skeleton
    "U": (0.95, 0.45, 0.10, 1.0),   # upper thirds-marked family
    "L": (0.20, 0.75, 0.35, 1.0),   # lower thirds-marked family
}
TIED_COLOUR = (0.95, 0.15, 0.25, 1.0)
UNTIED_COLOUR = (0.55, 0.55, 0.60, 1.0)
BASE_COLOUR = (0.25, 0.25, 0.30, 1.0)

HUMAN_HEIGHT = 1.75  # m, for scale reference


def parse_args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser(prog="build_scene")
    p.add_argument("--model", required=True, help="path to model.json")
    p.add_argument("--out", default=None, help="write a .blend here")
    p.add_argument("--render", default=None, help="render a preview PNG here")
    p.add_argument("--no-human", action="store_true", help="omit the scale figure")
    p.add_argument("--no-ground", action="store_true", help="omit the ground plane")
    p.add_argument(
        "--untied-nodes",
        action="store_true",
        help="also mark the 30 unlashed crossings (hidden by default)",
    )
    return p.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def setup_units(scene):
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0


def make_material(name, rgba):
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


def new_collection(name, parent):
    coll = bpy.data.collections.new(name)
    parent.children.link(coll)
    return coll


def rod_object(rod, radius_m, material, collection):
    """One bow as a poly curve with a round bevel at the real rod radius."""
    curve = bpy.data.curves.new(f"RodCurve_{rod['name']}", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius_m
    curve.bevel_resolution = 6
    curve.use_fill_caps = True

    spline = curve.splines.new("POLY")
    points = rod["points"]
    spline.points.add(len(points) - 1)
    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x * MM, y * MM, z * MM, 1.0)

    obj = bpy.data.objects.new(f"Rod_{rod['name']}", curve)
    obj["family"] = rod["family"]
    obj["layer"] = rod["layer"]
    obj["length_mm"] = rod["length_drawn"]
    obj.data.materials.append(material)
    collection.objects.link(obj)
    return obj


def move_to(obj, collection):
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def marker(name, xyz_mm, radius_m, material, collection):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius_m,
        segments=16,
        ring_count=8,
        location=(xyz_mm[0] * MM, xyz_mm[1] * MM, xyz_mm[2] * MM),
    )
    sphere = bpy.context.active_object
    sphere.name = name
    sphere.data.materials.append(material)
    return move_to(sphere, collection)


def add_ground(diameter_m, collection):
    bpy.ops.mesh.primitive_plane_add(size=diameter_m * 2.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "Ground"
    mat = make_material("Ground", (0.28, 0.30, 0.26, 1.0))
    plane.data.materials.append(mat)
    return move_to(plane, collection)


def add_human(radius_m, collection):
    """A crude 1.75 m figure. Only its height matters."""
    body_h = HUMAN_HEIGHT * 0.72
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.17, depth=body_h, location=(radius_m * 0.55, 0.0, body_h / 2.0)
    )
    body = bpy.context.active_object
    body.name = "HumanScale_Body"

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.115,
        location=(radius_m * 0.55, 0.0, body_h + 0.155),
    )
    head = bpy.context.active_object
    head.name = "HumanScale_Head"

    mat = make_material("HumanScale", (0.90, 0.75, 0.60, 1.0))
    for obj in (body, head):
        obj.data.materials.append(mat)
        move_to(obj, collection)
    return body, head


def add_camera_and_light(scene, radius_m, height_m):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 35.0
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (radius_m * 2.1, -radius_m * 2.3, height_m * 1.15)
    direction = Vector((0.0, 0.0, height_m * 0.42)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.location = (radius_m, -radius_m, height_m * 2.5)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))
    return cam, sun


def build(args):
    with open(args.model) as fh:
        data = json.load(fh)

    meta = data["meta"]
    if not data["rods"] or "points" not in data["rods"][0]:
        raise SystemExit(
            "this model has no rod polylines.\n"
            "regenerate it with:  python3 -m stardome build "
            f"{meta['variant']} --polylines --weave-mode layered"
        )
    if meta["weave_mode"] != "layered":
        print(
            f"[warning] weave_mode is {meta['weave_mode']!r}; in flat mode every "
            "crossing has two rods in the same place. Use --weave-mode layered."
        )

    radius_m = meta["dome_radius"] * MM
    height_m = meta["dome_height_measured"] * MM
    rod_radius_m = meta["rod_diameter"] * MM / 2.0

    scene = bpy.context.scene
    clear_scene()
    setup_units(scene)

    root = new_collection(f"StarDome_{meta['variant']}", scene.collection)
    rods_coll = new_collection("Rods", root)
    tied_coll = new_collection("Nodes_Tied", root)
    untied_coll = new_collection("Nodes_Untied", root)
    base_coll = new_collection("Nodes_Base", root)
    site_coll = new_collection("Site", root)

    materials = {f: make_material(f"Rod_{f}", c) for f, c in FAMILY_COLOUR.items()}
    tied_mat = make_material("Node_Tied", TIED_COLOUR)
    untied_mat = make_material("Node_Untied", UNTIED_COLOUR)
    base_mat = make_material("Node_Base", BASE_COLOUR)

    for rod in data["rods"]:
        rod_object(rod, rod_radius_m, materials[rod["family"]], rods_coll)

    # Big enough to find at a glance, small enough to still be honest about
    # where the crossing actually is: 25 mm at a 10 mm rod, about the footprint
    # a clamp would occupy.
    node_radius = rod_radius_m * 2.5
    for node in data["nodes"]:
        tied = node["rod_count"] == 4
        if not tied and not args.untied_nodes:
            continue
        marker(
            f"Node_{node['name']}",
            (node["x"], node["y"], node["z"]),
            node_radius,
            tied_mat if tied else untied_mat,
            tied_coll if tied else untied_coll,
        )

    for node in data["base_nodes"]:
        marker(
            f"Base_{node['name']}",
            (node["x"], node["y"], node["z"]),
            node_radius,
            base_mat,
            base_coll,
        )

    if not args.no_ground:
        add_ground(radius_m * 2.0, site_coll)
    if not args.no_human:
        add_human(radius_m, site_coll)

    add_camera_and_light(scene, radius_m, height_m)

    # The unlashed markers are noise for most work; keep them out of the way
    # but present, so toggling them on needs no rebuild.
    layer_coll = bpy.context.view_layer.layer_collection
    for child in layer_coll.children:
        for sub in child.children:
            if sub.name == "Nodes_Untied" and not args.untied_nodes:
                sub.hide_viewport = True

    return data


def render(scene, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.render.filepath = os.path.abspath(path)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath


def main():
    args = parse_args(sys.argv)
    data = build(args)
    meta = data["meta"]

    print(
        f"[star-dome] {meta['variant']}: {len(data['rods'])} rods, "
        f"{len(data['nodes'])} crossing points, "
        f"{meta['dome_diameter'] * MM:.2f} m across, "
        f"{meta['dome_height_measured'] * MM:.2f} m tall"
    )

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print(f"[star-dome] saved {args.out}")

    if args.render:
        path = render(bpy.context.scene, args.render)
        print(f"[star-dome] rendered {path}")


if __name__ == "__main__":
    main()
