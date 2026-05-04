"""
Proper asteroseismic analysis of HD 16467 — K0III red giant.
Stellar context: Teff=4966 K, log g=2.551, R=10.5 R_sun, Tmag=5.37
TIC 422971931, SPOC sectors 31, 70, 71.
Predicted nu_max ~ 43 µHz, delta_nu ~ 4.8 µHz from scaling relations.

Run from the hd16467/ directory:
    python hd16467_seismic.py
"""

import matplotlib
matplotlib.use("Agg")

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, correlate
from scipy.ndimage import uniform_filter1d
from pathlib import Path
import textwrap

from seismic_utils import (
    load_sectors_ppm, make_freq_grid, calibrate_psd, fit_harvey_model,
    harvey, gauss_env, full_model, PRED_NMAX, PRED_DELTANU,
)

PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# PART 1 — Lightcurve preparation
# ═══════════════════════════════════════════════════════════════════════
print("Loading HD 16467 SPOC sectors 31, 70, 71...")
t_days, flux_ppm, sector_info = load_sectors_ppm()

N          = len(t_days)
baseline_d = t_days[-1] - t_days[0]
print(f"\n  N={N}, baseline={baseline_d:.1f} d, rms={flux_ppm.std():.1f} ppm")

fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(t_days, flux_ppm, lw=0.3, alpha=0.6, color="steelblue")
ax.set_xlabel("Time (BTJD days)")
ax.set_ylabel("Flux (ppm)")
ax.set_title("HD 16467 – TESS SPOC lightcurve (no flattening)")
fig.tight_layout()
fig.savefig(PLOTS_DIR / "seismic_lc.png", dpi=150)
plt.close(fig)
print("Saved plots/seismic_lc.png")

# ═══════════════════════════════════════════════════════════════════════
# PART 2 — Empirically calibrated PSD
# ═══════════════════════════════════════════════════════════════════════
freq_uhz, freq_cd, df_uhz = make_freq_grid()

print("\nCalibrating PSD normalization via injected sine...")
psd, PSD_SCALE, C_noise = calibrate_psd(
    t_days, flux_ppm, freq_uhz, freq_cd, df_uhz, verbose=True
)
print("  (Dominated by astrophysical background, not pure instrument noise)")

# Full PSD (log-log)
fig, ax = plt.subplots(figsize=(12, 5))
ax.loglog(freq_uhz, psd, color="grey", lw=0.4, alpha=0.7, label="PSD")
for fl, fh, label, col in [(5, 50, "γ Dor", "#2ca02c"), (50, 300, "δ Sct", "#ff7f0e")]:
    ax.axvspan(fl, fh, alpha=0.07, color=col)
    ax.text((fl * fh)**0.5, 0.98, label, ha="center", va="top", fontsize=8,
            color=col, transform=ax.get_xaxis_transform())
ax.axhline(C_noise, color="tomato", lw=1, linestyle="--",
           label=f"200-300 µHz floor = {C_noise:.1f} ppm²/µHz")
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD (ppm² / µHz)")
ax.set_title("HD 16467 – Power Spectral Density (full range, log-log)")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "seismic_psd_full.png", dpi=150)
plt.close(fig)
print("Saved plots/seismic_psd_full.png")

# Zoom: 10–150 µHz
m_zoom = (freq_uhz >= 10) & (freq_uhz <= 150)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(freq_uhz[m_zoom], psd[m_zoom], color="steelblue", lw=0.6, alpha=0.8)
ax.axvline(PRED_NMAX, color="green", lw=1, linestyle=":",
           label=f"Predicted ν_max = {PRED_NMAX} µHz")
ax.axhline(C_noise, color="tomato", lw=0.8, linestyle="--",
           label=f"Noise floor = {C_noise:.1f} ppm²/µHz")
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD (ppm² / µHz)")
ax.set_title("HD 16467 – PSD zoom 10–150 µHz")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "seismic_psd_numax.png", dpi=150)
plt.close(fig)
print("Saved plots/seismic_psd_numax.png")

# ═══════════════════════════════════════════════════════════════════════
# PART 3 — Harvey background model fit
# ═══════════════════════════════════════════════════════════════════════
print("\nFitting Harvey background model...")
res = fit_harvey_model(freq_uhz, psd, C_noise=C_noise, verbose=True)

s1f, t1f = res["s1"], res["t1"]
s2f, t2f = res["s2"], res["t2"]
Hf,  nmf = res["H"],  res["nm"]
sef, Cf  = res["se"], res["C"]
popt      = res["popt"]
perr      = res["perr"]

