"""Whether it stands, and up to what wind.

`material.py` says what the rod can take; `loads.py` says what is asked of it.
This is where the two meet and a number becomes a verdict -- the thing
`configs/variants.toml` has been asking for in its own header since the file
was written, and the thing `docs/span.md` stops one step short of.

## What this reports, and what it refuses to report

It reports a **band**, not a number, and the band is the finding.

A bow in this dome is a curved member restrained at intervals by ninety
rod-on-rod contacts. How much of the wind it carries by bending and how much
it carries by arch action is not knowable in closed form -- `span.py` says
exactly this about the constant in front of `w a^4/EI` -- so two bounding
readings are computed and reported side by side:

**`beam`** -- the bow spans between its supports and carries the load in pure
bending. `M = w a^2 / 8`, `N = 0`. An upper bound on bending and a lower bound
on strength.

**`membrane`** -- the lattice is a discretised shell. A spherical shell under
normal pressure `p` carries `n = pR/2` per unit width, so a bow carries
`N = pRb/2` over its tributary strip and bends not at all. An upper bound on
axial force and a lower bound on bending.

**`envelope`** -- both at once, which is conservative and deliberately so.

On D6's worst span at 20 m/s those two differ by a factor of **670** in stress
-- 1122 MPa of bending against 1.7 MPa of axial -- and that gap is the honest
state of knowledge. Closing it is what a frame solve is for; quoting a single
limiting speed before it is closed would be inventing confidence. See
docs/strength.md.

## The rod is already loaded before the wind blows

Every bow is bent to the dome radius and stays bent, so it carries
`E d / 2R` permanently -- 83 MPa on D6, 133 on D3 -- against a creep-rupture
allowance of 112 MPa. **That check does not involve the wind at all**, and it
is the first one this module runs, because a variant that fails it fails
standing still in a calm.

## Which check binds is the answer, not the speed

The wind on a hemisphere is mostly suction, so the load arrives at ten driven
angles as uplift rather than at the rods as bending. The useful output is
therefore *which* check runs out first and at what speed, per variant -- and
what shutting the door is worth in m/s.

```bash
python3 -m stardome strength M
python3 -m stardome strength --all --material pultruded_rod
python3 -m stardome strength M --door open --holds contact
```
"""

from __future__ import annotations

import math

from . import loads as loads_mod
from . import material as material_mod
from . import span

# Every check this module runs, in the order a reader should meet them: the
# ones that do not involve the wind first.
CHECKS = (
    "bend_creep",
    "combined_tension",
    "combined_compression",
    "buckling",
    "anchor_uplift",
    "anchor_shear",
)

# Checks that set a limiting speed. `bend_creep` is not among them because it
# has no wind in it: a bow either survives being bent or it does not, and the
# wind cannot make that better.
MEMBER_CHECKS = ("combined_tension", "combined_compression", "buckling")

# How the bow is assumed to carry the load. See the module docstring.
LOAD_PATHS = ("beam", "membrane", "envelope")

# Deflection between supports, as a fraction of the span, at which
# small-deflection theory has stopped describing this structure. Past it the
# answer is VOID rather than merely large: the geometry has moved far enough
# that the stiffness used to compute it is the wrong stiffness.
#
# Deflection is deliberately NOT a strength check here, and finding out why
# was the first useful thing this module did. Under the `beam` reading a D6
# bow sags 80 mm between supports **under its own weight, in a dead calm** --
# 2.5% of the span. Scored as a serviceability failure that makes the beam
# reading fail at zero wind, which tells a reader nothing. Read instead as
# what it is, it says something much more useful: a Star Dome plainly does not
# sag 80 mm when you stand it up, so the beam reading is not conservative, it
# is **wrong**, and the truth lies towards the membrane end of the band.
#
# So the number below is a validity gate, and the sag itself is reported as a
# figure for a person to look at.
DEFLECTION_VOID = 0.10

