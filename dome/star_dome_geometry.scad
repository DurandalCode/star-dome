// ---------------------------------------------------------------------------
// star_dome_geometry.scad -- the Takekawa / SimplyDifferently Star Dome topology.
//
// Pure geometry. No rendering, no modules that emit solids. Everything in here
// is a function so that the same numbers can be echoed to the console, used to
// draw rods, or later handed to connector design without a second source of
// truth.
//
// ===========================================================================
// WHAT THIS DOME IS
// ===========================================================================
//
// This is NOT a geodesic strut dome. There are no short straight struts and no
// hub connectors. There are 15 long flexible rods, all exactly the same length,
// each bent into a single continuous arc that runs the full width of the dome
// and lands on the ground at both ends. Rods simply cross each other and are
// lashed or clamped where they meet.
//
// The reference design (Daisuke Takekawa, Kyushu Fieldwork Society; written up
// by Rene K. Mueller at simplydifferently.org/Star_Dome) specifies:
//
//   * 15 full-length bows, all identical.
//   * A 10-sided base polygon, with 3 bow ends meeting at each of the
//     10 ground points.  15 bows x 2 ends = 30 ends / 10 points = 3. Exact.
//   * Bow length lbow = c / 2, where c is the base circumference.
//   * Optionally 2 more identical bows bent into the base ring itself.
//   * The cover pattern is 6 pentagons + 10 triangles of equal side.
//
// ===========================================================================
// WHY EVERY BOW IS A GREAT SEMICIRCLE
// ===========================================================================
//
// c = pi * d, so lbow = pi * d / 2 = pi * R. That is exactly the length of half
// a great circle. Two points on the ground ring can only be joined by a great
// circle if they are diametrically opposite. So each bow runs from one base
// point, over the dome, to the base point directly across from it. This also
// explains the "2 extra bows make the base ring" note: the ring is 2 * pi * R,
// which is exactly two bow lengths.
//
// Consequence: with 10 base points there are only 5 diametral axes, and 15
// bows share them 3 to an axis -- the same "3 bows from each bottom point"
// the reference states.
//
// A bow is therefore fully described by (azimuth of its start point, tilt of
// its plane). See lib/great_circles.scad for the parameterisation. Arc angle t
// runs 0..180 along a bow and is proportional to length, so the reference
// instruction "mark the rod in thirds" means t = 60 and t = 120, and "mark it
// in fifths" means t = 36, 72, 108, 144.
//
// ===========================================================================
// THE THREE FAMILIES, AND HOW THEIR TILTS ARE DERIVED
// ===========================================================================
//
// The reference marking diagram is the key that pins the geometry down. It
// shows three groups of identically-marked rods:
//
//   10x  marked in THIRDS  (2 junctions each)   <- drawn blue
//    5x  marked in FIFTHS  (4 junctions each)   <- drawn green
//    2x  marked in FIFTHS, used for the base ring <- drawn red
//
// FAMILY G -- the 5 rods marked in fifths.
//   These are the dome's icosidodecahedral skeleton. Take an icosidodecahedron
//   (12 pentagons + 20 triangles, all edges equal) and orient it with one of
//   its 6 equatorial decagons horizontal. That decagon is the base ring and its
//   10 vertices are the base points. The other 5 equatorial decagons each cut
//   the ground plane at one diametral pair of base points, and each of their
//   upper halves is exactly 5 edges long -- one bow, marked in fifths, with the
//   4 interior marks landing on icosidodecahedron vertices.
//
//   Their tilt is the angle between two adjacent 5-fold axes of an
//   icosahedron: atan(2) = 63.4349 deg. This model asserts, rather than
//   assumes, that this tilt puts the G-G crossings exactly at t = 36, 72, 108
//   and 144 -- i.e. exactly on the fifth marks.
//
//   Family G plus the base ring is precisely the hemisphere of the
//   icosidodecahedron: 6 pentagons + 10 triangles. That is the reference's
//   cover pattern, and it is what "developed from a 2V geodesic dome" means.
//
// FAMILY U and FAMILY L -- the 10 rods marked in thirds.
//   Takekawa's addition. Family G alone puts only one bow at each base point;
//   these two families bring it to the stated three. Each is a set of 5 great
//   semicircles on the same 5 diametral axes, tilted so that their thirds
//   marks (t = 60 and t = 120) land exactly on the crossing nodes that family
//   G already created:
//
//     Family U (upper) -> the 5 high nodes,  z = 0.85065 * R
//     Family L (lower) -> the 5 lower nodes, z = 0.52573 * R
//
//   Both tilts are computed here from the G-G node heights, not typed in:
//
//     sin(60) * sin(tilt) = z_node   =>   tilt = asin(z_node / sin(60))
//
//   giving 79.1877 deg for U and 37.3774 deg for L.
//
// The result reproduces the reference marking diagram exactly, which is the
// strongest check available: 10 tied nodes, each joining 4 rods; every G rod
// tied at 4 points, all on fifth marks; every U and L rod tied at 2 points,
// both on third marks. 5*4 + 10*2 = 40 junction ends = 2 * 20 rod ends per
// node group. Nothing is left over and nothing is missing.
//
// The 5 high nodes are the pentagon at the top of the dome that the reference
// construction describes; the 5 lower nodes are the surrounding pentagon.
//
// ===========================================================================
// ASSUMPTIONS -- see dome/README.md for the full list
// ===========================================================================
//
// The reference gives a construction procedure and a marking diagram, not
// coordinates. The reading above is reconstructed from those two things plus
// the stated bow length. Where it could not be resolved from the source it is
// flagged in dome/README.md.
// ---------------------------------------------------------------------------

