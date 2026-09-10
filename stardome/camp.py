"""Several domes joined by corridors, and where they are allowed to stand.

A camp is not a free arrangement. A dome has **five** tall bays and no more,
at 72 degrees apart, and a corridor has to land in one of them -- so the
directions a dome can be joined in are quantised. Turn the dome and all five
turn together.

That gives the layout its rules:

- **Five neighbours maximum**, and only if every one of them sits on a
  different bay.
- **Every corridor runs along a bay azimuth at BOTH ends.** Two domes cannot
  be joined at whatever angle the site suggests; the pair has to agree.
- **A tree always solves.** Each dome's rotation is free until its first
  corridor is placed, and that one corridor fixes the other four directions.
  So hang the camp off a hub and every branch can be made to land.
- **A loop usually does not.** Closing a cycle means the last corridor has to
  come out at a bay that is already pointing the right way, and the 72 degree
  grid rarely obliges. This module refuses rather than fudging the angle.

## How far apart

Not a guess. The corridor's mouth on each dome reaches a known distance from
that dome's centre -- the cover is a sphere, so it is the same in every
direction -- and the gap between the two mouths is the corridor's own length:

    centre distance = reach(A) + length + reach(B)

## What this does not do

No structure, no ground modelling, no drainage, no fire separation, no
guy-line clashes between neighbours. It answers where the domes stand so
their doors line up, and how much corridor that costs.
"""

from __future__ import annotations

import math

from . import corridor as _corridor
from . import doorway

# Five tall bays, 72 degrees apart. Derived rather than assumed -- the count
# comes from the model -- but the layout maths wants it named.
BAYS = 5


def _bay_azimuths(data: dict) -> list:
    """The dome's five tall-bay directions, in its own frame, sorted."""
    bays = doorway.tall_bays(data)
    return sorted(b["centre_azimuth_deg"] % 360.0 for b in bays)


def _reach(data: dict, spec: dict) -> float:
    """How far the corridor's mouth stands from this dome's centre.

    The cover is a sphere above the base ring, so this is the same whichever
    bay the corridor lands on -- which is what makes the layout solvable at
    all.
    """
    m = _corridor.mouth(
        data,
        0.0,
        spec["width"],
        spec["height"],
        spec.get("samples", _corridor.ARC_SAMPLES),
        spec.get("kind", "hoop"),
        spec.get("brace_leg", _corridor.DEFAULT_BRACE_LEG_MM),
    )
    if not m["fits_on_dome"]:
        raise ValueError(
            "a corridor that size cannot meet this dome at all: " + m["note"]
        )
    return m["max_reach_mm"]


def _nearest_bay(azimuths: list, wanted: float) -> tuple:
    """The bay closest to a wanted direction, as (index, its own azimuth)."""
    best = None
    for i, a in enumerate(azimuths):
        gap = abs((a - wanted + 180.0) % 360.0 - 180.0)
        if best is None or gap < best[0]:
            best = (gap, i, a)
    return best[1], best[2]


