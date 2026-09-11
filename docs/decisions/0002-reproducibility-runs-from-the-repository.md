# 0002. Run anything reproducible from the repository, not through MCP

- **Status:** accepted
- **Date:** 2026-09-08, restated 2026-09-10 when milestone 0 closed
- **Where it lives:** `Makefile`, `docs/architecture.md`, `docs/roadmap.md` milestone 0

## The decision

**If a result cannot be rebuilt with one command from a clean clone, it is not a
result.** Every tool — OpenSCAD, FreeCAD, Blender — is driven headless from the
`Makefile`. MCP is for interactive inspection only, and is not required by any milestone.

## Why

Milestone 0 originally required "a confirmed working MCP setup" for each of the three
applications, and the project went a different way. That turned out to be the right
accident rather than a shortcut.

An MCP session is a conversation. It is not re-runnable, not diffable, not testable, and
not available to CI. Every geometric claim this project makes rests on `make check`
passing on a machine that is not the one that wrote the change, and none of that is
possible if the tools are driven by hand.

The three binaries are variables at the top of their `Makefile` sections — `OPENSCAD`,
`FREECADCMD`, `BLENDER` — so the only machine-specific thing in the repository is a path.

## What was rejected

MCP as the primary way to drive the CAD tools. Kept for looking at things, which it is
genuinely good at.

## What it costs

Headless FreeCAD gives objects no `ViewObject`, so `apply_view` is a no-op under
`freecadcmd` and `make clamps` produces correct geometry with no colours. Cosmetic, and
recorded so the absence does not read as a bug.
