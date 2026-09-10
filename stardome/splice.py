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

from . import materials

# The rod's bending modulus, from the catalogue rather than typed here.
ROD_MODULUS_MPA = materials.ROD[materials.DEFAULT_ROD]["modulus_mpa"]

# Bore clearance over the rod, so the section slides in.
DEFAULT_CLEARANCE_MM = 0.4

# Engagement each side of the joint, as a multiple of rod diameter. A sleeve
# joint wants several diameters of grip; six is a common rule of thumb and it
# is an input here rather than a result.
DEFAULT_ENGAGEMENT_D = 6.0

# How far a connector reaches along the rod from the crossing it sits on --
# half its channel length.
#
# A splice cannot be inside that AS THE PARTS STAND, because the sleeve is
# fatter than the rod and the channel is bored for the rod. That is a fact
# about the current connectors, not a law: a channel opened out to take a
# ferrule, or a connector and a splice made as one part, would change it.
# Nobody has designed either, so the reach is treated as occupied.
#
# From the parts as they stand: fan_node_v2's channel is 88.0 mm long, so it
# reaches 44 mm; crossing_clamp_v1's is 55 mm, so 27.5. The four-rod node is
# the governing one and is the default here. These are design outputs of
# connectors/, not constants of the dome -- change the part and change this.
CONNECTOR_REACH_MM = {
    "fan_node_v2": 44.0,
    "crossing_clamp_v1": 27.5,
}
DEFAULT_CONNECTOR_REACH_MM = 44.0

# The sleeve catalogue, flattened to the tuple this module works in. The
# values live in materials.py.
MATERIALS = {
    name: (e["modulus_mpa"], e["allowable_mpa"], e["density_kgm3"],
           e["min_wall_mm"], e["made_by"])
    for name, e in materials.SLEEVE.items()
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
                    limit_mm: float | None = None,
                    connector_reach_mm: float = DEFAULT_CONNECTOR_REACH_MM) -> dict:
    """How close a section joint comes to a crossing, and whether that is enough.

    The project has required from the start that a splice miss the crossings;
    this is what checks it. Sections divide the bow evenly, so the joints land
    at fixed fractions of its 180 degrees -- and whether those fractions
    collide with the crossing pattern is a fact about the topology, not a
    matter of care on site.

    **Missing the crossing POINT is not enough.** Two things have length. The
    connector reaches along the rod from the crossing it sits on -- 44 mm for
    the four-rod node -- and the sleeve reaches back from the joint. Neither
    can be inside the other, because the sleeve is fatter than the rod and the
    connector's channel is bored for the rod. So what has to fit between them
    is the sum.
    """
    from . import rod as _rod

    meta = data["meta"]
    radius = meta["dome_radius"]
    # The naive ceil, deliberately: this is a probe, and it has to be able to
    # answer for the divisions that DO land on a mark as well as the ones that
    # do not. rod.sections skips those, which is right for a cut list and
    # wrong for a check.
    bow = _rod.bows(data)["length_mm"]
    limit = (limit_mm if limit_mm is not None
             else meta.get("section_length") or 0.0)
    per_bow = max(1, math.ceil(bow / limit)) if limit > 0 else 1
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
    half_sleeve = (sleeve_length_mm if sleeve_length_mm is not None
                   else 2.0 * DEFAULT_ENGAGEMENT_D * meta["rod_diameter"]) / 2.0
    need = half_sleeve + connector_reach_mm

    return {
        "joints_per_bow": len(joints),
        "joints_deg": [round(j, 2) for j in joints],
        "closest_deg": round(gap_deg, 3),
        "closest_mm": round(gap_mm, 1),
        "on_bow": worst[1],
        "joint_deg": round(worst[2], 2),
        "crossing_deg": round(worst[3], 2),
        "half_sleeve_mm": round(half_sleeve, 1),
        "connector_reach_mm": round(connector_reach_mm, 1),
        "need_mm": round(need, 1),
        "clears": gap_mm >= need,
        "spare_mm": round(gap_mm - need, 1),
        "note": (
            "Even division puts the joints at fixed fractions of the bow, so "
            "whether they clear the crossings is a fact about the topology "
            "rather than something to be careful about on site."
        ),
    }


def choose_sections(data: dict, sleeve_length_mm: float | None = None,
                    limit_mm: float | None = None, most: int = 24,
                    connector_reach_mm: float = DEFAULT_CONNECTOR_REACH_MM) -> dict:
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
            data, need, limit_mm=bow / count + 1e-9,
            connector_reach_mm=connector_reach_mm,
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
                "need_mm": clear["need_mm"],
                "connector_reach_mm": clear["connector_reach_mm"],
                "note": (
                    "The transport minimum lands a joint on a crossing"
                    if count > floor else
                    "The transport minimum already clears"
                ),
            }
    raise ValueError(
        f"no section count up to {most} keeps the joints off the crossings"
    )


