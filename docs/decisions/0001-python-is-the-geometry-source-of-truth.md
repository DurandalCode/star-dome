# 0001. Let Python own the geometry, and freeze OpenSCAD as a second implementation

- **Status:** accepted
- **Date:** 2026-09-09
- **Where it lives:** `stardome/`, `dome/star_dome.scad`, `docs/architecture.md`, the `parity` CI job

## The decision

`stardome/` is the source of truth for dome geometry and `exports/<variant>/model.json`
(schema `star_dome_geometry/1`) is the only interchange format. OpenSCAD, FreeCAD and
Blender consume it; none of them recompute geometry.

`dome/star_dome.scad` is **frozen as a reference implementation of the baseline
topology**. It keeps computing its own geometry, CI regenerates it from scratch on every
push and compares it to the Python output field for field, and it does not grow.
Everything new goes only into `stardome/`.

If the two ever disagree on the baseline topology, `stardome/` is right.

## Why

The dome's geometry is analytic — great semicircles on a sphere. None of OpenSCAD's
strengths are used, and the things this project actually needs from a geometry layer are
things OpenSCAD cannot do without a text-scraping layer: node IDs, tangents, crossing
angles, symmetry classes, JSON and CSV export, unit tests. It has no dictionaries, no
file output, no sort, and no way to read back what it produced.

The argument was never about the D6 numbers, which already existed and were correct. It
was about what comes after: transport sections and cut lists, comparing D12 reinforcement
candidates on part count and unique part types, load cases. None of that is sphere
geometry, and two of the three downstream consumers are already Python.

Keeping the OpenSCAD model alive is not sentiment. Two implementations derived
independently agreeing is stronger evidence than either alone, and it has already earned
its keep by catching a field-labelling bug in `crossing_types` that connector generation
would have inherited.

## What was rejected

- **OpenSCAD as the producer, with a scraping layer on top.** Would have put a text
  parser on the critical path of every downstream tool.
- **Converting `star_dome.scad` into a consumer of `model.json`.** Cheaper to maintain,
  and it destroys the entire value of the cross-check: an implementation that reads the
  other one's output cannot disagree with it.
- **Deleting it.** Same objection, plus it carries the written derivation of the
  geometry in `dome/README.md`, which is still the best explanation of why the design is
  what it is.

## What it costs

Two implementations of the same maths, and the discipline not to grow the second one.
That is cheap only while the baseline topology does not move, which is why the freeze is
a rule rather than a judgement call — see [0006](0006-a-superseded-design-is-frozen.md).
