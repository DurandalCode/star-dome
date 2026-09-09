# -*- coding: utf-8 -*-
"""
Star Dome base-point hub, V1 -- the node's plate stack with one arm fewer.

WHY THIS IS NOT A NEW KIND OF PART

A great circle through a point on the sphere's equator has its tangent there in
the surface, and the surface at the equator is the vertical plane tangent to
the base ring. So the three bows leaving a base point are **coplanar** --
residual 5e-16 -- for exactly the same reason the four bows at a lashed node
are. See stardome/weave.py, ``base_fan``.

That makes this the four-rod fan with one arm removed:

    node fan   gaps 37.3774, 41.8103, 37.3774      four arms, spread 180
    base fan   gaps 41.8103, 37.3774               three arms, spread 79.1877

Both of the base fan's gaps are the node's. And each arm rises at exactly its
family's tilt -- 37.3774 for L, 63.4349 for G, 79.1877 for U -- because at the
equator the tangent's rise *is* the tilt.

WHAT IS DIFFERENT

Three things, and they all make the part smaller rather than larger.

**The rods end here.** At a node a bow passes through and the channel has to
run out both sides; here it runs one way only. Half the channel, half the arm.

**The fan plane stands vertical.** The part is built in its own frame with the
fan in XY and the stack along Z, the same as the node, but installed the plane
is the vertical tangent plane and the stack axis is horizontal and radial.
Nothing in the geometry cares; only the installer does.

**The empty sector points at the ground.** Three arms spanning 79 deg leave
281 deg of nothing, and once the part is stood up that sector faces down. The
driven steel angle that anchors this point goes there, in the fan plane,
through a slot in the hub -- so the anchorage and the part share one place
instead of competing for it.

WHAT THIS PART DOES AND DOES NOT DO

It gathers three bow ends and holds them to each other and to the stake. It
does **not** resist the dome spreading at its feet: that is the stake, through
the soil. See docs/skirt.md and stardome/connectors.py, where the stake is
listed as hardware to specify rather than a shape to design.

THE PARTS

    plate 0   bottom   groove up   for arm 1
    plate 1   middle   arm 1 down, arm 2 up      41.8103 deg between grooves
    plate 2   middle   arm 2 down, arm 3 up      37.3774 deg
    plate 3   cap      groove down for arm 3

Four prints per hub, ten hubs per dome. The ten base points are two mirror
sets of five, differing only in which side the G bow leaves on -- a planar
part turned over serves the other five, so it is still one geometry.

Helpers are copied from fan_node_v2.py rather than shared, as that file says:
all three connector scripts are exec'd standalone inside FreeCAD, so sharing
needs a path loader in each, and that refactor is worth doing once the family
settles.

Run:  exec(open('.../connectors/base_hub_v1.py').read()) inside FreeCAD, or
through connectors/generate_clamps.py, which drives it from the model data.
"""

import math
import os

import FreeCAD as App
import Part

DOC_NAME = "StarDome_BaseHub_V1"
USE_SPREADSHEET_IF_PRESENT = True

# Gaps between the three arms, in fan order. Overridden from the model by
# generate_clamps.py; these are D6's and they do not vary with diameter.
DEFAULT_FAN_GAPS = [41.810315, 37.377368]

PLATE_NAMES = ["Bottom", "Mid1", "Mid2", "Cap"]

OVERHANG_LIMIT_DEG = 45.0
NEGLIGIBLE_FACE_MM2 = 5.0

INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance added to each rod channel"),
    ("rodGap",                 0.0,  "mm",  "gap between adjacent rods; stack pitch is rodDiameter + this"),
    ("rodEngagement",         60.0,  "mm",  "how far a bow end is held inside its channel; sets arm length"),
    ("refRodLength",         300.0,  "mm",  "how far the reference rods are drawn past the hub. Drawing only, except that a longer rod makes the interference check strictly stricter -- there is no part out there for it to hit"),
    ("channelOverrun",         6.0,  "mm",  "how far each channel runs past the body"),
    ("minimumWall",            4.0,  "mm",  "minimum structural wall thickness"),
    ("baseFloor",              5.0,  "mm",  "material under the bottom plate's channel"),
    ("capThickness",           6.0,  "mm",  "material above the cap's channel"),
    ("tiltAllowance",          1.5,  "deg", "radial tilt a rod may arrive with"),
    ("stakeLegWidth",         30.0,  "mm",  "each leg of the driven steel angle, across"),
    ("stakeThickness",         3.0,  "mm",  "the angle's material thickness"),
    ("stakeLength",          500.0,  "mm",  "how long the angle is; drawing only, and it is mostly in the ground"),
    ("stakeClearance",         0.6,  "mm",  "fit clearance on the stake slot, per side"),
    ("stakeBoltDiameter",      8.5,  "mm",  "M8 clearance hole through the stake slot"),
    ("fastenerDiameter",       5.5,  "mm",  "M5 clearance hole diameter"),
    ("fastenerHeadDiameter",  10.0,  "mm",  "M5 head / washer outside diameter"),
    ("headClearance",          0.6,  "mm",  "diametral clearance for the head counterbore"),
    ("headBoreDepth",          4.4,  "mm",  "counterbore depth for head + washer"),
    ("nutAcrossFlats",         8.3,  "mm",  "M5 nut across flats + fit clearance"),
    ("nutRecessDepth",         4.6,  "mm",  "captive nut pocket depth"),
    ("boltHoleClearance",      0.4,  "mm",  "diametral print clearance on the bolt shank hole"),
    ("hubRadiusFactor",        2.2,  "-",   "hub radius as a multiple of rodDiameter"),
    ("armWidthFactor",         1.6,  "-",   "arm width as a multiple of the boss diameter"),
    ("edgeRadius",             2.0,  "mm",  "outer edge radius"),
]


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------
def azimuths_from_gaps(gaps):
    """Arm directions in the fan plane, starting at zero."""
    out = [0.0]
    for gap in gaps:
        out.append(out[-1] + gap)
    return out


def widest_arm_gap(azimuths):
    """The bisector of the widest gap *between two arms*, and its size.

    Not the empty sector -- that is the 281 deg with nothing in it at all.
    This is the roomiest place among the arms, which is where a slot running
    right through the hub has to come out.
    """
    ordered = sorted(a % 360.0 for a in azimuths)
    best = None
    for i in range(len(ordered) - 1):
        size = ordered[i + 1] - ordered[i]
        if best is None or size > best[1]:
            best = ((ordered[i] + ordered[i + 1]) / 2.0, size)
    return best


def empty_sector(azimuths):
    """The one sector with no arm in it, as (start, size) in degrees.

    Three arms spanning 79 deg leave 281 of nothing. That is where the stake
    and both bolts have to live, so it is worth naming rather than assuming.
    """
    ordered = sorted(a % 360.0 for a in azimuths)
    best = None
    for i, a in enumerate(ordered):
        nxt = ordered[(i + 1) % len(ordered)]
        size = (nxt - a) % 360.0
        if size == 0.0:
            size = 360.0
        if best is None or size > best[1]:
            best = (a, size)
    return best


def direction(azimuth_deg):
    r = math.radians(azimuth_deg)
    return App.Vector(math.cos(r), math.sin(r), 0.0)


def rod_solid(radius, length, azimuth_deg, z, reach_back):
    """The rod itself: it ends at the hub, so it only runs one way.

    ``reach_back`` is how far it is drawn past the centre, which is only for
    interference checking -- the real rod stops there.
    """
    d = direction(azimuth_deg)
    start = App.Vector(-d.x * reach_back, -d.y * reach_back, z)
    return Part.makeCylinder(radius, length + reach_back, start, d)


