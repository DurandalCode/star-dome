// ---------------------------------------------------------------------------
// star_dome.scad -- parametric Takekawa-style Star Dome, structural rods only.
//
// This is the geometric source of truth for the D4 / D6 / D8 / D12 variants.
// It draws rod centrelines swept as round members. It deliberately contains no
// connectors, no fabric cover and no reinforcement belts.
//
// The topology and the derivation of every angle live in
// star_dome_geometry.scad. Read that first; this file is presentation.
//
// USAGE
//
//   Open directly            -> renders the D6 reference variant.
//   Pick a variant           -> openscad -D 'variant="D8"' dome/star_dome.scad
//   Override a dimension     -> openscad -D 'rodDiameter=12' dome/star_dome.scad
//   Console report only      -> openscad -o /dev/null --render dome/star_dome.scad
//   Convenience wrappers     -> dome/variants/star_dome_d6.scad, etc.
//
// All dimensions in millimetres.
// ---------------------------------------------------------------------------

include <star_dome_geometry.scad>
include <../configs/variants.scad>

/* [Variant] */

// Named preset from configs/variants.scad. Sets the two dimensions below.
variant = "D6";                              // ["D4", "D6", "D8", "D12"]

/* [Main dimensions] */

// Nominal dome diameter: the diameter of the ground ring, in mm.
domeDiameter = sd_variant_diameter(variant);

// Rod stock diameter, in mm. Provisional -- see configs/variants.scad.
rodDiameter = sd_variant_rod_diameter(variant);

/* [Rendering] */

// Straight pieces used to approximate each 180-degree bow.
rodSegments = 48;

// 1 = draft, 2 = preview, 3 = final. Controls facet counts only.
renderQuality = 2;

/* [Visual aids] */

// Master switch for node markers.
showNodes = true;

// The structural base ring: the 2 optional extra bows bent into the ground.
showGroundRing = true;

// Rod numbers, node ids and base point numbers.
showLabels = false;

// Flat reference circle at the nominal diameter.
showGroundCircle = true;

// Markers at the 10 ground points where 3 rods land.
showBaseNodes = showNodes;

// Markers at the 10 lashed crossings where 4 rods meet.
showTiedNodes = showNodes;

// Markers at the 30 crossings that the reference does not lash.
showUntiedCrossings = false;

// XYZ axes at the origin.
showAxes = false;

/* [Weave] */

// "layered" gives every rod its own shell so crossings read as over/under.
// "flat" puts all centrelines exactly on the nominal sphere -- correct for
// measurement and export, but crossing rods then share a centreline.
weaveMode = "layered";                       // ["layered", "flat"]

// Multiplier on the rod diameter for the shell spacing. 1.0 makes crossing
// rods just touch; lower values tighten the dome at the cost of some
// interpenetration.
weaveGap = 1.0;

/* [Console report] */

// Echo the derived dimensions, rod schedule and node table.
reportSummary = true;

// Also echo every one of the 90 rod-to-rod crossings. Verbose.
reportAllCrossings = false;

/* [Hidden] */

domeRadius = domeDiameter / 2;
rodFacets    = renderQuality <= 1 ? 6  : renderQuality == 2 ? 12 : 24;
markerFacets = renderQuality <= 1 ? 8  : renderQuality == 2 ? 16 : 32;

COLOR_G       = [0.20, 0.65, 0.25];   // family G, as drawn in the reference
COLOR_U       = [0.30, 0.35, 0.85];   // family U, bracing
COLOR_L       = [0.45, 0.50, 0.95];   // family L, bracing
COLOR_BASE    = [0.75, 0.15, 0.15];   // base ring
COLOR_NODE    = [1.00, 0.75, 0.00];
COLOR_FOOT    = [1.00, 0.35, 0.00];
COLOR_LOOSE   = [0.55, 0.55, 0.60];

function sd_family_color(f) = f == "G" ? COLOR_G : f == "U" ? COLOR_U : COLOR_L;

function sd_offset(bow) = sd_layer_offset(bow, rodDiameter, weaveMode, weaveGap);

// Half the weave band, used for the bounding-box report.
function sd_weave_half_band() =
    weaveMode == "flat" ? 0 : (SD_BOW_COUNT - 1) / 2 * rodDiameter * weaveGap;

