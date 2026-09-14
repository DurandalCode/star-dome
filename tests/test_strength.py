"""Independent arithmetic and regressions for diagnostic calculation methods."""
from dataclasses import replace
import json
import math

import pytest

from stardome import config, cover, loads, material, model, span, strength

VARIANTS = ["D3", "D4", "D6", "D8", "D10", "D12"]

@pytest.fixture(scope="module")
def built():
    return {n: model.build(config.load(n), weave_mode="woven", include_polylines=True)
            for n in VARIANTS}

@pytest.fixture(scope="module")
def stock():
    return material.load()

@pytest.fixture(scope="module")
def cfg():
    return loads.load()

@pytest.fixture(scope="module")
def verdicts(built, stock, cfg):
    return {n: strength.analyse(d, stock, cfg) for n, d in built.items()}

@pytest.mark.parametrize("name", VARIANTS)
def test_reports_never_promote_scenarios_to_operating_limits(verdicts, name):
    v = verdicts[name]
    assert v["schema"] == "star_dome_strength/2"
    assert v["status"] == "screening_only"
    assert v["operational_limit_ms"] is None
    assert "band_ms" not in v
    assert v["pressure_cases"] == (-.3, .2)
    assert v["wind_directions_deg"] == tuple(float(a) for a in range(0, 360, 18))
    json.dumps(v, allow_nan=False)
    for p in v["paths"].values():
        assert "limit_ms" not in p
        assert p["binding_check"] in strength.CHECKS
        assert p["threshold_binding_check"] in strength.CHECKS
        if p["sag_ratio"] > strength.DEFLECTION_VOID:
            assert not p["linear_theory_holds"]
            assert p["status"] == "outside_linear_theory"

@pytest.mark.parametrize("name", VARIANTS)
def test_initial_curvature_stress_and_modulus_threshold(verdicts, built, stock, name):
    meta, r = built[name]["meta"], verdicts[name]["residual"]
    strain = meta["rod_diameter"] / (2*meta["dome_radius"])
    assert r["strain"] == pytest.approx(strain)
    assert r["stress_mpa"] == pytest.approx(strain*stock.modulus_mpa)
    assert r["critical_modulus_mpa"]*strain == pytest.approx(r["allowable_mpa"])

@pytest.mark.parametrize("holds", span.HOLDS)
def test_every_live_span_is_screened_and_area_is_conserved(built, stock, cfg, holds):
    data = built["D6"]
    actual = strength.unit_demands(data, stock, cfg, holds)["per_span"]
    expected = span.spans(data, holds)["per_rod"]
    assert len(actual) == sum(map(len, expected.values()))
    for name, spans in expected.items():
        for i, s in enumerate(spans):
            assert actual[f"{name}:{i}"]["span_mm"] == s["length_mm"]
    area = sum(s["tributary_area_mm2"] for s in actual.values())
    assert area == pytest.approx(loads.tributary(data)["dome_area_mm2"], abs=.01)
    assert area/1e6 == pytest.approx(cover.areas(data)["dome_m2"], rel=.002)


def test_geometry_cache_cannot_reuse_a_name_after_dimensions_change(built):
    old = strength._strips(built["D6"])
    changed = model.build(replace(config.load("D6"), diameter=8000),
                          weave_mode="woven", include_polylines=True)
    warm = strength._strips(changed)
    strength._STRIP_CACHE.clear()
    cold = strength._strips(changed)
    assert warm == cold
    assert sum(s["area_mm2"] for s in warm.values()) > 1.7*sum(s["area_mm2"] for s in old.values())
    assert warm["U1:0"]["length_mm"] > old["U1:0"]["length_mm"]


