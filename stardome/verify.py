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

        # --- the skirt is braced -------------------------------------------
        #
        # A ring of pin-ended verticals with a ring at each end is a mechanism:
        # every bay is a parallelogram. These check that it is not left that
        # way, since the drawing looks the same either way.
        bays = skirt["bay_count"]
        open_bays = set(skirt["open_bays"])
        expected_ring = set(range(bays)) - open_bays
        for tag in ("top_ring", "bottom_ring"):
            visited = {seg["bay"] for seg in skirt[tag]}
            want(
                visited == expected_ring,
                f"{tag} covers bays {sorted(visited)}, expected "
                f"{sorted(expected_ring)} -- every bay but the doorway",
            )
        # Removing the diagonals is not enough to make a doorway: a ring
        # segment across the bay is a bar along the ground and another at head
        # height. Neither is a hole.
        for tag in ("top_ring", "bottom_ring"):
            crossing = [seg for seg in skirt[tag] if seg["bay"] in open_bays]
            want(
                not crossing,
                f"{tag} still runs across the doorway in bay "
                f"{[seg['bay'] for seg in crossing]}",
            )
        want(
            abs(skirt["top_ring_length"] - skirt["bottom_ring_length"]) < 1e-3,
            "the two rings are the same polygon, so they should be the same "
            f"length: {skirt['top_ring_length']} vs {skirt['bottom_ring_length']}",
        )

        braced = {b["bay"] for b in skirt["braces"]}
        want(
            braced == set(range(bays)) - open_bays,
            f"bays {sorted(set(range(bays)) - open_bays - braced)} carry no "
            "diagonal and would rack",
        )
        for bay in braced:
            pair = [b for b in skirt["braces"] if b["bay"] == bay]
            want(
                len(pair) == 2,
                f"bay {bay} has {len(pair)} diagonals, expected a crossed pair",
            )
        want(
            all(b["member"] == "tension" for b in skirt["braces"]),
            "the diagonals must be tension members: a 1.8 m compression strut "
            "is the one thing in this structure that can buckle",
        )
        if skirt["braces"]:
            angle = skirt["brace_angle_deg"]
            want(
                30.0 <= angle <= 60.0,
                f"diagonals meet the ground at {angle:.1f} deg; outside 30-60 "
                "a brace is either mostly pulling the posts together or "
                "mostly lifting them",
            )
        want(
            len(open_bays) <= 1,
            f"{len(open_bays)} bays left open; one doorway is enough to weaken",
        )

        # An open bay leaves the top ring an open arc, which carries no hoop
        # tension at all. Something has to take that force over the doorway.
        header = skirt.get("header")
        if open_bays:
            want(
                header is not None,
                "the doorway bay breaks the top ring and nothing carries the "
                "hoop force over the opening",
            )
        if header is not None:
            want(
                header["bay"] in open_bays,
                f"the header sits over bay {header['bay']}, which is not the "
                f"doorway {sorted(open_bays)}",
            )
            want(
                len(set(header["rods"])) == 2,
                f"the header should tie two different bows, got {header['rods']}",
            )
            want(
                abs(header["a"][2] - header["b"][2]) < 1.0,
                "the header is not level: "
                f"{header['a'][2]:.1f} against {header['b'][2]:.1f}",
            )
            want(
                header["height_above_ground"] > skirt["height"],
                "the header is inside the skirt rather than over the doorway",
            )
            door = data.get("doorway")
            if door is not None:
                want(
                    header["height_above_ground"]
                    <= door["in_bay"]["clear_height_mm"] + skirt["height"] + 1.0,
                    "the header is above the dome's own opening, where it "
                    "carries nothing over anything",
                )
                # A lintel that blocks what the doorway was passing is not a
                # lintel, it is an obstruction. Measured against what the
                # opening actually admits, not what it is nominally sized for.
                from . import entrance

                for name in door.get("admits", []):
                    needs = max(z for z, _ in entrance.TEMPLATES[name])
                    want(
                        header["height_above_ground"] >= needs,
                        f"the door admits {name} at {needs:.0f} mm but the "
                        f"header sits at {header['height_above_ground']:.0f}",
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
    #
    # A door is either a tall bay -- the lancet, optionally cut open -- or a
    # portal, which is a low bay with the crossing that fills it removed. They
    # are different shapes with different heads, so they get different checks.
    door = data.get("doorway")
    if door is not None:
        bay = door["bay"]
        frame = door["frame"]
        cut = door.get("cut")
        diameter = meta["dome_diameter"]
        level = cut["level"] if cut else "none"

        want(
            door["bay_count"] == 5,
            f"expected 5 tall bays to choose a door from, got {door['bay_count']}",
        )

        points = door["outline"]["points"]
        ground = meta.get("ground_z", 0.0)
        want(
            abs(points[0][2] - ground) < 1e-3 and abs(points[-1][2] - ground) < 1e-3,
            f"door outline does not start and end at ground z={ground}",
        )

        if cut is not None:
            want(
                len(cut["spans"]) >= 2,
                f"a cut takes pieces off at least two rods, got {sorted(cut['spans'])}",
            )

    if door is not None and level == "portal":
        # Two U bows rising from adjacent base points, and one L bow lying
        # nearly level across the top: a doorway with a lintel rather than a
        # pointed arch. Its head is higher than the tall bay's, which is the
        # whole reason to prefer it.
        want(
            frame is None,
            "a portal has no lancet to describe, so frame should be empty",
        )
        want(
            0.298 < bay["clear_height_mm"] / diameter < 0.305,
            f"portal head is at {bay['clear_height_mm'] / diameter:.4f} of D, "
            "expected about 0.3009",
        )
        want(
            bay["clear_height_mm"] > 0.2629 * diameter,
            "a portal no taller than the tall bay's head node is not worth "
            "the rod it costs",
        )
        # Why this cut is affordable: both spans run to a bow end, so each bow
        # simply starts higher up instead of becoming two bows.
        want(
            cut["cost"]["severs_nothing"],
            f"the portal cut severs {cut['cost']['severed_bows']} -- both "
            "spans should run contiguously to a bow end",
        )
        want(
            not cut["cost"]["nodes_with_nothing_through"],
            "the portal cut should leave every node with something running "
            f"through it, but stranded {cut['cost']['nodes_with_nothing_through']}",
        )
        want(
            len(cut["spans"]) == 2,
            "the portal clears one crossing, so exactly two rods lose a span; "
            f"got {sorted(cut['spans'])}",
        )
        want(
            abs(cut["cost"]["rod_removed_fraction"] - 0.028) < 2e-3,
            "clearing the crossing costs about 2.8% of the rod, got "
            f"{cut['cost']['rod_removed_fraction']:.4f}",
        )

    elif door is not None:
        # The head is a node on a self-similar shape, so its height is an
        # exact fraction of the diameter at every size. The *clear* height
        # under it is that less the rod, and so drifts slightly with how thick
        # the rod is relative to the dome -- 0.2541 of D on D3, 0.2549 on D12.
        want(
            abs(frame["apex_point"][2] / diameter - 0.26287) < 1e-4,
            f"door head is at {frame['apex_point'][2] / diameter:.5f} of D, "
            "expected 0.26287",
        )
        # Its head is a lashed four-rod node and its feet are two base points.
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

        if level == "none":
            want(
                0.2535 < bay["clear_height_mm"] / diameter < 0.2555,
                f"door clear height is {bay['clear_height_mm'] / diameter:.4f} "
                "of D, expected about 0.254",
            )
            want(
                abs(bay["span_deg"] - 34.5) < 0.5,
                f"door bay spans {bay['span_deg']:.2f} deg, expected 34.5",
            )
            want(
                abs(max(p[2] for p in points) - frame["apex_point"][2]) < 1e-3,
                "door outline does not reach the head node",
            )
        else:
            # Taking rod away can only open the bay up.
            want(
                bay["clear_height_mm"] / diameter > 0.2535,
                "cutting made the opening shorter: "
                f"{bay['clear_height_mm'] / diameter:.4f} of D",
            )
            want(
                bay["span_deg"] >= 34.5 - 0.5,
                f"cutting made the bay narrower: {bay['span_deg']:.2f} deg",
            )
            # A cut here only ever takes pieces off rods meeting the head.
            want(
                set(cut["spans"]) <= set(frame["apex_rods"]),
                f"the cut takes {sorted(cut['spans'])}, which is not a subset "
                f"of the rods at the head node {sorted(frame['apex_rods'])}",
            )

        if level == "jambs":
            # The justification for this level: it is free of the one thing
            # that makes cutting expensive.
            want(
                cut["cost"]["severs_nothing"],
                f"the jamb cut severs {cut['cost']['severed_bows']} -- at this "
                "level only end pieces may go",
            )
            want(
                sorted(cut["spans"]) == sorted(frame["jamb_rods"]),
                f"the jamb cut takes {sorted(cut['spans'])}, expected "
                f"{sorted(frame['jamb_rods'])}",
            )
            want(
                abs(cut["cost"]["rod_removed_fraction"] - 2.0 / 75.0) < 1e-3,
                "two of fifteen bows' five equal pieces is 2/75 of the rod, "
                f"got {cut['cost']['rod_removed_fraction']:.4f}",
            )
            want(
                not cut["cost"]["nodes_with_nothing_through"],
                "the jamb cut should leave the head node with two rods still "
                f"through it, but stranded {cut['cost']['nodes_with_nothing_through']}",
            )
            want(
                max(p[2] for p in points) < frame["apex_point"][2] + 1e-3,
                "cut door outline rises above the head node",
            )
        elif level == "head":
            # Defined by going further, and the cost has to be visible.
            want(
                sorted(cut["spans"]) == sorted(frame["apex_rods"]),
                f"the head cut takes {sorted(cut['spans'])}, expected all four "
                f"rods at the head {sorted(frame['apex_rods'])}",
            )
            want(
                sorted(cut["cost"]["severed_bows"])
                == sorted(set(frame["apex_rods"]) - set(frame["jamb_rods"])),
                "the head cut should sever exactly the two non-jamb rods, got "
                f"{cut['cost']['severed_bows']}",
            )
            want(
                cut["cost"]["nodes_with_nothing_through"] == [frame["apex_node"]],
                "the head cut should strand exactly the head node, got "
                f"{cut['cost']['nodes_with_nothing_through']}",
            )
            want(
                max(p[2] for p in points) > frame["apex_point"][2],
                "the head cut should open the bay past its old head node",
            )

    # --- the fabric cover ---------------------------------------------------
    cover_data = data.get("cover")
    if cover_data:
        rc = cover_data["radius_mm"]
        want(
            rc > radius,
            f"the cover must lie outside the nominal sphere, got {rc} vs {radius}",
        )
        # It rests on the outermost rod, so it can never be further out than
        # that rod's surface -- a cover floating clear of the frame is a bug
        # in the radius, not a design.
        outer = meta["max_diameter_woven"] / 2.0
        want(
            abs(rc - outer) < 1e-6,
            f"cover radius {rc} should be the woven outer radius {outer}",
        )
        areas = cover_data["areas"]
        want(
            areas["total_m2"] <= areas["gross_m2"] + 1e-9,
            "cutting the doorway out cannot make the cover bigger",
        )
        # A hemisphere is 2*pi*R^2 and nothing else; this catches a factor of
        # two or a radius read in the wrong units at a glance.
        expect = 2.0 * math.pi * rc * rc / 1e6
        want(
            abs(areas["dome_m2"] - expect) < 0.02,
            f"dome fabric should be 2*pi*R^2 = {expect:.2f} m2, "
            f"got {areas['dome_m2']}",
        )
        gores = cover_data["gores"]
        want(
            gores["gore_width_mm"] <= gores["roll_width_mm"] + 1e-6,
            "the gore has to fit across the roll it is cut from",
        )

    # --- a corridor, when one is attached -----------------------------------
    corridor_data = data.get("corridor")
    if corridor_data and corridor_data.get("present"):
        m = corridor_data["mouth"]
        if m["fits_on_dome"]:
            rc = cover_data["radius_mm"]
            ground = meta.get("ground_z", 0.0) or 0.0
            for p in m["points"]:
                x, y, z = p
                # On the sphere above the base ring, on the skirt cylinder
                # below it. Either way the mouth must lie ON the cover: a
                # point off it is a corridor joined to thin air.
                got = (
                    math.sqrt(x * x + y * y + z * z) if z >= -1e-9
                    else math.hypot(x, y)
                )
                if abs(got - rc) > 0.5:
                    problems.append(
                        f"corridor mouth point {p} is {got:.1f} mm from the "
                        f"centre, not on the cover at {rc:.1f}"
                    )
                    break
                if z < ground - 1e-6:
                    problems.append(f"corridor mouth point {p} is below ground")
                    break

    return problems
