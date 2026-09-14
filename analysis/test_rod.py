"""Independent mechanics benchmarks; run separately from the stdlib CAD suite."""
import math
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from .rod import RodSystem
from .wind_study import build_cap, transfer_forces, tube_properties, settings
from stardome import config, material, model


def straight(n=30, length=1000, ea=2e6, ei=1e6):
    x = np.zeros((n+1, 3))
    x[:, 0] = np.linspace(0, length, n+1)
    edges = np.array([[i, i+1] for i in range(n)])
    triples = np.array([[i-1, i, i+1] for i in range(1, n)])
    return RodSystem(x, edges, triples, np.full(n, length/n),
                     np.full(n, ea), np.full(n-1, ei/(length/n)), np.arange(6))


def test_energy_gradient_tangent_and_objectivity():
    system = straight(6)
    rng = np.random.default_rng(91)
    x = system.x0+rng.normal(0, 12, system.x0.shape)
    zero = np.zeros_like(x)
    e, g, h = system.evaluate(x, zero, True)
    direction = rng.normal(size=x.shape)
    eps = 1e-3
    ep, gp = system.evaluate(x+eps*direction, zero)
    em, gm = system.evaluate(x-eps*direction, zero)
    assert (ep-em)/(2*eps) == pytest.approx(np.sum(g*direction), rel=1e-7)
    np.testing.assert_allclose((gp-gm).ravel()/(2*eps), h@direction.ravel(), rtol=1e-7, atol=1e-6)
    rot = Rotation.from_rotvec([.5, -.3, .8]).as_matrix()
    er, gr = system.evaluate(x@rot.T+[50, 100, 70], zero)
    assert er == pytest.approx(e, rel=1e-12)
    np.testing.assert_allclose(gr, g@rot.T, rtol=1e-10, atol=1e-7)
    np.testing.assert_allclose(g.sum(axis=0), 0, atol=1e-8)
    np.testing.assert_allclose(np.cross(x, g).sum(axis=0), 0, atol=1e-6)


def test_axial_extension_and_force_balance():
    s = straight(10)
    s.fixed = np.r_[0, np.arange(1, s.x0.size, 3), np.arange(2, s.x0.size, 3)]
    f = np.zeros_like(s.x0)
    f[-1, 0] = 100
    x, report = s.solve(f)
    assert report["status"] == "stable_equilibrium"
    assert x[-1, 0]-1000 == pytest.approx(100*1000/2e6, rel=1e-8)
    np.testing.assert_allclose(report["force_balance_n"], 0, atol=1e-7)


def test_cantilever_converges_to_euler_bernoulli():
    errors = []
    for n in (20, 40):
        s = straight(n)
        f = np.zeros_like(s.x0)
        f[-1, 1] = .003
        x, report = s.solve(f, tolerance_n=1e-7)
        assert report["status"] == "stable_equilibrium"
        expected = .003*1000**3/(3*1e6)
        errors.append(abs(x[-1, 1]/expected-1))
        np.testing.assert_allclose(report["moment_balance_nmm"], 0, atol=1e-4)
    assert errors[1] < errors[0]*.55
    assert errors[1] < .04


@pytest.mark.parametrize("ratio,stable", [(0.9, True), (1.1, False)])
def test_pinned_column_euler_buckling(ratio, stable):
    s = straight(40)
    s.fixed = np.array([0, 1, 2, s.x0.size-2, s.x0.size-1])
    f = np.zeros_like(s.x0)
    f[-1, 0] = -ratio*math.pi**2*1e6/1000**2
    _, result = s.solve(f)
    assert (result["minimum_tangent_eigenvalue_n_mm"] > 0) == stable
    assert result["residual_n"] < 1e-5


def test_force_transfer_preserves_resultant_and_moment():
    rng = np.random.default_rng(4)
    x, p = rng.normal(size=(25, 3))*1000, rng.normal(size=(300, 3))*1000
    f = rng.normal(size=p.shape)*100
    nodal, _ = transfer_forces(x, p, f)
    np.testing.assert_allclose(nodal.sum(axis=0), f.sum(axis=0), atol=1e-10)
    np.testing.assert_allclose(np.cross(x, nodal).sum(axis=0), np.cross(p, f).sum(axis=0), atol=1e-7)


