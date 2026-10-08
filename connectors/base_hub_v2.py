# -*- coding: utf-8 -*-
"""
Star Dome base-point hub, 2.0 -- one print, a fan of tubes on ribs, a sleeve
for the rebar.

WHAT 1.x TAUGHT (docs/base-hub.md)

1.x was the lashed node's plate stack with an arm removed: four plates, each
the full outline of the hub, one rod level between each pair, plus a cradle
for the stake. Printed and held in the hand, end on, it is a block with three
holes in it. Every level is solid across the footprint of every arm, though
each level holds one rod. Five prints a hub, fifty a dome, and four M5 bolts
to hold the stack together before a single bow goes in.

WHAT STAYS

**The levels.** The three bows meet at one point in one plane
(stardome/weave.py, ``base_fan``), so the ends could share a level. They do
not: a bow must be able to run on through the foot, so each keeps its own
level and its channel runs out of both sides. Same order, same fan gaps, same
frame as 1.x: fan in XY, stack along Z, -Y straight down once installed.

**The channel.** The printed 1.x BASE3-8 channel is Ø9.4, and a 10 mm
composite rebar goes in it. That is the fit 2.0 is drawn for:
``channelDiameter`` is that number, not one derived from the rod.

WHAT CHANGES

**There is no stack.** Each rod gets a tube, and each tube stands on a rib
down to the bed. The rib widens into the tube at 50 deg, so the underside of
every tube prints as a wall and not as an overhang:

        ( 3 )            tube
         \\ /             50 deg, self-supporting
          |   ( 2 )      rib
          |    \\ /
    ( 1 ) |     |
    ======================  bed

The channels print as horizontal holes with a pointed roof, which is a hole
an FDM printer closes without a bridge. One piece, no supports, no stack
bolts.

**Threading instead of laying in.** A closed tube has to be threaded. At a
base point that is nothing: the bow end goes in about ten centimetres.

**The channel is open behind the centre.** It runs ``channelExit`` past the
crossing and out through the core. Behind the centre the arms point into the ground, so a bow
cannot really pass through the foot; what the exit buys is a rod that may be
cut long, no blind pocket for water and grit, and a way to knock a jammed end
back out.

**The stake is a sleeve, not a cradle.** A vertical tunnel along -Y on the
bed side of the fan, under all three levels. Its roof is an 80 deg vee, apex
towards the fan, and two M8 bolts come up through its floor and push the bar
into the vee. A round bar touches both flanks of a vee at any diameter, so
one sleeve takes every bar from ``stakeRebarMin`` to ``stakeRebarMax``. The
vee roof is also what lets the tunnel print without supports.

FIELD SEQUENCE

    drive the rebar -> drop the hub down over it -> do up the two bolts ->
    push each bow end into its tube -> pin it

Nothing is assembled at home, and nothing loose has to be held while a bolt
is started. The bar stands proud above the foot through the top of the
sleeve, past the fan, for the cover's loops to drop over (decision 0014).

THE NUTS

The two M8 nuts sit in hex pockets in the tunnel floor, opening INTO the
tunnel. The bolt pushes the bar up and the nut down, so the nut bears on the
floor instead of being pushed out of its pocket. Drop both in before the hub
goes on the bar.

Helpers come from connectors/kit.py, shared with the other live generators.
connectors/base_hub_v1.py is 1.1 and is frozen.

Run:  exec(open('.../connectors/base_hub_v2.py').read()) inside FreeCAD, or
through connectors/generate_clamps.py, which drives it from the model data.
"""

import math
import os
import sys

import FreeCAD as App
import Part

try:
    REPO
except NameError:
    try:
        REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        REPO = os.path.expanduser("~/star-dome")

if os.path.join(REPO, "connectors") not in sys.path:
    sys.path.insert(0, os.path.join(REPO, "connectors"))
import kit  # noqa: E402  -- needs the path set above

DOC_NAME = "StarDome_BaseHub_V2"
TITLE = "Star Dome base hub 2.0 - parameters"
USE_SPREADSHEET_IF_PRESENT = True
VERSION = "2.0"

DEFAULT_FAN_GAPS = [41.810315, 37.377368]

# Every face that is not a wall rises at this angle from horizontal: channel
# and pin roofs, the flare under each tube. 45 is the printer's limit, and a
# face drawn at exactly 45 lands either side of it on rounding -- it did, and
# the same part read clean at one rod size and not at the next. 50 is not.
SLOPE_DEG = 50.0

