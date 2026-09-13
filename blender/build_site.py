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

``--walk`` turns the scene from something to look at into something to walk
through, which needs three changes at once and is useless without all three:
the covers go opaque, a lamp goes inside every dome and every corridor -- an
opaque dome in sunlight is a black hole from within -- and the scene camera
becomes an eye 1.7 m off the ground, standing outside the camp looking at it::

    make camp CAMP=court CAMP_KIND=portal CAMP_FLAGS="--cover --figures one --walk"

Blender does the walking: Numpad 0 for the camera view, then Shift+` for Walk
Navigation. W A S D to move, mouse to look, Q and E down and up, Shift to run,
Tab for gravity, left-click to keep where you got to and Esc to snap back.
Gravity is a preference rather than a scene setting, so it cannot be shipped
in the .blend: Preferences > Navigation > Walk > Gravity.

"""

import argparse
import glob
import json
import math
import os
import sys

import bmesh
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
        "--walk",
        action="store_true",
        help="set the scene up to be walked through at eye height rather than "
             "looked at: the covers go opaque, a lamp goes inside every dome "
             "and every corridor, and the camera stands 1.7 m off the ground. "
             "Blender's own Walk Navigation (Shift+`) does the walking",
    )
    p.add_argument(
        "--lamp-gain",
        dest="lamp_gain",
        type=float,
        default=1.0,
        help="multiply the inside lighting by this. What a fabric dome at "
             "dusk looks like is a taste, not a measurement, so it is a dial "
             "rather than a constant; 1.0 is 3 W per square metre of floor",
    )
    p.add_argument(
        "--figures",
        choices=("every", "one", "none"),
        default="every",
        help="how many of the two reference figures to stand in the scene. "
             "A size row wants them at every dome, which is the point of it; "
             "a camp of eight wants one pair somewhere to read the scale by, "
             "and sixteen people standing in doorways is clutter",
    )
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
        help="only the sizes with a short name (S, M, L, XL, XXL), skipping the "
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
                origin_y=0.0, fill=True):
    """The opening, outlined and filled, exactly as the model reports it.

    ``fill`` draws the translucent panel across the opening. It says "this is
    the hole" in a picture and it is a wall in a walk-through, so the walker
    does without it. Returns the outline's points as well, because cutting the
    hole out of the cover wants exactly the curve that was just drawn.
    """
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

    if not fill:
        return obj, None, points

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
    return obj, panel, points


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
# The other kind of corridor is boards, not rod: a timber P-frame. It arrives
# as solid meshes rather than centrelines, because a board has a thickness and
# a bent rod does not.
CORRIDOR_BOARD_COLOUR = (0.55, 0.38, 0.20, 1.0)

# Walking through it rather than looking at it. The cover has to stop being a
# window, the inside has to have light of its own -- an opaque dome in sunlight
# is a black hole from inside -- and the eye has to be where an eye is.
WALK_EYE_M = 1.70
WALK_LENS_MM = 24.0
# A lamp hangs at this fraction of the dome's clear height, and its power goes
# with the floor it has to cover. Watts, as EEVEE counts them. The first pass
# at this was 14 W/m2, which is a floodlit hangar: the fabric blew out white
# and the frame stopped reading against it.
WALK_LAMP_AT = 0.72
WALK_LAMP_W_PER_M2 = 3.0
WALK_CORRIDOR_LAMP_W = 18.0
# A tunnel lamp hangs this far under the roof. At head height it sat exactly
# where the walker's eyes go.
WALK_CORRIDOR_LAMP_DROP_M = 0.30


def load_plan(path):
    """A camp as `stardome camp --json` wrote it.

    The plan is consumed, not recomputed: where each dome stands, how far it
    is turned and the corridors between them all arrive as finished numbers.
    See docs/architecture.md.
    """
    with open(path) as handle:
        return json.load(handle)


