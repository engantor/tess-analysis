"""
Asteroseismic analysis of HD 206948 — K2III red giant.
Stellar context: Teff=4648 K (TIC), R=12.49 R☉, d=233 pc.
TIC 147384395, TESS-SPOC 200s sector 68.  QLP 200s sectors 68 and 95.
Predicted nu_max ~ 33 µHz, delta_nu ~ 3.75 µHz from scaling relations.

Run from the hd206948/ directory:
    python hd206948_seismic.py
"""

import matplotlib
matplotlib.use("Agg")

import warnings
warnings.filterwarnings("ignore")

import sys
import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk
from scipy.signal import find_peaks, correlate
from scipy.ndimage import uniform_filter1d
from astropy.stats import sigma_clip
from pathlib import Path
import textwrap

from seismic_utils import (
    make_freq_grid, calibrate_psd, fit_harvey_model,
    harvey, gauss_env, full_model, PRED_NMAX, PRED_DELTANU,
)

# Target-specific constants
TARGET      = "HD 206948"
TIC         = "TIC 147384395"
TEFF_K      = 4648.0    # K (TIC)
RAD_RSUN    = 12.49     # R☉ (TIC)
TEFF_SUN    = 5778.0    # K
LOGG_SUN    = 4.438
NUMAX_SUN   = 3090.0    # µHz

PLOTS_DIR = Path(__file__).parent / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# PART 1 — Lightcurve loading
# ═══════════════════════════════════════════════════════════════════════
print(f"Loading TESS lightcurves for {TARGET}...")

