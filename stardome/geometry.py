"""Star Dome bow geometry.

Every number here is derived, not typed in. The inputs are the base polygon
count (10), one icosahedral angle (``atan 2``), and the reference's rod
marking diagram. See dome/README.md for the full derivation.

A bow is half a great circle on the sphere of radius R, running from one base
point over the dome to the base point diametrically opposite. It is fully
described by two numbers: the azimuth of its starting base point, and the tilt
of its plane above the ground.

Parametrised by arc angle ``t`` in [0, 180] degrees, which is proportional to
length along the rod, so ``s = R * radians(t)``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import vec
from .vec import Vec3

BASE_POINT_COUNT = 10
BASE_STEP_DEG = 360.0 / BASE_POINT_COUNT

# Family G's tilt is the angle between adjacent 5-fold axes of an
# icosahedron. This is the one angle the design is seeded with.
TILT_G = math.degrees(math.atan(2.0))

# Family G is marked in fifths, families U and L in thirds.
MARKS_FIFTHS = (36.0, 72.0, 108.0, 144.0)
MARKS_THIRDS = (60.0, 120.0)


@dataclass(frozen=True)
class Bow:
    """One full-length rod, bent into a great semicircle."""

    name: str
    family: str
    number: int
    azimuth_deg: float
    tilt_deg: float
    foot_a: int
    foot_b: int
    layer: int

    @property
    def u(self) -> Vec3:
        """Unit vector to the starting base point (t = 0)."""
        a = math.radians(self.azimuth_deg)
        return (math.cos(a), math.sin(a), 0.0)

    @property
    def v(self) -> Vec3:
        """Unit vector in the bow plane, perpendicular to u (t = 90)."""
        a = math.radians(self.azimuth_deg)
        tilt = math.radians(self.tilt_deg)
        return (
            -math.sin(a) * math.cos(tilt),
            math.cos(a) * math.cos(tilt),
            math.sin(tilt),
        )

    @property
    def normal(self) -> Vec3:
        """Unit normal of the bow's plane."""
        return vec.unit(vec.cross(self.u, self.v))

    @property
    def axis(self) -> int:
        """Index of the diametral axis this bow sits on, 0..4.

        Three bows share each axis, which is the reference's "3 bows from
        each bottom point".
        """
        return min(self.foot_a, self.foot_b) % 5

    def point(self, t_deg: float, radius: float) -> Vec3:
        t = math.radians(t_deg)
        c, s = math.cos(t), math.sin(t)
        u, v = self.u, self.v
        return (
            radius * (c * u[0] + s * v[0]),
            radius * (c * u[1] + s * v[1]),
            radius * (c * u[2] + s * v[2]),
        )

    def tangent(self, t_deg: float) -> Vec3:
        """Unit tangent, in the direction of increasing t."""
        t = math.radians(t_deg)
        c, s = math.cos(t), math.sin(t)
        u, v = self.u, self.v
        return vec.unit(
            (
                -s * u[0] + c * v[0],
                -s * u[1] + c * v[1],
                -s * u[2] + c * v[2],
            )
        )

    def t_of(self, p: Vec3) -> float:
        """Arc angle of a point known to lie on this bow's great circle."""
        return math.degrees(math.atan2(vec.dot(p, self.v), vec.dot(p, self.u))) % 360.0

    def arclength(self, t_deg: float, radius: float) -> float:
        return radius * math.radians(t_deg)

    def length(self, radius: float) -> float:
        """Half a great circle: the same for all 15 bows, by design."""
        return math.pi * radius

    def tie_marks_deg(self) -> tuple:
        return MARKS_FIFTHS if self.family == "G" else MARKS_THIRDS

    def polyline(self, radius: float, segments: int) -> list:
        return [self.point(180.0 * i / segments, radius) for i in range(segments + 1)]


def _tilt_from_node_height(z_over_r: float) -> float:
    """Tilt that puts a thirds mark (t = 60) at the given node height.

    ``sin(60) * sin(tilt) = z/R``. This is why families U and L are not free
    parameters: their tilts are fixed by the node heights family G already
    created.
    """
    return math.degrees(math.asin(z_over_r / math.sin(math.radians(60.0))))


def family_tilts() -> dict:
    """The three family tilts, all derived from family G.

    Family G is seeded with the icosahedral angle. Its own crossings then sit
    at t = 36 and t = 72, whose heights fix the tilts of U and L.
    """
    sin_g = math.sin(math.radians(TILT_G))
    z_low = math.sin(math.radians(36.0)) * sin_g   # G-G crossings at t = 36/144
    z_high = math.sin(math.radians(72.0)) * sin_g  # G-G crossings at t = 72/108
    return {
        "G": TILT_G,
        "U": _tilt_from_node_height(z_high),
        "L": _tilt_from_node_height(z_low),
    }


def build_bows() -> list:
    """The 15 bows: 5 of family G, 5 of U, 5 of L.

    Family G starts from the odd base points, families U and L from the even
    ones. Each bow ends at the base point diametrically opposite its start,
    which flips the parity, so every one of the 10 base points ends up with
    exactly one G, one U and one L rod end -- the reference's 3 bow ends per
    ground point.

    ``layer`` is the rod's index in this list. It doubles as the weave shell
    index: a drawing convention for which rod passes outside at a crossing,
    NOT a build decision. See dome/README.md.
    """
    tilts = family_tilts()
    bows = []
    layer = 0
    for family, first_foot in (("G", 1), ("U", 0), ("L", 0)):
        for k in range(5):
            foot_a = (first_foot + 2 * k) % BASE_POINT_COUNT
            bows.append(
                Bow(
                    name=f"{family}{k + 1}",
                    family=family,
                    number=layer + 1,
                    azimuth_deg=foot_a * BASE_STEP_DEG,
                    tilt_deg=tilts[family],
                    foot_a=foot_a,
                    foot_b=(foot_a + 5) % BASE_POINT_COUNT,
                    layer=layer,
                )
            )
            layer += 1
    return bows


def base_points(radius: float) -> list:
    """The 10 ground points, b0 at azimuth 0."""
    out = []
    for i in range(BASE_POINT_COUNT):
        a = math.radians(i * BASE_STEP_DEG)
        out.append((radius * math.cos(a), radius * math.sin(a), 0.0))
    return out
