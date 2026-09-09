# -*- coding: utf-8 -*-
"""
Star Dome crossing clamp, prototype V1.

Two-piece clamp for two round GFRP rods that CROSS and CONTINUE through the
connector. The rods are not terminated by the connector; they are located and
clamped at the crossing while the rods themselves carry the structural load.

Architecture (see docs/crossing-clamp-v1.md for the reasoning):

    BottomClamp  - lower saddle. Holds the LOWER rod (rod B) in a 180 deg
                   U-channel that is open upward, and carries two raised
                   saddle segments that support the UPPER rod (rod A) from
                   below. Its top face (the seat) sits at the level of rod A's
                   axis minus clampGap.
    TopClamp     - cap. A 180 deg saddle over the UPPER rod (rod A), with two
                   bolt ears. Bolts pull it down, rod A is pressed onto rod B,
                   rod B is pressed into its channel: one bolted joint clamps
                   both rods.

Both halves print flat-on-bed with every rod groove facing up (print the cap
upside down). No supports required.

Run:  exec(open('/Users/danilaorehov/star-dome/connectors/crossing_clamp_v1.py').read())
inside FreeCAD, or via the FreeCAD MCP bridge.
"""

import math
import os

import FreeCAD as App
import Part

DOC_NAME = "StarDome_CrossingClamp_V1"
OUT_DIR = "/Users/danilaorehov/star-dome/connectors"
SAVE_PATH = os.path.join(OUT_DIR, "star_dome_crossing_clamp_v1.FCStd")

# If the document already carries a Parameters spreadsheet, its values win over
# the defaults below. That makes the spreadsheet the editable parameter store.
USE_SPREADSHEET_IF_PRESENT = True

# --------------------------------------------------------------------------
# Input parameters. Units: mm, degrees.
# --------------------------------------------------------------------------
INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance added to each rod channel"),
    ("crossingAngle",         72.0,  "deg", "angle between the two rod axes in plan view"),
    ("channelLength",         55.0,  "mm",  "length of each rod channel through the body"),
    ("verticalSeparation",    10.0,  "mm",  "distance between rod axes; forced to rodDiameter so the upper rod bears on the lower one"),
    ("minimumWall",            4.0,  "mm",  "minimum structural wall thickness"),
    ("edgeRadius",             4.0,  "mm",  "outer edge / corner radius"),
    ("fastenerDiameter",       5.5,  "mm",  "M5 clearance hole diameter"),
    ("fastenerHeadDiameter",  10.0,  "mm",  "M5 head / washer outside diameter"),
    # --- secondary inputs -------------------------------------------------
    ("capThickness",           6.0,  "mm",  "TopClamp material above the upper rod; it works in bending between the bolts"),
    ("clampGap",               1.2,  "mm",  "designed open gap at the parting faces; the bolts always squeeze the rods, faces never bottom out"),
    ("headClearance",          0.6,  "mm",  "diametral clearance for the head/washer counterbore"),
    ("headBoreDepth",          4.4,  "mm",  "counterbore depth for head + washer"),
    ("headConeHeight",         2.8,  "mm",  "tapered transition under the counterbore, printable upside down"),
    ("nutConeHeight",          2.2,  "mm",  "tapered transition above the nut pocket"),
    ("nutAcrossFlats",         8.3,  "mm",  "M5 nut across flats + fit clearance"),
    ("nutRecessDepth",         4.6,  "mm",  "captive nut pocket depth"),
    ("boltHoleClearance",      0.4,  "mm",  "diametral print clearance on the bolt shank hole"),
    ("flareLength",            5.0,  "mm",  "axial length of the flared channel entrance"),
    ("flareSlope",             0.2,  "mm",  "radial rise per mm of the entrance flare"),
    ("boltMargin",             0.0,  "mm",  "extra radial margin pushing the bolts away from the rods"),
]

DERIVED_NOTE = "derived - overwritten by the generator"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def axis_dir(angle_deg):
    a = math.radians(angle_deg)
    return App.Vector(math.cos(a), math.sin(a), 0.0)


