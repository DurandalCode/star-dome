"""Shared FreeCAD helpers for the connector generators.

What belongs here is what several parts do *identically*: raise a rod, cut a
hex socket, fillet a set of edges, judge an overhang, keep a parameter
spreadsheet, write a solid out for the slicer. None of it knows anything about
the dome -- it is a small CAD toolbox, and the dome geometry reaches it as
numbers that `stardome/` derived.

What deliberately stays in each part is the part: `build`, `verify`,
`derived_rows`, `populate`, `apply_view`, and the channel and plate shapes that
give a connector its character. Those share names across the generators but
only 2-40% of their text, because they are four different objects. Merging them
would buy a hundred lines and cost the ability to read any one part start to
finish.

`fan_node_v1.py` does not import this module. It is frozen as a record of the
superseded design, the same way `dome/star_dome.scad` is frozen as a reference
implementation, so a later change here cannot rewrite history.

Loading it: the generators are `exec()`d inside FreeCAD, where the source has
no `__file__`, so each one resolves the repository root first and puts this
directory on `sys.path`. See the preamble in any of them.
"""

import math
import os

import FreeCAD as App
import Part

# --------------------------------------------------------------------------
# printing
# --------------------------------------------------------------------------
# The steepest wall FDM will hold without support, and the face area below
# which a stray sliver is not worth reporting as the worst overhang.
OVERHANG_LIMIT_DEG = 45.0
NEGLIGIBLE_FACE_MM2 = 5.0

# Mesh tolerances for the STL that goes to the slicer. Shape.exportStl()
# tessellates at a default fine enough to produce ~24 MB for a 48 mm part,
# which is useless to a slicer; 0.02 mm linear is well under any FDM nozzle's
# resolution and lands around 1 MB.
LINEAR_DEFLECTION = 0.02
ANGULAR_DEFLECTION = 0.5


# --------------------------------------------------------------------------
# solids
# --------------------------------------------------------------------------
def direction(azimuth_deg):
    """Unit vector in the horizontal plane at this azimuth."""
    a = math.radians(azimuth_deg)
    return App.Vector(math.cos(a), math.sin(a), 0.0)


def rod_solid(radius, length, azimuth_deg, z):
    """A rod passing through the node: centred on the hub axis."""
    d = direction(azimuth_deg)
    base = App.Vector(-d.x * length / 2.0, -d.y * length / 2.0, z)
    return Part.makeCylinder(radius, length, base, d)


def rod_from_hub(radius, length, azimuth_deg, z, reach_back):
    """A rod that ENDS at the node, running one way only.

    A base hub's bows stop there rather than crossing, so the rod is a ray,
    not a line. `reach_back` draws it that far past the centre anyway, which
    is only for interference checking -- the real rod stops at the hub.
    """
    d = direction(azimuth_deg)
    start = App.Vector(-d.x * reach_back, -d.y * reach_back, z)
    return Part.makeCylinder(radius, length + reach_back, start, d)


def hex_prism(across_flats, height, base):
    """A hex socket or nut trap, measured across the flats as fasteners are."""
    r = across_flats / math.sqrt(3.0)
    pts = []
    for i in range(6):
        a = math.radians(60 * i)
        pts.append(
            App.Vector(base.x + r * math.cos(a), base.y + r * math.sin(a), base.z)
        )
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, 0, height))


def arm(length, width, height, z, azimuth_deg):
    """A spar running out from the hub along one azimuth."""
    box = Part.makeBox(length, width, height, App.Vector(0.0, -width / 2.0, z))
    box.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), azimuth_deg)
    return box


def azimuths_from_gaps(gaps, start=0.0):
    """Running sum of the gaps between arms: n gaps give n+1 azimuths.

    `start` is where the first arm sits, which is what ties a part's frame to
    the ground. A base hub passes its first arm's rise above horizontal, so
    +X is horizontal and a Top view shows the part as it stands; without it
    the frame is whatever the drawing happened to be rotated to.

    A fan that closes on itself has one more gap than it has arms -- the last
    one runs back to the first -- so those callers pass `gaps[:-1]`.
    """
    out = [start]
    for gap in gaps:
        out.append(out[-1] + gap)
    return out


# --------------------------------------------------------------------------
# validity and edges
# --------------------------------------------------------------------------
def ok(shape):
    """One sound solid with volume -- what every boolean here must return."""
    try:
        return shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 0
    except Exception:
        return False


