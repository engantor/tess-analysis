"""
Échelle diagram for HD 206948 solar-like oscillations.

Takes the sector 68 TESS-SPOC 200s PSD, subtracts the Harvey background
from the seismic fit, then folds it modulo Δν to produce the échelle
diagram: frequency mod Δν on x-axis, frequency on y-axis, power as
colour intensity.

If Δν is real, vertical ridges of excess power appear — these are the
resolved p-mode frequencies. If it looks like noise, Δν is not reliably
constrained by the current data.

Run from the hd206948/ directory:
    python echelle.py
"""

import matplotlib
matplotlib.use("Agg")

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk
from scipy.ndimage import uniform_filter1d
from astropy.stats import sigma_clip
from pathlib import Path

from seismic_utils import (
    make_freq_grid, calibrate_psd, harvey,
    PRED_NMAX, PRED_DELTANU,
)

SCRIPT_DIR = Path(__file__).parent
PLOTS_DIR  = SCRIPT_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

# Results from hd206948_seismic.py
NUMAX_FIT = 36.63    # µHz — fitted νmax
DNE_FIT   = 3.64     # µHz — Δν from ACF
DNE_PYSYD = 3.75     # µHz — pySYD value for comparison

# Harvey background parameters from seismic fit
S1, T1 = 1126.8, 5024.0    # σ₁ ppm, τ₁ s
S2, T2 = 1000.0, 12946.0   # σ₂ ppm, τ₂ s
CF     = 75.34              # white noise ppm²/µHz

print("=" * 65)
print("  HD 206948 — Échelle Diagram from Sector 68")
print("=" * 65)

# ── Load sector 68 ────────────────────────────────────────────────────────────
print("\nLoading TESS-SPOC 200s sector 68...")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    search = lk.search_lightcurve("HD 206948", mission="TESS",
                                   author="TESS-SPOC", exptime=200, sector=68)

if len(search) == 0:
    print("ERROR: TESS-SPOC 200s sector 68 not found.")
    raise SystemExit(1)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    lc = search.download()

lc   = lc.remove_nans()
med  = float(np.nanmedian(lc.flux.value))
ppm  = np.array(1e6 * (lc.flux.value / med - 1.0), dtype=np.float64)
clip = sigma_clip(ppm, sigma=5, maxiters=3, masked=True)
good = ~np.array(clip.mask, dtype=bool)
t_days   = lc.time.value[good]
flux_ppm = ppm[good]
idx = np.argsort(t_days)
t_days, flux_ppm = t_days[idx], flux_ppm[idx]
print(f"  {good.sum():,} cadences, baseline={t_days[-1]-t_days[0]:.1f} d")

# ── PSD ───────────────────────────────────────────────────────────────────────
freq_uhz, freq_cd, df_uhz = make_freq_grid(F_MIN=0.5, F_MAX=300.0, df=0.01)

print("\nComputing calibrated PSD...")
psd, PSD_SCALE, C_noise = calibrate_psd(
    t_days, flux_ppm, freq_uhz, freq_cd, df_uhz,
    nu_cal=PRED_NMAX, A_cal=10.0, verbose=False
)

# ── Background subtraction ────────────────────────────────────────────────────
background = harvey(freq_uhz, S1, T1) + harvey(freq_uhz, S2, T2) + CF
psd_bg_sub = np.clip(psd - background, 0, None)

# ── Échelle diagram ───────────────────────────────────────────────────────────
# Restrict to a window around the oscillation envelope: ±5 Δν around νmax
# This is the standard echelle region for p-mode identification.
nu_lo = max(NUMAX_FIT - 5.5 * DNE_FIT, 5.0)   # ~20 µHz
nu_hi = min(NUMAX_FIT + 5.5 * DNE_FIT, 150.0)  # ~57 µHz

print(f"\nBuilding échelle diagram:")
print(f"  Δν = {DNE_FIT:.2f} µHz  (from ACF)")
print(f"  Frequency window: {nu_lo:.1f} – {nu_hi:.1f} µHz")

