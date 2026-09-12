# 0019. Derive a camp's doors and turns from its links

- **Status:** accepted; refines [0018](0018-a-camp-is-a-plan-and-a-dome-is-turned-not-redrilled.md)
- **Date:** 2026-09-12
- **Where it lives:** `stardome/camp.py` (`doors_needed`, `best_turn`, `prepare`), `configs/camps.toml`, `docs/camp.md`

## The decision

A dome in a camp carries **one door per neighbour, pointed at it**, and is set down at
the **turn that suits its bays best**. Neither is written anywhere: the links determine
both, and `camp.prepare` builds each dome accordingly.

`configs/variants.toml` goes on describing a dome standing on its own. `turn` stays in
`configs/camps.toml` only as an override.

## Why

0018 left doors in `variants.toml` and said a dome short of one should be reported so a
person could add it. The first real camp showed what that costs: an XL hub with two
halls, one hall with two more domes and one of those with two small ones needs two, three
and three doors respectively — none of which belongs in a variant that also stands on its
own elsewhere. The count and the directions are facts about the *site*.

0018's objection to deriving the turn was that it "would have quietly rotated a dome away
from a door the designer aimed on purpose". Once the doors are derived too there is no
such door, so the objection lapses and the derivation is free.

**And the first plan failed for a reason nothing had said out loud.** A door goes in a
bay; a dome has five of each kind, 72° apart. So a dome cannot put a door on an arbitrary
bearing — the nearest bay may be 36° away. Worse:

> A bearing and its reverse differ by 180°, and 180 is not a multiple of 72, so two domes
> turned the same way can **never** both have a door on the line between them.

Turn one of the pair by 36° and both can. A camp whose links form a tree can always be
coloured that way, and the derived turns come out alternating 0° and 36° along every
corridor without anyone arranging it. The shipped `tree` — seven domes, six corridors —
lands square on a door at both ends of all six.

## What was rejected

- **Adding the doors to `variants.toml`.** D8 would carry three doors everywhere,
  including standing on its own, and the second and third cost rod and two part types
  each. A dome does not gain a doorway by being drawn next to another dome.
- **Overriding doors per camp.** Still rejected, and for 0018's reason: it writes a
  bearing in two files. Deriving is not overriding — nothing is written twice.
- **A variant per role**, `D8-hub` with three doors. It multiplies `variants.toml` by the
  shapes of every camp anybody ever draws.
- **Solving the turn analytically.** The objective is a maximum of absolute angular
  differences on a circular domain: corners everywhere, and a scan at a quarter of a
  degree is exact enough for a thing that is built with a tape measure.
- **Refusing a layout whose bearings are off the 72° grid.** It is a real plan with real
  doors a little off square, and the report says by how much.

## What it costs

**A camp's domes are not the variants they name.** `stardome camp --json` ships a model
per dome beside the plan, because a consumer cannot rebuild what it does not know; a
scene given only the variant draws the wrong doors, and `build_site.py` says so when a
plan predates them.

**The layout is constrained by the lattice.** Neighbours want to sit at bearings 72°
apart from a common dome. That is a real restriction on where a camp can put things, and
it is the price of the doors landing square.

**Nothing checks that the corridor fits, still.** `stardome camp` reports it; the joint
where a tunnel meets a cover — the hole, the hoop that lands on it, the load path — does
not exist. Milestones 5 and 8.
