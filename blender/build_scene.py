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
them from eye level, an orthographic plan and elevation, and one close-up per
kind of joint the schedule places::

    blender --background --factory-startup --python blender/build_scene.py -- \
        --model exports/model/star_dome_d6.json --hide-cuts --shots exports/shots

``--spans FILE`` draws what ``stardome span`` measured: every bow goes grey,
the points that hold it get a marker, and the longest unsupported runs are
drawn over the top in red. It is the one picture that says why the family has
a size ceiling -- see docs/span.md::

    python3 -m stardome build D12 --polylines --weave-mode layered
    python3 -m stardome span D12 --json
    blender --background --factory-startup --python blender/build_scene.py -- \
        --model exports/model/star_dome_d12.json \
        --spans exports/model/D12/span.json \
        --shots exports/shots
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import (  # noqa: E402  -- needs the path set above
    MM,
    import_stl,
    make_transparent,
    material as make_material,
    mirror_mesh,
    move_to,
    part_pieces,
    new_collection,
    place_instance,
    rod_runs,
    segment,
)

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
COVER_COLOUR = (0.88, 0.86, 0.80, 1.0)     # fabric: off-white, not a rod colour

# The span overlay. The rods go quiet so that the two things being compared --
# where a bow is held, and how far it runs unheld -- are the only things with
# a colour in the frame.
SPAN_QUIET_COLOUR = (0.52, 0.53, 0.55, 1.0)
SPAN_WORST_COLOUR = (0.93, 0.16, 0.13, 1.0)
SPAN_HELD_COLOUR = (0.12, 0.80, 0.42, 1.0)
CORRIDOR_COLOUR = (0.62, 0.72, 0.58, 1.0)  # corridor hoops, distinct from dome rods
JAMB_COLOUR = (1.00, 0.42, 0.05, 1.0)      # the two rods that frame it

# Printed parts, by what holds what. Deliberately away from the rod families:
# the question a connector picture answers is "what is at this joint", and a
# part the colour of the rod it grips answers nothing.
PART_COLOUR = {
    "four_rod_fan":   (0.93, 0.90, 0.86, 1.0),   # printed plastic, off-white
    "two_rod_clamp":  (0.72, 0.74, 0.78, 1.0),   # cooler grey, and there are 30
    "base_hub":       (0.55, 0.58, 0.62, 1.0),   # darker: it is on the ground
    "cut_termination": (1.00, 0.78, 0.10, 1.0),  # doorway yellow, like the opening
    "ground_stake":   (0.30, 0.31, 0.34, 1.0),   # steel, driven, not printed
    "rod_splice":     (0.62, 0.72, 0.58, 1.0),
}
# A part with no generator is drawn as a block in the warning colour, the same
# move the cut-away rod pieces use: a picture that quietly leaves out the 47
# parts nobody has designed is a picture of a dome that does not exist.
UNDESIGNED_COLOUR = (0.90, 0.10, 0.10, 1.0)

# The cover and what holds it on. The seam has to read against the fabric it
# is sewn into, so it is the one thing here darker than the cloth.
SEAM_COLOUR = (0.15, 0.13, 0.11, 1.0)
STRAP_COLOUR = (0.95, 0.35, 0.10, 1.0)
ROPE_COLOUR = (0.10, 0.35, 0.85, 1.0)
LOOP_COLOUR = (1.00, 0.80, 0.10, 1.0)

