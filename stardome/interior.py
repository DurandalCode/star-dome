"""How much of the floor you can stand on, and what a tall skirt costs.

The project's goal is a room for a live-action event, so the number that
matters is not the diameter and not the peak height. It is **how many square
metres a person can stand up in**, and a dome is bad at that: the ceiling is
falling away from you everywhere except the middle.

A skirt fixes it, dramatically, and this is where its real value shows -- far
more than in the headline height. It also costs something, and this measures
that too.

The interior surface is taken as the sphere the bows lie on. The rods
themselves stop short of the zenith (the top of the structure is 0.982*R, the
apex of family U), and a fabric cover pulled over them will sit a little inside
the sphere, so these areas are the optimistic case by a few percent.
"""

from __future__ import annotations

import math

# Standing heights worth reporting, mm. 1800 is a person; 2000 is a person in
# costume with something on their head, which at an event is the common case.
STANDING_HEIGHTS_MM = (1500.0, 1800.0, 2000.0, 2200.0)

_STEPS = 2000


def headroom_radius(radius: float, skirt: float, height: float) -> float:
    """How far from the centre you can still stand up.

    Interior height at distance r is skirt + sqrt(R^2 - r^2), so the usable
    disc has radius sqrt(R^2 - (height - skirt)^2) -- and the whole floor is
    usable once the skirt alone clears the height.
    """
    remaining = height - skirt
    if remaining <= 0.0:
        return radius
    if remaining >= radius:
        return 0.0
    return math.sqrt(radius * radius - remaining * remaining)


def usable_area(data: dict, height: float) -> dict:
    """Floor area with at least ``height`` of headroom."""
    meta = data["meta"]
    radius = meta["dome_radius"]
    skirt = meta.get("skirt_height", 0.0)
    r_use = headroom_radius(radius, skirt, height)
    floor = math.pi * radius * radius
    usable = math.pi * r_use * r_use
    return {
        "height_mm": height,
        "usable_radius_mm": round(r_use, 1),
        "usable_m2": round(usable / 1e6, 2),
        "floor_m2": round(floor / 1e6, 2),
        "fraction": round(usable / floor, 4) if floor else 0.0,
    }


def volume(data: dict) -> dict:
    """Enclosed volume: the spherical cap plus the cylinder of skirt under it."""
    meta = data["meta"]
    radius = meta["dome_radius"]
    skirt = meta.get("skirt_height", 0.0)
    cap = (2.0 / 3.0) * math.pi * radius ** 3
    barrel = math.pi * radius * radius * skirt
    return {
        "dome_m3": round(cap / 1e9, 2),
        "skirt_m3": round(barrel / 1e9, 2),
        "total_m3": round((cap + barrel) / 1e9, 2),
    }


def exposure(data: dict) -> dict:
    """A comparative wind figure, not an engineering one.

    The overturning moment about the downwind base edge grows with the
    silhouette's area and the height of its centroid; the righting arm is the
    base radius. So ``centroid_height / radius`` is the ratio of overturning
    arm to righting arm per unit of sail area -- dimensionless, and directly
    comparable between variants. Higher is easier to tip over.

    This is a shape comparison. It is not a wind load calculation, it has no
    pressure coefficient in it, and it must not be used to decide that
    anything is safe.
    """
    meta = data["meta"]
    radius = meta["dome_radius"]
    skirt = meta.get("skirt_height", 0.0)
    top = skirt + radius

    area = 0.0
    moment = 0.0
    step = top / _STEPS
    for i in range(_STEPS):
        z = (i + 0.5) * step
        if z <= skirt:
            width = 2.0 * radius
        else:
            dz = z - skirt
            if dz >= radius:
                continue
            width = 2.0 * math.sqrt(radius * radius - dz * dz)
        area += width * step
        moment += width * step * z

    centroid = moment / area if area else 0.0
    return {
        "silhouette_m2": round(area / 1e6, 2),
        "centroid_height_mm": round(centroid, 1),
        "tip_index": round(centroid / radius, 3),
        # Overall height over diameter. Below about 0.8 it reads as a dome;
        # at 1.0 it is taller than it is wide, which is a silo. This is what
        # separates "small dome on a skirt" from "tower".
        "slenderness": round(top / (2.0 * radius), 3),
        "note": (
            "Comparative shape figure only: overturning arm over righting arm, "
            "per unit sail area. No pressure coefficient, no safety claim."
        ),
    }


def rod_efficiency(data: dict, height: float = 1800.0) -> dict:
    """Square metres you can stand in, per metre of rod.

    The blunt way to compare a big dome against a small one on a skirt: both
    cost rod, and only one of them gives you a room.
    """
    meta = data["meta"]
    rod = meta["total_rod_length"]
    skirt_rod = 0.0
    if data.get("skirt"):
        skirt_rod = data["skirt"]["post_total_length"] + data["skirt"][
            "ground_ring_length"
        ]
    total = rod + skirt_rod
    area = usable_area(data, height)["usable_m2"]
    return {
        "height_mm": height,
        "dome_rod_m": round(rod / 1000.0, 1),
        "skirt_rod_m": round(skirt_rod / 1000.0, 1),
        "total_rod_m": round(total / 1000.0, 1),
        "usable_m2": area,
        "m2_per_rod_m": round(area / (total / 1000.0), 4) if total else 0.0,
    }


def analyse(data: dict) -> dict:
    return {
        "variant": data["meta"]["variant"],
        "skirt_height_mm": data["meta"].get("skirt_height", 0.0),
        "by_height": [usable_area(data, h) for h in STANDING_HEIGHTS_MM],
        "volume": volume(data),
        "exposure": exposure(data),
        "efficiency": rod_efficiency(data),
    }


def format_analysis(data: dict) -> str:
    a = analyse(data)
    meta = data["meta"]
    lines = [
        f"--- {a['variant']} interior  "
        f"(floor {a['by_height'][0]['floor_m2']:.2f} m2, "
        f"skirt {a['skirt_height_mm']:.0f} mm)",
    ]
    for entry in a["by_height"]:
        lines.append(
            f"  stand up in {entry['height_mm']:>5.0f} mm:  "
            f"{entry['usable_m2']:>6.2f} m2  "
            f"({entry['fraction'] * 100:>5.1f}% of the floor, "
            f"out to r={entry['usable_radius_mm']:.0f} mm)"
        )
    v = a["volume"]
    lines.append(
        f"  volume {v['total_m3']:.1f} m3 "
        f"(dome {v['dome_m3']:.1f} + skirt {v['skirt_m3']:.1f})"
    )
    e = a["exposure"]
    lines.append(
        f"  silhouette {e['silhouette_m2']:.2f} m2, centroid at "
        f"{e['centroid_height_mm']:.0f} mm, tip index {e['tip_index']:.3f}, "
        f"slenderness {e['slenderness']:.2f}"
        + ("  <- taller than wide" if e["slenderness"] >= 1.0 else "")
    )
    f = a["efficiency"]
    lines.append(
        f"  rod {f['total_rod_m']:.0f} m "
        f"(dome {f['dome_rod_m']:.0f} + skirt {f['skirt_rod_m']:.0f}) "
        f"-> {f['m2_per_rod_m']:.4f} m2 of standing floor per metre of rod"
    )
    return "\n".join(lines)
