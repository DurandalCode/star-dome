"""What things are made of, in one place, with their honesty labelled.

Before this, the same rod's density sat in two modules and its modulus in a
third. Change one and the mass in the rod report silently stopped agreeing
with the mass in the wind screening. That is the bug this file exists to
prevent, and it is worth being clear about what belongs here and what does
not.

## Three kinds of number, and only one kind lives here

**Physical constants** -- gravity, air density at a stated condition. Not
assumptions, though air density is a condition rather than a universal.

**Material properties we have NOT measured.** Every one of these is a trade
figure or a textbook range, and the real stock varies by supplier, by batch
and by coating. They are the reason half this project's reports carry a
warning. Each carries `measured: False` so that a report can say so, and so
that the day something IS weighed the change is one line.

**Not here:** anything variant-specific (that is `configs/variants.toml`,
which is the only file with a variant's numbers in it), anything derived from
the dome's geometry (`geometry.py`), and any design decision -- a section
limit, a seam allowance, an engagement length. Those are choices, not
properties, and they belong with the choosing.

## Choosing, per variant

A dome picks its rod and its fabric by name in `variants.toml`; the
properties come from here. That is why D3 on 8 mm and D12 on 12 mm can be the
same material without repeating its density twice.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# physical constants
# --------------------------------------------------------------------------
GRAVITY = 9.80665  # m/s2

# Air at 15 C, sea level. A condition, not a universal -- cold dense air
# pushes harder, and a mountain site pushes less.
AIR_DENSITY = 1.225  # kg/m3
AIR_CONDITION = "15 C, sea level"


def _entry(**kw) -> dict:
    """A material record, defaulting to unmeasured."""
    kw.setdefault("measured", False)
    return kw


# --------------------------------------------------------------------------
# the rod
# --------------------------------------------------------------------------
ROD = {
    "gfrp_pultruded": _entry(
        label="pultruded GFRP",
        modulus_mpa=40000.0,
        density_kgm3=1900.0,
        note=(
            "Fibre along the axis, so the bending modulus is the one that "
            "matters and it varies with fibre fraction. Confirm against the "
            "supplier's data sheet, and weigh a metre of the real stock."
        ),
    ),
}
DEFAULT_ROD = "gfrp_pultruded"


# --------------------------------------------------------------------------
# the cover
# --------------------------------------------------------------------------
# Areal weight in g/m2 INCLUDING a typical PU coating. Trade denier numbers
# are not a specification and the coating can move these by half again.
FABRIC = {
    "oxford_210d": _entry(label="210D Oxford", gsm=120.0),
    "oxford_420d": _entry(label="420D Oxford", gsm=190.0),
    "oxford_600d": _entry(label="600D Oxford", gsm=290.0),
}
DEFAULT_FABRIC = "oxford_600d"


# --------------------------------------------------------------------------
# the section ferrule
# --------------------------------------------------------------------------
# modulus, an allowable working stress, density, and the thinnest wall the
# process will give. The last one is what decides the comparison -- see
# docs/splice.md.
SLEEVE = {
    "aluminium_6061": _entry(
        label="aluminium 6061", modulus_mpa=69000.0, allowable_mpa=150.0,
        density_kgm3=2700.0, min_wall_mm=0.8, made_by="drawn tube, cut to length",
    ),
    "steel_mild": _entry(
        label="mild steel", modulus_mpa=200000.0, allowable_mpa=140.0,
        density_kgm3=7850.0, min_wall_mm=0.8, made_by="drawn tube, cut to length",
    ),
    "stainless_304": _entry(
        label="stainless 304", modulus_mpa=193000.0, allowable_mpa=120.0,
        density_kgm3=8000.0, min_wall_mm=0.8, made_by="drawn tube, cut to length",
    ),
    "printed_pla": _entry(
        label="printed PLA", modulus_mpa=3500.0, allowable_mpa=20.0,
        density_kgm3=1240.0, min_wall_mm=1.2, made_by="printed",
        note="Creep under sustained bending is the open question, not strength.",
    ),
    "printed_petg": _entry(
        label="printed PETG", modulus_mpa=2100.0, allowable_mpa=18.0,
        density_kgm3=1270.0, min_wall_mm=1.2, made_by="printed",
    ),
    "printed_nylon_cf": _entry(
        label="printed nylon-CF", modulus_mpa=6000.0, allowable_mpa=40.0,
        density_kgm3=1200.0, min_wall_mm=1.2, made_by="printed",
    ),
    "cast_aluminium": _entry(
        label="cast aluminium", modulus_mpa=70000.0, allowable_mpa=60.0,
        density_kgm3=2680.0, min_wall_mm=3.0,
        made_by="cast from a printed pattern",
    ),
    "cast_bronze": _entry(
        label="cast bronze", modulus_mpa=100000.0, allowable_mpa=90.0,
        density_kgm3=8800.0, min_wall_mm=3.0,
        made_by="cast from a printed pattern",
    ),
}
# The recorded decision: a steel sleeve, the rods butting inside it, a cross
# fastener each side. Note the made_by above -- "drawn tube, cut to length" is
# the whole of the manufacture. See docs/transport.md.
DEFAULT_SLEEVE = "steel_mild"


# --------------------------------------------------------------------------
# lookup
# --------------------------------------------------------------------------
CATALOGUES = {"rod": ROD, "fabric": FABRIC, "sleeve": SLEEVE}


def get(catalogue: str, name: str) -> dict:
    """One material, by catalogue and name, or a useful error."""
    if catalogue not in CATALOGUES:
        raise ValueError(
            f"no catalogue {catalogue!r}; have {sorted(CATALOGUES)}"
        )
    entries = CATALOGUES[catalogue]
    if name not in entries:
        raise ValueError(
            f"no {catalogue} called {name!r}; have {sorted(entries)}"
        )
    return entries[name]


def unmeasured() -> list:
    """Every property in here that nobody has put on a scale.

    A report that leans on these should be able to say which ones, rather
    than carrying a general disclaimer.
    """
    out = []
    for catalogue, entries in sorted(CATALOGUES.items()):
        for name, entry in sorted(entries.items()):
            if not entry.get("measured"):
                out.append(f"{catalogue}.{name}")
    return out
