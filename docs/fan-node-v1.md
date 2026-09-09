# Four-rod fan node V1 — design notes

Source of truth: `connectors/fan_node_v1.py`, driven from the model by
`connectors/generate_clamps.py`. The fan angles are not typed into the
generator — `stardome` derives them and the schedule passes them in.

Geometry background: [`tied-node.md`](tied-node.md).

## The governing constraint

Adjacent rods in the fan-order stack **touch**. Their axes are exactly one
diameter apart and they meet at the crossing point, so there is no room for
material between them — not at the centre, and not further out either, because
the vertical gap between their surfaces stays zero all along the rod.

A plate-per-layer sandwich is therefore impossible. Material can only live
**below rod 1, above rod 4, and in the sectors between the rods.**

## Architecture

- **Base** — a 180° saddle under rod 1, open upward, carrying two posts that
  rise through the fan's two widest sectors (63.4349°, the only ones that clear
  every rod) to meet the cap.
- **Cap** — a 180° saddle over rod 4, open downward, bolted down onto the posts.

Rods 2 and 3 are captured between rods 1 and 4 and contained laterally by the
posts. They are not gripped individually — the same compromise
`crossing_clamp_v1` makes, and defensible for the same reason: each rod is a
continuous arc already located by its other nodes and its two ground points, so
the joint has to hold the crossing together rather than fully constrain every
member.

Field sequence, which matches how the reference assembles the dome anyway:

> lay rod 1 in the base → drop rods 2 and 3 on it → lay rod 4 → cap → two bolts.

## D6 numbers, 10 mm rod

| | |
|---|---|
| stack height | 30.0 mm (3 rod diameters) |
| assembly height | 51.4 mm |
| footprint | 91.2 mm diameter |
| bolts | 2 × M5 × 53, at 34.6 mm from centre |
| channel | 10.4 mm diameter, 103.2 mm long |
| tilt slack | 1.35 mm, for the ~1.2° radial tilt the weave requires |
| post to nearest rod | 4.0 mm |
| volume | 35.5 cm³ base + 24.7 cm³ cap |

Verified in FreeCAD: both solids valid and single, zero interference with all
four rods and both bolts, base and cap do not intersect, and no material
overhangs a rod so every one can be dropped in.

## Printability

Both halves print **without supports**, the base on its underside and the cap
upside down so its saddle faces up:

| | worst overhang | area below 45° | flat ceiling |
|---|---|---|---|
| base | 14.9° on an 8.8 mm² face | 37 mm² | 0 mm² |
| cap, printed upside down | 49.99° | 0 mm² | 0 mm² |

The cap is clean outright. The base has 37 mm² below the limit — about a 6 mm
square, 4.6 mm above the bed, where the hexagonal nut pocket meets its round
taper and the circle only touches the hex at six corners. A slicer bridges
that without noticing, and for scale the accepted two-rod clamp V1 reports a
worst overhang around 43°, itself under the limit.

Chasing it further would mean a hex-to-round loft for a fastener recess, which
is not worth doing before anything has been printed.

Neither half has a single square millimetre of flat ceiling.

The headline angle ignores faces under 5 mm²: a sliver a millimetre across
bridges without anyone noticing and should not set the number. It still counts
in the area column.

Neither half has a horizontal round hole: every rod channel is an open groove
in a face that points at the sky in its print orientation, and the bolt holes
are vertical. That is what makes the result this clean, and it is a property of
the architecture rather than of tuning.

### Not a solid disc

The first version used a full disc for both halves: 73.8 + 66.9 = 141 cm³. A
disc is mostly dead material — the part only has to hold the rod at the centre
and reach the two bolts. Replacing it with a hub, two spars and two bolt
bosses gives the same footprint for **60 cm³, a 57% saving**, and about 0.6 l
of filament for the ten nodes a dome needs.

### Five bugs in the checks themselves

- **A flat ceiling worth 32 mm², from a one-micron gap.** The nut pocket ended
  at `z_base_bottom + nutRecessDepth - 0.001` while its taper began at
  `+ nutRecessDepth`. The micron between them left the pocket's top face
  exposed as a flat ring with nothing under it. The pocket now runs from below
  the bed up to exactly where the cone starts.
