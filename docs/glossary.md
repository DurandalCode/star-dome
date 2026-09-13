# Glossary

This project has its own vocabulary, some of it borrowed from the reference and
some of it invented here. Every term below appears in the code, the data
contract or the docs with exactly this meaning.

## The structure

**bow** — one full-length rod, bent into a great semicircle from a base point
to the base point diametrically opposite. There are 15, named `G1`–`G5`,
`U1`–`U5`, `L1`–`L5`. Every bow is the same length, `pi * R`.

**family** — one of the three groups of five bows, distinguished by the tilt of
their plane: **G** at `atan(2)` = 63.4349° (the one angle the design is seeded
with), **U** at 79.1877°, **L** at 37.3774°. U and L are not free parameters;
their tilts are fixed by the node heights family G creates.

**base point** — one of the 10 ground points at the corners of a regular
decagon, named `b0`–`b9`. Three bow ends land at each, one from each family.

**crossing** — one rod-to-rod contact. There are 90, which is every pair of
bows except the 15 that share both feet.

**node** — a distinct point where crossings happen. There are 40: **10 lashed
nodes** where four rods pass through one point, and **30 unlashed crossings**
where two do. Named `N00`–`N39`, top of the dome first.

**tied / lashed** — of a node or a crossing, one of the ten four-rod ones. The
reference ties these and leaves the rest.

**tie mark** — a mark along a bow where a lashed node falls: fifths on family G,
thirds on U and L. There are 40, one per rod per lashed node, and they are the
only points on a rod that anyone measures.

**fan** — the four rods at a lashed node seen in the node's tangent plane. They
are coplanar, so the node is a flat four-armed fan rather than a
three-dimensional tangle, and all ten are the same fan.

**stacking order** — which of the four rods at a lashed node sits innermost,
next, and so on along the radius. A build decision, not a geometric fact; the
project uses fan order, 1-2-3-4 — [decision 0010](decisions/0010-the-stacking-order-is-fan-order.md).

**weave** — the radial route each rod takes between its lashed nodes so that no
crossing has two rods in the same place. Solved by `weave.global_profile`;
interpolating straight between the nodes does not work.

**layer / weave shell** — a *drawing* convention for which rod passes outside at
a crossing, used to render the model with visible separation. **Not** a build
instruction.

**threading** — one assembly move where a bow has to be passed *under* a bow
already standing. The unit the assembly order is optimised in — `assembly.md`.

**node spread** — how far apart the four marks that should coincide at a lashed
node actually land, given measurement error. The unit the error budget is
expressed in — `tolerance.md`.

## The openings

**bay** — the gap between two adjacent bows at the base ring. There are ten,
alternating tall and low.

**lancet** — a **tall** bay: a pointed arch of two G bows meeting at a lashed
node, head at 0.2629 of the diameter.

**portal** — a **low** bay with the crossing that fills it removed: two U bows
rising from adjacent base points with one L bow lying nearly level across the
top, head at 0.3009 of the diameter. This is where the door goes —
[decision 0007](decisions/0007-the-door-is-a-portal-not-a-lancet.md).

**jamb / head node** — the two bows framing a lancet's sides, and the lashed
node at its point.

**cut level** — how much rod a doorway takes out: `none`, `jambs`, `head` or
`portal`. Set per door in `configs/variants.toml`.

**facing** — the azimuth a door asks for. A wish rather than a position: a door
can only sit in a bay, so the nearest eligible one takes it — low bays for a
portal, tall bays for everything else — and the record says where it **landed**.

**landless bow** — a bow whose ends were both cut away, so it is still
continuous and still loaded but stands on no foot. One door cannot make one;
two can.

**admits** — the list of human silhouettes that actually fit through a given
opening: `crawl`, `stoop`, `walk`, `walk_wide`, `carry`, `tall`. The config
records what gets in, not what was wanted —
[decision 0008](decisions/0008-the-config-records-what-a-dome-admits.md).

**skirt** — a vertical wall of posts under the base ring, raising the dome. Its
height is not a preference: it is the shortest that lets the chosen silhouette
through. Only S has one.

**header** — the member carrying hoop force over a skirt's doorway bay, since
an open bay breaks the top ring.

## The cover

**gore** — a tapered strip between two meridians, developable to the accuracy
anyone cuts fabric to. A spherical cover is sewn from these; the roll width
fixes how many.

**tip index** — silhouette centroid height over base radius, dimensionless.
**A shape comparison between variants, with no pressure coefficient in it and
no safety claim attached.**

## The parts

**fan node** (`FAN4-d-a`) — the connector at a lashed node, a stack of five
plates. 10 per dome.

**crossing clamp** (`CL2-d-a`) — the two-rod connector at an unlashed crossing.
30 per dome, and whether they are needed at all is still open.

**base hub** (`BASE3-d`) — the connector at a base point: the fan with one arm
fewer, plus a pad that bolts to a driven steel angle.

**stake** (`STAKE-BASE`) — the driven steel angle at each base point. This is
what resists the dome spreading at its feet, through soil, the way a tent peg
does. Hardware to specify, not a shape to design.

**splice** (`SPLICE-d`) — the joint between two transport sections of one bow.

**termination** (`TERM-d`) — the end of a bow that a doorway cut has severed.

**generator** — the script that builds a part. A part in the connector schedule
with `generator: null` is specified but not yet buildable, and the schedule
says so rather than skipping it.

## The pipeline

**producer** — something that writes geometry: `stardome` (the source of truth)
and `tools/export_geometry.py` (the OpenSCAD reference). They never write the
same filenames — [decision 0003](decisions/0003-two-producers-never-share-a-directory.md).

**consumer** — something that reads `model.json` and recomputes nothing:
OpenSCAD's viewer, FreeCAD's generators, Blender's scene builders.

**parity** — the CI job that regenerates the OpenSCAD model from scratch and
compares it to the Python output field for field.

**golden** — a small committed scalar summary per variant in `tests/golden/`,
so a change in the maths is a readable diff rather than an 84 kB blob.

**invariant** — an executable claim about the built model, in
`stardome/verify.py`. `make check` must pass before any geometric result is
reported as true.
