"""Crossings, nodes and symmetry classes.

Nothing here is hand-placed. Crossings are found by intersecting the bows'
great-circle planes; nodes are found by clustering coincident crossing points;
symmetry classes are found by grouping crossings under a D5 invariant.

Ordering conventions are chosen so that IDs depend on *where* a node is, not
on loop order, and therefore stay stable across runs and variants:

- nodes are ordered top of dome first, then by azimuth  -> N00 .. N39
- classes are ordered by height, then by angle          -> T00 .. T11

These match the OpenSCAD model in ``dome/`` so that both producers emit
interchangeable data. See docs/architecture.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import vec
from .geometry import Bow
from .vec import Vec3

# Tolerance for deciding that two crossing points are the same node, in mm.
# Coordinates are order 1e3 mm and computed in float64, so the real spread is
# around 1e-10; this is a generous margin that still cannot merge two
# genuinely distinct nodes (the closest distinct pair is order 1e2 mm apart).
POINT_TOL = 1e-6

DECIMALS = 6


def quantize(x: float, decimals: int = DECIMALS) -> float:
    return round(x, decimals)


def norm_az(a: float) -> float:
    return (a % 360.0 + 360.0) % 360.0


def fold_t(t: float) -> float:
    """Fold an arc position about the midpoint of the bow.

    A bow has no intrinsic direction, so t and 180-t describe the same
    position measured from either end. Folding makes the signature blind to
    which end the parameter runs from.
    """
    return min(t, 180.0 - t)


@dataclass
class Crossing:
    """One rod-to-rod contact."""

    index: int
    bow_a: Bow
    bow_b: Bow
    point: Vec3
    t_a: float
    t_b: float
    tangent_a: Vec3
    tangent_b: Vec3
    angle: float
    incl_a: float
    incl_b: float
    radial_gap: float
    node: int = -1
    tied: int = 0
    type_index: int = -1
    # Where each rod sits radially AT THIS CROSSING. Under the constant-offset
    # modes these are the rod's one offset; under ``woven`` they are its route
    # sampled here, and the same rod is above at one crossing and below at the
    # next. That is the whole point of a weave.
    offset_a: float = 0.0
    offset_b: float = 0.0

    def _outer_is_a(self) -> bool:
        if abs(self.offset_a - self.offset_b) > 1e-9:
            return self.offset_a > self.offset_b
        # Flat mode has no separation to read, so the drawing layer decides
        # and the answer stays the one it always gave.
        return self.bow_a.layer > self.bow_b.layer

    @property
    def rod_above(self) -> str:
        return self.bow_a.name if self._outer_is_a() else self.bow_b.name

    @property
    def rod_below(self) -> str:
        return self.bow_b.name if self._outer_is_a() else self.bow_a.name

    def signature(self) -> tuple:
        """A D5 invariant: equal signatures mean geometrically identical crossings.

        The group preserves height, the acute angle between two rods, whether
        the crossing is a lashed junction, the families involved, and each
        rod's folded arc position.
        """
        fams = tuple(sorted((self.bow_a.family, self.bow_b.family)))
        ts = tuple(sorted((quantize(fold_t(self.t_a)), quantize(fold_t(self.t_b)))))
        return (
            fams[0],
            fams[1],
            ts[0],
            ts[1],
            quantize(self.point[2]),
            quantize(self.angle),
            self.tied,
        )


WEAVE_MODES = ("flat", "layered", "woven")


def _radial_offsets(bows: list, rod_diameter: float, weave_mode: str, weave_gap: float) -> dict:
    """Per-rod radial offset from the nominal sphere.

    ``flat`` puts every centreline exactly on the nominal sphere -- the mode
    to use for measurement and for exported coordinates. ``layered`` gives
    each bow its own shell so that crossings read as clean over/under; it is
    a drawing convention only.

    ``woven`` has no per-rod constant to return, because a rod's offset
    changes along its own length -- that is what makes it a weave rather than
    a stack of shells. It comes back as zero here and arrives instead as the
    ``offset_fn`` that ``crossings`` and the model builder take, solved by
    ``weave.global_profile``.
    """
    if weave_mode in ("flat", "woven"):
        return {b.name: 0.0 for b in bows}
    if weave_mode != "layered":
        raise ValueError(
            f"unknown weave_mode {weave_mode!r} -- use one of {WEAVE_MODES}"
        )
    mid = (len(bows) - 1) / 2.0
    return {b.name: (b.layer - mid) * weave_gap * rod_diameter for b in bows}


def crossings(
    bows: list,
    radius: float,
    rod_diameter: float = 0.0,
    weave_mode: str = "flat",
    weave_gap: float = 1.0,
    offset_fn=None,
) -> list:
    """Every rod-to-rod crossing above the ground plane.

    Two bows on the same diametral axis share both endpoints, and their great
    circles meet only there, at z = 0. Those pairs are base points, not
    crossings, so they are skipped. Every other pair meets at exactly one
    point above ground: each bow is the upper half of its great circle, and
    two distinct great circles meet at one antipodal pair.

    ``rod_diameter``, ``weave_mode`` and ``weave_gap`` affect only the
    reported radial gap, never the coordinates.

    ``offset_fn(rod_name, t)`` overrides the per-rod constant where the offset
    varies along the rod, which is the ``woven`` mode. It cannot be worked out
    here: the route is solved from the crossings, so it is handed back in on a
    second pass.
    """
    offsets = _radial_offsets(bows, rod_diameter, weave_mode, weave_gap)
    if offset_fn is None:
        def offset_fn(name, t, _o=offsets):
            return _o[name]
    out = []
    for i in range(len(bows)):
        for j in range(i + 1, len(bows)):
            a, b = bows[i], bows[j]
            if a.axis == b.axis:
                continue
            direction = vec.cross(a.normal, b.normal)
            p = vec.scale(vec.unit(direction), radius)
            if p[2] < 0.0:
                p = vec.neg(p)
            t_a, t_b = a.t_of(p), b.t_of(p)
            tan_a, tan_b = a.tangent(t_a), b.tangent(t_b)
            off_a, off_b = offset_fn(a.name, t_a), offset_fn(b.name, t_b)
            out.append(
                Crossing(
                    index=len(out),
                    bow_a=a,
                    bow_b=b,
                    point=p,
                    t_a=t_a,
                    t_b=t_b,
                    tangent_a=tan_a,
                    tangent_b=tan_b,
                    angle=vec.crossing_angle(tan_a, tan_b),
                    incl_a=math.degrees(math.asin(min(1.0, abs(tan_a[2])))),
                    incl_b=math.degrees(math.asin(min(1.0, abs(tan_b[2])))),
                    radial_gap=abs(off_a - off_b),
                    offset_a=off_a,
                    offset_b=off_b,
                )
            )
    return out


def nodes(xs: list) -> list:
    """Distinct crossing points, ordered top of dome first, then by azimuth."""
    unique: list = []
    for c in xs:
        if not any(vec.dist(p, c.point) < POINT_TOL for p in unique):
            unique.append(c.point)
    unique.sort(key=lambda p: (-quantize(p[2]), quantize(norm_az(math.degrees(math.atan2(p[1], p[0]))))))
    return unique


def node_name(i: int) -> str:
    return f"N{i:02d}"


def type_name(i: int) -> str:
    return f"T{i:02d}"


def assign_nodes(xs: list, node_points: list) -> None:
    """Attach node indices, then mark which crossings are lashed junctions.

    A crossing is tied when four rods pass through the same point. Those are
    the reference's lashed junctions, and they land exactly on the rod
    marking distances -- 4 fifth marks per family-G rod, 2 third marks per
    U or L rod. ``verify`` asserts that correspondence rather than assuming
    it.
    """
    for c in xs:
        for i, p in enumerate(node_points):
            if vec.dist(p, c.point) < POINT_TOL:
                c.node = i
                break
        else:  # pragma: no cover - unreachable while node_points comes from nodes()
            raise AssertionError(f"crossing {c.index} matched no node")

    rods_at: list = [set() for _ in node_points]
    for c in xs:
        rods_at[c.node].add(c.bow_a.name)
        rods_at[c.node].add(c.bow_b.name)
    for c in xs:
        c.tied = 1 if len(rods_at[c.node]) == 4 else 0


def classes(xs: list) -> list:
    """Symmetry-distinct crossing geometries, ordered by height then angle.

    This is the number that matters for connector design: it is how many
    genuinely different parts the crossing connector family has to cover.
    """
    seen: list = []
    for c in xs:
        sig = c.signature()
        if sig not in seen:
            seen.append(sig)
    order = sorted(
        seen,
        key=lambda s: (-s[4], s[5]),
    )
    for c in xs:
        c.type_index = order.index(c.signature())
    return order


def rods_at_node(xs: list, node_index: int, bows: list) -> list:
    """Rod names passing through a node, in rod order."""
    names = set()
    for c in xs:
        if c.node == node_index:
            names.add(c.bow_a.name)
            names.add(c.bow_b.name)
    return [b.name for b in bows if b.name in names]


def rods_at_base_point(bows: list, foot: int) -> list:
    return [b.name for b in bows if foot in (b.foot_a, b.foot_b)]
