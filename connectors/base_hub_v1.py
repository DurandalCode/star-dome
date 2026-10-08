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
281 deg of nothing, and once the part is stood up that sector faces down. That
is where the driven stake has to be met, and it is not a preference: the
one direction a foot has no room in is straight up. Vertical out of the hub is
azimuth 90, the U arm sits at 79.19, and a rod is 5.7 mm across with a wall
round it -- so the vertical line is inside that arm for its first 67 mm. Above
a foot there is nothing but bows. Below it there is nothing at all.

THE REBAR IS MET ON A FLAT PAD AND CLOSED IN BY A CRADLE

The stake is a driven steel rebar (decision 0031). It used to be an angle, and
the pad on the bottom plate was drawn for that angle: a flat face straight
down from the hub with two M8 holes 50 mm apart and their nuts captive in the
far side. The pad has not changed for the bar, and must not -- BASE3-8 bottom
plates are already printed -- because a flat face and two holes is all a bar
needs from it too.

What goes round the far side is the **cradle**: a block with a 90 deg vee
along the bar, bolted to the pad by those two holes. A round bar touches both
flanks of a vee whatever its diameter, so the pad and the vee hold it on three
lines -- the flat and two flanks -- at every size:

    down          the cradle clamps. Per foot at 20 m/s the ground takes 154 N
                  of uplift and 188 N of shear (`make loads`). This is still
                  friction in plastic and needs a physical check
    height        ANY. Nothing is drilled, nothing is indexed: hard ground that
                  stops the bar 40 mm short is a cradle done up 40 mm further
                  down it
    size          ANY bar from `stakeRebarMin` to `stakeRebarMax`, 8 to 18 mm
                  across the ribs as drawn. The vee is cut just shallow enough
                  that on the thinnest bar the rim stops `stakeCradleGap`
                  short of the pad; a thicker bar only stands it further off.
                  So the bolts always pull on the steel, never on the plate

The angle's wrap fitted one leg width, and decision 0026 rejected a vee for it
because a 90 deg vee and a 90 deg corner have parallel faces and meet at one
size only. That is true of a corner and false of a round.

WHY THE CRADLE IS A SEPARATE PIECE AND NOT PART OF THE PLATE

The bar lies against the face the plate is PRINTED on, so any material
reaching round it would have to hang below that face, and below that face is
the bed. A second piece is printed in its own orientation: floor down, vee up,
the flanks 45 deg slopes facing the nozzle.

It is the fifth print of the hub -- 27 cm3 at BASE3-8, half what the wrap was --
and it is symmetric about the bar, so turning the hub over for the mirror
five feet does not turn it into a second part. The same two holes in the pad
also take an M8 U-bolt of `stakeBoltSpan` (decision 0026).

The bar passes BESIDE the hub, along the bottom plate's outer face, where the
whole half-space is empty.

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
    cradle    the vee that closes the bottom plate's pad round the rebar

Five prints per hub, ten hubs per dome. The ten base points are two mirror
sets of five, differing only in which side the G bow leaves on -- a planar
part turned over serves the other five, so it is still one geometry.

FIELD SEQUENCE

    at home   bolt the plate stack up: four bolts, nut captive in the bottom
              plate, head and washer down a counterbore in the cap. One tool,
              one end, and nothing to hold on the other side
    at the    drive the rebar -> lay the hub's pad against it -> close the
    dome      cradle round it and do up its two bolts -> push each bow end
              into its channel -> pin it

Note the order. The four-rod node has to be opened, a rod laid, a plate
closed, the next rod laid, and so on, because it CLAMPS its rods. This one
does not: the channels are a slide fit, so the stack is assembled once, on the
ground or at home, and the bow ends go in afterwards. That is a much better
thing to be doing in a field with cold hands.

The price of a slide fit is that the channel locates the rod and holds it
against nothing, so each arm carries a cross pin through arm and rod together.

EVERY NUT IN THIS PART IS CAPTIVE

V1 drilled the two stack bolts straight through all four plates and left it
there: no counterbore, no nut pocket, a bolt standing proud at one end and a
loose nut at the other, and two spanners to do up a joint that is assembled
blind inside a stack. The pockets were already in the parameter table --
``nutAcrossFlats``, ``nutRecessDepth``, ``headBoreDepth`` -- and nothing cut
them. They are cut now, the same way ``fan_node_v2`` cuts them:

    bottom plate   hex pocket at its outer face, opening onto the print bed,
                   with a cone up to the shank so the ceiling is not flat
    cap            counterbore for head and washer at its outer face -- which
                   is the cap's bed, because the cap prints flipped -- with a
                   cone down to the shank for the same reason

The cradle's two bolts are the same: their nuts sit captive in the pad's far
face -- a face that points UP while the bottom plate prints, so the pockets
need no cone and no support -- and the heads go under the cradle where a spanner
reaches them from the side you are already kneeling on.

Helpers come from connectors/kit.py, shared with the other live generators.