def load_ppm(author, exptime_s, label):
    """Download, normalise to ppm, sigma-clip. Returns (t_days, flux_ppm, info)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        search = lk.search_lightcurve(TARGET, mission="TESS",
                                       author=author, exptime=exptime_s)
    if len(search) == 0:
        return None, None, None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        coll = search.download_all()

    sectors_t, sectors_f, info = [], [], []
    for lc in coll:
        lc   = lc.remove_nans()
        med  = float(np.nanmedian(lc.flux.value))
        ppm  = np.array(1e6 * (lc.flux.value / med - 1.0), dtype=np.float64)
        clip = sigma_clip(ppm, sigma=5, maxiters=3, masked=True)
        good = ~np.array(clip.mask, dtype=bool)
        sectors_t.append(lc.time.value[good])
        sectors_f.append(ppm[good])
        rms = float(ppm[good].std())
        info.append({'sector': lc.sector, 'n': int(good.sum()), 'rms': rms})
        print(f"  [{label}] Sector {lc.sector}: {good.sum():,} cadences, "
              f"rms={rms:.1f} ppm")

    if not sectors_t:
        return None, None, None

    t   = np.concatenate(sectors_t)
    f   = np.concatenate(sectors_f)
    idx = np.argsort(t)
    return t[idx], f[idx], info

# Try TESS-SPOC 200s first
t_days, flux_ppm, sector_info = load_ppm("TESS-SPOC", 200, "TESS-SPOC")
pipeline_used = "TESS-SPOC 200s"

if t_days is None or len(t_days) == 0:
    print("  TESS-SPOC 200s not available — falling back to QLP 200s...")
    t_days, flux_ppm, sector_info = load_ppm("QLP", 200, "QLP")
    pipeline_used = "QLP 200s"

if t_days is None or len(t_days) == 0:
    print("ERROR: No 200s lightcurve data found for HD 206948 via TESS-SPOC or QLP.")
    print("Run check_sectors.py to verify available products.")
    sys.exit(1)

N          = len(t_days)
baseline_d = t_days[-1] - t_days[0]
sectors_used = [s['sector'] for s in sector_info]
print(f"\n  Pipeline : {pipeline_used}")
print(f"  Sectors  : {sectors_used}")
print(f"  N        : {N:,} cadences")
print(f"  Baseline : {baseline_d:.1f} days")
print(f"  rms      : {flux_ppm.std():.1f} ppm")

fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(t_days, flux_ppm, lw=0.3, alpha=0.6, color="steelblue")
ax.set_xlabel("Time (BTJD days)")
ax.set_ylabel("Flux (ppm)")
ax.set_title(f"{TARGET} – TESS {pipeline_used} lightcurve "
             f"(sectors {sectors_used}, no flattening)")
fig.tight_layout()
fig.savefig(PLOTS_DIR / "seismic_lc.png", dpi=150)
plt.close(fig)
print("Saved plots/seismic_lc.png")

# ═══════════════════════════════════════════════════════════════════════
# PART 2 — Empirically calibrated PSD
# ═══════════════════════════════════════════════════════════════════════
# Use F_MAX=300 so the 200-300 µHz noise floor measurement is valid.
# Oscillation analysis is restricted to 0.5-200 µHz in plots and fitting.
freq_uhz, freq_cd, df_uhz = make_freq_grid(F_MIN=0.5, F_MAX=300.0, df=0.01)

print("\nCalibrating PSD normalization via injected sine at predicted nu_max...")
psd, PSD_SCALE, C_noise = calibrate_psd(
    t_days, flux_ppm, freq_uhz, freq_cd, df_uhz,
    nu_cal=PRED_NMAX, A_cal=10.0, verbose=True
)

# Full PSD log-log (0.5-300 µHz)
fig, ax = plt.subplots(figsize=(12, 5))
ax.loglog(freq_uhz, psd, color="grey", lw=0.4, alpha=0.7, label="PSD")
ax.axvline(PRED_NMAX, color="green", lw=1.2, linestyle=":",
           label=f"Predicted ν_max = {PRED_NMAX} µHz")
ax.axhline(C_noise, color="tomato", lw=1, linestyle="--",
           label=f"200–300 µHz floor = {C_noise:.1f} ppm²/µHz")
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD (ppm² / µHz)")
ax.set_title(f"{TARGET} – Power Spectral Density (full range, log-log)")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "seismic_psd_full.png", dpi=150)
plt.close(fig)
print("Saved plots/seismic_psd_full.png")

# Zoom 5-100 µHz
m_zoom = (freq_uhz >= 5) & (freq_uhz <= 100)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(freq_uhz[m_zoom], psd[m_zoom], color="steelblue", lw=0.6, alpha=0.8)
ax.axvline(PRED_NMAX, color="green", lw=1.2, linestyle=":",
           label=f"Predicted ν_max = {PRED_NMAX} µHz")
ax.axhline(C_noise, color="tomato", lw=0.8, linestyle="--",
           label=f"Noise floor = {C_noise:.1f} ppm²/µHz")
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD (ppm² / µHz)")
ax.set_title(f"{TARGET} – PSD zoom 5–100 µHz")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "seismic_psd_numax.png", dpi=150)
plt.close(fig)
print("Saved plots/seismic_psd_numax.png")

# ═══════════════════════════════════════════════════════════════════════
# PART 3 — Harvey background model fit
# ═══════════════════════════════════════════════════════════════════════
# Initial guesses appropriate for K2III (R=12.5 R☉, larger than K0III):
#   - Granulation 1: τ~14000 s (~3.9 h), σ~80 ppm
#   - Granulation 2: τ~5000 s  (~1.4 h), σ~50 ppm
#   - Envelope at predicted nu_max, H estimated from PSD value there
#   - Allow nu_max to float freely in 15-60 µHz
psd_smooth_check = uniform_filter1d(psd, size=50)
psd_at_pred = float(psd_smooth_check[np.argmin(np.abs(freq_uhz - PRED_NMAX))])
H_init_guess = max(psd_at_pred - C_noise * 3, C_noise * 0.5)

p0_hd206948 = [
    80.0,         # s1 (σ₁, ppm)
    14000.0,      # t1 (τ₁, s = 3.9 h)
    50.0,         # s2 (σ₂, ppm)
    5000.0,       # t2 (τ₂, s = 1.4 h)
    H_init_guess, # H (ppm²/µHz)
    PRED_NMAX,    # nm (µHz) — will be allowed to float 15-60 µHz
    6.0,          # se (σ_env, µHz)
    C_noise,      # C (white noise, ppm²/µHz)
]

print(f"\n  Initial guesses: σ₁=80 ppm, τ₁=14000 s, σ₂=50 ppm, τ₂=5000 s")
print(f"    H_init={H_init_guess:.2f} ppm²/µHz, ν_max={PRED_NMAX} µHz, "
      f"σ_env=6 µHz, C={C_noise:.2f} ppm²/µHz")
print("\nFitting Harvey background model (fit range 1–200 µHz)...")

res = fit_harvey_model(
    freq_uhz, psd, C_noise=C_noise, nu_pred=PRED_NMAX,
    fit_range=(1.0, 200.0), smooth_bins=50, verbose=True,
    p0_override=p0_hd206948, numax_bounds=(15, 60)
)

s1f, t1f = res["s1"], res["t1"]
s2f, t2f = res["s2"], res["t2"]
Hf,  nmf = res["H"],  res["nm"]
sef, Cf  = res["se"], res["C"]
popt     = res["popt"]
perr     = res["perr"]

# Harvey fit plot
nu_pl    = np.geomspace(0.5, 300.0, 3000)
psd_smooth_plt = uniform_filter1d(psd, size=50)
fig, ax  = plt.subplots(figsize=(12, 5))
ax.loglog(freq_uhz, psd,            color="lightgrey", lw=0.4, alpha=0.7, label="Raw PSD")
ax.loglog(freq_uhz, psd_smooth_plt, color="darkgrey",  lw=0.8, label="Smoothed PSD")
ax.loglog(nu_pl, harvey(nu_pl, s1f, t1f), "--", color="#1f77b4", lw=1.5,
          label=f"Gran 1 (τ={t1f/3600:.1f} h)")
ax.loglog(nu_pl, harvey(nu_pl, s2f, t2f), "--", color="#ff7f0e", lw=1.5,
          label=f"Gran 2 (τ={t2f/3600:.1f} h)")
ax.loglog(nu_pl, gauss_env(nu_pl, Hf, nmf, sef), "--", color="#2ca02c", lw=1.5,
          label=f"Osc. env. (ν_max={nmf:.1f} µHz)")
ax.loglog(nu_pl, np.full_like(nu_pl, Cf), "--", color="red", lw=1.0,
          label=f"White noise C={Cf:.1f}")
ax.loglog(nu_pl, full_model(nu_pl, *popt), "-", color="black", lw=1.5,
          label="Total model")
ax.axvline(nmf,      color="#2ca02c", lw=1.0, linestyle=":", alpha=0.7)
ax.axvline(PRED_NMAX, color="green",  lw=0.8, linestyle="--", alpha=0.5,
           label=f"Predicted {PRED_NMAX} µHz")
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD (ppm² / µHz)")
ax.set_title(f"{TARGET} – Harvey background + oscillation envelope fit")
ax.legend(fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(PLOTS_DIR / "seismic_harvey_fit.png", dpi=150)
plt.close(fig)
print("Saved plots/seismic_harvey_fit.png")

# ═══════════════════════════════════════════════════════════════════════
# PART 4 — Significance check
# ═══════════════════════════════════════════════════════════════════════
significance = res["significance"]
det_label    = res["det_label"]
fit_success  = res["fit_success"]
nmax_ratio   = nmf / PRED_NMAX
nmax_flag    = abs(nmax_ratio - 1.0) > 0.35   # flag if >35% off prediction

print(f"\n  Significance: H={Hf:.2f} / background={res['gran_bkg']:.2f} "
      f"= {significance:.2f}")
print(f"  Detection: {det_label}")
if nmax_flag and significance >= 2:
    print(f"  ⚠  ν_max={nmf:.1f} µHz vs predicted {PRED_NMAX:.1f} µHz "
          f"({abs(nmax_ratio-1)*100:.0f}% off)")
if not fit_success:
    print("  ⚠  Fit did not converge — values based on initial guesses.")

# Early exit on non-detection
if significance < 2:
    SEP = "═" * 65
    print(f"\n{SEP}")
    print(f"  {TARGET} — NON-DETECTION")
    print(SEP)
    print(f"\n  H/background = {significance:.2f} < 2.0 — no oscillation envelope")
    print(f"  above the granulation background.")
    print(f"\n  Possible causes:")
    print(f"    - Only {len(sectors_used)} sector(s) of data — limited sensitivity")
    print(f"    - Large gap between sectors inflates window-function noise")
    print(f"    - Target is fainter/farther than HD 16467 (V=7.5, d=233 pc)")
    print(f"\n  Additional TESS sectors would be needed for a detection.")
    print(f"  Consider checking QLP or TGLC products if TESS-SPOC was used.")
    print(f"\n{SEP}\n")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════════════
# PART 5 — Δν search
# ═══════════════════════════════════════════════════════════════════════
dnu_found = None

if fit_success:
    print("\n  Running Δν search on background-subtracted envelope...")
    win_lo = max(nmf - 2.5 * sef, 0.5)
    win_hi = min(nmf + 2.5 * sef, 200.0)
    m_win  = (freq_uhz >= win_lo) & (freq_uhz <= win_hi)

    if m_win.sum() >= 20:
        background = (harvey(freq_uhz[m_win], s1f, t1f)
                      + harvey(freq_uhz[m_win], s2f, t2f) + Cf)
        psd_bg_sub = np.clip(psd[m_win] - background, 0, None)

        acf_raw = correlate(psd_bg_sub, psd_bg_sub, mode="full")
        acf     = acf_raw[len(psd_bg_sub):]
        acf    /= acf[0] if acf[0] != 0 else 1.0
        lag_uhz = np.arange(len(acf)) * df_uhz

        m_lag = (lag_uhz >= 0.5) & (lag_uhz <= 15.0)
        if m_lag.sum() > 3:
            peaks, props = find_peaks(acf[m_lag], prominence=0.05)
            if len(peaks):
                # Take the peak closest to the predicted Δν
                dists   = np.abs(lag_uhz[m_lag][peaks] - PRED_DELTANU)
                best    = peaks[np.argmin(dists)]
                dnu_found = float(lag_uhz[m_lag][best])
                print(f"  Δν (ACF peak): {dnu_found:.2f} µHz  "
                      f"(predicted {PRED_DELTANU:.2f} µHz, "
                      f"ratio {dnu_found/PRED_DELTANU:.3f})")
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

        lags_show = lag_uhz <= 15
        ax2.plot(lag_uhz[lags_show], acf[lags_show], color="steelblue", lw=0.8)
        ax2.axhline(0, color="grey", lw=0.5, linestyle="--")
        ax2.axvline(PRED_DELTANU, color="green", lw=1.0, linestyle=":",
                    label=f"Predicted Δν={PRED_DELTANU:.2f} µHz")
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
    print("\n  Skipping Δν search (fit did not converge).")

# ═══════════════════════════════════════════════════════════════════════
# PART 6 — Physical quantities from ν_max
# ═══════════════════════════════════════════════════════════════════════
# Implied log g from νmax scaling relation:
#   νmax/νmax_sun = (g/g_sun) * (Teff_sun/Teff)^0.5
#   → log g = LOGG_SUN + log10(νmax/νmax_sun) + 0.5*log10(Teff/Teff_sun)
logg_implied = None
mass_implied = None

if fit_success:
    logg_implied = (LOGG_SUN
                    + np.log10(nmf / NUMAX_SUN)
                    + 0.5 * np.log10(TEFF_K / TEFF_SUN))
    # Uncertainty propagation (σ_logg from σ_νmax only):
    # d(logg)/d(log10(νmax)) = 1; σ_νmax in µHz → σ_log10(νmax) = σ_νmax/(νmax * ln10)
    logg_implied_err = (perr[5] / (nmf * np.log(10))) if perr[5] > 0 else 0.0

    # Implied mass from νmax and TIC radius:
    #   g = g_sun * 10^(logg - logg_sun)
    #   M = g * R^2 / g_sun = 10^(logg_implied - LOGG_SUN) * R_sun^2 [in M_sun units]
    g_over_gsun = 10**(logg_implied - LOGG_SUN)
    mass_implied = g_over_gsun * RAD_RSUN**2   # M/M_sun = (g/g_sun) * (R/R_sun)^2
    # Note: this assumes g_sun = G*M_sun/R_sun^2 is absorbed into the ratio
    mass_implied_err = (mass_implied * logg_implied_err * np.log(10)
                        + mass_implied * 2 * 0.5 / RAD_RSUN)  # rough propagation

# ═══════════════════════════════════════════════════════════════════════
# PART 7 — Final summary
# ═══════════════════════════════════════════════════════════════════════
SEP = "═" * 65
print(f"\n{SEP}")
print(f"  {TARGET} Asteroseismic Analysis — Final Results")
print(SEP)

print(f"\n  ── Data ─────────────────────────────────────────────────")
print(f"  Pipeline        : {pipeline_used}")
print(f"  Sectors         : {sectors_used}")
print(f"  N cadences      : {N:,}")
print(f"  Baseline        : {baseline_d:.1f} days")

print(f"\n  ── Detection ────────────────────────────────────────────")
print(f"  Status          : {det_label}  (H/bkg = {significance:.2f})")

print(f"\n  ── ν_max ────────────────────────────────────────────────")
if fit_success:
    print(f"  Measured        : {nmf:.2f} ± {perr[5]:.2f} µHz")
else:
    print(f"  Measured        : {nmf:.2f} µHz  (initial guess, not fitted)")
print(f"  Predicted       : {PRED_NMAX:.1f} µHz")
print(f"  Ratio           : {nmax_ratio:.3f}" + ("  ⚠ >35% off" if nmax_flag else "  ✓"))

print(f"\n  ── Δν ───────────────────────────────────────────────────")
if dnu_found:
    print(f"  Measured        : {dnu_found:.2f} µHz")
    print(f"  Predicted       : {PRED_DELTANU:.2f} µHz  |  ratio {dnu_found/PRED_DELTANU:.3f}")
else:
    status_str = ("fit did not converge" if not fit_success else "no clear ACF peak")
    print(f"  Measured        : not constrained ({status_str})")
    print(f"  Predicted       : {PRED_DELTANU:.2f} µHz")

print(f"\n  ── Granulation ──────────────────────────────────────────")
print(f"  Component 1     : σ={s1f:.0f} ppm,  τ={t1f:.0f} s ({t1f/3600:.1f} h)")
print(f"  Component 2     : σ={s2f:.0f} ppm,  τ={t2f:.0f} s ({t2f/3600:.1f} h)")
print(f"  White noise     : C={Cf:.2f} ppm²/µHz")

print(f"\n  ── Physical quantities from ν_max ───────────────────────")
if logg_implied is not None:
    print(f"  Implied log g   : {logg_implied:.3f} ± {logg_implied_err:.3f}  "
          f"(from νmax={nmf:.1f} µHz, Teff={TEFF_K:.0f} K)")
    print(f"  Predicted log g : {LOGG_SUN + np.log10(PRED_NMAX/NUMAX_SUN) + 0.5*np.log10(TEFF_K/TEFF_SUN):.3f}  "
          f"(from predicted νmax={PRED_NMAX} µHz)")
if mass_implied is not None:
    print(f"  Implied mass    : {mass_implied:.2f} M☉  "
          f"(from νmax and R={RAD_RSUN} R☉ — uncertain: R has 5-10% error)")
    print(f"  (Caveat: mass is sensitive to radius error; "
          f"this assumes M = g × R² / g_sun in solar units)")

print(f"\n  ── Interpretation ───────────────────────────────────────")
if det_label == "MARGINAL":
    interp = (
        f"A marginal oscillation envelope is detected (H/bkg={significance:.2f}) "
        f"centred at ν_max={nmf:.1f} µHz "
        f"({'consistent with' if not nmax_flag else 'deviating from'} "
        f"the predicted {PRED_NMAX:.1f} µHz). The granulation components "
        f"(τ₁={t1f/3600:.1f} h, τ₂={t2f/3600:.1f} h) are physically reasonable "
        f"for a K2III giant (R≈12.5 R☉). Additional TESS sectors would confirm "
        f"or refute."
    )
elif det_label == "CONVINCING":
    interp = (
        f"A convincing oscillation envelope is detected (H/bkg={significance:.2f}) "
        f"at ν_max={nmf:.1f} µHz (predicted {PRED_NMAX:.1f} µHz). "
        f"Granulation (τ₁={t1f/3600:.1f} h, τ₂={t2f/3600:.1f} h) consistent "
        f"with K2III giant convection. "
        + (f"Δν={dnu_found:.2f} µHz (predicted {PRED_DELTANU:.2f} µHz) from ACF."
           if dnu_found else "Δν not reliably constrained from ACF.")
    )
else:
    interp = (
        f"No oscillation envelope above the granulation background "
        f"(H/bkg={significance:.2f}). Target is at 233 pc (vs HD 16467 at 131 pc) "
        f"and only {len(sectors_used)} sector(s) of 200s data are available. "
        f"Window-function noise from sector gaps limits sensitivity."
    )

for line in textwrap.wrap(interp, width=63):
    print(f"  {line}")
print(f"\n{SEP}\n")
