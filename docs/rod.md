# Buying and cutting the rod

```bash
python3 -m stardome rod S M L XL --stock 11800 --price 120
python3 -m stardome rod M --sweep --price 120
```

The same shape of question the cover asks. Fabric comes on a roll of a given
width; rod comes in a coil or a bar of a given length. Either way the stock's
dimension is a purchasing decision that decides the waste.

## Fifteen bows, one length

Every bow is a semicircle of the dome's own radius, so the frame is **one
length cut fifteen times** — `π · R`, 9424.8 mm on M.

Worth stating, because the model will say otherwise if asked in the wrong
mode. In `layered` the fifteen bows are drawn on fifteen slightly different
shells and come out with fifteen lengths spanning 2.3%. That is a drawing
convention, not a cutting instruction, and a cut list built from it would ask
for fifteen different pieces.

## The shopping list

11.8 m bar, 120 per metre:

| size | rod | bows | each | sections | splices | used m | bought m | kg | cost |
|---|---|---|---|---|---|---|---|---|---|
| S D4 | 8 | 15 | 6283 | 45 | 30 | 94.2 | 106.2 | 9.0 | 12 744 |
| M D6 | 10 | 15 | 9425 | 60 | 45 | 141.4 | 141.6 | 21.1 | 16 992 |
| L D8 | 10 | 15 | 12566 | 90 | 75 | 188.5 | 212.4 | 28.1 | 25 488 |
| XL D10 | 12 | 15 | 15708 | 105 | 90 | 235.6 | 247.8 | 50.6 | 29 736 |

Price per metre is yours. Diameters come from `variants.toml` and are still
provisional engineering assumptions.

## Sections come before stock

A bow is nine metres and nothing carries nine metres, so it is cut into
transport sections before the stock question arises — `section_length`, 2400
mm by default.

They divide **evenly**: four of 2356.2 mm rather than three of 2400 and a stub
of 225. Equal pieces splice with one part instead of two, and they stack
without anyone sorting them.

## Then the bar length, which is the whole game

M needs 141.4 m of rod and 45 splices whichever bar you buy. What changes is
what you pay for:

| bar mm | per bar | offcut mm | waste | bought m |
|---|---|---|---|---|
| 3000 | 1 | 644 | 21.5% | 180.0 |
| 4000 | 1 | 1644 | **41.1%** | 240.0 |
| 6000 | 2 | 1288 | 21.5% | 180.0 |
| 8000 | 3 | 931 | 11.6% | 160.0 |
| **11800** | 5 | 19 | **0.2%** | 141.6 |
| 12000 | 5 | 219 | 1.8% | 144.0 |

**Two hundred and forty metres against a hundred and forty-two, for the same
dome.** The bar length is the lever, not any cleverness in the cutting — and
picking the better bar costs nothing in splices.

A coil has no cutting waste at all: you unroll what the piece needs. Small
GFRP diameters are usually sold that way, which makes S and M the easy cases.

### Why the sweep does not just pick the best

Minimising offcut alone gives a silly answer. It will happily cut a bow into
eleven pieces of 857 mm to fill a 6 m bar exactly — 0% waste, and **ten
splices per bow** to make, carry and load. Waste is not the only cost, so the
section count stays the one the transport limit sets and only the bar moves.

## What this does not do

No allowance for the splice ferrule's own length, no kerf, no breakage
allowance, and no check that a rod of this diameter will take the bend.
Minimum bend radius equals the dome radius and is a live constraint — that
belongs to the supplier's data sheet, not here. See roadmap milestone 1.
