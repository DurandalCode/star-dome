"""The longest unsupported span, and the ceiling it puts on the family.

Every other module here measures the dome as a shape. This one asks the first
question that is not about shape: a bow is held at some points and free
between them, so **how far apart are those points, and what happens to that
distance when the dome gets bigger?**

The answer is the whole of milestone 7. The topology scales to any diameter --
every angle in it is the same at D3 and at D12, which is what makes the family
a family. What does not scale is the rod: span grows with the dome, and the
rod that holds a span grows with the *square* of it.

## A rod is held where something holds it, and that is a decision, not a fact

A bow touches other rods at every crossing, but touching is not holding. Ten
of the forty crossing points are lashed junctions with a printed connector;
the other thirty are rod-on-rod contacts that may never get a part at all --
milestone 5 has not decided. So there are two answers, and this module gives
both because the gap between them *is* the decision:

**`lashed`** -- a bow is held at its two feet and its tie marks, and nowhere
else. This is the position decision 0010 and `tolerance.held_spans` already
take, and it is the conservative one.

**`contact`** -- every crossing holds, because every crossing got a clamp.

The two differ by a factor of **5/3 in span**, which is a factor of **2.8 in
the rod diameter** it takes to hold it. That is the price of the thirty
clamps, and it is the first number anyone has put on them.

## Which family is weak depends on which answer you take, and they swap

Family G is marked in fifths and families U and L in thirds, so:

| held at | G span | U, L span | dome's worst |
|---|---|---|---|
| lashed nodes only | 36 deg | **60 deg** | 60 deg, on U and L |
| every contact | **36 deg** | 22.24 deg | 36 deg, on G |

Clamping the free crossings does nothing for family G -- all four of its
crossings are already lashed nodes -- and cuts U and L from 60 degrees to
22.24. The weak family swaps. Either way the worst span is a fixed fraction
of the dome radius, because the dome is similar to itself at every size.

## What the span does to the rod

Two domes in this family are geometrically similar: same angles, same
topology, every length proportional to R. Take one bow between two supports,
span `a`, diameter `d`, and let it sag under a load `w`:

    sag  ~  w a^4 / (E I),   I ~ d^4

The constant in front -- end fixity, arch action, the part of the load a bent
rod carries in compression rather than bending -- is not known here. It does
not need to be: **it is the same constant for both domes**, because they are
the same shape. So the *ratio* is meaningful even though neither sag is.

Two load types scale differently, and both are reported because which one
governs is milestone 8's to say:

**Self-weight.** `w ~ d^2`, so sag ratio is `(a/a0)^4 (d0/d)^2`.

**Pressure on the cover** -- wind, snow. The lattice carries it over a strip
as wide as the spacing between neighbouring rods, which scales with R, so
`w ~ p R` and the sag ratio is `(R/R0) (a/a0)^4 (d0/d)^4`.

## The two constraints on the rod pull opposite ways, and that sets a ceiling

To keep the reference dome's sag, the rod must be **at least**

    d  =  d0 (a/a0)^2                     self-weight
    d  =  d0 [(R/R0) (a/a0)^4]^(1/4)      pressure

To be bent to the dome radius at all, its outer fibre must survive a strain of
`d / 2R`, so for an allowable strain `e` the rod may be **at most**

    d  =  2 R e

One grows as R^2 (or R^1.25), the other only as R. They cross, and where they
cross is the largest dome of this family that can be built from rod that both
holds its span and survives being bent to shape:

    R_max  =  ( 2 e R0^p / (d0 k^q) ) ^ (1 / (p - 1))

`k` is the span factor -- 1 for the bare topology, less for anything that puts
a support in the middle of a span. Because `q` is 2 in the self-weight case,
**halving the worst span multiplies the ceiling by four.** That is why milestone
7's candidates are all measured against the span and not against each other.

```bash
python3 -m stardome span M
python3 -m stardome span --all --holds contact
```

Nothing here is a structural check. There is no modulus, no strength and no
load in it -- only ratios between two domes of the same shape, and they are
ratios to a reference whose own adequacy is assumed rather than shown. What an
allowable strain actually is for the stock, and which load governs, are
milestones 3 and 8. See docs/span.md.
"""