def has_volume(shape):
    """A sound shape with material in it -- however many solids that is.

    The looser sibling of `ok`. Intersecting a rod with a plate can land two
    or three separate lumps in one shape, and for "did these two things meet
    at all" that is a yes, not a malformed result.
    """
    try:
        return shape is not None and shape.isValid() and shape.Volume > 0.0
    except Exception:
        return False


def vol(shape):
    """Volume, or zero for anything that is not a usable solid.

    Interference checks intersect shapes that may not meet at all, and an
    empty common() has no Volume to ask for.
    """
    try:
        return shape.Volume
    except Exception:
        return 0.0


def is_vertical_edge(edge, tol=1e-6):
    """A straight edge running parallel to Z -- a plate's corner, typically."""
    try:
        if not isinstance(edge.Curve, Part.Line):
            return False
    except Exception:
        return False
    d = edge.Vertexes[-1].Point.sub(edge.Vertexes[0].Point)
    return abs(d.x) < tol and abs(d.y) < tol and abs(d.z) > tol


def fillet_by_predicate(shape, pred, radius, max_pass=2):
    """Fillet every edge matching `pred`, backing off until it takes.

    OCC refuses a fillet that would eat its own neighbour, and refuses the
    whole set if one edge in it is impossible. So: try the batch at three
    radii, and if the batch will not go, walk the edges one at a time at four
    radii each. Returns the shape and how many edges actually took.
    """
    if radius <= 0:
        return shape, 0
    edges = [e for e in shape.Edges if pred(e)]
    if not edges:
        return shape, 0
    for r in (radius, radius * 0.7, radius * 0.45):
        try:
            out = shape.makeFillet(r, edges).removeSplitter()
            if ok(out):
                return out, len(edges)
        except Exception:
            pass

    out = shape
    done = set()
    applied = 0
    for _ in range(len(edges) * max_pass):
        target = None
        for e in out.Edges:
            if not pred(e):
                continue
            # Filleting renumbers the edges, so identity is the position of
            # the edge's midpoint, not its index.
            key = tuple(
                round(c, 3)
                for c in (e.CenterOfMass.x, e.CenterOfMass.y, e.CenterOfMass.z)
            )
            if key in done:
                continue
            target = (e, key)
            break
        if target is None:
            break
        e, key = target
        done.add(key)
        for r in (radius, radius * 0.7, radius * 0.45, radius * 0.25):
            try:
                candidate = out.makeFillet(r, [e]).removeSplitter()
                if ok(candidate):
                    out = candidate
                    applied += 1
                    break
            except Exception:
                pass
    return out, applied


# --------------------------------------------------------------------------
# printability
# --------------------------------------------------------------------------
def _outward_normal(shape, face, u, v, eps=0.05):
    """The face normal that points out of the solid, or None where it cannot
    be told.

    `normalAt` follows the surface's own parameterisation, which after a cut
    may point into the material. Probing just off the surface settles it --
    except where the sample lands on the face's own edge, and then the probe
    ahead is outside the face's patch rather than outside the SOLID, and a
    single probe reads it as material. That is not an obscure case: a hexagon
    sampled on a square grid put four of its twelve usable samples on its own
    boundary, which is how the base hub's stake nut pocket -- a pocket that
    opens UPWARDS, away from the bed -- came to be reported as 91 mm2 of flat
    ceiling.

    So probe both ways. Agreement means the sample is on an edge and settles
    nothing; a caller that cannot use a normal should drop it rather than take
    the wrong one.
    """
    p = face.valueAt(u, v)
    n = face.normalAt(u, v)
    ahead = App.Vector(p.x + n.x * eps, p.y + n.y * eps, p.z + n.z * eps)
    behind = App.Vector(p.x - n.x * eps, p.y - n.y * eps, p.z - n.z * eps)
    into = shape.isInside(ahead, 1e-7, True)
    if into == shape.isInside(behind, 1e-7, True):
        return None
    return App.Vector(-n.x, -n.y, -n.z) if into else n