// Actual extents once the weave shells and the rod's own thickness are
// included. Each bow's widest point is its foot, at radius R + its offset;
// its highest point is its apex, at (R + offset) * sin(tilt).
function sd_overall_radius() =
    max([for (bw = sd_bows()) domeRadius + sd_offset(bw)]) + rodDiameter / 2;

function sd_overall_height() =
    max([for (bw = sd_bows()) (domeRadius + sd_offset(bw)) * sin(bw[SD_TILT])])
    + rodDiameter / 2;

// Membership test. Clearer than search() for a plain list of numbers.
function sd_contains(v, lst) = len([for (x = lst) if (x == v) 1]) > 0;

// The rods landing on base point i.
function sd_rods_at_base(i) =
    [for (bw = sd_bows()) if (sd_contains(i, sd_bow_feet(bw))) bw];

// ===========================================================================
// Drawing primitives
// ===========================================================================

// One straight piece of rod between two points.
module sd_segment(p1, p2, d) {
    v = p2 - p1;
    l = norm(v);
    if (l > 1e-9)
        translate(p1)
            rotate([0, acos(v.z / l), atan2(v.y, v.x)])
                cylinder(h = l, d = d, $fn = rodFacets);
}

// A polyline swept as a round member. Spheres at the interior joints keep the
// surface closed where the arc changes direction.
module sd_swept_polyline(pts, d) {
    for (i = [0 : len(pts) - 2]) sd_segment(pts[i], pts[i + 1], d);
    for (i = [1 : len(pts) - 2]) translate(pts[i]) sphere(d = d, $fn = rodFacets);
}

module sd_marker(p, d, col) {
    color(col) translate(p) sphere(d = d, $fn = markerFacets);
}

// Flat text lying in the XY plane, readable from above.
module sd_label(p, s, size) {
    color([0.1, 0.1, 0.1])
        translate(p)
            linear_extrude(height = max(1, rodDiameter / 8))
                text(s, size = size, halign = "center", valign = "center");
}

// ===========================================================================
// The dome
// ===========================================================================

// The 15 continuous structural members.
module sd_rods() {
    for (bw = sd_bows())
        color(sd_family_color(bw[SD_FAMILY]))
            sd_swept_polyline(
                sd_bow_polyline(bw, domeRadius, rodSegments, sd_offset(bw)),
                rodDiameter);
}

// The 2 optional bows bent into the ground ring. Drawn as a full torus
// because a bent rod follows the circle, not the decagon's chords.
module sd_ground_ring() {
    color(COLOR_BASE)
        rotate_extrude($fn = max(48, rodSegments))
            translate([domeRadius, 0]) circle(d = rodDiameter, $fn = rodFacets);
}

// Thin flat circle at the nominal diameter, purely for reference.
module sd_ground_circle() {
    w = max(2, rodDiameter / 5);
    color([0.6, 0.6, 0.6, 0.5])
        linear_extrude(height = w / 2)
            difference() {
                circle(r = domeRadius + w, $fn = 180);
                circle(r = domeRadius - w, $fn = 180);
            }
}

module sd_base_node_markers() {
    d = rodDiameter * 2.2;
    for (i = [0 : SD_BASE_POINTS - 1]) sd_marker(sd_base_point(i, domeRadius), d, COLOR_FOOT);
}

module sd_tied_node_markers() {
    d = rodDiameter * 2.2;
    for (p = sd_tied_nodes(domeRadius)) sd_marker(p, d, COLOR_NODE);
}

module sd_untied_crossing_markers() {
    d = rodDiameter * 1.4;
    for (c = sd_untied_pairs(domeRadius)) sd_marker(c[2], d, COLOR_LOOSE);
}

module sd_axes() {
    l = domeRadius * 1.25;
    w = rodDiameter * 0.6;
    color([0.9, 0.2, 0.2]) sd_segment([0, 0, 0], [l, 0, 0], w);
    color([0.2, 0.8, 0.2]) sd_segment([0, 0, 0], [0, l, 0], w);
    color([0.2, 0.4, 0.9]) sd_segment([0, 0, 0], [0, 0, l], w);
}

module sd_labels() {
    size = domeRadius / 18;

    // Rod number at each bow's apex, pushed a little clear of the rod.
    for (bw = sd_bows()) {
        p = sd_bow_point(bw, 90, domeRadius, sd_offset(bw) + rodDiameter * 2.5);
        sd_label(p, str(bw[SD_NAME]), size);
    }