Run:  exec(open('.../connectors/base_hub_v1.py').read()) inside FreeCAD, or
through connectors/generate_clamps.py, which drives it from the model data.
"""

import itertools
import math
import os
import sys

import FreeCAD as App
import Part

# REPO is overridable from the calling namespace before exec(); exec'd source
# has no __file__ to fall back on. Same contract as generate_clamps.py.
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

DOC_NAME = "StarDome_BaseHub_V1"
TITLE = "Star Dome base hub V1 - parameters"
USE_SPREADSHEET_IF_PRESENT = True

# Gaps between the three arms, in fan order. Overridden from the model by
# generate_clamps.py; these are D6's and they do not vary with diameter.
DEFAULT_FAN_GAPS = [41.810315, 37.377368]

PLATE_NAMES = ["Bottom", "Mid1", "Mid2", "Cap"]

# Which piece prints the other way up. The cap's channel faces DOWN in the
# part's own frame, so it goes on the bed on its outer face and the channel
# looks up at the nozzle; everything else is already that way round. It is a
# set rather than a rule in two places because the print sheet has to lay the
# pieces out the same way the printability check judged them.
FLIPPED_PIECES = {"Cap"}


def plate_names(arm_count):
    """One plate above each rod and one below the lot: arms + 1 pieces.

    A doorway jamb gathers two bow ends instead of three, so it is the same
    stack a plate shorter. Naming them by position rather than by number keeps
    a Bottom and a Cap in both.
    """
    return ["Bottom"] + [f"Mid{i}" for i in range(1, arm_count)] + ["Cap"]

INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter"),
    ("rodNominalDiameter",     0.0,  "mm",  "the rod as a structural member, when that is not what a caliper reads across it -- composite rebar is named by its equivalent diameter and measures more over its winding. 0 means the two are the same"),
    ("rodClearance",           1.4,  "mm",  "diametral clearance on each rod channel. A slide fit, not a clamp fit: the stack is bolted up first and the bow ends pushed in afterwards, which is a far better field sequence than laying a rod, closing a plate, laying the next. The rod is then LOCATED by the channel and HELD by the pin -- see rodPinDiameter"),
    ("rodPinDiameter",         0.0,  "mm",  "cross pin through arm and rod, once the rod is in. Without it a slide fit locates the rod and holds it against nothing"),
    ("rodPinAt",              40.0,  "mm",  "how far along the arm the pin sits"),
    ("rodGap",                 0.0,  "mm",  "gap between adjacent rods; stack pitch is rodDiameter + this"),
    ("rodEngagement",         60.0,  "mm",  "how far a bow end is held inside its channel; sets arm length"),
    ("refRodLength",         300.0,  "mm",  "how far the reference rods are drawn past the hub. Drawing only, except that a longer rod makes the interference check strictly stricter -- there is no part out there for it to hit"),
    ("channelOverrun",         6.0,  "mm",  "how far each channel runs past the body"),
    ("minimumWall",            0.0,  "mm",  "0 takes it from rodDiameter: 0.4 of the rod, never under 3 mm. A real number overrides"),
    ("baseFloor",              5.0,  "mm",  "material under the bottom plate's channel"),
    ("capThickness",           6.0,  "mm",  "material above the cap's channel"),
    ("tiltAllowance",          1.5,  "deg", "radial tilt a rod may arrive with"),
    ("firstArmRise",       37.3774,  "deg", "how far the first arm rises above horizontal once installed; this is what ties the part's own frame to the ground"),
    ("stakeRebarDiameter",    12.0,  "mm",  "the driven steel rebar the reference solid draws, and the bar the cradle is drawn seated on. Drawing only: the cradle takes anything from stakeRebarMin to stakeRebarMax"),
    ("stakeRebarMin",          8.0,  "mm",  "the thinnest bar the cradle must still clamp. Sets the vee's depth: on this bar the cradle's rim stops stakeCradleGap short of the pad"),
    ("stakeRebarMax",         18.0,  "mm",  "the thickest bar the cradle must still seat, measured across the ribs -- 18 is a 16 mm rebar. Only has to touch both flanks below the mouth"),
    ("stakeVeeAngle",         90.0,  "deg", "included angle of the cradle's vee. A round bar touches both flanks of a vee at ANY diameter, which is what makes one cradle universal"),
    ("stakeLength",          500.0,  "mm",  "how long the rebar is; drawing only, and it is mostly in the ground"),
    ("stakeStandProud",      120.0,  "mm",  "how much of the rebar is left above the foot once it is driven. Drawing only, but it is the field rule the reference solid checks: the bar has to clear the hub over all of it, and what stands above is what the cover's loop drops over -- decision 0014"),
    ("stakeBoltDiameter",      8.5,  "mm",  "clearance hole for each of the two bolts that pull the cradle onto the pad. 8.5 is M8"),
    ("stakeBoltSpan",         50.0,  "mm",  "centre to centre of those two bolts, one either side of the bar. It is also the span of the U-bolt this same hole pair takes instead -- see decision 0026"),
    ("stakeBoltAt",            0.0,  "mm",  "how far below the hub centre the pair sits. 0 puts it as close in as their own nuts allow past the stack bolts, which is the shortest pad that works"),
    ("stakeCradleGap",         0.6,  "mm",  "how far the cradle's rim stops short of the pad on the THINNEST bar, so the bolts pull it onto the bar and never bottom it out on the plate. Thicker bars only open it up"),
    ("stakeCradleLength",     40.0,  "mm",  "how much of the bar the cradle holds, along the bar. Longer holds the hub square to the bar"),
    ("stakeLugWidth",          0.0,  "mm",  "across the pad. 0 takes it from the bolt pair: its span plus a hole and a wall either side"),
    ("stakeLugThickness",      0.0,  "mm",  "through the pad, and it is what the two nuts bear on. 0 takes the plate's own floor, which is already more than the load needs"),
    ("fastenerSize",            0.0,  "",    "which metric bolt: 0 chooses it from the rod -- half the rod, snapped to M3/M4/M5/M6/M8 -- and 3, 4, 5, 6 or 8 forces one"),
    ("fastenerDiameter",       0.0,  "mm",  "clearance hole for the bolt. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("fastenerHeadDiameter",  0.0,  "mm",  "head / washer outside diameter. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("headClearance",          0.6,  "mm",  "diametral clearance for the head counterbore"),
    ("headBoreDepth",          0.0,  "mm",  "counterbore depth for head + washer. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("headConeHeight",         0.0,  "mm",  "taper off the head counterbore, so the cap prints upside down without a flat ceiling. 0 takes it from rodDiameter -- see kit.FASTENERS"),
    ("nutAcrossFlats",         0.0,  "mm",  "nut across flats + fit clearance. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("nutRecessDepth",         0.0,  "mm",  "captive nut pocket depth. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("nutConeHeight",          0.0,  "mm",  "taper off the nut pocket, for the same reason. 0 takes it from rodDiameter -- see kit.FASTENERS"),
    ("boltHoleClearance",      0.4,  "mm",  "diametral print clearance on the bolt shank hole"),
    ("hubRadiusFactor",        2.2,  "-",   "hub radius as a multiple of rodDiameter"),
    ("armWidthFactor",         1.6,  "-",   "arm width as a multiple of the boss diameter"),
    ("edgeRadius",             2.0,  "mm",  "outer edge radius"),
]


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------
def empty_sector(azimuths):
    """The one sector with no arm in it, as (start, size) in degrees.

    Three arms spanning 79 deg leave 281 of nothing. That is where the stake
    and the lower stack-bolt pair have to live, so it is worth naming.
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


def driven_rebar(radius, seat_z, y_from, y_to):
    """The steel rebar as it stands in the ground, in the part's own frame.

    Vertical, because you hammer it and the ground is down -- so it runs along
    Y, not along an azimuth. It lies against the pad's seating face at
    `seat_z`, below the bottom plate, where the whole half-space is empty.
    Drawn as the plain round it is clamped as; the ribs are not drawn.
    """
    return Part.makeCylinder(
        radius, y_to - y_from,
        App.Vector(0.0, y_from, seat_z - radius), App.Vector(0, 1, 0),
    )


def vee_depth(half_angle_deg, r_min, r_max, gap):
    """How deep the cradle's vee is, and what that does over a range of bars.

    A round bar in a vee touches both flanks whatever its size: its centre
    sits r / sin(a) above the apex, so its top is r (1 + 1/sin a) above it.
    The pad is that top. So the vee is cut just shallow enough that on the
    thinnest bar the rim still stops `gap` short of the pad -- and every
    thicker bar only stands the cradle further off. That is the whole reason
    this piece fits every bar in the range and the angle's wrap fitted one.

    The other end of the range is where the bar touches the flanks: r cos^2 a
    / sin a above the apex. It has to stay below the mouth, with a millimetre
    of flank above it, or the bar is bearing on the edge.

    Returns (depth, rim gap on the thickest bar, contact height on it).
    """
    s = math.sin(math.radians(half_angle_deg))
    c = math.cos(math.radians(half_angle_deg))
    depth = r_min * (1.0 + 1.0 / s) - gap
    contact = r_max * c * c / s
    if contact > depth - 1.0:
        raise ValueError(
            f"a {2.0 * r_max:g} mm bar touches the vee {contact:.1f} mm up a "
            f"flank that is only {depth:.1f} mm deep: narrow the range or "
            "open the vee"
        )
    return depth, r_max * (1.0 + 1.0 / s) - depth, contact


