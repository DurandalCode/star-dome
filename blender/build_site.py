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

``--cover`` drapes each dome in its fabric as one surface -- no seams and no
hem, the way a corridor's skin is drawn. The single-dome scene draws those
because there the question is how the cover is cut and held; here the question
is what a camp looks like.

``--connectors real`` stands the built parts on the rods. It needs a woven
model, because layered spreads a crossing over more than a connector stack is
tall, and it needs the meshes to have been exported. Whatever has none is
reported and left out rather than quietly missing::

    python3 -m stardome build S M L --polylines --weave-mode woven
    python3 -m stardome connectors S M L --json
    make clamps V=S && make clamps V=M && make clamps V=L
    make camp

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
    import_stl,
    make_transparent,
    material,
    move_to,
    new_collection,
    part_pieces,
    place_instance,
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
    p.add_argument(
        "--cover",
        action="store_true",
        help="drape each dome in its fabric -- the surface only, no seams and "
             "no hem, which is what a site view wants",
    )
    p.add_argument(
        "--connectors",
        choices=("none", "real"),
        default="none",
        help="stand the built connectors on the rods; needs a woven model and "
             "`make clamps` to have run",
    )
    p.add_argument(
        "--plan",
        default=None,
        metavar="FILE",
        help="a camp written by `stardome camp --json`: the domes go where it "
             "says, turned as it says, and its corridors are drawn between "
             "them. Replaces the size-row layout and --camp",
    )
    p.add_argument(
        "--connector-dir",
        default=None,
        help="where the exported meshes are; defaults to exports/connectors",
    )
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
        # Kept so the schedule beside it can be found later, the same way
        # build_scene keeps its cameras on the model it built them for.
        data["_path"] = path
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


COVER_COLOUR = (0.88, 0.86, 0.80, 1.0)
# Thinner than the single-dome scene's 0.28. A site view is looked at from
# far enough away that the fabric stacks up over a whole hemisphere, and at
# 0.28 it goes milky and hides the frame -- which is the one thing the
# translucency exists to avoid.
COVER_ALPHA = 0.14
# A corridor hoop is a thinner rod than a bow, bent far harder -- see
# docs/corridor.md. Drawn at a fixed radius because what it is made of is a
# purchasing decision nobody has taken.
CORRIDOR_HOOP_COLOUR = (0.75, 0.55, 0.25, 1.0)
CORRIDOR_HOOP_RADIUS_M = 0.005


def load_plan(path):
    """A camp as `stardome camp --json` wrote it.

    The plan is consumed, not recomputed: where each dome stands, how far it
    is turned and the corridors between them all arrive as finished numbers.
    See docs/architecture.md.
    """
    with open(path) as handle:
        return json.load(handle)


def plan_layout(plan, models):
    """Match each dome in the plan to the model of its variant.

    A camp can hold two domes of one variant -- they are one model placed
    twice, which is also why the model is built once and shared.
    """
    by_variant = {d["meta"]["variant"]: d for d in models}
    out = []
    for dome in plan["domes"]:
        data = by_variant.get(dome["variant"])
        if data is None:
            raise SystemExit(
                f"the plan wants {dome['variant']} for {dome['name']!r} and no "
                f"model of it was loaded.\n"
                "build it with:  python3 -m stardome build "
                f"{dome['variant']} --polylines --weave-mode woven"
            )
        out.append(
            {
                "name": dome["name"],
                "data": data,
                "at": (dome["at"][0] * MM, dome["at"][1] * MM),
                "turn": dome["turn_deg"],
            }
        )
    return out


def add_corridors(plan, collection, lift_is_ground=True):
    """The corridors, from the mouths and rings the plan already solved.

    Nothing is computed here. Each link arrives with its two mouth loops and
    the rings between them in camp coordinates, so the skin is a quad strip
    between matching points and a ring is a closed curve.
    """
    made = 0
    skin_mat = make_transparent(material("Corridor", COVER_COLOUR), COVER_ALPHA)
    hoop_mat = material("Corridor_Hoop", CORRIDOR_HOOP_COLOUR)
    for index, one in enumerate(plan.get("links") or ()):
        drawing = one.get("drawing")
        if not drawing:
            continue
        a, b = (
            [(px * MM, py * MM, pz * MM) for px, py, pz in loop]
            for loop in drawing["mouths"]
        )
        verts = a + b
        n = len(a)
        faces = [
            (i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)
        ]
        mesh = bpy.data.meshes.new(f"CorridorSkin_{index}")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(
            "Corridor_" + "_".join(one["between"]), mesh
        )
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(skin_mat)
        move_to(obj, collection)

        for k, ring in enumerate(drawing.get("rings") or ()):
            pts = [(px * MM, py * MM, pz * MM) for px, py, pz in ring]
            curve = bpy.data.curves.new(f"Hoop_{index}_{k}", "CURVE")
            curve.dimensions = "3D"
            curve.bevel_depth = CORRIDOR_HOOP_RADIUS_M
            curve.bevel_resolution = 3
            spline = curve.splines.new("POLY")
            spline.points.add(len(pts) - 1)
            for i, (px, py, pz) in enumerate(pts):
                spline.points[i].co = (px, py, pz, 1.0)
            spline.use_cyclic_u = True
            hoop = bpy.data.objects.new(f"Hoop_{index}_{k}", curve)
            hoop.data.materials.append(hoop_mat)
            bpy.context.scene.collection.objects.link(hoop)
            move_to(hoop, collection)
        made += 1
    return made


