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
class Door:
    """One doorway: how far it is cut open, and which way it faces.

    ``facing`` is an azimuth in degrees, and it is a *wish* rather than a
    position: a door can only go in a bay, there are ten of them, and which
    ones are eligible depends on the cut -- a portal is a low bay opened up
    and everything else is a tall one. The placement takes the eligible bay
    nearest the wish and reports where the door actually landed.

    ``None`` means "wherever this dome puts its first one", which is what
    every variant meant before a dome could have two.
    """

    cut: str = "none"
    facing: float | None = None
    # Silhouette this door is sized to. Empty means the variant's own `door`.
    template: str = ""


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
    # What a caliper reads across the rod, when that is not what the rod is
    # called. Composite rebar -- the fibreglass rod this is most likely to be
    # built from in practice -- is named by its EQUIVALENT diameter, the one
    # its cross-section area gives, while its surface carries a winding that
    # stands proud of it. Nothing goes in a channel cut to the name.
    #
    # So the two jobs one number used to do are split. `rod_diameter` is the
    # rod as a structural member: what the fastener is sized from, what the
    # splice sleeve is ten of, what bending is judged against. This is the rod
    # as an object that has to fit: channels, rod-on-rod contact at a node, the
    # weave's radial spacing, the doorway envelope, and the sphere the fabric
    # ends up resting on.
    #
    # Zero means they are the same, which is true of plain round rod and is
    # what every variant says until somebody measures one.
    rod_outer_diameter: float = 0.0
    # Every door on this dome. A camp is domes with doors facing each other,
    # so how many and which way is a property of the dome rather than
    # something the geometry picks -- see docs/doorway.md. Empty falls back to
    # the single door `door` and `door_cut` describe.
    doors: tuple = ()

    @property
    def doorways(self) -> tuple:
        """Every door on this dome, however the config spelled it.

        One reading for consumers, whether the variant carries a `doors`
        array or the older single `door` + `door_cut` pair.

        `door_cut` is normalised here as well as at load, because an override
        goes straight into the dataclass and skips the loader -- and the field
        still accepts the bool it used to be.
        """
        if self.doors:
            return tuple(
                Door(cut=_cut_level(d.cut), facing=d.facing, template=d.template)
                for d in self.doors
            )
        if self.door:
            return (
                Door(cut=_cut_level(self.door_cut), facing=None, template=self.door),
            )
        return ()

    @property
    def rod_fit_diameter(self) -> float:
        """The diameter anything has to clear. See `rod_outer_diameter`."""
        return self.rod_outer_diameter or self.rod_diameter

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


def _doors(body, defaults) -> tuple:
    """Parse `[[variants.X.doors]]`, or fall back to the single-door pair.

    An empty tuple means "there is no array here"; the variant's `door` and
    `door_cut` then describe the one door, exactly as they always did.
    """
    raw = body.get("doors")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("doors must be an array of tables, one per doorway")
    fallback = str(body.get("door", defaults.get("door", "")))
    out = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(f"doors[{i}] must be a table")
        unknown = set(entry) - {"cut", "facing", "template"}
        if unknown:
            raise ValueError(
                f"doors[{i}] has unknown keys {sorted(unknown)}; "
                "a door takes cut, facing and template"
            )
        facing = entry.get("facing")
        template = str(entry.get("template", "")) or fallback
        if not template:
            raise ValueError(
                f"doors[{i}] has no template and the variant has no `door` "
                "to fall back on; a doorway is sized to a silhouette"
            )
        out.append(
            Door(
                cut=_cut_level(entry.get("cut")),
                facing=None if facing is None else float(facing) % 360.0,
                template=template,
            )
        )
    if not out:
        raise ValueError("doors is empty; leave it out to have no door at all")
    return tuple(out)


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
            rod_outer_diameter=float(
                body.get("rod_outer_diameter", defaults.get("rod_outer_diameter", 0.0))
            ),
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
            doors=_doors(body, defaults),
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
