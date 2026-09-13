# 0026. Hold the angle with a bought U-bolt, and stop caring what size it is

- **Status:** accepted; replaces the fastening chosen in
  [0025](0025-the-angle-is-met-on-a-pad.md), which keeps the pad
- **Date:** 2026-09-13
- **Where it lives:** `connectors/base_hub_v1.py` (`u_bolt`, `arc_height`,
  the `stakeUBolt*` inputs)

## The decision

The base hub's pad stays exactly as [0025](0025-the-angle-is-met-on-a-pad.md)
left it — flat, on the outside of the bottom plate, straight down from the
hub. What goes round the angle is **an M8 U-bolt, both legs through the pad,
a nut and a washer on each.** Nothing is drilled in the steel.

| | 0025 | this |
|---|---|---|
| what holds it | one M8 through a drilled hole | a U-bolt round the section |
| what the angle needs | a row of Ø8.5 at 20 mm pitch | nothing |
| height on the angle | ±10 mm, in 20 mm steps | **any** |
| what leg it takes | the one it was drawn for | any up to 35 mm, on a 50 mm loop |
| printed parts per hub | 4 | 4 |

The reported `stakeUBoltFits` is that last row, and it is the whole point: the
size of the driven member stops being a dimension of the printed part.

## Why

0025 answered "the hub has to find its own height" with a ladder — a row of
holes down the angle's leg, bolt through whichever one lands. **Dry ground
does not take a ladder's answer.** An angle driven into hard soil stops where
it stops; the hole that was 40 mm above the ground on the last foot is 15 mm
below it on this one, and a row fine enough to always have a hole in the right
place is a row that has taken the section out of the steel.

So the requirement was really three:

1. **wrap the section**, not touch one face of it;
2. **hold at any height**, not at indexed heights;
3. **not care what size the angle is**, because `STAKE-BASE` is still chosen
   by guess ([`strength.md`](../strength.md)) and whatever gets chosen should
   not need the hub redrawn.

A loop of bent rod does all three, costs no print, and is the ordinary
hardware answer to "clamp this member to that plate". The pad gives it a flat
face to pull against and two holes to come up through, and that is all the
printed part has to know.

**The load was never the hard part.** Per foot at 20 m/s the ground takes
154 N of uplift (`make loads`). Two M8 nuts pulled up to what the plastic
under their washers will take — about 2.7 kN each before a PETG pad starts to
yield under a DIN 125 washer — clamp the section with of order 2 kN of slip
resistance across the steel-on-steel and steel-on-plastic contacts. That is
more than ten times the load, which is the margin friction wants.

## What was rejected

- **A printed vee that cradles the corner.** The obvious shape, and it fails
  requirement 3 by geometry: a 90° vee and a 90° corner have **parallel**
  faces, so they touch only when the corner reaches the apex. One vee fits one
  leg width exactly and lets anything smaller rattle in it. This is worth
  writing down because the vee looks right until it is drawn.
- **A printed two-piece clamp** — the pad plus a cap that pinches the angle's
  flat leg between two parallel faces. It does satisfy all three, and it stays
  the fallback if U-bolts are awkward to source. It costs a fifth print per
  hub, 10 per dome, and it grips one leg where the loop grips the section.
- **A set screw threaded into the pad, bearing on the angle.** What a set screw
  needs is something to press the member *against*, i.e. a socket. A socket
  needs material on the far side of the angle, and the far side of the angle is
  below the face the plate is printed on — which is below the bed. This part
  cannot have a socket; that is the same constraint that produced the flat pad
  in 0025.
- **Keeping the drilled hole row as well, as a backstop.** Two ways of holding
  one joint is two ways to get it wrong, and the hole row's only advantage —
  bearing rather than friction — is not worth 10 drilled angles at a tenth of
  the load.

## What it costs

**It is friction.** A bearing joint does not care about preload; this one
does, and plastic under a preload creeps. The parameter sheet says so in the
`stakeGrip` row: check the two nuts after the first night out. If a foot is
ever found to have crept, the printed two-piece clamp above does not fix that
either — the fix is a bearing joint, which means drilling the steel after all.

**The pad went from 38 mm across to 75.** The loop's span sets it: 50 mm
between the legs, plus a hole and a wall either side. One `BASE3-10` goes from
231.3 cm³ to 243.9 — still 43% under what the slot cost, and the bottom plate
is 86 cm³ against the 258 it started at. On M the base hubs are 2259 cm³ of
5101, which is 44% of the dome's plastic against the 59% the slot cost.

**Two more bought items at each foot.** `STAKE-BASE` was one line with no
answer; it is now an angle *and* a loop to go round it, and the loop's span is
the number that has to be looked up when the angle is finally chosen. The
fastener schedule counts neither — it did not count 0025's bolt either.
