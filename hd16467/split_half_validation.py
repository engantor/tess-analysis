"""
Split-half validation of the HD 16467 asteroseismic detection.

Fits the Harvey + Gaussian envelope model independently on:
  - Subset A: Sector 31 alone  (2020)
  - Subset B: Sectors 70 + 71  (2023)

If numax_A and numax_B agree within their formal uncertainties, that supports
the detection.  If they disagree by >2 sigma, that's a warning sign.

Saves results to split_half_results.json for use by detection_summary.py.

Run from the hd16467/ directory:
    python split_half_validation.py
"""

import matplotlib
matplotlib.use("Agg")

import warnings
warnings.filterwarnings("ignore")

import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d
from pathlib import Path

from seismic_utils import (
    load_sectors_ppm, make_freq_grid, calibrate_psd, fit_harvey_model,
    harvey, gauss_env, full_model, PRED_NMAX, PRED_DELTANU,
)

PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

SUBSETS = {
    "A (Sector 31)":    [31],
    "B (Sectors 70+71)": [70, 71],
}
COLORS = {
    "A (Sector 31)":    "#1f77b4",
    "B (Sectors 70+71)": "#ff7f0e",
}

freq_uhz, freq_cd, df_uhz = make_freq_grid()
results = {}

for label, sectors in SUBSETS.items():
    print(f"\n{'═'*60}")
    print(f"  Subset {label}  (sectors {sectors})")
    print("═"*60)

    try:
        t, f, info = load_sectors_ppm(sector_filter=sectors, verbose=True)
    except ValueError as e:
        print(f"  Could not load: {e}")
        results[label] = {"error": str(e)}
        continue

    N_s = len(t)
    baseline = t[-1] - t[0]
    print(f"  N={N_s}, baseline={baseline:.1f} d, rms={f.std():.1f} ppm")

    print(f"\n  Calibrating PSD...")
    psd, scale, C_noise = calibrate_psd(t, f, freq_uhz, freq_cd, df_uhz, verbose=True)

    print(f"\n  Fitting Harvey model...")
    res = fit_harvey_model(freq_uhz, psd, C_noise=C_noise, verbose=True)

    print(f"\n  Detection: {res['det_label']}  (H/bkg = {res['significance']:.2f})")
    print(f"  ν_max = {res['nm']:.2f} ± {res['nm_err']:.2f} µHz")

    results[label] = {
        "sectors":      sectors,
        "N":            N_s,
        "baseline_d":   float(baseline),
        "fit_success":  res["fit_success"],
        "det_label":    res["det_label"],
        "significance": float(res["significance"]),
        "numax":        float(res["nm"]),
        "numax_err":    float(res["nm_err"]),
        "sigma_env":    float(res["se"]),
        "H":            float(res["H"]),
        "H_err":        float(res["H_err"]),
        "s1":           float(res["s1"]),
        "t1":           float(res["t1"]),
        "s2":           float(res["s2"]),
        "t2":           float(res["t2"]),
        "C":            float(res["C"]),
        "popt":         [float(x) for x in res["popt"]],
        "psd_scale":    float(scale),
        "C_noise":      float(C_noise),
    }
    # Store psd for plotting
    results[label]["_psd"]      = psd
    results[label]["_psd_smooth"] = uniform_filter1d(psd, size=50)

# ── Side-by-side PSD plot ─────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
fig.suptitle("HD 16467 – Split-half PSD comparison (10–150 µHz)", fontsize=11)

