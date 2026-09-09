"""Build one Blender scene with several domes side by side, at 1:1.

A consumer, like build_scene.py: every coordinate comes from the models, and
nothing here recomputes geometry. This is the composition scene Milestone 2
asks for -- the whole family standing on one ground plane, each with a human
figure, so the sizes can be compared against something real rather than
against each other on a screen.

    python3 -m stardome build --all --polylines --weave-mode layered
    blender --background --factory-startup --python blender/build_site.py -- \
        --models exports/model/star_dome_d3.json exports/model/star_dome_d4.json \
        --out exports/blender/site.blend --render exports/blender/site.png

With no --models it takes every star_dome_*.json in exports/model, ordered by
diameter.

Domes are laid out in a row along X, ordered small to large, spaced by their
radii plus --gap. The row is the point: a dome twice the diameter is nowhere
near twice the useful volume, and standing them together is the only way that
reads.
"""

import argparse
import glob
import json
import math
import os
import sys

import bpy
from mathutils import Vector

MM = 0.001

FAMILY_COLOUR = {
    "G": (0.15, 0.55, 0.95, 1.0),
    "U": (0.95, 0.45, 0.10, 1.0),
    "L": (0.20, 0.75, 0.35, 1.0),
}
SKIRT_COLOUR = (0.80, 0.80, 0.78, 1.0)
BRACE_COLOUR = (0.35, 0.62, 0.78, 1.0)   # tension diagonals, not rod
DOOR_COLOUR = (1.00, 0.78, 0.10, 1.0)
GHOST_COLOUR = (0.90, 0.10, 0.10, 1.0)     # a piece cut out
JAMB_COLOUR = (1.00, 0.42, 0.05, 1.0)
GROUND_COLOUR = (0.26, 0.29, 0.24, 1.0)
LABEL_COLOUR = (0.95, 0.95, 0.95, 1.0)

# 1.8 m is a person; 2.2 m is a costumed character on stilts or in a frame.
# The pair is the point of the row: the same two figures at every size.
HUMAN_HEIGHTS = ((1.80, "Person", (0.92, 0.78, 0.62, 1.0)),
                 (2.20, "Tall", (0.55, 0.68, 0.45, 1.0)))
HUMAN_SPREAD = 0.42


def parse_args(argv):
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser(prog="build_site")
    p.add_argument("--models", nargs="*", default=None, help="model.json paths")
    p.add_argument("--dir", default="exports/model", help="where to look for models")
    p.add_argument("--out", default=None, help="write a .blend here")
    p.add_argument("--render", default=None, help="render a preview PNG here")
    p.add_argument("--gap", type=float, default=2.0, help="metres between domes")
    p.add_argument("--no-labels", action="store_true")
    p.add_argument(
        "--hide-cuts",
        action="store_true",
        help="leave the removed pieces out entirely instead of ghosting them, "
             "for a picture of the thing as built rather than of the decision",
    )
    p.add_argument(
        "--camp",
        type=float,
        default=0.0,
        metavar="DEPTH",
        help="curve the row back by this many metres at its ends, so it reads "
             "as a camp round a yard rather than as a size chart",
    )
    p.add_argument(
        "--named-only",
        action="store_true",
        help="only the sizes with a short name (S, M, L, XL), skipping the "
             "research variants at either end of the range",
    )
    return p.parse_args(argv)


def load_models(args):
    paths = args.models
    if not paths:
        paths = sorted(glob.glob(os.path.join(args.dir, "star_dome_*.json")))
        paths = [p for p in paths if "_connectors" not in p]
    models = []
    for path in paths:
        with open(path) as fh:
            data = json.load(fh)
        if not data.get("rods") or "points" not in data["rods"][0]:
            print(f"[site] skipping {os.path.basename(path)}: no rod polylines")
            continue
        models.append(data)
    if args.named_only:
        named = [d for d in models if d["meta"].get("alias")]
        if named:
            models = named
        else:
            print("[site] --named-only: no model carries an alias, keeping all")
    models.sort(key=lambda d: d["meta"]["dome_diameter"])
    return models


def material(name, rgba):
    mat = bpy.data.materials.new(name)
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.45
    mat.diffuse_color = rgba
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