def rod_channel(radius, length, azimuth_deg, z, tilt_deg, reach_back, steps=2):
    """A rod channel with flared ends, built in a local frame then placed.

    Building it in world coordinates raised `Bnd_Box is void` on some arms and
    produced invalid solids on others -- the same OCC instability fan_node_v2
    documents. Build along +X at the origin, then rotate and translate.
    """
    base = Part.makeCylinder(
        radius, length + reach_back, App.Vector(-reach_back, 0, 0), App.Vector(1, 0, 0)
    )
    solid = base
    for k in range(1, steps + 1):
        angle = tilt_deg * k / steps
        for sign in (1.0, -1.0):
            rotated = base.copy()
            rotated.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), sign * angle)
            solid = solid.fuse(rotated)
    solid = solid.removeSplitter()
    solid.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    solid.translate(App.Vector(0, 0, z))
    return solid


def angle_profile(leg, thickness, length, azimuth_deg, clearance=0.0):
    """A steel angle: an L in section, run along one azimuth.

    An angle rather than a flat bar, and that is not a detail. A blade in a
    slot can rotate in its own plane; an L cannot, because turning it drives
    one leg into the side of the slot. The hub gets its resistance to twisting
    on the stake for free, out of the section.

    Built in a local frame -- section in (Y, Z), extruded along +X -- then
    turned to the azimuth, the same way the rod channels are, because building
    boxes at an angle in world coordinates is where OCC starts producing
    invalid solids.
    """
    half = leg / 2.0 + clearance
    t = thickness + 2.0 * clearance
    # Two legs sharing the corner at (-half, -half) of a leg-square centred on
    # the axis, so the section sits centred whatever the leg width.
    flat = Part.makeBox(length, 2.0 * half, t, App.Vector(0.0, -half, -half))
    upright = Part.makeBox(length, t, 2.0 * half, App.Vector(0.0, -half, -half))
    solid = flat.fuse(upright).removeSplitter()
    solid.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    return solid


def arm(length, width, height, z, azimuth_deg):
    """A rectangular arm running out along one azimuth from the hub."""
    box = Part.makeBox(
        length, width, height, App.Vector(0.0, -width / 2.0, z)
    )
    box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    return box


def plate_blank(hub_radius, arm_length, arm_width, boss_radius, z_lo, z_hi,
                azimuths, stake_azimuth, stake_reach):
    """Hub disc, one arm per rod, and a tail out to the stake slot."""
    height = z_hi - z_lo
    body = Part.makeCylinder(
        hub_radius, height, App.Vector(0, 0, z_lo), App.Vector(0, 0, 1)
    )
    for az in azimuths:
        body = body.fuse(arm(arm_length, arm_width, height, z_lo, az))
    # The tail: material out to and around the stake slot, in the empty sector.
    body = body.fuse(
        arm(stake_reach, boss_radius * 2.0, height, z_lo, stake_azimuth)
    )
    return body.removeSplitter()