# The ground stake: 30 mm steel angle, 500 mm long, and how much of it stands
# out of the soil.
#
# The generator draws the angle centred on the hub and says in as many words
# that it is a reference solid and not a placement -- how deep it goes is a
# site decision, not a drawn one. It has to stand out far enough to pass
# through the hub's through-slot, which is what lets the hub be dropped on
# after the angle is driven and find its own height.
#
# Two thirds out is a shallow set, and it is a choice rather than a result:
# the angle is what resists the dome spreading at its feet, and it does that
# through the soil it is buried in. 167 mm of embedment is what this leaves.
# Whether that holds is milestone 8 and a field test, not geometry.
STAKE_LENGTH_M = 0.500
STAKE_LEG_M = 0.030
STAKE_ABOVE_GROUND = 2.0 / 3.0
# How far in from the base point the angle stands. The hub's slot is not on
# the base point: it runs UNDER the bow bundle, offset towards the dome
# centre, which is where base_hub_v1 puts it and why the hub has an empty
# sector at all. 36 mm on a three-arm hub with a 10 mm rod, measured off the
# built part -- a drawing figure for a proxy, since the angle itself is still
# hardware nobody has specified. The placement's local +Y is outward, so the
# offset is negative along it and the mirrored feet get it on the right side.
STAKE_SLOT_INSET_M = 0.036
# How far the angle stands up into the hub's slot when it is a post rather
# than a stake -- the base point is then the top of the member, not a point
# part way along it. Drawing only.
STAKE_SLOT_ENGAGEMENT_M = 0.060

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
    p.add_argument(
        "--spans",
        default=None,
        metavar="FILE",
        help="span.json from 'stardome span --json': draws the points that "
             "hold each bow and the longest runs between them",
    )
    p.add_argument("--no-human", action="store_true", help="omit the scale figure")
    p.add_argument(
        "--cover",
        action="store_true",
        help="draw the fabric cover; needs a model built with --polylines",
    )
    p.add_argument("--no-ground", action="store_true", help="omit the ground plane")
    p.add_argument(
        "--attachment",
        action="store_true",
        help=(
            "draw what holds the cover on: the hem rope, its ten loops, and "
            "the straps over the crown. Derived, see stardome/attachment.py"
        ),
    )
    p.add_argument(
        "--no-seams",
        action="store_true",
        help="omit the gore seams from the cover",
    )
    p.add_argument(
        "--connectors",
        choices=("none", "real", "proxy"),
        default="none",
        help=(
            "put the connectors on the dome. 'real' imports the STL each "
            "generator wrote into exports/connectors and stands it on its "
            "rods; 'proxy' blocks in the ones nothing builds yet. Needs a "
            "model built with --weave-mode woven."
        ),
    )
    p.add_argument(
        "--schedule",
        default=None,
        help="connector schedule JSON; defaults to the one beside --model",
    )
    p.add_argument(
        "--connector-dir",
        default=None,
        help="where the built connector STLs are; defaults to exports/connectors",
    )
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


def add_skirt(skirt, radius_m, rod_radius_m, material, collection, lift,
              brace_material=None, place=None, draw_posts=True):
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
    if not draw_posts:
        # The post and the stake are one member -- the same steel angle, the
        # ground a skirt-height further down (decision 0017). When the
        # connectors are being placed, the stake proxy IS the post and drawing
        # this as well would put two members in one place.
        for obj in made:
            bpy.data.objects.remove(obj, do_unlink=True)
        made = []

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


