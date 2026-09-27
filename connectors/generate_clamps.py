# -*- coding: utf-8 -*-
"""Generate the crossing clamps the dome actually needs, from the model data.

This is a consumer, not a source of geometry. It reads the connector schedule
that ``stardome`` derives from the dome model and builds one clamp per part
the schedule asks for, at that part's real crossing angle. It computes no dome
geometry of its own -- see docs/architecture.md.

    python3 -m stardome connectors D6 --json      # write the schedule
    <FreeCAD> connectors/generate_clamps.py       # build the parts

Run inside FreeCAD:

    exec(open('<repo>/connectors/generate_clamps.py').read())

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
import sys
import zipfile
from xml.etree import ElementTree

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

# Which closure the clamps get: "bolt" is the V1 joint -- two bolts, two
# nuts, a loose cap -- and "hinge" hangs the cap on a pin and leaves one bolt
# in an open slot. Both are the same generator and the same parameters; see
# docs/quick-release.md. Set it before exec()ing this file, or in the
# environment, which is how it reaches `make clamps`:
#
#     STAR_DOME_CLOSURE=hinge make clamps V=M
#
try:
    STYLE
except NameError:
    STYLE = os.environ.get("STAR_DOME_CLOSURE", "bolt")

CLOSURES = {"bolt": 0, "hinge": 1}
if STYLE not in CLOSURES:
    raise ValueError("closure must be one of %s, not %r"
                     % (", ".join(sorted(CLOSURES)), STYLE))

if os.path.join(REPO, "connectors") not in sys.path:
    sys.path.insert(0, os.path.join(REPO, "connectors"))
import kit  # noqa: E402  -- needs the path set above

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
    namespace = {"SUPPRESS_AUTORUN": True, "__file__": CLAMP_SOURCE, "REPO": REPO}
    with open(CLAMP_SOURCE) as handle:
        exec(compile(handle.read(), CLAMP_SOURCE, "exec"), namespace)
    return namespace


FAN_SOURCE = os.path.join(REPO, "connectors", "fan_node_v2.py")
BASE_SOURCE = os.path.join(REPO, "connectors", "base_hub_v1.py")
TERM_SOURCE = os.path.join(REPO, "connectors", "term_clamp_v1.py")
SPLICE_SOURCE = os.path.join(REPO, "connectors", "rod_splice_v2.py")
COLLAR_SOURCE = os.path.join(REPO, "connectors", "skirt_collar_v1.py")
LOADED = {}


def load_module(source):
    """Load a generator's functions without letting it auto-build."""
    if source not in LOADED:
        namespace = {"SUPPRESS_AUTORUN": True, "__file__": source, "REPO": REPO}
        with open(source) as handle:
            exec(compile(handle.read(), source, "exec"), namespace)
        LOADED[source] = namespace
    return LOADED[source]


def load_fan_module():
    """Load the four-rod fan generator, likewise without auto-building."""
    return load_module(FAN_SOURCE)


def build_base(part):
    """Build the base hub at the fan the schedule derived from the model.

    Three arms at a plain foot, two where a doorway cut took a bow away. The
    generator takes the gaps, so the difference is one shorter list -- and the
    first arm's angle with it, because a hub that lost its lowest arm starts
    somewhere else and the part is drawn in the frame it stands in.

    That angle is the schedule's ``arm_azimuths_deg``, not its ``rises_deg``.
    They agree for a three-arm hub and do not for a two-arm one, where the
    outer arm sits at 116.5651 deg and rises 63.4349.
    """
    base = load_module(BASE_SOURCE)
    values = {alias: value for (alias, value, _u, _n) in base["INPUTS"]}
    values["rodDiameter"] = float(part["rod_diameter"])
    values["rodNominalDiameter"] = float(
        part.get("rod_nominal_diameter") or part["rod_diameter"]
    )
    values["firstArmRise"] = float(part["arm_azimuths_deg"][0])
    geo, dims = base["build"](values, fan_gaps=part["fan_gaps_deg"])
    return base, geo, dims, values


