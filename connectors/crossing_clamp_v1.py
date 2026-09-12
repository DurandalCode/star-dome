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

Run:  exec(open('<repo>/connectors/crossing_clamp_v1.py').read())
inside FreeCAD, or via the FreeCAD MCP bridge, or `make clamps`.
"""

import math
import os
import sys

import FreeCAD as App
import Part

# REPO is overridable from the calling namespace before exec(), which is how
# the MCP bridge and a worktree checkout point this at the right tree --
# exec'd source has no __file__ to fall back on. Same contract as
# generate_clamps.py; `make clamps` passes it.
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

DOC_NAME = "StarDome_CrossingClamp_V1"
TITLE = "Star Dome crossing clamp V1 - parameters"
OUT_DIR = os.path.join(REPO, "connectors")
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
    ("rodNominalDiameter",     0.0,  "mm",  "the rod as a structural member, when that is not what a caliper reads across it -- composite rebar is named by its equivalent diameter and measures more over its winding. 0 means the two are the same"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance added to each rod channel"),
    ("crossingAngle",         72.0,  "deg", "angle between the two rod axes in plan view"),
    ("channelLength",         55.0,  "mm",  "length of each rod channel through the body"),
    ("verticalSeparation",    10.0,  "mm",  "distance between rod axes; forced to rodDiameter so the upper rod bears on the lower one"),
    ("minimumWall",            0.0,  "mm",  "0 takes it from rodDiameter: 0.4 of the rod, never under 3 mm. A real number overrides"),
    ("edgeRadius",             4.0,  "mm",  "outer edge / corner radius"),
    ("fastenerSize",            0.0,  "",    "which metric bolt: 0 chooses it from the rod -- half the rod, snapped to M3/M4/M5/M6/M8 -- and 3, 4, 5, 6 or 8 forces one"),
    ("fastenerDiameter",       0.0,  "mm",  "clearance hole for the bolt. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("fastenerHeadDiameter",  0.0,  "mm",  "head / washer outside diameter. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    # --- secondary inputs -------------------------------------------------
    ("capThickness",           6.0,  "mm",  "TopClamp material above the upper rod; it works in bending between the bolts"),
    ("clampGap",               1.2,  "mm",  "designed open gap at the parting faces; the bolts always squeeze the rods, faces never bottom out"),
    ("headClearance",          0.6,  "mm",  "diametral clearance for the head/washer counterbore"),
    ("headBoreDepth",          0.0,  "mm",  "counterbore depth for head + washer. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("headConeHeight",         0.0,  "mm",  "tapered transition under the counterbore, printable upside down"),
    ("nutConeHeight",          0.0,  "mm",  "tapered transition above the nut pocket"),
    ("nutAcrossFlats",         0.0,  "mm",  "nut across flats + fit clearance. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("nutRecessDepth",         0.0,  "mm",  "captive nut pocket depth. 0 takes it from rodDiameter -- see kit.FASTENERS; a real number overrides"),
    ("boltHoleClearance",      0.4,  "mm",  "diametral print clearance on the bolt shank hole"),
    ("flareLength",            5.0,  "mm",  "axial length of the flared channel entrance"),
    ("flareSlope",             0.2,  "mm",  "radial rise per mm of the entrance flare"),
    ("boltMargin",             0.0,  "mm",  "extra radial margin pushing the bolts away from the rods"),
]



# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
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
    d = kit.direction(angle_deg)
    cones = []
    for sign in (1.0, -1.0):
        dd = App.Vector(d.x * sign, d.y * sign, 0)
        t0 = channel_length / 2.0 - flare_len
        h = flare_len + overrun
        base = App.Vector(dd.x * t0, dd.y * t0, z)
        cones.append(Part.makeCone(radius, radius + slope * h, h, base, dd))
    return cones[0].fuse(cones[1])


def dist_point_to_line(px, py, angle_deg):
    """Perpendicular distance in plan from a point to a line through the origin."""
    a = math.radians(angle_deg)
    return abs(-math.sin(a) * px + math.cos(a) * py)


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
def build(values):
    # The bolt is chosen from the rod unless somebody typed one in; see
    # kit.scale_to_rod. Doing it here rather than in the caller means every
    # route into this part -- the driver, the spreadsheet, term_clamp_v1 --
    # gets the same answer.
    chosen = kit.scale_to_rod(values)
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
    cyl_a = kit.rod_solid(R, big, angA, zA)
    cyl_b = kit.rod_solid(R, big, angB, zB)
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
        nut = kit.hex_prism(nut_af, nut_depth, App.Vector(p.x, p.y, z_bottom - 0.001))
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
    bottom, n1 = kit.fillet_by_predicate(bottom, vertical_edge, er)
    bottom, n2 = kit.fillet_by_predicate(bottom, horizontal_at(z_seat), er / 2.0)
    n3 = 0  # bottom face stays sharp: bed adhesion + flat seating
    stats["bottom_fillets"] = (n1, n2, n3)

    cap, m1 = kit.fillet_by_predicate(cap, vertical_edge, er)
    cap, m2 = kit.fillet_by_predicate(cap, horizontal_at(z_top), er / 2.0)
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
    rodA = kit.rod_solid(D / 2.0, rod_len, angA, zA)
    rodB = kit.rod_solid(D / 2.0, rod_len, angB, zB)

    # ---- reference bolts -------------------------------------------------
    bolts = []
    for p in bolt_pts:
        bolts.append(Part.makeCylinder(fd / 2.0, z_top - z_bottom + clamp_gap,
                                       App.Vector(p.x, p.y, z_bottom)))

    geo = dict(bottom=bottom, cap=cap, rodA=rodA, rodB=rodB, bolts=bolts)
    dims = dict(
        chosen_from_rod=chosen,R=R, v=v, zA=zA, zB=zB, z_seat=z_seat, z_cap=z_cap,
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
        (
            "fastenerChosen",
            dims["chosen_from_rod"].get("fastenerSize", 0),
            "M",
            "which metric bolt this part was drawn for. Chosen from the rod "
            "unless fastenerSize said otherwise -- half the rod, snapped",
        ),
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
    doc = kit.document(DOC_NAME)
    sheet, values = kit.read_or_build_parameters(doc, INPUTS, USE_SPREADSHEET_IF_PRESENT)

    # enforce the 2-piece drop-in constraint
    forced = None
    need = values["rodDiameter"]
    if abs(values["verticalSeparation"] - need) > 1e-6:
        forced = (values["verticalSeparation"], need)
        values["verticalSeparation"] = need

    geo, dims = build(values)
    kit.write_parameters(doc, sheet, INPUTS, values, derived_rows(dims, values), TITLE)
    populate(doc, geo)
    doc.recompute()
    doc.saveAs(SAVE_PATH)

    rep = verify(geo, dims, values)
    rep["verticalSeparation_forced"] = forced
    rep["saved_to"] = SAVE_PATH
    return rep


# Executing this file builds the clamp immediately, which is what the usage
# note above documents. A driver that wants to call build() itself for several
# parts sets SUPPRESS_AUTORUN in the exec namespace first; see
# connectors/generate_clamps.py.
if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint
    pprint.pprint(REPORT, width=110)
