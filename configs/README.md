# Dome configurations

Named variants live here. Keep dimensions explicit and use millimetres.

Initial target family:
- D4: 4000 mm
- D6: 6000 mm
- D8: 8000 mm
- D12: 12000 mm (experimental XL)

Rod diameters are intentionally not fixed yet; 8-10 mm is the first prototype range, with larger diameters/tubes expected for larger variants.

## Where the numbers live

[`variants.scad`](variants.scad) is the machine-readable version of the table
above and the only file in the repository holding a variant-specific dimension.
The OpenSCAD model in [`dome/`](../dome) reads it; edit it there and every
variant follows.

Current provisional rod diameters: D4 8 mm, D6 10 mm, D8 10 mm, D12 12 mm.
These are assumptions for visual and geometric work, not structural results.
