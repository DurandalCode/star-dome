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
    assembly,
    attachment,
    bom,
    config,
    connectors,
    corridor,
    cover,
    doorway,
    entrance,
    export,
    interior,
    model,
    span,
    tolerance,
    topology,
    verify,
    weave,
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
        # The schedule is about parts, and a part sits on the rods as woven,
        # not on the nominal sphere. Where each one goes and which way up it
        # faces cannot be answered without the route, so the schedule is
        # always built on it whatever mode the rest of the run asked for.
        data = model.build(variant, weave_mode="woven")
        sched = connectors.schedule(data)
        if args.json:
            # Filed under the geometry's name, not the alias the user typed,
            # so the schedule lands beside the model.json it belongs to --
            # `stardome connectors M` and `stardome build D6` write a matching
            # pair, which is what every consumer downstream assumes.
            path = (
                Path(args.out)
                / f"star_dome_{variant.name.lower()}_connectors.json"
            )
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


def cmd_assembly(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        if args.json:
            path = Path(args.out) / name / "assembly.json"
            export.write_json(assembly.analyse(data), path)
            print(f"{name}: {path}")
        else:
            print(assembly.format_analysis(data))
    return 0


def cmd_tolerance(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        kwargs = dict(
            trials=args.trials,
            ground_sigma=args.ground,
            cut_sigma=args.cut,
            mark_sigma=args.mark,
            ground_method=args.ground_method,
            mark_method=args.mark_method,
            criterion=args.criterion,
            curvature_budget=args.budget,
        )
        if args.json:
            path = Path(args.out) / name / "tolerance.json"
            export.write_json(tolerance.study(data, **kwargs), path)
            print(f"{name}: {path}")
        else:
            print(tolerance.format_study(data, **kwargs))
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
        # A dome with one door reports it the way it always did. With more
        # than one, which openings it has comes first -- the single-door
        # report cannot say that.
        if len(doorway.doors_on(data)) > 1:
            print(doorway.format_doors(data))
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


def cmd_attachment(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        print(attachment.format_analysis(data, args.hem, args.strap_tail))
    return 0


def cmd_cover(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        if args.skirt is not None:
            variant = config.load(
                name, args.config, skirt_height=float(args.skirt)
            )
        data = model.build(variant, weave_mode=args.weave_mode)
        print(cover.format_analysis(data, roll_width_mm=args.roll))
    return 0


def cmd_corridor(args) -> int:
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
            )
        )
    return 0


def cmd_bom(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        # The schedule is always built on the woven route, for the same reason
        # `connectors` builds it there: where a part goes and which way up is
        # derived from the weave, not from the drawing convention.
        data = model.build(variant, weave_mode="woven")
        if args.json:
            path = Path(args.out) / name / "bom.json"
            export.write_json(
                bom.analyse(data, connectors.schedule(data), args.parts), path
            )
            print(f"{name}: {path}")
        else:
            print(
                bom.format_analysis(
                    data, connectors.schedule(data), args.parts
                )
            )
    return 0


def cmd_span(args) -> int:
    ref_variant = config.load(args.reference, args.config)
    ref = span.reference(
        model.build(ref_variant, weave_mode=args.weave_mode), args.holds
    )
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(variant, weave_mode=args.weave_mode)
        if args.json:
            out = span.analyse(data, ref, args.holds)
            # Both readings, because a consumer drawing the spans wants to
            # show what the thirty clamps are worth rather than pick a side.
            out["clamp_value"] = span.clamp_value(data)
            out["spans_contact"] = span.spans(data, "contact")
            path = Path(args.out) / name / "span.json"
            export.write_json(out, path)
            print(f"{name}: {path}")
            continue
        print(span.format_analysis(data, ref, args.holds))
        if args.clamps:
            v = span.clamp_value(data)
            print(
                f"  clamping the free crossings: "
                f"{v['lashed']['length_mm']:.0f} mm on "
                f"{v['lashed']['family']} -> {v['contact']['length_mm']:.0f} mm "
                f"on {v['contact']['family']}, "
                f"{v['span_ratio']:.2f}x in span and "
                f"{v['rod_diameter_ratio']:.2f}x in rod diameter"
            )
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
        ("assembly", cmd_assembly, "the order the bows go up in, and what it costs"),
        ("tolerance", cmd_tolerance, "how accurately the ground, the rods and the marks must be measured"),
        ("entrance", cmd_entrance, "where a doorway fits, and how big it can be"),
        ("doorway", cmd_doorway, "the chosen door: which bay, framed by what"),
        ("interior", cmd_interior, "how much floor you can stand on, and what a skirt costs"),
        ("cover", cmd_cover, "fabric area, and how few gores it sews from"),
        ("attachment", cmd_attachment, "how the cover is held on, and on what"),
        ("corridor", cmd_corridor, "a covered corridor on the doorway, and whether it fits"),
        ("span", cmd_span, "the longest unsupported span, and the ceiling it sets"),
        ("bom", cmd_bom, "everything one dome is made of, counted in one place"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("variant", nargs="*", help="variant name, e.g. D6")
        p.add_argument("--all", action="store_true", help="every named variant")
        p.add_argument(
            "--weave-mode",
            dest="weave_mode",
            default="flat",
            choices=topology.WEAVE_MODES,
            help=(
                "flat (default) for measurement; layered is a drawing "
                "convention; woven is the solved route the connectors sit on"
            ),
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
        if name == "snapshot":
            p.add_argument("-o", "--out", default="tests/golden", type=Path)
        if name == "scad-config":
            p.add_argument("-o", "--out", default="configs/variants.scad", type=Path)
        if name in ("interior", "doorway", "cover", "corridor"):
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
        if name == "attachment":
            p.add_argument(
                "--hem",
                type=float,
                default=attachment.DEFAULT_HEM_MM,
                help="mm of fabric turned under at the base edge",
            )
            p.add_argument(
                "--strap-tail",
                dest="strap_tail",
                type=float,
                default=attachment.DEFAULT_STRAP_TAIL_MM,
                help="mm of webbing past each foot, for tensioning",
            )
        if name == "cover":
            p.add_argument(
                "--roll",
                type=float,
                default=cover.DEFAULT_ROLL_WIDTH_MM,
                help="fabric roll width, mm; sets the gore count",
            )
        if name == "corridor":
            p.add_argument("--width", type=float, default=corridor.DEFAULT_WIDTH_MM)
            p.add_argument("--height", type=float, default=corridor.DEFAULT_HEIGHT_MM)
            p.add_argument("--length", type=float, default=corridor.DEFAULT_LENGTH_MM)
            p.add_argument("--pitch", type=float, default=corridor.DEFAULT_PITCH_MM)
        if name == "bom":
            p.add_argument(
                "--parts",
                default=bom.DEFAULT_PARTS_DIR,
                help="where the built connector meshes are; their solid "
                     "volume is read off them rather than kept in the source",
            )
            p.add_argument("--json", action="store_true",
                           help="write the list instead of printing it")
            p.add_argument("-o", "--out", default="exports/model", type=Path)
        if name == "span":
            p.add_argument(
                "--holds",
                default="lashed",
                choices=span.HOLDS,
                help="what holds a bow: lashed (feet and tie marks, the "
                     "conservative reading) or contact (every crossing clamped)",
            )
            p.add_argument(
                "--reference",
                default=span.REFERENCE_VARIANT,
                help="the dome everything is scaled against",
            )
            p.add_argument(
                "--clamps",
                action="store_true",
                help="also price the thirty free crossings, in span and in rod",
            )
            p.add_argument("--json", action="store_true",
                           help="write the analysis instead of printing it")
            p.add_argument("-o", "--out", default="exports/model", type=Path)
        if name == "assembly":
            p.add_argument("--json", action="store_true", help="write the analysis instead of printing it")
            p.add_argument("-o", "--out", default="exports/model", type=Path)
        if name == "tolerance":
            p.add_argument("--trials", type=int, default=tolerance.DEFAULT_TRIALS)
            p.add_argument("--ground", type=float, default=tolerance.DEFAULT_GROUND_SIGMA,
                           help="one-sigma error pegging a base point, mm")
            p.add_argument("--cut", type=float, default=tolerance.DEFAULT_CUT_SIGMA,
                           help="one-sigma error cutting a bow to length, mm")
            p.add_argument("--mark", type=float, default=tolerance.DEFAULT_MARK_SIGMA,
                           help="one-sigma error placing a tie mark, mm")
            p.add_argument("--ground-method", dest="ground_method",
                           default="radial", choices=tolerance.GROUND_METHODS)
            p.add_argument("--mark-method", dest="mark_method",
                           default="from-end", choices=tolerance.MARK_METHODS)
            p.add_argument("--criterion", default="curvature",
                           choices=tolerance.CRITERIA,
                           help="what a node spread is allowed to be: extra "
                                "bending (default) or marks still overlapping")
            p.add_argument("--budget", type=float,
                           default=tolerance.DEFAULT_CURVATURE_BUDGET,
                           help="extra curvature allowed, as a fraction of the "
                                "rod's own; only used by --criterion curvature")
            p.add_argument("--json", action="store_true", help="write the study instead of printing it")
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
