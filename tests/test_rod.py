"""Buying and cutting the rod.

The correctness point worth guarding is the first one: the cut list reads the
NOMINAL bow length. Taken from a layered model it would ask for fifteen
different pieces, and the dome wants one piece fifteen times.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, model, rod

VARIANTS = sorted(config.load_all())
NAMED = ("S", "M", "L", "XL")


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param), weave_mode="layered")


# --- one length, fifteen times --------------------------------------------
def test_the_cut_length_does_not_depend_on_the_drawing_convention():
    """layered draws fifteen shells; the frame is still fifteen equal bows."""
    flat = model.build(config.load("M"), weave_mode="flat")
    layered = model.build(config.load("M"), weave_mode="layered")
    assert rod.bows(flat) == rod.bows(layered)
    assert layered["meta"]["rod_length_class_count"] == 15  # the drawing
    assert flat["meta"]["rod_length_class_count"] == 1      # the frame


def test_a_bow_is_a_semicircle_of_the_dome_radius(built):
    b = rod.bows(built)
    assert b["count"] == 15
    assert b["length_mm"] == pytest.approx(
        math.pi * built["meta"]["dome_radius"], abs=0.1
    )
    assert b["bend_radius_mm"] == built["meta"]["dome_radius"]


def test_the_total_is_the_bow_fifteen_times(built):
    b = rod.bows(built)
    # length_mm is rounded before it is reported and total_mm is not, so
    # fifteen of them can differ by fifteen roundings.
    assert b["total_mm"] == pytest.approx(b["count"] * b["length_mm"], abs=1.0)
    assert b["total_m"] == pytest.approx(b["total_mm"] / 1000.0, abs=0.01)


# --- sections -------------------------------------------------------------
def test_sections_divide_the_bow_evenly_and_stay_under_the_limit(built):
    limit = built["meta"]["section_length"]
    s = rod.sections(built)
    assert s["length_mm"] <= limit + 1e-6
    assert s["per_bow"] == math.ceil(rod.bows(built)["length_mm"] / limit)
    assert s["length_mm"] * s["per_bow"] == pytest.approx(
        rod.bows(built)["length_mm"], abs=0.5
    )


def test_every_section_is_the_same_piece(built):
    """Which is why they are divided evenly instead of cut to the limit."""
    s = rod.sections(built)
    limit = built["meta"]["section_length"]
    stub = rod.bows(built)["length_mm"] - (s["per_bow"] - 1) * limit
    # The even division is longer than the stub the naive cut would leave.
    assert s["length_mm"] > stub or s["per_bow"] == 1


def test_splices_are_one_fewer_than_sections(built):
    s = rod.sections(built)
    assert s["splices_per_bow"] == s["per_bow"] - 1
    assert s["splices_total"] == s["splices_per_bow"] * 15


def test_no_limit_means_the_bow_travels_whole(built):
    s = rod.sections(built, limit_mm=0.0)
    assert s["per_bow"] == 1
    assert s["splices_total"] == 0


# --- stock ----------------------------------------------------------------
def test_a_coil_has_no_cutting_waste(built):
    plan = rod.cut_plan(built, rod.COIL)
    assert plan["stock"] == "coil"
    assert plan["waste_m"] == 0.0
    assert plan["bought_m"] == plan["used_m"]
    assert plan["efficiency"] == 1.0


def test_a_bar_never_buys_less_than_it_uses(built):
    for bar in (3000.0, 6000.0, 11800.0):
        plan = rod.cut_plan(built, bar)
        assert plan["bought_m"] >= plan["used_m"]
        assert plan["waste_m"] >= 0.0
        assert 0.0 < plan["efficiency"] <= 1.0


def test_sections_per_bar_is_what_fits_whole(built):
    plan = rod.cut_plan(built, 6000.0)
    sec = rod.sections(built)
    assert plan["sections_per_stock"] == int(6000.0 // sec["length_mm"])
    assert plan["offcut_per_stock_mm"] == pytest.approx(
        6000.0 - plan["sections_per_stock"] * sec["length_mm"], abs=0.2
    )


def test_a_bar_shorter_than_a_section_is_refused(built):
    with pytest.raises(ValueError):
        rod.cut_plan(built, 500.0)


def test_a_bar_that_divides_the_section_wastes_least():
    """The finding: the bar length is the lever, not any cleverness in cutting."""
    d = model.build(config.load("M"))
    rows = rod.stock_sweep(d)
    by_bar = {r["stock_mm"]: r["waste_pct"] for r in rows}
    assert by_bar[11800.0] < 1.0
    assert by_bar[6000.0] > 20.0
    # And it costs nothing in splices to pick the better bar.
    assert len({r["splices_per_bow"] for r in rows}) == 1


# --- mass and the summary -------------------------------------------------
def test_mass_is_the_rod_volume(built):
    meta = built["meta"]
    area = math.pi * (meta["rod_diameter"] / 2000.0) ** 2
    assert rod.mass(built)["kg"] == pytest.approx(
        area * rod.bows(built)["total_m"] * rod.GFRP_DENSITY, abs=0.1
    )


def test_the_summary_has_a_row_for_every_named_size():
    rows = [
        rod.summary_row(model.build(config.load(n)), stock_mm=11800.0,
                        price_per_m=120.0)
        for n in NAMED
    ]
    assert [r["alias"] for r in rows] == list(NAMED)
    for key in ("used_m", "bought_m", "cost", "sections"):
        values = [r[key] for r in rows]
        assert values == sorted(values)


def test_the_summary_needs_no_price(built):
    r = rod.summary_row(built)
    assert "cost" not in r
    assert "cost" not in rod.format_summary([r]).split("\n")[3]


def test_the_summary_says_which_stock_it_priced(built):
    row = rod.summary_row(built, stock_mm=6000.0)
    assert "6000 mm bar" in rod.format_summary([row], 6000.0)
    assert "coil" in rod.format_summary([rod.summary_row(built)], None)
