# Four-rod fan node V2 — a stack of plates

Source of truth: `connectors/fan_node_v2.py`, driven from the model by
`connectors/generate_clamps.py`. The fan angles are not typed into the
generator — `stardome` derives them and the schedule passes them in.

Geometry background: [`tied-node.md`](tied-node.md). V1, superseded:
[`fan-node-v1.md`](fan-node-v1.md).

## Why V2 exists

V1 clamped the four rods as a bundle: a saddle under rod 1, a cap over rod 4,
rods 2 and 3 squeezed between them. It held the crossing together but it did
**not locate the middle rods at all**. Nothing stopped them sliding or rolling
inside the bundle except friction, and the dome's shape depends on the rods
crossing at the right angles at the right points.

V1 defended that with a constraint it called governing: adjacent rods touch, so
there is no room for material between them. That is true **only because V1 set
the stack pitch to exactly one rod diameter**, a choice inherited from the
two-rod clamp where the rods deliberately bear on each other. Nothing in the
dome requires it.

Open the pitch and every pair has room between it. That is the whole of V2.

## Architecture

| plate | channels | angle between them |
|---|---|---|
| Bottom | rod 1, groove up | — |
| Mid1 | rod 1 down, rod 2 up | 37.3774° |
| Mid2 | rod 2 down, rod 3 up | 41.8103° |
| Mid3 | rod 3 down, rod 4 up | 37.3774° |
| Cap | rod 4, groove down | — |

Every rod sits in a real channel, wrapped 180° from below by one plate and 180°
from above by the next, so each is positively located and each is still liftable
straight out. No rod touches another rod, which removes the three
crossed-cylinder contacts on fibreglass that V1's own notes flagged as the first
thing to check on a printed prototype.

**All five plates are different parts.** Mid1 and Mid3 have the same angle
between their grooves, but the two through-bolts pin each plate's orientation in
the fan and the groove pairs sit at different azimuths, so one cannot stand in
for the other. Five distinct prints per node, ten nodes per dome. An earlier
note in this project claimed three types; that was wrong.

### Field sequence

> open the stack → lay rod 1 → close Mid1 → rod 2 → Mid2 → rod 3 → Mid3 →
> rod 4 → Cap → tighten two bolts.

Five loose pieces at height in the wind is exactly what the project's first rule
says not to do. The answer is that the bolts keep the stack captive: assemble it
once, carry it as one hinged sandwich, open it to lay each rod. In the field it
is still one object per node.

## D6 numbers, 10 mm rod

| | V2 | V1 |
|---|---|---|
| pieces per node | 5 | 2 |
| rods positively located | 4 | 2 |
| rod-on-rod contacts | 0 | 3 |
| stack pitch | 13.40 mm | 10 mm |
| stack height | 40.2 mm | 30 mm |
| assembly height | 63.9 mm | 51.4 mm |
| footprint | 76.0 mm | 91.2 mm |
| bolts | 2 × M5 × 70 | 2 × M5 × 55 |
| volume per node | 115.7 cm³ | 60.2 cm³ |

13.40 mm is the **floor** for a 3 mm web: two channel radii plus the web, with
nothing else in the way. The stack cannot be made denser without thinning the
web, which is the piece carrying the clamping load between two rods.

V2 is still 1.9× the plastic of V1 and 12 mm taller. That is the price of
putting every rod in a channel, and it should be weighed honestly before ten of
these get printed. The footprint shrinks because V2 needs no solid posts beside
the rods — only bolt holes.

## The pitch is derived, and the web is measured

The pitch has to leave real material between two channels, and the first attempt
did not:

```
pitch = webThickness + channelRadius + upperReach
```

Three versions of this arithmetic were wrong before it was right:

1. `pitch = 2*channelRadius + web` left **0.85 mm of web instead of 3**: the
   tilt slack stretches both channels and a gable reaches 41% higher than the
   channel radius, and neither was accounted for.
