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
python3 -m stardome assembly --all    # the order the bows go up in
python3 -m stardome tolerance --all   # what the tape measure has to achieve
make venv && make check               # invariants + test suite
```

`stardome/` has no third-party dependencies; `pytest` is needed only for the
tests. `exports/<variant>/model.json` (schema `star_dome_geometry/1`) is the
single interchange format every other tool reads — see
[`docs/architecture.md`](docs/architecture.md).

## Project guidance

- Agent instructions: [`AGENTS.md`](AGENTS.md)
- Why it is like that: [`docs/decisions/`](docs/decisions/README.md)
- What the words mean: [`docs/glossary.md`](docs/glossary.md)
- Roadmap: [`docs/roadmap.md`](docs/roadmap.md)
- Dome geometry: [`dome/README.md`](dome/README.md)
- Crossing clamp V1: [`docs/crossing-clamp-v1.md`](docs/crossing-clamp-v1.md)
- Connectors on the dome: [`docs/placement.md`](docs/placement.md)
- The doorway: [`docs/doorway.md`](docs/doorway.md)
- How much room you get: [`docs/interior.md`](docs/interior.md)
- The fabric cover: [`docs/cover.md`](docs/cover.md)
- The covered corridor: [`docs/corridor.md`](docs/corridor.md)
- Putting it up: [`docs/assembly.md`](docs/assembly.md)
- How accurately to measure it: [`docs/tolerance.md`](docs/tolerance.md)

## Sizes

Four sizes are a chosen build -- skirt settled, doorway settled -- and carry a
short name. Either name loads the same dome.

| | dome | skirt | overall | clear opening | you get in |
|---|---|---|---|---|---|
| **S** | D4 | 1350 mm | 3.31 m | 1210 mm over the skirt | everything, up to a 2.2 m character |
| **M** | D6 | none | 2.95 m | 1816 mm | carrying something, but not 800 mm wide and not 2.2 m tall |
| **L** | D8 | none | 3.93 m | 2423 mm | everything, up to a 2.2 m character |
| **XL** | D10 | none | 4.91 m | 3029 mm | everything, with room to spare |

Every one of them walks in, because the door is a portal cut into a low bay
rather than the tall bay's pointed arch — 2.8% of the rod, nothing severed.
**M is the only built size that turns anything away**: the 800 mm-wide
silhouette and the 2.2 m character do not fit it.

M, L and XL are bare by choice. Only S has a skirt, and it is there for
standing floor area rather than for the door — a 4 m dome is 19% usable bare.

D3 and D12 stay in `configs/variants.toml` without a short name: they are the
ends of the range, kept for study rather than to build. See
[`docs/doorway.md`](docs/doorway.md) for where each skirt height comes from.

The full geometric family is D3, D4, D6, D8, D10 and D12 — one entry per
diameter, nothing else fixed. D12 in particular is explicitly experimental:
wind loading, anchoring, cover behaviour, rod buckling and bending, and
connector loads must all be validated before any real-world use, and at 5.9 m
tall it is a serious thing to stand up by hand.

## Reference concept

Primary inspiration: SimplyDifferently Star Dome / Takekawa-style Star Dome geometry.

https://simplydifferently.org/Star_Dome?page=0
