# Star Dome — OpenSCAD geometry

Parametric model of the Takekawa-style Star Dome. This is the geometric source
of truth for the D4, D6, D8 and D12 variants.

It models **structural rod centrelines only**. No connectors, no fabric cover,
no reinforcement belts.

## What this dome is

Not a geodesic strut dome. There are no short straight struts and no hubs.
There are **15 long flexible rods, all exactly the same length**, each bent into
one continuous arc that runs the full width of the dome and lands on the ground
at both ends. Rods cross each other and are lashed or clamped where they meet.

From the reference (Daisuke Takekawa / Kyushu Fieldwork Society, written up by
René K. Müller at <https://simplydifferently.org/Star_Dome>):

- 15 full-length bows, all identical.
- A 10-sided base polygon; **3 bow ends at each of the 10 ground points**
  (15 × 2 = 30 ends ÷ 10 points = 3 exactly).
- Bow length `lbow = c / 2`, where `c` is the base circumference.
- Optionally 2 further identical bows bent into the base ring itself.
- Cover pattern: 6 pentagons + 10 triangles of equal side.

## How the geometry is derived

Nothing in the model is a hand-placed coordinate. Everything follows from the
base polygon count, one icosahedral angle, and the reference's rod-marking
diagram.

### 1. Every bow is a great semicircle

`c = π·d`, so `lbow = π·d/2 = π·R` — exactly half a great circle. Two points on
the ground ring can only be joined by a great circle if they are diametrically
opposite, so each bow runs from one base point, over the dome, to the base point
directly across from it.

This also explains the two optional base-ring bows: the ring is `2πR`, exactly
two bow lengths.

With 10 base points there are only 5 diametral axes, so the 15 bows sit 3 to an
axis — the reference's "3 bows from each bottom point".

A bow is fully described by two numbers: the azimuth of its starting base point
and the tilt of its plane above the ground. Arc angle `t` runs 0…180° along a
bow and is proportional to length, so the reference instruction "mark the rod in
thirds" means `t = 60°, 120°`, and "mark it in fifths" means
`t = 36°, 72°, 108°, 144°`.

### 2. The marking diagram fixes the three families

The reference's marking diagram is what pins the design down. It shows three
groups of identically-marked rods:

| count | marks  | junctions per rod | reference colour |
|-------|--------|-------------------|------------------|
| 10    | thirds | 2                 | blue             |
| 5     | fifths | 4                 | green            |
| 2     | fifths | (base ring)       | red              |

**Family G** — the 5 rods marked in fifths. These are the dome's
icosidodecahedral skeleton. Orient an icosidodecahedron (12 pentagons +
20 triangles, all edges equal) with one of its 6 equatorial decagons horizontal:
that decagon is the base ring and its 10 vertices are the base points. Each of
the other 5 equatorial decagons crosses the ground plane at one diametral pair
of base points, and its upper half is exactly 5 edges long — one bow, marked in
fifths, with the 4 interior marks landing on icosidodecahedron vertices.

Its tilt is the angle between adjacent 5-fold axes of an icosahedron,
`atan(2) = 63.4349°`. The model *asserts* rather than assumes that this tilt
puts the G–G crossings at exactly 36°, 72°, 108° and 144°.

Family G plus the base ring **is** the icosidodecahedron hemisphere:
6 pentagons + 10 triangles — the reference's cover pattern, and what
"developed from a 2V geodesic dome" means.

**Families U and L** — the 10 rods marked in thirds; Takekawa's addition.
Family G alone puts only one bow at each base point; these bring it to three.
Each family is 5 great semicircles on the same 5 diametral axes, tilted so that
their thirds marks land exactly on crossing nodes family G already created:

- family **U** (upper) → the 5 high nodes, `z = 0.850651·R`
- family **L** (lower) → the 5 lower nodes, `z = 0.525731·R`

Both tilts are computed from the G–G node heights, not typed in:

```
sin(60°) · sin(tilt) = z_node   ⟹   tilt = asin(z_node / sin 60°)
```

giving **79.1877°** for U and **37.3774°** for L.

### 3. Why this reading is the right one

The result reproduces the reference marking diagram exactly, with nothing left
over and nothing missing:

- 10 tied nodes, each joining 4 rods.
- Every family-G rod tied at 4 points, all on fifth marks.
- Every U and L rod tied at 2 points, both on third marks.
- 5×4 + 10×2 = 40 junction ends, which is 2 × 20 — the two halves balance.

The 5 high nodes are the pentagon at the top of the dome that the reference
construction describes; the 5 lower nodes are the surrounding pentagon.

## Files

```
dome/star_dome.scad            parameters, rendering, visual aids, console report
dome/star_dome_geometry.scad   topology, families, nodes, derived dimensions
dome/lib/great_circles.scad    great-circle ("bow") maths on a sphere
dome/lib/vectors.scad          generic 3D vector helpers
dome/variants/star_dome_*.scad one-line wrappers per named variant
configs/variants.scad          the named D4 / D6 / D8 / D12 presets
```

`configs/variants.scad` is the only file containing a variant-specific number.

## Usage

```bash
OSC=/Applications/OpenSCAD-2021.01.app/Contents/MacOS/OpenSCAD

# open the D6 reference variant in the GUI
$OSC dome/star_dome.scad

# a named variant
$OSC -D 'variant="D8"' dome/star_dome.scad
$OSC dome/variants/star_dome_d8.scad

# override a single dimension
$OSC -D 'rodDiameter=12' dome/star_dome.scad

# export a mesh for Blender
$OSC -o exports/star_dome_d6.stl dome/variants/star_dome_d6.scad

# console report + a preview image
$OSC -o /tmp/preview.png --imgsize=800,600 dome/star_dome.scad
```

## Parameters

| parameter | default | meaning |
|---|---|---|
| `variant` | `"D6"` | named preset from `configs/variants.scad` |
| `domeDiameter` | from variant | ground-ring diameter, mm |
| `rodDiameter` | from variant | rod stock diameter, mm |
| `rodSegments` | `48` | straight pieces per 180° bow |
| `renderQuality` | `2` | 1 draft / 2 preview / 3 final; facet counts only |
| `showNodes` | `true` | master switch for node markers |
| `showGroundRing` | `true` | the 2 optional bows bent into the ground ring |
| `showLabels` | `false` | rod numbers, node ids, base point numbers |
| `showGroundCircle` | `true` | flat reference circle at the nominal diameter |
| `showBaseNodes` | `showNodes` | markers at the 10 ground points |
| `showTiedNodes` | `showNodes` | markers at the 10 lashed crossings |
| `showUntiedCrossings` | `false` | markers at the 30 unlashed crossings |
| `showAxes` | `false` | XYZ axes at the origin |
| `weaveMode` | `"layered"` | `"layered"` or `"flat"` — see below |
| `weaveGap` | `1.0` | shell spacing, as a multiple of rod diameter |
| `reportSummary` | `true` | echo dimensions, rod schedule, node table |
| `reportAllCrossings` | `false` | also echo all 90 rod-to-rod crossings |

### Weave modes

Every pair of the 15 bows crosses somewhere, and in the exact model all of them
lie on one sphere, so at every crossing two centrelines coincide. Real rods
cannot do that — one passes outside the other.

- **`"layered"`** (default) gives each bow its own thin shell, spaced by the rod
  diameter, so no two centrelines ever coincide and every crossing reads as a
  clean over/under. Because all 15 bows cross each other, constant offsets need
  all 15 shells distinct; the band is `14 × weaveGap × rodDiameter` thick,
  centred on the nominal sphere. Mean radius and total rod length are unchanged,
  but individual rods differ in length by a couple of percent and the 3 rod ends
  at each base point spread radially across the band.
- **`"flat"`** puts every centreline exactly on the nominal sphere. Use it for
  measurement, for true base-point coordinates, and for centreline export. All
  15 rods then come out at exactly the same length, as the design intends.

## Console output

With `reportSummary = true` the model echoes:

- overall diameter and height (nominal and as-drawn), structural height,
  base edge arc and chord;
- bow length, per-rod length, total rod length, base ring length;
- the rod schedule: family, feet, azimuth, tilt, length, tie-mark distances
  in mm along the rod;
- the 10 base nodes with coordinates and which rods land there;
- the 10 tied crossings with coordinates, the 4 rods through each, and every
  pairwise crossing angle;
- the untied crossings (all 90 pairs with `reportAllCrossings = true`);
- topology and symmetry checks.

## Validation (D6, OpenSCAD 2021.01)

Rendered and checked. All of the following are computed by the model itself and
echoed to the console:

| check | result |
|---|---|
| continuous members | 15 |
| rod ends per base node | 3 at every one of the 10 base points |
| tied nodes | 10 |
| rods through each tied node | 4 at every node |
| tied junctions per rod | 12 for family G, 6 for U and L |
| tied node heights | 5 × `0.850651·R`, 5 × `0.525731·R` |
| total crossings above ground | 90 (10 four-rod nodes + 30 two-rod crossings) |
| rotation by 72° / 144° | symmetry |
| rotation by 36° | *not* a symmetry — the top pentagram is only 5-fold |
| mirrors at azimuth 90° / 162° | symmetry |
| symmetry group | D5, order 10 |
| max abs. height of the 30 rod ends | 0 mm — every rod end is on the ground plane |
| bow lengths (`weaveMode="flat"`) | all 15 identical at `π·R` |
| G tie marks | exactly 1/5, 2/5, 3/5, 4/5 of rod length |
| U and L tie marks | exactly 1/3, 2/3 of rod length |

Crossing angles are constant across all 10 nodes, which is further evidence the
symmetry is exact: G/G 63.4349°, G/U and G/L 37.3774° and 79.1877°,
U/U and L/L 41.8103°.

D6 derived dimensions: bow length 9424.78 mm each, total rod length
141372 mm (plus 18849.6 mm if the 2 base-ring bows are used), structural height
2946.74 mm.

## Assumptions and ambiguities

The reference gives a construction procedure, formulas and a marking diagram —
but no coordinates and no angles. The following were reconstructed, and are the
places to challenge first if the model ever disagrees with a physical build.

1. **Bows are great circles.** The reference gives `lbow = c/2 = π·R`, which is
   exactly a great semicircle, and an unconstrained elastic rod held against a
   sphere settles onto a great circle. Taken as the intended idealisation. A
   real rod under cover and wind load will not be a perfect great circle.

2. **The reference's 15 great circles are not the icosahedral 15-great-circle
   figure.** That figure exists, but no plane cuts it into 10 ground points with
   3 circles each, so it cannot be the Star Dome. The arrangement used here has
   D5 symmetry rather than full icosahedral symmetry.

3. **Family assignment of the "thirds" rods.** The marking diagram shows
   10 identical thirds-marked rods but does not say they form two differently
   tilted groups. Two groups is the only arrangement found that gives 3 rods per
   base point *and* lands every thirds mark on a real node. Both groups start
   from the even base points, with family G on the odd ones; the reverse is the
   same dome rotated 36°.

4. **Which crossings are lashed.** Taken directly from the mark counts: 4 per
   green rod, 2 per blue rod. The other 30 crossings are places where rods touch
   but the reference does not tie them. Whether a real build wants clamps there
   is an open question for the prototype.

5. **Four rods meet at every tied node.** This follows from the reconstruction
   and is not stated in the reference. It is a significant input to connector
   design — a crossing clamp has to handle 4 rods at three distinct angles, not
   2 — and should be checked against photographs and a physical mock-up before
   any connector work starts.

6. **Base edge `s`.** The reference's formulas treat `s` as `c/10`, i.e. an arc
   length, because its base ring is two bent rods. A cover panel or a ground
   beam would measure the chord instead. Both are reported; for D6 the arc is
   1884.96 mm and the chord 1854.10 mm.

7. **Dome height is not the sphere radius.** No bow passes over the zenith, so
   the top of the structure is the apex of family U at `0.982247·R`, not `R`.
   The reference's surface-area and volume formulas assume a full hemisphere,
   which the cover will approximate but the rods do not reach.

8. **Rod diameters are provisional.** See `configs/variants.scad`. Nothing here
   has been checked against fiberglass properties, buckling, minimum bend
   radius, wind load, cover load or anchoring. Every bow is bent to a radius
   equal to the dome radius, so required bend radius scales directly with the
   variant: 2000 mm for D4 up to 6000 mm for D12.

9. **The weave is a drawing convention, not a build instruction.** `"layered"`
   picks an arbitrary but consistent over/under order so crossings are legible.
   Which rod actually passes outside at each crossing is a build decision that
   has not been made.
