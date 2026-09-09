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

``--shots DIR`` renders a set of named views instead of one frame -- four of
them from eye level, plus an orthographic plan and elevation::

    blender --background --factory-startup --python blender/build_scene.py -- \
        --model exports/model/star_dome_d6.json --hide-cuts --shots exports/shots
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
SKIRT_COLOUR = (0.72, 0.72, 0.70, 1.0)
BRACE_COLOUR = (0.35, 0.62, 0.78, 1.0)   # tension diagonals, not rod
DOOR_COLOUR = (1.00, 0.78, 0.10, 1.0)      # the opening itself
GHOST_COLOUR = (0.90, 0.10, 0.10, 1.0)     # a piece cut out
JAMB_COLOUR = (1.00, 0.42, 0.05, 1.0)      # the two rods that frame it

# Two figures, not one. 1.8 m is a person; 2.2 m is a costumed character on
# stilts or in a frame, and whether that gets through the door is a question a
# person-sized figure never asks. See entrance.TEMPLATES["tall"].
HUMAN_HEIGHTS = ((1.80, "Person", (0.90, 0.75, 0.60, 1.0)),
                 (2.20, "Tall", (0.55, 0.68, 0.45, 1.0)))
# Sideways spacing in the doorway, m. Enough to read as two figures, small
# enough that both stay inside the opening on the narrow variants.
HUMAN_SPREAD = 0.42


def parse_args(argv):
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser(prog="build_scene")
    p.add_argument("--model", required=True, help="path to model.json")
    p.add_argument(
        "--label-nodes",
        action="store_true",
        help="write each crossing's name beside it, so a node can be named "
             "from the viewport instead of by clicking through the outliner",
    )
    p.add_argument(
        "--shots",
        default=None,
        metavar="DIR",
        help="render a set of named views into this directory, first-person "
             "ones included, as well as the single default frame. "
             "e.g. --shots exports/shots",
    )
    p.add_argument(
        "--hide-cuts",
        action="store_true",
        help="leave the removed pieces out entirely instead of ghosting them",
    )
    p.add_argument(
        "--no-doorway",
        action="store_true",
        help="skip the doorway highlight even if the model carries one",
    )
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


def rod_object(rod, radius_m, material, collection, lift=0.0, points=None,
               suffix="", bevel=None):
    """One bow, or one piece of one, as a poly curve bevelled at rod radius."""
    points = rod["points"] if points is None else points
    curve = bpy.data.curves.new(f"RodCurve_{rod['name']}{suffix}", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius_m if bevel is None else bevel
    curve.bevel_resolution = 6
    curve.use_fill_caps = True

    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x * MM, y * MM, z * MM + lift, 1.0)

    obj = bpy.data.objects.new(f"Rod_{rod['name']}{suffix}", curve)
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


def marker(name, xyz_mm, radius_m, material, collection, lift=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius_m,
        segments=16,
        ring_count=8,
        location=(xyz_mm[0] * MM, xyz_mm[1] * MM, xyz_mm[2] * MM + lift),
    )
    sphere = bpy.context.active_object
    sphere.name = name
    sphere.data.materials.append(material)
    return move_to(sphere, collection)


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


def add_skirt(skirt, radius_m, rod_radius_m, material, collection, lift,
              brace_material=None, place=None):
    """Posts, a ring at each end, and the diagonals that stop it racking.

    The model keeps the dome's base ring at z = 0 and hangs the skirt below it
    into negative z, so the whole assembly is lifted by the skirt height here
    to stand it on the ground plane.
    """
    place = place or (lambda x, y: (x * MM, y * MM))
    brace_material = brace_material or material
    made = []

    for post in skirt["posts"]:
        z_lo = post["z_bottom"] * MM + lift
        z_hi = post["z_top"] * MM + lift
        px, py = place(post["x"], post["y"])
        bpy.ops.mesh.primitive_cylinder_add(
            radius=rod_radius_m,
            depth=z_hi - z_lo,
            location=(px, py, (z_lo + z_hi) / 2.0),
            vertices=16,
        )
        obj = bpy.context.active_object
        obj.name = f"Skirt_{post['name']}"
        obj.data.materials.append(material)
        made.append(move_to(obj, collection))

    for tag in ("top_ring", "bottom_ring"):
        for seg in skirt.get(tag, ()):
            made.append(
                segment(f"Skirt_{seg['name']}", seg["a"], seg["b"], rod_radius_m,
                        material, collection, place, lift)
            )

    # Thinner than the rod, and its own colour: a strap is not a stick, and
    # the drawing should not suggest it is.
    header = skirt.get("header")
    if header:
        # Rod, not strap: it spans the doorway and has to hold itself up.
        segment("Skirt_Header", header["a"], header["b"], rod_radius_m,
                material, collection, place, lift)

    for brace in skirt.get("braces", ()):
        made.append(
            segment(f"Skirt_{brace['name']}", brace["a"], brace["b"],
                    rod_radius_m * 0.45, brace_material, collection, place, lift)
        )
    return [m for m in made if m is not None]


