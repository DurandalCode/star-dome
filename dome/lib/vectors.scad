// ---------------------------------------------------------------------------
// vectors.scad -- small, dependency-free 3D vector helpers.
//
// Everything here is generic maths. Nothing in this file knows anything about
// the Star Dome; keep it that way so it stays reusable for connectors, belts
// and any later reinforcement studies.
//
// Units: unitless. The caller decides whether a vector is in millimetres.
// Angles: degrees, matching OpenSCAD's own trigonometric functions.
// ---------------------------------------------------------------------------

// Squared length. Useful when you only need to compare magnitudes.
function v_len2(v) = v.x * v.x + v.y * v.y + v.z * v.z;

// Euclidean length.
function v_len(v) = sqrt(v_len2(v));

// Unit vector. Returns the zero vector for a degenerate input rather than
// producing nan, so a bad input shows up as an obviously wrong picture
// instead of silently poisoning downstream arithmetic.
function v_unit(v) =
    let (l = v_len(v))
    l < 1e-12 ? [0, 0, 0] : v / l;

function v_dot(a, b) = a.x * b.x + a.y * b.y + a.z * b.z;

function v_cross(a, b) = [
    a.y * b.z - a.z * b.y,
    a.z * b.x - a.x * b.z,
    a.x * b.y - a.y * b.x
];

// Unsigned angle between two vectors, in degrees, clamped against the
// floating-point drift that can push the cosine just outside [-1, 1].
function v_angle(a, b) =
    let (c = v_dot(v_unit(a), v_unit(b)))
    acos(max(-1, min(1, c)));

// Acute angle between two *lines* (not rays), in degrees: 0..90.
// This is the meaningful measure for two rods crossing each other, where the
// direction each rod happens to be drawn in carries no physical meaning.
function v_line_angle(a, b) =
    let (t = v_angle(a, b))
    t > 90 ? 180 - t : t;

function v_dist(a, b) = v_len(a - b);

// Rotation of a point about the Z axis by `deg` degrees.
// Used constantly because the Star Dome is built by repeating one member
// around a vertical axis.
function v_rot_z(v, deg) = [
    v.x * cos(deg) - v.y * sin(deg),
    v.x * sin(deg) + v.y * cos(deg),
    v.z
];

// Point on a circle of radius r in the XY plane at height z.
function v_cyl(r, az, z = 0) = [r * cos(az), r * sin(az), z];

// Total length of an open polyline given as a list of points.
function polyline_length(pts, i = 0) =
    i >= len(pts) - 1
        ? 0
        : v_dist(pts[i], pts[i + 1]) + polyline_length(pts, i + 1);
