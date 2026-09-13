# 0021. Wind is the only load case

- **Status:** accepted
- **Date:** 2026-09-13
- **Where it lives:** `configs/loads.toml`, `stardome/loads.py`, `docs/strength.md`, milestone 8 in `docs/roadmap.md`

## The decision

Milestone 8 asks for "расчётные случаи нагружения, прежде всего ветер и нагрузку
от обшивки". It gets wind, self weight and cover weight, and it does not get snow.

A Star Dome here is a temporary event structure: it goes up for a weekend and comes
down again, and it is not standing in February. The operating rule is the mitigation,
and leaving snow out is what turns the deliverable into **a wind speed** rather than
a map of Russia.

## Why

Because the two cases do not merely differ in size, they differ in what the answer
*is*. A snow case is a site question — which district, which winter, which roof
shape coefficient — and it produces a yes or a no for one place. A wind case with no
site in it produces an **operating limit**, which is a thing a person can act on
anywhere: watch the forecast, and take it down at N metres per second.

That also matches what this repository can honestly hold. It has no site, no soil
and no season in it; it has a dome. A load case that needs a postcode does not
belong in it.

## What was rejected

- **Snow as a second case.** Not because it is small — it is enormous. 1.8 kPa on a
  6 m dome is 51 kN, against the 300 Pa the wind case is about, and it would govern
  everything by a factor of five or more. It is rejected because the structure is not
  under it, and pretending otherwise would size a dome for a load its operating rule
  removes.
- **A combined wind-plus-snow envelope.** Same reason, and it would additionally
  hide which of the two was doing the work.
- **A site-specific design wind from SP 20.13330.** Requires a site. `configs/loads.toml`
  records how to convert a code's reference velocity into the gust speed this project
  takes as input, and stops there.

## What it costs

**Somebody will leave one up.** The calculation is silent about a dome standing in
December, and silent is worse than conservative, because a reader who has seen a wind
limit may assume the whole envelope has been checked. `docs/strength.md` says so
explicitly and `configs/loads.toml` names itself as the file snow would go in.

**There is no gust dynamics in it either.** The input is a peak gust treated
quasi-statically. A 6 m lattice of 10 mm rod under a loose membrane is light and
flexible, and whether its own response matters is a question this case does not ask.
