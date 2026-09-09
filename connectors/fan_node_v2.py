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

Open the pitch by a web thickness and every pair has room between it. Then the
part becomes a stack of plates, each carrying a channel on both faces:

    pitch = 2 * channelRadius + webThickness

Every rod ends up in a real channel, wrapped 180 deg from below by one plate
and 180 deg from above by the next. No rod touches another rod, which also
removes the three crossed-cylinder contacts on fibreglass that V1's own notes
flagged as the first thing to check on a printed prototype.

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

Helpers are copied from fan_node_v1.py rather than shared. All three connector
scripts are exec'd standalone inside FreeCAD, so sharing needs a path loader in
each; that refactor is worth doing once the family settles, not while its
architecture is still moving.

Run:  exec(open('.../connectors/fan_node_v2.py').read()) inside FreeCAD, or
through connectors/generate_clamps.py, which drives it from the model data.
"""

import math
import os

import FreeCAD as App
import Part

DOC_NAME = "StarDome_FanNode_V2"
USE_SPREADSHEET_IF_PRESENT = True

DEFAULT_FAN_GAPS = [37.377368, 41.810315, 37.377368, 63.434949]

PLATE_NAMES = ["Bottom", "Mid1", "Mid2", "Mid3", "Cap"]

OVERHANG_LIMIT_DEG = 45.0
NEGLIGIBLE_FACE_MM2 = 5.0

INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance added to each rod channel"),
    ("webThickness",           3.0,  "mm",  "material between two stacked rods; sets the stack pitch"),
    ("channelOverrun",         6.0,  "mm",  "how far each channel runs past the body; channel length is DERIVED"),
    ("minimumWall",            4.0,  "mm",  "minimum structural wall thickness"),
    ("baseFloor",              5.0,  "mm",  "material under the bottom plate's channel"),
    ("capThickness",           6.0,  "mm",  "material above the cap's channel"),
    ("tiltAllowance",          1.5,  "deg", "radial tilt a rod may arrive with; the weave needs up to 1.2 deg"),
    ("teardropRoof",           1.0,  "-",   "1 = give every downward channel a 45 deg roof so it prints unsupported"),
    ("fastenerDiameter",       5.5,  "mm",  "M5 clearance hole diameter"),
    ("fastenerHeadDiameter",  10.0,  "mm",  "M5 head / washer outside diameter"),
    ("headClearance",          0.6,  "mm",  "diametral clearance for the head counterbore"),
    ("headBoreDepth",          4.4,  "mm",  "counterbore depth for head + washer"),
    ("headConeHeight",         2.8,  "mm",  "taper off the head counterbore, so the cap prints upside down"),
    ("nutAcrossFlats",         8.3,  "mm",  "M5 nut across flats + fit clearance"),
    ("nutRecessDepth",         4.6,  "mm",  "captive nut pocket depth"),
    ("nutConeHeight",          2.2,  "mm",  "taper off the nut pocket, so the bottom plate prints on the bed"),
    ("boltHoleClearance",      0.4,  "mm",  "diametral print clearance on the bolt shank hole"),
    ("hubRadiusFactor",        2.2,  "-",   "hub radius as a multiple of rodDiameter; sets channel length"),
    ("armWidthFactor",         1.6,  "-",   "arm width as a multiple of the boss diameter"),
    ("edgeRadius",             2.0,  "mm",  "outer edge radius"),
    ("rimFilletFactor",        0.6,  "-",   "rim fillet as a fraction of edgeRadius"),
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def azimuths_from_gaps(gaps):
    out = [0.0]
    for gap in gaps[:-1]:
        out.append(out[-1] + gap)
    return out


def widest_gap_bisector(azimuths, gaps):
    widest = max(range(len(gaps)), key=lambda i: gaps[i])
    return azimuths[widest % len(azimuths)] + gaps[widest] / 2.0


def direction(azimuth_deg):
    a = math.radians(azimuth_deg)
    return App.Vector(math.cos(a), math.sin(a), 0.0)


def rod_solid(radius, length, azimuth_deg, z):
    d = direction(azimuth_deg)
    base = App.Vector(-d.x * length / 2.0, -d.y * length / 2.0, z)
    return Part.makeCylinder(radius, length, base, d)


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


def rod_channel(radius, length, azimuth_deg, z, tilt_slack, roof=False):
    """Channel for one rod, stretched vertically for tilt, optionally gabled."""
    body = rod_solid(radius, length, azimuth_deg, z)
    if tilt_slack > 0.0:
        for dz in (-tilt_slack, tilt_slack):
            body = body.fuse(rod_solid(radius, length, azimuth_deg, z + dz))
    if roof:
        body = body.fuse(teardrop_roof(radius, length, azimuth_deg, z + tilt_slack))
    return body.removeSplitter()


def hex_prism(across_flats, height, base):
    r = across_flats / math.sqrt(3.0)
    pts = []
    for i in range(6):
        a = math.radians(60 * i)
        pts.append(App.Vector(base.x + r * math.cos(a), base.y + r * math.sin(a), base.z))
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, 0, height))


def arm(length, width, height, z, azimuth_deg):
    box = Part.makeBox(length, width, height, App.Vector(0.0, -width / 2.0, z))
    box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    return box


def plate_blank(hub_radius, arm_length, arm_width, boss_radius, z_lo, z_hi, azimuth_deg):
    """Hub, two spars, two bolt bosses. The channels get cut out of this."""
    height = z_hi - z_lo
    body = Part.makeCylinder(
        hub_radius, height, App.Vector(0, 0, z_lo), App.Vector(0, 0, 1)
    )
    for az in (azimuth_deg, azimuth_deg + 180.0):
        body = body.fuse(arm(arm_length, arm_width, height, z_lo, az))
        d = direction(az)
        body = body.fuse(
            Part.makeCylinder(
                boss_radius,
                height,
                App.Vector(d.x * arm_length, d.y * arm_length, z_lo),
                App.Vector(0, 0, 1),
            )
        )
    return body.removeSplitter()


def _ok(shape):
    try:
        return shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 0
    except Exception:
        return False


def fillet_by_predicate(shape, pred, radius, max_pass=2):
    if radius <= 0:
        return shape, 0
    edges = [e for e in shape.Edges if pred(e)]
    if not edges:
        return shape, 0
    for r in (radius, radius * 0.7, radius * 0.45):
        try:
            out = shape.makeFillet(r, edges).removeSplitter()
            if _ok(out):
                return out, len(edges)
        except Exception:
            pass
    out = shape
    done = set()
    applied = 0
    for _ in range(len(edges) * max_pass):
        target = None
        for e in out.Edges:
            if not pred(e):
                continue
            key = tuple(
                round(c, 3)
                for c in (e.CenterOfMass.x, e.CenterOfMass.y, e.CenterOfMass.z)
            )
            if key in done:
                continue
            target = (e, key)
            break
        if target is None:
            break
        e, key = target
        done.add(key)
        for r in (radius, radius * 0.7, radius * 0.45, radius * 0.25):
            try:
                candidate = out.makeFillet(r, [e]).removeSplitter()
                if _ok(candidate):
                    out = candidate
                    applied += 1
                    break
            except Exception:
                pass
    return out, applied


def is_vertical_edge(edge, tol=1e-6):
    try:
        if not isinstance(edge.Curve, Part.Line):
            return False
    except Exception:
        return False
    d = edge.Vertexes[-1].Point.sub(edge.Vertexes[0].Point)
    return abs(d.x) < tol and abs(d.y) < tol and abs(d.z) > tol


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
def build(values, fan_gaps=None):
    gaps = list(fan_gaps or DEFAULT_FAN_GAPS)
    azimuths = azimuths_from_gaps(gaps)

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
    # webThickness is the material that actually remains at the thinnest point,
    # which is above the lower channel and below the upper one:
    #
    #   both channels are stretched by tilt_slack, top and bottom;
    #   a gabled channel reaches sqrt(2)*channel_r above its axis, not
    #   channel_r, so the roof eats a further 0.414*channel_r.
    #
    # Setting pitch to 2*channel_r + web, as the first attempt did, left 0.85 mm
    # of web instead of 3 -- and that web is the piece carrying the clamping
    # load between two rods.
    upper_reach = channel_r * math.sqrt(2.0) if roof else channel_r
    pitch = values["webThickness"] + channel_r + upper_reach + 2.0 * tilt_slack
    levels = [(k - 1.5) * pitch for k in range(4)]

    z_bottom = levels[0] - channel_r - tilt_slack - values["baseFloor"]
    z_top = levels[3] + channel_r + tilt_slack + values["capThickness"]

    bolt_points = [
        App.Vector(direction(az).x * bolt_offset, direction(az).y * bolt_offset, 0.0)
        for az in (bolt_azimuth, bolt_azimuth + 180.0)
    ]

    shank_r = (values["fastenerDiameter"] + values["boltHoleClearance"]) / 2.0
    head_r = (values["fastenerHeadDiameter"] + values["headClearance"]) / 2.0

    rods = [rod_solid(rod_d / 2.0, length, azimuths[k], levels[k]) for k in range(4)]
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
                    tilt_slack,
                    roof=roof and downward,
                )
            )

        for cut in shank_cut():
            body = body.cut(cut)

        if index == 0:
            nut_top = z_bottom + values["nutRecessDepth"]
            for p in bolt_points:
                body = body.cut(
                    hex_prism(
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

        body, n_vertical = fillet_by_predicate(
            body, is_vertical_edge, values["edgeRadius"]
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
        "fan_gaps_deg": gaps,
        "fan_azimuths_deg": azimuths,
        "rod_levels_mm": levels,
        "stack_pitch_mm": pitch,
        "web_thickness_mm": values["webThickness"],
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
def _vol(shape):
    try:
        return shape.Volume
    except Exception:
        return 0.0


def _outward_normal(shape, face, u, v, eps=0.05):
    p = face.valueAt(u, v)
    n = face.normalAt(u, v)
    probe = App.Vector(p.x + n.x * eps, p.y + n.y * eps, p.z + n.z * eps)
    if shape.isInside(probe, 1e-7, True):
        return App.Vector(-n.x, -n.y, -n.z)
    return n


def printability(shape, flipped=False, samples=5):
    """Overhangs for one print orientation. See docs/fan-node-v1.md for the
    five ways this check was wrong before it was right."""
    sign = 1.0 if flipped else -1.0
    zs = [v.Point.z for v in shape.Vertexes]
    if not zs:
        return {}
    bed_z = max(zs) if flipped else min(zs)
    worst = 90.0
    worst_area = 0.0
    steep_area = 0.0
    flat_area = 0.0
    for face in shape.Faces:
        u0, u1, v0, v1 = face.ParameterRange
        normals = []
        for i in range(samples):
            for j in range(samples):
                u = u0 + (u1 - u0) * (i + 0.5) / samples
                v = v0 + (v1 - v0) * (j + 0.5) / samples
                try:
                    if not face.isPartOfDomain(u, v):
                        continue
                    normals.append(_outward_normal(shape, face, u, v))
                except Exception:
                    continue
        if not normals:
            continue
        face_zs = [vx.Point.z for vx in face.Vertexes]
        if not face_zs:
            continue
        if abs(max(face_zs) - bed_z) < 0.01 and abs(min(face_zs) - bed_z) < 0.01:
            continue
        face_worst = 90.0
        for n in normals:
            if n.z * sign <= 1e-3:
                continue
            face_worst = min(face_worst, math.degrees(math.acos(min(1.0, abs(n.z)))))
        if face_worst < OVERHANG_LIMIT_DEG:
            steep_area += face.Area
        if face.Area >= NEGLIGIBLE_FACE_MM2 and face_worst < worst:
            worst = face_worst
            worst_area = round(face.Area, 2)
        if all(n.z * sign > 0.999 for n in normals):
            flat_area += face.Area
    return {
        "worst_overhang_deg": round(worst, 2),
        "worst_overhang_face_area_mm2": worst_area,
        "area_steeper_than_limit_mm2": round(steep_area, 2),
        "flat_ceiling_area_mm2": round(flat_area, 2),
    }


def verify(geo, dims, values):
    report = {"plates": {}}
    plates = geo["plates"]
    names = geo["names"]

    for name, shape, (z_lo, z_hi) in zip(names, plates, dims["plate_spans_mm"]):
        zs = [v.Point.z for v in shape.Vertexes]
        report["plates"][name] = {
            "valid": shape.isValid(),
            "solids": len(shape.Solids),
            "volume_cm3": round(_vol(shape) / 1000.0, 2),
            "z_span": (round(min(zs), 3), round(max(zs), 3)),
            "z_span_expected": (round(z_lo, 3), round(z_hi, 3)),
        }

    # Nothing may occupy a rod's or a bolt's space.
    interference = {}
    for name, shape in zip(names, plates):
        for i, rod in enumerate(geo["rods"], start=1):
            interference[f"{name}_x_rod{i}"] = round(_vol(shape.common(rod)), 4)
        for j, bolt in enumerate(geo["bolts"]):
            interference[f"{name}_x_bolt{j}"] = round(_vol(shape.common(bolt)), 4)
    for a in range(len(plates)):
        for b in range(a + 1, len(plates)):
            interference[f"{names[a]}_x_{names[b]}"] = round(
                _vol(plates[a].common(plates[b])), 4
            )
    report["interference_mm3"] = interference

    # A channel that ends blind inside a plate cannot take a rod. Probe with a
    # rod several times the footprint; only a through channel clears it.
    probe_length = dims["body_radius_mm"] * 6.0
    blind = {}
    for i, azimuth in enumerate(dims["fan_azimuths_deg"], start=1):
        probe = rod_solid(
            values["rodDiameter"] / 2.0, probe_length, azimuth, dims["rod_levels_mm"][i - 1]
        )
        blind[f"rod{i}"] = round(sum(_vol(p.common(probe)) for p in plates), 4)
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

    # Measure the web rather than trusting the pitch arithmetic: walk the
    # node's own axis, where the two channels come closest, and see how much
    # material is actually left between them.
    step = 0.05
    webs = {}
    for name, shape, (z_lo, z_hi) in zip(names, plates, dims["plate_spans_mm"]):
        if name == "Bottom" or name == "Cap":
            continue
        solid_mm = 0.0
        z = z_lo
        while z <= z_hi:
            if shape.isInside(App.Vector(0.0, 0.0, z), 1e-7, True):
                solid_mm += step
            z += step
        webs[name] = round(solid_mm, 2)
    report["web_measured_mm"] = webs
    report["web_requested_mm"] = round(values["webThickness"], 3)

    # The cap prints flipped so its channel faces up; every other plate prints
    # with its upward channel up.
    report["printability"] = {
        name: printability(shape, flipped=(name == "Cap"))
        for name, shape in zip(names, plates)
    }

    report["key_dims"] = {
        "stack_pitch_mm": round(dims["stack_pitch_mm"], 3),
        "web_thickness_mm": round(dims["web_thickness_mm"], 3),
        "stack_height_mm": round(dims["stack_height_mm"], 3),
        "assembly_height_mm": round(dims["assembly_height_mm"], 3),
        "footprint_diameter_mm": round(dims["body_radius_mm"] * 2, 3),
        "bolt_offset_mm": round(dims["bolt_offset_mm"], 3),
        "bolt_length_needed_mm": round(dims["bolt_length_needed_mm"], 1),
        "channel_diameter_mm": round(dims["channel_radius_mm"] * 2, 3),
        "tilt_slack_mm": round(dims["tilt_slack_mm"], 3),
        "total_volume_cm3": round(sum(_vol(p) for p in plates) / 1000.0, 2),
        "pieces_per_node": len(plates),
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
    sheet.set("A1", "Star Dome four-rod fan node V2 - parameters")
    row = 3
    sheet.set(f"A{row}", "INPUT")
    row += 1
    for alias, value, unit, note in INPUTS:
        sheet.set(f"A{row}", alias)
        sheet.set(f"B{row}", repr(float(values.get(alias, value))))
        sheet.set(f"C{row}", unit)
        sheet.set(f"D{row}", note)
        # Without an alias the cell is a report, not a parameter store.
        try:
            sheet.setAlias(f"B{row}", alias)
        except Exception:
            pass
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


def read_or_build_parameters(doc):
    sheet = None
    for o in doc.Objects:
        if o.Name == "Parameters" or o.Label == "Parameters":
            sheet = o
            break
    values = {alias: value for (alias, value, _u, _n) in INPUTS}
    if sheet is not None and USE_SPREADSHEET_IF_PRESENT:
        for alias in list(values):
            try:
                values[alias] = float(sheet.get(alias))
            except Exception:
                pass
    return sheet, values


def run(fan_gaps=None, out_dir=None, doc_path=None):
    if doc_path and os.path.exists(doc_path):
        doc = App.openDocument(doc_path)
    elif DOC_NAME in App.listDocuments():
        doc = App.getDocument(DOC_NAME)
    else:
        doc = App.newDocument(DOC_NAME)
    sheet, values = read_or_build_parameters(doc)
    geo, dims = build(values, fan_gaps)
    report = verify(geo, dims, values)
    populate(doc, geo)
    write_parameters(doc, sheet, values, derived_rows(dims, values))
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
