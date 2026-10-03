# -*- coding: utf-8 -*-
"""
Star Dome skirt collar, prototype V1.

WHAT THE SKIRT'S JOINTS TURNED OUT TO BE

The schedule used to read the skirted base point as eight members -- three bow
ends, the post head, two ring chords and two brace heads -- and it was the
busiest joint in the structure with nothing designed for it. None of that had
to be true.

`base_hub_v1` already carries a through slot for a driven steel angle and two
bolts across it. **A skirt post is that same angle, longer**: driven at the
bottom, standing in the hub's slot at the top, one member doing both jobs. So
the post is no more a member of the base point than a stake is, and the hub is
the same part on a skirted dome as on a bare one.

What is left is the skirt's own two members at each end of each post -- a ring
chord and a brace -- times two sides. That is this part.

ONE PART, BOTH ENDS

The head and the foot are the same shape. At both, the chords leave level and
the braces leave at the same angle: downward at the head, upward at the foot.
Turn the collar over about the outward radius and one becomes the other, so
there is one geometry and twenty of them on a ten-post dome.

THE TWO MEMBERS ARE COPLANAR, WHICH IS WHY A FLAT LUG IS ENOUGH

The chord to the next post and the brace to that post's other end leave on the
same plan azimuth -- 90 + 180/n from the outward radius, 108 deg on a decagon
-- one level and one at the brace angle. Both therefore lie in ONE vertical
plane, so one flat lug per side carries both, with a hole for each.

WHAT THIS PART DELIBERATELY DOES NOT DECIDE

**What the ring chord is made of.** A GFRP rod of the dome's own diameter
buckles at well under a hundred newtons over a chord this long, so the ring is
a section somebody has to specify -- milestone 8. That is exactly why the lug
ends in a bolt hole rather than a socket: a hole takes a rod end fitting, an
angle bolted flat, or a strap, and does not have to be redrawn when the
question is answered.

**Whether a printed collar can carry the ring's force.** It locates the
members and clamps the post. The load path through it is not checked here and
nothing in this file checks it.

Run:  exec(open('<repo>/connectors/skirt_collar_v1.py').read())
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

DOC_NAME = "StarDome_SkirtCollar_V1"
TITLE = "Star Dome skirt collar V1 - parameters"
OUT_DIR = os.path.join(REPO, "connectors")
SAVE_PATH = os.path.join(OUT_DIR, "star_dome_skirt_collar_v1.FCStd")
USE_SPREADSHEET_IF_PRESENT = True

# Brace arm up. Both ways round are real orientations (`verify` reports both);
# arm up leaves about a third of the area steeper than 45 deg that arm down
# does -- 254 mm2 against 787 at the default parameters.
FLIPPED_PIECES = {"Collar"}

# The post section is the hub's stake section. If one moves the other has to,
# because they are the same piece of steel.
INPUTS = [
    ("rodDiameter",          8.0,  "mm", "the dome's own rod; sets the fastener and the wall"),
    ("postLeg",             30.0,  "mm", "each leg of the steel angle the post is, across"),
    ("postThickness",        3.0,  "mm", "the angle's material thickness"),
    ("postClearance",        0.6,  "mm", "fit clearance on the post bore, per side"),
    ("chordAzimuth",       108.0, "deg", "plan angle of a ring chord from the outward radius"),
    ("braceRise",        47.5226, "deg", "how far the brace leaves off level"),
    ("collarHeight",        46.0,  "mm", "how much of the post the collar grips"),
    ("armWidth",            18.0,  "mm", "across each lug arm, square to the member it holds"),
    ("holeMargin",          10.0,  "mm", "material past a bolt hole, out to the arm's end"),
    ("minimumWall",          0.0,  "mm", "0 takes it from the rod -- see kit.wall_for"),
    ("lugThickness",         6.0,  "mm", "the flat lug either side"),
    ("lugReach",            34.0,  "mm", "how far the lug stands out past the bore"),
    ("fastenerSize",         0.0,  "",   "which metric bolt: 0 chooses it from the rod"),
    ("fastenerDiameter",     0.0,  "mm", "clearance hole; 0 takes it from rodDiameter"),
    ("boltHoleClearance",    0.4,  "mm", "diametral print clearance on a bolt shank hole"),
    ("clampBoltDiameter",    0.0,  "mm", "the two bolts pinching the post; 0 follows the fastener"),
    ("edgeRadius",           1.5,  "mm", "fillet on the outside edges"),
]


def _bore(values):
    """The square the angle's section sits inside, plus fit clearance."""
    return values["postLeg"] + 2.0 * values["postClearance"]


