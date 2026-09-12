"""Variant configuration loading.

``configs/variants.toml`` is the only file in the repository that contains a
variant-specific number. Everything else derives from it.
"""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "variants.toml"


@dataclass(frozen=True)
class Variant:
    """One named dome variant, with every dimension resolved."""

    name: str
    diameter: float
    rod_diameter: float
    note: str
    rod_segments: int
    section_length: float
    weave_gap: float
    skirt_height: float
    # Short size name for the sizes that are an actual product -- S, M, L, XL.
    # The D-names stay the geometric family; an alias is a chosen build of one,
    # with its skirt and its door settled. Empty for the research variants.
    alias: str = ""
    # Which person-silhouette the doorway is sized to, from entrance.TEMPLATES.
    # Empty means this variant has no door worked out and none is serialised.
    door: str = ""
    # How far the doorway is cut open. "none" leaves the lancet alone;
    # "jambs" removes the two end pieces that frame it, which severs nothing;
    # "head" also removes the two pieces still crossing above them, which
    # severs two bows and leaves the head node with nothing passing through
    # it. See doorway.CUT_LEVELS.
    door_cut: str = "none"

    @property
    def radius(self) -> float:
        return self.diameter / 2.0

    @property
    def overall_height(self) -> float:
        """Structural height including the skirt the dome stands on.

        The dome's own height is the apex of family U, which is a derived
        angle, not a typed constant -- see geometry.family_tilts.
        """
        from . import geometry

        apex = math.sin(math.radians(geometry.family_tilts()["U"]))
        return self.skirt_height + self.radius * apex

    @property
    def bend_radius(self) -> float:
        """Radius every bow is bent to.

        Equal to the dome radius by construction, which is why it scales
        directly with the variant and is a hard constraint on rod selection
        rather than an afterthought. See docs/roadmap.md milestones 4, 6, 8.
        """
        return self.radius


CUT_LEVELS = ("none", "jambs", "head", "portal")


def _cut_level(value) -> str:
    """Read door_cut, accepting the bool it used to be."""
    if value is None or value is False:
        return "none"
    if value is True:
        return "jambs"
    text = str(value)
    if text not in CUT_LEVELS:
        raise ValueError(
            f"door_cut must be one of {CUT_LEVELS}, got {value!r}"
        )
    return text


def load_all(path=None) -> dict:
    """Load every named variant, with ``[defaults]`` folded in."""
    path = Path(path) if path is not None else DEFAULT_CONFIG
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)

    defaults = raw.get("defaults", {})
    variants = {}
    for name, body in raw.get("variants", {}).items():
        variants[name] = Variant(
            name=name,
            diameter=float(body["diameter"]),
            rod_diameter=float(body["rod_diameter"]),
            note=str(body.get("note", "")),
            rod_segments=int(body.get("rod_segments", defaults.get("rod_segments", 48))),
            section_length=float(
                body.get("section_length", defaults.get("section_length", 2400))
            ),
            weave_gap=float(body.get("weave_gap", defaults.get("weave_gap", 1.0))),
            skirt_height=float(
                body.get("skirt_height", defaults.get("skirt_height", 0.0))
            ),
            alias=str(body.get("alias", "")),
            door=str(body.get("door", defaults.get("door", ""))),
            door_cut=_cut_level(body.get("door_cut", defaults.get("door_cut"))),
        )
    if not variants:
        raise ValueError(f"no [variants.*] tables found in {path}")

    aliases = [v.alias for v in variants.values() if v.alias]
    clash = set(aliases) & set(variants)
    if clash:
        raise ValueError(f"alias collides with a variant name: {sorted(clash)}")
    if len(aliases) != len(set(aliases)):
        raise ValueError(f"duplicate aliases in {path}: {sorted(aliases)}")
    return variants


def resolve(name: str, path=None) -> str:
    """Canonical variant name for a name or an alias.

    ``S`` and ``D4`` are the same dome; the short names are what a person
    says and the D-names are what the geometry is filed under.

    Case does not count. A person types ``d6`` as readily as ``D6``, and the
    Makefile asks this to turn whatever was typed into the name the files are
    filed under -- so refusing a lowercase one fails the build rather than the
    lookup, and does it after the model has already been written.
    """
    variants = load_all(path)
    if name in variants:
        return name
    folded = name.casefold()
    for canonical, variant in variants.items():
        if canonical.casefold() == folded:
            return canonical
        if variant.alias and variant.alias.casefold() == folded:
            return canonical
    known = ", ".join(
        sorted(f"{n}={v.alias}" if v.alias else n for n, v in variants.items())
    )
    raise KeyError(f"unknown variant {name!r} -- known: {known}")


def load(name: str, path=None, **overrides) -> Variant:
    """Load one variant by name or by alias.

    Fails loudly rather than silently falling back, so a typo in a variant
    name cannot quietly produce the wrong dome.
    """
    variants = load_all(path)
    variant = variants[resolve(name, path)]
    if overrides:
        variant = replace(variant, **overrides)
    return variant