def capsule_prism(length, half_width, z_lo, z_hi, angle_deg):
    """Stadium/capsule footprint extruded between two z levels, rotated in plan."""
    h = z_hi - z_lo
    straight = length - 2.0 * half_width
    box = Part.makeBox(straight, 2.0 * half_width, h,
                       App.Vector(-straight / 2.0, -half_width, z_lo))
    c1 = Part.makeCylinder(half_width, h, App.Vector(-straight / 2.0, 0, z_lo))
    c2 = Part.makeCylinder(half_width, h, App.Vector(straight / 2.0, 0, z_lo))
    s = box.fuse(c1).fuse(c2).removeSplitter()
    s = s.copy()
    s.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle_deg)
    return s


def rod_cylinder(radius, length, angle_deg, z):
    d = axis_dir(angle_deg)
    base = App.Vector(-d.x * length / 2.0, -d.y * length / 2.0, z)
    return Part.makeCylinder(radius, length, base, d)


def rod_slot(half_width, length, angle_deg, z_lo, z_hi):
    """Prismatic slot straight above a rod channel, so the rod can be lifted out."""
    h = z_hi - z_lo
    box = Part.makeBox(length, 2.0 * half_width, h,
                       App.Vector(-length / 2.0, -half_width, z_lo))
    box = box.copy()
    box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle_deg)
    return box


def entrance_flare(radius, angle_deg, z, channel_length, flare_len, slope, overrun):
    """Two cones, one per channel end, opening the mouth into a shallow trumpet."""
    d = axis_dir(angle_deg)
    cones = []
    for sign in (1.0, -1.0):
        dd = App.Vector(d.x * sign, d.y * sign, 0)
        t0 = channel_length / 2.0 - flare_len
        h = flare_len + overrun
        base = App.Vector(dd.x * t0, dd.y * t0, z)
        cones.append(Part.makeCone(radius, radius + slope * h, h, base, dd))
    return cones[0].fuse(cones[1])


def hex_prism(across_flats, height, base):
    r = across_flats / (2.0 * math.cos(math.radians(30.0)))
    pts = []
    for i in range(6):
        a = math.radians(60.0 * i)
        pts.append(App.Vector(base.x + r * math.cos(a), base.y + r * math.sin(a), base.z))
    pts.append(pts[0])
    face = Part.Face(Part.makePolygon(pts))
    return face.extrude(App.Vector(0, 0, height))


def dist_point_to_line(px, py, angle_deg):
    """Perpendicular distance in plan from a point to a line through the origin."""
    a = math.radians(angle_deg)
    return abs(-math.sin(a) * px + math.cos(a) * py)


def _ok(s):
    try:
        return s.isValid() and len(s.Solids) == 1 and s.Volume > 0
    except Exception:
        return False


def fillet_by_predicate(shape, pred, radius, max_pass=2):
    """Fillet every edge matching pred. Falls back to per-edge filleting, and
    silently skips edges that cannot take the radius."""
    if radius <= 0:
        return shape, 0
    edges = [e for e in shape.Edges if pred(e)]
    if not edges:
        return shape, 0
    for r in (radius, radius * 0.7, radius * 0.45):
        try:
            s = shape.makeFillet(r, edges).removeSplitter()
            if _ok(s):
                return s, len(edges)
        except Exception:
            pass
    # per-edge fallback: re-find matching edges after every successful fillet
    out = shape
    done = set()
    applied = 0
    for _ in range(len(edges) * max_pass):
        target = None
        for e in out.Edges:
            if not pred(e):
                continue
            key = tuple(round(c, 3) for c in
                        (e.CenterOfMass.x, e.CenterOfMass.y, e.CenterOfMass.z))
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
                s = out.makeFillet(r, [e]).removeSplitter()
                if _ok(s):
                    out = s
                    applied += 1
                    break
            except Exception:
                pass
    return out, applied


