"""
pySYD validation of the HD 206948 asteroseismic detection.

Prepares TESS-SPOC 200s sector 68 as pySYD input, runs pySYD's global
analysis pipeline, then compares its numax/delta_nu estimates against
our Harvey fit results.

Saves results to pysyd_results.json and diagnostic plots to plots/.

Run from the hd206948/ directory:
    python run_pysyd.py

pySYD Python 3.14 compatibility patches (same as hd16467):
  venv/lib/python3.14/site-packages/pysyd/target.py, line ~1752:
    if pl and pa:
        l, a = pl.pop(idx if idx is not None else -1), ...
"""

import warnings
warnings.filterwarnings("ignore")

import sys
import json
import shutil
import subprocess
import numpy as np
from pathlib import Path

# Make paths relative to this script's location
SCRIPT_DIR = Path(__file__).parent
PLOTS_DIR  = SCRIPT_DIR / "plots"
INP_DIR    = SCRIPT_DIR / "pysyd_input"
OUT_DIR    = SCRIPT_DIR / "pysyd_output"
PLOTS_DIR.mkdir(exist_ok=True)
INP_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

# ── Check pySYD ───────────────────────────────────────────────────────────────
try:
    import pysyd
    PYSYD_VERSION = getattr(pysyd, "__version__", "unknown")
    print(f"pySYD version: {PYSYD_VERSION}")
except ImportError:
    print("ERROR: pySYD is not installed.")
    print("Install it with:  pip install pysyd")
    sys.exit(1)

from seismic_utils import load_sectors_ppm

# ── Stellar / target parameters ───────────────────────────────────────────────
STAR_NAME  = "TIC147384395"
TEFF       = 4648.0    # K (TIC)
NUMAX_EST  = 36.6      # µHz — Harvey fit result to guide pySYD's background fit

# Our Harvey fit results for comparison
OUR_NUMAX     = 36.63
OUR_NUMAX_ERR = 0.07
OUR_DNE       = 3.64    # µHz from ACF

# ── Prepare lightcurve input ──────────────────────────────────────────────────
print(f"\nLoading TESS-SPOC 200s sector 68 for {STAR_NAME}...")
t_days, flux_ppm, sector_info = load_sectors_ppm(
    identifier="HD 206948", author="TESS-SPOC", exptime=200, verbose=True
)

# pySYD load_file() does NOT support comment lines — plain two-column data
lc_file = INP_DIR / f"{STAR_NAME}_LC.txt"
with open(lc_file, "w") as fh:
    for t, f in zip(t_days, flux_ppm):
        fh.write(f"{t:.6f}  {f:.4f}\n")
print(f"Saved {lc_file}  ({len(t_days):,} cadences, no header)")

# ── Run pySYD ─────────────────────────────────────────────────────────────────
print(f"\nRunning pySYD on {STAR_NAME}  (numax_estimate={NUMAX_EST} µHz)...")

pysyd_success = False
pysyd_output  = {}

try:
    import argparse
    from pysyd import pipeline as pysyd_pipeline

    args = argparse.Namespace(
        # Paths
        inpdir      = str(INP_DIR),
        infdir      = str(INP_DIR),
        outdir      = str(OUT_DIR),
        # Stars
        stars       = [STAR_NAME],
        # Overrides (lists matching length of stars)
        numax       = [NUMAX_EST],
        dnu         = None,
        lower_ex    = None,
        upper_ex    = None,
        lower_bg    = None,
        upper_bg    = None,
        lower_ps    = None,
        upper_ps    = None,
        lower_ech   = None,
        upper_ech   = None,
        # Processing flags
        oversampling_factor = None,
        n_laws      = None,
        kep_corr    = False,
        notching    = False,
        stitch      = False,
        force       = False,
        gap         = 20,
        # Modules
        background  = True,
        globe       = True,
        # Output
        save        = True,
        verbose     = True,
        overwrite   = True,
        warnings    = False,
        show        = False,
        cli         = True,
        notebook    = False,
        test        = False,
        # Fitting
        n_trials    = 3,
        mc_iter     = 200,
        seed        = None,
        # Background model
        metric      = 'bic',
        # Smoothing
        sm_par      = None,
        sp_smooth   = None,
        # Misc
        mode        = 'run',
        todo        = str(INP_DIR / "todo.txt"),
        info        = str(INP_DIR / "star_info.csv"),
    )

    pysyd_pipeline.run(args)
    pysyd_success = True
    print("  pySYD Python API ran successfully ✓")

