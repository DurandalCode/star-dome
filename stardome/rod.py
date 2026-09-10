"""Buying and cutting the rod, the same way the cover module buys fabric.

The two problems rhyme. Fabric comes on a roll of a given width and the cover
has to be cut from it; rod comes in a coil or a bar of a given length and the
bows have to be cut from that. In both cases the stock's dimension is a
purchasing decision that decides the waste, and in both cases the answer is
worth having before anyone orders anything.

## Fifteen bows, one length

Every bow is a semicircle of the dome's own radius, so the whole frame is
**one length cut fifteen times** -- `pi * R`, 9424.8 mm on M.

That is worth stating because the model will tell you otherwise if asked in
the wrong mode. In `layered` the fifteen bows are drawn on fifteen slightly
different shells and come out with fifteen different lengths spanning 2.3%;
that is a drawing convention, not a cutting instruction. This module reads
the nominal length, which is the same in both modes.

## Sections, before stock

A bow is nine metres long and nothing carries nine metres, so it is already
cut into transport sections before the question of stock arises --
`section_length` in the config, 2400 mm by default. The sections are divided
**evenly**: four of 2356.2 mm rather than three of 2400 and a stub of 225,
because equal pieces splice with one part instead of two and stack without
sorting.

## Then stock

Small-diameter GFRP usually comes in a coil, and a coil has no cutting waste
at all -- you unroll what you need. Larger diameters come in bars, and then
the bar length against the section length decides everything: a 2356 mm
section from a 6 m bar leaves 1287 mm over, 21% of it wasted, while the same
section from a 12 m bar leaves 219 mm, under 2%.

That is the same shape of result as the fabric roll: the stock dimension
barely changes what the structure needs and changes a great deal what you buy.

## What this does not do

No allowance for the splice ferrule's own length, no kerf, no breakage
allowance, and no check that a rod of this diameter will take the bend --
minimum bend radius is a live constraint (roadmap milestone 1) and belongs to
the supplier's data sheet, not here.
"""

from __future__ import annotations

import math

from . import geometry

# Nominal GFRP density, kg/m3, for the mass figure. Same assumption the wind
# screening makes; confirm against the supplier before it matters.
GFRP_DENSITY = 1900.0

# A coil rather than a bar: no cutting waste, because you unroll what you need.
COIL = None


def _mark_divisors() -> tuple:
    """The section counts that land joints on the rod marks.

    A bow spans 180 degrees. The G family is marked in fifths and U and L in
    thirds, so the first mark of each set gives the divisor directly --
    derived rather than written down, so it stays true if the marking moves.
    """
    out = set()
    for marks in (geometry.MARKS_THIRDS, geometry.MARKS_FIFTHS):
        out.add(round(180.0 / min(marks)))
    return tuple(sorted(out))


MARK_DIVISORS = _mark_divisors()


def misses_the_marks(count: int) -> bool:
    """Does dividing a bow into this many equal pieces miss every mark?

    The crossings sit on the marks, so a count divisible by 3 or by 5 puts
    joints dead on them. See docs/splice.md.
    """
    return all(count % d != 0 for d in MARK_DIVISORS)


def bows(data: dict) -> dict:
    """The frame as it is cut: how many bows, and how long each one is.

    The NOMINAL length, which is the same whichever weave mode the model was
    built in. A cut list taken from the layered drawing would ask for fifteen
    different pieces, and the dome does not want fifteen different pieces.
    """
    meta = data["meta"]
    length = meta["rod_length_nominal"]
    count = meta["rod_count"]
    return {
        "count": count,
        "length_mm": round(length, 1),
        "total_mm": round(count * length, 1),
        "total_m": round(count * length / 1000.0, 2),
        "diameter_mm": meta["rod_diameter"],
        "bend_radius_mm": meta["dome_radius"],
        "note": (
            "One length, fifteen times: every bow is a semicircle of the "
            "dome's own radius. Bend radius equals the dome radius, which is "
            "a rod-selection constraint, not a note."
        ),
    }