def _ok(shape):
    try:
        return shape is not None and shape.isValid() and shape.Volume > 0.0
    except Exception:
        return False


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def build(values, fan_gaps=None):
    gaps = list(fan_gaps or DEFAULT_FAN_GAPS)
    if len(gaps) != 2:
        raise ValueError(
            f"a three-arm fan has two gaps, got {len(gaps)}: {gaps}"
        )
    azimuths = azimuths_from_gaps(gaps)

    rod_d = values["rodDiameter"]
    channel_r = rod_d / 2.0 + values["rodClearance"] / 2.0
    wall = values["minimumWall"]

    # The empty sector is where everything that is not a rod has to go.
    sector_start, sector_size = empty_sector(azimuths)

    # The stake runs right through the hub, so its axis is not the bisector of
    # the empty sector -- that would come out 2 deg from an arm. It is set by
    # where it has to *exit*: the middle of the widest gap between two arms.
    #
    # A through slot is what makes the part usable in the field. Drive the
    # angle to whatever depth the ground gives, then drop the hub on: it finds
    # its own height. A blind slot means controlling the driven depth to the
    # millimetre, standing in a field, ten times per dome.
    exit_azimuth, exit_gap = widest_arm_gap(azimuths)
    stake_axis = (exit_azimuth + 180.0) % 360.0

    boss_r = values["fastenerHeadDiameter"] / 2.0 + wall
    slot_half = values["stakeLegWidth"] / 2.0 + values["stakeClearance"]

    # Two bolts, one either side of the stake slot, far enough round that each
    # clears the nearest arm and far enough out that its boss clears the slot.
    # fan_node_v2 puts them opposite each other, which works for a fan that
    # spans 180; three arms spanning 79 put the opposite direction 2 deg from
    # an arm, so they go side by side instead.
    stake_azimuth = stake_axis
    bolt_spread = min(sector_size / 2.0 - 12.0, 55.0)
    bolt_azimuths = [stake_azimuth - bolt_spread, stake_azimuth + bolt_spread]
    closest = min(
        abs(math.sin(math.radians(b - a)))
        for b in bolt_azimuths
        for a in azimuths
    )
    bolt_offset = max(
        (boss_r + channel_r) / max(closest, 1e-6),
        (slot_half + boss_r + wall) / max(
            abs(math.sin(math.radians(bolt_spread))), 1e-6
        ),
    )

    hub_r = values["hubRadiusFactor"] * rod_d
    arm_w = values["armWidthFactor"] * boss_r * 2.0
    arm_len = values["rodEngagement"] + values["channelOverrun"]
    stake_reach = bolt_offset + boss_r + values["edgeRadius"]

    length = arm_len
    reach_back = hub_r
    tilt_slack = (length / 2.0) * math.tan(math.radians(values["tiltAllowance"]))

    pitch = rod_d + values["rodGap"]
    levels = [(k - 1.0) * pitch for k in range(3)]

    # The angle passes right through, and it cannot go through the middle: its
    # section is 30 mm deep along the stack axis whatever way it is rolled,
    # and the three rods with their walls already occupy 38 of the stack's
    # 43 mm. There is no room, and the check below says so in mm3.
    #
    # So it goes UNDER the bundle, through a deepened base plate. In the part's
    # own frame that is -Z; installed, the stack axis is horizontal and radial,
    # so the angle still stands vertical in the fan plane and is simply offset
    # radially from the rods. The offset is a moment, and it is the one the
    # ground and the angle's own bending are best placed to take.
    slot_span = values["stakeLegWidth"] + 2.0 * values["stakeClearance"]
    slot_top = levels[0] - channel_r - tilt_slack - wall
    slot_bottom = slot_top - slot_span
    z_bottom = slot_bottom - values["baseFloor"]
    z_top = levels[2] + channel_r + tilt_slack + values["capThickness"]

    bolt_points = [
        App.Vector(
            direction(az).x * bolt_offset, direction(az).y * bolt_offset, 0.0
        )
        for az in bolt_azimuths
    ]

    shank_r = (values["fastenerDiameter"] + values["boltHoleClearance"]) / 2.0
    head_r = (values["fastenerHeadDiameter"] + values["headClearance"]) / 2.0

    # Drawn well past the arm so the three directions read at a glance. The
    # channels stay at the working length; only the rods are long.
    ref_len = max(length, values["refRodLength"])
    rods = [
        rod_solid(rod_d / 2.0, ref_len, azimuths[k], levels[k], reach_back)
        for k in range(3)
    ]
    channels = [
        rod_channel(
            channel_r, length, azimuths[k], levels[k],
            values["tiltAllowance"], reach_back,
        )
        for k in range(3)
    ]

    bolt_height = (z_top + 2.0) - (z_bottom - 2.0)
    bolts = [
        Part.makeCylinder(
            shank_r, bolt_height, App.Vector(p.x, p.y, z_bottom - 2.0),
            App.Vector(0, 0, 1),
        )
        for p in bolt_points
    ]

    # The stake slot: an L-section hole running out along the bisector of the
    # empty sector, so that once the part is stood up it points at the ground.
    # The angle passes right through the hub and on into the earth, so the slot
    # runs the full reach and out the back.
    through = stake_reach + arm_len + 8.0
    slot_centre_z = (slot_top + slot_bottom) / 2.0
    slot = angle_profile(
        values["stakeLegWidth"],
        values["stakeThickness"],
        2.0 * through,
        stake_azimuth,
        values["stakeClearance"],
    )
    slot.translate(
        App.Vector(
            -direction(stake_azimuth).x * through,
            -direction(stake_azimuth).y * through,
            slot_centre_z,
        )
    )

    # And a cross bolt through it, perpendicular to the blade and in the fan
    # plane, which is what stops the hub lifting off the stake.
    cross_at = bolt_offset * 0.55
    cross_dir = direction(stake_azimuth + 90.0)
    cross_centre = direction(stake_azimuth).multiply(cross_at)
    cross = Part.makeCylinder(
        values["stakeBoltDiameter"] / 2.0,
        (slot_half + boss_r + wall) * 2.0 + 4.0,
        App.Vector(
            cross_centre.x - cross_dir.x * ((slot_half + boss_r + wall) + 2.0),
            cross_centre.y - cross_dir.y * ((slot_half + boss_r + wall) + 2.0),
            slot_centre_z,
        ),
        cross_dir,
    )

    plates = []
    for i in range(4):
        z_lo = z_bottom if i == 0 else levels[i - 1]
        z_hi = z_top if i == 3 else levels[i]
        blank = plate_blank(
            hub_r, arm_len, arm_w, boss_r, z_lo, z_hi,
            azimuths, stake_azimuth, stake_reach,
        )
        solid = blank
        for ch in channels:
            solid = solid.cut(ch)
        for bolt in bolts:
            solid = solid.cut(bolt)
        solid = solid.cut(slot)
        solid = solid.cut(cross)
        solid = solid.removeSplitter()
        if not _ok(solid):
            raise RuntimeError(f"plate {PLATE_NAMES[i]} came out invalid")
        plates.append(solid)

    # The angle itself, drawn: mostly in the ground, and the reason the empty
    # sector exists.
    # Drawn passing right through and out the far side, which is the point.
    protrude = arm_len * 0.5
    stake = angle_profile(
        values["stakeLegWidth"],
        values["stakeThickness"],
        values["stakeLength"],
        stake_azimuth,
    )
    stake.translate(
        App.Vector(
            -direction(stake_azimuth).x * protrude,
            -direction(stake_azimuth).y * protrude,
            slot_centre_z,
        )
    )

    # A keep-out around each rod: the channel plus a wall, over the length the
    # part actually holds it. Nothing may be cut out of this.
    keepouts = [
        Part.makeCylinder(
            channel_r + wall,
            arm_len,
            App.Vector(0.0, 0.0, levels[k]),
            direction(azimuths[k]),
        )
        for k in range(3)
    ]

    geo = {
        "plates": plates,
        "rods": rods,
        "channels": channels,
        "keepouts": keepouts,
        "slot": slot,
        "stake": stake,
    }
    dims = {
        "fan_gaps_deg": gaps,
        "arm_azimuths_deg": azimuths,
        "fan_spread_deg": azimuths[-1] - azimuths[0],
        "empty_sector_deg": sector_size,
        "stake_azimuth_deg": stake_azimuth,
        "bolt_azimuths_deg": bolt_azimuths,
        "bolt_offset_mm": bolt_offset,
        "rod_levels_mm": levels,
        "pitch_mm": pitch,
        "hub_radius_mm": hub_r,
        "arm_length_mm": arm_len,
        "ref_rod_length_mm": ref_len,
        "arm_width_mm": arm_w,
        "stake_reach_mm": stake_reach,
        "stake_exit_azimuth_deg": exit_azimuth,
        "stake_exit_gap_deg": exit_gap,
        "stake_leg_mm": values["stakeLegWidth"],
        "slot_centre_z_mm": slot_centre_z,
        "slot_clear_of_rods_mm": levels[0] - channel_r - slot_top,
        "stake_thickness_mm": values["stakeThickness"],
        "z_bottom_mm": z_bottom,
        "z_top_mm": z_top,
        "stack_height_mm": z_top - z_bottom,
        "plate_count": len(plates),
    }
    return geo, dims


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
def _vol(shape):
    try:
        return shape.Volume
    except Exception:
        return 0.0


