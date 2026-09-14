"""Extensible, isotropic, twist-relaxed discrete rods, in N and mm.

Natural rods are straight. Bending energy uses the discrete curvature binormal
2(t0 cross t1)/(1+t0 dot t1), not rotations measured from the assembled shape.
No material-frame torsion, shear deformation, contact or material nonlinearity.
This is an idealisation for sensitivity studies, not a validated dome model.
"""

from dataclasses import dataclass
import numpy as np
from scipy import sparse
from scipy.linalg import eigh
from scipy.sparse.linalg import spsolve


def bend_local(p, k):
    """Energy and gradient of k/2 * |curvature_binormal|^2.

    Holomorphic implementation permits complex-step differentiation of the
    gradient for a consistent tangent. k = EI / rest dual length for a rod.
    """
    e0, e1 = p[:, 1] - p[:, 0], p[:, 2] - p[:, 1]
    l0 = np.sqrt(np.sum(e0 * e0, axis=1))
    l1 = np.sqrt(np.sum(e1 * e1, axis=1))
    t0, t1 = e0 / l0[:, None], e1 / l1[:, None]
    c = np.sum(t0 * t1, axis=1)
    dc = -4 * k / (1 + c) ** 2
    g0 = dc[:, None] * (t1 - c[:, None] * t0) / l0[:, None]
    g1 = dc[:, None] * (t0 - c[:, None] * t1) / l1[:, None]
    return 2 * k * (1 - c) / (1 + c), np.stack((-g0, g0-g1, g1), axis=1)


@dataclass
class RodSystem:
    x0: np.ndarray
    edges: np.ndarray
    triples: np.ndarray
    rest: np.ndarray
    ea: np.ndarray
    bend_k: np.ndarray
    fixed: np.ndarray

    def evaluate(self, x, force, tangent=False):
        edges, triples = self.edges, self.triples
        delta = x[edges[:, 1]] - x[edges[:, 0]]
        lengths = np.linalg.norm(delta, axis=1)
        if np.any(lengths < 1e-8):
            raise ValueError("collapsed rod edge")
        t = delta / lengths[:, None]
        axial = self.ea * (lengths / self.rest - 1)
        energy = float(np.sum(self.ea / (2*self.rest) * (lengths-self.rest)**2))
        gradient = -force.copy()
        np.add.at(gradient, edges[:, 0], -axial[:, None]*t)
        np.add.at(gradient, edges[:, 1], axial[:, None]*t)
        local = x[triples]
        e, g = bend_local(local, self.bend_k)
        if not np.all(np.isfinite(e)):
            raise ValueError("folded rod singularity")
        energy += float(e.sum() - np.sum(force*(x-self.x0)))
        np.add.at(gradient, triples.ravel(), g.reshape(-1, 3))
        if not tangent:
            return energy, gradient
        eye = np.eye(3)[None]
        tt = t[:, :, None]*t[:, None, :]
        a = self.ea[:, None, None]/self.rest[:, None, None]*tt
        a += (axial/lengths)[:, None, None]*(eye-tt)
        h_edge = np.concatenate((np.concatenate((a, -a), axis=2),
                                 np.concatenate((-a, a), axis=2)), axis=1)
        h_bend = np.empty((len(triples), 9, 9))
        for j in range(9):
            perturbed = local.astype(complex)
            perturbed[:, j//3, j%3] += 1j*1e-20
            h_bend[:, :, j] = bend_local(perturbed, self.bend_k)[1].reshape(-1, 9).imag/1e-20
        rows, cols, values = [], [], []
        for indices, blocks in ((edges, h_edge), (triples, h_bend)):
            dofs = (3*indices[:, :, None] + np.arange(3)).reshape(len(indices), -1)
            rows.append(np.broadcast_to(dofs[:, :, None], blocks.shape).ravel())
            cols.append(np.broadcast_to(dofs[:, None, :], blocks.shape).ravel())
            values.append(blocks.ravel())
        h = sparse.coo_matrix((np.concatenate(values),
                               (np.concatenate(rows), np.concatenate(cols))),
                              shape=(x.size, x.size)).tocsr()
        return energy, gradient, (h+h.T)*0.5

    def solve(self, force, start=None, tolerance_n=1e-5, max_iterations=200):
        """Damped Newton equilibrium; failure is not interpreted as collapse.

        Return a residual and the smallest constrained tangent eigenvalue.
        Negative eigenvalue distinguishes an unstable stationary point from a
        stable solution. No eigenvalue is inferred from optimiser success.
        """
        x = self.x0.copy() if start is None else start.copy()
        free = np.setdiff1d(np.arange(x.size), self.fixed)
        x.ravel()[self.fixed] = self.x0.ravel()[self.fixed]
        converged = False
        for iteration in range(max_iterations+1):
            energy, gradient, h = self.evaluate(x, force, True)
            g = gradient.ravel()[free]
            residual = float(np.max(np.abs(g), initial=0))
            if residual <= tolerance_n:
                converged = True
                break
            if iteration == max_iterations:
                break
            hf = h[free][:, free]
            shift = 0.0
            accepted = False
            for _ in range(18):
                p = spsolve(hf + sparse.eye(len(free), format="csr")*shift, -g)
                slope = float(g@p)
                if np.all(np.isfinite(p)) and slope < 0:
                    alpha = 1.0
                    for _ in range(24):
                        trial = x.copy()
                        trial.ravel()[free] += alpha*p
                        try:
                            trial_energy, trial_gradient = self.evaluate(trial, force)
                        except ValueError:
                            trial_energy = np.inf
                        rounding = 64*np.finfo(float).eps*max(1, abs(energy))
                        improves_residual = (trial_energy <= energy+rounding and
                                             np.max(np.abs(trial_gradient.ravel()[free])) < .9*residual)
                        if trial_energy <= energy + 1e-4*alpha*slope or improves_residual:
                            x = trial
                            accepted = True
                            break
                        alpha *= 0.5
                if accepted:
                    break
                shift = 1e-5 if shift == 0 else shift*10
            if not accepted:
                break
        # Evaluate the actual last iterate also when line search failed.
        energy, gradient, h = self.evaluate(x, force, True)
        residual = float(np.max(np.abs(gradient.ravel()[free]), initial=0))
        converged = residual <= tolerance_n
        eigenvalue = float(eigh(h[free][:, free].toarray(), subset_by_index=[0, 0],
                               check_finite=False, eigvals_only=True)[0]) if converged else None
        status = ("stable_equilibrium" if eigenvalue is not None and eigenvalue > 1e-9
                  else "unstable_or_neutral_equilibrium" if converged else "not_converged")
        reaction = np.zeros(x.size)
        reaction[self.fixed] = gradient.ravel()[self.fixed]
        reaction = reaction.reshape(-1, 3)
        return x, {
            "status": status, "iterations": iteration, "residual_n": residual,
            "minimum_tangent_eigenvalue_n_mm": eigenvalue,
            "max_displacement_mm": float(np.linalg.norm(x-self.x0, axis=1).max()),
            "force_balance_n": (reaction+force).sum(axis=0).tolist(),
            "moment_balance_nmm": np.cross(x, reaction+force).sum(axis=0).tolist(),
            "reactions_n": reaction.tolist(),
        }
