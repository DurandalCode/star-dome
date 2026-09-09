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
