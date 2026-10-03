#!/usr/bin/env python3
"""Turn a dome's connectors into Bambu Studio projects, plates already laid out.

WHAT THIS IS FOR

`make clamps` writes every piece in the frame it is DESIGNED in, next to its
STEP, its FreeCAD document and the reference rods -- the right set for CAD and
for the Blender scene, and a poor one for a slicer: forty-odd files to pick
through, pieces lying on the wrong face, and the counts in a JSON file.

This reads the manifest `make clamps` writes beside them and produces, per
variant, what a printer actually wants:

    exports/print/<variant>/<variant>_dome.3mf   every printed piece one dome
                                                 needs, at its count, arranged
                                                 onto as many plates as it takes
    exports/print/<variant>/<part>.3mf           one of that part: the fit check
                                                 before printing the rest, or a
                                                 spare
    exports/print/<variant>/stl/<part>_<piece>.stl
                                                 each piece on its print face,
                                                 for any other slicer

Open a .3mf and press print, plate by plate. The pieces are already the right
way up -- each generator's FLIPPED_PIECES says which ones print upside down,
the same orientation its overhang check judged -- so in the slicer: place, do
not rotate. See docs/printing.md.

HOW

Turning a piece over is done here, on the mesh: half a turn about X, then
dropped so its lowest point is z = 0. Nothing is scaled or rebuilt. Arranging
is Bambu Studio's own: its command line loads the pieces, clones each to its
count and packs them onto the printer's plates, so the project opens exactly
as the GUI would have arranged it. A piece wider than the plate is reported
and left out rather than shrunk.

The printer, process and filament are Bambu's system presets, by name, with
three settings changed to what docs/printing.md asks for: four walls, 35%
infill, no supports. Everything else is the preset's.

Run:

    make prints V=S                              # after `make clamps V=S`
    tools/print_plates.py d4
    tools/print_plates.py d6 --filament "Bambu PLA Basic @BBL P2S"
    tools/print_plates.py d4 --printer "Bambu Lab X1 Carbon 0.4 nozzle" \\
        --process "0.20mm Standard @BBL X1C" \\
        --filament "Bambu PETG Basic @BBL X1C"
    tools/print_plates.py d4 --stl-only          # no Bambu Studio needed

Plain Python, no FreeCAD: everything it needs is already on disk.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS_DIR = os.path.join(REPO, "exports", "connectors")
OUT_ROOT = os.path.join(REPO, "exports", "print")

BAMBU = os.environ.get(
    "BAMBU_STUDIO", "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
)
PROFILES = os.environ.get(
    "BAMBU_PROFILES",
    os.path.expanduser(
        "~/Library/Application Support/BambuStudio/system/BBL"
    ),
)

PRINTER = "Bambu Lab P2S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL P2S"
# PETG, because that is what goes in a field; the fit check can be PLA.
FILAMENT = "Bambu PETG Basic @BBL P2S 0.4 nozzle"

# What docs/printing.md asks for. Every load in these parts goes through the
# walls round a hole or a channel, and no piece is drawn to need support.
PROCESS_OVERRIDES = {
    "wall_loops": "4",
    "sparse_infill_density": "35%",
    "enable_support": "0",
}


# --------------------------------------------------------------------------
# meshes
# --------------------------------------------------------------------------
def read_stl(path):
    """Binary STL -> (header, list of 12-float facets). FreeCAD writes binary."""
    with open(path, "rb") as handle:
        data = handle.read()
    count = struct.unpack_from("<I", data, 80)[0] if len(data) >= 84 else -1
    if len(data) != 84 + 50 * count:
        raise ValueError("%s is not a binary STL" % path)
    facets = [
        struct.unpack_from("<12f", data, 84 + 50 * i) for i in range(count)
    ]
    return facets


def write_stl(path, facets, name):
    header = name.encode("ascii", "replace")[:80].ljust(80, b" ")
    with open(path, "wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(facets)))
        for facet in facets:
            handle.write(struct.pack("<12f", *facet))
            handle.write(b"\0\0")


def onto_the_bed(facets, flipped):
    """The piece as it is printed: turned half a turn about X if it prints the
    other way up, then moved so its footprint starts at the origin and its
    lowest point is z = 0.

    About X rather than Y, the way the overhang check turns it. A rotation, not
    a mirror: (y, z) -> (-y, -z) keeps the facet winding, so no normal needs
    reversing.
    """
    if flipped:
        facets = [
            tuple(v for i in range(4) for v in (f[3 * i], -f[3 * i + 1], -f[3 * i + 2]))
            for f in facets
        ]
    lows = [min(f[k] for f in facets for k in range(3 + axis, 12, 3)) for axis in range(3)]
    moved = []
    for f in facets:
        out = list(f[:3])
        for i in range(1, 4):
            out.extend(f[3 * i + axis] - lows[axis] for axis in range(3))
        moved.append(tuple(out))
    return moved


def footprint(facets):
    return tuple(
        max(f[k] for f in facets for k in range(3 + axis, 12, 3))
        - min(f[k] for f in facets for k in range(3 + axis, 12, 3))
        for axis in range(3)
    )


# --------------------------------------------------------------------------
# Bambu Studio
# --------------------------------------------------------------------------
def preset(kind, name):
    """A system preset with its `inherits` chain folded in.

    The command line does not walk the chain itself: handed the P2S preset as
    it stands, it fell back to a 200 x 200 default plate, because the real
    256 x 256 lives two files up.
    """
    path = os.path.join(PROFILES, kind, name + ".json")
    if not os.path.exists(path):
        raise SystemExit(
            "no Bambu Studio %s preset called %r\n  looked in %s"
            % (kind, name, os.path.dirname(path))
        )
    with open(path) as handle:
        values = json.load(handle)
    parent = values.pop("inherits", None)
    if parent:
        folded = preset(kind, parent)
        folded.update(values)
        values = folded
    return values


def plate_area(machine):
    """Width and depth of the printable area, from the preset's outline."""
    points = [tuple(float(v) for v in p.split("x")) for p in machine["printable_area"]]
    xs, ys = zip(*points)
    return max(xs) - min(xs), max(ys) - min(ys)


