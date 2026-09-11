"""How accurately the dome has to be measured, and where the accuracy matters.

The assembly order says which bow goes up when. This says how carefully each
one has to be cut and marked first, and how carefully the ground has to be
pegged out -- which decides whether the field method is a tape measure or a
template, and that in turn is most of what "fast assembly" means.

## The only things anyone measures

Forty marks and ten pegs. That is the whole measured content of a Star Dome:

- **10 base points** on the ground, at the corners of a regular decagon.
- **15 bows** cut to length, each a semicircle of `pi * R`.
- **40 tie marks** along them -- fifths on family G, thirds on U and L. Every
  mark lands on a lashed node and every lashed node is where four marks meet,
  so 10 nodes x 4 rods = 40, exactly the marks the model carries.

The other 30 crossings are **not measured at all**. Nobody marks them, nothing
locates them; they fall where the weave puts them. So an error budget for this
structure is an error budget on 10 pegs, 15 lengths and 40 marks, and nothing
else.

## The two exact sensitivities

A bow is an arc of length `L` whose chord is the base diameter `c`. Both are
measured quantities, and together they fix the arc: `c/L = 2 sin(t/2) / t`
gives the subtended angle, and the rise -- how far the arc stands off its own
chord -- follows.

Differentiating at the semicircle gives two constants that do not depend on
the dome's size at all:

    d(rise) / d(rod length)     =  +1/2
    d(rise) / d(base diameter)  =  -(pi/4 - 1/2)  =  -0.285398

Both are **less than one**, which is the headline of this whole module: the
shape attenuates measurement error rather than amplifying it. Cut a 6 m dome's
bow 10 mm long and it stands 5 mm higher. Peg the ring 10 mm wide and it
stands 2.9 mm lower. Nothing here is a knife edge.

The derivation, for the record. Write `t = pi + f`. Holding the chord fixed,
`L sin(t/2)/t = c/2` expands to `L(1 - f/pi) = L0` to first order, so
`f = pi * dL / L0`; substituting into `rise = (L/t)(1 + sin(f/2))` gives
`d(rise) = dL/2`. Holding the length fixed instead gives `f = -pi^2 dc / (2L)`
and `d(rise) = -dc (pi/4 - 1/2)`.

## Common mode is free; only the differences cost

If every bow is 10 mm long and the ring is pegged 10 mm wide everywhere, the
result is a slightly different dome that fits itself perfectly. Marks are
placed as fractions of each rod's own length, so they scale with it. Nothing
binds, nothing is pre-stressed, and the only consequence is a dome a few
millimetres off nominal.

What costs is **differential** error: this bow long and that one short, this
peg out and its neighbour in. Then the four marks that should meet at a node
do not, and the rods have to be flexed until they do. That flexing is
pre-stress in a structure whose members are already bent to a known radius,
which is why the number to watch is not the dome's height but the **node
spread** -- and, through it, the extra curvature that spread forces.

## Node spread, and what it is allowed to be

At a lashed node the four rods' tangents are coplanar (`weave.node_fan`), so
the four marks that should coincide there land in one plane. The spread is the
largest distance between any two of them: the gap the rods must be sprung
across before the connector will close.

Saying whether a given spread is acceptable needs a criterion, and **the
criterion is where the whole answer lives** -- the two available here differ
by an order of magnitude, so it is an argument rather than a constant.

**`curvature` (the default, and the operative one).** A spread `s` sprung
across a span `a` bends the rod into a parabola of curvature `2s/a^2`. The rod
is already bent to the dome radius, so report that as a fraction of the
curvature it is holding anyway. Pure geometry: no modulus, no strength,
nothing to look up. The span comes from the marking scheme, because a rod is
held at its feet and its tie marks and nowhere else -- the 30 unlashed
crossings are not clamps. Family G's fifths give the tightest span and
therefore set the tolerance.

**`overlap`.** The four marks at a node must still fall within a rod diameter
of each other. This is a tidy landmark and it is what a connector drawing
asks, but it is **not** a failure mode: a mark is a build aid, not a stop. The
connector sits where the four rods agree to cross, not on anybody's mark, and
the rods run through it and slide in their channels. Choosing this criterion
asks for about ten times the care that the curvature one does, for no physical
reason.

Neither is a limit. Where the real limit sits needs the strength and the
ultimate strain of the actual stock -- milestone 3's one open item that
depends on nothing else. And `2s/a^2` is a worst case on top of that: it holds
the two neighbouring nodes rigid, where a real frame spreads the displacement
over several spans and pays less.

## Field method matters more than field care

Two methods measure the same thing and accumulate error completely
differently, and the module prices both:

- **the ground**, pegged radially from a centre peg (ten independent errors)
  or chained around the perimeter (a random walk that has to be forced closed);
- **the marks**, each measured from the rod's end (independent) or stepped off
  the previous one (cumulative).

The sigmas below are assumptions about a person with a tape, not measurements.
They are inputs; change them and the answer changes.
"""

