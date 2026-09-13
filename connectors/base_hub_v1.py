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
is where the driven steel angle has to be met, and it is not a preference: the
one direction a foot has no room in is straight up. Vertical out of the hub is
azimuth 90, the U arm sits at 79.19, and a rod is 5.7 mm across with a wall
round it -- so the vertical line is inside that arm for its first 67 mm. Above
a foot there is nothing but bows. Below it there is nothing at all.

THE ANGLE IS MET ON A FLAT PAD AND A BOUGHT LOOP

V1 ran the angle through an L-section slot cut clean across the base plate.
It held, and it charged for it three times:

    the plate     46.8 mm thick over all 104 x 113 mm of it, because the slot
                  band and the floor under it are added to the WHOLE plate --
                  258 cm3 of the hub's 431, and the base hubs were 59% of
                  the dome's plastic (docs/bom.md)
    the print     2643 mm2 of flat slot roof at 0 deg of overhang, the worst
                  face in the kit and the one docs/roadmap.md names
    the fit       100 mm of slot that a driven angle must be straight and
                  untwisted along before the hub will go on at all

None of that is what the slot was FOR. It was for three things: hold the hub
down on the angle, let it find its own height whatever depth the ground gave,
and let the angle stand proud above the foot for the cover's loops to drop
over (decision 0014).

What does all three, and one more, is a **flat pad and a U-bolt over it**:

    down          the loop clamps. Per foot at 20 m/s the ground takes 154 N
                  of uplift and 188 N of shear (`make loads`), and two nuts
                  on an M8 loop hold that with the preload to spare -- see
                  what it costs, below, because this is friction and friction
                  in plastic creeps
    height        ANY. Nothing is drilled, nothing is indexed, nothing has to
                  line up: hard ground that stops the angle 40 mm short is a
                  loop done up 40 mm further down it
    twist         the pad is flat and the loop is round, so an angle a few
                  degrees out of square beds down instead of jamming
    size          the loop takes any leg up to what `stakeUBoltFits` reports
                  -- 35.1 mm on the 50 mm loop this is drawn with. The part is
                  drawn round L30 and holds L25 or L35 exactly as well,
                  because the section it grips is not a dimension of the
                  printed part at all

That last one is the reason it is a bought loop rather than a printed socket
or a printed vee. A 90 deg vee looks like the obvious way to cradle an angle
and is not size-agnostic at all: a 90 deg corner and a 90 deg vee have
PARALLEL faces, so they touch only when the corner reaches the apex. One vee
holds exactly one leg width, and anything smaller rattles in it.

The angle passes the hub as it always did -- it just passes BESIDE it now,
inboard of the bottom plate's outer face, where the whole half-space is empty,
instead of through a hole in the middle of it.

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

FIELD SEQUENCE

    at home   bolt the four plates up: two bolts, nut captive in the bottom
              plate, head and washer down a counterbore in the cap. One tool,
              one end, and nothing to hold on the other side
    at the    drive the angle -> lay the hub's pad against it -> drop the
    dome      U-bolt over the angle and through the pad, two nuts -> push
              each bow end into its channel -> pin it

Note the order. The four-rod node has to be opened, a rod laid, a plate
closed, the next rod laid, and so on, because it CLAMPS its rods. This one
does not: the channels are a slide fit, so the stack is assembled once, on the
ground or at home, and the bow ends go in afterwards. That is a much better
thing to be doing in a field with cold hands.

The price of a slide fit is that the channel locates the rod and holds it
against nothing, so each arm carries a cross pin through arm and rod together.

THE STACK'S NUTS ARE CAPTIVE; THE LOOP'S TWO ARE NOT

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

