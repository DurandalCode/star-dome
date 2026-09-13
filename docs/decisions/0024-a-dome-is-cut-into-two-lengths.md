# 0024. A dome is cut into at most two section lengths

- **Status:** accepted
- **Date:** 2026-09-13
- **Where it lives:** `stardome/connectors.py` (`_section_kit`, `splice_joints`,
  `section_kit`), `stardome/bom.py` (`materials`), `tests/test_connectors.py`

## The decision

The whole dome — every bow, both bow families, and the two bows a doorway cut
shortens — is cut from a kit of **at most two lengths**. One where one will do;
never three.

The kit is solved once per dome rather than bow by bow. Choosing how many
pieces of each length two stretches are made of gives two linear equations in
the two lengths, which fix them exactly; every candidate kit is then laid
against every stretch and its joints checked against every crossing. Of the
kits that survive, the one that cuts the dome into the fewest sections wins,
and ties go to the kit whose two lengths are closest together.

## Why

The constraint is logistical, not geometric. Sections are not a number in a
model: they are a bundle somebody straps to a roof rack, carries across a
field, and hands out in the dark. Telling them apart is done by eye against
the other sections in the bundle, and getting it wrong is a bow that will not
close — discovered at the far end of the bow, after the near end is up.

That reading was not what the geometry had been optimising for. Each bow was
divided evenly and each joint that landed on a crossing was then nudged the
shortest distance that cleared it. Per bow that is the best possible answer:
the most even division that is legal. Dome-wide it produced this:

| size | cut lengths before | |
|---|---|---|
| S · D4 | 2174, 2094, 2014, 1655 | four |
| M · D6 | 2356, 1862 | two |
| L · D8 | 2194, 2094, 1994, 1986 | four |
| XL · D10 | 2244, 2069 | two |
| D12 | 2356, 2214, 2147, 2128, 2094, 2089, 1974 | **seven** |

On S, 2094 and 2014 differ by 80 mm over two metres — four parts in one bag,
indistinguishable without a tape. D12 asked for seven, three of them inside
60 mm of each other. That is the opposite of design philosophy 2, *prefer a
small number of repeated parts over many unique parts*, applied to the part
there is most of.

Solved dome-wide instead:

| size | kit after | sections | splices |
|---|---|---|---|
| D3 | 2356 | 30 | 15 — unchanged |
| S · D4 | 2314, 1655 | 45 | 30 — unchanged |
| M · D6 | 2356, 1862 | 60 | 45 — unchanged |
| L · D8 | 2149, 1986 | 88 | 73 — unchanged |
| XL · D10 | 2244, 2069 | 103 | 88 — unchanged |
| D12 | 2188, 2048 | 131 | 116 — five more |

M and XL do not move: the even division already met the constraint, and the
solver takes the even answer when the even answer is legal. D3 collapses to a
single length. Every size anyone is asked to build pays **nothing** for this —
same section count, same splice count, same transport limit.

## What was rejected

**Keeping the per-bow nudge.** It is geometrically freer and the joints stay
closer to the even division. It is also what produced the four- and
seven-length cut lists above, and nothing about it can be told to stop: the
nudge is local, so each bow arrives at its own honest answer and the kit is
whatever falls out.

**Letting a section run past the transport length to unify.** A longer section
buys a lot of kits. It also defeats the only reason splices exist, so the
transport limit stays hard and is under test.

**A kit fixed across the size range.** One pair of lengths for S through XL
would be better still for a workshop that builds all four. It does not exist:
a bow is πR long and the crossings scale with it, so the lengths that close
D4 do not close D10. The scope is one dome.

## What it costs

**Joints sit further from the even division.** On S the worst is 220 mm off,
where the nudge managed 80. The division was never the requirement — clearing
the crossings is — and the clearances improved with it: S's tightest is now
102 mm against an 80 mm sleeve, L's 108 mm against 100 mm.

**A bow is no longer a repeating pattern.** L's full bows read
2149·2149·1986·1986·2149·2149, not six of anything. That is a marking and
assembly-order problem, which the field-marking milestone owns anyway; it is
a cheaper problem than four near-identical parts in a bag.

**D12 takes five more splices.** No two-length kit closes its bows in eight
sections, so the full bows go to nine. D12 is a research variant with no
alias and nobody is asked to build it.

**The solver can fail.** If no kit of two lengths clears every crossing it
raises rather than quietly emitting a third length. That is the intended
behaviour: a third length is a decision, not a fallback.
