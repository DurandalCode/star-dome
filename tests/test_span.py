"""The span between supports, and the scaling law built on it.

Two things are worth guarding here. The first is that the span is a property
of the *topology*, not of a size: every variant must report the same span as a
fraction of its own radius, because the family is similar to itself. If that
ever stops being true, either the topology changed or the span is being
measured against the wrong thing.

The second is that the two readings of "held" -- feet and tie marks, or every
crossing -- must stay exactly 5/3 apart, because that ratio is the only number
anybody has put on the thirty unlashed crossings.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, model, span, tolerance

VARIANTS = ["D3", "D4", "D6", "D8", "D10", "D12"]


@pytest.fixture(scope="module")
def built():
    return {name: model.build(config.load(name)) for name in VARIANTS}


@pytest.fixture(scope="module")
def ref(built):
    return span.reference(built[span.REFERENCE_VARIANT], "lashed")


# --- the span is a shape, not a size ----------------------------------------


@pytest.mark.parametrize("holds", span.HOLDS)
def test_the_span_is_the_same_fraction_at_every_size(built, holds):
    """Similarity is the premise the whole scaling argument rests on.

    Every angle in this family is the same at D3 and at D12, so the worst span
    has to be the same multiple of the radius at both. The millimetres differ;
    the fraction may not.
    """
    fractions = {
        name: span.spans(data, holds)["fraction_of_radius"]
        for name, data in built.items()
    }
    assert len(set(round(f, 9) for f in fractions.values())) == 1, fractions

    # And it is the arc it looks like: 60 degrees held at the marks, 36 with
    # every crossing clamped. Derived from the marking scheme, not typed in.
    expected = math.radians(60.0 if holds == "lashed" else 36.0)
    assert fractions["D6"] == pytest.approx(expected, abs=1e-9)


def test_the_worst_span_scales_linearly_with_the_dome(built):
    for name, data in built.items():
        s = span.spans(data, "lashed")
        radius = data["meta"]["dome_radius"]
        assert s["worst"]["length_mm"] == pytest.approx(
            radius * math.radians(60.0), abs=1e-3
        ), name


# --- which family is weak depends on what holds it --------------------------


def test_clamping_the_free_crossings_swaps_the_weak_family(built):
    """Family G is held only at lashed nodes, so clamps do nothing for it.

    U and L cross other rods six more times each. Clamp those and they go from
    the worst spans in the dome to the best, and G -- untouched -- becomes the
    binding one.
    """
    for name, data in built.items():
        loose = span.spans(data, "lashed")["worst"]
        tight = span.spans(data, "contact")["worst"]
        assert loose["family"] in ("U", "L"), name
        assert tight["family"] == "G", name
        assert loose["arc_deg"] == pytest.approx(60.0), name
        assert tight["arc_deg"] == pytest.approx(36.0), name


def test_what_the_thirty_clamps_are_worth(built):
    """5/3 in span is (5/3)^2 in rod diameter, because d ~ a^2 at equal sag."""
    for name, data in built.items():
        v = span.clamp_value(data)
        # Both are reported rounded, the way every other number here is.
        assert v["span_ratio"] == pytest.approx(5.0 / 3.0, abs=1e-6), name
        assert v["rod_diameter_ratio"] == pytest.approx(25.0 / 9.0, abs=1e-6), name


def test_family_g_gains_nothing_from_clamping(built):
    for name, data in built.items():
        loose = span.spans(data, "lashed")["per_family"]["G"]
        tight = span.spans(data, "contact")["per_family"]["G"]
        assert loose["arc_deg"] == pytest.approx(tight["arc_deg"]), name


# --- it agrees with the module that already measures spans ------------------


def test_it_agrees_with_the_tolerance_budget(built):
    """`tolerance.held_spans` takes the tightest span; this takes the longest.

    Both read the same table -- a bow held at its feet and its tie marks -- and
    the marking is even, so for every family the two ends of that table are
    the same number. Two modules deriving one span independently and landing
    on it is the check worth having.
    """
    for name, data in built.items():
        tight = tolerance.held_spans(data)
        loose = span.spans(data, "lashed")["per_family"]
        for family, mm in tight.items():
            assert loose[family]["length_mm"] == pytest.approx(mm, abs=1e-3), (
                f"{name} {family}"
            )


# --- a bow with a hole in it ------------------------------------------------


def test_a_cut_bow_is_held_at_the_term_not_at_a_foot_it_no_longer_has(built):
    """The portal takes an end piece off two bows. What is left starts at a
    clamp against another rod, and the span must be measured from there."""
    data = built["D6"]
    cut = {
        rod["name"]: rod["cut_spans_deg"]
        for rod in data["rods"]
        if rod.get("cut_spans_deg")
    }
    assert cut, "D6 is expected to carry a portal cut"

    held = span.supports(data, "lashed")
    for name, spans_removed in cut.items():
        (lo, hi), = spans_removed
        kinds = dict(held[name])
        assert lo not in kinds or kinds[lo] != "node"
        starts = [t for t, _ in held[name]]
        # Nothing is reported inside the piece that was cut away.
        assert not [t for t in starts if lo + 1e-9 < t < hi - 1e-9], name
        # The surviving end is a term, and the far foot is still a foot.
        assert ("term" in dict(held[name]).values()), name


def test_an_uncut_g_bow_is_held_at_its_four_tie_marks(built):
    data = built["D6"]
    held = span.supports(data, "lashed")
    rod = next(r for r in data["rods"] if r["name"] == "G1")
    assert [round(t, 6) for t, _ in held["G1"]] == [
        0.0, *[round(m, 6) for m in rod["tie_marks_deg"]], 180.0
    ]
    assert [kind for _, kind in held["G1"]] == [
        "foot", "node", "node", "node", "node", "foot"
    ]


# --- the scaling law --------------------------------------------------------


def test_the_reference_compares_equal_to_itself(built, ref):
    data = built[span.REFERENCE_VARIANT]
    s = span.spans(data, "lashed")
    for case in span.LOAD_CASES:
        assert span.sag_ratio(
            case,
            data["meta"]["dome_radius"],
            s["worst"]["length_mm"],
            data["meta"]["rod_diameter"],
            ref,
        ) == pytest.approx(1.0, abs=1e-9), case
        assert span.parity_rod(
            case, data["meta"]["dome_radius"], s["worst"]["length_mm"], ref
        ) == pytest.approx(data["meta"]["rod_diameter"], abs=1e-9), case


def test_bend_strain_is_the_geometry_it_says_it_is(ref):
    # A 10 mm rod bent to 3000 mm: the outer fibre travels 5/3000 further.
    assert span.bend_strain(10.0, 3000.0) == pytest.approx(10.0 / 6000.0)
    assert ref["bend_strain"] == pytest.approx(10.0 / 6000.0)


@pytest.mark.parametrize("case", sorted(span.LOAD_CASES))
@pytest.mark.parametrize("strain", span.STRAIN_SAMPLES)
def test_at_the_ceiling_the_two_constraints_meet(ref, case, strain):
    """The ceiling is defined as the radius where the rod that holds the span
    is exactly the rod the allowable strain permits. Solve it, then check the
    two sides really are equal there rather than trusting the algebra."""
    top = span.ceiling(case, strain, ref)
    radius = top["radius_mm"]
    a = radius * span.ref_fraction(ref)
    needs = span.parity_rod(case, radius, a, ref)
    allows = 2.0 * radius * strain
    assert needs == pytest.approx(allows, rel=1e-6)


def test_shortening_the_span_buys_the_ceiling_back_quadratically(ref):
    """Self-weight parity has d ~ a^2, so halving the span is four times the
    radius. This is the whole reason milestone 7 measures candidates against
    the span and not against each other."""
    bare = span.ceiling("self_weight", 0.004, ref, span_factor=1.0)
    halved = span.ceiling("self_weight", 0.004, ref, span_factor=0.5)
    assert halved["radius_mm"] == pytest.approx(4.0 * bare["radius_mm"], rel=1e-6)


def test_the_configured_xl_rods_are_thinner_than_similarity_asks(built, ref):
    """The config says the rod diameters are provisional assumptions. This is
    the first check of them: similarity wants d ~ R, and past the reference
    every variant is under it."""
    for name in ("D8", "D10", "D12"):
        a = span.analyse(built[name], ref)
        assert a["rod"]["under_rodded_by"] > 1.0, name
    assert span.analyse(built["D6"], ref)["rod"]["under_rodded_by"] == pytest.approx(1.0)


def test_an_unknown_holds_or_case_says_so():
    with pytest.raises(ValueError, match="unknown holds"):
        span.spans({"rods": [], "crossings": [], "meta": {}}, "welded")
    with pytest.raises(ValueError, match="unknown load case"):
        span.parity_rod("snow", 3000.0, 1000.0, {})


@pytest.mark.parametrize("holds", span.HOLDS)
def test_no_span_crosses_a_removed_middle_interval(holds):
    from dataclasses import replace
    data = model.build(replace(config.load("D6"), door_cut="head", doors=()))
    actual = span.spans(data, holds)["per_rod"]
    split_rods = 0
    for rod in data["rods"]:
        live = span.live_intervals(rod)
        split_rods += len(live) > 1
        for s in actual[rod["name"]]:
            assert any(lo-1e-6 <= s["t_lo_deg"] and s["t_hi_deg"] <= hi+1e-6 for lo, hi in live)
        assert sum(s["arc_deg"] for s in actual[rod["name"]]) == pytest.approx(sum(hi-lo for lo,hi in live), abs=1e-6)
    assert split_rods > 0
