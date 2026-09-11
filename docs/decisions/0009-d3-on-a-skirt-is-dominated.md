# 0009. Treat D3 on a skirt as dominated by D4 on a skirt

- **Status:** accepted
- **Date:** 2026-09-09
- **Where it lives:** `stardome/interior.py`, `docs/interior.md`

## The decision

D3 + 1600 mm is dominated by D4 + 1320 mm on every axis that matters. Choose D3 only when
the site is too small for 4 m.

| | standing room | of floor | overall | tip index | slenderness | rod |
|---|---|---|---|---|---|---|
| D3 + 1600 | 6.94 m² | 98% | 3073 mm | 0.939 | **1.03** | 96 m |
| D4 + 1320 | **11.84 m²** | 94% | 3284 mm | **0.740** | 0.83 | 120 m |

70% more standing room, a materially lower tipping index, 37% better rod efficiency, and
still wider than it is tall where D3 is not.

## Why

The earlier result — "a 3 m dome on a 1 m skirt has more than twice the standing room of a
bare 4 m dome" — is true, and it was the wrong comparison. It set a skirted dome against a
bare one. **The honest comparison is skirt against skirt**, each carrying the same door.

Once that is done, D3 pays for its smaller footprint twice: once in area and once in
stability.

## What was rejected

D3 as a small sleeping pod on 1300–1600 mm of skirt. Not eliminated — the 3 m footprint
and 96 m of rod against 120 m are real advantages — but it is a size chosen for a
constraint, not a size chosen on merit.

## What it costs

Nothing in the code; D3 stays in `configs/variants.toml`. What it costs is the earlier
headline, which was quoted for a day and was comparing the wrong two things.

Note for the next comparison of this kind: `tip_index` is the silhouette centroid height
over the base radius, dimensionless and comparable between variants. **It is a shape
comparison. There is no pressure coefficient in it and it proves nothing about safety.**