include <lib/great_circles.scad>

// --- base polygon -----------------------------------------------------------

// The reference calls for a 10-sided base polygon. Written as a constant
// rather than a literal so the derived quantities below read as maths.
SD_BASE_POINTS = 10;
SD_BASE_STEP   = 360 / SD_BASE_POINTS;   // 36 deg between adjacent base points

// Number of continuous members, and the split the reference marking diagram
// gives them.
SD_BOW_COUNT      = 15;
SD_FAMILY_SIZE    = 5;    // 5 bows per family, stepped 72 deg apart
SD_BASE_BOW_COUNT = 2;    // the optional pair bent into the ground ring

// --- family tilts -----------------------------------------------------------

// Family G: the icosidodecahedral decagons. Adjacent 5-fold axes of an
// icosahedron are atan(2) apart, so a decagon whose axis is tilted by that
// amount from vertical sits at that same angle from the ground plane.
SD_TILT_G = atan(2);      // 63.43495 deg

// Where family G crosses itself. Taken as actual great-circle intersections so
// the node ring heights are derived, never typed.
//   neighbours two base steps apart -> the HIGH nodes (the top pentagon)
//   neighbours four base steps apart -> the LOW nodes
SD_NODE_HIGH_DIR = gc_intersection(1 * SD_BASE_STEP, SD_TILT_G,
                                   3 * SD_BASE_STEP, SD_TILT_G);
SD_NODE_LOW_DIR  = gc_intersection(1 * SD_BASE_STEP, SD_TILT_G,
                                   5 * SD_BASE_STEP, SD_TILT_G);

SD_Z_HIGH = SD_NODE_HIGH_DIR.z;   // 0.850651 -- as a fraction of R
SD_Z_LOW  = SD_NODE_LOW_DIR.z;    // 0.525731

// Junction marks, as fractions of a bow's length. Straight from the reference
// marking diagram. Because bows are great circles, fraction * 180 = arc angle.
SD_TIE_FRACTIONS_G = [1/5, 2/5, 3/5, 4/5];   // "marked in fifths"
SD_TIE_FRACTIONS_B = [1/3, 2/3];             // "marked in thirds"

SD_TIE_ANGLES_G = [for (f = SD_TIE_FRACTIONS_G) 180 * f];   // 36 72 108 144
SD_TIE_ANGLES_B = [for (f = SD_TIE_FRACTIONS_B) 180 * f];   // 60 120