def stake_cradle(span, bolt_r, wall, half_angle_deg, depth, length,
                 z_apex, at_y):
    """The cradle: a block with a vee that closes the pad into a ring.

    WHY A VEE, WHEN 0026 REJECTED ONE. A 90 deg vee and a 90 deg corner have
    parallel faces, so they meet at one size only; that was true of the angle.
    A round bar touches both flanks of a vee at any diameter. With the pad as
    the third side the bar is held on three lines -- two flanks and the flat
    -- and the bolts squeeze all three. One cradle, every bar in the range.

    WHY IT IS A SEPARATE PIECE, still. The bar lies against the face the
    bottom plate is printed on, so anything reaching round it would hang
    below the bed. The cradle is printed in its own orientation: floor down,
    vee up, and the flanks are 45 deg slopes that face the nozzle.

    THE RIM STOPS SHORT, on every bar: see vee_depth. The bolts always pull
    it onto the steel, never onto the plate.
    """
    half_out = span / 2.0 + bolt_r + wall
    z_base = z_apex - wall
    z_rim = z_apex + depth
    y0 = at_y - length / 2.0
    body = Part.makeBox(
        2.0 * half_out, length, z_rim - z_base,
        App.Vector(-half_out, y0, z_base),
    )
    # The vee, as a triangular prism along the bar, apex down. It runs a
    # millimetre past the rim and past both ends so the cut is clean.
    over = 1.0
    half_mouth = (depth + over) * math.tan(math.radians(half_angle_deg))
    profile = Part.makePolygon([
        App.Vector(0.0, y0 - over, z_apex),
        App.Vector(half_mouth, y0 - over, z_rim + over),
        App.Vector(-half_mouth, y0 - over, z_rim + over),
        App.Vector(0.0, y0 - over, z_apex),
    ])
    vee = Part.Face(profile).extrude(App.Vector(0, length + 2.0 * over, 0))
    return body.cut(vee).removeSplitter()


def arc_height(radius, offset):
    """How far a circle of this radius has risen from its lowest point, `offset`
    to the side. Zero if the offset is outside the circle."""
    return math.sqrt(max(radius ** 2 - offset ** 2, 0.0))


def u_bolt(rod_radius, span, at_y, z_top_of_legs, z_bend):
    """The bought U-bolt, drawn: two legs up through the pad and a bend round
    the angle.

    Built from primitives rather than swept along a wire, for the reason every
    other solid here is: a sweep that fails returns something that still looks
    like a shape and is not one. The bend is a whole torus with the half that
    is not wanted cut off, so which way round OCC decided to sweep it does not
    matter.

    Everything is in the fan plane -- the loop lies in XZ at one Y, because the
    angle it goes round is vertical and the pad it comes up through is flat.
    """
    legs = None
    for sign in (-1.0, 1.0):
        leg = Part.makeCylinder(
            rod_radius, z_top_of_legs - z_bend,
            App.Vector(sign * span / 2.0, at_y, z_bend),
            App.Vector(0, 0, 1),
        )
        legs = leg if legs is None else legs.fuse(leg)
    bend = Part.makeTorus(
        span / 2.0, rod_radius, App.Vector(0.0, at_y, z_bend),
        App.Vector(0, 1, 0),
    )
    below = Part.makeBox(
        span + 4.0 * rod_radius, 4.0 * rod_radius, span / 2.0 + 2.0 * rod_radius,
        App.Vector(
            -(span / 2.0 + 2.0 * rod_radius), at_y - 2.0 * rod_radius,
            z_bend - span / 2.0 - 2.0 * rod_radius,
        ),
    )
    return legs.fuse(bend.common(below)).removeSplitter()


def plate_blank(hub_radius, arm_length, arm_width, boss_radius, z_lo, z_hi,
                azimuths, bolt_points=()):
    """Hub disc, rod arms, an integral lower flange, and upper bolt bosses.

    The lower bolt pair sits beyond the hub disc. A wide flange carries both
    holes inside the plate outline, rather than attaching circular ears through
    narrow radial webs. The upper pair sits in the gaps between rod arms.

    There used to be a tail here as well, carrying material out to and around
    the stake slot. The slot is gone and the tail went with it: the stake pad
    belongs to the bottom plate alone, and the other three were paying for a
    spar to a hole they do not have.
    """
    height = z_hi - z_lo
    body = Part.makeCylinder(
        hub_radius, height, App.Vector(0, 0, z_lo), App.Vector(0, 0, 1)
    )
    for az in azimuths:
        body = body.fuse(kit.arm(arm_length, arm_width, height, z_lo, az))
    if len(bolt_points) >= 2:
        left, right = sorted(bolt_points[:2], key=lambda point: point.x)

        def tangent(point, side):
            """Outer common tangent of the hub and one lower bolt circle."""
            distance = math.hypot(point.x, point.y)
            offset = (hub_radius - boss_radius) / distance
            along = math.sqrt(1.0 - offset ** 2)
            nx = (offset * point.x - side * along * point.y) / distance
            ny = (side * along * point.x + offset * point.y) / distance
            return ((hub_radius * nx, hub_radius * ny),
                    (point.x + boss_radius * nx,
                     point.y + boss_radius * ny))

        left_hub, left_boss = tangent(left, -1.0)
        right_hub, right_boss = tangent(right, 1.0)
        flange_outline = [
            left_hub, right_hub, right_boss,
            (right.x, right.y - boss_radius),
            (left.x, left.y - boss_radius), left_boss, left_hub,
        ]
        flange = Part.Face(Part.makePolygon([
            App.Vector(x, y, z_lo) for x, y in flange_outline
        ])).extrude(App.Vector(0, 0, height))
        body = body.fuse(flange)
        for point in (left, right):
            body = body.fuse(Part.makeCylinder(
                boss_radius, height, App.Vector(point.x, point.y, z_lo),
                App.Vector(0, 0, 1),
            ))
    for point in bolt_points[2:]:
        boss = Part.makeCylinder(
            boss_radius, height, App.Vector(point.x, point.y, z_lo),
            App.Vector(0, 0, 1),
        )
        reach = math.hypot(point.x, point.y)
        az = math.degrees(math.atan2(point.y, point.x))
        body = body.fuse(boss).fuse(
            kit.arm(reach, boss_radius, height, z_lo, az)
        )
    return body.removeSplitter()


