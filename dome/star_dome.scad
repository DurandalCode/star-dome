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
include <lib/formatting.scad>
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

/* [Debug: crossing inspection] */

// Marker + node-ID label at every crossing point.
debugCrossings = false;

// Restrict the debug display to a single symmetry class of crossing.
// -1 shows every class; 0..11 shows only that one and fades the rods that
// take no part in it. Class IDs come from the console report and the export.
debugCrossingType = -1;

// Marker size, as a multiple of the rod diameter.
debugMarkerScale = 2.6;

/* [Console report] */

// Draw the dome. Turn off to get the report or the data export on its own.
renderModel = true;

// Echo the derived dimensions, rod schedule and node table.
reportSummary = true;

// Echo the machine-readable DATA| lines that tools/export_geometry.py parses.
emitGeometryData = false;

// Decimals used in the data export.
dataDecimals = 6;

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

// Computed once here rather than inside the report modules: each of these is
// an O(n^2) pass over the 90 crossings, and recomputing them per echo line
// makes the report noticeably slow.
SD_X     = sd_crossings_full(domeRadius, rodDiameter, weaveMode, weaveGap);
SD_NODES = sd_node_points(SD_X);
SD_TYPES = sd_crossing_types(SD_X);

// Crossings belonging to one symmetry class, and the rods that take part.
function sd_selected_sig() =
    debugCrossingType >= 0 && debugCrossingType < len(SD_TYPES)
        ? SD_TYPES[debugCrossingType] : undef;

function sd_debug_crossings() =
    let (sig = sd_selected_sig())
    sig == undef ? SD_X : [for (c = SD_X) if (c[SDX_SIG] == sig) c];

function sd_debug_rod_ids() =
    let (sel = sd_debug_crossings())
    [for (i = [0 : SD_BOW_COUNT - 1])
        if (len([for (c = sel) if (c[SDX_A] == i || c[SDX_B] == i) 1]) > 0) i];

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
// When a single crossing class is selected for inspection, rods that take no
// part in it are faded rather than hidden, so the selected pair still reads in
// the context of the whole dome.
module sd_rods() {
    active = sd_debug_rod_ids();
    fade   = debugCrossings && sd_selected_sig() != undef;
    for (bw = sd_bows())
        let (
            c = sd_family_color(bw[SD_FAMILY]),
            on = !fade || sd_contains(bw[SD_ID], active)
        )
        color(on ? c : [c[0], c[1], c[2], 0.12])
            sd_swept_polyline(
                sd_bow_polyline(bw, domeRadius, rodSegments, sd_offset(bw)),
                rodDiameter);
}

// Debug display: a marker at every crossing point, with its node ID beside it.
// Markers sit on the nominal sphere. Under the layered weave the rods are
// offset onto their own shells, so a marker sits between them rather than on
// either one -- that gap is the reported radial_gap.
module sd_debug_crossing_markers() {
    sel  = sd_debug_crossings();
    size = domeRadius / 22;
    for (c = sel) {
        p     = c[SDX_POINT];
        node  = sd_node_index(SD_NODES, p);
        four  = sd_node_rod_count(SD_X, p) > 2;
        col   = c[SDX_TIED] ? COLOR_NODE : COLOR_LOOSE;
        sd_marker(p, rodDiameter * debugMarkerScale * (four ? 1.25 : 1.0), col);
        sd_label(p * (1 + size / domeRadius * 1.1), sd_node_name(node), size);
    }
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
    if (debugCrossings)      sd_debug_crossing_markers();
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
    sd_report_crossing_types();
    sd_report_checks();
}

// ===========================================================================

// ===========================================================================
// Crossing classification report
// ===========================================================================

module sd_report_crossing_types() {
    echo("");
    echo(str("  --- crossing classes: ", len(SD_TYPES),
             " symmetry-distinct geometries over ", len(SD_X), " rod pairs ---"));
    echo("  id    fams  count  tied   height mm    angle deg    inclination a/b deg");
    for (i = [0 : len(SD_TYPES) - 1]) {
        sig = SD_TYPES[i];
        mem = sd_type_members(SD_X, sig);
        c   = mem[0];
        echo(str("  ", sd_type_name(i),
                 "   ", sig[0], sig[1],
                 "     ", len(mem) < 10 ? " " : "", len(mem),
                 "    ", c[SDX_TIED] ? "yes " : "no  ",
                 "  ", num_str(c[SDX_POINT].z, 3),
                 "    ", num_str(c[SDX_ANGLE], 4),
                 "      ", num_str(c[SDX_INCA], 3), " / ", num_str(c[SDX_INCB], 3)));
    }
    angles = sd_distinct([for (c = SD_X) c[SDX_ANGLE]], 4);
    echo(str("  distinct crossing angles: ", len(angles), " -> ",
             join([for (a = angles) num_str(a, 4)], ", "), " deg"));
    echo("  NOTE: crossing angles are NOT all equal; a connector family must cover the whole set.");
}