def build_fan(part):
    """Build the fan node at the fan angles the schedule derived from the model."""
    fan = load_fan_module()
    values = {alias: value for (alias, value, _u, _n) in fan["INPUTS"]}
    values["rodDiameter"] = float(part["rod_diameter"])
    values["rodNominalDiameter"] = float(
        part.get("rod_nominal_diameter") or part["rod_diameter"]
    )
    geo, dims = fan["build"](values, fan_gaps=part["fan_gaps_deg"])
    return geo, dims, values


def fresh_document(part_id):
    """One FreeCAD document per part, so every part is openable and editable."""
    name = "StarDome_%s" % part_id.replace("-", "_").replace(".", "p")
    if name in App.listDocuments():
        App.closeDocument(name)
    return App.newDocument(name)


def save_document(doc, path):
    """Save a document that opens with its manufactured pieces visible.

    FreeCAD's command-line process writes the solids but omits GuiDocument.xml.
    The GUI then opens the file with every shape hidden. A minimal view record
    is enough to preserve visibility without depending on FreeCADGui headless.
    Keep that record to visibility: a hand-written Transparency property made
    BASE2-10 fail to open in the GUI while its BREP solids were unchanged.
    Reference rods and bought steel stay available in the tree but hidden.
    """
    if getattr(App, "GuiUp", 0):
        for obj in doc.Objects:
            view = getattr(obj, "ViewObject", None)
            if view is None:
                continue
            if obj.Name.startswith("Ref_"):
                view.Visibility = False
        doc.saveAs(path)
        return
    doc.saveAs(path)
    providers = ElementTree.Element("ViewProviderData")
    for obj in doc.Objects:
        if obj.TypeId == "Spreadsheet::Sheet":
            continue
        provider = ElementTree.SubElement(providers, "ViewProvider", {
            "name": obj.Name, "expanded": "0",
        })
        properties = ElementTree.SubElement(provider, "Properties", {
            "Count": "1", "TransientCount": "0",
        })
        visibility = ElementTree.SubElement(properties, "Property", {
            "name": "Visibility", "type": "App::PropertyBool", "status": "1",
        })
        ElementTree.SubElement(visibility, "Bool", {
            "value": "false" if obj.Name.startswith("Ref_") else "true",
        })
    providers.set("Count", str(len(providers)))
    root = ElementTree.Element("Document", {"SchemaVersion": "1"})
    root.append(providers)
    xml = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
        if "GuiDocument.xml" not in archive.namelist():
            archive.writestr("GuiDocument.xml", xml)


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
    values["rodNominalDiameter"] = float(
        part.get("rod_nominal_diameter") or part["rod_diameter"]
    )
    values["crossingAngle"] = float(part["crossing_angle"])
    values["fastenerStyle"] = CLOSURES[STYLE]
    # The two-piece drop-in constraint drives this; see docs/crossing-clamp-v1.md.
    values["verticalSeparation"] = values["rodDiameter"]
    geo, dims = clamp["build"](values)
    return geo, dims, values


def export_solid(shape, stem):
    """kit.export_solid, bound to this run's output directory."""
    return kit.export_solid(shape, stem, OUT_DIR)


def clear_exports(part_id):
    """Delete what a previous run wrote for this part, before writing again.

    A part's pieces are named by the generator, and a generator can rename
    them: the splice went from a two-piece clamp -- BottomSleeve and TopSleeve
    -- to a one-piece ferrule. Nothing removed the old pair, and the scene
    builder, which takes every ``<part id>_*.stl`` it finds, went on placing a
    part that no longer exists, in a shape nobody had drawn for two versions.

    So the output for a part is rebuilt rather than added to. Only files that
    start with this part's id are touched; everything else in the directory is
    another part's business.
    """
    if not os.path.isdir(OUT_DIR):
        return []
    gone = []
    for name in sorted(os.listdir(OUT_DIR)):
        if not (name.startswith(part_id + "_") or name.startswith(part_id + ".")):
            continue
        if not name.endswith((".step", ".stl", ".FCStd", ".FCBak")):
            continue
        os.remove(os.path.join(OUT_DIR, name))
        gone.append(name)
    return gone


