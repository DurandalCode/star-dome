"""The verdict, and the two bounds it sits between.

This is the first module in the project that turns a geometry into a
pass or a fail, so the tests here are less about arithmetic than about the
shape of the argument staying intact:

- the band must keep its sense -- the membrane reading cannot come out below
  the beam one, or the two bounds have swapped and the report is lying about
  which way the uncertainty runs;
- the check that has no wind in it must stay separated from the ones that do,
  because "fails standing in a calm" and "fails at 8 m/s" are different
  sentences;
- and the answer must keep agreeing with `span.py`, which computed the spans
  everything here is built on, long before there was a material.

One test is a full hand calculation of the governing number, written out
longhand. It is here because a limiting wind speed is the kind of result a
reader has no independent feel for, and the repository's standard is that two
routes to a number are better evidence than one.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, loads, material, model, span, strength

VARIANTS = ["D3", "D4", "D6", "D8", "D10", "D12"]


@pytest.fixture(scope="module")
def built():
    return {
        name: model.build(
            config.load(name), weave_mode="woven", include_polylines=True
        )
        for name in VARIANTS
    }


@pytest.fixture(scope="module")
def stock():
    return material.load()


@pytest.fixture(scope="module")
def cfg():
    return loads.load()


@pytest.fixture(scope="module")
def verdicts(built, stock, cfg):
    return {n: strength.analyse(d, stock, cfg) for n, d in built.items()}


# --- the check with no wind in it -------------------------------------------


@pytest.mark.parametrize("name", VARIANTS)
def test_the_residual_is_the_strain_span_computes_times_the_modulus(
    built, stock, verdicts, name
):
    """`span.bend_strain` is geometry and has been tested since before there
    was a material; this is the same quantity in megapascals. `docs/span.md`
    quotes the strain and `docs/strength.md` quotes the stress, so the two
    must never drift."""
    v = verdicts[name]
    meta = built[name]["meta"]
    assert v["residual"]["strain"] == pytest.approx(
        span.bend_strain(meta["rod_diameter"], meta["dome_radius"]), abs=1e-9
    )
    assert v["residual"]["stress_mpa"] == pytest.approx(
        stock.modulus_mpa * v["residual"]["strain"], abs=0.01
    )


def test_the_rod_is_worked_hardest_on_the_smallest_dome(verdicts):
    """The finding that inverts the project's own intuition.

    Everything written here so far treats D12 as the risky end of the range
    and D3 as the safe one. On the permanent stress from being bent to shape
    it is exactly the other way round, and for a dull reason: rod diameter is
    quantised at 8, 10 and 12 mm while the radius halves, so `d/2R` is worst
    where the dome is smallest. If this ordering ever reverses, either the
    variants changed or the check did.
    """
    used = [verdicts[n]["residual"]["utilisation"] for n in VARIANTS]
    assert used == sorted(used, reverse=True), dict(zip(VARIANTS, used))


def test_the_creep_check_does_not_move_with_the_wind(built, stock, cfg):
    """A bow either survives being bent or it does not, and no wind speed
    makes that better. Keeping it out of the limiting-speed search is what
    lets the report say "fails in a calm" rather than "limit 0 m/s"."""
    data = built["D3"]
    calm = strength.analyse(data, stock, cfg)["residual"]["utilisation"]
    blowing = strength.analyse(data, stock, cfg, door="open")["residual"]["utilisation"]
    assert calm == blowing


# --- the band keeps its sense -----------------------------------------------


@pytest.mark.parametrize("name", ["D4", "D6", "D8", "D10", "D12"])
def test_the_membrane_reading_is_the_optimistic_end_of_the_band(verdicts, name):
    """The two readings bound how a bow carries the wind: all of it in
    bending, or all of it in arch action. Bending is far the harsher, so the
    membrane limit must be the higher of the two. Swapped, the report would
    be quoting the band backwards."""
    p = verdicts[name]["paths"]
    assert p["membrane"]["limit_ms"] >= p["beam"]["limit_ms"], name


@pytest.mark.parametrize("name", ["D4", "D6", "D8", "D10", "D12"])
def test_the_envelope_is_not_more_optimistic_than_either_bound(verdicts, name):
    """The envelope applies both actions at once and so must be the most
    conservative of the three. If it ever came out above one of its own
    bounds, the load paths are not being combined but replaced."""
    p = verdicts[name]["paths"]
    assert p["envelope"]["limit_ms"] <= p["beam"]["limit_ms"] + 1e-9, name
    assert p["envelope"]["limit_ms"] <= p["membrane"]["limit_ms"] + 1e-9, name


def test_the_band_is_wide_enough_to_be_the_finding(verdicts):
    """The reason PR 1 refuses to quote a single speed. If closed forms ever
    narrowed this to a few per cent the frame solver would not be worth
    building -- so the width is asserted, not hoped for."""
    p = verdicts["D6"]["paths"]
    assert p["membrane"]["limit_ms"] > 1.5 * p["beam"]["limit_ms"]


def test_a_bigger_dome_stands_less_wind(verdicts):
    """Same topology, same shape, more of it: the span grows with the radius
    and the rod does not keep up, which is the whole of `docs/span.md`
    restated in metres per second."""
    limits = [verdicts[n]["paths"]["membrane"]["limit_ms"]
              for n in ["D4", "D6", "D8", "D10", "D12"]]
    assert limits == sorted(limits, reverse=True), limits


# --- it still agrees with the module the spans came from --------------------


def test_clamping_the_free_crossings_swaps_the_family_that_binds(built, stock, cfg):
    """`span.md` says the weak family swaps when the thirty unlashed crossings
    are clamped: U and L at 60 degrees become G at 36. If the strength module
    is reading spans correctly, the rod it names must swap families too, and
    the span it binds at must be the one `span.spans` reports."""
    data = built["D6"]
    seen = {}
    for holds in span.HOLDS:
        verdict = strength.analyse(data, stock, cfg, holds)
        rod = verdict["paths"]["membrane"]["binding_rod"]
        unit = strength.unit_demands(data, stock, cfg, holds)
        seen[holds] = (unit["per_rod"][rod]["family"],
                       unit["per_rod"][rod]["span_mm"])
        assert unit["per_rod"][rod]["span_mm"] == pytest.approx(
            span.spans(data, holds)["worst"]["length_mm"], abs=1e-6
        )
    assert seen["lashed"][0] in ("U", "L")
    assert seen["contact"][0] == "G"
    assert seen["lashed"][1] > seen["contact"][1]


def test_clamping_the_free_crossings_buys_wind(built, stock, cfg):
    """`span.py` prices the thirty clamps at 5/3 in span and 2.78x in rod
    diameter. This is the same question in the units a field rule is written
    in, and it is the first time milestone 5 has had one."""
    data = built["D6"]
    loose = strength.analyse(data, stock, cfg, "lashed")["paths"]["membrane"]
    tight = strength.analyse(data, stock, cfg, "contact")["paths"]["membrane"]
    assert tight["limit_ms"] > loose["limit_ms"]


def test_shutting_the_door_buys_wind_and_costs_nothing(built, stock, cfg):
    """The only mitigation in this whole calculation that needs no part, no
    plastic and no decision -- and the only one nobody had written down."""
    data = built["D6"]
    shut = strength.analyse(data, stock, cfg, door="shut")["paths"]["membrane"]
    opened = strength.analyse(data, stock, cfg, door="open")["paths"]["membrane"]
    assert shut["limit_ms"] > opened["limit_ms"]


# --- the machinery ----------------------------------------------------------


def test_bisection_finds_what_the_closed_form_would(cfg):
    """Every check here happens to be a quadratic in the speed, so the limit
    could be solved in one line. It is bisected instead, because a moment
    magnifier or a compression-only contact would stop it being quadratic and
    the caller should not have to notice. This pins the two together while
    they still agree."""
    # u(v) = (a + b v^2) / 1, solved at u = 1.
    a, b = 0.3, 0.004
    closed = math.sqrt((1.0 - a) / b)
    found = strength.limiting_speed(lambda v: a + b * v * v)
    assert found == pytest.approx(closed, abs=1e-4)


def test_a_structure_already_over_at_zero_wind_reports_zero_not_a_failure(cfg):
    """A real answer, and one this project needs: D3 is over on the bend
    alone, and "0 m/s" says so more usefully than an exception."""
    assert strength.limiting_speed(lambda v: 1.5) == 0.0


def test_the_sag_is_reported_rather_than_scored(verdicts):
    """Deflection is a validity gate here, not a strength check, and the
    reason is in the number: under the beam reading a D6 bow sags about 2.5%
    of its span in a dead calm. Scored as a limit that makes the beam reading
    fail at zero wind, which says nothing. Read as what it is, it says the
    beam reading is not conservative but wrong, because a Star Dome visibly
    does not do that when you stand it up."""
    p = verdicts["D6"]["paths"]["beam"]
    assert p["sag_ratio"] > 0.0
    assert "deflection" not in strength.MEMBER_CHECKS
    assert p["linear_theory_holds"] in (True, False)


def test_the_binding_check_is_one_the_module_admits_to(verdicts):
    for name in VARIANTS:
        for path in strength.LOAD_PATHS:
            assert verdicts[name]["paths"][path]["binding_check"] in strength.CHECKS


# --- one number, done twice -------------------------------------------------


def test_the_governing_limit_survives_being_worked_out_by_hand(built, stock, cfg):
    """The whole calculation for D6, written out longhand and compared.

    A limiting wind speed is a number a reader has no independent feel for, so
    this walks the governing check from first principles -- velocity pressure,
    net coefficient, membrane thrust over the tributary strip, Euler load on
    the unsupported span -- and asserts the module lands on the same place.

    At the limit the governing utilisation must be exactly 1.0 by definition,
    which is what makes this checkable at all.
    """
    data = built["D6"]
    verdict = strength.analyse(data, stock, cfg, "lashed", "shut")
    path = verdict["paths"]["membrane"]
    assert path["binding_check"] == "buckling"

    name = path["binding_rod"]
    demand = strength.unit_demands(data, stock, cfg, "lashed", "shut")["per_rod"][name]
    speed = path["limit_ms"]

    # By hand, in newtons and millimetres.
    q = 0.5 * cfg.air_density_kg_m3 * speed ** 2          # Pa
    pressure = q * demand["cp_net"] * 1e-6                 # N/mm^2
    radius = data["meta"]["dome_radius"]
    thrust = pressure * radius * demand["strip_mm"] / 2.0  # N, n = pR/2 per width
    second = math.pi * data["meta"]["rod_diameter"] ** 4 / 64.0
    euler = math.pi ** 2 * stock.modulus_mpa * second / demand["span_mm"] ** 2

    assert thrust / euler == pytest.approx(1.0, abs=2e-3), (thrust, euler)