from __future__ import annotations

import math
import random
import statistics

from . import geometry, vec

# One-sigma field errors, in millimetres. Assumptions, not measurements: a
# steel tape read to the nearest millimetre by one person, on grass, is about
# this good. Override them from the CLI.
DEFAULT_GROUND_SIGMA = 10.0
DEFAULT_CUT_SIGMA = 3.0
DEFAULT_MARK_SIGMA = 3.0
DEFAULT_TRIALS = 2000

GROUND_METHODS = ("radial", "chained")
MARK_METHODS = ("from-end", "stepped")

CRITERIA = ("curvature", "overlap")

# How much extra bending a node mismatch may force, as a fraction of the
# curvature the rod is already holding. A judgement, not a limit: where the
# real limit sits needs the strength and the ultimate strain of the actual
# stock, which is milestone 3's one open item that depends on nothing else.
DEFAULT_CURVATURE_BUDGET = 0.10

# The exact constants derived in the module docstring.
D_RISE_D_LENGTH = 0.5
D_RISE_D_CHORD = -(math.pi / 4.0 - 0.5)


# --- the arc ---------------------------------------------------------------


def theta_for(chord_over_length: float) -> float:
    """Subtended angle of a circular arc, from chord / arc length.

    ``chord/length = 2 sin(t/2) / t`` is strictly decreasing on (0, 2*pi), so
    a bisection is exact to machine precision and needs no starting guess. A
    semicircle is the ratio 2/pi.
    """
    if not 0.0 < chord_over_length < 1.0:
        raise ValueError(f"chord/length must be in (0, 1), got {chord_over_length}")
    low, high = 1e-12, 2.0 * math.pi - 1e-12
    for _ in range(200):
        mid = 0.5 * (low + high)
        if 2.0 * math.sin(mid / 2.0) / mid > chord_over_length:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def arc_rise(chord: float, length: float) -> float:
    """How far an arc of this length stands off a chord of this length."""
    theta = theta_for(chord / length)
    return (length / theta) * (1.0 - math.cos(theta / 2.0))


def arc_points(foot_a, foot_b, length: float, bulge_ref, fractions) -> list:
    """Points at the given fractions of arc length, measured from ``foot_a``.

    ``bulge_ref`` is the nominal direction the bow stands off its chord --
    ``Bow.v``, the point at t = 90 relative to the dome centre. Moving a foot
    tilts the bow's plane rather than choosing a new one, so the plane taken
    here is the one through both feet whose bulge is as close to ``bulge_ref``
    as the new chord allows.

    The arc is built on an explicit in-plane basis rather than by rotating
    about a normal. A normal has two directions and at the semicircle the term
    that would reveal a wrong choice, ``radius * cos(theta/2)``, is exactly
    zero -- so a sign error there survives every nominal check and only shows
    up once something is perturbed. This construction has no sign to get
    wrong: ``e1`` points at ``foot_a`` and ``e2`` points at the bulge.
    """
    chord_vec = vec.sub(foot_b, foot_a)
    chord = vec.norm(chord_vec)
    theta = theta_for(chord / length)
    radius = length / theta

    along = vec.unit(chord_vec)
    bulge = vec.unit(
        vec.sub(bulge_ref, vec.scale(along, vec.dot(bulge_ref, along)))
    )

    midpoint = vec.scale(vec.add(foot_a, foot_b), 0.5)
    centre = vec.sub(midpoint, vec.scale(bulge, radius * math.cos(theta / 2.0)))

    e1 = vec.unit(vec.sub(foot_a, centre))
    e2 = vec.unit(vec.sub(bulge, vec.scale(e1, vec.dot(bulge, e1))))

    out = []
    for f in fractions:
        angle = theta * f
        out.append(
            vec.add(
                centre,
                vec.add(
                    vec.scale(e1, radius * math.cos(angle)),
                    vec.scale(e2, radius * math.sin(angle)),
                ),
            )
        )
    return out


