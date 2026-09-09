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

## 4. What is still open

- **The part itself.** The schedule now carries the fan as a specified part
  with `generator: null`. Nothing builds it yet.
- **Global weave consistency.** The local geometry at each node is settled.
  Whether one consistent over/under assignment exists across all 90 contacts
  at once — including the 30 unlashed crossings a rod passes on its way
  between nodes — is a separate computation that has not been done.
- **Whether the reference really has four rods per node.** This is a
  reconstruction from the rod marking diagram, not a quoted fact. Verify
  against photographs or a physical mock-up before committing to tooling.