// Families U and L must pass through the existing G-G nodes at their own
// thirds marks. On a bow of tilt a, the point at arc angle t sits at height
// sin(t) * sin(a) * R, so the tilt that puts the first third mark on a node of
// height z is asin(z / sin(60)).
SD_TILT_U = asin(SD_Z_HIGH / sin(SD_TIE_ANGLES_B[0]));   // 79.18768 deg
SD_TILT_L = asin(SD_Z_LOW  / sin(SD_TIE_ANGLES_B[0]));   // 37.37737 deg

// --- self-checks ------------------------------------------------------------
// These are the load-bearing claims of the reconstruction. If a future edit
// breaks one, the render should stop rather than quietly produce a dome that
// no longer matches the reference marking diagram.

assert(abs(gc_param_of_point(1 * SD_BASE_STEP, SD_TILT_G, SD_NODE_HIGH_DIR) - 108) < 1e-6,
       "family G self-crossing must land on the 3/5 mark");
assert(abs(gc_param_of_point(1 * SD_BASE_STEP, SD_TILT_G, SD_NODE_LOW_DIR) - 144) < 1e-6,
       "family G self-crossing must land on the 4/5 mark");

// --- the bow table ----------------------------------------------------------
//
// Each family is 5 bows generated by stepping 2 base positions at a time, i.e.
// rotating by 72 deg. Family G starts on the odd base points and families U
// and L on the even ones; that offset is what interleaves the top pentagon
// with the pentagon below it.
//
// Record layout. Index constants rather than raw numbers so call sites read.
SD_ID = 0;   // 0..14, stable rod number is SD_ID + 1
SD_NAME = 1; SD_FAMILY = 2; SD_START = 3; SD_AZ = 4; SD_TILT = 5;
SD_TIES = 6; // tie marks as arc angles
SD_LAYER = 7; // weave shell, 0 = innermost

SD_FAMILY_STARTS_G = [1, 3, 5, 7, 9];    // odd base points
SD_FAMILY_STARTS_U = [0, 2, 4, 6, 8];    // even base points
SD_FAMILY_STARTS_L = [0, 2, 4, 6, 8];

function sd_family_spec() = [
    // [family letter, start indices, tilt, tie angles, human description]
    ["G", SD_FAMILY_STARTS_G, SD_TILT_G, SD_TIE_ANGLES_G,
     "icosidodecahedral decagon halves, marked in fifths"],
    ["U", SD_FAMILY_STARTS_U, SD_TILT_U, SD_TIE_ANGLES_B,
     "upper bracing bows, thirds marks on the top pentagon nodes"],
    ["L", SD_FAMILY_STARTS_L, SD_TILT_L, SD_TIE_ANGLES_B,
     "lower bracing bows, thirds marks on the lower pentagon nodes"]
];

// The 15 bows, in a stable order: G1..G5, U1..U5, L1..L5.
// Rod number = SD_ID + 1, so rods 1-5 are family G, 6-10 U, 11-15 L.
function sd_bows() = [
    for (fi = [0 : len(sd_family_spec()) - 1])
        let (f = sd_family_spec()[fi])
        for (k = [0 : len(f[1]) - 1])
            let (start = f[1][k], id = fi * 5 + k)
            [ id,
              str(f[0], k + 1),
              f[0],
              start,
              start * SD_BASE_STEP,
              f[2],
              f[3],
              id ]
];

// The 2 optional base-ring bows. Each is bent into half the ground ring, so
// each covers 5 of the 10 base edges -- hence "marked in fifths" like family G.
function sd_base_bows() = [
    for (k = [0 : SD_BASE_BOW_COUNT - 1])
        [ SD_BOW_COUNT + k, str("B", k + 1), "B", k * 5,
          k * 5 * SD_BASE_STEP, 0, SD_TIE_ANGLES_G, -1 ]
];

