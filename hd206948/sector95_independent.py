"""
Sector 95 independent asteroseismic analysis of HD 206948.

Loads ONLY QLP 200s sector 95 (the sector NOT used in the primary seismic
run), fits the Harvey + Gaussian model independently, and reports νmax.
This is a temporal stability check: sector 95 is ~700 days after sector 68.
A consistent νmax confirms the oscillation is stable and not a sector-68
artefact.

Run from the hd206948/ directory:
    python sector95_independent.py
"""

import matplotlib
matplotlib.use("Agg")

import warnings
warnings.filterwarnings("ignore")

import json
import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk
from scipy.ndimage import uniform_filter1d
from astropy.stats import sigma_clip
from pathlib import Path

from seismic_utils import (
    make_freq_grid, calibrate_psd, fit_harvey_model,
    harvey, gauss_env, full_model, PRED_NMAX,
)

SCRIPT_DIR = Path(__file__).parent
PLOTS_DIR  = SCRIPT_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

# Results from sector 68 for comparison
S68_NUMAX     = 36.63
S68_NUMAX_ERR = 0.07
S68_DNE       = 3.64
PRED_DNE      = 3.75

print("=" * 65)
print("  HD 206948 — Sector 95 Independent Analysis")
print("=" * 65)

# ── Load QLP 200s sector 95 ───────────────────────────────────────────────────
print("\nDownloading QLP 200s sector 95...")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    search = lk.search_lightcurve("HD 206948", mission="TESS",
                                   author="QLP", exptime=200, sector=95)

if len(search) == 0:
    print("ERROR: QLP 200s sector 95 not found for HD 206948.")
    print("Run check_sectors.py to verify available products.")
    raise SystemExit(1)

print(f"  Found: {len(search)} product(s)")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    lc = search.download()

lc  = lc.remove_nans()
med = float(np.nanmedian(lc.flux.value))
ppm = np.array(1e6 * (lc.flux.value / med - 1.0), dtype=np.float64)
clip = sigma_clip(ppm, sigma=5, maxiters=3, masked=True)
good = ~np.array(clip.mask, dtype=bool)
t_days   = lc.time.value[good]
flux_ppm = ppm[good]
idx      = np.argsort(t_days)
t_days, flux_ppm = t_days[idx], flux_ppm[idx]

N          = len(t_days)
baseline_d = t_days[-1] - t_days[0]
rms        = flux_ppm.std()
print(f"  Sector 95: {N:,} cadences, baseline={baseline_d:.1f} d, rms={rms:.1f} ppm")
print(f"  Time span: BTJD {t_days[0]:.1f} – {t_days[-1]:.1f}")

# Time gap between sectors
t_gap = t_days[0] - 60182.0   # approximate end of sector 68
print(f"  Gap from sector 68: ~{t_gap:.0f} days")

# ── PSD ───────────────────────────────────────────────────────────────────────
freq_uhz, freq_cd, df_uhz = make_freq_grid(F_MIN=0.5, F_MAX=300.0, df=0.01)

print("\nCalibrating PSD...")
psd, PSD_SCALE, C_noise = calibrate_psd(
    t_days, flux_ppm, freq_uhz, freq_cd, df_uhz,
    nu_cal=PRED_NMAX, A_cal=10.0, verbose=True
)

# ── Harvey fit ────────────────────────────────────────────────────────────────
# Same initial guesses as sector 68
psd_smooth_check = uniform_filter1d(psd, size=50)
psd_at_pred = float(psd_smooth_check[np.argmin(np.abs(freq_uhz - PRED_NMAX))])
H_init = max(psd_at_pred - C_noise * 3, C_noise * 0.5)

p0 = [80.0, 14000.0, 50.0, 5000.0, H_init, PRED_NMAX, 6.0, C_noise]

print("\nFitting Harvey model...")
res = fit_harvey_model(
    freq_uhz, psd, C_noise=C_noise, nu_pred=PRED_NMAX,
    fit_range=(1.0, 200.0), smooth_bins=50, verbose=True,
    p0_override=p0, numax_bounds=(15, 60)
)

s1f, t1f = res["s1"], res["t1"]
s2f, t2f = res["s2"], res["t2"]
Hf,  nmf = res["H"],  res["nm"]
sef, Cf  = res["se"], res["C"]
popt     = res["popt"]
perr     = res["perr"]
significance = res["significance"]
det_label    = res["det_label"]
fit_success  = res["fit_success"]

# ── Plots ─────────────────────────────────────────────────────────────────────
psd_smooth_plt = uniform_filter1d(psd, size=50)
nu_pl = np.geomspace(0.5, 300.0, 3000)

# Full PSD + fit
fig, ax = plt.subplots(figsize=(12, 5))
ax.loglog(freq_uhz, psd,            color="lightgrey", lw=0.4, alpha=0.7, label="Raw PSD")
ax.loglog(freq_uhz, psd_smooth_plt, color="darkgrey",  lw=0.8, label="Smoothed")
ax.loglog(nu_pl, harvey(nu_pl, s1f, t1f), "--", color="#1f77b4", lw=1.5,
          label=f"Gran 1 (τ={t1f/3600:.1f} h)")
ax.loglog(nu_pl, harvey(nu_pl, s2f, t2f), "--", color="#ff7f0e", lw=1.5,
          label=f"Gran 2 (τ={t2f/3600:.1f} h)")
ax.loglog(nu_pl, gauss_env(nu_pl, Hf, nmf, sef), "--", color="#2ca02c", lw=1.5,
          label=f"Osc. env. (ν_max={nmf:.1f} µHz)")
