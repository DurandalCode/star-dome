# 0007. Put the door in a low bay, as a portal with a lintel

- **Status:** accepted; supersedes the tall-bay lancet
- **Date:** 2026-09-09
- **Where it lives:** `stardome/doorway.py`, `configs/variants.toml` (`door_cut = "portal"`), `docs/doorway.md`

## The decision

The door goes in one of the five **low** bays, not one of the five tall ones. A low bay is
bounded by two U bows rising from adjacent base points and, across the top, one L bow
lying nearly level between two crossings at the same height — a doorway with a *lintel*,
whose head stands at **0.3009 of D** against the lancet's 0.2629.

What fills it is a second pair of L bows crossing low in the middle. Each gives up its end
piece and the piece past that crossing; both spans run contiguously to a bow end, so
**neither bow is severed** — each simply starts higher up. 2.8% of the rod, nothing cut in
two, no node left with nothing running through it.

## Why

The door was in the wrong bay. Everything measured before this — that a walk-in entrance
does not exist below D10, that D6 needs 760 mm of skirt, that D3 does not work — was
measured against the tall bay, and the tall bay is not the best opening the dome has.

| | clear | 1800 wide | admits |
|---|---|---|---|
| M lancet, jambs cut | 1563 mm | 0 | stoop |
| **M portal** | **1816 mm** | **942 mm** | **carry** |
| L portal | 2423 mm | 1641 mm | tall |

## What was rejected

- **The tall bay uncut**, and **the tall bay with its jambs cut out.** Both are still
  computed and still testable; `door_cut` takes `none`, `jambs`, `head` or `portal`.
- **Cutting only the legs of the filling crossing**, which does nothing at all — the next
  piece up still slants across the opening. That is why an earlier measurement called
  cutting there worthless.

A greedy piece-by-piece search cannot find this cut, because neither bow helps until both
are taken. Worth remembering before trusting the next incremental search.

## What it costs

**The margin on M is 16 mm** — 1816 mm of clear height against an 1800 mm silhouette.
That is an accident, not a margin, and it stops being true as soon as a cover is hemmed
round the opening. There is a test that says so.

Two documents were left stating the pre-portal conclusions and are wrong where they do:
`entrance.md` still ends "D6 wants a skirt", and `interior.md` still recommends
D6 + 760 mm as the reference prototype. Neither is what `configs/variants.toml` does.
