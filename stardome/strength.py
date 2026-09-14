"""Traceable strength screening, not a prediction of operational wind capacity.

Wind is tried as beam bending, ideal shell axial action, and their algebraic
combination. Gravity is a separate beam-bending action in all three scenarios.
Neither scenario bounds a flexible, jointed dome. See docs/strength.md and
ADR 0028 for equations, assumptions and the checks still missing.
"""

from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from dataclasses import asdict

from . import geometry, loads as loads_mod, material as material_mod, reactions, span, vec

CHECKS = ("bend_creep", "sustained_tension", "combined_tension",
          "combined_compression", "buckling", "anchor_uplift", "anchor_shear")
MEMBER_CHECKS = CHECKS[:-2]
LOAD_PATHS = ("beam", "membrane", "envelope")
DEFLECTION_VOID = 0.10  # diagnostic threshold, not a serviceability allowance
# Cuts destroy five-fold symmetry. A sampled full circle is still not a
# certified continuous directional maximum; the resolution is reported.
DIRECTION_SAMPLES = tuple(float(a) for a in range(0, 360, 18))
REFERENCE_SPEED_MS = 20.0  # avoid amplifying milli-newton output rounding at 1 m/s
_STRIP_CACHE: dict = {}


def _strips(data: dict, holds: str = "lashed") -> dict:
    """Partition cover onto live spans, cached by the complete JSON geometry.

    Boundary samples divide area equally between the adjacent live spans.
    The nearest-point discretisation is approximate; total area is conserved.
    No pressure or material property is stored in this geometry-only cache.
    """
    encoded = json.dumps(data, sort_keys=True, allow_nan=False,
                         separators=(",", ":")).encode()
    key = (hashlib.sha256(encoded).hexdigest(), holds,
           loads_mod.LOAD_MERIDIANS, loads_mod.LOAD_PARALLELS)
    if key in _STRIP_CACHE:
        return _STRIP_CACHE[key]
    facets = [
        {"centroid": c, "area_mm2": a, "normal": n,
         "force_n": [0.0, 0.0, 0.0], "skirt": sk}
        for c, a, n, sk in loads_mod._facets(
            data, loads_mod.LOAD_MERIDIANS, loads_mod.LOAD_PARALLELS)
    ]
    spread = loads_mod.scatter(data, facets)
    spans = span.spans(data, holds)["per_rod"]
    out = {}
    for rod in data["rods"]:
        name = rod["name"]
        bow = geometry.Bow(**{k: rod[k] for k in (
            "name", "family", "number", "azimuth_deg", "tilt_deg", "foot_a", "foot_b", "layer")})
        local = []
        for i, s in enumerate(spans[name]):
            item = {"rod": name, "family": rod["family"], **s,
                    "area_mm2": 0.0, "radials": []}
            out[f"{name}:{i}"] = item
            local.append(item)
        for index, facet in spread["by_rod"][name]:
            t = bow.t_of(rod["points"][index])
            if t > 360.0 - 1e-6:
                t = 0.0
            candidates = [s for s in local
                          if s["t_lo_deg"] - 1e-5 <= t <= s["t_hi_deg"] + 1e-5]
            if not candidates:
                raise ValueError(f"cover assigned outside a live span on {name} at {t}")
            radial = vec.unit(facet["centroid"])
            for s in candidates:
                s["area_mm2"] += facet["area_mm2"] / len(candidates)
                s["radials"].append(radial)
    if len(_STRIP_CACHE) >= 8:
        del _STRIP_CACHE[next(iter(_STRIP_CACHE))]
    _STRIP_CACHE[key] = out
    return out


def _coefficients(radials, loads, door):
    """Keep pressure and suction separate; suction does not buckle a strut."""
    inward = outward = 0.0
    for a in DIRECTION_SAMPLES:
        dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
        for rx, ry, _rz in radials:
            t = math.degrees(math.acos(max(-1.0, min(1.0, -(rx*dx + ry*dy)))))
            external = loads_mod.shape_coefficient(t, loads)
            for cpi in loads_mod.pressure_cases(door, loads):
                net = external - cpi
                inward = max(inward, net)
                outward = max(outward, -net)
    return inward, outward


