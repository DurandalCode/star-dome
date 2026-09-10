# Transport length, and the joint that follows from it

Two decisions are recorded here. The first is computed, the second is taken.

## The section length

A bow is a semicircle of the dome's radius — 9.4 m on M, 18.8 m on D12 — and
nothing carries that, so it travels in sections and is spliced on site. How
long a section may be is a decision about the vehicle, and it decides how many
splices the dome has.

Sections are **equal** and their count is **divisible by neither 3 nor 5**.
That is not a preference: the U and L bows are marked in thirds and G in
fifths, the crossings sit on those marks, and an even division into 3, 5, 6, 9,
10 or 12 puts joints dead on them. See [`splice.md`](splice.md).

Clean is not the same as clear, though — eight sections on D12 miss the marks
by 0.26°, which on a six metre radius is 27 mm and nowhere near enough for a
ferrule and a connector side by side. Both tests have to pass.

| limit | D3 | S D4 | M D6 | L D8 | XL D10 | D12 | splices |
|---|---|---|---|---|---|---|---|
| 2.0 m | 4×1178 | 4×1571 | 7×1346 | 7×1795 | **none** | 23×820 | — |
| 2.5 m | 2×2356 | 4×1571 | 4×2356 | 7×1795 | 7×2244 | 23×820 | — |
| 3.0 m | 2×2356 | 4×1571 | 4×2356 | 7×1795 | 7×2244 | 7×2693 | 375 |
| **3.5 m** | 2×2356 | **2×3142** | 4×2356 | **4×3142** | 7×2244 | 7×2693 | **300** |
| 4.0 m | 2×2356 | 2×3142 | 4×2356 | 4×3142 | 4×3927 | 7×2693 | 255 |

**3.5 m is the answer.** Everything divides equally, one cut list per dome, and
S and L both drop to their two- and four-section form. 300 splices across the
whole family.

**3.0 m is the floor** for equal sections. It costs 75 more splices — S goes
4×1571 instead of 2×3142, L goes 7×1795 instead of 4×3142 — and buys 500 mm
of vehicle.

**Below 3.0 m the equal division breaks.** D12 falls off a cliff to 23 sections
of 820 mm and D10 has no answer at all at 2.0 m. Sections can still be placed,
but only **unequally**: `splice.place_splices` puts each joint in a gap between
crossings and reaches the theoretical minimum count — D12 in 8 sections at
2.5 m — at the price of unequal pieces and a separate cut list for G against
U and L.

**4.0 m buys almost nothing** over 3.5: only D10 improves, 7 sections to 4.

### Lengths that more than one dome shares

The family falls into two chains by radius, and within a chain the same
section serves several domes:

    2356 mm   D3 (2), M D6 (4), D12 (8)      radii 1500 / 3000 / 6000
    3142 mm   S D4 (2), L D8 (4)             radii 2000 / 4000
    1571 mm   S D4 (4), L D8 (8)
    1178 mm   D3 (4), M D6 (8), D12 (16)

XL D10 shares with nobody: 5000 is not a power of two away from any other
radius in the set, so no clean count lands it on a shared length. It sits at
2244 mm on its own.

At the recommended 3.5 m that gives **four distinct section lengths for six
domes** — 2356, 3142, 2244, 2693.

## The joint

**Decided, not computed: steel, male–female, with a threaded stud.** One
section end carries a male spigot, the other a female socket, and a stud pulls
them together. Field-serviceable with a spanner, no adhesive on site, and the
same part at every joint.

The one thing already computed that bears on it: **steel at the thinnest wall
anyone will sell is about 4.5× the rod's bending stiffness**, so the joint is a
harder spot than the rod around it and the bow will take a little extra
curvature just outside each ferrule. A male–female joint mitigates that where a
plain sleeve cannot, because its stiffness is set by how far the spigot
reaches rather than by a wall thickness that has a manufacturing floor — make
the engagement longer and gentler rather than the wall thicker. That is a
design lever, and it is the one to use.

What is still open, and is not a calculation:

- the engagement length, which trades the hard spot against the part's own size;
- whether the steel is bonded into the GFRP or pinned through it;
- the stud's thread and whether it is captive;
- corrosion between steel and a wet composite;
- and creep, temperature and UV, which is why the printed alternative was left
  on the table rather than adopted.

See [`splice.md`](splice.md) for the material comparison this decision
overrides, and roadmap milestone 5.
