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
docs/           design notes, roadmap, architecture, references
configs/        named dome variants (variants.toml is the source of truth)
stardome/       Python geometry core — source of truth for the dome maths
tests/          invariants, golden summaries, OpenSCAD parity checks
dome/           OpenSCAD model: viewer and independent cross-check
connectors/     FreeCAD-oriented connector design areas
blender/        integration scripts and scene workflow
exports/        generated output; ignored by Git
```

## Generating the geometry

```bash
python3 -m stardome report --all      # derived dimensions per variant
python3 -m stardome verify --all      # geometric invariants
python3 -m stardome build --all       # model.json + CSV into exports/model
make venv && make check               # invariants + test suite
```

`stardome/` has no third-party dependencies; `pytest` is needed only for the
tests. `exports/<variant>/model.json` (schema `star_dome_geometry/1`) is the
single interchange format every other tool reads — see
[`docs/architecture.md`](docs/architecture.md).

## Project guidance

- Agent instructions: [`AGENTS.md`](AGENTS.md)
- Roadmap: [`docs/roadmap.md`](docs/roadmap.md)
- Dome geometry: [`dome/README.md`](dome/README.md)
- Crossing clamp V1: [`docs/crossing-clamp-v1.md`](docs/crossing-clamp-v1.md)

## Initial variants

- D4 — small experimental dome
- D6 — reference prototype
- D8 — large dome
- D12 — XL / physical-limit research variant

The D12 variant is explicitly experimental. Wind loading, anchoring, cover behavior, rod buckling/bending, and connector loads must be validated before real-world use.

## Reference concept

Primary inspiration: SimplyDifferently Star Dome / Takekawa-style Star Dome geometry.

https://simplydifferently.org/Star_Dome?page=0