def add_cover(cover, collection, lift):
    """The fabric, as the model exported it.

    Translucent, because an opaque cover hides the entire structure and the
    whole reason for the scene is to look at the structure through it.
    """
    data = cover.get("mesh")
    if not data:
        return None
    verts = [(x * MM, y * MM, z * MM + lift) for x, y, z in data["vertices"]]
    mesh = bpy.data.meshes.new("Cover")
    mesh.from_pydata(verts, [], [f[:] for f in data["faces"]])
    mesh.update()
    obj = bpy.data.objects.new("Cover", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mat = make_transparent(make_material("Cover", COVER_COLOUR), 0.28)
    obj.data.materials.append(mat)
    return move_to(obj, collection)


def surface_frame(point):
    """Outward radial and a tangent basis at a point on the cover.

    The cover is a sphere about the origin, so the outward normal is the point
    itself. Everything laid ON the fabric -- a seam, a strap -- needs that, or
    it comes out as a tube floating near the surface rather than something
    lying on it.
    """
    out = Vector(point)
    out.normalize()
    up = Vector((0.0, 0.0, 1.0))
    side = out.cross(up)
    if side.length < 1e-6:
        side = out.cross(Vector((1.0, 0.0, 0.0)))
    side.normalize()
    return out, side


def add_ribbon(points, width_m, lift_m, material, collection, name, lift=0.0):
    """A flat strap lying on the cover: a quad strip, not a tube.

    Webbing is flat and it lies down. Drawn as a bevelled curve it comes out
    round, which reads as rope and hides the one thing a strap picture is for
    -- that it bears on the fabric over its whole width.
    """
    verts, faces = [], []
    for i, p in enumerate(points):
        out, _ = surface_frame(p)
        along = Vector(points[min(i + 1, len(points) - 1)]) - Vector(
            points[max(i - 1, 0)]
        )
        if along.length < 1e-9:
            continue
        along.normalize()
        across = out.cross(along)
        across.normalize()
        seat = Vector(p) + out * lift_m
        verts.append(tuple(seat - across * (width_m / 2.0)))
        verts.append(tuple(seat + across * (width_m / 2.0)))
    for i in range(len(verts) // 2 - 1):
        a = 2 * i
        faces.append((a, a + 1, a + 3, a + 2))
    if not faces:
        return None
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(v[0], v[1], v[2] + lift) for v in verts], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    return move_to(obj, collection)


def add_seams(cover, collection, lift):
    """The gore seams, drawn where the cover is actually sewn.

    The cover is not a surface, it is `n` tapered strips joined along
    meridians, and the seams are the one feature of it a build ever has to
    line up. Drawn proud of the fabric so they read against it, and at the
    fabric's own radius so they are on the cloth rather than near it.
    """
    gores = cover.get("gores") or {}
    count = gores.get("count")
    radius = cover.get("radius_mm")
    if not count or not radius:
        return 0

    r = radius * MM
    # Opaque, unlike the cloth: a seam seen through a translucent cover on the
    # far side is not a seam anybody can count.
    mat = make_material("Cover_Seam", SEAM_COLOUR)
    # A seam runs pole to base along a meridian. The phase is not set by
    # anything yet -- see docs/cover.md -- so the first seam is put on the
    # doorway's centre, which is the one azimuth on the dome anybody can find.
    phase = cover.get("seam_phase_deg", 0.0)
    made = 0
    for k in range(count):
        azimuth = math.radians(phase + 360.0 * k / count)
        points = []
        for j in range(41):
            theta = (math.pi / 2.0) * j / 40.0
            points.append((
                math.cos(azimuth) * r * math.sin(theta),
                math.sin(azimuth) * r * math.sin(theta),
                r * math.cos(theta),
            ))
        # 30 mm is a flat-felled seam at this scale, and the seam is the one
        # feature of the cover a build has to line up -- so it is drawn proud
        # enough to read against the cloth rather than scaled to disappear.
        add_ribbon(points, 0.030, 0.008, mat, collection, f"Seam_{k:02d}", lift)
        made += 1
    return made


def add_attachment(data, collection, lift):
    """What holds the cover on: hem rope, loops, and the straps over the crown.

    All of it comes from `stardome.attachment`, which derives it -- five
    straps because the strap family has five bows and each runs foot to foot,
    ten loops because there are ten feet, and a rope broken where the doorway
    is. Nothing here chooses any of it.
    """
    spec = data.get("attachment")
    if not spec:
        return {}

    cover_r = data["cover"]["radius_mm"] * MM
    strap_mat = make_material("Strap", STRAP_COLOUR)
    rope_mat = make_material("HemRope", ROPE_COLOUR)
    loop_mat = make_material("HemLoop", LOOP_COLOUR)

    made = {"straps": 0, "loops": 0, "rope": 0}

    family = spec["straps"]["family"]
    for rod in data["rods"]:
        if rod["family"] != family:
            continue
        scale = cover_r / (data["meta"]["dome_radius"] * MM)
        points = [tuple(c * MM * scale for c in p) for p in rod["points"]]
        add_ribbon(points, 0.050, 0.006, strap_mat, collection,
                   f"Strap_{rod['name']}", lift)
        made["straps"] += 1

    # The rope, broken where the doorway takes it out.
    door = (data.get("doorway") or {}).get("bay") or {}
    half = door.get("span_deg", 0.0) / 2.0
    centre = door.get("centre_azimuth_deg", 0.0)
    run = []
    for i in range(721):
        azimuth = 360.0 * i / 720.0
        gap = abs((azimuth - centre + 180.0) % 360.0 - 180.0)
        if half and gap <= half:
            if len(run) > 1:
                add_ribbon(run, 0.016, 0.004, rope_mat, collection,
                           f"HemRope_{made['rope']}", lift)
                made["rope"] += 1
            run = []
            continue
        t = math.radians(azimuth)
        run.append((math.cos(t) * cover_r, math.sin(t) * cover_r, 0.010))
    if len(run) > 1:
        add_ribbon(run, 0.016, 0.004, rope_mat, collection,
                   f"HemRope_{made['rope']}", lift)
        made["rope"] += 1

    for base in data["base_nodes"]:
        azimuth = math.atan2(base["y"], base["x"])
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.055, minor_radius=0.010,
            location=(math.cos(azimuth) * cover_r,
                      math.sin(azimuth) * cover_r, 0.055 + lift),
            rotation=(math.pi / 2.0, 0.0, azimuth),
        )
        obj = bpy.context.active_object
        obj.name = f"HemLoop_{base['name']}"
        obj.data.materials.append(loop_mat)
        move_to(obj, collection)
        made["loops"] += 1
    return made


