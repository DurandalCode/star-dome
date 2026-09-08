# Agent instructions

This repository is a physical-design workspace for temporary Star Dome structures.

## Design philosophy

1. Preserve fast assembly as a first-class requirement.
2. Prefer a small number of repeated parts over many unique parts.
3. Keep dome geometry parametric and reproducible.
4. Treat Blender as the integration / composition environment, not the geometric source of truth.
5. Treat OpenSCAD as the source of truth for generated dome geometry.
6. Treat FreeCAD as the source of truth for manufactured connector geometry.
7. Work in millimetres for CAD and exported geometry unless a tool requires otherwise.
8. Keep real-world safety assumptions explicit. Do not claim a structural variant is safe without calculations/tests.
9. Preserve the original Star Dome fast-assembly idea when adding reinforcement: add repeated systems before adding unique nodes.
10. Prefer local/free tooling and avoid introducing services that require extra paid subscriptions.

## Current concept

- Takekawa-style Star Dome topology.
- Long continuous round fiberglass members pass through/cross at joints.
- Printed connectors should clamp or locate crossings without creating sharp stress concentrations.
- Small variants target ~4 m diameter, reference prototype ~6 m, large ~8 m, XL research ~10–12 m.
- The XL design may add reinforcement arcs, belts, anchoring, or a denser secondary lattice while preserving simple repeated assembly actions.
- Blender scenes must use the actual generated dome geometry when evaluating entrances, corridors, clearances, and human scale.

## Tool responsibilities

### OpenSCAD
- Generate dome centerlines and printable/mesh previews of rods.
- Keep diameter, rod diameter, reinforcement scheme, and named variants parameterized.
- Export geometry for Blender integration.
- Expose stable names/IDs for arcs and crossings where practical so downstream tooling can reason about entrances and interfaces.

### FreeCAD
- Design crossing clamps, base nodes, belt attachments, and corridor interfaces.
- Use parameters for rod diameter, clearance, wall thickness, fastener dimensions, and print tolerances.
- Prefer connector families driven by a small set of parameters rather than unique hand-modeled parts.

### Blender
- Import generated full-detail dome geometry at 1:1 scale.
- Build covers, entrances, and covered corridors against the actual rod layout.
- Place human-scale figures and furniture for clearance/ergonomics checks.
- Keep imported structural geometry replaceable so regenerated variants can update the scene.

## Roadmap discipline

- Read `docs/roadmap.md` before starting substantial work.
- Keep work aligned with the earliest incomplete milestone unless the user explicitly asks to jump ahead.
- Update the roadmap when a milestone is materially completed or when a design decision changes the plan.
- Do not mark structural validation complete based only on visual inspection or CAD geometry.

## Repo hygiene

- Do not commit generated STL/3MF/OBJ/GLB exports unless there is a specific reason.
- Prefer source files, scripts, configs, and documentation in Git.
- Keep large Blender caches, renders, temporary meshes, and slicer output out of Git.
- Record non-obvious design decisions in `docs/` rather than only in commit messages.
