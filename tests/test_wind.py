"""Wind screening.

These lock in arithmetic and two findings, not a design. Nothing in this file
says a dome is safe, and `test_the_report_admits_what_it_leaves_out` is here
to make sure the module keeps saying so.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, interior, model, wind

VARIANTS = sorted(config.load_all())
BARE = ("D6", "D8", "D10", "D12")


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param), weave_mode="layered")


# --- the arithmetic -------------------------------------------------------
def test_dynamic_pressure_is_half_rho_v_squared():
    assert wind.pressure(20.0) == pytest.approx(
        0.5 * wind.AIR_DENSITY * 400.0, rel=1e-9
    )
    # And it goes as the square: double the wind, four times the pressure.
    assert wind.pressure(20.0) == pytest.approx(4.0 * wind.pressure(10.0), rel=1e-9)


def test_mass_is_rod_volume_plus_fabric_area(built):
    m = wind.mass(built, "oxford_600d")
    meta = built["meta"]
    area = math.pi * (meta["rod_diameter"] / 2000.0) ** 2
    expect = area * (meta["total_rod_length"] / 1000.0) * wind.GFRP_DENSITY
    assert m["rods_kg"] == pytest.approx(expect, abs=0.1)
    assert m["total_kg"] == pytest.approx(m["rods_kg"] + m["cover_kg"], abs=0.1)
    # total_kg is rounded before it is reported; weight_N is not, so allow a
    # newton of slack rather than pretending they were computed together.
    assert m["weight_N"] == pytest.approx(m["total_kg"] * wind.GRAVITY, abs=1.0)


def test_an_unknown_fabric_is_refused(built):
    with pytest.raises(ValueError):
        wind.mass(built, "canvas")


def test_at_the_tipping_speed_the_moments_balance(built):
    """The definition, checked against the thing it is defined from."""
    v = wind.tipping_speed(built)
    a = wind.anchors(built, v)
    assert a["overturning_Nm"] == pytest.approx(a["righting_Nm"], rel=1e-3)


def test_below_the_tipping_speed_it_stands_and_above_it_does_not(built):
    v = wind.tipping_speed(built)
    assert wind.anchors(built, v * 0.9)["stands_on_its_own"]
    assert not wind.anchors(built, v * 1.1)["stands_on_its_own"]
    assert wind.anchors(built, v * 0.9)["hold_down_total_N"] == 0.0


def test_hold_down_grows_with_the_square_of_the_wind(built):
    """Past the tipping point the deficit is dominated by the v^2 term."""
    v = wind.tipping_speed(built)
    a = wind.anchors(built, v * 2.0)["hold_down_total_N"]
    b = wind.anchors(built, v * 4.0)["hold_down_total_N"]
    assert b > 3.5 * a


# --- the findings ---------------------------------------------------------
def test_a_bare_dome_tips_at_about_the_same_speed_whatever_its_size():
    """Mass and sail both scale with R^2 and the levers with R, so it cancels.

    The spread that is left tracks the rod diameter steps in the config, not
    the diameter of the dome.
    """
    speeds = [
        wind.tipping_speed(model.build(config.load(n), weave_mode="layered"))
        for n in BARE
    ]
    assert min(speeds) > 12.0
    assert max(speeds) < 15.0
    assert (max(speeds) - min(speeds)) / min(speeds) < 0.15


def test_a_skirt_costs_wind():
    """The finding the interior work implied and this puts a number on.

    A skirt adds sail and lifts the centroid without adding much mass, so the
    dome that gains a walk-in door loses the wind it can stand in.
    """
    bare = model.build(config.load("D4", skirt_height=0.0), weave_mode="layered")
    skirted = model.build(config.load("D4", skirt_height=1350.0), weave_mode="layered")
    assert wind.tipping_speed(skirted) < wind.tipping_speed(bare)
    # And it is not a rounding difference.
    assert wind.tipping_speed(bare) - wind.tipping_speed(skirted) > 1.0


def test_the_skirted_small_dome_is_the_weakest_in_the_family():
    speeds = {
        n: wind.tipping_speed(model.build(config.load(n), weave_mode="layered"))
        for n in VARIANTS
    }
    weakest = min(speeds, key=speeds.get)
    assert config.load(weakest).skirt_height > 0


def test_heavier_fabric_buys_wind(built):
    light = wind.tipping_speed(built, fabric="oxford_210d")
    heavy = wind.tipping_speed(built, fabric="oxford_600d")
    assert heavy > light


def test_a_higher_force_coefficient_costs_wind(built):
    assert wind.tipping_speed(built, cf=0.65) < wind.tipping_speed(built, cf=0.35)


def test_the_cover_is_a_serious_share_of_the_mass(built):
    """Rod is not the heavy part on anything but the smallest dome."""
    m = wind.mass(built, "oxford_600d")
    assert m["cover_kg"] > 0.25 * m["total_kg"]


# --- what it refuses to claim ---------------------------------------------
def test_the_report_admits_what_it_leaves_out(built):
    a = wind.analyse(built)
    assert a["assumptions"]["uplift_included"] is False
    assert a["assumptions"]["code"] is None
    assert a["assumptions"]["safety_factors"] is None
    assert "SCREENING ONLY" in a["note"]
    assert "SCREENING ONLY" in wind.format_analysis(built)


def test_the_force_coefficient_is_carried_as_an_assumption(built):
    a = wind.analyse(built, cf=0.42)
    assert a["cf"] == 0.42
    assert a["assumptions"]["cf"] == 0.42
    assert len(a["tipping_speed_by_cf"]) == len(wind.CF_RANGE)


# --- the corridor and the camp --------------------------------------------
def test_a_corridor_is_mostly_side():
    sail = wind.corridor_sail({"kind": "hoop", "width": 900.0, "height": 1950.0},
                              3000.0)
    assert sail["broadside_m2"] > 3.0 * sail["end_on_m2"]


def test_a_longer_corridor_is_more_sail():
    spec = {"kind": "hoop", "width": 900.0, "height": 1950.0}
    assert (wind.corridor_sail(spec, 6000.0)["broadside_m2"]
            == pytest.approx(2.0 * wind.corridor_sail(spec, 3000.0)["broadside_m2"],
                             rel=1e-6))