m_ech = (freq_uhz >= nu_lo) & (freq_uhz <= nu_hi)
freq_ech = freq_uhz[m_ech]
psd_ech  = psd_bg_sub[m_ech]

# Smooth slightly to reduce single-bin noise before folding
psd_ech_smooth = uniform_filter1d(psd_ech, size=3)

def make_echelle(freq, power, delta_nu, eps=0.0):
    """
    Build a 2D échelle image.

    Returns
    -------
    echelle_2d  : 2D array (n_rows × n_cols)
    x_axis      : 1D array, frequency mod delta_nu (cols)
    y_axis      : 1D array, frequency (row centres)
    """
    # Use a fixed column width equal to Δν with oversampling factor ~5
    n_cols   = max(int(round(delta_nu / df_uhz)), 10)
    n_points = len(freq)
    n_rows   = n_points // n_cols

    if n_rows < 2:
        raise ValueError(f"Too few rows ({n_rows}) for echelle. "
                         f"Check frequency range and delta_nu.")

    # Trim to integer number of rows
    n_use  = n_rows * n_cols
    freq_t = freq[:n_use]
    pwr_t  = power[:n_use]

    echelle_2d = pwr_t.reshape(n_rows, n_cols)
    x_axis = (freq_t[:n_cols] - freq_t[0]) % delta_nu
    # y-axis: frequency at the start of each row
    y_axis = np.array([freq_t[i * n_cols] for i in range(n_rows)])

    return echelle_2d, x_axis, y_axis

echelle_2d, x_axis, y_axis = make_echelle(freq_ech, psd_ech_smooth, DNE_FIT)
print(f"  Échelle grid: {echelle_2d.shape[0]} rows × {echelle_2d.shape[1]} cols")

# ── Plots ─────────────────────────────────────────────────────────────────────

# 1. Background-subtracted PSD in the echelle window
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(freq_ech, psd_ech_smooth, color="steelblue", lw=0.7, label="BG-subtracted PSD")
ax.axhline(0, color="grey", lw=0.5, linestyle="--")
# Mark expected mode positions
n_lo = int(np.ceil(nu_lo / DNE_FIT))
n_hi = int(np.floor(nu_hi / DNE_FIT))
for n in range(n_lo, n_hi + 1):
    ax.axvline(n * DNE_FIT, color="tomato", lw=0.5, alpha=0.4)
ax.set_xlabel("Frequency (µHz)")
ax.set_ylabel("PSD – background (ppm²/µHz)")
ax.set_title(f"HD 206948 — Background-subtracted PSD (Δν comb at {DNE_FIT} µHz)")
ax.legend(fontsize=9)
ax.set_xlim(nu_lo, nu_hi)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "echelle_bgsub.png", dpi=150)
plt.close(fig)

# 2. Échelle diagram
fig, ax = plt.subplots(figsize=(6, 8))

# Clip colour scale to highlight ridges without saturation from isolated bright bins
vmax = np.percentile(echelle_2d, 98)
vmin = 0

img = ax.imshow(
    echelle_2d,
    origin="lower",
    aspect="auto",
    extent=[x_axis[0], x_axis[-1] + (x_axis[1]-x_axis[0]),
            y_axis[0], y_axis[-1]],
    cmap="YlOrRd",
    vmin=vmin, vmax=vmax,
    interpolation="nearest",
)
cbar = fig.colorbar(img, ax=ax, label="BG-subtracted PSD (ppm²/µHz)", pad=0.02)

ax.set_xlabel(f"Frequency mod Δν  (Δν = {DNE_FIT:.2f} µHz)")
ax.set_ylabel("Frequency (µHz)")
ax.set_title(f"HD 206948 — Échelle diagram\n"
             f"νmax = {NUMAX_FIT:.1f} µHz, Δν = {DNE_FIT:.2f} µHz")

