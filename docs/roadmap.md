# Roadmap

This roadmap is intentionally prototype-first. The project should prove geometry, assembly, and connector behavior on smaller variants before treating XL variants as buildable structures.

## Milestone 0 — Workspace and toolchain

**Goal:** establish a reproducible local workflow with no required paid CAD services.

- [x] Repository skeleton.
- [x] Tool responsibilities documented: OpenSCAD / FreeCAD / Blender.
- [x] Agent guidance in `AGENTS.md`.
- [ ] Confirm working MCP setup for OpenSCAD.
- [ ] Confirm working MCP setup for FreeCAD.
- [ ] Confirm working MCP setup for Blender.
- [ ] Document local setup on macOS.

**Exit criterion:** an agent can generate/edit geometry in all three applications locally.

## Milestone 1 — Reference Star Dome geometry

**Goal:** reproduce the baseline Takekawa-style Star Dome as a parametric model.

- [x] Implement the base Star Dome topology in OpenSCAD.
- [x] Parameterize dome diameter and rod diameter.
- [x] Generate the D6 reference variant first.
- [x] Identify and name arcs, base points, and crossing points.
- [x] Add simple geometry checks and derived dimensions.
- [x] Generate D4, D8, and D12 research variants from the same model.

**Exit criterion:** all named variants are generated from one source model without hand-editing geometry. **Met.** See [`dome/README.md`](../dome/README.md).