// --- weave ------------------------------------------------------------------
//
// Every pair of the 15 bows crosses somewhere on the sphere, and in the exact
// mathematical model all of them lie on that one sphere, so at every crossing
// two centrelines coincide. Real rods cannot do that -- one passes outside the
// other.
//
// "layered" gives each bow its own thin shell, spaced by the rod diameter, so
// no two centrelines ever coincide and every crossing reads as a clean
// over/under. Because all 15 bows cross each other, constant offsets need all
// 15 shells to be distinct; the band is (SD_BOW_COUNT - 1) * gap * rod
// diameter thick and is centred on the nominal sphere, so the mean radius and
// the total rod length are unchanged.
//
// "flat" puts every centreline exactly on the nominal sphere. Use it for
// measurement and for exporting true centrelines; do not use it to judge how
// the crossings look.
function sd_layer_offset(bow, rod_diameter, mode = "layered", gap = 1.0) =
    mode == "flat"
        ? 0
        : (bow[SD_LAYER] - (SD_BOW_COUNT - 1) / 2) * rod_diameter * gap;

// --- points and polylines ---------------------------------------------------

function sd_base_point(i, radius) = v_cyl(radius, i * SD_BASE_STEP, 0);

function sd_base_points(radius) =
    [for (i = [0 : SD_BASE_POINTS - 1]) sd_base_point(i, radius)];

function sd_bow_point(bow, t, radius, offset = 0) =
    gc_bow_point(bow[SD_AZ], bow[SD_TILT], t, radius + offset);

function sd_bow_polyline(bow, radius, segments, offset = 0) =
    gc_bow_polyline(bow[SD_AZ], bow[SD_TILT], radius, segments, 0, 180, offset);

// Tie-mark positions along one bow, as points.
function sd_bow_tie_points(bow, radius, offset = 0) =
    [for (t = bow[SD_TIES]) sd_bow_point(bow, t, radius, offset)];

// The two base points a bow lands on. They are diametrically opposite.
function sd_bow_feet(bow) =
    [bow[SD_START], (bow[SD_START] + SD_BASE_POINTS / 2) % SD_BASE_POINTS];

// --- crossings --------------------------------------------------------------
//
// Found analytically from plane normals, so these are exact, not sampled.
// A pair sharing a diametral axis meets on the ground ring rather than in the
// air; gc_intersection returns undef for those and they are skipped here. They
// are reported separately as base connections.
//
// Record: [ id_a, id_b, point, t_a, t_b, crossing angle (deg) ]
function sd_crossing_pairs(radius) = [
    for (a = [0 : SD_BOW_COUNT - 2])
        for (b = [a + 1 : SD_BOW_COUNT - 1])
            let (
                ba = sd_bows()[a], bb = sd_bows()[b],
                dir = gc_intersection(ba[SD_AZ], ba[SD_TILT], bb[SD_AZ], bb[SD_TILT])
            )
            if (dir != undef)
                let (
                    ta = gc_param_of_point(ba[SD_AZ], ba[SD_TILT], dir),
                    tb = gc_param_of_point(bb[SD_AZ], bb[SD_TILT], dir)
                )
                [ a, b, dir * radius, ta, tb,
                  v_line_angle(gc_bow_tangent(ba[SD_AZ], ba[SD_TILT], ta),
                               gc_bow_tangent(bb[SD_AZ], bb[SD_TILT], tb)) ]
];

// A crossing counts as TIED when it falls on a marked junction of both rods.
function sd_is_tied(cross, tol = 1e-6) =
    let (ba = sd_bows()[cross[0]], bb = sd_bows()[cross[1]])
    sd_angle_is_marked(ba, cross[3], tol) && sd_angle_is_marked(bb, cross[4], tol);

function sd_angle_is_marked(bow, t, tol = 1e-6) =
    len([for (m = bow[SD_TIES]) if (abs(m - t) < tol) 1]) > 0;

function sd_tied_pairs(radius) =
    [for (c = sd_crossing_pairs(radius)) if (sd_is_tied(c)) c];

function sd_untied_pairs(radius) =
    [for (c = sd_crossing_pairs(radius)) if (!sd_is_tied(c)) c];