def spin_for_door(data):
    """Turn each dome so its door faces the camera, which sits at -Y.

    Without this the doors land at whatever azimuth the geometry gives them
    and half the row shows its blank side, which defeats the comparison the
    scene exists to make. Spinning a dome about its own axis changes nothing
    about it -- the structure is five-fold symmetric.
    """
    door = data.get("doorway")
    if not door:
        return 0.0
    return 270.0 - door["bay"]["apex_azimuth_deg"]


def _place(x_mm, y_mm, origin_x, spin_deg, origin_y=0.0):
    """Model mm -> scene metres, spun about the dome's own axis and offset."""
    a = math.radians(spin_deg)
    x = x_mm * math.cos(a) - y_mm * math.sin(a)
    y = x_mm * math.sin(a) + y_mm * math.cos(a)
    return x * MM + origin_x, y * MM + origin_y


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


def add_rod(rod, radius_m, material_, collection, origin_x, lift, spin_deg=0.0,
            points=None, suffix="", bevel=None, origin_y=0.0):
    points = rod["points"] if points is None else points
    curve = bpy.data.curves.new(f"C_{rod['name']}{suffix}", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius_m if bevel is None else bevel
    curve.bevel_resolution = 4
    curve.use_fill_caps = True
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for i, (x, y, z) in enumerate(points):
        px, py = _place(x, y, origin_x, spin_deg, origin_y)
        spline.points[i].co = (px, py, z * MM + lift, 1.0)
    obj = bpy.data.objects.new(f"Rod_{rod['name']}{suffix}", curve)
    obj.data.materials.append(material_)
    collection.objects.link(obj)
    return obj


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


def add_skirt(skirt, radius_m, rod_radius_m, material_, collection, origin_x,
              lift, spin_deg=0.0, origin_y=0.0, brace_material=None):
    for post in skirt["posts"]:
        z_lo = post["z_bottom"] * MM + lift
        z_hi = post["z_top"] * MM + lift
        px, py = _place(post["x"], post["y"], origin_x, spin_deg, origin_y)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=rod_radius_m,
            depth=z_hi - z_lo,
            location=(px, py, (z_lo + z_hi) / 2.0),
            vertices=12,
        )
        obj = bpy.context.active_object
        obj.name = f"Skirt_{post['name']}"
        obj.data.materials.append(material_)
        move_to(obj, collection)

    def place(x, y):
        return _place(x, y, origin_x, spin_deg, origin_y)

    for tag in ("top_ring", "bottom_ring"):
        for seg in skirt.get(tag, ()):
            segment(f"Skirt_{seg['name']}", seg["a"], seg["b"], rod_radius_m,
                    material_, collection, place, lift)
    header = skirt.get("header")
    if header:
        # Rod, not strap: it spans the doorway and has to hold itself up.
        segment("Skirt_Header", header["a"], header["b"], rod_radius_m,
                material_, collection, place, lift)

    for brace in skirt.get("braces", ()):
        segment(f"Skirt_{brace['name']}", brace["a"], brace["b"],
                rod_radius_m * 0.45, brace_material or material_, collection,
                place, lift)


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


def add_doorway(door, rod_radius_m, collection, origin_x, lift, spin_deg=0.0,
                origin_y=0.0):
    """The opening, outlined and filled, exactly as the model reports it."""
    points = [
        (*_place(x, y, origin_x, spin_deg, origin_y), z * MM + lift)
        for x, y, z in door["outline"]["points"]
    ]

    curve = bpy.data.curves.new("DoorwayOutline", "CURVE")
    curve.dimensions = "3D"
    # Thicker than the rods it lies on, so the frame reads as a highlight
    # rather than as one more orange line among fifteen.
    curve.bevel_depth = rod_radius_m * 1.25
    curve.bevel_resolution = 4
    curve.use_fill_caps = True
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x, y, z, 1.0)
    spline.use_cyclic_u = True
    obj = bpy.data.objects.new("Doorway_Outline", curve)
    obj.data.materials.append(material("Doorway_Outline", DOOR_COLOUR))
    collection.objects.link(obj)

    centre = tuple(sum(q[i] for q in points) / len(points) for i in range(3))
    mesh = bpy.data.meshes.new("DoorwayPanel")
    mesh.from_pydata(
        [centre] + points,
        [],
        [(0, i + 1, (i + 1) % len(points) + 1) for i in range(len(points))],
    )
    mesh.update()
    panel_mat = make_transparent(material("Doorway_Panel", DOOR_COLOUR), 0.16)
    panel = bpy.data.objects.new("Doorway_Panel", mesh)
    panel.data.materials.append(panel_mat)
    if hasattr(panel, "visible_shadow"):
        panel.visible_shadow = False
    collection.objects.link(panel)
    return obj, panel


