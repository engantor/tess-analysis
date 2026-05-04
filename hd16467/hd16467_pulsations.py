"""
Extended frequency analysis of HD 16467 — a K0III giant.
Searches for asteroseismic signal (solar-like oscillations / pulsations)
in the TESS lightcurve using a wide-range Lomb-Scargle periodogram,
window-function simulation, ACF, and top-peak extraction.
"""

import matplotlib
matplotlib.use("Agg")

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba
import lightkurve as lk
from scipy.signal import find_peaks, correlate
from pathlib import Path

PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

# Conversion constant: 1 µHz = UDAY cycles/day
UDAY = 86400e-6   # 0.0864 c/d per µHz

# ── 1. Load lightcurve (same as hd16467.py) ───────────────────────────────────
print("Searching and downloading HD 16467 SPOC lightcurves (sectors 31, 70, 71)...")
search = lk.search_lightcurve("HD 16467", mission="TESS", author="SPOC")
lc_collection = search.download_all()
lc = lc_collection.stitch().remove_nans().normalize()
print(f"  {len(lc)} cadences  |  baseline: "
      f"{lc.time.value[-1] - lc.time.value[0]:.1f} days")

# ── 2. Flatten for ACF and BLS (light detrend only) ──────────────────────────
flat_lc = lc.flatten(window_length=401)

# ── 3. Wide Lomb-Scargle periodogram (1–1000 µHz) ────────────────────────────
F_MIN_UHZ = 1.0
F_MAX_UHZ = 1000.0
f_min_cd = F_MIN_UHZ * UDAY
f_max_cd = F_MAX_UHZ * UDAY

print(f"\nRunning Lomb-Scargle periodogram ({F_MIN_UHZ:.0f}–{F_MAX_UHZ:.0f} µHz) "
      f"with oversample_factor=10...")
pg = lc.to_periodogram(
    method="lombscargle",
    minimum_frequency=f_min_cd,
    maximum_frequency=f_max_cd,
    oversample_factor=10,
)

freq_cd   = pg.frequency.value           # cycles/day
freq_uhz  = freq_cd / UDAY               # µHz
power     = pg.power.value

# ── 4. Window function (white noise at same timestamps) ───────────────────────
print("Computing window function (white-noise simulation)...")
rng = np.random.default_rng(seed=42)
noise_flux = rng.standard_normal(len(lc))

# Build a minimal fake LightCurve with the same time axis
from lightkurve import LightCurve
import astropy.units as au
lc_noise = LightCurve(
    time=lc.time,
    flux=noise_flux * au.dimensionless_unscaled,
)
pg_noise = lc_noise.to_periodogram(
    method="lombscargle",
    minimum_frequency=f_min_cd,
    maximum_frequency=f_max_cd,
    oversample_factor=10,
)
power_noise = pg_noise.power.value

# Normalise noise periodogram to the same median level as the real one
# (so shape of window artefacts is visible without scale confusion)
power_noise_scaled = power_noise * (np.median(power) / np.median(power_noise))

# ── 5. Full periodogram plot (log x-axis, annotated regions) ─────────────────
# Annotation regions (µHz)
REGIONS = [
    (1,   5,   "Long-period\nrot./activity", "#dce8f5"),
    (5,   50,  "γ Dor\n(5–50 µHz)",          "#d5e8d4"),
    (50,  500, "δ Sct\n(50–500 µHz)",         "#fff2cc"),
    (500, 1000,"Solar-like\n(peak >500 µHz)", "#f8cecc"),
]

fig, ax = plt.subplots(figsize=(14, 5))
for f_lo, f_hi, label, colour in REGIONS:
    ax.axvspan(f_lo, f_hi, color=colour, alpha=0.35, zorder=0)
    mid = 10**((np.log10(f_lo) + np.log10(f_hi)) / 2)
    ax.text(mid, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1,
            label, ha="center", va="top", fontsize=7.5,
            color="grey", transform=ax.get_xaxis_transform())

ax.plot(freq_uhz, power,       color="steelblue",  lw=0.7, alpha=0.9,
        label="Real lightcurve")
ax.plot(freq_uhz, power_noise_scaled, color="tomato", lw=0.5, alpha=0.4,
        label="White-noise (window function)")
ax.set_xscale("log")
ax.set_xlim(F_MIN_UHZ, F_MAX_UHZ)
ax.set_xlabel("Frequency (µHz)", fontsize=11)
ax.set_ylabel("LS Power", fontsize=11)
ax.set_title("HD 16467 – Lomb-Scargle Periodogram (1–1000 µHz)\n"
             "Red = window-function baseline (same timestamps, white noise)",
             fontsize=11)
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_pg_full.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_pg_full.png")

