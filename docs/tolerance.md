# How accurately this has to be measured

[`assembly.md`](assembly.md) says which bow goes up when. This says how
carefully each one has to be cut and marked before it does, and how carefully
the ground has to be pegged out. The answer decides the field method — tape
measure or template — and that is most of what "fast assembly" means in
practice.

```bash
python3 -m stardome tolerance D6
python3 -m stardome tolerance --all --ground 2 --cut 3 --mark 2
python3 -m stardome tolerance D6 --mark-method stepped
make tolerance GROUND=2 CUT=3 MARK=2
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
needs rod stiffness and belongs to milestone 8. Two lengths are worth having
beside it: the connector's **0.4 mm** rod clearance, which is absorbed without
flexing anything, and the **rod diameter**, past which the four marks no
longer overlap at all.

## What the field has to hold

Spread is linear in the error, to within a fraction of a percent over a range
of eight in sigma — so the useful figure is spread per millimetre of care, and
the tolerance each measurement needs is then a division rather than a search.
On M, with a 10 mm rod:

| measurement | spread per mm of σ | hold to |
|---|---|---|
| **base point placement** | 4.34 mm | **± 2.3 mm** |
| **tie mark placement** | 4.21 mm | **± 2.4 mm** |
| rod cut length | 2.03 mm | ± 4.9 mm |

Reading the raw sigmas instead would have ranked these by which one was
guessed largest; per millimetre of care, pegs and marks matter equally and
cutting matters half as much. That is worth knowing, because cutting is the
one people worry about.

**The coefficients are identical on every variant** — 4.31 / 4.22 / 2.03 on
D3 through D12, to three figures, because the shape is self-similar. Only the
target moves, with the rod:

| rod | variants | hold pegs and marks to |
|---|---|---|
| 8 mm | D3, D4 | ± 1.9 mm |
| 10 mm | D6, D8 | ± 2.3 mm |
| 12 mm | D10, D12 | ± 2.8 mm |

So **the tolerance is absolute, not proportional.** A 3 m dome needs the pegs
placed to ± 1.9 mm and a 12 m dome to ± 2.8 mm — relative to its own size the
small one is four times the demand. That is the same shape of result as
[`assembly.md`](assembly.md)'s: the small variants are not the easy ones.

## What a casual build looks like

Sigmas of 10 mm on the pegs and 3 mm on cuts and marks — a person with a steel
tape, on grass, not being especially careful. 2000 trials:

| | median | p90 | p95 | worst |
|---|---|---|---|---|
| worst node spread | **32.3 mm** | 41.4 | 44.8 | 61.0 |
| mean node spread | 23.4 mm | 29.9 | 31.9 | 40.4 |
| height off nominal | 4.8 mm | 8.5 | 10.0 | 17.1 |

The height is fine — five millimetres on a three-metre dome. The nodes are
not: **32 mm is over three rod diameters**, so at the worst node the four
marks that should coincide do not overlap at all, and the rods have to be
sprung that far to close the connector. Held to ± 2 mm on pegs and marks
instead, the same table's worst spread falls to 9.1 mm median — inside one rod
diameter, where the marks at least still overlap.

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

- **The ground wants a template, not a tape.** Ten pegs to ± 2 mm is a marked
  chain, a pre-cut rope with the decagon's ten positions on it, or a ground
  frame — anything that turns ten measurements into one object that was made
  once, carefully, indoors. This is the single largest lever in the budget.
- **Mark the rods against a jig, from one end.** Same argument, and the
  from-end rule is free on top of it.
- **Stop worrying about cut length.** ± 5 mm is loose, and a bow cut from a
  coil is easily better than that.
- **Nothing here is close to failing.** Every sensitivity is below one and
  every required tolerance is millimetres rather than tenths. The structure is
  forgiving; it just is not forgiving of a garden tape on wet grass.

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
