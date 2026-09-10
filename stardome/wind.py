"""What the wind does to a covered dome, to the nearest order of magnitude.

**This is a screening calculation, not a structural check.** It exists to
answer one question early: how far off is this from standing up, and what has
to hold it down. It is not a design, it does not use a building code, it has
no partial factors, and nothing here may be used to decide that a dome is safe
to put people in. That is milestone 8, and it needs supplier data and testing.
See AGENTS.md, rule 8.

## What it does compute, honestly

The physics down to the force is not controversial:

    q = 0.5 * rho * v^2          dynamic pressure, Pa
    F = q * Cf * A               drag on the silhouette, N
    M_over = F * h_centroid      about the downwind base edge
    M_right = W * R              the structure's own weight resisting it

and the single number that matters most:

    v_tip = sqrt( 2 * W * R / (rho * Cf * A * h) )

the wind at which those two moments are equal. Below it the dome sits still
because it is heavy enough. Above it, **everything is the anchors.**

## Where the honesty runs out

Three inputs are assumptions, and they are the ones that move the answer:

- **Cf, the force coefficient.** A covered dome is a bluff body and the real
  figure depends on shape, ground effect, porosity and Reynolds number. The
  default here is a round number in the usual range for a hemisphere, and the
  report sweeps it rather than pretending to one value.
- **Material densities.** Pultruded GFRP and coated Oxford both vary by
  supplier, and the coating on a fabric can double its weight.
- **Uplift is not in this at all.** A dome in wind carries suction over its
  crown, and for something this light that is often the governing action --
  it lifts before it slides. Leaving it out makes these numbers
  **optimistic**, and that is the wrong direction to be wrong in.

So: use this to see that a bare frame does not hold itself down, and to size
the question. Do not use it to size an anchor.
"""

from __future__ import annotations

import math

from . import cover, interior, materials

AIR_DENSITY = materials.AIR_DENSITY
GRAVITY = materials.GRAVITY

# Force coefficient on the silhouette of a covered dome. A hemisphere sits
# somewhere around here, but the value depends on ground effect and on how
# taut the cover is, and this project has measured neither. Swept in the
# report rather than trusted.
DEFAULT_CF = 0.5
CF_RANGE = (0.35, 0.5, 0.65)

GFRP_DENSITY = materials.ROD[materials.DEFAULT_ROD]["density_kgm3"]

# Kept as a name; the weights live in materials.py.
FABRIC = {name: entry["gsm"] for name, entry in materials.FABRIC.items()}
DEFAULT_FABRIC = materials.DEFAULT_FABRIC

# Wind speeds worth a line, m/s. The names are the Beaufort description, which
# is a description of the sea and the trees, not a design load.
SPEEDS = (
    (10.0, "fresh breeze"),
    (15.0, "near gale"),
    (20.0, "gale"),
    (25.0, "strong gale"),
    (30.0, "storm"),
)

# How many of the ten base points are taken to share the hold-down. The
# upwind side does the work; a third of them is a screening guess and it is
# named here so it can be argued with.
ANCHORS_SHARING = 4


def pressure(speed_ms: float) -> float:
    """Dynamic pressure, Pa. The uncontroversial half of the calculation."""
    return 0.5 * AIR_DENSITY * speed_ms * speed_ms


def mass(data: dict, fabric: str = DEFAULT_FABRIC) -> dict:
    """What the thing weighs: rods, cover, and the total.

    Connectors, ties, pins and the stakes are not in it -- they are small
    against the rods and none of them is designed yet.
    """
    meta = data["meta"]
    if fabric not in FABRIC:
        raise ValueError(f"unknown fabric {fabric!r}; have {sorted(FABRIC)}")

    rod_area = math.pi * (meta["rod_diameter"] / 2000.0) ** 2  # m2
    rod_length = meta["total_rod_length"] / 1000.0  # m
    rods = rod_area * rod_length * GFRP_DENSITY

    fabric_m2 = cover.areas(data)["total_m2"]
    skin = fabric_m2 * FABRIC[fabric] / 1000.0

    total = rods + skin
    return {
        "fabric": fabric,
        "fabric_gsm": FABRIC[fabric],
        "rods_kg": round(rods, 1),
        "cover_kg": round(skin, 1),
        "total_kg": round(total, 1),
        "weight_N": round(total * GRAVITY, 1),
        "note": (
            "Rods and cover only. No connectors, ties, pins or stakes -- "
            "small against the rods, and none of them designed yet."
        ),
    }


def drag(data: dict, speed_ms: float, cf: float = DEFAULT_CF) -> dict:
    """Horizontal force on the covered silhouette."""
    exposure = interior.exposure(data)
    area = exposure["silhouette_m2"]
    q = pressure(speed_ms)
    force = q * cf * area
    return {
        "speed_ms": speed_ms,
        "pressure_pa": round(q, 1),
        "cf": cf,
        "silhouette_m2": area,
        "force_N": round(force, 1),
        "centroid_height_m": round(exposure["centroid_height_mm"] / 1000.0, 3),
    }


