"""Minimal 3D vector helpers.

Deliberately stdlib-only: ``stardome`` must import unchanged inside the
Python interpreters bundled with FreeCAD and Blender, without installing
anything. A vector is a plain ``tuple[float, float, float]``.
"""

from __future__ import annotations

import math

Vec3 = tuple[float, float, float]


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a: Vec3, k: float) -> Vec3:
    return (a[0] * k, a[1] * k, a[2] * k)


def neg(a: Vec3) -> Vec3:
    return (-a[0], -a[1], -a[2])


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a: Vec3) -> float:
    return math.sqrt(dot(a, a))


def unit(a: Vec3) -> Vec3:
    n = norm(a)
    if n == 0.0:
        raise ValueError("cannot normalise a zero-length vector")
    return (a[0] / n, a[1] / n, a[2] / n)


def dist(a: Vec3, b: Vec3) -> float:
    return norm(sub(a, b))


def angle_between(a: Vec3, b: Vec3) -> float:
    """Angle between two vectors in degrees, in [0, 180]."""
    c = dot(unit(a), unit(b))
    # Guard against the tiny overshoot that makes acos raise on parallel input.
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def crossing_angle(a: Vec3, b: Vec3) -> float:
    """Acute angle between two undirected lines, in degrees, in [0, 90].

    Rod tangents carry an arbitrary direction (which end of the bow the arc
    parameter runs from), so the meaningful quantity at a crossing is the
    acute angle, not the signed angle between tangent vectors.
    """
    a_ = angle_between(a, b)
    return min(a_, 180.0 - a_)


def rotate_z(a: Vec3, degrees: float) -> Vec3:
    c = math.cos(math.radians(degrees))
    s = math.sin(math.radians(degrees))
    return (a[0] * c - a[1] * s, a[0] * s + a[1] * c, a[2])


def mirror_about_azimuth(a: Vec3, azimuth_deg: float) -> Vec3:
    """Reflect through the vertical plane containing the given azimuth."""
    t = math.radians(2.0 * azimuth_deg)
    c, s = math.cos(t), math.sin(t)
    return (a[0] * c + a[1] * s, a[0] * s - a[1] * c, a[2])


def round_vec(a: Vec3, ndigits: int = 6) -> Vec3:
    return (round(a[0], ndigits), round(a[1], ndigits), round(a[2], ndigits))
