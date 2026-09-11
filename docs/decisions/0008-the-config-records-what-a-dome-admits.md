# 0008. Leave M and L bare, and record what a dome admits rather than what it is sized for

- **Status:** accepted
- **Date:** 2026-09-09
- **Where it lives:** `configs/variants.toml` (`door`, `admits`), `stardome/doorway.py`, `docs/doorway.md`

## The decision

M (D6) and L (D8) have no skirt, by choice. S (D4) keeps 1350 mm because a 4 m dome
without one admits nothing at all, not even a crawl. XL (D10) needs none.

The model reports `admits` — **every silhouette that gets through** — not just whether the
chosen one squeaks past.

## Why

A skirt is the cheapest way to buy standing room and a walk-in door, and it is not free:
it raises the tipping index, it is the part that has to be braced, and it stops the thing
reading as a dome. Taking it off the middle of the range is a deliberate trade, and the
honest way to carry that trade is to make the config say what you actually get rather than
what was wanted.

**Naming only the chosen silhouette hid both failures and headroom.** A variant that
admits nothing looked the same in the data as one that admits everything, because the
field recorded an intention.

The new `tall` silhouette, 700 × 2200, exists for the same reason: a costumed character on
stilts or in a frame is not a person, and 1.8 m is not the test a live event actually
applies. **XL takes it bare by 31 mm** and nothing smaller takes it at all.

## What was rejected

Giving every size the skirt its walk-in door would need. That is what
[0009](0009-d3-on-a-skirt-is-dominated.md) priced, and it turns the middle of the range
into something taller and windier than the room it buys is worth.

## What it costs

A bare D6 is a dome you enter on all fours, and a bare D8 is one you duck into — until
[0007](0007-the-door-is-a-portal-not-a-lancet.md) put the door in the other bay, after
which both walk in. The decision survived the thing that changed its premise, which is
worth noting: it was a decision about skirts, not about doors.
