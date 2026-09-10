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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import (  # noqa: E402  -- needs the path set above
    MM,
    make_transparent,
    material,
    move_to,
    new_collection,
    rod_runs,
    segment,
)

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
CORRIDOR_COLOUR = (0.62, 0.72, 0.58, 1.0)      # corridor hoops, not dome rod
CORRIDOR_SKIN_COLOUR = (0.88, 0.86, 0.80, 1.0)  # fabric
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
        "--aerial",
        action="store_true",
        help="look down on the camp, so the corridors read as tunnels rather "
             "than as frames round each doorway",
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


def add_corridor(corridor, rod_radius_m, material_, skin_material, collection,
                 origin_x, lift, spin_deg=0.0, origin_y=0.0):
    """Hoops and skin, straight from the model, placed like everything else."""
    drawing = corridor.get("drawing")
    if not drawing:
        return

    def put(x, y, z):
        px, py = _place(x, y, origin_x, spin_deg, origin_y)
        return (px, py, z * MM + lift)

    for i, hoop in enumerate(drawing["hoops"], start=1):
        curve = bpy.data.curves.new(f"CorridorHoop_{i}", "CURVE")
        curve.dimensions = "3D"
        spline = curve.splines.new("POLY")
        spline.points.add(len(hoop) - 1)
        for point, (x, y, z) in zip(spline.points, hoop):
            point.co = (*put(x, y, z), 1.0)
        curve.bevel_depth = rod_radius_m
        curve.bevel_resolution = 3
        obj = bpy.data.objects.new(f"Corridor_Hoop_{i}", curve)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(material_)
        move_to(obj, collection)

    skin = drawing["skin"]
    mesh = bpy.data.meshes.new("Corridor_Skin")
    mesh.from_pydata([put(*v) for v in skin["vertices"]], [],
                     [f[:] for f in skin["faces"]])
    mesh.update()
    obj = bpy.data.objects.new("Corridor_Skin", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(skin_material)
    move_to(obj, collection)


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


def add_label(text, origin_x, y, material_, collection, size=0.62):
    bpy.ops.object.text_add(location=(origin_x, y, 0.05))
    obj = bpy.context.active_object
    obj.data.body = text
    obj.data.align_x = "CENTER"
    # Scaled to the dome it names, so a 3 m label does not run into a 4 m one.
    obj.data.size = size
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
    corridor_mat = material("Corridor_Hoop", CORRIDOR_COLOUR)
    corridor_skin_mat = make_transparent(
        material("Corridor_Skin", CORRIDOR_SKIN_COLOUR), 0.30
    )

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
        corridor = data.get("corridor") or {}
        if corridor.get("present") and corridor.get("drawing"):
            add_corridor(
                corridor, rod_radius_m, corridor_mat, corridor_skin_mat,
                coll, x, lift, spin, origin_y=y0,
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
            add_label(
                text, x, -radius_m - 1.6 + y0, label_mat, coll,
                size=max(0.30, radius_m * 0.16),
            )

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


def add_camera_and_light(scene, span, max_radius, tallest, aspect=2000.0 / 900.0,
                         aerial=False):
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
    needed = (span * 0.72) / math.tan(half_angle)
    # Low and close to the row's own height rather than high and far: a long
    # row seen from far above is mostly ground.
    # Nearly level with the row. Higher than this and a long row is mostly
    # ground; the domes stand side by side so nothing occludes anything.
    if aerial:
        # A camp is read from above: every door faces the yard, so every
        # corridor points at a level camera and foreshortens to a frame round
        # the doorway. Lifting the eye is what turns them back into tunnels.
        cam.location = (span * 0.5, -needed * 0.72, tallest * 2.9)
        target = Vector((span * 0.5, max_radius * 0.15, tallest * 0.30))
    else:
        # Nearly level with the row: a long row seen from far above is mostly
        # ground, and the domes stand side by side so nothing occludes
        # anything.
        cam.location = (span * 0.5, -needed, tallest * 0.8)
        target = Vector((span * 0.5, 0.0, tallest * 0.45))
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
    add_camera_and_light(bpy.context.scene, span, max_radius, tallest,
                         aerial=args.aerial)

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
