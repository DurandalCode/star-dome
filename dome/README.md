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
dome/star_dome.scad            parameters, rendering, visual aids, reports, data export
dome/star_dome_geometry.scad   topology, families, nodes, analysis, derived dimensions
dome/lib/great_circles.scad    great-circle ("bow") maths on a sphere
dome/lib/vectors.scad          generic 3D vector helpers
dome/lib/sorting.scad          deterministic sort, so generated IDs stay stable
dome/lib/formatting.scad       exact fixed-point number formatting for export
dome/variants/star_dome_*.scad one-line wrappers per named variant
configs/variants.scad          the named D4 / D6 / D8 / D12 presets
tools/export_geometry.py       turns the model's DATA| lines into JSON + CSV
```

`configs/variants.scad` is the only file containing a variant-specific number.
`tools/export_geometry.py` contains no geometry at all — see "Engineering
geometry report" below.

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
| `debugCrossings` | `false` | marker + node-ID label at every crossing point |
| `debugCrossingType` | `-1` | `-1` = all classes; `0`…`11` isolates one and fades the rods not involved |
| `debugMarkerScale` | `2.6` | debug marker size, as a multiple of rod diameter |
| `renderModel` | `true` | draw the dome; off for report/export only |
| `reportSummary` | `true` | echo dimensions, rod schedule, node table, crossing classes |
| `reportAllCrossings` | `false` | also echo all 90 rod-to-rod crossings |
| `emitGeometryData` | `false` | echo the machine-readable `DATA\|` lines |
| `dataDecimals` | `6` | decimals used in the data export |

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

## Engineering geometry report

### Why it is split across two files

OpenSCAD cannot write files — it can only print. So the model emits tagged
`DATA|` lines and `tools/export_geometry.py` turns them into JSON and CSV.

The exporter contains **no geometry**. It does not know what a bow is, how many
crossings there should be, or what any angle is; it parses whatever the model
prints and cross-checks the row counts against the model's own totals. That
keeps OpenSCAD the single source of truth, as `AGENTS.md` requires, and means
the export cannot drift away from the rendered dome.

One consequence worth knowing: OpenSCAD prints every number at 6 significant
digits and offers no way to ask for more, which would silently round a crossing
coordinate to about 0.01 mm on a 6 m dome. `dome/lib/formatting.scad` works
around that by never handing a long number to `str()` — it splits values into
short chunks and reassembles them as text, so the export is exact to the
requested decimals.

### Running it

```bash
tools/export_geometry.py                 # D6, the reference variant
tools/export_geometry.py --variant D8
tools/export_geometry.py --all           # every variant in configs/
tools/export_geometry.py --weave layered # report the drawn radial gaps too
```

Output lands in `exports/geometry/`:

```
star_dome_<variant>.json                 everything, nested
star_dome_<variant>_crossings.csv        the 90 rod-to-rod crossings
star_dome_<variant>_crossing_types.csv   the 12 symmetry classes
star_dome_<variant>_nodes.csv            the 40 distinct crossing points
star_dome_<variant>_base_nodes.csv       the 10 ground points
star_dome_<variant>_rods.csv             the rod schedule
```

`exports/` is git-ignored as generated output, per `AGENTS.md`. Regenerate it
with one command rather than committing it.

### What a crossing record contains

Per rod pair: stable node ID, both rod IDs and families, XYZ of the crossing,
arc position along each rod in both degrees and millimetres, the unit tangent
of each rod at the crossing, the acute angle between those tangents, each rod's
inclination above horizontal, which rod passes above which, the radial gap
between them, whether the junction is lashed, and its symmetry class.

Conventions, stated because they are choices rather than facts:

- **Coordinates** are nominal centrelines on the sphere, identical to
  `weaveMode = "flat"`. That is the only configuration in which two rods
  genuinely intersect at a point. Under the layered weave they pass at a small
  radial gap instead, reported per pair as `radial_gap` rather than folded into
  the coordinates.
- **Inclination** is the unsigned angle of the rod tangent above horizontal,
  0…90°. Unsigned because a rod has no inherent direction: which way you walk
  along it must not change the answer.
- **Above** means the rod on the outer weave shell. This comes from the weave
  layering, which is a drawing convention — not a validated build decision.

### Two different crossing counts

Both are correct and both matter:

- **40 distinct crossing points** — 10 where four rods pass through one point,
  30 where two do.
- **90 rod-to-rod pairs** — `10 × C(4,2) + 30 × 1`. The tables are per pair,
  because a connector clamps a pair of rods.

## Crossing taxonomy (D6, and identical in shape for every variant)

**12 symmetry-distinct crossing geometries**, six of size 5 and six of size 10,
totalling the 90 pairs. Heights scale with the dome; angles do not.

| type | rods | count | lashed | height (D6) | angle | inclination a / b |
|------|------|-------|--------|-------------|-------|-------------------|
| T00 | U–U | 5  | no  | 2919.75 mm | 70.5288° | 7.62° / 7.62° |
| T01 | G–U | 10 | yes | 2551.95 mm | 37.3774° | 16.05° / 29.41° |
| T02 | U–U | 5  | yes | 2551.95 mm | 41.8103° | 29.41° / 29.41° |
| T03 | G–G | 5  | yes | 2551.95 mm | 63.4349° | 16.05° / 16.05° |
| T04 | G–U | 10 | yes | 2551.95 mm | 79.1877° | 16.05° / 29.41° |
| T05 | L–U | 10 | no  | 1804.50 mm | 70.5288° | 50.94° / 4.70° |
| T06 | G–L | 10 | yes | 1577.19 mm | 37.3774° | 46.35° / 17.67° |
| T07 | L–L | 5  | yes | 1577.19 mm | 41.8103° | 17.67° / 17.67° |
| T08 | G–G | 5  | yes | 1577.19 mm | 63.4349° | 46.35° / 46.35° |
| T09 | G–L | 10 | yes | 1577.19 mm | 79.1877° | 46.35° / 17.67° |
| T10 | L–U | 10 | no  | 1115.24 mm | 70.5288° | 65.39° / 28.68° |
| T11 | L–L | 5  | no  | 689.26 mm  | 70.5288° | 34.19° / 34.19° |

**Five distinct crossing angles: 37.3774°, 41.8103°, 63.4349°, 70.5288°,
79.1877°.** They are not all equal, and no connector that assumes a single
angle will fit this dome.

Two patterns fall out of the table:

- Every **lashed** crossing is at 37.3774°, 41.8103°, 63.4349° or 79.1877°.
- Every **unlashed** crossing is at 70.5288° = `acos(1/3)`, the tetrahedral
  angle, without exception.

### How the classes were verified

The model groups crossings by an invariant signature: the families involved,
each rod's folded arc position, the height, the angle and the lashed flag —
every one of which the D5 symmetry group preserves.

That grouping was then checked against the group action itself: all 10 elements
of D5 (five rotations, five mirrors) were applied to all 90 crossings and the
orbits computed directly. The orbit partition and the signature partition are
identical — the signature neither over-splits nor under-splits. Orbit sizes are
5 and 10, both of which divide the group order, as they must.

## Debug render mode

```bash
# every crossing point marked and labelled with its node ID
openscad -D debugCrossings=true dome/star_dome.scad

