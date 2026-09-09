# The four-rod node

The ten lashed nodes are where the Star Dome actually needs a connector. They
looked like the hard case: four rods meeting at one point with six pairwise
angles between them, and a two-piece two-rod clamp cannot serve that.

They are not the hard case. This document records why, and the one build
decision the analysis leaves open — now taken.

Everything here is computed, not asserted:

```bash
python3 -m stardome weave D6
```

## 1. The four rods are coplanar

Every bow is a great circle, and a great circle's tangent at a point lies in
the sphere's tangent plane at that point. All four rods therefore leave the
node in **one plane**, perpendicular to the radius.

The model confirms it: the largest out-of-plane component of any tangent at
any lashed node, in any variant, is around `3e-16` — zero to machine
precision. `tests/test_weave.py::test_all_four_tangents_are_coplanar` holds it
there.

This changes the part completely. The node is not a three-dimensional tangle;
it is a **flat four-armed fan**, with the rods stacked along the radius across
that plane.

## 2. One fan serves all ten nodes

Read the fan round from either side and the gaps between angular neighbours
are always:

```
37.3774°   41.8103°   37.3774°   63.4349°        (sum: 180°)
```

The five high nodes read **G-U-U-G** around the fan and the five low ones read
**L-G-G-L**, so the families swap roles. As geometry the two are the same
cyclic sequence, which means the same part fits all ten. Congruence is decided
by comparing canonical gap sequences up to rotation and reflection, not by
comparing pairwise angles — a set of four lines is not determined by its
pairwise angles alone.

Together with the two-rod result, this settles the connector count for the
baseline dome:

| part | count | geometry |
|---|---|---|
| four-rod fan | 10 | planar, gaps 37.3774 / 41.8103 / 37.3774 / 63.4349 |
| two-rod clamp | 30 | 70.5288° = `acos(1/3)`, and optional — the reference does not lash these |

**Two connector geometries for the whole dome**, not the twelve its symmetry
classes might suggest.

## 3. The stacking order

Four rods cannot share a point, so they stack along the radius. Only rods
**adjacent in the stack** touch, so choosing the order is choosing which three
of the fan's angles become rod-on-rod contacts.

Numbering the fan 1-2-3-4 in angular order, the contact angles available are:

| pair | angle | families (high / low) |
|---|---|---|
| 1-2 | 37.3774 | G-U / L-G |
| 1-3 | 79.1877 | G-U / L-G |
| 1-4 | 63.4349 | G-G / L-L |
| 2-3 | 41.8103 | U-U / G-G |
| 2-4 | 79.1877 | U-G / G-L |
| 3-4 | 37.3774 | U-G / G-L |

The twelve distinct orders (reversals collapsed — turning the stack inside out
gives the same contacts) and their consequences are enumerated by
`stardome.weave.stacking_options`. The serious candidates:

| order | contacts | distinct | note |
|---|---|---|---|
| **1-2-3-4** | **37.3774 / 41.8103 / 37.3774** | 2 | the three shallowest angles the fan offers |
| 2-1-4-3 | 37.3774 / 63.4349 / 37.3774 | 2 | |
| 1-4-2-3 | 63.4349 / 79.1877 / 41.8103 | 3 | keeps family G innermost |

### Decision: fan order, 1-2-3-4

Each rod lies immediately outside its angular neighbour. Chosen because:

- **Shallowest contacts.** Crossed cylinders bear over a longer effective
  length the closer they are to parallel. `docs/crossing-clamp-v1.md` already
  flags rod-on-rod contact on fibreglass as the first thing to check on a
  printed prototype, so this is not a theoretical preference.
- **Two distinct saddle angles, not three.**
- **The stack is palindromic** — it reads the same from inside or outside.
- **One sentence in the field:** stack them in the order they fan out.

Stack height is three rod diameters: 30 mm at D6.

### The cost, quantified

Under fan order a rod does not keep the same level everywhere. Family G rods
take all four levels across the four nodes they pass; family L rods take the
two outer ones; family U rods stay in the middle two.

That was the one worry, and measuring it settles it. Three levels is three rod
diameters — 30 mm — spread over the arc between two tie marks, about 1.9 m at
D6. The worst slope is **1.6%**, on a rod already bent to a 3000 mm radius.
Not a constraint.

`stardome.weave.migration` reports it per rod;
`tests/test_weave.py::test_radial_migration_is_negligible` keeps it under 2%.

## 4. Does the weave close globally?

