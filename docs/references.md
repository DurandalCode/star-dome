# References

## Star Dome

Primary reference:
- SimplyDifferently — Star Dome: https://simplydifferently.org/Star_Dome?page=0

Use this as geometric/construction inspiration, not as proof that scaled-up variants are structurally safe.

Source images used to check the reconstruction (full-size versions live under
`/Present/` on that site; the pages themselves show reduced copies):

- Construction diagram, the four numbered panels:
  https://simplydifferently.org/Present/StarDome/stardome-structure.png
- Step 5 detail:
  https://simplydifferently.org/Present/StarDome/stardome-compose.png
- Bamboo stick model, showing how junctions are actually tied:
  https://simplydifferently.org/Present/Pics/2006.StarDome/img_0022.jpg

## What the reference says about the cover

Checked against the source rather than assumed, because the first guess here
was wrong. The reference gives **two** cover patterns and prefers the second.

**Faceted: 6 pentagons and 10 triangles, all of side `s`.** That is exactly
half an icosidodecahedron -- the solid whose equatorial decagons *are* the G
family bows -- so `s` is the model's own `base_edge_chord`, which comes out at
`R / phi` exactly. Every panel is flat, so it develops with no distortion at
all. The reference discourages it for weather:

> "I personally would only consider this cover pattern for interior use or
> sun shade application, but not for serious outdoor (rain cover)
> application, it's just too complicate and too many parts and seams to sew
> leak-free."

**Leaves: 5 or 10 of them, pieced from horizontal lanes.** The preferred
pattern. Each leaf is a gore spanning 72 or 36 degrees of azimuth, and
because a leaf is far wider than any roll, it is built up from **horizontal
canvas lanes of width `wcanvas` laid overlapping** -- shingled, upper over
lower, so rain sheds down the slope without the joint having to be
watertight. One larger triangle at the base is the entry.

> "choose 5 or 10 leafs, and have one larger triangle at the base be the
> entry"

Sizing, from the originator: **"Daisuke Takekawa ... recommends to make it
10% larger in case you plan to cover it over the construction."**

Seaming: "flat felled seam", or overlay, or interlocked; sewn part by part in
sequence; and "consider to seal the stitching holes from sewing with silicon
or good clear tape for canvas". No seam allowance figures are given.

## Resolved

- **Exact geometric construction of the 15-member reference dome.** Reconstructed
  from the reference's bow-length formula and rod-marking diagram, and
  implemented in `dome/`. Derivation and the assumptions it rests on are in
  [`dome/README.md`](../dome/README.md).
- **Explicit construction points or derived spherical curves?** Derived spherical
  curves. Every bow is a great semicircle joining two diametrically opposite base
  points, which is what the reference's `lbow = c/2` requires. No coordinate in
  the model is hand-placed.
- **Do four rods really meet at a lashed junction?** Yes. Checked against the
  reference's own construction diagram, `stardome-structure.png`. Panel 1 draws
  the pentagram of 5 blue bows and rings 5 junctions, each with **two** blue
  bows crossing. Panel 2 adds the 5 green bows, and the same 5 rings now carry
  **two blue plus two green**. That is the reconstruction in
  [`dome/README.md`](../dome/README.md) confirmed from the source, not inferred.
  See [`tied-node.md`](tied-node.md).

## Questions to resolve

- Rod/tube material properties for candidate fiberglass products.
- Practical minimum bend radius and transport format.
- Cover attachment and load distribution.
- Wind and anchoring limits for each size.
- Entrance/corridor modifications that do not compromise the primary load paths.