def verify(geo, dims, values):
    """Checks that would have caught the mistakes V1 of the fan node made."""
    problems = []
    plates = geo["plates"]

    for name, plate in zip(PLATE_NAMES, plates):
        if not _ok(plate):
            problems.append(f"{name}: not a valid solid")

    # No plate may eat into a rod.
    interference = 0.0
    for name, plate in zip(PLATE_NAMES, plates):
        for i, rod in enumerate(geo["rods"]):
            common = plate.common(rod)
            v = _vol(common)
            if v > 0.5:
                interference += v
                problems.append(
                    f"{name} overlaps rod {i + 1} by {v:.1f} mm3"
                )

    # Every rod must be enclosed: it should be held from below by one plate and
    # above by the next, over the engagement length.
    engaged = []
    for i in range(len(geo["rods"])):
        below = plates[i]
        above = plates[i + 1]
        engaged.append(_ok(below) and _ok(above))
    if not all(engaged):
        problems.append(f"rods not enclosed by a pair of plates: {engaged}")

    # The stack must not be taller than the rods are apart times their count,
    # plus the floor and cap -- a sanity bound that catches a runaway pitch.
    # The slot band is part of the stack now: the angle passes under the rods,
    # so the base plate carries its own leg width plus a wall.
    bound = (
        dims["pitch_mm"] * 3
        + values["baseFloor"]
        + values["capThickness"]
        + values["stakeLegWidth"]
        + 2.0 * values["stakeClearance"]
        + values["minimumWall"]
        + 8.0
    )
    if dims["stack_height_mm"] > bound:
        problems.append(
            f"stack is {dims['stack_height_mm']:.1f} mm, expected under {bound:.1f}"
        )

    # The angle's leg has to fit between the outer faces of the stack, or the
    # slot breaks out of the top or bottom instead of being a slot.
    if dims["slot_clear_of_rods_mm"] < values["minimumWall"] - 1e-6:
        problems.append(
            f"only {dims['slot_clear_of_rods_mm']:.1f} mm of material between "
            f"the slot and the lowest rod, wanted {values['minimumWall']:.1f}"
        )

    # And the plates must not eat into it either.
    if geo.get("stake") is not None:
        for name, plate in zip(PLATE_NAMES, plates):
            v = _vol(plate.common(geo["stake"]))
            if v > 0.5:
                problems.append(f"{name} overlaps the stake by {v:.1f} mm3")

    # A slot that runs right through can take the wall out from under a rod.
    # Check inside the part only: two lines in one plane always cross
    # eventually, and where they cross out in the air there is nothing to
    # remove.
    if geo.get("slot") is not None:
        for i, keepout in enumerate(geo.get("keepouts", [])):
            v = _vol(geo["slot"].common(keepout))
            if v > 1.0:
                problems.append(
                    f"the stake slot cuts {v:.1f} mm3 out of the wall around "
                    f"rod {i + 1}"
                )

    # The stake slot has to be in the empty sector, not through an arm.
    for az in dims["arm_azimuths_deg"]:
        separation = abs(
            (dims["stake_azimuth_deg"] - az + 180.0) % 360.0 - 180.0
        )
        if separation < 30.0:
            problems.append(
                f"stake slot at {dims['stake_azimuth_deg']:.1f} deg is only "
                f"{separation:.1f} deg from the arm at {az:.1f}"
            )

    return {
        "problems": problems,
        "ok": not problems,
        "rod_interference_mm3": round(interference, 2),
        "plate_volumes_mm3": [round(_vol(p), 1) for p in plates],
        "stack_height_mm": round(dims["stack_height_mm"], 2),
        "arm_azimuths_deg": [round(a, 4) for a in dims["arm_azimuths_deg"]],
        "stake_azimuth_deg": round(dims["stake_azimuth_deg"], 4),
        "empty_sector_deg": round(dims["empty_sector_deg"], 4),
    }