def clean_count(count: int) -> bool:
    """Does this many equal sections keep every joint off a crossing?

    Divisible by three and the joints land on the thirds, where U and L are
    marked; divisible by five and they land on the fifths, where G is. Any
    other count clears. See choose_sections for why.
    """
    return count % 3 != 0 and count % 5 != 0


def equal_sections(data: dict, limit_mm: float, most: int = 40,
                   sleeve_length_mm: float | None = None,
                   connector_reach_mm: float = DEFAULT_CONNECTOR_REACH_MM) -> dict:
    """The fewest EQUAL sections no longer than the limit that clear the marks.

    This is the recommended division and it is the simple one: take the
    smallest count that is divisible by neither three nor five, gives a
    section short enough to carry, AND leaves room beside each joint.

    Clean is not the same as clear. Eight sections on D12 miss the marks by
    0.26 degrees, which on a six metre radius is 27 mm -- no collision, and
    nowhere near enough for a ferrule and a connector. Both tests have to
    pass. Because the count is clean, the even
    division already lands every joint in a gap -- there is nothing to nudge,
    every section is the same piece, and one cut list serves all fifteen bows.

    Aiming instead at the middle of each gap gives slightly more clearance and
    costs unequal sections and a cut list per family; ``place_splices`` does
    that, and this does not.
    """
    from . import rod as _rod

    meta = data["meta"]
    bow = _rod.bows(data)["length_mm"]
    for count in range(2, most + 1):
        if not clean_count(count):
            continue
        length = bow / count
        if length > limit_mm:
            continue
        room = joint_clearance(data, sleeve_length_mm,
                               limit_mm=length + 1e-9,
                               connector_reach_mm=connector_reach_mm)
        if room["clears"]:
            return {
                "clearance_mm": room["closest_mm"],
                "need_mm": room["need_mm"],
                "sections": count,
                "length_mm": round(length, 1),
                "splices_per_bow": count - 1,
                "splices_total": (count - 1) * meta["rod_count"],
                "equal": True,
                "cut_lists": 1,
                "limit_mm": limit_mm,
                "note": (
                    f"{count} is divisible by neither 3 nor 5, so the even "
                    "division already misses every mark. One length, "
                    f"{count * meta['rod_count']} pieces per dome."
                ),
            }
    raise ValueError(
        f"no equal division up to {most} sections is both under "
        f"{limit_mm:.0f} mm and clear of the crossings -- use place_splices, "
        "which allows unequal sections, or carry a longer piece"
    )


def free_spans(data: dict, margin_mm: float,
               family: str | None = None) -> dict:
    """Where a bow has room, expressed as intervals of its own parameter.

    The crossings are not evenly spaced and the families do not agree. G is
    crossed at 36, 72, 108, 144 -- five equal spans. U and L are crossed at
    eight places in an alternating rhythm, 22.24 then 15.52 degrees, so their
    spans come in two sizes.

    ``margin_mm`` is what has to stay clear each side of a splice: half the
    ferrule plus however far the connector reaches along the rod. The second
    half of that is an assumption about the parts as they stand rather than a
    law -- see CONNECTOR_REACH_MM.
    """
    meta = data["meta"]
    radius = meta["dome_radius"]
    margin_deg = math.degrees(margin_mm / radius)

    positions: dict = {}
    for crossing in data["crossings"]:
        for fam_key, t_key in (("family_a", "t_a_deg"), ("family_b", "t_b_deg")):
            positions.setdefault(crossing[fam_key], set()).add(
                round(crossing[t_key], 6)
            )

    out = {}
    for fam, marks in positions.items():
        if family and fam != family:
            continue
        edges = [0.0] + sorted(marks) + [180.0]
        spans = []
        for lo, hi in zip(edges, edges[1:]):
            # The bow's own ends are held by a base hub, not crossed, so the
            # margin there is the hub's grip rather than a crossing's reach.
            start = lo + (margin_deg if lo > 0 else margin_deg)
            end = hi - (margin_deg if hi < 180.0 else margin_deg)
            if end > start:
                spans.append((round(start, 4), round(end, 4)))
        out[fam] = {
            "crossings_deg": sorted(marks),
            "usable_deg": spans,
            "widest_gap_deg": round(
                max(hi - lo for lo, hi in zip(edges, edges[1:])), 4
            ),
            "narrowest_gap_deg": round(
                min(hi - lo for lo, hi in zip(edges, edges[1:])), 4
            ),
            "narrowest_half_mm": round(
                math.radians(
                    min(hi - lo for lo, hi in zip(edges, edges[1:])) / 2.0
                ) * radius, 1
            ),
        }
    return out


