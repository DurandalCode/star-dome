# -*- coding: utf-8 -*-
"""
Star Dome four-rod node connector, prototype V1.

The ten lashed nodes of the baseline dome are a FLAT FOUR-ARMED FAN: all four
rod tangents are coplanar, because a great circle's tangent lies in the
sphere's tangent plane. See docs/tied-node.md. The rods stack along the radius
in fan order, each lying immediately outside its angular neighbour.

    fan gaps        37.3774  41.8103  37.3774  63.4349 deg   (sum 180)
    stack contacts  37.3774  41.8103  37.3774 deg
    stack height    3 x rodDiameter

THE GOVERNING CONSTRAINT

Adjacent rods in the stack touch. Their axes are exactly one diameter apart
and they meet at the crossing point, so there is NO room for material between
them -- not at the centre, and not further out either, because the vertical
gap between their surfaces stays zero all along. A plate-per-layer sandwich is
therefore impossible.

Material can only live:

    below rod 1, above rod 4, and in the sectors between the rods.

So the part is:

    Base  - a 180 deg saddle under rod 1, open upward, carrying two posts that
            rise through the two widest sectors of the fan to the cap.
    Cap   - a 180 deg saddle over rod 4, open downward, bolted to the posts.

Rods 2 and 3 are captured between rods 1 and 4 and contained laterally by the
posts. They are not gripped individually, which is the same compromise
crossing_clamp_v1 makes: each rod is a continuous arc located by its other
nodes and by its two ground points, so the joint has to hold the crossing
together, not fully constrain every member.

FIELD SEQUENCE, which matches how the reference builds the dome anyway:

    lay rod 1 in the base -> drop rods 2 and 3 on it -> lay rod 4 -> cap ->
    two bolts.

The two bolts sit on the bisectors of the fan's 63.4349 deg gaps, the only
sectors wide enough to clear every rod.

Run:  exec(open('.../connectors/fan_node_v1.py').read()) inside FreeCAD, or
through connectors/generate_clamps.py, which drives it from the model data.
"""

import math
import os

import FreeCAD as App
import Part

DOC_NAME = "StarDome_FanNode_V1"

# If the document already carries a Parameters spreadsheet, its values win over
# the defaults below, the same convention crossing_clamp_v1 uses.
USE_SPREADSHEET_IF_PRESENT = True

# Fan gaps of the baseline Star Dome node, in angular order. The generator does
# not derive these -- stardome does, and generate_clamps.py passes them in.
DEFAULT_FAN_GAPS = [37.377368, 41.810315, 37.377368, 63.434949]

INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance added to each rod channel"),
    ("channelOverrun",         6.0,  "mm",  "how far each rod channel runs past the body; the channel length is DERIVED from the footprint so it can never end blind"),
    ("minimumWall",            4.0,  "mm",  "minimum structural wall thickness"),
    ("baseFloor",              5.0,  "mm",  "material under rod 1's channel"),
    ("capThickness",           6.0,  "mm",  "material above rod 4; works in bending between the bolts"),
    ("clampGap",               1.2,  "mm",  "designed open gap at the parting faces, so the bolts always squeeze"),
    ("tiltAllowance",          1.5,  "deg", "radial tilt a rod may arrive with; the weave needs up to 1.2 deg"),
    ("fastenerDiameter",       5.5,  "mm",  "M5 clearance hole diameter"),
    ("fastenerHeadDiameter",  10.0,  "mm",  "M5 head / washer outside diameter"),
    ("headClearance",          0.6,  "mm",  "diametral clearance for the head counterbore"),
    ("headBoreDepth",          4.4,  "mm",  "counterbore depth for head + washer"),
    ("nutAcrossFlats",         8.3,  "mm",  "M5 nut across flats + fit clearance"),
    ("nutRecessDepth",         4.6,  "mm",  "captive nut pocket depth"),
    ("boltHoleClearance",      0.4,  "mm",  "diametral print clearance on the bolt shank hole"),
    ("postWallFactor",         1.0,  "mm",  "multiplier on minimumWall for the post-to-rod clearance"),
    ("edgeRadius",             2.0,  "mm",  "outer edge radius"),
    ("hubRadiusFactor",        2.2,  "mm",  "hub radius as a multiple of rodDiameter; sets the saddle length"),
    ("armWidthFactor",         1.6,  "mm",  "arm width as a multiple of the post diameter"),
    ("headConeHeight",         2.8,  "mm",  "tapered transition off the head counterbore, so it prints upside down"),
    ("nutConeHeight",          2.2,  "mm",  "tapered transition off the nut pocket, so it prints on the bed"),
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def azimuths_from_gaps(gaps):
    """Fan directions, in degrees, from the gaps between angular neighbours."""
    out = [0.0]
    for gap in gaps[:-1]:
        out.append(out[-1] + gap)
    return out