Fixing the stack at the ten lashed nodes says nothing about the thirty
unlashed crossings a rod passes on its way between them. Those rods must also
not share space: their axes need at least one rod diameter of separation.

```bash
python3 -m stardome weave D6
```

### The obvious guess fails

Route each rod straight between the offsets its lashed nodes dictate, and
**15 of the 30 unlashed crossings interpenetrate**. The worst leaves 1.12 mm
between the axes of two 10 mm rods — an 8.9 mm overlap. Every stacking order
fails this way; fan order is simply the worst of them, at 15 collisions
against 5 for the best.

That result is kept as `weave.linear_profile_violations` and a test, because
it is the reason the solver below has to exist. It is not an argument against
fan order: linear interpolation was an arbitrary guess at the route, not a
constraint of the design.

### A consistent weave does exist

`weave.global_profile` holds the lashed-node offsets fixed, lets the rod float
between them, and relaxes until every crossing clears. It converges, for every
stacking order, and the answer is better than it had to be:

| variant | rod | radial band | worst slope | tightest separation |
|---|---|---|---|---|
| D4 | 8 mm | ±12 mm | 2.06% (1.18°) | 8.0000 mm |
| D6 | 10 mm | ±15 mm | 1.72% (0.98°) | 10.0000 mm |
| D8 | 10 mm | ±15 mm | 1.29% (0.74°) | 10.0000 mm |
| D12 | 12 mm | ±18 mm | 1.03% (0.59°) | 12.0000 mm |

Two things matter here:

- **The band is exactly the stack's own half-height**, 1.5 rod diameters. The
  weave asks for no radial room beyond what four stacked rods already occupy.
  There is no hidden thickness to design around.
- **The route is gentle.** A rod leaves its great circle by about one degree.
  It also means the weave gets *easier* as the dome grows — the arc between
  nodes grows faster than the rod does — so **D4 is the tight case**, not D12.

### What this means for the part

The rod does not arrive at a lashed node parallel to the sphere: it comes in
at up to about 1.2° of radial tilt, and generally at a different tilt on each
side. A channel bored exactly tangent will pre-stress the rod. Flared mouths
already help; whether the fan needs an explicit tilt allowance is a question
for the printed prototype.

## 5. Checked against the reference

The four-rod node was a reconstruction, and the roadmap held it as something to
confirm before spending effort on tooling. It is confirmed, from the
reference's own construction diagram rather than from a photograph:

- **Panel 1** draws the pentagram of 5 blue bows and rings 5 junctions. Two
  blue bows cross at each ring.
- **Panel 2** adds the 5 green bows. The same 5 rings now carry **two blue plus
  two green** — four rods, in exactly the two-of-one-family, two-of-another
  pattern this model predicts.

The reference's own text does not state a number; it says only that the count
"varies by location", which is why the diagram is the evidence.

### But the reference does not build them as one joint

The bamboo model photograph shows how those junctions are actually made:
**pairwise cable ties, two or three of them clustered over a short span along
the rods**, not one bundle of four. The rods are visibly not concurrent — they
pass a few rod-widths apart.

That is worth stating plainly, because it makes the fan part a **departure from
the reference's practice, not a reproduction of it**. A rigid four-rod part
forces exact concurrency where the original tolerates a spread. Two
consequences for the design:

- The fan should tolerate the rods arriving slightly off the ideal point —
  slots and flared mouths rather than exact bores, on top of the ~1.2° radial
  tilt allowance from the weave analysis.
- A legitimate alternative is not to make a four-rod part at all, but a short
  stack of two-rod clamps, which is closer to what the reference does. That
  keeps one part family instead of two, at the cost of more pieces per node.

The same photograph shows ties at many more crossings than the ten marked ones,
so the original builder did tie two-rod crossings as well. That is evidence
against dropping the 30 unlashed clamps entirely on the reference's authority —
it should be settled on a D4 prototype instead.

## 6. What is still open

- ~~The part itself.~~ Built: `connectors/fan_node_v1.py`, driven from the
  model by `connectors/generate_clamps.py`. See
  [`fan-node-v1.md`](fan-node-v1.md) for the architecture, the numbers, and
  what is still crude about it.
- **Fan part or a stack of two-rod clamps.** Still open. The reference does the
  latter, and it would keep a single part family. V1 of the fan exists so the
  two can be compared on real numbers rather than argued about.
- **Near-crossing interference.** The check is axis separation *at* the
  crossing point. Two rods meeting at the fan's shallowest angle, 37.4°, stay
  close for some distance either side of it; whether finite-diameter rods
  clear each other over that whole region is not modelled.