# ── 6. Top-5 peaks via scipy.signal.find_peaks ───────────────────────────────
# Strategy:
#   1. Smooth both real and noise periodograms with a broad Gaussian to get
#      the local noise floor at each frequency.
#   2. Compute SNR = real_power / smoothed_noise at each point.
#   3. Find peaks in the SNR array; require SNR > 3 and min separation of
#      at least 1 µHz (to avoid detecting adjacent samples in the same peak).
from scipy.ndimage import uniform_filter1d

# Samples per µHz — depends on oversample_factor and baseline
df_uhz = (freq_uhz[1] - freq_uhz[0]) if len(freq_uhz) > 1 else 1.0
min_sep_samples = max(int(1.0 / df_uhz), 10)   # 1 µHz minimum separation

# Smooth the noise periodogram over a ~5 µHz window to get the local floor
smooth_window = max(int(5.0 / df_uhz), 50)
noise_floor = uniform_filter1d(power_noise_scaled, size=smooth_window)
noise_floor = np.where(noise_floor > 0, noise_floor, np.finfo(float).tiny)

snr = power / noise_floor

SNR_THRESHOLD = 3.0
peak_indices, _ = find_peaks(
    snr,
    height=SNR_THRESHOLD,
    distance=min_sep_samples,
)

# Sort by SNR descending
if len(peak_indices):
    sorted_idx = np.argsort(snr[peak_indices])[::-1]
    top_peaks = peak_indices[sorted_idx[:5]]
else:
    top_peaks = []

print(f"\n── Top peaks (SNR > {SNR_THRESHOLD}, min separation {min_sep_samples} samples "
      f"≈ {min_sep_samples * df_uhz:.2f} µHz) ──────────────")
print(f"  {'Rank':<5} {'Freq (µHz)':>12} {'Period (days)':>14} "
      f"{'Period (hours)':>15} {'LS Power':>12}  {'SNR':>6}")
print(f"  {'-'*5} {'-'*12} {'-'*14} {'-'*15} {'-'*12}  {'-'*6}")

peak_info = []
for rank, pidx in enumerate(top_peaks, 1):
    f_uhz    = freq_uhz[pidx]
    p_days   = 1.0 / (f_uhz * UDAY)
    p_hours  = p_days * 24.0
    pw       = power[pidx]
    snr_val  = snr[pidx]
    peak_info.append((f_uhz, p_days, p_hours, pw, snr_val))
    print(f"  {rank:<5} {f_uhz:>12.2f} {p_days:>14.4f} {p_hours:>15.2f} "
          f"{pw:>12.6f}  {snr_val:>6.1f}")

if not peak_info:
    print("  No peaks found with SNR > 3 above the noise floor.")
    print("  This star appears photometrically quiet at all frequencies 1–1000 µHz.")

# ── 7. Zoom periodogram around strongest peak region ─────────────────────────
if peak_info:
    dominant_f = peak_info[0][0]   # peak_info entries: (f_uhz, p_days, p_hours, pw, snr)
    # Zoom ±40% around dominant frequency, but always show at least 10 µHz window
    zoom_half = max(dominant_f * 0.4, 15.0)
    z_lo = max(dominant_f - zoom_half, F_MIN_UHZ)
    z_hi = min(dominant_f + zoom_half, F_MAX_UHZ)

    zmask = (freq_uhz >= z_lo) & (freq_uhz <= z_hi)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(freq_uhz[zmask], power[zmask], color="steelblue", lw=0.8)

    # Mark top peaks that fall in this window
    for rank, (f_uhz, p_days, p_hours, pw, snr_val) in enumerate(peak_info, 1):
        if z_lo <= f_uhz <= z_hi:
            ax.axvline(f_uhz, color="tomato", lw=1.0, linestyle="--", alpha=0.7)
            ax.text(f_uhz, pw * 1.02, f"#{rank}\n{f_uhz:.1f} µHz\n{p_hours:.1f} h",
                    ha="center", va="bottom", fontsize=7.5, color="tomato")

    ax.set_xlim(z_lo, z_hi)
    ax.set_xlabel("Frequency (µHz)", fontsize=11)
    ax.set_ylabel("LS Power", fontsize=11)
    ax.set_title(f"HD 16467 – Zoom: {z_lo:.0f}–{z_hi:.0f} µHz  "
                 f"(dominant peak at {dominant_f:.1f} µHz  /  "
                 f"{peak_info[0][2]:.1f} h)", fontsize=11)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "hd16467_pg_zoom.png", dpi=150)
    plt.close(fig)
    print("Saved plots/hd16467_pg_zoom.png")
