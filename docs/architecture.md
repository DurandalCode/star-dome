# Project architecture

The project separates four concerns: the geometry itself, the parts that get
manufactured, the scene that gets composed, and the data contract that joins
them.

## 0. Geometry — Python (`stardome/`)

`stardome/` is the source of truth for dome geometry. It is pure standard
library, so it imports unchanged inside the Python interpreters bundled with
FreeCAD and Blender without installing anything.

It owns:

- the topology: 15 bows in three families, on 5 diametral axes;
- all derived angles, which follow from one icosahedral angle and the
  reference's rod marking diagram — nothing is a hand-placed coordinate;
- crossings, nodes, and the symmetry classes that determine how many
  genuinely different connectors the design needs;
- derived dimensions, rod schedule, tie marks;
- serialisation to the data contract below.

```bash
python3 -m stardome report --all      # derived dimensions
python3 -m stardome verify --all      # geometric invariants
python3 -m stardome build --all       # model.json + CSV tables
make check                            # verify + tests
```

### Why Python and not OpenSCAD

The dome's geometry is analytic: great semicircles on a sphere. None of
OpenSCAD's strengths (CSG, booleans on solids) are used, while the things
this project actually needs from its geometry layer — node IDs, tangents,
crossing angles, symmetry classes, JSON/CSV export, unit tests — are things
OpenSCAD cannot do without a text-scraping layer. It has no dictionaries, no
file output, no sort, and no way to read back what it produced.

Meanwhile two of the three downstream consumers, FreeCAD and Blender, are
already Python, as is anything later that touches cut lists, wind loads or a
bill of materials.

The OpenSCAD model in `dome/` remains a second, independent implementation of
the same maths. That is deliberate and useful: the two producers emit the same
schema and are compared field for field by
`tests/test_geometry.py::test_matches_openscad_export`. Agreement between two
implementations derived independently is stronger evidence than either alone,
and it has already earned its keep by catching a field-labelling bug that
connector generation would have inherited.

### The reference-implementation policy

Keeping two implementations is only cheap while the maths does not move, so
the split is fixed rather than left to judgement:

- `dome/star_dome.scad` is **frozen as a reference implementation of the
  baseline topology**. It is not dead code — CI regenerates it from scratch on
  every push and compares it to the Python output — but it does not grow.
- **Everything new goes only into `stardome/`**: transport sections and
  ferrules, cut lists, tension belts, the D12 reinforcement candidates, load
  inputs. None of it is sphere geometry, and none of it is expressible in
  OpenSCAD without another scraping layer.
- The parity test therefore covers the baseline dome permanently, and new work
  is covered by the invariants in `stardome/verify.py` and the golden
  snapshots instead.

The rule for resolving a disagreement: if the two ever diverge on the baseline
topology, `stardome/` is the one that is right, and the divergence is a bug in
whichever change caused it.

## 1. Data contract — `model.json`

Schema `star_dome_geometry/1`. This is the **only** interchange format.
Everything else — STL, GLB, STEP, 3MF, CSV — is derived from it and must never
be an input to an engineering decision.

| section | content |
|---|---|
| `meta` | variant, units, derived dimensions, stated conventions |
| `rods` | 15 bows: family, feet, azimuth, tilt, lengths, weave layer, tie marks |
| `base_nodes` | the 10 ground points and which 3 rods land at each |
| `nodes` | 40 distinct crossing points: 10 four-rod, 30 two-rod |
| `crossings` | 90 rod-to-rod contacts: point, tangents, angle, inclination, over/under |
| `crossing_types` | 12 symmetry-distinct crossing geometries |
| `doorway` | the chosen bay, its frame, and the opening's outline |
| `cover` | the fabric: radius, areas, gore layout; its mesh with `--polylines` |
| `corridor` | with `--corridor`: a tunnel on the doorway, and whether it fits |

Three rules keep the pipeline honest:

1. **JSON is the contract.** Meshes are pictures of the data, not the data.
2. **No consumer recomputes geometry.** If a Blender script calculates a
   crossing angle, that is an architecture bug.