def bolt_reach(bolt_azimuths, azimuths, boss_r, channel_r, wall, reach_back):
    """How far out a stack-bolt group must sit to miss every rod channel.

    An arm is a RAY, not a line: the rods END at the hub and there is nothing
    on the far side. Treating them as lines -- which the first version did,
    copying the node, where every rod does pass through -- makes a bolt sitting
    nearly opposite an arm look blocked by it, and the offset needed to "clear"
    a phantom ran to 247 mm. The tail then reached out that far and the bottom
    plate came out 311 mm across.

    But the ray is not the whole story either, and the slot used to hide that.
    Every channel is cut `reach_back` past the hub centre, so a bow end pushed
    home bottoms out on material rather than on air; that stub is real, and the
    bolt at 215 deg sits 2.4 deg off the line of the arm at 37.4 -- squarely
    behind it. While the slot was there it forced the bolts out to 34.9 mm and
    the question never came up. With the slot gone, nothing else would have
    kept them off the stub.

    So each bolt clears each channel whichever of the two ways is cheaper: past
    its flank, or past the blunt end of the stub behind it.
    """
    want = 0.0
    for b in bolt_azimuths:
        for a in azimuths:
            separation = abs((b - a + 180.0) % 360.0 - 180.0)
            if separation < 90.0:                    # in front: the arm itself
                sideways = math.sin(math.radians(separation))
                want = max(want, (boss_r + channel_r) / max(sideways, 1e-6))
                continue
            behind = 180.0 - separation              # the stub, reach_back long
            sideways = math.sin(math.radians(behind))
            endwise = math.cos(math.radians(behind))
            ways = [(boss_r + channel_r) / max(sideways, 1e-6)]
            if endwise > 1e-6:
                ways.append((reach_back + boss_r + wall) / endwise)
            want = max(want, min(ways))
    return want


