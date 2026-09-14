"""Reproduce the one-at-a-time and directional studies, with source hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy
import scipy
from .wind_study import ROOT, run, settings
from stardome import loads


def plan():
    cfg = settings()
    for variant, area_key in (("D4", "area_factors_d8"), ("D6", "area_factors_d10")):
        base = {"variant": variant, "step": cfg["study"]["mesh_step_deg"],
                "modulus": cfg["rod"]["modulus_mpa"][0], "speeds": cfg["study"]["wind_ms"]}
        scenarios = [("continuous", {}), ("mesh-refined", {"step": cfg["study"]["refined_step_deg"]}),
                     ("lashed", {"holds": "lashed"})]
        scenarios += [(f"E{e:g}", {"modulus": e}) for e in cfg["rod"]["modulus_mpa"][1:]]
        scenarios += [(f"area{a:g}", {"area_factor": a}) for a in cfg["rod"][area_key] if a != 1]
        scenarios += [(f"tension{t:g}", {"tension": t}) for t in cfg["fabric"]["tension_n_m"] if t != 0]
        scenarios += [(f"eta{eta:g}", {"eta": eta}) for eta in cfg["tube"]["joint_efficiency"]]
        scenarios += [("eta0.1-tension50", {"eta": .1, "tension": 50})]
        for label, kw in scenarios:
            yield f"{variant}-{label}", base | kw
        # Directional sweep of the continuous cap: both closed-door pressure
        # signs and the windward dominant-opening pressure scenario. Reusing
        # the latter at all angles is an envelope study, not a fixed-door CFD.
        cpis = sorted({*loads.pressure_cases("shut", loads.load()),
                       *loads.pressure_cases("open", loads.load())})
        for cpi in cpis:
            for az in cfg["study"]["azimuth_deg"]:
                yield f"{variant}-cpi{cpi:g}-az{az:g}", base | {"azimuth": az, "cpi": cpi}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", type=Path, required=True)
    args = parser.parse_args()
    args.o.mkdir(parents=True, exist_ok=True)
    sources = sorted([*ROOT.joinpath("analysis").glob("*.py"),
                      *ROOT.joinpath("stardome").glob("*.py"), *ROOT.joinpath("configs").glob("*.toml")])
    manifest = {"python": platform.python_version(), "numpy": numpy.__version__,
                "scipy": scipy.__version__, "operational_limit_ms": None,
                "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sources}, "results": []}
    for name, kwargs in plan():
        report = run(**kwargs)
        path = args.o / (name+".json")
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+"\n")
        manifest["results"].append({"name": name, "inputs": kwargs,
                                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        print(name, report["assembly"]["status"],
              [(c["wind_ms"], round(c.get("short_term_criterion_utilisation", -1), 3), c["status"])
               for c in report["cases"]], flush=True)
    (args.o / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n")


if __name__ == "__main__":
    main()