def widest_gap_bisector(azimuths, gaps):
    """Azimuth of the bisector of the widest sector -- where a bolt can go."""
    widest = max(range(len(gaps)), key=lambda i: gaps[i])
    start = azimuths[widest % len(azimuths)]
    return start + gaps[widest] / 2.0


def direction(azimuth_deg):
    a = math.radians(azimuth_deg)
    return App.Vector(math.cos(a), math.sin(a), 0.0)


def rod_solid(radius, length, azimuth_deg, z):
    """A rod as a cylinder centred on the origin, at height z."""
    d = direction(azimuth_deg)
    base = App.Vector(-d.x * length / 2.0, -d.y * length / 2.0, z)
    return Part.makeCylinder(radius, length, base, d)


def rod_channel(radius, length, azimuth_deg, z, tilt_slack):
    """The rod's channel, stretched vertically so the rod may arrive tilted.

    A rod does not reach a node parallel to the sphere: the weave brings it in
    at up to about 1.2 deg of radial tilt, generally different on each side. A
    channel bored exactly tangent would pre-stress it.
    """
    body = rod_solid(radius, length, azimuth_deg, z)
    if tilt_slack <= 0.0:
        return body
    for dz in (-tilt_slack, tilt_slack):
        body = body.fuse(rod_solid(radius, length, azimuth_deg, z + dz))
    return body.removeSplitter()


def hex_prism(across_flats, height, base):
    r = across_flats / math.sqrt(3.0)
    pts = []
    for i in range(6):
        a = math.radians(60 * i)
        pts.append(App.Vector(base.x + r * math.cos(a), base.y + r * math.sin(a), base.z))
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    return Part.Face(wire).extrude(App.Vector(0, 0, height))


def arm(length, width, height, z, azimuth_deg):
    """A rectangular spar from the hub out to a bolt post."""
    box = Part.makeBox(length, width, height, App.Vector(0.0, -width / 2.0, z))
    box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    return box


def plate(hub_radius, arm_length, arm_width, post_radius, z_lo, z_hi, azimuth_deg):
    """Hub plus two spars plus two bolt bosses, instead of a solid disc.

    A full disc is mostly dead material: the part only has to hold the rod at
    the centre and reach the two bolts. This is the same footprint, half the
    plastic.
    """
    height = z_hi - z_lo
    body = Part.makeCylinder(
        hub_radius, height, App.Vector(0, 0, z_lo), App.Vector(0, 0, 1)
    )
    for sign in (1.0, -1.0):
        az = azimuth_deg if sign > 0 else azimuth_deg + 180.0
        body = body.fuse(arm(arm_length, arm_width, height, z_lo, az))
        d = direction(az)
        body = body.fuse(
            Part.makeCylinder(
                post_radius,
                height,
                App.Vector(d.x * arm_length, d.y * arm_length, z_lo),
                App.Vector(0, 0, 1),
            )
        )
    return body.removeSplitter()


