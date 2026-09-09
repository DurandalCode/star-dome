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


def scad_variants(variants: dict) -> str:
    """Render ``configs/variants.scad`` from the TOML presets.

    OpenSCAD cannot read TOML, and the reference implementation in ``dome/``
    needs the same variant numbers the Python core uses. Generating this file
    keeps the *parameters* single-sourced while leaving the *geometry* in the
    two implementations independent -- which is the whole point of the
    cross-check. See docs/architecture.md.

    The public names here are load-bearing: ``dome/star_dome.scad`` calls
    ``sd_variant_diameter`` and friends.
    """
    rows = [
        (f'"{v.name}",', f"{v.diameter:g}", f"{v.rod_diameter:g}", v.note)
        for v in variants.values()
    ]
    name_w = max(len(r[0]) for r in rows)
    dia_w = max(len(r[1]) for r in rows)
    rod_w = max(len(r[2]) for r in rows)
    entries = ",\n".join(
        f"    [{name:<{name_w}} {dia:>{dia_w}}, {rod:>{rod_w}}, \"{note}\"]"
        for name, dia, rod, note in rows
    )
    bend = "\n".join(
        f"//   {v.name:<4}->  {v.bend_radius:g} mm" for v in variants.values()
    )
    return f"""\
// ---------------------------------------------------------------------------
// configs/variants.scad -- named Star Dome variants.
//
// GENERATED FILE. Do not edit.
//
//     python3 -m stardome scad-config
//
// The source of truth is configs/variants.toml. This file exists because
// OpenSCAD cannot read TOML and dome/star_dome.scad needs the same numbers the
// Python core uses. Parameters are single-sourced; the geometry in dome/ stays
// an independent implementation, which is what makes the cross-check in
// tests/test_geometry.py worth anything. See docs/architecture.md.
//
// All dimensions in millimetres (see AGENTS.md).
//
// ---------------------------------------------------------------------------
// ROD DIAMETERS ARE PROVISIONAL
//
// The values below are engineering *assumptions*, not results. Nothing here
// has been checked against fiberglass rod properties, buckling, bending
// stress, minimum bend radius, wind load, cover load or anchoring, and the
// geometric model deliberately says nothing about whether a given rod can
// survive being bent to the required radius.
//
// Every bow is bent to a radius equal to the dome radius, so the required
// bend radius scales directly with the variant:
//
{bend}
//
// Confirm each against the real rod stock before treating a variant as
// buildable. See docs/roadmap.md milestones 4, 6 and 8.
// ---------------------------------------------------------------------------

// Record layout.
SDV_NAME = 0; SDV_DIAMETER = 1; SDV_ROD_DIAMETER = 2; SDV_NOTE = 3;

SD_VARIANTS = [
{entries}
];

// Look a variant up by name. Fails loudly rather than silently falling back,
// so a typo in a -D override cannot quietly render the wrong dome.
function sd_variant(name) =
    let (hits = [for (v = SD_VARIANTS) if (v[SDV_NAME] == name) v])
    assert(len(hits) == 1, str("unknown variant '", name,
                               "' -- known: ", [for (v = SD_VARIANTS) v[SDV_NAME]]))
    hits[0];

function sd_variant_diameter(name)     = sd_variant(name)[SDV_DIAMETER];
function sd_variant_rod_diameter(name) = sd_variant(name)[SDV_ROD_DIAMETER];
function sd_variant_note(name)         = sd_variant(name)[SDV_NOTE];
"""


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
        "skirt_height", "overall_height",
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