- **Every upward face read as an overhang.** The cap is printed upside down,
  and the first check mirrored the shape to analyse it. Mirroring reverses face
  orientation, so `face.Orientation` lied and the part failed on its own good
  faces. The check now takes a print direction instead of mirroring, and finds
  the outward normal by stepping off the surface and asking the solid whether
  that point is inside — which no fuse, cut or mirror can confuse.
- **Sampling ignored trimming.** Face normals were sampled over the parameter
  rectangle, which covers the holes cut out of a trimmed face as well as the
  material. Samples landing in a hole read a normal for material that is not
  there, the probe then lands inside the solid, and the sign flips — which is
  how the base's flat top face came to be reported as a 0° overhang. Samples
  are now filtered by `isPartOfDomain`.

Adding fillets then produced two more of the same kind:

- **`Shape.BoundBox` is only an outer estimate.** After filleting it put the
  base's floor at −142 mm instead of −25.2, so no face matched the bed and the
  bed itself was reported as an unsupported ceiling. Bed level and face extents
  now come from vertex coordinates, which are exact.
- **`MeshPart.meshFromShape` leaves the shape reporting `isValid() == False`.**
  The driver verified after exporting, so a solid that had just written a valid
  STEP was reported as broken. Verification now runs before meshing, in both
  the fan and the two-rod clamp.

All five were errors in the verification rather than in the part. That is the
pattern to expect from checks written alongside the thing they check, and it is
the argument for keeping the checks in the repository where they can be read
and doubted rather than trusting a green line of output.

## Fillets

Vertical silhouette corners on both halves at `edgeRadius`, and the rim of each
part's upward face in its own print orientation at 60% of that: 26 + 7 edges on
the base, 16 + 25 on the cap. The bed-contact faces are left sharp on purpose,
because a fillet there costs first-layer adhesion.

Filleting the upward face also rounds where each rod channel opens onto it,
which is the edge that would otherwise bear into the rod. That is the point of
doing it rather than a side effect.

Edges that cannot take the radius are skipped rather than failing the build: a
missing fillet is cosmetic, a failed solid is not.

## The bug the first attempt had

`channelLength` was a hand-picked 76 mm while the body came out 91 mm across,
so every rod channel ended **blind** about 7 mm short of the rim. The rods
could not have been inserted at all.

The interference check did not catch it, because the reference rods used for
that check were the same 76 mm — a rod that ends blind inside the body does not
intersect anything. The check was comparing the part against a rod shaped to
fit its own mistake.

Two fixes, both kept:

- the channel length is **derived** from the footprint, never given;
- `verify` probes with a rod six times the footprint, which only clears if the
  channel runs right through. `blind_channel_mm3` reports it per rod.

## Known compromises for V1

1. **It is still big.** 91 mm across and 60 cm³ for the pair, against 48 × 54 mm
   and 36 cm³ for the two-rod clamp. The footprint is set by how far out the
   bolts have to sit to clear every rod, so it will not shrink much without
   changing where the load is taken.
2. **The nut-pocket transition** leaves 37 mm2 below the 45 deg overhang limit,
   at the six corners where a round taper meets a hexagonal pocket. Bridgeable, but not clean.
3. **Three crossed-cylinder contacts in series.** The clamping path is
   cap → rod 4 → rod 3 → rod 2 → rod 1 → base. `crossing-clamp-v1.md` already
   flags one such contact on fibreglass as the first thing to check on a
   printed prototype; here there are three, and the middle rods are held by
   friction alone.
4. **Nothing tested in plastic.** Every number here comes from the solid model.
   No sample has been printed, no bolt torqued, no rod bent into it.
5. **A departure from the reference.** The original ties these junctions with
   two or three pairwise cable ties over a short span, letting the rods spread.
   A rigid part forces exact concurrency. The tilt slack helps; whether it is
   enough is a question for the printed prototype, and a stack of two-rod
   clamps remains a legitimate alternative.