def derived_rows(dims, values):
    return [
        ("fanSpread", round(dims["fan_spread_deg"], 4), "deg",
         "angle from the lowest arm to the highest"),
        ("emptySector", round(dims["empty_sector_deg"], 4), "deg",
         "the sector with no arm; the stake and both bolts live here"),
        ("stakeAzimuth", round(dims["stake_azimuth_deg"], 4), "deg",
         "bisector of that sector; points at the ground once installed"),
        ("boltOffset", round(dims["bolt_offset_mm"], 3), "mm",
         "how far out the bolts sit"),
        ("stackHeight", round(dims["stack_height_mm"], 3), "mm",
         "bottom of the base plate to top of the cap"),
        ("armLength", round(dims["arm_length_mm"], 3), "mm",
         "hub centre to the end of an arm"),
        ("refRodDrawn", round(dims["ref_rod_length_mm"], 1), "mm",
         "length of each reference rod; drawing only"),
        ("stakeLeg", round(dims["stake_leg_mm"], 1), "mm",
         "each leg of the driven angle"),
        ("slotCentre", round(dims["slot_centre_z_mm"], 2), "mm",
         "where the through slot sits on the stack axis; below every rod"),
        ("slotClearance", round(dims["slot_clear_of_rods_mm"], 2), "mm",
         "material between the slot and the lowest rod"),
        ("stakeExit", round(dims["stake_exit_azimuth_deg"], 2), "deg",
         "where the angle comes out: the middle of the widest gap between arms"),
        ("stakeSection", f"L{dims['stake_leg_mm']:g}x{dims['stake_leg_mm']:g}"
         f"x{dims['stake_thickness_mm']:g}", "-",
         "the angle to buy"),
        ("plateCount", dims["plate_count"], "-", "prints per hub"),
    ]


