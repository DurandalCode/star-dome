"""Geometric invariants of the Star Dome.

These are the claims dome/README.md makes about the reconstruction. Keeping
them as executable checks rather than a table in a document means a change to
the maths cannot quietly break the topology: ``python3 -m stardome verify
--all`` fails instead.

Every check returns a human-readable problem string, or nothing.
"""

from __future__ import annotations

import math

from . import geometry, topology
from .vec import Vec3, dist, mirror_about_azimuth, rotate_z

TOL = 1e-6

# Node heights the reconstruction predicts, as multiples of the dome radius.
# Derived, not typed in: a literal to 6 decimals drifts past a 1e-3 mm
# tolerance once the radius reaches D12's 6000 mm.
_SIN_G = math.sin(math.radians(geometry.TILT_G))
Z_HIGH = math.sin(math.radians(72.0)) * _SIN_G  # G-G crossings at t = 72/108
Z_LOW = math.sin(math.radians(36.0)) * _SIN_G   # G-G crossings at t = 36/144

# All 30 unlashed crossings sit at this angle. acos(1/3) is the tetrahedral
# angle; that it falls out of the construction is a good sign the topology is
# the intended one.
UNTIED_ANGLE = math.degrees(math.acos(1.0 / 3.0))


def _point_set_maps_to_itself(points: list, transform) -> bool:
    moved = [transform(p) for p in points]
    for p in moved:
        if not any(dist(p, q) < 1e-3 for q in points):
            return False
    return True


