"""Command line entry point.

    python3 -m stardome build D6
    python3 -m stardome build --all -o exports/model
    python3 -m stardome report D6
    python3 -m stardome verify --all

Everything an agent or a Makefile needs is here; nothing requires opening a
GUI. See docs/architecture.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import (
    camp,
    config,
    connectors,
    corridor,
    cover,
    doorway,
    entrance,
    export,
    interior,
    model,
    verify,
    weave,
    wind,
)


def _variant_names(args) -> list:
    if args.all:
        return list(config.load_all(args.config))
    if not args.variant:
        raise SystemExit("give a variant name, or --all")
    return args.variant


def cmd_build(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        spec = None
        if args.corridor:
            spec = {"include_geometry": args.polylines}
        elif args.corridor_fit:
            # Size the corridor to what this dome's own doorway admits, which
            # is how a camp of different sizes gets corridors that are each
            # buildable rather than one that fits nobody.
            probe = model.build(variant, weave_mode=args.weave_mode)
            fitted = corridor.fitted_spec(probe)
            if fitted:
                spec = dict(fitted, include_geometry=args.polylines)
        data = model.build(
            variant,
            weave_mode=args.weave_mode,
            include_polylines=args.polylines,
            corridor_spec=spec,
        )
        paths = export.write_all(data, args.out)
        print(f"{name}: {len(paths)} files -> {args.out}")
    return 0


def cmd_report(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        meta = data["meta"]
        print(f"--- {name} -- {meta['variant_note']}")
        print(f"  diameter          {meta['dome_diameter']:.1f} mm")
        print(f"  structural height {meta['dome_height_nominal']:.1f} mm")
        if meta.get("skirt_height"):
            print(f"  skirt             {meta['skirt_height']:.1f} mm")
            print(f"  overall height    {meta['overall_height']:.1f} mm")
        print(f"  bend radius       {meta['dome_radius']:.1f} mm  (every bow)")
        print(f"  rods              {meta['rod_count']} x {meta['rod_length_nominal']:.1f} mm"
              f"  = {meta['total_rod_length']:.1f} mm total")
        print(f"  crossing points   {meta['crossing_point_count']}"
              f"  ({meta['crossing_pair_count']} rod-to-rod contacts)")
        print(f"  connector classes {meta['crossing_type_count']}")
        angles = sorted({t["angle_deg"] for t in data["crossing_types"]})
        print(f"  crossing angles   {', '.join(f'{a:.4f}' for a in angles)} deg")
    return 0


def cmd_snapshot(args) -> int:
    """Refresh the small golden files that guard against silent maths changes."""
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        path = out / f"{name.lower()}.json"
        path.write_text(export.summary(data), encoding="utf-8")
        print(f"{name}: {path}")
    return 0


def cmd_connectors(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        sched = connectors.schedule(data)
        if args.json:
            path = Path(args.out) / f"star_dome_{name.lower()}_connectors.json"
            export.write_json(sched, path)
            print(f"{name}: {path}")
        else:
            print(connectors.format_schedule(sched))
    return 0


def cmd_weave(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        print(weave.format_analysis(data))
        print(weave.format_global(data))
    return 0


def cmd_entrance(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        print(entrance.format_analysis(data, clearance_mm=args.clearance))
        if args.door:
            height, width = args.door
            r = entrance.skirt_for_door(
                data, height, width, clearance_mm=args.clearance
            )
            if not r["possible"]:
                print(f"  a {width:g} x {height:g} door: {r['why']}")
            else:
                print(
                    f"  a {width:g} x {height:g} door needs "
                    f"{r['skirt_needed_mm']:.0f} mm of skirt "
                    f"(dome reaches {r['dome_reach_mm']:.0f} mm at that width; "
                    f"{r['skirt_present_mm']:.0f} mm present) -> "
                    f"{r['overall_height_mm']:.0f} mm overall"
                )
    return 0


def cmd_doorway(args) -> int:
    for name in _variant_names(args):
        overrides = {}
        if args.skirt is not None:
            overrides["skirt_height"] = float(args.skirt)
        variant = config.load(name, args.config, **overrides)
        template = args.template or variant.door or doorway.DEFAULT_TEMPLATE
        data = model.build(variant, weave_mode=args.weave_mode)
        print(doorway.format_analysis(data, template, clearance_mm=args.clearance))
        if args.cut:
            cuts = doorway.jamb_cut(data)
            r = doorway.with_cut(data, cuts, template, args.clearance)
            cost = r["cost"]
            spans = ", ".join(
                f"{rod} {lo:.0f}-{hi:.0f} deg"
                for rod, s in r["cuts"].items()
                for lo, hi in s
            )
            print(f"  cut the jambs out ({spans}):")
            print(
                f"    clear {r['clear_height_mm']:.0f} mm, "
                + ", ".join(
                    f"{h} mm high: {w:.0f} wide" for h, w in r["widths_mm"].items()
                )
            )
            print(f"    admits: {', '.join(r['admits']) or 'nothing'}")
            print(
                f"    costs {cost['rod_removed_mm'] / 1000:.1f} m of rod "
                f"({cost['rod_removed_fraction'] * 100:.1f}%), "
                + (
                    "severs nothing -- both are end pieces"
                    if cost["severs_nothing"]
                    else f"SEVERS {', '.join(cost['severed_bows'])}"
                )
            )
        if args.skirt_for:
            wanted = args.skirt_for
            needed = doorway.skirt_for_template(
                data, wanted, clearance_mm=args.clearance
            )
            if needed != needed:  # NaN
                print(f"  no skirt under 3 m lets a {wanted} silhouette through")
            else:
                print(
                    f"  a {wanted} silhouette needs {needed:.0f} mm of skirt "
                    f"({variant.skirt_height:.0f} mm present)"
                )
    return 0


def cmd_interior(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        if args.skirt is not None:
            variant = config.load(
                name, args.config, skirt_height=float(args.skirt)
            )
        data = model.build(variant, weave_mode=args.weave_mode)
        print(interior.format_analysis(data))
    return 0


def cmd_cover(args) -> int:
    if args.summary:
        rows = []
        for name in _variant_names(args):
            variant = config.load(name, args.config)
            if args.skirt is not None:
                variant = config.load(name, args.config, skirt_height=float(args.skirt))
            data = model.build(variant, weave_mode=args.weave_mode)
            rows.append(cover.summary_row(
                data, args.roll, args.lap, args.oversize, args.price, args.leaves
            ))
        print(cover.format_summary(rows, args.roll, args.oversize, args.price))
        return 0
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        if args.skirt is not None:
            variant = config.load(
                name, args.config, skirt_height=float(args.skirt)
            )
        data = model.build(variant, weave_mode=args.weave_mode)
        if args.patterns:
            print(cover.format_patterns(
                data,
                roll_width_mm=args.roll,
                lap_mm=args.lap,
                oversize=args.oversize,
                price_per_m=args.price,
            ))
        else:
            print(cover.format_analysis(data, roll_width_mm=args.roll))
    return 0


def cmd_corridor(args) -> int:
    # Each kind has its own sensible size, so an unset flag means "this kind's
    # default" rather than "the hoop's default applied to a timber frame".
    if args.kind == "portal":
        args.width = args.width or corridor.DEFAULT_PORTAL_WIDTH_MM
        args.height = args.height or corridor.DEFAULT_PORTAL_HEIGHT_MM
        args.pitch = args.pitch or corridor.DEFAULT_PORTAL_PITCH_MM
    else:
        args.width = args.width or corridor.DEFAULT_WIDTH_MM
        args.height = args.height or corridor.DEFAULT_HEIGHT_MM
        args.pitch = args.pitch or corridor.DEFAULT_PITCH_MM
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        if args.skirt is not None:
            variant = config.load(
                name, args.config, skirt_height=float(args.skirt)
            )
        data = model.build(variant, weave_mode=args.weave_mode)
        print(
            corridor.format_analysis(
                data,
                width=args.width,
                height=args.height,
                length=args.length,
                pitch=args.pitch,
                kind=args.kind,
                brace_leg=args.brace,
            )
        )
    return 0


# The camp the project keeps coming back to: a hall with three ways out of
# it, one of which leads on to a fourth dome. Labels are what the links name.
DEFAULT_CAMP = ["L", "M", "S", "S", "S"]
DEFAULT_LINKS = ["L:M", "L:S1", "L:S2", "M:S3"]


def _camp_labels(variants: list) -> list:
    """S, S, S becomes S1, S2, S3; a lone M stays M."""
    seen = {}
    out = []
    for v in variants:
        seen[v] = seen.get(v, 0) + 1
        out.append(v)
    count = dict(seen)
    running = {}
    for i, v in enumerate(variants):
        if count[v] == 1:
            out[i] = v
        else:
            running[v] = running.get(v, 0) + 1
            out[i] = f"{v}{running[v]}"
    return out


def cmd_camp(args) -> int:
    variants = args.dome or DEFAULT_CAMP
    labels = _camp_labels(variants)
    built = {}
    for label, variant in zip(labels, variants):
        built[label] = model.build(
            config.load(variant, args.config),
            weave_mode=args.weave_mode,
            include_polylines=args.polylines,
        )

    links = []
    for text in (args.link or DEFAULT_LINKS):
        if ":" not in text:
            raise SystemExit(f"link {text!r} should look like L:M")
        a, b = text.split(":", 1)
        links.append((a.strip(), b.strip()))

    spec = {
        "kind": args.kind,
        "width": args.width if args.width is not None else (
            corridor.DEFAULT_PORTAL_WIDTH_MM if args.kind == "portal"
            else corridor.DEFAULT_WIDTH_MM
        ),
        "height": args.height if args.height is not None else (
            corridor.DEFAULT_PORTAL_HEIGHT_MM if args.kind == "portal"
            else corridor.DEFAULT_HEIGHT_MM
        ),
        "length": args.length,
        "pitch": args.pitch if args.pitch is not None else (
            corridor.DEFAULT_PORTAL_PITCH_MM if args.kind == "portal"
            else corridor.DEFAULT_PITCH_MM
        ),
        "brace_leg": args.brace,
    }

    try:
        plan = camp.solve(built, links, spec)
    except ValueError as problem:
        raise SystemExit(f"cannot lay this camp out: {problem}")

    camp.geometry(plan, built)
    overlaps = camp.clashes(plan, built)
    plan["clashes"] = overlaps
    plan["junctions"] = camp.junctions(plan, built)

    if args.json:
        path = Path(args.out) / "star_dome_camp.json"
        export.write_json(plan, path)
        print(f"camp: {path}")
    else:
        print(camp.format_plan(plan))
        if overlaps:
            print()
            for bad in overlaps:
                print(
                    f"  CLASH  {bad['a']} and {bad['b']} overlap by "
                    f"{bad['overlap_mm'] / 1000.0:.2f} m"
                )
    return 0


def cmd_wind(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        if args.skirt is not None:
            variant = config.load(
                name, args.config, skirt_height=float(args.skirt)
            )
        data = model.build(variant, weave_mode=args.weave_mode)
        print(wind.format_analysis(data, cf=args.cf, fabric=args.fabric))
        print()
    return 0


def cmd_scad_config(args) -> int:
    """Regenerate configs/variants.scad from configs/variants.toml."""
    variants = config.load_all(args.config)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(export.scad_variants(variants), encoding="utf-8")
    print(f"{path}  ({', '.join(variants)})")
    return 0


def cmd_verify(args) -> int:
    failures = 0
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        problems = verify.check(data)
        if problems:
            failures += len(problems)
            print(f"{name}: {len(problems)} FAILED")
            for p in problems:
                print("   ", p)
        else:
            print(f"{name}: all invariants hold")
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stardome", description=__doc__)
    parser.add_argument("--config", default=None, help="path to variants.toml")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, fn, helptext in (
        ("build", cmd_build, "generate model.json + CSV tables"),
        ("report", cmd_report, "print the derived dimensions"),
        ("verify", cmd_verify, "check the geometric invariants"),
        ("snapshot", cmd_snapshot, "refresh the committed golden summaries"),
        ("scad-config", cmd_scad_config, "regenerate configs/variants.scad from the TOML"),
        ("connectors", cmd_connectors, "derive which connector parts the dome needs"),
        ("weave", cmd_weave, "four-rod node fan geometry and the stacking order"),
        ("entrance", cmd_entrance, "where a doorway fits, and how big it can be"),
        ("doorway", cmd_doorway, "the chosen door: which bay, framed by what"),
        ("interior", cmd_interior, "how much floor you can stand on, and what a skirt costs"),
        ("cover", cmd_cover, "fabric area, and how few gores it sews from"),
        ("corridor", cmd_corridor, "a covered corridor on the doorway, and whether it fits"),
        ("camp", cmd_camp, "several domes joined by corridors, and where they may stand"),
        ("wind", cmd_wind, "SCREENING ONLY: sail area, drag and what has to hold it down"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("variant", nargs="*", help="variant name, e.g. D6")
        p.add_argument("--all", action="store_true", help="every named variant")
        p.add_argument(
            "--weave-mode",
            dest="weave_mode",
            default="flat",
            choices=("flat", "layered"),
            help="flat (default) for measurement; layered is a drawing convention",
        )
        if name == "build":
            p.add_argument("-o", "--out", default="exports/model", type=Path)
            p.add_argument(
                "--polylines",
                action="store_true",
                help="include sampled rod centrelines and the cover mesh (large)",
            )
            p.add_argument(
                "--corridor",
                action="store_true",
                help="attach a corridor to the doorway and carry it in the model",
            )
            p.add_argument(
                "--corridor-fit",
                dest="corridor_fit",
                action="store_true",
                help="same, but sized to the largest this dome's doorway admits",
            )
        if name == "snapshot":
            p.add_argument("-o", "--out", default="tests/golden", type=Path)
        if name == "scad-config":
            p.add_argument("-o", "--out", default="configs/variants.scad", type=Path)
        if name in ("interior", "doorway", "cover", "corridor", "wind"):
            p.add_argument(
                "--skirt",
                type=float,
                default=None,
                help="override the variant's skirt height, mm, to try a trade",
            )
        if name == "doorway":
            p.add_argument(
                "--template",
                default=None,
                help="person silhouette to fit; default is the variant's own",
            )
            p.add_argument(
                "--cut",
                action="store_true",
                help="also report the doorway with its two jamb pieces cut out",
            )
            p.add_argument(
                "--skirt-for",
                dest="skirt_for",
                default=None,
                metavar="TEMPLATE",
                help="also solve for the shortest skirt this silhouette needs",
            )
        if name in ("entrance", "doorway"):
            p.add_argument(
                "--clearance",
                type=float,
                default=0.0,
                help="mm kept clear of every rod surface, on top of the rod radius",
            )
            p.add_argument(
                "--door",
                nargs=2,
                type=float,
                metavar=("HEIGHT", "WIDTH"),
                help="also solve for the skirt a door of this size would need",
            )
        if name == "cover":
            p.add_argument(
                "--roll",
                type=float,
                default=cover.DEFAULT_ROLL_WIDTH_MM,
                help="fabric roll width, mm; sets the gore count",
            )
            p.add_argument(
                "--patterns",
                action="store_true",
                help="compare the three cutting patterns instead of the areas",
            )
            p.add_argument(
                "--summary",
                action="store_true",
                help="one line per size, for comparing sizes rather than patterns",
            )
            p.add_argument(
                "--leaves",
                type=int,
                default=5,
                help="leaves in the summary's leaf pattern; 5 or 10",
            )
            p.add_argument(
                "--price",
                type=float,
                default=None,
                metavar="PER_M",
                help="price per running metre of roll, to cost each pattern",
            )
            p.add_argument(
                "--lap",
                type=float,
                default=cover.DEFAULT_LAP_MM,
                help="overlap between horizontal lanes in a leaf, mm",
            )
            p.add_argument(
                "--oversize",
                type=float,
                default=cover.DEFAULT_OVERSIZE,
                help="fraction larger than the frame; Takekawa's figure is 0.10",
            )
        if name == "corridor":
            p.add_argument(
                "--kind",
                choices=corridor.KINDS,
                default="hoop",
                help="hoop: bent rod, narrow. portal: boards in a P-frame with "
                     "knee braces, 1.5-2 m wide",
            )
            p.add_argument("--width", type=float, default=None)
            p.add_argument("--height", type=float, default=None)
            p.add_argument("--length", type=float, default=corridor.DEFAULT_LENGTH_MM)
            p.add_argument("--pitch", type=float, default=None)
            p.add_argument(
                "--brace",
                type=float,
                default=corridor.DEFAULT_BRACE_LEG_MM,
                help="knee-brace leg, mm; portal only",
            )
        if name == "wind":
            p.add_argument(
                "--cf", type=float, default=wind.DEFAULT_CF,
                help="force coefficient on the silhouette; assumed, not measured",
            )
            p.add_argument(
                "--fabric", default=wind.DEFAULT_FABRIC,
                choices=sorted(wind.FABRIC),
                help="cover fabric; areal weights are nominal, weigh the roll",
            )
        if name == "camp":
            p.add_argument(
                "--dome", action="append",
                help="a dome in the camp, repeatable; default L M S S S",
            )
            p.add_argument(
                "--link", action="append", metavar="A:B",
                help="a corridor between two labels, repeatable; "
                     "default L:M L:S1 L:S2 M:S3",
            )
            p.add_argument("--kind", choices=corridor.KINDS, default="hoop")
            p.add_argument("--width", type=float, default=None)
            p.add_argument("--height", type=float, default=None)
            p.add_argument("--length", type=float, default=corridor.DEFAULT_LENGTH_MM)
            p.add_argument("--pitch", type=float, default=None)
            p.add_argument(
                "--brace", type=float, default=corridor.DEFAULT_BRACE_LEG_MM
            )
            p.add_argument(
                "--polylines", action="store_true",
                help="carry rod centrelines too, so a scene can be built from it",
            )
            p.add_argument("--json", action="store_true")
            p.add_argument("-o", "--out", default="exports/model", type=Path)
        if name == "connectors":
            p.add_argument("--json", action="store_true", help="write the schedule instead of printing it")
            p.add_argument("-o", "--out", default="exports/model", type=Path)
        p.set_defaults(func=fn)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