def plates_in(project):
    with zipfile.ZipFile(project) as archive:
        config = archive.read("Metadata/model_settings.config").decode()
    return config.count("<plate>")


def arrange(stls, counts, settings, project, work):
    """Load the pieces, clone each to its count, let Bambu pack the plates."""
    command = [
        BAMBU,
        "--orient", "0",
        "--arrange", "1",
        "--clone-objects", ",".join(str(c) for c in counts),
        "--load-settings", "%s;%s" % (settings["machine"], settings["process"]),
        "--load-filaments", settings["filament"],
        "--export-3mf", project,
    ] + stls
    # It writes result.json into the working directory, and says nothing
    # useful on stdout; run it somewhere disposable and read that instead.
    run = subprocess.run(command, cwd=work, capture_output=True, text=True)
    result_path = os.path.join(work, "result.json")
    result = {}
    if os.path.exists(result_path):
        with open(result_path) as handle:
            result = json.load(handle)
        os.remove(result_path)
    if run.returncode != 0 or result.get("return_code", 0) != 0 or not os.path.exists(project):
        tail = "\n".join(run.stdout.splitlines()[-15:] + run.stderr.splitlines()[-15:])
        raise SystemExit(
            "Bambu Studio failed on %s: %s\n%s"
            % (os.path.basename(project), result.get("error_string", run.returncode), tail)
        )
    return plates_in(project)


# --------------------------------------------------------------------------
def run(variant, printer, process, filament, stl_only):
    variant = variant.lower()
    manifest_path = os.path.join(PARTS_DIR, "star_dome_%s_prints.json" % variant)
    if not os.path.exists(manifest_path):
        raise SystemExit(
            "no print manifest at %s\nrun:  make clamps V=%s"
            % (os.path.relpath(manifest_path, REPO), variant.upper())
        )
    with open(manifest_path) as handle:
        manifest = json.load(handle)

    out_dir = os.path.join(OUT_ROOT, variant)
    # Generated, and only ever by this script: rebuilt rather than added to, or
    # a piece a generator has renamed lives on in the folder.
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    stl_dir = os.path.join(out_dir, "stl")
    os.makedirs(stl_dir)

    settings = None
    bed = None
    work = tempfile.mkdtemp(prefix="print_plates_")
    if not stl_only:
        if not os.path.exists(BAMBU):
            raise SystemExit(
                "Bambu Studio not found at %s\n"
                "set BAMBU_STUDIO, or pass --stl-only for the turned STLs alone"
                % BAMBU
            )
        machine = preset("machine", printer)
        bed = plate_area(machine)
        settings = {}
        for kind, values in (
            ("machine", machine),
            ("process", dict(preset("process", process), **PROCESS_OVERRIDES)),
            ("filament", preset("filament", filament)),
        ):
            settings[kind] = os.path.join(work, kind + ".json")
            with open(settings[kind], "w") as handle:
                json.dump(values, handle, indent=1)

    report = {"variant": variant, "printer": printer, "plate_mm": bed,
              "parts": [], "too_big": []}
    dome_stls, dome_counts = [], []
    for part in manifest["parts"]:
        stls = []
        for piece in part["pieces"]:
            facets = onto_the_bed(
                read_stl(os.path.join(PARTS_DIR, piece["stl"])), piece["flipped"]
            )
            size = footprint(facets)
            if bed and (size[0] > bed[0] or size[1] > bed[1]):
                report["too_big"].append(
                    {"piece": piece["stl"], "footprint_mm": [round(s, 1) for s in size[:2]]}
                )
                continue
            path = os.path.join(stl_dir, piece["stl"])
            write_stl(path, facets, piece["stl"])
            stls.append(path)

        entry = {"id": part["id"], "count": part["count"],
                 "pieces": len(part["pieces"])}
        if settings and stls:
            project = os.path.join(out_dir, part["id"] + ".3mf")
            entry["plates_for_one"] = arrange(stls, [1] * len(stls), settings, project, work)
        report["parts"].append(entry)
        dome_stls.extend(stls)
        dome_counts.extend([part["count"]] * len(stls))

    if settings and dome_stls:
        project = os.path.join(out_dir, "%s_dome.3mf" % variant)
        report["dome_plates"] = arrange(dome_stls, dome_counts, settings, project, work)
        report["dome_prints"] = sum(dome_counts)
    shutil.rmtree(work, ignore_errors=True)
    report["out_dir"] = os.path.relpath(out_dir, REPO)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("variant", help="d4, d6, ... as the schedule files it")
    parser.add_argument("--printer", default=PRINTER, help="Bambu machine preset")
    parser.add_argument("--process", default=PROCESS, help="Bambu process preset")
    parser.add_argument("--filament", default=FILAMENT, help="Bambu filament preset")
    parser.add_argument("--stl-only", action="store_true",
                        help="write the turned STLs and skip Bambu Studio")
    args = parser.parse_args(argv)
    report = run(args.variant, args.printer, args.process, args.filament, args.stl_only)
    json.dump(report, sys.stdout, indent=2)
    print()
    if report["too_big"]:
        print("left out, wider than the plate: %s"
              % ", ".join(p["piece"] for p in report["too_big"]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
