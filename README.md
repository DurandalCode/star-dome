# Star Dome Lab

Parametric design workspace for experimental Star Dome structures based on the Takekawa-style concept: long continuous flexible members, simple crossing joints, fast assembly, and fabric covers.

## Goals

- Build a family of domes around 4 m, 6 m, 8 m, and 10–12 m diameter.
- Keep assembly fast enough for temporary role-playing event structures.
- Use round fiberglass rods/tubes as the primary structural members.
- Explore reinforcement strategies for very large domes without losing assembly simplicity.
- Design printable crossing, base, belt, and corridor-interface connectors.
- Compose multiple full-detail domes and covered corridors in Blender at real scale.
- Keep the toolchain local and free apart from the AI clients already used by the project.

## Toolchain

- **OpenSCAD** — parametric dome geometry and generated structural variants.
- **FreeCAD** — printable connectors, tolerances, hardware interfaces, STEP/STL/3MF output.
- **Blender** — site composition, real-scale arrangement, entrances, corridors, covers, people, and visual clearance checks.
- **Claude Code / Codex** — agent clients driving the local tools through MCP.
- **GitHub** — source control and design history.

No paid CAD subscription is required by the intended workflow.

## Repository layout

```text
docs/           design notes, geometry, construction, references
configs/        named dome variants
dome/           OpenSCAD parametric geometry
connectors/     FreeCAD-oriented connector design areas
blender/        integration scripts and scene workflow
exports/        generated output; mostly ignored by Git
```

## Initial variants

- D4 — small experimental dome
- D6 — reference prototype
- D8 — large dome
- D12 — XL / physical-limit research variant

The D12 variant is explicitly experimental. Wind loading, anchoring, cover behavior, rod buckling/bending, and connector loads must be validated before real-world use.

## Reference concept

Primary inspiration: SimplyDifferently Star Dome / Takekawa-style Star Dome geometry.

https://simplydifferently.org/Star_Dome?page=0