from __future__ import annotations

import math

# What counts as holding a bow. ``lashed`` is the position decision 0010 and
# ``tolerance.held_spans`` already take; ``contact`` is what the dome becomes
# if the thirty free crossings each get a clamp.
HOLDS = ("lashed", "contact")

# The dome everything else is measured against: the reference prototype, the
# only variant anybody is proposing to build first. It is a variant name
# rather than a set of numbers so that editing configs/variants.toml moves the
# baseline with it.
REFERENCE_VARIANT = "D6"

# Each load case is the pair of exponents its scaling gives:
#
#     sag / sag0  =  (R/R0)^r * (a/a0)^4 * (d0/d)^m
#
# ``r`` is how the load per unit length grows with the dome (0 when the rod
# carries only itself, 1 when it carries pressure over a strip that widens
# with the dome), and ``m`` is how the second moment of area fights it.
LOAD_CASES = {
    "self_weight": (0, 2),
    "pressure": (1, 4),
}

# Outer-fibre strains to print the ceiling against. Not a property of any
# stock -- the column to read once somebody has measured one. The reference
# dome itself works at 0.167%, so an allowance under that condemns the dome
# this project is already proposing to build.
STRAIN_SAMPLES = (0.002, 0.004, 0.006, 0.008)

TOL = 1e-9


# --- where a bow is held ----------------------------------------------------


def live_intervals(rod: dict) -> list:
    """The arc of a bow that still exists, as ``[lo, hi]`` in degrees.

    A doorway cut takes pieces out of one or two bows. What is left is not a
    shorter bow but a bow with a hole in it, and the piece on each side has a
    free end held by a ``TERM`` clamp instead of a foot.
    """
    out = [[0.0, 180.0]]
    for lo, hi in rod.get("cut_spans_deg") or []:
        nxt = []
        for a, b in out:
            if hi <= a + TOL or lo >= b - TOL:
                nxt.append([a, b])
                continue
            if lo > a + TOL:
                nxt.append([a, lo])
            if hi < b - TOL:
                nxt.append([hi, b])
        out = nxt
    return out


def supports(data: dict, holds: str = "lashed") -> dict:
    """``rod name -> [(t in degrees, what holds it)]``, along each bow.

    The ends of a live interval are always held: a bow stands on a foot at
    ``t = 0`` and ``t = 180``, and where a doorway cut gave it a free end
    instead, a ``TERM`` clamp holds that end against the rod it used to cross.
    """
    if holds not in HOLDS:
        raise ValueError(f"unknown holds {holds!r} -- use one of {HOLDS}")

    at: dict = {rod["name"]: [] for rod in data["rods"]}
    for crossing in data["crossings"]:
        if holds == "lashed" and not crossing["tied"]:
            continue
        at[crossing["rod_a"]].append(crossing["t_a_deg"])
        at[crossing["rod_b"]].append(crossing["t_b_deg"])

    out = {}
    for rod in data["rods"]:
        held = []
        for lo, hi in live_intervals(rod):
            held.append((lo, "foot" if lo <= TOL else "term"))
            for t in sorted(set(at[rod["name"]])):
                if lo + TOL < t < hi - TOL:
                    held.append((t, "node" if holds == "lashed" else "crossing"))
            held.append((hi, "foot" if hi >= 180.0 - TOL else "term"))
        out[rod["name"]] = held
    return out