def add_ground(diameter_m, collection):
    bpy.ops.mesh.primitive_plane_add(size=diameter_m * 2.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "Ground"
    mat = make_material("Ground", (0.28, 0.30, 0.26, 1.0))
    plane.data.materials.append(mat)
    return move_to(plane, collection)


def add_figure(height, label, colour, x, y, collection):
    """A crude figure of a given height. Only the height matters.

    Proportions scale with it, so the tall one reads as tall rather than as a
    person standing closer to the camera.
    """
    body_h = height * 0.72
    scale = height / 1.75
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.17 * scale, depth=body_h, location=(x, y, body_h / 2.0)
    )
    body = bpy.context.active_object
    body.name = f"{label}_Body"

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.115 * scale,
        location=(x, y, body_h + 0.155 * scale),
    )
    head = bpy.context.active_object
    head.name = f"{label}_Head"

    mat = make_material(f"Figure_{label}", colour)
    for obj in (body, head):
        obj.data.materials.append(mat)
        move_to(obj, collection)
    return body, head


def add_humans(radius_m, collection, facing_deg=None):
    """Both figures, side by side, standing in the doorway when there is one.

    The doorway is the one place in the dome where "does this fit" is not
    obvious by eye, and it is the only place where the two heights say
    different things.
    """
    if facing_deg is None:
        centre = (radius_m * 0.55, 0.0)
        along = (0.0, 1.0)
    else:
        a = math.radians(facing_deg)
        centre = (math.cos(a) * radius_m, math.sin(a) * radius_m)
        along = (-math.sin(a), math.cos(a))  # the door's own tangent

    made = []
    offsets = (-HUMAN_SPREAD, HUMAN_SPREAD)
    for (height, label, colour), offset in zip(HUMAN_HEIGHTS, offsets):
        made.append(
            add_figure(
                height,
                label,
                colour,
                centre[0] + along[0] * offset,
                centre[1] + along[1] * offset,
                collection,
            )
        )
    return made


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


