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

- **How the reference cuts the cover.** Two ways, and it gives both: a patchwork
  of **6 pentagons and 10 triangles, all of side `s`** — which is the
  icosidodecahedron hemisphere, and which this project's own geometry contains
  exactly (20 vertices, 35 edges of `R/phi`, 25 of them on the G bows) — or "a
  leaf-like cover, e.g. choose 5 or 10 leafs, and have one larger triangle at
  the base be the entry", which is the gore cut. Takekawa also recommends
  making the cover **10% larger** if it goes over the construction. Both are
  computed and compared in [`cover.md`](cover.md).

## Questions to resolve

- Rod/tube material properties for candidate fiberglass products. **Answered
  from standards, not from tests** — `configs/materials.toml` and
  [`strength.md`](strength.md). Still open as a measurement: nobody has put a
  caliper or a test rig on a real coil.
- Practical minimum bend radius and transport format. **Answered for the
  sustained case**: composite rebar to GOST 31938 minima may be left bent at
  1.79 m on 8 mm rod, 2.23 m on 10 and 2.68 m on 12. That is the check D3
  fails. A *transport* bend radius is a different and much easier number — the
  coil itself winds at 1.2 m diameter.
- Cover attachment and load distribution. Loads yes, attachment no: the bolt
  rope, the hem and the five crown straps of `attachment.py` still carry no
  check of their own.
- Wind and anchoring limits for each size. **A band per size, not a limit** —
  [decision 0023](decisions/0023-the-strength-answer-is-a-band-until-the-frame-is-solved.md).
  And anchoring is now the governing question rather than a footnote: a bare
  dome lifts rather than tips, and `STAKE-BASE` has still not been chosen.
- Entrance/corridor modifications that do not compromise the primary load paths.

## Standards referenced

Cited in `configs/materials.toml` and `configs/loads.toml` against the numbers
they supply, rather than listed here and forgotten:

- **ГОСТ 31938-2012** — composite polymer reinforcement, table 1: the tensile,
  compressive and shear minima for glass composite (АКС), and the 50 GPa
  modulus floor.
- **ACI 440.1R-15** — the environmental reduction for GFRP exposed to earth
  and weather, and the creep-rupture stress limit that makes a permanently
  bent bow a different check from a gust.
- **EN 1991-1-4**, figure 7.12 — external pressure coefficients for a dome on
  a circular base, read at rise over span of 0.5, and section 7.2.9 for the
  dominant-opening internal coefficient.

None of the three is a code for this structure. There is no design code for a
temporary bent-rod lattice, so these are the nearest published figures and the
partial factor that bridges the gap is a judgement in `materials.toml`.
