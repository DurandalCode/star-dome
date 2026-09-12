"""Everything one dome is made of, counted in one place.

Every other module here answers one question well and counts what it needs to
answer it: the schedule counts connectors, the cover counts fabric, the
attachment counts webbing, the report counts rod. Nobody had ever added them
up, so the dome was thoroughly measured as a **shape** and had never been
measured as a **quantity** -- no parts list, no plastic, no idea which part
the print farm actually spends its time on.

## Where each number comes from

Nothing here is computed twice. The parts come from ``connectors.schedule``,
the rod from the model's own ``meta``, the fabric from ``cover``, the webbing
and the rope from ``attachment``, the skirt's members from the ``skirt`` block.
This module joins them; it derives no geometry of its own.

## The plastic is measured, not estimated

A connector's volume is a property of the drawn solid, and the drawn solid
lives in FreeCAD. Rather than keep a copy of that number in the source -- where
it would drift the first time a generator changed -- the volume is read off the
exported meshes in ``exports/connectors``, by summing the signed tetrahedra of
each closed triangle mesh. That is exact for a closed mesh and needs nothing
installed.

So the plastic column is present when the parts have been built and honestly
absent when they have not:

```bash
make clamps V=M          # build the parts first, if you want the plastic
python3 -m stardome bom M
python3 -m stardome bom --all --parts exports/connectors
```

**The volumes are of the solid part.** Real filament at a normal infill is
roughly half of it, and which half is a slicer's answer, not this project's.
Nothing here multiplies by a density.

## What it deliberately does not count

**Fasteners.** How many bolts a part takes is a property of the generator that
draws it, and the schedule does not carry it yet. The bolt *size* is derived --
half the rod, snapped to a standard -- and is reported; the count is not, and
saying "about two per part" would be worse than saying nothing.

See docs/bom.md.
"""

from __future__ import annotations

import os
import struct

# Where `make clamps` puts the exported meshes.
DEFAULT_PARTS_DIR = os.path.join("exports", "connectors")

# Pieces the generators export as reference geometry -- the rods a part is
# drawn around, and the assembled stack. They are drawings, not parts, and
# counting them would roughly double the plastic.
REFERENCE_MARKER = "_ref-"


def stl_volume_mm3(path: str) -> float:
    """Volume of a closed binary STL, by summed signed tetrahedra.

    Each triangle and the origin make a tetrahedron whose signed volume is
    ``v0 . (v1 x v2) / 6``; over a closed surface the outside cancels and what
    is left is the enclosed solid. Exact, and it needs no mesh library.
    """
    with open(path, "rb") as handle:
        handle.read(80)
        (count,) = struct.unpack("<I", handle.read(4))
        total = 0.0
        for _ in range(count):
            values = struct.unpack("<12fH", handle.read(50))
            ax, ay, az, bx, by, bz, cx, cy, cz = values[3:12]
            total += (
                ax * (by * cz - bz * cy)
                - ay * (bx * cz - bz * cx)
                + az * (bx * cy - by * cx)
            )
    return abs(total) / 6.0


def measured(parts_dir: str = DEFAULT_PARTS_DIR) -> dict:
    """``part id -> {piece: cm3}`` for whatever has actually been built.

    An empty dict is a perfectly good answer: it means nobody has run the
    generators yet, and the caller reports the parts without their plastic
    rather than inventing it.
    """
    out: dict = {}
    if not os.path.isdir(parts_dir):
        return out
    for name in sorted(os.listdir(parts_dir)):
        if not name.endswith(".stl") or REFERENCE_MARKER in name:
            continue
        stem = name[:-4]
        if "_" not in stem:
            continue
        part_id, piece = stem.rsplit("_", 1)
        try:
            volume = stl_volume_mm3(os.path.join(parts_dir, name))
        except (OSError, struct.error):  # pragma: no cover - a truncated file
            continue
        out.setdefault(part_id, {})[piece] = round(volume / 1000.0, 3)
    return out


def printed(schedule: dict, volumes: dict) -> dict:
    """The connector half of the list: what gets made, and what it costs."""
    rows = []
    for part in schedule["parts"]:
        pieces = volumes.get(part["id"]) or {}
        each = round(sum(pieces.values()), 3)
        rows.append(
            {
                "id": part["id"],
                "count": part["count"],
                "state": part.get("state", "generated"),
                "generator": part.get("generator"),
                "pieces_per_part": len(pieces),
                "prints": len(pieces) * part["count"],
                "cm3_each": each,
                "cm3_total": round(each * part["count"], 3),
                "measured": bool(pieces),
            }
        )
    total = round(sum(r["cm3_total"] for r in rows), 3)
    for row in rows:
        row["share"] = round(row["cm3_total"] / total, 4) if total else 0.0
    rows.sort(key=lambda r: (-r["cm3_total"], -r["count"]))
    return {
        "rows": rows,
        "parts": sum(r["count"] for r in rows),
        "part_types": len(rows),
        "prints": sum(r["prints"] for r in rows),
        "cm3": total,
        "all_measured": all(
            r["measured"] for r in rows if r["state"] == "generated"
        ),
        "note": (
            "Volumes are of the solid part. Real filament at a normal infill "
            "is roughly half of it, and which half is a slicer's answer."
        ),
    }


