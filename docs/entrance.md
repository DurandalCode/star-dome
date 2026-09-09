# Entrances

The Star Dome has no door. It has fifteen rods and whatever gaps they leave, and
an entrance has to live in one of those gaps without cutting a member. This is
that question answered by measurement.

```bash
python3 -m stardome entrance D6
python3 -m stardome entrance --all --door 1800 700
make entrances
```

## The method

Unroll the dome. Every rod is a curve on a sphere; map each of its points to
`(azimuth, z)` and the structure becomes a flat elevation, 360° wide. A
ground-standing doorway is then an axis-aligned rectangle with its bottom edge
on z = 0.

For each azimuth the height available from the ground is the lowest a rod
reaches there, less the rod's radius — a **door envelope**, a histogram of free
height against azimuth. From it:

- the widest door of a given height is the longest run of the histogram at or
  above it;
- the largest door by area is the classic largest-rectangle-under-a-histogram
  problem, solved exactly rather than sampled.

Widths are arc length along the base circle, which is what a frame and a cover
panel get cut to.

The envelope is **resolution-dependent** and deliberately conservative: a rod
blocks a whole bin plus a margin, so coarse bins under-report. At the default
1440 bins (a quarter of a degree) the D/4 ratio below comes out at 0.255; at
360 bins it reads 0.229. Tests run at the default for that reason.

## The tallest gap is a quarter of the diameter

Every variant is the same shape at a different size, so this is a ratio, not a
lookup: the tallest unobstructed spot at the base ring is **0.2549 × diameter**.

| variant | free height | largest opening | @1200 | @1600 | @1800 | @2000 |
|---|---|---|---|---|---|---|
| D3 | 762 mm | 471 × 422 | — | — | — | — |
| D4 | 1018 mm | 628 × 564 | — | — | — | — |
| D6 | 1528 mm | 942 × 848 | 497 | — | — | — |
| D8 | 2038 mm | 1256 × 1132 | 1152 | 663 | 384 | 70 |
| D10 | 2548 mm | 1570 × 1416 | 1789 | 1353 | 1091 | 829 |
| D12 | 3059 mm | 1885 × 1700 | 2409 | 1990 | 1728 | 1518 |

Widths in mm at the given clear height. Openings repeat with the dome's D5
symmetry, so they come in fives or tens around the perimeter.

**Read that table for what it says.** A walk-in entrance — call it 1800 mm
clear at a useful width — does not exist below D10. **D6, the reference
prototype, cannot take a door you can walk through**: its best is 497 mm wide
at 1200 mm high. You duck and turn sideways. D3 and D4 have no 1200 mm opening
at all; they are crawl-in shelters.

## Which is what the skirt is really for

A skirt bay is a vertical wall between two posts, so unlike the dome it has no
ceiling curving in: the opening is the full bay height by the post-to-post
chord. On a small dome it is the only place a standing door fits.

`skirt_for_door` solves it the useful way round — given the door you want, how
much skirt does it need:

For **1800 × 700 mm**:

| variant | dome reaches | skirt needed | present | overall height |
|---|---|---|---|---|
| D3 | 200 mm | **1600 mm** | 1000 | 3073 mm |
| D4 | 480 mm | **1320 mm** | 0 | 3284 mm |
| D6 | 1040 mm | **760 mm** | 0 | 3707 mm |
| D8 | 1550 mm | **250 mm** | 0 | 4179 mm |
| D10 | 2080 mm | none | 0 | 4911 mm |
| D12 | 2600 mm | none | 0 | 5894 mm |

Two things fall out of this.

**D6 wants a skirt.** 760 mm turns the reference prototype from something you
crawl into to something you walk into, for 760 mm of extra height on a 6 m
dome. That is a much better trade than it sounds.

**D3 does not work.** It needs 1600 mm of skirt for a standing door, giving a
3.07 m structure over a 3 m footprint — taller than it is wide, which is a silo
rather than a dome. Either D3 accepts a crawl entrance, or the size is wrong
for a room you walk into.

## What this does not tell you

- **Nothing about the cover.** The fabric has to be cut and hemmed around the
  same gap, and a door in a bay removes whatever the fabric was doing for that
  bay's stiffness.
- **Nothing about the frame.** A door frame has its own stiffness, weight and
  attachment problem, and none of it is designed.
- **Nothing about the skirt's bracing.** Taking a bay out for a door removes
  exactly the bay a diagonal would have gone in. `docs/skirt.md` already says
  the skirt racks unbraced; a doorway makes that worse, not better.
- **Nothing about load paths.** An opening in a structure that gets its
  stiffness from being a closed surface is a real structural change, not a
  cosmetic one.