def add_doorway(door, rod_radius_m, collection, lift):
    """Draw the chosen opening: its outline, its frame, and the hole itself.

    The outline comes straight from the model as rod centrelines, so nothing
    here decides where the door is -- see stardome/doorway.py. The filled
    panel is what makes it read at a glance: a doorway drawn as a line among
    fifteen other lines is invisible, and the whole point of standing this up
    in Blender is to see whether a person walks through it.
    """
    points = [(x * MM, y * MM, z * MM + lift) for x, y, z in door["outline"]["points"]]

    curve = bpy.data.curves.new("DoorwayOutline", "CURVE")
    curve.dimensions = "3D"
    # Thicker than the rods it lies on, so the frame reads as a highlight
    # rather than as one more line among fifteen.
    curve.bevel_depth = rod_radius_m * 1.25
    curve.bevel_resolution = 6
    curve.use_fill_caps = True
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x, y, z, 1.0)
    spline.use_cyclic_u = True

    outline_mat = make_material("Doorway_Outline", DOOR_COLOUR)
    obj = bpy.data.objects.new("Doorway_Outline", curve)
    obj.data.materials.append(outline_mat)
    collection.objects.link(obj)

    # The opening as a surface, fanned from its centroid because the arch is
    # curved and a single n-gon across it would not be planar.
    centre = (
        sum(p[0] for p in points) / len(points),
        sum(p[1] for p in points) / len(points),
        sum(p[2] for p in points) / len(points),
    )
    mesh = bpy.data.meshes.new("DoorwayPanel")
    verts = [centre] + points
    faces = [
        (0, i + 1, (i + 1) % len(points) + 1) for i in range(len(points))
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    panel_mat = make_transparent(
        make_material("Doorway_Panel", DOOR_COLOUR), 0.16
    )

    panel = bpy.data.objects.new("Doorway_Panel", mesh)
    panel.data.materials.append(panel_mat)
    if hasattr(panel, "visible_shadow"):
        panel.visible_shadow = False
    collection.objects.link(panel)

    return obj, panel


def door_azimuth_deg(door):
    """Which way the door faces, for aiming the camera and the figure."""
    return door["bay"]["apex_azimuth_deg"]


def label_node(name, xyz_mm, size_m, material, collection, lift=0.0):
    """The node's name, standing up beside it and facing the camera.

    Reading a crossing off the outliner means clicking it first, which is the
    wrong way round when the question is "which crossing is that one".
    """
    bpy.ops.object.text_add(
        location=(
            xyz_mm[0] * MM,
            xyz_mm[1] * MM,
            xyz_mm[2] * MM + lift + size_m * 0.6,
        )
    )
    obj = bpy.context.active_object
    obj.data.body = name
    obj.data.align_x = "CENTER"
    obj.data.size = size_m
    obj.name = f"Label_{name}"
    obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    obj.data.materials.append(material)
    return move_to(obj, collection)


def add_camera_and_light(scene, radius_m, height_m, facing_deg=None):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 35.0
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    if facing_deg is None:
        cam.location = (radius_m * 2.1, -radius_m * 2.3, height_m * 1.15)
    else:
        # Stand off along the door's own azimuth, so the opening is not hidden
        # behind the far side of the dome.
        a = math.radians(facing_deg)
        distance = radius_m * 3.1
        cam.location = (
            math.cos(a) * distance,
            math.sin(a) * distance,
            height_m * 0.95,
        )
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


# Eye height for the first-person views. Not the figure's 1.8 m: eyes sit
# below the top of a head.
EYE_HEIGHT = 1.70


def _aim(cam, at):
    direction = Vector(at) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def shot_cameras(scene, radius_m, height_m, facing_deg):
    """The views worth having, as named cameras.

    A three-quarter view answers "what shape is it". The questions an event
    actually asks are answered from eye level: can I see out, does the door
    frame anything, how low is the edge where the useful floor stops. So most
    of these stand a person up inside and look around.
    """
    a = math.radians(facing_deg if facing_deg is not None else 0.0)
    out = (math.cos(a), math.sin(a))          # towards the door, from centre
    across = (-math.sin(a), math.cos(a))
    centre = (0.0, 0.0, EYE_HEIGHT)
    door = (out[0] * radius_m, out[1] * radius_m, EYE_HEIGHT)

    views = {
        # Outside, three-quarter, the whole thing.
        "outside": dict(
            loc=(out[0] * radius_m * 2.6 - across[0] * radius_m * 1.4,
                 out[1] * radius_m * 2.6 - across[1] * radius_m * 1.4,
                 height_m * 0.9),
            at=(0.0, 0.0, height_m * 0.45),
            lens=35.0,
        ),
        # Standing outside the door, about to walk in.
        "approach": dict(
            loc=(out[0] * (radius_m + 4.0), out[1] * (radius_m + 4.0), EYE_HEIGHT),
            at=(out[0] * radius_m * 0.2, out[1] * radius_m * 0.2, EYE_HEIGHT),
            lens=28.0,
        ),
        # Standing in the middle, looking back out of the door.
        "inside": dict(loc=centre, at=door, lens=16.0),
        # Standing in the middle, looking at the far wall -- where the ceiling
        # comes down is the real limit on a dome, and it only reads from here.
        "inside_back": dict(
            loc=centre,
            # Level, not down: the question is where the ceiling crosses eye
            # height, and aiming at the floor answers a different one.
            at=(-out[0] * radius_m, -out[1] * radius_m, EYE_HEIGHT),
            lens=18.0,
        ),
        # Straight up at the crown.
        # Straight up needs a very short lens or it shows one pentagon.
        "up": dict(loc=centre, at=(0.0, 0.0, height_m), lens=11.0),
        # In the doorway itself, looking in.
        "doorway": dict(
            loc=(out[0] * (radius_m - 0.2), out[1] * (radius_m - 0.2), EYE_HEIGHT),
            at=(-out[0] * radius_m, -out[1] * radius_m, EYE_HEIGHT * 0.7),
            lens=16.0,
        ),
    }

    made = {}
    for name, spec in views.items():
        data = bpy.data.cameras.new(f"Cam_{name}")
        data.lens = spec["lens"]
        cam = bpy.data.objects.new(f"Cam_{name}", data)
        scene.collection.objects.link(cam)
        cam.location = spec["loc"]
        _aim(cam, spec["at"])
        made[name] = cam

    # Two orthographic drawings, which are not photographs and read better for
    # dimensions than any perspective view.
    #
    # ortho_scale governs the *wider* axis of the frame, and the frame is
    # 16:10. A plan has to fit the diameter in both directions, so its scale is
    # set from the short axis and multiplied back up; an elevation is wider
    # than it is tall and the diameter governs directly.
    aspect = 1600.0 / 1000.0
    diameter_m = radius_m * 2.0
    for name, loc, at, scale in (
        ("plan", (0.0, 0.0, height_m * 4.0), (0.0, 0.0, 0.0),
         diameter_m * 1.2 * aspect),
        (
            "elevation",
            (out[0] * radius_m * 8.0, out[1] * radius_m * 8.0, height_m * 0.5),
            (0.0, 0.0, height_m * 0.5),
            diameter_m * 1.3,
        ),
    ):
        data = bpy.data.cameras.new(f"Cam_{name}")
        data.type = "ORTHO"
        data.ortho_scale = scale
        cam = bpy.data.objects.new(f"Cam_{name}", data)
        scene.collection.objects.link(cam)
        cam.location = loc
        _aim(cam, at)
        made[name] = cam

    return made


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
    rod_radius_m = meta["rod_diameter"] * MM / 2.0
    # The model puts the dome's base ring at z = 0 and any skirt below it, so
    # lift the lot to stand the finished structure on the ground plane.
    lift = meta.get("skirt_height", 0.0) * MM
    height_m = meta.get("overall_height", meta["dome_height_measured"]) * MM

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

    door = data.get("doorway")
    # A portal has no lancet, so no pair of jambs to pick out: the
    # traced outline and the ghosts of the cut pieces carry it instead.
    jambs = (
        set(door["frame"]["jamb_rods"])
        if door and door.get("frame")
        else set()
    )
    jamb_mat = make_material("Rod_Jamb", JAMB_COLOUR)

    ghost_mat = make_transparent(make_material("Rod_Cut", GHOST_COLOUR), 0.50)
    ghost_coll = None

    for rod in data["rods"]:
        # The two rods that frame the door get their own colour: they are what
        # a cover panel is hemmed against and what a frame bolts to.
        mat = jamb_mat if rod["name"] in jambs else materials[rod["family"]]
        runs = rod_runs(rod)
        for index, (points, present) in enumerate(runs):
            if present:
                suffix = f"_{index}" if len(runs) > 1 else ""
                rod_object(rod, rod_radius_m, mat, rods_coll, lift, points, suffix)
            elif not args.hide_cuts:
                if ghost_coll is None:
                    ghost_coll = new_collection("Cut_Away", root)
                rod_object(
                    rod,
                    rod_radius_m,
                    ghost_mat,
                    ghost_coll,
                    lift,
                    points,
                    "_cut",
                    bevel=rod_radius_m * 0.7,
                )

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
            lift,
        )

    if args.label_nodes:
        label_coll = new_collection("Labels", root)
        label_mat = make_material("NodeLabel", (0.98, 0.98, 0.98, 1.0))
        # Sized off the dome so the text is legible at any variant.
        size = radius_m * 0.055
        for node in data["nodes"]:
            if node["rod_count"] != 4 and not args.untied_nodes:
                continue
            label_node(
                node["name"],
                (node["x"], node["y"], node["z"]),
                size,
                label_mat,
                label_coll,
                lift,
            )
        for node in data["base_nodes"]:
            label_node(
                node["name"],
                (node["x"], node["y"], node["z"]),
                size,
                label_mat,
                label_coll,
                lift,
            )

    for node in data["base_nodes"]:
        marker(
            f"Base_{node['name']}",
            (node["x"], node["y"], node["z"]),
            node_radius,
            base_mat,
            base_coll,
            lift,
        )

    if data.get("skirt"):
        skirt_coll = new_collection("Skirt", root)
        add_skirt(
            data["skirt"],
            radius_m,
            rod_radius_m,
            make_material("Skirt", SKIRT_COLOUR),
            skirt_coll,
            lift,
            make_material("Skirt_Brace", BRACE_COLOUR),
        )

    facing = None
    if door and not args.no_doorway:
        door_coll = new_collection("Doorway", root)
        add_doorway(door, rod_radius_m, door_coll, lift)
        facing = door_azimuth_deg(door)

    if not args.no_ground:
        add_ground(radius_m * 2.0, site_coll)
    if not args.no_human:
        add_humans(radius_m, site_coll, facing)

    default_cam, _ = add_camera_and_light(scene, radius_m, height_m, facing)
    data["_shot_cameras"] = shot_cameras(scene, radius_m, height_m, facing)
    data["_default_camera"] = default_cam

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

    skirt = meta.get("skirt_height", 0.0)
    tall = meta.get("overall_height", meta["dome_height_measured"])
    print(
        f"[star-dome] {meta['variant']}: {len(data['rods'])} rods, "
        f"{len(data['nodes'])} crossing points, "
        f"{meta['dome_diameter'] * MM:.2f} m across, "
        f"{tall * MM:.2f} m tall"
        + (f" (dome {meta['dome_height_measured'] * MM:.2f} m "
           f"+ {skirt * MM:.2f} m skirt)" if skirt else "")
    )

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print(f"[star-dome] saved {args.out}")

    if args.render:
        path = render(bpy.context.scene, args.render)
        print(f"[star-dome] rendered {path}")

    if args.shots:
        scene = bpy.context.scene
        stem = meta["variant"].lower()
        os.makedirs(os.path.abspath(args.shots), exist_ok=True)
        for name, cam in data["_shot_cameras"].items():
            scene.camera = cam
            out = os.path.join(args.shots, f"{stem}_{name}.png")
            render(scene, out)
            print(f"[star-dome] shot {name} -> {out}")
        scene.camera = data["_default_camera"]


if __name__ == "__main__":
    main()
