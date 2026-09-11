"""The error budget: the arc solver, the two exact sensitivities, and scaling.

``test_a_perfect_build_reproduces_the_model`` is the one that makes everything
else mean something. The perturbed geometry is built by a completely different
route from ``geometry.Bow`` -- from a chord and an arc length rather than from
an azimuth and a tilt -- so running it with zero error is an independent
reconstruction of the same dome, and it has to land on the model's own nodes.

``test_common_mode_error_costs_nothing`` is the one that keeps the headline
honest. The claim is that only *differences* bind; a uniformly wrong dome has
to come out with no mismatch at all, or the claim is wrong and so is every
recommendation that follows from it.
"""

from __future__ import annotations

import math
import random

import pytest

from stardome import config, geometry, model, tolerance, vec

VARIANTS = sorted(config.load_all())


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param))


@pytest.fixture(scope="module")
def d6():
    return model.build(config.load("D6"))


# --- the arc solver --------------------------------------------------------


def test_a_semicircle_is_the_ratio_two_over_pi():
    assert tolerance.theta_for(2.0 / math.pi) == pytest.approx(math.pi, abs=1e-12)


@pytest.mark.parametrize("theta", [0.3, 1.0, 2.0, math.pi, 4.0, 6.0])
def test_theta_for_inverts_its_own_formula(theta):
    ratio = 2.0 * math.sin(theta / 2.0) / theta
    assert tolerance.theta_for(ratio) == pytest.approx(theta, abs=1e-9)


def test_theta_for_rejects_an_impossible_arc():
    with pytest.raises(ValueError):
        tolerance.theta_for(1.5)  # a chord longer than the arc
    with pytest.raises(ValueError):
        tolerance.theta_for(0.0)


def test_arc_starts_and_ends_on_its_feet():
    a, b = (1000.0, 0.0, 0.0), (-1000.0, 40.0, 0.0)
    points = tolerance.arc_points(a, b, 3400.0, (0.0, 0.0, 1.0), [0.0, 1.0])
    assert vec.dist(points[0], a) < 1e-9
    assert vec.dist(points[-1], b) < 1e-9


def test_arc_has_the_length_it_was_given():
    a, b = (1000.0, 0.0, 0.0), (-980.0, 0.0, 0.0)
    length = 3200.0
    points = tolerance.arc_points(
        a, b, length, (0.0, 0.0, 1.0), [i / 2000.0 for i in range(2001)]
    )
    walked = sum(vec.dist(points[i], points[i + 1]) for i in range(2000))
    # Chords under-report an arc; at 2000 segments the deficit is parts per
    # million, which is what this checks.
    assert walked == pytest.approx(length, rel=1e-6)


def test_arc_bulges_towards_the_reference_not_away():
    """The sign that a rotation-about-a-normal construction gets wrong.

    At the semicircle the term that would expose it is exactly zero, so this
    uses a chord shorter than the semicircle's to make it bite.
    """
    a, b = (1000.0, 0.0, 0.0), (-1000.0, 0.0, 0.0)
    for up in ((0.0, 0.0, 1.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)):
        middle = tolerance.arc_points(a, b, math.pi * 1000.0 * 1.2, up, [0.5])[0]
        assert vec.dot(middle, up) > 0.0


# --- against the model itself ----------------------------------------------


def test_mark_map_is_forty_marks_on_ten_nodes(built):
    marks = tolerance.mark_map(built)
    assert len(marks) == 10
    assert all(len(v) == 4 for v in marks.values())
    assert sum(len(v) for v in marks.values()) == 40
    assert sum(len(r["tie_marks_deg"]) for r in built["rods"]) == 40


def test_a_perfect_build_reproduces_the_model(built):
    """Zero error, built from chord and arc length, has to land on the nodes.

    This is the cross-check: nothing in ``arc_points`` knows about azimuths,
    tilts or great circles, so agreement is two independent constructions of
    the same dome rather than one of them checking itself.
    """
    marks = tolerance.mark_map(built)
    result = tolerance.build_once(
        built, marks, random.Random(1), 0.0, 0.0, 0.0, "radial", "from-end"
    )
    assert result["worst_spread_mm"] < 1e-6
    assert result["height_mm"] == pytest.approx(
        built["meta"]["dome_height_nominal"], abs=1e-3
    )


def test_common_mode_error_costs_nothing(built):
    """A uniformly wrong dome fits itself perfectly.

    Scale the ring and every bow by the same factor and the marks, being
    fractions of each rod's own length, scale with them. If this ever produced
    a mismatch, "only differences bind" would be false.
    """
    marks = tolerance.mark_map(built)
    bows = {b.name: b for b in geometry.build_bows()}
    radius = built["meta"]["dome_radius"]
    factor = 1.004

    wanted: dict = {}
    for node, members in marks.items():
        for rod, fraction in members:
            wanted.setdefault(rod, []).append((fraction, node))
    feet = geometry.base_points(radius * factor)

    placed = {}
    for rod, entries in wanted.items():
        entries.sort()
        bow = bows[rod]
        points = tolerance.arc_points(
            feet[bow.foot_a],
            feet[bow.foot_b],
            math.pi * radius * factor,
            bow.v,
            [f for f, _n in entries],
        )
        for (_f, node), point in zip(entries, points):
            placed[(rod, node)] = point

    for node, members in marks.items():
        pts = [placed[(rod, node)] for rod, _f in members]
        spread = max(
            vec.dist(a, b) for i, a in enumerate(pts) for b in pts[i + 1:]
        )
        assert spread < 1e-6, f"{node} mismatched under a uniform error"


