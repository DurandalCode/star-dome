# -*- coding: utf-8 -*-
"""The hinged closure: a clamp that never comes apart.

WHAT THIS IS FOR

A clamp in this family is two printed halves pulled together by two bolts.
The bolts are not the expensive part. THIS is:

    put the bottom half on the standing rod, lay the upper rod, hold the cap,
    start two bolts from above into two nuts that can fall out of their traps,
    ten turns each, two tools, at head height

The bolts are half a minute of it. The other half is that a two-piece clamp
becomes THREE SEPARATE OBJECTS the moment it is opened, at the exact moment
both hands are busy -- and the dome asks for that thirty-two times over
(`python3 -m stardome bom M`). Every quick-release mechanism on the market
answers "how do I tighten this without a tool", and that is the wrong half.

So this module draws the other way of closing the same two halves:

    the cap is HINGED to the bottom half on one side, on a steel pin, so the
    connector is one object from the moment it is printed and never becomes
    two in a field;

    on the other side it keeps ONE bolt, standing in a slot that is open to
    the outside rather than in a drilled hole -- so the ear comes out from
    under the washer sideways instead of the bolt having to be wound out.

Slacken four turns, lift the cap the two millimetres its hinge slot allows,
swing it. Nothing is ever a separate piece, including while it is open. See
docs/quick-release.md for the mechanisms that were measured and rejected on
the way here, and decision 0020 for what this one costs.

THE HINGE AXIS IS NOT A CHOICE

The cap wraps the upper rod through 180 degrees, so its channel is a half
cylinder whose diameter lies in the parting plane. A half cylinder turned
about ANY line in that plane clears the rod at once -- the near lip moves
away, not in -- and turned about a line anywhere else it digs in. So the pin
sits in the parting plane, at the upper rod's axis height, parallel to the
upper rod, and that is the only family of positions that works at all.

TWO THINGS THAT ARE NOT VISIBLE IN A CLOSED VIEW

Both were built, and both looked perfectly sound shut:

**A square cheek cannot hinge.** A rectangular lug's corners stand ten
millimetres from the pin, in the middle of the arc the cap's own edge sweeps.
Above the pin a fork can only be a circle.

**Nothing wider than the fork gap may sit above the pin.** It swings outward
and DOWNWARD as the cap opens -- a point directly over the pin lands at pin
height at ninety degrees -- onto the cheeks.

Neither shows up in an interference check on the closed part, which is why
`crossing_clamp_v1.verify` opens the joint through eight positions and
measures it instead.

WHAT IS NOT ANSWERED HERE

How hard it grips. Nothing in this project computes force, so nothing here
can say whether one bolt holds what two did -- the second station now takes
its share in shear through a steel pin instead of in tension through a bolt.
That is a question for milestone 3's test rig, and it is why the bolted
closure stays the default.

Every solid here is drawn in a local frame -- x along the pin axis, y outward
from the joint, z up -- and then turned about the vertical to the station it
belongs at. The frames of this family are all rotations about Z, which is why
one angle is enough.
"""

import math

import FreeCAD as App
import Part

import kit


# --------------------------------------------------------------------------
# the closure, sized from the fastener it replaces
# --------------------------------------------------------------------------
# The same rule as decision 0013's: the pieces follow the bolt, the bolt
# follows the rod, and the print fits stay absolute, because a tolerance is
# not a proportion.
PIN_PER_BOLT = 0.6          # the hinge pin, against the bolt it replaces
BLADE_PER_BOLT = 1.2        # the tongue's thickness -- what the fork straddles
CHEEK_PER_WALL = 0.75       # a fork cheek, against the part's wall

# Print fits. Absolute, and they are the reason a printed hinge turns at all.
PIN_FIT = 0.3               # diametral, on a pin hole
BLADE_FIT = 0.6             # total, across a blade running in a fork


def sizes(bolt, wall):
    """Every dimension of the hinge, from the bolt it stands in for."""
    pin = min(kit.PIN_SIZES, key=lambda d: (abs(d - PIN_PER_BOLT * bolt), d))
    blade = round(BLADE_PER_BOLT * bolt, 2)
    cheek = max(kit.MINIMUM_WALL_FLOOR, wall * CHEEK_PER_WALL)
    return {
        "pin": pin,
        "blade": blade,
        "fork_gap": round(blade + BLADE_FIT, 2),
        "cheek": round(cheek, 2),
        "fork_width": round(blade + BLADE_FIT + 2.0 * cheek, 2),
    }


# --------------------------------------------------------------------------
# solids
# --------------------------------------------------------------------------
def _placed(shape, station, azimuth_deg):
    """Put a locally-drawn solid at its station, turned about the vertical.

    Local x runs along the pin axis, local y outward from the joint, local z
    up -- so a single rotation about Z lands it, and nothing here has to
    compose two rotations and get one of them backwards.
    """
    shape = shape.copy()
    shape.Placement = App.Placement(
        station, App.Rotation(App.Vector(0, 0, 1), azimuth_deg)
    )
    return shape


