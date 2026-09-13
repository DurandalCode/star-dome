# 0022. A material is a named candidate, not a constant

- **Status:** accepted
- **Date:** 2026-09-13
- **Where it lives:** `configs/materials.toml`, `stardome/material.py`, `docs/strength.md`

## The decision

`configs/materials.toml` carries several candidate stocks; one of them is named as
the reference in `material.REFERENCE_MATERIAL`, and every quoted result travels with
the name of the material it belongs to. `--material` selects another.

The reference is **composite GFRP rebar to GOST 31938, at the minimum the standard
permits** — not a datasheet figure, not a measurement.

## Why

Nobody has measured a bar. Milestone 3's one open item that depends on nothing else
is still open, and it will stay open until somebody buys a coil. So a single set of
material constants would be a guess presented as a property of the world, and this
project has spent four milestones being careful not to do that — `span.py` reports a
row of four sample strains rather than pick one, for exactly this reason.

Choosing the standard's *minimum* as the reference makes the argument run in the
useful direction: **a variant that passes on these numbers passes on any conforming
stock.** The converse is weaker and is stated as such — a variant that fails might
still be fine on real stock, and the answer to that is to measure a bar rather than
to argue about it.

This is the same device as `span.REFERENCE_VARIANT = "D6"`: a name, not a set of
numbers, so editing the config moves the baseline and everything downstream with it.

## What was rejected

- **One material, one set of constants.** Simpler and quotable, and it would have
  made every number in `docs/strength.md` a statement about a stock nobody has.
- **A supplier datasheet as the reference.** Better numbers, and they describe one
  manufacturer's bar rather than the class. Kept as a candidate (`pultruded_rod`)
  rather than as the baseline.
- **Deriving the shear modulus from a Poisson's ratio.** Tried, and wrong: `G = E/2(1+ν)`
  is isotropic, and unidirectional glass composite runs G/E near 0.08 against an
  isotropic 0.4. It overstates torsional stiffness about fivefold, which matters
  nowhere in the closed-form checks and matters a great deal to a frame solve of a
  *curved* member. `G` is an input, and `tests/test_material.py` fails anything above
  G/E = 0.2.
- **Reusing the creep-rupture ratio on the compression side.** There is no published
  sustained-compression figure for GFRP — ACI 440 declines to credit FRP in
  compression at all — so applying 0.20 there would have put a number in this
  repository with nothing behind it. The compression fibre gets the short-term
  allowable in both terms, and `docs/strength.md` names it as a judgement.

## What it costs

**Every number now needs a qualifier, and a reader who skips it reads the wrong
number.** "D6 stands 8.2 m/s" is meaningless without "on GOST 31938 minima, held at
the tie marks, door shut". The reports print all three and the documents repeat them,
which is wordier than a table of speeds and is the price of the answer being true.

**The goldens are now material-dependent.** A snapshot pins one material, and changing
the reference moves committed files. That is intended — it is the same property
`variants.toml` has — but it means a material edit is a reviewable change rather than
a quiet one.
