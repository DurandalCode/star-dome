# -*- coding: utf-8 -*-
"""
Star Dome cut-bow termination, prototype V1.

The doorway is opened by removing the end piece of two L bows, so each of them
now STARTS at a crossing instead of passing through it. What holds it there is
not the crossing clamp: that part assumes both rods run on out the other side,
and one of these does not.

So this is the crossing clamp with one channel closed:

    the surviving rod  -- the one that still passes through -- keeps its
        channel, its flare at both mouths and its saddle, unchanged;
    the terminating rod -- the one that stops -- keeps its channel and its
        flare at the mouth it comes IN by, and gets a wall at the other end.

One thing that follows is worth saying out loud rather than discovering in a
field. **This is the only joint in the dome where load arrives along a rod and
into printed plastic.** Everywhere else a rod is gripped across its axis and
the rod carries the force onward; here the bow end bears on a wall. The wall is
``minimumWall`` thick over the full channel section, and whether that is enough
is a question for a test rig, not for this file. Nothing in the geometry
answers it.

The part is not handed twice over. The wall is drawn at the +X end, and the
crossing whose bow comes the other way takes the same part turned half a turn
about the stack axis -- which maps each channel onto itself and swaps the ends.
Handedness proper, the mirror the crossing clamp needs, is a separate question
and the schedule reports it the same way.

Run:  exec(open('<repo>/connectors/term_clamp_v1.py').read())
inside FreeCAD, or via `make clamps`.
"""

import math
import os
import sys

import FreeCAD as App
import Part

try:
    REPO
except NameError:
    try:
        REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        REPO = os.path.expanduser("~/star-dome")

if os.path.join(REPO, "connectors") not in sys.path:
    sys.path.insert(0, os.path.join(REPO, "connectors"))
import kit  # noqa: E402  -- needs the path set above

DOC_NAME = "StarDome_TermClamp_V1"
TITLE = "Star Dome cut-bow termination V1 - parameters"
OUT_DIR = os.path.join(REPO, "connectors")
SAVE_PATH = os.path.join(OUT_DIR, "star_dome_term_clamp_v1.FCStd")
USE_SPREADSHEET_IF_PRESENT = True

# Both halves print as drawn, the same way up `verify` judges them.
FLIPPED_PIECES = set()

CLAMP_SOURCE = os.path.join(REPO, "connectors", "crossing_clamp_v1.py")
_CLAMP = None


def clamp_module():
    """The V1 crossing clamp's own functions, loaded without auto-building.

    This part is that part with one channel closed, and saying so in code
    rather than in a comment is what keeps the two from drifting. Everything
    structural -- the saddle, the bolt pattern, the flares, the fillet rules,
    the printability argument -- belongs to the clamp and is not restated here.
    """
    global _CLAMP
    if _CLAMP is None:
        namespace = {"SUPPRESS_AUTORUN": True, "__file__": CLAMP_SOURCE, "REPO": REPO}
        with open(CLAMP_SOURCE) as handle:
            exec(compile(handle.read(), CLAMP_SOURCE, "exec"), namespace)
        _CLAMP = namespace
    return _CLAMP


def _inputs():
    base = [row for row in clamp_module()["INPUTS"]]
    return base + [
        ("endWallThickness", 5.0, "mm",
         "material behind the terminating rod's end. This is the only place in "
         "the dome where a rod pushes along its own axis into printed plastic"),
        ("endEngagement", 0.0, "mm",
         "how much FURTHER the channel runs past the crossing before the wall, "
         "over what the crossing clamp's channelLength already gives. Zero "
         "keeps the part the same size as the clamp beside it"),
    ]


INPUTS = _inputs()