def add_humans(origin_x, offset_y, mats, collection, name, origin_y=0.0):
    """Both figures side by side. Proportions scale with height, so the tall
    one reads as tall rather than as one standing nearer the camera."""
    for (height, label, _), dx in zip(HUMAN_HEIGHTS, (-HUMAN_SPREAD, HUMAN_SPREAD)):
        body_h = height * 0.72
        scale = height / 1.75
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.17 * scale,
            depth=body_h,
            location=(origin_x + dx, offset_y + origin_y, body_h / 2.0),
            vertices=16,
        )
        body = bpy.context.active_object
        body.name = f"{name}_{label}_Body"
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.115 * scale,
            location=(origin_x + dx, offset_y + origin_y, body_h + 0.155 * scale),
            segments=16,
            ring_count=8,
        )
        head = bpy.context.active_object
        head.name = f"{name}_{label}_Head"
        for obj in (body, head):
            obj.data.materials.append(mats[label])
            move_to(obj, collection)


def add_label(text, origin_x, y, material_, collection):
    bpy.ops.object.text_add(location=(origin_x, y, 0.05))
    obj = bpy.context.active_object
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.size = 0.62
    obj.data.extrude = 0.01
    # Standing up, not lying on the ground: a label flat on the floor reads as
    # a smear from any camera that can see the whole row.
    obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    obj.name = f"Label_{text.split()[0]}"
    obj.data.materials.append(material_)
    return move_to(obj, collection)


