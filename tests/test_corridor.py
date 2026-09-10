"""A covered corridor on the doorway.

Two results are worth locking in. The corridor bends rod far harder than the
dome does, which is a purchasing constraint rather than a drawing one; and a
corridor cannot be bigger than the hole it is attached to, which is the check
everyone skips.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, corridor, cover, model

VARIANTS = sorted(config.load_all())
WITH_DOOR = [n for n in VARIANTS if config.load(n).door]


@pytest.fixture(scope="module", params=WITH_DOOR)
def built(request):
    return model.build(
        config.load(request.param), weave_mode="layered", corridor_spec={}
    )


# --- the section ----------------------------------------------------------
def test_the_section_is_a_silhouette_that_closes_at_the_crown():
    s = corridor.section(900.0, 1950.0)
    assert s[0] == (0.0, 450.0)
    heights = [h for h, _ in s]
    assert heights == sorted(heights)
    assert heights[-1] == pytest.approx(1950.0)
    assert s[-1][1] == pytest.approx(0.0, abs=1e-9)


def test_the_roof_is_a_semicircle_over_the_legs():
    width, height = 900.0, 1950.0
    half, leg = width / 2.0, height - width / 2.0
    for h, w in corridor.section(width, height):
        if h <= leg:
            assert w == pytest.approx(half)
        else:
            assert w == pytest.approx(math.sqrt(half * half - (h - leg) ** 2), abs=1e-6)


def test_a_tunnel_shorter_than_its_own_arch_is_refused():
    with pytest.raises(ValueError):
        corridor.section(900.0, 400.0)


# --- the hoop -------------------------------------------------------------
def test_the_hoop_bends_rod_harder_than_the_dome_does(built):
    h = built["corridor"]["hoop"]
    assert h["bend_radius_mm"] < h["dome_bend_radius_mm"]
    assert h["times_tighter_than_dome"] > 1.0


def test_the_hoop_is_two_legs_and_a_half_circle():
    h = corridor.hoop(900.0, 1950.0, 10.0, 3000.0)
    assert h["bend_radius_mm"] == pytest.approx(450.0)
    assert h["leg_height_mm"] == pytest.approx(1500.0)
    assert h["rod_length_mm"] == pytest.approx(2 * 1500.0 + math.pi * 450.0, abs=0.1)


def test_a_wider_corridor_bends_rod_less_hard():
    narrow = corridor.hoop(700.0, 1950.0, 10.0, 3000.0)
    wide = corridor.hoop(1100.0, 1950.0, 10.0, 3000.0)
    assert wide["bend_radius_mm"] > narrow["bend_radius_mm"]


# --- the mouth ------------------------------------------------------------
def test_the_mouth_lies_on_the_cover(built):
    m = built["corridor"]["mouth"]
    assert m["fits_on_dome"]
    rc = cover.radius(built)
    for x, y, z in m["points"]:
        on = math.sqrt(x * x + y * y + z * z) if z >= 0 else math.hypot(x, y)
        assert on == pytest.approx(rc, abs=0.5)


def test_the_mouth_is_closed(built):
    m = built["corridor"]["mouth"]
    assert m["closed"]
    assert m["point_count"] == len(m["points"])
    assert m["point_count"] % 2 == 0


def test_the_joint_is_not_flat(built):
    """A curved dome and a straight tunnel do not meet in a plane."""
    m = built["corridor"]["mouth"]
    assert m["step_mm"] > 1.0
    assert m["max_reach_mm"] > m["min_reach_mm"]


def test_a_bigger_dome_is_flatter_where_the_corridor_lands():
    """The same tunnel on a larger sphere leaves a smaller step."""
    steps = []
    for name in ("D6", "D8", "D10", "D12"):
        d = model.build(config.load(name), weave_mode="layered", corridor_spec={})
        steps.append(d["corridor"]["mouth"]["step_mm"])
    assert steps == sorted(steps, reverse=True)


# --- fitting through the doorway ------------------------------------------
def test_a_corridor_cannot_be_taller_than_the_opening_allows(built):
    t = built["corridor"]["through_doorway"]
    if t["fits"]:
        assert built["corridor"]["height_mm"] <= t["available_height_mm"]


def test_the_bare_reference_dome_will_not_take_a_walking_corridor():
    """D6 bare admits a person on all fours, so it admits a corridor the same way.

    This is the same result the doorway and entrance work already found,
    arrived at from the other end -- and it is why M and L have no corridor
    without a skirt.
    """
    d6 = model.build(config.load("D6", skirt_height=0.0), corridor_spec={})
    assert not d6["corridor"]["through_doorway"]["fits"]
    tallest = corridor.tallest_that_fits(d6, corridor.DEFAULT_WIDTH_MM)
    assert tallest["tallest_mm"] < corridor.DEFAULT_HEIGHT_MM


def test_a_skirt_is_what_lets_the_corridor_in():
    bare = model.build(config.load("D6", skirt_height=0.0), corridor_spec={})
    tall = model.build(config.load("D6", skirt_height=1200.0), corridor_spec={})
    assert not bare["corridor"]["through_doorway"]["fits"]
    assert tall["corridor"]["through_doorway"]["fits"]


def test_the_biggest_dome_takes_it_bare():
    d10 = model.build(config.load("D10"), corridor_spec={})
    assert d10["corridor"]["through_doorway"]["fits"]


# --- what gets through ----------------------------------------------------
def test_the_default_corridor_admits_what_the_doorway_is_sized_for():
    """Both default to the "carry" silhouette; a corridor that fails it is a trap."""
    assert "carry" in corridor.admits(
        corridor.DEFAULT_WIDTH_MM, corridor.DEFAULT_HEIGHT_MM
    )


def test_the_semicircular_roof_pinches_the_head():
    """900 x 1900 passes shoulders and fails heads -- which is why 1950 is default."""
    assert "carry" not in corridor.admits(900.0, 1900.0)
    assert "carry" in corridor.admits(900.0, 1950.0)


def test_a_bigger_tunnel_admits_at_least_as_much():
    small = set(corridor.admits(800.0, 1800.0))
    big = set(corridor.admits(1200.0, 2300.0))
    assert small <= big


def test_quantities_scale_with_length():
    d = model.build(config.load("D10"), weave_mode="layered")
    short = corridor.place(d, length=2000.0)
    long_ = corridor.place(d, length=6000.0)
    assert long_["cover_m2"] > short["cover_m2"]
    assert long_["hoop_count"] > short["hoop_count"]
    assert long_["floor_m2"] == pytest.approx(3.0 * short["floor_m2"], rel=1e-6)


def test_a_variant_with_no_doorway_has_nothing_to_attach_to():
    d3 = model.build(config.load("D3"), corridor_spec={})
    assert d3["corridor"]["present"] is False