def connector_dir(model_path, override=None):
    """Where the exported meshes live: beside the models, not among them."""
    if override:
        return override
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(model_path))),
        "connectors",
    )


def load_schedule(model_path, override=None):
    """The schedule that goes with one model, or None if there is not one.

    A site is several domes and some of them may never have had their
    connectors written. That is not a reason to refuse the whole scene the way
    the single-dome script does -- it is a reason to say which dome went
    without.
    """
    stem = os.path.splitext(model_path)[0]
    path = f"{stem}_connectors.json"
    if not os.path.exists(path):
        return None
    with open(path) as handle:
        schedule = json.load(handle)
    return schedule if schedule.get("placements") else None


def add_cover(data, collection, origin_x, spin_deg, origin_y, lift):
    """The fabric as one surface, and nothing else.

    The single-dome scene draws the seams and the hem as well, because there
    the question is how the cover is cut and held. Here the question is what
    a camp looks like, so the cover is a skin -- the same way a corridor's is
    -- and translucent, because an opaque one hides the structure the scene
    exists to show.
    """
    mesh_data = (data.get("cover") or {}).get("mesh")
    if not mesh_data:
        return None
    verts = []
    for vx, vy, vz in mesh_data["vertices"]:
        px, py = _place(vx, vy, origin_x, spin_deg, origin_y)
        verts.append((px, py, vz * MM + lift))
    mesh = bpy.data.meshes.new(f"Cover_{data['meta']['variant']}")
    mesh.from_pydata(verts, [], [f[:] for f in mesh_data["faces"]])
    mesh.update()
    obj = bpy.data.objects.new(f"Cover_{data['meta']['variant']}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(
        make_transparent(material("Cover", COVER_COLOUR), COVER_ALPHA)
    )
    return move_to(obj, collection)


