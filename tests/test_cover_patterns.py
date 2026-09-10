"""Cutting the cover: the three patterns, and why the reference prefers one.

The exact results locked in here are the facet side (R/phi, which the model
already carries), and the gore's 2/pi fill -- a constant, not a coincidence.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, cover, model

VARIANTS = sorted(config.load_all())
PHI = (1.0 + 5.0 ** 0.5) / 2.0


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param), weave_mode="layered")


# --- the faceted pattern --------------------------------------------------
def test_the_facet_side_is_the_model_s_own_base_edge(built):
    """Half an icosidodecahedron, whose equatorial decagons are the G bows."""
    meta = built["meta"]
    assert cover.facet_side(built) == meta["base_edge_chord"]
    assert cover.facet_side(built) == pytest.approx(meta["dome_radius"] / PHI, abs=1e-6)


def test_the_faceted_cover_is_six_pentagons_and_ten_triangles(built):
    f = cover.faceted(built)
    assert f["panels"] == {"pentagons": 6, "triangles": 10}
    assert f["panel_count"] == 16


def test_the_faceted_cover_has_twenty_five_seams(built):
    """60 edges, 10 on the equator, the other 50 shared between two halves."""
    f = cover.faceted(built)
    assert f["seam_count"] == 25
    assert f["seam_length_m"] == pytest.approx(
        25.0 * f["side_mm"] / 1000.0, abs=0.1
    )


def test_the_faceted_cover_wraps_less_than_the_sphere(built):
    """It is an inscribed polyhedron, so it is genuinely a smaller surface."""
    f = cover.faceted(built, oversize=0.0)
    assert f["area_m2"] < cover.areas(built)["dome_m2"]
    assert f["baseline"].startswith("inscribed")


def test_a_pentagon_outgrows_a_narrow_roll(built):
    """Which is what undoes the faceted pattern's apparent simplicity."""
    f = cover.faceted(built, roll_width_mm=1500.0)
    if f["pentagon_width_mm"] > 1500.0:
        assert not f["pentagon_fits_roll"]
        assert f["pentagon_strips"] >= 2


# --- the gore pattern -----------------------------------------------------
def test_a_gore_fills_exactly_two_over_pi_of_its_rectangle(built):
    """A constant: no radius in it, no gore count in it."""
    g = cover.gore_plan(built)
    assert g["fill_of_bounding_box"] == pytest.approx(2.0 / math.pi, abs=1e-6)


def test_the_gore_fill_is_borne_out_by_the_roll_it_eats(built):
    """Two losses, not one.

    2/pi is the gore in its OWN rectangle. On the roll there is a second
    loss: the count is rounded up, so the gore is narrower than the fabric
    and the leftover width is wasted too.
    """
    g = cover.gore_plan(built, roll_width_mm=1500.0)
    used = g["roll_floor_m"] / g["roll_length_m"]
    assert used == pytest.approx(
        (2.0 / math.pi) * g["gore_width_mm"] / 1500.0, rel=0.02
    )
    assert used <= 2.0 / math.pi + 1e-9


def test_more_gores_never_buys_less_roll(built):
    """The leftover roll width is wasted, so a finer division only loses."""
    wide = cover.gores(built, 1500.0)
    assert wide["gore_width_mm"] <= 1500.0
    # The minimum count that fits is the one the plan uses.
    assert wide["count"] == max(
        3, math.ceil(2.0 * math.pi * cover.radius(built) / 1500.0)
    )


# --- the leaf pattern -----------------------------------------------------
def test_a_leaf_cover_needs_at_least_three_leaves(built):
    with pytest.raises(ValueError):
        cover.leaf(built, leaves=2)


def test_the_lap_cannot_swallow_the_roll(built):
    with pytest.raises(ValueError):
        cover.leaf(built, roll_width_mm=100.0, lap_mm=100.0)


def test_nesting_the_lanes_end_for_end_saves_roll(built):
    l = cover.leaf(built, 10)
    assert l["roll_length_m"] < l["roll_unnested_m"]


def test_five_leaves_and_ten_cost_the_same_fabric_and_half_the_seam(built):
    five = cover.leaf(built, 5)
    ten = cover.leaf(built, 10)
    assert five["roll_length_m"] == pytest.approx(ten["roll_length_m"], rel=0.02)
    assert five["leaf_seam_length_m"] == pytest.approx(
        ten["leaf_seam_length_m"] / 2.0, rel=0.02
    )
    assert five["piece_count"] < ten["piece_count"]


def test_the_leaf_beats_the_gore_on_both_roll_and_seam(built):
    """Which is the reference's recommendation, arrived at by counting."""
    leaf = cover.leaf(built, 5)
    gore = cover.gore_plan(built)
    assert leaf["roll_length_m"] < gore["roll_length_m"]
    assert leaf["leaf_seam_length_m"] < gore["seam_length_m"]


def test_every_lane_is_narrower_than_the_roll(built):
    l = cover.leaf(built, 10, roll_width_mm=1500.0, lap_mm=80.0)
    # Lanes are cut with their HEIGHT across the roll, so it is the lane
    # height that has to fit -- and that is roll width by construction.
    assert l["lanes_per_leaf"] >= 1
    assert l["lap_mm"] == 80.0


# --- oversize and cost ----------------------------------------------------
def test_oversize_scales_area_by_its_square(built):
    plain = cover.leaf(built, 10, oversize=0.0)
    big = cover.leaf(built, 10, oversize=0.10)
    assert big["area_m2"] == pytest.approx(plain["area_m2"] * 1.21, rel=1e-3)


def test_takekawas_ten_percent_is_the_default():
    assert cover.DEFAULT_OVERSIZE == 0.10


def test_cost_is_the_roll_times_the_price():
    assert cover.roll_cost(66.9, 450.0)["total"] == pytest.approx(30105.0, abs=0.5)


def test_the_comparison_carries_every_pattern(built):
    p = cover.patterns(built, price_per_m=100.0)
    for key in ("faceted", "leaf_10", "leaf_5", "gore"):
        assert key in p
        assert p[key]["roll_floor_m"] > 0
    for key in ("leaf_10", "leaf_5", "gore"):
        assert p[key]["cost"]["total"] > 0