for ax, (label, sectors) in zip(axes, SUBSETS.items()):
    r = results.get(label, {})
    if "_psd" not in r:
        ax.text(0.5, 0.5, f"Data unavailable\n{r.get('error','')}",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title(label)
        continue

    psd      = r["_psd"]
    psd_sm   = r["_psd_smooth"]
    color    = COLORS[label]

    m_zoom = (freq_uhz >= 10) & (freq_uhz <= 150)
    ax.plot(freq_uhz[m_zoom], psd[m_zoom], color=color, lw=0.5, alpha=0.4,
            label="PSD")
    ax.plot(freq_uhz[m_zoom], psd_sm[m_zoom], color=color, lw=1.0, alpha=0.9,
            label="Smoothed")

    if r.get("fit_success"):
        popt = r["popt"]
        nu_pl = np.linspace(10, 150, 1000)
        total = full_model(nu_pl, *popt)
        gran  = (harvey(nu_pl, popt[0], popt[1])
                 + harvey(nu_pl, popt[2], popt[3]) + popt[7])
        ax.plot(nu_pl, total, "-", color="black", lw=1.5, label="Total fit")
        ax.plot(nu_pl, gran,  "--", color="grey",  lw=1.0, label="Granulation")
        nm = r["numax"]
        ax.axvline(nm, color="tomato", lw=1.5, linestyle="--",
                   label=f"ν_max={nm:.1f}±{r['numax_err']:.1f} µHz")

    ax.axvline(PRED_NMAX, color="green", lw=1.0, linestyle=":",
               label=f"Predicted {PRED_NMAX} µHz", alpha=0.7)

    title = (f"{label}\n"
             f"N={r['N']}, baseline={r['baseline_d']:.0f} d\n"
             f"Status: {r.get('det_label','?')}  "
             f"H/bkg={r.get('significance',0):.2f}")
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("Frequency (µHz)")
    ax.set_ylabel("PSD (ppm²/µHz)" if ax is axes[0] else "")
    ax.legend(fontsize=7, loc="upper right")

fig.tight_layout()
fig.savefig(PLOTS_DIR / "split_half_psd.png", dpi=150)
plt.close(fig)
print(f"\nSaved plots/split_half_psd.png")

# ── Consistency check ─────────────────────────────────────────════════════────
print(f"\n{'═'*60}")
print("  Split-half consistency check")
print("═"*60)

rA = results.get("A (Sector 31)", {})
rB = results.get("B (Sectors 70+71)", {})

if rA.get("fit_success") and rB.get("fit_success"):
    nmA, eA = rA["numax"], max(rA["numax_err"], 0.01)
    nmB, eB = rB["numax"], max(rB["numax_err"], 0.01)
    diff    = abs(nmA - nmB)
    sigma_diff = diff / np.sqrt(eA**2 + eB**2)

    print(f"  Subset A ν_max = {nmA:.2f} ± {eA:.2f} µHz  "
          f"({rA['det_label']})")
    print(f"  Subset B ν_max = {nmB:.2f} ± {eB:.2f} µHz  "
          f"({rB['det_label']})")
    print(f"  Difference     = {diff:.2f} µHz  ({sigma_diff:.1f}σ)")

    if sigma_diff < 2.0:
        verdict = "CONSISTENT — supports detection"
        consistent = True
    elif sigma_diff < 4.0:
        verdict = "MARGINAL INCONSISTENCY — warrants caution"
        consistent = False
    else:
        verdict = "INCONSISTENT — detection is unreliable"
        consistent = False
    print(f"  Verdict        : {verdict}")

    # Also check detection status for each subset
    both_detected = (rA.get("significance", 0) >= 2
                     and rB.get("significance", 0) >= 2)
    if not both_detected:
        detected_in = []
        if rA.get("significance", 0) >= 2:
            detected_in.append("A")
        if rB.get("significance", 0) >= 2:
            detected_in.append("B")
        if detected_in:
            print(f"\n  ⚠  Envelope detected only in subset(s) {detected_in}.")
            print(f"     This is expected for MARGINAL signals with limited data.")
        else:
            print(f"\n  ⚠  Envelope NOT detected at marginal significance in either subset.")
            print(f"     The full-dataset detection (using all 3 sectors) relies on the")
            print(f"     combined SNR from all data.")

    summary = {
        "numax_A":      nmA, "numax_A_err":  eA,
        "numax_B":      nmB, "numax_B_err":  eB,
        "diff_sigma":   float(sigma_diff),
        "consistent":   consistent,
        "verdict":      verdict,
        "det_A":        rA["det_label"],
        "det_B":        rB["det_label"],
        "sig_A":        float(rA["significance"]),
        "sig_B":        float(rB["significance"]),
    }
else:
    missing = []
    if not rA.get("fit_success"):
        missing.append("A")
    if not rB.get("fit_success"):
        missing.append("B")
    print(f"  Cannot compare: fit failed for subset(s) {missing}")
    summary = {"error": f"fit failed for subset(s) {missing}"}

# ── Save JSON results ─────────────────────────────────────────────────────────
# Strip non-serialisable numpy arrays before saving
save_results = {}
for k, v in results.items():
    save_results[k] = {kk: vv for kk, vv in v.items()
                       if not kk.startswith("_")}

output = {"subsets": save_results, "consistency": summary}
out_path = Path("split_half_results.json")
with open(out_path, "w") as fh:
    json.dump(output, fh, indent=2)
print(f"\nResults saved to {out_path}")