def build(values, fan_gaps=None):
    # The bolt, the pin and the wall come from the rod unless somebody
    # typed them in; see kit.scale_to_rod.
    chosen = kit.scale_to_rod(values)
    gaps = list(fan_gaps or DEFAULT_FAN_GAPS)
    if not 1 <= len(gaps) <= 2:
        raise ValueError(
            f"a base fan has one gap or two, got {len(gaps)}: {gaps}. "
            "Three bow ends at a plain foot, two where a doorway cut took "
            "one away; anything else is a different joint."
        )
    azimuths = kit.azimuths_from_gaps(gaps, values["firstArmRise"])

    rod_d = values["rodDiameter"]
    channel_r = rod_d / 2.0 + values["rodClearance"] / 2.0
    wall = values["minimumWall"]

    # The empty sector is where everything that is not a rod has to go.
    sector_start, sector_size = empty_sector(azimuths)

    # The stake is DRIVEN, so it is vertical. Nothing else about it is
    # negotiable: you hammer it into the ground, and the ground is down.
    #
    # The part is drawn in the frame it stands in: arm azimuths ARE their
    # rises above horizontal, so +X is horizontal, -Y is straight down, and a
    # Top view shows the hub as it sits on the ground.
    #
    # An earlier version put the stake on the middle of the widest gap between
    # arms, which gave it the most room and had it entering the earth 32 deg
    # off plumb. Room is worth having; plumb is worth more.
    stake_azimuth = 270.0

    boss_r = values["fastenerHeadDiameter"] / 2.0 + wall
    hub_r = values["hubRadiusFactor"] * rod_d
    arm_w = values["armWidthFactor"] * boss_r * 2.0
    arm_len = values["rodEngagement"] + values["channelOverrun"]

    length = arm_len
    reach_back = hub_r
    tilt_slack = (length / 2.0) * math.tan(math.radians(values["tiltAllowance"]))

    arm_count = len(azimuths)
    pitch = rod_d + values["rodGap"]
    levels = [(k - (arm_count - 1) / 2.0) * pitch for k in range(arm_count)]

    # The floor under the lowest channel and the cap over the highest, and
    # nothing else. The base plate used to carry the stake slot's 31 mm band
    # as well -- across the whole plate, because a plate is one thickness --
    # which is where 258 of the hub's 431 cm3 went.
    z_bottom = levels[0] - channel_r - tilt_slack - values["baseFloor"]
    z_top = levels[-1] + channel_r + tilt_slack + values["capThickness"]

    # Two bolts below the hub and two in the upper bow sector. Each must clear
    # the channel and its wall in every plate.
    bolt_spread = min(sector_size / 2.0 - 12.0, 55.0)
    lower_bolt_azimuths = [stake_azimuth - bolt_spread,
                           stake_azimuth + bolt_spread]
    if len(azimuths) == 3:
        upper_bolt_azimuths = [
            (left + right) / 2.0 for left, right in zip(azimuths, azimuths[1:])
        ]
    else:
        # A doorway foot has one bow gap. Put the pair just outside its two
        # arms so it still has four stack bolts without overlapping bosses.
        half_gap = gaps[0] / 2.0
        upper_bolt_azimuths = [azimuths[0] - half_gap,
                               azimuths[-1] + half_gap]
    bolt_azimuths = lower_bolt_azimuths + upper_bolt_azimuths
    bolt_offset = bolt_reach(
        lower_bolt_azimuths, azimuths, boss_r, channel_r, wall, reach_back
    )
    upper_bolt_offset = bolt_reach(
        upper_bolt_azimuths, azimuths, boss_r, channel_r, wall, reach_back
    )

    bolt_points = [
        App.Vector(
            kit.direction(az).x * reach, kit.direction(az).y * reach, 0.0
        )
        for az, reach in zip(bolt_azimuths,
                             [bolt_offset] * 2 + [upper_bolt_offset] * 2)
    ]

    # --- where the stake is met ---------------------------------------------
    #
    # On the bottom plate's outer face, straight down from the hub: a flat pad
    # the rebar lies against, and two bolts through it that pull the cradle
    # round the far side. The pad was drawn for the angle and has not changed
    # for the bar: it is a flat face and two holes, and that is all a bar
    # needs from it too.
    #
    # The face is the one the plate is printed on, and that is not a detail --
    # it is the whole reason the pad is on this side and this way up. Material
    # on the far side of the bar would have to hang below that face, and on
    # an FDM bed that is below the bed. So the plate offers a flat face and two
    # holes, and everything that goes round the other three sides is a SEPARATE
    # piece -- which is printed in its own orientation and is therefore allowed
    # to be the shape the joint actually wants.
    stake_size, stake_bolt = kit.fastener_for_clearance(
        values["stakeBoltDiameter"]
    )
    stake_span = values["stakeBoltSpan"]
    stake_r = (values["stakeBoltDiameter"] + values["boltHoleClearance"]) / 2.0
    washer_r = stake_bolt["washer"] / 2.0
    lug_w = values["stakeLugWidth"] or (
        stake_span + 2.0 * (values["stakeBoltDiameter"] + wall)
    )
    lug_thick = max(
        values["stakeLugThickness"] or (stake_bolt["nut_depth"] + wall),
        levels[0] - z_bottom,
    )

    # How far down the pad the pair sits. Their nuts are captive in the pad's
    # far face, in the same band as the next plate up, so the pockets have to
    # miss that plate's bolt bosses -- which is what sets this, not the hub's
    # own radius.
    stake_at = values["stakeBoltAt"] or (hub_r + washer_r + wall)
    keep_off = boss_r + washer_r + 1.0
    for point in bolt_points[:2]:
        sideways = abs(abs(point.x) - stake_span / 2.0)
        if sideways < keep_off:
            stake_at = max(
                stake_at,
                abs(point.y) + math.sqrt(keep_off ** 2 - sideways ** 2),
            )
    stake_reach = stake_at + washer_r + wall
    pad_top = z_bottom + lug_thick
    stake_points = [
        App.Vector(sign * stake_span / 2.0, -stake_at, 0.0)
        for sign in (-1.0, 1.0)
    ]

    shank_r = (values["fastenerDiameter"] + values["boltHoleClearance"]) / 2.0
    head_r = (values["fastenerHeadDiameter"] + values["headClearance"]) / 2.0

    # Drawn well past the arm so the three directions read at a glance. The
    # channels stay at the working length; only the rods are long.
    ref_len = max(length, values["refRodLength"])
    rods = [
        kit.rod_from_hub(rod_d / 2.0, ref_len, azimuths[k], levels[k], reach_back)
        for k in range(arm_count)
    ]
    channels = [
        rod_channel(
            channel_r, length, azimuths[k], levels[k],
            values["tiltAllowance"], reach_back,
        )
        for k in range(arm_count)
    ]

    # A cross pin per arm, through the arm's width and the rod with it. With a
    # slide fit the channel no longer grips anything, and a bow end that is
    # merely located can walk out of its own accord.
    pins = []
    for k in range(arm_count):
        along = kit.direction(azimuths[k]).multiply(values["rodPinAt"])
        across = kit.direction(azimuths[k] + 90.0)
        span = arm_w + 8.0
        pins.append(
            Part.makeCylinder(
                values["rodPinDiameter"] / 2.0,
                span,
                App.Vector(
                    along.x - across.x * span / 2.0,
                    along.y - across.y * span / 2.0,
                    levels[k],
                ),
                across,
            )
        )

    bolt_height = (z_top + 2.0) - (z_bottom - 2.0)
    bolts = [
        Part.makeCylinder(
            shank_r, bolt_height, App.Vector(p.x, p.y, z_bottom - 2.0),
            App.Vector(0, 0, 1),
        )
        for p in bolt_points
    ]

    # The pad. A flat spar straight down from the hub, in the bottom plate's
    # own band -- it carries two holes and a face and nothing else, so it has
    # no reason to be thicker than the plate it grows from. If somebody asks
    # for a thicker one anyway, the part of it that stands above the plate has
    # to keep out of every other plate's way, and it is cut to shape by the
    # neighbours themselves rather than by a clearance somebody guessed.
    pad = kit.arm(stake_reach, lug_w, lug_thick, z_bottom, stake_azimuth)
    if pad_top > levels[0] + 1e-9:
        room = 1.0
        pad = pad.cut(
            plate_blank(
                hub_r + room, arm_len + room, arm_w + 2.0 * room, boss_r + room,
                levels[0], pad_top + 1.0, azimuths, bolt_points,
            )
        )
    pad = pad.removeSplitter()

    # The two bolts that pull the cradle on, and the nuts they land in. The
    # pockets open on the pad's far face -- which is the face pointing UP while
    # the bottom plate is printed, so they need no cone and no support, and the
    # nut is dropped in from outside once and turned never.
    stake_holes = []
    for p in stake_points:
        stake_holes.append(
            Part.makeCylinder(
                stake_r, lug_thick + 4.0,
                App.Vector(p.x, p.y, z_bottom - 2.0), App.Vector(0, 0, 1),
            )
        )
        stake_holes.append(
            kit.hex_prism(
                stake_bolt["nut_af"], stake_bolt["nut_depth"] + 1.0,
                App.Vector(p.x, p.y, pad_top - stake_bolt["nut_depth"]),
            )
        )

    # The nut pocket and the head counterbore for the four stack bolts. Both
    # open onto the face their plate is printed on -- the bottom plate's outer
    # face is its bed, and so is the cap's, because the cap prints flipped so
    # its channel faces up. Each gets a cone up to the shank, because the step
    # from a pocket to a hole is otherwise a flat ceiling, and a flat ceiling
    # is the one thing an FDM machine cannot do at all.
    nut_af = values["nutAcrossFlats"]
    nut_circum_stack = nut_af / math.sqrt(3.0)

    def nut_pockets():
        cuts = []
        for p in bolt_points:
            cuts.append(
                kit.hex_prism(
                    nut_af, values["nutRecessDepth"] + 1.0,
                    App.Vector(p.x, p.y, z_bottom - 1.0),
                )
            )
            cuts.append(
                Part.makeCone(
                    nut_circum_stack, shank_r, values["nutConeHeight"],
                    App.Vector(p.x, p.y, z_bottom + values["nutRecessDepth"]),
                    App.Vector(0, 0, 1),
                )
            )
        return cuts

    def head_bores():
        cuts = []
        for p in bolt_points:
            cuts.append(
                Part.makeCylinder(
                    head_r, values["headBoreDepth"] + 1.0,
                    App.Vector(p.x, p.y, z_top - values["headBoreDepth"]),
                    App.Vector(0, 0, 1),
                )
            )
            cuts.append(
                Part.makeCone(
                    shank_r, head_r, values["headConeHeight"],
                    App.Vector(
                        p.x, p.y,
                        z_top - values["headBoreDepth"] - values["headConeHeight"],
                    ),
                    App.Vector(0, 0, 1),
                )
            )
        return cuts

    names = plate_names(arm_count)
    plates = []
    for i in range(len(names)):
        z_lo = z_bottom if i == 0 else levels[i - 1]
        z_hi = z_top if i == len(names) - 1 else levels[i]
        blank = plate_blank(
            hub_r, arm_len, arm_w, boss_r, z_lo, z_hi, azimuths, bolt_points,
        )
        if i == 0:
            blank = blank.fuse(pad).removeSplitter()
        solid = blank
        for ch in channels:
            solid = solid.cut(ch)
        for bolt in bolts:
            solid = solid.cut(bolt)
        for pin in pins:
            solid = solid.cut(pin)
        if i == 0:
            for hole in stake_holes:
                solid = solid.cut(hole)
            for cut in nut_pockets():
                solid = solid.cut(cut)
        if i == len(names) - 1:
            for cut in head_bores():
                solid = solid.cut(cut)
        solid = solid.removeSplitter()
        if not kit.has_volume(solid):
            raise RuntimeError(f"plate {names[i]} came out invalid")
        plates.append(solid)

    # The rebar itself, drawn where it is driven: standing on the pad's face,
    # mostly in the ground, and `stakeStandProud` of it above the foot. That
    # last part is the interesting one -- it runs up PAST the hub, along the
    # bottom plate's outer face, and what it has to miss up there is the whole
    # part. So it is drawn over all of that length rather than stopping at the
    # pad, and `verify` asks whether it touches anything.
    proud = values["stakeStandProud"]
    bar_r = values["stakeRebarDiameter"] / 2.0
    stake = driven_rebar(
        bar_r, z_bottom, -(values["stakeLength"] - proud), proud,
    )

    # The cradle, and the two holes through it. It is the fifth print of the
    # hub, drawn seated on the reference bar; on any other bar in the range
    # it sits nearer the pad or further off, and the bolts take up the rest.
    half_vee = values["stakeVeeAngle"] / 2.0
    vee_deep, gap_widest, contact_widest = vee_depth(
        half_vee, values["stakeRebarMin"] / 2.0, values["stakeRebarMax"] / 2.0,
        values["stakeCradleGap"],
    )
    z_apex = z_bottom - bar_r - bar_r / math.sin(math.radians(half_vee))
    cradle = stake_cradle(
        stake_span, stake_r, wall, half_vee, vee_deep,
        values["stakeCradleLength"], z_apex, -stake_at,
    )
    cradle_deep = vee_deep + wall
    for p in stake_points:
        cradle = cradle.cut(
            Part.makeCylinder(
                stake_r, cradle_deep + 4.0,
                App.Vector(p.x, p.y, z_apex - wall - 2.0),
                App.Vector(0, 0, 1),
            )
        )
    cradle = cradle.removeSplitter()
    if not kit.ok(cradle):
        raise RuntimeError("the stake cradle came out invalid")
    # One bolt length for the whole range: long enough to take a full nut on
    # the thickest bar, and on the thinnest what is left over stands up the
    # nut's own access column, which verify keeps clear.
    bolt_needed = cradle_deep + gap_widest + lug_thick
    bolt_spare = z_top - pad_top
    # It is a print of this hub like any other, so it travels with them: five
    # pieces per hub, four plates and the cradle.
    names = names + ["Cradle"]
    plates = plates + [cradle]

    # A keep-out around each rod: the channel plus a wall, over the length the
    # part actually holds it. Nothing may be cut out of this.
    keepouts = [
        Part.makeCylinder(
            channel_r + wall,
            arm_len,
            App.Vector(0.0, 0.0, levels[k]),
            kit.direction(azimuths[k]),
        )
        for k in range(arm_count)
    ]

    geo = {
        "plates": plates,
        "names": names,
        "rods": rods,
        "channels": channels,
        "keepouts": keepouts,
        # A ring of material that must exist round each bolt in every plate.
        "bolt_probes": [
            Part.makeCylinder(
                boss_r, z_top - z_bottom,
                App.Vector(p.x, p.y, z_bottom), App.Vector(0, 0, 1),
            ).cut(
                Part.makeCylinder(
                    shank_r + 0.01, z_top - z_bottom + 2.0,
                    App.Vector(p.x, p.y, z_bottom - 1.0), App.Vector(0, 0, 1),
                )
            )
            for p in bolt_points
        ],
        # The same probe for each stake bolt: a ring of pad that has to be
        # there round the hole, or the bolt comes up through air.
        "stake_probes": [
            Part.makeCylinder(
                washer_r + wall, lug_thick,
                App.Vector(p.x, p.y, z_bottom), App.Vector(0, 0, 1),
            ).cut(
                Part.makeCylinder(
                    stake_r + 0.01, lug_thick + 2.0,
                    App.Vector(p.x, p.y, z_bottom - 1.0), App.Vector(0, 0, 1),
                )
            )
            for p in stake_points
        ],
        "stake_cuts": list(stake_holes),
        # Each nut is dropped into its pocket from outside, and a bolt has to
        # be started into it. What must be empty is the column above it.
        "nut_access": [
            Part.makeCylinder(
                washer_r, z_top - pad_top,
                App.Vector(p.x, p.y, pad_top), App.Vector(0, 0, 1),
            )
            for p in stake_points
        ],
        "pad": pad,
        "stake": stake,
        "cradle": cradle,
    }
    dims = {
        "chosen_from_rod": chosen,
        "fan_gaps_deg": gaps,
        "arm_azimuths_deg": azimuths,
        "fan_spread_deg": azimuths[-1] - azimuths[0],
        "empty_sector_deg": sector_size,
        "stake_azimuth_deg": stake_azimuth,
        "bolt_azimuths_deg": bolt_azimuths,
        "bolt_offset_mm": bolt_offset,
        "upper_bolt_offset_mm": upper_bolt_offset,
        "rod_levels_mm": levels,
        "pitch_mm": pitch,
        "hub_radius_mm": hub_r,
        "arm_length_mm": arm_len,
        "ref_rod_length_mm": ref_len,
        "arm_width_mm": arm_w,
        "stake_reach_mm": stake_reach,
        "first_arm_rise_deg": values["firstArmRise"],
        "stake_rebar_mm": values["stakeRebarDiameter"],
        "stake_rebar_min_mm": values["stakeRebarMin"],
        "stake_rebar_max_mm": values["stakeRebarMax"],
        "stake_bolt_at_mm": stake_at,
        "stake_bolt_size": stake_size,
        "stake_bolt_mm": values["stakeBoltDiameter"],
        "stake_bolt_span_mm": stake_span,
        "stake_bolt_length_mm": bolt_needed,
        "stake_bolt_spare_mm": bolt_spare,
        "stake_bolt_bearing_mm": lug_thick - stake_bolt["nut_depth"],
        "cradle_width_mm": 2.0 * (stake_span / 2.0 + stake_r + wall),
        "cradle_length_mm": values["stakeCradleLength"],
        "cradle_depth_mm": cradle_deep,
        "vee_angle_deg": values["stakeVeeAngle"],
        "vee_depth_mm": vee_deep,
        "cradle_gap_min_mm": values["stakeCradleGap"],
        "cradle_gap_max_mm": gap_widest,
        "vee_contact_max_mm": contact_widest,
        "stake_nut_af_mm": stake_bolt["nut_af"],
        "stake_offset_mm": abs(z_bottom) + bar_r,
        "stake_stand_proud_mm": proud,
        "lug_width_mm": lug_w,
        "lug_thickness_mm": lug_thick,
        "stack_bolt_length_mm": (
            (z_top - values["headBoreDepth"]) - z_bottom
            + values["nutRecessDepth"]
        ),
        "z_bottom_mm": z_bottom,
        "z_top_mm": z_top,
        "stack_height_mm": z_top - z_bottom,
        "plate_count": len(plates),
    }
    return geo, dims


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
def verify(geo, dims, values):
    """Checks that would have caught the mistakes V1 of the fan node made."""
    problems = []
    plates = geo["plates"]

    for name, plate in zip(geo["names"], plates):
        if not kit.ok(plate):
            problems.append(f"{name}: not one valid solid")

    # No plate may eat into a rod.
    interference = 0.0
    for name, plate in zip(geo["names"], plates):
        for i, rod in enumerate(geo["rods"]):
            common = plate.common(rod)
            v = kit.vol(common)
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
        engaged.append(kit.has_volume(below) and kit.has_volume(above))
    if not all(engaged):
        problems.append(f"rods not enclosed by a pair of plates: {engaged}")

    # The stack must not be taller than the rods are apart times their count,
    # plus the floor and cap -- a sanity bound that catches a runaway pitch.
    # It used to carry the slot band as well, which is 31 mm of it gone.
    bound = (
        dims["pitch_mm"] * 3
        + values["baseFloor"]
        + values["capThickness"]
        + values["minimumWall"]
        + 8.0
    )
    if dims["stack_height_mm"] > bound:
        problems.append(
            f"stack is {dims['stack_height_mm']:.1f} mm, expected under {bound:.1f}"
        )

    # The bar passes the hub rather than through it, and that claim is
    # the one thing about this design that could quietly stop being true: it is
    # drawn over its whole standing length, and it must touch nothing. A face
    # to face contact on the pad is not a touch -- it has no volume.
    if geo.get("stake") is not None:
        for name, plate in zip(geo["names"], plates):
            if name == "Cradle":
                continue      # the one piece that is meant to be against it
            v = kit.vol(plate.common(geo["stake"]))
            if v > 0.5:
                problems.append(
                    f"{name} is in the bar's way by {v:.1f} mm3 -- it has "
                    f"{dims['stake_stand_proud_mm']:.0f} mm to stand proud in"
                )

    # Every bolt has to pass through material, in every plate of the STACK --
    # the cradle is not one of them and has its own two bolts. Cutting a hole
    # through open air leaves the stack with nothing holding it together, and
    # it looks exactly the same in a render.
    for name, plate in zip(geo["names"], plates):
        if name == "Cradle":
            continue
        for i, probe in enumerate(geo.get("bolt_probes", [])):
            v = kit.vol(plate.common(probe))
            if v < 1.0:
                problems.append(
                    f"{name} has no material round bolt {i + 1}: the hole is "
                    "cut through air"
                )

    # And the same for both legs of the loop that holds the whole dome down.
    for i, probe in enumerate(geo.get("stake_probes", [])):
        v = kit.vol(plates[0].common(probe))
        if v < 1.0:
            problems.append(
                f"stake bolt {i + 1} has no pad round it: the hole is "
                "cut through air"
            )

    # Its nuts stand on the pad's far face, in the band the next plate up
    # lives in. Nothing may be standing where a spanner has to be.
    for i, access in enumerate(geo.get("nut_access", [])):
        for name, plate in zip(geo["names"][1:], plates[1:]):
            v = kit.vol(plate.common(access))
            if v > 0.5:
                problems.append(
                    f"{name} stands over stake nut {i + 1} by "
                    f"{v:.1f} mm3: there is nowhere to put a spanner"
                )

    # The cradle closes the pad into a ring round the bar, and that is the
    # whole claim. On the reference bar it must touch and not cut; on every
    # bar in the range its rim must stop short of the pad, or the bolts clamp
    # plastic to plastic with the bar loose inside. vee_depth builds it that
    # way and raises if the thickest bar would ride the mouth; this re-asks it
    # of the numbers that came out.
    cradle = geo.get("cradle")
    if cradle is not None:
        if geo.get("stake") is not None:
            v = kit.vol(cradle.common(geo["stake"]))
            if v > 0.5:
                problems.append(
                    f"the cradle cuts into the bar by {v:.1f} mm3"
                )
        for name, plate in zip(geo["names"], plates):
            if name == "Cradle":
                continue
            v = kit.vol(plate.common(cradle))
            if v > 0.5:
                problems.append(f"the cradle runs into {name} by {v:.1f} mm3")
        for i, rod in enumerate(geo["rods"]):
            v = kit.vol(cradle.common(rod))
            if v > 0.5:
                problems.append(f"the cradle runs into rod {i + 1} by {v:.1f} mm3")
        if dims["cradle_gap_min_mm"] <= 0.0:
            problems.append(
                "on the thinnest bar the cradle's rim lands on the pad: the "
                "bolts clamp the plate, not the bar"
            )
        # One bolt length for the range: what the thinnest bar leaves over
        # stands up the nut's access column, and must not run out of it.
        bolt = 5 * math.ceil(dims["stake_bolt_length_mm"] / 5.0)
        proud_of_nut = bolt - (
            dims["stake_bolt_length_mm"]
            - dims["cradle_gap_max_mm"] + dims["cradle_gap_min_mm"]
        )
        if proud_of_nut > dims["stake_bolt_spare_mm"]:
            problems.append(
                f"on the thinnest bar an M{dims['stake_bolt_size']:g} x "
                f"{bolt:g} stands {proud_of_nut:.1f} mm up past its nut, and "
                f"there is {dims['stake_bolt_spare_mm']:.1f} mm to stand into"
            )

    # Nothing cut for the stake may take the wall out from under a rod.
    for cut in geo.get("stake_cuts", []):
        for i, keepout in enumerate(geo.get("keepouts", [])):
            v = kit.vol(cut.common(keepout))
            if v > 1.0:
                problems.append(
                    f"a stake bolt hole cuts {v:.1f} mm3 out of the wall around "
                    f"rod {i + 1}"
                )

    # The pad has to be in the empty sector, not under an arm.
    for az in dims["arm_azimuths_deg"]:
        separation = abs(
            (dims["stake_azimuth_deg"] - az + 180.0) % 360.0 - 180.0
        )
        if separation < 30.0:
            problems.append(
                f"the stake pad at {dims['stake_azimuth_deg']:.1f} deg is only "
                f"{separation:.1f} deg from the arm at {az:.1f}"
            )

    # No two plates may occupy the same place. Nothing checked this while every
    # plate was one flat slab; the pad is the first feature that stands off its
    # own plate and into the next one's band, so it is the first that could.
    for (name_a, a), (name_b, b) in itertools.combinations(
        list(zip(geo["names"], plates)), 2
    ):
        v = kit.vol(a.common(b))
        if v > 0.5:
            problems.append(f"{name_a} and {name_b} overlap by {v:.1f} mm3")

    # The bolts pull rather than bear, so what the pad owes them is a floor
    # under each captive nut -- and that floor is what the whole clamp reacts
    # against.
    if dims["stake_bolt_bearing_mm"] < values["minimumWall"] - 1e-6:
        problems.append(
            f"only {dims['stake_bolt_bearing_mm']:.1f} mm of pad is left under "
            f"the stake nuts, wanted {values['minimumWall']:.1f}"
        )

    # The cap prints flipped so its channel faces up; every other piece prints
    # with its upward channel up. Same convention as the four-rod node, and
    # the same set the print sheet lays out from -- see FLIPPED_PIECES.
    printability = {
        name: kit.printability(plate, flipped=(name in FLIPPED_PIECES))
        for name, plate in zip(geo["names"], plates)
    }

    return {
        "problems": problems,
        "ok": not problems,
        "printability": printability,
        "rod_interference_mm3": round(interference, 2),
        "plate_volumes_mm3": [round(kit.vol(p), 1) for p in plates],
        "stack_height_mm": round(dims["stack_height_mm"], 2),
        "arm_azimuths_deg": [round(a, 4) for a in dims["arm_azimuths_deg"]],
        "stake_azimuth_deg": round(dims["stake_azimuth_deg"], 4),
        "empty_sector_deg": round(dims["empty_sector_deg"], 4),
    }