# Wind directions tried, in degrees. The dome has five-fold symmetry, so
# sweeping 0 to 72 covers every distinct direction, and the doorway is the
# only thing that breaks it.
DIRECTION_SAMPLES = (0.0, 18.0, 36.0, 54.0, 72.0)

# Speed the unit load field is built at. Pressure goes as the square of the
# speed, so the whole field scales from one evaluation -- which is what makes
# solving for a limiting speed closed-form instead of forty re-integrations.
REFERENCE_SPEED_MS = 1.0


# --- what one bow is asked to carry -----------------------------------------


# The scatter is pure geometry -- which bow is nearest which patch of cover --
# so it does not move with the wind, the material, the holds reading or the
# door. It is also the expensive part: a nearest-neighbour pass over some
# fourteen thousand facets against eight hundred centreline samples. Computing
# it once per dome turns a bisection over wind speeds from minutes into
# milliseconds, so it is memoised on the only things it actually depends on.
_STRIP_CACHE: dict = {}


def _strips(data: dict) -> dict:
    """Per bow: its share of the cover, as radial directions and areas.

    The direction is what a pressure coefficient is a function of, so keeping
    directions rather than points is enough to re-evaluate any wind from any
    azimuth without touching the geometry again.
    """
    from . import vec

    meta = data["meta"]
    key = (meta["variant"], meta["weave_mode"], meta.get("door_cut", ""),
           loads_mod.LOAD_MERIDIANS, loads_mod.LOAD_PARALLELS)
    if key in _STRIP_CACHE:
        return _STRIP_CACHE[key]

    facets = [
        {"centroid": c, "area_mm2": a, "normal": n, "force_n": [0.0, 0.0, 0.0],
         "skirt": sk}
        for c, a, n, sk in loads_mod._facets(
            data, loads_mod.LOAD_MERIDIANS, loads_mod.LOAD_PARALLELS
        )
    ]
    spread = loads_mod.scatter(data, facets)
    ground = meta.get("ground_z", 0.0)
    skirt = meta.get("skirt_height", 0.0) or 0.0
    centre = [0.0, 0.0, ground + skirt]

    out = {}
    for name, items in spread["by_rod"].items():
        out[name] = {
            "area_mm2": sum(f["area_mm2"] for _, f in items),
            "radials": [
                vec.unit(vec.sub(f["centroid"], centre)) for _, f in items
            ],
        }
    _STRIP_CACHE[key] = out
    return out


def _peak_coefficients(data, loads, azimuths, door) -> dict:
    """Worst net pressure coefficient over each bow's tributary strip.

    The worst over the whole strip is then applied over the whole span, which
    is conservative: no bow sees its peak suction everywhere at once.
    """
    strips = _strips(data)
    cpi = loads_mod.internal_coefficient(door, loads)
    directions = [
        (math.cos(math.radians(a)), math.sin(math.radians(a)))
        for a in azimuths
    ]

    out = {}
    for name, strip in strips.items():
        worst = 0.0
        for dx, dy in directions:
            for rx, ry, rz in strip["radials"]:
                cos_t = max(-1.0, min(1.0, -(rx * dx + ry * dy)))
                polar = math.degrees(math.acos(cos_t))
                net = loads_mod.shape_coefficient(polar, loads) - cpi
                if abs(net) > worst:
                    worst = abs(net)
        out[name] = {"cp_net": worst, "area_mm2": strip["area_mm2"]}
    return out


