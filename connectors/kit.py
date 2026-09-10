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

# Mesh tolerances for the STL that goes to the slicer. 0.02 mm linear is well
# under any FDM nozzle's resolution and lands around 1 MB.
LINEAR_DEFLECTION = 0.02
ANGULAR_DEFLECTION = 0.5


# --------------------------------------------------------------------------
# solids
# --------------------------------------------------------------------------
def direction(azimuth_deg):
    """Unit vector in the horizontal plane at this azimuth."""
    a = math.radians(azimuth_deg)
    return App.Vector(math.cos(a), math.sin(a), 0.0)


def rod_solid(radius, length, azimuth_deg, z, reach_back=None):
    """A rod lying at `azimuth_deg`, at height `z`.

    By default it is centred on the hub axis, which is what a rod passing
    through a crossing does. `reach_back` instead starts it that far behind
    the axis, for a rod that ends at the node rather than passing through.
    """
    d = direction(azimuth_deg)
    back = length / 2.0 if reach_back is None else reach_back
    base = App.Vector(-d.x * back, -d.y * back, z)
    return Part.makeCylinder(radius, length, base, d)


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
    """Running sum of the gaps between arms, as absolute azimuths.

    n gaps describe n+1 arms when the fan is open (a base hub's three rods,
    two gaps) and n arms when it closes on itself, so callers pass the gap
    list they mean and take as many azimuths as they have arms.
    """
    out = [start]
    for gap in gaps[:-1]:
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
    """The face normal that points out of the solid.

    `normalAt` follows the surface's own parameterisation, which after a cut
    may point into the material. Probing just off the surface settles it.
    """
    p = face.valueAt(u, v)
    n = face.normalAt(u, v)
    probe = App.Vector(p.x + n.x * eps, p.y + n.y * eps, p.z + n.z * eps)
    if shape.isInside(probe, 1e-7, True):
        return App.Vector(-n.x, -n.y, -n.z)
    return n


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
                    normals.append(_outward_normal(shape, face, u, v))
                except Exception:
                    continue
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