// ===========================================================================
// Machine-readable export
//
// OpenSCAD cannot write files, so the data leaves as tagged DATA| lines and
// tools/export_geometry.py turns them into JSON and CSV. Keeping the emitter
// here means the export and the rendered dome cannot drift apart: there is
// still exactly one implementation of the geometry.
//
// Numbers go through num_str() because OpenSCAD's own number printing silently
// truncates to 6 significant digits -- see lib/formatting.scad.
// ===========================================================================

module sd_emit_data() {
    R  = domeRadius;
    dp = dataDecimals;
    pts     = sd_all_rod_points(R, rodSegments, rodDiameter, weaveMode, weaveGap);
    nominal = sd_rod_nominal_lengths(R);
    drawn   = sd_rod_drawn_lengths(R, rodDiameter, weaveMode, weaveGap);
    classes = sd_distinct(nominal, dp);

    echo("DATA|begin|star_dome_geometry|1");
    echo(str("DATA|meta|variant|", variant));
    echo(str("DATA|meta|variant_note|", sd_variant_note(variant)));
    echo("DATA|meta|units|mm");
    echo(str("DATA|meta|dome_diameter|", num_str(domeDiameter, dp)));
    echo(str("DATA|meta|dome_radius|", num_str(R, dp)));
    echo(str("DATA|meta|rod_diameter|", num_str(rodDiameter, dp)));
    echo(str("DATA|meta|weave_mode|", weaveMode));
    echo(str("DATA|meta|weave_gap|", num_str(weaveGap, dp)));
    echo(str("DATA|meta|rod_segments|", rodSegments));
    echo(str("DATA|meta|rod_count|", SD_BOW_COUNT));
    echo(str("DATA|meta|base_node_count|", SD_BASE_POINTS));
    echo(str("DATA|meta|crossing_point_count|", len(SD_NODES)));
    echo(str("DATA|meta|crossing_pair_count|", len(SD_X)));
    echo(str("DATA|meta|crossing_type_count|", len(SD_TYPES)));
    echo(str("DATA|meta|rod_length_nominal|", num_str(sd_bow_length(R), dp)));
    echo(str("DATA|meta|rod_length_class_count|", len(classes)));
    echo(str("DATA|meta|rod_length_classes|", num_list_str(classes, dp)));
    echo(str("DATA|meta|total_rod_length|", num_str(sd_total_rod_length(R), dp)));
    echo(str("DATA|meta|base_ring_length|", num_str(sd_base_ring_length(R), dp)));
    echo(str("DATA|meta|dome_height_nominal|", num_str(sd_structural_height(R), dp)));
    echo(str("DATA|meta|dome_height_measured|", num_str(sd_measured_height(pts), dp)));
    echo(str("DATA|meta|max_diameter_measured|", num_str(2 * sd_measured_max_radius(pts), dp)));
    echo(str("DATA|meta|max_diameter_incl_rod|",
             num_str(2 * sd_measured_max_radius(pts) + rodDiameter, dp)));
    echo(str("DATA|meta|base_edge_arc|", num_str(sd_base_edge_arc(R), dp)));
    echo(str("DATA|meta|base_edge_chord|", num_str(sd_base_edge_chord(R), dp)));
    echo("DATA|meta|coordinate_basis|nominal centreline on the sphere (same as weaveMode=flat); weave offsets are reported per crossing as radial_gap");
    echo("DATA|meta|inclination_convention|unsigned angle of the rod tangent above horizontal, 0..90 deg");
    echo("DATA|meta|above_convention|the rod on the outer weave shell (higher layer index); a drawing convention, not a build decision");

    echo(str("DATA|rodhead|number|name|family|foot_a|foot_b|azimuth_deg|tilt_deg",
             "|length_nominal|length_drawn|layer|radial_offset|tie_marks_deg|tie_marks_mm"));
    for (bw = sd_bows()) {
        o = sd_offset(bw);
        echo(str("DATA|rod|", bw[SD_ID] + 1, "|", bw[SD_NAME], "|", bw[SD_FAMILY],
                 "|", sd_bow_feet(bw)[0], "|", sd_bow_feet(bw)[1],
                 "|", num_str(bw[SD_AZ], dp), "|", num_str(bw[SD_TILT], dp),
                 "|", num_str(nominal[bw[SD_ID]], dp),
                 "|", num_str(drawn[bw[SD_ID]], dp),
                 "|", bw[SD_LAYER], "|", num_str(o, dp),
                 "|", num_list_str(bw[SD_TIES], dp),
                 "|", num_list_str([for (t = bw[SD_TIES]) gc_arc_length(R, 0, t)], dp)));
    }