# It prints on the face that is flat: the floor of the stake sleeve.
FLIPPED_PIECES = set()

INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal bow rod; sizes the wall and the cross pin"),
    ("rodNominalDiameter",     0.0,  "mm",  "the rod as a structural member when that is not rodDiameter. 0 means the same"),
    ("channelDiameter",        9.4,  "mm",  "the bore each bow end goes into. 9.4 is the printed 1.x BASE3-8 channel, which takes a 10 mm composite rebar. 0 takes rodDiameter + rodClearance"),
    ("rodClearance",           1.4,  "mm",  "diametral clearance, used only when channelDiameter is 0"),
    ("rodPitch",               0.0,  "mm",  "level to level. 0 takes the channel diameter, so the rods clear each other where they cross at the centre"),
    ("rodEngagement",         60.0,  "mm",  "how far a bow end is held in its tube, from the centre"),
    ("channelOverrun",         6.0,  "mm",  "how far each tube runs past the engagement"),
    ("channelExit",           18.0,  "mm",  "how far the channel runs on behind the centre and out"),
    ("tiltAllowance",          1.5,  "deg", "out-of-plane tilt a rod may arrive with; flares the tube mouth"),
    ("minimumWall",            0.0,  "mm",  "0 takes it from rodDiameter: 0.4 of the rod, never under 3 mm"),
    ("ribWidth",               1.6,  "mm",  "width of the rib under each tube: four lines of a 0.4 nozzle. It holds the tube up while it prints and stiffens the arm across the fan; at 1.5 walls it was a quarter of the hub's plastic. 0 takes 1.5 walls"),
    ("coreRadius",             0.0,  "mm",  "the solid round the crossing. 0 takes the tube's outside radius plus a wall"),
    ("rodPinDiameter",         0.0,  "mm",  "cross pin through tube and rod. 0 takes it from the rod"),
    ("rodPinAt",              40.0,  "mm",  "how far along the tube the pin sits"),
    ("firstArmRise",       37.3774,  "deg", "how far the first arm rises above horizontal once installed"),
    ("stakeRebarDiameter",    12.0,  "mm",  "the bar the reference solid draws. Drawing only"),
    ("stakeRebarMin",          8.0,  "mm",  "the thinnest bar the sleeve must still clamp: the bolt has to reach it"),
    ("stakeRebarMax",         18.0,  "mm",  "the thickest, across the ribs; 18 is a 16 mm rebar. The tunnel is sized for it"),
    ("stakeVeeAngle",         80.0,  "deg", "included angle of the sleeve's vee roof. A round bar touches both flanks of a vee at any diameter; 80 keeps each flank 50 deg off horizontal, safely printable"),
    ("stakeClearance",         1.0,  "mm",  "radial room round the thickest bar, so a bar not quite straight still goes in"),
    ("stakeSleeveLength",     80.0,  "mm",  "how much of the bar the sleeve holds"),
    ("stakeSleeveAbove",      20.0,  "mm",  "how far the sleeve reaches above the hub centre; the rest is below it"),
    ("stakeBoltDiameter",      8.5,  "mm",  "clearance hole for the two set bolts. 8.5 is M8"),
    ("stakeLength",          500.0,  "mm",  "how long the rebar is; drawing only"),
    ("stakeStandProud",      120.0,  "mm",  "how much of the bar is left above the foot. Drawing only, but verify checks the bar clears the part over all of it -- decision 0014"),
    ("refRodLength",         300.0,  "mm",  "how far the reference rods are drawn"),
]


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------
def along_x(profile_points, x0, x1):
    """Extrude a closed YZ-plane polygon along +X from x0 to x1."""
    pts = [App.Vector(x0, y, z) for (y, z) in profile_points]
    pts.append(pts[0])
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(App.Vector(x1 - x0, 0, 0))


def along_y(profile_points, y0, y1):
    """Extrude a closed XZ-plane polygon along +Y from y0 to y1."""
    pts = [App.Vector(x, y0, z) for (x, z) in profile_points]
    pts.append(pts[0])
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(App.Vector(0, y1 - y0, 0))


def place(shape, azimuth_deg, z):
    """Turn a shape built along +X onto its arm's azimuth and lift it."""
    shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    shape.translate(App.Vector(0, 0, z))
    return shape