    // Base point numbers, just outside the ring.
    for (i = [0 : SD_BASE_POINTS - 1])
        sd_label(v_cyl(domeRadius + size * 2.2, i * SD_BASE_STEP, 0), str("b", i), size * 0.9);

    // Tied node ids, matching the console report's ordering.
    nodes = sd_tied_nodes(domeRadius);
    for (i = [0 : len(nodes) - 1])
        sd_label(nodes[i] * 1.06, str("n", i), size * 0.9);
}

module star_dome() {
    sd_rods();
    if (showGroundRing)      sd_ground_ring();
    if (showGroundCircle)    sd_ground_circle();
    if (showBaseNodes)       sd_base_node_markers();
    if (showTiedNodes)       sd_tied_node_markers();
    if (showUntiedCrossings) sd_untied_crossing_markers();
    if (showAxes)            sd_axes();
    if (showLabels)          sd_labels();
}

// ===========================================================================
// Console report
// ===========================================================================

module sd_report_dimensions() {
    R  = domeRadius;
    hb = sd_weave_half_band();

    echo(str("=== Star Dome '", variant, "' -- ", sd_variant_note(variant), " ==="));
    echo(str("  nominal diameter      ", domeDiameter, " mm"));
    echo(str("  nominal radius        ", R, " mm"));
    echo(str("  rod diameter          ", rodDiameter, " mm  (PROVISIONAL)"));
    echo(str("  continuous members    ", SD_BOW_COUNT,
             "  + ", SD_BASE_BOW_COUNT, " optional base-ring bows"));
    echo(str("  base points           ", SD_BASE_POINTS, "  (3 rod ends each)"));
    echo("");
    echo(str("  bow length (each)     ", sd_bow_length(R), " mm   = pi * R, all identical"));
    echo(str("  total rod length      ", sd_total_rod_length(R), " mm  (", SD_BOW_COUNT, " bows)"));
    echo(str("  base ring length      ", sd_base_ring_length(R), " mm  (= 2 bow lengths)"));
    echo(str("  total incl. base ring ", sd_total_rod_length(R) + sd_base_ring_length(R), " mm"));
    echo("");
    echo(str("  structural height     ", sd_structural_height(R),
             " mm   (apex of the tallest family, = ",
             sd_structural_height(R) / R, " * R)"));
    echo(str("  enclosing hemisphere  ", R, " mm   (no bow passes over the zenith)"));
    echo(str("  base edge, arc        ", sd_base_edge_arc(R), " mm"));
    echo(str("  base edge, chord      ", sd_base_edge_chord(R), " mm"));
    echo("");
    echo(str("  weave mode            ", weaveMode, ", gap ", weaveGap,
             " x rod diameter, half-band ", hb, " mm"));
    echo(str("  overall diameter      ", 2 * sd_overall_radius(), " mm  (incl. weave + rod)"));
    echo(str("  overall height        ", sd_overall_height(), " mm  (incl. weave + rod)"));
    if (weaveMode != "flat")
        echo(str("  note: with weaveMode=\"layered\" the 3 rod ends at each base point are",
                 " spread radially across the ", 2 * hb,
                 " mm weave band. Use weaveMode=\"flat\" for true centreline coordinates."));
}

module sd_report_families() {
    echo("");
    echo("  --- families ---");
    for (f = sd_family_spec())
        echo(str("  family ", f[0], "  tilt ", f[2], " deg  ties at ", f[3],
                 " deg   ", f[4]));
}

module sd_report_rods() {
    R = domeRadius;
    echo("");
    echo("  --- rod schedule (rod number = list order) ---");
    for (bw = sd_bows()) {
        o = sd_offset(bw);
        echo(str("  ", bw[SD_ID] + 1, "  ", bw[SD_NAME],
                 "  family ", bw[SD_FAMILY],
                 "  feet b", sd_bow_feet(bw)[0], "-b", sd_bow_feet(bw)[1],
                 "  azimuth ", bw[SD_AZ], " deg",
                 "  tilt ", bw[SD_TILT], " deg",
                 "  length ", gc_arc_length(R + o), " mm",
                 "  ties at ", [for (t = bw[SD_TIES]) gc_arc_length(R + o, 0, t)], " mm"));
    }
}