The U-bolt is the exception and cannot be anything else: it is threaded at
both ends and has no head to hold, so its two nuts are turned, with a washer
each, on the pad's far face. They are the only loose fasteners at a foot.

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
    ("stakeLegWidth",         30.0,  "mm",  "each leg of the driven steel angle, across"),
    ("stakeThickness",         3.0,  "mm",  "the angle's material thickness"),
    ("stakeLength",          500.0,  "mm",  "how long the angle is; drawing only, and it is mostly in the ground"),
    ("stakeStandProud",      120.0,  "mm",  "how much of the angle is left above the foot once it is driven. Drawing only, but it is the field rule the reference solid checks: the angle has to clear the hub over all of it, and what stands above is what the cover's loop drops over -- decision 0014"),
    ("stakeUBoltDiameter",     8.5,  "mm",  "clearance hole for each leg of the U-bolt. 8.5 is M8"),
    ("stakeUBoltSpan",        50.0,  "mm",  "centre to centre of the U-bolt's two legs -- which is what decides the biggest angle it will go round, and the only number that has to be looked up when a different one is bought"),
    ("stakeUBoltAt",           0.0,  "mm",  "how far below the hub centre the U-bolt sits. 0 puts it as close in as its own nuts allow past the stack bolts, which is the shortest pad that works"),
    ("stakeUBoltClear",        3.0,  "mm",  "slack between the angle's section and the inside of the loop; what stops a 30 mm angle needing a 30 mm loop"),
    ("stakeLugWidth",          0.0,  "mm",  "across the pad. 0 takes it from the U-bolt: its span plus a hole and a wall either side"),
    ("stakeLugThickness",      0.0,  "mm",  "through the pad, and it is what the U-bolt's legs bear on. 0 takes the plate's own floor, which is already more than the load needs"),
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


