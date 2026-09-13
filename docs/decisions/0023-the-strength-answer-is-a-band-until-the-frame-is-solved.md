# 0023. The strength answer is a band until the frame is solved

- **Status:** accepted
- **Date:** 2026-09-13
- **Where it lives:** `stardome/strength.py`, `docs/strength.md`

## The decision

`stardome strength` reports **two limiting wind speeds per variant, not one**: a
`beam` reading in which the bow carries the load entirely in bending, and a
`membrane` reading in which it carries it entirely as shell thrust. Neither is
preferred, and the report says the width of the band is the finding.

A single limiting speed waits for a frame solve.

## Why

Because the gap is two orders of magnitude, and no closed form closes it.

On D6 at 20 m/s the beam reading gives 1458 MPa of bending stress and the membrane
reading gives 4.4 MPa of thrust. Against an 800 MPa bar the first is impossible and
the second is nothing. The truth depends entirely on how much the ninety rod-on-rod
contacts force the bow to act as part of a shell — which is a stiffness question, and
`span.py` already said so about the unknown constant in front of `w a⁴/EI`.

Picking one and quoting it would have been inventing confidence. Reporting both makes
the state of knowledge legible, and it sets a measurable bar for the next piece of
work: the frame solve is worth building exactly insofar as it narrows this.

The two bounds are also **wrong in known directions**, which is more useful than a
midpoint would have been:

- the beam bound is refuted by the dome standing up at all — under it a D6 bow sags
  80 mm in a dead calm, which a real Star Dome visibly does not do;
- the membrane bound gives the bow the full shell thrust and then buckles it as a
  pin-ended strut over its whole free span, as though the shell it belongs to were
  not restraining it.

So the truth is above the beam figure and above the membrane one, and the table is a
table of floors.

## What was rejected

- **A single number from the envelope reading.** It is the most conservative of the
  three and it is dominated by the bound that is refuted, so it would have been the
  most confidently wrong answer available.
- **A midpoint, or a weighted blend.** There is nothing to weight it with. A blend
  would have hidden the uncertainty inside a number that looks like knowledge.
- **Waiting for the frame solve and publishing nothing.** The material, the loads,
  the anchor path and the bend check are all independent of how the bow carries the
  wind, and the bend check alone already condemns D3. Holding it back would have
  delayed a result that does not depend on the unresolved part.
- **Scoring deflection as a strength check.** Under the beam reading it fails at zero
  wind, which reports "0 m/s" and tells a reader nothing. It is a validity gate on
  small-deflection theory instead, and the sag is printed for a person to look at.

## What it costs

**There is no operating limit yet.** The deliverable milestone 8 actually wants is a
number a marshal can act on, and a band from 3.5 to 8.2 m/s is not one. Until the
frame solve lands, the only defensible field rule is the lower figure, and the lower
figure is known to be too low.

**Two readings are two chances to quote the wrong one.** The same hazard decision
0015 accepted for `lashed` and `contact`, and handled the same way: both printed,
side by side, with the gap named.
