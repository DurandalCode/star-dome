# 0012. Measure a node mismatch against the bending it forces, not against the rod diameter

- **Status:** accepted
- **Date:** 2026-09-11
- **Where it lives:** `stardome/tolerance.py` (`--criterion`), `docs/tolerance.md`

## The decision

A node spread `s` sprung across a span `a` is judged by the curvature it forces,
`2s/a²`, expressed as a fraction of the `1/R` the rod is already holding. The default
budget is 10%. The span comes from the marking scheme, because a rod is held at its feet
and its tie marks and nowhere else.

The older criterion — the four marks at a node must land within a rod diameter of each
other — is kept as `--criterion overlap` and labelled as the question a connector drawing
asks, not as a limit.

## Why

The overlap criterion was chosen because it was a tidy geometric landmark, and it is not a
failure mode. **A mark is a build aid, not a stop.** The connector seats where the four
rods agree to cross, not on anybody's mark; the rods run straight through it and slide in
their channels. Nothing fails when the marks stop overlapping.

It asks for roughly ten times the care, and it produced a recommendation that was simply
wrong: that the ground needed a template rather than a tape. Under the curvature
criterion a casual tape-measure build — 32 mm of spread on M — costs 5.4% of the bend the
rod is already carrying, and the pegs want ± 14 mm.

The second thing it got wrong was the scaling. The allowance is `budget × span² / 2R` and
the span is proportional to `R`, so the tolerance is **proportional to the dome** — about
one part in 215 of the radius at every size. Pinning the target to the rod diameter, which
does not scale with the dome, made it look absolute and made the small variants look four
times harder. They are not, on this axis. (They are on the assembly axis, for an unrelated
reason — `docs/assembly.md`.)

## What was rejected

Baking either criterion in as a constant. The two differ by an order of magnitude, so the
choice is the answer and it belongs in the interface.

## What it costs

`2s/a²` holds the two neighbouring nodes rigid, so it is a worst case — a real frame
spreads the displacement over several spans and pays less. And 10% is a judgement, not a
limit. Where the limit actually sits needs the strength and ultimate strain of real stock,
which is milestone 3's one open item that depends on nothing else, and which this makes
more worth doing rather than less.