def post_solid(values, length, z):
    """The post itself, for drawing and for clearance checks.

    An L in section, not a bar. The hub gets its resistance to twisting on the
    post out of that section, and so does this -- a square bore round an L
    cannot spin the post without driving one leg into a wall.
    """
    leg = values["postLeg"]
    t = values["postThickness"]
    half = leg / 2.0
    flat = Part.makeBox(leg, t, length, App.Vector(-half, -half, z))
    upright = Part.makeBox(t, leg, length, App.Vector(-half, -half, z))
    return flat.fuse(upright).removeSplitter()


def ray_arm(values, azimuth_deg, rise_deg, length, width):
    """A flat arm running out along one member's own ray.

    The lug is not a rectangle: the chord leaves level and the brace leaves at
    the brace angle, so an arm that reached both would be mostly material
    holding nothing. One arm per member instead, each lying in the vertical
    plane at this azimuth and pointing where its member goes.
    """
    thickness = values["lugThickness"]
    box = Part.makeBox(
        length, thickness, width,
        App.Vector(0.0, -thickness / 2.0, -width / 2.0),
    )
    # Tip it up out of the horizontal, then swing it round to its azimuth --
    # in that order, because the rise is measured in the vertical plane the
    # azimuth defines.
    box.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -rise_deg)
    box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    return box


def lug(values, azimuth_deg, bore, chord_at, brace_at):
    """One side's pair of arms: the chord's, level, and the brace's, inclined."""
    width = values["armWidth"]
    margin = values["holeMargin"]
    chord = ray_arm(values, azimuth_deg, 0.0, chord_at + margin, width)
    brace = ray_arm(
        values, azimuth_deg, -values["braceRise"], brace_at + margin, width
    )
    return chord.fuse(brace).removeSplitter()


def hole_axis(values, azimuth_deg, rise_deg, distance, diameter, length):
    """A bolt hole through a lug, drilled perpendicular to the plate.

    The member leaves along (azimuth, rise); the hole sits on that ray at
    ``distance`` and runs across the plate, which is the direction a bolt in a
    lug always runs.
    """
    d = kit.direction(azimuth_deg)
    rise = math.radians(rise_deg)
    centre = App.Vector(
        d.x * distance * math.cos(rise),
        d.y * distance * math.cos(rise),
        distance * math.sin(rise),
    )
    across = kit.direction(azimuth_deg + 90.0)
    start = centre - across.multiply(length / 2.0)
    return Part.makeCylinder(
        diameter / 2.0, length, start, kit.direction(azimuth_deg + 90.0)
    )


def build(values):
    """The collar: a bored block on the post, a lug either side, two pinch bolts."""
    kit.scale_to_rod(values)
    bore = _bore(values)
    # The bore is a hole through a block, so the block has to be the bore plus
    # a wall on each side or there is no block left after the cut.
    wall = values["minimumWall"]
    height = values["collarHeight"]
    bolt = values["fastenerDiameter"] + values["boltHoleClearance"]
    clamp_bolt = values["clampBoltDiameter"] or bolt

    outer = bore + 2.0 * wall
    body = Part.makeBox(
        outer, outer, height,
        App.Vector(-outer / 2.0, -outer / 2.0, -height / 2.0),
    )

    # Holes are placed first, because the arms have to be long enough to
    # carry them and the arm length is the hole distance plus a margin.
    chord_at = bore / 2.0 + values["lugReach"] * 0.45
    brace_at = bore / 2.0 + values["lugReach"] * 0.45

    azimuths = (values["chordAzimuth"], -values["chordAzimuth"])
    for azimuth in azimuths:
        body = body.fuse(lug(values, azimuth, bore, chord_at, brace_at))
    body = body.removeSplitter()
    body, _filleted = kit.fillet_by_predicate(
        body, kit.is_vertical_edge, values["edgeRadius"]
    )

    # The bore runs right through, over the whole height of the part and not
    # just of its body: the brace arm dips below the body, and a bore that
    # stopped at the body would leave that arm sitting in the post's way.
    span = body.BoundBox
    cut = Part.makeBox(
        bore, bore, span.ZLength + 8.0,
        App.Vector(-bore / 2.0, -bore / 2.0, span.ZMin - 4.0),
    )
    solid = body.cut(cut)

    # Two bolts pinching across the bore, on the diagonals that press the
    # angle's corner into the opposite corner. A single bolt on the centre
    # line would let the post rock about it.
    #
    # One is at +45 high and the other at -45 low, and that pairing is not
    # decoration: turning the collar over about the outward radius maps each
    # onto the other, so the flipped head collar is exactly the foot collar.
    # Two bolts on the same diagonal would break that and make this two parts.
    pinch = []
    span = outer + 2.0 * values["lugThickness"] + 20.0
    for azimuth, z in ((45.0, height / 4.0), (-45.0, -height / 4.0)):
        axis = kit.direction(azimuth)
        start = App.Vector(
            -axis.x * span / 2.0, -axis.y * span / 2.0, z
        )
        pinch.append(
            Part.makeCylinder(clamp_bolt / 2.0, span, start, axis)
        )
    for hole in pinch:
        solid = solid.cut(hole)

    # One hole per member per side: the chord on the level, the brace down its
    # own ray. Distances are measured from the post axis along each ray.
    across = outer + 2.0 * values["lugThickness"] + 20.0
    holes = []
    for azimuth in azimuths:
        holes.append(
            hole_axis(values, azimuth, 0.0, chord_at, bolt, across)
        )
        holes.append(
            hole_axis(values, azimuth, -values["braceRise"], brace_at, bolt, across)
        )
    for hole in holes:
        solid = solid.cut(hole)

    solid = solid.removeSplitter()
    dims = {
        "bore_mm": bore,
        "outer_mm": outer,
        "height_mm": height,
        "wall_mm": wall,
        "bolt_mm": bolt,
        "clamp_bolt_mm": clamp_bolt,
        "chord_hole_at_mm": chord_at,
        "brace_hole_at_mm": brace_at,
        "lug_span_mm": 2.0 * (bore / 2.0 + values["lugReach"]),
    }
    return {"collar": solid, "post": post_solid(values, height * 3.0, -height * 1.5)}, dims


