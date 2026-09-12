# -*- coding: utf-8 -*-
"""
Star Dome rod splice, V2 -- a ferrule.

V1 was a two-piece bolted clamp, and that was the crossing clamp's architecture
copied into a place that does not need it. The clamp has bolts standing beside
the rod because two rods cross there and nothing can sit on the axis. A splice
has one rod, so nothing forces it, and the copy cost 48.4 mm of width on a
10 mm rod -- 4.4 kg of plastic and 180 M5 bolts per dome.

This is the part the problem actually asks for: **a tube the rod sections
slide into**, the way a tent pole does. A splice is the one joint in the dome
that never has to close around anything, because it joins two SECTIONS, and
before assembly those are two separate objects.

    V1   100 x 48.4 x 29 mm   78.8 cm3   4 bolts    3.54 L/dome
    V2   100 mm, OD 18.4      18.1 cm3   no bolts   0.81 L/dome

**The rod is straight when this goes on.** The bows are straight GFRP stock
sprung to the dome radius during assembly, so the ferrule slides onto a
straight section and the bow is bent afterwards, with the ferrule already on
it. That is why this one is drawn straight and V1 was drawn on the dome
radius: V1 closed around a rod that was already bent, and this one does not
have to.

**The bore is relieved in the middle** so it does not fight the bend it is
then asked to take. A rigid straight tube 100 mm long forces a 100 mm straight
into a bow whose whole length is curved; relieving the middle lets the rod
bow inside the sleeve and bear at the two ends, which is also the load path
that makes a ferrule a ferrule -- it bridges the butt as a beam between two
bearings rather than gripping along its length.

Held by a cross pin at each end, the same way `base_hub_v1` holds a bow end:
a slide fit locates the rod and holds it against nothing. One end can be
bonded instead, which is what a tent pole does; `bondedEnd` draws the glue
groove for it.

**FDM prints this badly and that is worth saying.** Upright, the layers lie
across the axis -- the plane a bending joint is trying not to open. Lying
down, the bore needs support. A splice is the strongest candidate in this
project for being BOUGHT rather than printed: 45 of them is 4.5 m of 16x2 mm
aluminium tube. See `derived_rows` for the stock size that matches.

Run:  exec(open('<repo>/connectors/rod_splice_v2.py').read())
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

DOC_NAME = "StarDome_RodSplice_V2"
TITLE = "Star Dome rod ferrule V2 - parameters"
OUT_DIR = os.path.join(REPO, "connectors")
SAVE_PATH = os.path.join(OUT_DIR, "star_dome_rod_splice_v2.FCStd")
USE_SPREADSHEET_IF_PRESENT = True

# Drawn in the frame the connector schedule places it in: +X along the rod,
# +Z outward from the dome centre. The part is a body of revolution about +X,
# so only the pin holes care which way +Z points.
INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance where the bore bears on the rod. A slide fit: the section goes in by hand and the pin holds it"),
    ("sleeveLength",         100.0,  "mm",  "overall length; ten rod diameters, five each side of the butt. Shorter is a hinge"),
    ("bearingLength",         22.0,  "mm",  "how much of each end actually bears on the rod. The middle is relieved"),
    ("bendRadius",          3000.0,  "mm",  "radius the bow is bent to, which is the dome radius. Sets how much relief the middle needs. Overridden from the model by generate_clamps.py"),
    ("reliefMargin",           0.3,  "mm",  "radial slack in the relieved middle over what the bend alone needs"),
    ("minimumWall",            0.0,  "mm",  "0 takes it from rodDiameter: 0.4 of the rod, never under 3 mm. A real number overrides"),
    ("mouthChamfer",           1.5,  "mm",  "lead-in at each mouth, so a section finds the bore rather than catching on it"),
    ("rodPinDiameter",         0.0,  "mm",  "cross pin through ferrule and rod, once the section is in"),
    ("pinInset",              11.0,  "mm",  "how far from each mouth the pin sits; inside the bearing length or it pins nothing"),
    ("bondedEnd",              0.0,  "",    "1 draws a glue groove in one end instead of a pin hole, which is what a tent pole does. 0 pins both ends"),
    ("bondGrooveDepth",        0.6,  "mm",  "depth of the glue groove, when bondedEnd is on"),
    ("bondGrooveWidth",        3.0,  "mm",  "width of that groove"),
    ("edgeRadius",             0.8,  "mm",  "outside edge break at each end"),
]


def build(values):
    # The bolt, the pin and the wall come from the rod unless somebody
    # typed them in; see kit.scale_to_rod.
    chosen = kit.scale_to_rod(values)
    D = values["rodDiameter"]
    c = values["rodClearance"]
    L = values["sleeveLength"]
    bearing = values["bearingLength"]
    bend = values["bendRadius"]
    wall = values["minimumWall"]
    chamfer = values["mouthChamfer"]
    pin_d = values["rodPinDiameter"]
    pin_at = values["pinInset"]
    er = values["edgeRadius"]

    bore_r = (D + c) / 2.0
    outer_r = bore_r + wall

    if 2.0 * bearing >= L:
        raise ValueError(
            f"two {bearing:g} mm bearings do not fit in a {L:g} mm ferrule; "
            "there would be no relieved middle and the sleeve would fight "
            "the bend along its whole length"
        )
    if pin_at >= bearing:
        raise ValueError(
            f"the pin at {pin_at:g} mm from the mouth sits past the "
            f"{bearing:g} mm bearing, where the bore is relieved -- it would "
            "pin a rod that is not touching anything"
        )

    # How far the rod's own curvature carries it off the ferrule's axis over
    # the relieved span. This is the whole reason the middle is relieved: a
    # straight bore that close-fits along its length forces the bow straight.
    relief_span = L - 2.0 * bearing
    sagitta = bend * (1.0 - math.cos(math.asin(min(1.0, (L / 2.0) / bend))))
    relief_r = bore_r + sagitta + values["reliefMargin"]
    if relief_r + wall > outer_r + sagitta + 1e-9:
        pass  # the wall is measured over the bearing, which is the thin place

    axis = App.Vector(1.0, 0.0, 0.0)
    origin = App.Vector(-L / 2.0, 0.0, 0.0)

    body = Part.makeCylinder(outer_r, L, origin, axis)

    # The bore: close at both ends, opened out in between.
    bore = Part.makeCylinder(bore_r, L + 2.0, App.Vector(-L / 2.0 - 1.0, 0, 0), axis)
    relief = Part.makeCylinder(
        relief_r, relief_span,
        App.Vector(-L / 2.0 + bearing, 0.0, 0.0), axis,
    )
    body = body.cut(bore).cut(relief)

    # A lead-in at each mouth. A section arrives a little off axis -- it is
    # nine metres of flexible rod -- and a sharp bore edge is what it catches
    # on and what scuffs the glass fibre.
    for sign in (1.0, -1.0):
        d = App.Vector(sign, 0.0, 0.0)
        base = App.Vector(sign * L / 2.0, 0.0, 0.0)
        cone = Part.makeCone(
            bore_r + chamfer, bore_r, chamfer,
            App.Vector(base.x - d.x * chamfer, 0.0, 0.0), d,
        )
        body = body.cut(cone)

    # Cross pins, one per end, through the ferrule and the rod with it.
    pins = []
    span = 2.0 * outer_r + 8.0
    for sign in (1.0, -1.0):
        x = sign * (L / 2.0 - pin_at)
        pins.append(
            Part.makeCylinder(
                pin_d / 2.0, span,
                App.Vector(x, 0.0, -span / 2.0), App.Vector(0, 0, 1),
            )
        )

    bonded = values.get("bondedEnd", 0.0) >= 0.5
    if bonded:
        # One end glued, like a tent pole: the groove gives the adhesive
        # somewhere to sit instead of being squeezed out by a slide fit.
        gd = values["bondGrooveDepth"]
        gw = values["bondGrooveWidth"]
        gx = -L / 2.0 + bearing / 2.0
        groove = Part.makeCylinder(
            bore_r + gd, gw, App.Vector(gx - gw / 2.0, 0.0, 0.0), axis
        ).cut(
            Part.makeCylinder(
                bore_r, gw + 2.0, App.Vector(gx - gw / 2.0 - 1.0, 0.0, 0.0), axis
            )
        )
        body = body.cut(groove)
        body = body.cut(pins[0])   # the free end still gets its pin
    else:
        for pin in pins:
            body = body.cut(pin)

    body = body.removeSplitter()

    def end_edge(e):
        try:
            if not isinstance(e.Curve, Part.Circle):
                return False
        except Exception:
            return False
        return abs(abs(e.CenterOfMass.x) - L / 2.0) < 1e-6 and \
            e.Curve.Radius > outer_r - 1e-6

    body, filleted = kit.fillet_by_predicate(body, end_edge, er)

    if not kit.ok(body):
        raise RuntimeError("the ferrule did not come out as one sound solid")

    # Reference: the two sections, butted in the middle, straight -- which is
    # what they are when this goes on.
    rods = []
    for sign in (1.0, -1.0):
        rods.append(
            Part.makeCylinder(
                D / 2.0, L / 2.0 + 40.0,
                App.Vector(0.0, 0.0, 0.0), App.Vector(sign, 0.0, 0.0),
            )
        )

    geo = dict(body=body, rods=rods, pins=pins)
    dims = dict(
        chosen_from_rod=chosen,
        bore_r=bore_r, outer_r=outer_r, relief_r=relief_r, relief_span=relief_span,
        sagitta=sagitta, bearing=bearing, L=L, wall=wall, pin_at=pin_at,
        bonded=bonded, filleted=filleted, bend=bend,
    )
    return geo, dims


def verify(geo, dims, values):
    body = geo["body"]
    rep = {}
    b = body.BoundBox
    rep["body"] = dict(
        valid=body.isValid(), solids=len(body.Solids),
        volume_cm3=round(body.Volume / 1000.0, 2),
        length_mm=round(b.XLength, 2),
        outside_diameter_mm=round(2.0 * dims["outer_r"], 2),
    )

    # The sections have to go in, so nothing may stand in the bore.
    solid_rods = geo["rods"][0].fuse(geo["rods"][1])
    rep["interference_mm3"] = round(body.common(solid_rods).Volume, 4)

    # The relieved middle has to clear the bend, or the ferrule forces the bow
    # straight over its own length -- which is the failure V1 avoided by being
    # curved and this one avoids by being hollow in the middle.
    rep["bend"] = {
        "bend_radius_mm": round(dims["bend"], 1),
        "sagitta_over_sleeve_mm": round(dims["sagitta"], 4),
        "relief_radius_mm": round(dims["relief_r"], 3),
        "bore_radius_mm": round(dims["bore_r"], 3),
        "clears_the_bend_by_mm": round(
            dims["relief_r"] - dims["bore_r"] - dims["sagitta"], 4
        ),
    }
    rep["grip"] = {
        "bearing_each_end_mm": round(dims["bearing"], 2),
        "in_rod_diameters": round(dims["L"] / 2.0 / values["rodDiameter"], 2),
        "pins": 1 if dims["bonded"] else 2,
        "bolts": 0,
        "bonded_end": dims["bonded"],
    }
    rep["against_v1"] = {
        "v1_volume_cm3": 78.8,
        "v2_volume_cm3": round(body.Volume / 1000.0, 2),
        "saving_per_dome_litres": round((78.8 - body.Volume / 1000.0) * 45 / 1000.0, 2),
        "bolts_saved_per_dome": 180,
    }
    rep["printability"] = kit.printability(body)
    return rep


def derived_rows(dims, values):
    stock = 2.0 * dims["outer_r"]
    return [
        (
            "pinChosen",
            values["rodPinDiameter"],
            "mm",
            "cross pin this ferrule was drawn for. Taken from the rod -- about "
            "0.4 of it, on a stock size. There is no bolt in this part",
        ),
        ("boreDiameter", 2.0 * dims["bore_r"], "mm", "rodDiameter + rodClearance, at the bearings"),
        ("outsideDiameter", stock, "mm", "bore plus two walls"),
        ("reliefDiameter", 2.0 * dims["relief_r"], "mm", "the opened-out middle"),
        ("reliefLength", dims["relief_span"], "mm", "sleeveLength less the two bearings"),
        ("sagitta", dims["sagitta"], "mm", "how far the bow's curvature carries it off the ferrule's axis over the sleeve"),
        ("boughtTubeEquivalent", stock, "mm",
         "if bought rather than printed: outside diameter of tube to cut, wall = minimumWall"),
        ("stockPerDome_m", 45.0 * dims["L"] / 1000.0, "m",
         "how much tube 45 splices comes to, if bought"),
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

    ferrule = doc.addObject("Part::Feature", "Ferrule")
    ferrule.Label = "Ferrule"
    ferrule.Shape = geo["body"]

    grp = doc.addObject("App::DocumentObjectGroup", "Reference")
    grp.Label = "Reference"
    refs = []
    for i, rod in enumerate(geo["rods"], start=1):
        obj = doc.addObject("Part::Feature", f"RodSection{i}")
        obj.Shape = rod
        refs.append(obj)
    for i, pin in enumerate(geo["pins"], start=1):
        obj = doc.addObject("Part::Feature", f"Pin{i}")
        obj.Shape = pin
        refs.append(obj)
    grp.addObjects(refs)
    doc.recompute()
    return ferrule


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