def lug(station, azimuth_deg, width, reach_in, reach_out, z_lo, z_hi):
    """A rectangular ear at a pin station, wider than a round boss can be.

    The bolted part puts a cylindrical boss here, sized to hold a washer. A
    fork has to hold a blade between two cheeks and is wider than that, and
    there is room for it: the station sits well clear of both rod channels.

    Inboard and outboard reach are separate because on a hinge they are not
    the same question. Inboard the lug has to run far enough to meet its own
    half's body; outboard it has to stop, because anything the cap carries
    past the hinge axis swings DOWN when the cap swings up, straight into the
    other half. `z_lo` and `z_hi` are absolute; the station's own z is
    ignored.
    """
    box = Part.makeBox(width, reach_in + reach_out, z_hi - z_lo,
                       App.Vector(-width / 2.0, -reach_in, z_lo))
    return _placed(box, App.Vector(station.x, station.y, 0.0), azimuth_deg)


def fork_slot(station, azimuth_deg, gap, along, out, z_lo, z_hi):
    """The cut that turns a lug into a fork.

    A slab of material taken out across the pin axis: `gap` thick, reaching
    `along` inboard from the station and `out` outboard, and open on the
    outboard side so whatever runs in the fork can swing out of it. The
    inboard limit is deliberate -- run it further and the slab reaches a rod
    channel, which is a part that looks right in every view and lets its rod
    out of the side.
    """
    box = Part.makeBox(gap, out + along, z_hi - z_lo,
                       App.Vector(-gap / 2.0, -along, z_lo))
    return _placed(box, App.Vector(station.x, station.y, 0.0), azimuth_deg)


def pin_hole(station, azimuth_deg, diameter, length, z):
    """A pin bore through a fork, on the pin axis."""
    cyl = Part.makeCylinder(
        (diameter + PIN_FIT) / 2.0, length,
        App.Vector(-length / 2.0, 0.0, z),
        App.Vector(1, 0, 0),
    )
    return _placed(cyl, App.Vector(station.x, station.y, 0.0), azimuth_deg)


def pin_slot(station, azimuth_deg, diameter, length, z, rise):
    """A pin bore stretched downward, so the part it is in can still move.

    The hinge cannot be a close fit on both counts: it has to hold the cap
    captive AND let the bolt pull the cap down onto the rods. The slot is
    what gives it the second one. `rise` is how far the cap may lift off the
    closed position -- measured downward in the cap's own material, because
    it is the cap that moves and the pin that stays.
    """
    hole = pin_hole(station, azimuth_deg, diameter, length, z)
    if rise <= 0:
        return hole
    low = pin_hole(station, azimuth_deg, diameter, length, z - rise)
    d = diameter + PIN_FIT
    box = Part.makeBox(length, d, rise,
                       App.Vector(-length / 2.0, -d / 2.0, z - rise))
    box = _placed(box, App.Vector(station.x, station.y, 0.0), azimuth_deg)
    return hole.fuse(low).fuse(box).removeSplitter()


def ear_slot(station, azimuth_deg, width, reach, z_lo, z_hi):
    """The open-ended slot in the cap's ear that the bolt sits in.

    Open rather than drilled, and that is the whole trick: a closed hole has
    to be wound over the bolt and off it again, which is the ten turns this
    module exists to remove. Slacken four, lift the cap the millimetres its
    hinge slot allows, and the ear comes out from under the washer sideways
    while the bolt stays in the nut it is threaded into.
    """
    box = Part.makeBox(width, reach + width / 2.0, z_hi - z_lo,
                       App.Vector(-width / 2.0, -width / 2.0, z_lo))
    return _placed(box, App.Vector(station.x, station.y, 0.0), azimuth_deg)


def knuckle(station, azimuth_deg, radius, width, z):
    """The round end of a tongue, turned about its own pin.

    A square tongue in a fork jams the moment it starts to rotate. Below the
    pin the tongue is a cylinder about the pin axis, so it sweeps its own
    slot and nothing else.
    """
    cyl = Part.makeCylinder(
        radius, width, App.Vector(-width / 2.0, 0.0, z), App.Vector(1, 0, 0)
    )
    return _placed(cyl, App.Vector(station.x, station.y, 0.0), azimuth_deg)


