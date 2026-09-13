# The fabric cover

```bash
python3 -m stardome cover D6
make covers ROLL=1500
```

The cover is not a design decision. The rods are already a sphere, so the
fabric is a sphere, and everything below follows from which sphere.

## It is not the nominal sphere

The fabric rides on the **outermost rod surface**, not on the nominal
centreline sphere. A four-rod stack is three diameters tall, so the rod on the
outside of it sits 1.5 diameters off its great circle, and the fabric clears
that rod's surface half a diameter further out again: **r + 2d**.

| | D6 |
|---|---|
| nominal radius | 3000 mm |
| cover radius | 3020 mm |
| more radius | +0.7% |
| **more fabric** | **+1.3%** |

The model carries this as `meta.max_diameter_woven`, and it is the same figure
whatever weave mode was asked for — how the model is *drawn* must not change
how much fabric gets cut.

**Two conventions were wrong here in turn, and the second was worse.** Reading
a flat model put the fabric on the nominal sphere, 15 mm under the outermost
rod. Reading a `layered` one — which is what this document used to quote — put
it on r = 3075, **55 mm over**: `layered` gives each of the 15 bows its own
shell and spreads them across fourteen rod diameters, and the dome is built on
a weave that spans three. That is 3.7% too much fabric on M, cut into a cover
that then has 3.7% too much of itself to flog in the wind. A cover can be too
big as easily as too small, and only one of those is obvious on site.

`test_the_cover_radius_is_the_weave_and_not_a_drawing_convention` checks the
closed form against the route `weave.global_profile` actually solves.

## Three ways to cut it

The dome can be cut like a sphere, like itself, or for a budget, and the three
are genuinely different answers rather than a matter of taste.

**Gores** are meridian strips, the answer for any sphere: one shape, the
fewest pieces, and the fewest seams at every roll width. They are what
`gores()` computes and what this document described on its own for a long
time.