else:
    print("Skipping zoom plot (no peaks found).")

# ── 8. Autocorrelation function ───────────────────────────────────────────────
# Computed on the flattened, mean-subtracted flux array.
# NOTE: sector gaps (months-long) mean the lag axis is approximate
# (we use the median cadence to convert sample lags to days).
# The ACF is still informative for within-sector periodicity.
print("\nComputing autocorrelation function...")
flux_vals = flat_lc.flux.value
flux_dm   = flux_vals - np.mean(flux_vals)
acf_full  = correlate(flux_dm, flux_dm, mode="full")
acf_full /= acf_full[len(flux_dm) - 1]   # normalise to 1 at zero lag

# Positive lags only
acf = acf_full[len(flux_dm) - 1:]

# Lag axis in days via median cadence
dt_days = np.median(np.diff(lc.time.value))
lags_days = np.arange(len(acf)) * dt_days

# Plot 0 – 10 days
max_lag_days = 10.0
mask_lag = lags_days <= max_lag_days

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(lags_days[mask_lag], acf[mask_lag], color="steelblue", lw=0.8)
ax.axhline(0, color="grey", lw=0.6, linestyle="--")
# Mark lag = dominant period if known
if peak_info:
    for f_uhz, p_days, p_hours, pw, *_ in peak_info[:2]:
        if p_days <= max_lag_days:
            ax.axvline(p_days, color="tomato", lw=1.0, linestyle=":", alpha=0.8,
                       label=f"P = {p_days:.3f} d ({p_hours:.1f} h)")
ax.set_xlabel("Lag (days)", fontsize=11)
ax.set_ylabel("Autocorrelation", fontsize=11)
ax.set_title("HD 16467 – ACF (flattened lightcurve, 0–10 days)\n"
             "Note: sector gaps make long lags approximate",
             fontsize=10)
ax.set_xlim(0, max_lag_days)
if peak_info:
    ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_acf.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_acf.png")

# ── 9. Classification ─────────────────────────────────────────────────────────
# Stellar context (from hd16467_context.py):
#   K0III giant, Teff=4966 K, log g=2.551, R=10.5 Rsun
#   Predicted νmax ≈ 43 µHz (period ≈ 6.4 h), Δν ≈ 4.8 µHz
TEFF      = 4966
LOGG      = 2.551
SP_TYPE   = "K0III"
NMAX_PRED = 43.3   # µHz  (solar-like scaling: νmax/νmax_sun = (g/g_sun)*(Teff_sun/Teff)^0.5)
DELT_PRED =  4.8   # µHz  (Δν/Δν_sun = (ρ/ρ_sun)^0.5, M≈1.5 Msun assumed)

import textwrap

print(f"\n── Asteroseismic Classification ──────────────────────────────")
print(f"  Stellar context : {SP_TYPE}, Teff={TEFF} K, log g={LOGG}")
print(f"  Predicted ν_max : {NMAX_PRED:.1f} µHz  "
      f"(period ≈ {1e6/NMAX_PRED/3600:.1f} h)  |  Δν ≈ {DELT_PRED:.1f} µHz")