def unit_demands(data: dict, material, loads, holds: str = "lashed",
                 door: str = "shut") -> dict:
    meta = data["meta"]
    diameter, radius = meta["rod_diameter"], meta["dome_radius"]
    if not all(math.isfinite(v) and v > 0 for v in (diameter, radius)):
        raise ValueError("rod diameter and dome radius must be positive")
    ei = material.modulus_mpa * material.second_moment(diameter)
    rod_weight = material.linear_mass(diameter) * loads.gravity_m_s2 / 1000.0
    out = {}
    for key, strip in _strips(data, holds).items():
        length = strip["length_mm"]
        width = strip["area_mm2"] / length
        inward, outward = _coefficients(strip["radials"], loads, door)
        # g/m2 -> kg/mm2, multiplied by tributary width -> kg/mm.
        fabric_weight = loads.fabric_g_m2 * 1e-9 * width * loads.gravity_m_s2
        out[key] = {
            "rod": strip["rod"], "family": strip["family"],
            "t_lo_deg": strip["t_lo_deg"], "t_hi_deg": strip["t_hi_deg"],
            "span_mm": length, "strip_mm": width,
            "area_mm2": material.area(diameter),
            "tributary_area_mm2": strip["area_mm2"],
            "cp_inward": inward, "cp_outward": outward,
            "gravity_n_per_mm": rod_weight + fabric_weight,
            "rod_weight_n_per_mm": rod_weight, "fabric_weight_n_per_mm": fabric_weight,
            "euler_n": math.pi**2 * ei / length**2,
            "second_moment_mm4": material.second_moment(diameter),
            "section_modulus_mm3": material.section_modulus(diameter),
        }
    return {
        "holds": holds, "door": door, "radius_mm": radius,
        "rod_diameter_mm": diameter,
        "residual_stress_mpa": material.bend_stress(diameter, radius),
        "per_span": out,
    }


def member_state(demand: dict, unit: dict, material, loads,
                 speed_ms: float, path: str = "envelope") -> dict:
    if path not in LOAD_PATHS:
        raise ValueError(f"unknown load path {path!r}")
    q = loads_mod.velocity_pressure(speed_ms, loads)
    a, width = demand["span_mm"], demand["strip_mm"]
    gravity = demand["gravity_n_per_mm"]
    wind = q * max(demand["cp_inward"], demand["cp_outward"]) * 1e-6 * width
    bends = path in ("beam", "envelope")
    thrusts = path in ("membrane", "envelope")
    mg = gravity * a*a / 8.0
    mw = wind * a*a / 8.0 if bends else 0.0
    axial_per_cp = q * 1e-6 * unit["radius_mm"] * width / 2.0 if thrusts else 0.0
    nc = axial_per_cp * demand["cp_inward"]
    nt = axial_per_cp * demand["cp_outward"]
    section = demand["section_modulus_mm3"]
    residual = unit["residual_stress_mpa"]
    sustained = residual + mg / section
    # Each sign is a separate envelope. Opposite axial forces are not added
    # together. No stabilising relief from the opposite fibre is credited.
    return {
        "gravity_n_per_mm": gravity, "wind_n_per_mm": wind,
        "gravity_moment_nmm": mg, "wind_moment_nmm": mw,
        "axial_compression_n": nc, "axial_tension_n": nt,
        "residual_mpa": residual, "sustained_tension_mpa": sustained,
        "tension_mpa": sustained + mw / section + nt / demand["area_mm2"],
        "compression_mpa": sustained + mw / section + nc / demand["area_mm2"],
        "deflection_mm": 5*(gravity + (wind if bends else 0))*a**4 /
                         (384*material.modulus_mpa*demand["second_moment_mm4"]),
    }


def utilisations(demand: dict, unit: dict, material, loads,
                 speed_ms: float, path: str = "envelope") -> dict:
    s = member_state(demand, unit, material, loads, speed_ms, path)
    return {
        "bend_creep": s["residual_mpa"] / material.allowable("sustained", "tension"),
        "sustained_tension": s["sustained_tension_mpa"] / material.allowable("sustained", "tension"),
        "combined_tension": s["tension_mpa"] / material.allowable("short_term", "tension"),
        "combined_compression": s["compression_mpa"] / material.allowable("short_term", "compression"),
        "buckling": s["axial_compression_n"] / demand["euler_n"],
    }


@lru_cache(maxsize=32)
def _anchor_cases(anchors_json, data_json, loads, door):
    data, anchors = json.loads(data_json), json.loads(anchors_json)
    if loads.anchor_count != len(anchors):
        raise ValueError("configured anchor count differs from the model's base points")
    cases = []
    q = loads_mod.velocity_pressure(REFERENCE_SPEED_MS, loads)
    # Integrate each actual direction. This remains correct if the cover
    # later becomes asymmetric; F and M must come from the same pressure case.
    for cpi in loads_mod.pressure_cases(door, loads):
        for azimuth in DIRECTION_SAMPLES:
            wind = loads_mod.resultants(data, REFERENCE_SPEED_MS, loads,
                azimuth_deg=azimuth, door=door, cp_internal=cpi)
            r = reactions.distribute(anchors, [v/q for v in wind["force_n"]],
                                     [v/q for v in wind["moment_nmm"]])
            cases.append({"azimuth_deg": azimuth, "cp_internal": cpi, **r})
    return tuple(cases)


