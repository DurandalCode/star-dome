"""Optional nonlinear cap study. Run: python -m analysis.wind_study --help.

Fixed, pinned bow feet; coincident translating crossings with free rotations;
straight stress-free rods. D4 is the CAP on fixed supports, not its skirt.
Wind is a reference-geometry dead force field, not an aeroelastic calculation.
"""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
import tomllib

import numpy as np
from scipy.spatial import cKDTree

from stardome import config, connectors, geometry, loads, material, model, span
from .rod import RodSystem

ROOT = Path(__file__).resolve().parent.parent


def settings():
    with open(ROOT / "configs/wind-study.toml", "rb") as f:
        return tomllib.load(f)


def tube_properties(tube):
    d, t, length = (tube[k] for k in ("outside_mm", "wall_mm", "length_mm"))
    if not all(math.isfinite(v) and v > 0 for v in (d, t, length)) or 2*t >= d:
        raise ValueError("tube requires positive dimensions and 2*wall < outside")
    for key in ("modulus_mpa", "yield_mpa", "density_kg_m3"):
        if not math.isfinite(tube[key]) or tube[key] <= 0:
            raise ValueError(f"invalid tube {key}")
    bore = d-2*t
    area = math.pi/4*(d*d-bore*bore)
    inertia = math.pi/64*(d**4-bore**4)
    return {"nominal_bore_mm": bore, "area_mm2": area, "inertia_mm4": inertia,
            "section_modulus_mm3": 2*inertia/d,
            "gross_yield_moment_nm": tube["yield_mpa"]*2*inertia/d/1000,
            "tube_rotation_stiffness_nmm": tube["modulus_mpa"]*inertia/length,
            "mass_kg": area*length*tube["density_kg_m3"]*1e-9}