# --- what a mismatch actually costs -----------------------------------------


def held_spans(data: dict) -> dict:
    """Arc between consecutive held points on a rod, per family, in mm.

    A rod is held at its two feet and at its tie marks, and nowhere else --
    the 30 unlashed crossings are not clamps and may not even get a part. So
    the span a mismatch has to be sprung across is the gap between marks, or
    between a foot and the nearest mark. Derived from the marking scheme
    rather than typed in: family G is marked in fifths and U and L in thirds,
    and a bow is 180 degrees of arc.
    """
    radius = data["meta"]["dome_radius"]
    out = {}
    for rod in data["rods"]:
        held = [0.0] + list(rod["tie_marks_deg"]) + [180.0]
        gap = min(held[i + 1] - held[i] for i in range(len(held) - 1))
        out[rod["family"]] = round(radius * math.radians(gap), 3)
    return out


def curvature_ratio(spread_mm: float, span_mm: float, radius_mm: float) -> float:
    """Extra curvature a node mismatch forces, against the rod's own.

    Hold a rod at two points ``span`` apart and push it ``spread`` sideways at
    the middle: the parabola through those three points is
    ``y = spread (1 - x^2/span^2)``, whose curvature is ``2*spread/span^2``.
    The rod is already bent to the dome radius, so the honest way to report
    the mismatch is as a fraction of the curvature it is holding anyway.

    This is the yardstick to use, and it is pure geometry -- no modulus, no
    strength, nothing that has to be looked up. It is also a **worst case**:
    it assumes the two neighbouring nodes are rigid, where a real frame
    spreads the displacement over several spans and pays less.
    """
    return (2.0 * spread_mm / (span_mm * span_mm)) * radius_mm


def spread_for_curvature(budget: float, span_mm: float, radius_mm: float) -> float:
    """Node spread that costs a given fraction of the rod's own curvature."""
    return budget * span_mm * span_mm / (2.0 * radius_mm)


# --- what gets measured ----------------------------------------------------


def mark_map(data: dict) -> dict:
    """``node -> [(rod, fraction of the rod's length)]`` for the 40 tie marks.

    Every tie mark lands on a lashed node and every lashed node takes four of
    them. Built by matching the nominal mark point against the node, so a
    change in the marking scheme cannot silently fall out of step with it.
    """
    bows = {b.name: b for b in geometry.build_bows()}
    radius = data["meta"]["dome_radius"]
    tied = [n for n in data["nodes"] if n["rod_count"] == 4]

    out: dict = {n["name"]: [] for n in tied}
    for rod in data["rods"]:
        bow = bows[rod["name"]]
        for t in rod["tie_marks_deg"]:
            point = bow.point(t, radius)
            for node in tied:
                if vec.dist(point, (node["x"], node["y"], node["z"])) < 1e-6:
                    out[node["name"]].append((rod["name"], t / 180.0))
                    break
    return out


def _ground(radius: float, sigma: float, method: str, rng) -> list:
    """Ten base points with their placement error.

    ``radial`` pegs each point from a centre peg: one radius and one angle per
    point, independent of the others. ``chained`` steps around the perimeter,
    so the along-ring errors accumulate as a random walk -- and then the ring
    has to close, which a surveyor does by spreading the closure error evenly.
    That leaves a Brownian bridge rather than a walk, which is the thing worth
    seeing.
    """
    step = 360.0 / geometry.BASE_POINT_COUNT
    if method == "radial":
        radial = [rng.gauss(0.0, sigma) for _ in range(geometry.BASE_POINT_COUNT)]
        along = [rng.gauss(0.0, sigma) for _ in range(geometry.BASE_POINT_COUNT)]
    elif method == "chained":
        radial = [rng.gauss(0.0, sigma) for _ in range(geometry.BASE_POINT_COUNT)]
        walk = [0.0]
        for _ in range(geometry.BASE_POINT_COUNT - 1):
            walk.append(walk[-1] + rng.gauss(0.0, sigma))
        closure = walk[-1] + rng.gauss(0.0, sigma)
        n = geometry.BASE_POINT_COUNT
        along = [w - closure * i / n for i, w in enumerate(walk)]
    else:
        raise ValueError(f"ground method must be one of {GROUND_METHODS}")

    points = []
    for i in range(geometry.BASE_POINT_COUNT):
        a = math.radians(i * step)
        r = radius + radial[i]
        tangent = (-math.sin(a), math.cos(a), 0.0)
        points.append(
            (
                r * math.cos(a) + tangent[0] * along[i],
                r * math.sin(a) + tangent[1] * along[i],
                0.0,
            )
        )
    return points