def driven_angle(leg, thickness, seat_z, y_from, y_to):
    """The steel angle as it stands in the ground, in the part's own frame.

    Vertical, because you hammer it and the ground is down -- so it runs along
    Y, not along an azimuth. One leg lies flat against the pad's seating face
    at `seat_z` and is what the bolt goes through; the other drops away from it
    inboard, where the whole half-space below the bottom plate is empty.

    Which way that second leg points is free -- it meets nothing either way --
    and it is drawn inboard so that the section reads as the L it is rather
    than as a bar seen edge on.
    """
    across = Part.makeBox(
        leg, y_to - y_from, thickness,
        App.Vector(-leg / 2.0, y_from, seat_z - thickness),
    )
    down = Part.makeBox(
        thickness, y_to - y_from, leg,
        App.Vector(-leg / 2.0, y_from, seat_z - leg),
    )
    return across.fuse(down).removeSplitter()


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
    """Hub disc, one arm per rod, and a boss per bolt.

    The bosses are not decoration. The bolts sit 35 mm out on azimuths 55 deg
    either side of straight down and the hub disc reaches 22 mm -- so without
    them the bolt holes were cut through open air and the stack had nothing
    holding it together at all.

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
    for point in bolt_points:
        boss = Part.makeCylinder(
            boss_radius, height, App.Vector(point.x, point.y, z_lo),
            App.Vector(0, 0, 1),
        )
        # A web back to the hub, so the boss is carried rather than perched.
        reach = math.hypot(point.x, point.y)
        az = math.degrees(math.atan2(point.y, point.x))
        body = body.fuse(boss).fuse(
            kit.arm(reach, boss_radius, height, z_lo, az)
        )
    return body.removeSplitter()


def bolt_reach(bolt_azimuths, azimuths, boss_r, channel_r, wall, reach_back):
    """How far out the two stack bolts must sit to miss every rod channel.

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

    # Two bolts, one either side of straight down, far enough round that each
    # clears the nearest arm. fan_node_v2 puts them opposite each other, which
    # works for a fan that spans 180; three arms spanning 79 put the opposite
    # direction 2 deg from an arm, so they go side by side instead.
    bolt_spread = min(sector_size / 2.0 - 12.0, 55.0)
    bolt_azimuths = [stake_azimuth - bolt_spread, stake_azimuth + bolt_spread]
    bolt_offset = bolt_reach(
        bolt_azimuths, azimuths, boss_r, channel_r, wall, reach_back
    )

    bolt_points = [
        App.Vector(
            kit.direction(az).x * bolt_offset, kit.direction(az).y * bolt_offset, 0.0
        )
        for az in bolt_azimuths
    ]

    # --- where the angle is met ---------------------------------------------
    #
    # On the bottom plate's outer face, straight down from the hub: a flat pad
    # the angle's leg lies against, and a U-bolt over the whole section, both
    # legs of it through the pad and a nut on each.
    #
    # The face is the one the plate is printed on, and that is not a detail --
    # it is the whole reason the pad is on this side and this way up. Material
    # on the far side of the angle would have to hang below that face, and on
    # an FDM bed that is below the bed. So the part offers a flat face and two
    # holes, and everything that goes round the other three sides is a piece of
    # bent steel rod that costs nothing to print and does not care how big the
    # angle is.
    stake_size, stake_bolt = kit.fastener_for_clearance(
        values["stakeUBoltDiameter"]
    )
    u_span = values["stakeUBoltSpan"]
    u_r = (values["stakeUBoltDiameter"] + values["boltHoleClearance"]) / 2.0
    washer_r = stake_bolt["washer"] / 2.0
    lug_w = values["stakeLugWidth"] or (
        u_span + 2.0 * (values["stakeUBoltDiameter"] + wall)
    )
    lug_thick = max(values["stakeLugThickness"] or 0.0, levels[0] - z_bottom)

    # How far down the pad the loop sits. Its nuts stand on the pad's far face,
    # in the same band as the next plate up, so they have to miss that plate's
    # bolt bosses -- which is what sets this, not the hub's own radius.
    u_at = hub_r + washer_r + wall
    keep_off = boss_r + washer_r + 1.0
    for point in bolt_points:
        sideways = abs(abs(point.x) - u_span / 2.0)
        if sideways < keep_off:
            u_at = max(
                u_at,
                abs(point.y) + math.sqrt(keep_off ** 2 - sideways ** 2),
            )
    stake_reach = u_at + washer_r + wall
    pad_top = z_bottom + lug_thick
    u_points = [
        App.Vector(sign * u_span / 2.0, -u_at, 0.0) for sign in (-1.0, 1.0)
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

    # The two holes the U-bolt's legs come up through. Nothing else: the loop
    # is bought bent, the nuts land on the pad's far face, and the part has no
    # opinion about how big the angle inside the loop is.
    stake_holes = [
        Part.makeCylinder(
            u_r, lug_thick + 4.0,
            App.Vector(p.x, p.y, z_bottom - 2.0), App.Vector(0, 0, 1),
        )
        for p in u_points
    ]

    # The nut pocket and the head counterbore for the two stack bolts. Both
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

    # The angle itself, drawn where it is driven: standing on the pad's face,
    # mostly in the ground, and `stakeStandProud` of it above the foot. That
    # last part is the interesting one -- it runs up PAST the hub, on the
    # inboard side of the bottom plate, and what it has to miss up there is the
    # whole part. So it is drawn over all of that length rather than stopping
    # at the pad, and `verify` asks whether it touches anything.
    proud = values["stakeStandProud"]
    stake = driven_angle(
        values["stakeLegWidth"],
        values["stakeThickness"],
        z_bottom,
        -(values["stakeLength"] - proud),
        proud,
    )

    # The loop, drawn where it goes: round the angle's whole section, up
    # through the pad, with a nut and a washer standing on the far face.
    #
    # Its depth is set by the section it has to clear, not by the angle it was
    # bought for -- which is the point of it. `stakeUBoltClear` is the slack
    # inside the loop, and `verify` reports the biggest angle that still fits
    # so that a leg somebody scales up cannot quietly foul the bend.
    # Where the bend has to sit is decided at the angle's TIP, not on the
    # loop's centreline: the arc has risen by then. Clear the corner furthest
    # from the middle and everything nearer clears itself.
    u_bend_z = (
        z_bottom
        - values["stakeLegWidth"]
        - values["stakeUBoltClear"]
        - u_r
        + arc_height(u_span / 2.0, values["stakeLegWidth"] / 2.0)
    )
    u_leg_top = pad_top + stake_bolt["nut_depth"] + 2.0
    loop = u_bolt(u_r, u_span, -u_at, u_leg_top, u_bend_z)
    u_clear_depth = z_bottom - (u_bend_z - u_span / 2.0 + u_r)
    u_clear_width = u_span - 2.0 * u_r
    # How deep the loop hangs is a placement and follows whatever angle it is
    # drawn round, so it is never what binds. How WIDE it is, is bought: the
    # span between its legs is the one number that says what will go inside.
    u_fits = u_clear_width - 2.0 * values["stakeUBoltClear"]

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
        # The same probe for each of the U-bolt's legs: a ring of pad that has
        # to be there round the hole, or the leg comes up through air.
        "stake_probes": [
            Part.makeCylinder(
                washer_r + wall, lug_thick,
                App.Vector(p.x, p.y, z_bottom), App.Vector(0, 0, 1),
            ).cut(
                Part.makeCylinder(
                    u_r + 0.01, lug_thick + 2.0,
                    App.Vector(p.x, p.y, z_bottom - 1.0), App.Vector(0, 0, 1),
                )
            )
            for p in u_points
        ],
        "stake_cuts": list(stake_holes),
        # A nut and a washer stand on the pad's far face at each leg, in the
        # band the next plate up lives in. What must be empty is that column.
        "nut_access": [
            Part.makeCylinder(
                washer_r, stake_bolt["nut_depth"] + 2.0,
                App.Vector(p.x, p.y, pad_top), App.Vector(0, 0, 1),
            )
            for p in u_points
        ],
        "pad": pad,
        "stake": stake,
        "loop": loop,
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
        "rod_levels_mm": levels,
        "pitch_mm": pitch,
        "hub_radius_mm": hub_r,
        "arm_length_mm": arm_len,
        "ref_rod_length_mm": ref_len,
        "arm_width_mm": arm_w,
        "stake_reach_mm": stake_reach,
        "first_arm_rise_deg": values["firstArmRise"],
        "stake_leg_mm": values["stakeLegWidth"],
        "stake_thickness_mm": values["stakeThickness"],
        "stake_bolt_at_mm": u_at,
        "stake_bolt_size": stake_size,
        "stake_bolt_mm": values["stakeUBoltDiameter"],
        "stake_bolt_bearing_mm": lug_thick,
        "u_bolt_span_mm": u_span,
        "u_bolt_clear_depth_mm": u_clear_depth,
        "u_bolt_clear_width_mm": u_clear_width,
        # What the loop will go round, whatever was driven: its span, less
        # its own rod at both legs, less the slack.
        "u_bolt_fits_leg_mm": u_fits,
        "stake_nut_af_mm": stake_bolt["nut_af"],
        "stake_offset_mm": abs(z_bottom) + values["stakeLegWidth"] / 2.0,
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
        if not kit.has_volume(plate):
            problems.append(f"{name}: not a valid solid")

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

    # The angle passes the hub rather than through it now, and that claim is
    # the one thing about this design that could quietly stop being true: it is
    # drawn over its whole standing length, and it must touch nothing. A face
    # to face contact on the pad is not a touch -- it has no volume.
    if geo.get("stake") is not None:
        for name, plate in zip(geo["names"], plates):
            v = kit.vol(plate.common(geo["stake"]))
            if v > 0.5:
                problems.append(
                    f"{name} is in the angle's way by {v:.1f} mm3 -- it has "
                    f"{dims['stake_stand_proud_mm']:.0f} mm to stand proud in"
                )

    # Every bolt has to pass through material, in every plate. Cutting a hole
    # through open air leaves the stack with nothing holding it together, and
    # it looks exactly the same in a render.
    for name, plate in zip(geo["names"], plates):
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
                f"the U-bolt's leg {i + 1} has no pad round it: the hole is "
                "cut through air"
            )

    # Its nuts stand on the pad's far face, in the band the next plate up
    # lives in. Nothing may be standing where a spanner has to be.
    for i, access in enumerate(geo.get("nut_access", [])):
        for name, plate in zip(geo["names"][1:], plates[1:]):
            v = kit.vol(plate.common(access))
            if v > 0.5:
                problems.append(
                    f"{name} stands over the U-bolt's nut {i + 1} by "
                    f"{v:.1f} mm3: there is nowhere to put a spanner"
                )

    # The loop goes round the angle, and round is the whole claim: it must
    # clear the section it is drawn round, and it must clear the part.
    loop = geo.get("loop")
    if loop is not None:
        if geo.get("stake") is not None:
            v = kit.vol(loop.common(geo["stake"]))
            if v > 0.5:
                problems.append(
                    f"the U-bolt fouls the angle by {v:.1f} mm3: its "
                    f"{dims['u_bolt_span_mm']:.0f} mm span takes a leg up to "
                    f"{dims['u_bolt_fits_leg_mm']:.1f} mm"
                )
        for name, plate in zip(geo["names"], plates):
            v = kit.vol(plate.common(loop))
            if v > 0.5:
                problems.append(f"the U-bolt runs into {name} by {v:.1f} mm3")
        for i, rod in enumerate(geo["rods"]):
            v = kit.vol(loop.common(rod))
            if v > 0.5:
                problems.append(
                    f"the U-bolt runs into rod {i + 1} by {v:.1f} mm3"
                )

    # And it has to be a loop this angle actually fits inside.
    if dims["u_bolt_fits_leg_mm"] < dims["stake_leg_mm"] - 1e-6:
        problems.append(
            f"the U-bolt takes a leg of {dims['u_bolt_fits_leg_mm']:.1f} mm "
            f"and the angle's is {dims['stake_leg_mm']:.1f}"
        )

    # Nothing cut for the stake may take the wall out from under a rod.
    for cut in geo.get("stake_cuts", []):
        for i, keepout in enumerate(geo.get("keepouts", [])):
            v = kit.vol(cut.common(keepout))
            if v > 1.0:
                problems.append(
                    f"a U-bolt hole cuts {v:.1f} mm3 out of the wall around "
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

    # The legs have to bear on something. The pad is the plate's own floor, so
    # this only bites if somebody thins the floor under the rod.
    if dims["stake_bolt_bearing_mm"] < dims["stake_bolt_mm"] - 1e-6:
        problems.append(
            f"the U-bolt's legs bear on {dims['stake_bolt_bearing_mm']:.1f} mm "
            f"of pad, under their own {dims['stake_bolt_mm']:.1f} mm diameter"
        )

    # The cap prints flipped so its channel faces up; every other plate prints
    # with its upward channel up. Same convention as the four-rod node.
    printability = {
        name: kit.printability(plate, flipped=(name == "Cap"))
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
         "the sector with no arm; the stake pad and both bolts live here"),
        ("stakeAzimuth", round(dims["stake_azimuth_deg"], 4), "deg",
         "where the pad reaches for the angle; straight down once installed"),
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
        ("stakeSection", f"L{dims['stake_leg_mm']:g}x{dims['stake_leg_mm']:g}"
         f"x{dims['stake_thickness_mm']:g}", "-",
         "the angle to buy"),
        ("stakePlumb", "vertical", "-",
         "the stake axis is straight down once installed; that is what "
         "firstArmRise is for"),
        ("padReach", round(dims["stake_reach_mm"], 2), "mm",
         "hub centre to the end of the pad, straight down"),
        ("padSize", f"{dims['lug_width_mm']:g} x {dims['lug_thickness_mm']:g}",
         "mm", "across the pad and through it"),
        ("stakeUBoltAt", round(dims["stake_bolt_at_mm"], 2), "mm",
         "how far down the pad the loop sits"),
        ("stakeUBolt",
         f"M{dims['stake_bolt_size']:g} U-bolt, "
         f"{dims['u_bolt_span_mm']:g} mm span", "-",
         "the loop to buy: two nuts and two washers with it, and nothing "
         "drilled in the angle at all"),
        ("stakeUBoltFits", round(dims["u_bolt_fits_leg_mm"], 1), "mm",
         "the biggest angle leg this loop goes round. Anything smaller is "
         "held the same way, which is the point: the driven member's size "
         "stops being a dimension of the printed part"),
        ("stakeGrip", "friction", "-",
         "the loop clamps rather than bears, so the hub sits at whatever "
         "height the ground gave the angle -- and the two nuts want checking "
         "after the first night, because plastic under a preload creeps"),
        ("stakeBoltBearing", round(dims["stake_bolt_bearing_mm"], 2), "mm",
         "pad each leg bears on. At 20 m/s the ground takes 154 N of uplift "
         "per foot, which is under 1 MPa on this"),
        ("stakeStandProud", round(dims["stake_stand_proud_mm"], 1), "mm",
         "leave this much of the angle above the foot: it clears the hub over "
         "all of it, and the cover's loop drops over what is left"),
        ("stakeOffset", round(dims["stake_offset_mm"], 2), "mm",
         "how far the angle's section sits inboard of the bow bundle. It is a "
         "moment, and it is the one the ground and the angle's own bending "
         "are best placed to take"),
        ("stackBolt",
         f"M{dims['chosen_from_rod'].get('fastenerSize', 0):g} x "
         f"{math.ceil(dims['stack_bolt_length_mm'] / 5.0) * 5:g}", "-",
         "the two that hold the plates together: head and washer down the "
         "cap's counterbore, nut captive in the bottom plate"),
        ("padSizeNote", f"loop {dims['u_bolt_clear_width_mm']:.0f} wide x "
         f"{dims['u_bolt_clear_depth_mm']:.0f} deep inside", "mm",
         "what the U-bolt leaves for the angle to sit in"),
        ("plateCount", dims["plate_count"], "-", "prints per hub"),
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
    if geo.get("loop") is not None:
        obj = doc.addObject("Part::Feature", "Ref_UBolt")
        obj.Shape = geo["loop"]
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
        elif obj.Name in ("Ref_Stake", "Ref_UBolt"):
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
