# -*- coding: utf-8 -*-
"""
Star Dome bow splice, V1 -- the sleeve that joins two transport sections.

WHY THIS PART EXISTS

A bow is a semicircle of the dome's radius -- 9.4 m on M, 18.8 m on D12 -- and
nothing carries that, so it travels in sections and is joined on site. The
recorded transport limit is 3500 mm, which puts M at four sections of 2356 and
D12 at seven of 2693. See docs/transport.md.

WHAT IT IS

**A length of tube. One per joint, and nothing else to make.** The rods enter
from both ends and butt in the middle; one cross fastener each side holds them
in. There is no thread, no shoulder and no stud.

    rod ----->[==================|==================]<----- rod
              o                                     o
             bolt            they butt            bolt

An earlier draft made this a male-female pair pulled together by a threaded
stud. That was wrong, and the reason is worth keeping written down.

**The stud was carrying a load the joint does not have.** A bow is an arch:
along its length it is in compression, and compression crosses a butted joint
end to end through the fibreglass itself, which is the strongest thing GFRP
does. Tension and torsion are what actually need holding, and a cross fastener
holds both. The stud pulled two halves together against a load that is mostly
not there.

**And the thread was the only reason the wall was thick.** Tapping a hole
needs meat round it -- 2 mm of it -- and 2 mm of steel is 15.6x the rod's
bending stiffness on M. That is the whole problem with this part, and it was
self-inflicted: with no thread the wall drops to the least anyone rolls, and
the ratio drops with it.

    wall           0.8    1.0    1.2    1.5    2.0
    EI / rod EI    4.5    6.0    7.6   10.3   15.6      (10 mm rod)

The old design reached 4.5x only at the very mouth, by tapering the outside
away from a 15.6x middle. A plain tube is 4.5x along its whole length, so the
taper has nothing left to soften and is gone too.

WHY 0.8 IS NOT AN ARBITRARY MINIMUM

At 0.8 the outside diameter lands on a size tube is actually drawn in, with
the bore coming out exactly right:

    rod  8  ->  bore  8.4  ->  10 x 0.8
    rod 10  ->  bore 10.4  ->  12 x 0.8
    rod 12  ->  bore 12.4  ->  14 x 0.8

No other wall does that. At 1.0 a 10 mm rod wants a 12.4 OD, which is not a
size; the nearest stock is 14 x 1.0, whose bore is 12 -- 2 mm of slop on a
10 mm rod. So the stiffness optimum and the buyable part are the same part.
materials.SLEEVE already said as much: steel_mild is recorded as "drawn tube,
cut to length", min_wall 0.8.

THE THING THIS PART IS STILL FIGHTING

4.5x is better than 15.6x and it is not 1x. To match a GFRP rod's EI, steel
would need a 0.2 mm wall; nobody draws that. The bow is bent everywhere, so
the sleeve carries bending continuously and does not share the curve -- the
rod takes the extra bend just outside the mouth. That is inherent to steel and
is the price of the recorded material decision, not a fault in the drawing.
Whether it is acceptable is a load question, and load questions are milestone
8. verify() reports the ratio so the price stays visible.

NOTHING IS FORMED

An earlier version flared both mouths, arguing that a square bore edge is a
stress raiser on fibreglass. Dropped. Flaring is a forming operation on every
one of the 43 parts a dome takes, there is 0.8 mm of wall to form it in, and
it was the one feature pulling this part back out of "cut to length" and into
"made". The bore edge still wants breaking -- but that is a deburr note on the
drawing, not a feature on the model, and it does not need a tool of its own.

So the manufacture is now: cut the tube, drill two holes, break the edges.

WHAT THE FASTENER IS

The part is a tube with two cross holes; what goes through them does not
change the part. A bolt and nut is the default because it is captive and comes
apart with a spanner. A spring pin drops into the same hole and needs no nut,
at the cost of a hammer to remove. Either, or one of each, is a field choice.

The rod is drilled through the sleeve's own hole at assembly, so the sleeve is
its own drilling jig and the rod cannot sit short. That matches the two rods
to that joint; they get marked as a pair.

    make splices                      the material comparison
    python3 -m stardome rod --all     what the sections come to

Run:  exec(open('<repo>/connectors/splice_v1.py').read()) inside FreeCAD, or
through connectors/generate_clamps.py.
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

# stardome is pure standard library precisely so it imports inside FreeCAD's
# interpreter. The moduli and the density come from its catalogue rather than
# being typed again here -- see docs/architecture.md, "Where a number lives".
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from stardome import materials  # noqa: E402

ROD_MODULUS = materials.ROD["gfrp_pultruded"]["modulus_mpa"]
STEEL = materials.SLEEVE[materials.DEFAULT_SLEEVE]
STEEL_MODULUS = STEEL["modulus_mpa"]
STEEL_DENSITY = STEEL["density_kgm3"]
STEEL_MIN_WALL = STEEL["min_wall_mm"]

# The tightest half-span between two crossings, from stardome's own free_spans
# on the smallest dome that uses this part. A fact about the dome, an input
# here. python3 -m stardome splice --all reports it.
MIN_HALF_SPAN_MM = 200.0

# Outside diameters tube is drawn in, in the range this part uses. Checked
# against, not chosen from: the drawing follows the rod, and verify says
# whether the result is something you can buy.
STOCK_OD_MM = (8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 25.0)

DOC_NAME = "StarDome_Splice_V1"
TITLE = "Star Dome bow splice V1 - parameters"
USE_SPREADSHEET_IF_PRESENT = True

INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter. 8 for D3/D4, 10 for D6/D8, 12 for D10/D12 -- the whole part follows it"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance in the bore: a slide fit, so the joint goes together by hand and comes apart with a punch"),
    ("engagementFactor",       6.0,  "-",   "how far each rod goes in, in rod diameters. The lever that trades the hard spot against the part's length"),
    ("wall",                   0.8,  "mm",  "tube wall. The least steel is drawn in, which is also the softest this joint can be, which is also the wall that lands the OD on a stock size"),
    ("buttGap",                0.0,  "mm",  "clearance between the two rod ends. 0 = they butt, so compression crosses the joint through the fibreglass and not through the bolts"),
    ("boltDiameter",           4.0,  "mm",  "cross fastener each side: holds tension and torsion. A bolt and nut, or a spring pin in the same hole"),
    ("boltAt",                22.0,  "mm",  "how far each cross hole sits from its own end of the sleeve"),
    ("endChamfer",             0.4,  "mm",  "chamfer on the outside of each end, so the sleeve does not catch on the cover"),
]


def build(values):
    rod_d = values["rodDiameter"]
    clearance = values["rodClearance"]
    engagement = values["engagementFactor"] * rod_d
    wall = values["wall"]
    butt_gap = values["buttGap"]
    bolt_d = values["boltDiameter"]
    bolt_at = values["boltAt"]
    chamfer = values["endChamfer"]

    bore_r = (rod_d + clearance) / 2.0
    od = 2.0 * (bore_r + wall)
    length = 2.0 * engagement + butt_gap

    # The body: a tube, bored end to end. One end at z = 0, the other at
    # z = length, and the part is its own mirror about the middle.
    body = Part.makeCylinder(od / 2.0, length,
                             App.Vector(0, 0, 0), App.Vector(0, 0, 1))
    body = body.cut(
        Part.makeCylinder(bore_r, length + 2.0,
                          App.Vector(0, 0, -1.0), App.Vector(0, 0, 1))
    )

    # One cross hole per side, the same distance from its own end. Drilled at
    # right angles to each other, so neither rod loses width in the same
    # direction as its neighbour and the two holes cannot line up.
    through = od + 4.0
    holes = [
        Part.makeCylinder(bolt_d / 2.0, through,
                          App.Vector(0, -through / 2.0, bolt_at),
                          App.Vector(0, 1, 0)),
        Part.makeCylinder(bolt_d / 2.0, through,
                          App.Vector(-through / 2.0, 0, length - bolt_at),
                          App.Vector(1, 0, 0)),
    ]
    for hole in holes:
        body = body.cut(hole)

    # Chamfer the outside of both ends: the sleeve sits under the cover.
    if chamfer > 0:
        def on_an_end(edge):
            try:
                zs = [v.Point.z for v in edge.Vertexes]
                rs = [math.hypot(v.Point.x, v.Point.y) for v in edge.Vertexes]
            except Exception:
                return False
            if not zs or not rs:
                return False
            at_end = (all(abs(z) < 1e-6 for z in zs)
                      or all(abs(z - length) < 1e-6 for z in zs))
            return at_end and all(abs(r - od / 2.0) < 1e-6 for r in rs)

        body, _ = kit.fillet_by_predicate(body, on_an_end, chamfer)

    sleeve = body.removeSplitter()

    # --- reference geometry, for the drawing rather than the part ----------
    stick_out = 70.0
    rods = [
        Part.makeCylinder(rod_d / 2.0, engagement + stick_out,
                          App.Vector(0, 0, -stick_out), App.Vector(0, 0, 1)),
        Part.makeCylinder(rod_d / 2.0, engagement + stick_out,
                          App.Vector(0, 0, length - engagement),
                          App.Vector(0, 0, 1)),
    ]
    bolts = [
        Part.makeCylinder(bolt_d / 2.0, through,
                          App.Vector(0, -through / 2.0, bolt_at),
                          App.Vector(0, 1, 0)),
        Part.makeCylinder(bolt_d / 2.0, through,
                          App.Vector(-through / 2.0, 0, length - bolt_at),
                          App.Vector(1, 0, 0)),
    ]

    geo = {"sleeve": sleeve, "rods": rods, "bolts": bolts}
    dims = {
        "rod_diameter_mm": rod_d,
        "bore_diameter_mm": 2.0 * bore_r,
        "engagement_mm": engagement,
        "length_mm": length,
        "od_mm": od,
        "wall_mm": wall,
        "butt_gap_mm": butt_gap,
        "bolt_diameter_mm": bolt_d,
        "bolt_at_mm": bolt_at,
        "over_rod_mm": od - rod_d,
    }
    return geo, dims


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
def _second_moment(od, bore):
    return math.pi * (od ** 4 - bore ** 4) / 64.0


def _nearest_stock(od):
    return min(STOCK_OD_MM, key=lambda s: abs(s - od))


def verify(geo, dims, values):
    """Every way this part could be wrong that geometry can see."""
    problems = []
    sleeve = geo["sleeve"]

    if not kit.ok(sleeve):
        problems.append("the sleeve is not one sound solid")

    bore = dims["bore_diameter_mm"]
    if bore <= dims["rod_diameter_mm"]:
        problems.append("the bore does not clear the rod")

    wall = dims["wall_mm"]
    if wall < STEEL_MIN_WALL - 1e-9:
        problems.append(
            f"a {wall:.2f} mm wall is under the {STEEL_MIN_WALL:.1f} mm the "
            f"catalogue records as the least {STEEL['label']} is drawn in"
        )

    # The point of a 0.8 wall: the OD comes out on a size you can buy.
    stock = _nearest_stock(dims["od_mm"])
    off_stock = abs(stock - dims["od_mm"])
    if off_stock > 0.05:
        problems.append(
            f"OD {dims['od_mm']:.1f} is {off_stock:.1f} mm off the nearest "
            f"stock tube ({stock:.0f}); it would have to be turned"
        )

    # The cross hole must be inside the engaged rod, with rod either side of
    # it: at the end it tears out, past the rod end it holds nothing.
    if dims["bolt_at_mm"] >= dims["engagement_mm"]:
        problems.append("the cross hole is past the end of the rod")
    if dims["bolt_at_mm"] < 2.0 * dims["bolt_diameter_mm"]:
        problems.append(
            f"the cross hole is {dims['bolt_at_mm']:.0f} mm from the end, "
            f"under two fastener diameters of edge distance"
        )

    # The two holes are at right angles, so they can only foul each other if
    # the sleeve is short enough for them to overlap in z.
    if dims["length_mm"] - 2.0 * dims["bolt_at_mm"] < dims["bolt_diameter_mm"]:
        problems.append("the two cross holes run into each other")

    # What the fastener bears on, in the sleeve. A thin wall is the trade this
    # part makes, and this is the number it is traded against.
    bearing_mm2 = 2.0 * wall * dims["bolt_diameter_mm"]

    # The stiffness step, which is now one number rather than two.
    rod_i = math.pi * dims["rod_diameter_mm"] ** 4 / 64.0
    ei_rod = ROD_MODULUS * rod_i
    ratio = STEEL_MODULUS * _second_moment(dims["od_mm"], bore) / ei_rod

    # The whole sleeve has to sit in the gap between two crossings. The room
    # is a fact about the dome, not about this part, so it is an input here.
    if dims["length_mm"] / 2.0 > MIN_HALF_SPAN_MM:
        problems.append(
            f"half the sleeve is {dims['length_mm'] / 2.0:.0f} mm, more than "
            f"the {MIN_HALF_SPAN_MM:.0f} mm the tightest span leaves"
        )

    return {
        "problems": problems,
        "ok": not problems,
        "sleeve_volume_cm3": round(kit.vol(sleeve) / 1000.0, 2),
        "sleeve_mass_g": round(
            kit.vol(sleeve) / 1000.0 * STEEL_DENSITY / 1000.0, 1
        ),
        "stiffness_vs_rod": round(ratio, 1),
        "stock_tube": f"{stock:.0f} x {wall:g}",
        "bolt_bearing_mm2": round(bearing_mm2, 1),
        "rod_width_lost_at_hole": round(
            dims["bolt_diameter_mm"] / dims["rod_diameter_mm"], 2
        ),
        "parts_per_joint": 1,
        "key_dims": {
            "length_mm": round(dims["length_mm"], 1),
            "od_mm": round(dims["od_mm"], 1),
            "bore_mm": round(bore, 2),
            "over_rod_mm": round(dims["over_rod_mm"], 1),
        },
        "note": (
            "Geometry only. Nothing here is a load check: the bending the "
            "joint actually sees, whether steel at this stiffness is "
            "acceptable, and what the cross hole costs the rod, are all "
            "milestone 8."
        ),
    }


def derived_rows(dims, values):
    stock = _nearest_stock(dims["od_mm"])
    return [
        ("bore", round(dims["bore_diameter_mm"], 2), "mm",
         "slide fit on the rod, so the joint goes together by hand"),
        ("engagement", round(dims["engagement_mm"], 1), "mm",
         f"{values['engagementFactor']:g} rod diameters into each end"),
        ("length", round(dims["length_mm"], 1), "mm",
         "the whole part; has to sit between two crossings"),
        ("OD", round(dims["od_mm"], 1), "mm",
         f"stock tube {stock:.0f} x {values['wall']:g}, cut to length"),
        ("overRod", round(dims["over_rod_mm"], 1), "mm",
         "how much fatter than the rod, all the way along"),
        ("bolt", f"{values['boltDiameter']:g} mm at "
                 f"{values['boltAt']:g} from each end", "-",
         "one per side, at right angles to each other; bolt or spring pin"),
        ("perJoint", 1, "-", "one tube. Nothing else to make"),
    ]


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------
# docs/colours.md: the made part is translucent so you can see the rods
# inside it, the rods are solid, and bought steel is grey.
SLEEVE_COLOUR = (0.35, 0.52, 0.78)
SLEEVE_TRANSPARENCY = 55
BOLT_COLOUR = (0.55, 0.55, 0.58)
# Both rods are the same bow, so both are that bow's family colour -- but the
# whole subject of this drawing is where they meet, and two identical blues
# butted end to end show nothing. So they take a light and a dark of the one
# hue, the way the base hub ramps its plates to show stacking order. Family
# read intact, joint visible.
ROD_COLOURS = [
    (0.15, 0.55, 0.95),   # G family blue
    (0.09, 0.33, 0.60),   # the same blue, darker: the other section
]


def populate(doc, geo):
    obj = doc.addObject("Part::Feature", "Sleeve")
    obj.Shape = geo["sleeve"]
    for i, rod in enumerate(geo["rods"], start=1):
        obj = doc.addObject("Part::Feature", f"ref_Rod{i}")
        obj.Shape = rod
    for i, bolt in enumerate(geo["bolts"], start=1):
        obj = doc.addObject("Part::Feature", f"Bolt{i}")
        obj.Shape = bolt
    doc.recompute()
    return doc


def apply_view(doc):
    """Colours per docs/colours.md.

    A no-op without a GUI: freecadcmd gives objects no ViewObject, so a
    document built by generate_clamps.py carries geometry and no appearance.
    Colour it with the GUI up -- see docs/colours.md.
    """
    rod_index = 0
    for obj in doc.Objects:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        if obj.Name.startswith("Sleeve"):
            colour, transparency = SLEEVE_COLOUR, SLEEVE_TRANSPARENCY
        elif obj.Name.startswith("ref_Rod"):
            colour = ROD_COLOURS[rod_index % len(ROD_COLOURS)]
            transparency = 0
            rod_index += 1
        elif obj.Name.startswith("Bolt"):
            colour, transparency = BOLT_COLOUR, 0
        else:
            continue
        view.ShapeColor = colour
        if hasattr(view, "Transparency"):
            view.Transparency = transparency
    return doc


def run(out_dir=None, doc_path=None, rod_diameter=None):
    doc = kit.document(DOC_NAME, doc_path)
    sheet, values = kit.read_or_build_parameters(
        doc, INPUTS, USE_SPREADSHEET_IF_PRESENT
    )
    if rod_diameter:
        values["rodDiameter"] = float(rod_diameter)
        # Everything that scales with the rod, scales with the rod. The wall
        # does not: it is the least steel is drawn in, at every size.
        values["boltDiameter"] = max(3.0, round(rod_diameter * 0.4))

    geo, dims = build(values)
    report = verify(geo, dims, values)
    populate(doc, geo)
    apply_view(doc)
    kit.write_parameters(doc, sheet, INPUTS, values, derived_rows(dims, values),
                         TITLE)
    doc.recompute()

    path = doc_path or (
        os.path.join(out_dir, "star_dome_splice_v1.FCStd") if out_dir else None
    )
    if path:
        doc.saveAs(path)
        report["saved_to"] = path
    return report


if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint

    pprint.pprint(REPORT, width=112)
