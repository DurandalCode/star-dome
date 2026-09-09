// ---------------------------------------------------------------------------
// great_circles.scad -- great-circle ("bow") maths on a sphere.
//
// The Star Dome is built from long flexible rods that are all bent into arcs
// lying on one sphere. An unconstrained elastic rod held against a sphere
// settles onto a great circle, so a great circle is the right idealisation for
// a Takekawa bow, and it is the reason every bow in the reference design comes
// out at exactly the same length.
//
// A "bow" here is the upper half of a great circle whose two ends sit on the
// equator, i.e. on the ground ring. Two points on the equator can only be
// joined by a great circle if they are diametrically opposite, which is why
// every Star Dome bow spans the full width of the dome.
//
// A bow is described by two numbers:
//
//   az    -- azimuth (degrees) of the base point the bow starts from.
//   tilt  -- angle (degrees) between the bow's plane and the ground plane.
//            tilt = 90 gives a bow straight over the zenith; smaller tilts
//            give flatter bows whose apex leans away from the start point.
//
// The bow is parameterised by an arc angle t in [0, 180] degrees. Because the
// arc is a great circle, t is proportional to arc length: t = 180 * (l / lbow).
// This is what makes the reference construction's "mark the rod in thirds /
// fifths" instructions translate directly into angles.
//
// Local frame before the azimuth rotation:
//
//   P(t) = R * ( cos t, sin t * cos(tilt), sin t * sin(tilt) )
//
//   t = 0    -> the start base point, on +X
//   t = 90   -> the apex of the bow
//   t = 180  -> the opposite base point, on -X
//
// Angles are degrees throughout, matching OpenSCAD's trig functions.
// ---------------------------------------------------------------------------

include <vectors.scad>

// Point on a bow at arc angle t, on a sphere of radius radius.
function gc_bow_point(az, tilt, t, radius = 1) =
    v_rot_z(radius * [cos(t), sin(t) * cos(tilt), sin(t) * sin(tilt)], az);

// Unit tangent of a bow at arc angle t, pointing in the direction of
// increasing t. This is the rod's local axis, and the thing to compare when
// asking at what angle two rods cross.
function gc_bow_tangent(az, tilt, t) =
    v_unit(v_rot_z([-sin(t), cos(t) * cos(tilt), cos(t) * sin(tilt)], az));

// Unit normal of the plane the bow lies in. Two bows intersect along the cross
// product of their plane normals, which is how every crossing below is found:
// analytically, never by sampling and searching for near-misses.
function gc_bow_normal(az, tilt) =
    v_unit(v_rot_z([0, -sin(tilt), cos(tilt)], az));

// Recover the arc angle t of a point that is known to lie on a given bow.
// Inverse of gc_bow_point; used to express a crossing as "a fraction along
// rod n", which is the number you actually need when marking a real rod.
function gc_param_of_point(az, tilt, p) =
    let (q = v_rot_z(p, -az))
    atan2(sqrt(q.y * q.y + q.z * q.z), q.x);

// The two points where two great circles meet, as a unit vector pair (+d, -d).
// Returns the one in the upper hemisphere. Returns undef when the circles are
// the same circle, or when they meet on the equator -- for the Star Dome the
// equator case means "these two bows share a base point", which is a ground
// connection rather than a crossing and is reported separately.
function gc_intersection(az1, tilt1, az2, tilt2, eps = 1e-7) =
    let (
        n1 = gc_bow_normal(az1, tilt1),
        n2 = gc_bow_normal(az2, tilt2),
        c  = v_cross(n1, n2)
    )
    v_len(c) < eps
        ? undef
        : let (d = v_unit(c), up = d.z < 0 ? -d : d)
          up.z < eps ? undef : up;

// Sample a bow into a polyline of `segments` straight pieces.
// `radial_offset` shifts the whole arc off the nominal sphere; the Star Dome
// model uses it to lift each rod onto its own thin shell so that crossing rods
// pass over and under one another instead of sharing a centreline.
function gc_bow_polyline(az, tilt, radius, segments, t_from = 0, t_to = 180, radial_offset = 0) =
    [for (i = [0 : segments])
        gc_bow_point(az, tilt, t_from + (t_to - t_from) * i / segments,
                     radius + radial_offset)];

// Arc length of a great-circle bow. A full half circle is pi * radius, which
// is exactly half the circumference of the dome's base ring -- the identity
// the reference design is built on.
function gc_arc_length(radius, t_from = 0, t_to = 180) =
    PI * radius * (t_to - t_from) / 180;