def verify(geo, dims, values):
    """What the part has to be true for, checked on the solid rather than claimed."""
    collar = geo["collar"]
    rep = {
        "valid_solid": kit.ok(collar),
        "volume_cm3": round(kit.vol(collar) / 1000.0, 2),
        "bbox": [
            round(collar.BoundBox.XLength, 2),
            round(collar.BoundBox.YLength, 2),
            round(collar.BoundBox.ZLength, 2),
        ],
        "dims": {k: round(v, 3) for k, v in dims.items()},
    }

    # The post must actually pass through, and with its fit clearance intact.
    post = geo["post"]
    rep["post_passes"] = not kit.has_volume(collar.common(post))

    # Turned over about the outward radius, the HEAD collar has to be the FOOT
    # collar. Not symmetric -- it is not, and must not be: the brace leaves
    # downward at one end and upward at the other. So the check builds the
    # foot explicitly and asks whether the flipped head is that part.
    foot_values = dict(values)
    foot_values["braceRise"] = -values["braceRise"]
    foot = build(foot_values)[0]["collar"]
    flipped = collar.copy()
    flipped.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 180.0)
    shared = kit.vol(flipped.common(foot))
    both = kit.vol(flipped.fuse(foot))
    rep["head_turned_over_is_the_foot"] = {
        "shared_fraction": round(shared / both, 4) if both else 0.0,
        "note": (
            "1.0 means one printed geometry serves both ends of every post: "
            "turn a head collar over about the outward radius and it is a "
            "foot collar. The chords leave level at both ends and the braces "
            "leave at the same angle, down at the head and up at the foot."
        ),
    }

    # The bore stands up either way -- the part is used both ways up, so both
    # are real orientations and the better one is a choice, not a constraint.
    rep["printability"] = {
        "brace_arm_down": kit.printability(collar),
        "brace_arm_up": kit.printability(collar, flipped=True),
    }
    return rep


def derived_rows(dims, values):
    return [
        ("bore", dims["bore_mm"], "mm", "square the post's angle sits in, with clearance"),
        ("outer", dims["outer_mm"], "mm", "across the clamped body"),
        ("lugSpan", dims["lug_span_mm"], "mm", "lug tip to lug tip"),
        ("chordHoleAt", dims["chord_hole_at_mm"], "mm", "ring chord bolt, from the post axis"),
        ("braceHoleAt", dims["brace_hole_at_mm"], "mm", "brace bolt, along its own ray"),
        ("clampBolt", dims["clamp_bolt_mm"], "mm", "the two bolts pinching the post"),
    ]


def populate(doc, geo):
    made = []
    for name, shape in (("Collar", geo["collar"]),):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        made.append(obj)
    return made


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