def build(args, models):
    scene = bpy.context.scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"

    root = new_collection("Site", scene.collection)
    mats = {f: material(f"Rod_{f}", c) for f, c in FAMILY_COLOUR.items()}
    skirt_mat = material("Skirt", SKIRT_COLOUR)
    human_mats = {
        label: material(f"Figure_{label}", colour)
        for _, label, colour in HUMAN_HEIGHTS
    }
    label_mat = material("Label", LABEL_COLOUR)
    jamb_mat = material("Rod_Jamb", JAMB_COLOUR)
    ghost_mat = make_transparent(material("Rod_Cut", GHOST_COLOUR), 0.50)
    brace_mat = material("Skirt_Brace", BRACE_COLOUR)

    x = 0.0
    placed = []
    max_radius = 0.0
    # A camp rather than a size chart: the ends of the row swing back so the
    # domes stand round a yard, with every door still facing the open side.
    span_guess = sum(d["meta"]["dome_radius"] * MM * 2 for d in models) + (
        args.gap * max(0, len(models) - 1)
    )
    for index, data in enumerate(models):
        meta = data["meta"]
        radius_m = meta["dome_radius"] * MM
        rod_radius_m = meta["rod_diameter"] * MM / 2.0
        lift = meta.get("skirt_height", 0.0) * MM

        if placed:
            x += args.gap + radius_m
        if args.camp and len(models) > 1:
            # Parabolic: flat in the middle, swept back at both ends.
            t = (x / span_guess) * 2.0 - 1.0
            y0 = args.camp * t * t
        else:
            y0 = 0.0
        coll = new_collection(meta["variant"], root)

        door = data.get("doorway")
        spin = spin_for_door(data)
        # A portal has no lancet, so no pair of jambs to pick out: the
        # traced outline and the ghosts of the cut pieces carry it instead.
        jambs = (
            set(door["frame"]["jamb_rods"])
            if door and door.get("frame")
            else set()
        )

        for rod in data["rods"]:
            mat = jamb_mat if rod["name"] in jambs else mats[rod["family"]]
            runs = rod_runs(rod)
            for piece, (pts, present) in enumerate(runs):
                if present:
                    suffix = f"_{piece}" if len(runs) > 1 else ""
                    add_rod(
                        rod, rod_radius_m, mat, coll, x, lift, spin, pts, suffix,
                        origin_y=y0,
                    )
                elif not args.hide_cuts:
                    add_rod(
                        rod,
                        rod_radius_m,
                        ghost_mat,
                        coll,
                        x,
                        lift,
                        spin,
                        pts,
                        "_cut",
                        bevel=rod_radius_m * 0.7,
                        origin_y=y0,
                    )
        if data.get("skirt"):
            add_skirt(
                data["skirt"], radius_m, rod_radius_m, skirt_mat, coll, x, lift,
                spin, origin_y=y0, brace_material=brace_mat,
            )
        if door:
            add_doorway(door, rod_radius_m, coll, x, lift, spin, origin_y=y0)
            # In the doorway, not beside it: the row exists to be read at a
            # glance, and the one thing worth reading is whether the person
            # gets in.
            add_humans(
                x, -radius_m, human_mats, coll, meta["variant"], origin_y=y0
            )
        else:
            add_humans(
                x + radius_m * 0.45, 0.0, human_mats, coll, meta["variant"],
                origin_y=y0,
            )

        if not args.no_labels:
            skirt_mm = meta.get("skirt_height", 0.0)
            tall = meta.get("overall_height", meta["dome_height_measured"]) * MM
            # One line. Rotated upright, extra lines run downwards and end up
            # under the ground plane, where nobody reads them.
            name = meta.get("alias") or meta["variant"]
            text = f"{name}  {meta['dome_diameter'] * MM:.0f} x {tall:.1f} m"
            if skirt_mm:
                text += f" (+{skirt_mm * MM:.1f} skirt)"
            add_label(text, x, -radius_m - 1.6 + y0, label_mat, coll)

        placed.append((meta["variant"], x, radius_m, meta))
        max_radius = max(max_radius, radius_m)
        x += radius_m

    span = x
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(span / 2.0, 0.0, 0.0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.scale = (span * 4.0, span * 3.0, 1.0)
    ground.data.materials.append(material("Ground", GROUND_COLOUR))
    move_to(ground, root)

    return placed, span, max_radius


def add_camera_and_light(scene, span, max_radius, tallest, aspect=2000.0 / 900.0):
    """Frame the whole row from its length rather than by guesswork.

    The horizontal half-angle of a 35 mm-format camera is atan(18/lens); the
    distance needed to fit `span` follows from that, with a margin. Guessing
    it, as the first attempt did, cut the end domes off the frame.
    """
    lens = 40.0
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)

    half_angle = math.atan(18.0 / lens)
    needed = (span * 0.78) / math.tan(half_angle)
    height = max(tallest * 1.6, needed * 0.20)
    cam.location = (span * 0.5, -needed, height)
    target = Vector((span * 0.5, 0.0, tallest * 0.40))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 3.5
    sun = bpy.data.objects.new("Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.location = (span * 0.4, -span * 0.3, tallest * 3.0)
    sun.rotation_euler = (math.radians(52), 0.0, math.radians(30))


def render(scene, path, width=2000, height=900):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = os.path.abspath(path)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath


def main():
    args = parse_args(sys.argv)
    models = load_models(args)
    if not models:
        raise SystemExit(
            "no models with polylines found.\n"
            "run:  python3 -m stardome build --all --polylines --weave-mode layered"
        )

    placed, span, max_radius = build(args, models)
    tallest = max(
        m.get("overall_height", m["dome_height_measured"]) * MM for _, _, _, m in placed
    )
    add_camera_and_light(bpy.context.scene, span, max_radius, tallest)

    print(f"[site] {len(placed)} domes over {span:.1f} m, tallest {tallest:.2f} m")
    for name, x, radius_m, meta in placed:
        tall = meta.get("overall_height", meta["dome_height_measured"]) * MM
        skirt = meta.get("skirt_height", 0.0) * MM
        print(
            f"[site]   {name:<4} {meta['dome_diameter'] * MM:>5.1f} m across, "
            f"{tall:>5.2f} m tall"
            + (f" (incl. {skirt:.1f} m skirt)" if skirt else "")
            + f", centre at x={x:.1f} m"
        )

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print(f"[site] saved {args.out}")
    if args.render:
        print(f"[site] rendered {render(bpy.context.scene, args.render)}")


if __name__ == "__main__":
    main()
