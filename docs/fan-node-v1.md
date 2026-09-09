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
| volume | 73.8 cm³ base + 66.9 cm³ cap |

Verified in FreeCAD: both solids valid and single, zero interference with all
four rods and both bolts, base and cap do not intersect, and no material
overhangs a rod so every one can be dropped in.

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

1. **It is big.** 91 mm across and 141 cm³ for the pair, against 48 × 54 mm and
   36 cm³ for the two-rod clamp. Ten of them is about 1.4 litres of filament.
2. **The cap is a plain disc** and mostly dead material — it only needs to span
   between the two bolts over rod 4. An easy large saving, not yet taken. The
   base disc has the same problem.
3. **Three crossed-cylinder contacts in series.** The clamping path is
   cap → rod 4 → rod 3 → rod 2 → rod 1 → base. `crossing-clamp-v1.md` already
   flags one such contact on fibreglass as the first thing to check on a
   printed prototype; here there are three, and the middle rods are held by
   friction alone.
4. **No fillets and no printability pass.** V1 of the two-rod clamp has both;
   this does not yet.
5. **A departure from the reference.** The original ties these junctions with
   two or three pairwise cable ties over a short span, letting the rods spread.
   A rigid part forces exact concurrency. The tilt slack helps; whether it is
   enough is a question for the printed prototype, and a stack of two-rod
   clamps remains a legitimate alternative.
