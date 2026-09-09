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

- [ ] Implement the base Star Dome topology in OpenSCAD.
- [ ] Parameterize dome diameter and rod diameter.
- [ ] Generate the D6 reference variant first.
- [ ] Identify and name arcs, base points, and crossing points.
- [ ] Add simple geometry checks and derived dimensions.
- [ ] Generate D4, D8, and D12 research variants from the same model.

**Exit criterion:** all named variants are generated from one source model without hand-editing geometry.

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