def check(data: dict) -> list:
    """Run every invariant against a built model. Returns a list of failures."""
    problems: list = []
    meta = data["meta"]
    radius = meta["dome_radius"]

    def want(condition: bool, message: str) -> None:
        if not condition:
            problems.append(message)

    # --- counts -------------------------------------------------------------
    want(len(data["rods"]) == 15, f"expected 15 rods, got {len(data['rods'])}")
    want(
        len(data["base_nodes"]) == 10,
        f"expected 10 base points, got {len(data['base_nodes'])}",
    )
    want(
        len(data["crossings"]) == 90,
        f"expected 90 rod-to-rod contacts, got {len(data['crossings'])}",
    )
    want(
        len(data["nodes"]) == 40,
        f"expected 40 distinct crossing points, got {len(data['nodes'])}",
    )

    # --- 3 rod ends at every base point -------------------------------------
    for b in data["base_nodes"]:
        want(
            len(b["rods"]) == 3,
            f"base point {b['name']} has {len(b['rods'])} rod ends, expected 3",
        )
        want(
            abs(b["z"]) < TOL,
            f"base point {b['name']} is not on the ground plane: z={b['z']}",
        )
        families = sorted(r[0] for r in b["rods"])
        want(
            families == ["G", "L", "U"],
            f"base point {b['name']} has families {families}, expected one of each",
        )

    # --- tied nodes join four rods ------------------------------------------
    tied_nodes = [n for n in data["nodes"] if n["rod_count"] == 4]
    untied_nodes = [n for n in data["nodes"] if n["rod_count"] == 2]
    want(len(tied_nodes) == 10, f"expected 10 four-rod nodes, got {len(tied_nodes)}")
    want(
        len(untied_nodes) == 30,
        f"expected 30 two-rod crossings, got {len(untied_nodes)}",
    )
    want(
        len(tied_nodes) + len(untied_nodes) == len(data["nodes"]),
        "some node joins neither 2 nor 4 rods",
    )

    # --- tied node heights ---------------------------------------------------
    highs = [n for n in tied_nodes if abs(n["z"] - Z_HIGH * radius) < 1e-3]
    lows = [n for n in tied_nodes if abs(n["z"] - Z_LOW * radius) < 1e-3]
    want(len(highs) == 5, f"expected 5 high tied nodes, got {len(highs)}")
    want(len(lows) == 5, f"expected 5 low tied nodes, got {len(lows)}")

    # --- tied junctions per rod ---------------------------------------------
    per_rod: dict = {r["name"]: 0 for r in data["rods"]}
    for c in data["crossings"]:
        if c["tied"]:
            per_rod[c["rod_a"]] += 1
            per_rod[c["rod_b"]] += 1
    for rod in data["rods"]:
        # A family-G rod passes through 4 tied nodes and meets 3 other rods at
        # each of them; U and L rods pass through 2.
        expected = 12 if rod["family"] == "G" else 6
        want(
            per_rod[rod["name"]] == expected,
            f"rod {rod['name']} has {per_rod[rod['name']]} tied contacts, "
            f"expected {expected}",
        )

    # --- rod lengths ---------------------------------------------------------
    if meta["weave_mode"] == "flat":
        want(
            meta["rod_length_class_count"] == 1,
            f"flat weave should give one rod length class, got "
            f"{meta['rod_length_class_count']}",
        )
        nominal = math.pi * radius
        for rod in data["rods"]:
            want(
                abs(rod["length_nominal"] - nominal) < 1e-3,
                f"rod {rod['name']} length {rod['length_nominal']} != pi*R {nominal}",
            )

    # --- tie marks are exact fractions of the rod ---------------------------
    for rod in data["rods"]:
        length = rod["length_nominal"]
        if rod["family"] == "G":
            expected = [length * k / 5.0 for k in (1, 2, 3, 4)]
        else:
            expected = [length * k / 3.0 for k in (1, 2)]
        got = rod["tie_marks_mm"]
        want(
            len(got) == len(expected)
            and all(abs(a - b) < 1e-3 for a, b in zip(got, expected)),
            f"rod {rod['name']} tie marks {got} are not the expected fractions "
            f"{[round(e, 3) for e in expected]}",
        )

    # --- every tie mark lands on a tied node --------------------------------
    bows = {b.name: b for b in geometry.build_bows()}
    tied_points = [(n["x"], n["y"], n["z"]) for n in tied_nodes]
    for rod in data["rods"]:
        bow = bows[rod["name"]]
        for t in rod["tie_marks_deg"]:
            p = bow.point(t, radius)
            want(
                any(dist(p, q) < 1e-3 for q in tied_points),
                f"rod {rod['name']} tie mark at t={t} does not land on a tied node",
            )

    # --- unlashed crossings all share one angle -----------------------------
    for c in data["crossings"]:
        if not c["tied"]:
            want(
                abs(c["angle_deg"] - UNTIED_ANGLE) < 1e-4,
                f"untied crossing {c['index']} at {c['angle_deg']} deg, "
                f"expected acos(1/3) = {UNTIED_ANGLE:.6f}",
            )

    # --- symmetry group D5, order 10 ----------------------------------------
    pts: list = [(n["x"], n["y"], n["z"]) for n in data["nodes"]]
    for k in (1, 2, 3, 4):
        want(
            _point_set_maps_to_itself(pts, lambda p, a=72.0 * k: rotate_z(p, a)),
            f"rotation by {72 * k} deg is not a symmetry",
        )
    want(
        not _point_set_maps_to_itself(pts, lambda p: rotate_z(p, 36.0)),
        "rotation by 36 deg maps the node set to itself -- the top pentagon "
        "should only be 5-fold, so this would mean the topology is wrong",
    )
    for azimuth in (90.0, 162.0):
        want(
            _point_set_maps_to_itself(
                pts, lambda p, a=azimuth: mirror_about_azimuth(p, a)
            ),
            f"mirror at azimuth {azimuth} deg is not a symmetry",
        )

    # --- skirt ---------------------------------------------------------------
    #
    # The dome frame keeps its base ring at z = 0, so a skirt hangs below into
    # negative z and the ground sits at -height. Checked here so a change to
    # that convention cannot pass silently: every consumer that draws a skirt
    # has to know which way it goes.
    skirt = data.get("skirt")
    if skirt is None:
        want(
            meta.get("skirt_height", 0.0) == 0.0,
            f"meta says skirt_height={meta.get('skirt_height')} but there is "
            f"no skirt block",
        )
    else:
        want(
            len(skirt["posts"]) == len(data["base_nodes"]),
            f"{len(skirt['posts'])} skirt posts for "
            f"{len(data['base_nodes'])} base points",
        )
        want(
            skirt["ground_z"] == -skirt["height"],
            f"ground at {skirt['ground_z']} for a {skirt['height']} skirt",
        )
        by_name = {b["name"]: b for b in data["base_nodes"]}
        for post in skirt["posts"]:
            base_node = by_name.get(post["base_node"])
            want(base_node is not None, f"post {post['name']} has no base node")
            if base_node is None:
                continue
            want(
                abs(post["x"] - base_node["x"]) < TOL
                and abs(post["y"] - base_node["y"]) < TOL,
                f"post {post['name']} is not under {base_node['name']}",
            )
            want(
                abs(post["z_top"] - base_node["z"]) < TOL,
                f"post {post['name']} does not reach its base node",
            )
            want(
                abs((post["z_top"] - post["z_bottom"]) - skirt["height"]) < 1e-3,
                f"post {post['name']} is not {skirt['height']} long",
            )
        want(
            abs(
                meta["overall_height"]
                - (skirt["height"] + meta["dome_height_nominal"])
            )
            < 1e-3,
            "overall height is not skirt + dome",
        )

    # --- crossing classes ----------------------------------------------------
    want(
        meta["crossing_type_count"] == 12,
        f"expected 12 symmetry-distinct crossing geometries, got "
        f"{meta['crossing_type_count']}",
    )
    total = sum(t["count"] for t in data["crossing_types"])
    want(
        total == len(data["crossings"]),
        f"crossing classes cover {total} contacts, expected {len(data['crossings'])}",
    )
    tied_contacts = sum(t["count"] for t in data["crossing_types"] if t["tied"])
    want(
        tied_contacts == 60,
        f"expected 60 lashed contacts (10 nodes x 6 pairs), got {tied_contacts}",
    )

    # --- doorway -------------------------------------------------------------
    door = data.get("doorway")
    if door is not None:
        bay = door["bay"]
        frame = door["frame"]
        diameter = meta["dome_diameter"]

        cut = door.get("cut")

        want(
            door["bay_count"] == 5,
            f"expected 5 tall bays to choose a door from, got {door['bay_count']}",
        )
        # The head is a node on a self-similar shape, so its height is an
        # exact fraction of the diameter at every size. The *clear* height
        # under it is that less the rod, and so drifts slightly with how thick
        # the rod is relative to the dome -- 0.2541 of D on D3, 0.2549 on D12.
        want(
            abs(frame["apex_point"][2] / diameter - 0.26287) < 1e-4,
            f"door head is at {frame['apex_point'][2] / diameter:.5f} of D, "
            "expected 0.26287",
        )
        if cut is None:
            want(
                0.2535 < bay["clear_height_mm"] / diameter < 0.2555,
                f"door clear height is {bay['clear_height_mm'] / diameter:.4f} "
                "of D, expected about 0.254",
            )
            want(
                abs(bay["span_deg"] - 34.5) < 0.5,
                f"door bay spans {bay['span_deg']:.2f} deg, expected 34.5",
            )
        else:
            # Taking rod away can only open the bay up.
            want(
                bay["clear_height_mm"] / diameter > 0.2535,
                f"cutting the jambs made the opening shorter: "
                f"{bay['clear_height_mm'] / diameter:.4f} of D",
            )
            want(
                bay["span_deg"] >= 34.5 - 0.5,
                f"cutting the jambs made the bay narrower: {bay['span_deg']:.2f} deg",
            )
            # The whole justification for cutting at all.
            want(
                cut["cost"]["severs_nothing"],
                f"the door cut severs {cut['cost']['severed_bows']} -- only end "
                "pieces may be removed without turning a bow into two bows",
            )
            want(
                sorted(cut["spans"]) == sorted(frame["jamb_rods"]),
                f"the cut takes {sorted(cut['spans'])}, expected the jambs "
                f"{sorted(frame['jamb_rods'])}",
            )
            want(
                abs(cut["cost"]["rod_removed_fraction"] - 2.0 / 75.0) < 1e-3,
                "cutting two of fifteen bows' five equal pieces should remove "
                f"2/75 of the rod, got {cut['cost']['rod_removed_fraction']:.4f}",
            )
        # The whole point of this doorway: it cuts nothing. Its head is a
        # lashed four-rod node and its feet are two base points.
        apex = next(
            (n for n in data["nodes"] if n["name"] == frame["apex_node"]), None
        )
        want(apex is not None, f"door head {frame['apex_node']} is not a node")
        if apex is not None:
            want(
                apex["rod_count"] == 4,
                f"door head {apex['name']} has {apex['rod_count']} rods, expected 4",
            )
        feet_names = {b["name"] for b in data["base_nodes"]}
        want(
            set(frame["feet"]) <= feet_names,
            f"door feet {frame['feet']} are not base points",
        )
        want(
            len(frame["jamb_rods"]) == 2
            and len(set(frame["jamb_rods"])) == 2
            and all(r in frame["apex_rods"] for r in frame["jamb_rods"]),
            f"door jambs {frame['jamb_rods']} do not both meet at the head",
        )
        # The outline has to start and end on the ground, or it is not a hole
        # anyone can walk through.
        points = door["outline"]["points"]
        ground = meta.get("ground_z", 0.0)
        want(
            abs(points[0][2] - ground) < 1e-3 and abs(points[-1][2] - ground) < 1e-3,
            f"door outline does not start and end at ground z={ground}",
        )
        if cut is None:
            want(
                abs(max(p[2] for p in points) - frame["apex_point"][2]) < 1e-3,
                "door outline does not reach the head node",
            )
        else:
            # A traced outline follows the rod surface, so it stops a rod short
            # of the centreline it runs under.
            want(
                max(p[2] for p in points) < frame["apex_point"][2] + 1e-3,
                "cut door outline rises above the head node",
            )
        want(
            door["door"]["fits"],
            f"the {door['door']['template']} silhouette does not fit "
            f"{meta['variant']}'s door -- the skirt in variants.toml is too short",
        )

    return problems
