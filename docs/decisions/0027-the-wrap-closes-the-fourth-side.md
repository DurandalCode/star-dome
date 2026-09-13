# 0027. Close the angle in with a printed wrap, and let the pad keep the bolts

- **Status:** accepted; the fastening of [0026](0026-the-loop-is-bought-not-printed.md)
  becomes the alternative rather than the default, and the pad of
  [0025](0025-the-angle-is-met-on-a-pad.md) is unchanged
- **Date:** 2026-09-13
- **Where it lives:** `connectors/base_hub_v1.py` (`stake_wrap`, the
  `stakeWrap*` inputs), the hub's fifth print

## The decision

A **fifth printed piece** closes round the driven angle where the bottom
plate's pad cannot. It is a shallow box, pulled onto the angle by the same two
bolts the pad already carried for a U-bolt:

| what touches the steel | |
|---|---|
| the pad | the standing leg's outer face |
| the wrap's floor | the same leg's inner face — the clamped pair |
| two side walls | that leg's two edges |
| two reliefs | the other leg passes through one of them |

Three sides from the wrap and the fourth from the pad. The wrap is
67 × 32 × 11.4 mm and 18.4 cm³; one `BASE3-10` goes from 243.9 cm³ to
261.1 cm³ and from four prints to five.

Nothing else moves: the pad, its two holes at `stakeBoltSpan`, the captive
nuts in its far face, the stack, and the angle's own position are all as 0025
and 0026 left them. **The same two holes still take an M8 U-bolt**, so the
loop of 0026 remains a field alternative rather than a dead end — and the one
property it has that the wrap does not is in "What it costs" below.

## Why

0026's loop holds the section and does not care what size it is, which is
right, and it stands off the steel on a round rod, which is what got looked at
again: what was wanted was something **прилегающее** — a wrap that lies on the
angle rather than a hoop that spans it. A wrap is also stiffer per gram than a
bent rod, and it cannot rotate on the section the way a round loop can.

**Why it has to be a separate piece.** Everything the bottom plate can offer
the angle is a flat face and a hole. The angle lies against the face the plate
is *printed on*; any material reaching round the far side would hang below
that face, and below that face is the bed. That constraint produced the flat
pad in 0025 and it has not changed. What has changed is the realisation that
it binds **the plate**, not the joint: a second piece prints in its own
orientation, and in that orientation every pocket of this shape opens upwards.
The wrap needs no support, has no roof anywhere in it, and sits on the bed on
a flat face.

**The rim stops short.** `stakeWrapGap` (0.6 mm) holds the wrap clear of the
pad so that the bolts pull it onto the *angle*. Without it the two bolts clamp
plastic to plastic with the angle loose between them — which looks identical
in a render, and holds nothing. `verify` checks the gap is positive for the
same reason it checks everything else here: because it is invisible.

**Two reliefs, not one.** The angle's second leg stands out of one edge of the
first, so a wrap that made room at one edge only would be handed — and five of
the ten feet take the hub turned over. Cutting the relief at both edges costs
a few grams and makes the piece indifferent to which way the angle was driven
and which way up the hub is.

## What was rejected

- **A vee that cradles the corner.** Still rejected, and for the geometric
  reason [0026](0026-the-loop-is-bought-not-printed.md) records: a 90° vee and
  a 90° corner have parallel faces and touch only at the apex.
- **Making the wrap a full box round the whole section**, standing leg and
  all. It would wrap a fourth face that carries nothing — the section's own
  stiffness comes from that leg, not from what is round it — and it would put
  30 mm of plastic where 11.4 mm does the same job.
- **Bonding the wrap into the bottom plate as one print.** The thing that
  cannot be done at all; see above.
- **Keeping the U-bolt as the default and the wrap as an option.** The holes
  take either, so this is a documentation choice rather than a geometric one.
  The wrap is drawn because it is what was asked for; the loop keeps its
  record.

## What it costs

**A fifth print, ten times a dome.** 184 cm³ of plastic and ten more pieces to
keep track of. `bom.md` counts prints, not parts, precisely so that this shows
up: M goes from 197 prints to 207.

**The size-indifference of 0026 is gone.** The loop went round anything up to
35 mm; the wrap is drawn round one leg width with 0.4 mm of fit. What it costs
to change is bounded, and deliberately: the wrap is the ONE piece of this hub
drawn round a bought section, so buying a different angle reprints 18 cm³ and
leaves the hub alone. If that trade is ever the wrong way round, the same pad
takes the loop.

**It is still friction.** Two M8 bolts pulling a plastic box onto a steel
section, against 154 N of uplift per foot at 20 m/s. Plastic under a preload
creeps; the parameter sheet says to check the two bolts after the first night
out, and that has not changed either.
