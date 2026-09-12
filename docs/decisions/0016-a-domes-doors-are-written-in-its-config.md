# 0016. Write a dome's doors in its config, and aim them by azimuth

- **Status:** accepted
- **Date:** 2026-09-12
- **Where it lives:** `configs/variants.toml` (`[[variants.X.doors]]`), `stardome/config.py` (`Door`), `stardome/doorway.py` (`place_all`), `docs/doorway.md`

## The decision

A variant carries an array of doors instead of a single `door` + `door_cut` pair.
Each door says how far it is cut open and which way it faces:

```toml
[[variants.D10.doors]]
cut = "portal"
facing = 18

[[variants.D10.doors]]
cut = "none"
facing = 198
template = "tall"
```

`facing` is an azimuth and a **wish**, not a position: a door can only sit in a bay,
there are ten, and which are eligible depends on the cut — low bays for a portal, tall
bays for everything else. The nearest eligible bay takes the door and the record says
where it landed. Two doors aimed at one bay is an error.

The single-door pair still works and every variant in the file still uses it. It means
one door, placed where the geometry puts the first one, and it produces byte-identical
output — which is what let this land without moving a golden file.

## Why

The geometry was choosing something that is not geometry. Which way a door faces is a
fact about where the dome is pitched — at the yard, at the corridor to the next dome —
and how many it has is a fact about what it is for. A camp of three domes with one
automatically-placed door each cannot be laid out at all.

The measurement that prompted it: at the XL end the uncut tall bay is already a door
(`carry` from D 8656, a 2.2 m character from D 9848), so `cut` stops being one setting
the whole dome shares and becomes a per-door choice — a wide portal at the front, a bay
left whole at the back, on the same dome.

**Doors are not independent, and that is the part worth writing down.** A cut takes rod
out of the free-height envelope everywhere, not only in front of the door that asked for
it. Placement therefore resolves every door, unions the cuts, and only then measures each
opening on the dome all of them leave. A per-door loop would have reported each door on a
dome that does not exist.

## What was rejected

- **A door count and a spacing.** Rotationally even doors are the one arrangement a camp
  never wants; the whole point is aiming them at different things.
- **Naming the bay by index.** `bay = 3` is stable but means nothing to a person laying
  out a site, and the indices renumber the moment a cut changes which bays are tall.
- **Snapping silently.** A door that asked for 200° and got the bay at 198° must say so;
  the record carries both `facing_deg` and `landed_deg`.
- **Keeping consumers on the single `doorway`.** The cover, the hem, the base hubs and
  the terminations all count doors now. Leaving them reading the first one would have
  produced a parts list that is wrong in exactly the case the feature exists for.

## What it costs

**`data["doorway"]` survives as the first door.** The corridor hangs off it and the
cover's first seam falls on it, because that is the one azimuth on a built dome anybody
can find without measuring — but it is now a privileged member of a list rather than the
only one, and any consumer that reads it is answering about one door out of several.

**Two portals can leave a bow standing on nothing.** One door's two jamb pieces come off
two different bows; two doors can take both ends off the same bow, and it then reaches no
foot at all. It is still continuous and still loaded, hanging in the lattice between its
crossings. Reported by name rather than forbidden — whether it stands is statics, not
geometry.

**The schedule's base-hub grouping got stricter.** It grouped feet by member count alone,
on the stated assumption that the fan is the same shape at all of them up to a mirror.
That assumption is a single-door assumption; it now reads the union of every door's cuts,
and the two-portal case is a test.
