"""What to make the splice ferrule out of, and why the obvious answer is wrong.

A bow is nine metres long, travels in 2400 mm sections, and is **bent
everywhere**. So the sleeve that joins two sections is not a tension coupler:
it has to carry bending, continuously, along a member that has no straight
part anywhere.

That changes which material wins, and it inverts the intuition.

## Strength is the easy half

Bending a rod of diameter `d` to radius `R` puts a known moment in it:

    M = E_rod * I_rod / R          I_rod = pi * d^4 / 64
    sigma_rod = E_rod * d / (2R)

For M's 10 mm rod at R = 3000 that is 6.5 N*m and 67 MPa -- comfortable for
GFRP. Any sleeve of any of these materials survives it at a wall you could
actually make. Strength is not what decides this.

## Stiffness is the hard half

A sleeve much stiffer than the rod does not share the curve: the bow goes
straight through the joint and takes the extra bend just outside it, which is
a stress riser exactly where the section changes. Matching `E*I` is what keeps
the curvature continuous.

And that is where the metals lose. To match a GFRP rod's bending stiffness,
**steel would need a 0.2 mm wall.** The thinnest tube anyone will sell is four
times that, so any makeable steel sleeve is 4-5x too stiff. Cast metal, with a
3 mm minimum wall, is 10-15x too stiff.

Printed plastic matches naturally, because its modulus is *low*: PLA wants a
4.2 mm wall, which is an easy print, and it lands on the rod's stiffness by
construction.

## What this does NOT settle

- **Only the moment from being bent to shape.** Wind, snow and handling add
  to it and are not here. That is milestone 8.
- **Creep.** A PLA sleeve under a constant bending moment for a season is a
  different question from one under a test load for a minute, and this
  calculation cannot see the difference. It is the single strongest argument
  against the printed answer and it needs a test, not a formula.
- **Temperature and UV**, which a black plastic part in the sun cares about.
- **The transfer.** The bearing model here is a first approximation; how the
  sleeve actually grips -- bonded, pinned, swaged, taper -- is a design that
  does not exist yet.

Screening only. Nothing here says any of these is safe. See docs/splice.md.
"""

from __future__ import annotations

import math

# The rod, as an assumption. Pultruded GFRP varies by supplier and by fibre
# fraction; confirm against a data sheet.
ROD_MODULUS_MPA = 40000.0

# Bore clearance over the rod, so the section slides in.
DEFAULT_CLEARANCE_MM = 0.4

# Engagement each side of the joint, as a multiple of rod diameter. A sleeve
# joint wants several diameters of grip; six is a common rule of thumb and it
# is an input here rather than a result.
DEFAULT_ENGAGEMENT_D = 6.0

# name: (E MPa, allowable MPa, density kg/m3, minimum wall mm, how it is made)
MATERIALS = {
    "aluminium_6061": (69000.0, 150.0, 2700.0, 0.8, "drawn tube, cut to length"),
    "steel_mild": (200000.0, 140.0, 7850.0, 0.8, "drawn tube, cut to length"),
    "stainless_304": (193000.0, 120.0, 8000.0, 0.8, "drawn tube, cut to length"),
    "printed_pla": (3500.0, 20.0, 1240.0, 1.2, "printed"),
    "printed_petg": (2100.0, 18.0, 1270.0, 1.2, "printed"),
    "printed_nylon_cf": (6000.0, 40.0, 1200.0, 1.2, "printed"),
    "cast_aluminium": (70000.0, 60.0, 2680.0, 3.0, "cast from a printed pattern"),
    "cast_bronze": (100000.0, 90.0, 8800.0, 3.0, "cast from a printed pattern"),
}


def shape_moment(data: dict) -> dict:
    """The bending the bow carries just from being the shape it is.

    A lower bound on what the splice sees: wind, snow and handling add to it
    and are not in this number.
    """
    meta = data["meta"]
    d = meta["rod_diameter"]
    radius = meta["dome_radius"]
    inertia = math.pi * d ** 4 / 64.0
    return {
        "rod_diameter_mm": d,
        "bend_radius_mm": radius,
        "second_moment_mm4": round(inertia, 2),
        "moment_Nmm": round(ROD_MODULUS_MPA * inertia / radius, 1),
        "rod_stress_mpa": round(ROD_MODULUS_MPA * d / (2.0 * radius), 1),
        "stiffness_EI": round(ROD_MODULUS_MPA * inertia, 1),
        "note": (
            "From curvature alone. Live load is milestone 8 and is not in it."
        ),
    }


