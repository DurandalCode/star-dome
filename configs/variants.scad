// ---------------------------------------------------------------------------
// configs/variants.scad -- named Star Dome variants.
//
// GENERATED FILE. Do not edit.
//
//     python3 -m stardome scad-config
//
// The source of truth is configs/variants.toml. This file exists because
// OpenSCAD cannot read TOML and dome/star_dome.scad needs the same numbers the
// Python core uses. Parameters are single-sourced; the geometry in dome/ stays
// an independent implementation, which is what makes the cross-check in
// tests/test_geometry.py worth anything. See docs/architecture.md.
//
// All dimensions in millimetres (see AGENTS.md).
//
// ---------------------------------------------------------------------------
// ROD DIAMETERS ARE PROVISIONAL
//
// The values below are engineering *assumptions*, not results. Nothing here
// has been checked against fiberglass rod properties, buckling, bending
// stress, minimum bend radius, wind load, cover load or anchoring, and the
// geometric model deliberately says nothing about whether a given rod can
// survive being bent to the required radius.
//
// Every bow is bent to a radius equal to the dome radius, so the required
// bend radius scales directly with the variant:
//
//   D3  ->  1500 mm
//   D4  ->  2000 mm
//   D6  ->  3000 mm
//   D8  ->  4000 mm
//   D10 ->  5000 mm
//   D12 ->  6000 mm
//
// Confirm each against the real rod stock before treating a variant as
// buildable. See docs/roadmap.md milestones 4, 6 and 8.
// ---------------------------------------------------------------------------

// Record layout.
SDV_NAME = 0; SDV_DIAMETER = 1; SDV_ROD_DIAMETER = 2; SDV_NOTE = 3;

SD_VARIANTS = [
    ["D3",   3000,  8, "small dome on a 1 m skirt; 1473 mm of dome is not standing height on its own"],
    ["D4",   4000,  8, "S -- smallest size with a walk-in door; needs the tallest skirt to get one"],
    ["D6",   6000, 10, "M -- reference prototype; best all-round trade in the family"],
    ["D8",   8000, 10, "L -- large dome; the skirt is barely a sill. Expect reinforcement work"],
    ["D10", 10000, 12, "XL -- takes a walk-in door with no skirt at all; expect D8's reinforcement work"],
    ["D12", 12000, 12, "research variant beyond XL; explicitly unvalidated, and 5.9 m tall to erect"]
];

// Look a variant up by name. Fails loudly rather than silently falling back,
// so a typo in a -D override cannot quietly render the wrong dome.
function sd_variant(name) =
    let (hits = [for (v = SD_VARIANTS) if (v[SDV_NAME] == name) v])
    assert(len(hits) == 1, str("unknown variant '", name,
                               "' -- known: ", [for (v = SD_VARIANTS) v[SDV_NAME]]))
    hits[0];

function sd_variant_diameter(name)     = sd_variant(name)[SDV_DIAMETER];
function sd_variant_rod_diameter(name) = sd_variant(name)[SDV_ROD_DIAMETER];
function sd_variant_note(name)         = sd_variant(name)[SDV_NOTE];
