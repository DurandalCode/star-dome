# 0004. Make the four-rod node a stack of plates, not a bundle clamp

- **Status:** accepted; its stated pitch rationale is reversed by [0005](0005-the-rods-bear-on-each-other-at-the-node.md)
- **Date:** 2026-09-09
- **Where it lives:** `connectors/fan_node_v2.py`, `docs/fan-node-v2.md`

## The decision

The connector at each of the ten lashed nodes is a stack of five plates — Bottom, Mid1,
Mid2, Mid3, Cap — each carrying a channel on one or both faces. Every rod is wrapped 180°
from below by one plate and 180° from above by the next.

All five are **different parts**. Mid1 and Mid3 have the same angle between their grooves,
but the two through-bolts pin each plate's orientation in the fan and the groove pairs sit
at different azimuths, so one cannot stand in for the other. Five distinct prints per
node, ten nodes per dome. An earlier note in this project claimed three types; that was
wrong.

## Why

V1 clamped the four rods as a bundle: saddle under rod 1, cap over rod 4, rods 2 and 3
squeezed in between. It held the crossing together but it **did not locate the middle two
rods at all** — nothing stopped them sliding or rolling except friction. The dome's shape
depends on the rods crossing at the right angles at the right points, and friction is not
a guide.

## What was rejected

- **V1's bundle clamp.** Frozen rather than deleted, per
  [0006](0006-a-superseded-design-is-frozen.md).
- **A short stack of two-rod clamps at each node.** Still a legitimate alternative, and
  the reference itself lashes these joints in pairs rather than as one bundle of four.
  It stays open, to be settled on printed samples — `docs/roadmap.md` milestone 3.

## What it costs

Five loose pieces at height in the wind, which is exactly what design rule 1 says not to
do. The answer is that the bolts keep the stack captive: assemble it once, carry it as one
hinged sandwich, open it to lay each rod. In the field it is still one object per node.