def printability(shape, flipped=False, samples=5):
    """Overhangs for one print orientation.

    See docs/fan-node-v1.md for the five ways this check was wrong before it
    was right. The short version: sample each face rather than trusting one
    normal, ignore the face sitting on the bed, and count a channel roof as a
    bridge rather than an overhang.
    """
    sign = 1.0 if flipped else -1.0
    zs = [v.Point.z for v in shape.Vertexes]
    if not zs:
        return {}
    bed_z = max(zs) if flipped else min(zs)
    worst = 90.0
    worst_area = 0.0
    steep_area = 0.0
    bridge_area = 0.0
    flat_area = 0.0
    for face in shape.Faces:
        u0, u1, v0, v1 = face.ParameterRange
        normals = []
        for i in range(samples):
            for j in range(samples):
                u = u0 + (u1 - u0) * (i + 0.5) / samples
                v = v0 + (v1 - v0) * (j + 0.5) / samples
                try:
                    if not face.isPartOfDomain(u, v):
                        continue
                    normal = _outward_normal(shape, face, u, v)
                except Exception:
                    continue
                if normal is not None:   # None means the sample sat on an edge
                    normals.append(normal)
        if not normals:
            continue
        face_zs = [vx.Point.z for vx in face.Vertexes]
        if not face_zs:
            continue
        if abs(max(face_zs) - bed_z) < 0.01 and abs(min(face_zs) - bed_z) < 0.01:
            continue
        face_worst = 90.0
        for n in normals:
            if n.z * sign <= 1e-3:
                continue
            face_worst = min(face_worst, math.degrees(math.acos(min(1.0, abs(n.z)))))

        # A rod channel's roof is a BRIDGE: a horizontal-axis cylindrical
        # surface, walled on both sides, exactly like the top of every
        # horizontal hole in every printed part. FDM spans that routinely.
        # Counting it as an unsupported overhang makes a sound part look
        # broken, so it is reported separately.
        bridged = False
        try:
            surface = face.Surface
            # A flare tilts each channel piece by up to the tilt allowance, so
            # a channel wall's axis is near-horizontal rather than exactly so.
            # Bolt holes are vertical, |z| ~ 1.
            if isinstance(surface, Part.Cylinder) and abs(surface.Axis.z) < 0.2:
                bridged = True
        except Exception:
            pass

        if face_worst < OVERHANG_LIMIT_DEG:
            if bridged:
                bridge_area += face.Area
                continue
            steep_area += face.Area
        if face.Area >= NEGLIGIBLE_FACE_MM2 and face_worst < worst:
            worst = face_worst
            worst_area = round(face.Area, 2)
        if all(n.z * sign > 0.999 for n in normals):
            flat_area += face.Area
    return {
        "worst_overhang_deg": round(worst, 2),
        "worst_overhang_face_area_mm2": worst_area,
        "area_steeper_than_limit_mm2": round(steep_area, 2),
        "bridged_channel_area_mm2": round(bridge_area, 2),
        "flat_ceiling_area_mm2": round(flat_area, 2),
    }


# --------------------------------------------------------------------------
# document and parameter sheet
# --------------------------------------------------------------------------
SHEET_NAME = "Parameters"


def document(name, path=None):
    """The document to build into: reopen a saved one, or start it."""
    if path and os.path.exists(path):
        return App.openDocument(path)
    if name in App.listDocuments():
        return App.getDocument(name)
    return App.newDocument(name)


def find_sheet(doc):
    """The parameter sheet, if this document already carries one."""
    for obj in doc.Objects:
        if obj.Name == SHEET_NAME or obj.Label == SHEET_NAME:
            return obj
    for obj in doc.Objects:
        if obj.TypeId == "Spreadsheet::Sheet":
            return obj
    return None


def read_or_build_parameters(doc, inputs, use_sheet=True):
    """Defaults from the INPUTS table, overridden by the document's sheet.

    This is what makes the saved .FCStd a parameter store rather than a
    picture: edit a value in the spreadsheet, rerun, and the part rebuilds
    around it. Anything unreadable falls back to the default rather than
    failing, because a half-edited sheet should still build.
    """
    values = {alias: value for (alias, value, _unit, _note) in inputs}
    sheet = find_sheet(doc)
    if sheet is None:
        sheet = doc.addObject("Spreadsheet::Sheet", SHEET_NAME)
        sheet.Label = SHEET_NAME
    elif use_sheet:
        for alias in list(values):
            try:
                values[alias] = float(sheet.get(alias))
            except Exception:
                pass
    return sheet, values


def _cell(value):
    """A spreadsheet cell, and whether it is worth an alias.

    Numbers get an alias so expressions elsewhere in the document can point at
    them; text like "L30x30x3" or "slide, 1.4 mm" cannot be referenced and
    does not get one.
    """
    try:
        return repr(round(float(value), 4)), True
    except (TypeError, ValueError):
        return str(value), False