def unit_demands(data: dict, material, loads, holds: str = "lashed",
                 door: str = "shut") -> dict:
    """Per bow: its span, its strip, its permanent load and its wind per pascal.

    Everything that does not depend on the wind speed, computed once. A speed
    then enters only through the velocity pressure, and every check below is
    a quadratic in it.
    """
    meta = data["meta"]
    radius = meta["dome_radius"]
    diameter = meta["rod_diameter"]
    spans = span.spans(data, holds)
    peaks = _peak_coefficients(data, loads, DIRECTION_SAMPLES, door)

    area = material.area(diameter)
    second = material.second_moment(diameter)
    modulus = material.section_modulus(diameter)
    ei = material.modulus_mpa * second
    self_n_per_mm = material.linear_mass(diameter) * loads.gravity_m_s2 / 1000.0

    out = {}
    for rod in data["rods"]:
        name = rod["name"]
        items = spans["per_rod"][name]
        if not items:
            continue
        worst = max(items, key=lambda s: s["arc_deg"])
        length = worst["length_mm"]
        strip = peaks[name]["area_mm2"] / rod["length_drawn"]
        out[name] = {
            "family": rod["family"],
            "span_mm": length,
            "strip_mm": strip,
            "cp_net": peaks[name]["cp_net"],
            # Line load per pascal of velocity pressure, N/mm.
            # p [Pa] = q * cp_net; p [N/mm^2] = p [Pa] * 1e-6; times strip [mm].
            "wind_n_per_mm_per_pa": peaks[name]["cp_net"] * strip * 1e-6,
            "self_n_per_mm": self_n_per_mm,
            # Euler on the unsupported span, pinned-pinned. `holds` moves the
            # span, and that is the whole price of the thirty clamps.
            "euler_n": math.pi ** 2 * ei / (length * length),
            "area_mm2": area,
            "second_moment_mm4": second,
            "section_modulus_mm3": modulus,
        }
    return {
        "holds": holds,
        "door": door,
        "radius_mm": radius,
        "rod_diameter_mm": diameter,
        "residual_stress_mpa": material.bend_stress(diameter, radius),
        "per_rod": out,
    }


# --- what that does to it, at a speed ---------------------------------------


def member_state(demand: dict, unit: dict, material, loads,
                 speed_ms: float, path: str = "envelope") -> dict:
    """Stress, force and deflection in one bow at one wind speed."""
    if path not in LOAD_PATHS:
        raise ValueError(f"unknown load path {path!r} -- use one of {LOAD_PATHS}")
    q = loads_mod.velocity_pressure(speed_ms, loads)
    a = demand["span_mm"]
    w = demand["wind_n_per_mm_per_pa"] * q + demand["self_n_per_mm"]

    bends = path in ("beam", "envelope")
    thrusts = path in ("membrane", "envelope")

    moment = w * a * a / 8.0 if bends else 0.0
    # Membrane force in a spherical shell under normal pressure: n = pR/2 per
    # unit width, carried over the bow's own strip.
    pressure = q * demand["cp_net"] * 1e-6            # N/mm^2
    axial = (pressure * unit["radius_mm"] * demand["strip_mm"] / 2.0
             if thrusts else 0.0)

    sigma_m = moment / demand["section_modulus_mm3"]
    sigma_n = axial / demand["area_mm2"]
    residual = unit["residual_stress_mpa"]

    deflection = (5.0 * w * a ** 4
                  / (384.0 * material.modulus_mpa * demand["second_moment_mm4"])
                  if bends else 0.0)

    return {
        "line_load_n_per_mm": w,
        "moment_nmm": moment,
        "axial_n": axial,
        "residual_mpa": residual,
        # The axial force is compression, so it relieves the tension fibre.
        # That relief is deliberately NOT taken: it reverses if the wind lifts
        # rather than presses, and a bound that depends on the sign of the
        # load is not a bound.
        "tension_mpa": residual + sigma_m,
        "compression_mpa": residual + sigma_m + sigma_n,
        "deflection_mm": deflection,
    }