def _marks(fractions, sigma: float, method: str, rng) -> list:
    """Where the marks actually end up, as fractions of the nominal length.

    ``from-end`` reads every mark off the tape from the same rod end, so the
    errors are independent. ``stepped`` measures each from the last one, so
    they accumulate -- the fourth mark on a G bow carries four of them.
    """
    if method == "from-end":
        return [(f, rng.gauss(0.0, sigma)) for f in fractions]
    if method == "stepped":
        out = []
        running = 0.0
        for f in fractions:
            running += rng.gauss(0.0, sigma)
            out.append((f, running))
        return out
    raise ValueError(f"mark method must be one of {MARK_METHODS}")


# --- one build -------------------------------------------------------------


def build_once(data: dict, marks_by_node: dict, rng, ground_sigma: float,
               cut_sigma: float, mark_sigma: float, ground_method: str,
               mark_method: str) -> dict:
    """One imaginary dome, built by someone with a tape and a bad day."""
    bows = {b.name: b for b in geometry.build_bows()}
    radius = data["meta"]["dome_radius"]
    nominal_length = math.pi * radius

    feet = _ground(radius, ground_sigma, ground_method, rng)

    wanted: dict = {}
    for node, members in marks_by_node.items():
        for rod, fraction in members:
            wanted.setdefault(rod, []).append((fraction, node))
    for entries in wanted.values():
        entries.sort()

    placed: dict = {}
    heights = []
    lengths = []
    for rod, entries in sorted(wanted.items()):
        bow = bows[rod]
        length = nominal_length + rng.gauss(0.0, cut_sigma)
        lengths.append(length)
        marked = _marks(
            [f for f, _n in entries], mark_sigma, mark_method, rng
        )
        # A mark error is a distance along the rod; as a fraction of the rod
        # it is that distance over the rod's own length.
        fractions = [f + error / length for f, error in marked]
        points = arc_points(
            feet[bow.foot_a], feet[bow.foot_b], length, bow.v,
            fractions + [0.5],
        )
        for (_f, node), point in zip(entries, points):
            placed[(rod, node)] = point
        heights.append(points[-1][2])

    spreads = {}
    for node, members in marks_by_node.items():
        pts = [placed[(rod, node)] for rod, _f in members]
        spreads[node] = max(
            vec.dist(a, b)
            for i, a in enumerate(pts)
            for b in pts[i + 1:]
        )

    return {
        "worst_spread_mm": max(spreads.values()),
        "mean_spread_mm": statistics.fmean(spreads.values()),
        "height_mm": max(heights),
        "length_spread_mm": max(lengths) - min(lengths),
    }


# --- the study -------------------------------------------------------------


def _quantiles(values: list) -> dict:
    ordered = sorted(values)

    def at(q):
        return ordered[min(len(ordered) - 1, int(q * len(ordered)))]

    return {
        "median": round(at(0.5), 3),
        "p90": round(at(0.9), 3),
        "p95": round(at(0.95), 3),
        "max": round(ordered[-1], 3),
    }