3. **Anything reproducible from parameters stays out of Git**, except one small
   golden snapshot per variant in `tests/golden/` — scalars and the class table
   only, so a change in the maths shows up as a readable diff in review rather
   than an 84 kB blob.

`meta` carries its own conventions in words (`coordinate_basis`,
`inclination_convention`, `above_convention`) so a consumer cannot silently
misread the numbers.

### Where a number lives

Four homes, and the rule is what KIND of number it is.

| kind | home | example |
|---|---|---|
| variant-specific | `configs/variants.toml` | diameter, rod diameter, skirt, section limit |
| a material's properties | `stardome/materials.py` | GFRP density and modulus, fabric weight, sleeve moduli |
| derived from the topology | `stardome/geometry.py` | the family tilts, `MARKS_THIRDS`, `MARKS_FIFTHS` |
| a design decision | with the module that makes it | seam allowance, knee-brace leg, engagement length |

A variant **names** its materials rather than describing them, so two domes on
different rod diameters share one density instead of repeating it.

This exists because the same rod's density was once typed in two modules and
its modulus in a third: measuring the real stock would have meant editing
three places, and the mass in the rod report could stop agreeing with the mass
in the wind screening without anything noticing.
`tests/test_materials.py` walks the package's syntax tree and fails if any
module defines a constant whose name says "material property" and whose value
is a literal.

The same trap has a second form that a catalogue does not fix: a **derivation**
duplicated. The section count was worked out three different ways in three
modules before the transport limit changed and they disagreed. That one is
fixed by one function, not one file.

### Where generated files go

The two producers write to separate directories, and must keep doing so:

| directory | written by | read by |
|---|---|---|
| `exports/model/` | `stardome` — the source of truth | FreeCAD, Blender, everything downstream |
| `exports/geometry/` | `tools/export_geometry.py` — the OpenSCAD reference | the parity tests only |
| `exports/connectors/` | `connectors/generate_clamps.py` | slicers, the workshop |
| `exports/blender/` | `blender/build_scene.py` | people |

They shared `exports/geometry/` briefly, and the effect was exactly what you
would expect: a Blender rebuild overwrote the OpenSCAD reference with Python
output and the parity tests started comparing the Python model against itself.
Two producers must never write the same filenames.

### Divergences from the OpenSCAD exporter

Parity is exact across all four variants for every rod, node, crossing and
`meta` field, with one deliberate exception.

In `crossing_types`, `tools/export_geometry.py` labels `family_a`/`family_b`
from the sorted signature while taking `t_a`/`incl_a` from the representative
crossing's own rod order. For the two L/U classes (T05 and T10) those orders
disagree, so its "a" columns pair one rod's family with another rod's angles.
`stardome/` reports every per-rod field in the representative's order, matching
`example_rods`. Connector generation reads exactly these fields, so the
inconsistent labelling is worth not inheriting.

## 2. Structural preview — OpenSCAD

`dome/` renders the dome for visual inspection and carries the written
derivation of the geometry in `dome/README.md`, which is the best explanation
of *why* the design is what it is.

Its role going forward is viewer and cross-check, not producer.

## 3. Manufactured parts — FreeCAD

FreeCAD is used for parts that must be printed or dimensioned precisely:

- crossing clamps;
- base/anchor interfaces;
- belt clips;
- corridor/entrance transition parts.

These are parametric around rod diameter and print clearance, and driven by
script (`connectors/*.py`), not hand-modelled.

The clamp generation chain is:

```bash
python3 -m stardome connectors D6            # what parts are needed, and why
python3 -m stardome connectors D6 --json     # the schedule as data
<FreeCAD> connectors/generate_clamps.py      # build and export them
```

`stardome/connectors.py` groups every crossing into the part that would serve
it, so "how many connector types does this dome need" is answered by the data
rather than by argument. `connectors/generate_clamps.py` is a consumer: it
reads that schedule, drives `crossing_clamp_v1.py` once per part at that part's
real crossing angle, and exports STEP plus a slicer-sized STL into
`exports/connectors/`. It computes no dome geometry of its own.

The schedule reports what it cannot build instead of quietly skipping it: each
part carries a `generator`, and a part with `generator: null` is specified but
not yet buildable.

