# Decisions

One file per decision that would otherwise only be recoverable by reading a
closed pull request.

## Why this exists

The most valuable thing in this project is not the geometry — that can be
recomputed. It is the **reversals**: the places where a plausible approach was
tried, measured, and abandoned for a stated reason. OpenSCAD as the producer.
MCP as the way to drive the tools. A lancet door. D3 on a skirt. Spacing the
rods apart at the node. Every one of those was the obvious answer first, and
every one is now recorded only in the body of a merged pull request that a
clean clone cannot see and `grep` cannot reach.

A decision record is not documentation of how something works — `docs/` does
that, at length. It is a record of **what was chosen, what was rejected, and
what the choice costs**, so that the next person to have the rejected idea
finds out in thirty seconds that it was already tried.

## When to write one

Write a record when:

- a decision reverses an earlier one, or contradicts something a document
  already says;
- a plausible alternative was measured and lost, and the measurement is the
  reason;
- the choice constrains future work — a policy, an interface, a convention;
- someone would reasonably ask "why is it like that?" and the code cannot
  answer.

Do **not** write one for something a document already explains in place. The
architecture of the pipeline lives in `architecture.md`; the record only says
that it was a choice, against what, and why.

## Format

Numbered, four digits, never renumbered. Status is `accepted`, `superseded by
NNNN`, or `reversed by NNNN` — records are appended, never edited to say
something different from what was decided at the time. Correcting one means
writing the next.

```markdown
# NNNN. Title in the imperative

- **Status:** accepted
- **Date:** YYYY-MM-DD
- **Where it lives:** the files and documents this governs

## The decision
## Why
## What was rejected
## What it costs
```

## The record

| | decision | status |
|---|---|---|
| [0001](0001-python-is-the-geometry-source-of-truth.md) | Python owns the geometry; OpenSCAD is frozen as a second implementation | accepted |
| [0002](0002-reproducibility-runs-from-the-repository.md) | Anything reproducible runs as a script from the repo, not through MCP | accepted |
| [0003](0003-two-producers-never-share-a-directory.md) | Two producers never write the same filenames | accepted |
| [0004](0004-the-lashed-node-is-a-stack-of-plates.md) | The four-rod node is a stack of plates, not a bundle clamp | accepted |
| [0005](0005-the-rods-bear-on-each-other-at-the-node.md) | The rods bear on each other at the node centre; the plate is a cross | partly reverses 0004 |
| [0006](0006-a-superseded-design-is-frozen.md) | A superseded design is frozen, not deleted and not updated | accepted |
| [0007](0007-the-door-is-a-portal-not-a-lancet.md) | The door is a portal in a low bay, not the tall bay's lancet | reverses 0008's premise |
| [0008](0008-the-config-records-what-a-dome-admits.md) | M and L are bare by choice, and the config records what gets in | accepted |
| [0009](0009-d3-on-a-skirt-is-dominated.md) | D3 on a skirt is dominated by D4 on a skirt | accepted |
| [0010](0010-the-stacking-order-is-fan-order.md) | The radial stacking order at a lashed node is fan order, 1-2-3-4 | accepted |
| [0011](0011-the-pull-request-is-the-check-not-the-review.md) | The PR exists so the checks run elsewhere; never merge before they report | accepted |
| [0012](0012-mismatch-is-measured-against-bending.md) | A node mismatch is measured against the bending it forces | accepted |
| [0013](0013-the-bolt-is-half-the-rod.md) | The fastener is sized from the rod: half it, snapped to a standard bolt | accepted |
| [0014](0014-the-cover-hangs-on-the-stakes.md) | The cover hangs on the stakes the dome already stands on, with no new part | accepted |
| [0015](0015-a-reinforcement-is-judged-by-the-span-it-removes.md) | A reinforcement is judged by the span it removes, because the rod goes as the span squared | accepted |
| [0016](0016-a-domes-doors-are-written-in-its-config.md) | A dome's doors are written in its config and aimed by azimuth | accepted |
| [0017](0017-the-skirt-post-is-the-stake-made-longer.md) | The skirt post is the stake made longer, and the skirt's own members go on a collar | accepted |
| [0018](0018-a-camp-is-a-plan-and-a-dome-is-turned-not-redrilled.md) | A camp is its own config, and a dome is turned to face a neighbour rather than re-drilled | refined by 0019 |
| [0019](0019-a-camp-builds-its-own-domes.md) | A camp derives its doors and turns from its links; a door sits on a 72° grid | accepted |
| [0020](0020-the-hinge-is-worth-more-than-the-lever.md) | The clamp gains a hinged closure: one bolt instead of two, and nothing loose when it is open | accepted |
| [0021](0021-wind-is-the-only-load-case.md) | Wind is the only load case; the dome comes down before winter, so the answer is an operating limit | accepted |
| [0022](0022-a-material-is-a-named-candidate-not-a-constant.md) | A material is a named candidate with its source attached, and the reference is a standard's minimum | accepted |
| [0023](0023-the-strength-answer-is-a-band-until-the-frame-is-solved.md) | Strength reports two bounding readings, not one speed, until a frame solve closes the gap | accepted |
| [0024](0024-a-dome-is-cut-into-two-lengths.md) | A dome is cut into at most two section lengths, solved dome-wide rather than bow by bow | accepted |
| [0025](0025-the-angle-is-met-on-a-pad.md) | The base hub meets its driven angle on a flat pad with one bolt, not in a slot through the plate | fastening replaced by 0026 |
| [0026](0026-the-loop-is-bought-not-printed.md) | The angle is held by a bought U-bolt over the pad: any height, any leg up to the loop's span | the alternative since 0027 |
| [0027](0027-the-wrap-closes-the-fourth-side.md) | A fifth printed piece wraps the angle on three sides; the pad is the fourth, and the bolts are the same two | refined by 0028; replaced by 0031 |
| [0028](0028-join-the-wrap-ears-and-add-upper-stack-bolts.md) | The wrap ears join below the angle tip; two upper stack bolts bring the plate stack to four | refined by 0029 |
| [0029](0029-put-the-lower-stack-bolts-inside-the-base-plate.md) | A wide flange encloses the lower stack-bolt pair within every base plate | accepted |
| [0030](0030-bambu-studio-arranges-the-plates.md) | Print exports are Bambu Studio projects arranged by Bambu itself, for every part, not bed STLs for the hub | accepted |
| [0031](0031-the-stake-is-rebar-and-a-vee-takes-any-bar.md) | The stake is driven rebar, held by a vee cradle on the unchanged pad that takes any bar from 8 to 18 mm | replaces the wrap of 0027 and 0028 |

## Not here yet

Work on the `apply-cut` branch — the section splice, the transport length, the
wind screening figure — has decisions in it that will want records when it
lands. They are deliberately not written in advance: a record describes what
`main` does.
