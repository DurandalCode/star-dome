# The fabric cover

```bash
python3 -m stardome cover D6
make covers ROLL=1500
```

The cover is not a design decision. The rods are already a sphere, so the
fabric is a sphere, and everything below follows from which sphere.

## It is not the nominal sphere

The fabric rides on the **outermost rod surface**, not on the nominal
centreline sphere. In the layered weave a bow leaves its great circle by up to
a rod diameter and a half, and the cover goes over whichever rod ends up
furthest out.

| | D6 |
|---|---|
| nominal radius | 3000 mm |
| cover radius | 3075 mm |
| more radius | +2.5% |
| **more fabric** | **+5.1%** |

Three square metres on a sixty square metre cover — and 5.1% more sail area to
hold down, which is the part that matters later.

The model carries this as `meta.max_diameter_woven`, computed from the layered
offsets **whatever weave mode was asked for**. The weave is a fact about the
built dome; `flat` and `layered` are drawing conventions. Reading
`max_diameter_incl_rod` from a flat-mode model understates every cover in the
family, and `test_the_cover_radius_ignores_the_drawing_convention` exists to
stop that coming back.

## How much there is

| variant | dome | skirt | doorway | total | gores |
|---|---|---|---|---|---|
| D3 + 1000 skirt | 15.29 | 9.80 | — | 25.09 | 7 |
| D4 + 1350 skirt | 26.66 | 17.47 | 1.15 | 42.98 | 9 |
| D6 bare | 59.41 | — | 2.59 | 56.82 | 13 |
| D8 bare | 104.34 | — | 4.62 | 99.72 | 18 |
| D10 bare | 162.79 | — | 7.21 | 155.57 | 22 |
| D12 bare | 233.03 | — | 10.39 | 222.64 | 26 |

All m², gores on a 1500 mm roll. The dome is a hemisphere zone, `2*pi*R^2`;
the skirt is a cylinder under it; the doorway is cut out and is also the piece
the door panel is made from.

Note what the last column does. Fabric goes up with `R^2` and seams go up with
`R` — D12 needs 4x D6's fabric but only twice its seams. The cover is the one
part of this dome that gets *easier* per square metre as it grows.

## How it is cut

Three patterns, two of them from the reference. Checked against the source
rather than assumed, because the first guess here was the wrong one. See
[`references.md`](references.md) for the quotes.

```bash
python3 -m stardome cover D6 --patterns --price 450
```

D6, 1500 mm roll, +10% oversize (Takekawa's own figure):

| | pieces | area m² | roll m | floor | seam m |
|---|---|---|---|---|---|
| faceted | 16 | 60.95 | — | 40.6 | 51.0 |
| leaf ×10 | 40 | 71.89 | 55.8 | 47.9 | 53.1 |
| **leaf ×5** | **20** | 71.89 | **55.8** | 47.9 | **26.6** |
| gore | 15 | 71.89 | 79.7 | 47.9 | 79.7 |

*floor* is area ÷ roll width: the roll you would buy if fabric came in the
shape you wanted.

### Every size, one line

```bash
python3 -m stardome cover S M L XL --summary --roll 1500 --price 450
```

| size | across | area m² | bought | pieces | roll m | seam m | cost | vs gore |
|---|---|---|---|---|---|---|---|---|
| S D4 | 4 m + 1.35 | 32.26 | 39.9 | 15 | 26.6 | 17.8 | 11 970 | +4 050 |
| M D6 | 6 m | 71.89 | 80.2 | 20 | 53.5 | 26.6 | 24 075 | +11 790 |
| L D8 | 8 m | 126.25 | 133.5 | 25 | 89.0 | 35.2 | 40 050 | +20 160 |
| XL D10 | 10 m | 196.97 | 234.5 | 35 | 156.3 | 44.0 | 70 335 | +24 660 |

*bought* is roll metres × roll width: the fabric you pay for, waste included.
*vs gore* is what the one-piece pattern would add. The price per metre is
yours — pass whatever the supplier quotes.

**Running metres compare only within one roll width.** A 3 m roll is not the
same price per metre as a 1.5 m one, so to compare widths, price the *bought
area* instead. Same cover on M: 83.2 m² bought on a 1 m roll, 80.2 on 1.5 m,
80.7 on 3 m — the width barely moves the fabric, it moves the handling.

Most of the waste is one continuous strip down the run, where the lane is
shorter than the roll is wide: 260 mm on S, 112 on M, 28 on L, 175 on XL. The
entry triangle and every patch come out of it.

### Faceted — 6 pentagons and 10 triangles

Half an icosidodecahedron, the solid whose equatorial decagons **are** the G
family bows. So the panel side is the model's own `base_edge_chord`, which is
`R / φ` exactly — no new constant anywhere.

Every panel is flat, so it develops with no distortion at all, and it wraps
less fabric than the others because it is the *inscribed* polyhedron: a
different surface, not a like-for-like saving.

The reference does not recommend it for weather — "too many parts and seams
to sew leak-free" — and a narrow roll takes away its other advantage too: a
D6 pentagon is 3300 mm across, so on 1500 mm fabric each one has to be pieced
from three strips before you even start.

### Leaf — the reference's choice, and the numbers agree

5 or 10 leaves, each a gore spanning 72° or 36°. A leaf is far wider than any
roll, so it is built from **horizontal lanes laid overlapping** — shingled,
upper over lower — and rain sheds down the slope without the joint having to
be watertight. One larger triangle at the base is the entry.

Two things make it win:

- **The lanes nest.** Each is very nearly a trapezoid; turn every other one
  end for end and two share a rectangle, so each costs its *mean* width
  instead of its widest. That is 55.8 m of roll against 66.9 unnested.
- **Five leaves, not ten.** Same fabric, half the seams, half the pieces. Ten
  only buys easier handling — a 3.9 m lane is a lot of cloth to move.

Against one-piece gores that is **30% less roll and a third of the seam**, and
the gap widens with size: on D10 it is 167 m against 211, and 44 m of seam
against 211.

### Gore — one piece each, and the price of it

No horizontal joints at all, which is the clean-looking option. It costs:

> **A gore fills exactly 2/π = 63.66% of its own bounding rectangle** — at any
> radius, for any gore count.

And no nesting recovers it. At the equator a gore is already the full width of
its strip, so a flipped neighbour has nowhere to go; the nesting pitch comes
out at exactly one gore length. Raising the count does not help either — it
only leaves more of the roll's width unused, so the roll fill *falls*.

`cover.gore_outline(data, count)` still gives one gore as a flat pattern:
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
