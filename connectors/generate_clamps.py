# -*- coding: utf-8 -*-
"""Generate the crossing clamps the dome actually needs, from the model data.

This is a consumer, not a source of geometry. It reads the connector schedule
that ``stardome`` derives from the dome model and builds one clamp per part
the schedule asks for, at that part's real crossing angle. It computes no dome
geometry of its own -- see docs/architecture.md.

    python3 -m stardome connectors D6 --json      # write the schedule
    <FreeCAD> connectors/generate_clamps.py       # build the parts

Run inside FreeCAD:

    exec(open('/Users/danilaorehov/star-dome/connectors/generate_clamps.py').read())

Optionally set VARIANT beforehand to pick a dome:

    VARIANT = "D8"; exec(open('.../generate_clamps.py').read())

Outputs, per part, into exports/connectors/:

    <part id>_BottomClamp.step / .stl
    <part id>_TopClamp.step / .stl
    <part id>.FCStd

What this deliberately does NOT do: the schedule's ``unsupported`` entries.
Ten nodes of the baseline dome join four rods at one point, and the V1
architecture holds two. That is a design gap, not an export setting, and it is
reported rather than silently skipped.
"""

import json
import os

import FreeCAD as App
import Part

# Both are overridable from the calling namespace before exec(), which is how
# the MCP bridge and a worktree checkout point this at the right tree --
# exec'd source has no __file__ to fall back on.
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
    VARIANT = "D6"

CLAMP_SOURCE = os.path.join(REPO, "connectors", "crossing_clamp_v1.py")
OUT_DIR = os.path.join(REPO, "exports", "connectors")

# exports/model is the Python producer's output. exports/geometry belongs to
# the OpenSCAD reference export and is read only by the parity tests; see
# docs/architecture.md, "Where generated files go".
SCHEDULE_PATH = os.path.join(
    REPO, "exports", "model", "star_dome_%s_connectors.json" % VARIANT.lower()
)


def load_clamp_module():
    """Load the V1 generator's functions without letting it auto-build."""
    namespace = {"SUPPRESS_AUTORUN": True, "__file__": CLAMP_SOURCE}
    with open(CLAMP_SOURCE) as handle:
        exec(compile(handle.read(), CLAMP_SOURCE, "exec"), namespace)
    return namespace


FAN_SOURCE = os.path.join(REPO, "connectors", "fan_node_v2.py")
FAN = None


def load_fan_module():
    """Load the four-rod fan generator, likewise without auto-building."""
    global FAN
    if FAN is None:
        namespace = {"SUPPRESS_AUTORUN": True, "__file__": FAN_SOURCE}
        with open(FAN_SOURCE) as handle:
            exec(compile(handle.read(), FAN_SOURCE, "exec"), namespace)
        FAN = namespace
    return FAN


def build_fan(part):
    """Build the fan node at the fan angles the schedule derived from the model."""
    fan = load_fan_module()
    values = {alias: value for (alias, value, _u, _n) in fan["INPUTS"]}
    values["rodDiameter"] = float(part["rod_diameter"])
    geo, dims = fan["build"](values, fan_gaps=part["fan_gaps_deg"])
    return geo, dims, values


def fresh_document(part_id):
    """One FreeCAD document per part, so every part is openable and editable."""
    name = "StarDome_%s" % part_id.replace("-", "_").replace(".", "p")
    if name in App.listDocuments():
        App.closeDocument(name)
    return App.newDocument(name)


def export_pair(first, second, part_id, suffix_a, suffix_b):
    files = []
    facets = {}
    for solid, suffix in ((first, suffix_a), (second, suffix_b)):
        step_path, stl_path, count = export_solid(solid, part_id + suffix)
        files.extend((step_path, stl_path))
        facets[suffix.lstrip("_")] = count
    return files, facets


def load_schedule():
    if not os.path.exists(SCHEDULE_PATH):
        raise SystemExit(
            "no connector schedule at %s\n"
            "run:  python3 -m stardome connectors %s --json" % (SCHEDULE_PATH, VARIANT)
        )
    with open(SCHEDULE_PATH) as handle:
        return json.load(handle)


def build_part(clamp, part):
    """Build one clamp at the schedule's rod diameter and crossing angle."""
    values = {alias: value for (alias, value, _u, _n) in clamp["INPUTS"]}
    values["rodDiameter"] = float(part["rod_diameter"])
    values["crossingAngle"] = float(part["crossing_angle"])
    # The two-piece drop-in constraint drives this; see docs/crossing-clamp-v1.md.
    values["verticalSeparation"] = values["rodDiameter"]
    geo, dims = clamp["build"](values)
    return geo, dims, values