def utilisations(demand: dict, unit: dict, material, loads,
                 speed_ms: float, path: str = "envelope") -> dict:
    """Every member check on one bow, as a fraction of what is allowed."""
    state = member_state(demand, unit, material, loads, speed_ms, path)
    return {
        # No wind in this one at all. A bow fails it standing in a calm.
        "bend_creep": state["residual_mpa"]
        / material.allowable("sustained", "tension"),
        "combined_tension": state["tension_mpa"]
        / material.allowable("short_term", "tension"),
        "combined_compression": state["compression_mpa"]
        / material.allowable("short_term", "compression"),
        "buckling": state["axial_n"] / demand["euler_n"],
    }


def anchor_demand(data: dict, loads, door: str = "shut") -> dict:
    """Uplift and shear on one anchor, per unit of velocity pressure.

    Computed once at a reference speed and scaled, for the same reason the
    member side is: pressure goes as the square of the speed, so the shape of
    the field never changes and re-integrating the cover at every step of a
    bisection would be forty identical integrals.
    """
    reference = loads_mod.resultants(data, REFERENCE_SPEED_MS, loads, door=door)
    q = loads_mod.velocity_pressure(REFERENCE_SPEED_MS, loads)
    return {
        "uplift_n_per_pa": reference["uplift_per_anchor_n"] / q,
        "shear_n_per_pa": reference["shear_per_anchor_n"] / q,
    }


def anchor_utilisations(data: dict, loads, speed_ms: float,
                        door: str = "shut", demand: dict | None = None) -> dict:
    """What the ten driven angles are asked to hold, over what they hold.

    Uplift shared equally between the ten, which they are not -- see
    `loads.resultants`. The number is an average and the worst foot is worse.
    """
    demand = demand or anchor_demand(data, loads, door)
    q = loads_mod.velocity_pressure(speed_ms, loads)
    return {
        "anchor_uplift": max(0.0, demand["uplift_n_per_pa"] * q)
        / loads.anchor_capacity_n,
        "anchor_shear": demand["shear_n_per_pa"] * q
        / loads.anchor_shear_capacity_n,
    }


# --- solving for the speed that uses it all up ------------------------------