def distance_to_rod_axis(point, azimuth_deg):
    """Perpendicular distance from a point to a rod's axis line, in plan."""
    d = direction(azimuth_deg)
    return abs(point.x * d.y - point.y * d.x)


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
def build(values, fan_gaps=None):
    gaps = list(fan_gaps or DEFAULT_FAN_GAPS)
    azimuths = azimuths_from_gaps(gaps)

    rod_d = values["rodDiameter"]
    channel_r = rod_d / 2.0 + values["rodClearance"] / 2.0
    wall = values["minimumWall"]

    # Rod 1 innermost, rod 4 outermost; adjacent rods touch.
    levels = [(k - 1.5) * rod_d for k in range(4)]

    z_base_top = levels[0]                       # rod 1 axis: the base's seat
    z_base_bottom = levels[0] - channel_r - values["baseFloor"]
    z_cap_bottom = levels[3]                     # rod 4 axis: the cap's seat
    z_cap_top = levels[3] + channel_r + values["capThickness"]

    # --- where the bolts can go ------------------------------------------
    bolt_azimuth = widest_gap_bisector(azimuths, gaps)
    bolt_dir = direction(bolt_azimuth)
    post_r = values["fastenerHeadDiameter"] / 2.0 + wall
    # The post must clear every rod. The nearest rod line governs.
    closest = min(
        abs(math.sin(math.radians(bolt_azimuth - a))) for a in azimuths
    )
    bolt_offset = (post_r + channel_r + wall * values["postWallFactor"]) / closest
    body_r = bolt_offset + post_r + values["edgeRadius"]

    # The channel length is DERIVED from the footprint, never given. A fixed
    # length shorter than the body leaves a blind pocket and the rod cannot be
    # inserted at all -- which is exactly what a hand-picked 76 mm did on the
    # first attempt, at a body that came out 91 mm across.
    length = 2.0 * (body_r + values["channelOverrun"])
    tilt_slack = (length / 2.0) * math.tan(math.radians(values["tiltAllowance"]))

    bolt_points = [
        App.Vector(bolt_dir.x * bolt_offset, bolt_dir.y * bolt_offset, 0.0),
        App.Vector(-bolt_dir.x * bolt_offset, -bolt_dir.y * bolt_offset, 0.0),
    ]

    # --- cut volumes ------------------------------------------------------
    rods = [rod_solid(rod_d / 2.0, length, azimuths[k], levels[k]) for k in range(4)]
    channels = [
        rod_channel(channel_r, length * 1.02, azimuths[k], levels[k], tilt_slack)
        for k in range(4)
    ]
    channel_cut = channels[0]
    for c in channels[1:]:
        channel_cut = channel_cut.fuse(c)
    channel_cut = channel_cut.removeSplitter()

    shank_r = (values["fastenerDiameter"] + values["boltHoleClearance"]) / 2.0
    bolts = []
    bolt_cuts = []
    for p in bolt_points:
        start = App.Vector(p.x, p.y, z_base_bottom - 1.0)
        height = (z_cap_top + 1.0) - (z_base_bottom - 1.0)
        bolts.append(
            Part.makeCylinder(
                values["fastenerDiameter"] / 2.0, height, start, App.Vector(0, 0, 1)
            )
        )
        bolt_cuts.append(
            Part.makeCylinder(shank_r, height, start, App.Vector(0, 0, 1))
        )
        # Captive nut pocket in the underside of the base. The base prints
        # with that face on the bed, so the pocket opens downward and is free;
        # the step up to the shank hole would be a ceiling, hence the cone.
        # The pocket runs from below the bed up to exactly where the cone
        # starts. Leaving even a micron between them exposes the pocket's top
        # face as a flat ring with nothing under it -- a 32 mm2 ceiling the
        # printer would have to bridge, for the sake of a rounding gap.
        nut_top = z_base_bottom + values["nutRecessDepth"]
        bolt_cuts.append(
            hex_prism(
                values["nutAcrossFlats"],
                values["nutRecessDepth"] + 1.0,
                App.Vector(p.x, p.y, z_base_bottom - 1.0),
            )
        )
        nut_circum_r = values["nutAcrossFlats"] / math.sqrt(3.0)
        bolt_cuts.append(
            Part.makeCone(
                nut_circum_r,
                shank_r,
                values["nutConeHeight"],
                App.Vector(p.x, p.y, nut_top),
                App.Vector(0, 0, 1),
            )
        )

    hub_r = values["hubRadiusFactor"] * rod_d
    arm_w = values["armWidthFactor"] * post_r * 2.0

    # --- base -------------------------------------------------------------
    base = plate(
        hub_r, bolt_offset, arm_w, post_r, z_base_bottom, z_base_top, bolt_azimuth
    )
    for p in bolt_points:
        base = base.fuse(
            Part.makeCylinder(
                post_r,
                z_cap_bottom - values["clampGap"] - z_base_bottom,
                App.Vector(p.x, p.y, z_base_bottom),
                App.Vector(0, 0, 1),
            )
        )
    base = base.removeSplitter().cut(channel_cut)
    for c in bolt_cuts:
        base = base.cut(c)

    # --- cap --------------------------------------------------------------
    cap = plate(
        hub_r, bolt_offset, arm_w, post_r, z_cap_bottom, z_cap_top, bolt_azimuth
    )
    cap = cap.cut(channel_cut)
    head_r = (values["fastenerHeadDiameter"] + values["headClearance"]) / 2.0
    for p in bolt_points:
        cap = cap.cut(
            Part.makeCylinder(
                shank_r,
                z_cap_top - z_cap_bottom + 2.0,
                App.Vector(p.x, p.y, z_cap_bottom - 1.0),
                App.Vector(0, 0, 1),
            )
        )
        cap = cap.cut(
            Part.makeCylinder(
                head_r,
                values["headBoreDepth"] + 1.0,
                App.Vector(p.x, p.y, z_cap_top - values["headBoreDepth"]),
                App.Vector(0, 0, 1),
            )
        )
        # The cap prints upside down so its saddle faces up; the counterbore
        # then opens at the bed and the step down to the shank needs a taper.
        cap = cap.cut(
            Part.makeCone(
                shank_r,
                head_r,
                values["headConeHeight"],
                App.Vector(
                    p.x,
                    p.y,
                    z_cap_top - values["headBoreDepth"] - values["headConeHeight"],
                ),
                App.Vector(0, 0, 1),
            )
        )

    geo = {
        "base": base,
        "cap": cap,
        "rods": rods,
        "bolts": bolts,
        "channel_cut": channel_cut,
    }
    dims = {
        "fan_gaps_deg": gaps,
        "fan_azimuths_deg": azimuths,
        "rod_levels_mm": levels,
        "stack_height_mm": levels[3] - levels[0],
        "channel_radius_mm": channel_r,
        "channel_length_mm": length,
        "tilt_slack_mm": tilt_slack,
        "bolt_azimuth_deg": bolt_azimuth,
        "bolt_offset_mm": bolt_offset,
        "post_radius_mm": post_r,
        "body_radius_mm": body_r,
        "assembly_height_mm": z_cap_top - z_base_bottom,
        "bolt_length_needed_mm": (z_cap_top - z_base_bottom)
        - values["headBoreDepth"]
        + 6.0,
        "z_base_bottom": z_base_bottom,
        "z_base_top": z_base_top,
        "z_cap_bottom": z_cap_bottom,
        "z_cap_top": z_cap_top,
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


def _outward_normal(shape, face, u, v, eps=0.05):
    """Outward normal, decided by probing rather than by face.Orientation.

    Orientation is easy to get wrong after fuses, cuts and mirrors, and a
    flipped sign turns every upward face into an overhang. Stepping off the
    surface and asking the solid whether that point is inside settles it.
    """
    p = face.valueAt(u, v)
    n = face.normalAt(u, v)
    probe = App.Vector(p.x + n.x * eps, p.y + n.y * eps, p.z + n.z * eps)
    if shape.isInside(probe, 1e-7, True):
        return App.Vector(-n.x, -n.y, -n.z)
    return n


def printability(shape, flipped=False, samples=5):
    """Overhangs and unsupported ceilings for one print orientation.

    ``flipped=True`` means the part is printed upside down: the bed is at its
    ZMax and the build direction is -Z. Mirroring the shape instead would
    reverse face orientations and make every upward face read as an overhang,
    which is a way to fail this check on a perfectly good part.

    ``worst_overhang_deg`` is measured from horizontal: 90 is a vertical wall,
    45 the usual FDM limit, 0 a flat ceiling with nothing under it.
    ``flat_ceiling_area_mm2`` is the area facing away from the bed that a
    slicer would have to bridge or support.
    """
    sign = 1.0 if flipped else -1.0
    bed_z = shape.BoundBox.ZMax if flipped else shape.BoundBox.ZMin
    worst = 90.0
    worst_at = None
    worst_area = 0.0
    flat_area = 0.0
    for face in shape.Faces:
        u0, u1, v0, v1 = face.ParameterRange
        normals = []
        for i in range(samples):
            for j in range(samples):
                u = u0 + (u1 - u0) * (i + 0.5) / samples
                v = v0 + (v1 - v0) * (j + 0.5) / samples
                # The parameter rectangle covers the whole underlying surface,
                # including the holes cut out of a trimmed face. Sampling
                # there reads a normal for material that is not present, and
                # the probe then lands inside the solid and flips the sign --
                # which is how a flat top face came to be reported as a 0 deg
                # overhang.
                try:
                    if not face.isPartOfDomain(u, v):
                        continue
                    normals.append(_outward_normal(shape, face, u, v))
                except Exception:
                    continue
        if not normals:
            continue
        box = face.BoundBox
        on_bed = abs(box.ZMax - bed_z) < 0.01 and abs(box.ZMin - bed_z) < 0.01
        if on_bed:
            continue
        for n in normals:
            if n.z * sign <= 1e-3:
                continue
            angle = math.degrees(math.acos(min(1.0, abs(n.z))))
            if angle < worst:
                worst = angle
                worst_at = (round(box.ZMin, 2), round(box.ZMax, 2))
                worst_area = round(face.Area, 2)
        flat = [n for n in normals if n.z * sign > 0.999]
        if len(flat) == len(normals):
            flat_area += face.Area
    return {
        "worst_overhang_deg": round(worst, 2),
        "worst_overhang_z_range": worst_at,
        "worst_overhang_face_area_mm2": worst_area,
        "flat_ceiling_area_mm2": round(flat_area, 2),
    }


def verify(geo, dims, values):
    """Check the things that would make the part unusable, not that it is good."""
    report = {}

    for name in ("base", "cap"):
        shape = geo[name]
        report[name] = {
            "valid": shape.isValid(),
            "solids": len(shape.Solids),
            "volume_cm3": round(_vol(shape) / 1000.0, 2),
        }

    # Nothing may occupy a rod's space, or a bolt's.
    interference = {}
    for name in ("base", "cap"):
        for i, rod in enumerate(geo["rods"], start=1):
            interference[f"{name}_x_rod{i}"] = round(
                _vol(geo[name].common(rod)), 4
            )
        for j, bolt in enumerate(geo["bolts"]):
            interference[f"{name}_x_bolt{j}"] = round(_vol(geo[name].common(bolt)), 4)
    interference["base_x_cap"] = round(_vol(geo["base"].common(geo["cap"])), 4)
    report["interference_mm3"] = interference

    # A rod as long as the reference rod proves nothing: if the channel ends
    # blind inside the body, a rod of the same length ends blind too and the
    # intersection is still zero. Probe with a rod several times the footprint,
    # which only clears if the channel runs right through.
    probe_length = dims["body_radius_mm"] * 6.0
    blind = {}
    for i, azimuth in enumerate(dims["fan_azimuths_deg"], start=1):
        probe = rod_solid(
            values["rodDiameter"] / 2.0,
            probe_length,
            azimuth,
            dims["rod_levels_mm"][i - 1],
        )
        blind[f"rod{i}"] = round(
            _vol(geo["base"].common(probe)) + _vol(geo["cap"].common(probe)), 4
        )
    report["blind_channel_mm3"] = blind

    # Release: the base must not reach above rod 1's axis inside the rods'
    # footprint, and the cap must not reach below rod 4's axis, or the rods
    # could not be dropped in.
    body_r = dims["body_radius_mm"]
    above = Part.makeCylinder(
        body_r * 2,
        dims["z_cap_top"] - dims["z_base_top"] + 1.0,
        App.Vector(0, 0, dims["z_base_top"]),
        App.Vector(0, 0, 1),
    )
    posts_only = geo["base"].common(above)
    # Everything the base has above the seat must be the posts: check it does
    # not overhang any rod.
    overhang = 0.0
    for rod in geo["rods"]:
        overhang += _vol(posts_only.common(rod))
    report["release"] = {
        "base_material_above_seat_cm3": round(_vol(posts_only) / 1000.0, 2),
        "base_overhang_into_rods_mm3": round(overhang, 4),
        "cap_min_z": round(geo["cap"].BoundBox.ZMin, 3),
        "rod4_axis_z": round(dims["rod_levels_mm"][3], 3),
    }

    # Printing: the base sits on its underside, the cap is flipped so its
    # saddle faces up, which is why the cap is analysed mirrored.
    report["printability"] = {
        "base": printability(geo["base"], flipped=False),
        "cap_printed_upside_down": printability(geo["cap"], flipped=True),
    }

    # Clearances that decide whether it can be printed and bolted.
    report["key_dims"] = {
        "stack_height_mm": round(dims["stack_height_mm"], 3),
        "assembly_height_mm": round(dims["assembly_height_mm"], 3),
        "footprint_diameter_mm": round(dims["body_radius_mm"] * 2, 3),
        "bolt_offset_mm": round(dims["bolt_offset_mm"], 3),
        "bolt_length_needed_mm": round(dims["bolt_length_needed_mm"], 1),
        "channel_diameter_mm": round(dims["channel_radius_mm"] * 2, 3),
        "tilt_slack_mm": round(dims["tilt_slack_mm"], 3),
        "post_to_nearest_rod_mm": round(
            min(
                distance_to_rod_axis(
                    App.Vector(
                        math.cos(math.radians(dims["bolt_azimuth_deg"]))
                        * dims["bolt_offset_mm"],
                        math.sin(math.radians(dims["bolt_azimuth_deg"]))
                        * dims["bolt_offset_mm"],
                        0.0,
                    ),
                    a,
                )
                for a in dims["fan_azimuths_deg"]
            )
            - dims["post_radius_mm"]
            - dims["channel_radius_mm"],
            3,
        ),
    }
    return report


def derived_rows(dims, values):
    rows = []
    for key, value in dims.items():
        if isinstance(value, (int, float)):
            rows.append((key, round(value, 4), "", "derived"))
        else:
            rows.append((key, str(value), "", "derived"))
    return rows


def populate(doc, geo):
    keep = {"Parameters"}
    for o in reversed(list(doc.Objects)):
        if o.Name in keep or o.Label in keep:
            continue
        try:
            doc.removeObject(o.Name)
        except Exception:
            pass

    base = doc.addObject("Part::Feature", "FanBase")
    base.Label = "FanBase"
    base.Shape = geo["base"]

    cap = doc.addObject("Part::Feature", "FanCap")
    cap.Label = "FanCap"
    cap.Shape = geo["cap"]

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
    return base, cap


def write_parameters(doc, sheet, values, derived):
    if sheet is None:
        for o in doc.Objects:
            if o.Name == "Parameters" or o.Label == "Parameters":
                sheet = o
                break
    if sheet is None:
        sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
        sheet.Label = "Parameters"
    sheet.clearAll()
    sheet.set("A1", "Star Dome four-rod fan node V1 - parameters")
    row = 3
    sheet.set(f"A{row}", "INPUT")
    row += 1
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
    return sheet


def run(fan_gaps=None, out_dir=None):
    doc = (
        App.getDocument(DOC_NAME)
        if DOC_NAME in App.listDocuments()
        else App.newDocument(DOC_NAME)
    )
    values = {alias: value for (alias, value, _u, _n) in INPUTS}
    geo, dims = build(values, fan_gaps)
    populate(doc, geo)
    write_parameters(doc, None, values, derived_rows(dims, values))
    doc.recompute()

    report = verify(geo, dims, values)
    if out_dir:
        path = os.path.join(out_dir, "star_dome_fan_node_v1.FCStd")
        doc.saveAs(path)
        report["saved_to"] = path
    return report


if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint

    pprint.pprint(REPORT, width=110)