# --------------------------------------------------------------------------
# document
# --------------------------------------------------------------------------
# See docs/colours.md. A light-to-dark ramp so the stacking order reads without
# selecting anything, and the family colours for the rods -- the same three a
# bow gets in every Blender scene.
PLATE_COLOURS = [
    (0.86, 0.86, 0.89),
    (0.76, 0.81, 0.89),
    (0.70, 0.76, 0.87),
    (0.62, 0.70, 0.85),
]
PLATE_TRANSPARENCY = 55
FAMILY_COLOUR = {
    "G": (0.15, 0.55, 0.95),
    "U": (0.95, 0.45, 0.10),
    "L": (0.20, 0.75, 0.35),
}
# Arms in fan order at a base point are L, U, G -- see weave.base_fan. Family
# colours work here, unlike at the four-rod node, because no two arms share a
# family.
ROD_FAMILIES = ["L", "U", "G"]
# Steel, and not one of the rod families: it is the one member here that is
# bought rather than made.
STAKE_COLOUR = (0.45, 0.45, 0.48)


def populate(doc, geo):
    # Everything except the parameter sheet, which run() still holds a handle
    # to and writes after this.
    for obj in list(doc.Objects):
        if obj.TypeId == "Spreadsheet::Sheet":
            continue
        doc.removeObject(obj.Name)
    for name, solid in zip(PLATE_NAMES, geo["plates"]):
        obj = doc.addObject("Part::Feature", f"Plate_{name}")
        obj.Shape = solid
    for i, rod in enumerate(geo["rods"]):
        obj = doc.addObject("Part::Feature", f"Ref_Rod{i + 1}")
        obj.Shape = rod
    if geo.get("stake") is not None:
        obj = doc.addObject("Part::Feature", "Ref_Stake")
        obj.Shape = geo["stake"]
    doc.recompute()