@pytest.mark.parametrize("variant", ["D4", "D6"])
def test_cap_topology_and_rest_length(variant):
    data = model.build(config.load(variant))
    m = material.load_all()["gost31938_2022"]
    system, info = build_cap(data, m)
    from stardome.span import live_intervals
    expected = sum(hi-lo for rod in data["rods"] for lo, hi in live_intervals(rod))
    assert system.rest.sum() == pytest.approx(math.radians(expected)*data["meta"]["dome_radius"])
    assert system.rest.min() > 1
    assert len(set(system.fixed//3)) == 10
    assert len(info["splice_nodes"]) == len(info["splices"])
    assert info["splice_triples"].sum() == len(info["splices"])
    # Joint compliance must reduce precisely the scheduled bending terms.
    softer, _ = build_cap(data, m, joint_efficiency=.1)
    assert np.all(softer.bend_k[info["splice_triples"]] < system.bend_k[info["splice_triples"]])
    np.testing.assert_equal(softer.bend_k[~info["splice_triples"]], system.bend_k[~info["splice_triples"]])


def test_tube_gross_section_uses_annulus_not_solid_bar():
    t = tube_properties(settings()["tube"])
    assert t["nominal_bore_mm"] == 12
    assert t["inertia_mm4"] == pytest.approx(math.pi/64*(16**4-12**4))
    assert t["gross_yield_moment_nm"] == pytest.approx(225*t["inertia_mm4"]/8/1000)


def test_closed_circle_bending_energy_converges_and_is_not_stress_free():
    errors = []
    for n in (30, 60):
        radius, ei = 2000, 1e7
        theta = np.arange(n)*2*np.pi/n
        x = radius*np.column_stack((np.cos(theta), np.sin(theta), np.zeros(n)))
        edges = np.column_stack((np.arange(n), (np.arange(n)+1)%n))
        triples = np.column_stack(((np.arange(n)-1)%n, np.arange(n), (np.arange(n)+1)%n))
        # Zero axial energy isolates the curvature formula from stretching.
        rest = np.linalg.norm(x[edges[:, 1]]-x[edges[:, 0]], axis=1)
        s = RodSystem(x, edges, triples, rest, np.full(n, 2e6),
                      np.full(n, ei/(2*np.pi*radius/n)), np.array([], dtype=int))
        energy, gradient = s.evaluate(x, np.zeros_like(x))
        expected = ei*np.pi/radius
        assert energy > 0
        assert np.linalg.norm(gradient) > 0
        errors.append(abs(energy/expected-1))
    assert errors[1] < .26*errors[0]


def test_unresolved_load_path_never_claims_full_load(monkeypatch):
    from .wind_study import load_path
    s = straight(4)
    def fake_solve(force, start=None, **kwargs):
        f = float(force[-1, 1])
        return start.copy(), {"status": "stable_equilibrium" if f <= .6 else "not_converged",
                              "residual_n": 0 if f <= .6 else 2,
                              "minimum_tangent_eigenvalue_n_mm": 1 if f <= .6 else None}
    monkeypatch.setattr(s, "solve", fake_solve)
    target = np.zeros_like(s.x0)
    target[-1, 1] = 1
    _, report = load_path(s, s.x0, np.zeros_like(target), target, .125)
    assert report["status"] == "load_path_unresolved"
    assert .59 < report["reached_load_fraction"] <= .6
    assert report["attempted_load_fraction"] > .6


def test_membrane_prestress_is_self_equilibrated_and_loads_interior():
    from .wind_study import cap_loads
    from stardome import loads
    data = model.build(config.load("D6"))
    m = material.load_all()["gost31938_2022"]
    system, info = build_cap(data, m)
    args = (data, system, info, m, loads.load(), 0, 0, .2)
    f0, _ = cap_loads(*args, 0, False)
    f1, _ = cap_loads(*args, 50, False)
    delta = f1-f0
    np.testing.assert_allclose(delta.sum(axis=0), 0, atol=1e-9)
    np.testing.assert_allclose(np.cross(system.x0, delta).sum(axis=0), 0, atol=1e-6)
    free = np.setdiff1d(np.arange(system.x0.size), system.fixed)
    assert np.linalg.norm(delta.ravel()[free]) > 1