def add_connectors(schedule, directory, collection, staging, origin_x,
                   spin_deg, origin_y, lift, meshes):
    """Stand the built connectors on one dome's rods.

    Each printed piece is imported once for the whole site and instanced after
    that -- three domes of a hundred connectors each is well over a thousand
    pieces, and importing every one makes a file nobody can open. ``meshes``
    is that cache, shared across the domes.

    What has no exported mesh is not drawn, and the count comes back so the
    caller can say so. A site view that quietly leaves out the parts nobody
    has built would show a camp that cannot be put up as though it could.
    """
    placed = missing = 0
    for spot in schedule.get("placements", ()):
        key = spot["part"]
        if key not in meshes:
            loaded = []
            for path in part_pieces(key, directory):
                obj = import_stl(path)
                if obj is None:
                    continue
                # The import is the source of the mesh, not a copy in the
                # scene: every real one is an instance over this same data.
                obj.hide_render = obj.hide_viewport = True
                move_to(obj, staging)
                loaded.append(obj.data)
            meshes[key] = loaded
        pieces = meshes[key]
        if not pieces:
            missing += 1
            continue
        for index, mesh in enumerate(pieces):
            place_instance(
                f"{key}_{spot['at']}_{index}",
                mesh,
                spot["origin_mm"],
                spot["basis"],
                collection,
                lift,
                place=lambda mx, my: _place(mx, my, origin_x, spin_deg, origin_y),
                spin_deg=spin_deg,
            )
        placed += 1
    return placed, missing


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

    x = 0.0
    placed = []
    max_radius = 0.0
    plan = load_plan(args.plan) if args.plan else None
    layout = plan_layout(plan, models) if plan else [{"data": d} for d in models]
    # One import per printed piece for the whole site, shared between domes:
    # three domes of a hundred connectors each is over a thousand pieces.
    connector_meshes = {}
    fitted = {}
    staging = new_collection("_ConnectorSource", root)
    # A camp rather than a size chart: the ends of the row swing back so the
    # domes stand round a yard, with every door still facing the open side.
    span_guess = sum(d["meta"]["dome_radius"] * MM * 2 for d in models) + (
        args.gap * max(0, len(models) - 1)
    )
    for index, item in enumerate(layout):
        data = item["data"]
        meta = data["meta"]
        radius_m = meta["dome_radius"] * MM
        rod_radius_m = meta["rod_diameter"] * MM / 2.0
        lift = meta.get("skirt_height", 0.0) * MM

        if plan is None:
            if placed:
                x += args.gap + radius_m
            if args.camp and len(models) > 1:
                # Parabolic: flat in the middle, swept back at both ends.
                t = (x / span_guess) * 2.0 - 1.0
                y0 = args.camp * t * t
            else:
                y0 = 0.0
            # A row aims every door at the viewer, because the row exists to
            # be read. A plan aims them at each other.
            spin = spin_for_door(data)
            coll_name = meta["variant"]
        else:
            x, y0 = item["at"]
            spin = item["turn"]
            coll_name = item["name"]
        coll = new_collection(coll_name, root)

        door = data.get("doorway")
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
        if args.cover:
            add_cover(data, coll, x, spin, y0, lift)
        if args.connectors != "none":
            if meta["weave_mode"] != "woven":
                raise SystemExit(
                    f"--connectors needs a woven model; {meta['variant']} is "
                    f"{meta['weave_mode']!r}.\n"
                    "'layered' is a drawing convention: it puts each bow on "
                    "its own shell, up to 14 rod diameters apart at a "
                    "crossing, and a connector stack is one. Rebuild with "
                    "--weave-mode woven."
                )
            schedule = load_schedule(data["_path"])
            if schedule is None:
                fitted[meta["variant"]] = None
            else:
                fitted[meta["variant"]] = add_connectors(
                    schedule,
                    connector_dir(data["_path"], args.connector_dir),
                    coll, staging, x, spin, y0, lift, connector_meshes,
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

        placed.append((coll_name, x, radius_m, meta))
        max_radius = max(max_radius, radius_m)
        if plan is None:
            x += radius_m

    centre_y = 0.0
    if plan is None:
        span = x
        centre_x = span / 2.0
    else:
        # A plan is two-dimensional, so the span is the bigger side of what it
        # covers and the ground is centred on the middle of it, not on the end
        # of a row that does not exist.
        xs = [item["at"][0] for item in layout]
        ys = [item["at"][1] for item in layout]
        span = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) + 2.0 * max_radius
        centre_x = (max(xs) + min(xs)) / 2.0
        centre_y = (max(ys) + min(ys)) / 2.0
    span = max(span, 1.0)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(centre_x, 0.0, 0.0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.scale = (span * 4.0, span * 3.0, 1.0)
    ground.data.materials.append(material("Ground", GROUND_COLOUR))
    move_to(ground, root)

    if plan is not None:
        links = add_corridors(plan, new_collection("Corridors", root))
        print(f"[site]   {links} corridors drawn")
        for problem in plan.get("problems") or ():
            print(f"[site]   plan says: {problem}")

    for name, result in sorted(fitted.items()):
        if result is None:
            print(
                f"[site]   {name}: no connector schedule -- write one with "
                f"`python3 -m stardome connectors {name} --json`"
            )
            continue
        done, short = result
        print(
            f"[site]   {name}: {done} connectors placed"
            + (
                f", {short} skipped with no exported mesh -- run `make clamps`"
                if short
                else ""
            )
        )

    return placed, span, max_radius, (centre_x, centre_y)


def add_camera_and_light(scene, span, max_radius, tallest, aspect=2000.0 / 900.0,
                         centre=(None, 0.0), overhead=False):
    """Frame the whole site from its size rather than by guesswork.

    The horizontal half-angle of a 35 mm-format camera is atan(18/lens); the
    distance needed to fit `span` follows from that, with a margin. Guessing
    it, as the first attempt did, cut the end domes off the frame.

    A row is looked at nearly level with itself, because a long row seen from
    above is mostly ground. A camp is not a row -- it has depth, and a level
    camera hides whatever stands behind -- so ``overhead`` lifts the eye and
    pulls it back along the diagonal instead.
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
    cx = span * 0.5 if centre[0] is None else centre[0]
    cy = centre[1]
    if overhead:
        # High enough to see past the near domes, and back far enough that the
        # whole plan is in frame rather than only its front row.
        height = max(tallest * 2.6, span * 0.45)
        cam.location = (cx, cy - needed * 0.78, height)
        target = Vector((cx, cy, tallest * 0.3))
    else:
        height = tallest * 0.8
        cam.location = (cx, -needed, height)
        target = Vector((cx, 0.0, tallest * 0.45))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 3.5
    sun = bpy.data.objects.new("Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.location = (cx, cy - span * 0.3, tallest * 3.0 + span * 0.2)
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

    placed, span, max_radius, centre = build(args, models)
    tallest = max(
        m.get("overall_height", m["dome_height_measured"]) * MM for _, _, _, m in placed
    )
    add_camera_and_light(
        bpy.context.scene, span, max_radius, tallest,
        centre=centre, overhead=bool(args.plan),
    )

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