# --------------------------------------------------------------------------
# document / spreadsheet
# --------------------------------------------------------------------------
def fresh_document():
    if DOC_NAME in App.listDocuments():
        doc = App.getDocument(DOC_NAME)
    else:
        doc = App.newDocument(DOC_NAME)
    return doc


def read_or_build_parameters(doc):
    sheet = None
    for o in doc.Objects:
        if o.Name == "Parameters" or o.Label == "Parameters":
            sheet = o
            break
    values = {a: v for (a, v, _u, _n) in INPUTS}
    if sheet is not None and USE_SPREADSHEET_IF_PRESENT:
        for alias in list(values.keys()):
            try:
                got = sheet.get(alias)
                values[alias] = float(got)
            except Exception:
                pass
    return sheet, values


def write_parameters(doc, sheet, values, derived):
    if sheet is None:
        sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
        sheet.Label = "Parameters"
    sheet.clearAll()
    sheet.set("A1", "Star Dome crossing clamp V1 - parameters")
    sheet.set("A2", "INPUT")
    sheet.set("B2", "value")
    sheet.set("C2", "unit")
    sheet.set("D2", "note")
    row = 3
    for alias, _default, unit, note in INPUTS:
        sheet.set("A%d" % row, alias)
        sheet.set("B%d" % row, repr(float(values[alias])))
        sheet.set("C%d" % row, unit)
        sheet.set("D%d" % row, note)
        try:
            sheet.setAlias("B%d" % row, alias)
        except Exception:
            pass
        row += 1

    row += 1
    sheet.set("A%d" % row, "DERIVED")
    sheet.set("B%d" % row, "value")
    sheet.set("C%d" % row, "unit")
    sheet.set("D%d" % row, DERIVED_NOTE)
    row += 1
    for alias, val, unit, note in derived:
        sheet.set("A%d" % row, alias)
        sheet.set("B%d" % row, repr(round(float(val), 4)))
        sheet.set("C%d" % row, unit)
        sheet.set("D%d" % row, note)
        try:
            sheet.setAlias("B%d" % row, alias)
        except Exception:
            pass
        row += 1
    return sheet


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
def build(values):
    D = values["rodDiameter"]
    c = values["rodClearance"]
    ang = values["crossingAngle"]
    L = values["channelLength"]
    wall = values["minimumWall"]
    er = values["edgeRadius"]
    fd = values["fastenerDiameter"]
    fhd = values["fastenerHeadDiameter"]
    clamp_gap = values["clampGap"]
    head_clr = values["headClearance"]
    head_depth = values["headBoreDepth"]
    head_cone_h = values["headConeHeight"]
    nut_cone_h = values["nutConeHeight"]
    cap_t = values["capThickness"]
    nut_af = values["nutAcrossFlats"]
    nut_depth = values["nutRecessDepth"]
    bolt_clr = values["boltHoleClearance"]
    flare_len = values["flareLength"]
    flare_slope = values["flareSlope"]
    bolt_margin = values["boltMargin"]

    chan_d = D + c
    R = chan_d / 2.0                       # rod channel radius
    v = values["verticalSeparation"]       # rod axis separation
    half_ang = ang / 2.0
    angA = +half_ang                       # upper rod
    angB = -half_ang                       # lower rod
    zA = +v / 2.0
    zB = -v / 2.0

    z_seat = zA - clamp_gap                # top face of BottomClamp
    z_cap = zA                             # bottom face of TopClamp
    z_bottom = zB - R - wall
    z_top = zA + R + cap_t

    hw = R + wall                          # capsule half width in plan
    boss_r = fhd / 2.0 + wall
    bolt_offset = ((R + fhd / 2.0 + head_clr / 2.0 + wall + bolt_margin)
                   / math.cos(math.radians(half_ang)))
    bolt_pts = [App.Vector(0, +bolt_offset, 0), App.Vector(0, -bolt_offset, 0)]

    big = max(L, bolt_offset * 2.0) * 4.0

    # ---- shared cutting tools -------------------------------------------
    cyl_a = rod_cylinder(R, big, angA, zA)
    cyl_b = rod_cylinder(R, big, angB, zB)
    flare_a = entrance_flare(R, angA, zA, L, flare_len, flare_slope, 6.0)
    flare_b = entrance_flare(R, angB, zB, L, flare_len, flare_slope, 6.0)
    slot_b = rod_slot(R, big, angB, zB, z_top + 10.0)

    bolt_holes = []
    for p in bolt_pts:
        bolt_holes.append(Part.makeCylinder((fd + bolt_clr) / 2.0, big,
                                            App.Vector(p.x, p.y, z_bottom - 10.0)))
    bolt_cut = bolt_holes[0].fuse(bolt_holes[1])

    # ---- bottom clamp ----------------------------------------------------
    body = capsule_prism(L, hw, z_bottom, z_seat, angA)
    body = body.fuse(capsule_prism(L, hw, z_bottom, z_seat, angB))
    for p in bolt_pts:
        body = body.fuse(Part.makeCylinder(boss_r, z_seat - z_bottom,
                                           App.Vector(p.x, p.y, z_bottom)))
    bottom = body.removeSplitter()

    bottom = bottom.cut(cyl_b).cut(slot_b).cut(cyl_a)
    bottom = bottom.cut(flare_a).cut(flare_b)
    bottom = bottom.cut(bolt_cut)
    for p in bolt_pts:
        nut = hex_prism(nut_af, nut_depth, App.Vector(p.x, p.y, z_bottom - 0.001))
        cone = Part.makeCone(nut_af / (2.0 * math.cos(math.radians(30.0))),
                             (fd + bolt_clr) / 2.0, nut_cone_h,
                             App.Vector(p.x, p.y, z_bottom + nut_depth - 0.001))
        bottom = bottom.cut(nut).cut(cone)
    bottom = bottom.removeSplitter()

    # ---- top clamp -------------------------------------------------------
    cap = capsule_prism(L, hw, z_cap, z_top, angA)
    for p in bolt_pts:
        cap = cap.fuse(Part.makeCylinder(boss_r, z_top - z_cap,
                                         App.Vector(p.x, p.y, z_cap)))
    cap = cap.removeSplitter()
    cap = cap.cut(cyl_a).cut(flare_a)
    cap = cap.cut(bolt_cut)
    for p in bolt_pts:
        bore = Part.makeCylinder((fhd + head_clr) / 2.0, head_depth + 0.001,
                                 App.Vector(p.x, p.y, z_top - head_depth))
        cone = Part.makeCone((fd + bolt_clr) / 2.0, (fhd + head_clr) / 2.0, head_cone_h + 0.002,
                             App.Vector(p.x, p.y, z_top - head_depth - head_cone_h))
        cap = cap.cut(bore).cut(cone)
    cap = cap.removeSplitter()

    # ---- rounding --------------------------------------------------------
    bolt_keepout = max((fhd + head_clr) / 2.0,
                       nut_af / (2.0 * math.cos(math.radians(30.0)))) + 0.6

    def outer(pt):
        if dist_point_to_line(pt.x, pt.y, angA) < R + 0.6:
            return False
        if dist_point_to_line(pt.x, pt.y, angB) < R + 0.6:
            return False
        for p in bolt_pts:
            if math.hypot(pt.x - p.x, pt.y - p.y) < bolt_keepout:
                return False
        return True

    def vertical_edge(e):
        try:
            if not isinstance(e.Curve, Part.Line):
                return False
        except Exception:
            return False
        d = e.Vertexes[-1].Point.sub(e.Vertexes[0].Point)
        if d.Length < 2.0:
            return False
        d.normalize()
        if abs(d.z) < 0.999:
            return False
        return outer(e.CenterOfMass)

    def horizontal_at(z_level, tol=1e-4):
        def pred(e):
            for vx in e.Vertexes:
                if abs(vx.Point.z - z_level) > tol:
                    return False
            if e.Length < 1.0:
                return False
            return outer(e.CenterOfMass)
        return pred

    stats = {}
    bottom, n1 = fillet_by_predicate(bottom, vertical_edge, er)
    bottom, n2 = fillet_by_predicate(bottom, horizontal_at(z_seat), er / 2.0)
    n3 = 0  # bottom face stays sharp: bed adhesion + flat seating
    stats["bottom_fillets"] = (n1, n2, n3)

    cap, m1 = fillet_by_predicate(cap, vertical_edge, er)
    cap, m2 = fillet_by_predicate(cap, horizontal_at(z_top), er / 2.0)
    m3 = 0  # cap parting face stays flat
    stats["cap_fillets"] = (m1, m2, m3)

    for nm in ("bottom", "cap"):
        sh = bottom if nm == "bottom" else cap
        if not sh.isValid():
            try:
                sh.fix(1e-7, 1e-7, 1e-7)
            except Exception:
                pass
            sh = sh.removeSplitter()
        if nm == "bottom":
            bottom = sh
        else:
            cap = sh
    stats["bottom_valid"] = bottom.isValid()
    stats["cap_valid"] = cap.isValid()

    # ---- reference rods --------------------------------------------------
    rod_len = L + 60.0
    rodA = rod_cylinder(D / 2.0, rod_len, angA, zA)
    rodB = rod_cylinder(D / 2.0, rod_len, angB, zB)

    # ---- reference bolts -------------------------------------------------
    bolts = []
    for p in bolt_pts:
        bolts.append(Part.makeCylinder(fd / 2.0, z_top - z_bottom + clamp_gap,
                                       App.Vector(p.x, p.y, z_bottom)))

    geo = dict(bottom=bottom, cap=cap, rodA=rodA, rodB=rodB, bolts=bolts)
    dims = dict(R=R, v=v, zA=zA, zB=zB, z_seat=z_seat, z_cap=z_cap,
                z_bottom=z_bottom, z_top=z_top, hw=hw, boss_r=boss_r,
                bolt_offset=bolt_offset, chan_d=chan_d, angA=angA, angB=angB,
                clamp_gap=clamp_gap, head_depth=head_depth, nut_depth=nut_depth,
                bolt_pts=bolt_pts, flare_len=flare_len, flare_slope=flare_slope,
                cap_t=cap_t, head_cone_h=head_cone_h, nut_cone_h=nut_cone_h,
                stats=stats, L=L, wall=wall, fd=fd, fhd=fhd, head_clr=head_clr)
    return geo, dims


