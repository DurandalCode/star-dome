# Wind, to the nearest order of magnitude

```bash
python3 -m stardome wind --all
make wind FABRIC=oxford_600d
```

> **This is a screening calculation, not a structural check.** No building
> code, no partial factors, no gust factor, no terrain category, and **no
> uplift**. It exists to size the question early. Nothing here may be used to
> decide that a dome is safe to put people in — that is milestone 8, and it
> needs supplier data and testing. See AGENTS.md, rule 8.

## The one number

    v_tip = sqrt( 2 * W * R / (rho * Cf * A * h) )

The wind at which the overturning moment about the downwind base edge equals
the righting moment from the structure's own weight. Below it the dome sits
still because it is heavy enough. Above it, **everything is the anchors.**

Covered in 600D Oxford at 290 g/m², with `Cf = 0.5` assumed:

| | mass | silhouette | holds itself to |
|---|---|---|---|
| D3 + 1000 skirt | 14.0 kg | 6.53 m² | **9.6 m/s** (35 km/h) |
| S — D4 + 1350 skirt | 21.5 kg | 11.68 m² | **8.9 m/s** (32 km/h) |
| M — D6 bare | 37.6 kg | 14.14 m² | 14.2 m/s (51 km/h) |
| L — D8 bare | 57.0 kg | 25.13 m² | 13.1 m/s (47 km/h) |
| XL — D10 bare | 95.7 kg | 39.27 m² | 13.6 m/s (49 km/h) |
| D12 bare | 125.3 kg | 56.55 m² | 12.9 m/s (47 km/h) |

## Two findings

### A bare dome tips at the same speed whatever its size

12.9 to 14.2 m/s across a dome that doubles in diameter. That is not a
coincidence and it is not luck: mass goes as R² (the cover dominates), sail
area goes as R², and both levers go as R, so it cancels. The spread that is
left tracks the **rod diameter steps** in the config — D10 and D12 use 12 mm
where D6 and D8 use 10 — not the size of the dome.

Practically: **you cannot make a Star Dome stand up in more wind by building
it bigger.** Ballast and anchors are the only levers.

### A skirt costs wind, and now there is a number on it

S holds itself down to **8.9 m/s — 32 km/h, a fresh breeze.** M, which is a
bigger dome, manages 14.2. The skirt adds sail and lifts the centroid without
adding much mass, so the dome that gains a walk-in door loses most of the
wind it could stand in.

That is the third time the skirt trade has come up — floor area
([`interior.md`](interior.md)), doorway height ([`doorway.md`](doorway.md)),
and now this. It is the same decision each time and this is its harshest
side.

## What has to hold it down

D6 covered, past its own tipping speed:

| wind | pressure | force | hold-down | per anchor |
|---|---|---|---|---|
| 10 m/s fresh breeze | 61 Pa | 433 N | stands | — |
| 15 m/s near gale | 138 Pa | 974 N | 5 kgf | 1 kgf |
| 20 m/s gale | 245 Pa | 1732 N | 37 kgf | 9 kgf |
| 25 m/s strong gale | 383 Pa | 2706 N | 80 kgf | 20 kgf |
| 30 m/s storm | 551 Pa | 3897 N | 131 kgf | 33 kgf |

Sharing assumed over 4 of the 10 base points — the upwind side does the work,
and a third of them is a screening guess, named so it can be argued with.

## The camp

Five domes and four corridors, on the default layout:

    mass    159 kg of domes + 15 kg of corridor cover = 174 kg
    sail    74.3 m² of domes + 23.4 m² of corridors  = 97.7 m² broadside
    weakest S1, tipping at 8.9 m/s

Summed, **not solved**: domes standing near each other shelter one another
and none of that is modelled. So the drag total is an upper bound, while the
anchor demand is not — because uplift is still missing. Two errors pointing
opposite ways do not make a safe number, only a rough one.

## Where the honesty runs out

Three inputs are assumptions, and they are the ones that move the answer.

**Cf, the force coefficient.** A covered dome is a bluff body; the real figure
depends on shape, ground effect, porosity and Reynolds number, and this
project has measured none of them. The report sweeps it rather than trusting
one value — D6 tips at 16.9, 14.2 or 12.4 m/s for Cf of 0.35, 0.5, 0.65.

**Material densities.** Pultruded GFRP at 1900 kg/m³ and Oxford at its trade
denier weight are both nominal. A PU coating can add half again to a fabric.
Weigh a sample of the actual roll and a metre of the actual rod.

**Uplift is not in this at all.** A dome in wind carries suction over its
crown, and for something this light that is often what actually lifts it — it
goes up before it slides. Leaving it out makes every number here
**optimistic**, which is the wrong direction to be wrong in.

## What would make this real

In roughly this order: weigh the actual rod and fabric; pick a wind code and
its terrain and gust factors; get a pressure distribution for a hemisphere on
the ground rather than one lumped Cf; add uplift; then design an anchor and
test one in the soil it will be driven into. Milestone 8.
