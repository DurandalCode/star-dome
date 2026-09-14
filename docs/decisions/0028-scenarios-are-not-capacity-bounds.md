# 0028. Treat closed-form calculations as diagnostic scenarios

- **Status:** accepted; supersedes the capacity-bounding interpretation of
  [0023](0023-the-strength-answer-is-a-band-until-the-frame-is-solved.md),
  the operating-limit interpretation of
  [0021](0021-wind-is-the-only-load-case.md), and
  the minimum-property guarantee assumed in
  [0022](0022-a-material-is-a-named-candidate-not-a-constant.md).
- **Date:** 2026-09-14
- **Where it lives:** `stardome/strength.py`, `loads.py`, `reactions.py`,
  `material.py`, `span.py`, [`docs/strength.md`](../strength.md)

## Decision

Report utilisations at a supplied wind speed, explicit pressure cases,
applicability flags and diagnostic criterion crossings. Do not publish an
operating wind speed or a guaranteed interval between beam and membrane
answers. Version the JSON contract to `star_dome_strength/2` and leave
`operational_limit_ms` null. Retain the old ADR as the historical decision.

## Evidence that changed the interpretation

1. A minimum stiffness is not a pessimistic material envelope for imposed
   curvature. At d=8 mm and R=2 m, E=50 GPa gives 100 MPa while E=60 GPa gives
   120 MPa, straddling the configured 112 MPa criterion.
2. The old membrane path dropped gravity although the load had been
   computed. Including bow and fabric gravity in a separate beam scenario
   already exceeds the default D6 sustained-tension criterion in calm.
3. Closed-door internal pressure needs both signs. Choosing only −0.3
   missed the +0.2 uplift case. The windward opening scenario now uses the
   ≥3 opening ratio factor 0.9 rather than the ratio-2 factor 0.75.
4. Global force divided by ten discards overturning. A rigid equal-spring
   ring gives Fz/n + 2M/(nr) at the aligned anchor, not Fz/n.
5. A removed middle interval was accidentally counted as a live span;
   geometry caching also reused tributary widths after a same-name resize.

These are reproducible implementation and reasoning errors. None establishes
how the real frame redistributes force, so fixing them does not turn a closed
form into a validated capacity prediction.

## Alternatives rejected and cost

Keeping the former positive wind band by excluding gravity or choosing only
helpful pressure signs would preserve a misleading result. Relabelling the
old material values as current standard guarantees would also invent evidence.
A complete nonlinear frame solver needs joint and stock data not yet present;
adding one without benchmarks would only move the uncertainty.

The chosen intermediate step preserves useful, testable calculations: live
span checks, separate compression and suction, gravity, full force/moment
anchor screening and material sensitivity. Its cost is loss of a convenient
single answer, intentional JSON incompatibility, and a larger computation
for all sampled wind directions. The benefit is a report whose claims match
its evidence. Physical properties, load paths and support stiffness still
need measurement and a validated frame model before field limits can be set.