def spans(data: dict, holds: str = "lashed") -> dict:
    """Every unsupported length in the dome, and the worst of them.

    Each span is reported in degrees of arc and in millimetres, because the
    first is the same at every size and the second is what a person measures.
    """
    if holds not in HOLDS:
        raise ValueError(f"unknown holds {holds!r} -- use one of {HOLDS}")
    radius = data["meta"]["dome_radius"]
    held = supports(data, holds)

    per_rod: dict = {}
    per_family: dict = {}
    for rod in data["rods"]:
        name, family = rod["name"], rod["family"]
        items = []
        points = held[name]
        live = live_intervals(rod)
        for (t_lo, kind_lo), (t_hi, kind_hi) in zip(points, points[1:]):
            if not any(lo - TOL <= t_lo and t_hi <= hi + TOL for lo, hi in live):
                continue
            gap = t_hi - t_lo
            if gap <= TOL:
                continue
            items.append(
                {
                    "t_lo_deg": round(t_lo, 6),
                    "t_hi_deg": round(t_hi, 6),
                    "arc_deg": round(gap, 6),
                    "length_mm": round(radius * math.radians(gap), 3),
                    "between": f"{kind_lo}-{kind_hi}",
                }
            )
        per_rod[name] = items
        widest = max((s["arc_deg"] for s in items), default=0.0)
        if widest > per_family.get(family, {}).get("arc_deg", -1.0):
            per_family[family] = {
                "rod": name,
                "arc_deg": round(widest, 6),
                "length_mm": round(radius * math.radians(widest), 3),
            }

    family = max(per_family, key=lambda f: per_family[f]["arc_deg"])
    worst = per_family[family]
    where = next(
        s for s in per_rod[worst["rod"]] if s["arc_deg"] == worst["arc_deg"]
    )
    return {
        "variant": data["meta"]["variant"],
        "holds": holds,
        "radius_mm": radius,
        "per_rod": per_rod,
        "per_family": per_family,
        "worst": {
            "family": family,
            "rod": worst["rod"],
            "arc_deg": worst["arc_deg"],
            "length_mm": worst["length_mm"],
            "t_lo_deg": where["t_lo_deg"],
            "t_hi_deg": where["t_hi_deg"],
            "between": where["between"],
        },
        # The same at every diameter, because the dome is similar to itself.
        # This is the number that carries scaling; the millimetres do not.
        "fraction_of_radius": round(math.radians(worst["arc_deg"]), 9),
        "count_at_worst": sum(
            1
            for items in per_rod.values()
            for s in items
            if abs(s["arc_deg"] - worst["arc_deg"]) < 1e-6
        ),
        "span_count": sum(len(items) for items in per_rod.values()),
    }


def clamp_value(data: dict) -> dict:
    """What clamping the thirty free crossings is worth, as a span ratio.

    The answer milestone 5 has been putting off: not an opinion about whether
    a rod-on-rod contact holds, but the factor between the dome that assumes
    it does and the dome that assumes it does not.
    """
    loose = spans(data, "lashed")["worst"]
    tight = spans(data, "contact")["worst"]
    ratio = loose["arc_deg"] / tight["arc_deg"]
    return {
        "lashed": loose,
        "contact": tight,
        "span_ratio": round(ratio, 6),
        # d ~ a^2 under self-weight parity, which is the harsher of the two.
        "rod_diameter_ratio": round(ratio ** 2, 6),
        "note": (
            "The span the dome has to hold if a rod-on-rod contact does not "
            "hold, over the span if every crossing is clamped. The rod ratio "
            "is what that costs in diameter at equal sag under self-weight."
        ),
    }


# --- what the span does to the rod ------------------------------------------


def bend_strain(diameter_mm: float, radius_mm: float) -> float:
    """Outer-fibre strain of a straight rod bent to a radius: ``d / 2R``.

    Pure geometry -- the fibre furthest from the neutral axis travels on a
    circle of radius ``R + d/2`` where the axis travels on ``R``. No modulus
    and no strength: whether a given stock survives it is milestone 3.
    """
    return diameter_mm / (2.0 * radius_mm)