def anchor_demand(data: dict, loads, door: str = "shut") -> dict:
    cases = _anchor_cases(json.dumps(data["base_nodes"], sort_keys=True),
                          json.dumps(data, sort_keys=True, allow_nan=False), loads, door)
    up = max(cases, key=lambda c: c["max_uplift_n"])
    shear = max(cases, key=lambda c: c["max_shear_n"])
    return {
        "model": "rigid_base_equal_bilateral_springs", "status": "screening_only",
        "uplift_n_per_pa": up["max_uplift_n"],
        "shear_n_per_pa": shear["max_shear_n"],
        "uplift_case": {k: up[k] for k in ("azimuth_deg", "cp_internal")},
        "shear_case": {k: shear[k] for k in ("azimuth_deg", "cp_internal")},
        "cases_per_pa": cases,
        "note": "Wind only, no weight credited against uplift. Base rigidity, equal soil "
                "stiffness, pull-out, bearing and combined shear/uplift remain unverified.",
    }


def anchor_utilisations(data, loads, speed_ms, door="shut", demand=None):
    demand = demand if demand is not None else anchor_demand(data, loads, door)
    q = loads_mod.velocity_pressure(speed_ms, loads)
    return {
        "anchor_uplift": demand["uplift_n_per_pa"]*q / loads.anchor_capacity_n,
        "anchor_shear": demand["shear_n_per_pa"]*q / loads.anchor_shear_capacity_n,
    }


def limiting_speed(evaluate, lo=0.0, hi=120.0, tol=1e-6):
    """First threshold crossing for these monotone algebraic scenarios.

    Infinity means no crossing within the search range, not infinite capacity.
    The report serialises this as null with an explicit range status.
    """
    if evaluate(lo) >= 1.0:
        return 0.0
    if evaluate(hi) < 1.0:
        return math.inf
    while hi-lo > tol:
        mid = (lo+hi)/2
        if evaluate(mid) < 1:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2


def analyse(data, material, loads, holds="lashed", door="shut", speed_ms=20.0):
    loads_mod.velocity_pressure(speed_ms, loads)
    unit = unit_demands(data, material, loads, holds, door)
    anchor = anchor_demand(data, loads, door)
    per_span = unit["per_span"]
    if not per_span:
        raise ValueError("no live spans to screen")

    def worst(path, speed):
        candidates = []
        for key, d in per_span.items():
            candidates.extend((value, check, d["rod"], key)
                              for check, value in utilisations(d, unit, material, loads, speed, path).items())
        candidates.extend((value, check, "anchors", "") for check, value in
                          anchor_utilisations(data, loads, speed, door, anchor).items())
        return max(candidates)

    paths = {}
    for path in LOAD_PATHS:
        threshold = limiting_speed(lambda v: worst(path, v)[0])
        value, check, rod, key = worst(path, speed_ms)
        sag, sag_key = max((member_state(d, unit, material, loads, speed_ms, path)["deflection_mm"]
                            / d["span_mm"], key) for key, d in per_span.items())
        at = threshold if math.isfinite(threshold) else 120.0
        threshold_sag = max(member_state(d, unit, material, loads, at, path)["deflection_mm"]
                            / d["span_mm"] for d in per_span.values())
        _, threshold_check, threshold_rod, threshold_key = worst(path, at)
        paths[path] = {
            "threshold_ms": round(threshold, 3) if math.isfinite(threshold) else None,
            "threshold_status": "already_exceeded_at_zero_wind" if threshold == 0 else
                "crossing_found" if math.isfinite(threshold) else "not_reached_through_120_ms",
            "threshold_binding_check": threshold_check,
            "threshold_binding_rod": threshold_rod,
            "threshold_binding_span": threshold_key or None,
            "threshold_linear_theory_holds": threshold_sag <= DEFLECTION_VOID,
            "at_speed_ms": speed_ms, "utilisation": value, "binding_check": check,
            "binding_rod": rod, "binding_span": key or None,
            "sag_ratio": sag, "sag_span": sag_key,
            "linear_theory_holds": sag <= DEFLECTION_VOID,
            "status": "outside_linear_theory" if sag > DEFLECTION_VOID else "screening_only",
        }
    strain = span.bend_strain(unit["rod_diameter_mm"], unit["radius_mm"])
    allowable = material.allowable("sustained", "tension")
    return {
        "schema": "star_dome_strength/2", "variant": data["meta"]["variant"],
        "status": "screening_only", "operational_limit_ms": None,
        "inputs": {"material": asdict(material), "loads": asdict(loads),
                   "pressure_mesh": {"meridians": loads_mod.LOAD_MERIDIANS,
                                     "parallels": loads_mod.LOAD_PARALLELS}},
        "geometry_sha256": hashlib.sha256(json.dumps(data, sort_keys=True,
            allow_nan=False, separators=(",", ":")).encode()).hexdigest(),
        "material": material.name, "material_source": material.source,
        "material_basis": "supplied_properties_not_a_guaranteed_batch_envelope",
        "modulus_mpa": material.modulus_mpa, "holds": holds, "door": door,
        "pressure_cases": loads_mod.pressure_cases(door, loads),
        "wind_directions_deg": DIRECTION_SAMPLES,
        "radius_mm": unit["radius_mm"], "rod_diameter_mm": unit["rod_diameter_mm"],
        "residual": {
            "strain": strain, "stress_mpa": unit["residual_stress_mpa"],
            "allowable_mpa": allowable,
            "utilisation": unit["residual_stress_mpa"]/allowable,
            "passes": unit["residual_stress_mpa"] <= allowable,
            "critical_modulus_mpa": allowable/strain,
            "scope": "initial bend only, for the supplied E and allowable",
        },
        "paths": paths, "span_demands": per_span,
        "anchors": anchor,
        "anchors_at_speed": anchor_utilisations(data, loads, speed_ms, door, anchor),
        "unverified": ["frame stability and geometric nonlinearity", "joint stiffness and strength",
                       "drilled rod sections and splices", "local weave curvature",
                       "soil and bearing capacities",
                       "sustained compression properties", "actual cover and opening pressures",
                       "printed parts, hardware and skirt weight in member checks",
                       "continuous wind-direction maximum"],
        "note": "Independent algebraic scenarios, not capacity bounds. Gravity bending "
                "includes rods and tributary fabric in every scenario. Thresholds are "
                "diagnostics, not operational wind limits or proof of failure of the real frame.",
    }