# --- the two exact sensitivities -------------------------------------------


@pytest.mark.parametrize("radius", [1500.0, 3000.0, 6000.0])
def test_rise_per_millimetre_of_rod_is_exactly_a_half(radius):
    length = math.pi * radius
    chord = 2.0 * radius
    step = 1.0
    slope = (
        tolerance.arc_rise(chord, length + step)
        - tolerance.arc_rise(chord, length - step)
    ) / (2.0 * step)
    assert slope == pytest.approx(tolerance.D_RISE_D_LENGTH, abs=1e-7)


@pytest.mark.parametrize("radius", [1500.0, 3000.0, 6000.0])
def test_rise_per_millimetre_of_base_diameter_is_the_stated_constant(radius):
    length = math.pi * radius
    chord = 2.0 * radius
    step = 1.0
    slope = (
        tolerance.arc_rise(chord + step, length)
        - tolerance.arc_rise(chord - step, length)
    ) / (2.0 * step)
    assert slope == pytest.approx(tolerance.D_RISE_D_CHORD, abs=1e-7)
    assert tolerance.D_RISE_D_CHORD == pytest.approx(-(math.pi / 4.0 - 0.5))


def test_both_sensitivities_attenuate():
    """Under one in magnitude, which is the reason the dome is forgiving."""
    assert abs(tolerance.D_RISE_D_LENGTH) < 1.0
    assert abs(tolerance.D_RISE_D_CHORD) < 1.0


def test_a_semicircle_rise_is_the_radius():
    assert tolerance.arc_rise(6000.0, math.pi * 3000.0) == pytest.approx(3000.0)


# --- the study -------------------------------------------------------------


@pytest.fixture(scope="module")
def study(d6):
    return tolerance.study(d6, trials=400)


def test_spread_is_linear_in_sigma(d6):
    """The whole 'per mm of sigma' framing depends on this, and on it the
    required tolerances are a division rather than a search.

    Linear to first order, not exactly: the arc is a smooth but curved
    function of its inputs, so the ratio drifts by a fraction of a percent
    over a range of eight in sigma. That is the second-order term, and it is
    far below the confidence anyone has in the sigmas themselves.
    """
    marks = tolerance.mark_map(d6)
    ratios = []
    for sigma in (1.0, 2.0, 4.0, 8.0):
        rng = random.Random(7)
        values = sorted(
            tolerance.build_once(
                d6, marks, rng, sigma, 0.0, 0.0, "radial", "from-end"
            )["worst_spread_mm"]
            for _ in range(200)
        )
        ratios.append(values[190] / sigma)
    assert max(ratios) - min(ratios) < 0.01 * max(ratios)


def test_the_study_is_deterministic(d6):
    assert tolerance.study(d6, trials=100) == tolerance.study(d6, trials=100)


def test_stepping_marks_off_each_other_is_worse_than_reading_from_the_end(study):
    by_method = study["by_method"]["marks"]
    assert by_method["stepped"]["p95"] > by_method["from-end"]["p95"]


def test_cut_length_matters_least(study):
    per_mm = study["spread_per_mm_of_sigma"]
    assert per_mm["cut"] < per_mm["ground"]
    assert per_mm["cut"] < per_mm["marks"]


def test_required_tolerance_is_the_rod_diameter_over_the_sensitivity(study):
    rod = study["reference_lengths_mm"]["rod_diameter"]
    for name, per_mm in study["spread_per_mm_of_sigma"].items():
        assert study["sigma_for_one_rod_diameter_mm"][name] == pytest.approx(
            rod / per_mm, abs=0.01
        )


def test_zero_sigma_everywhere_gives_no_spread(d6):
    result = tolerance.study(d6, trials=20, ground_sigma=0.0, cut_sigma=0.0,
                             mark_sigma=0.0)
    assert result["combined"]["worst_spread"]["max"] < 1e-6
    assert result["combined"]["height_error"]["max"] < 1e-3


# --- what it says about size -----------------------------------------------


def test_sensitivity_does_not_depend_on_dome_size(built):
    """The coefficients come from a self-similar shape, so they are the same
    at 3 m and at 12 m -- which means the tolerance is absolute, and a small
    dome is proportionally the harder one to build."""
    here = tolerance.study(built, trials=300)["spread_per_mm_of_sigma"]
    reference = {"ground": 4.312, "marks": 4.222, "cut": 2.026}
    for name, value in reference.items():
        assert here[name] == pytest.approx(value, abs=0.02)


def test_required_tolerance_follows_the_rod_and_nothing_else(built):
    """Two domes with the same rod need the same care, whatever their size."""
    study = tolerance.study(built, trials=300)
    rod = built["meta"]["rod_diameter"]
    expected = {8: 1.9, 10: 2.3, 12: 2.8}[int(rod)]
    assert study["sigma_for_one_rod_diameter_mm"]["ground"] == pytest.approx(
        expected, abs=0.1
    )