def tube_on_rib(outer_r, rib_w, z, z_bed, x0, x1):
    """One arm's material, built along +X at height z: a tube and its rib.

    The rib runs straight down to the bed and widens into the tube at
    SLOPE_DEG. The flare starts where a line at that slope is tangent to the
    tube and comes in to the rib's width; below that the rib is straight.
    Everything under the tube is then wall or printable slope.
    """
    b = math.radians(SLOPE_DEG)
    tangent_x = outer_r * math.sin(b)
    tangent_z = z - outer_r * math.cos(b)
    half = rib_w / 2.0
    flare_end = tangent_z - (tangent_x - half) * math.tan(b)
    tube = Part.makeCylinder(outer_r, x1 - x0, App.Vector(x0, 0, z), App.Vector(1, 0, 0))
    if z - outer_r <= z_bed + 1e-6:
        # The lowest tube sits on the bed already; give it a flat foot.
        foot = along_x(
            [(-tangent_x, z_bed), (tangent_x, z_bed),
             (tangent_x, tangent_z), (-tangent_x, tangent_z)],
            x0, x1,
        )
        return tube.fuse(foot)
    rib = along_x(
        [(-half, z_bed), (half, z_bed), (half, flare_end),
         (tangent_x, tangent_z), (-tangent_x, tangent_z),
         (-half, flare_end)],
        x0, x1,
    )
    return tube.fuse(rib)


def teardrop_channel(radius, x0, x1, z, tilt_deg, steps=2):
    """The bore, built along +X: round, with a pointed roof at SLOPE_DEG.

    The roof is what lets a horizontal hole print without a bridge. The two
    mouths flare by `tilt_deg` out of the fan plane, as 1.x's did, so a rod
    that arrives a little out of plane does not bear on the lip.
    """
    b = math.radians(SLOPE_DEG)
    base = Part.makeCylinder(radius, x1 - x0, App.Vector(x0, 0, 0), App.Vector(1, 0, 0))
    roof = along_x(
        [(-radius * math.sin(b), radius * math.cos(b)),
         (radius * math.sin(b), radius * math.cos(b)),
         (0.0, radius / math.cos(b))],
        x0, x1,
    )
    solid = base.fuse(roof)
    # Turned about the crossing, so both mouths flare and the middle does not.
    for k in range(1, steps + 1):
        angle = tilt_deg * k / steps
        for sign in (1.0, -1.0):
            turned = base.copy()
            turned.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), sign * angle)
            solid = solid.fuse(turned)
    solid = solid.removeSplitter()
    solid.translate(App.Vector(0, 0, z))
    return solid


def stake_tunnel_profile(apex_z, half_vee_deg, r_max, clearance, floor_z):
    """The sleeve's cross-section in XZ: a vee roof, apex up, over straight
    sides wide enough for the thickest bar, down to the floor.

    A bar of radius r pushed up into a vee of half-angle a has its centre
    r / sin(a) under the apex, whatever r is.
    """
    half = r_max + clearance
    shoulder = apex_z - half / math.tan(math.radians(half_vee_deg))
    return [
        (0.0, apex_z), (half, shoulder), (half, floor_z),
        (-half, floor_z), (-half, shoulder),
    ]


def driven_rebar(radius, centre_z, y_from, y_to):
    return Part.makeCylinder(
        radius, y_to - y_from, App.Vector(0.0, y_from, centre_z), App.Vector(0, 1, 0),
    )