# Mesh deflection for the printable export. Shape.exportStl() tessellates at a
# default fine enough to produce ~24 MB for a 48 mm part, which is useless to a
# slicer; 0.02 mm linear is well under any FDM nozzle's resolution and lands
# around 1 MB.
LINEAR_DEFLECTION = 0.02
ANGULAR_DEFLECTION = 0.5


def export_solid(shape, stem):
    import MeshPart

    step_path = os.path.join(OUT_DIR, stem + ".step")
    stl_path = os.path.join(OUT_DIR, stem + ".stl")
    shape.exportStep(step_path)
    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=LINEAR_DEFLECTION,
        AngularDeflection=ANGULAR_DEFLECTION,
        Relative=False,
    )
    mesh.write(stl_path)
    return step_path, stl_path, mesh.CountFacets


def run():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    clamp = load_clamp_module()
    sched = load_schedule()
    report = {"variant": sched["meta"]["variant"], "built": [], "not_covered": []}

    for part in sched["parts"]:
        generator = part.get("generator")

        if generator == "fan_node_v2":
            fan = load_fan_module()
            geo, dims, values = build_fan(part)

            doc = fresh_document(part["id"])
            fan["populate"](doc, geo)
            fan["write_parameters"](doc, None, values, fan["derived_rows"](dims, values))
            doc.recompute()
            fcstd = os.path.join(OUT_DIR, part["id"] + ".FCStd")
            doc.saveAs(fcstd)

            # Verify BEFORE meshing. MeshPart.meshFromShape attaches
            # triangulation to the shape and leaves isValid() returning False
            # afterwards, so a check that runs after the export reports a
            # perfectly good solid as broken.
            checks = fan["verify"](geo, dims, values)

            files = []
            facets = {}
            for plate_name, solid in zip(geo["names"], geo["plates"]):
                step_path, stl_path, count = export_solid(
                    solid, "%s_%s" % (part["id"], plate_name)
                )
                files.extend((step_path, stl_path))
                facets[plate_name] = count

            report["built"].append(
                {
                    "id": part["id"],
                    "kind": part["kind"],
                    "generator": generator,
                    "rod_diameter": part["rod_diameter"],
                    "count_needed": part["count"],
                    "pieces_per_node": len(geo["plates"]),
                    "fan_gaps_deg": part["fan_gaps_deg"],
                    "fcstd": fcstd,
                    "files": [os.path.basename(f) for f in files],
                    "mesh_facets": facets,
                    "checks": checks,
                }
            )
            continue

        if generator != "crossing_clamp_v1":
            report["not_covered"].append(
                {
                    "id": part["id"],
                    "kind": part["kind"],
                    "count": part["count"],
                    "why": part.get("note")
                    or "no generator for this part kind (%r)" % part["kind"],
                }
            )
            continue

        geo, dims, values = build_part(clamp, part)

        doc_name = "StarDome_%s" % part["id"].replace("-", "_").replace(".", "p")
        if doc_name in App.listDocuments():
            App.closeDocument(doc_name)
        doc = App.newDocument(doc_name)
        clamp["populate"](doc, geo)
        clamp["write_parameters"](
            doc, None, values, clamp["derived_rows"](dims, values)
        )
        doc.recompute()

        fcstd = os.path.join(OUT_DIR, part["id"] + ".FCStd")
        doc.saveAs(fcstd)

        # Same ordering rule as the fan: verify the solid before meshing it.
        checks = clamp["verify"](geo, dims, values)

        files = []
        facets = {}
        for solid, suffix in ((geo["bottom"], "_BottomClamp"), (geo["cap"], "_TopClamp")):
            step_path, stl_path, count = export_solid(solid, part["id"] + suffix)
            files.extend((step_path, stl_path))
            facets[suffix.lstrip("_")] = count
        report["built"].append(
            {
                "id": part["id"],
                "crossing_angle": part["crossing_angle"],
                "rod_diameter": part["rod_diameter"],
                "count_needed": part["count"],
                "nodes": len(part["nodes"]),
                "fcstd": fcstd,
                "files": [os.path.basename(f) for f in files],
                "mesh_facets": facets,
                "checks": checks,
            }
        )

    for entry in sched["unsupported"]:
        report["not_covered"].append(
            {
                "kind": entry["kind"],
                "count": entry["count"],
                "pair_angles": entry["pair_angles"],
                "why": entry["reason"],
            }
        )

    return report


REPORT = run()
import pprint

pprint.pprint(REPORT, width=118)