def test_gravity_and_signed_axial_actions_against_hand_calculation(stock, cfg):
    # Synthetic one-metre span: force result independent of cover partition.
    d, length, width, radius, speed = 10., 1000., 200., 3000., 20.
    area, inertia, section = math.pi*d*d/4, math.pi*d**4/64, math.pi*d**3/32
    rod_w = area*1e-9*stock.density_kg_m3*cfg.gravity_m_s2
    fabric_w = cfg.fabric_g_m2*1e-9*width*cfg.gravity_m_s2
    demand = dict(span_mm=length, strip_mm=width, cp_inward=.4, cp_outward=1.4,
                  gravity_n_per_mm=rod_w+fabric_w, area_mm2=area,
                  second_moment_mm4=inertia, section_modulus_mm3=section,
                  euler_n=math.pi**2*stock.modulus_mpa*inertia/length**2)
    unit = dict(radius_mm=radius, residual_stress_mpa=stock.modulus_mpa*d/(2*radius))
    q = .5*cfg.air_density_kg_m3*speed**2
    mg = (rod_w+fabric_w)*length**2/8
    mw = q*1.4e-6*width*length**2/8
    nc, nt = q*.4e-6*radius*width/2, q*1.4e-6*radius*width/2
    for path in strength.LOAD_PATHS:
        s = strength.member_state(demand, unit, stock, cfg, speed, path)
        assert s["gravity_moment_nmm"] == pytest.approx(mg)
        assert s["sustained_tension_mpa"] == pytest.approx(unit["residual_stress_mpa"]+mg/section)
        assert s["wind_moment_nmm"] == pytest.approx(0 if path == "membrane" else mw)
        assert s["axial_compression_n"] == pytest.approx(0 if path == "beam" else nc)
        assert s["axial_tension_n"] == pytest.approx(0 if path == "beam" else nt)
        u = strength.utilisations(demand, unit, stock, cfg, speed, path)
        assert u["buckling"] == pytest.approx(0 if path == "beam" else nc/demand["euler_n"])
    suction = {**demand, "cp_inward": 0}
    assert strength.utilisations(suction, unit, stock, cfg, speed, "membrane")["buckling"] == 0


def test_fabric_weight_is_included_even_in_membrane_scenario(built, stock, cfg):
    data = built["D6"]
    normal = strength.unit_demands(data, stock, cfg)
    heavy = strength.unit_demands(data, stock, replace(cfg, fabric_g_m2=500))
    for key, d in normal["per_span"].items():
        h = heavy["per_span"][key]
        assert h["fabric_weight_n_per_mm"] == 2*d["fabric_weight_n_per_mm"]
        s = strength.member_state(d, normal, stock, cfg, 0, "membrane")
        assert s["gravity_moment_nmm"] > 0
        assert s["wind_moment_nmm"] == s["axial_compression_n"] == 0
    v = strength.analyse(data, stock, cfg, speed_ms=0)
    for p in v["paths"].values():
        assert p["threshold_ms"] == 0
        assert p["threshold_status"] == "already_exceeded_at_zero_wind"
        assert p["threshold_binding_check"] == "sustained_tension"


def test_bisection_crossing_calm_and_no_crossing_are_distinct():
    a, b = .3, .004
    assert strength.limiting_speed(lambda v: a+b*v*v) == pytest.approx(math.sqrt((1-a)/b), abs=1e-6)
    assert strength.limiting_speed(lambda v: 1.5) == 0
    assert math.isinf(strength.limiting_speed(lambda v: .5))


def test_anchor_demand_includes_skirt_moment_and_both_pressure_cases(built, cfg):
    data = built["D4"]
    demand = strength.anchor_demand(data, cfg)
    assert len(demand["cases_per_pa"]) == 2*len(strength.DIRECTION_SAMPLES)
    r = loads.resultants(data, 20, cfg)
    q = loads.velocity_pressure(20, cfg)
    assert demand["uplift_n_per_pa"]*q > 1.2*r["lift_n"]/cfg.anchor_count
    assert demand["uplift_case"]["cp_internal"] == .2
    u20 = strength.anchor_utilisations(data, cfg, 20, demand=demand)
    u10 = strength.anchor_utilisations(data, cfg, 10, demand=demand)
    assert u20["anchor_uplift"] == 4*u10["anchor_uplift"]
    with pytest.raises(ValueError, match="count"):
        strength.anchor_demand(data, replace(cfg, anchor_count=9))


def test_cli_uses_requested_wind_and_modulus_in_json(tmp_path):
    from stardome import cli
    assert cli.main(["strength", "S", "--wind", "7", "--modulus", "60000",
                     "--json", "--out", str(tmp_path)]) == 0
    v = json.loads((tmp_path / "S" / "strength.json").read_text())
    assert v["modulus_mpa"] == 60000
    assert v["inputs"]["material"]["modulus_mpa"] == 60000
    assert v["inputs"]["loads"]["cp_internal_closed_positive"] == .2
    assert len(v["geometry_sha256"]) == 64
    assert v["residual"]["stress_mpa"] == pytest.approx(120)
    assert not v["residual"]["passes"]
    assert all(p["at_speed_ms"] == 7 for p in v["paths"].values())
    assert v["operational_limit_ms"] is None
