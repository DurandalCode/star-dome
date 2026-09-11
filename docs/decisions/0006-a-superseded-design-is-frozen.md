# 0006. Freeze a superseded design; do not delete it and do not update it

- **Status:** accepted
- **Date:** 2026-09-09, generalised 2026-09-10 when `connectors/kit.py` was extracted
- **Where it lives:** `dome/star_dome.scad`, `connectors/fan_node_v1.py`, `docs/fan-node-v1.md`, `docs/architecture.md`

## The decision

A superseded design stays in the repository, unchanged, and is not carried along by later
refactors. `connectors/fan_node_v1.py` imports nothing from `connectors/kit.py` even
though every other generator does.

## Why

**A superseded part is documentation, and documentation that silently follows the current
code is not a record of anything.** If a later change to the shared kit can rewrite what
an earlier design actually was, then the earlier design is no longer evidence about
anything — and the whole reason to keep it is to be able to say what was tried and what it
did.

The same argument, from the other side, freezes `dome/star_dome.scad`: its value is that
it is an *independent* implementation, so anything that makes it track `stardome/` empties
it out. See [0001](0001-python-is-the-geometry-source-of-truth.md).

## What was rejected

- **Deleting V1.** It is the record of why the node is a stack of plates rather than a
  bundle, and half of [0005](0005-the-rods-bear-on-each-other-at-the-node.md) is an
  argument with it.
- **Migrating V1 onto the shared kit for consistency.** Consistency is the cost, not the
  benefit.

## What it costs

Duplicated helpers that a linter will flag forever, and a file that will not be touched
when the kit's interface changes. Both are the point.