def reference(data: dict, holds: str = "lashed") -> dict:
    """The three numbers every other dome is compared against."""
    s = spans(data, holds)
    return {
        "variant": data["meta"]["variant"],
        "holds": holds,
        "radius_mm": data["meta"]["dome_radius"],
        "rod_diameter_mm": data["meta"]["rod_diameter"],
        "span_mm": s["worst"]["length_mm"],
        "bend_strain": round(
            bend_strain(data["meta"]["rod_diameter"], data["meta"]["dome_radius"]), 9
        ),
    }


def sag_ratio(case: str, radius_mm: float, span_mm: float,
              diameter_mm: float, ref: dict) -> float:
    """How much more this bow sags between supports than the reference's does.

    Same material, same load type, same shape -- so the unknown constant in
    front cancels and this is a real comparison. It is not a sag.
    """
    r, m = _case(case)
    return (
        (radius_mm / ref["radius_mm"]) ** r
        * (span_mm / ref["span_mm"]) ** 4
        * (ref["rod_diameter_mm"] / diameter_mm) ** m
    )


def parity_rod(case: str, radius_mm: float, span_mm: float, ref: dict) -> float:
    """Diameter that sags exactly as much as the reference does."""
    r, m = _case(case)
    return ref["rod_diameter_mm"] * (
        (radius_mm / ref["radius_mm"]) ** r * (span_mm / ref["span_mm"]) ** 4
    ) ** (1.0 / m)


def similar_rod(radius_mm: float, ref: dict) -> float:
    """Diameter plain similarity asks for: ``d ~ R``, which holds the strain.

    Not the same thing as the parity rod, and the gap between them is the
    finding -- similarity keeps the bending the same and lets the sag go.
    """
    return ref["rod_diameter_mm"] * radius_mm / ref["radius_mm"]


def ceiling(case: str, strain_allowed: float, ref: dict,
            span_factor: float = 1.0) -> dict:
    """Largest dome whose equal-sag rod still bends to shape.

    The parity rod grows as ``R^p`` and the rod an allowable strain permits
    grows as ``R``; ``p > 1`` in both load cases, so they cross exactly once.

        d0 k^q (R/R0)^p  =  2 R e   ->   R = ( 2 e R0^p / (d0 k^q) ) ^ 1/(p-1)

    ``span_factor`` is the worst span as a fraction of the bare topology's, so
    reinforcement that halves the span enters as ``k = 0.5`` and buys back
    ``k^-q`` -- four times the radius in the self-weight case.
    """
    r, m = _case(case)
    p = (r + 4.0) / m
    q = 4.0 / m
    radius = (
        2.0 * strain_allowed * ref["radius_mm"] ** p
        / (ref["rod_diameter_mm"] * span_factor ** q)
    ) ** (1.0 / (p - 1.0))
    return {
        "case": case,
        "strain_allowed": strain_allowed,
        "span_factor": span_factor,
        "radius_mm": round(radius, 1),
        "diameter_mm": round(2.0 * radius, 1),
        "rod_diameter_mm": round(2.0 * radius * strain_allowed, 2),
        "exponents": {"p": round(p, 6), "q": round(q, 6)},
    }


def _case(case: str) -> tuple:
    if case not in LOAD_CASES:
        raise ValueError(
            f"unknown load case {case!r} -- use one of {tuple(LOAD_CASES)}"
        )
    return LOAD_CASES[case]


# --- the whole answer for one dome ------------------------------------------