The 15 bows resolve into three families of 5: family G at tilt `atan(2)` (the icosidodecahedron's equatorial decagons, marked in fifths) and families U and L at 79.1877 deg and 37.3774 deg (marked in thirds), giving 3 rod ends at each of the 10 base points and 10 tied nodes of 4 rods each. Symmetry group D5.

Two results matter for later milestones:

- **Four rods meet at every tied crossing**, not two. Milestone 3's crossing connector has to handle that, at three distinct crossing angles. Verify against photographs and a physical mock-up before designing the part.
- **Every bow is bent to a radius equal to the dome radius** (2000 mm for D4 up to 6000 mm for D12), so minimum bend radius is a direct constraint on rod selection, not an afterthought.

An engineering geometry report is generated from the same model by
`tools/export_geometry.py` into `exports/geometry/` (JSON + CSV): every rod-to-rod
crossing with coordinates, tangents, angles, inclinations, over/under and symmetry
class. The exporter contains no geometry of its own; OpenSCAD stays the single
source of truth.

Rod diameters in `configs/variants.scad` remain provisional engineering assumptions. Nothing structural has been validated.

## Milestone 1.5 — Geometry core and data contract

**Goal:** give Milestones 2 and 3 something machine-readable to consume, and put the geometry somewhere it can be unit-tested.

- [x] Move the geometry to a dependency-free Python package, `stardome/`.
- [x] Move variant configuration to `configs/variants.toml`.
- [x] Emit schema `star_dome_geometry/1` as `model.json` plus flat CSV views.
- [x] Turn the `dome/README.md` validation table into executable invariants (`stardome verify`).
- [x] Commit one small golden summary per variant under `tests/golden/`.
- [x] Cross-check the Python and OpenSCAD producers field for field.
- [x] Freeze `dome/star_dome.scad` as a reference implementation and run the cross-check in CI on every push.
- [ ] Add a `blender/` scene builder that reads `model.json`.
- [ ] Add a FreeCAD clamp generator that reads `crossing_types`.
- [ ] Retire `configs/variants.scad` in favour of `configs/variants.toml`, or generate one from the other.

**Exit criterion:** every downstream tool reads geometry from `model.json` and none of them recompute it. **Partly met** — the producer, contract, tests and cross-check exist; Blender and FreeCAD are not yet wired up.

`dome/star_dome.scad` deliberately keeps computing its own geometry: that independence is the whole value of the cross-check. It is frozen rather than converted into a data consumer, so the baseline topology stays under permanent two-implementation verification while all new work goes into `stardome/` alone. See [`docs/architecture.md`](architecture.md), "The reference-implementation policy".

Why this milestone exists: the geometry here is analytic, and the deliverables that Milestones 2 and 3 actually need — node IDs, tangents, crossing angles, symmetry classes, exported as JSON — are the things OpenSCAD cannot produce without a text-scraping layer. Two of the three consumers are already Python. See [`docs/architecture.md`](architecture.md).

The two producers agree exactly on all four variants for every rod, node, crossing and `meta` field. The one deliberate divergence is `crossing_types.family_a`/`family_b` in the two L/U classes, where the OpenSCAD exporter's labels and its angle columns refer to different rods; the Python output is self-consistent. Connector generation reads those fields, so this matters.

## Milestone 2 — Blender integration and human-scale composition

**Goal:** use real generated structural geometry for spatial planning.

- [ ] Export/import the generated dome geometry into Blender at 1:1 scale.
- [ ] Keep individual arcs/crossings identifiable where practical.
- [ ] Add reusable human scale figures.
- [ ] Add basic fabric-cover representation.
- [ ] Build an entrance-clearance inspection workflow.
- [ ] Build a simple covered-corridor generator / placement workflow.
- [ ] Create a composition scene with multiple D4/D6/D8/D12 instances.

**Exit criterion:** entrances and corridors can be positioned against the actual rod layout and inspected from human eye level.

## Milestone 3 — First printable crossing connector

**Goal:** replace rope/lashing at a representative crossing with a fast reusable printed connector.

- [ ] Choose reference fiberglass rod diameter(s), initially 8 and/or 10 mm.
- [ ] Measure real rod tolerance and surface behavior.
- [x] Design a crossing clip/clamp in FreeCAD. V1 two-piece bolted clamp, see `docs/crossing-clamp-v1.md`.
- [x] Avoid sharp contact edges and point loading on fiberglass. Flared mouths, 180 deg saddles; rod-on-rod contact at the crossing is still to be validated.
- [x] Make clearance, rod diameter, wall thickness, and fastener dimensions parametric. 8/10/12 mm variants generate from one parameter set.
- [ ] Print and test repeated assembly/disassembly.
- [ ] Record failure modes and revise.
- [ ] Reconcile the clamp with the generated crossing geometry (see below).

**Geometry constraints the connector has to meet.** From the Milestone 1 model,
regenerate with `tools/export_geometry.py`:

- There are **40 distinct crossing points**, not 20: 10 where **four** rods pass
  through one point and 30 where two do. Clamp V1 is a two-rod part.
- There are **90 rod-to-rod contacts** in **12 symmetry-distinct geometries**, at
  **five distinct crossing angles**: 37.3774, 41.8103, 63.4349, 70.5288 and
  79.1877 deg. A part that assumes one angle will not fit.
- The 60 lashed contacts use four of those angles; all 30 unlashed contacts are at
  70.5288 deg = `acos(1/3)`.
- Rod inclination at a crossing ranges from 4.7 to 65.4 deg above horizontal, so
  the clamp cannot assume the rod pair sits in a convenient plane.

The four-rod nodes are a reconstruction, not a quoted fact from the reference;
verify against photographs or a physical mock-up before committing to a part.

**What the connector schedule says.** `python3 -m stardome connectors D6` groups
every crossing into the part that would serve it, and the answer is awkward:

- The 30 unlashed crossings are two-rod contacts at **one** angle, so a single
  clamp geometry covers all of them. `connectors/generate_clamps.py` builds it
  from the model data and exports STEP + STL.
- The 10 lashed nodes join four rods and are **not covered at all** by the V1
  architecture.

So V1 currently solves the crossings the reference leaves alone, and does not
solve the ones it ties. Closing that is the real content of this milestone.

- [ ] Decide whether the 30 unlashed crossings want clamps at all, or whether effort belongs entirely at the four-rod nodes.
- [ ] Decide the radial stacking order at a four-rod node. It is currently a drawing convention (`above_convention` in the model meta), not a build decision, and a four-rod part cannot be designed without it.
- [ ] Design a four-rod node connector, or a scheme that splits one node into stacked two-rod clamps.

**Exit criterion:** one connector can be assembled repeatedly in the field without damaging the rod or requiring fiddly hardware.

## Milestone 4 — D4/D6 physical prototype

**Goal:** validate the basic system before scaling up.

- [ ] Build a partial full-scale star / crossing mockup.
- [ ] Build D4 or D6 complete frame.
- [ ] Measure assembly time and crew size.
- [ ] Check shape repeatability and connector movement under load.
- [ ] Test cover fit and entrance placement.
- [ ] Test base restraint / anchoring concept under controlled conditions.
- [ ] Feed measured geometry and problems back into CAD.

**Exit criterion:** a complete small/reference dome can be assembled, covered, dismantled, and reassembled predictably.

## Milestone 5 — Connector family and interfaces

**Goal:** keep field assembly simple while supporting a complete temporary structure.

- [ ] Base / ground connector.
- [ ] Crossing connector family for chosen rod sizes.
- [ ] Belt / tension-member attachment.
- [ ] Cover attachment that does not concentrate load on one printed part.
- [ ] Entrance / corridor interface connector.
- [ ] Labeling or keying system for field assembly.

**Exit criterion:** the structure needs only a small, understandable family of repeated printed parts.

## Milestone 6 — D8 large variant

**Goal:** find the practical upper range of the mostly-classic Star Dome system.

- [ ] Select rod/tube size from measured prototype behavior rather than simple geometric scaling.
- [ ] Analyze free spans and deformation.
- [ ] Evaluate lower perimeter tension belt.
- [ ] Evaluate one additional circumferential / stabilizing belt.
- [ ] Validate anchoring strategy and cover load paths.
- [ ] Build only after structural assumptions have been reviewed and tested appropriately.

**Exit criterion:** determine whether D8 is viable with the baseline topology plus minimal repeated reinforcement.

## Milestone 7 — XL topology research: D10–D12

**Goal:** explore how far the fast-assembly concept can scale without pretending the baseline design scales directly.

Candidate reinforcement strategies to compare:

- perimeter tension ring / belt;
- one or more circumferential stabilizing belts;
- additional repeated reinforcement arcs;
- denser secondary Star Dome lattice;
- partial double lattice;
- fiberglass tube instead of solid rod;
- dedicated entrance/corridor framing;
- distributed cover webbing that transfers wind loads to anchor points.

For every candidate, compare:

- part count;
- number of unique part types;
- field assembly actions;
- assembly time;
- transport volume/length;
- largest unsupported span;
- likely failure modes;
- anchoring demands;
- interaction with entrances and corridors.

**Exit criterion:** select one XL concept worth detailed engineering, or establish a practical size ceiling below 10–12 m.

## Milestone 8 — Structural validation and field rules

**Goal:** turn promising prototypes into a documented temporary-structure system.

- [ ] Define material properties from actual supplier data / testing.
- [ ] Establish load cases, especially wind and cover loads.
- [ ] Validate rods/tubes, connectors, belts, base points, and anchors.
- [ ] Define weather / wind operating limits.
- [ ] Define inspection and retirement criteria for fiberglass and printed parts.
- [ ] Write assembly, anchoring, evacuation, and dismantling instructions.

**Exit criterion:** build/no-build decisions are based on explicit engineering limits rather than visual confidence.

## Near-term priority

The next concrete path is:

1. finish MCP/local-tool setup;
2. generate the baseline D6 Star Dome in OpenSCAD;
3. import that exact geometry into Blender;
4. inspect entrance locations with a human-scale figure;
5. design and print one representative crossing connector;
6. only then make decisions about rod diameter and XL reinforcement from measured behavior.