def solve(domes: dict, links: list, spec: dict | None = None) -> dict:
    """Place every dome so that each link lands in a bay at both ends.

    ``domes`` maps a label to a built model. ``links`` is a list of
    ``(label_a, label_b)``. The graph must be a tree: connected, and one fewer
    link than it has domes.
    """
    spec = dict(spec or {})
    spec.setdefault("kind", "hoop")
    spec.setdefault("width", _corridor.DEFAULT_WIDTH_MM)
    spec.setdefault("height", _corridor.DEFAULT_HEIGHT_MM)
    spec.setdefault("length", _corridor.DEFAULT_LENGTH_MM)
    spec.setdefault("pitch", _corridor.DEFAULT_PITCH_MM)

    labels = list(domes)
    if len(links) != len(labels) - 1:
        raise ValueError(
            f"{len(labels)} domes need exactly {len(labels) - 1} corridors to "
            f"form a tree, got {len(links)}. A loop cannot be guaranteed to "
            "close on a 72 degree grid; see the module docstring."
        )

    adjacency = {label: [] for label in labels}
    for a, b in links:
        for end in (a, b):
            if end not in adjacency:
                raise ValueError(f"link names unknown dome {end!r}")
        adjacency[a].append(b)
        adjacency[b].append(a)

    for label, neighbours in adjacency.items():
        if len(neighbours) > BAYS:
            raise ValueError(
                f"{label} has {len(neighbours)} corridors but a dome has only "
                f"{BAYS} tall bays to land them in"
            )

    # Root the tree at the busiest dome: the hub's own bays are the tightest
    # constraint, so satisfying it first is what keeps the rest free.
    root = max(labels, key=lambda label: len(adjacency[label]))

    placed = {root: {"x": 0.0, "y": 0.0, "spin": 0.0}}
    used = {label: set() for label in labels}
    corridors = []
    order = [root]
    seen = {root}

    while order:
        parent = order.pop(0)
        p = placed[parent]
        p_bays = _bay_azimuths(domes[parent])
        reach_p = _reach(domes[parent], spec)

        for child in adjacency[parent]:
            if child in seen:
                continue
            # The first free bay of the parent, in its own order.
            free = [i for i in range(len(p_bays)) if i not in used[parent]]
            if not free:
                raise ValueError(f"{parent} has run out of bays")
            bay_index = free[0]
            used[parent].add(bay_index)
            world = (p_bays[bay_index] + p["spin"]) % 360.0

            # Turn the child so one of ITS bays points back along the link.
            c_bays = _bay_azimuths(domes[child])
            back = (world + 180.0) % 360.0
            c_index, c_own = _nearest_bay(c_bays, 0.0)
            spin_child = (back - c_own) % 360.0
            used[child].add(c_index)

            reach_c = _reach(domes[child], spec)
            distance = reach_p + spec["length"] + reach_c

            angle = math.radians(world)
            placed[child] = {
                "x": p["x"] + math.cos(angle) * distance,
                "y": p["y"] + math.sin(angle) * distance,
                "spin": spin_child,
            }
            corridors.append({
                "from": parent,
                "to": child,
                "world_azimuth_deg": round(world, 4),
                "bay_azimuth_from_deg": round(p_bays[bay_index], 4),
                "bay_azimuth_to_deg": round(c_own, 4),
                "centre_distance_mm": round(distance, 1),
                "length_mm": round(spec["length"], 1),
                "reach_from_mm": round(reach_p, 1),
                "reach_to_mm": round(reach_c, 1),
            })
            seen.add(child)
            order.append(child)

    if len(seen) != len(labels):
        missing = sorted(set(labels) - seen)
        raise ValueError(f"the camp is not connected: {', '.join(missing)} unreachable")

    return {
        "domes": [
            {
                "label": label,
                "variant": domes[label]["meta"]["variant"],
                "alias": domes[label]["meta"].get("alias"),
                "x_mm": round(placed[label]["x"], 1),
                "y_mm": round(placed[label]["y"], 1),
                "spin_deg": round(placed[label]["spin"], 4),
                "corridors": len(adjacency[label]),
                "bays_free": BAYS - len(used[label]),
            }
            for label in labels
        ],
        "corridors": corridors,
        "corridor_spec": spec,
        "totals": totals(domes, corridors, spec),
        "note": (
            "Every corridor lands in a tall bay at both ends. Directions are "
            "quantised to 72 degrees because a dome has five bays and no more."
        ),
    }


def _cover_reach(radius: float, lift: float, v: float, z: float) -> float:
    """Horizontal distance from a dome's axis to its cover, at ``(v, z)``.

    ``z`` is measured from the common ground and ``lift`` is how far the base
    ring stands above it -- a skirted dome's sphere is up in the air, and its
    skirt is a cylinder below. Two domes in one camp rarely share a lift, so
    this cannot be done in either dome's own frame.
    """
    dz = z - lift
    inside = radius * radius - v * v - (dz * dz if dz >= 0.0 else 0.0)
    return math.sqrt(inside) if inside > 0.0 else 0.0


