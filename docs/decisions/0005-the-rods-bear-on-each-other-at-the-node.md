# 0005. Let the rods bear on each other at the node centre

- **Status:** accepted; partly reverses [0004](0004-the-lashed-node-is-a-stack-of-plates.md)
- **Date:** 2026-09-09
- **Where it lives:** `connectors/fan_node_v2.py` (`rodGap`), `docs/fan-node-v2.md`

## The decision

The stack pitch is `rodDiameter + rodGap`, and **`rodGap` defaults to 0**. Adjacent rods
bear on each other at the crossing, the two channels of a middle plate overlap near the
centre, and the plate simply has a hole there. It is a **cross whose arms carry the
channels**, open in the middle.

## Why

V2 was created on the argument that V1's "adjacent rods touch, so there is no room for
material between them" was only true because V1 had set the pitch to one rod diameter —
open the pitch and every pair has room. That reasoning is correct **only at the crossing
point**.

Move away from the centre and the two rods diverge in plan. Their axes stay one diameter
apart vertically, but the vertical gap between their *surfaces* opens up, because the
vertical line through a point off the axis cuts a shorter chord of each cylinder. So
material can live between two touching rods everywhere except a small lens around the
crossing. Measured on Mid2, walking out along the bisector: nothing at 3–5 mm, 0.25 mm at
6, 0.95 mm at 8, 1.95 mm at 10, full plate thickness beyond 15. All five plates remain
single valid solids — the hole disconnects nothing.

And touching is better than spacing, not merely tighter:

- **The clamping load goes rod-to-rod at the crossing**, as the reference intends and as
  the two-rod clamp already does. The plates locate; they do not carry.
- **There is no thin web to creep.** A 2 mm rib under sustained bolt preload, loaded in
  compression by a crossed-cylinder patch in PETG or ASA, was the weakest claim in the
  spaced version. It is gone.

## What was rejected

A positive gap. Every millimetre thickens the rib by a millimetre at every radius —
closing the centre hole once past 0.4 mm — and costs 3 mm of stack height, in exchange
for a web whose long-term behaviour under preload nobody can vouch for.

## What it costs

The three crossed-cylinder rod-on-rod contacts that V1's own notes flagged as the first
thing to check on a printed prototype **are back, deliberately**. Milestone 3's
"confirm rod-on-rod contact in the crossing" is still open and this is why.

A bug found on the way, worth keeping: the guard that gives a gabled channel extra room
was applied unconditionally, which pushed the pitch to 10.4 even at zero gap and quietly
parted the rods by 0.4 mm — the one thing "touching" was supposed to rule out.