def _tube(bore: float, od: float) -> tuple:
    inertia = math.pi * (od ** 4 - bore ** 4) / 64.0
    modulus = inertia / (od / 2.0)
    return inertia, modulus


def _od_for_inertia(bore: float, target: float) -> float:
    return (bore ** 4 + 64.0 * target / math.pi) ** 0.25


def _od_for_modulus(bore: float, target: float) -> float:
    """Smallest outer diameter whose section modulus reaches the target."""
    lo, hi = bore + 1e-6, bore + 200.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if _tube(bore, mid)[1] < target:
            lo = mid
        else:
            hi = mid
    return hi


def sleeve(data: dict, material: str,
           clearance_mm: float = DEFAULT_CLEARANCE_MM,
           engagement_d: float = DEFAULT_ENGAGEMENT_D) -> dict:
    """One sleeve in one material: the wall each criterion asks for, and the
    wall you can actually make."""
    if material not in MATERIALS:
        raise ValueError(f"unknown material {material!r}; have {sorted(MATERIALS)}")
    modulus, allowable, density, min_wall, how = MATERIALS[material]

    shape = shape_moment(data)
    d = shape["rod_diameter_mm"]
    bore = d + clearance_mm
    moment = shape["moment_Nmm"]

    od_stiff = _od_for_inertia(bore, shape["stiffness_EI"] / modulus)
    od_strong = _od_for_modulus(bore, moment / allowable)
    od_makeable = bore + 2.0 * min_wall
    od = max(od_stiff, od_strong, od_makeable)

    inertia, section = _tube(bore, od)
    length = 2.0 * engagement_d * d
    volume = math.pi * (od ** 2 - bore ** 2) / 4.0 * length  # mm3

    # Bearing on the bore, from a triangular pressure block each side of the
    # joint reacting the moment. A first approximation, not a joint design.
    engagement = engagement_d * d
    bearing = 3.0 * moment / (d * engagement * engagement)

    return {
        "material": material,
        "made_by": how,
        "modulus_mpa": modulus,
        "bore_mm": round(bore, 2),
        "od_for_stiffness_mm": round(od_stiff, 2),
        "wall_for_stiffness_mm": round((od_stiff - bore) / 2.0, 2),
        "od_for_strength_mm": round(od_strong, 2),
        "wall_for_strength_mm": round((od_strong - bore) / 2.0, 2),
        "min_wall_mm": min_wall,
        "od_mm": round(od, 2),
        "wall_mm": round((od - bore) / 2.0, 2),
        "governed_by": (
            "stiffness" if od_stiff >= max(od_strong, od_makeable)
            else "strength" if od_strong >= od_makeable
            else "what can be made"
        ),
        "stiffness_ratio": round(modulus * inertia / shape["stiffness_EI"], 2),
        "stress_mpa": round(moment / section, 1),
        "allowable_mpa": allowable,
        "utilisation": round(moment / section / allowable, 2),
        "length_mm": round(length, 1),
        "mass_g": round(volume * density / 1e6, 1),
        "bearing_mpa": round(bearing, 3),
        "over_rod_mm": round(od - d, 2),
    }


def compare(data: dict, clearance_mm: float = DEFAULT_CLEARANCE_MM,
            engagement_d: float = DEFAULT_ENGAGEMENT_D,
            materials=None) -> list:
    """Every material, worst-of-the-criteria wall, sorted by stiffness match."""
    names = materials or list(MATERIALS)
    rows = [sleeve(data, name, clearance_mm, engagement_d) for name in names]
    return sorted(rows, key=lambda r: abs(math.log(r["stiffness_ratio"])))


def per_dome(data: dict, row: dict, splices: int | None = None) -> dict:
    """What a whole dome's worth of one sleeve comes to."""
    if splices is None:
        from . import rod as _rod

        splices = _rod.sections(data)["splices_total"]
    return {
        "splices": splices,
        "mass_kg": round(splices * row["mass_g"] / 1000.0, 2),
        "material": row["material"],
    }