# --------------------------------------------------------------------------
# assembly into the document
# --------------------------------------------------------------------------
def populate(doc, geo):
    keep = {"Parameters"}
    for o in reversed(list(doc.Objects)):
        if o.Name in keep or o.Label in keep:
            continue
        try:
            doc.removeObject(o.Name)
        except Exception:
            pass

    bottom = doc.addObject("Part::Feature", "BottomClamp")
    bottom.Label = "BottomClamp"
    bottom.Shape = geo["bottom"]

    cap = doc.addObject("Part::Feature", "TopClamp")
    cap.Label = "TopClamp"
    cap.Shape = geo["cap"]

    grp = doc.addObject("App::DocumentObjectGroup", "Reference")
    grp.Label = "Reference"
    ra = doc.addObject("Part::Feature", "RodA_upper")
    ra.Shape = geo["rodA"]
    rb = doc.addObject("Part::Feature", "RodB_lower")
    rb.Shape = geo["rodB"]
    b1 = doc.addObject("Part::Feature", "Bolt_M5_plusY")
    b1.Shape = geo["bolts"][0]
    b2 = doc.addObject("Part::Feature", "Bolt_M5_minusY")
    b2.Shape = geo["bolts"][1]
    grp.addObjects([ra, rb, b1, b2])

    doc.recompute()

    try:
        import FreeCADGui as Gui
        vo = doc.getObject("BottomClamp").ViewObject
        vo.ShapeColor = (0.62, 0.66, 0.72)
        vo = doc.getObject("TopClamp").ViewObject
        vo.ShapeColor = (0.90, 0.55, 0.20)
        vo.Transparency = 45
        for n, col in (("RodA_upper", (0.20, 0.65, 0.30)),
                       ("RodB_lower", (0.20, 0.45, 0.75))):
            o = doc.getObject(n)
            o.ViewObject.ShapeColor = col
            o.ViewObject.Transparency = 55
        for n in ("Bolt_M5_plusY", "Bolt_M5_minusY"):
            o = doc.getObject(n)
            o.ViewObject.ShapeColor = (0.85, 0.85, 0.30)
            o.ViewObject.Transparency = 30
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.SendMsgToActiveView("ViewFit")
    except Exception:
        pass

    return bottom, cap


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
def verify(geo, dims, values):
    bottom = geo["bottom"]
    cap = geo["cap"]
    rodA = geo["rodA"]
    rodB = geo["rodB"]
    rep = {}

    def bb(s):
        b = s.BoundBox
        return dict(x=round(b.XLength, 2), y=round(b.YLength, 2), z=round(b.ZLength, 2),
                    xmin=round(b.XMin, 2), xmax=round(b.XMax, 2),
                    ymin=round(b.YMin, 2), ymax=round(b.YMax, 2),
                    zmin=round(b.ZMin, 2), zmax=round(b.ZMax, 2))

    rep["bottom"] = dict(valid=bottom.isValid(), solids=len(bottom.Solids),
                         volume_cm3=round(bottom.Volume / 1000.0, 2), bbox=bb(bottom))
    rep["top"] = dict(valid=cap.isValid(), solids=len(cap.Solids),
                      volume_cm3=round(cap.Volume / 1000.0, 2), bbox=bb(cap))

    asm = bottom.fuse(cap)
    rep["assembly_bbox"] = bb(asm)

    def d(a, b):
        try:
            return round(a.distToShape(b)[0], 3)
        except Exception:
            return None

    rep["clearances"] = {
        "bottom_to_rodA": d(bottom, rodA),
        "bottom_to_rodB": d(bottom, rodB),
        "top_to_rodA": d(cap, rodA),
        "top_to_rodB": d(cap, rodB),
        "bottom_to_top": d(bottom, cap),
        "boltA_to_rodA": d(geo["bolts"][0], rodA),
        "boltA_to_rodB": d(geo["bolts"][0], rodB),
        "boltB_to_rodA": d(geo["bolts"][1], rodA),
        "boltB_to_rodB": d(geo["bolts"][1], rodB),
        "rodA_to_rodB": d(rodA, rodB),
    }

    # interference: common volume must be zero
    rep["interference_mm3"] = {
        "bottom_x_rodA": round(bottom.common(rodA).Volume, 4),
        "bottom_x_rodB": round(bottom.common(rodB).Volume, 4),
        "top_x_rodA": round(cap.common(rodA).Volume, 4),
        "top_x_rodB": round(cap.common(rodB).Volume, 4),
        "bottom_x_top": round(bottom.common(cap).Volume, 4),
        "bottom_x_bolts": round(bottom.common(geo["bolts"][0].fuse(geo["bolts"][1])).Volume, 4),
        "top_x_bolts": round(cap.common(geo["bolts"][0].fuse(geo["bolts"][1])).Volume, 4),
    }

    # release check: no clamp material above the release plane of each rod
    R = dims["R"]
    big = 400.0
    aboveA = Part.makeBox(big, big, big, App.Vector(-big / 2, -big / 2, dims["zA"] + 1e-6))
    rep["release"] = {
        "bottom_material_above_rodA_axis_mm3": round(bottom.common(aboveA).Volume, 4),
        "top_min_z": round(cap.BoundBox.ZMin, 3),
        "bottom_max_z": round(bottom.BoundBox.ZMax, 3),
    }
    # material of the bottom half directly above rod B (would trap rod B)
    trap = rod_slot(R, dims["L"] + 20.0, dims["angB"], dims["zB"], dims["z_top"] + 10.0)
    rep["release"]["bottom_material_above_rodB_mm3"] = round(bottom.common(trap).Volume, 4)

    # contact lengths
    interrupt = (2.0 * R) / math.sin(math.radians(values["crossingAngle"]))
    rep["contact"] = {
        "rodA_saddle_length_mm": round(dims["L"] - 2 * dims["flare_len"] - interrupt, 2),
        "rodB_channel_length_mm": round(dims["L"] - 2 * dims["flare_len"], 2),
        "crossing_interruption_mm": round(interrupt, 2),
    }

    rep["key_dims"] = {
        "channel_diameter": round(dims["chan_d"], 3),
        "rod_axis_separation": round(dims["v"], 3),
        "bolt_offset_from_centre": round(dims["bolt_offset"], 3),
        "parting_gap": round(dims["clamp_gap"], 3),
        "bottom_height": round(dims["z_seat"] - dims["z_bottom"], 2),
        "top_height": round(dims["z_top"] - dims["z_cap"], 2),
        "stack_height_untightened": round(dims["z_top"] - dims["z_bottom"], 2),
        "bolt_grip_length": round(dims["z_top"] - dims["head_depth"]
                                  - (dims["z_bottom"] + dims["nut_depth"]), 2),
        "mouth_wall_thickness": round(dims["hw"] - (dims["R"] + dims["flare_slope"] * dims["flare_len"]), 2),
        "cap_floor_under_washer": round(dims["z_top"] - dims["head_depth"]
                                        - dims["head_cone_h"] - dims["z_cap"], 2),
        "bolt_length_needed": round(dims["z_top"] - dims["head_depth"]
                                    - (dims["z_bottom"] + dims["nut_depth"]) + 4.0, 1),
        "wall_bolt_bore_to_channel": round(
            dims["bolt_offset"] * math.cos(math.radians(values["crossingAngle"] / 2.0))
            - dims["R"] - (dims["fhd"] + dims["head_clr"]) / 2.0, 2),
    }
    rep["fillets"] = dims["stats"]
    return rep


