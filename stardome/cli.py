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

from . import config, connectors, export, model, verify


def _variant_names(args) -> list:
    if args.all:
        return list(config.load_all(args.config))
    if not args.variant:
        raise SystemExit("give a variant name, or --all")
    return args.variant


def cmd_build(args) -> int:
    for name in _variant_names(args):
        variant = config.load(name, args.config)
        data = model.build(
            variant,
            weave_mode=args.weave_mode,
            include_polylines=args.polylines,
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
                help="include sampled rod centrelines (large)",
            )
        if name == "snapshot":
            p.add_argument("-o", "--out", default="tests/golden", type=Path)
        if name == "scad-config":
            p.add_argument("-o", "--out", default="configs/variants.scad", type=Path)
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