def write_parameters(doc, sheet, inputs, values, derived, title):
    """Rewrite the parameter sheet: the inputs, then what they produced.

    The inputs are aliased so they can be edited and read back;
    `read_or_build_parameters` is the other half of that.
    """
    if sheet is None:
        sheet = find_sheet(doc)
    if sheet is None:
        sheet = doc.addObject("Spreadsheet::Sheet", SHEET_NAME)
        sheet.Label = SHEET_NAME
    sheet.clearAll()
    sheet.set("A1", title)

    row = 3
    sheet.set("A%d" % row, "INPUT")
    sheet.set("B%d" % row, "value")
    sheet.set("C%d" % row, "unit")
    sheet.set("D%d" % row, "note")
    row += 1
    for alias, default, unit, note in inputs:
        sheet.set("A%d" % row, alias)
        sheet.set("B%d" % row, repr(float(values.get(alias, default))))
        sheet.set("C%d" % row, unit)
        sheet.set("D%d" % row, note)
        # Without an alias the cell is a report, not a parameter store.
        try:
            sheet.setAlias("B%d" % row, alias)
        except Exception:
            pass
        row += 1

    row += 1
    sheet.set("A%d" % row, "DERIVED")
    sheet.set("B%d" % row, "value")
    sheet.set("C%d" % row, "unit")
    sheet.set("D%d" % row, "derived - overwritten by the generator")
    row += 1
    for alias, value, unit, note in derived:
        text, aliasable = _cell(value)
        sheet.set("A%d" % row, alias)
        sheet.set("B%d" % row, text)
        sheet.set("C%d" % row, unit)
        sheet.set("D%d" % row, note)
        if aliasable:
            try:
                sheet.setAlias("B%d" % row, alias)
            except Exception:
                pass
        row += 1
    return sheet


# --------------------------------------------------------------------------
# export
# --------------------------------------------------------------------------
def export_solid(shape, stem, out_dir):
    """STEP for CAD, STL for the slicer. Returns both paths and the facet count."""
    import MeshPart

    step_path = os.path.join(out_dir, stem + ".step")
    stl_path = os.path.join(out_dir, stem + ".stl")
    shape.exportStep(step_path)
    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=LINEAR_DEFLECTION,
        AngularDeflection=ANGULAR_DEFLECTION,
        Relative=False,
    )
    mesh.write(stl_path)
    return step_path, stl_path, mesh.CountFacets


# --------------------------------------------------------------------------
# fasteners, sized from the rod
# --------------------------------------------------------------------------
# Every connector here used to carry an M5 set as a constant, whatever rod it
# was drawn around. That is why a clamp on a 6 mm rod came out eight times the
# rod across and one on a 16 mm rod only three and a half: the part was sized
# by the bolt, and the bolt never moved.
#
# **The rule is a convention, not a derivation.** Nothing in this project
# computes force, so nothing here can tell you what bolt a joint needs. What
# it can do is stop the bolt being a constant: the bolt is taken as half the
# rod, snapped to the nearest size in the M3-M8 family. That keeps M5 on the
# 10 mm rod the whole project is drawn around, so the parts already built do
# not move, and it gives the other diameters something proportionate instead
# of something inherited.
#
# Values are ISO clearance holes (ISO 273 medium), DIN 125 washer outside
# diameters -- the generators counterbore for a washer, not a bare head -- and
# ISO 4032 nuts with the same 0.3 mm across-flats fit the M5 set always had.
# The two cones are the printable transitions off the counterbore and the nut
# pocket, kept at the proportion the M5 set used.
FASTENERS = {
    3: dict(clearance=3.4, washer=7.0, nut_af=5.8, nut_depth=2.6,
            head_depth=2.8, head_cone=1.8, nut_cone=1.4),
    4: dict(clearance=4.5, washer=9.0, nut_af=7.3, nut_depth=3.4,
            head_depth=3.6, head_cone=2.3, nut_cone=1.8),
    5: dict(clearance=5.5, washer=10.0, nut_af=8.3, nut_depth=4.6,
            head_depth=4.4, head_cone=2.8, nut_cone=2.2),
    6: dict(clearance=6.6, washer=12.0, nut_af=10.3, nut_depth=5.4,
            head_depth=5.2, head_cone=3.4, nut_cone=2.6),
    8: dict(clearance=9.0, washer=16.0, nut_af=13.3, nut_depth=7.0,
            head_depth=6.8, head_cone=4.5, nut_cone=3.5),
}