def analyse(data: dict, ref: dict, holds: str = "lashed") -> dict:
    """The span, what it asks of the rod, and where the family runs out."""
    s = spans(data, holds)
    radius = data["meta"]["dome_radius"]
    diameter = data["meta"]["rod_diameter"]
    span_mm = s["worst"]["length_mm"]

    cases = {}
    for case in LOAD_CASES:
        needs = parity_rod(case, radius, span_mm, ref)
        cases[case] = {
            "sag_ratio": round(sag_ratio(case, radius, span_mm, diameter, ref), 4),
            "parity_rod_mm": round(needs, 2),
            "parity_bend_strain": round(bend_strain(needs, radius), 9),
            "ceiling": [
                ceiling(case, e, ref, s["fraction_of_radius"] / ref_fraction(ref))
                for e in STRAIN_SAMPLES
            ],
        }

    return {
        "variant": s["variant"],
        "holds": holds,
        "reference": ref,
        "spans": s,
        "rod": {
            "configured_mm": diameter,
            "similar_mm": round(similar_rod(radius, ref), 2),
            "bend_strain": round(bend_strain(diameter, radius), 9),
            "under_rodded_by": round(similar_rod(radius, ref) / diameter, 4),
        },
        "cases": cases,
        "note": (
            "Ratios between two domes of the same shape, and nothing else. No "
            "modulus, no strength, no load, and the reference's own adequacy "
            "is assumed rather than shown -- milestones 3 and 8."
        ),
    }


def ref_fraction(ref: dict) -> float:
    """The reference's own span as a fraction of its radius."""
    return ref["span_mm"] / ref["radius_mm"]


# Past this the ceiling stops being a statement about a temporary event
# structure: nobody is putting up a 100 m dome of bent rod in an afternoon,
# and the similarity the whole comparison rests on was never asked to reach
# that far.
DISPLAY_LIMIT_MM = 100_000.0


def _metres(diameter_mm: float) -> str:
    if diameter_mm > DISPLAY_LIMIT_MM:
        return f"{'>100':>9}"
    return f"{diameter_mm / 1000.0:9.1f}"


def format_analysis(data: dict, ref: dict, holds: str = "lashed") -> str:
    a = analyse(data, ref, holds)
    s = a["spans"]
    w = s["worst"]
    rod = a["rod"]
    out = [
        f"--- {a['variant']} unsupported span  "
        f"(held at: {'feet and tie marks' if holds == 'lashed' else 'every crossing'})",
        f"  worst span      {w['length_mm']:.0f} mm on family {w['family']} "
        f"({w['rod']}, t {w['t_lo_deg']:.2f}-{w['t_hi_deg']:.2f} deg), "
        f"{s['count_at_worst']} of {s['span_count']} spans are this long",
        "  per family      "
        + "   ".join(
            f"{f} {s['per_family'][f]['length_mm']:.0f}"
            for f in sorted(s["per_family"])
        ),
        f"  as a fraction   {s['fraction_of_radius']:.4f} of the dome radius "
        "-- the same at every size",
        "",
        f"  against {ref['variant']}, same material, same load, same shape:",
        f"    rod          {rod['configured_mm']:.1f} mm configured, "
        f"similarity asks {rod['similar_mm']:.1f} mm "
        f"({rod['under_rodded_by']:.2f}x)",
        f"    bent to      {rod['bend_strain'] * 100:.3f}% outer-fibre strain "
        f"({ref['bend_strain'] * 100:.3f}% on {ref['variant']})",
    ]
    for case, c in a["cases"].items():
        out.append(
            f"    {case:12} sags {c['sag_ratio']:.1f}x as much; equal sag wants "
            f"{c['parity_rod_mm']:.1f} mm rod, "
            f"bent to {c['parity_bend_strain'] * 100:.3f}% strain"
        )
    out += [
        "",
        "  largest dome of this family whose equal-sag rod still bends to shape:",
        "    strain allowed  "
        + "".join(f"{e * 100:>8.1f}%" for e in STRAIN_SAMPLES),
    ]
    for case, c in a["cases"].items():
        out.append(
            f"    {case:14}"
            + "".join(_metres(x["diameter_mm"]) for x in c["ceiling"])
        )
    out.append(
        f"    the pressure row does not bind: it grows as the fourth power of "
        f"the allowance, so anything this family could be built at clears it."
    )
    out += [
        "",
        "  " + a["note"],
    ]
    return "\n".join(out)
