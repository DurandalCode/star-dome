# What the rod can actually take

[`span.md`](span.md) measures the demand and then stops, in as many words:
*"There is no modulus, no strength and no load anywhere in it."*
[`configs/variants.toml`](../configs/variants.toml) says the same thing about
its own contents — the rod diameters are *"engineering assumptions, not
results"*. This is the first document in the project with all three in it.

```bash
make materials                          # what each candidate stock can take
make loads WIND=20                      # what the wind does to the shell
make strength                           # the limiting speed, and what binds it
python3 -m stardome strength M --compare
python3 -m stardome strength M --material pultruded_rod --door open
```

Three new inputs, and each is its own file so that a number can be argued with
without touching the code: [`materials.toml`](../configs/materials.toml) for
the stock, [`loads.toml`](../configs/loads.toml) for the wind, and every value
in both carries the standard it came from.

## The answer is a band, and the width of it is the point

A bow is a curved member held at intervals. How much of the wind it carries by
bending and how much by arch action is not knowable in closed form — `span.md`
says exactly this about the unknown constant in front of `w a⁴/EI` — so two
bounding readings are computed and neither is preferred:

- **`beam`** — the bow spans between its supports and carries everything in
  bending. `M = wa²/8`, no axial force.
- **`membrane`** — the lattice is a discretised shell. A sphere under normal
  pressure carries `n = pR/2` per unit width, so a bow takes `N = pRb/2` over
  its strip and bends not at all.

On D6's worst span at 20 m/s the two differ by a factor of **670**: 1122 MPa
of bending stress against 1.7 MPa of axial. Against an 800 MPa bar the first
is impossible and the second is nothing. Quoting a single limiting speed
across a gap that wide would be inventing confidence. Closing it is what a
frame solve is for, and it is the next piece of work.

## Before the wind blows, the rod is already loaded

Every bow is bent to the dome radius and **stays bent** for as long as the
dome is up. Glass composite fails under permanent stress at a fraction of its
short-term strength — creep rupture, the governing limit state for this
material and one with no equivalent in steel.

So the first check has no wind in it at all. The reference stock is composite
rebar to **GOST 31938**, at the minimum the standard permits, which allows
**112 MPa allowed permanently** out of an 800 MPa bar. The reference dome M
carries **83 MPa** of that before anything at all happens to it:

| | D3 | D4 | D6 | D8 | D10 | D12 |
|---|---|---|---|---|---|---|
| strain from being bent | **0.267%** | 0.200% | 0.167% | 0.125% | 0.120% | 0.100% |
| stress at E = 50 GPa | **133 MPa** | 100 | 83 | 63 | 60 | 50 |
| against 112 MPa allowed permanently | **1.19** | 0.89 | 0.74 | 0.56 | 0.54 | 0.45 |
| | **fails** | passes | passes | passes | passes | passes |

**The rod is worked hardest on the smallest dome, and this inverts what the
project has been assuming.** Every document here so far treats D12 as the
risky end of the range and D3 as the safe one. On the stress that never comes
off it is the other way round, for a dull reason: rod diameter is quantised at
8, 10 and 12 mm while the radius halves, so `d/2R` is worst where the dome is
smallest.

Read as a bend radius instead, composite rebar at the minimum its standard
permits may be left bent to:

| rod | 8 mm | 10 mm | 12 mm |
|---|---|---|---|
| tightest radius it may be held at | **1.79 m** | 2.23 m | 2.68 m |

D3's radius is 1.5 m. That is the whole of its failure, and the fix is
arithmetic rather than research: **6.7 mm rod, or a bigger dome.**
[Decision 0009](decisions/0009-d3-on-a-skirt-is-dominated.md) already found D3
dominated on floor area. This is a second, independent reason, and a harder
one — the first was about value and this one is about the bar breaking.

## What the wind does

It lifts. It does not push it over, and it does not push it over at any speed:

> Pressure acts normal to the shell. Every normal of a sphere is radial. So
> every facet force passes through the sphere's centre — and for a bare dome
> that centre sits **in the ground plane**. The resultant is a pure force with
> no couple at all.

[`interior.md`](interior.md) ranks the variants on a `tip_index` and says of
it, correctly, that "it is a shape comparison and it proves nothing about
safety". This is the answer it declined to give: **the rigid-body failure mode
is uplift on the ten driven angles, and tipping is not in the running.** A
skirt is what creates a real overturning couple, by lifting the sphere's
centre off the ground — a cost of a skirt that nobody had priced.

And the dome is nowhere near heavy enough to hold itself down:

| at 20 m/s, door shut | D3 | D4 | D6 | D8 | D10 | D12 |
|---|---|---|---|---|---|---|
| lift, N | 873 | 1543 | 3463 | 6136 | 9584 | 13779 |
| what it weighs, N | 128 | 195 | 352 | 528 | 894 | 1161 |
| lift over weight | 6.8 | 7.9 | **9.8** | 11.6 | 10.7 | 11.9 |