// The 10 distinct tied nodes, derived as the family-G self-crossings.
// Family G is the first SD_FAMILY_SIZE entries of sd_bows(), and every pair of
// its members crosses once above ground: C(5,2) = 10 nodes. Every one of them
// also carries exactly 2 bracing bows, which sd_bows_through() confirms.
function sd_tied_nodes(radius) = [
    for (a = [0 : SD_FAMILY_SIZE - 2])
        for (b = [a + 1 : SD_FAMILY_SIZE - 1])
            let (dir = gc_intersection(sd_bows()[a][SD_AZ], SD_TILT_G,
                                       sd_bows()[b][SD_AZ], SD_TILT_G))
            if (dir != undef) dir * radius
];

// Which bows pass through a given point (a point is on a bow's great circle
// when it lies in the bow's plane).
function sd_bows_through(p, tol = 1e-6) = [
    for (bw = sd_bows())
        if (abs(v_dot(gc_bow_normal(bw[SD_AZ], bw[SD_TILT]), v_unit(p))) < tol)
            bw[SD_ID]
];

// --- derived dimensions -----------------------------------------------------

// Length of one bow. Every bow is half a great circle, so they are all equal --
// the property the whole design is built around.
function sd_bow_length(radius) = gc_arc_length(radius);

function sd_total_rod_length(radius) = SD_BOW_COUNT * sd_bow_length(radius);

function sd_base_ring_length(radius) = 2 * PI * radius;

// Highest point of the structure. It is NOT the top of the sphere: no bow runs
// over the zenith, so the apex of the tallest family is the top of the dome.
function sd_structural_height(radius) =
    radius * max([for (bw = sd_bows()) sin(bw[SD_TILT])]);

// Base polygon edge, both ways. The reference works in arc length (its base
// ring is two bent rods); the straight chord is what a cover panel or a
// ground beam would actually measure.
function sd_base_edge_arc(radius)   = 2 * PI * radius / SD_BASE_POINTS;
function sd_base_edge_chord(radius) = 2 * radius * sin(SD_BASE_STEP / 2);

// --- symmetry ---------------------------------------------------------------
//
// The dome has D5 symmetry, order 10: rotation by 72 degrees, plus 5 mirror
// planes. Note what is NOT there -- rotation by 36 degrees maps the base
// decagon onto itself but does not map the rod set onto itself, because the
// pentagram at the top only has 5-fold symmetry. That is why the 10 base points
// fall into two rotational classes that the mirrors then tie together.
//
// A bow is identified by (start azimuth, tilt). Under the mirror through
// azimuth 90 the bow starting at az becomes the bow starting at -az: the
// mirror image runs the other way round, so it is indexed from its far foot.

function sd_norm_az(a) = ((a % 360) + 360) % 360;

function sd_has_bow(az, tilt, tol = 1e-6) =
    len([for (bw = sd_bows())
            if (abs(sd_norm_az(bw[SD_AZ]) - sd_norm_az(az)) < tol
                && abs(bw[SD_TILT] - tilt) < tol) 1]) > 0;

// True when rotating the whole rod set by `deg` about Z reproduces it exactly.
function sd_rotation_is_symmetry(deg) =
    len([for (bw = sd_bows()) if (!sd_has_bow(bw[SD_AZ] + deg, bw[SD_TILT])) 1]) == 0;

// True when mirroring about the vertical plane at `az_plane` reproduces it.
function sd_mirror_is_symmetry(az_plane) =
    len([for (bw = sd_bows())
            if (!sd_has_bow(2 * az_plane - bw[SD_AZ] + 180, bw[SD_TILT])) 1]) == 0;

// Every bow ends on the ground plane at both ends, by construction: the bow
// runs t = 0..180 and both of those arc angles sit on the equator. This
// recomputes it from the drawn endpoints rather than asserting it.
function sd_foot_heights(radius) =
    [for (bw = sd_bows())
        each [sd_bow_point(bw, 0, radius).z, sd_bow_point(bw, 180, radius).z]];
