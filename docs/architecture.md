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
script (`connectors/*.py`), not hand-modelled. The natural next step is for
the clamp generator to read `crossing_types` from `model.json` and emit one
part per class at that class's real angle, so "how many connector types does
this need" is answered by the data instead of by argument.

MCP is for interactive inspection. Anything that must be reproducible runs as
a script from the repository: if a result cannot be rebuilt with one command
from a clean clone, it is not a result.

## 4. Composition and ergonomics — Blender

Blender is the assembly and site-layout environment, never the geometric
source of truth.

The scene is built from `model.json` at 1:1 scale — rods as curves with a
real-radius bevel, objects named by rod and node ID — so entrances and
corridors are checked against actual rod positions rather than a generic
hemisphere.

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
