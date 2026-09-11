# 0003. Never let two producers write the same filenames

- **Status:** accepted
- **Date:** 2026-09-09
- **Where it lives:** `docs/architecture.md`, the `exports/` layout

## The decision

Each producer writes to its own directory and must keep doing so:

| directory | written by | read by |
|---|---|---|
| `exports/model/` | `stardome` — the source of truth | everything downstream |
| `exports/geometry/` | `tools/export_geometry.py` — the OpenSCAD reference | the parity tests only |
| `exports/connectors/` | `connectors/generate_clamps.py` | slicers, the workshop |
| `exports/blender/` | `blender/build_scene.py` | people |

## Why

They shared `exports/geometry/` briefly and the effect was exactly what you would expect:
a Blender rebuild overwrote the OpenSCAD reference with Python output, and the parity
tests started comparing the Python model against itself. **They passed.**

That is the failure mode worth recording. A cross-check that has quietly become a
self-check reports success, so nothing draws attention to it. The only defence is a
layout rule.

## What was rejected

One `exports/` directory with the producer in the filename. Would have worked, and puts
the guarantee in a naming convention that any script can break by accident instead of in
a directory that a script has no reason to write to.

## What it costs

Four directories instead of one, and `make clean` has to know about all of them.
