"""Wind-resultant and mass screening for the configured cover geometry.

Internal pressure is evaluated as independent signed cases. The closed smooth
shell pressure approximation is not a validated aerodynamic model of fabric,
doors or a connected camp. Tributary areas are a nearest-sample partition,
not a solved load path. See docs/strength.md for scope and equations.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import cover, vec

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "loads.toml"

# Whether the dome's one dominant opening is letting the wind in. `open` is
# the door facing the wind, which is the worst case for uplift.
DOOR_STATES = ("shut", "open")

# How finely the cover is diced to integrate pressure over it. Finer than the
# mesh `cover.mesh` hands a renderer, because this one is being integrated
# rather than drawn, and the tributary partition is only as sharp as the
# facets are small.
LOAD_MERIDIANS = 120
LOAD_PARALLELS = 48


@dataclass(frozen=True)
class Loads:
    """Everything in ``configs/loads.toml``, resolved."""

    air_density_kg_m3: float
    cp_windward: float
    cp_crown: float
    cp_lee: float
    cp_internal_open: float
    cp_internal_closed: float
    gravity_m_s2: float
    fabric_g_m2: float
    plastic_density_kg_m3: float
    infill_fraction: float
    hem_rope_g_m: float
    webbing_g_m: float
    anchor_capacity_n: float
    anchor_shear_capacity_n: float
    anchor_count: int
    cp_internal_closed_positive: float = 0.2

    def __post_init__(self):
        for name, value in vars(self).items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        for name in ("air_density_kg_m3", "gravity_m_s2", "anchor_capacity_n",
                     "anchor_shear_capacity_n", "anchor_count"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        for name in ("fabric_g_m2", "plastic_density_kg_m3", "hem_rope_g_m", "webbing_g_m"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if not 0 <= self.infill_fraction <= 1:
            raise ValueError("infill_fraction must be between zero and one")
        if int(self.anchor_count) != self.anchor_count:
            raise ValueError("anchor_count must be an integer")


def load(path=None) -> Loads:
    """Read loads; older configurations receive the missing +0.2 shut case."""
    path = Path(path) if path is not None else DEFAULT_CONFIG
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)
    wind, weights, anchors = raw["wind"], raw["weights"], raw["anchors"]
    count = float(anchors["count"])
    if not math.isfinite(count) or not count.is_integer():
        raise ValueError("anchor_count must be a finite integer")
    return Loads(
        air_density_kg_m3=float(wind["air_density_kg_m3"]),
        cp_windward=float(wind["cp_windward"]),
        cp_crown=float(wind["cp_crown"]),
        cp_lee=float(wind["cp_lee"]),
        cp_internal_open=float(wind["cp_internal_open"]),
        cp_internal_closed=float(wind["cp_internal_closed"]),
        cp_internal_closed_positive=float(wind.get("cp_internal_closed_positive", 0.2)),
        gravity_m_s2=float(weights["gravity_m_s2"]),
        fabric_g_m2=float(weights["fabric_g_m2"]),
        plastic_density_kg_m3=float(weights["plastic_density_kg_m3"]),
        infill_fraction=float(weights["infill_fraction"]),
        hem_rope_g_m=float(weights["hem_rope_g_m"]),
        webbing_g_m=float(weights["webbing_g_m"]),
        anchor_capacity_n=float(anchors["capacity_n"]),
        anchor_shear_capacity_n=float(anchors["shear_capacity_n"]),
        anchor_count=int(count),
    )


# --- wind pressure ----------------------------------------------------------


def velocity_pressure(speed_ms: float, loads: Loads) -> float:
    """``0.5 rho v^2``, in pascals.

    The speed is the PEAK GUST at the dome, not a code's reference velocity at
    10 m in open country. There is no terrain category and no height profile
    in this project, because those describe a site and this repository
    describes a dome -- see configs/loads.toml.
    """
    if not math.isfinite(speed_ms) or speed_ms < 0:
        raise ValueError("wind speed must be finite and non-negative")
    return 0.5 * loads.air_density_kg_m3 * speed_ms * speed_ms


def shape_coefficient(polar_deg: float, loads: Loads) -> float:
    """External pressure coefficient at a point on the shell.

    ``polar_deg`` is the angle between the point's outward normal and the
    direction the wind is coming FROM: 0 at the windward springing, 90 at the
    crown and at the two sides, 180 in the wake. Linear between the three
    tabulated points, which is how EN 1991-1-4 figure 7.12 is read.

    The great-circle angle extends the tabulated meridian over the cover.
    Applying ground-level hemisphere coefficients to a raised skirt or a
    flexible, open fabric cover remains an unvalidated approximation.
    """
    t = max(0.0, min(180.0, polar_deg))
    if t <= 90.0:
        f = t / 90.0
        return loads.cp_windward + f * (loads.cp_crown - loads.cp_windward)
    f = (t - 90.0) / 90.0
    return loads.cp_crown + f * (loads.cp_lee - loads.cp_crown)


def internal_coefficient(door: str, loads: Loads) -> float:
    """Positive internal pressure case used by the single-field API.

    This is the uplift case, not an envelope of every limit state. Use
    `pressure_cases` and pass each `cp_internal` for a complete screening.
    """
    if door == "open":
        return loads.cp_internal_open
    if door == "shut":
        return max(loads.cp_internal_closed, loads.cp_internal_closed_positive)
    raise ValueError(f"unknown door state {door!r} -- use one of {DOOR_STATES}")


def pressure_cases(door: str, loads: Loads) -> tuple:
    """Independent internal-pressure cases; never blend their force fields."""
    internal_coefficient(door, loads)  # validate even for an empty geometry
    if door == "open":
        return (loads.cp_internal_open,)
    return tuple(sorted({loads.cp_internal_closed, loads.cp_internal_closed_positive}))


# --- the cover, diced and pushed on -----------------------------------------


def _facets(data: dict, meridians: int, parallels: int) -> list:
    """Cover facets as ``(centroid, area_mm2, outward_normal, is_skirt)``.

    Triangulates whatever `cover.mesh` produced -- quads over the dome and the
    skirt, triangles at the apex -- so the area is exact for the mesh rather
    than approximated by a quad's diagonal.
    """
    mesh = cover.mesh(data, meridians=meridians, parallels=parallels)
    verts = mesh["vertices"]
    ground = data["meta"].get("ground_z", 0.0)
    skirt = data["meta"].get("skirt_height", 0.0) or 0.0

    out = []
    for face in mesh["faces"]:
        corners = [verts[i] for i in face]
        for a, b, c in ((corners[0], corners[i], corners[i + 1])
                        for i in range(1, len(corners) - 1)):
            ab = vec.sub(b, a)
            ac = vec.sub(c, a)
            cross = vec.cross(ab, ac)
            area = 0.5 * vec.norm(cross)
            if area <= 0.0:
                continue
            centroid = [(a[i] + b[i] + c[i]) / 3.0 for i in range(3)]
            normal = vec.unit(cross)
            # cover.mesh winds its rings consistently, but rather than trust
            # that, point every normal away from the dome's own centre. The
            # centre of a bare dome is the origin at ground level; with a
            # skirt the sphere sits on top of it.
            centre = [0.0, 0.0, ground + skirt]
            if vec.dot(normal, vec.sub(centroid, centre)) < 0.0:
                normal = vec.neg(normal)
            out.append((centroid, area, normal, centroid[2] < ground + skirt - 1e-6))
    return out


def facet_loads(data: dict, speed_ms: float, loads: Loads,
                azimuth_deg: float = 0.0, door: str = "shut",
                meridians: int = LOAD_MERIDIANS,
                parallels: int = LOAD_PARALLELS, *, cp_internal=None) -> list:
    """Every cover facet with the wind force on it, in newtons.

    ``azimuth_deg`` is the direction the wind blows TOWARDS, in the same
    azimuth convention the rest of the model uses. Force is positive outward
    when the net coefficient is suction, which is most of the shell.
    """
    q = velocity_pressure(speed_ms, loads)
    default_cpi = internal_coefficient(door, loads)
    cpi = default_cpi if cp_internal is None else cp_internal
    if not math.isfinite(cpi) or not math.isfinite(azimuth_deg):
        raise ValueError("pressure coefficient and wind direction must be finite")
    a = math.radians(azimuth_deg)
    downwind = [math.cos(a), math.sin(a), 0.0]
    ground = data["meta"].get("ground_z", 0.0)
    skirt = data["meta"].get("skirt_height", 0.0) or 0.0
    centre = [0.0, 0.0, ground + skirt]

    out = []
    for centroid, area, normal, is_skirt in _facets(data, meridians, parallels):
        radial = vec.unit(vec.sub(centroid, centre))
        # Angle from the windward stagnation direction, which is -downwind.
        cos_t = max(-1.0, min(1.0, -vec.dot(radial, downwind)))
        polar = math.degrees(math.acos(cos_t))
        cpe = shape_coefficient(polar, loads)
        pressure = q * (cpe - cpi)          # Pa, positive pushes inward
        # Pa * mm^2 = 1e-6 N. Inward is -normal.
        magnitude = -pressure * area * 1e-6
        force = [magnitude * n for n in normal]
        out.append(
            {
                "centroid": centroid,
                "area_mm2": area,
                "normal": normal,
                "polar_deg": polar,
                "cp_external": cpe,
                "pressure_pa": pressure,
                "force_n": force,
                "skirt": is_skirt,
            }
        )
    return out


# --- which bow carries which piece of cover ---------------------------------


def _bow_points(data: dict) -> list:
    """``(rod name, index, point)`` for every sample on every bow centreline.

    Needs the model built with polylines. Without them there is no centreline
    to be near, and guessing one from the tie marks would be the kind of
    recomputation `AGENTS.md` calls an architecture bug.
    """
    from . import geometry, span

    out = []
    for rod in data["rods"]:
        points = rod.get("points")
        if not points:
            raise ValueError(
                f"rod {rod['name']} has no polyline. Build the model with "
                "include_polylines=True -- the tributary partition needs a "
                "centreline to measure distance to."
            )
        bow = geometry.Bow(**{k: rod[k] for k in (
            "name", "family", "number", "azimuth_deg", "tilt_deg", "foot_a", "foot_b", "layer"
        )})
        live = span.live_intervals(rod)
        for i, point in enumerate(points):
            t = bow.t_of(point)
            if t > 360 - 1e-6:
                t = 0.0
            if not any(lo - 1e-6 <= t <= hi + 1e-6 for lo, hi in live):
                continue
            out.append((rod["name"], i, point))
    if not out:
        raise ValueError("no live bow samples to carry the cover")
    return out


def scatter(data: dict, facets: list) -> dict:
    """Assign each cover facet to the nearest point on the nearest bow.

    A partition, not a smearing: every facet goes to exactly one bow, so the
    tributary areas sum to the cover area with no residue. That identity is
    the test that this function is right.

    Skirt facets are assigned too, but flagged, because the skirt is its own
    structure -- posts, two rings and crossed diagonals, see docs/skirt.md --
    and its wind is not the bows' to carry. `analyse` reports the split.
    """
    samples = _bow_points(data)
    by_rod: dict = {rod["name"]: [] for rod in data["rods"]}
    skirt_area = 0.0
    skirt_force = [0.0, 0.0, 0.0]

    for facet in facets:
        if facet["skirt"]:
            skirt_area += facet["area_mm2"]
            skirt_force = vec.add(skirt_force, facet["force_n"])
            continue
        centroid = facet["centroid"]
        best, best_d2 = None, None
        for name, index, point in samples:
            dx = point[0] - centroid[0]
            dy = point[1] - centroid[1]
            dz = point[2] - centroid[2]
            d2 = dx * dx + dy * dy + dz * dz
            if best_d2 is None or d2 < best_d2:
                best, best_d2 = (name, index), d2
        by_rod[best[0]].append((best[1], facet))

    return {
        "by_rod": by_rod,
        "skirt_area_mm2": skirt_area,
        "skirt_force_n": skirt_force,
    }


def tributary(data: dict, meridians: int = LOAD_MERIDIANS,
              parallels: int = LOAD_PARALLELS) -> dict:
    """How much cover each bow carries, in mm^2, and as a strip width.

    The width is the area over the bow's own drawn length -- an average, and
    reported as one, because the real strip is wider near the crown where five
    bows converge than it is near a foot.
    """
    facets = [
        {"centroid": c, "area_mm2": a, "normal": n, "force_n": [0.0, 0.0, 0.0],
         "skirt": s}
        for c, a, n, s in _facets(data, meridians, parallels)
    ]
    spread = scatter(data, facets)
    lengths = live_lengths(data)
    per_rod = {}
    for name, items in spread["by_rod"].items():
        area = sum(f["area_mm2"] for _, f in items)
        per_rod[name] = {
            "area_mm2": round(area, 3),
            "width_mm": round(area / lengths[name], 3) if lengths[name] else 0.0,
            "facets": len(items),
        }
    return {
        "per_rod": per_rod,
        "dome_area_mm2": round(sum(v["area_mm2"] for v in per_rod.values()), 3),
        "skirt_area_mm2": round(spread["skirt_area_mm2"], 3),
    }


# --- what the whole dome feels ----------------------------------------------


def resultants(data: dict, speed_ms: float, loads: Loads,
               azimuth_deg: float = 0.0, door: str = "shut",
               meridians: int = LOAD_MERIDIANS,
               parallels: int = LOAD_PARALLELS, *, cp_internal=None) -> dict:
    """Force and signed moment about (0, 0, ground_z), from one pressure field.

    The ideal bare sphere has almost no resultant moment about its centre.
    That geometric fact does not establish the real structure's failure mode.
    Legacy per-anchor fields are arithmetic averages, not support demands.
    """
    facets = facet_loads(data, speed_ms, loads, azimuth_deg, door,
                         meridians, parallels, cp_internal=cp_internal)
    ground = data["meta"].get("ground_z", 0.0)
    total = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    area = 0.0
    for facet in facets:
        force = facet["force_n"]
        arm = [facet["centroid"][0], facet["centroid"][1],
               facet["centroid"][2] - ground]
        total = vec.add(total, force)
        moment = vec.add(moment, vec.cross(arm, force))
        area += facet["area_mm2"]
    drag = math.hypot(total[0], total[1])
    return {
        "speed_ms": speed_ms,
        "door": door,
        "azimuth_deg": azimuth_deg,
        "velocity_pressure_pa": round(velocity_pressure(speed_ms, loads), 3),
        "cp_internal": internal_coefficient(door, loads) if cp_internal is None else cp_internal,
        "area_mm2": round(area, 3),
        "force_n": [round(v, 3) for v in total],
        "moment_nmm": [round(v, 3) for v in moment],
        "lift_n": round(total[2], 3),
        "drag_n": round(drag, 3),
        # About the horizontal axis across the wind, at ground level. Zero for
        # a bare dome by the argument in the docstring; non-zero once a skirt
        # lifts the sphere's centre off the ground.
        "overturning_nmm": round(math.hypot(moment[0], moment[1]), 3),
        # What one driven angle is asked to hold, if the ten share equally.
        #
        # THEY DO NOT. The windward feet stand in positive pressure and are
        # pushed down; the side and lee feet are in suction and are pulled up,
        # so the worst foot sees more than this and the best sees less. How
        # much more is a question about how the lattice distributes load,
        # which is exactly what a frame solve answers and a rigid-body sum
        # cannot. Until then this is an average wearing the word "per".
        "uplift_per_anchor_n": round(total[2] / max(1, loads.anchor_count), 3),
        "shear_per_anchor_n": round(drag / max(1, loads.anchor_count), 3),
        "anchor_capacity_n": loads.anchor_capacity_n,
        "anchor_shear_capacity_n": loads.anchor_shear_capacity_n,
    }


def live_lengths(data: dict) -> dict:
    """Nominal surviving rod lengths, matching the cut schedule, in mm.

    Radial weave corrections and finite ferrule stiffness are not resolved.
    Removed material must not retain self-weight or tributary length.
    """
    from . import span
    radius = data["meta"]["dome_radius"]
    return {r["name"]: radius * math.radians(sum(hi-lo for lo, hi in span.live_intervals(r)))
            for r in data["rods"]}


def self_weight(data: dict, material, loads: Loads,
                plastic_cm3: float = 0.0) -> dict:
    """Partial mass inventory in kg and N, with explicit exclusions.

    Optional plastic volume is supplied by the caller; this function does
    not read CAD meshes automatically. Zero is unmeasured, not weightless.
    """
    if not math.isfinite(plastic_cm3) or plastic_cm3 < 0:
        raise ValueError("plastic volume must be finite and non-negative")
    meta = data["meta"]
    g = loads.gravity_m_s2
    rod_m = sum(live_lengths(data).values()) / 1000.0
    rod_kg = rod_m * material.linear_mass(meta["rod_diameter"])

    # Include the door panels in the inventory. The same closed shell is used
    # for the wind and member screening; opening geometry is not solved yet.
    fabric_m2 = cover.areas(data)["gross_m2"]
    fabric_kg = fabric_m2 * loads.fabric_g_m2 / 1000.0

    plastic_kg = plastic_cm3 * loads.infill_fraction \
        * loads.plastic_density_kg_m3 / 1e6

    attachment = data.get("attachment", {})
    rope_kg = attachment.get("hem", {}).get("rope_length_mm", 0.0) * loads.hem_rope_g_m / 1e6
    webbing_kg = attachment.get("webbing_total_m", 0.0) * loads.webbing_g_m / 1000.0
    total_kg = rod_kg + fabric_kg + plastic_kg + rope_kg + webbing_kg
    return {
        "rod_kg": round(rod_kg, 3),
        "fabric_kg": round(fabric_kg, 3),
        "plastic_kg": round(plastic_kg, 3),
        "rope_kg": round(rope_kg, 3),
        "webbing_kg": round(webbing_kg, 3),
        "total_kg": round(total_kg, 3),
        "total_n": round(total_kg * g, 3),
        # What a bow carries of itself, per unit length. The load case that
        # never comes off, and the one span.py scales as w ~ d^2.
        "rod_n_per_mm": round(
            material.linear_mass(meta["rod_diameter"]) * g / 1000.0, 9
        ),
        "plastic_measured": plastic_cm3 > 0.0,
        "basis": "nominal live rods, closed cover including doors, rope and webbing; "
                 "steel hardware, skirt stock and unbuilt plastic are not included",
    }


def analyse(data: dict, material, loads: Loads, speed_ms: float = 20.0,
            door: str = "shut") -> dict:
    """Independent wind cases and a partial weight inventory."""
    from . import reactions
    cases = []
    for cpi in pressure_cases(door, loads):
        wind = resultants(data, speed_ms, loads, door=door, cp_internal=cpi)
        cases.append({**wind, "anchor_screening": reactions.distribute(
            data["base_nodes"], wind["force_n"], wind["moment_nmm"])})
    return {
        "schema": "star_dome_loads/2", "variant": data["meta"]["variant"],
        "speed_ms": speed_ms, "door": door, "status": "screening_only",
        "wind": max(cases, key=lambda c: c["lift_n"]),
        "wind_cases": cases, "azimuth_deg": 0.0,
        "tributary": tributary(data), "weight": self_weight(data, material, loads),
    }


def format_analysis(data: dict, material, loads: Loads,
                    speed_ms: float = 20.0, door: str = "shut") -> str:
    a = analyse(data, material, loads, speed_ms, door)
    t, m = a["tributary"], a["weight"]
    out = [f"--- {a['variant']} wind screening at {speed_ms:g} m/s, door {door}",
           "  Direction: 0 degrees; use strength for the full-circle sample."]
    for w in a["wind_cases"]:
        r = w["anchor_screening"]
        out += [f"  cpi {w['cp_internal']:+.2f}: lift {w['lift_n']:.0f} N, drag {w['drag_n']:.0f} N",
                f"    overturning {w['overturning_nmm']/1000:.1f} N*m",
                f"    rigid-base anchor maximum: uplift {r['max_uplift_n']:.0f} N, shear {r['max_shear_n']:.0f} N",
                f"    {r['note']}"]
    out += [f"  Cover partition: {t['dome_area_mm2']/1e6:.2f} m2 onto live bows",
            f"  Partial mass: rods {m['rod_kg']:.2f}, fabric {m['fabric_kg']:.2f}, plastic {m['plastic_kg']:.2f}, "
            f"rope {m['rope_kg']:.2f}, webbing {m['webbing_kg']:.2f} kg",
            f"  Total of included items: {m['total_kg']:.2f} kg = {m['total_n']:.0f} N",
            f"  Basis: {m['basis']}",
            "  No operational wind limit or complete structural validation is established."]
    return "\n".join(out)