def apply_view(doc):
    """Plates translucent, rods in their family colours. See docs/colours.md.

    A no-op headless, and not because the import fails: FreeCADGui imports
    perfectly well under freecadcmd, but `ViewObject` is None whenever
    `App.GuiUp` is 0, so guarding on the import alone passes and then colours
    nothing. Guard on GuiUp.
    """
    if not getattr(App, "GuiUp", 0):
        return
    try:
        import FreeCADGui as Gui
    except ImportError:
        return
    if not hasattr(doc, "Objects"):
        return
    for obj in doc.Objects:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        if obj.Name.startswith("Plate_"):
            idx = PLATE_NAMES.index(obj.Name.split("_", 1)[1])
            view.ShapeColor = PLATE_COLOURS[idx % len(PLATE_COLOURS)]
            view.Transparency = PLATE_TRANSPARENCY
        elif obj.Name == "Ref_Stake":
            view.ShapeColor = STAKE_COLOUR
            view.Transparency = 0
        elif obj.Name.startswith("Ref_Rod"):
            idx = int(obj.Name[-1]) - 1
            view.ShapeColor = FAMILY_COLOUR[ROD_FAMILIES[idx % len(ROD_FAMILIES)]]
            view.Transparency = 0
    try:
        Gui.SendMsgToActiveView("ViewFit")
    except Exception:
        pass


def write_parameters(doc, sheet, values, derived):
    if sheet is None:
        return
    sheet.clearAll()
    sheet.set("A1", "alias")
    sheet.set("B1", "value")
    sheet.set("C1", "unit")
    sheet.set("D1", "note")
    row = 2
    for alias, value, unit, note in INPUTS:
        sheet.set(f"A{row}", alias)
        sheet.set(f"B{row}", str(values.get(alias, value)))
        sheet.set(f"C{row}", unit)
        sheet.set(f"D{row}", note)
        row += 1
    row += 1
    sheet.set(f"A{row}", "DERIVED")
    row += 1
    for alias, value, unit, note in derived:
        sheet.set(f"A{row}", alias)
        sheet.set(f"B{row}", str(value))
        sheet.set(f"C{row}", unit)
        sheet.set(f"D{row}", note)
        row += 1
    doc.recompute()


def read_or_build_parameters(doc):
    values = {alias: value for alias, value, _, _ in INPUTS}
    sheet = None
    if USE_SPREADSHEET_IF_PRESENT:
        for obj in doc.Objects:
            if obj.TypeId == "Spreadsheet::Sheet":
                sheet = obj
                break
        if sheet is None:
            sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    return sheet, values


def run(fan_gaps=None, out_dir=None, doc_path=None, rod_diameter=None):
    if doc_path and os.path.exists(doc_path):
        doc = App.openDocument(doc_path)
    elif DOC_NAME in App.listDocuments():
        doc = App.getDocument(DOC_NAME)
    else:
        doc = App.newDocument(DOC_NAME)
    sheet, values = read_or_build_parameters(doc)
    if rod_diameter:
        values["rodDiameter"] = float(rod_diameter)
    geo, dims = build(values, fan_gaps)
    report = verify(geo, dims, values)
    populate(doc, geo)
    apply_view(doc)
    write_parameters(doc, sheet, values, derived_rows(dims, values))
    doc.recompute()
    path = doc_path or (
        os.path.join(out_dir, "star_dome_base_hub_v1.FCStd") if out_dir else None
    )
    if path:
        doc.saveAs(path)
        report["saved_to"] = path
    return report


if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint

    pprint.pprint(REPORT, width=112)
