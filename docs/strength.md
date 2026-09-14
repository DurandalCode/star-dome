# Calculation methods and their limits

`stardome strength` reports diagnostic scenarios, **not capacity bounds**.
The operational wind limit is unknown. The beam, membrane and combined
calculations have no demonstrated ordering relative to the real flexible
frame. Passing one, or even all three, does not establish safety; exceeding a
criterion identifies a problem with that scenario or its inputs, not a proven
failure of the built dome. [Decision 0028](decisions/0028-scenarios-are-not-capacity-bounds.md)
replaces the bounding interpretation in decision 0023.

```bash
python3 -m stardome strength M --wind 10
python3 -m stardome strength S --wind 10 --modulus 60000
python3 -m stardome strength M --wind 10 --compare
python3 -m stardome strength M --wind 10 --json
make strength WIND=10
```

The JSON contract is `star_dome_strength/2`, with `status: screening_only`
and `operational_limit_ms: null`. Version 1's `band_ms` and `limit_ms` are
removed deliberately. Consumers must migrate to scenario `utilisation`,
`at_speed_ms`, `binding_check`, `binding_span` and diagnostic `threshold_ms`.
A threshold is never a suggested operating speed. Reports retain resolved
material/load inputs, pressure mesh resolution and a SHA-256 geometry digest
so a changed configuration can be distinguished from the previous result.

## Material: stiffness can make prescribed bending worse

