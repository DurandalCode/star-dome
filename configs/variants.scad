// ---------------------------------------------------------------------------
// configs/variants.scad -- named Star Dome variants.
//
// This is the file to edit when a size or a rod choice changes. Nothing else
// in dome/ contains a variant-specific number.
//
// All dimensions in millimetres (see AGENTS.md).
//
// ---------------------------------------------------------------------------
// ROD DIAMETERS ARE PROVISIONAL
//
// The values below are engineering *assumptions*, not results. They are a
// starting point for visual and geometric work only. Nothing here has been
// checked against fiberglass rod properties, buckling, bending stress, minimum
// bend radius, wind load, cover load or anchoring, and the geometric model
// deliberately says nothing about whether a given rod can survive being bent
// to the required radius.
//
// Every bow in this design is bent to a radius equal to the dome radius, so
// the required bend radius scales directly with the variant:
//
//   D4  ->  2000 mm      D8  ->  4000 mm
//   D6  ->  3000 mm      D12 ->  6000 mm
//
// Confirm each against the real rod stock before treating a variant as
// buildable. See docs/roadmap.md milestones 4, 6 and 8.
// ---------------------------------------------------------------------------

// Record layout.
SDV_NAME = 0; SDV_DIAMETER = 1; SDV_ROD_DIAMETER = 2; SDV_NOTE = 3;

SD_VARIANTS = [
    ["D4",   4000,  8, "small experimental dome"],
    ["D6",   6000, 10, "reference prototype"],
    ["D8",   8000, 10, "large dome; expect reinforcement work"],
    ["D12", 12000, 12, "XL research variant; explicitly unvalidated"]
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
