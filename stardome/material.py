"""Candidate material properties and circular-section calculations.

The defaults are legacy reference and typical values, not measured batch
properties. Under prescribed curvature stress is E*d/(2R): a higher modulus
raises bend stress while improving Euler stiffness. A minimum E therefore
cannot establish a worst-case material envelope. Reduction factors borrowed
from concrete-reinforcement guidance are screening assumptions for this dome.
See docs/strength.md and ADR 0028.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "materials.toml"

# The stock every result is quoted against unless something says otherwise:
# the rod this is most likely to be built from in Russia, at the minimum its
# standard permits. It is a name rather than a set of numbers so that editing
# configs/materials.toml moves the baseline with it.
REFERENCE_MATERIAL = "gost31938"

# How long the load is on. `sustained` is the bend, which never comes off;
# `short_term` is wind, which is minutes.
TERMS = ("sustained", "short_term")

# Which fibre of a bent rod is being checked. They have different strengths in
# this material and the weaker one is not the obvious one.
FIBRES = ("tension", "compression")


@dataclass(frozen=True)
class Material:
    """One candidate stock, with every property resolved.

    Stresses are MPa, which is N/mm^2 -- the same newtons and millimetres
    every other module here works in, so nothing needs converting at the
    boundary.
    """

    name: str
    label: str
    modulus_mpa: float
    tensile_strength_mpa: float
    compressive_strength_mpa: float
    shear_strength_mpa: float
    density_kg_m3: float
    source: str
    environmental_factor: float
    safety_factor: float
    sustained_stress_ratio: float
    shear_modulus_mpa: float
    # Wall thickness over outside diameter. Zero is a solid bar.
    wall_ratio: float = 0.0
    # Whether `rod_diameter` in variants.toml is the outside of this stock or
    # the equivalent diameter its cross-section area gives. Composite rebar is
    # the second kind: it carries a winding standing proud of the name, which
    # is why variants.toml splits rod_diameter from rod_outer_diameter.
    named_by: str = "outside"

    def __post_init__(self):
        for name in ("modulus_mpa", "tensile_strength_mpa", "compressive_strength_mpa",
                     "shear_strength_mpa", "density_kg_m3", "shear_modulus_mpa", "safety_factor"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("environmental_factor", "sustained_stress_ratio"):
            value = getattr(self, name)
            if not math.isfinite(value) or not 0 < value <= 1:
                raise ValueError(f"{name} must be in (0, 1]")
        if not math.isfinite(self.wall_ratio) or not 0 <= self.wall_ratio < 0.5:
            raise ValueError("wall_ratio must be in [0, 0.5)")

    # --- the material itself ------------------------------------------------

    @property
    def shear_ratio(self) -> float:
        """``G / E``. About 0.08 for this material, against 0.4 isotropic.

        Kept as a property so a test can catch a shear modulus that was
        derived from a Poisson's ratio instead of measured -- the single
        easiest mistake to make with a unidirectional composite, and one that
        stiffens a curved member against exactly the load the wind applies.
        """
        return self.shear_modulus_mpa / self.modulus_mpa

    @property
    def is_hollow(self) -> bool:
        return self.wall_ratio > 0.0

    def strength(self, fibre: str = "tension") -> float:
        """Configured strength on one side of the neutral axis."""
        if fibre == "tension":
            return self.tensile_strength_mpa
        if fibre == "compression":
            return self.compressive_strength_mpa
        raise ValueError(f"unknown fibre {fibre!r} -- use one of {FIBRES}")

    def design_strength(self, fibre: str = "tension") -> float:
        """Strength left after weather, before any duration reduction."""
        return self.environmental_factor * self.strength(fibre)

    def allowable(self, term: str = "sustained", fibre: str = "tension") -> float:
        """The stress this stock may carry, for a load of this duration.

        `sustained` applies the creep-rupture ratio, because a bent bow never
        unbends. `short_term` applies the partial factor instead, because wind
        is minutes and creep does not get a chance.
        """
        if term not in TERMS:
            raise ValueError(f"unknown term {term!r} -- use one of {TERMS}")
        design = self.design_strength(fibre)
        if term == "sustained" and fibre == "tension":
            return self.sustained_stress_ratio * design
        # Compression, either term, and that is a judgement rather than a code
        # limit. The creep-rupture ratio is a TENSION figure: ACI 440 declines
        # to credit FRP as compression reinforcement at all, so there is no
        # published sustained-compression ratio to apply, and inventing one by
        # reusing 0.20 would put a number in this repository with nothing
        # behind it. The compression fibre therefore gets the short-term
        # allowable in both terms. It is named as a limit in docs/strength.md.
        return design / self.safety_factor

    def allowable_strain(self, term: str = "sustained",
                         fibre: str = "tension") -> float:
        """Allowable stress over the modulus.

        This is the number `docs/span.md` prints four guesses at, and the one
        the whole family's ceiling turns on. Supplying it is the point of this
        module.
        """
        return self.allowable(term, fibre) / self.modulus_mpa

    # --- a rod of this material, at a diameter ------------------------------

    def inner_diameter(self, diameter_mm: float) -> float:
        """The bore, mm. Zero for a solid bar.

        `wall_ratio` is wall over outside diameter, so a tube's bore is
        ``d(1 - 2t/d)``. A solid bar is not that formula at ``t = 0`` -- that
        would be a shell of zero thickness -- so solid is its own case.
        """
        if not self.is_hollow:
            return 0.0
        return diameter_mm * (1.0 - 2.0 * self.wall_ratio)

    def area(self, diameter_mm: float) -> float:
        """Cross-section area, mm^2."""
        d = diameter_mm
        return math.pi / 4.0 * (d * d - self.inner_diameter(d) ** 2)

    def second_moment(self, diameter_mm: float) -> float:
        """Second moment of area about a diameter, mm^4."""
        d = diameter_mm
        return math.pi / 64.0 * (d ** 4 - self.inner_diameter(d) ** 4)

    def polar_moment(self, diameter_mm: float) -> float:
        """Torsion constant of a circular section, mm^4. Twice the above."""
        return 2.0 * self.second_moment(diameter_mm)

    def section_modulus(self, diameter_mm: float) -> float:
        """``I / c``, mm^3. The outer fibre is at half the outside diameter."""
        return self.second_moment(diameter_mm) / (diameter_mm / 2.0)

    def radius_of_gyration(self, diameter_mm: float) -> float:
        """``sqrt(I/A)``, mm. What slenderness is measured in."""
        return math.sqrt(self.second_moment(diameter_mm) / self.area(diameter_mm))

    def linear_mass(self, diameter_mm: float) -> float:
        """Mass per unit length, kg/m.

        The first density in this repository. `docs/bom.md` closes with
        "Money, and mass. Both want a supplier and a material, and this project
        has neither yet" -- half of that is now answered.
        """
        return self.area(diameter_mm) * 1e-6 * self.density_kg_m3

    # --- what bending it to shape costs -------------------------------------

    def bend_stress(self, diameter_mm: float, radius_mm: float) -> float:
        """Outer-fibre stress of a straight rod bent to a radius, MPa.

        `span.bend_strain` is the geometry -- `d / 2R`, no material in it.
        This is the same quantity in megapascals, and it is the stress the bow
        carries permanently.
        """
        return self.modulus_mpa * diameter_mm / (2.0 * radius_mm)

    def bend_utilisation(self, diameter_mm: float, radius_mm: float,
                         fibre: str = "tension") -> float:
        """Bend stress over what a permanent stress is allowed to be.

        Above 1.0 initial bending exceeds the configured criterion, without
        gravity or wind. This is not a measured creep-rupture limit.
        """
        return self.bend_stress(diameter_mm, radius_mm) / self.allowable(
            "sustained", fibre
        )

    def bendable_diameter(self, radius_mm: float, fibre: str = "tension") -> float:
        """Thickest rod of this stock that may be bent to a radius.

        The `d <= 2 R e` constraint `span.ceiling` is built on, with a configured
        allowable strain in it instead of a sample.
        """
        return 2.0 * radius_mm * self.allowable_strain("sustained", fibre)


def load_all(path=None) -> dict:
    """Load every material, with ``[defaults]`` folded in."""
    path = Path(path) if path is not None else DEFAULT_CONFIG
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)

    defaults = raw.get("defaults", {})
    out = {}
    for name, body in raw.get("materials", {}).items():
        source = str(body.get("source", "")).strip()
        if not source:
            raise ValueError(
                f"material {name!r} has no `source`. Every number in that file "
                "states where it came from; one without a source is a guess "
                "wearing a standard's clothes."
            )

        def pick(key, _body=body):
            if key in _body:
                return _body[key]
            if key in defaults:
                return defaults[key]
            raise ValueError(
                f"material {name!r} has no {key} and [defaults] does not "
                "supply one"
            )

        out[name] = Material(
            name=name,
            label=str(body.get("label", name)),
            modulus_mpa=float(body["modulus_mpa"]),
            tensile_strength_mpa=float(body["tensile_strength_mpa"]),
            compressive_strength_mpa=float(body["compressive_strength_mpa"]),
            shear_strength_mpa=float(body["shear_strength_mpa"]),
            density_kg_m3=float(body["density_kg_m3"]),
            source=source,
            environmental_factor=float(pick("environmental_factor")),
            safety_factor=float(pick("safety_factor")),
            sustained_stress_ratio=float(pick("sustained_stress_ratio")),
            shear_modulus_mpa=float(pick("shear_modulus_mpa")),
            wall_ratio=float(pick("wall_ratio")),
            named_by=str(body.get("named_by", "outside")),
        )
    if not out:
        raise ValueError(f"no [materials.*] tables found in {path}")
    return out


def load(name: str = REFERENCE_MATERIAL, path=None) -> Material:
    """Load one material by name. Fails loudly rather than falling back."""
    materials = load_all(path)
    if name in materials:
        return materials[name]
    folded = name.casefold()
    for key, candidate in materials.items():
        if key.casefold() == folded:
            return candidate
    raise KeyError(
        f"unknown material {name!r} -- known: {', '.join(sorted(materials))}"
    )


def format_material(m: Material, rod_diameter_mm: float = 10.0) -> str:
    """One candidate, as a person reads it."""
    out = [
        f"--- {m.name}  {m.label}",
        f"  source        {m.source}",
        f"  stiffness     E {m.modulus_mpa:.0f} MPa, G {m.shear_modulus_mpa:.0f} "
        f"(G/E {m.shear_ratio:.3f} -- unidirectional, not isotropic)",
        f"  strength      {m.tensile_strength_mpa:.0f} MPa tension, "
        f"{m.compressive_strength_mpa:.0f} compression, "
        f"{m.shear_strength_mpa:.0f} shear",
        f"  density       {m.density_kg_m3:.0f} kg/m3"
        + (f", tube with a {m.wall_ratio:.0%} wall" if m.is_hollow else ", solid"),
        "",
        "  assumed stress criteria after environment and duration reductions:",
        "    term          tension            compression",
    ]
    for term in TERMS:
        out.append(
            f"    {term:12}  {m.allowable(term, 'tension'):6.1f} MPa "
            f"({m.allowable_strain(term, 'tension') * 100:.3f}%)   "
            f"{m.allowable(term, 'compression'):6.1f} MPa "
            f"({m.allowable_strain(term, 'compression') * 100:.3f}%)"
        )
    out += [
        "    sustained uses an assumed creep reduction and applies to the bend, "
        "which never comes off.",
        "    there is no published sustained figure in compression, so that "
        "column repeats the short-term one.",
        "",
        f"  a {rod_diameter_mm:.0f} mm rod of it:",
        f"    section       A {m.area(rod_diameter_mm):.2f} mm2, "
        f"I {m.second_moment(rod_diameter_mm):.1f} mm4, "
        f"W {m.section_modulus(rod_diameter_mm):.1f} mm3, "
        f"r {m.radius_of_gyration(rod_diameter_mm):.2f} mm",
        f"    mass          {m.linear_mass(rod_diameter_mm):.4f} kg/m",
        "",
        "  radii at the initial-bend criterion for this E (not operating approval):",
        "    " + "  ".join(
            f"{d:.0f} mm rod -> {d / (2.0 * m.allowable_strain('sustained')) / 1000.0:.2f} m"
            for d in (8.0, 10.0, 12.0)
        ),
        "",
        "  Candidate values, not measured stock. A higher E raises bend stress; "
        "test the batch and sustained behaviour -- milestone 3.",
    ]
    return "\n".join(out)
