# How accurately this has to be measured

[`assembly.md`](assembly.md) says which bow goes up when. This says how
carefully each one has to be cut and marked before it does, and how carefully
the ground has to be pegged out. The answer decides what the field method has
to be, and that is most of what "fast assembly" means in practice.

The short version: **a tape measure is enough, at every size.** Getting there
took one wrong turn, which is recorded below rather than deleted, because the
wrong turn was about the criterion and not about the arithmetic — and that is
the part worth not repeating.

```bash
python3 -m stardome tolerance D6
python3 -m stardome tolerance --all --budget 0.2
python3 -m stardome tolerance D6 --criterion overlap
python3 -m stardome tolerance D6 --mark-method stepped
make tolerance GROUND=10 CUT=3 MARK=3
```

## Everything anyone measures: ten pegs, fifteen lengths, forty marks

- **10 base points**, at the corners of a regular decagon on the ground.
- **15 bows**, each cut to `pi * R` — 9425 mm on M.
- **40 tie marks**: fifths on family G, thirds on U and L.

Every tie mark lands on a lashed node and every lashed node is where four of
them meet, so 10 × 4 = 40, exactly the marks the model carries. The other
**30 crossings are not measured at all** — nobody marks them and nothing
locates them; they fall where the weave puts them. So the error budget for
this structure is an error budget on ten pegs, fifteen lengths and forty
marks, and on nothing else.

## Two exact sensitivities, and they both attenuate

A bow is an arc of length `L` whose chord is the base diameter `c`. Both are
measured, and together they fix the arc through `c/L = 2 sin(t/2) / t`.
Differentiating at the semicircle gives two constants:

| | |
|---|---|
| d(rise) / d(rod length) | **+1/2** exactly |
| d(rise) / d(base diameter) | **−(π/4 − ½) = −0.285398** |

Neither depends on the dome's size. Both are **below one in magnitude**, which
is the first good news here: the shape attenuates measurement error rather
than amplifying it. Cut a bow 10 mm long and the dome stands 5 mm higher; peg
the ring 10 mm wide and it stands 2.9 mm lower. Nothing about this geometry is
a knife edge.

The derivation, for the record. Write `t = π + f`. Holding the chord fixed,
`L sin(t/2)/t = c/2` expands to `L(1 − f/π) = L₀`, so `f = π·dL/L₀`;
substituting into `rise = (L/t)(1 + sin(f/2))` gives `d(rise) = dL/2`. Holding
the length fixed instead gives `f = −π²·dc/(2L)` and
`d(rise) = −dc·(π/4 − ½)`.

## But height is the wrong thing to watch

A uniformly wrong dome fits itself perfectly. Make every bow 10 mm long and
peg the ring 10 mm wide everywhere, and because the marks are fractions of
each rod's *own* length, they scale with it. Nothing binds, nothing is
pre-stressed, and the result is simply a slightly different dome.

**Only differences cost.** This bow long and that one short, this peg out and
its neighbour in — then the four marks that should meet at a node do not, and
the rods have to be sprung until they do. So the number that matters is not
the dome's height but the **node spread**: the largest distance between the
four marks that were supposed to coincide.

It is a kinematic mismatch, not a force. Turning millimetres into newtons
needs rod stiffness and belongs to milestone 8.

## The criterion is where the whole answer lives

Saying whether a given spread is acceptable needs a criterion, and the two
available differ by **an order of magnitude**, so it is an argument to
`--criterion` rather than a constant in the code.

**`curvature`, the default and the operative one.** A spread `s` sprung across
a span `a` bends the rod into a parabola of curvature `2s/a²`. The rod is
already bent to the dome radius, so report that as a fraction of the curvature
it is holding anyway. Pure geometry — no modulus, no strength, nothing to look
up. The span comes from the marking scheme, because a rod is held at its feet
and its tie marks and **nowhere else**: the 30 unlashed crossings are not
clamps and may not get a part at all. Family G's fifths give the tightest
span, 1885 mm on M, so they set the tolerance.

**`overlap`.** The four marks at a node must land within a rod diameter of
each other. This is the question a connector drawing asks, and it was the
first thing this document used — wrongly. It is **not a failure mode**: a mark
is a build aid, not a stop. The connector sits where the four rods agree to
cross, not on anybody's mark, and the rods run straight through it and slide
in their channels. Choosing it asks for about ten times the care for no
physical reason, and the recommendation that came out of it — that the ground
needed a template rather than a tape — was wrong.

Neither is a limit. Where the real limit sits needs the strength and the
ultimate strain of the actual stock, which is milestone 3's one open item that
depends on nothing else. And `2s/a²` is a worst case on top of that: it holds
the two neighbouring nodes rigid, where a real frame spreads the displacement
over several spans and pays less than this says.

## What the field has to hold

Spread is linear in the error, to within a fraction of a percent over a range
of eight in sigma — so the useful figure is spread per millimetre of care, and
the tolerance each measurement needs is then a division rather than a search.
On M, against a 10% curvature budget (59 mm of spread):

| measurement | spread per mm of σ | hold to |
|---|---|---|
| base point placement | 4.34 mm | **± 14 mm** |
| tie mark placement | 4.21 mm | **± 14 mm** |
| rod cut length | 2.03 mm | ± 29 mm |

Reading the raw sigmas instead would have ranked these by which one was
guessed largest; per millimetre of care, pegs and marks matter equally and
cutting matters half as much. That is worth knowing, because cutting is the
one people worry about.