def build(values):
    """The crossing clamp, with the upper rod's channel walled off at +X.

    The upper rod is the terminating one because that is how the dome comes
    out: at both of M's terminations the bow that stops is the one running on
    the outside, and the cap goes over it either way.
    """
    clamp = clamp_module()
    geo, dims = clamp["build"](values)

    R = dims["R"]
    angA = dims["angA"]
    zA = dims["zA"]
    hw = dims["hw"]
    L = dims["L"]
    wall = values["endWallThickness"]
    reach = values["endEngagement"]

    # Where the bow end stops, measured along its own axis from the crossing.
    # The body runs to L/2; the wall occupies the last `wall` of it, so the rod
    # goes in as far as there is channel and then meets material.
    stop = L / 2.0 + reach - wall
    if stop <= R:
        raise ValueError(
            f"the end wall at {stop:.1f} mm would sit inside the crossing "
            f"itself (the channels meet within {R:.1f} mm of it); give the "
            "part endEngagement, or a longer channelLength"
        )

    # The envelope the wall may fill: the part's own body over the terminating
    # channel, full height, beyond the stop. Taking it from the body rather
    # than drawing a plug keeps the outside profile exactly the clamp's.
    envelope = clamp["capsule_prism"](
        L + 2.0 * reach, hw, dims["z_bottom"], dims["z_top"], angA
    )
    big = (L + reach) * 4.0
    beyond = Part.makeBox(
        big, big, big,
        App.Vector(stop, -big / 2.0, dims["z_bottom"] - 1.0),
    )
    beyond = beyond.copy()
    beyond.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angA)
    fill = envelope.common(beyond)

    # Only the terminating channel and its flare are being filled; the
    # surviving rod runs straight through the same region and must not be.
    keep_clear = kit.rod_solid(R, big, dims["angB"], dims["zB"])
    keep_clear = keep_clear.fuse(
        clamp["rod_slot"](R, big, dims["angB"], dims["zB"], dims["z_top"] + 10.0)
    )
    keep_clear = keep_clear.fuse(clamp["entrance_flare"](
        R, dims["angB"], dims["zB"], L, dims["flare_len"], dims["flare_slope"], 6.0
    ))
    for point in dims["bolt_pts"]:
        keep_clear = keep_clear.fuse(Part.makeCylinder(
            dims["boss_r"] + 0.6, big,
            App.Vector(point.x, point.y, dims["z_bottom"] - 10.0),
        ))
    fill = fill.cut(keep_clear)

    def slab(z_lo, z_hi):
        return Part.makeBox(
            big, big, z_hi - z_lo, App.Vector(-big / 2.0, -big / 2.0, z_lo)
        )

    bottom = geo["bottom"].fuse(fill.common(slab(dims["z_bottom"], dims["z_seat"])))
    cap = geo["cap"].fuse(fill.common(slab(dims["z_cap"], dims["z_top"])))
    bottom = bottom.removeSplitter()
    cap = cap.removeSplitter()
    if not kit.ok(bottom) or not kit.ok(cap):
        raise RuntimeError("the end wall did not close into one sound solid")

    # The terminating rod stops at the wall; the other one still runs through.
    rod_len = L + 60.0
    rodA = kit.rod_from_hub(
        values["rodDiameter"] / 2.0, 0.0, angA + 180.0, zA, rod_len
    )
    rodA = rodA.cut(Part.makeBox(
        big, big, big, App.Vector(stop, -big / 2.0, zA - big / 2.0)
    ).copy())

    geo = dict(geo)
    geo["bottom"] = bottom
    geo["cap"] = cap
    geo["rodA"] = rodA
    dims = dict(dims)
    dims["stop_mm"] = stop
    dims["end_wall_mm"] = wall
    dims["end_engagement_mm"] = reach
    return geo, dims


