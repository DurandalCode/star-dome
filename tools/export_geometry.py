#!/usr/bin/env python3
"""Export the Star Dome engineering geometry report from OpenSCAD.

WHY A SCRIPT AT ALL

OpenSCAD cannot write files. It can only print to the console. So the geometry
model emits tagged ``DATA|`` lines and this script turns them into JSON and CSV.

The important consequence: this script contains **no geometry**. It does not
know what a bow is, how many crossings there should be, or what any angle is.
Every number comes from ``dome/star_dome.scad``, which stays the single source
of truth as AGENTS.md requires. If the dome changes, this script needs no edit.

USAGE

    tools/export_geometry.py                 # D6, the reference variant
    tools/export_geometry.py --variant D8
    tools/export_geometry.py --all           # every variant in configs/
    tools/export_geometry.py --weave flat    # nominal centrelines (default)

OUTPUT (under exports/geometry/, git-ignored as generated output)

    star_dome_<variant>.json                 everything, nested
    star_dome_<variant>_crossings.csv        the 90 rod-to-rod crossings
    star_dome_<variant>_crossing_types.csv   the symmetry classes
    star_dome_<variant>_nodes.csv            distinct crossing points
    star_dome_<variant>_base_nodes.csv       ground points
    star_dome_<variant>_rods.csv             rod schedule
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODEL = REPO / "dome" / "star_dome.scad"

# Columns whose value is a ";"-separated list rather than a scalar.
LIST_COLUMNS = {
    "rods",
    "tie_marks_deg",
    "tie_marks_mm",
    "example_rods",
    # Always a list, even when the dome has only one rod length class -- which
    # it always should. Without this it would decay to a bare float in the
    # single-class case and change type on a dome that had more.
    "rod_length_classes",
}

# DATA tag -> key in the JSON document. A "<tag>head" line supplies the column
# names for the matching "<tag>" rows, so adding a field in the .scad file needs
# no change here.
SECTIONS = {
    "rod": "rods",
    "basenode": "base_nodes",
    "node": "nodes",
    "crossing": "crossings",
    "type": "crossing_types",
}

ECHO_RE = re.compile(r'^ECHO:\s*"(.*)"\s*$')


def find_openscad(explicit: str | None) -> str:
    """Locate the OpenSCAD binary.

    On macOS it usually lives inside an .app bundle and is not on PATH, so fall
    back to the standard bundle locations before giving up.
    """
    if explicit:
        return explicit
    found = shutil.which("openscad") or shutil.which("OpenSCAD")
    if found:
        return found
    for pattern in ("/Applications/OpenSCAD*.app/Contents/MacOS/OpenSCAD",):
        matches = sorted(Path("/").glob(pattern.lstrip("/")))
        if matches:
            return str(matches[-1])
    sys.exit(
        "openscad not found. Put it on PATH or pass --openscad /path/to/OpenSCAD"
    )


def coerce(value: str, column: str):
    """Turn a text field into a number when it plainly is one."""
    if column in LIST_COLUMNS:
        return [coerce(v, "") for v in value.split(";")] if value else []
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def run_openscad(binary: str, variant: str, weave: str, decimals: int) -> list[str]:
    """Run the model in data-emitting mode and return its DATA| lines."""
    # OpenSCAD in command-line mode insists on producing an output file even
    # when all we want is its console output, so it renders a throwaway PNG
    # into a temp dir. renderModel=false keeps that render trivial.
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            binary,
            "-o", str(Path(tmp) / "discard.png"),
            "--imgsize=64,64",
            "-D", f'variant="{variant}"',
            "-D", f'weaveMode="{weave}"',
            "-D", f"dataDecimals={decimals}",
            "-D", "renderModel=false",
            "-D", "reportSummary=false",
            "-D", "emitGeometryData=true",
            str(MODEL),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        sys.exit(f"openscad failed ({proc.returncode}):\n{out}")

    lines = []
    for raw in out.splitlines():
        m = ECHO_RE.match(raw.strip())
        if m and m.group(1).startswith("DATA|"):
            lines.append(m.group(1))
    if not lines:
        sys.exit("no DATA| lines in the OpenSCAD output; is emitGeometryData wired up?")
    return lines


def parse(lines: list[str]) -> dict:
    doc: dict = {"meta": {}}
    headers: dict[str, list[str]] = {}
    for key in SECTIONS.values():
        doc[key] = []

    for line in lines:
        parts = line.split("|")
        tag = parts[1]
        if tag == "meta":
            doc["meta"][parts[2]] = coerce("|".join(parts[3:]), parts[2])
        elif tag.endswith("head"):
            headers[tag[: -len("head")]] = parts[2:]
        elif tag in SECTIONS:
            cols = headers.get(tag)
            if cols is None:
                sys.exit(f"row '{tag}' arrived before its header line")
            values = parts[2:]
            if len(values) != len(cols):
                sys.exit(
                    f"row '{tag}' has {len(values)} fields, header declares {len(cols)}"
                )
            doc[SECTIONS[tag]].append(
                {c: coerce(v, c) for c, v in zip(cols, values)}
            )
    return doc


def verify(doc: dict) -> list[str]:
    """Cross-check the row counts against the model's own summary numbers.

    This catches a truncated or partially parsed run. It deliberately checks
    nothing about the geometry itself -- that belongs in the .scad file.
    """
    meta = doc["meta"]
    problems = []
    for key, section in (
        ("rod_count", "rods"),
        ("base_node_count", "base_nodes"),
        ("crossing_point_count", "nodes"),
        ("crossing_pair_count", "crossings"),
        ("crossing_type_count", "crossing_types"),
    ):
        expected = meta.get(key)
        actual = len(doc[section])
        if expected is not None and expected != actual:
            problems.append(f"{section}: {actual} rows, meta says {expected}")

    total = sum(t["count"] for t in doc["crossing_types"])
    if total != len(doc["crossings"]):
        problems.append(
            f"crossing type counts sum to {total}, but there are {len(doc['crossings'])} crossings"
        )
    return problems


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {k: (";".join(str(x) for x in v) if isinstance(v, list) else v)
                 for k, v in row.items()}
            )


def export(binary: str, variant: str, weave: str, decimals: int, outdir: Path) -> dict:
    lines = run_openscad(binary, variant, weave, decimals)
    doc = parse(lines)
    doc["schema"] = "star_dome_geometry/1"
    doc["source"] = "dome/star_dome.scad"

    problems = verify(doc)
    if problems:
        sys.exit("export self-check failed:\n  " + "\n  ".join(problems))

    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"star_dome_{variant.lower()}"
    (outdir / f"{stem}.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for section, suffix in (
        ("crossings", "crossings"),
        ("crossing_types", "crossing_types"),
        ("nodes", "nodes"),
        ("base_nodes", "base_nodes"),
        ("rods", "rods"),
    ):
        write_csv(outdir / f"{stem}_{suffix}.csv", doc[section])
    return doc


def variants_from_config() -> list[str]:
    """Read the variant names straight out of configs/variants.scad."""
    text = (REPO / "configs" / "variants.scad").read_text(encoding="utf-8")
    block = text.split("SD_VARIANTS", 1)[1]
    return re.findall(r'\["(\w+)",', block)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", default="D6")
    ap.add_argument("--all", action="store_true", help="export every named variant")
    ap.add_argument("--weave", default="flat", choices=["flat", "layered"],
                    help="flat (default) gives true centreline coordinates")
    ap.add_argument("--decimals", type=int, default=6)
    ap.add_argument("--outdir", default=str(REPO / "exports" / "geometry"))
    ap.add_argument("--openscad", default=None)
    args = ap.parse_args()

    binary = find_openscad(args.openscad)
    outdir = Path(args.outdir)
    targets = variants_from_config() if args.all else [args.variant]

    for variant in targets:
        doc = export(binary, variant, args.weave, args.decimals, outdir)
        m = doc["meta"]
        print(
            f"{variant}: {m['rod_count']} rods, "
            f"{m['crossing_point_count']} crossing points, "
            f"{m['crossing_pair_count']} rod pairs, "
            f"{m['crossing_type_count']} symmetry classes, "
            f"{m['rod_length_class_count']} rod length class"
            f"{'' if m['rod_length_class_count'] == 1 else 'es'} "
            f"-> {outdir}/star_dome_{variant.lower()}.json"
        )


if __name__ == "__main__":
    main()