def plan_layout(plan, models, plan_path):
    """The model of each dome in the plan.

    A dome in a camp carries a door per neighbour, so it is not the plain
    variant: the plan ships each one and names it, and that file is what gets
    drawn. Falling back to the variant is for a plan written before they were
    shipped, and it draws the wrong doors -- so it says so.
    """
    by_variant = {d["meta"]["variant"]: d for d in models}
    beside = os.path.dirname(os.path.abspath(plan_path))
    out = []
    for dome in plan["domes"]:
        if dome.get("model"):
            with open(os.path.join(beside, dome["model"])) as handle:
                data = json.load(handle)
        else:
            print(
                f"[site] {dome['name']}: the plan ships no model, drawing the "
                f"plain {dome['variant']} -- its doors will be wrong"
            )
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
                "doors": list(dome.get("doors") or ()),
            }
        )
    return out


def add_corridors(plan, collection, lift_is_ground=True, alpha=None):
    """The corridors, from the mouths and rings the plan already solved.

    Nothing is computed here. Each link arrives with its two mouth loops and
    the rings between them in camp coordinates, so the skin is a quad strip
    between matching points and a ring is a closed curve.
    """
    made = 0
    # The corridor's skin keeps its single face, so it keeps its own alpha.
    skin_mat = make_transparent(
        material("Corridor", COVER_COLOUR),
        COVER_ALPHA if alpha is None else alpha,
    )
    hoop_mat = material("Corridor_Hoop", CORRIDOR_HOOP_COLOUR)
    board_mat = material("Corridor_Board", CORRIDOR_BOARD_COLOUR)
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

        # A timber portal is five boards with thickness, so the plan ships it
        # as a solid rather than as a curve to be bevelled.
        for k, frame in enumerate(drawing.get("frames") or ()):
            verts = [(px * MM, py * MM, pz * MM) for px, py, pz in frame["vertices"]]
            fmesh = bpy.data.meshes.new(f"Frame_{index}_{k}")
            fmesh.from_pydata(verts, [], [list(f) for f in frame["faces"]])
            fmesh.update()
            board = bpy.data.objects.new(f"Frame_{index}_{k}", fmesh)
            board.data.materials.append(board_mat)
            bpy.context.scene.collection.objects.link(board)
            move_to(board, collection)
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


def add_cover(data, collection, origin_x, spin_deg, origin_y, lift,
              alpha=None):
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
    # The cover is given thickness so its openings can be cut, so a sight line
    # through it now crosses TWO faces where it used to cross one. At face
    # value 0.14 that reads as 0.26 and the camp turns milky. Thin each face
    # until the pair comes to what the single one was: 1-(1-a)^2 == 0.14.
    if alpha is None:
        alpha = 1.0 - math.sqrt(1.0 - COVER_ALPHA)
    obj.data.materials.append(
        make_transparent(material("Cover", COVER_COLOUR), alpha)
    )
    return move_to(obj, collection)


# How far a hole-cutter reaches either side of the surface it cuts. The mouth
# lies ON the cover, so this only has to be more than the cover is thick --
# which is nothing -- plus enough to survive the curvature it sits on.
CUTTER_REACH_M = 1.0


