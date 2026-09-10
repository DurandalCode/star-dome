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

**Decided, not computed: a steel sleeve, the rods butting inside it, one cross
fastener each side.** A length of drawn tube, cut to length — one part per
joint and nothing to machine. Field-serviceable with a spanner, no adhesive on
site, and the same part at every joint.

The one thing already computed that bears on it: **steel at the thinnest wall
anyone will sell is about 4.5× the rod's bending stiffness** on M, so the joint
is a harder spot than the rod around it and the bow takes a little extra
curvature just outside each sleeve.

An earlier version of this page said a male–female joint with a threaded stud
mitigated that where a plain sleeve could not, because its stiffness would be
set by how far the spigot reached rather than by a wall with a manufacturing
floor. **That was wrong.** The rod is solid, so nothing goes inside it: both
designs wrap the rod in a tube, and the wall of that tube sets the stiffness
either way. The thread did not replace the wall — it made the wall thicker,
2 mm instead of 0.8, which is 15.6× instead of 4.5×. The lever was real but it
pointed the other way, and 4.5× is now the whole joint rather than its softest
point. See [`splice.md`](splice.md).

The engagement is the lever that is actually left: 6 rod diameters each side,
120 mm overall on M, against 379 mm of free span between crossings.

What is still open, and is not a calculation:

- whether 6d of engagement is the right trade of hard spot against part length;
- whether the cross fastener is a bolt or a spring pin, and what its hole
  costs the rod — it takes 40% of the rod's width at that section;
- corrosion between steel and a wet composite;
- and creep, temperature and UV, which is why the printed alternative was left
  on the table rather than adopted.

See [`splice.md`](splice.md) for the material comparison this decision
overrides, and roadmap milestone 5.