# Mark expected ridge positions (ℓ=0 near εΔν, ℓ=2 near (ε−0.12)Δν)
# ε ≈ 0.5–0.9 for giants; mark as vertical dashed lines for reference
for frac, label, col in [(0.5, "ℓ=0?", "blue"), (0.88, "ℓ=2?", "green")]:
    ax.axvline(frac * DNE_FIT, color=col, lw=1.0, linestyle="--", alpha=0.7,
               label=f"{label} (ε={frac:.2f})")

ax.legend(fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(PLOTS_DIR / "echelle.png", dpi=150)
plt.close(fig)

# Also try with pySYD's Δν for comparison
try:
    echelle_pysyd, x_pysyd, y_pysyd = make_echelle(freq_ech, psd_ech_smooth, DNE_PYSYD)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8), sharey=True)
    for ax_e, ech, x_ax, dnu, label in [
        (ax1, echelle_2d,   x_axis,  DNE_FIT,   f"Δν={DNE_FIT:.2f} µHz (ACF)"),
        (ax2, echelle_pysyd, x_pysyd, DNE_PYSYD, f"Δν={DNE_PYSYD:.2f} µHz (pySYD)"),
    ]:
        v_max = np.percentile(ech, 98)
        ax_e.imshow(
            ech, origin="lower", aspect="auto",
            extent=[x_ax[0], x_ax[-1] + (x_ax[1]-x_ax[0]),
                    y_axis[0], y_axis[-1]],
            cmap="YlOrRd", vmin=0, vmax=v_max, interpolation="nearest",
        )
        ax_e.set_xlabel(f"Frequency mod Δν  ({label})")
        ax_e.set_title(label)
    ax1.set_ylabel("Frequency (µHz)")
    fig.suptitle(f"HD 206948 — Échelle diagram comparison\n"
                 f"νmax = {NUMAX_FIT:.1f} µHz", y=1.01)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "echelle_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved plots/echelle_comparison.png (ACF vs pySYD Δν)")
except Exception as e:
    print(f"  Comparison echelle skipped: {e}")

print("Saved plots/echelle_bgsub.png")
print("Saved plots/echelle.png")

# ── Assess ridge quality ──────────────────────────────────────────────────────
# A vertical ridge in the echelle has high column-to-column variance in each row
# vs low row-to-row variance within a column.
# Quantify: column variance across the echelle (high = ridges present).
col_means = echelle_2d.mean(axis=0)
col_std   = col_means.std()
mean_val  = echelle_2d.mean()
contrast  = col_std / mean_val if mean_val > 0 else 0

print(f"\n  Échelle grid: {echelle_2d.shape[0]} rows × {echelle_2d.shape[1]} cols")
print(f"  Column contrast ratio: {contrast:.3f}")
print(f"  (> 0.3 suggests ridge structure; < 0.1 is noise-dominated)")

if contrast > 0.3:
    print("  → Ridge structure detected — Δν is likely real.")
    print("    Mode identification (ℓ=0, 2) may be possible.")
elif contrast > 0.1:
    print("  → Marginal structure — individual modes marginally resolved.")
    print("    Sector 68 baseline (24 days) gives freq resolution 0.48 µHz;")
    print("    adjacent modes separated by ~3.64 µHz, so they should be resolved.")
    print("    Residual window-function power may obscure the ridges.")
else:
    print("  → No clear ridge structure — modes are not resolved in this dataset.")
    print("    The Δν from the ACF is the large-scale spacing, but individual")
    print("    modes are not visible above the noise.")

SEP = "─" * 65
print(f"\n{SEP}")
print("  Summary")
print(SEP)
print(f"  Δν used for echelle : {DNE_FIT:.2f} µHz (ACF) / "
      f"{DNE_PYSYD:.2f} µHz (pySYD)")
print(f"  νmax                : {NUMAX_FIT:.1f} µHz")
print(f"  Echelle window      : {nu_lo:.1f}–{nu_hi:.1f} µHz ({echelle_2d.shape[0]} rows)")
print(f"  Column contrast     : {contrast:.3f}")
print(f"  See plots/echelle.png and plots/echelle_comparison.png")
print(f"{SEP}\n")