def study(data: dict, trials: int = DEFAULT_TRIALS,
          ground_sigma: float = DEFAULT_GROUND_SIGMA,
          cut_sigma: float = DEFAULT_CUT_SIGMA,
          mark_sigma: float = DEFAULT_MARK_SIGMA,
          ground_method: str = "radial",
          mark_method: str = "from-end",
          criterion: str = "curvature",
          curvature_budget: float = DEFAULT_CURVATURE_BUDGET,
          seed: int = 20260911) -> dict:
    """Monte Carlo over the whole measured chain, plus one source at a time.

    The one-at-a-time runs are the point of it. A combined figure says how bad
    it gets; only the isolated ones say which measurement to be careful with,
    and that is the decision this module exists to inform.
    """
    marks_by_node = mark_map(data)

    def run(gs, cs, ms, gm=ground_method, mm=mark_method):
        rng = random.Random(seed)
        rows = [
            build_once(data, marks_by_node, rng, gs, cs, ms, gm, mm)
            for _ in range(trials)
        ]
        return {
            "worst_spread": _quantiles([r["worst_spread_mm"] for r in rows]),
            "mean_spread": _quantiles([r["mean_spread_mm"] for r in rows]),
            "height_error": _quantiles(
                [abs(r["height_mm"] - data["meta"]["dome_height_nominal"])
                 for r in rows]
            ),
        }

    combined = run(ground_sigma, cut_sigma, mark_sigma)
    sources = {
        "ground": run(ground_sigma, 0.0, 0.0),
        "cut": run(0.0, cut_sigma, 0.0),
        "marks": run(0.0, 0.0, mark_sigma),
    }

    # Each source run again at one millimetre of sigma. Spread is linear in
    # sigma -- everything here is a first-order displacement of a smooth
    # geometry -- so one run per source gives the sensitivity, and the
    # tolerance each measurement needs follows by division rather than by a
    # search. It also removes the sigmas above from the comparison: reading
    # the raw table instead would rank the sources by which sigma was guessed
    # largest.
    if criterion not in CRITERIA:
        raise ValueError(f"criterion must be one of {CRITERIA}, got {criterion!r}")

    rod = data["meta"]["rod_diameter"]
    radius = data["meta"]["dome_radius"]
    spans = held_spans(data)
    # The tightest span is the one that pays most for a given mismatch, so it
    # is the one the tolerance has to satisfy.
    span = min(spans.values())

    # Two possible targets, and which one is chosen changes the answer by an
    # order of magnitude, so it is an argument rather than a constant.
    #
    #   curvature  the mismatch may add this fraction to the bending the rod
    #              already carries. The operative one.
    #   overlap    the four marks at a node must still overlap within a rod
    #              diameter. A tidy landmark, but a mark is a build aid and
    #              not a stop: the connector sits where the rods agree to
    #              cross, not on anybody's mark. Kept because it is the
    #              question a connector drawing asks, not because anything
    #              fails past it.
    allowed = (
        spread_for_curvature(curvature_budget, span, radius)
        if criterion == "curvature"
        else rod
    )

    unit = {
        "ground": run(1.0, 0.0, 0.0),
        "cut": run(0.0, 1.0, 0.0),
        "marks": run(0.0, 0.0, 1.0),
    }
    per_mm = {
        name: body["worst_spread"]["p95"] for name, body in unit.items()
    }
    needed = {
        name: round(allowed / value, 2) if value else None
        for name, value in per_mm.items()
    }

    methods = {
        "ground": {
            m: run(1.0, 0.0, 0.0, gm=m)["worst_spread"]
            for m in GROUND_METHODS
        },
        "marks": {
            m: run(0.0, 0.0, 1.0, mm=m)["worst_spread"]
            for m in MARK_METHODS
        },
    }

    return {
        "variant": data["meta"]["variant"],
        "trials": trials,
        "sigmas_mm": {
            "ground": ground_sigma,
            "cut": cut_sigma,
            "mark": mark_sigma,
        },
        "methods_used": {"ground": ground_method, "marks": mark_method},
        "nodes_measured": len(marks_by_node),
        "marks": sum(len(v) for v in marks_by_node.values()),
        "sensitivity": {
            "rise_per_rod_length": D_RISE_D_LENGTH,
            "rise_per_base_diameter": round(D_RISE_D_CHORD, 6),
            "note": (
                "Exact at the semicircle and independent of dome size. Both "
                "are below 1, so the shape attenuates measurement error."
            ),
        },
        "combined": combined,
        "by_source": sources,
        "by_method": methods,
        "spread_per_mm_of_sigma": {k: round(v, 3) for k, v in per_mm.items()},
        "criterion": criterion,
        "curvature_budget": curvature_budget,
        "held_spans_mm": spans,
        "tightest_span_mm": span,
        "allowed_spread_mm": round(allowed, 2),
        "required_sigma_mm": needed,
        "curvature_cost": {
            key: round(
                curvature_ratio(
                    combined["worst_spread"][key], span, radius
                ), 5
            )
            for key in ("median", "p95", "max")
        },
        "dominant_source": max(per_mm, key=per_mm.get),
        "reference_lengths_mm": {
            "rod_diameter": rod,
            "connector_clearance": 0.4,
            "note": (
                "Spread under the clearance is absorbed by the connector "
                "without flexing anything. Spread over a rod diameter means "
                "the four marks no longer overlap. Between them the rods are "
                "sprung, and how much force that takes is milestone 8."
            ),
        },
    }


