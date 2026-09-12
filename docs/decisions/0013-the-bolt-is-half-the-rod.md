# 0013. Size the fastener from the rod: half the rod, snapped to a standard bolt

- **Status:** accepted
- **Date:** 2026-09-12
- **Where it lives:** `connectors/kit.py` (`FASTENERS`, `scale_to_rod`), every generator's
  `fastenerSize` input

## The decision

Every connector took an M5 set as a constant, whatever rod it was drawn around. The bolt
is now chosen from the rod — **half the rod diameter, snapped to the nearest of
M3/M4/M5/M6/M8** — and the wall and the cross pin follow it:

| rod | bolt | pin | wall |
|---|---|---|---|
| 6 mm | M3 | 2.5 | 3.0 |
| 8 mm | M4 | 3.0 | 3.2 |
| **10 mm** | **M5** | **4.0** | **4.0** |
| 12 mm | M6 | 5.0 | 4.8 |
| 16 mm | M8 | 6.0 | 6.4 |

Wall is `0.4 × rod` with a 3 mm floor. The pin is `0.4 × rod` on stock sizes. Print fits
— `boltHoleClearance`, `headClearance`, `rodClearance` — stay absolute, because a
tolerance is not a proportion.

Zero in any of those inputs means "take it from the rod"; a real number overrides, and
`fastenerSize` pins the bolt family on its own.

## Why

The parts were sized by the bolt, and the bolt never moved. Measured across the family,
a two-rod clamp came out **8.1 × the rod** at 6 mm and **3.8 ×** at 16 mm — the same part
in absolute terms, wrapped round rods that differ by a factor of nearly three. The base
hub was worse: **113 mm across at every diameter from 6 to 16**, completely deaf to the
rod.

After: the clamp is 5.3 × the rod at 10, 12 and 16 mm, and the fan 6.4 × at all three.
The part now follows the member it holds.

**Half the rod is a convention, not a derivation.** Nothing in this project computes
force, so nothing here can say what bolt a joint needs. What the rule does is stop the
bolt being an accident of which dome was drawn first. Milestone 8 replaces it with a
number if it ever produces one.

The rule was chosen to land on M5 at 10 mm precisely so the reference prototype does not
move: **all 17 of M's printed pieces come out byte-identical**, and only the 8 mm and
12 mm parts change — the 8 mm ones smaller, the 12 mm ones larger, which was the point.

## What was rejected

- **Leaving it.** Cheapest, and it means every dome that is not D6 carries a connector
  sized for a dome it is not.
- **Scaling the fastener continuously** — an M4.7 for a 9.4 mm rod. There is no such
  bolt. Snapping to the standard family is what makes the output orderable.
- **Scaling the print fits too.** A 0.4 mm bolt-hole clearance is a property of the
  printer, not of the rod, and scaling it would make small parts loose and large ones
  tight for no reason.
- **Scaling the wall without a floor.** Below about 3 mm a printed wall is perimeters
  rather than structure, whatever it is wrapped around.

## What it costs

**The base hub still does not scale properly**: 17.7 × the rod at 6 mm and 8.1 × at
16 mm, against the clamp's flat 5.3. Its size is set by the 30 mm stake slot and the bolt
spread around it, and the stake is sized for the ground, not for the rod. Fixing that
means sizing the stake, which is `STAKE-BASE` — still the one part in the schedule with
no answer at all.

Verified by a before/after diff of every exported STL rather than by a regression test,
which is this project's practice for connector geometry: the shapes are meant to move.
