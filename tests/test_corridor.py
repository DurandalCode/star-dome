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
    h = built["corridor"]["rib"]
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


# --- the timber portal ----------------------------------------------------
def test_the_portal_opening_is_a_trapezoid_not_a_rectangle():
    """The knee braces cut both top corners, and that is clear opening lost."""
    s = corridor.portal_section(1800.0, 2100.0, 300.0)
    assert s[0] == (0.0, 900.0)
    assert s[1] == (1800.0, 900.0)
    assert s[-1] == (2100.0, 600.0)


def test_a_brace_wider_than_the_opening_is_refused():
    with pytest.raises(ValueError):
        corridor.portal_section(500.0, 2100.0, 300.0)


def test_the_portal_cut_list_adds_up():
    f = corridor.portal_frame(1800.0, 2100.0, 300.0)
    total = sum(m["count"] * m["length_mm"] for m in f["members"])
    assert f["board_length_mm"] == pytest.approx(total, abs=0.2)
    assert f["overall_width_mm"] > f["clear_width_mm"]
    assert f["overall_height_mm"] > f["clear_height_mm"]


def test_the_brace_is_the_hypotenuse_of_its_own_corner():
    f = corridor.portal_frame(1800.0, 2100.0, 300.0)
    brace = next(m for m in f["members"] if m["name"] == "knee brace")
    assert brace["length_mm"] == pytest.approx(300.0 * math.sqrt(2.0), abs=0.1)


def test_the_portal_is_wider_where_it_matters():
    """Full width up to the braces is the whole point of a square frame.

    Not that it admits more silhouettes -- at 2100 mm both kinds pass every
    template, because the widest of them is only 800 mm across. The portal's
    gain is room: at head height it is more than twice as wide, and that is
    two-way traffic and furniture rather than one more person shape.
    """
    hoop = corridor.section(900.0, 2100.0)
    portal = corridor.portal_section(1800.0, 2100.0, 300.0)
    at_head = 1800.0
    assert corridor._clear_half_width(portal, at_head) > (
        2.0 * corridor._clear_half_width(hoop, at_head)
    )


def test_the_portal_is_worse_at_getting_through_the_lancet():
    """Its advantage inside is its disadvantage at the door.

    A bay narrows toward its head, and a portal demands full width right up to
    the braces -- where the hoop has already curved in.
    """
    d10 = model.build(config.load("D10"), weave_mode="layered")
    hoop = corridor.widest_that_fits(d10, 1950.0, 25.0, "hoop")["widest_mm"]
    portal = corridor.widest_that_fits(d10, 1950.0, 25.0, "portal")["widest_mm"]
    assert portal < hoop


def test_a_portal_wider_than_its_door_is_reported_as_a_bottleneck_not_a_failure():
    d10 = model.build(config.load("D10"), weave_mode="layered")
    c = corridor.place(d10, width=1800.0, height=2100.0, kind="portal")
    assert not c["through_doorway"]["fits"]
    assert c["bottleneck"]["at"] == "the dome's doorway"
    # And a person is still unaffected: the doorway admits them anyway.
    assert "carry" in c["bottleneck"]["doorway_admits"]


def test_both_kinds_measure_skin_and_floor_the_same_way():
    d10 = model.build(config.load("D10"), weave_mode="layered")
    for kind, w, h in (("hoop", 900.0, 1950.0), ("portal", 1800.0, 2100.0)):
        c = corridor.place(d10, width=w, height=h, kind=kind)
        assert c["floor_m2"] == pytest.approx(w * c["length_mm"] / 1e6, rel=1e-6)
        assert c["cover_m2"] > 0
        assert c["kind"] == kind


def test_an_unknown_kind_is_refused():
    with pytest.raises(ValueError):
        corridor.section_for("geodesic", 900.0, 1950.0)


def test_the_portal_draws_as_boards():
    d10 = model.build(config.load("D10"), weave_mode="layered")
    c = corridor.place(
        d10, width=1800.0, height=2100.0, pitch=1200.0,
        kind="portal", include_geometry=True,
    )
    drawing = c["drawing"]
    assert drawing["kind"] == "portal"
    assert drawing["frames"] and not drawing["hoops"]
    # Five members, eight corners each.
    assert len(drawing["frames"][0]["vertices"]) == 40
    assert len(drawing["frames"][0]["faces"]) == 30
