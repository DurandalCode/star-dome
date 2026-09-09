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
| stack pitch | 17.86 mm | 10 mm |
| stack height | 53.6 mm | 30 mm |
| assembly height | 77.3 mm | 51.4 mm |
| footprint | 76.0 mm | 91.2 mm |
| bolts | 2 × M5 × 80 | 2 × M5 × 55 |
| volume per node | 139.8 cm³ | 60.2 cm³ |

V2 is **2.3× the plastic and 50% taller**. That is the price of putting every
rod in a channel, and it should be weighed honestly against V1 before ten of
these get printed. The footprint shrinks because V2 needs no solid posts beside
the rods — only bolt holes.

## The pitch is derived, and the web is measured

The pitch has to leave real material between two channels, and the first attempt
did not:

```
pitch = webThickness + channelRadius + upperReach + 2 * tiltSlack
```

where `upperReach` is `channelRadius` for a plain channel and
`sqrt(2) * channelRadius` for a gabled one. Setting `pitch = 2*channelRadius +
web`, as the first attempt did, left **0.85 mm of web instead of 3** — because
the tilt slack stretches both channels and the gable reaches 41% higher than the
channel radius. That web is the piece carrying the clamping load between two
rods.

`verify` now walks the node's own axis, where the two channels come closest, and
reports how much material is actually there: **3.0 mm on all three middle
plates**, matching the request. Measured, not asserted.

## Printability

All five plates print without supports, the cap upside down and the rest as they
sit:

| plate | worst overhang | area below 45° | flat ceiling |
|---|---|---|---|
| Bottom | 50.06° | 26 mm² | 0 mm² |
| Mid1 | 45.00° | 0 mm² | 0 mm² |
| Mid2 | 45.00° | 0 mm² | 0 mm² |
| Mid3 | 45.00° | 0 mm² | 0 mm² |
| Cap | 49.99° | 0 mm² | 0 mm² |

Each middle plate carries one channel that opens downward whichever way it is
printed. `teardropRoof` caps those with a 45° gable tangent to the channel, so
they print unsupported; the extra clearance sits above the rod where it does
nothing. The middle plates land at exactly 45.0° because that is what the gable
is set to.

Bottom's 26 mm² is the same hexagonal-pocket-meets-round-taper corner as V1's.

**Turning the gable off** (`teardropRoof = 0`) saves 6.5 mm of stack height and
13 cm³, at the cost of ~800 mm² per middle plate of arched channel roof. That
roof is a *bridge* between two walls, which FDM handles routinely — every
horizontal hole in every printed part is one — but this checker cannot tell a
bridge from a free-air overhang, so it reports it as a failure. The gable is on
by default because it makes the check mean something.

## Known compromises for V2

1. **Five distinct plates per node**, fifty per dome. Mitigated by keeping the
   stack captive on its bolts, not eliminated.
2. **2.3× the material of V1** and a 77 mm tall assembly.
3. **Nothing tested in plastic.** Every number here comes from the solid model.
   No sample printed, no bolt torqued, no rod bent into it.
4. **Helpers are copied** from `fan_node_v1.py` rather than shared. All three
   connector scripts are exec'd standalone inside FreeCAD, so sharing needs a
   path loader in each; worth doing once the family settles, not while the
   architecture is still moving.
5. **The clamping load still passes through the plates in series.** Each web is
   3 mm; whether that is enough is a question for a printed sample, not for the
   model.
