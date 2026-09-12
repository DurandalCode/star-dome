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

## Not here yet

Work on the `apply-cut` branch — the section splice, the transport length, the
wind screening figure — has decisions in it that will want records when it
lands. They are deliberately not written in advance: a record describes what
`main` does.