def derived_rows(dims, values):
    return [
        (
            "fastenerChosen",
            dims["chosen_from_rod"].get("fastenerSize", 0),
            "M",
            "which metric bolt this part was drawn for. Chosen from the rod "
            "unless fastenerSize said otherwise -- half the rod, snapped",
        ),
        ("fanSpread", round(dims["fan_spread_deg"], 4), "deg",
         "angle from the lowest arm to the highest"),
        ("emptySector", round(dims["empty_sector_deg"], 4), "deg",
         "the sector with no arm; the stake pad and lower stack bolts live here"),
        ("stakeAzimuth", round(dims["stake_azimuth_deg"], 4), "deg",
         "where the pad reaches for the bar; straight down once installed"),
        ("boltOffset", round(dims["bolt_offset_mm"], 3), "mm",
         "how far out the lower stack-bolt pair sits"),
        ("upperBoltOffset", round(dims["upper_bolt_offset_mm"], 3), "mm",
         "how far out the added upper pair sits between the bow arms"),
        ("stackHeight", round(dims["stack_height_mm"], 3), "mm",
         "bottom of the base plate to top of the cap"),
        ("armLength", round(dims["arm_length_mm"], 3), "mm",
         "hub centre to the end of an arm"),
        ("refRodDrawn", round(dims["ref_rod_length_mm"], 1), "mm",
         "length of each reference rod; drawing only"),
        ("stakeRebar",
         f"{dims['stake_rebar_min_mm']:g} to {dims['stake_rebar_max_mm']:g}",
         "mm", "any driven rebar in this range, the smaller across its core and "
         "the larger across its ribs. One cradle takes all of it"),
        ("stakePlumb", "vertical", "-",
         "the stake axis is straight down once installed; that is what "
         "firstArmRise is for"),
        ("padReach", round(dims["stake_reach_mm"], 2), "mm",
         "hub centre to the end of the pad, straight down"),
        ("padSize", f"{dims['lug_width_mm']:g} x {dims['lug_thickness_mm']:g}",
         "mm", "across the pad and through it"),
        ("stakeBoltAt", round(dims["stake_bolt_at_mm"], 2), "mm",
         "how far down the pad the two bolts sit"),
        ("stakeBolt",
         f"M{dims['stake_bolt_size']:g} x "
         f"{5 * math.ceil(dims['stake_bolt_length_mm'] / 5.0):g}, two of", "-",
         "head and washer under the cradle, nut captive in the pad. Long "
         "enough for the thickest bar; on a thinner one the spare stands up "
         "the nut's access column. The same pair of holes takes an "
         f"M{dims['stake_bolt_size']:g} U-bolt of "
         f"{dims['stake_bolt_span_mm']:g} mm span instead -- decision 0026"),
        ("cradleSize",
         f"{dims['cradle_width_mm']:g} x {dims['cradle_length_mm']:g} x "
         f"{dims['cradle_depth_mm']:.1f}", "mm",
         "the fifth print of the hub: across, along the bar, and deep"),
        ("cradleVee",
         f"{dims['vee_angle_deg']:g} deg, {dims['vee_depth_mm']:.2f} deep", "-",
         "a round bar touches both flanks at any diameter, and the pad is the "
         "third side: three lines of contact on every bar in the range"),
        ("cradleGap",
         f"{dims['cradle_gap_min_mm']:.1f} to {dims['cradle_gap_max_mm']:.1f}",
         "mm", "how far the rim stands off the pad, thinnest bar to thickest. "
         "Never zero, so the bolts always pull on the steel"),
        ("stakeGrip", "friction", "-",
         "the cradle clamps rather than bears, so the hub sits at whatever "
         "height the ground gave the bar -- and the two bolts want checking "
         "after the first night, because plastic under a preload creeps"),
        ("stakeBoltBearing", round(dims["stake_bolt_bearing_mm"], 2), "mm",
         "pad left under each nut pocket. At 20 m/s the ground takes 154 N of "
         "uplift per foot, and this joint is in clamp, not in bearing"),
        ("stakeStandProud", round(dims["stake_stand_proud_mm"], 1), "mm",
         "leave this much of the bar above the foot: it clears the hub over "
         "all of it, and the cover's loop drops over what is left"),
        ("stakeOffset", round(dims["stake_offset_mm"], 2), "mm",
         "how far the bar's axis sits inboard of the bow bundle. It is a "
         "moment, and it is the one the ground and the bar's own bending "
         "are best placed to take. Drawn for the reference bar"),
        ("stackBolt",
         f"M{dims['chosen_from_rod'].get('fastenerSize', 0):g} x "
         f"{math.ceil(dims['stack_bolt_length_mm'] / 5.0) * 5:g}", "-",
         "four that hold the plates together: head and washer down the "
         "cap's counterbore, nut captive in the bottom plate"),
        ("plateCount", dims["plate_count"], "-",
         "prints per hub: the plates of the stack, plus the cradle"),
        ("rodFit", f"slide, {values['rodClearance']:g} mm", "-",
         "bolt the stack up first, then push the bow ends in and pin them"),
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
# The cradle is printed like the plates and belongs to the same family, but it
# is not in the stack, so it is the ramp's colour warmed up rather than the
# next step of it.
CRADLE_COLOUR = (0.90, 0.78, 0.45)


def populate(doc, geo):
    # Everything except the parameter sheet, which run() still holds a handle
    # to and writes after this.
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
        if obj.Name == "Plate_Cradle":
            view.ShapeColor = CRADLE_COLOUR
            view.Transparency = 0
        elif obj.Name.startswith("Plate_"):
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


def run(fan_gaps=None, out_dir=None, doc_path=None, rod_diameter=None):
    if doc_path and os.path.exists(doc_path):
        doc = App.openDocument(doc_path)
    elif DOC_NAME in App.listDocuments():
        doc = App.getDocument(DOC_NAME)
    else:
        doc = App.newDocument(DOC_NAME)
    sheet, values = kit.read_or_build_parameters(doc, INPUTS, USE_SPREADSHEET_IF_PRESENT)
    if rod_diameter:
        values["rodDiameter"] = float(rod_diameter)
    geo, dims = build(values, fan_gaps)
    report = verify(geo, dims, values)
    populate(doc, geo)
    apply_view(doc)
    kit.write_parameters(doc, sheet, INPUTS, values, derived_rows(dims, values), TITLE)
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