def run():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    clamp = load_clamp_module()
    sched = load_schedule()
    report = {"variant": sched["meta"]["variant"], "closure": STYLE,
              "built": [], "not_covered": []}

    for part in sched["parts"]:
        generator = part.get("generator")
        if generator:
            stale = clear_exports(part["id"])
            if stale:
                report.setdefault("replaced", {})[part["id"]] = stale

        if generator == "base_hub_v1":
            base, geo, dims, values = build_base(part)

            doc = fresh_document(part["id"])
            base["populate"](doc, geo)
            kit.write_parameters(
                doc, None, base["INPUTS"], values,
                base["derived_rows"](dims, values), base["TITLE"],
            )
            doc.recompute()
            fcstd = os.path.join(OUT_DIR, part["id"] + ".FCStd")
            save_document(doc, fcstd)

            # Same ordering rule the other two follow: verify the solid before
            # meshing it, or exportStl leaves isValid() false afterwards.
            checks = base["verify"](geo, dims, values)

            files = []
            facets = {}
            for plate_name, solid in zip(geo["names"], geo["plates"]):
                step_path, stl_path, count = export_solid(
                    solid, "%s_%s" % (part["id"], plate_name)
                )
                files.extend((step_path, stl_path))
                facets[plate_name] = count
            for rod_index, rod in enumerate(geo["rods"], start=1):
                step_path, stl_path, _count = export_solid(
                    rod, "%s_ref-Rod%d" % (part["id"], rod_index)
                )
                files.extend((step_path, stl_path))
            assembly = Part.makeCompound(list(geo["plates"]) + list(geo["rods"]))
            step_path, stl_path, count = export_solid(
                assembly, "%s_ref-Assembly" % part["id"]
            )
            files.extend((step_path, stl_path))
            facets["ref-Assembly"] = count

            report["built"].append(
                {
                    "id": part["id"],
                    "kind": part["kind"],
                    "generator": generator,
                    "rod_diameter": part["rod_diameter"],
                    "count_needed": part["count"],
                    "pieces_per_hub": len(geo["plates"]),
                    "fan_gaps_deg": part["fan_gaps_deg"],
                    "first_arm_rise_deg": values["firstArmRise"],
                    "fcstd": fcstd,
                    "files": [os.path.basename(f) for f in files],
                    "mesh_facets": facets,
                    "checks": checks,
                }
            )
            continue

        if generator == "skirt_collar_v1":
            collar = load_module(COLLAR_SOURCE)
            values = {alias: value for (alias, value, _u, _n) in collar["INPUTS"]}
            values["rodDiameter"] = float(part["rod_diameter"])
            values["rodNominalDiameter"] = float(
                part.get("rod_nominal_diameter") or part["rod_diameter"]
            )
            # Both angles come off the dome, not out of the generator: the
            # chord azimuth from the post count and the brace rise from the
            # skirt's own proportions.
            values["chordAzimuth"] = float(part["chord_azimuths_deg"][0])
            values["braceRise"] = float(part["brace_rise_deg"])
            geo, dims = collar["build"](values)

            doc = fresh_document(part["id"])
            collar["populate"](doc, geo)
            kit.write_parameters(
                doc, None, collar["INPUTS"], values,
                collar["derived_rows"](dims, values), collar["TITLE"],
            )
            doc.recompute()
            fcstd = os.path.join(OUT_DIR, part["id"] + ".FCStd")
            save_document(doc, fcstd)
            checks = collar["verify"](geo, dims, values)

            step_path, stl_path, facet_count = export_solid(
                geo["collar"], part["id"] + "_Collar"
            )
            report["built"].append(
                {
                    "id": part["id"],
                    "kind": part["kind"],
                    "generator": generator,
                    "rod_diameter": part["rod_diameter"],
                    "count_needed": part["count"],
                    "fcstd": fcstd,
                    "files": [os.path.basename(f) for f in (step_path, stl_path)],
                    "mesh_facets": {"Collar": facet_count},
                    "checks": checks,
                }
            )
            continue

        if generator == "rod_splice_v2":
            splice = load_module(SPLICE_SOURCE)
            values = {alias: value for (alias, value, _u, _n) in splice["INPUTS"]}
            values["rodDiameter"] = float(part["rod_diameter"])
            values["rodNominalDiameter"] = float(
                part.get("rod_nominal_diameter") or part["rod_diameter"]
            )
            # The ferrule is straight -- the section is straight when it goes
            # on -- but the bow is bent to the dome radius afterwards, and that
            # is what decides how much the middle has to be relieved by.
            values["bendRadius"] = float(part["bend_radius"])
            values["sleeveLength"] = float(part["sleeve_length"])
            geo, dims = splice["build"](values)

            doc = fresh_document(part["id"])
            splice["populate"](doc, geo)
            kit.write_parameters(
                doc, None, splice["INPUTS"], values,
                splice["derived_rows"](dims, values), splice["TITLE"],
            )
            doc.recompute()
            fcstd = os.path.join(OUT_DIR, part["id"] + ".FCStd")
            save_document(doc, fcstd)
            checks = splice["verify"](geo, dims, values)

            step_path, stl_path, facet_count = export_solid(
                geo["body"], part["id"] + "_Ferrule"
            )
            files = [step_path, stl_path]
            facets = {"Ferrule": facet_count}
            report["built"].append(
                {
                    "id": part["id"],
                    "kind": part["kind"],
                    "generator": generator,
                    "rod_diameter": part["rod_diameter"],
                    "bend_radius": part["bend_radius"],
                    "count_needed": part["count"],
                    "fcstd": fcstd,
                    "files": [os.path.basename(f) for f in files],
                    "mesh_facets": facets,
                    "checks": checks,
                }
            )
            continue

        if generator == "term_clamp_v1":
            term = load_module(TERM_SOURCE)
            values = {alias: value for (alias, value, _u, _n) in term["INPUTS"]}
            values["rodDiameter"] = float(part["rod_diameter"])
            values["rodNominalDiameter"] = float(
                part.get("rod_nominal_diameter") or part["rod_diameter"]
            )
            values["crossingAngle"] = float(part["crossing_angle"])
            values["verticalSeparation"] = values["rodDiameter"]
            geo, dims = term["build"](values)

            doc = fresh_document(part["id"])
            term["populate"](doc, geo)
            kit.write_parameters(
                doc, None, term["INPUTS"], values,
                term["derived_rows"](dims, values), term["TITLE"],
            )
            doc.recompute()
            fcstd = os.path.join(OUT_DIR, part["id"] + ".FCStd")
            save_document(doc, fcstd)
            checks = term["verify"](geo, dims, values)

            files, facets = export_pair(
                geo["bottom"], geo["cap"], part["id"], "_BottomClamp", "_TopClamp"
            )
            report["built"].append(
                {
                    "id": part["id"],
                    "kind": part["kind"],
                    "generator": generator,
                    "crossing_angle": part["crossing_angle"],
                    "rod_diameter": part["rod_diameter"],
                    "count_needed": part["count"],
                    "fcstd": fcstd,
                    "files": [os.path.basename(f) for f in files],
                    "mesh_facets": facets,
                    "checks": checks,
                }
            )
            continue

        if generator == "fan_node_v2":
            fan = load_fan_module()
            geo, dims, values = build_fan(part)

            doc = fresh_document(part["id"])
            fan["populate"](doc, geo)
            kit.write_parameters(
                doc, None, fan["INPUTS"], values,
                fan["derived_rows"](dims, values), fan["TITLE"],
            )
            doc.recompute()
            fcstd = os.path.join(OUT_DIR, part["id"] + ".FCStd")
            save_document(doc, fcstd)

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

            # The rods are reference geometry, not parts to print, but without
            # them neither the STEP set nor a slicer preview shows what the
            # node is actually holding. Named ref- so nobody prints one.
            for rod_index, rod in enumerate(geo["rods"], start=1):
                step_path, stl_path, count = export_solid(
                    rod, "%s_ref-Rod%d" % (part["id"], rod_index)
                )
                files.extend((step_path, stl_path))

            # One file with the whole node in place: five plates and four rods,
            # for looking at rather than printing.
            assembly = Part.makeCompound(list(geo["plates"]) + list(geo["rods"]))
            step_path, stl_path, count = export_solid(
                assembly, "%s_ref-Assembly" % part["id"]
            )
            files.extend((step_path, stl_path))
            facets["ref-Assembly"] = count

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
        kit.write_parameters(
            doc, None, clamp["INPUTS"], values,
            clamp["derived_rows"](dims, values), clamp["TITLE"],
        )
        doc.recompute()

        fcstd = os.path.join(OUT_DIR, part["id"] + ".FCStd")
        save_document(doc, fcstd)

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