# --------------------------------------------------------------------------
# a bolt station, turned into a hinge or into a catch
# --------------------------------------------------------------------------
# Both take the two halves and give them back changed, so a generator reads as
# "put a hinge here, put a catch there" rather than as forty lines of boxes.
# `station` is where the bolt used to go; `azimuth` turns the local frame so
# that local x is the pin axis -- always the upper rod's direction, see the
# module docstring -- and local y points away from the joint.
def hinge(bottom, cap, station, azimuth_deg, s, reach,
          z_pin, z_bottom, z_top, lift):
    """The side the cap swings on. Returns (bottom, cap, report)."""
    cheek, pin = s["cheek"], s["pin"]
    knuckle_r = pin / 2.0 + cheek
    z_knuckle = z_pin - knuckle_r
    z_fork_top = z_pin + knuckle_r

    # The fork is a block up to the pin and a semicircular crown above it,
    # and the crown is not styling. The cap's body stands 0.8 mm further from
    # the pin than the crown's radius, and as the cap swings, every edge of
    # it sweeps an arc about that pin. A square cheek has corners out at ten
    # millimetres from the pin, sitting in the middle of that sweep -- which
    # is a hinge that binds at ten degrees and looks perfectly sound closed.
    # Turned about the pin, the fork can only be a circle.
    bottom = bottom.fuse(
        lug(station, azimuth_deg, s["fork_width"], reach / 2.0, reach / 2.0,
            z_bottom, z_pin)
    )
    bottom = bottom.fuse(
        knuckle(station, azimuth_deg, knuckle_r, s["fork_width"], z_pin)
    ).removeSplitter()

    # The slot runs a millimetre further in than the tongue does, so the
    # blade never meets its own end wall as it turns.
    in_reach = reach / 2.0 - cheek
    bottom = bottom.cut(
        fork_slot(station, azimuth_deg, s["fork_gap"],
                  in_reach + 1.0, reach,
                  z_knuckle - lift - 1.0, z_fork_top + 1.0)
    )

    # The tongue stays one blade all the way up, and that is not a saving:
    # it is the swing. Anything on the cap that is WIDER than the fork gap
    # and sits ABOVE the pin swings outboard and downward as the cap opens --
    # a point directly over the pin ends up at pin height at ninety degrees --
    # and lands on the cheeks. So the tongue keeps the slot's width from the
    # knuckle to the cap's top face, and reaches inboard exactly as far as
    # the slot does, which is far enough to meet the cap's own body: the
    # station stands a rod-and-a-wall clear of it, and the blade crosses that
    # gap. Nothing outboard of the pin except the knuckle, which turns in its
    # own radius and sweeps nothing.
    cap = cap.fuse(
        lug(station, azimuth_deg, s["blade"], in_reach, 0.0, z_pin, z_top)
    )
    cap = cap.fuse(
        knuckle(station, azimuth_deg, knuckle_r, s["blade"], z_pin)
    ).removeSplitter()

    # The bore runs right through whatever is in its way rather than
    # stopping at the fork, because a hole that ends inside the body is a
    # pin that can be driven in and never driven out. What it must not do is
    # graze a rod channel, and `verify` measures that rather than assuming
    # it -- the two axes are skew and the margin is not obvious by eye.
    length = 6.0 * reach
    bottom = bottom.cut(pin_hole(station, azimuth_deg, pin, length, z_pin))
    cap = cap.cut(pin_slot(station, azimuth_deg, pin, length, z_pin, lift))
    return bottom.removeSplitter(), cap.removeSplitter(), {
        "pin_mm": pin,
        "pin_z_mm": round(z_pin, 3),
        "knuckle_radius_mm": round(knuckle_r, 3),
        "lift_mm": round(lift, 3),
        "tongue_mm": s["blade"],
        "tongue_reach_mm": round(in_reach, 3),
        "fork_top_mm": round(z_fork_top, 3),
    }


def catch(cap, station, azimuth_deg, reach, z_cap, z_top,
          bolt, bolt_fit, washer):
    """The side that keeps its bolt -- and stops it being a loose object.

    Nothing changes on the bottom half: the same bolt, the same captive nut
    in the same trap. What changes is the cap's ear, which stops being a
    drilled hole with a counterbore and becomes a slot open to the outside.

    That one cut is what the hinge needs to be worth anything. With a hole,
    opening the joint means winding the bolt all the way out and holding it,
    a washer and a cap in one hand. With a slot: slacken four or five turns,
    lift the cap the two millimetres its hinge slot allows, and swing it --
    the ear comes out from under the washer sideways and the bolt never
    leaves the nut it is threaded into. Nothing in the joint is ever a
    separate piece, at any point, including while it is open.

    The washer is what makes the slot safe: it spans more than twice the
    slot, so the ear cannot pull through it however the load arrives. Which
    is also the constraint -- `washer` has to be checked against the slot,
    and `verify` does.
    """
    cap = cap.cut(
        ear_slot(station, azimuth_deg, bolt + bolt_fit, reach,
                 z_cap - 1.0, z_top + 1.0)
    )
    return cap.removeSplitter(), {
        "ear_slot_mm": round(bolt + bolt_fit, 3),
        "washer_mm": washer,
        "washer_over_slot": round(washer / (bolt + bolt_fit), 2),
        "opens_toward": round(azimuth_deg + 90.0, 4),
    }
