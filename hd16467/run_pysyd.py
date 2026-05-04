"""
pySYD validation of the HD 16467 asteroseismic detection.

Prepares input files, runs pySYD's global analysis pipeline, then
compares its numax/delta_nu estimates against our Harvey fit results.

Saves results to pysyd_results.json for use by detection_summary.py.

Run from the hd16467/ directory:
    python run_pysyd.py
"""

import warnings
warnings.filterwarnings("ignore")

import sys
import json
import shutil
import subprocess
import numpy as np
from pathlib import Path

# ── Check pySYD is importable ─────────────────────────────────────────────────
try:
    import pysyd
    PYSYD_VERSION = getattr(pysyd, "__version__", "unknown")
    print(f"pySYD version: {PYSYD_VERSION}")
except ImportError:
    print("ERROR: pySYD is not installed.")
    print("Install it with:  pip install pysyd")
    sys.exit(1)

from seismic_utils import load_sectors_ppm

# ── Stellar parameters ────────────────────────────────────────────────────────
STAR_NAME  = "TIC422971931"
NUMAX_EST  = 43.0     # µHz  (from scaling relation)

# pySYD v6 file convention: <inpdir>/<star>_LC.txt (NO header lines)
INP_DIR  = Path("pysyd_input")
OUT_DIR  = Path("pysyd_output")
INP_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

# ── Prepare lightcurve input file ─────────────────────────────────────────────
print("\nLoading HD 16467 SPOC sectors 31, 70, 71...")
t_days, flux_ppm, sector_info = load_sectors_ppm(verbose=True)

# pySYD load_file() does NOT support comment lines — write plain two-column data
lc_file = INP_DIR / f"{STAR_NAME}_LC.txt"
with open(lc_file, "w") as fh:
    for t, f in zip(t_days, flux_ppm):
        fh.write(f"{t:.6f}  {f:.4f}\n")
print(f"Saved {lc_file}  ({len(t_days)} cadences, no header)")

# ── Attempt Python API (pySYD v6) ─────────────────────────────────────────────
print(f"\nRunning pySYD on {STAR_NAME}...")
print(f"  numax estimate: {NUMAX_EST} µHz")

pysyd_success = False
pysyd_output  = {}