A bare M weighs 36 kg and the wind at 20 m/s pulls up 353 kgf. Nothing about
this structure holds it down except the pegs, which is exactly what
[decision 0014](decisions/0014-the-cover-hangs-on-the-stakes.md) assumed when
it hung the cover on them too.

## The limiting wind speed, and what sets it

On composite rebar at the standard's minimum, held at feet and tie marks only:

| | beam | membrane | what binds | on | with all 30 crossings clamped | with the door open |
|---|---|---|---|---|---|---|
| D3 | — | — | *fails bent* | — | — | — |
| D4 | 4.0 | **11.8** | buckling | L4 | 16.6 | 9.1 |
| D6 | 3.5 | **8.2** | buckling | L4 | 11.5 | 6.3 |
| D8 | 2.4 | **4.6** | buckling | L4 | 6.5 | 3.6 |
| D10 | 2.1 | **4.2** | buckling | L4 | 6.0 | 3.3 |
| D12 | 1.3 | **3.0** | buckling | L4 | 4.2 | 2.3 |

Three things to take from it.

**Stability governs, not strength.** Every variant that gets a number at all
is stopped by buckling, not by the bar breaking. A 10 mm rod over D6's worst
unsupported span carries **24.5 N** before it goes — and the rod's own weight
over that span is 4.8 N. [`skirt.md`](skirt.md) noticed the same thing in
passing about a diagonal: "a GFRP rod of the dome's own diameter buckles at
well under a hundred newtons over a chord this long". It is true of the dome
itself.

**The thirty clamps are worth about 1.4× in wind speed.**
[`span.md`](span.md) priced them at 5/3 in span and 2.78× in rod diameter;
this is the same question in the units a field rule is written in, and it is
the first number [milestone 5](roadmap.md) has had in m/s. The gain is capped
because the weak family swaps: with the free crossings clamped, family G's
36° span becomes the worst, and G gains nothing from clamps because all four
of its crossings were already lashed nodes. Exactly as `span.md` predicted,
and the strength module reproduces it from the same spans.

**Shutting the door is worth about 1.3×, and it is free.** An open door facing
the wind lets internal pressure in, which pushes outward everywhere the
outside is already sucking. No part, no plastic, no decision — and it was
never written down.

## What the two bounds are each wrong about

Both ends of the band are known to be wrong, and in known directions. That is
more useful than it sounds, because it says which way the truth lies.

**The beam bound is refuted by the dome standing up.** Under it a D6 bow sags
**80 mm between supports in a dead calm**, under nothing but its own weight —
2.5% of the span. A Star Dome visibly does not do that when you erect one. So
the beam reading is not conservative, it is *wrong*, and the truth lies
towards the membrane end.

**The membrane bound assumes the shell and then denies it.** It gives the bow
the full shell thrust and then buckles it as a pin-ended strut over its whole
unsupported span — as though the ninety rod-on-rod contacts that make it part
of a shell were not there. A curved, laterally restrained member does not
buckle at the straight-strut Euler load. This is the single most conservative
assumption in the calculation and it is the one the frame solve removes.

So the honest reading of the table is: **these are floors, and the real
numbers are above them.** How far above is not something a closed form can
say.

## What this does not do

- **No stock has been measured.** Every value in `materials.toml` is a
  standard's minimum or a typical datasheet figure. A variant that passes here
  passes on any conforming bar, which is the useful direction; a variant that
  fails might still be fine on real stock, and the answer to that is to
  measure a bar rather than to argue. [Milestone 3](roadmap.md) is unchanged.
- **The pressure coefficients are a smooth sealed hemisphere's.** This is a
  lattice of round rods under a flogging membrane with a hole in it. It is the
  largest single uncertainty here by a wide margin, and no amount of precision
  downstream of it is worth anything.
- **The anchors share equally, which they do not.** The windward feet stand in
  positive pressure and are pushed down; the side and lee feet are pulled up.
  The worst foot sees more than the average, and how much more is a question
  about how the lattice distributes load.
- **No connector is checked.** `TERM`'s 5 mm wall, `SPLICE`'s sleeve in
  bending, the fan node's plates, the base hub — none of them. Joint forces
  are what a frame solve produces and a closed form cannot.
- **The pull-out capacity of a driven angle is a placeholder**, and
  `STAKE-BASE` has not even been chosen. That number is a soil question and
  this repository has no soil in it.
- **Snow is out of scope by operating rule.** The dome comes down before
  winter. If one is ever left up, nothing here covers it, and the margin is
  not close: 1.8 kPa of snow on a 6 m dome is 51 kN, against the 300 Pa this
  document is about.
- **Nothing here says how it fails.** Glass composite is brittle: no yield, no
  warning, no redistribution. A utilisation of 1.0 is not a safe design point
  for this material with people underneath, and the partial factor that
  reflects that judgement is an input in `materials.toml`, not a result.