2. Adding `2 * tiltSlack` fixed the web but spent **2.3 mm of pitch per
   interface** on tilt clearance at the node centre — which is precisely where
   the rod needs none. See "The flare" below.
3. Removing it left the pitch at its floor, `web + 2 * channelRadius` = 13.40 mm.

`verify` walks the node's own axis, where the two channels come closest, and
reports how much material is actually there: **2.95 mm measured on all three
middle plates** against 3.0 requested, the difference being the 0.05 mm probe
step. Measured, not asserted.

## The flare

Tilt clearance used to widen the channel uniformly along its whole length. That
is wrong twice over. The tilt is a rotation of the rod about the transverse axis
through the node centre, so the rod sits on the nominal axis at the centre and
deviates only towards the ends — and the centre is exactly where the web between
two stacked channels is thinnest.

The channel is now the swept volume of the rod rotated through the allowed
range: **narrow in the middle, flared at the mouths.** It costs nothing in pitch
and recovered 2.3 mm per interface, 6.9 mm off the stack.

It is built in a local frame with the rod along +X and its axis at the origin,
then placed. Fusing nearly-tangent cylinders is badly conditioned in OCC and the
result depends on how the seams happen to line up: done in world coordinates it
raised `Bnd_Box is void` on the fourth rod and produced an invalid solid on the
third, while the first two were fine. In the local frame every rod is the same
well-conditioned problem.

## Printability

All five plates print without supports, the cap upside down and the rest as they
sit:

| plate | worst overhang | unsupported below 45° | bridged channel roof | flat ceiling |
|---|---|---|---|---|
| Bottom | 50.06° | 26 mm² | 0 mm² | 0 mm² |
| Mid1 | 88.35° | 0 mm² | 866 mm² | 0 mm² |
| Mid2 | 90.00° | 0 mm² | 721 mm² | 0 mm² |
| Mid3 | 86.50° | 0 mm² | 721 mm² | 0 mm² |
| Cap | 49.99° | 0 mm² | 0 mm² | 0 mm² |

Each middle plate carries one channel that opens downward whichever way it is
printed. Its roof is a **bridge**: a horizontal-axis cylindrical surface walled
on both sides, exactly like the top of every horizontal hole in every printed
part, and FDM spans that routinely. The checker now classifies those separately
instead of counting them as unsupported overhang, which was making a sound part
look broken.

Bottom's 26 mm² is the same hexagonal-pocket-meets-round-taper corner as V1's.

### The gable is currently broken — leave `teardropRoof` at 0

`teardropRoof` was meant to cap each downward channel with a gable so its roof
never exceeds 45°, removing the bridge. Two things went wrong:

- Added *after* the flare, the gable only covered the nominal axis and the
  flared ends stuck out from under it as shallow round overhangs, dropping the
  middle plates from 45° to 26°. Fusing it *before* the flare fixes that, and
  the gable is built steeper than 45° by the tilt allowance so it still clears
  45° after being rotated.
- With that in place, the gabled cut then **silently removes nothing** from the
  middle plates, though the identical operation works in isolation — another
  instance of OCC boolean instability. `verify` catches it as 2094 mm³ of rod
  interference and a blind channel, so it cannot ship unnoticed, but it is not
  fixed.

The plain channel is the default and is what gives the density anyway: the gable
would cost 2.35 mm of pitch per interface, 7 mm on the stack.

## Known compromises for V2

1. **Five distinct plates per node**, fifty per dome. Mitigated by keeping the
   stack captive on its bolts, not eliminated.
2. **1.9x the material of V1** and a 63.9 mm tall assembly.
3. **Nothing tested in plastic.** Every number here comes from the solid model.
   No sample printed, no bolt torqued, no rod bent into it.
4. **Helpers are copied** from `fan_node_v1.py` rather than shared. All three
   connector scripts are exec'd standalone inside FreeCAD, so sharing needs a
   path loader in each; worth doing once the family settles, not while the
   architecture is still moving.
5. **The clamping load still passes through the plates in series.** Each web is
   3 mm; whether that is enough is a question for a printed sample, not for the
   model.