The configured `gost31938` candidate retains the historical **GOST 31938-2012**
reference values: E = 50 GPa and tensile strength = 800 MPa. They are not a
measured batch, nor a verified set of properties under the replacement 2022
edition. The [official standards register](https://protect.gost.ru/gost/details/0e7bbf20-144c-46ae-970f-a41e7fa9c072)
records the replacement. Typical densities and shear moduli remain separately
identified in `configs/materials.toml`.

For a straight circular rod held at nominal radius R:

- initial outer-fibre strain: ε₀ = d / (2R);
- initial stress magnitude: σ₀ = E ε₀, on both tensile and compressive fibres;
- assumed sustained tensile criterion: f_s = 0.20 × 0.70 × f_t;
- assumed short-term criteria: f_td = 0.70 f_t / 1.5 and f_cd = 0.70 f_c / 1.5.

These reductions are screening assumptions. ACI 440.1R concerns **concrete
reinforced with FRP bars** ([ACI scope](https://www.concrete.org/publications/internationalconcreteabstractsportal/m/details/id/51687817));
borrowing its reduction factors does not validate a freestanding bent-rod
frame. Sustained compression, resin, temperature, moisture, drilling and
repeated assembly need stock-specific evidence.

For D6, d = 10 mm and R = 3000 mm, the initial stress rounds to **83 MPa**
against the configured **112 MPa** sustained-tension criterion. The initial
bend reaches that criterion at **67.2 GPa**. This only tests initial bending.
For D4, d = 8 mm and R = 2000 mm, σ₀ rises from 100 MPa at E = 50 GPa to
120 MPa at E = 60 GPa: the result switches from below to above 112 MPa.
Both moduli exceed the old minimum. Consequently a minimum E is **not** a
conservative input for prescribed curvature, even though higher E improves
Euler stiffness and reduces load-induced deflection.

`--modulus` overrides E in MPa to inspect this sensitivity. Keep strength
properties explicit; a real batch needs measured E bounds, section dimensions,
strength and sustained-bend tests. Do not invent an upper E by relabelling a
standard's minimum. Nominal curvature omits the extra local curvature from
weaving and fittings.

## Wind: independent pressure cases

The input is an assumed local peak gust V in m/s. q = ρV²/2 in Pa; negative
or non-finite speeds are rejected. No site exposure, terrain, height conversion,
reliability factors or validated design load combinations are supplied.

The external pressure approximation retains configured coefficients +0.8,
−1.2, −0.4 along the windward-to-leeward meridian. Interpolation uses the
angle to the windward direction. It is based on the smooth ground-level
hemisphere idealisation; its use for a woven fabric cover and a raised skirt
is unvalidated. This is not a complete EN 1991-1-4 design procedure.

Internal coefficients are independent cases:

| Door scenario | cpi | Meaning |
|---|---:|---|
| shut | −0.3 and +0.2 | Unknown permeability: check both signs separately |
| open, windward dominant opening | +0.72 | 0.90 × 0.8, assuming opening-area ratio ≥ 3 |

EN 1991-1-4 §7.2.9(5) gives 0.75 at ratio 2 and 0.90 at ratio ≥ 3;
§7.2.9(6), Note 2 uses both +0.2 and −0.3 when permeability cannot be
estimated. See the [standard text](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1991.1.4.2005.pdf)
and the [JRC worked example](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/SX016a-EN-EU.pdf).
The project does not know the actual leakage or pressure inside connected
corridors. `open` is a scenario, not an automatic envelope of every possible
opening orientation. Both door modes currently integrate the closed cover
surface; opening geometry and fabric flapping are not solved.

Each facet carries F = −q(cpe − cpi) A n, with 10⁻⁶ converting Pa·mm² to N.
The full signed resultant moment Σ(r × F) is measured about the ground origin.
`loads.resultants` defaults to the positive internal-pressure case for uplift;
`loads.analyse` reports both shut cases at azimuth 0. `strength` samples the
whole circle at 18° steps and reports the directions. This finite sample does
not certify a continuous directional maximum. Force and moment for an anchor
case always come from the same direction and internal pressure.

## Live spans and tributary cover

Each bow is split at supports **within each surviving interval**. A removed
middle segment has no span and no self-weight. A free crossing becomes a
support only in the `contact` scenario; actual lashing and clamp stiffness
remain unmeasured. Spans use nominal arc lengths, consistent with the cut
schedule, not the extra length or stiffness of a woven route and splice.

Cover facets are assigned to the nearest sampled point on a surviving bow,
then to its live span. A point at a support shares its facet area equally
between adjacent live spans. Skirt facets are excluded from bow demands and
included in global resultants. All dome facet area is conserved, but nearest
sample assignment is a discretisation, not a solved fabric-to-frame load path.
For each span of length a, its representative width is b = tributary area / a.
Every live span is checked separately; no per-bow average is combined with an
unrelated longest span. The cache key includes all geometry, support mode and
mesh resolution, so changing dimensions under an existing variant name cannot
reuse stale areas or lengths.

## Member equations and combinations

Use N and mm below. For a circular section, A, I and W = I/(d/2) include any
configured tube bore. Gravity line load is

    wg = ρrod A 10⁻⁹ g + mfabric b 10⁻⁹ g   [N/mm]

where ρrod is kg/m³ and mfabric is g/m². This treats all of the tributary
weight as transverse uniform loading in a simply supported beam scenario.
It is an explicit idealisation; actual orientation, continuous-arch action
and redistribution require a frame model. Gravity bending remains present
in **every** wind scenario:

    Mg = wg a² / 8

For each span, the directional and internal-pressure sample gives separate
maxima cp_in = max(0, cpe − cpi) and cp_out = max(0, cpi − cpe). Let
p_in = q cp_in 10⁻⁶ and p_out = q cp_out 10⁻⁶, in N/mm².

| Wind scenario | Additional bending | Compression / tension |
|---|---|---|
| beam | Mw = max(p_in, p_out) b a² / 8 | Nc = Nt = 0 |
| membrane | Mw = 0 | Nc = p_in Rb/2; Nt = p_out Rb/2 |
| envelope | beam Mw | membrane Nc and Nt, checked separately |

The membrane expression is an ideal spherical-shell analogy, not a solution
of this sparse lattice. Pressure and suction do not buckle a member in the
same way: **only Nc enters Euler**, never abs(Nt). The combined scenario
adds separate worst actions which may not occur in one physical wind field.
It is an algebraic diagnostic, not a third admissible equilibrium solution.

The checked ratios are:

- initial bend: σ₀ / f_s;
- sustained tension: (σ₀ + Mg/W) / f_s;
- total tension: (σ₀ + (Mg+Mw)/W + Nt/A) / f_td;
- total compression: (σ₀ + (Mg+Mw)/W + Nc/A) / f_cd;
- Euler screening: Nc / (π²EI/a²), with pinned ends and effective length a.

Opposing stress relief is not credited. This still does not prove an upper
bound for a curved member: imperfections, bending/compression interaction,
local buckling, postbuckling and joint flexibility are absent. Sustained
compression has no validated criterion here and remains an explicit gap.

Deflection is 5w a⁴/(384EI), with gravity always present and wind transverse
only in the beam/combined scenarios. A sag/span above 10% marks
`outside_linear_theory`; 10% is a diagnostic flag, not an allowable deflection
or proof that smaller displacement validates all assumptions.

The search over 0–120 m/s locates a criterion crossing only:

- `already_exceeded_at_zero_wind`: the selected scenario exceeds a criterion
  in calm; report the criterion and span, with threshold 0;
- `crossing_found`: report the crossing and linear-theory flag;
- `not_reached_through_120_ms`: serialize threshold as null, not infinity.

With the default D6 inputs and lashed supports, rod and fabric gravity already
exceed the assumed sustained-tension criterion in the beam gravity model.
All three scenario thresholds are therefore zero. This replaces the old
positive wind band; suppressing gravity to retain that band would hide the
model's inconsistency. It is not proof that the actual dome fails in calm.

## Anchors: equilibrium with moment, under stated support assumptions

The new support screening assumes a rigid base and identical independent
spring stiffness at every anchor. Vertical springs work in both directions:
positive load is uplift, negative load requires compression bearing. This is
especially restrictive for a bare dome whose feet have no proven rigid ring.
No lower/upper bound for the real support reactions is claimed.

Coordinates are projected to ground and centred at the anchor centroid.
Solve Rzi = α + β yi − γ xi from ΣRz = Fz, ΣyRz = Mx,
−ΣxRz = My. Translate the applied moment to that centroid first. In-plane
load combines equal translation with torsion:

    Rxi = Fx/n − Mz yi / Σ(x²+y²)
    Ryi = Fy/n + Mz xi / Σ(x²+y²)

Returned vectors are loads delivered to anchors, opposite to reactions on
the dome. Their sum and all three moments reproduce the applied resultant.
For a regular ring of radius r, an anchor aligned with a horizontal moment M
has uplift Fz/n + 2M/(nr), illustrating why average Fz/n can be too small.

Worst uplift and shear are reported with their pressure/direction witnesses.
They can govern in different cases. Soil capacities remain placeholders;
bearing, combined uplift/shear interaction, unequal stiffness, loss of contact,
rod prestress, and footing movement are unverified. Global wind screening
credits no favourable weight against uplift.

## What remains before an operating limit

The mass inventory includes nominal surviving bows, closed cover including
door panels, hem rope and webbing. Optional plastic volume must be supplied
by the caller. Steel hardware, skirt stock and unmeasured plastic are excluded
explicitly. Member gravity includes only bows and tributary fabric, so the
inventory total must not be mistaken for a complete applied gravity case.

Next work needs measured rod and joint properties; equilibrium of the
prestressed assembled frame; geometric nonlinearity and stability under
consistent wind/gravity combinations; connector, drilled section, belt and
soil checks; and comparison against controlled component and prototype tests.
The [roadmap](roadmap.md) keeps structural validation and field rules open.

Regression tests cover signed pressures, area conservation, cut intervals,
cache invalidation, E sensitivity, gravity in every scenario, dimensional hand
calculations, six-component anchor equilibrium, ring reactions and report
semantics. Passing software tests verifies implementation of these assumptions;
it does not validate the assumptions against a physical structure.
