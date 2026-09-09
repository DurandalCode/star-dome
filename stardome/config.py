"""Variant configuration loading.

``configs/variants.toml`` is the only file in the repository that contains a
variant-specific number. Everything else derives from it.
"""

from __future__ import annotations

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

    @property
    def radius(self) -> float:
        return self.diameter / 2.0

    @property
    def bend_radius(self) -> float:
        """Radius every bow is bent to.

        Equal to the dome radius by construction, which is why it scales
        directly with the variant and is a hard constraint on rod selection
        rather than an afterthought. See docs/roadmap.md milestones 4, 6, 8.
        """
        return self.radius


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
        )
    if not variants:
        raise ValueError(f"no [variants.*] tables found in {path}")
    return variants


def load(name: str, path=None, **overrides) -> Variant:
    """Load one variant by name.

    Fails loudly rather than silently falling back, so a typo in a variant
    name cannot quietly produce the wrong dome.
    """
    variants = load_all(path)
    if name not in variants:
        known = ", ".join(sorted(variants))
        raise KeyError(f"unknown variant {name!r} -- known: {known}")
    variant = variants[name]
    if overrides:
        variant = replace(variant, **overrides)
    return variant