# Cross pins, where a slide fit locates a rod and something has to hold it.
# Roughly four tenths of the rod, on stock sizes, which keeps the 4 mm pin the
# base hub already uses on its 10 mm rod.
PIN_SIZES = (2.0, 2.5, 3.0, 4.0, 5.0, 6.0)

# The wall has a floor that has nothing to do with the rod: below about 3 mm a
# printed wall is perimeters and not structure, whatever it is wrapped around.
# Above that it follows the rod.
MINIMUM_WALL_FLOOR = 3.0
WALL_PER_ROD = 0.4


def fastener_size_for(rod_diameter):
    """Which metric bolt a rod of this size gets. Half the rod, snapped."""
    want = rod_diameter / 2.0
    return min(FASTENERS, key=lambda m: (abs(m - want), m))


def fastener_for_clearance(clearance):
    """The row whose clearance hole this is: 8.5 is the M8's, and so on.

    Everything else in this table is reached through the rod, because the rod
    is what the part is drawn around. One fastener is not: the bolt that holds
    a base hub to its driven angle is sized by the ground, and it arrives as
    the hole it needs rather than as a thread. Its nut still has to come from
    somewhere, and it comes from here.
    """
    size = min(FASTENERS, key=lambda m: abs(FASTENERS[m]["clearance"] - clearance))
    return size, FASTENERS[size]


def pin_for(rod_diameter):
    """Cross-pin diameter for a rod: about 0.4 of it, on a stock size."""
    want = 0.4 * rod_diameter
    return min(PIN_SIZES, key=lambda d: (abs(d - want), d))


def wall_for(rod_diameter):
    """Structural wall for a rod, with a printing floor under it."""
    return max(MINIMUM_WALL_FLOOR, WALL_PER_ROD * rod_diameter)


# Inputs a generator can leave at zero and have filled in from the rod. The
# key is the generator's alias; the value says where the number comes from.
SCALED_INPUTS = {
    "fastenerDiameter": lambda f, rod: f["clearance"],
    "fastenerHeadDiameter": lambda f, rod: f["washer"],
    "headBoreDepth": lambda f, rod: f["head_depth"],
    "headConeHeight": lambda f, rod: f["head_cone"],
    "nutConeHeight": lambda f, rod: f["nut_cone"],
    "nutAcrossFlats": lambda f, rod: f["nut_af"],
    "nutRecessDepth": lambda f, rod: f["nut_depth"],
    # Both follow the structural rod, not the caliper: a wall carries load and
    # a pin shears, and neither cares how much winding is wrapped round it.
    "minimumWall": lambda f, rod: wall_for(rod),
    "rodPinDiameter": lambda f, rod: pin_for(rod),
}


def scale_to_rod(values):
    """Fill in every scalable input the caller left at zero.

    Zero means "take it from the rod". A real number means the person wanted
    that number and gets it -- which is what keeps the parameter spreadsheet
    an override and not a decoration.

    ``fastenerSize`` pins the bolt family: zero chooses it from the rod, and
    3, 4, 5, 6 or 8 forces one. Returns what it decided, for the parameter
    sheet to report, because a part whose bolt was chosen for it should say
    which bolt that was.
    """
    # The channel is cut to what the rod measures; the bolt is sized from what
    # the rod IS. For plain round rod these are the same number and nothing
    # changes. For composite rebar they are not: a nominal 10 mm rod measures
    # about 11 over its winding, and sizing the bolt from the caliper reading
    # buys an M6 to hold a rod an M5 is right for.
    rod = values["rodDiameter"]
    strength = values.get("rodNominalDiameter") or rod
    size = int(values.get("fastenerSize") or 0) or fastener_size_for(strength)
    if size not in FASTENERS:
        raise ValueError(
            f"no M{size} in the fastener table; known: "
            + ", ".join("M%d" % m for m in sorted(FASTENERS))
        )
    fastener = FASTENERS[size]

    chosen = {"fastenerSize": size}
    for alias, source in SCALED_INPUTS.items():
        if alias not in values:
            continue
        if values[alias]:          # a real number the caller asked for
            continue
        values[alias] = source(fastener, strength)
        chosen[alias] = values[alias]
    if "fastenerSize" in values:
        values["fastenerSize"] = size
    return chosen
