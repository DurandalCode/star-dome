# -*- coding: utf-8 -*-
"""
Lay a connector's pieces out the way they are printed, and say what fits.

WHAT THIS IS FOR

`generate_clamps.py` exports every piece in the frame the part is DESIGNED in,
which is the right frame for putting a connector on a dome and the wrong one
for putting it on a bed. Two of the four things a slicer needs are missing from
it: which face each piece sits on, and whether the set fits the machine at all.
Both are known here -- the generator already says which pieces print the other
way up, because that is what its overhang check was judged against -- and
nobody should be turning parts by hand in a slicer and guessing.

So this writes a second set of meshes: each piece turned onto the face it
prints on, dropped so that face is at z = 0, and packed onto beds.

    exports/print/<variant>/<part>_<piece>.stl     one piece, ready to place
    exports/print/<variant>/<part>_bed<N>.stl      a bedful, already arranged

The pieces are the same solids `generate_clamps.py` builds. Nothing here
changes geometry; if a piece does not fit the bed, it says so rather than
scaling anything.

WHAT IT DOES NOT DO

**Supports, and it should not need to.** Every piece of the base hub prints
face-down with nothing steeper than 45 deg over it -- `make clamps` reports
that per piece, and if that ever stops being true the answer is to change the
part, not to switch supports on.

**Settings.** Layer height, walls, infill and material are a slicer's and a
filament's business, and `docs/printing.md` says what this project assumes and
why rather than pretending to a profile.

Run:

    <freecadcmd> connectors/print_sheet.py
    VARIANT='d6' BED='256x256' <freecadcmd> connectors/print_sheet.py

or through `make prints V=S BED=220x220`, which regenerates the schedule first.
"""

import json
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

try:
    VARIANT
except NameError:
    VARIANT = os.environ.get("VARIANT", "d4")

try:
    BED
except NameError:
    BED = os.environ.get("BED", "220x220")

if os.path.join(REPO, "connectors") not in sys.path:
    sys.path.insert(0, os.path.join(REPO, "connectors"))
import kit  # noqa: E402  -- needs the path set above

# Room round each piece on the bed. Brim, a skirt, and the plain fact that a
# slicer's arrange would leave more.
SPACING = 6.0
# And off the edge, where a bed's first layer is least trustworthy.
MARGIN = 5.0

BASE_SOURCE = os.path.join(REPO, "connectors", "base_hub_v1.py")
OUT_ROOT = os.path.join(REPO, "exports", "print")


def load(source):
    """A generator's functions, without letting it auto-build."""
    namespace = {"SUPPRESS_AUTORUN": True, "__file__": source, "REPO": REPO}
    with open(source) as handle:
        exec(compile(handle.read(), source, "exec"), namespace)
    return namespace


def bed_size(text):
    """`220x220` -> (220.0, 220.0). A bed is two numbers and no units."""
    try:
        wide, deep = (float(part) for part in text.lower().split("x"))
    except ValueError:
        raise ValueError(f"a bed is WIDTHxDEPTH in mm, not {text!r}")
    return wide, deep


def true_box(shape):
    """The box the solid actually occupies.

    `Shape.BoundBox` is taken from the surfaces' control points, not from the
    surfaces, so on anything curved it can stand a fraction of a millimetre
    proud of the real thing. That is harmless in a drawing and not harmless
    here: it is the difference between a piece that sits on the bed and one
    that floats 0.43 mm above it, which is what the middle plates did.
    """
    try:
        return shape.optimalBoundingBox(True)
    except Exception:      # an older OCC: the loose box, and a note in the log
        App.Console.PrintWarning(
            "print_sheet: no optimalBoundingBox here; pieces may sit proud\n"
        )
        return shape.BoundBox


def onto_the_bed(solid, flipped):
    """The piece as it is printed: turned if it prints the other way up, and
    dropped so the face it sits on is z = 0 with its corner at the origin.

    Turned about X rather than Y, so that a piece which is longer than it is
    wide stays that way round and the packing below sees the footprint it will
    actually occupy.
    """
    piece = solid.copy()
    if flipped:
        piece.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 180.0)
    box = true_box(piece)
    piece.translate(App.Vector(-box.XMin, -box.YMin, -box.ZMin))
    return piece