try:
    import argparse
    from pysyd import pipeline as pysyd_pipeline

    # pySYD v6 check_cli expects these override attributes as lists or None
    args = argparse.Namespace(
        # Paths
        inpdir      = str(INP_DIR),
        infdir      = str(INP_DIR),       # star_info.csv will be written here if needed
        outdir      = str(OUT_DIR),
        # Stars
        stars       = [STAR_NAME],
        # Override arrays (must be lists of same length as stars, or None)
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
        # Modules to run
        background  = True,
        globe       = True,
        # Output/display
        save        = True,
        verbose     = True,
        overwrite   = True,
        warnings    = False,
        show        = False,
        cli         = True,
        notebook    = False,
        test        = False,
        # Fitting options
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

    # Find the pySYD binary (in the same venv as this Python)
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
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
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
if pysyd_success:
    # pySYD v6 writes to OUT_DIR/<star>/<star>_*
    star_out   = OUT_DIR / STAR_NAME
    search_dirs = [star_out, OUT_DIR]

    print(f"\n  Searching for pySYD output in {star_out}...")
    for sdir in search_dirs:
        if sdir.exists():
            files = list(sdir.rglob("*.csv"))
            if files:
                print(f"  CSV files found:")
                for f in sorted(files):
                    print(f"    {f}")
                break

    import csv as csv_mod

    def read_flat_csv(path):
        """Read pySYD output CSV — handles long-format (parameter,value) and wide-format."""
        result = {}
        with open(path) as fh:
            lines = [l for l in fh.read().splitlines() if l.strip()]
        if not lines:
            return result

        # Detect long-format: header is "parameter,value"
        headers = [h.strip().lower() for h in lines[0].split(",")]
        if len(headers) == 2 and "parameter" in headers and "value" in headers:
            # Long-format: each row is a parameter name and its value
            for line in lines[1:]:
                parts = line.split(",", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    try:
                        result[key] = float(parts[1].strip())
                    except ValueError:
                        result[key] = parts[1].strip()
            return result

        # Wide-format: DictReader (one row per star)
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

    # Try multiple output file patterns
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for pattern in ["*global*", "*result*", "*output*", f"{STAR_NAME}*.csv"]:
            matches = list(search_dir.glob(pattern))
            if not matches:
                matches = list(search_dir.rglob(pattern))
            for csv_file in sorted(matches):
                try:
                    raw = read_flat_csv(csv_file)
                    if not raw:
                        continue
                    print(f"\n  Parsed {csv_file.name}:")
                    for k, v in list(raw.items())[:20]:
                        print(f"    {k}: {v}")

                    # Try multiple possible column name variants
                    numax_keys = ["numax", "numax_smooth", "nuMax", "nu_max",
                                  "numax_global", "nu_max_global"]
                    dnu_keys   = ["dnu", "Dnu", "delta_nu", "deltanu",
                                  "dnu_global", "delta_nu_global"]
                    err_suffixes = ["_err", "_e", "_unc", "e_", "_error"]

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
                except Exception as parse_err:
                    print(f"  Could not parse {csv_file}: {parse_err}")
            if "numax" in pysyd_output:
                break

    # Copy pySYD diagnostic plots to hd16467/plots/
    PLOTS_DIR = Path("plots")
    PLOTS_DIR.mkdir(exist_ok=True)
    copied = 0
    for search_dir in search_dirs:
        if search_dir.exists():
            for img in search_dir.rglob("*.png"):
                dest = PLOTS_DIR / f"pysyd_{img.name}"
                shutil.copy2(img, dest)
                copied += 1
    if copied:
        print(f"\n  Copied {copied} diagnostic plots to plots/pysyd_*.png")

# ── Print comparison table ────────────────────────────────────────────────────
OUR_NUMAX      = 43.43
OUR_NUMAX_ERR  = 0.10
OUR_DNE_NOTE   = "ACF at MARGINAL SNR — unreliable"

SEP = "═" * 65
print(f"\n{SEP}")
print("  HD 16467 — Harvey fit vs pySYD comparison")
print(SEP)
print(f"  {'Quantity':<20}  {'Our Harvey fit':>22}  {'pySYD':>14}")
print(f"  {'-'*20}  {'-'*22}  {'-'*14}")

numax_ours  = f"{OUR_NUMAX:.2f} ± {OUR_NUMAX_ERR:.2f} µHz"
numax_pysyd = (f"{pysyd_output['numax']:.2f} ± "
               f"{pysyd_output.get('numax_err', 0):.2f} µHz"
               if "numax" in pysyd_output else "not available")
print(f"  {'ν_max':<20}  {numax_ours:>22}  {numax_pysyd:>14}")

dnu_ours  = f"1.87 µHz (unreliable)"
dnu_pysyd = (f"{pysyd_output['dnu']:.2f} ± "
             f"{pysyd_output.get('dnu_err', 0):.2f} µHz"
             if "dnu" in pysyd_output else "not available")
print(f"  {'Δν':<20}  {dnu_ours:>22}  {dnu_pysyd:>14}")
print(SEP)

if "numax" in pysyd_output:
    nm_p  = pysyd_output["numax"]
    nm_pe = pysyd_output.get("numax_err", 0.5)
    diff  = abs(OUR_NUMAX - nm_p)
    sigma = diff / np.sqrt(OUR_NUMAX_ERR**2 + nm_pe**2) if nm_pe > 0 else 0
    print(f"\n  ν_max agreement: {diff:.2f} µHz = {sigma:.1f}σ")
    if sigma < 2:
        print("  → Consistent — pySYD confirms our detection.")
    elif sigma < 4:
        print("  → Marginal inconsistency.")
    else:
        print("  → Inconsistent — results in tension.")
    if "dnu" in pysyd_output and pysyd_output["dnu"] > 0:
        dnu_p = pysyd_output["dnu"]
        print(f"\n  Δν from pySYD: {dnu_p:.2f} µHz  (predicted {4.8:.1f} µHz)")
        if abs(dnu_p - 4.8) / 4.8 < 0.3:
            print("  → pySYD Δν is consistent with prediction — improvement over our ACF!")
        else:
            print(f"  → pySYD Δν differs from prediction by "
                  f"{abs(dnu_p-4.8)/4.8*100:.0f}%.")

if not pysyd_success:
    print(f"\n  ⚠  pySYD did not complete successfully.")
    print(f"     See error messages above.")
    print(f"     Common issues:")
    print(f"       Python 3.14 may not be fully supported — pySYD targets 3.9–3.11")
    print(f"       Try: pip install 'pysyd==5.*' for an older API")
    pysyd_output["error"] = "pySYD did not run successfully"

# ── Save results JSON ─────────────────────────────────────────────────────────
output = {
    "pysyd_success": pysyd_success,
    "pysyd_version": PYSYD_VERSION,
    "our_numax":     OUR_NUMAX,
    "our_numax_err": OUR_NUMAX_ERR,
    "our_dnu_note":  OUR_DNE_NOTE,
    **{k: v for k, v in pysyd_output.items()},
}
out_path = Path("pysyd_results.json")
with open(out_path, "w") as fh:
    json.dump(output, fh, indent=2)
print(f"\nResults saved to {out_path}")