def sections(data: dict, limit_mm: float | None = None) -> dict:
    """Transport sections: how a nine-metre bow is carried.

    Divided evenly rather than cut to the limit with a stub left over: equal
    sections splice with one part instead of two, and stack without sorting.

    And the count skips anything divisible by 3 or 5, because those put the
    joints on the rod marks, where the crossings are. Whether the remaining
    counts leave enough ROOM beside a joint is a separate question that needs
    the ferrule and the connector -- see ``splice.equal_sections``.
    """
    meta = data["meta"]
    bow = bows(data)
    limit = limit_mm if limit_mm is not None else meta.get("section_length") or 0.0
    if limit <= 0:
        return {
            "per_bow": 1,
            "length_mm": bow["length_mm"],
            "total": bow["count"],
            "splices_per_bow": 0,
            "splices_total": 0,
            "note": "no transport limit given, so the bow travels whole",
        }

    per_bow = max(1, math.ceil(bow["length_mm"] / limit))
    while not misses_the_marks(per_bow):
        per_bow += 1
    length = bow["length_mm"] / per_bow
    return {
        "per_bow": per_bow,
        "limit_mm": round(limit, 1),
        "length_mm": round(length, 1),
        "total": per_bow * bow["count"],
        "splices_per_bow": per_bow - 1,
        "splices_total": (per_bow - 1) * bow["count"],
        "note": (
            f"{per_bow} equal sections of {length:.0f} mm. Counts divisible "
            f"by {' or '.join(str(d) for d in MARK_DIVISORS)} are skipped: "
            "they put the joints on the rod marks, where the crossings are."
        ),
    }


