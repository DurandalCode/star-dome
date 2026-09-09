// Convenience wrapper: renders the D12 Star Dome variant.
//
// The assignment comes AFTER the include on purpose. OpenSCAD gives a variable
// its last assigned value in a scope, so this overrides the default in
// star_dome.scad. Dimensions still come from configs/variants.scad.
//
//   openscad -o exports/star_dome_d12.stl dome/variants/star_dome_d12.scad

include <../star_dome.scad>
variant = "D12";