module sd_report_base_nodes() {
    R = domeRadius;
    echo("");
    echo("  --- base nodes (10, three rod ends each) ---");
    for (i = [0 : SD_BASE_POINTS - 1]) {
        p    = sd_base_point(i, R);
        rods = [for (bw = sd_rods_at_base(i)) bw[SD_NAME]];
        echo(str("  b", i, "  ", p, "   rods ", rods));
    }
}

module sd_report_tied_nodes() {
    R     = domeRadius;
    nodes = sd_tied_nodes(R);
    ties  = sd_tied_pairs(R);
    echo("");
    echo(str("  --- tied crossings: ", len(nodes),
             " nodes, ", len(ties), " rod-to-rod pairs ---"));
    for (i = [0 : len(nodes) - 1]) {
        p     = nodes[i];
        thru  = sd_bows_through(p);
        names = [for (b = thru) sd_bows()[b][SD_NAME]];
        pairs = [for (c = ties) if (v_dist(c[2], p) < 1e-6)
                    str(sd_bows()[c[0]][SD_NAME], "/", sd_bows()[c[1]][SD_NAME],
                        " ", c[5], "deg")];
        echo(str("  n", i, "  ", p,
                 "   z/R ", p.z / R,
                 "   rods ", names));
        echo(str("        crossing angles: ", pairs));
    }
}

module sd_report_untied() {
    R = domeRadius;
    loose = sd_untied_pairs(R);
    echo("");
    echo(str("  --- untied crossings: ", len(loose),
             " (rods touch here but the reference does not lash them) ---"));
    if (reportAllCrossings)
        for (c = loose)
            echo(str("  ", sd_bows()[c[0]][SD_NAME], "/", sd_bows()[c[1]][SD_NAME],
                     "  ", c[2],
                     "  t=", c[3], "/", c[4], " deg",
                     "  angle ", c[5], " deg"));
}

module sd_report_checks() {
    R      = domeRadius;
    ties   = sd_tied_pairs(R);
    nodes  = sd_tied_nodes(R);
    feet   = [for (i = [0 : SD_BASE_POINTS - 1]) len(sd_rods_at_base(i))];
    perRod = [for (bw = sd_bows())
                len([for (c = ties) if (c[0] == bw[SD_ID] || c[1] == bw[SD_ID]) 1])];
    echo("");
    echo("  --- topology checks ---");
    echo(str("  bows                       ", len(sd_bows()), "   expect 15"));
    echo(str("  rod ends per base node     ", feet, "   expect all 3"));
    echo(str("  tied nodes                 ", len(nodes), "   expect 10"));
    echo(str("  rods through each node     ",
             [for (p = nodes) len(sd_bows_through(p))], "   expect all 4"));
    echo(str("  tied junctions per rod     ", perRod,
             "   expect 12 for family G (4 nodes x 3 partners) and 6 for U/L"));
    echo(str("  node heights z/R           ",
             [for (p = nodes) p.z / R]));
    echo(str("  total crossings above base ", len(sd_crossing_pairs(R)), "   expect 90"));
    echo("");
    echo(str("  rotation  72 deg is a symmetry  ", sd_rotation_is_symmetry(72),  "   expect true"));
    echo(str("  rotation 144 deg is a symmetry  ", sd_rotation_is_symmetry(144), "   expect true"));
    echo(str("  rotation  36 deg is a symmetry  ", sd_rotation_is_symmetry(36),
             "   expect false: the top pentagram is only 5-fold"));
    echo(str("  mirror at azimuth  90 deg       ", sd_mirror_is_symmetry(90),  "   expect true"));
    echo(str("  mirror at azimuth 162 deg       ", sd_mirror_is_symmetry(162), "   expect true"));
    echo(str("  => symmetry group D5, order 10"));
    echo("");
    echo(str("  max |z| of the 30 rod ends      ", max([for (z = sd_foot_heights(R)) abs(z)]),
             " mm   expect 0: every rod end sits on the ground plane"));
    echo(str("  distinct base azimuths          ",
             len([for (i = [0 : SD_BASE_POINTS - 1]) i]), "   expect 10"));
}

module sd_report() {
    sd_report_dimensions();
    sd_report_families();
    sd_report_rods();
    sd_report_base_nodes();
    sd_report_tied_nodes();
    sd_report_untied();
    sd_report_checks();
}

// ===========================================================================

star_dome();
if (reportSummary) sd_report();