def pack(pieces, bed):
    """Shelf packing, tallest first: the arrangement a person does by hand.

    Returns a list of beds, each a list of (name, solid, x, y). A piece too big
    for the bed gets a bed of its own and is reported by the caller; nothing is
    rotated to make it fit, because a piece that only fits diagonally is a
    piece somebody will print wrong.
    """
    wide, deep = bed
    order = sorted(
        pieces, key=lambda item: -true_box(item[1]).YLength
    )
    beds, current = [], []
    x = y = MARGIN
    shelf = 0.0
    for name, solid in order:
        box = true_box(solid)
        if x + box.XLength + MARGIN > wide and current:
            x = MARGIN
            y += shelf + SPACING
            shelf = 0.0
        if y + box.YLength + MARGIN > deep and current:
            beds.append(current)
            current = []
            x = y = MARGIN
            shelf = 0.0
        current.append((name, solid, x, y))
        x += box.XLength + SPACING
        shelf = max(shelf, box.YLength)
    if current:
        beds.append(current)
    return beds


def fits(solid, bed):
    box = true_box(solid)
    return (
        box.XLength + 2.0 * MARGIN <= bed[0]
        and box.YLength + 2.0 * MARGIN <= bed[1]
    )


def run(variant=None, bed=None):
    variant = (variant or VARIANT).lower()
    bed = bed_size(bed or BED)
    schedule_path = os.path.join(
        REPO, "exports", "model", "star_dome_%s_connectors.json" % variant
    )
    with open(schedule_path) as handle:
        schedule = json.load(handle)

    base = load(BASE_SOURCE)
    out_dir = os.path.join(OUT_ROOT, variant)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    report = {"variant": variant, "bed_mm": list(bed), "parts": []}
    for part in schedule["parts"]:
        if part.get("generator") != "base_hub_v1":
            continue
        values = {alias: value for (alias, value, _u, _n) in base["INPUTS"]}
        values["rodDiameter"] = float(part["rod_diameter"])
        values["rodNominalDiameter"] = float(
            part.get("rod_nominal_diameter") or part["rod_diameter"]
        )
        values["firstArmRise"] = float(part["arm_azimuths_deg"][0])
        geo, _dims = base["build"](values, fan_gaps=part["fan_gaps_deg"])
        flipped = base["FLIPPED_PIECES"]

        pieces = [
            (name, onto_the_bed(solid, name in flipped))
            for name, solid in zip(geo["names"], geo["plates"])
        ]

        entry = {
            "id": part["id"],
            "count": part["count"],
            "pieces": [],
            "too_big": [],
            "files": [],
        }
        for name, solid in pieces:
            box = true_box(solid)
            entry["pieces"].append(
                {
                    "piece": name,
                    "on_the_bed": "outer face, printed upside down"
                    if name in flipped
                    else "as drawn, lower face down",
                    "footprint_mm": [round(box.XLength, 1), round(box.YLength, 1)],
                    "tall_mm": round(box.ZLength, 1),
                    "cm3": round(kit.vol(solid) / 1000.0, 1),
                    "each_dome": part["count"],
                }
            )
            if not fits(solid, bed):
                entry["too_big"].append(name)
            step, stl, _facets = kit.export_solid(
                solid, "%s_%s" % (part["id"], name), out_dir
            )
            entry["files"].extend(os.path.basename(f) for f in (step, stl))

        beds = pack(pieces, bed)
        for index, laid in enumerate(beds, start=1):
            placed = []
            for name, solid, x, y in laid:
                copy = solid.copy()
                copy.translate(App.Vector(x, y, 0.0))
                placed.append(copy)
            _step, stl, _facets = kit.export_solid(
                Part.makeCompound(placed),
                "%s_bed%d" % (part["id"], index),
                out_dir,
            )
            entry["files"].append(os.path.basename(stl))
        entry["beds_per_hub"] = len(beds)
        entry["bed_contents"] = [
            [name for name, _s, _x, _y in laid] for laid in beds
        ]
        entry["beds_per_dome"] = len(beds) * part["count"]
        report["parts"].append(entry)

    report["out_dir"] = out_dir
    return report


if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint

    pprint.pprint(REPORT, width=100)
