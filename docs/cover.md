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