def verify(geo, dims, values):
    """The clamp's own checks, plus the two this part adds.

    The wall has to BE there -- a fill that quietly cut to nothing would leave
    an ordinary clamp and look fine -- and the rod has to reach it, because a
    bow end floating short of its stop is carrying nothing.
    """
    clamp = clamp_module()
    rep = clamp["verify"](geo, dims, values)

    R = dims["R"]
    stop = dims["stop_mm"]
    wall = dims["end_wall_mm"]
    big = 400.0

    # The wall is the slice of channel between where the rod stops and where
    # the body ends. Measuring against the channel's whole length instead
    # would report a sound wall as 2% closed, which is a metric problem and
    # not a part problem -- so this measures the slice.
    def sleeve(start, length):
        d = kit.direction(dims["angA"])
        axis = App.Vector(d.x, d.y, 0.0)
        base = App.Vector(d.x * start, d.y * start, dims["zA"])
        return Part.makeCylinder(R, length, base, axis)

    solid = geo["bottom"].fuse(geo["cap"])
    wall_slice = sleeve(stop, wall)
    filled = wall_slice.common(solid).Volume

    # The wall is DOMED, because the body it is cut from ends in the clamp's
    # own rounded profile: thickest on the axis, tapering towards the channel
    # wall. And it is SPLIT, like everything else in a two-piece clamp, so the
    # thickness is measured in each half rather than through the parting gap
    # between them -- probing straight down the axis reads that gap as missing
    # material and halves the answer.
    probe_r = 0.5
    d = kit.direction(dims["angA"])

    def axial_material(shape, z_off):
        probe = Part.makeCylinder(
            probe_r, wall * 6.0,
            App.Vector(d.x * stop, d.y * stop, dims["zA"] + z_off),
            App.Vector(d.x, d.y, 0.0),
        )
        return probe.common(shape).Volume / (math.pi * probe_r * probe_r)

    in_cap = axial_material(geo["cap"], +R / 2.0)
    in_bottom = axial_material(geo["bottom"], -R / 2.0)
    # And the rod must still be able to get IN: the channel in front of the
    # stop has to be empty over the length the part is meant to hold.
    grip = min(stop - R, dims["L"] / 2.0)
    ahead = sleeve(stop - grip, grip)
    blocked = ahead.common(solid).Volume

    rep["termination"] = {
        "end_wall_thickness_mm": round(wall, 2),
        "rod_end_at_mm": round(stop, 2),
        "wall_in_cap_mm": round(in_cap, 2),
        "wall_in_bottom_mm": round(in_bottom, 2),
        "wall_backed_fraction": (
            round(filled / wall_slice.Volume, 4) if wall_slice.Volume else 0.0
        ),
        "channel_ahead_blocked_mm3": round(blocked, 2),
        "grip_length_mm": round(grip, 2),
        "bearing_area_mm2": round(math.pi * R * R, 2),
    }
    rep["printability"] = {
        "bottom": kit.printability(geo["bottom"]),
        "cap": kit.printability(geo["cap"]),
    }
    return rep


def derived_rows(dims, values):
    rows = clamp_module()["derived_rows"](dims, values)
    return rows + [
        ("rodEndStopAt", dims["stop_mm"], "mm",
         "how far from the crossing the terminating bow's end sits"),
        ("endWall", dims["end_wall_mm"], "mm", "material behind that end"),
    ]


def populate(doc, geo):
    return clamp_module()["populate"](doc, geo)


def run():
    doc = kit.document(DOC_NAME)
    sheet, values = kit.read_or_build_parameters(doc, INPUTS, USE_SPREADSHEET_IF_PRESENT)
    values["verticalSeparation"] = values["rodDiameter"]
    geo, dims = build(values)
    kit.write_parameters(doc, sheet, INPUTS, values, derived_rows(dims, values), TITLE)
    populate(doc, geo)
    doc.recompute()
    doc.saveAs(SAVE_PATH)
    rep = verify(geo, dims, values)
    rep["saved_to"] = SAVE_PATH
    return rep


if not globals().get("SUPPRESS_AUTORUN"):
    REPORT = run()
    import pprint
    pprint.pprint(REPORT, width=110)