**The coefficients are identical on every variant** — 4.31 / 4.22 / 2.03 on
D3 through D12, to three figures, because the shape is self-similar. So is the
allowance, because the span it is built from scales with the dome:

| | span (family G) | 10% of its own curvature is | hold pegs and marks to |
|---|---|---|---|
| D3 | 942 mm | 30 mm of spread | ± 7 mm |
| D4 | 1257 mm | 39 mm | ± 9 mm |
| D6 | 1885 mm | 59 mm | ± 14 mm |
| D8 | 2513 mm | 79 mm | ± 18 mm |
| D10 | 3142 mm | 99 mm | ± 23 mm |
| D12 | 3770 mm | 118 mm | ± 27 mm |

The allowance is `budget × span² / 2R` and the span is proportional to `R`, so
the tolerance is **proportional to the dome** — about one part in 215 of the
radius, at every size. Every variant is the same relative demand, and all of
them are in tape-measure territory.

(An earlier draft of this document read the tolerance off the `overlap`
criterion and concluded the opposite: ± 2 mm, absolute, with the small domes
four times the demand. That came from pinning the target to the rod diameter,
which does not scale with the dome. It was wrong. The one place the small
variants really are harder is the number of assembly moves, which
[`assembly.md`](assembly.md) settles on its own.)

## What a casual build looks like

Sigmas of 10 mm on the pegs and 3 mm on cuts and marks — a person with a steel
tape, on grass, not being especially careful. 2000 trials:

| | median | p90 | p95 | worst |
|---|---|---|---|---|
| worst node spread | **32.3 mm** | 41.4 | 44.8 | 61.0 |
| mean node spread | 23.4 mm | 29.9 | 31.9 | 40.4 |
| height off nominal | 4.8 mm | 8.5 | 10.0 | 17.1 |

The height is fine — five millimetres on a three-metre dome. And so are the
nodes: 32 mm of spread over an 1885 mm span is **5.4% of the curvature the rod
is already holding**, rising to 7.5% at p95 and about 10% at the very worst
trial. Inside the budget, from a person with a tape who is not being careful.

Thirty-two millimetres *is* over three rod diameters, and by the `overlap`
criterion that reads as a failure. It is not one. It means the connector seats
where the four rods agree rather than on any single mark, and each rod is
sprung about half the spread to get there — a few per cent of extra bend on a
member already bent to 3 m.

Where it comes from, one source at a time at those same sigmas:

| source | median worst spread |
|---|---|
| ground pegs only | 30.6 mm |
| tie marks only | 9.4 mm |
| cut length only | 4.3 mm |

## Method beats care

Two ways of taking the same measurement accumulate error differently, and at
equal per-measurement accuracy the difference is free:

| | p95 spread per mm of σ | |
|---|---|---|
| marks read from the rod's end | **4.21 mm** | independent errors |
| marks stepped off the previous one | 6.47 mm | they accumulate |
| ground pegged radially from a centre peg | 4.34 mm | ten independent errors |
| ground chained round the perimeter, closure spread | 3.90 mm | a walk, then forced closed |

**Read every mark from the same end of the rod.** Stepping off the previous
mark costs 54% more spread for exactly the same care, because the fourth mark
on a G bow carries four errors instead of one. It is the cheapest improvement
available anywhere in this document.

The ground is the opposite story: the two methods come out within 10% of each
other, which is inside the confidence anyone has in these sigmas. Chaining
wins slightly — spreading the closure error turns a random walk into a bridge,
which suppresses exactly the neighbour-to-neighbour differences that bind —
but not by enough to choose on. What decides the ground is not the method but
the per-measurement accuracy, and ± 2 mm across a 6 m circle on grass is not
what a tape does.

## What this suggests

- **A tape is enough.** ± 14 mm on the pegs of a 6 m dome, ± 7 mm on a 3 m
  one, is ordinary care with a steel tape. There is no template to build, no
  ground frame, no jig. This is the main conclusion and it is the opposite of
  what the first draft of this document said.
- **Read every mark from the same end of the rod.** The one rule worth
  keeping, because it is free: stepping off the previous mark costs 54% more
  spread for identical care.
- **Stop worrying about cut length entirely.** ± 29 mm on M. A bow cut from a
  coil is an order of magnitude better than it needs to be.
- **Nothing here is close to failing**, and the reason is structural rather
  than lucky: both exact sensitivities are below one, common-mode error is
  free, and the mismatch that is left gets spread over a span three orders of
  magnitude longer than itself.
- **The thing to actually go and do** is milestone 3's open item — buy rod and
  measure it. Everything above is expressed as a fraction of the bending the
  rod already carries, and how much of that fraction is affordable is the one
  number nobody here has.

## What this does not tell you

- **Nothing about force.** Node spread is the gap the rods must be sprung
  across, in millimetres. What that costs in stress, in a member already bent
  to the dome radius, needs rod stiffness — milestone 8.
- **Nothing about whether the connector takes it.** Some of the spread slides
  out along the channel and some does not, and which is which depends on the
  part. That is a question for the printed samples.
- **The sigmas are assumptions, not measurements.** They are a guess about a
  person with a tape. Every number above scales with them, so the first
  prototype should measure its own and re-run this.
- **Errors are taken as independent and Gaussian.** A tape that reads 2 mm
  short reads 2 mm short every time, and that is a common-mode error, which
  this document has already said costs nothing. A tape that stretches with
  temperature is not independent either, and that one is not modelled at all.