def tipping_speed(data: dict, cf: float = DEFAULT_CF,
                  fabric: str = DEFAULT_FABRIC) -> float:
    """The wind at which the dome's own weight stops holding it down, m/s.

    Equate the overturning moment about the downwind base edge with the
    righting moment from self weight and solve for v. Below this the dome
    stands on its own; above it every newton comes from the ground.
    """
    meta = data["meta"]
    m = mass(data, fabric)
    exposure = interior.exposure(data)
    radius = meta["dome_radius"] / 1000.0
    height = exposure["centroid_height_mm"] / 1000.0
    area = exposure["silhouette_m2"]
    if height <= 0 or area <= 0:
        return float("inf")
    return math.sqrt(
        2.0 * m["weight_N"] * radius / (AIR_DENSITY * cf * area * height)
    )


def anchors(data: dict, speed_ms: float, cf: float = DEFAULT_CF,
            fabric: str = DEFAULT_FABRIC,
            sharing: int = ANCHORS_SHARING) -> dict:
    """What the ground has to hold, once the dome's weight has run out.

    The deficit is the overturning moment less the righting moment, taken
    back to a force at the base radius. Spreading it over ``sharing`` upwind
    base points is a screening assumption, not a load path.
    """
    meta = data["meta"]
    m = mass(data, fabric)
    d = drag(data, speed_ms, cf)
    radius = meta["dome_radius"] / 1000.0

    over = d["force_N"] * d["centroid_height_m"]
    right = m["weight_N"] * radius
    deficit = over - right
    hold = max(0.0, deficit) / radius

    return {
        "speed_ms": speed_ms,
        "overturning_Nm": round(over, 1),
        "righting_Nm": round(right, 1),
        "stands_on_its_own": deficit <= 0,
        "hold_down_total_N": round(hold, 1),
        "hold_down_total_kgf": round(hold / GRAVITY, 1),
        "sharing": sharing,
        "per_anchor_N": round(hold / sharing, 1) if sharing else None,
        "per_anchor_kgf": round(hold / sharing / GRAVITY, 1) if sharing else None,
        "note": (
            "Screening only. Uplift over the crown is NOT included, so this "
            "is optimistic. Spreading over the upwind points is an assumption."
        ),
    }


def sweep(data: dict, cf: float = DEFAULT_CF, fabric: str = DEFAULT_FABRIC,
          speeds=SPEEDS) -> list:
    """One row per wind speed."""
    return [
        dict(anchors(data, speed, cf, fabric), label=label)
        for speed, label in speeds
    ]


def analyse(data: dict, cf: float = DEFAULT_CF,
            fabric: str = DEFAULT_FABRIC) -> dict:
    """Everything, with the assumptions carried alongside the answers."""
    return {
        "mass": mass(data, fabric),
        "exposure": interior.exposure(data),
        "cf": cf,
        "tipping_speed_ms": round(tipping_speed(data, cf, fabric), 2),
        "tipping_speed_by_cf": {
            str(c): round(tipping_speed(data, c, fabric), 2) for c in CF_RANGE
        },
        "rows": sweep(data, cf, fabric),
        "assumptions": {
            "air_density_kgm3": AIR_DENSITY,
            "gfrp_density_kgm3": GFRP_DENSITY,
            "fabric_gsm": FABRIC[fabric],
            "cf": cf,
            "uplift_included": False,
            "code": None,
            "safety_factors": None,
        },
        "note": (
            "SCREENING ONLY. No building code, no partial factors, no uplift, "
            "no gust factor, no terrain category. Not a basis for deciding "
            "anything is safe. See docs/wind.md and roadmap milestone 8."
        ),
    }


def corridor_sail(spec: dict, length_mm: float) -> dict:
    """A corridor's own silhouette, broadside and end-on.

    Broadside is the one that matters -- a tunnel is mostly side -- and it
    grows with length, which is the argument against long corridors that
    nobody makes when drawing them.
    """
    from . import corridor as _corridor

    outline = _corridor.section_for(
        spec.get("kind", "hoop"), spec["width"], spec["height"],
        spec.get("samples", _corridor.ARC_SAMPLES),
        spec.get("brace_leg", _corridor.DEFAULT_BRACE_LEG_MM),
    )
    height = outline[-1][0]
    # End-on: the clear section, both halves, by trapezoids.
    end_on = 0.0
    for i in range(len(outline) - 1):
        h0, w0 = outline[i]
        h1, w1 = outline[i + 1]
        end_on += (w0 + w1) * (h1 - h0)

    return {
        "broadside_m2": round(height * length_mm / 1e6, 2),
        "end_on_m2": round(end_on / 1e6, 2),
        "height_mm": round(height, 1),
    }