def limiting_speed(evaluate, lo: float = 0.0, hi: float = 120.0,
                   tol: float = 1e-6) -> float:
    """Speed at which ``evaluate(v)`` first reaches 1.0.

    Bisection rather than the closed form, even though every check here
    happens to be a quadratic in the speed. Two reasons: it does not care
    which check is governing, and it will still be right when a check stops
    being quadratic -- a moment magnifier, or a compression-only contact.
    A test pins it against the closed form on a linear check.

    Returns 0.0 when the structure is already over at zero wind, which is a
    real answer and not a failure to converge.
    """
    if evaluate(lo) >= 1.0:
        return 0.0
    if evaluate(hi) < 1.0:
        return math.inf
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if evaluate(mid) < 1.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def analyse(data: dict, material, loads, holds: str = "lashed",
            door: str = "shut") -> dict:
    """The whole verdict for one dome: both bounds, every check, the speed."""
    unit = unit_demands(data, material, loads, holds, door)
    per_rod = unit["per_rod"]

    def worst_member(path, speed):
        best_name, best_check, best_value = None, None, -1.0
        for name, demand in per_rod.items():
            for check, value in utilisations(
                demand, unit, material, loads, speed, path
            ).items():
                if value > best_value:
                    best_name, best_check, best_value = name, check, value
        return best_name, best_check, best_value

    def worst_sag(path, speed):
        """Deepest sag between supports, as a fraction of its own span."""
        worst = 0.0
        where = None
        for name, demand in per_rod.items():
            state = member_state(demand, unit, material, loads, speed, path)
            ratio = state["deflection_mm"] / demand["span_mm"]
            if ratio > worst:
                worst, where = ratio, (name, state["deflection_mm"])
        return worst, where

    anchor = anchor_demand(data, loads, door)

    def anchors(speed):
        checks = anchor_utilisations(data, loads, speed, door, anchor)
        name = max(("anchor_uplift", "anchor_shear"), key=lambda k: checks[k])
        return name, checks[name]

    paths = {}
    for path in LOAD_PATHS:
        def evaluate(v, _p=path):
            member = worst_member(_p, v)[2]
            return max(member, anchors(v)[1])

        limit = limiting_speed(evaluate)
        at = limit if math.isfinite(limit) and limit > 0 else 0.0
        rod, check, value = worst_member(path, at)
        anchor_name, anchor_value = anchors(at)
        binding = check if value >= anchor_value else anchor_name
        sag_ratio, sag_where = worst_sag(path, at)
        paths[path] = {
            "limit_ms": None if math.isinf(limit) else round(limit, 2),
            "binding_check": binding,
            # `bend_creep` is true of every bow at once -- it is a property
            # of the diameter and the radius, not of one member -- so naming
            # a rod for it would invite somebody to go and look at that rod.
            "binding_rod": rod if binding in MEMBER_CHECKS else (
                "every bow" if binding == "bend_creep" else None
            ),
            "member_utilisation": round(value, 4),
            "anchor_utilisation": round(anchor_value, 4),
            "sag_ratio": round(sag_ratio, 5),
            "sag_mm": round(sag_where[1], 1) if sag_where else 0.0,
            "sag_rod": sag_where[0] if sag_where else None,
            # Past this the stiffness used to compute the answer is not the
            # stiffness the deformed structure has, and the answer is void.
            "linear_theory_holds": sag_ratio <= DEFLECTION_VOID,
        }

    # The check with no wind in it, reported on its own because a failure here
    # is not a wind limit at all.
    creep = unit["residual_stress_mpa"] / material.allowable("sustained", "tension")
    return {
        "variant": data["meta"]["variant"],
        "material": material.name,
        "holds": holds,
        "door": door,
        "rod_diameter_mm": unit["rod_diameter_mm"],
        "radius_mm": unit["radius_mm"],
        "residual": {
            "stress_mpa": round(unit["residual_stress_mpa"], 2),
            "strain": round(span.bend_strain(unit["rod_diameter_mm"],
                                             unit["radius_mm"]), 9),
            "allowable_mpa": round(material.allowable("sustained", "tension"), 2),
            "utilisation": round(creep, 4),
            "passes": creep <= 1.0,
        },
        "bendable_rod_mm": round(material.bendable_diameter(unit["radius_mm"]), 2),
        "paths": paths,
        "band_ms": [
            paths["envelope"]["limit_ms"],
            paths["membrane"]["limit_ms"],
        ],
        "note": (
            "A band, not a number. The beam and membrane readings bound how "
            "the bow carries the wind and nothing here decides between them; "
            "a frame solve does. No connector is checked, the anchors are "
            "shared equally when they are not, and the pressure coefficients "
            "are a smooth hemisphere's."
        ),
    }


def _speed(value) -> str:
    if value is None:
        return "  none"
    if value <= 0.0:
        return "  0.0 "
    return f"{value:6.1f}"