def solid_from(name, verts, faces, collection):
    """A closed mesh with its normals facing out, fit to cut with."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return move_to(obj, collection)


def mouth_cutter(loop, bearing_deg, name, collection, reach=CUTTER_REACH_M):
    """The tunnel's mouth as a solid prism, for cutting the cover open.

    The mouth is a closed curve lying on the cover. Swept along the corridor's
    own axis it becomes a plug through the cover, and the cover minus that plug
    is a cover with a doorway the shape of the tunnel in it.
    """
    a = math.radians(bearing_deg)
    dx, dy = math.cos(a) * reach, math.sin(a) * reach
    n = len(loop)
    verts = []
    for sign in (-1.0, 1.0):
        for px, py, pz in loop:
            verts.append((px * MM + dx * sign, py * MM + dy * sign, pz * MM))
    faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    faces.append(list(range(n - 1, -1, -1)))
    faces.append(list(range(n, 2 * n)))
    return solid_from(name, verts, faces, collection)


# The thickest the fabric is ever drawn, and the thinnest worth drawing.
COVER_THICKNESS_MAX_M = 0.010
COVER_THICKNESS_MIN_M = 0.002


def fabric_thickness(data):
    """How thick to draw this dome's cover, in metres.

    It has to be thick enough to be a solid -- see ``give_it_thickness`` -- and
    thinner than the room between the cover and the outside of the rod it is
    draped over, or the inner face swallows the frame and the dome is a plain
    shell from inside. That room is small and it is not the same at every size:
    18 mm on XL, 15 on L, 12 on S. Half of it, capped.
    """
    from_the_rod = (
        cover_radius_mm(data)
        - data["meta"]["dome_radius"]
        - data["meta"]["rod_diameter"] / 2.0
    ) * MM
    return max(
        COVER_THICKNESS_MIN_M, min(COVER_THICKNESS_MAX_M, from_the_rod * 0.5)
    )


def cover_radius_mm(data):
    """The radius the cover mesh was built on, read off the mesh itself.

    The model ships the surface rather than the number, so this measures what
    arrived instead of recomputing what `stardome` already decided.
    """
    verts = (data.get("cover") or {}).get("mesh", {}).get("vertices") or ()
    return max(
        (math.hypot(math.hypot(v[0], v[1]), v[2]) for v in verts),
        default=data["meta"]["dome_radius"],
    )


def give_it_thickness(obj, thickness):
    """Turn a surface into a shell with two sides.

    Fabric is thin, not infinitely thin, and the difference decides whether a
    hole can be cut in it. The exact boolean solver decides what is inside a
    target by winding number, and an open sheet has none -- asked to take a
    plug out of one it welds the plug's own end cap in instead, which is a
    cover with a bump where a doorway should be. A ray out of the hub stopped
    dead on it, one metre short of where the cover actually is.
    """
    mod = obj.modifiers.new("Thickness", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = -1.0                 # grow inward; the outside stays put
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return True
    except RuntimeError:
        obj.modifiers.remove(mod)
        return False


def door_cutter(points, at, name, collection, reach=CUTTER_REACH_M):
    """The doorway as a solid plug, swept out of the dome along its own radius.

    The opening spans about a third of a bay in azimuth, so it is not flat and
    no single direction is normal to all of it. It does not have to be: the
    cover is 30 mm thick and the sweep is a metre, so the mean outward radius
    passes clean through every part of the curve.
    """
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    out = Vector((cx - at[0], cy - at[1], 0.0))
    if out.length < 1e-6:
        out = Vector((1.0, 0.0, 0.0))
    out.normalize()

    n = len(points)
    verts = []
    for sign in (-1.0, 1.0):
        for px, py, pz in points:
            verts.append((px + out.x * reach * sign,
                          py + out.y * reach * sign,
                          pz))
    faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    faces.append(list(range(n - 1, -1, -1)))
    faces.append(list(range(n, 2 * n)))
    return solid_from(name, verts, faces, collection)


def cut_out(target, cutters):
    """Take the cutters out of the target, and throw them away.

    One boolean per cutter rather than one over a joined cutter: a cover is an
    open surface, and the exact solver copes with that far better one plug at
    a time than with several at once.
    """
    done = 0
    for cutter in cutters:
        mod = target.modifiers.new(f"Hole_{done}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = cutter
        # A cover is an open shell, and the exact solver decides inside-ness
        # by winding number, which an open shell does not have. Without this
        # it plugs the hole with the cutter's own end cap instead of opening
        # one -- a ray out of the hub stopped on the cover a metre short of
        # where the cover is.
        if hasattr(mod, "use_hole_tolerant"):
            mod.use_hole_tolerant = True
        bpy.context.view_layer.objects.active = target
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            done += 1
        except RuntimeError as bad:
            print(f"[site]   could not open {target.name}: {bad}")
            target.modifiers.remove(mod)
    for cutter in cutters:
        bpy.data.objects.remove(cutter, do_unlink=True)
    return done


def corridor_bearings(plan):
    """``dome name -> the bearings it has a corridor on``."""
    out = {}
    for one in (plan or {}).get("links") or ():
        a, b = one["between"]
        out.setdefault(a, []).append(one["bearing_deg"] % 360.0)
        out.setdefault(b, []).append((one["bearing_deg"] + 180.0) % 360.0)
    return out


def facing_a_corridor(door, turn_deg, bearings, within=36.0):
    """Is this door the one a corridor lands on?

    Within half a bay of a corridor's bearing and it is: a door is placed in
    the nearest bay to the bearing that asked for it, so it is never further
    off than that and nothing else can be nearer.
    """
    if not bearings:
        return False
    at = ((door.get("bay") or {}).get("centre_azimuth_deg", 0.0) + turn_deg) % 360.0
    return any(
        abs((at - b + 180.0) % 360.0 - 180.0) <= within for b in bearings
    )


def open_the_covers(plan, covers, doors, collection):
    """Cut the cover open wherever something is supposed to go through it.

    The cover is a closed shell of revolution: it has no doorway and no hole
    where a corridor lands, so a camp that looks joined is a row of sealed
    domes with tubes leaning on them and a door painted on. It does not show
    while the fabric is see-through. It is the whole thing once you are inside
    -- and in a walk-through it is a wall.

    Two kinds of opening, one mechanism: a plug swept along the axis of
    whatever is meant to pass through, taken out of the cover.
    """
    for cover in {id(c): c for c in covers.values() if c is not None}.values():
        give_it_thickness(cover, cover.get("fabric_m", COVER_THICKNESS_MAX_M))

    mouths = 0
    for one in (plan or {}).get("links") or ():
        drawing = one.get("drawing")
        if not drawing:
            continue
        for name, loop in zip(one["between"], drawing["mouths"]):
            cover = covers.get(name)
            if cover is None:
                continue
            cutter = mouth_cutter(
                loop, one["bearing_deg"], f"Mouth_{name}_{mouths}", collection
            )
            mouths += cut_out(cover, [cutter])

    holes = 0
    for name, points, at in doors:
        cover = covers.get(name)
        if cover is None:
            continue
        cutter = door_cutter(points, at, f"Door_{name}_{holes}", collection)
        holes += cut_out(cover, [cutter])
    return mouths, holes


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


def add_lamp(name, location, watts, collection, radius=0.35):
    """One soft point light, for a space that has a roof on it."""
    data = bpy.data.lights.new(name, type="POINT")
    data.energy = watts
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    return move_to(obj, collection)


def add_inside_lights(spots, plan, collection, gain=1.0):
    """A lamp inside every dome and every corridor.

    Only needed once the cover is opaque, and then it is not optional: a closed
    dome in sunlight is a black hole from the inside, and seeing the inside is
    the whole point of walking through the camp.

    Power goes with the floor a lamp has to cover, so the 12 m dome is not lit
    to the same few watts as the 4 m one. ``spots`` comes from the dome loop,
    because a row works out where its domes stand as it lays them and only the
    loop knows.
    """
    made = 0
    for spot in spots:
        watts = gain * WALK_LAMP_W_PER_M2 * math.pi * spot["radius_m"] ** 2
        add_lamp(
            f"Lamp_{spot['name']}",
            (spot["x"], spot["y"], spot["tall"] * WALK_LAMP_AT),
            watts,
            collection,
        )
        made += 1

    for index, one in enumerate((plan or {}).get("links") or ()):
        drawing = one.get("drawing")
        if not drawing:
            continue
        # Midway along the run, at head height: the two mouth loops averaged.
        points = drawing["mouths"][0] + drawing["mouths"][1]
        cx = sum(p[0] for p in points) / len(points) * MM
        cy = sum(p[1] for p in points) / len(points) * MM
        roof = (one.get("section") or {}).get("height_mm", 0.0) * MM
        lamp = add_lamp(
            f"Lamp_Corridor_{index}",
            (cx, cy, max(1.0, roof - WALK_CORRIDOR_LAMP_DROP_M)),
            gain * WALK_CORRIDOR_LAMP_W,
            collection,
            radius=0.15,
        )
        # A tunnel lamp is fill, and a shadow map for each one overruns
        # EEVEE's pool -- sixteen lights in this camp asked for 2400 of the
        # 2048 it has. The domes keep theirs, where shadow is the whole
        # character of the space.
        lamp.data.use_shadow = False
        made += 1
    return made


# How far clear of the outermost cover the walk starts.
APPROACH_M = 5.0


def approach(spots):
    """Where to start a walk: outside the camp, looking at it.

    Two rules were tried before this one and both put the eye somewhere
    useless. "The point with the most room round it" is unbounded on open
    ground -- the answer is always the far corner of whatever box you searched,
    28 m away with its back to the camp. "Three metres out along the biggest
    dome's door bearing" lands INSIDE the corridor hanging off that door,
    because a corridor is what a door faces in a camp; the view is a portal
    frame at arm's length.

    So: out past everything, on the side the biggest dome is on, looking back
    at the middle. You see the whole camp, and walking straight ahead takes you
    to the door of the largest thing in it.
    """
    if not spots:
        return (0.0, -APPROACH_M), Vector((0.0, 1.0, 0.0))
    cx = sum(s["x"] for s in spots) / len(spots)
    cy = sum(s["y"] for s in spots) / len(spots)

    dome = max(spots, key=lambda s: s["radius_m"])
    out = Vector((dome["x"] - cx, dome["y"] - cy, 0.0))
    if out.length < 1e-6:
        # The biggest dome IS the middle -- a row of one, or a hub camp
        # weighted evenly. Back off the way a row's doors face.
        out = Vector((0.0, -1.0, 0.0))
    out.normalize()

    reach = max(
        math.hypot(s["x"] - cx, s["y"] - cy) + s["radius_m"] for s in spots
    )
    stand = (cx + out.x * (reach + APPROACH_M), cy + out.y * (reach + APPROACH_M))
    return stand, Vector((cx - stand[0], cy - stand[1], 0.0))


def add_eye_camera(scene, spots):
    """A camera where an eye is, for Blender's own Walk Navigation to drive.

    The overview camera is a portrait of the camp and is no use for walking: it
    stands well back and well up. This one stands on the ground just outside
    the camp -- see ``approach`` -- and is short-sighted enough at the near
    end that putting your face through a doorway does not clip the world away.
    """
    data = bpy.data.cameras.new("Eye")
    data.lens = WALK_LENS_MM
    data.clip_start = 0.05
    data.clip_end = 500.0
    cam = bpy.data.objects.new("Eye", data)
    scene.collection.objects.link(cam)

    stand, look = approach(spots)
    cam.location = (stand[0], stand[1], WALK_EYE_M)
    if look.length < 1e-6:
        look = Vector((0.0, 1.0, 0.0))
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    return cam


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
    # Where each dome ended up, for anything that has to be put INSIDE it. A
    # row works its positions out as it lays them, so only the loop knows.
    spots = []
    # Each dome's cover object by the dome's own name, so a corridor can be
    # cut out of the right one. Two domes of the same variant share a variant
    # name and do not share a cover.
    covers = {}
    # Each dome's doorway outline, for cutting the opening out of its cover.
    doors_to_cut = []
    max_radius = 0.0
    plan = load_plan(args.plan) if args.plan else None
    layout = (
        plan_layout(plan, models, args.plan)
        if plan
        else [{"data": d} for d in models]
    )
    corridors = corridor_bearings(plan)
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
    # Which domes get the two reference figures. "one" puts the pair at the
    # biggest dome in the scene: it is the one whose door has the most room to
    # spare, so a figure standing in it reads as scale rather than as a fit
    # check somebody has to squint at.
    if args.figures == "none" or not layout:
        figures_at = set()
    elif args.figures == "one":
        figures_at = {
            max(
                range(len(layout)),
                key=lambda k: layout[k]["data"]["meta"]["dome_radius"],
            )
        }
    else:
        figures_at = set(range(len(layout)))

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

        # A dome in a camp carries a door per neighbour and may carry one more
        # to get in by, so this is a list. ``doorway`` is the first of them,
        # kept for a dome that has only one.
        all_doors = list(data.get("doorways") or ())
        if not all_doors and data.get("doorway"):
            all_doors = [data["doorway"]]
        door = all_doors[0] if all_doors else None
        # A portal has no lancet, so no pair of jambs to pick out: the
        # traced outline and the ghosts of the cut pieces carry it instead.
        jambs = set()
        for one_door in all_doors:
            if one_door.get("frame"):
                jambs |= set(one_door["frame"]["jamb_rods"])

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
            cover_obj = add_cover(
                data, coll, x, spin, y0, lift,
                alpha=1.0 if args.walk else None,
            )
            if cover_obj is not None:
                cover_obj["fabric_m"] = fabric_thickness(data)
            covers[coll_name] = cover_obj
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
        for one_door in all_doors:
            _outline, _panel, door_points = add_doorway(
                one_door, rod_radius_m, coll, x, lift, spin, origin_y=y0,
                fill=not args.walk,
            )
            # A door with a corridor on it is opened to the TUNNEL'S mouth and
            # not to the whole bay. The bay is the wider of the two -- 3.0 m of
            # clear opening against an 1.8 m portal on XL -- so cutting both
            # leaves a slot of daylight all round the tunnel where the cover
            # has been taken away and nothing has been put back.
            if not facing_a_corridor(one_door, spin, corridors.get(coll_name)):
                doors_to_cut.append((coll_name, door_points, (x, y0)))
        if index in figures_at:
            if door:
                # In the doorway, not beside it: the row exists to be read at
                # a glance, and the one thing worth reading is whether the
                # person gets in.
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
        spots.append({
            "name": coll_name,
            "x": x,
            "y": y0,
            "radius_m": radius_m,
            "tall": meta.get("overall_height", meta["dome_height_measured"]) * MM,
            # Which way this dome's first door points, in camp bearings. A row
            # aims every door at the viewer, who stands at -Y.
            "door_deg": (item.get("doors") or [270.0])[0],
        })
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
        links = add_corridors(
            plan, new_collection("Corridors", root),
            alpha=1.0 if args.walk else None,
        )
        print(f"[site]   {links} corridors drawn")
    if covers:
        mouths, doors = open_the_covers(
            plan, covers, doors_to_cut, new_collection("_Cutters", root)
        )
        print(
            f"[site]   cover opened: {mouths} corridor mouths, {doors} doorways"
        )
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

    if args.walk:
        lamps = add_inside_lights(
            spots, plan, new_collection("Lights", root), gain=args.lamp_gain
        )
        print(f"[site]   {lamps} lamps inside, and the covers are opaque")

    return placed, span, max_radius, (centre_x, centre_y), spots


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

    placed, span, max_radius, centre, spots = build(args, models)
    tallest = max(
        m.get("overall_height", m["dome_height_measured"]) * MM for _, _, _, m in placed
    )
    add_camera_and_light(
        bpy.context.scene, span, max_radius, tallest,
        centre=centre, overhead=bool(args.plan),
    )
    overview = bpy.context.scene.camera
    if args.walk:
        add_eye_camera(bpy.context.scene, spots)
        # A lamp in every dome is a shadow map in every dome, and EEVEE's pool
        # is 512 MB by default. Eight domes overran it.
        try:
            bpy.context.scene.eevee.shadow_pool_size = "2048"
        except (AttributeError, TypeError):
            pass
        print(
            "[site] walk mode: the Eye camera is the scene camera, 1.7 m up.\n"
            "[site]   in Blender: Numpad 0 for the camera view, then Shift+` "
            "to walk it.\n"
            "[site]   W A S D to move, mouse to look, Q/E down and up, Shift "
            "to run, Tab for gravity,\n"
            "[site]   left-click to keep where you walked to and Esc to snap "
            "back. Turning gravity on\n"
            "[site]   for good is Preferences > Navigation > Walk > Gravity."
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
        # The Eye is the scene camera so that Numpad 0 lands you on the ground
        # ready to walk. A still taken from it is a picture of the inside of
        # one dome, which is no use as a preview, so the overview takes the
        # render and hands the camera straight back.
        scene = bpy.context.scene
        eye = scene.camera
        if args.walk and overview is not None:
            scene.camera = overview
        print(f"[site] rendered {render(scene, args.render)}")
        scene.camera = eye


if __name__ == "__main__":
    main()