def add_corridor(corridor, rod_radius_m, collection, lift):
    """Hoops as tubes and the skin over them, both straight from the model."""
    drawing = corridor.get("drawing")
    if not drawing:
        return None

    # A corridor the model says will not pass its own doorway still gets
    # drawn -- seeing why it fails is the point -- but in the colour this
    # scene already uses for "this is not really there".
    fits = corridor.get("through_doorway", {}).get("fits", True)
    colour = CORRIDOR_COLOUR if fits else GHOST_COLOUR
    hoop_mat = make_material("Corridor_Hoop" if fits else "Corridor_TooBig", colour)
    for i, hoop in enumerate(drawing["hoops"], start=1):
        curve = bpy.data.curves.new(f"Corridor_Hoop_{i}", "CURVE")
        curve.dimensions = "3D"
        spline = curve.splines.new("POLY")
        spline.points.add(len(hoop) - 1)
        for point, (x, y, z) in zip(spline.points, hoop):
            point.co = (x * MM, y * MM, z * MM + lift, 1.0)
        curve.bevel_depth = rod_radius_m
        curve.bevel_resolution = 3
        obj = bpy.data.objects.new(f"Corridor_Hoop_{i}", curve)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(hoop_mat)
        move_to(obj, collection)

    skin = drawing["skin"]
    verts = [(x * MM, y * MM, z * MM + lift) for x, y, z in skin["vertices"]]
    mesh = bpy.data.meshes.new("Corridor_Skin")
    mesh.from_pydata(verts, [], [f[:] for f in skin["faces"]])
    mesh.update()
    obj = bpy.data.objects.new("Corridor_Skin", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(
        make_transparent(
            make_material("Corridor_Skin", COVER_COLOUR if fits else colour), 0.30
        )
    )
    return move_to(obj, collection)


def add_doorway(door, rod_radius_m, collection, lift, suffix=""):
    """Draw one opening: its outline, its frame, and the hole itself.

    The outline comes straight from the model as rod centrelines, so nothing
    here decides where the door is -- see stardome/doorway.py. The filled
    panel is what makes it read at a glance: a doorway drawn as a line among
    fifteen other lines is invisible, and the whole point of standing this up
    in Blender is to see whether a person walks through it.
    """
    points = [(x * MM, y * MM, z * MM + lift) for x, y, z in door["outline"]["points"]]

    curve = bpy.data.curves.new(f"DoorwayOutline{suffix}", "CURVE")
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
    obj = bpy.data.objects.new(f"Doorway_Outline{suffix}", curve)
    obj.data.materials.append(outline_mat)
    collection.objects.link(obj)

    # The opening as a surface, fanned from its centroid because the arch is
    # curved and a single n-gon across it would not be planar.
    centre = (
        sum(p[0] for p in points) / len(points),
        sum(p[1] for p in points) / len(points),
        sum(p[2] for p in points) / len(points),
    )
    mesh = bpy.data.meshes.new(f"DoorwayPanel{suffix}")
    verts = [centre] + points
    faces = [
        (0, i + 1, (i + 1) % len(points) + 1) for i in range(len(points))
    ]
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    panel_mat = make_transparent(
        make_material("Doorway_Panel", DOOR_COLOUR), 0.16
    )

    panel = bpy.data.objects.new(f"Doorway_Panel{suffix}", mesh)
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


def load_schedule(args):
    """The connector schedule that goes with this model, or a clear refusal."""
    path = args.schedule
    if path is None:
        stem = os.path.splitext(args.model)[0]
        path = f"{stem}_connectors.json"
    if not os.path.exists(path):
        raise SystemExit(
            f"no connector schedule at {path}\n"
            "write one with:  python3 -m stardome connectors <variant> --json"
        )
    with open(path) as fh:
        sched = json.load(fh)
    if not sched.get("placements"):
        raise SystemExit(
            "the schedule has no placements.\n"
            + (sched.get("placements_note") or "")
        )
    return sched


def add_connectors(args, sched, root, lift, rod_radius_m):
    """Stand every connector the schedule places on the rods it holds.

    Each printed piece is imported once and instanced after that, sharing one
    mesh between all its copies -- 107 connectors on M come to several hundred
    pieces, and importing each one would make a file nobody can open.

    What has no generator is blocked in instead, in the warning colour. That
    is the honest picture: the dome is 47 parts short, and leaving them out
    would show a structure that cannot be built yet as though it could.
    """
    parts = {p["id"]: p for p in sched["parts"]}
    directory = args.connector_dir or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(args.model))), "connectors"
    )

    collections = {}
    meshes = {}
    materials = {}
    counts = {"real": 0, "proxy": 0, "pieces": 0}
    missing = []

    staging = new_collection("_ConnectorSource", root)
    for spot in sched["placements"]:
        part = parts[spot["part"]]
        kind = spot["kind"]
        coll = collections.get(kind)
        if coll is None:
            coll = collections[kind] = new_collection(
                "Connectors_" + kind.replace("_", " ").title().replace(" ", ""),
                root,
            )

        key = spot["part"]
        if key not in meshes:
            pieces = part_pieces(key, directory) if args.connectors == "real" else []
            loaded = []
            for path in pieces:
                obj = import_stl(path)
                if obj is None:
                    continue
                mesh = obj.data
                mesh.name = os.path.basename(path)[:-4]
                mat = materials.get(key)
                if mat is None:
                    mat = materials[key] = make_material(
                        f"Part_{key}", PART_COLOUR.get(kind, UNTIED_COLOUR)
                    )
                mesh.materials.clear()
                mesh.materials.append(mat)
                move_to(obj, staging)
                obj.hide_render = obj.hide_viewport = True
                loaded.append(mesh)
            meshes[key] = loaded
            if not loaded:
                missing.append(key)

        pieces = meshes[key]
        if pieces:
            for index, mesh in enumerate(pieces):
                use = mesh
                if spot.get("hand") == "mirrored":
                    name = f"{mesh.name}_mirrored"
                    use = bpy.data.meshes.get(name) or mirror_mesh(mesh, name)
                place_instance(
                    f"{key}_{spot['at']}_{index}", use,
                    spot["origin_mm"], spot["basis"], coll, lift,
                )
                counts["pieces"] += 1
            counts["real"] += 1
        elif args.connectors in ("real", "proxy"):
            proxy_block(spot, part, coll, lift, rod_radius_m * 2.0, materials)
            counts["proxy"] += 1
            counts["pieces"] += 1

    if missing:
        print(
            "[connectors] blocked in as proxies, nothing builds them yet: "
            + ", ".join(sorted(missing))
        )
    print(
        f"[connectors] {counts['real']} placed from STL, {counts['proxy']} as "
        f"proxies, {counts['pieces']} pieces in the scene"
    )
    return counts


