"""Serialisation of the model to JSON and CSV.

JSON is the interchange contract: FreeCAD, Blender and the OpenSCAD viewer
all read it, and nothing downstream recomputes geometry. The CSV files are
flat views of the same data for humans and spreadsheets -- generated from the
model, never hand-edited.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

CSV_TABLES = {
    "rods": "rods",
    "base_nodes": "base_nodes",
    "nodes": "nodes",
    "crossings": "crossings",
    "crossing_types": "crossing_types",
}


def _flatten(value):
    """CSV cannot hold a list, so join it the way the reference exporter does."""
    if isinstance(value, list):
        return ";".join(str(v) for v in value)
    return value


def write_json(data: dict, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return path


def write_csv(rows: list, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    fields = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _flatten(v) for k, v in row.items()})
    return path


def write_all(data: dict, out_dir: Path | str, stem: str | None = None) -> list:
    """Write ``<stem>.json`` plus one CSV per table. Returns the paths."""
    out_dir = Path(out_dir)
    stem = stem or f"star_dome_{data['meta']['variant'].lower()}"
    written = [write_json(data, out_dir / f"{stem}.json")]
    for table, key in CSV_TABLES.items():
        written.append(write_csv(data[key], out_dir / f"{stem}_{table}.csv"))
    return written


def summary(data: dict) -> str:
    """The short golden snapshot: scalars only, no per-crossing detail.

    Small enough to live in Git and be diffed in a pull request, so a change
    in the maths shows up as a readable number change rather than a 84 kB
    blob.
    """
    meta = data["meta"]
    keys = [
        "variant", "units", "dome_diameter", "dome_radius", "rod_diameter",
        "rod_count", "base_node_count", "crossing_point_count",
        "crossing_pair_count", "crossing_type_count", "rod_length_nominal",
        "rod_length_class_count", "total_rod_length", "base_ring_length",
        "dome_height_nominal", "base_edge_arc", "base_edge_chord",
    ]
    out = {k: meta[k] for k in keys}
    out["crossing_types"] = [
        {
            "name": t["name"],
            "count": t["count"],
            "families": f"{t['family_a']}{t['family_b']}",
            "z": t["z"],
            "angle_deg": t["angle_deg"],
            "tied": t["tied"],
        }
        for t in data["crossing_types"]
    ]
    out["node_heights"] = sorted({n["z"] for n in data["nodes"]}, reverse=True)
    return json.dumps(out, indent=1, ensure_ascii=False) + "\n"