# --------------------------------------------------------------------------
# the part
# --------------------------------------------------------------------------
def build(values, fan_gaps=None):
    chosen = kit.scale_to_rod(values)
    gaps = list(fan_gaps or DEFAULT_FAN_GAPS)
    if not 1 <= len(gaps) <= 2:
        raise ValueError(f"a base fan has one gap or two, got {len(gaps)}: {gaps}")
    azimuths = kit.azimuths_from_gaps(gaps, values["firstArmRise"])
    arm_count = len(azimuths)

    rod_d = values["rodDiameter"]
    wall = values["minimumWall"]
    channel_d = values["channelDiameter"] or (rod_d + values["rodClearance"])
    channel_r = channel_d / 2.0
    pitch = values["rodPitch"] or channel_d
    outer_r = channel_r + wall
    rib_w = values["ribWidth"] or 1.5 * wall
    core_r = values["coreRadius"] or (outer_r + wall)
    front = values["rodEngagement"] + values["channelOverrun"]
    back = values["channelExit"]

    levels = [k * pitch for k in range(arm_count)]

    # --- the stake sleeve, under the lowest level ----------------------------
    # Roof apex one wall under the lowest channel; floor deep enough for the
    # thickest bar; then the nut and a wall under it. The floor of the sleeve
    # is the bed.
    r_min = values["stakeRebarMin"] / 2.0
    r_max = values["stakeRebarMax"] / 2.0
    half_vee = values["stakeVeeAngle"] / 2.0
    under_apex = 1.0 / math.sin(math.radians(half_vee))   # centre depth per unit radius
    apex_z = levels[0] - channel_r - wall
    lowest_bar_z = apex_z - r_max * under_apex - r_max   # bottom of the thickest bar
    tunnel_floor = lowest_bar_z - values["stakeClearance"]
    stake_size, stake_bolt = kit.fastener_for_clearance(values["stakeBoltDiameter"])
    z_bed = tunnel_floor - stake_bolt["nut_depth"] - wall
    z_top = levels[-1] + outer_r

    sleeve_half = r_max + values["stakeClearance"] + wall
    sleeve_hi = values["stakeSleeveAbove"]
    sleeve_lo = sleeve_hi - values["stakeSleeveLength"]

    # --- material -----------------------------------------------------------
    body = Part.makeCylinder(
        core_r, z_top - z_bed, App.Vector(0, 0, z_bed), App.Vector(0, 0, 1),
    )
    for k, az in enumerate(azimuths):
        # Tubes run forward only. Behind the centre the channel just leaves
        # through the core: a tube out there would stand on a rib the bar's
        # tunnel has to cut away, and come out as a ring hanging in the air.
        arm = tube_on_rib(outer_r, rib_w, levels[k], z_bed, -wall, front)
        body = body.fuse(place(arm, az, 0.0))
    # Its top stops half a wall over the vee's apex. A full wall would put it
    # exactly tangent to the lowest channel, and OCC does not survive a
    # cylinder cut that grazes a plane.
    sleeve = Part.makeBox(
        2.0 * sleeve_half, sleeve_hi - sleeve_lo, apex_z + 0.5 * wall - z_bed,
        App.Vector(-sleeve_half, sleeve_lo, z_bed),
    )
    # No removeSplitter here: merging the faces of this union makes the next
    # channel cut return an unorientable shell. It is done once, at the end.
    body = body.fuse(sleeve)

    # --- cuts ---------------------------------------------------------------
    channels = []
    for k, az in enumerate(azimuths):
        ch = teardrop_channel(
            channel_r, -back - 1.0, front + 1.0, levels[k], values["tiltAllowance"],
        )
        channels.append(place(ch, az, 0.0))
    for ch in channels:
        body = body.cut(ch)

    # The bar's tunnel runs the whole height of the part, not just the
    # sleeve: above the sleeve the bar goes on past the hub, and anything in
    # its way is cut to the same vee roof so it still prints.
    reach = front + core_r + values["stakeStandProud"]
    tunnel = along_y(
        stake_tunnel_profile(apex_z, half_vee, r_max, values["stakeClearance"], tunnel_floor),
        -reach, reach,
    )
    body = body.cut(tunnel)

    # Two set bolts up through the floor, each into a nut in a pocket that
    # opens into the tunnel.
    bolt_r = (values["stakeBoltDiameter"]) / 2.0
    bolt_ys = [sleeve_lo + values["stakeSleeveLength"] * f for f in (0.25, 0.75)]
    stake_cuts = []
    for y in bolt_ys:
        stake_cuts.append(Part.makeCylinder(
            bolt_r, tunnel_floor - z_bed + 2.0, App.Vector(0, y, z_bed - 1.0),
            App.Vector(0, 0, 1),
        ))
        stake_cuts.append(kit.hex_prism(
            stake_bolt["nut_af"], stake_bolt["nut_depth"] + 1.0,
            App.Vector(0, y, tunnel_floor - stake_bolt["nut_depth"]),
        ))
    for cut in stake_cuts:
        body = body.cut(cut)

    # Cross pins, one per tube, horizontal and across it -- teardrops too, so
    # a small pin hole prints the same way the channels do.
    pin_r = values["rodPinDiameter"] / 2.0
    pins = []
    for k, az in enumerate(azimuths):
        along = kit.direction(az).multiply(values["rodPinAt"])
        span = 2.0 * outer_r + 4.0
        pin = teardrop_channel(pin_r, -span / 2.0, span / 2.0, levels[k], 0.0, steps=0)
        pin.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), az + 90.0)
        pin.translate(App.Vector(along.x, along.y, 0.0))
        pins.append(pin)
    for pin in pins:
        body = body.cut(pin)

    body = body.common(Part.makeBox(
        1000, 1000, z_top - z_bed, App.Vector(-500, -500, z_bed),
    )).removeSplitter()
    if not kit.ok(body):
        raise RuntimeError("the hub came out as something other than one valid solid")

    # --- reference solids ---------------------------------------------------
    # Drawn at what goes into the channel, not at the rod's name: a 10 mm
    # composite rebar goes into the printed Ø9.4, so a Ø10 cylinder here would
    # report an interference the real rod does not have.
    ref_len = max(front, values["refRodLength"])
    ref_r = min(rod_d, channel_d - 0.4) / 2.0
    rods = [
        kit.rod_from_hub(ref_r, ref_len, azimuths[k], levels[k], back)
        for k in range(arm_count)
    ]
    bar_r = values["stakeRebarDiameter"] / 2.0
    proud = values["stakeStandProud"]
    stake = driven_rebar(
        bar_r, apex_z - bar_r * under_apex, -(values["stakeLength"] - proud), proud,
    )

    # Bolt length: from the bed face, through the floor and nut, up to the
    # thinnest bar's underside, which is the furthest it ever has to reach.
    reach_thin = (apex_z - r_min * under_apex - r_min) - z_bed
    reach_thick = lowest_bar_z - z_bed
    sleeve_bore = 2.0 * (r_max + values["stakeClearance"])

    geo = {
        "plates": [body],
        "names": ["Hub"],
        "rods": rods,
        "channels": channels,
        "stake": stake,
        "tunnel": tunnel,
        "keepouts": [
            place(Part.makeCylinder(
                channel_r + wall * 0.5, front, App.Vector(0, 0, 0), App.Vector(1, 0, 0),
            ), az, levels[k])
            for k, az in enumerate(azimuths)
        ],
    }
    dims = {
        "version": VERSION,
        "chosen_from_rod": chosen,
        "fan_gaps_deg": gaps,
        "arm_azimuths_deg": azimuths,
        "rod_levels_mm": levels,
        "pitch_mm": pitch,
        "channel_diameter_mm": channel_d,
        "tube_outer_diameter_mm": 2.0 * outer_r,
        "rib_width_mm": rib_w,
        "core_radius_mm": core_r,
        "arm_front_mm": front,
        "channel_exit_mm": back,
        "z_bed_mm": z_bed,
        "z_top_mm": z_top,
        "print_height_mm": z_top - z_bed,
        "stake_rebar_min_mm": values["stakeRebarMin"],
        "stake_rebar_max_mm": values["stakeRebarMax"],
        "stake_rebar_mm": values["stakeRebarDiameter"],
        "sleeve_length_mm": values["stakeSleeveLength"],
        "sleeve_width_mm": 2.0 * sleeve_half,
        "sleeve_bore_mm": sleeve_bore,
        "stake_bolt_size": stake_size,
        "stake_bolt_reach_thin_mm": reach_thin,
        "stake_bolt_reach_thick_mm": reach_thick,
        "stake_bolt_length_mm": 5 * math.ceil(reach_thin / 5.0),
        "stake_nut_depth_mm": stake_bolt["nut_depth"],
        "stake_offset_mm": levels[1 if arm_count > 2 else 0] - (apex_z - bar_r * under_apex),
        "stake_stand_proud_mm": proud,
        "pin_diameter_mm": values["rodPinDiameter"],
        "plate_count": 1,
    }
    return geo, dims


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
def verify(geo, dims, values):
    problems = []
    body = geo["plates"][0]
    if not kit.ok(body):
        problems.append("Hub: not one valid solid")

    interference = 0.0
    for i, rod in enumerate(geo["rods"]):
        v = kit.vol(body.common(rod))
        if v > 0.5:
            interference += v
            problems.append(f"the hub overlaps rod {i + 1} by {v:.1f} mm3")

    # Each tube must actually be a tube: material all round the channel over
    # the engagement, not a channel cut through air or through a rib only.
    for i, keep in enumerate(geo["keepouts"]):
        ring = keep.cut(geo["channels"][i])
        have = kit.vol(body.common(ring))
        want = kit.vol(ring)
        if want > 0 and have < 0.9 * want:
            problems.append(
                f"tube {i + 1} has only {100 * have / want:.0f}% of its wall"
            )

    # The bar passes the hub and must touch nothing, over all it stands proud.
    v = kit.vol(body.common(geo["stake"]))
    if v > 0.5:
        problems.append(f"the hub is in the bar's way by {v:.1f} mm3")

    printability = {"Hub": kit.printability(body, flipped=False)}
    return {
        "problems": problems,
        "ok": not problems,
        "printability": printability,
        "rod_interference_mm3": round(interference, 2),
        "plate_volumes_mm3": [round(kit.vol(body), 1)],
        "print_height_mm": round(dims["print_height_mm"], 2),
        "arm_azimuths_deg": [round(a, 4) for a in dims["arm_azimuths_deg"]],
    }