For the baseline topology the schedule comes to **two connector geometries**:
a four-rod fan at the 10 lashed nodes, and one two-rod clamp covering all 30
unlashed crossings. `stardome/weave.py` derives the fan — the four rods at a
lashed node are coplanar, so the node is flat, and all ten nodes are the same
shape. It also enumerates the radial stacking orders with the rod-on-rod
contacts each creates, and records the one the project chose. See
[`tied-node.md`](tied-node.md).

```bash
python3 -m stardome weave D6
```

MCP is for interactive inspection. Anything that must be reproducible runs as
a script from the repository: if a result cannot be rebuilt with one command
from a clean clone, it is not a result.

### What the generators share, and what they must not

`connectors/kit.py` holds the CAD primitives every part needs — rod and plate
solids, hex sockets, edge filleting, the printability check, the parameter
spreadsheet, STEP/STL export. `blender/kit.py` does the same for the two scene
builders. Neither knows anything about the dome: geometry reaches them as
numbers `stardome/` derived.

What stays in each part is the part — `build`, `verify`, `derived_rows`,
`populate`, and the channel and plate shapes that give a connector its
character. Those share names across the generators but only 2–40% of their
text, and merging them would trade a hundred lines for the ability to read any
one part start to finish.

Extraction is not mechanical, because a shared name is not a shared meaning.
Three of the base hub's helpers looked like the fan node's and were not: its
fan is open, so *n* gaps give *n*+1 arms where the node's closes on itself; its
bows *end* at the hub, so the solid is a ray rather than a centred cylinder;
and its validity check asks "did these two things meet at all", where
intersecting a rod with a plate legitimately lands two or three lumps, not one
solid. Each pair is two names in the kit rather than one function with a flag.

**`connectors/fan_node_v1.py` imports none of this.** It is frozen as a record
of the superseded bundle-clamp design, for the same reason
`dome/star_dome.scad` is frozen as a reference implementation: a later change
to the kit must not be able to rewrite what an earlier design actually was.
A superseded part is documentation, and documentation that silently follows
the current code is not a record of anything.

## 4. Composition and ergonomics — Blender

Blender is the assembly and site-layout environment, never the geometric
source of truth.

The scene is built from `model.json` at 1:1 scale by `blender/build_scene.py`:

```bash
make blender            # D6 by default
make blender V=D12
```

Rods become poly curves bevelled at the real rod radius, coloured by family;
objects carry their model IDs (`Rod_G1`, `Node_N07`, `Base_b0`) so a
regenerated variant can be matched against an existing scene. Tied nodes,
unlashed crossings, base points and site objects each get their own
collection. The model is in millimetres and the scene is metres, built 1:1, so
a 1.8 m doorway and the 1.75 m scale figure measure correctly against the
rods — which is the entire reason to do this in Blender rather than eyeball it.

The scene builder requires a model generated with `--polylines
--weave-mode layered`. In flat mode all 15 centrelines lie on one sphere and
every crossing has two rods occupying the same space, which makes a clearance
check meaningless; the script warns if given one. Rod centreline points come
from the model rather than being recomputed from azimuth and tilt, so Blender
stays a pure consumer.

Typical checks:

- can a 1.8–2.2 m tall opening fit between structural members;
- does a corridor intersect rods or covers;
- human-scale circulation around dome edges;
- visual and practical composition of several domes.

## Data flow

```text
configs/variants.toml
        |
        v
stardome/                     <- geometry source of truth
        |
        v
exports/<variant>/model.json  <- schema star_dome_geometry/1
        |
        +--> dome/            OpenSCAD viewer + independent cross-check
        +--> connectors/      FreeCAD: one part per crossing class
        +--> blender/         1:1 site composition
        +--> *.csv            flat views for humans and spreadsheets
```

## Cost constraint

The baseline stack must not require paid CAD subscriptions or paid cloud
rendering/CAD APIs. The intended external paid capability is limited to
whatever Claude Code / Codex access the user already has.

`stardome/` has no third-party dependencies at all; `pytest` is needed only to
run the test suite.