except Exception as api_err:
    print(f"  Python API failed: {api_err}")
    print("  Trying pySYD CLI binary...")

    pysyd_bin = Path(sys.executable).parent / "pysyd"
    if not pysyd_bin.exists():
        pysyd_bin = shutil.which("pysyd") or "pysyd"

    cmd = [
        str(pysyd_bin), "run",
        "--inpdir",  str(INP_DIR),
        "--infdir",  str(INP_DIR),
        "--out",     str(OUT_DIR),
        "--star",    STAR_NAME,
        "--numax",   str(NUMAX_EST),
        "--overwrite",
        "--verbose",
    ]
    print(f"  Command: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=300, cwd=str(SCRIPT_DIR))
        stdout_tail = proc.stdout[-4000:] if len(proc.stdout) > 4000 else proc.stdout
        print(stdout_tail)
        if proc.returncode == 0:
            pysyd_success = True
            print("  pySYD CLI ran successfully ✓")
        else:
            print(f"  CLI stderr:\n{proc.stderr[-2000:]}")
            print(f"  Return code: {proc.returncode}")
    except Exception as cli_err:
        print(f"  CLI also failed: {cli_err}")

# ── Parse pySYD output ────────────────────────────────────────────────────────
import csv as csv_mod

def read_flat_csv(path):
    """Read pySYD CSV — handles long-format (parameter,value) and wide-format."""
    result = {}
    with open(path) as fh:
        lines = [l for l in fh.read().splitlines() if l.strip()]
    if not lines:
        return result
    headers = [h.strip().lower() for h in lines[0].split(",")]
    if len(headers) == 2 and "parameter" in headers and "value" in headers:
        for line in lines[1:]:
            parts = line.split(",", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                try:
                    result[key] = float(parts[1].strip())
                except ValueError:
                    result[key] = parts[1].strip()
        return result
    try:
        reader = csv_mod.DictReader(lines)
        for row in reader:
            for k, v in row.items():
                if k:
                    try:
                        result[k.strip()] = float(v.strip())
                    except (ValueError, AttributeError):
                        result[k.strip()] = str(v).strip() if v else ""
    except Exception:
        pass
    return result

if pysyd_success:
    star_out    = OUT_DIR / STAR_NAME
    search_dirs = [star_out, OUT_DIR]

    print(f"\n  Searching for pySYD output in {star_out}...")
    for sdir in search_dirs:
        if sdir.exists():
            csvs = list(sdir.rglob("*.csv"))
            if csvs:
                print(f"  CSV files found:")
                for f in sorted(csvs):
                    print(f"    {f}")
                break

    numax_keys = ["numax", "numax_smooth", "nuMax", "nu_max",
                  "numax_global", "nu_max_global"]
    dnu_keys   = ["dnu", "Dnu", "delta_nu", "deltanu",
                  "dnu_global", "delta_nu_global"]
    err_suffixes = ["_err", "_e", "_unc", "e_", "_error"]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for pattern in ["*global*", "*result*", "*output*", f"{STAR_NAME}*.csv"]:
            for csv_file in sorted(search_dir.rglob(pattern)):
                try:
                    raw = read_flat_csv(csv_file)
                    if not raw:
                        continue
                    print(f"\n  Parsed {csv_file.name}:")
                    for k, v in list(raw.items())[:20]:
                        print(f"    {k}: {v}")

                    for key in numax_keys:
                        if key in raw and isinstance(raw[key], float):
                            pysyd_output["numax"] = raw[key]
                            for suf in err_suffixes:
                                ek = key + suf
                                if ek in raw and isinstance(raw[ek], float):
                                    pysyd_output["numax_err"] = raw[ek]
                                    break
                            break

                    for key in dnu_keys:
                        if key in raw and isinstance(raw[key], float):
                            pysyd_output["dnu"] = raw[key]
                            for suf in err_suffixes:
                                ek = key + suf
                                if ek in raw and isinstance(raw[ek], float):
                                    pysyd_output["dnu_err"] = raw[ek]
                                    break
                            break

                    if "numax" in pysyd_output:
                        break
                except Exception as pe:
                    print(f"  Could not parse {csv_file}: {pe}")
            if "numax" in pysyd_output:
                break

    # Copy diagnostic plots to hd206948/plots/
    copied = 0
    for sdir in search_dirs:
        if sdir.exists():
            for img in sdir.rglob("*.png"):
                dest = PLOTS_DIR / f"pysyd_{img.name}"
                shutil.copy2(img, dest)
                copied += 1
    if copied:
        print(f"\n  Copied {copied} diagnostic plot(s) to plots/pysyd_*.png")

# ── Comparison table ──────────────────────────────────────────────────────────
SEP = "═" * 65
print(f"\n{SEP}")
print("  HD 206948 — Harvey fit vs pySYD comparison")
print(SEP)
print(f"  {'Quantity':<20}  {'Our Harvey fit':>22}  {'pySYD':>14}")
print(f"  {'-'*20}  {'-'*22}  {'-'*14}")

numax_ours  = f"{OUR_NUMAX:.2f} ± {OUR_NUMAX_ERR:.2f} µHz"
numax_pysyd = (f"{pysyd_output['numax']:.2f} ± "
               f"{pysyd_output.get('numax_err', 0):.2f} µHz"
               if "numax" in pysyd_output else "not available")
dnu_ours    = f"{OUR_DNE:.2f} µHz (ACF)"
dnu_pysyd   = (f"{pysyd_output['dnu']:.2f} ± "
               f"{pysyd_output.get('dnu_err', 0):.2f} µHz"
               if "dnu" in pysyd_output else "not available")

print(f"  {'ν_max':<20}  {numax_ours:>22}  {numax_pysyd:>14}")
print(f"  {'Δν':<20}  {dnu_ours:>22}  {dnu_pysyd:>14}")
print(SEP)

if "numax" in pysyd_output:
    nm_p  = pysyd_output["numax"]
    nm_pe = pysyd_output.get("numax_err", 0.5)
    diff  = abs(OUR_NUMAX - nm_p)
    sigma = diff / np.sqrt(OUR_NUMAX_ERR**2 + nm_pe**2) if nm_pe > 0 else 0
    print(f"\n  ν_max agreement: Δ={diff:.2f} µHz = {sigma:.1f}σ")
    if sigma < 2:
        print("  → Consistent — pySYD confirms our Harvey fit detection.")
    elif sigma < 4:
        print("  → Marginal inconsistency — investigate background model choices.")
    else:
        print("  → Inconsistent — results in tension; check pySYD background model.")

    if "dnu" in pysyd_output:
        dnu_p = pysyd_output["dnu"]
        diff_dnu = abs(OUR_DNE - dnu_p)
        print(f"\n  Δν agreement: Harvey/ACF={OUR_DNE:.2f} µHz, pySYD={dnu_p:.2f} µHz "
              f"(Δ={diff_dnu:.2f} µHz)")
        if diff_dnu < 0.3:
            print("  → Consistent — pySYD Δν confirms ACF result.")
        elif diff_dnu < 0.7:
            print("  → Marginal — within ACF uncertainty from single sector.")
        else:
            print("  → Inconsistent — Δν values differ significantly.")

if not pysyd_success:
    print(f"\n  ⚠  pySYD did not complete successfully.")
    print(f"     Python 3.14 patches may be needed — see hd16467/run_pysyd.py")
    pysyd_output["error"] = "pySYD did not run successfully"

# ── Save results JSON ─────────────────────────────────────────────────────────
output = {
    "pysyd_success": pysyd_success,
    "pysyd_version": PYSYD_VERSION,
    "our_numax":     OUR_NUMAX,
    "our_numax_err": OUR_NUMAX_ERR,
    "our_dnu":       OUR_DNE,
    **{k: v for k, v in pysyd_output.items()},
}
out_path = SCRIPT_DIR / "pysyd_results.json"
with open(out_path, "w") as fh:
    json.dump(output, fh, indent=2)
print(f"\nResults saved to {out_path}")
