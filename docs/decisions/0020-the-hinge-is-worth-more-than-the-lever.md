# 0020. The hinge is worth more than the lever: close the clamp, do not just tighten it

- **Status:** accepted
- **Date:** 2026-09-12
- **Where it lives:** `connectors/closure.py`, `crossing_clamp_v1.py`
  (`fastenerStyle`), `stardome/connectors.py` (the fastener schedule),
  [`quick-release.md`](../quick-release.md)

## The decision

The crossing clamp gains a second closure, chosen by one parameter and drawn by
the same generator:

    fastenerStyle = 0   two bolts, two nuts, a loose cap   (V1, the default)
    fastenerStyle = 1   the cap hinged on a steel pin, and ONE bolt standing
                        in a slot that is open to the outside

Both stay. `fastenerStyle = 0` is the default and its output is byte-identical
to what it was before this change — verified by a before/after STEP and STL
diff, which is this project's practice for connector geometry.

The schedule now also counts fasteners, which it never did, and counts them
**split by where they are worked**: 84 bolts in the field against 20 in the
shop on M, because `base_hub_v1` does its stack up at home and `fan_node_v2`
does not.

## Why

The survey started from the wrong question. Every quick-release mechanism worth
the name — bicycle cam skewer, over-centre toggle latch, wedge key, cam strap,
detent pin — answers *"how do I tighten this without a tool?"*, and on this part
that is half the cost at most. The other half is that **a two-piece clamp
becomes three separate objects the moment it is opened**, at head height, with
both hands busy: sixty bolts, sixty nuts and thirty caps per dome, each one
droppable into grass.

A hinge removes that, and it removes a fastener with it. One motion — swing the
cap shut — replaces holding a cap while starting two bolts into two nuts that
fall out of their traps.

The gain is measured, not asserted:

| M | bolted | hinged |
|---|---|---|
| bolts worked in the field | 84 | **52** |
| loose pieces per clamp, open | 3 | **1** |
| plastic, per clamp | 36.3 cm³ | 34.4 cm³ |
| unsupported overhang, cap | 414 mm² | 84 mm² |

The cap gets *easier* to print, not harder: the two head counterbores were most
of its overhang, and the hinged cap has one. The bottom half takes 27 mm² back
— the pin bore's roof across the fork gap, a 6.6 mm bridge — and both halves
still print flat with no support.

## What was rejected

- **A one-piece cam latch.** Right mechanism, wrong envelope. The reach from a
  pivot low in the bottom half to a bearing surface on top of the cap is 24 mm,
  against an eccentricity of 2, so the cam degenerates into a thin arc on a
  24 mm radius that sweeps across the cap as soon as the lever moves. Built,
  and the swing check failed it at ten degrees.
- **A linked over-centre toggle.** Fixes the reach and needs a clevis that can
  contain a bolt head — 11 mm across, inside a 6.6 mm fork gap. Nesting it the
  other way round works and costs three printed pieces and three pins per
  clamp: 150 prints a dome against 60.
- **A printed cam lever on the remaining bolt.** The cam's working face is a
  line contact at roughly 1.5 kN, which is why the trade specifies 45 HRC
  there. Printed PETG flattens. The mechanism is kept — as *hardware*: an M5
  bicycle seat-collar lever is an orderable part that drops onto the bolt this
  design keeps, and it is listed the way the driven steel angle is listed.
- **A strap over a printed saddle**, which is what the reference dome actually
  does at its nodes. Cheapest of all and gives grip without location. Left open
  rather than rejected: milestone 3 already asks whether the thirty untied
  crossings need a clamp at all, and if the answer is no, this is what replaces
  them.
- **Hinging on any other axis.** Not a preference. The cap wraps the rod through
  180°, so a hinge in the parting plane clears the rod immediately and a hinge
  anywhere else digs the near lip into it. The axis was forced.

## What it costs

**One printed part is now a wear part.** A knuckle with 2.85 mm of material
round its bore, turning on a steel pin, opened and closed at every build and
teardown. Nobody has cycled one.

**The load path changed and nothing measured it.** The second station used to
take its share in bolt tension; it now takes it in shear through a 3 mm pin.
Nothing in this project computes force, so whether that is equivalent is a
question for milestone 3's test rig. That is the whole reason both closures
stay: a joint whose load path has never been measured is not a joint to make
compulsory.

**Two shapes to keep alive instead of one.** Mitigated by their being one
generator with one branch rather than two files — the same decision
`term_clamp_v1.py` already made about not restating the clamp.

**It does not touch the fan node**, which is twenty of the remaining fifty-two
field bolts and a harder problem: five plates on two bolts, opened and closed
around four rods. Nothing here solves it, and the hinge does not obviously
generalise to a stack.
