# -*- coding: utf-8 -*-
"""
Star Dome bow splice, V1 -- the ferrule that joins two transport sections.

WHY THIS PART EXISTS

A bow is a semicircle of the dome's radius -- 9.4 m on M, 18.8 m on D12 -- and
nothing carries that, so it travels in sections and is joined on site. The
recorded transport limit is 3500 mm, which puts M at four sections of 2356 and
D12 at seven of 2693. See docs/transport.md.

WHAT IT IS

**One part, used twice, with a bought stud between.** Each half is a steel
socket: bored for the rod at the outer end, tapped at the inner end, and the
two are pulled together by a threaded stud. The alternative -- a male half and
a female half -- is two parts to make, two to stock and two to pick up in a
field with cold hands, for no gain. The stud IS the male.

    rod -> [ bore, engagement ][ shoulder ][ thread ] | [ thread ][ shoulder ][ bore ] <- rod
                                                     stud

A cross pin through ferrule and rod carries the axial load and stops the rod
turning; the bore is a slide fit, not an interference one, so the joint can be
made and unmade with a punch.

THE THING THIS PART IS FIGHTING

The bow is **bent everywhere**, so the ferrule carries bending continuously,
and steel is the wrong stiffness for that: to match a GFRP rod's EI a steel
tube would need a 0.2 mm wall, and this one needs 2 mm to hold a thread and a
pin. That is 15.6x the rod's stiffness on M -- the joint does not share the
curve, and the bow takes the extra bend just outside it.

Steel is the recorded decision (docs/transport.md), so the part carries it the
only way it can: **the outside tapers.** Full diameter at the joint face where
the thread and the stud need meat, thinning to the least wall anyone rolls by
the mouth where the rod leaves. That spreads the stiffness step over the
engagement instead of standing it at one section, and it takes the ratio at
the mouth from 15.6x down to 4.5x. verify() reports both ends, so the cost of
turning the taper off is visible rather than assumed.

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
STEEL_MODULUS = materials.SLEEVE["steel_mild"]["modulus_mpa"]
STEEL_DENSITY = materials.SLEEVE["steel_mild"]["density_kgm3"]

# The tightest half-span between two crossings, from stardome's own free_spans
# on the smallest dome that uses this part. A fact about the dome, an input
# here. python3 -m stardome splice --all reports it.
MIN_HALF_SPAN_MM = 200.0

DOC_NAME = "StarDome_Splice_V1"
TITLE = "Star Dome bow splice V1 - parameters"
USE_SPREADSHEET_IF_PRESENT = True

INPUTS = [
    # alias,                 value,  unit,  note
    ("rodDiameter",           10.0,  "mm",  "nominal GFRP rod diameter. 8 for D3/D4, 10 for D6/D8, 12 for D10/D12 -- the whole part follows it"),
    ("rodClearance",           0.4,  "mm",  "diametral clearance in the bore: a slide fit, so the joint can be made and unmade with a punch"),
    ("engagementFactor",       6.0,  "-",   "how far the rod goes in, in rod diameters. The lever that trades the hard spot against the part's length"),
    ("jointWall",              2.0,  "mm",  "wall at the joint face, where the thread and the stud need meat"),
    ("mouthWall",              0.8,  "mm",  "wall at the mouth, where the rod leaves. The thinnest anyone rolls; this is what softens the stiffness step"),
    ("taper",                  1.0,  "-",   "1 = taper the outside from joint to mouth, 0 = straight tube. Off costs a 3x harder step -- see verify"),
    ("studDiameter",           6.0,  "mm",  "M6 stud between the two halves. Must clear the bore's own wall"),
    ("threadDepth",           14.0,  "mm",  "tapped depth each side. Wants at least one diameter of thread"),
    ("shoulderThickness",      3.0,  "mm",  "material between the bottom of the rod bore and the tapped hole; the rod butts on it"),
    ("mouthFlare",             2.5,  "mm",  "axial length of the flared mouth. A square bore edge is a stress raiser on fibreglass"),
    ("mouthFlareRise",         0.35, "mm",  "radial rise of that flare"),
    ("pinDiameter",            4.0,  "mm",  "cross pin through ferrule and rod: carries the axial load and stops the rod turning"),
    ("pinAt",                 22.0,  "mm",  "how far the pin sits from the mouth"),
    ("faceChamfer",            0.6,  "mm",  "chamfer on the joint face, so two ferrules seat without a burr holding them apart"),
]


def _rod_bore(bore_r, length, z):
    """The bore the rod slides into, opening at the mouth."""
    return Part.makeCylinder(bore_r, length, App.Vector(0, 0, z),
                             App.Vector(0, 0, 1))


def _flare(bore_r, rise, length, z):
    """A cone opening the mouth, so the rod does not bear on a square edge."""
    return Part.makeCone(bore_r + rise, bore_r, length,
                         App.Vector(0, 0, z), App.Vector(0, 0, 1))


def build(values):
    rod_d = values["rodDiameter"]
    clearance = values["rodClearance"]
    engagement = values["engagementFactor"] * rod_d
    joint_wall = values["jointWall"]
    mouth_wall = values["mouthWall"]
    tapered = values["taper"] >= 0.5
    stud_d = values["studDiameter"]
    thread_depth = values["threadDepth"]
    shoulder = values["shoulderThickness"]
    flare_len = values["mouthFlare"]
    flare_rise = values["mouthFlareRise"]
    pin_d = values["pinDiameter"]
    pin_at = values["pinAt"]
    chamfer = values["faceChamfer"]

    bore_r = (rod_d + clearance) / 2.0
    mouth_od = 2.0 * (bore_r + mouth_wall)
    joint_od = 2.0 * (bore_r + joint_wall)
    length = engagement + shoulder + thread_depth

    # The body: mouth at z = 0, joint face at z = length. Tapered outside runs
    # the whole way, so the section changes gradually rather than at a step.
    if tapered:
        body = Part.makeCone(mouth_od / 2.0, joint_od / 2.0, length,
                             App.Vector(0, 0, 0), App.Vector(0, 0, 1))
    else:
        body = Part.makeCylinder(joint_od / 2.0, length,
                                 App.Vector(0, 0, 0), App.Vector(0, 0, 1))

    # The bore for the rod, from the mouth in.
    body = body.cut(_rod_bore(bore_r, engagement, 0.0))
    # Flare it, so the fibreglass does not bear on a square edge.
    body = body.cut(_flare(bore_r, flare_rise, flare_len, 0.0))

    # The tapped hole, from the joint face in. Drawn at the tapping diameter:
    # a thread is a note on a drawing, not a solid.
    tap_r = (stud_d * 0.85) / 2.0
    body = body.cut(
        Part.makeCylinder(tap_r, thread_depth + 0.01,
                          App.Vector(0, 0, length - thread_depth),
                          App.Vector(0, 0, 1))
    )

    # The cross pin, through everything at pin_at from the mouth.
    pin_hole = Part.makeCylinder(
        pin_d / 2.0, joint_od + 4.0,
        App.Vector(0, -(joint_od + 4.0) / 2.0, pin_at),
        App.Vector(0, 1, 0),
    )
    body = body.cut(pin_hole)

    # Chamfer the joint face so a burr cannot hold two ferrules apart.
    if chamfer > 0:
        def on_face(edge):
            try:
                return all(abs(v.Point.z - length) < 1e-6 for v in edge.Vertexes)
            except Exception:
                return False

        body, _ = kit.fillet_by_predicate(body, on_face, chamfer)

    ferrule = body.removeSplitter()

    # --- reference geometry, for the drawing rather than the part ----------
    mirror = ferrule.copy()
    mirror.rotate(App.Vector(0, 0, length), App.Vector(1, 0, 0), 180.0)
    mirror.translate(App.Vector(0, 0, 0))

    stud = Part.makeCylinder(
        stud_d / 2.0, 2.0 * thread_depth,
        App.Vector(0, 0, length - thread_depth), App.Vector(0, 0, 1),
    )

    rod_ref = Part.makeCylinder(
        rod_d / 2.0, engagement + 60.0,
        App.Vector(0, 0, -60.0), App.Vector(0, 0, 1),
    )

    pins = [
        Part.makeCylinder(pin_d / 2.0, joint_od + 4.0,
                          App.Vector(0, -(joint_od + 4.0) / 2.0, pin_at),
                          App.Vector(0, 1, 0)),
        Part.makeCylinder(pin_d / 2.0, joint_od + 4.0,
                          App.Vector(0, -(joint_od + 4.0) / 2.0,
                                     2.0 * length - pin_at),
                          App.Vector(0, 1, 0)),
    ]

    geo = {
        "ferrule": ferrule,
        "mirror": mirror,
        "stud": stud,
        "rod": rod_ref,
        "pins": pins,
    }
    dims = {
        "rod_diameter_mm": rod_d,
        "bore_diameter_mm": 2.0 * bore_r,
        "engagement_mm": engagement,
        "length_mm": length,
        "pair_length_mm": 2.0 * length,
        "mouth_od_mm": mouth_od,
        "joint_od_mm": joint_od,
        "joint_wall_mm": joint_wall,
        "mouth_wall_mm": mouth_wall,
        "tapered": 1.0 if tapered else 0.0,
        "stud_diameter_mm": stud_d,
        "stud_length_mm": 2.0 * thread_depth,
        "thread_depth_mm": thread_depth,
        "shoulder_mm": shoulder,
        "pin_diameter_mm": pin_d,
        "pin_at_mm": pin_at,
        "over_rod_mm": joint_od - rod_d,
    }
    return geo, dims


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
def _second_moment(od, bore):
    return math.pi * (od ** 4 - bore ** 4) / 64.0


def verify(geo, dims, values):
    """Every way this part could be wrong that geometry can see."""
    problems = []
    ferrule = geo["ferrule"]

    if not kit.ok(ferrule):
        problems.append("the ferrule is not one sound solid")

    bore = dims["bore_diameter_mm"]
    if bore <= dims["rod_diameter_mm"]:
        problems.append("the bore does not clear the rod")

    # The tapped hole must leave wall at the joint end.
    tap_d = values["studDiameter"] * 0.85
    wall_at_thread = (dims["joint_od_mm"] - tap_d) / 2.0
    if wall_at_thread < 1.5:
        problems.append(
            f"only {wall_at_thread:.1f} mm of wall round the thread"
        )

    # The stud has to fit inside the rod's own bore, or it cannot be dropped
    # in from the joint face at all.
    if values["studDiameter"] >= bore:
        problems.append(
            f"an M{values['studDiameter']:g} stud does not fit a "
            f"{bore:.1f} mm bore"
        )

    # The pin must be in the engaged length, and clear of the tapped hole.
    if dims["pin_at_mm"] >= dims["engagement_mm"]:
        problems.append("the cross pin is past the end of the rod")
    thread_starts = dims["length_mm"] - dims["thread_depth_mm"]
    if dims["pin_at_mm"] + dims["pin_diameter_mm"] / 2.0 > thread_starts:
        problems.append("the cross pin runs into the tapped hole")

    # The rod must butt on the shoulder, not on the stud.
    if dims["shoulder_mm"] <= 0:
        problems.append("no shoulder for the rod to butt against")

    # The point of the taper: how hard the step is at each end.
    rod_i = math.pi * dims["rod_diameter_mm"] ** 4 / 64.0
    ei_rod = ROD_MODULUS * rod_i
    joint_ratio = STEEL_MODULUS * _second_moment(
        dims["joint_od_mm"], bore) / ei_rod
    mouth_ratio = STEEL_MODULUS * _second_moment(
        dims["mouth_od_mm"], bore) / ei_rod

    if dims["tapered"] and mouth_ratio >= joint_ratio:
        problems.append("the taper does not soften anything")

    # The whole pair has to sit in the gap between two crossings. The room is
    # a fact about the dome, not about this part, so it is an input here.
    if dims["pair_length_mm"] / 2.0 > MIN_HALF_SPAN_MM:
        problems.append(
            f"half the pair is {dims['pair_length_mm'] / 2.0:.0f} mm, more "
            f"than the {MIN_HALF_SPAN_MM:.0f} mm the tightest span leaves"
        )

    return {
        "problems": problems,
        "ok": not problems,
        "ferrule_volume_cm3": round(kit.vol(ferrule) / 1000.0, 2),
        "ferrule_mass_g": round(
            kit.vol(ferrule) / 1000.0 * STEEL_DENSITY / 1000.0, 1
        ),
        "stiffness_at_joint": round(joint_ratio, 1),
        "stiffness_at_mouth": round(mouth_ratio, 1),
        "softened_by": round(joint_ratio / mouth_ratio, 2) if mouth_ratio else None,
        "wall_at_thread_mm": round(wall_at_thread, 2),
        "key_dims": {
            "length_mm": round(dims["length_mm"], 1),
            "pair_length_mm": round(dims["pair_length_mm"], 1),
            "joint_od_mm": round(dims["joint_od_mm"], 1),
            "mouth_od_mm": round(dims["mouth_od_mm"], 1),
            "over_rod_mm": round(dims["over_rod_mm"], 1),
        },
        "note": (
            "Geometry only. Nothing here is a load check: the bending the "
            "joint actually sees, and whether steel at this stiffness is "
            "acceptable, is milestone 8."
        ),
    }


def derived_rows(dims, values):
    rows = [
        ("bore", round(dims["bore_diameter_mm"], 2), "mm",
         "slide fit on the rod, so the joint comes apart with a punch"),
        ("engagement", round(dims["engagement_mm"], 1), "mm",
         f"{values['engagementFactor']:g} rod diameters into each half"),
        ("length", round(dims["length_mm"], 1), "mm", "one ferrule"),
        ("pairLength", round(dims["pair_length_mm"], 1), "mm",
         "the whole splice; has to sit between two crossings"),
        ("jointOD", round(dims["joint_od_mm"], 1), "mm",
         "at the joint face, where the thread needs meat"),
        ("mouthOD", round(dims["mouth_od_mm"], 1), "mm",
         "at the mouth, where the rod leaves"),
        ("overRod", round(dims["over_rod_mm"], 1), "mm",
         "how much fatter than the rod at its widest"),
        ("stud", f"M{values['studDiameter']:g} x "
                 f"{dims['stud_length_mm']:.0f}", "-",
         "bought; the male half of a male-female joint"),
        ("pin", f"{values['pinDiameter']:g} mm at "
                f"{values['pinAt']:g}", "-",
         "carries the axial load and stops the rod turning"),
        ("perSplice", 2, "-", "identical halves, one part number"),
    ]
    return rows


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------
FERRULE_COLOUR = (0.55, 0.55, 0.58)
STUD_COLOUR = (0.80, 0.70, 0.25)
ROD_COLOUR = (0.15, 0.55, 0.95)
PIN_COLOUR = (0.35, 0.35, 0.38)


def populate(doc, geo):
    for name, shape, colour in (
        ("Ferrule", geo["ferrule"], FERRULE_COLOUR),
        ("Ferrule_Mirror", geo["mirror"], FERRULE_COLOUR),
        ("Stud", geo["stud"], STUD_COLOUR),
        ("ref_Rod", geo["rod"], ROD_COLOUR),
    ):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
    for i, pin in enumerate(geo["pins"], start=1):
        obj = doc.addObject("Part::Feature", f"Pin{i}")
        obj.Shape = pin
    doc.recompute()
    return doc


def apply_view(doc):
    """Colours per docs/colours.md; the rod is its family blue."""
    if not hasattr(App, "Gui"):
        return doc
    try:
        gui = App.Gui
    except Exception:
        return doc
    for obj in doc.Objects:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        if obj.Name.startswith("Ferrule"):
            view.ShapeColor = FERRULE_COLOUR
            view.Transparency = 40
        elif obj.Name.startswith("Stud"):
            view.ShapeColor = STUD_COLOUR
        elif obj.Name.startswith("ref_Rod"):
            view.ShapeColor = ROD_COLOUR
        elif obj.Name.startswith("Pin"):
            view.ShapeColor = PIN_COLOUR
    return doc


def run(out_dir=None, doc_path=None, rod_diameter=None):
    doc = kit.document(DOC_NAME, doc_path)
    sheet, values = kit.read_or_build_parameters(
        doc, INPUTS, USE_SPREADSHEET_IF_PRESENT
    )
    if rod_diameter:
        values["rodDiameter"] = float(rod_diameter)
        # Everything that scales with the rod, scales with the rod.
        values["studDiameter"] = max(4.0, round(rod_diameter * 0.6))
        values["pinDiameter"] = max(3.0, round(rod_diameter * 0.4))

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