def joint_clearance(data: dict, sleeve_length_mm: float | None = None,
                    limit_mm: float | None = None) -> dict:
    """How close a section joint comes to a crossing, and whether that is enough.

    The project has required from the start that a splice miss the crossings;
    this is what checks it. Sections divide the bow evenly, so the joints land
    at fixed fractions of its 180 degrees -- and whether those fractions
    collide with the crossing pattern is a fact about the topology, not a
    matter of care on site.
    """
    from . import rod as _rod

    meta = data["meta"]
    radius = meta["dome_radius"]
    sec = _rod.sections(data, limit_mm)
    per_bow = sec["per_bow"]
    if per_bow < 2:
        return {"joints_per_bow": 0, "clears": True,
                "note": "the bow travels whole, so there is no joint to clear"}

    joints = [180.0 * i / per_bow for i in range(1, per_bow)]

    by_rod: dict = {}
    for crossing in data["crossings"]:
        for rod_key, t_key in (("rod_a", "t_a_deg"), ("rod_b", "t_b_deg")):
            by_rod.setdefault(crossing[rod_key], set()).add(crossing[t_key])

    worst = None
    for name, angles in by_rod.items():
        for joint in joints:
            for angle in angles:
                gap = abs(angle - joint)
                if worst is None or gap < worst[0]:
                    worst = (gap, name, joint, angle)

    gap_deg = worst[0]
    gap_mm = math.radians(gap_deg) * radius
    need = (sleeve_length_mm if sleeve_length_mm is not None
            else 2.0 * DEFAULT_ENGAGEMENT_D * meta["rod_diameter"]) / 2.0

    return {
        "joints_per_bow": len(joints),
        "joints_deg": [round(j, 2) for j in joints],
        "closest_deg": round(gap_deg, 3),
        "closest_mm": round(gap_mm, 1),
        "on_bow": worst[1],
        "joint_deg": round(worst[2], 2),
        "crossing_deg": round(worst[3], 2),
        "half_sleeve_mm": round(need, 1),
        "clears": gap_mm >= need,
        "spare_mm": round(gap_mm - need, 1),
        "note": (
            "Even division puts the joints at fixed fractions of the bow, so "
            "whether they clear the crossings is a fact about the topology "
            "rather than something to be careful about on site."
        ),
    }


def choose_sections(data: dict, sleeve_length_mm: float | None = None,
                    limit_mm: float | None = None, most: int = 16) -> dict:
    """The fewest sections whose joints clear every crossing.

    The transport limit sets a MINIMUM count. It does not follow that the
    minimum is usable, and the reason is not bad luck.

    The U and L bows are **marked in thirds** -- that is the reference's own
    rod-marking scheme, ``geometry.MARKS_THIRDS``, and a third of 180 degrees
    is 60 and 120. The crossings sit on those marks, because sitting on the
    marks is what the marks are for. Dividing a bow into three puts a joint
    at the third points too. So the two constructions are the same
    construction, and they collide by definition rather than by accident.

    The same holds for G, which is marked in fifths. So the rule is exact:

        **a section count divisible by 3 or by 5 lands joints dead on
        crossings; any other count clears.**

    3, 6, 9, 12 hit the thirds; 5 and 10 hit the fifths; 2, 4, 7, 8, 11, 13
    are clean. The search below still runs, because clearing at all is not
    the same as clearing by more than half a sleeve -- D12 needs to get past
    8 and 11 on margin before 13 finally gives it room.

    So the count is searched upward from the transport minimum, and the first
    one that clears is the answer. It costs sections -- and a splice each --
    which is why it is worth reporting what it cost.
    """
    from . import rod as _rod

    meta = data["meta"]
    bow = _rod.bows(data)["length_mm"]
    limit = limit_mm if limit_mm is not None else meta.get("section_length") or 0.0
    need = (sleeve_length_mm if sleeve_length_mm is not None
            else 2.0 * DEFAULT_ENGAGEMENT_D * meta["rod_diameter"])

    floor = max(1, math.ceil(bow / limit)) if limit > 0 else 1
    for count in range(floor, most + 1):
        clear = joint_clearance(
            data, need, limit_mm=bow / count + 1e-9
        )
        if clear["clears"]:
            return {
                "sections": count,
                "transport_minimum": floor,
                "extra_sections": count - floor,
                "extra_splices_per_bow": count - floor,
                "extra_splices_total": (count - floor) * meta["rod_count"],
                "length_mm": round(bow / count, 1),
                "clearance_mm": clear["closest_mm"],
                "clearance_deg": clear["closest_deg"],
                "note": (
                    "The transport minimum lands a joint on a crossing"
                    if count > floor else
                    "The transport minimum already clears"
                ),
            }
    raise ValueError(
        f"no section count up to {most} keeps the joints off the crossings"
    )