def proxy_size(spot, part, rod_d):
    """How big the thing that goes here would be, and where its middle sits.

    Sized off what the part has to do, not off a guess. A splice is a sleeve
    of a known length round a rod. A termination is a clamp with one channel
    closed, so it is a clamp. A stake is a 30 mm steel angle half a metre
    long, driven, so it hangs below the foot rather than straddling it.

    Returns the box in metres and how far to shift it along local +Y and +Z,
    which is what stands the stake in the hub's slot rather than on the base
    point, and part of the way out of the ground rather than all the way in.
    """
    kind = spot["kind"]
    if kind == "rod_splice":
        length = part.get("sleeve_length", rod_d * 10.0) * MM
        return (length, rod_d * 2.2 * MM, rod_d * 2.2 * MM), 0.0, 0.0
    if kind == "cut_termination":
        return (rod_d * 5.0 * MM, rod_d * 4.5 * MM, rod_d * 3.0 * MM), 0.0, 0.0
    if kind == "ground_stake":
        # Local +Z points down the way it is driven, so a positive shift sinks
        # it. Standing it proud takes a negative one. Local +Y is outward, and
        # the slot is inboard of the foot.
        #
        # Under a skirt this member is the POST as well -- the same angle, the
        # ground a skirt-height further down -- so how much of it stands above
        # the soil comes from the schedule rather than from the constant. See
        # docs/decisions/0017.
        standing = part.get("standing_mm")
        if standing:
            # The origin is the base point, which under a skirt is the TOP of
            # the post: the member runs down from here to the ground and on
            # into it, and only enough sticks up to sit in the hub's slot.
            above = STAKE_SLOT_ENGAGEMENT_M
            below = standing * MM + STAKE_LENGTH_M * (1.0 - STAKE_ABOVE_GROUND)
            length = above + below
        else:
            above = STAKE_LENGTH_M * STAKE_ABOVE_GROUND
            length = STAKE_LENGTH_M
            below = length - above
        return (
            (STAKE_LEG_M, STAKE_LEG_M, length),
            -(above - below) / 2.0,
            -STAKE_SLOT_INSET_M,
        )
    members = max(1, part.get("members", 2))
    return (
        (rod_d * 12.0 * MM, rod_d * 3.0 * MM, rod_d * members * MM),
        0.0,
        0.0,
    )