def derived_rows(dims, values):
    return [
        ("version", dims["version"], "-", "base hub version; see docs/base-hub.md"),
        ("channel", round(dims["channel_diameter_mm"], 2), "mm",
         "bore of each tube, pointed roof on top for printing"),
        ("pitch", round(dims["pitch_mm"], 2), "mm", "level to level"),
        ("tubeOutside", round(dims["tube_outer_diameter_mm"], 2), "mm", "each tube, across"),
        ("rib", round(dims["rib_width_mm"], 2), "mm", "the rib under each tube"),
        ("printHeight", round(dims["print_height_mm"], 1), "mm", "bed to top"),
        ("stakeRebar",
         f"{dims['stake_rebar_min_mm']:g} to {dims['stake_rebar_max_mm']:g}", "mm",
         "any driven rebar in this range; the sleeve takes all of it"),
        ("sleeve", f"{dims['sleeve_length_mm']:g} long, {dims['sleeve_bore_mm']:g} bore",
         "mm", "drop the hub over the driven bar"),
        ("stakeBolt",
         f"M{dims['stake_bolt_size']:g} x {dims['stake_bolt_length_mm']:g}, two of", "-",
         "up through the sleeve floor, into a nut in the tunnel, tip on the bar"),
        ("stakeOffset", round(dims["stake_offset_mm"], 1), "mm",
         "bar axis to the middle rod level"),
        ("pin", round(dims["pin_diameter_mm"], 1), "mm", "cross pin per tube"),
        ("plateCount", 1, "-", "one print per hub"),
    ]