# isolate one symmetry class; rods not involved fade to 12% opacity
openscad -D debugCrossings=true -D debugCrossingType=4 dome/star_dome.scad
```

Lashed nodes get a larger amber marker, unlashed ones a smaller grey marker.
Markers sit on the nominal sphere, so under the layered weave a marker sits
between the two rods rather than on either — that offset is the reported
`radial_gap`.

A class of 10 crossings may show fewer than 10 markers: at the four-rod nodes,
two pairs of the same class share one point.

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
| distinct crossing points | 40 (10 four-rod, 30 two-rod) |
| rod-to-rod crossing pairs | 90 |
| symmetry-distinct crossing geometries | 12 (6 orbits of 5, 6 of 10) |
| signature classes vs. true D5 orbits | identical partition |
| distinct crossing angles | 5 |
| rod length classes (nominal) | 1 |
| export row counts vs. model totals | agree for all four variants |

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

5. **Four rods meet at every tied node.** ~~Not stated in the reference.~~
   **Confirmed** against the reference's own construction diagram
   (`stardome-structure.png`): panel 1 rings 5 junctions of the blue pentagram,
   each with two blue bows crossing; panel 2 adds the green bows and the same
   5 rings carry two blue plus two green. Four rods, in the pattern this model
   predicts.

   The reference *builds* those junctions with pairwise cable ties, several of
   them clustered over a short span, rather than as one four-rod bundle — see
   the bamboo model photo. A single rigid four-rod part is therefore a
   departure from the reference's practice, not a copy of it. See
   [`../docs/tied-node.md`](../docs/tied-node.md).

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
   picks an arbitrary but consistent over/under order so crossings are legible:
   rods are stacked by family, G innermost, then U, then L, and by index within
   a family. The `rod_above` / `rod_below` columns in the export report exactly
   that ordering. It is internally consistent and it is what the renders show,
   but it is not a validated build decision, and it is not symmetric — two
   crossings in the same symmetry class can have opposite over/under. Deciding
   the real weave order is prototype work.

10. **The 30 unlashed crossings.** The reference's mark counts say these rods
    touch but are not tied. They all sit at the same 70.5288° angle. Whether a
    real build wants a clamp, a spacer or nothing at all there is open, and it
    matters: they are a third of all rod-to-rod contacts.