def format_analysis(data, material, loads, holds="lashed", door="shut", speed_ms=20.0):
    a = analyse(data, material, loads, holds, door, speed_ms)
    r = a["residual"]
    lines = [f"--- {a['variant']} strength screening on {a['material']} (E={a['modulus_mpa']:g} MPa)",
             f"  wind {speed_ms:g} m/s; held at {holds}; door {door}; cpi cases {list(a['pressure_cases'])}",
             "  operational wind limit: UNKNOWN",
             f"  initial bend {r['stress_mpa']:.1f} MPa / {r['allowable_mpa']:.1f} MPa = {r['utilisation']:.3f}",
             f"  E at this bend criterion's threshold: {r['critical_modulus_mpa']/1000:.2f} GPa",
             "  Higher E increases initial bend stress; a minimum E is not a worst-case guarantee.",
             "", "  scenario    utilisation  governing check         location     sag/span"]
    for path, p in a["paths"].items():
        lines.append(f"  {path:11} {p['utilisation']:10.2f}  {p['binding_check']:22} "
                     f"{p['binding_span'] or p['binding_rod']:12} {p['sag_ratio']:.1%}  {p['status']}")
        threshold = "not reached through 120 m/s" if p["threshold_ms"] is None else f"{p['threshold_ms']:.3f} m/s"
        validity = "outside linear theory" if not p["threshold_linear_theory_holds"] else "algebraic screening only"
        lines.append(f"    criterion crossing: {threshold} ({p['threshold_status']}; {p['threshold_binding_check']}; {validity})")
    lines += ["", "  anchors: rigid base / equal stiffness, with force AND moment; wind only",
              f"    uplift {a['anchors_at_speed']['anchor_uplift']:.2f}, shear {a['anchors_at_speed']['anchor_shear']:.2f} of placeholder capacities",
              "", "  " + a["note"], "  Unverified: " + "; ".join(a["unverified"])]
    return "\n".join(lines)


def compare(data, material, loads, holds="lashed", speed_ms=20.0):
    """Compare diagnostic utilisation at the same speed, not invented limits."""
    def score(mat, held, door):
        a = analyse(data, mat, loads, held, door, speed_ms)
        return {p: a["paths"][p]["utilisation"] for p in LOAD_PATHS}
    return {
        "speed_ms": speed_ms, "status": "screening_only",
        "holds": {h: score(material, h, "shut") for h in span.HOLDS},
        "door": {d: score(material, holds, d) for d in loads_mod.DOOR_STATES},
        "materials": {name: score(mat, holds, "shut") for name, mat in material_mod.load_all().items()},
    }


def format_comparison(data, material, loads, holds="lashed", speed_ms=20.0):
    c = compare(data, material, loads, holds, speed_ms)
    out = [f"\n  Scenario utilisations at {speed_ms:g} m/s (beam / membrane / envelope):"]
    for group in ("holds", "door", "materials"):
        for name, values in c[group].items():
            out.append(f"    {group}/{name}: " + " / ".join(f"{values[p]:.2f}" for p in LOAD_PATHS))
    return "\n".join(out)
