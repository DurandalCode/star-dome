"""Rigid base, equal spring stiffness: an explicit anchor screening model.

The returned vectors are loads delivered to anchors, opposite to reactions
on the structure. Their sum and moment reproduce the applied wind resultant.
Vertical springs act in both directions: tension anchors and compression
bearing. Loss of contact, unequal soil stiffness and a flexible base require
a different model. This is not a conservative bound for the real dome.
"""

from __future__ import annotations

import math


def _solve3(matrix, rhs):
    rows = [list(row) + [value] for row, value in zip(matrix, rhs)]
    for j in range(3):
        p = max(range(j, 3), key=lambda i: abs(rows[i][j]))
        if abs(rows[p][j]) < 1e-12:
            raise ValueError("anchors must span a plane, not a line")
        rows[j], rows[p] = rows[p], rows[j]
        pivot = rows[j][j]
        rows[j] = [x / pivot for x in rows[j]]
        for i in range(3):
            if i != j:
                scale = rows[i][j]
                rows[i] = [a - scale * b for a, b in zip(rows[i], rows[j])]
    return [row[-1] for row in rows]


def distribute(anchors: list, force_n: list, moment_nmm: list) -> dict:
    """Distribute F and M about the ground origin to anchor ground projections.

    Coordinates are millimetres. Vertical load is affine in x and y. In-plane
    shear comprises uniform translation and a tangential torsional component.
    The calculation is centred and scaled to avoid mixing metres squared with
    unit entries in the vertical equilibrium solve.
    """
    if len(anchors) < 3:
        raise ValueError("at least three anchors are required")
    values = list(force_n) + list(moment_nmm)
    values += [a[k] for a in anchors for k in ("x", "y")]
    if len(force_n) != 3 or len(moment_nmm) != 3 or not all(map(math.isfinite, values)):
        raise ValueError("finite 3D forces, moments and anchor coordinates required")
    n = len(anchors)
    cx = sum(a["x"] for a in anchors) / n
    cy = sum(a["y"] for a in anchors) / n
    xy = [(a["x"] - cx, a["y"] - cy) for a in anchors]
    scale = max(math.hypot(x, y) for x, y in xy)
    if scale <= 0:
        raise ValueError("anchors cannot coincide")
    fx, fy, fz = force_n
    mx, my, mz = moment_nmm
    mx -= cy * fz
    my += cx * fz
    mz -= cx * fy - cy * fx
    basis = [(1.0, y / scale, -x / scale) for x, y in xy]
    gram = [[sum(b[i] * b[j] for b in basis) for j in range(3)] for i in range(3)]
    coeff = _solve3(gram, (fz, mx / scale, my / scale))
    polar = sum(x * x + y * y for x, y in xy)
    rows = []
    for a, (x, y), b in zip(anchors, xy, basis):
        vertical = sum(c * v for c, v in zip(coeff, b))
        sx, sy = fx / n - mz * y / polar, fy / n + mz * x / polar
        rows.append({
            "anchor": a["name"], "x_mm": a["x"], "y_mm": a["y"],
            "force_n": [sx, sy, vertical],
            "uplift_n": max(0.0, vertical),
            "bearing_n": max(0.0, -vertical),
            "shear_n": math.hypot(sx, sy),
        })
    return {
        "model": "rigid_base_equal_bilateral_springs",
        "status": "screening_only",
        "anchors": rows,
        "max_uplift_n": max(r["uplift_n"] for r in rows),
        "max_shear_n": max(r["shear_n"] for r in rows),
        "max_bearing_n": max(r["bearing_n"] for r in rows),
        "note": "Equal stiffness, rigid base and bilateral vertical restraint assumed; "
                "soil capacity, bearing and combined uplift/shear are not validated.",
    }