ax.loglog(nu_pl, full_model(nu_pl, *popt), "-", color="black", lw=1.5,
          label="Total model")
ax.axvline(nmf,       color="#2ca02c", lw=1.0, linestyle=":", alpha=0.7)
ax.axvline(S68_NUMAX, color="tomato",  lw=1.0, linestyle="--", alpha=0.7,
           label=f"Sector 68 ν_max={S68_NUMAX:.1f} µHz")
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD (ppm² / µHz)")
ax.set_title(f"HD 206948 — Sector 95 (QLP 200s) Harvey fit")
ax.legend(fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(PLOTS_DIR / "sector95_harvey_fit.png", dpi=150)
plt.close(fig)

# Zoom 5-100 µHz comparison
m_zoom = (freq_uhz >= 5) & (freq_uhz <= 100)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(freq_uhz[m_zoom], psd[m_zoom], color="steelblue", lw=0.6, alpha=0.8,
        label="Sector 95 PSD")
ax.axvline(nmf,       color="#2ca02c", lw=1.5, linestyle="-",
           label=f"Sector 95 ν_max = {nmf:.1f} µHz")
ax.axvline(S68_NUMAX, color="tomato",  lw=1.5, linestyle="--",
           label=f"Sector 68 ν_max = {S68_NUMAX:.1f} µHz")
ax.axvline(PRED_NMAX, color="green",   lw=1.0, linestyle=":",
           label=f"Predicted ν_max = {PRED_NMAX:.1f} µHz")
ax.axhline(C_noise,   color="grey",    lw=0.8, linestyle=":",
           label=f"Noise floor = {C_noise:.1f}")
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD (ppm² / µHz)")
ax.set_title("HD 206948 — Sector 95 PSD zoom 5–100 µHz")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "sector95_psd.png", dpi=150)
plt.close(fig)

print("Saved plots/sector95_harvey_fit.png and plots/sector95_psd.png")

# ── Consistency check ─────────────────────────────────────────────────────────
nmax_ratio = nmf / S68_NUMAX
nmax_diff  = nmf - S68_NUMAX
if perr[5] > 0 and S68_NUMAX_ERR > 0:
    sigma_diff = abs(nmax_diff) / np.sqrt(perr[5]**2 + S68_NUMAX_ERR**2)
else:
    sigma_diff = None

# ── Results ───────────────────────────────────────────────────────────────────
SEP = "═" * 65
print(f"\n{SEP}")
print("  HD 206948 — Sector 95 vs Sector 68 Consistency")
print(SEP)

print(f"\n  ── Sector 95 fit ────────────────────────────────────────")
print(f"  Sector          : 95 (QLP 200s)")
print(f"  N cadences      : {N:,}")
print(f"  Baseline        : {baseline_d:.1f} days")
print(f"  rms             : {rms:.1f} ppm")
print(f"  Detection       : {det_label}  (H/bkg = {significance:.2f})")
if fit_success:
    print(f"  ν_max           : {nmf:.2f} ± {perr[5]:.2f} µHz")
else:
    print(f"  ν_max           : {nmf:.2f} µHz  (fit did not converge)")
print(f"  Gran. τ₁        : {t1f/3600:.1f} h")
print(f"  Gran. τ₂        : {t2f/3600:.1f} h")

print(f"\n  ── Comparison ───────────────────────────────────────────")
print(f"  Sector 68 ν_max : {S68_NUMAX:.2f} ± {S68_NUMAX_ERR:.2f} µHz")
print(f"  Sector 95 ν_max : {nmf:.2f} ± {(perr[5] if fit_success else 0):.2f} µHz")
print(f"  Difference      : {nmax_diff:+.2f} µHz  (ratio {nmax_ratio:.3f})")
if sigma_diff is not None:
    print(f"  Significance    : {sigma_diff:.1f}σ")
    if sigma_diff < 2:
        consistency = "CONSISTENT"
        note = "Temporal stability confirmed — star not varying over 700-day baseline."
    elif sigma_diff < 3:
        consistency = "MARGINAL"
        note = "Marginal inconsistency — likely scatter from short baselines."
    else:
        consistency = "INCONSISTENT"
        note = "Significant discrepancy — investigate."
    print(f"  Assessment      : {consistency}")
    print(f"  → {note}")

print(f"\n  ── Note on uncertainties ────────────────────────────────")
print(f"  Sector 68 alone: 24.4-day baseline, σ(νmax)=0.07 µHz (formal)")
print(f"  Sector 95 alone: {baseline_d:.1f}-day baseline, "
      f"σ(νmax)={perr[5]:.2f} µHz (formal)")
print(f"  Single-sector formal uncertainties are optimistic;")
print(f"  true νmax uncertainty ≈ 0.5 µHz from PSD variance.")

print(f"\n{SEP}\n")

# ── Save JSON ─────────────────────────────────────────────────────────────────
results = {
    "sector":          95,
    "pipeline":        "QLP",
    "n_cadences":      N,
    "baseline_days":   float(baseline_d),
    "rms_ppm":         float(rms),
    "detection":       det_label,
    "significance":    float(significance),
    "fit_success":     fit_success,
    "numax":           float(nmf),
    "numax_err":       float(perr[5]) if fit_success else None,
    "gran_tau1_h":     float(t1f / 3600),
    "gran_tau2_h":     float(t2f / 3600),
    "sector68_numax":  S68_NUMAX,
    "numax_diff":      float(nmax_diff),
    "sigma_diff":      float(sigma_diff) if sigma_diff is not None else None,
}
out_path = SCRIPT_DIR / "sector95_results.json"
with open(out_path, "w") as fh:
    json.dump(results, fh, indent=2)
print(f"Results saved to {out_path}")