def format_study(data: dict, **kwargs) -> str:
    """Human-readable summary, for the CLI."""
    s = study(data, **kwargs)
    sigma = s["sigmas_mm"]
    lines = [
        f"--- {s['variant']} tolerance budget  "
        f"({s['trials']} trials, {s['marks']} marks on "
        f"{s['nodes_measured']} nodes)",
        f"  sigmas: ground {sigma['ground']:g} mm, cut {sigma['cut']:g} mm, "
        f"mark {sigma['mark']:g} mm"
        f"   ({s['methods_used']['ground']} ground, "
        f"{s['methods_used']['marks']} marks)",
        "  exact sensitivities, any size:"
        f"   rise per mm of rod {s['sensitivity']['rise_per_rod_length']:+.4f},"
        f"   rise per mm of base diameter "
        f"{s['sensitivity']['rise_per_base_diameter']:+.4f}",
        "",
        "  node spread (mm)        median     p90     p95     max",
    ]
    rows = [("all three", s["combined"])] + [
        (f"{name} only", body) for name, body in s["by_source"].items()
    ]
    for label, body in rows:
        q = body["worst_spread"]
        lines.append(
            f"    {label:<18} {q['median']:>8.2f} {q['p90']:>7.2f} "
            f"{q['p95']:>7.2f} {q['max']:>7.2f}"
        )
    lines.append("")
    cost = s["curvature_cost"]
    lines.append(
        f"  what that costs in bending, over the tightest span "
        f"({s['tightest_span_mm']:.0f} mm, family G):"
        f"   median {cost['median'] * 100:.1f}%, p95 {cost['p95'] * 100:.1f}% "
        f"of the curvature the rod already holds"
    )
    lines.append("")
    if s["criterion"] == "curvature":
        target = (
            f"{s['curvature_budget'] * 100:.0f}% extra curvature, which is "
            f"{s['allowed_spread_mm']:.0f} mm of spread"
        )
    else:
        target = (
            f"four marks overlapping within a rod diameter, "
            f"{s['allowed_spread_mm']:.0f} mm of spread"
        )
    lines.append(f"  per mm of care, against a target of {target} at p95:")
    for name, value in sorted(
        s["spread_per_mm_of_sigma"].items(), key=lambda kv: -kv[1]
    ):
        needed = s["required_sigma_mm"][name]
        flag = "  <- dominant" if name == s["dominant_source"] else ""
        lines.append(
            f"    {name:<8} {value:>5.2f} mm of spread per mm of sigma"
            f"   ->  hold to +/-{needed:.0f} mm{flag}"
        )
    lines.append("")
    lines.append("  method, at one mm of sigma either way (p95 spread):")
    for family, options in s["by_method"].items():
        best = min(options, key=lambda k: options[k]["p95"])
        for name, q in options.items():
            mark = "  <- cheaper" if name == best else ""
            lines.append(f"    {family:<8} {name:<10} {q['p95']:>7.2f} mm{mark}")
    lines.append("")
    ref = s["reference_lengths_mm"]
    lines.append(
        f"  for scale: connector clearance {ref['connector_clearance']:g} mm, "
        f"rod diameter {ref['rod_diameter']:g} mm"
        f"   (the 'overlap' criterion targets the latter, and asks about ten "
        f"times the care)"
    )
    q = s["combined"]["height_error"]
    lines.append(
        f"  height off nominal: median {q['median']:.1f} mm, "
        f"p95 {q['p95']:.1f} mm, worst {q['max']:.1f} mm"
    )
    return "\n".join(lines)
