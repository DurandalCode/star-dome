# -*- coding: utf-8 -*-
"""
Star Dome rod splice, prototype V1.

A bow is a semicircle 9.4 m long on M and it travels in 2400 mm sections, so it
is joined along its length -- 45 times per dome, which makes this the most
numerous part in the structure by a wide margin.

Two things make it different from every other connector here.

**The rod is bent at the joint.** Every bow is bent to the dome radius the
whole way round; there is no straight piece to splice. So the sleeve is drawn
on that radius too, by revolving its section about the dome centre rather than
extruding it along a line. The alternative -- a straight sleeve -- does not
merely look wrong: it forces the rod straight over its own length and leaves a
misfit at each end. That misfit is reported as ``sagitta_mm`` below, and on M
it is 0.42 mm against a 0.40 mm channel clearance, so a straight sleeve is
already marginal at the smallest rod and gets worse as the dome shrinks.

**The joint carries bending.** A continuous member was cut, and what replaces
it has to do what it did. That is why the sleeve is long -- ten rod diameters,
five each side of the butt -- and why it is bolted at both ends rather than in
the middle. A short collar in the centre is a hinge at the one place the bow
was carrying moment.

Nothing here says whether it carries ENOUGH. That is a test rig, and the
roadmap's milestone 8.

Run:  exec(open('<repo>/connectors/rod_splice_v1.py').read())
inside FreeCAD, or via `make clamps`.
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

DOC_NAME = "StarDome_RodSplice_V1"
TITLE = "Star Dome rod splice V1 - parameters"
OUT_DIR = os.path.join(REPO, "connectors")
SAVE_PATH = os.path.join(OUT_DIR, "star_dome_rod_splice_v1.FCStd")
USE_SPREADSHEET_IF_PRESENT = True

# The part is drawn in the frame the connector schedule places it in: +X along
# the rod, +Z outward from the dome centre, so the centre of the bend is at
# (0, 0, -bendRadius) and the sleeve is a revolve about the Y axis through it.
INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance on the channel"),
    ("bendRadius",          3000.0,  "mm",  "radius the bow is bent to, which is the dome radius. Overridden from the model by generate_clamps.py"),
    ("sleeveLength",         100.0,  "mm",  "arc length of the sleeve; ten rod diameters, five each side of the butt. Shorter is a hinge"),
    ("minimumWall",            4.0,  "mm",  "wall under the channel"),
    ("capThickness",           5.0,  "mm",  "material over the channel in the cap"),
    ("clampGap",               0.8,  "mm",  "parting gap between the halves, closed by the bolts"),
    ("buttGap",                1.0,  "mm",  "space left between the two rod ends, so a section cut a millimetre long still seats"),
    ("boltInsetFactor",       0.16,  "mm",  "how far in from each end the bolts sit, as a fraction of sleeveLength"),
    ("fastenerDiameter",       5.5,  "mm",  "M5 clearance hole diameter"),
    ("fastenerHeadDiameter",  10.0,  "mm",  "M5 head / washer outside diameter"),
    ("headClearance",          0.6,  "mm",  "clearance around the head bore"),
    ("headBoreDepth",          4.0,  "mm",  "depth of the head counterbore in the cap"),
    ("nutAcrossFlats",         8.1,  "mm",  "M5 nut across the flats"),
    ("nutRecessDepth",         4.4,  "mm",  "nut trap depth in the bottom half"),
    ("boltHoleClearance",      0.3,  "mm",  "added to the bolt shank hole"),
    ("boltMargin",             1.0,  "mm",  "extra wall between the bolt boss and the channel"),
    ("flareLength",            5.0,  "mm",  "length of the trumpet at each mouth"),
    ("flareSlope",            0.18,  "mm",  "radial opening per mm of flare"),
    ("edgeRadius",             1.0,  "mm",  "outside edge break"),
]


def revolve(profile_points, bend_radius, half_angle_deg):
    """Sweep a closed section about the bend centre, symmetric about x = 0.

    ``profile_points`` are (y, z) in the plane x = 0 -- the plane that contains
    both the bend centre and the revolve axis -- so revolving them traces the
    section along the rod's own arc. This is what makes the part CURVED rather
    than merely long: a sleeve drawn straight and a rod bent to 3000 mm do not
    touch along their length.
    """
    pts = [App.Vector(0.0, y, z) for y, z in profile_points]
    pts.append(pts[0])
    face = Part.Face(Part.makePolygon(pts))
    centre = App.Vector(0.0, 0.0, -bend_radius)
    axis = App.Vector(0.0, 1.0, 0.0)
    solid = face.revolve(centre, axis, 2.0 * half_angle_deg)
    # revolve() starts at the profile and sweeps one way, so bring it back to
    # centre on x = 0 and the part is symmetric about the butt.
    solid = solid.copy()
    solid.rotate(centre, axis, -half_angle_deg)
    return solid


def channel_solid(radius, bend_radius, half_angle_deg):
    """The rod itself, or the hole it goes in: a circle swept along the arc."""
    # The section has to lie in a plane that CONTAINS the revolve axis, which
    # is the Y axis through the bend centre -- so the circle's normal is X.
    # Give it the axis direction instead and the revolve sweeps the face
    # inside its own plane and comes back with no volume at all.
    circle = Part.Wire(
        Part.makeCircle(
            radius, App.Vector(0, 0, 0), App.Vector(1, 0, 0)
        ).Edges
    )
    face = Part.Face(circle)
    centre = App.Vector(0.0, 0.0, -bend_radius)
    axis = App.Vector(0.0, 1.0, 0.0)
    solid = face.revolve(centre, axis, 2.0 * half_angle_deg)
    solid = solid.copy()
    solid.rotate(centre, axis, -half_angle_deg)
    return solid


def build(values):
    D = values["rodDiameter"]
    c = values["rodClearance"]
    bend = values["bendRadius"]
    length = values["sleeveLength"]
    wall = values["minimumWall"]
    cap_t = values["capThickness"]
    gap = values["clampGap"]
    fd = values["fastenerDiameter"]
    fhd = values["fastenerHeadDiameter"]
    head_clr = values["headClearance"]
    head_depth = values["headBoreDepth"]
    nut_af = values["nutAcrossFlats"]
    nut_depth = values["nutRecessDepth"]
    bolt_clr = values["boltHoleClearance"]
    bolt_margin = values["boltMargin"]
    flare_len = values["flareLength"]
    flare_slope = values["flareSlope"]
    er = values["edgeRadius"]

    R = (D + c) / 2.0
    boss_r = fhd / 2.0 + wall
    bolt_y = R + boss_r + bolt_margin
    hw = bolt_y + boss_r          # half width in plan: the bolt bosses set it
    half_angle = math.degrees(length / 2.0 / bend)

    z_bottom = -(R + wall)
    z_seat = -gap                 # top face of the lower half
    z_top = R + cap_t

    # The two halves, each swept on the bend radius.
    bottom = revolve(
        [(-hw, z_bottom), (hw, z_bottom), (hw, z_seat), (-hw, z_seat)],
        bend, half_angle,
    )
    cap = revolve(
        [(-hw, 0.0), (hw, 0.0), (hw, z_top), (-hw, z_top)],
        bend, half_angle,
    )

    # The channel, and a straight slot above it so the rod drops in rather
    # than threading: the bottom half is a trough, not a tube.
    long_angle = half_angle * 3.0
    channel = channel_solid(R, bend, long_angle)
    drop = revolve(
        [(-R, 0.0), (R, 0.0), (R, z_top + 20.0), (-R, z_top + 20.0)],
        bend, long_angle,
    )

    # Flares at both mouths. The rod leaves the sleeve at an angle to it --
    # that is the whole point of a curved joint -- so the mouth is opened up
    # the same way the clamps' are, by a cone on the rod's own axis there.
    flares = []
    for sign in (1.0, -1.0):
        a = math.radians(sign * half_angle)
        # The rod's position and tangent at the sleeve's end.
        point = App.Vector(
            math.sin(a) * bend, 0.0, math.cos(a) * bend - bend
        )
        tangent = App.Vector(sign * math.cos(a), 0.0, -sign * math.sin(a))
        h = flare_len + 6.0
        base = point - tangent.multiply(flare_len)
        flares.append(
            Part.makeCone(
                R + flare_slope * flare_len, R, flare_len,
                base, App.Vector(sign * math.cos(a), 0.0, -sign * math.sin(a)),
            )
        )
        flares.append(
            Part.makeCylinder(
                R + flare_slope * flare_len, h,
                point, App.Vector(sign * math.cos(a), 0.0, -sign * math.sin(a)),
            )
        )
    flare = flares[0]
    for f in flares[1:]:
        flare = flare.fuse(f)

    # Four bolts: one each side of the rod, at each end of the sleeve. Two in
    # the middle would let the joint hinge about them, which is the one thing
    # a splice on a bent member may not do.
    inset = length * values["boltInsetFactor"]
    bolt_x = length / 2.0 - inset
    bolt_pts = [
        App.Vector(sx * bolt_x, sy * bolt_y, 0.0)
        for sx in (1.0, -1.0)
        for sy in (1.0, -1.0)
    ]
    big = (length + z_top - z_bottom) * 4.0
    bolt_cut = None
    for p in bolt_pts:
        hole = Part.makeCylinder(
            (fd + bolt_clr) / 2.0, big,
            App.Vector(p.x, p.y, z_bottom - big / 2.0),
        )
        bolt_cut = hole if bolt_cut is None else bolt_cut.fuse(hole)

    bottom = bottom.cut(channel).cut(drop).cut(flare).cut(bolt_cut)
    for p in bolt_pts:
        nut = kit.hex_prism(
            nut_af, nut_depth, App.Vector(p.x, p.y, z_bottom - 0.001)
        )
        bottom = bottom.cut(nut)
    bottom = bottom.removeSplitter()

    cap = cap.cut(channel).cut(flare).cut(bolt_cut)
    for p in bolt_pts:
        bore = Part.makeCylinder(
            (fhd + head_clr) / 2.0, head_depth + 0.001,
            App.Vector(p.x, p.y, z_top - head_depth),
        )
        cap = cap.cut(bore)
    cap = cap.removeSplitter()

    def outer(pt):
        if abs(pt.y) < R + 0.6:
            return False
        for p in bolt_pts:
            if math.hypot(pt.x - p.x, pt.y - p.y) < boss_r + 0.6:
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
        return abs(d.z) > 0.999 and outer(e.CenterOfMass)

    stats = {}
    bottom, stats["bottom_fillets"] = kit.fillet_by_predicate(
        bottom, vertical_edge, er
    )
    cap, stats["cap_fillets"] = kit.fillet_by_predicate(cap, vertical_edge, er)

    if not kit.ok(bottom) or not kit.ok(cap):
        raise RuntimeError("a splice half did not come out as one sound solid")

    # Reference: the two rod sections, butted in the middle with buttGap
    # between them, on the real arc.
    butt = values["buttGap"]
    rod_half = math.degrees((length + 60.0) / 2.0 / bend)
    rods = []
    for sign in (1.0, -1.0):
        piece = channel_solid(D / 2.0, bend, rod_half)
        cut = revolve(
            [(-hw * 3, z_bottom - 20.0), (hw * 3, z_bottom - 20.0),
             (hw * 3, z_top + 20.0), (-hw * 3, z_top + 20.0)],
            bend, math.degrees(butt / 2.0 / bend),
        )
        big_box = Part.makeBox(
            big, big, big,
            App.Vector(-sign * big if sign > 0 else 0.0, -big / 2.0, -big / 2.0),
        )
        piece = piece.cut(cut).cut(big_box)
        rods.append(piece)

    geo = dict(bottom=bottom, cap=cap, rods=rods, channel=channel)
    dims = dict(
        R=R, hw=hw, bend=bend, length=length, half_angle=half_angle,
        z_bottom=z_bottom, z_seat=z_seat, z_top=z_top, boss_r=boss_r,
        bolt_y=bolt_y, bolt_x=bolt_x, bolt_pts=bolt_pts, stats=stats,
        sagitta=bend * (1.0 - math.cos(math.radians(half_angle))),
        wall=wall, cap_t=cap_t, gap=gap, flare_len=flare_len,
    )
    return geo, dims


def verify(geo, dims, values):
    bottom, cap = geo["bottom"], geo["cap"]
    rep = {}

    def bb(s):
        b = s.BoundBox
        return dict(x=round(b.XLength, 2), y=round(b.YLength, 2),
                    z=round(b.ZLength, 2))

    rep["bottom"] = dict(valid=bottom.isValid(), solids=len(bottom.Solids),
                         volume_cm3=round(bottom.Volume / 1000.0, 2),
                         bbox=bb(bottom))
    rep["cap"] = dict(valid=cap.isValid(), solids=len(cap.Solids),
                      volume_cm3=round(cap.Volume / 1000.0, 2), bbox=bb(cap))

    # The halves must not touch: the clamp gap is what the bolts close.
    rep["parting_gap_mm"] = round(bottom.common(cap).Volume, 4)

    # The rod sections have to go in and stay out of the plastic.
    solid = bottom.fuse(cap)
    rep["interference_mm3"] = {
        f"rod{i + 1}": round(solid.common(rod).Volume, 4)
        for i, rod in enumerate(geo["rods"])
    }

    # What a straight sleeve would have cost, which is the argument for
    # revolving this one.
    rep["bend"] = {
        "bend_radius_mm": round(dims["bend"], 1),
        "sleeve_arc_deg": round(2.0 * dims["half_angle"], 4),
        "sagitta_mm": round(dims["sagitta"], 4),
        "channel_clearance_mm": round(values["rodClearance"], 3),
        "a_straight_sleeve_would_misfit_by": round(
            dims["sagitta"] - values["rodClearance"] / 2.0, 4
        ),
    }
    rep["grip"] = {
        "each_side_mm": round(dims["length"] / 2.0 - values["buttGap"] / 2.0, 2),
        "in_rod_diameters": round(
            (dims["length"] / 2.0) / values["rodDiameter"], 2
        ),
        "bolts_per_splice": len(dims["bolt_pts"]),
    }
    rep["printability"] = {
        "bottom": kit.printability(bottom),
        "cap": kit.printability(cap, flipped=True),
    }
    rep["fillets"] = dims["stats"]
    return rep


def derived_rows(dims, values):
    return [
        ("channelRadius", dims["R"], "mm", "rod plus half the clearance"),
        ("sleeveArc", 2.0 * dims["half_angle"], "deg", "how much of the bow the sleeve covers"),
        ("sagitta", dims["sagitta"], "mm", "how far the arc departs from a straight sleeve over half its length"),
        ("halfWidth", dims["hw"], "mm", "set by the bolt bosses, not by the rod"),
        ("boltOffsetY", dims["bolt_y"], "mm", ""),
        ("boltOffsetX", dims["bolt_x"], "mm", "from the butt, along the rod"),
        ("stackHeight", dims["z_top"] - dims["z_bottom"], "mm", "assembled, untightened"),
    ]


def populate(doc, geo):
    keep = {"Parameters"}
    for o in reversed(list(doc.Objects)):
        if o.Name in keep or o.Label in keep:
            continue
        try:
            doc.removeObject(o.Name)
        except Exception:
            pass

    bottom = doc.addObject("Part::Feature", "BottomSleeve")
    bottom.Label = "BottomSleeve"
    bottom.Shape = geo["bottom"]
    cap = doc.addObject("Part::Feature", "TopSleeve")
    cap.Label = "TopSleeve"
    cap.Shape = geo["cap"]

    grp = doc.addObject("App::DocumentObjectGroup", "Reference")
    grp.Label = "Reference"
    refs = []
    for i, rod in enumerate(geo["rods"], start=1):
        obj = doc.addObject("Part::Feature", f"RodSection{i}")
        obj.Shape = rod
        refs.append(obj)
    grp.addObjects(refs)
    doc.recompute()
    return bottom, cap


def run():
    doc = kit.document(DOC_NAME)
    sheet, values = kit.read_or_build_parameters(doc, INPUTS, USE_SPREADSHEET_IF_PRESENT)
    geo, dims = build(values)
    kit.write_parameters(doc, sheet, INPUTS, values, derived_rows(dims, values), TITLE)
    populate(doc, geo)
    doc.recompute()
    doc.saveAs(SAVE_PATH)
    rep = verify(geo, dims, values)
    rep["saved_to"] = SAVE_PATH
    return rep


if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint
    pprint.pprint(REPORT, width=110)