def build_cap(data, mat, step_deg=10, holds="contact", area_factor=1.0,
              joint_efficiency=None, tube=None):
    if not math.isfinite(step_deg) or not 0 < step_deg <= 30:
        raise ValueError("mesh step must be in (0, 30] degrees")
    if holds not in ("contact", "lashed"):
        raise ValueError("holds must be contact or lashed")
    if not math.isfinite(area_factor) or area_factor <= 0:
        raise ValueError("area factor must be finite and positive")
    if joint_efficiency is not None and (not math.isfinite(joint_efficiency) or joint_efficiency < 0):
        raise ValueError("joint efficiency must be finite and nonnegative")
    radius = data["meta"]["dome_radius"]
    diameter = data["meta"]["rod_diameter"]*math.sqrt(area_factor)
    area, inertia = mat.area(diameter), mat.second_moment(diameter)
    tube = settings()["tube"] if tube is None else tube
    tp = tube_properties(tube)
    # The current transport schedule owns splice locations. Do not invent
    # equally spaced joints or bridge a door cut.
    splices = connectors.splice_joints(data, data["meta"]["section_length"],
                                       tube["length_mm"])
    bows = {b.name: b for b in geometry.build_bows()}
    positions, lookup, stretches, edge_rest = [], {}, [], []
    edges, triples, dual, splice_triples = [], [], [], []
    for rod in data["rods"]:
        name = rod["name"]
        marks = [c[f"t_{side}_deg"] for c in data["crossings"]
                 for side in ("a", "b") if c[f"rod_{side}"] == name]
        joints = [j["t_deg"] for j in splices if j["rod"] == name]
        for lo, hi in span.live_intervals(rod):
            # Door cuts and crossing angles have different export rounding.
            # Snap within 0.001 degree (<=0.053 mm at D6), preserving the
            # authoritative live-interval endpoints and total rod length.
            ts = [lo]
            for v in sorted(marks+joints):
                if v > ts[-1]+.001 and v < hi-.001:
                    ts.append(v)
            ts.append(hi)
            refined = [ts[0]]
            for a, b in zip(ts, ts[1:]):
                n = math.ceil((b-a)/step_deg)
                refined.extend(a+(b-a)*i/n for i in range(1, n+1))
            ids = []
            for t in refined:
                i = len(positions)
                positions.append(bows[name].point(t, radius))
                lookup[name, round(t, 5)] = i
                ids.append(i)
            for mark in marks+joints:
                near = min(range(len(refined)), key=lambda i: abs(refined[i]-mark))
                if abs(refined[near]-mark) < .001:
                    lookup[name, round(mark, 5)] = ids[near]
            stretches.append((name, ids))
            rest = [radius*math.radians(b-a) for a, b in zip(refined, refined[1:])]
            edges.extend(zip(ids, ids[1:]))
            edge_rest.extend(rest)
            for i in range(1, len(ids)-1):
                triples.append(ids[i-1:i+2])
                dual.append((rest[i-1]+rest[i])/2)
                splice_triples.append(any(abs(refined[i]-j) < 1e-4 for j in joints))
    parent = list(range(len(positions)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(a, b):
        parent[root(b)] = root(a)
    terminal_ids = {ids[i] for _, ids in stretches for i in (0, -1)}
    for crossing in data["crossings"]:
        a = lookup.get((crossing["rod_a"], round(crossing["t_a_deg"], 5)))
        b = lookup.get((crossing["rod_b"], round(crossing["t_b_deg"], 5)))
        if a is not None and b is not None and (holds == "contact" or crossing["tied"]
                                               or a in terminal_ids or b in terminal_ids):
            union(a, b)
    # Bow feet at a common base hub share translations, but not rotations.
    feet = {}
    for i, p in enumerate(positions):
        if abs(p[2]) < 1e-5:
            key = tuple(round(v, 4) for v in p)
            if key in feet:
                union(feet[key], i)
            feet[key] = i
    unique = sorted({root(i) for i in range(len(positions))})
    number = {i: n for n, i in enumerate(unique)}
    remap = np.array([number[root(i)] for i in range(len(positions))])
    x0 = np.array([positions[i] for i in unique], dtype=float)
    edges, triples = remap[np.array(edges)], remap[np.array(triples)]
    bend_k = mat.modulus_mpa*inertia/np.array(dual)
    splice_triples = np.array(splice_triples)
    if joint_efficiency is not None:
        kj = joint_efficiency*tp["tube_rotation_stiffness_nmm"]
        bend_k[splice_triples] = (1/(1/bend_k[splice_triples]+1/kj) if kj > 0 else 0)
    fixed_nodes = np.where(np.abs(x0[:, 2]) < 1e-5)[0]
    fixed = (3*fixed_nodes[:, None]+np.arange(3)).ravel()
    system = RodSystem(x0, edges, triples, np.array(edge_rest),
                       np.full(len(edges), mat.modulus_mpa*area), bend_k, fixed)
    return system, {"diameter_mm": diameter, "area_mm2": area, "inertia_mm4": inertia,
                    "splice_triples": splice_triples, "splices": splices,
                    "splice_nodes": [int(remap[lookup[j["rod"], round(j["t_deg"], 5)]])
                                     for j in splices], "tube": tp}


def transfer_forces(x, points, forces):
    """Nearest-node partition with explicit force AND moment conservation.

    A least-norm correction removes partition eccentricity. This does not solve
    the fabric load path. Report correction norm so a poor partition is visible.
    Coordinates are centred/scaled for a well-conditioned six-equation solve.
    """
    centre = x.mean(axis=0)
    scale = np.linalg.norm(x-centre, axis=1).max()
    r = (x-centre)/scale
    p = (points-centre)/scale
    assigned = cKDTree(x).query(points)[1]
    nodal = np.zeros_like(x)
    np.add.at(nodal, assigned, forces)
    b = np.zeros((6, len(x), 3))
    b[:3] = np.broadcast_to(np.eye(3)[:, None, :], (3, len(x), 3))
    b[3, :, 1], b[3, :, 2] = -r[:, 2], r[:, 1]
    b[4, :, 0], b[4, :, 2] = r[:, 2], -r[:, 0]
    b[5, :, 0], b[5, :, 1] = -r[:, 1], r[:, 0]
    b = b.reshape(6, -1)
    target = np.r_[forces.sum(axis=0), np.cross(p, forces).sum(axis=0)]
    correction = b.T@np.linalg.solve(b@b.T, target-b@nodal.ravel())
    relative = float(np.linalg.norm(correction)/max(np.linalg.norm(nodal), 1e-12))
    nodal += correction.reshape(-1, 3)
    return nodal, relative


def cap_loads(data, system, info, mat, loading, speed, azimuth, cpi, tension, tube_mass):
    if not math.isfinite(tension) or tension < 0:
        raise ValueError("fabric tension must be finite and nonnegative")
    facets = [f for f in loads.facet_loads(data, speed, loading, azimuth,
                                          meridians=60, parallels=24, cp_internal=cpi)
              if not f["skirt"]]
    points = np.array([f["centroid"] for f in facets])
    forces = np.array([f["force_n"] for f in facets])
    area = np.array([f["area_mm2"] for f in facets])*1e-6
    # Spherical isotropic prestress idealisation. No fabric stiffness credited.
    preload_pa = 2*tension/(data["meta"]["dome_radius"]/1000)
    preload_forces = -(preload_pa*area)[:, None]*np.array([f["normal"] for f in facets])
    forces += preload_forces
    forces[:, 2] -= area*loading.fabric_g_m2/1000*loading.gravity_m_s2
    result, correction = transfer_forces(system.x0, points, forces)
    # Membrane pretension is internal to the cap + hem system, not an extra
    # external downward load. Return its opposite resultant and moment to the
    # fixed rim. The distribution around that rim remains an idealisation.
    fixed_nodes = np.unique(system.fixed//3)
    rim, _ = transfer_forces(system.x0[fixed_nodes], points, -preload_forces)
    result[fixed_nodes] += rim
    masses = system.rest*info["area_mm2"]*mat.density_kg_m3*1e-9
    for end in (0, 1):
        np.add.at(result[:, 2], system.edges[:, end], -masses*loading.gravity_m_s2/2)
    if tube_mass:
        np.add.at(result[:, 2], info["splice_nodes"], -info["tube"]["mass_kg"]*loading.gravity_m_s2)
    return result, correction


def stresses(system, info, mat, x):
    e = x[system.edges[:, 1]]-x[system.edges[:, 0]]
    axial = mat.modulus_mpa*(np.linalg.norm(e, axis=1)/system.rest-1)
    p = x[system.triples]
    t0, t1 = p[:, 1]-p[:, 0], p[:, 2]-p[:, 1]
    t0 /= np.linalg.norm(t0, axis=1)[:, None]
    t1 /= np.linalg.norm(t1, axis=1)[:, None]
    c = np.clip(np.sum(t0*t1, axis=1), -1+1e-12, 1)
    kb = np.sqrt(4*(1-c)/(1+c))
    moments = system.bend_k*kb*(1+kb**2/4)
    bending = moments*info["diameter_mm"]/2/info["inertia_mm4"]
    # Adjacent axial stresses + local bending; maxima also cover bare ends.
    by_edge = {tuple(edge): a for edge, a in zip(system.edges, axial)}
    adjacent = np.array([[by_edge[tuple(t[:2])], by_edge[tuple(t[1:])]]
                         for t in system.triples])
    tension = max(0, float(axial.max()), float((adjacent+bending[:, None]).max()))
    compression = max(0, float(-axial.min()), float((-adjacent+bending[:, None]).max()))
    splice_m = moments[info["splice_triples"]]
    return {"max_tensile_stress_mpa": tension, "max_compressive_stress_mpa": compression,
            "short_term_criterion_utilisation": max(tension/mat.allowable("short_term", "tension"),
                                                       compression/mat.allowable("short_term", "compression")),
            "sustained_criterion_utilisation": max(tension/mat.allowable("sustained", "tension"),
                                                      compression/mat.allowable("sustained", "compression")),
            "max_splice_moment_nm": float(splice_m.max(initial=0)/1000)}


def load_path(system, start, force_from, force_to, initial_step=1.0):
    """Load continuation with subdivision; never relabel a partial load as full.

    This tracks sampled equilibria, not a certified bifurcation-free path.
    Very large jumps are subdivided even if Newton found another equilibrium.
    """
    x, fraction, step = start, 0.0, initial_step
    path = []
    radius = np.linalg.norm(system.x0, axis=1).max()
    while fraction < 1-1e-12:
        target = min(1.0, fraction+step)
        trial, result = system.solve(force_from+target*(force_to-force_from), start=x)
        jump = float(np.linalg.norm(trial-x, axis=1).max())
        if result["status"] != "stable_equilibrium" or jump > .05*radius:
            step *= .5
            if step < 1/256:
                result["last_attempt_status"] = result["status"]
                result["status"] = "load_path_unresolved"
                result["reached_load_fraction"] = fraction
                result["attempted_load_fraction"] = target
                result["path_steps"] = path
                return trial, result
            continue
        x, fraction = trial, target
        path.append({"load_fraction": fraction, "residual_n": result["residual_n"],
                     "minimum_tangent_eigenvalue_n_mm": result["minimum_tangent_eigenvalue_n_mm"],
                     "increment_displacement_mm": jump})
        step = min(initial_step, step*1.5)
    result["reached_load_fraction"] = 1.0
    result["path_steps"] = path
    return x, result


def run(variant="D6", step=10, modulus=50000, tension=0, eta=None,
        holds="contact", area_factor=1, speeds=(0, 2, 5, 10, 15, 20), azimuth=0, cpi=0.2):
    for value in (modulus, area_factor):
        if not math.isfinite(value) or value <= 0:
            raise ValueError("modulus and area factor must be positive")
    for value in speeds:
        loads.velocity_pressure(value, loads.load())
    data = model.build(config.load(variant))
    cfg = settings()
    mat = replace(material.load_all()[cfg["rod"]["material"]], modulus_mpa=modulus)
    loading = loads.load()
    system, info = build_cap(data, mat, step, holds, area_factor, eta, cfg["tube"])
    zero = np.zeros_like(system.x0)
    x, assembly = system.solve(zero)
    assembly.update(stresses(system, info, mat, x))
    cases = []
    if assembly["status"] == "stable_equilibrium":
        # Establish gravity + membrane preload BEFORE applying any wind.
        previous_force = zero
        for speed in dict.fromkeys([0.0, *speeds]):
            force, correction = cap_loads(data, system, info, mat, loading,
                                         speed, azimuth, cpi, tension, eta is not None)
            x, result = load_path(system, x, previous_force, force,
                                 initial_step=.125 if speed == 0 else 1)
            if result["status"] == "stable_equilibrium":
                result.update(stresses(system, info, mat, x))
            else:
                result["last_iterate_stresses_not_for_design"] = stresses(system, info, mat, x)
            result.update(wind_ms=speed, transfer_correction_fraction=correction)
            result.pop("reactions_n")
            cases.append(result)
            if result["status"] != "stable_equilibrium":
                break
            previous_force = force
    assembly.pop("reactions_n")
    return {
        "schema": "star_dome_cap_study/1", "operational_limit_ms": None,
        "scope": "twist-relaxed cap on fixed pinned feet; skirt, anchors, connector strength excluded",
        "inputs": {"variant": variant, "mesh_step_deg": step, "material": asdict(mat),
                   "loads": asdict(loading), "fabric_tension_n_m": tension,
                   "pretension_boundary": "equal opposite resultant/moment returned to fixed rim",
                   "joint_efficiency": eta, "holds": holds, "area_factor": area_factor,
                   "tube": cfg["tube"], "azimuth_towards_deg": azimuth, "cp_internal": cpi,
                   "requested_wind_ms": list(speeds)},
        "geometry_sha256": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
        "nodes": len(system.x0), "edges": len(system.edges), "splices": len(info["splices"]),
        "tube_section": info["tube"], "assembly": assembly, "cases": cases,
        "limitations": ["No material twist/shear, crossing slip or eccentric weave geometry",
                        "D4 skirt, header and soil supports absent; this is the cap only",
                        "Reference-geometry pressure, no aeroelasticity or fabric stiffness",
                        "No certified splice law; gross tube section ignores holes/contact",
                        "Connector/hem/webbing mass omitted; rod and roof fabric mass included",
                        "Nonconvergence is not proof of physical collapse",
                        "Local gust scenarios do not establish code site wind actions"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variant", choices=("D4", "D6"))
    parser.add_argument("--step", type=float, default=10)
    parser.add_argument("--modulus", type=float, default=50000)
    parser.add_argument("--tension", type=float, default=0)
    parser.add_argument("--eta", type=float, default=None, help="omit for continuous rods")
    parser.add_argument("--holds", choices=("contact", "lashed"), default="contact")
    parser.add_argument("--area-factor", type=float, default=1)
    parser.add_argument("--winds", type=float, nargs="+", default=[0, 2, 5, 10, 15, 20])
    parser.add_argument("--azimuth", type=float, default=0)
    parser.add_argument("--cpi", type=float, default=0.2)
    parser.add_argument("-o", type=Path, required=True)
    args = parser.parse_args()
    out = args.o
    del args.o
    kwargs = vars(args)
    kwargs["speeds"] = kwargs.pop("winds")
    report = run(**kwargs)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+"\n")
    print(f"{report['inputs']['variant']}: {report['assembly']['status']}; "
          f"{len(report['cases'])} load steps; operational limit unestablished; {out}")


if __name__ == "__main__":
    main()