def cut_plan(data: dict, stock_mm: float | None = COIL,
             limit_mm: float | None = None) -> dict:
    """Cutting the sections out of coil or bar.

    ``stock_mm=None`` is a coil: you unroll what you need and there is no
    cutting waste. A bar has to be divided into whole sections, and whatever
    is left at the end of each bar is offcut.
    """
    bow = bows(data)
    sec = sections(data, limit_mm)
    used_m = bow["total_m"]

    if not stock_mm:
        return {
            "stock": "coil",
            "stock_mm": None,
            "sections_per_stock": None,
            "stock_count": None,
            "used_m": used_m,
            "bought_m": used_m,
            "waste_m": 0.0,
            "efficiency": 1.0,
            "note": "A coil has no cutting waste: unroll what the piece needs.",
        }

    per_stock = int(stock_mm // sec["length_mm"])
    if per_stock < 1:
        raise ValueError(
            f"a {stock_mm:.0f} mm bar is shorter than one "
            f"{sec['length_mm']:.0f} mm section"
        )
    count = math.ceil(sec["total"] / per_stock)
    bought = count * stock_mm / 1000.0
    offcut = stock_mm - per_stock * sec["length_mm"]

    return {
        "stock": "bar",
        "stock_mm": round(stock_mm, 1),
        "sections_per_stock": per_stock,
        "offcut_per_stock_mm": round(offcut, 1),
        "stock_count": count,
        "used_m": used_m,
        "bought_m": round(bought, 2),
        "waste_m": round(bought - used_m, 2),
        "efficiency": round(used_m / bought, 4) if bought else 0.0,
        "note": (
            f"{per_stock} section(s) per bar, {offcut:.0f} mm left over each "
            "time. The bar length is the lever here, not the dome."
        ),
    }


def mass(data: dict) -> dict:
    """What the rod weighs, on the nominal density."""
    meta = data["meta"]
    bow = bows(data)
    area = math.pi * (meta["rod_diameter"] / 2000.0) ** 2
    kg = area * bow["total_m"] * GFRP_DENSITY
    return {
        "kg": round(kg, 1),
        "kg_per_m": round(area * GFRP_DENSITY, 4),
        "note": "Nominal GFRP density; weigh a metre of the real stock.",
    }


def summary_row(data: dict, stock_mm: float | None = COIL,
                limit_mm: float | None = None,
                price_per_m: float | None = None) -> dict:
    """One size, one line -- the rod half of the shopping list."""
    meta = data["meta"]
    bow = bows(data)
    sec = sections(data, limit_mm)
    plan = cut_plan(data, stock_mm, limit_mm)
    row = {
        "variant": meta["variant"],
        "alias": meta.get("alias"),
        "diameter_mm": meta["dome_diameter"],
        "rod_mm": meta["rod_diameter"],
        "bows": bow["count"],
        "bow_length_mm": bow["length_mm"],
        "sections": sec["total"],
        "section_length_mm": sec["length_mm"],
        "splices": sec["splices_total"],
        "used_m": plan["used_m"],
        "bought_m": plan["bought_m"],
        "waste_m": plan["waste_m"],
        "stock_count": plan["stock_count"],
        "mass_kg": mass(data)["kg"],
    }
    if price_per_m is not None:
        row["cost"] = round(plan["bought_m"] * price_per_m, 2)
    return row


def format_summary(rows: list, stock_mm: float | None = COIL,
                   price_per_m: float | None = None) -> str:
    """Several sizes on one page, the same shape the cover summary takes."""
    priced = price_per_m is not None
    stock = f"{stock_mm:.0f} mm bar" if stock_mm else "coil"
    lines = [
        f"--- rod  ({stock}"
        + (f", {price_per_m:g} per metre)" if priced else ")"),
        "",
        f"  {'size':<10}{'rod':>6}{'bows':>6}{'each mm':>10}{'sections':>10}"
        f"{'splices':>9}{'used m':>9}{'bought m':>10}{'kg':>8}"
        + (f"{'cost':>10}" if priced else ""),
    ]
    for r in rows:
        name = f"{r['alias']} {r['variant']}" if r["alias"] else r["variant"]
        money = f"{r['cost']:>10.0f}" if priced else ""
        lines.append(
            f"  {name:<10}{r['rod_mm']:>5.0f}{'':1}{r['bows']:>6}"
            f"{r['bow_length_mm']:>10.0f}{r['sections']:>10}{r['splices']:>9}"
            f"{r['used_m']:>9.1f}{r['bought_m']:>10.1f}{r['mass_kg']:>8.1f}{money}"
        )
    lines += [
        "",
        "  Every bow is one length: a semicircle of the dome's own radius,",
        "  cut fifteen times. Sections divide it evenly, so they splice with",
        "  one part rather than two.",
    ]
    if stock_mm:
        lines.append(
            "  From a bar, whatever is left at its end is offcut; from a coil "
            "there is no cutting waste."
        )
    else:
        lines.append("  A coil has no cutting waste -- unroll what the piece needs.")
    lines.append(
        "  Bend radius equals the dome radius. Confirm the stock will take it."
    )
    return "\n".join(lines)


# Bar lengths GFRP is actually sold in, plus the two that divide a bow. Given
# as candidates to compare, not as a recommendation -- what a supplier stocks
# is the constraint, and it is not this module's to guess.
STOCK_CANDIDATES = (3000.0, 4000.0, 6000.0, 8000.0, 11800.0, 12000.0)


def stock_sweep(data: dict, candidates=STOCK_CANDIDATES,
                limit_mm: float | None = None,
                price_per_m: float | None = None) -> list:
    """Waste against bar length, with the splice count kept in view.

    Minimising offcut alone gives a silly answer -- it will happily cut a bow
    into eleven pieces to fill a bar exactly, and that is ten splices to make
    and ten places to leak load. So this reports the trade rather than
    choosing: the section count stays the sensible one the transport limit
    sets, and only the bar changes.
    """
    sec = sections(data, limit_mm)
    used = bows(data)["total_m"]
    rows = []
    for bar in candidates:
        if bar < sec["length_mm"]:
            continue
        plan = cut_plan(data, bar, limit_mm)
        row = {
            "stock_mm": bar,
            "sections_per_stock": plan["sections_per_stock"],
            "offcut_mm": plan["offcut_per_stock_mm"],
            "waste_pct": round(100.0 * plan["waste_m"] / plan["bought_m"], 1),
            "bought_m": plan["bought_m"],
            "used_m": used,
            "splices_per_bow": sec["splices_per_bow"],
        }
        if price_per_m is not None:
            row["cost"] = round(plan["bought_m"] * price_per_m, 2)
        rows.append(row)
    return rows


def format_stock_sweep(data: dict, candidates=STOCK_CANDIDATES,
                       limit_mm: float | None = None,
                       price_per_m: float | None = None) -> str:
    """The bar-length trade, as a page for a person."""
    meta = data["meta"]
    bow = bows(data)
    sec = sections(data, limit_mm)
    rows = stock_sweep(data, candidates, limit_mm, price_per_m)
    priced = price_per_m is not None

    lines = [
        f"--- {meta.get('alias') or meta['variant']} rod stock  "
        f"(bow {bow['length_mm']:.0f} mm in {sec['per_bow']} sections of "
        f"{sec['length_mm']:.0f} mm)",
        "",
        f"  {'bar mm':>8}{'per bar':>9}{'offcut mm':>11}{'waste':>8}"
        f"{'bought m':>10}" + (f"{'cost':>10}" if priced else ""),
    ]
    for r in rows:
        money = f"{r['cost']:>10.0f}" if priced else ""
        lines.append(
            f"  {r['stock_mm']:>8.0f}{r['sections_per_stock']:>9}"
            f"{r['offcut_mm']:>11.0f}{r['waste_pct']:>7.1f}%"
            f"{r['bought_m']:>10.1f}{money}"
        )
    lines += ["", f"  needs {bow['total_m']:.1f} m of rod, "
                  f"{sec['splices_total']} splices whichever bar you buy"]
    if rows:
        best = min(rows, key=lambda r: r["waste_pct"])
        lines.append(
            f"  best of these: {best['stock_mm']:.0f} mm at "
            f"{best['waste_pct']:.1f}% waste"
        )
    lines += [
        "",
        "  A coil has no cutting waste at all; these are bars.",
        "  Cutting the bow into more sections would fill a bar better and "
        "cost a splice each time --",
        "  the section count here is the one the transport limit sets, not "
        "the one that fills a bar.",
    ]
    return "\n".join(lines)