if peak_info:
    dom_f, dom_p_d, dom_p_h, dom_pw, dom_snr = peak_info[0]

    # Where the dominant peak sits in the frequency taxonomy
    below_gdor = dom_f < 5
    in_gdor    = 5  <= dom_f < 50
    in_dsct    = 50 <= dom_f < 500
    above_dsct = dom_f >= 500

    # Is it near the predicted νmax (within ±50%)? K-giant scaling has ~±0.3 dex log g uncertainty
    near_nmax = abs(dom_f - NMAX_PRED) / NMAX_PRED < 0.5

    # Are detected peaks clustered in the sub-νmax regime (long-period g/mixed modes)?
    all_freqs = [p[0] for p in peak_info]
    frac_below_nmax = sum(f < NMAX_PRED for f in all_freqs) / len(all_freqs)
    peaks_sub_nmax = frac_below_nmax >= 0.8

    # Check if any peak coincides with the window-function noise simulation
    # (peaks at the same frequency in both real and noise PG are suspects)
    window_suspects = []
    for pi_info in peak_info:
        f_uhz_peak = pi_info[0]
        # Find nearest frequency bin in noise PG
        idx = np.argmin(np.abs(freq_uhz - f_uhz_peak))
        snr_in_noise = power_noise_scaled[idx] / noise_floor[idx]
        if snr_in_noise > 2.0:
            window_suspects.append(f"{f_uhz_peak:.1f} µHz")

    # Check if top peaks form a comb-like pattern (Δν spacing)
    if len(peak_info) >= 3:
        freqs = sorted([p[0] for p in peak_info[:5]])
        diffs = np.diff(freqs)
        median_spacing = np.median(diffs)
        spacing_regular = (np.std(diffs) / median_spacing < 0.3) and (len(diffs) >= 3)
    else:
        median_spacing = None
        spacing_regular = False

    print(f"\n  Dominant peak   : {dom_f:.2f} µHz  ({dom_p_h:.1f} h / {dom_p_d:.3f} d)  "
          f"SNR vs noise floor = {dom_snr:.0f}")
    print(f"  All top peaks   : {', '.join(f'{p[0]:.1f}' for p in peak_info)} µHz")
    if median_spacing:
        print(f"  Median spacing  : {median_spacing:.2f} µHz  "
              f"({'regular comb' if spacing_regular else 'irregular — not a simple Δν ladder'})")
    if window_suspects:
        print(f"  Window-function suspects: {', '.join(window_suspects)}")
        print(f"    → Check hd16467_pg_full.png: if these appear in the red (noise) trace too,")
        print(f"      they may be sampling artifacts from the sector gaps, not astrophysics.")
    else:
        print(f"  No obvious window-function coincidences found.")

    # ── Classify ────────────────────────────────────────────────────────────
    if near_nmax:
        classification = "Solar-like oscillator (K red giant)"
        reasoning = (
            f"Dominant peak ({dom_f:.1f} µHz) is within 50% of the scaling-relation "
            f"prediction for ν_max ({NMAX_PRED:.1f} µHz) for a K0III giant. "
            f"The spectral type and log g = {LOGG} place this star in the red-giant "
            f"solar-like oscillation regime. The sub-day periodicity is consistent with "
            f"stochastically excited pressure modes."
        )
    elif peaks_sub_nmax and in_gdor:
        classification = (
            "K-giant low-frequency variability — likely g-mode/mixed-mode oscillations "
            "or activity (NOT γ Dor)"
        )
        reasoning = (
            f"All detected peaks ({min(all_freqs):.1f}–{max(all_freqs):.1f} µHz) lie "
            f"well below the predicted ν_max of {NMAX_PRED:.1f} µHz. γ Dor pulsation "
            f"(A/F main-sequence) is ruled out by the K0III spectral type. "
            f"These frequencies are consistent with (a) g-mode or mixed-mode oscillations "
            f"on the low-frequency wing of the red-giant oscillation envelope — possible if "
            f"the star is more evolved or less massive than assumed — or (b) rotational "
            f"modulation / activity at 2–3 day timescales (though the estimated P_rot from "
            f"v sin i is ~50+ days, making rotation an unlikely explanation for the "
            f"sub-3-day peaks). Compare these peaks to the window-function trace in "
            f"hd16467_pg_full.png before drawing firm conclusions."
        )
    elif in_dsct:
        classification = "Uncertain — δ Sct frequency but K0III spectral type is inconsistent"
        reasoning = (
            f"Peaks at {dom_f:.1f} µHz fall in the δ Sct instability strip range "
            f"(50–500 µHz), but {SP_TYPE} is far outside the strip (A0–F5 main sequence). "
            f"These peaks are likely window-function artifacts or instrumental systematics. "
            f"Check the noise simulation overlay in hd16467_pg_full.png."
        )
    else:
        classification = "Uncertain — see plots"
        reasoning = (
            f"Detected peaks at {min(all_freqs):.1f}–{max(all_freqs):.1f} µHz do not "
            f"cleanly map to a known variability class. Inspect hd16467_pg_full.png "
            f"to compare against the window-function baseline."
        )
else:
    classification = "No significant variability detected (all frequencies 1–1000 µHz)"
    reasoning = (
        "No peaks with SNR > 3 above the noise floor were found across the full "
        f"1–1000 µHz range. The {SP_TYPE} primary may have oscillation amplitudes "
        "below the TESS detection threshold, or the signal may be diluted by the "
        "3-year sector gap in the dataset. The star is photometrically quiet."
    )

print(f"\n  Classification  : {classification}")
print(f"\n  Reasoning:")
for line in textwrap.wrap(reasoning, width=65):
    print(f"    {line}")

print(f"\n  ACF note: Check hd16467_acf.png.")
p_nmax_h = 1e6 / NMAX_PRED / 3600
print(f"    If this is a solar-like oscillator, expect recurring ACF peaks")
print(f"    at ~{p_nmax_h:.1f}-hour lags. Decaying oscillation in ACF = quasi-periodic;")
print(f"    single spike at zero lag only = noise-dominated at that timescale.")
print("─────────────────────────────────────────────────────────────")