# Harvey fit plot
nu_pl = np.geomspace(0.5, 300.0, 3000)
psd_smooth = uniform_filter1d(psd, size=50)
fig, ax = plt.subplots(figsize=(12, 5))
ax.loglog(freq_uhz, psd, color="lightgrey", lw=0.4, alpha=0.7, label="Raw PSD")
ax.loglog(freq_uhz, psd_smooth, color="darkgrey", lw=0.8, label="Smoothed PSD")
ax.loglog(nu_pl, harvey(nu_pl, s1f, t1f), "--", color="#1f77b4", lw=1.5,
          label=f"Gran 1 (τ={t1f/3600:.0f} h)")
ax.loglog(nu_pl, harvey(nu_pl, s2f, t2f), "--", color="#ff7f0e", lw=1.5,
          label=f"Gran 2 (τ={t2f/3600:.1f} h)")
ax.loglog(nu_pl, gauss_env(nu_pl, Hf, nmf, sef), "--", color="#2ca02c", lw=1.5,
          label=f"Osc. env. (ν_max={nmf:.1f} µHz)")
ax.loglog(nu_pl, np.full_like(nu_pl, Cf), "--", color="red", lw=1.0,
          label=f"White noise C={Cf:.1f}")
ax.loglog(nu_pl, full_model(nu_pl, *popt), "-", color="black", lw=1.5,
          label="Total model")
ax.axvline(nmf, color="#2ca02c", lw=1.0, linestyle=":", alpha=0.7)
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD (ppm² / µHz)")
ax.set_title("HD 16467 – Harvey background + oscillation envelope fit")
ax.legend(fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(PLOTS_DIR / "seismic_harvey_fit.png", dpi=150)
plt.close(fig)
print("Saved plots/seismic_harvey_fit.png")

# ═══════════════════════════════════════════════════════════════════════
# PART 4 — Significance
# ═══════════════════════════════════════════════════════════════════════
significance = res["significance"]
det_label    = res["det_label"]
fit_success  = res["fit_success"]
nmax_ratio   = nmf / PRED_NMAX
nmax_flag    = abs(nmax_ratio - 1.0) > 0.30

print(f"\n  Significance: H={Hf:.2f} / background={res['gran_bkg']:.2f} = {significance:.2f}")
print(f"  Detection: {det_label}")
if nmax_flag and significance >= 2:
    print(f"  ⚠  ν_max={nmf:.1f} µHz vs predicted {PRED_NMAX:.1f} µHz "
          f"({abs(nmax_ratio-1)*100:.0f}% off)")
if not fit_success:
    print("  ⚠  Fit did not converge — values based on initial guesses.")

# ═══════════════════════════════════════════════════════════════════════
# PART 5 — Δν search
# ═══════════════════════════════════════════════════════════════════════
dnu_found = None

if significance >= 2 and fit_success:
    print("\n  Running Δν search on background-subtracted envelope...")
    win_lo = max(nmf - 2.5 * sef, 0.5)
    win_hi = min(nmf + 2.5 * sef, 300.0)
    m_win  = (freq_uhz >= win_lo) & (freq_uhz <= win_hi)

    if m_win.sum() >= 20:
        background = (harvey(freq_uhz[m_win], s1f, t1f)
                      + harvey(freq_uhz[m_win], s2f, t2f) + Cf)
        psd_bg_sub = np.clip(psd[m_win] - background, 0, None)

        acf_raw = correlate(psd_bg_sub, psd_bg_sub, mode="full")
        acf     = acf_raw[len(psd_bg_sub):]
        acf    /= acf[0] if acf[0] != 0 else 1.0
        lag_uhz = np.arange(len(acf)) * df_uhz

        m_lag = (lag_uhz >= 1.0) & (lag_uhz <= 20.0)
        if m_lag.sum() > 3:
            peaks, _ = find_peaks(acf[m_lag], prominence=0.05)
            if len(peaks):
                dnu_found = float(lag_uhz[m_lag][peaks[0]])
                print(f"  Δν (ACF peak): {dnu_found:.2f} µHz  "
                      f"(predicted {PRED_DELTANU:.1f} µHz)")
            else:
                print("  No significant ACF peak — Δν not constrained.")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))
        ax1.plot(freq_uhz[m_win], psd[m_win], color="grey", lw=0.7, label="PSD")
        ax1.plot(freq_uhz[m_win], background, "--", color="red", lw=1.0,
                 label="Background")
        ax1.plot(freq_uhz[m_win], psd_bg_sub, color="steelblue", lw=0.8,
                 label="BG-subtracted")
        ax1.set_xlabel("Frequency (µHz)")
        ax1.set_ylabel("PSD (ppm²/µHz)")
        ax1.set_title(f"Windowed PSD ({win_lo:.0f}–{win_hi:.0f} µHz)")
        ax1.legend(fontsize=9)

        lags_show = lag_uhz <= 20
        ax2.plot(lag_uhz[lags_show], acf[lags_show], color="steelblue", lw=0.8)
        ax2.axhline(0, color="grey", lw=0.5, linestyle="--")
        ax2.axvline(PRED_DELTANU, color="green", lw=1.0, linestyle=":",
                    label=f"Predicted Δν={PRED_DELTANU} µHz")
        if dnu_found:
            ax2.axvline(dnu_found, color="tomato", lw=1.5, linestyle="--",
                        label=f"ACF peak Δν={dnu_found:.2f} µHz")
        ax2.set_xlabel("Lag (µHz)")
        ax2.set_ylabel("ACF (norm.)")
        ax2.set_title("ACF of background-subtracted PSD")
        ax2.legend(fontsize=9)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / "seismic_deltanu.png", dpi=150)
        plt.close(fig)
        print("  Saved plots/seismic_deltanu.png")