def geometry(plan: dict, domes: dict) -> dict:
    """Add world-space ribs and skin to every corridor in a solved plan.

    World coordinates, in millimetres, on the shared ground -- so a consumer
    draws them as they come, with no transform of its own. That matters more
    here than for a single dome: a corridor belongs to two domes at once and
    has no natural frame of its own.
    """
    from . import cover as _cover

    spec = plan["corridor_spec"]
    kind = spec.get("kind", "hoop")
    brace = spec.get("brace_leg", _corridor.DEFAULT_BRACE_LEG_MM)
    at = {d["label"]: d for d in plan["domes"]}

    for link in plan["corridors"]:
        a, b = at[link["from"]], at[link["to"]]
        da, db = domes[link["from"]], domes[link["to"]]
        ra, rb = _cover.radius(da), _cover.radius(db)
        lift_a = da["meta"].get("skirt_height", 0.0) or 0.0
        lift_b = db["meta"].get("skirt_height", 0.0) or 0.0
        distance = link["centre_distance_mm"]

        angle = math.radians(link["world_azimuth_deg"])
        eu = (math.cos(angle), math.sin(angle))
        ev = (-math.sin(angle), math.cos(angle))

        profile = _corridor._profile(
            spec["width"], spec["height"], spec.get("samples", _corridor.ARC_SAMPLES),
            kind, brace,
        )

        def world(u, v, z):
            return [
                round(a["x_mm"] + eu[0] * u + ev[0] * v, 3),
                round(a["y_mm"] + eu[1] * u + ev[1] * v, 3),
                round(z, 3),
            ]

        near = [_cover_reach(ra, lift_a, v, z) for v, z in profile]
        far = [distance - _cover_reach(rb, lift_b, v, z) for v, z in profile]
        u_start, u_end = max(near), min(far)

        ribs = []
        frames = []
        if u_end > u_start:
            count = max(2, int((u_end - u_start) // spec["pitch"]) + 1)
            step = (u_end - u_start) / (count - 1)
            members = (
                _corridor._portal_members(
                    spec["width"], spec["height"], brace,
                    _corridor.DEFAULT_BOARD_THICKNESS_MM,
                    _corridor.DEFAULT_BOARD_WIDTH_MM,
                )
                if kind == "portal" else []
            )
            for i in range(count):
                u = u_start + i * step
                if kind == "portal":
                    verts, faces = [], []
                    for _name, p0, p1 in members:
                        bv, bf = _corridor._board_box(
                            p0, p1, eu, ev, u, 0.0,
                            _corridor.DEFAULT_BOARD_THICKNESS_MM,
                            _corridor.DEFAULT_BOARD_WIDTH_MM,
                        )
                        base = len(verts)
                        verts.extend(
                            [[p[0] + a["x_mm"], p[1] + a["y_mm"], p[2]] for p in bv]
                        )
                        faces.extend([[k + base for k in f] for f in bf])
                    frames.append({"vertices": verts, "faces": faces})
                else:
                    ribs.append([world(u, v, z) for v, z in profile])

        verts = [world(u, v, z) for u, (v, z) in zip(near, profile)]
        verts += [world(u, v, z) for u, (v, z) in zip(far, profile)]
        n = len(profile)
        faces = [[i, i + 1, n + i + 1, n + i] for i in range(n - 1)]

        link["clear_run_mm"] = round(max(0.0, u_end - u_start), 1)
        link["drawing"] = {
            "kind": kind,
            "rib_count": len(ribs) or len(frames),
            "hoops": ribs,
            "frames": frames,
            "skin": {
                "vertex_count": len(verts),
                "face_count": len(faces),
                "vertices": verts,
                "faces": faces,
            },
            "note": (
                "World millimetres on the shared ground. Both ends are cut to "
                "their own dome's cover, so neither is square."
            ),
        }
    return plan


def clashes(plan: dict, domes: dict) -> list:
    """Pairs of domes whose covers overlap. A layout that solves can still collide."""
    from . import cover as _cover

    out = []
    entries = plan["domes"]
    for i, a in enumerate(entries):
        for b in entries[i + 1:]:
            ra = _cover.radius(domes[a["label"]])
            rb = _cover.radius(domes[b["label"]])
            gap = math.dist((a["x_mm"], a["y_mm"]), (b["x_mm"], b["y_mm"])) - ra - rb
            if gap < 0:
                out.append({
                    "a": a["label"],
                    "b": b["label"],
                    "overlap_mm": round(-gap, 1),
                })
    return out


def totals(domes: dict, corridors: list, spec: dict) -> dict:
    """What the camp costs in corridor, and how much ground it covers."""
    kind = spec.get("kind", "hoop")
    per_rib = (
        _corridor.portal_frame(spec["width"], spec["height"],
                               spec.get("brace_leg", _corridor.DEFAULT_BRACE_LEG_MM))
        ["board_length_mm"]
        if kind == "portal"
        else _corridor.hoop(spec["width"], spec["height"], 10.0, 3000.0)["rod_length_mm"]
    )
    ribs_each = int(spec["length"] // spec["pitch"]) + 1
    return {
        "corridor_count": len(corridors),
        "corridor_length_m": round(len(corridors) * spec["length"] / 1000.0, 1),
        "ribs": len(corridors) * ribs_each,
        "rib_material_m": round(len(corridors) * ribs_each * per_rib / 1000.0, 1),
        "material": "board" if kind == "portal" else "rod",
    }


def format_plan(plan: dict) -> str:
    """The camp, as a page for a person."""
    xs = [d["x_mm"] for d in plan["domes"]]
    ys = [d["y_mm"] for d in plan["domes"]]
    spec = plan["corridor_spec"]
    t = plan["totals"]

    lines = [
        f"--- camp of {len(plan['domes'])}, joined by {t['corridor_count']} "
        f"{spec['kind']} corridors {spec['width']:.0f} x {spec['height']:.0f} mm",
        "",
        f"  {'dome':<6}{'stands at':<22}{'turned':>9}{'links':>7}{'bays left':>11}",
    ]
    for d in plan["domes"]:
        # The label, not the alias: three S domes are three different places
        # in this camp and the plan is about which is which.
        name = d["label"]
        where = f"{d['x_mm'] / 1000.0:+.1f}, {d['y_mm'] / 1000.0:+.1f} m"
        lines.append(
            f"  {name:<6}{where:<22}{d['spin_deg']:>8.1f}°{d['corridors']:>7}"
            f"{d['bays_free']:>11}"
        )

    lines += ["", "  corridors"]
    for c in plan["corridors"]:
        a = next(d for d in plan["domes"] if d["label"] == c["from"])
        b = next(d for d in plan["domes"] if d["label"] == c["to"])
        lines.append(
            f"    {a['label']:<4} -> {b['label']:<4}"
            f"  bearing {c['world_azimuth_deg']:6.1f}°,"
            f"  centres {c['centre_distance_mm'] / 1000.0:5.1f} m apart"
        )

    lines += [
        "",
        f"  footprint       {(max(xs) - min(xs)) / 1000.0:.1f} x "
        f"{(max(ys) - min(ys)) / 1000.0:.1f} m between dome centres",
        f"  corridor        {t['corridor_length_m']:.1f} m in {t['corridor_count']} runs, "
        f"{t['ribs']} ribs, {t['rib_material_m']:.1f} m of {t['material']}",
        "",
        "  Every corridor lands in a tall bay at both ends; a dome has five,",
        "  72 degrees apart, so the camp's angles are not free.",
    ]
    return "\n".join(lines)