def proxy_block(spot, part, collection, lift, rod_d, materials):
    """A block the size of the joint, where no generator exists yet.

    It says "something goes here and it is this big", which is all an
    undesigned part has earned. Drawing nothing instead would show a dome that
    can be built out of what exists, and 57 of M's 107 connectors do not.
    """
    (length, width, height), shift, sideways = proxy_size(spot, part, rod_d)

    mat = materials.get("__undesigned__")
    if mat is None:
        mat = materials["__undesigned__"] = make_material(
            "Part_Undesigned", UNDESIGNED_COLOUR
        )

    mesh = bpy.data.meshes.get("Proxy_Cube")
    if mesh is None:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        seed = bpy.context.active_object
        mesh = seed.data
        mesh.name = "Proxy_Cube"
        mesh.materials.append(mat)
        bpy.data.objects.remove(seed, do_unlink=True)

    obj = bpy.data.objects.new(f"{spot['part']}_{spot['at']}", mesh)
    collection.objects.link(obj)

    ex, ey, ez = (Vector(row) for row in spot["basis"])
    origin = spot["origin_mm"]
    centre = (
        origin[0] * MM + ez.x * shift + ey.x * sideways,
        origin[1] * MM + ez.y * shift + ey.y * sideways,
        origin[2] * MM + lift + ez.z * shift + ey.z * sideways,
    )
    obj.matrix_world = Matrix((
        (ex.x, ey.x, ez.x, centre[0]),
        (ex.y, ey.y, ez.y, centre[1]),
        (ex.z, ey.z, ez.z, centre[2]),
        (0.0, 0.0, 0.0, 1.0),
    )) @ Matrix.Diagonal((length, width, height, 1.0))
    return obj


def add_camera_and_light(scene, radius_m, height_m, facing_deg=None,
                         framing_m=None):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 35.0
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    framing_m = radius_m if framing_m is None else framing_m
    if facing_deg is None:
        cam.location = (framing_m * 2.1, -framing_m * 2.3, height_m * 1.15)
    else:
        # Stand off along the door's own azimuth, so the opening is not hidden
        # behind the far side of the dome.
        a = math.radians(facing_deg)
        distance = framing_m * 3.1
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


def joint_cameras(scene, data, lift, rod_radius_m, placements=None):
    """Close on one joint of each kind, which is the only way to check one.

    A whole-dome view shows that connectors are there. It cannot show whether
    they are ON the rods -- at 6 m across, being a rod diameter out looks
    identical to being right. These stand about twenty rod diameters off one
    joint, which is close enough to see a channel miss.
    """
    made = {}
    rod_d = rod_radius_m * 2.0

    wanted = []
    lashed = [n for n in data["nodes"] if n["rod_count"] == 4]
    if lashed:
        wanted.append(("node", max(lashed, key=lambda n: n["z"])))
    crossings = [n for n in data["nodes"] if n["rod_count"] == 2]
    if crossings:
        wanted.append(("crossing", max(crossings, key=lambda n: n["z"])))

    door = data.get("doorway")
    cut = (door or {}).get("cut") or {}
    ends = set()
    for rod, spans in (cut.get("spans") or {}).items():
        ends.add(rod)
    feet = data["base_nodes"]
    if door and ends:
        # The doorway foot: the one the cut took a bow from, which is the one
        # worth looking at because it is a different part from the other eight.
        jamb = min(
            feet,
            key=lambda b: abs(
                math.degrees(math.atan2(b["y"], b["x"]))
                - door["bay"]["centre_azimuth_deg"]
            ) % 360.0,
        )
    else:
        jamb = feet[0]
    wanted.append(("foot", jamb))

    # One close-up per KIND of part actually placed, so a joint that gets a
    # generator gets a camera without anyone remembering to add one. The three
    # above are the named views this project already had; everything else is
    # aimed at the first placement of its kind.
    already = {"four_rod_fan", "two_rod_clamp", "base_hub"}
    seen = set()
    for spot in placements or ():
        kind = spot["kind"]
        if kind in already or kind in seen:
            continue
        seen.add(kind)
        x, y, z = spot["origin_mm"]
        wanted.append((kind, {"x": x, "y": y, "z": z}))

    for name, node in wanted:
        at = (node["x"] * MM, node["y"] * MM, node["z"] * MM + lift)
        # Stand off along the outward radius, so the camera is outside the
        # shell looking in rather than buried in it. A foot is on the ground
        # with a figure standing next to it, so it needs more room and a
        # flatter angle than a node up in the air does.
        reach = rod_d * (34.0 if name == "foot" else 20.0)
        out = Vector((at[0], at[1], 0.0))
        out = out.normalized() if out.length > 1e-9 else Vector((1.0, 0.0, 0.0))
        # Off to one side as well: straight down the radius at a foot is
        # straight at whoever is standing in the doorway.
        side = Vector((-out.y, out.x, 0.0)) * (reach * 0.55)
        cam_data = bpy.data.cameras.new(f"Cam_{name}")
        cam_data.lens = 50.0
        cam = bpy.data.objects.new(f"Cam_{name}", cam_data)
        scene.collection.objects.link(cam)
        cam.location = (
            at[0] + out.x * reach + side.x,
            at[1] + out.y * reach + side.y,
            at[2] + reach * (0.5 if name == "foot" else 0.35),
        )
        _aim(cam, at)
        made[name] = cam
    return made


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