def format_analysis(data: dict, material, loads, holds: str = "lashed",
                    door: str = "shut") -> str:
    a = analyse(data, material, loads, holds, door)
    r = a["residual"]
    verdict = "passes" if r["passes"] else "FAILS"
    out = [
        f"--- {a['variant']} strength on {a['material']}  "
        f"(held at: {'feet and tie marks' if holds == 'lashed' else 'every crossing'}, "
        f"door {door})",
        "",
        "  before any wind at all -- the bow is bent and stays bent:",
        f"    residual      {r['stress_mpa']:.1f} MPa at {r['strain'] * 100:.3f}% strain, "
        f"against {r['allowable_mpa']:.1f} MPa allowed as a permanent stress",
        f"    creep check   {r['utilisation']:.2f} of allowable -- {verdict}",
        f"    this stock bends to {a['radius_mm']:.0f} mm at up to "
        f"{a['bendable_rod_mm']:.1f} mm diameter; this dome carries "
        f"{a['rod_diameter_mm']:.1f}",
    ]
    if not r["passes"]:
        # There is no wind limit to report. The bow is over its permanent
        # allowance standing in a calm, so every reading returns zero and a
        # band of zeros would read like a band rather than like a refusal.
        out += [
            "",
            "  there is no limiting wind speed to report: the rod is already "
            "over its permanent",
            "  allowance standing in a dead calm, and no wind makes that "
            "better.",
            f"    the fix is arithmetic -- {a['bendable_rod_mm']:.1f} mm rod at "
            f"this radius, or a larger dome at this rod.",
            "",
            "  Judged against a standard's minimum, not a measured bar. A real "
            "coil is usually",
            "  better, and measuring one is milestone 3.",
        ]
        return "\n".join(out)

    out += [
        "",
        "  limiting wind speed, by how the bow is assumed to carry the load:",
        "    path        limit    binding check          on",
    ]
    for path in LOAD_PATHS:
        p = a["paths"][path]
        out.append(
            f"    {path:11} {_speed(p['limit_ms'])} m/s  "
            f"{p['binding_check']:20}  {p['binding_rod'] or '10 anchors'}"
        )
    out += [
        "",
        f"  the band is {_speed(a['paths']['envelope']['limit_ms']).strip()} to "
        f"{_speed(a['paths']['membrane']['limit_ms']).strip()} m/s, and the "
        "width of it is the finding.",
        "",
        "  " + a["note"],
    ]
    return "\n".join(out)


def compare(data: dict, material, loads, holds: str = "lashed") -> dict:
    """What each open choice is worth, in metres per second.

    Three decisions nobody has made are priced here, on the membrane reading
    because that is the one that is not refuted by the dome standing up:

    - **the thirty unlashed crossings.** `span.py` already prices them at 5/3
      in span and 2.78x in rod diameter. This is the same question in the
      units a field rule is written in.
    - **the door.** Free to shut, and the only mitigation in this whole
      calculation that costs nothing and needs no part.
    - **the stock.** Rebar at the standard's minimum against a pultruded rod.
    """
    def limit(mat, hold, door):
        return analyse(data, mat, loads, hold, door)["paths"]["membrane"]["limit_ms"]

    base = limit(material, holds, "shut")
    other = "contact" if holds == "lashed" else "lashed"
    out = {
        "base_ms": base,
        "holds": {holds: base, other: limit(material, other, "shut")},
        "door": {"shut": base, "open": limit(material, holds, "open")},
        "materials": {
            name: limit(material_mod.load(name), holds, "shut")
            for name in sorted(material_mod.load_all())
        },
    }
    return out


def _ratio(a, b) -> str:
    if not a or not b:
        return "   --"
    return f"{a / b:.2f}x"


def format_comparison(data: dict, material, loads,
                      holds: str = "lashed") -> str:
    if not analyse(data, material, loads, holds)["residual"]["passes"]:
        return ("\n  nothing to price: the rod fails bent, and no choice on "
                "this list is about that.")
    c = compare(data, material, loads, holds)
    base = c["base_ms"]
    other = next(k for k in c["holds"] if k != holds)
    out = [
        "",
        "  what the open choices are worth, on the membrane reading:",
        f"    clamps      {_speed(c['holds'][holds]).strip()} -> "
        f"{_speed(c['holds'][other]).strip()} m/s going {holds} -> {other}   "
        f"({_ratio(c['holds'][other], base)})",
        f"    the door    {_speed(c['door']['shut']).strip()} shut against "
        f"{_speed(c['door']['open']).strip()} m/s open and facing the wind   "
        f"({_ratio(c['door']['open'], base)})  -- free, and nobody has written it down",
    ]
    for name, value in c["materials"].items():
        out.append(
            f"    {name:11} {_speed(value).strip():>6} m/s   "
            f"({_ratio(value, base)})"
        )
    return "\n".join(out)