def camp_totals(plan: dict, domes: dict, cf: float = DEFAULT_CF,
                fabric: str = DEFAULT_FABRIC) -> dict:
    """The whole camp: mass, sail area and hold-down, summed.

    **Summed, not solved.** Domes standing near each other shelter one
    another, and this models none of that -- so the total is an upper bound
    on the drag and, because uplift is still missing, not an upper bound on
    what the anchors see. Two errors in opposite directions is not a safe
    number; it is a rough one.
    """
    spec = plan["corridor_spec"]
    mass_total = 0.0
    sail_total = 0.0
    per_dome = []

    for entry in plan["domes"]:
        data = domes[entry["label"]]
        m = mass(data, fabric)
        e = interior.exposure(data)
        mass_total += m["total_kg"]
        sail_total += e["silhouette_m2"]
        per_dome.append({
            "label": entry["label"],
            "mass_kg": m["total_kg"],
            "silhouette_m2": e["silhouette_m2"],
            "tipping_speed_ms": round(tipping_speed(data, cf, fabric), 2),
        })

    corridor_sail_m2 = 0.0
    corridor_skin_m2 = 0.0
    for link in plan["corridors"]:
        sail = corridor_sail(spec, spec["length"])
        corridor_sail_m2 += sail["broadside_m2"]
        # Skin area for the fabric mass: perimeter x length, both sides.
        corridor_skin_m2 += sail["broadside_m2"] * 2.2  # rough wrap factor

    corridor_mass = corridor_skin_m2 * FABRIC[fabric] / 1000.0

    return {
        "domes": len(plan["domes"]),
        "corridors": len(plan["corridors"]),
        "dome_mass_kg": round(mass_total, 1),
        "corridor_cover_kg": round(corridor_mass, 1),
        "total_mass_kg": round(mass_total + corridor_mass, 1),
        "dome_sail_m2": round(sail_total, 2),
        "corridor_sail_broadside_m2": round(corridor_sail_m2, 2),
        "total_sail_m2": round(sail_total + corridor_sail_m2, 2),
        "weakest": min(per_dome, key=lambda d: d["tipping_speed_ms"]),
        "per_dome": per_dome,
        "note": (
            "Summed, not solved: no shelter between neighbours, no uplift, "
            "no gusts. An upper bound on drag and NOT an upper bound on what "
            "the anchors see. Corridor fabric uses a rough 2.2x wrap factor."
        ),
    }


def format_analysis(data: dict, cf: float = DEFAULT_CF,
                    fabric: str = DEFAULT_FABRIC) -> str:
    """The wind screening, as a page for a person."""
    meta = data["meta"]
    a = analyse(data, cf, fabric)
    m = a["mass"]
    e = a["exposure"]

    lines = [
        f"--- {meta['variant']} in wind, covered in {fabric.replace('_', ' ')}"
        f" ({m['fabric_gsm']:.0f} g/m2)",
        "",
        f"  mass            {m['rods_kg']:.1f} kg of rod + {m['cover_kg']:.1f} kg "
        f"of cover = {m['total_kg']:.1f} kg ({m['weight_N']:.0f} N)",
        f"  silhouette      {e['silhouette_m2']:.2f} m2, centroid at "
        f"{e['centroid_height_mm'] / 1000.0:.2f} m",
        f"  force coeff     {cf} (assumed)",
        "",
        f"  IT HOLDS ITSELF DOWN TO {a['tipping_speed_ms']:.1f} m/s"
        f"  ({a['tipping_speed_ms'] * 3.6:.0f} km/h)",
        "    and above that every newton comes from the ground:",
        "",
        f"    {'wind':<22}{'pressure':>10}{'force':>10}{'hold down':>12}"
        f"{'per anchor':>13}",
    ]
    for row in a["rows"]:
        d = drag(data, row["speed_ms"], cf)
        speed = f"{row['speed_ms']:.0f} m/s  {row['label']}"
        if row["stands_on_its_own"]:
            hold = "stands"
            each = "--"
        else:
            hold = f"{row['hold_down_total_kgf']:.0f} kgf"
            each = f"{row['per_anchor_kgf']:.0f} kgf"
        lines.append(
            f"    {speed:<22}{d['pressure_pa']:>9.0f}P{d['force_N']:>9.0f}N"
            f"{hold:>12}{each:>13}"
        )

    spread = a["tipping_speed_by_cf"]
    lines += [
        "",
        f"    tipping speed across Cf {', '.join(f'{k}: {v:.1f}' for k, v in spread.items())} m/s",
        "",
        f"  Sharing assumed over {ANCHORS_SHARING} of the 10 base points.",
        "",
        "  SCREENING ONLY. No code, no factors, no gusts, and NO UPLIFT --",
        "  which for something this light is often what actually lifts it.",
        "  These numbers are optimistic. Nothing here says anything is safe.",
    ]
    return "\n".join(lines)