# --- the span overlay -------------------------------------------------------


def point_at_t(rod, t_deg):
    """A point on a bow, by the bow parameter, from the bow's own polyline.

    The model samples t evenly from 0 to 180, so the index gives t back. A
    value between two samples is interpolated along the chord the model
    supplied rather than recomputed from the sphere: this script owns no
    geometry, and at 48 segments the chord is under two millimetres off the
    arc it stands in for. See docs/architecture.md.
    """
    points = rod["points"]
    last = len(points) - 1
    x = max(0.0, min(1.0, t_deg / 180.0)) * last
    i = int(math.floor(x))
    if i >= last:
        return tuple(points[last])
    a, b = points[i], points[i + 1]
    f = x - i
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))


def span_polyline(rod, t_lo, t_hi):
    """The rod's own samples between two t values, with both ends pinned on."""
    points = rod["points"]
    last = len(points) - 1
    out = [point_at_t(rod, t_lo)]
    for i, point in enumerate(points):
        t = 180.0 * i / last
        if t_lo + 1e-9 < t < t_hi - 1e-9:
            out.append(tuple(point))
    out.append(point_at_t(rod, t_hi))
    return out


def add_spans(data, analysis, rod_radius_m, root, lift):
    """Draw what `stardome span` measured, over the top of the bows.

    Three things go in the frame and nothing else: the points that hold each
    bow, the longest unsupported runs between them, and -- as a marker a shade
    smaller -- the crossings that would hold it if the thirty unlashed
    contacts were clamped. The difference between those two is the whole
    finding.
    """
    spans = analysis["spans"]
    worst = spans["worst"]["arc_deg"]
    by_name = {rod["name"]: rod for rod in data["rods"]}

    worst_coll = new_collection("Span_Worst", root)
    held_coll = new_collection("Span_Held", root)
    worst_mat = make_material("Span_Worst", SPAN_WORST_COLOUR)
    held_mat = make_material("Span_Held", SPAN_HELD_COLOUR)

    drawn = 0
    held_at = {}
    for name, items in spans["per_rod"].items():
        rod = by_name.get(name)
        if rod is None or "points" not in rod:
            continue
        held_at.setdefault(name, set())
        for item in items:
            held_at[name].add(item["t_lo_deg"])
            held_at[name].add(item["t_hi_deg"])
            if abs(item["arc_deg"] - worst) > 1e-6:
                continue
            rod_object(
                rod,
                rod_radius_m,
                worst_mat,
                worst_coll,
                lift,
                span_polyline(rod, item["t_lo_deg"], item["t_hi_deg"]),
                f"_span{drawn}",
                bevel=rod_radius_m * 2.2,
            )
            drawn += 1

    held = 0
    for name, ts in held_at.items():
        rod = by_name.get(name)
        if rod is None or "points" not in rod:
            continue
        for t in sorted(ts):
            marker(
                f"Held_{name}_{t:.0f}",
                point_at_t(rod, t),
                rod_radius_m * 4.5,
                held_mat,
                held_coll,
                lift,
            )
            held += 1

    print(
        f"[star-dome] spans: {drawn} runs of {worst:.4f} deg "
        f"({spans['worst']['length_mm']:.0f} mm) on family "
        f"{spans['worst']['family']}, {held} holding points, "
        f"held at {analysis['holds']}"
    )
    return {"worst_runs": drawn, "held_points": held}


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
    if meta["weave_mode"] == "flat":
        print(
            "[warning] weave_mode is 'flat'; every crossing has two rods in "
            "the same place. Use --weave-mode layered to look at the weave, "
            "or woven to put connectors on it."
        )
    if args.connectors != "none" and meta["weave_mode"] != "woven":
        raise SystemExit(
            f"--connectors needs a woven model; this one is "
            f"{meta['weave_mode']!r}.\n"
            "'layered' is a drawing convention: it puts each bow on its own "
            "shell, up to 14 rod diameters apart at a crossing, and a "
            "connector stack is one. Rebuild with:\n"
            f"  python3 -m stardome build {meta['variant']} --polylines "
            "--weave-mode woven"
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

    if args.spans:
        quiet = make_material("Rod_Quiet", SPAN_QUIET_COLOUR)
        materials = {f: quiet for f in FAMILY_COLOUR}
    else:
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
        if args.connectors != "none":
            # The marker is a stand-in for the connector. With the connector
            # itself in the scene it is a ball inside a part.
            continue
        marker(
            f"Node_{node['name']}",
            (node["x"], node["y"], node["z"]),
            node_radius,
            tied_mat if tied else untied_mat,
            tied_coll if tied else untied_coll,
            lift,
        )

    schedule = None
    if args.connectors != "none":
        schedule = load_schedule(args)
        add_connectors(args, schedule, root, lift, rod_radius_m)

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
        if args.connectors != "none":
            continue  # the base hub itself is in the scene
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
            draw_posts=args.connectors == "none",
        )

    facing = None
    # Every door the dome has, not only the one the corridor hangs off. The
    # camera still faces the first: it is the one the model calls "the
    # doorway" and the one a person is put in front of.
    every_door = data.get("doorways") or ([door] if door else [])
    if every_door and not args.no_doorway:
        door_coll = new_collection("Doorway", root)
        for index, one in enumerate(every_door):
            add_doorway(one, rod_radius_m, door_coll, lift, suffix=f"_{index}"
                        if len(every_door) > 1 else "")
        facing = door_azimuth_deg(every_door[0])

    if data.get("cover", {}).get("mesh") and args.cover:
        cover_coll = new_collection("Cover", root)
        add_cover(data["cover"], cover_coll, lift)
        if not args.no_seams:
            seams = add_seams(
                data["cover"], new_collection("Cover_Seams", root), lift
            )
            print(
                f"[cover] {seams} gore seams, first on the doorway at "
                f"{data['cover'].get('seam_phase_deg', 0.0):.1f} deg"
            )

    if args.attachment:
        made = add_attachment(data, new_collection("Attachment", root), lift)
        if made:
            print(
                f"[attachment] {made['straps']} straps over the crown, "
                f"{made['loops']} hem loops, rope in {made['rope']} run(s)"
            )

    if data.get("corridor", {}).get("present"):
        add_corridor(
            data["corridor"], rod_radius_m, new_collection("Corridor", root), lift
        )

    if args.spans:
        with open(args.spans) as fh:
            analysis = json.load(fh)
        if analysis["variant"] != meta["variant"]:
            raise SystemExit(
                f"--spans is {analysis['variant']}'s analysis and --model is "
                f"{meta['variant']}'s; they have to be the same dome"
            )
        add_spans(data, analysis, rod_radius_m, root, lift)

    if not args.no_ground:
        add_ground(radius_m * 2.0, site_coll)
    if not args.no_human:
        add_humans(radius_m, site_coll, facing)

    # A corridor comes straight out of the doorway, which is straight at the
    # camera. Framing on the dome alone crops it off the bottom of the frame,
    # so the stand-off grows by what is hanging off the front.
    framing_m = radius_m
    corridor = data.get("corridor") or {}
    if corridor.get("present") and corridor.get("drawing"):
        framing_m += corridor["length_mm"] * MM

    default_cam, _ = add_camera_and_light(scene, radius_m, height_m, facing,
                                          framing_m)
    shots = shot_cameras(scene, radius_m, height_m, facing)
    shots.update(
        joint_cameras(
            scene, data, lift, rod_radius_m,
            (schedule or {}).get("placements") if args.connectors != "none" else None,
        )
    )
    data["_shot_cameras"] = shots
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
