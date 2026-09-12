# -*- coding: utf-8 -*-
"""
Star Dome four-rod node connector, V2 -- a stack of plates.

WHY V2 EXISTS

V1 clamped the four rods as a bundle: a saddle under rod 1, a cap over rod 4,
and rods 2 and 3 squeezed in between. It held the crossing together but it did
not LOCATE the middle rods at all -- nothing stopped them sliding or rolling
inside the bundle except friction, and the dome's shape depends on the rods
crossing at the right angles at the right points.

V1 justified that with a constraint it called governing: adjacent rods in the
stack touch, so there is no room for material between them. That is true only
because V1 set the stack pitch to exactly one rod diameter, inherited from the
two-rod clamp where the rods deliberately bear on each other. Nothing in the
dome requires it.

That reasoning was half right, and the half it got wrong is worth stating
before the part is described, because two revisions of V2 were built on it.
Rods touching leaves no room for material between them ONLY AT THE CROSSING
POINT. Move away from the centre and the two surfaces diverge, so material can
live between two touching rods everywhere except a small lens around the node.

So the part is a stack of plates, each carrying a channel on both faces:

    pitch = rodDiameter + rodGap

and rodGap DEFAULTS TO ZERO. Every rod ends up in a real channel, wrapped
180 deg from below by one plate and 180 deg from above by the next -- but at
the centre the two channels of a middle plate overlap and the plate simply has
a hole there, where the rods bear on each other. That is deliberate: the
clamping load goes rod-to-rod as the reference intends, and there is no thin
web to creep under sustained bolt preload.

It also means the three crossed-cylinder contacts on fibreglass that V1's own
notes flagged are still there, on purpose, and still the first thing to check
on a printed prototype. See docs/decisions/0005-the-rods-bear-on-each-other-at-the-node.md
and the section "The rods touch at the centre" in docs/fan-node-v2.md.

THE PARTS

    plate 0   bottom   groove up   for rod 1
    plate 1   middle   rod 1 down, rod 2 up     37.3774 deg between grooves
    plate 2   middle   rod 2 down, rod 3 up     41.8103 deg
    plate 3   middle   rod 3 down, rod 4 up     37.3774 deg
    plate 4   cap      groove down for rod 4

All five are DIFFERENT parts. Plates 1 and 3 have the same angle between their
grooves, but the two through-bolts pin each plate's orientation in the fan, and
the groove pairs sit at different azimuths, so one cannot stand in for the
other. Five distinct prints per node, ten nodes per dome.

The cost is five loose pieces at height in the wind, which is exactly what the
project's first rule says not to do. The answer is that the bolts keep the
stack captive: assemble it once, carry it as one hinged sandwich, open it to
lay each rod. In the field it is still one object per node.

FIELD SEQUENCE

    open the stack -> lay rod 1 -> close plate 1 -> lay rod 2 -> plate 2 ->
    rod 3 -> plate 3 -> rod 4 -> cap -> tighten two bolts.

Helpers now come from connectors/kit.py. They used to be copied from
fan_node_v1.py, on the grounds that sharing needs a path loader in each script
and the refactor could wait for the family to settle. The loader turned out to
be six lines, and Milestone 5 adds three to five more parts to the family, so
it was cheaper to do it before them than after.

Run:  exec(open('.../connectors/fan_node_v2.py').read()) inside FreeCAD, or
through connectors/generate_clamps.py, which drives it from the model data.
"""

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

DOC_NAME = "StarDome_FanNode_V2"
TITLE = "Star Dome four-rod fan node V2 - parameters"
USE_SPREADSHEET_IF_PRESENT = True

DEFAULT_FAN_GAPS = [37.377368, 41.810315, 37.377368, 63.434949]

PLATE_NAMES = ["Bottom", "Mid1", "Mid2", "Mid3", "Cap"]

OVERHANG_LIMIT_DEG = kit.OVERHANG_LIMIT_DEG

INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance added to each rod channel"),
    ("rodGap",                 0.0,  "mm",  "gap between adjacent rods at the crossing; the stack pitch is rodDiameter + this. 0 means they bear on each other and the plate has a hole at the node centre. Every mm here thickens the rib by a mm at every radius and costs 3 mm of stack height."),
    ("channelOverrun",         6.0,  "mm",  "how far each channel runs past the body; channel length is DERIVED"),
    ("minimumWall",            0.0,  "mm",  "0 takes it from rodDiameter: 0.4 of the rod, never under 3 mm. A real number overrides"),
    ("baseFloor",              5.0,  "mm",  "material under the bottom plate's channel"),
    ("capThickness",           6.0,  "mm",  "material above the cap's channel"),
    ("tiltAllowance",          1.5,  "deg", "radial tilt a rod may arrive with; the weave needs up to 1.2 deg"),
    ("teardropRoof",           0.0,  "-",   "1 = gable every downward channel. CURRENTLY BROKEN, see docs/fan-node-v2.md: with the flare in place the gabled cut silently removes nothing from the middle plates, and verify() catches it as rod interference. Leave at 0."),
    ("fastenerSize",            0.0,  "",    "which metric bolt: 0 chooses it from the rod -- half the rod, snapped to M3/M4/M5/M6/M8 -- and 3, 4, 5, 6 or 8 forces one"),
    ("fastenerDiameter",       0.0,  "mm",  "clearance hole for the bolt. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("fastenerHeadDiameter",  0.0,  "mm",  "head / washer outside diameter. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("headClearance",          0.6,  "mm",  "diametral clearance for the head counterbore"),
    ("headBoreDepth",          0.0,  "mm",  "counterbore depth for head + washer. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("headConeHeight",         0.0,  "mm",  "taper off the head counterbore, so the cap prints upside down"),
    ("nutAcrossFlats",         0.0,  "mm",  "nut across flats + fit clearance. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("nutRecessDepth",         0.0,  "mm",  "captive nut pocket depth. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("nutConeHeight",          0.0,  "mm",  "taper off the nut pocket, so the bottom plate prints on the bed"),
    ("boltHoleClearance",      0.4,  "mm",  "diametral print clearance on the bolt shank hole"),
    ("hubRadiusFactor",        2.2,  "-",   "hub radius as a multiple of rodDiameter; sets channel length"),
    ("armWidthFactor",         1.6,  "-",   "arm width as a multiple of the boss diameter"),
    ("edgeRadius",             2.0,  "mm",  "outer edge radius"),
    ("rimFilletFactor",        0.6,  "-",   "rim fillet as a fraction of edgeRadius"),
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def widest_gap_bisector(azimuths, gaps):
    widest = max(range(len(gaps)), key=lambda i: gaps[i])
    return azimuths[widest % len(azimuths)] + gaps[widest] / 2.0


def _local_teardrop_roof(radius, length, angle_deg):
    """A gable tangent to the channel at `angle_deg` from horizontal.

    Built with the rod along +X and its axis at the origin. The tangent lines
    touch the circle at (+/- r sin a, r cos a) and meet at r / cos a, so a 45
    deg gable peaks at sqrt(2) r. It is set steeper than 45 by the tilt
    allowance, because the finished channel is rotated through +/- that much
    to make the flare, and a gable built at exactly 45 comes out at 43.5 on
    one side afterwards.
    """
    a = math.radians(angle_deg)
    half = radius * math.sin(a)
    apex = radius / math.cos(a)
    pts = [
        App.Vector(-length / 2.0, -half, radius * math.cos(a)),
        App.Vector(-length / 2.0, 0.0, apex),
        App.Vector(-length / 2.0, half, radius * math.cos(a)),
    ]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(length, 0, 0))


def teardrop_roof(radius, length, azimuth_deg, z):
    """A 45 deg gable over a channel, tangent to it at the 45 deg points.

    A channel cut into a plate's underside opens downward, and its roof is a
    flat-topped arch the printer would have to bridge. Capping it with a gable
    whose sides never exceed 45 deg makes it print unsupported. The extra
    clearance sits above the rod, where it does nothing.
    """
    half = radius / math.sqrt(2.0)
    apex = radius * math.sqrt(2.0)
    pts = [
        App.Vector(-length / 2.0, -half, half),
        App.Vector(-length / 2.0, 0.0, apex),
        App.Vector(-length / 2.0, half, half),
    ]
    pts.append(pts[0])
    prism = Part.Face(Part.makePolygon(pts)).extrude(App.Vector(length, 0, 0))
    prism.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    prism.translate(App.Vector(0, 0, z))
    return prism


def rod_channel(radius, length, azimuth_deg, z, tilt_deg, steps=2, roof=False):
    """Channel for one rod, flared at the ends to admit a tilted rod.

    The rod arrives at up to `tilt_deg` of radial tilt, which is a rotation
    about the transverse axis through the node centre -- so at the centre the
    rod is on the nominal axis and the deviation grows towards the ends. The
    channel is therefore the swept volume of the rod rotated through the
    allowed range, approximated by fusing a few rotated copies: narrow in the
    middle, flared at the mouths.

    Widening the channel uniformly instead, as the first version did, spends
    tilt clearance at the node centre -- which is exactly where the web
    between two stacked channels is thinnest, and where the rod needs no
    clearance at all. That cost 2.3 mm of stack pitch per interface for
    nothing.

    Built in a local frame with the rod along +X and its axis through the
    origin, then placed. Fusing nearly-tangent cylinders is badly conditioned
    in OCC and the outcome depends on how the seams happen to line up: done in
    world coordinates, this raised "Bnd_Box is void" on the fourth rod and
    produced an invalid solid on the third, while the first two were fine.
    In the local frame every rod is the same well-conditioned problem.
    """
    origin = App.Vector(0.0, 0.0, 0.0)
    base = Part.makeCylinder(
        radius, length, App.Vector(-length / 2.0, 0.0, 0.0), App.Vector(1, 0, 0)
    )
    # The gable goes on BEFORE the flare, so every tilted position carries its
    # own roof. Added afterwards it only covers the nominal axis, and the
    # flared ends stick out from under it as shallow round overhangs -- which
    # is what happened first, dropping the middle plates from 45 deg to 26.
    if roof:
        base = base.fuse(
            _local_teardrop_roof(radius, length, OVERHANG_LIMIT_DEG + tilt_deg)
        ).removeSplitter()

    body = base
    if tilt_deg > 0.0 and steps > 0:
        for k in range(1, steps + 1):
            angle = tilt_deg * k / steps
            for sign in (1.0, -1.0):
                turned = base.copy()
                turned.rotate(origin, App.Vector(0, 1, 0), sign * angle)
                body = body.fuse(turned)
    body = body.removeSplitter()
    body.rotate(origin, App.Vector(0, 0, 1), azimuth_deg)
    body.translate(App.Vector(0.0, 0.0, z))
    return body


def plate_blank(hub_radius, arm_length, arm_width, boss_radius, z_lo, z_hi, azimuth_deg):
    """Hub, two spars, two bolt bosses. The channels get cut out of this."""
    height = z_hi - z_lo
    body = Part.makeCylinder(
        hub_radius, height, App.Vector(0, 0, z_lo), App.Vector(0, 0, 1)
    )
    for az in (azimuth_deg, azimuth_deg + 180.0):
        body = body.fuse(kit.arm(arm_length, arm_width, height, z_lo, az))
        d = kit.direction(az)
        body = body.fuse(
            Part.makeCylinder(
                boss_radius,
                height,
                App.Vector(d.x * arm_length, d.y * arm_length, z_lo),
                App.Vector(0, 0, 1),
            )
        )
    return body.removeSplitter()


def build(values, fan_gaps=None):
    # The bolt, the pin and the wall come from the rod unless somebody
    # typed them in; see kit.scale_to_rod.
    chosen = kit.scale_to_rod(values)
    gaps = list(fan_gaps or DEFAULT_FAN_GAPS)
    azimuths = kit.azimuths_from_gaps(gaps[:-1])

    rod_d = values["rodDiameter"]
    channel_r = rod_d / 2.0 + values["rodClearance"] / 2.0
    wall = values["minimumWall"]
    roof = values["teardropRoof"] >= 0.5

    # Bolts sit on the bisector of the fan's widest sector, the only place a
    # boss clears every rod. The boss has to hold a head or a nut, so its
    # radius, not the bolt's, sets how far out it must sit. None of this
    # depends on the stack pitch, so it is settled first.
    bolt_azimuth = widest_gap_bisector(azimuths, gaps)
    boss_r = values["fastenerHeadDiameter"] / 2.0 + wall
    closest = min(abs(math.sin(math.radians(bolt_azimuth - a))) for a in azimuths)
    bolt_offset = (boss_r + channel_r) / closest

    hub_r = values["hubRadiusFactor"] * rod_d
    arm_w = values["armWidthFactor"] * boss_r * 2.0
    body_r = bolt_offset + boss_r + values["edgeRadius"]

    length = 2.0 * (body_r + values["channelOverrun"])
    tilt_slack = (length / 2.0) * math.tan(math.radians(values["tiltAllowance"]))

    # Opening the pitch is the whole point of V2: it is what makes room for a
    # plate between every pair of rods. The pitch is DERIVED so that
    # the pitch is rodDiameter + rodGap, so the rib that remains between two
    # which is at the node centre, above the lower channel and below the upper
    # one:
    #
    #   the lower channel reaches channel_r above its axis, or sqrt(2)*channel_r
    #   if it is gabled for printing;
    #   the upper channel reaches channel_r below its axis.
    #
    # Tilt no longer appears here. The channel is flared at its ends rather
    # than widened along its whole length, so at the centre it is exactly the
    # rod -- see rod_channel. Two earlier versions of this arithmetic were
    # wrong: the first left 0.85 mm of web instead of 3, the second spent
    # 2.3 mm per interface on tilt clearance the centre does not need.
    upper_reach = (
        channel_r
        / math.cos(math.radians(OVERHANG_LIMIT_DEG + values["tiltAllowance"]))
        if roof
        else channel_r
    )
    # One dial: how far apart adjacent rods sit at the crossing.
    #
    # At rodGap = 0 they bear on each other, as the reference intends and as
    # the two-rod clamp already does. The two channels then overlap in a lens
    # around the node centre and the plate has a hole there -- but only there.
    # Away from the centre the rods diverge in plan, the vertical gap between
    # their surfaces opens up, and the plate is solid again: a cross whose arms
    # carry the channels.
    #
    # Opening the gap thickens that rib by the same amount at every radius,
    # including the centre, and costs 3 mm of stack height per mm. The rib is
    # not the load path -- that stays rod-to-rod through the crossing -- but it
    # is what stops a rod climbing sideways out of its channel, and at zero gap
    # it starts at 0.25 mm and only reaches 2 mm at radius 10.
    #
    # A gabled channel reaches higher than channel_r, so it needs the extra
    # room; see upper_reach.
    pitch = rod_d + values["rodGap"]
    if roof:
        # A gable reaches higher than the channel radius, so it needs the room.
        # Applying this guard unconditionally, as the first attempt did, pushed
        # the pitch to 10.4 even at zero gap and quietly parted the rods by
        # 0.4 mm -- which is exactly what "touching" was meant to rule out.
        pitch = max(pitch, channel_r + upper_reach)
    levels = [(k - 1.5) * pitch for k in range(4)]

    # The outer faces do need the tilt clearance: that is where the flare is
    # widest, and the rod must still be enclosed.
    z_bottom = levels[0] - channel_r - tilt_slack - values["baseFloor"]
    z_top = levels[3] + channel_r + tilt_slack + values["capThickness"]

    bolt_points = [
        App.Vector(kit.direction(az).x * bolt_offset, kit.direction(az).y * bolt_offset, 0.0)
        for az in (bolt_azimuth, bolt_azimuth + 180.0)
    ]

    shank_r = (values["fastenerDiameter"] + values["boltHoleClearance"]) / 2.0
    head_r = (values["fastenerHeadDiameter"] + values["headClearance"]) / 2.0

    rods = [kit.rod_solid(rod_d / 2.0, length, azimuths[k], levels[k]) for k in range(4)]
    bolt_height = (z_top + 2.0) - (z_bottom - 2.0)
    bolts = [
        Part.makeCylinder(
            values["fastenerDiameter"] / 2.0,
            bolt_height,
            App.Vector(p.x, p.y, z_bottom - 2.0),
            App.Vector(0, 0, 1),
        )
        for p in bolt_points
    ]

    def shank_cut():
        return [
            Part.makeCylinder(
                shank_r,
                bolt_height,
                App.Vector(p.x, p.y, z_bottom - 2.0),
                App.Vector(0, 0, 1),
            )
            for p in bolt_points
        ]

    # --- the five plates --------------------------------------------------
    spans = [(z_bottom, levels[0])]
    spans += [(levels[k], levels[k + 1]) for k in range(3)]
    spans += [(levels[3], z_top)]

    # Which rod channels each plate carries, and whether that channel opens
    # downward in the plate's own print orientation.
    #   bottom: rod 0, groove up
    #   mid k : rod k down, rod k+1 up
    #   cap   : rod 3 down, but the cap prints flipped so it faces up
    carries = [
        [(0, False)],
        [(0, True), (1, False)],
        [(1, True), (2, False)],
        [(2, True), (3, False)],
        [(3, False)],
    ]

    plates = []
    fillet_counts = []
    for index, (z_lo, z_hi) in enumerate(spans):
        body = plate_blank(hub_r, bolt_offset, arm_w, boss_r, z_lo, z_hi, bolt_azimuth)

        for rod_index, downward in carries[index]:
            body = body.cut(
                rod_channel(
                    channel_r,
                    length * 1.02,
                    azimuths[rod_index],
                    levels[rod_index],
                    values["tiltAllowance"],
                    roof=roof and downward,
                )
            )

        for cut in shank_cut():
            body = body.cut(cut)

        if index == 0:
            nut_top = z_bottom + values["nutRecessDepth"]
            for p in bolt_points:
                body = body.cut(
                    kit.hex_prism(
                        values["nutAcrossFlats"],
                        values["nutRecessDepth"] + 1.0,
                        App.Vector(p.x, p.y, z_bottom - 1.0),
                    )
                )
                body = body.cut(
                    Part.makeCone(
                        values["nutAcrossFlats"] / math.sqrt(3.0),
                        shank_r,
                        values["nutConeHeight"],
                        App.Vector(p.x, p.y, nut_top),
                        App.Vector(0, 0, 1),
                    )
                )
        elif index == len(spans) - 1:
            for p in bolt_points:
                body = body.cut(
                    Part.makeCylinder(
                        head_r,
                        values["headBoreDepth"] + 1.0,
                        App.Vector(p.x, p.y, z_top - values["headBoreDepth"]),
                        App.Vector(0, 0, 1),
                    )
                )
                body = body.cut(
                    Part.makeCone(
                        shank_r,
                        head_r,
                        values["headConeHeight"],
                        App.Vector(
                            p.x,
                            p.y,
                            z_top - values["headBoreDepth"] - values["headConeHeight"],
                        ),
                        App.Vector(0, 0, 1),
                    )
                )

        body, n_vertical = kit.fillet_by_predicate(
            body, kit.is_vertical_edge, values["edgeRadius"]
        )
        plates.append(body)
        fillet_counts.append(n_vertical)

    geo = {
        "plates": plates,
        "names": list(PLATE_NAMES),
        "rods": rods,
        "bolts": bolts,
    }
    dims = {
        "chosen_from_rod": chosen,
        "fan_gaps_deg": gaps,
        "fan_azimuths_deg": azimuths,
        "rod_levels_mm": levels,
        "stack_pitch_mm": pitch,
        "rod_gap_mm": values["rodGap"],
        "stack_height_mm": levels[3] - levels[0],
        "assembly_height_mm": z_top - z_bottom,
        "channel_radius_mm": channel_r,
        "channel_length_mm": length,
        "tilt_slack_mm": tilt_slack,
        "bolt_azimuth_deg": bolt_azimuth,
        "bolt_offset_mm": bolt_offset,
        "boss_radius_mm": boss_r,
        "body_radius_mm": body_r,
        "bolt_length_needed_mm": (z_top - z_bottom) - values["headBoreDepth"] + 6.0,
        "plate_spans_mm": spans,
        "fillets_vertical": fillet_counts,
        "z_bottom": z_bottom,
        "z_top": z_top,
    }
    return geo, dims


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
def verify(geo, dims, values):
    report = {"plates": {}}
    plates = geo["plates"]
    names = geo["names"]

    for name, shape, (z_lo, z_hi) in zip(names, plates, dims["plate_spans_mm"]):
        zs = [v.Point.z for v in shape.Vertexes]
        report["plates"][name] = {
            "valid": shape.isValid(),
            "solids": len(shape.Solids),
            "volume_cm3": round(kit.vol(shape) / 1000.0, 2),
            "z_span": (round(min(zs), 3), round(max(zs), 3)),
            "z_span_expected": (round(z_lo, 3), round(z_hi, 3)),
        }

    # Nothing may occupy a rod's or a bolt's space.
    interference = {}
    for name, shape in zip(names, plates):
        for i, rod in enumerate(geo["rods"], start=1):
            interference[f"{name}_x_rod{i}"] = round(kit.vol(shape.common(rod)), 4)
        for j, bolt in enumerate(geo["bolts"]):
            interference[f"{name}_x_bolt{j}"] = round(kit.vol(shape.common(bolt)), 4)
    for a in range(len(plates)):
        for b in range(a + 1, len(plates)):
            interference[f"{names[a]}_x_{names[b]}"] = round(
                kit.vol(plates[a].common(plates[b])), 4
            )
    report["interference_mm3"] = interference

    # A channel that ends blind inside a plate cannot take a rod. Probe with a
    # rod several times the footprint; only a through channel clears it.
    probe_length = dims["body_radius_mm"] * 6.0
    blind = {}
    for i, azimuth in enumerate(dims["fan_azimuths_deg"], start=1):
        probe = kit.rod_solid(
            values["rodDiameter"] / 2.0, probe_length, azimuth, dims["rod_levels_mm"][i - 1]
        )
        blind[f"rod{i}"] = round(sum(kit.vol(p.common(probe)) for p in plates), 4)
    report["blind_channel_mm3"] = blind

    # Every rod must lift straight out of the plate below it and be clear of
    # the plate above: each plate spans exactly one pitch, so no plate can wrap
    # a rod by more than 180 deg. Checked rather than assumed.
    wrap = {}
    for name, shape, (z_lo, z_hi) in zip(names, plates, dims["plate_spans_mm"]):
        zs = [v.Point.z for v in shape.Vertexes]
        wrap[name] = {
            "below_span_mm": round(max(0.0, z_lo - min(zs)), 4),
            "above_span_mm": round(max(0.0, max(zs) - z_hi), 4),
        }
    report["wrap"] = wrap

    # Measure the web rather than trusting the pitch arithmetic. With the rods
    # touching there is nothing at the node centre by design, so the useful
    # number is the PROFILE: how far out material starts, and how thick the
    # rib is once it does. Walked along the bisector of the plate's two
    # channels, where the two rods are closest in plan.
    step = 0.05
    azimuths = dims["fan_azimuths_deg"]
    webs = {}
    for index, (name, shape, (z_lo, z_hi)) in enumerate(
        zip(names, plates, dims["plate_spans_mm"])
    ):
        if name in ("Bottom", "Cap"):
            continue
        lower, upper = azimuths[index - 1], azimuths[index]
        bisector = math.radians((lower + upper) / 2.0)
        profile = []
        starts_at = None
        # A handful of stations, not a fine walk: this is a probe per point
        # against the solid, and a 0.5 mm sweep out to the rim cost ninety
        # thousand of them and killed the FreeCAD process twice.
        for radius_mm in (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0):
            x = math.cos(bisector) * radius_mm
            y = math.sin(bisector) * radius_mm
            solid_mm = 0.0
            z = z_lo
            while z <= z_hi:
                if shape.isInside(App.Vector(x, y, z), 1e-7, True):
                    solid_mm += step
                z += step
            if starts_at is None and solid_mm >= 1.0:
                starts_at = radius_mm
            profile.append((radius_mm, round(solid_mm, 2)))
        webs[name] = {
            "rib_starts_at_mm": starts_at,
            "rib_thickness_at_r": profile,
        }
    report["web_profile"] = webs
    report["rod_gap_mm"] = round(values["rodGap"], 3)

    # The cap prints flipped so its channel faces up; every other plate prints
    # with its upward channel up.
    report["printability"] = {
        name: kit.printability(shape, flipped=(name == "Cap"))
        for name, shape in zip(names, plates)
    }

    report["key_dims"] = {
        "stack_pitch_mm": round(dims["stack_pitch_mm"], 3),
        "rod_gap_mm": round(dims["rod_gap_mm"], 3),
        "stack_height_mm": round(dims["stack_height_mm"], 3),
        "assembly_height_mm": round(dims["assembly_height_mm"], 3),
        "footprint_diameter_mm": round(dims["body_radius_mm"] * 2, 3),
        "bolt_offset_mm": round(dims["bolt_offset_mm"], 3),
        "bolt_length_needed_mm": round(dims["bolt_length_needed_mm"], 1),
        "channel_diameter_mm": round(dims["channel_radius_mm"] * 2, 3),
        "tilt_slack_mm": round(dims["tilt_slack_mm"], 3),
        "total_volume_cm3": round(sum(kit.vol(p) for p in plates) / 1000.0, 2),
        "pieces_per_node": len(plates),
    }
    return report


def derived_rows(dims, values):
    rows = [(
        "fastenerChosen",
        dims["chosen_from_rod"].get("fastenerSize", 0),
        "M",
        "which metric bolt this part was drawn for. Chosen from the rod "
        "unless fastenerSize said otherwise -- half the rod, snapped",
    )]
    for key, value in dims.items():
        if isinstance(value, (int, float)):
            rows.append((key, round(value, 4), "", "derived"))
        else:
            rows.append((key, str(value), "", "derived"))
    return rows


# Colours for the saved view. The plates are made translucent so the rods can
# be seen threading through them, and each rod gets its own colour because the
# whole point of the node is which rod sits at which level.
# See docs/colours.md. Distinct per-rod colours here rather than family ones:
# this fan is G-U-U-G, so family colours would give two identical pairs and
# lose exactly what the drawing is for.
PLATE_COLOUR = (0.35, 0.52, 0.78)
PLATE_TRANSPARENCY = 55
ROD_COLOURS = [
    (0.95, 0.35, 0.25),   # rod 1, innermost
    (0.98, 0.72, 0.15),
    (0.35, 0.80, 0.45),
    (0.55, 0.45, 0.90),   # rod 4, outermost
]
BOLT_COLOUR = (0.55, 0.55, 0.58)


def apply_view(doc):
    """Colour and transparency for the saved document.

    A no-op without a GUI: freecadcmd gives objects no ViewObject, so a
    headless rebuild produces correct geometry and no view settings. Run this
    inside FreeCAD itself -- or through the MCP bridge against a GUI instance --
    and save, to keep the colours in the file.
    """
    touched = 0
    for obj in doc.Objects:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        name = obj.Name
        if name.startswith("Plate_"):
            colour, transparency = PLATE_COLOUR, PLATE_TRANSPARENCY
        elif name.startswith("Rod"):
            try:
                index = int(name[3:]) - 1
            except ValueError:
                index = 0
            colour, transparency = ROD_COLOURS[index % len(ROD_COLOURS)], 0
        elif name.startswith("Bolt"):
            colour, transparency = BOLT_COLOUR, 0
        else:
            continue
        for attr in ("ShapeColor", "DiffuseColor"):
            if hasattr(view, attr):
                try:
                    setattr(view, attr, colour)
                except Exception:
                    pass
        if hasattr(view, "Transparency"):
            view.Transparency = transparency
        if hasattr(view, "Visibility"):
            view.Visibility = True
        touched += 1
    return touched


def populate(doc, geo):
    for o in reversed(list(doc.Objects)):
        if o.Name == "Parameters" or o.Label == "Parameters":
            continue
        try:
            doc.removeObject(o.Name)
        except Exception:
            pass

    for name, shape in zip(geo["names"], geo["plates"]):
        obj = doc.addObject("Part::Feature", "Plate_" + name)
        obj.Label = "Plate_" + name
        obj.Shape = shape

    grp = doc.addObject("App::DocumentObjectGroup", "Reference")
    grp.Label = "Reference"
    members = []
    for i, rod in enumerate(geo["rods"], start=1):
        o = doc.addObject("Part::Feature", f"Rod{i}")
        o.Shape = rod
        members.append(o)
    for j, bolt in enumerate(geo["bolts"]):
        o = doc.addObject("Part::Feature", f"Bolt_M5_{j}")
        o.Shape = bolt
        members.append(o)
    grp.addObjects(members)
    doc.recompute()
    apply_view(doc)


def run(fan_gaps=None, out_dir=None, doc_path=None):
    if doc_path and os.path.exists(doc_path):
        doc = App.openDocument(doc_path)
    elif DOC_NAME in App.listDocuments():
        doc = App.getDocument(DOC_NAME)
    else:
        doc = App.newDocument(DOC_NAME)
    sheet, values = kit.read_or_build_parameters(doc, INPUTS, USE_SPREADSHEET_IF_PRESENT)
    geo, dims = build(values, fan_gaps)
    report = verify(geo, dims, values)
    populate(doc, geo)
    kit.write_parameters(doc, sheet, INPUTS, values, derived_rows(dims, values), TITLE)
    doc.recompute()
    path = doc_path or (
        os.path.join(out_dir, "star_dome_fan_node_v2.FCStd") if out_dir else None
    )
    if path:
        doc.saveAs(path)
        report["saved_to"] = path
    return report


if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint

    pprint.pprint(REPORT, width=112)
