"""What the dome is asked to carry.

`material.py` says what the rod can take. This says what is asked of it, and
between them they are the two halves `docs/span.md` is missing when it says
"there is no modulus, no strength and no load anywhere in it".

## Wind only, and that is a decision

There is no snow here. A Star Dome is a temporary event structure: it goes up
for a weekend and comes down again, and it is not standing in February.
Leaving snow out is what turns the answer into a **wind speed** rather than a
map of Russia. See `configs/loads.toml`, which is where snow would go if that
operating rule ever stopped being true, and decision 0021.

## The wind on this dome is mostly lift, not push

Worth saying before any of the machinery, because it decides what the answer
will be about. The pressure coefficient on a hemisphere is positive only near
the windward springing and negative over most of the rest -- `+0.8` at the
windward base, `-1.2` over the crown, `-0.4` in the wake. Integrate that over
a dome and the resultant is dominated by **suction lifting the whole thing off
its ten anchors**, not by drag pushing it sideways.

Which means the limiting wind speed is quite likely to be set by the anchors
rather than by the rod, and that the field rule this work produces is about
pegs and about shutting the door.

## The door is a hole in a sealed shell, and it matters

A dome has exactly one dominant opening. Facing the wind it lets internal
pressure in, which pushes outward everywhere the outside is already sucking --
the worst case for uplift by a wide margin. Shut, or turned away, the internal
coefficient goes slightly negative and helps. Both readings are computed and
the gap between them is the price of leaving the door open, in m/s.

## The tributary strip is not estimated, it is partitioned

A bow carries the wind over a strip of cover as wide as its share of the
shell. Guessing that width as "cover area over rod length" is within a few per
cent on average and wrong everywhere in particular -- the strips are wider
near the crown, where five bows converge, than near the feet.

So it is not guessed. `cover.mesh` already builds the fabric surface at the
radius it actually rests on; every facet of it is assigned to the nearest bow
centreline, and the assignment is a **partition**: each square millimetre goes
to exactly one bow. Two identities follow and both are tests:

- the tributary areas sum to `cover.areas`' own total, exactly;
- the scattered forces sum to the resultant computed independently.

That is the same class of check `cover.py` keeps on its gore widths.

```bash
python3 -m stardome loads M --wind 20
python3 -m stardome loads --all --wind 25 --door open
```

Nothing here is a strength check; that is `strength.py`. And the pressure
coefficients are for a smooth sealed hemisphere in a wind tunnel, which a
lattice of round rods under a flogging membrane with a hole in it is not --
the largest single uncertainty in this work, named as such in
docs/strength.md.
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


def load(path=None) -> Loads:
    """Read the load configuration. No defaults in code -- it is all in TOML."""
    path = Path(path) if path is not None else DEFAULT_CONFIG
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)
    wind, weights, anchors = raw["wind"], raw["weights"], raw["anchors"]
    return Loads(
        air_density_kg_m3=float(wind["air_density_kg_m3"]),
        cp_windward=float(wind["cp_windward"]),
        cp_crown=float(wind["cp_crown"]),
        cp_lee=float(wind["cp_lee"]),
        cp_internal_open=float(wind["cp_internal_open"]),
        cp_internal_closed=float(wind["cp_internal_closed"]),
        gravity_m_s2=float(weights["gravity_m_s2"]),
        fabric_g_m2=float(weights["fabric_g_m2"]),
        plastic_density_kg_m3=float(weights["plastic_density_kg_m3"]),
        infill_fraction=float(weights["infill_fraction"]),
        hem_rope_g_m=float(weights["hem_rope_g_m"]),
        webbing_g_m=float(weights["webbing_g_m"]),
        anchor_capacity_n=float(anchors["capacity_n"]),
        anchor_shear_capacity_n=float(anchors["shear_capacity_n"]),
        anchor_count=int(anchors["count"]),
    )


# --- wind pressure ----------------------------------------------------------


def velocity_pressure(speed_ms: float, loads: Loads) -> float:
    """``0.5 rho v^2``, in pascals.

    The speed is the PEAK GUST at the dome, not a code's reference velocity at
    10 m in open country. There is no terrain category and no height profile
    in this project, because those describe a site and this repository
    describes a dome -- see configs/loads.toml.
    """
    return 0.5 * loads.air_density_kg_m3 * speed_ms * speed_ms


def shape_coefficient(polar_deg: float, loads: Loads) -> float:
    """External pressure coefficient at a point on the shell.

    ``polar_deg`` is the angle between the point's outward normal and the
    direction the wind is coming FROM: 0 at the windward springing, 90 at the
    crown and at the two sides, 180 in the wake. Linear between the three
    tabulated points, which is how EN 1991-1-4 figure 7.12 is read.

    On the windward-leeward meridian this is exactly the figure. Off it, the
    great-circle angle is the natural generalisation and is what makes one
    table cover a whole dome -- and one table covers the whole *family*, too,
    because the rise-to-span ratio is a constant of the topology, the same at
    D3 and at D12.
    """
    t = max(0.0, min(180.0, polar_deg))
    if t <= 90.0:
        f = t / 90.0
        return loads.cp_windward + f * (loads.cp_crown - loads.cp_windward)
    f = (t - 90.0) / 90.0
    return loads.cp_crown + f * (loads.cp_lee - loads.cp_crown)


def internal_coefficient(door: str, loads: Loads) -> float:
    """Internal pressure coefficient, by what the door is doing."""
    if door == "open":
        return loads.cp_internal_open
    if door == "shut":
        return loads.cp_internal_closed
    raise ValueError(f"unknown door state {door!r} -- use one of {DOOR_STATES}")


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
                parallels: int = LOAD_PARALLELS) -> list:
    """Every cover facet with the wind force on it, in newtons.

    ``azimuth_deg`` is the direction the wind blows TOWARDS, in the same
    azimuth convention the rest of the model uses. Force is positive outward
    when the net coefficient is suction, which is most of the shell.
    """
    q = velocity_pressure(speed_ms, loads)
    cpi = internal_coefficient(door, loads)
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
    out = []
    for rod in data["rods"]:
        points = rod.get("points")
        if not points:
            raise ValueError(
                f"rod {rod['name']} has no polyline. Build the model with "
                "include_polylines=True -- the tributary partition needs a "
                "centreline to measure distance to."
            )
        for i, point in enumerate(points):
            out.append((rod["name"], i, point))
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
    lengths = {rod["name"]: rod["length_drawn"] for rod in data["rods"]}
    per_rod = {}
    for name, items in spread["by_rod"].items():
        area = sum(f["area_mm2"] for _, f in items)
        per_rod[name] = {
            "area_mm2": round(area, 3),
            "width_mm": round(area / lengths[name], 3),
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
               parallels: int = LOAD_PARALLELS) -> dict:
    """Net force and overturning moment on the whole dome, from the wind.

    Rigid-body statics over the cover: no structural model needed, and
    therefore the one part of this that a frame solver cannot improve on.

    **The overturning moment comes out at zero, and that is a result rather
    than a bug.** Pressure acts normal to the shell; every normal of a sphere
    is radial; so every facet force passes through the sphere's centre -- and
    for a bare dome that centre sits in the ground plane. The resultant is
    therefore a pure force through the base centre, with no couple: lift
    straight up and drag straight sideways.

    So **a bare Star Dome does not blow over, it takes off.** `interior.md`
    compares variants on a `tip_index` and says of it, correctly, that "it is
    a shape comparison and it proves nothing about safety". This is the answer
    it declined to give: the rigid-body failure mode is uplift on the ten
    anchors, and tipping is not in the running. A skirt puts the sphere's
    centre above the ground and a real couple appears, which is why D3 and D4
    report a moment and the bare sizes do not.
    """
    facets = facet_loads(data, speed_ms, loads, azimuth_deg, door,
                         meridians, parallels)
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
        "cp_internal": internal_coefficient(door, loads),
        "area_mm2": round(area, 3),
        "force_n": [round(v, 3) for v in total],
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


def self_weight(data: dict, material, loads: Loads,
                plastic_cm3: float = 0.0) -> dict:
    """What the dome weighs, in newtons. The first density in this project.

    `docs/bom.md` closes with "Money, and mass. Both want a supplier and a
    material, and this project has neither yet." It has a material now, so the
    mass half is answered here and the money half is still open.

    `plastic_cm3` comes from `bom.measured`, which reads it off the exported
    connector meshes -- so it is honestly zero until `make clamps` has run,
    the same way the BOM's own plastic column is.
    """
    meta = data["meta"]
    g = loads.gravity_m_s2
    rod_m = meta["total_rod_length"] / 1000.0
    rod_kg = rod_m * material.linear_mass(meta["rod_diameter"])

    fabric_m2 = cover.areas(data)["total_m2"]
    fabric_kg = fabric_m2 * loads.fabric_g_m2 / 1000.0

    plastic_kg = plastic_cm3 * loads.infill_fraction \
        * loads.plastic_density_kg_m3 / 1e6

    total_kg = rod_kg + fabric_kg + plastic_kg
    return {
        "rod_kg": round(rod_kg, 3),
        "fabric_kg": round(fabric_kg, 3),
        "plastic_kg": round(plastic_kg, 3),
        "total_kg": round(total_kg, 3),
        "total_n": round(total_kg * g, 3),
        # What a bow carries of itself, per unit length. The load case that
        # never comes off, and the one span.py scales as w ~ d^2.
        "rod_n_per_mm": round(
            material.linear_mass(meta["rod_diameter"]) * g / 1000.0, 9
        ),
        "plastic_measured": plastic_cm3 > 0.0,
    }


def analyse(data: dict, material, loads: Loads, speed_ms: float = 20.0,
            door: str = "shut") -> dict:
    """Wind and weight on one dome at one speed."""
    return {
        "variant": data["meta"]["variant"],
        "speed_ms": speed_ms,
        "door": door,
        "wind": resultants(data, speed_ms, loads, door=door),
        "tributary": tributary(data),
        "weight": self_weight(data, material, loads),
    }


def format_analysis(data: dict, material, loads: Loads,
                    speed_ms: float = 20.0, door: str = "shut") -> str:
    a = analyse(data, material, loads, speed_ms, door)
    w, t, m = a["wind"], a["tributary"], a["weight"]
    widths = sorted(t["per_rod"].items(), key=lambda kv: kv[1]["width_mm"])
    spread = widths[-1][1]["width_mm"] / widths[0][1]["width_mm"]
    # Against drag times the radius, which is the scale a real couple would be
    # on. A bare dome comes out four orders of magnitude below that -- the
    # residue of a faceted mesh, not a moment.
    scale = max(1.0, w["drag_n"] * data["meta"]["dome_radius"])
    flat = (
        "  -- zero, and that is a result: pressure normal to a sphere has no "
        "couple about its own centre, and a bare dome's centre sits on the "
        "ground. It lifts; it does not tip."
    ) if w["overturning_nmm"] / scale < 0.01 else (
        "  -- the skirt puts the sphere's centre above the ground, so here "
        "there is a real couple."
    )
    measured = "" if m["plastic_measured"] else "  (no meshes built yet)"
    out = [
        f"--- {a['variant']} wind at {speed_ms:.0f} m/s, door {door}",
        f"  velocity pressure  {w['velocity_pressure_pa']:.0f} Pa "
        f"(internal coefficient {w['cp_internal']:+.2f})",
        f"  lift               {w['lift_n']:.0f} N up",
        f"  drag               {w['drag_n']:.0f} N sideways",
        f"  overturning        {w['overturning_nmm'] / 1e6:.1f} N*m" + flat,
        "",
        f"  per anchor, if the {loads.anchor_count} share equally (they do not):",
        f"    uplift           {w['uplift_per_anchor_n']:.0f} N against "
        f"{loads.anchor_capacity_n:.0f} N  "
        f"({w['uplift_per_anchor_n'] / loads.anchor_capacity_n:.2f})",
        f"    shear            {w['shear_per_anchor_n']:.0f} N against "
        f"{loads.anchor_shear_capacity_n:.0f} N  "
        f"({w['shear_per_anchor_n'] / loads.anchor_shear_capacity_n:.2f})",
        "",
        "  what each bow carries of the cover:",
        f"    strips           {widths[0][1]['width_mm']:.0f} mm on "
        f"{widths[0][0]} to {widths[-1][1]['width_mm']:.0f} mm on "
        f"{widths[-1][0]}, a {spread:.2f}x spread -- an average width is "
        "wrong everywhere in particular",
        f"    partition        {t['dome_area_mm2'] / 1e6:.2f} m2 over 15 bows, "
        f"against {cover.areas(data)['dome_m2']:.2f} m2 of shell",
        "",
        "  and what it weighs:",
        f"    rod              {m['rod_kg']:.1f} kg",
        f"    cover            {m['fabric_kg']:.1f} kg",
        f"    printed          {m['plastic_kg']:.1f} kg" + measured,
        f"    total            {m['total_kg']:.1f} kg = {m['total_n']:.0f} N, "
        f"against {w['lift_n']:.0f} N of lift",
    ]
    return "\n".join(out)