def format_comparison(data: dict, clearance_mm: float = DEFAULT_CLEARANCE_MM,
                      engagement_d: float = DEFAULT_ENGAGEMENT_D) -> str:
    """The splice material question, as a page for a person."""
    meta = data["meta"]
    shape = shape_moment(data)
    rows = compare(data, clearance_mm, engagement_d)
    from . import rod as _rod

    splices = _rod.sections(data)["splices_total"]

    lines = [
        f"--- {meta.get('alias') or meta['variant']} splice ferrule, "
        f"{splices} of them",
        "",
        f"  the bow carries {shape['moment_Nmm'] / 1000.0:.2f} N*m and "
        f"{shape['rod_stress_mpa']:.0f} MPa just from being bent to "
        f"{shape['bend_radius_mm']:.0f} mm.",
        "  Live load is not in that. The sleeve has to match it in BENDING,",
        "  which is a stiffness problem before it is a strength one.",
        "",
        f"  {'material':<18}{'wall mm':>9}{'OD':>7}{'stiff x':>9}"
        f"{'stress':>8}{'use':>6}{'g each':>8}{'kg/dome':>9}  governed by",
    ]
    for r in rows:
        total = per_dome(data, r, splices)
        lines.append(
            f"  {r['material']:<18}{r['wall_mm']:>9.2f}{r['od_mm']:>7.1f}"
            f"{r['stiffness_ratio']:>9.1f}{r['stress_mpa']:>8.1f}"
            f"{r['utilisation']:>6.2f}{r['mass_g']:>8.1f}{total['mass_kg']:>9.2f}"
            f"  {r['governed_by']}"
        )

    best = rows[0]
    naive = joint_clearance(data, best["length_mm"])
    chosen = choose_sections(data, best["length_mm"])
    lines += ["", "  and it has to miss the crossings:"]
    if chosen["extra_sections"]:
        lines += [
            f"    {chosen['transport_minimum']} sections is what transport "
            f"allows, and it puts a joint {naive['closest_mm']:.0f} mm from a "
            "crossing --",
            f"    on top of one. {chosen['sections']} sections instead: "
            f"{chosen['length_mm']:.0f} mm each, nearest crossing "
            f"{chosen['clearance_mm']:.0f} mm away.",
            f"    Costs {chosen['extra_splices_total']} extra splices over "
            "the dome.",
        ]
    else:
        lines += [
            f"    {chosen['sections']} sections of "
            f"{chosen['length_mm']:.0f} mm, nearest crossing "
            f"{chosen['clearance_mm']:.0f} mm away. The transport minimum "
            "already clears.",
        ]
    lines += [
        "",
        f"  'stiff x' is the sleeve's EI over the rod's. 1.0 shares the curve;",
        "  much above it and the bow goes straight through the joint and takes",
        "  the extra bend just outside, where the section changes.",
        "",
        f"  Closest match: {best['material']} at {best['stiffness_ratio']:.1f}x,"
        f" {best['wall_mm']:.1f} mm wall, {best['od_mm']:.1f} mm over the "
        f"{shape['rod_diameter_mm']:.0f} mm rod.",
        "",
        "  SCREENING ONLY. Shape moment alone -- no wind, no snow, no",
        "  handling. No creep, which is the strongest argument against the",
        "  printed answer and needs a test rather than a formula. The grip",
        "  itself -- bonded, pinned, swaged -- is not designed.",
    ]
    return "\n".join(lines)