**Leaves** are the answer when the fabric bill is what hurts. See
[below](#the-leaf-buys-the-fabric-back) — the short version is that a leaf is a
gore that has stopped trying to cross the roll in one piece, and stops paying
the `2/pi` tax for it.

**Faces** are the answer for this dome, which is not a sphere with a lattice
drawn on it. Its ten feet and its ten lashed nodes are the twenty vertices of
an **icosidodecahedron hemisphere** — edge `R/phi`, which is the base chord,
1854.1 mm on M — and its faces are **six pentagons and ten triangles with
every edge the same length**. That is the cut the reference gives, and it took
going back to the source to find it.

| roll | gores | faces |
|---|---|---|
| 1500 mm | 13 pieces, 61.7 m | 32 pieces, 77.1 m |
| 2000 mm | 10 pieces, 47.4 m | 22 pieces, 63.2 m |
| 3200 mm | 6 pieces, 28.5 m | 16 pieces, 46.4 m |

**Gores always beat faces on seam length, at every roll**, and the arithmetic
invites the opposite conclusion so it is worth saying plainly. A face is small and
fixed, so a wider roll only saves its internal cuts; a gore is as wide as the
roll allows, so a wider roll deletes whole gores and whole seams with them.
`test_the_roll_decides_which_cut_is_cheaper` asserts the direction.

### What the faces buy instead

- **25 of the 35 edges lie along the G bows.** The other ten are the base
  ring, where there is no rod and no second panel — that edge is the hem. So a
  seam is not merely a join in cloth: it lands on a member, and the cover can
  be held along it rather than only at its edge.
- **Panel corners land on connectors that already exist** — the base hub and
  the four-rod fan, the two strongest points in the structure.
- **Every edge is the same length.** One number for the whole cover, against a
  gore whose every section is a different width.
- **The crown is a pentagon.** Gores bring all 13 seams to a point at the
  pole, which is not sewable and wants a crown patch; the face cut has no such
  place.

### What they cost, on the 1500 mm roll anybody buys

A pentagon's narrowest way across is **2853 mm** — across the flats, not the
3154 mm of its long diagonal, and getting that wrong makes the face cut look
absurd rather than merely dearer. So on a 1500 mm roll a pentagon is two
strips and one internal seam of 2.8 m, a triangle two strips and 1.4 m, and
the total comes to 32 pieces against 13, and 77.1 m of seam against 61.7.

Those internal seams land on nothing. They are the price of a narrow roll, and
they disappear entirely at 3200.

**Flat faces are not a sphere.** Six pentagons and ten triangles come to
50.4 m² flat against the shell's 57.3 m², so a panel wants easing onto the
curve — the reference says make it 10% larger — and none of that is in these
numbers.

## The leaf buys the fabric back

Both cuts above are billed by the roll, and a gore is expensive there for a
reason that no amount of cleverness removes: **a gore fills exactly `2/pi` —
63.66% — of its own bounding rectangle**, at any radius and at any count. The
taper is waste, and nesting cannot recover it, because at the equator the gore
is already the full strip width and a flipped neighbour has nowhere to go.
`test_a_gore_fills_two_over_pi_of_its_rectangle` pins it.

A **leaf** stops paying that. It is a gore that has given up crossing the roll
in one piece: one fifth of the dome's azimuth, far wider than any roll, built
from horizontal lanes laid overlapping, upper over lower. The lane is cut with
its **height across the roll and its width along it**, so the roll no longer
caps anything, and because the lanes are near-trapezoids, turning every other
one end for end lets two share a rectangle — a lane then costs its *mean*
width instead of its widest.

On M, five leaves of four lanes, lapped 80 mm:

| | pieces | seam | lap | roll |
|---|---|---|---|---|
| gores | 13 | 61.7 m | — | **61.7 m** |
| leaf ×5 | 20 | 23.7 m | 38.8 m | **47.8 m** |

**Around a quarter of the fabric, at every size in the family** — 17% on S,
31% on XL. The horizontal joints are **laps, not seams**: upper over lower
sheds water down the slope without the joint having to be watertight, which is
the reference's own reason for cutting it this way for rain. The vertical
seams run down the slope too, where the water is already going.

What it costs is joining, and **whether that is a cost at all depends on the
size**. A gore's seam count is set by the roll, so it grows with the dome —
7 on D3, 26 on D12 — while the leaf keeps five vertical seams however big the
dome gets and only its laps grow:

| | D3 | S | M | L | XL | D12 |
|---|---|---|---|---|---|---|
| gore seam | 16.7 | 28.5 | 61.7 | 107.3 | 173.6 | 246.0 |
| leaf seam + lap | 18.8 | 33.5 | 62.5 | 99.5 | 144.5 | 197.5 |
| roll saved | 31% | 17% | 23% | 26% | 31% | 32% |

So below M the leaf trades a little extra joining for the cloth; **from L up
it is simply cheaper on both at once**, and by D12 it saves 78 m of fabric and
48 m of joining together. That reversal is the one figure here that changes
direction across the family, so
`test_whether_the_laps_are_worth_it_depends_on_the_size` asserts it rather
than leaving it to this table to be right.

Two smaller things fall out. The lane rarely fills the roll exactly — 254 mm
is left over on M — and that is a **continuous strip down the whole run**,
which is where patches and the entry triangle come from. And more leaves do
not cost more fabric: ten leaves are each half as wide, so the roll is
untouched and only the seam count doubles.

## How much there is

| variant | dome | skirt | doorway | total | gores |
|---|---|---|---|---|---|
| D3 + 1000 skirt | 14.44 | 9.53 | — | 23.97 | 7 |
| D4 + 1350 skirt | 25.54 | 17.10 | 1.15 | 41.48 | 9 |
| D6 bare | 57.31 | — | 2.59 | 54.71 | 13 |
| D8 bare | 101.54 | — | 4.62 | 96.92 | 17 |
| D10 bare | 158.59 | — | 7.21 | 151.38 | 22 |
| D12 bare | 228.01 | — | 10.39 | 217.62 | 26 |

All m², gores on a 1500 mm roll. The dome is a hemisphere zone, `2*pi*R^2`;
the skirt is a cylinder under it; the doorway is cut out and is also the piece
the door panel is made from.

Note what the last column does. Fabric goes up with `R^2` and seams go up with
`R` — D12 needs 4x D6's fabric but only twice its seams. The cover is the one
part of this dome that gets *easier* per square metre as it grows.

## How it is cut

A sphere is not developable, so the cover is sewn from **gores** — tapered
strips between two meridians. At the equator the gores share the whole
circumference between them, so each is `2*pi*R/n` across, and that is what has
to cross the roll of fabric being cut from:

    gore length          pi * R / 2
    gore half width      pi * R * sin(theta) / n      at polar angle theta
    gore full width      2 * pi * R / n               at the equator

D6 on a 1500 mm roll: **13 gores of 1486 × 4830 mm, 62.8 m of seam.**

The roll width is an input, not a fact about the world — pass `--roll` for
what the supplier actually sells. Fewer gores means fewer seams and less
labour, so the answer wanted is always the smallest `n` that fits.

`cover.gore_outline(data, count)` gives one gore as a flat pattern:
`(along, half_width)` from the pole, ready to mark out.

## What this does not do

- **No sag.** The fabric is taken as lying on the sphere. Real fabric dips
  between the rods and picks up a little area doing it, so these are the
  optimistic figures.
- **No seam allowance, no hem, no base overlap.** Cutting-room numbers, and
  they depend on the machine and the material.
- **No load, no wind, no attachment.** Cover attachment is milestone 5;
  pressure and anchoring are milestone 8. Nothing here is a structural claim.
- The exported mesh is a closed surface. The doorway is **not** cut out of it
  — `doorway.outline` is drawn over it instead.

## In the scene

`make blender` builds the model with `--polylines`, which carries the cover
mesh, and `--cover` draws it translucent so the structure still reads through
it. See [`architecture.md`](architecture.md).