else:
    reason = ("fit did not converge" if not fit_success
              else f"significance {significance:.2f} < 2")
    print(f"\n  Skipping Δν search ({reason}).")

# ═══════════════════════════════════════════════════════════════════════
# PART 6 — Final summary
# ═══════════════════════════════════════════════════════════════════════
SEP = "═" * 65
print(f"\n{SEP}")
print(f"  HD 16467 Asteroseismic Analysis — Final Results")
print(SEP)

print(f"\n  ── Detection ────────────────────────────────────────────")
print(f"  Status          : {det_label}  (H/bkg = {significance:.2f})")

print(f"\n  ── ν_max ────────────────────────────────────────────────")
if fit_success:
    print(f"  Measured        : {nmf:.2f} ± {perr[5]:.2f} µHz")
else:
    print(f"  Measured        : {nmf:.2f} µHz (initial guess, not fitted)")
print(f"  Predicted       : {PRED_NMAX:.1f} µHz")
print(f"  Ratio           : {nmax_ratio:.3f}" + ("  ⚠ >30% off" if nmax_flag else "  ✓"))

print(f"\n  ── Δν ───────────────────────────────────────────────────")
if dnu_found:
    print(f"  Measured        : {dnu_found:.2f} µHz")
    print(f"  Predicted       : {PRED_DELTANU} µHz  |  ratio {dnu_found/PRED_DELTANU:.3f}")
else:
    status_str = ("fit did not converge" if not fit_success
                  else ("significance < 2" if significance < 2 else "no clear ACF peak"))
    print(f"  Measured        : not constrained ({status_str})")
    print(f"  Predicted       : {PRED_DELTANU} µHz")

print(f"\n  ── Granulation ──────────────────────────────────────────")
print(f"  Component 1 : σ={s1f:.0f} ppm,  τ={t1f:.0f} s ({t1f/3600:.1f} h)")
print(f"  Component 2 : σ={s2f:.0f} ppm,  τ={t2f:.0f} s ({t2f/3600:.1f} h)")
print(f"  White noise : C={Cf:.2f} ppm²/µHz")

print(f"\n  ── Interpretation ───────────────────────────────────────")
if det_label == "MARGINAL":
    interp = (
        f"A marginal oscillation envelope is detected (H/bkg={significance:.2f}) "
        f"centred at ν_max={nmf:.1f} µHz "
        f"({'consistent with' if not nmax_flag else 'deviating from'} "
        f"the predicted {PRED_NMAX:.1f} µHz). The granulation components "
        f"(τ₁={t1f/3600:.1f} h, τ₂={t2f/3600:.1f} h) are physically reasonable "
        f"for a K giant. Additional TESS sectors would confirm or refute."
    )
elif det_label == "CONVINCING":
    interp = (
        f"A convincing oscillation envelope is detected (H/bkg={significance:.2f}) "
        f"at ν_max={nmf:.1f} µHz (predicted {PRED_NMAX:.1f} µHz). "
        f"Granulation (τ₁={t1f/3600:.1f} h, τ₂={t2f/3600:.1f} h) consistent "
        f"with K giant convection. "
        + (f"Δν={dnu_found:.2f} µHz (predicted {PRED_DELTANU} µHz) from ACF." if dnu_found else "")
    )
else:
    interp = (
        f"No oscillation envelope above the granulation background "
        f"(H/bkg={significance:.2f}). Limited by window-function artefacts "
        f"from the 3-year gap between sector 31 and sectors 70-71."
    )

for line in textwrap.wrap(interp, width=63):
    print(f"  {line}")
print(f"\n{SEP}\n")