def materials(data: dict, schedule: dict | None = None) -> dict:
    """Everything that is cut to length or to area rather than printed.

    The section count comes from the splice schedule rather than from dividing
    a bow by the transport length. They disagree, and the schedule is right: a
    doorway cut shortens two bows, so they need one splice fewer each, and a
    bow is cut into one more section than it has joints.
    """
    meta = data["meta"]
    cover = data.get("cover") or {}
    attachment = data.get("attachment") or {}
    skirt = data.get("skirt")

    section = meta.get("section_length") or 0.0
    bow = meta["rod_length_nominal"]
    joints = 0
    if schedule:
        joints = sum(
            part["count"]
            for part in schedule["parts"]
            if part["kind"] == "rod_splice"
        )
    out = {
        "rod_m": round(meta["total_rod_length"] / 1000.0, 2),
        "bows": meta["rod_count"],
        "bow_length_mm": round(bow, 1),
        "section_length_mm": round(section, 1),
        "splices": joints,
        "sections": joints + meta["rod_count"] if joints else 0,
        "anchors": len(data["base_nodes"]),
        # Half the rod, snapped to a standard bolt -- connectors/kit.py.
        "fastener": _fastener_for(meta["rod_diameter"]),
    }
    if cover.get("areas"):
        out["fabric_m2"] = cover["areas"]["total_m2"]
        out["fabric_gross_m2"] = cover["areas"]["gross_m2"]
    if cover.get("gores"):
        out["gores"] = cover["gores"].get("count")
        out["seam_m"] = round((cover["gores"].get("seam_length_mm") or 0) / 1000.0, 1)
    if attachment:
        out["webbing_m"] = attachment.get("webbing_total_m")
        out["hem_rope_m"] = round(
            (attachment["hem"]["rope_length_mm"]) / 1000.0, 2
        )
    if skirt:
        out["skirt"] = {
            "posts_m": round(skirt["post_total_length"] / 1000.0, 2),
            "rings_m": round(
                (skirt["top_ring_length"] + skirt["bottom_ring_length"]) / 1000.0, 2
            ),
            "braces_m": round(skirt["brace_total_length"] / 1000.0, 2),
            "post_height_mm": skirt["height"],
        }
    return out


# The bolt table lives in connectors/kit.py, which only imports inside
# FreeCAD. These are its sizes, and the rule is decision 0013's: half the rod,
# snapped to the nearest standard.
BOLT_SIZES = (3, 4, 5, 6, 8)


def _fastener_for(rod_diameter: float) -> str:
    want = rod_diameter / 2.0
    size = min(BOLT_SIZES, key=lambda m: (abs(m - want), m))
    return f"M{size}"


def analyse(data: dict, schedule: dict, parts_dir: str = DEFAULT_PARTS_DIR) -> dict:
    volumes = measured(parts_dir)
    return {
        "variant": data["meta"]["variant"],
        "alias": data["meta"].get("alias", ""),
        "diameter_mm": data["meta"]["dome_diameter"],
        "rod_diameter_mm": data["meta"]["rod_diameter"],
        "parts_dir": parts_dir,
        "printed": printed(schedule, volumes),
        "materials": materials(data, schedule),
    }


def format_analysis(data: dict, schedule: dict,
                    parts_dir: str = DEFAULT_PARTS_DIR) -> str:
    a = analyse(data, schedule, parts_dir)
    p, m = a["printed"], a["materials"]
    name = f"{a['variant']}" + (f" ({a['alias']})" if a["alias"] else "")
    out = [
        f"--- {name} bill of materials  "
        f"({a['diameter_mm'] / 1000.0:.0f} m, rod {a['rod_diameter_mm']:g} mm)",
        "",
        f"  {'printed':22}{'parts':>6}{'prints':>8}{'cm3 ea':>10}"
        f"{'cm3 all':>11}{'share':>8}",
    ]
    for row in p["rows"]:
        if row["measured"]:
            body = (
                f"{row['pieces_per_part'] * row['count']:>8}"
                f"{row['cm3_each']:>10.1f}{row['cm3_total']:>11.1f}"
                f"{row['share'] * 100:>7.1f}%"
            )
        else:
            label = "hardware" if row["state"] == "hardware" else (
                "nothing yet" if row["state"] == "undesigned" else "not built"
            )
            body = f"{label:>36}"
        out.append(f"  {row['id']:22}{row['count']:>6}{body}")
    out += [
        f"  {'':22}{'-' * 6:>6}{'-' * 8:>8}{'':10}{'-' * 11:>11}",
        f"  {'total':22}{p['parts']:>6}{p['prints']:>8}{'':10}{p['cm3']:>11.1f}",
    ]
    if not p["all_measured"]:
        out.append(
            "  (some parts are not built; run `make clamps` for their plastic)"
        )
    out += [
        "",
        f"  rod         {m['rod_m']:>8.1f} m   {m['bows']} bows x "
        f"{m['bow_length_mm']:.0f} mm"
        + (
            f", in {m['sections']} sections of <= {m['section_length_mm']:.0f} mm"
            if m["sections"]
            else ""
        ),
    ]
    if "fabric_m2" in m:
        out.append(
            f"  fabric      {m['fabric_m2']:>8.1f} m2"
            + (
                f"  {m['gores']} gores, {m['seam_m']:.1f} m of seam"
                if m.get("gores")
                else ""
            )
        )
    if "webbing_m" in m:
        out.append(
            f"  webbing     {m['webbing_m']:>8.1f} m   "
            f"incl. {m['hem_rope_m']:.1f} m of hem rope"
        )
    if m.get("skirt"):
        s = m["skirt"]
        out.append(
            f"  skirt       {s['posts_m']:>8.1f} m   of post at "
            f"{s['post_height_mm']:.0f} mm, {s['rings_m']:.1f} m of ring, "
            f"{s['braces_m']:.1f} m of brace strap"
        )
    out += [
        f"  anchors     {m['anchors']:>8}     driven steel angles",
        f"  fastener    {m['fastener']:>8}     half the rod, snapped; "
        "how many per part is not derived yet",
        "",
        "  " + p["note"],
    ]
    return "\n".join(out)
