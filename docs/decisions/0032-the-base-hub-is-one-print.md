# 0032. Print the base hub in one piece: a tube per bow on a rib, and a sleeve for the bar

- **Status:** accepted; replaces the plate stack the base hub inherited from
  [0004](0004-the-lashed-node-is-a-stack-of-plates.md), and the cradle of
  [0031](0031-the-stake-is-rebar-and-a-vee-takes-any-bar.md), which keeps its
  argument that a vee takes any round bar
- **Date:** 2026-10-08
- **Where it lives:** `connectors/base_hub_v2.py`, [`base-hub.md`](../base-hub.md)

## The decision

Base hub 2.0 is **one print**. Each bow gets a closed tube at its 1.x level,
in fan order, at the 1.x fan angles. Each tube stands on a rib down to the
bed, and the rib flares into the tube at 50° to horizontal. Behind the centre
every channel leaves through a small core. Under all three levels runs a
sleeve for the rebar, 80 mm long. Its roof is an 80° vee and two M8 set bolts
push the bar into it from below. Every channel, pin hole and vee prints with a
pointed roof. Nothing needs supports.

| | 1.1 | 2.0 |
|---|---|---|
| prints per hub | 5 | **1** |
| `BASE3-8` plastic | 222 cm³ | **98 cm³** |
| `BASE3-10` plastic | 295 cm³ | **121 cm³** |
| bolts done up at home | 4 × M5 | **none** |
| stake grip | 40 mm cradle, loose, two bolts | **80 mm sleeve, part of the hub, two bolts** |
| bars it takes | 8–18 mm | 8–18 mm |
| bow ends | slid into split channels | threaded into tubes |

On M that is **169 prints a dome instead of 207**, and the hubs fall from 49%
of the plastic to 29%.

## Why

The printed 1.x `BASE3-8` showed what the stack costs. Each plate is the full
outline of the hub, so every level is solid across every arm while holding one
rod. Seen end on, the stack is a block with three holes in it. The stack is
there because a lashed node needs it: there the rods pass through each other's
crossing and have to be laid in between plates. A base point needs neither. A
bow end goes about ten centimetres into the hub, so threading it into a closed
tube costs nothing. A closed tube needs no plate on either side of it.

The levels stay. The three bows meet at one point in one plane, so the ends
could share a level, but the channel should be able to take a bow running on
through the foot. Behind the centre the arms point into the ground, so what
that buys in practice is a channel open at the back: a rod cut long still
fits, nothing collects in a blind pocket, and a jammed end can be knocked out.

The field sequence follows the user's concept: drive the bar, drop the hub
over it, do up two bolts, push the bows in, pin them. The sleeve replaces the
cradle because it is longer, it is part of the hub, and it leaves nothing loose
to hold while a bolt is started.

## What was rejected

- **Two halves split on the middle rod.** Two prints, no supports, the middle
  rod laid in. It loses to one piece once threading is free.
- **The 1.x plates, each with only its own arms.** It removes the solid
  blocks, but keeps four prints and four stack bolts.
- **One piece with all three tubes in the fan plane.** That gives the least
  plastic and the shortest part. It was dropped because a bow could no longer
  run through the foot.
- **One piece with supports under the upper tubes.** The ribs do the same job
  and stay in the part, as stiffness.
- **The sleeve above the tubes.** Over most of its length nothing would be
  under it, so it needs a rib or a block anyway. Under the tubes it sits on
  the bed.
- **A 90° vee and 45° roofs.** A face drawn at exactly the printer's limit
  passes or fails the overhang check on rounding. It did both, at two rod
  sizes. Every slope is now 50°.

## What it costs

- **Height.** The sleeve sits under all three levels, so the part is about
  70 mm tall on the bed, and the ribs under the upper tubes are up to 50 mm
  deep. Most of 2.0's plastic is ribs.
- **The bar sits further from the bows.** It is 27 mm from the middle level
  on `BASE3-10`, against 25 mm from the outer plate face in 1.x, and the foot's
  shear acts on that lever.
- **The channel is the printed 1.x number, Ø9.4.** That is taken from one fit
  in the hand: a 10 mm composite rebar goes in, an 8 mm one rattles. It is not
  derived from the rod. Nobody has measured the rebar across its winding.
- **The nuts go in first.** The two M8 nuts drop into pockets in the tunnel
  floor before the hub goes onto the bar. Once the bar is in, the nuts cannot
  be reached.
- **Nothing is proven.** Rib stiffness, the tubes' layer lines and the grip
  of the set bolts are all unmeasured. 2.0 is a fit check, like 1.x was.