def place_splices(data: dict, max_section_mm: float,
                  sleeve_length_mm: float | None = None,
                  connector_reach_mm: float = DEFAULT_CONNECTOR_REACH_MM) -> dict:
    """Splices in the gaps between crossings, as few as the length limit allows.

    The even division asks the wrong question. It divides the bow by a number
    and then checks whether the joints happen to miss the crossings; half the
    time they do not, and when they do it is luck. This asks the right one:
    the crossings leave gaps, a splice has to sit inside one with room each
    side, and no section may be longer than a vehicle.

    Greedy from the foot: each splice goes as far along as the length limit
    allows while still landing in a gap. That is the fewest splices.
    """
    meta = data["meta"]
    radius = meta["dome_radius"]
    margin = ((sleeve_length_mm if sleeve_length_mm is not None
               else 2.0 * DEFAULT_ENGAGEMENT_D * meta["rod_diameter"]) / 2.0
              + connector_reach_mm)
    max_deg = math.degrees(max_section_mm / radius)
    spans = free_spans(data, margin)

    result = {}
    for fam, info in spans.items():
        usable = info["usable_deg"]
        cuts = []
        at = 0.0
        while 180.0 - at > max_deg + 1e-9:
            reach = at + max_deg
            best = None
            for lo, hi in usable:
                if lo > reach + 1e-9 or hi <= at + 1e-9:
                    continue
                candidate = min(hi, reach)
                if candidate > at + 1e-9 and (best is None or candidate > best):
                    best = candidate
            if best is None:
                raise ValueError(
                    f"family {fam}: no gap within {max_section_mm:.0f} mm of "
                    f"{math.radians(at) * radius:.0f} mm along the bow"
                )
            cuts.append(round(best, 4))
            at = best
        lengths = [
            round(math.radians(b - a) * radius, 1)
            for a, b in zip([0.0] + cuts, cuts + [180.0])
        ]
        result[fam] = {
            "cuts_deg": cuts,
            "sections": len(cuts) + 1,
            "splices_per_bow": len(cuts),
            "section_lengths_mm": lengths,
            "longest_section_mm": max(lengths),
            "equal": len(set(lengths)) == 1,
        }

    bows_per_family = {}
    for r in data["rods"]:
        bows_per_family[r["family"]] = bows_per_family.get(r["family"], 0) + 1

    total = sum(
        result[f]["splices_per_bow"] * bows_per_family.get(f, 0) for f in result
    )
    return {
        "max_section_mm": max_section_mm,
        "margin_mm": round(margin, 1),
        "by_family": result,
        "splices_total": total,
        "cut_lists": len({tuple(v["section_lengths_mm"]) for v in result.values()}),
        "note": (
            "Sections are UNEQUAL, and the families do not share a cut list. "
            "That is the price of putting the joints where the room is."
        ),
    }


def transport_needed(data: dict, sleeve_length_mm: float | None = None,
                     connector_reach_mm: float = DEFAULT_CONNECTOR_REACH_MM,
                     most: int = 40) -> dict:
    """The shortest section -- and so the shortest vehicle -- that works.

    Two constraints pull against each other. Transport wants MANY sections,
    because each is shorter. Clearance wants FEW, because more joints means
    more chances to land on a crossing, and the counts that clear are sparse:
    nothing divisible by 3 or 5, and of what is left only some clear by more
    than a sleeve plus a connector.

    So the useful question is not "how many sections" but "how long a section
    may be", which is a decision about the van rather than the dome.
    """
    from . import rod as _rod

    meta = data["meta"]
    bow = _rod.bows(data)["length_mm"]
    need = (sleeve_length_mm if sleeve_length_mm is not None
            else 2.0 * DEFAULT_ENGAGEMENT_D * meta["rod_diameter"])

    workable = []
    for count in range(2, most + 1):
        clear = joint_clearance(data, need, limit_mm=bow / count + 1e-9,
                                connector_reach_mm=connector_reach_mm)
        if clear["clears"]:
            workable.append({
                "sections": count,
                "length_mm": round(bow / count, 1),
                "clearance_mm": clear["closest_mm"],
            })
    if not workable:
        raise ValueError("no section count clears at all")

    # The fewest sections is the longest section, so it needs the longest
    # vehicle; the shortest section is the most splices. Report both ends.
    fewest = min(workable, key=lambda w: w["sections"])
    return {
        "options": workable,
        "fewest_sections": fewest["sections"],
        "longest_section_mm": fewest["length_mm"],
        "splices_at_fewest": (fewest["sections"] - 1) * meta["rod_count"],
        "current_limit_mm": meta.get("section_length"),
        "fits_current": (
            fewest["length_mm"] <= (meta.get("section_length") or 0.0)
        ),
        "note": (
            "Fewest sections means the longest piece and the fewest splices. "
            "Whether it fits is a question about the vehicle."
        ),
    }


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