def derived_rows(dims, values):
    return [
        ("channelDiameter", dims["chan_d"], "mm", "rodDiameter + rodClearance"),
        ("channelRadius", dims["R"], "mm", ""),
        ("rodAxisZ_upper", dims["zA"], "mm", "upper rod axis height"),
        ("rodAxisZ_lower", dims["zB"], "mm", "lower rod axis height"),
        ("seatZ", dims["z_seat"], "mm", "BottomClamp top face"),
        ("capBottomZ", dims["z_cap"], "mm", "TopClamp bottom face"),
        ("bodyBottomZ", dims["z_bottom"], "mm", ""),
        ("bodyTopZ", dims["z_top"], "mm", ""),
        ("capsuleHalfWidth", dims["hw"], "mm", "channelRadius + minimumWall"),
        ("bossRadius", dims["boss_r"], "mm", "fastenerHeadDiameter/2 + minimumWall"),
        ("boltOffset", dims["bolt_offset"], "mm", "bolt axis distance from the crossing, on the Y axis"),
        ("stackHeight", dims["z_top"] - dims["z_bottom"], "mm", "assembled, untightened; the clampGap is already inside these coordinates"),
        ("capThicknessOverRod", dims["z_top"] - dims["zA"] - dims["R"], "mm", ""),
    ]


def run():
    doc = fresh_document()
    sheet, values = read_or_build_parameters(doc)

    # enforce the 2-piece drop-in constraint
    forced = None
    need = values["rodDiameter"]
    if abs(values["verticalSeparation"] - need) > 1e-6:
        forced = (values["verticalSeparation"], need)
        values["verticalSeparation"] = need

    geo, dims = build(values)
    write_parameters(doc, sheet, values, derived_rows(dims, values))
    populate(doc, geo)
    doc.recompute()
    doc.saveAs(SAVE_PATH)

    rep = verify(geo, dims, values)
    rep["verticalSeparation_forced"] = forced
    rep["saved_to"] = SAVE_PATH
    return rep


REPORT = run()
import pprint
pprint.pprint(REPORT, width=110)
