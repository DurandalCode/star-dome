# 0029. Use standards for material inputs and explicit scenarios for unknowns

- **Status:** accepted; extends 0028 without changing its operating-limit rule.
- **Date:** 2026-09-14
- **Where:** `configs/wind-study.toml`, `configs/materials.toml`, `analysis/`,
  [wind-study.md](../wind-study.md)

The next step is a benchmarked nonlinear cap idealisation, kept outside the
dependency-free geometry package. It uses the existing geometry and live rod
intervals, naturally straight rods, assembly prestress, force/moment-conserving
load transfer and a constrained tangent stability check. NumPy/SciPy are optional
analysis dependencies and have their own CI job.

GOST 31938-2022 supplies a new, separately named ASK candidate. Keep the historical
2012 candidate unchanged for reproducibility. A conditional purchased AV aluminium
tube is specified by alloy, temper and GOST 18475-82, rather than by the word
"aluminium". Its gross section is calculable; its contact, drilled holes and pins
do not acquire a validated joint law from the tube standard.

Use explicit sensitivity grids for E, area, joint rotational compliance and
fabric prestress. Reject the alternative of labelling an assumed fabric tension
as a measured average, or a tube EI as the stiffness of an assembled splice.
No standard-derived upper E has been established.

The cost of a tractable first model is explicit: fixed pinned feet, coincident
crossing centrelines with free rotations, relaxed material twist, no shear or
contact, no skirt/ground solve and a fixed reference pressure field. Membrane
pretension is an inward loading scenario without unmeasured stiffness credit.
These choices are not proved conservative. The report remains a cap study and
leaves `operational_limit_ms` null. A solver failure remains an unresolved load
path, not a reported failure wind speed.

Proceeding to an operating limit requires the omitted load paths and component
properties, coupled stability checks and physical validation. The calculation
can now identify which assumptions deserve measurement first.
