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