    echo("DATA|basenodehead|index|name|x|y|z|rods");
    for (i = [0 : SD_BASE_POINTS - 1]) {
        p = sd_base_point(i, R);
        echo(str("DATA|basenode|", i, "|b", i,
                 "|", num_str(p.x, dp), "|", num_str(p.y, dp), "|", num_str(p.z, dp),
                 "|", join([for (bw = sd_rods_at_base(i)) bw[SD_NAME]], ";")));
    }

    echo("DATA|nodehead|index|name|x|y|z|rod_count|rods");
    for (i = [0 : len(SD_NODES) - 1]) {
        p = SD_NODES[i];
        echo(str("DATA|node|", i, "|", sd_node_name(i),
                 "|", num_str(p.x, dp), "|", num_str(p.y, dp), "|", num_str(p.z, dp),
                 "|", len(sd_bows_through(p)),
                 "|", join([for (b = sd_bows_through(p)) sd_bows()[b][SD_NAME]], ";")));
    }

    echo(str("DATA|crossinghead|index|node|rod_a|rod_b|family_a|family_b|x|y|z",
             "|t_a_deg|t_b_deg|s_a_mm|s_b_mm",
             "|tan_a_x|tan_a_y|tan_a_z|tan_b_x|tan_b_y|tan_b_z",
             "|angle_deg|incl_a_deg|incl_b_deg|rod_above|rod_below|radial_gap",
             "|tied|type"));
    for (i = [0 : len(SD_X) - 1]) {
        c  = SD_X[i];
        ba = sd_bows()[c[SDX_A]]; bb = sd_bows()[c[SDX_B]];
        p  = c[SDX_POINT];
        ta = c[SDX_TANA];        tb = c[SDX_TANB];
        echo(str("DATA|crossing|", i,
                 "|", sd_node_name(sd_node_index(SD_NODES, p)),
                 "|", ba[SD_NAME], "|", bb[SD_NAME],
                 "|", ba[SD_FAMILY], "|", bb[SD_FAMILY],
                 "|", num_str(p.x, dp), "|", num_str(p.y, dp), "|", num_str(p.z, dp),
                 "|", num_str(c[SDX_TA], dp), "|", num_str(c[SDX_TB], dp),
                 "|", num_str(gc_arc_length(R, 0, c[SDX_TA]), dp),
                 "|", num_str(gc_arc_length(R, 0, c[SDX_TB]), dp),
                 "|", num_str(ta.x, dp), "|", num_str(ta.y, dp), "|", num_str(ta.z, dp),
                 "|", num_str(tb.x, dp), "|", num_str(tb.y, dp), "|", num_str(tb.z, dp),
                 "|", num_str(c[SDX_ANGLE], dp),
                 "|", num_str(c[SDX_INCA], dp), "|", num_str(c[SDX_INCB], dp),
                 "|", sd_bows()[c[SDX_OUTER]][SD_NAME],
                 "|", sd_bows()[c[SDX_INNER]][SD_NAME],
                 "|", num_str(c[SDX_GAP], dp),
                 "|", c[SDX_TIED] ? 1 : 0,
                 "|", sd_type_name(sd_type_index(SD_TYPES, c[SDX_SIG]))));
    }

    echo(str("DATA|typehead|index|name|count|family_a|family_b|z|angle_deg",
             "|incl_a_deg|incl_b_deg|t_a_deg|t_b_deg|tied|example_rods"));
    for (i = [0 : len(SD_TYPES) - 1]) {
        sig = SD_TYPES[i];
        mem = sd_type_members(SD_X, sig);
        c   = mem[0];
        echo(str("DATA|type|", i, "|", sd_type_name(i), "|", len(mem),
                 "|", sig[0], "|", sig[1],
                 "|", num_str(c[SDX_POINT].z, dp),
                 "|", num_str(c[SDX_ANGLE], dp),
                 "|", num_str(c[SDX_INCA], dp), "|", num_str(c[SDX_INCB], dp),
                 "|", num_str(c[SDX_TA], dp), "|", num_str(c[SDX_TB], dp),
                 "|", c[SDX_TIED] ? 1 : 0,
                 "|", sd_bows()[c[SDX_A]][SD_NAME], ";", sd_bows()[c[SDX_B]][SD_NAME]));
    }
    echo("DATA|end|star_dome_geometry|1");
}

if (renderModel) star_dome();
if (reportSummary) sd_report();
if (emitGeometryData) sd_emit_data();
