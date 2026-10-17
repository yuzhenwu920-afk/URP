"""Frozen-input Sobol runner. No crop model or proxy is bundled.

Commands: prepare, benchmark, run, analyze. See README.md for the adapter contract.
The separate test suite uses analytic functions; it does not validate a crop model.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import time
from pathlib import Path

import numpy as np
from SALib.sample import sobol as sample_sobol
from SALib.analyze import sobol as analyze_sobol

NAMES = ["CCx", "CGC_CD", "CDC_CD", "SenescenceCD", "Kcb",
         "WP_early", "WP_late", "HI0"]
OUTPUTS = ["Y_13pct", "B_t_ha", "Tr_mm", "Es_mm", "ET_mm", "MaxCC"]
WATER = ["Irrigation_mm", "Rain_mm", "CR_mm", "GwIn_mm", "Runoff_mm",
         "DeepPerc_mm", "TileDrain_mm", "Profile_initial_mm", "Profile_final_mm",
         "Surface_initial_mm", "Surface_final_mm", "Water_balance_residual_mm",
         "Max_daily_balance_residual_mm"]
REQUIRED = OUTPUTS + ["Y_dry"] + WATER


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               allow_nan=False), encoding="utf-8")
    temp.replace(path)


def versions():
    return {p: importlib.metadata.version(p) for p in ["numpy", "scipy", "SALib"]}


def problem(case):
    bounds = np.array([case["support_bounds"][name] for name in NAMES], dtype=float)
    if bounds.shape != (8, 2) or not np.isfinite(bounds).all() or np.any(bounds[:, 0] >= bounds[:, 1]):
        raise ValueError("Invalid parameter support bounds")
    return {"num_vars": 8, "names": NAMES, "bounds": bounds.tolist()}


def saltelli_labels(n):
    return [f"block{block:05d}:{role}" for block in range(n)
            for role in ["A"] + [f"AB_{k}" for k in NAMES] + ["B"]]


def prepare(config, target, n=128, seeds=(101, 202, 303)):
    if n < 2 or n & (n - 1):
        raise ValueError("N must be a power of two")
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    settings = read(config)
    manifest = {"status": "DESIGN_ONLY_NO_MODEL_RESPONSES", "config_sha256": sha(config),
                "versions": versions(), "N": n, "D": 8, "calc_second_order": False,
                "distribution": "independent_uniform_on_declared_common_global_physical_ranges",
                "not_MCMC_prior_or_posterior": True, "runs": []}
    for year, case in settings["cases"].items():
        p = problem(case)
        for seed in seeds:
            x = sample_sobol.sample(p, n, calc_second_order=False, scramble=True, seed=seed)
            name = f"X_{year}_N{n}_seed{seed}.npy"
            np.save(target / name, x, allow_pickle=False)
            labels = saltelli_labels(n)
            csv_name = name.replace(".npy", ".csv")
            with (target / csv_name).open("w", encoding="utf-8", newline="") as f:
                import csv
                w = csv.writer(f)
                w.writerow(["row_id", "saltelli_role"] + NAMES)
                w.writerows([i, label, *row] for i, (label, row) in enumerate(zip(labels, x)))
            assert x.shape == (n * 10, 8)
            manifest["runs"].append({"year": int(year), "seed": seed, "N": n,
                                     "file": name, "sha256": sha(target / name),
                                     "csv": csv_name, "csv_sha256": sha(target / csv_name),
                                     "rows": len(x)})
    manifest["total_model_calls_required"] = sum(r["rows"] for r in manifest["runs"])
    write(target / "design_manifest.json", manifest)
    return manifest


def load_design(config, designs, year, seed):
    designs = Path(designs)
    m = read(designs / "design_manifest.json")
    if m["config_sha256"] != sha(config):
        raise ValueError("Config changed after design generation")
    run = next(r for r in m["runs"] if r["year"] == year and r["seed"] == seed)
    path = designs / run["file"]
    if sha(path) != run["sha256"]:
        raise ValueError("Design checksum mismatch")
    x = np.load(path, allow_pickle=False)
    case = read(config)["cases"][str(year)]
    bounds = np.array(problem(case)["bounds"])
    if x.shape != (run["rows"], 8) or not np.isfinite(x).all():
        raise ValueError("Design shape or values invalid")
    if np.any(x < bounds[:, 0]) or np.any(x > bounds[:, 1]):
        raise ValueError("Design outside declared parameter bounds")
    return case, run, x


def load_adapter(path):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("urp_real_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    info = module.provenance()
    if info.get("engine") != "Modified_DI_AquaCrop" or info.get("deterministic") is not True:
        raise ValueError("Adapter must explicitly identify the deterministic Modified DI model")
    files = info.get("files", [])
    roles = {entry.get("role") for entry in files}
    if not {"model_source", "input"}.issubset(roles):
        raise ValueError("Provenance requires hashed model source and input files")
    for entry in files:
        source = Path(entry["path"])
        if not source.is_absolute():
            source = path.parent / source
        if sha(source) != entry["sha256"]:
            raise ValueError(f"Source/input checksum mismatch: {source.name}")
    identity = hashlib.sha256(json.dumps({"adapter_sha256": sha(path), "provenance": info},
                            sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return module, identity, info


def check_response(raw, case, expected_irrigation=None):
    """Reject missing ledger fields and units inconsistent with conservation.

    This checks arithmetic consistency, not validation against field measurements.
    CR and GwIn must be separate additive inflows; storage covers the full profile.
    """
    values = {key: float(raw[key]) for key in REQUIRED}
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError("Nonfinite model response")
    signed = {"Water_balance_residual_mm"}
    if any(value < -1e-9 for key, value in values.items() if key not in signed):
        raise ValueError("Negative physical quantity")
    if values["MaxCC"] > 1.005 + 1e-9:
        raise ValueError("MaxCC must be a fraction, not a percentage")
    if not math.isclose(values["Y_dry"], .87 * values["Y_13pct"], abs_tol=1e-7, rel_tol=1e-7):
        raise ValueError("Yield moisture conversion must satisfy Y_dry = 0.87*Y_13pct")
    if not math.isclose(values["ET_mm"], values["Tr_mm"] + values["Es_mm"], abs_tol=1e-6):
        raise ValueError("ET must equal Tr + Es")
    residual = (values["Irrigation_mm"] + values["Rain_mm"] + values["CR_mm"] + values["GwIn_mm"]
                - values["ET_mm"] - values["Runoff_mm"] - values["DeepPerc_mm"] - values["TileDrain_mm"]
                - values["Profile_final_mm"] + values["Profile_initial_mm"]
                - values["Surface_final_mm"] + values["Surface_initial_mm"])
    tolerance = case["acceptance"]["water_balance_atol_mm"]
    if (abs(residual) > tolerance or abs(values["Water_balance_residual_mm"]) > tolerance
            or abs(residual - values["Water_balance_residual_mm"]) > tolerance
            or values["Max_daily_balance_residual_mm"] > tolerance):
        raise ValueError(f"Water ledger does not close: residual={residual}")
    expected = case["baseline_irrigation_mm"] if expected_irrigation is None else expected_irrigation
    if not math.isclose(values["Irrigation_mm"], expected, abs_tol=1e-6, rel_tol=0):
        raise ValueError("Actual irrigation differs from requested management")
    values["IWP_kg_m3"] = 100 * values["Y_13pct"] / expected if expected > 0 else None
    values["ETWP_kg_m3"] = 100 * values["Y_13pct"] / values["ET_mm"] if values["ET_mm"] > 0 else None
    return values


def evaluate(module, params, year, case):
    started = time.perf_counter()
    raw = module.simulate(params=dict(params), year=year, management=None)
    return check_response(raw, case), time.perf_counter() - started


def benchmark(config, adapter, year, output):
    case = read(config)["cases"][str(year)]
    if case["baseline_expected"] is None:
        raise ValueError(f"{year}: original phase-2 and matched baseline outputs are not verified")
    module, identity, info = load_adapter(adapter)
    rows = [evaluate(module, case["central_params"], year, case) for _ in range(2)]
    for key in REQUIRED:
        a, b = rows[0][0][key], rows[1][0][key]
        if not math.isclose(a, b, abs_tol=1e-9, rel_tol=1e-10):
            raise ValueError(f"Repeated baseline changed: {key}; reset model state between calls")
    for key, expected in case["baseline_expected"].items():
        if not math.isclose(rows[0][0][key], expected,
                            abs_tol=case["acceptance"]["baseline_atol"],
                            rel_tol=case["acceptance"]["baseline_rtol"]):
            raise ValueError(f"Original baseline not reproduced: {key}={rows[0][0][key]} vs {expected}")
    result = {"status": "BASELINE_REPRODUCTION_PASSED", "not_external_validation": True,
              "year": year, "config_sha256": sha(config), "adapter_identity": identity,
              "model_provenance": info, "response": rows[0][0],
              "repeat_seconds": [r[1] for r in rows], "versions": versions()}
    write(output, result)
    return result


def run_design(config, designs, adapter, baseline_receipt, year, seed, journal, limit=None):
    case, design, x = load_design(config, designs, year, seed)
    module, identity, info = load_adapter(adapter)
    receipt = read(baseline_receipt)
    if (receipt["status"] != "BASELINE_REPRODUCTION_PASSED" or receipt["year"] != year
            or receipt["config_sha256"] != sha(config) or receipt["adapter_identity"] != identity):
        raise ValueError("A passing receipt for this year, config and adapter is required")
    journal = Path(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    metadata = journal.with_suffix(".metadata.json")
    fingerprint = {"year": year, "seed": seed, "rows_required": len(x),
                   "design_sha256": design["sha256"], "config_sha256": sha(config),
                   "adapter_identity": identity, "baseline_receipt_sha256": sha(baseline_receipt),
                   "versions": versions()}
    if metadata.exists():
        old = read(metadata)
        if old["fingerprint"] != fingerprint:
            raise ValueError("Cannot resume a different design or model version")
    elif journal.exists():
        raise ValueError("Existing response journal has no provenance")
    completed = parse_journal(journal, case, x, require_complete=False) if journal.exists() else {}
    write(metadata, {"status": "PARTIAL", "fingerprint": fingerprint, "model_provenance": info,
                     "successful_rows": len(completed)})
    calls = 0
    with journal.open("a", encoding="utf-8") as f:
        for i, vector in enumerate(x):
            if i in completed:
                continue
            if limit is not None and calls >= limit:
                break
            params = dict(zip(NAMES, map(float, vector)))
            try:
                value, seconds = evaluate(module, params, year, case)
            except Exception as error:
                write(journal.with_suffix(".failure.json"), {"status": "FAILED_NO_IMPUTATION",
                      "row_id": i, "params": params, "error": str(error), "fingerprint": fingerprint})
                raise
            f.write(json.dumps({"row_id": i, "params": params, "outputs": value,
                                "seconds": seconds}, allow_nan=False) + "\n")
            f.flush()
            completed[i] = value
            calls += 1
            if calls % 100 == 0:
                print(f"{year} seed={seed}: {len(completed)}/{len(x)} responses", flush=True)
    status = "COMPLETE" if len(completed) == len(x) else "PARTIAL"
    write(metadata, {"status": status, "fingerprint": fingerprint,
                     "model_provenance": info, "successful_rows": len(completed)})
    return {"status": status, "successful_rows": len(completed), "new_calls": calls}


def parse_journal(journal, case, x, require_complete=True):
    completed = {}
    with Path(journal).open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)  # Never silently discard a truncated or invalid line.
            i = r["row_id"]
            if type(i) is not int or not 0 <= i < len(x) or i in completed:
                raise ValueError("Duplicate or invalid row_id")
            if not np.array_equal([r["params"][name] for name in NAMES], x[i]):
                raise ValueError("Response parameter vector does not match the frozen design")
            completed[i] = check_response(r["outputs"], case)
    if require_complete and len(completed) != len(x):
        raise ValueError(f"Incomplete Saltelli design: {len(completed)}/{len(x)}; no rows may be dropped")
    return completed


def sensitivity(p, y, seed=9001):
    y = np.asarray(y, dtype=float)
    if not np.isfinite(y).all():
        raise ValueError("Cannot analyze nonfinite responses")
    # A and B only, not the correlated AB hybrids, estimate output variance.
    stride = p["num_vars"] + 2
    base = np.r_[y[0::stride], y[stride - 1::stride]]
    variance = float(np.var(base, ddof=1))
    scale = max(float(np.mean(base ** 2)), np.finfo(float).tiny)
    if variance <= 1e-14 * scale:
        return {"status": "CONSTANT_OR_NUMERICALLY_DEGENERATE", "variance_AB": variance,
                "indices": None}
    si = analyze_sobol.analyze(p, y, calc_second_order=False, num_resamples=512,
                               conf_level=.95, seed=seed, print_to_console=False)
    rows = [{"parameter": name, "S1": float(si["S1"][j]), "ST": float(si["ST"][j]),
             "S1_95ci_halfwidth": float(si["S1_conf"][j]),
             "ST_95ci_halfwidth": float(si["ST_conf"][j]),
             "variance_times_ST": variance * float(si["ST"][j])}
            for j, name in enumerate(p["names"])]
    if not all(math.isfinite(v) for r in rows for k, v in r.items() if k != "parameter"):
        raise ValueError("Nonfinite sensitivity estimate; investigate sample size and output variance")
    return {"status": "ESTIMATED", "variance_AB": variance, "indices": rows}


def analyze(config, designs, year, seed, journal, output):
    case, design, x = load_design(config, designs, year, seed)
    meta = read(Path(journal).with_suffix(".metadata.json"))
    fingerprint = meta["fingerprint"]
    if (meta["status"] != "COMPLETE" or fingerprint["config_sha256"] != sha(config)
            or fingerprint["design_sha256"] != design["sha256"]
            or fingerprint["year"] != year or fingerprint["seed"] != seed):
        raise ValueError("Complete response provenance does not match this design")
    rows = parse_journal(journal, case, x)
    p = problem(case)
    result = {"status": "SOBOL_ESTIMATED_NO_FORCED_RANKING", "year": year, "seed": seed,
              "N": design["N"], "response_sha256": sha(journal), "fingerprint": fingerprint,
              "space": "common_global_independent_uniform_physical_ranges_not_MCMC_posterior",
              "confidence_interval_note": "bootstrap halfwidths conditional on one design; compare scrambles and N",
              "outputs": {name: sensitivity(p, [rows[i][name] for i in range(len(x))], seed + 8000)
                          for name in OUTPUTS}}
    write(output, result)
    return {"status": result["status"], "year": year, "N": design["N"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ["prepare", "benchmark", "run", "analyze"]:
        p = sub.add_parser(command)
        p.add_argument("--config", type=Path, default=Path(__file__).with_name("study_config.json"))
        if command == "prepare":
            p.add_argument("--out", type=Path, required=True)
            p.add_argument("--n", type=int, default=128)
        else:
            p.add_argument("--year", type=int, required=True)
            if command in ["benchmark", "run"]:
                p.add_argument("--adapter", type=Path, required=True)
            if command in ["benchmark", "analyze"]:
                p.add_argument("--out", type=Path, required=True)
            if command in ["run", "analyze"]:
                p.add_argument("--designs", type=Path, required=True)
                p.add_argument("--seed", type=int, default=101)
                p.add_argument("--journal", type=Path, required=True)
            if command == "run":
                p.add_argument("--baseline-receipt", type=Path, required=True)
                p.add_argument("--limit", type=int)
    a = parser.parse_args()
    if a.command == "prepare":
        result = prepare(a.config, a.out, a.n)
        result = {k: v for k, v in result.items() if k != "runs"}
    elif a.command == "benchmark":
        result = benchmark(a.config, a.adapter, a.year, a.out)
    elif a.command == "run":
        result = run_design(a.config, a.designs, a.adapter, a.baseline_receipt,
                            a.year, a.seed, a.journal, a.limit)
    else:
        result = analyze(a.config, a.designs, a.year, a.seed, a.journal, a.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