# --------------------------------------------------------------------------
# document
# --------------------------------------------------------------------------
HUB_COLOUR = (0.76, 0.81, 0.89)
STAKE_COLOUR = (0.45, 0.45, 0.48)
FAMILY_COLOUR = {
    "G": (0.15, 0.55, 0.95),
    "U": (0.95, 0.45, 0.10),
    "L": (0.20, 0.75, 0.35),
}
ROD_FAMILIES = ["L", "U", "G"]


def populate(doc, geo):
    for obj in list(doc.Objects):
        if obj.TypeId == "Spreadsheet::Sheet":
            continue
        doc.removeObject(obj.Name)
    for name, solid in zip(geo["names"], geo["plates"]):
        obj = doc.addObject("Part::Feature", f"Plate_{name}")
        obj.Shape = solid
    for i, rod in enumerate(geo["rods"]):
        obj = doc.addObject("Part::Feature", f"Ref_Rod{i + 1}")
        obj.Shape = rod
    obj = doc.addObject("Part::Feature", "Ref_Stake")
    obj.Shape = geo["stake"]
    doc.recompute()


def apply_view(doc):
    if not getattr(App, "GuiUp", 0):
        return
    for obj in doc.Objects:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        if obj.Name.startswith("Plate_"):
            view.ShapeColor = HUB_COLOUR
        elif obj.Name == "Ref_Stake":
            view.ShapeColor = STAKE_COLOUR
        elif obj.Name.startswith("Ref_Rod"):
            idx = int(obj.Name[-1]) - 1
            view.ShapeColor = FAMILY_COLOUR[ROD_FAMILIES[idx % len(ROD_FAMILIES)]]


def run(fan_gaps=None, out_dir=None, doc_path=None):
    if DOC_NAME in App.listDocuments():
        doc = App.getDocument(DOC_NAME)
    else:
        doc = App.newDocument(DOC_NAME)
    sheet, values = kit.read_or_build_parameters(doc, INPUTS, USE_SPREADSHEET_IF_PRESENT)
    geo, dims = build(values, fan_gaps)
    report = verify(geo, dims, values)
    populate(doc, geo)
    apply_view(doc)
    kit.write_parameters(doc, sheet, INPUTS, values, derived_rows(dims, values), TITLE)
    doc.recompute()
    path = doc_path or (
        os.path.join(out_dir, "star_dome_base_hub_v2.FCStd") if out_dir else None
    )
    if path:
        doc.saveAs(path)
        report["saved_to"] = path
    return report


if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint

    pprint.pprint(REPORT, width=112)
