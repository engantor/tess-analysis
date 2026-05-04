import matplotlib
matplotlib.use("Agg")

import warnings
import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk
from pathlib import Path

PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

# ── 1. Search MAST — try identifiers in order ─────────────────────────────────
IDENTIFIERS = ["HD 16467", "HIP 12318"]
PREFERRED_AUTHORS = ["SPOC", "QLP"]

search_lc = None
used_ident = None
for ident in IDENTIFIERS:
    result = lk.search_lightcurve(ident, mission="TESS")
    if len(result) > 0:
        search_lc = result
        used_ident = ident
        break

if search_lc is None:
    raise RuntimeError(
        "No TESS lightcurves found for HD 16467 under any tried identifier."
    )

# Filter to preferred author in priority order
spoc_mask = [row["author"] == "SPOC" for row in search_lc.table]
qlp_mask  = [row["author"] == "QLP"  for row in search_lc.table]

if any(spoc_mask):
    chosen_author = "SPOC"
    search_spoc = search_lc[spoc_mask]
elif any(qlp_mask):
    chosen_author = "QLP"
    search_spoc = search_lc[qlp_mask]
else:
    chosen_author = search_lc.table["author"][0]
    search_spoc = search_lc

print(f"Identifier used  : {used_ident}")
print(f"Pipeline selected: {chosen_author}")
print(f"\nAll available TESS products for HD 16467:")
print(search_lc)
print(f"\nUsing {len(search_spoc)} {chosen_author} sector(s):")
print(search_spoc)

# ── 2. Target pixel file for sector 0 — aperture inspection ──────────────────
print("\nDownloading target pixel file for aperture inspection...")
tpf_search = lk.search_targetpixelfile(used_ident, mission="TESS", author=chosen_author)
tpf = tpf_search[0].download()

fig, ax = plt.subplots(figsize=(6, 6))
tpf.plot(aperture_mask=tpf.pipeline_mask, ax=ax)
ax.set_title(
    f"HD 16467 – TESS Aperture\n"
    f"Sector {tpf.sector}  |  {tpf.camera}/{tpf.ccd}  |  21\"/px\n"
    "(check whether visual companion falls inside shaded mask)"
)
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_aperture.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_aperture.png")

# ── 3. Download all LC sectors and stitch ────────────────────────────────────
print(f"\nDownloading {len(search_spoc)} lightcurve sector(s)...")
lc_collection = search_spoc.download_all()

if len(search_spoc) > 1:
    print("Stitching sectors...")
    lc = lc_collection.stitch()
else:
    lc = lc_collection[0]

lc = lc.remove_nans().normalize()

time_arr  = lc.time.value
flux_arr  = lc.flux.value
time_span = time_arr[-1] - time_arr[0]
n_sectors = len(search_spoc)

# ── 4. Raw lightcurve plot + zoomed first-10-days view ───────────────────────
fig, ax = plt.subplots(figsize=(14, 4))
lc.plot(ax=ax, alpha=0.6, label=f"{chosen_author} — {n_sectors} sector(s)")
ax.set_title(f"HD 16467 – Raw TESS Lightcurve ({chosen_author})")
ax.set_xlabel("Time (BTJD days)")
ax.set_ylabel("Normalized Flux")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_raw.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_raw.png")

# Zoomed: first 10 days
t0 = time_arr[0]
zoom_mask = (time_arr >= t0) & (time_arr <= t0 + 10)
lc_zoom = lc[zoom_mask]

fig, ax = plt.subplots(figsize=(12, 4))
lc_zoom.scatter(ax=ax, s=4, alpha=0.7, label="First 10 days")
ax.set_title("HD 16467 – Zoomed First 10 Days (eclipse search by eye)")
ax.set_xlabel("Time (BTJD days)")
ax.set_ylabel("Normalized Flux")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_zoom.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_zoom.png")

# ── 5. Dual periodograms ──────────────────────────────────────────────────────
PERIOD_MIN = 0.5
PERIOD_MAX = 15.0
PERIOD_STEP = 0.001
period_grid = np.arange(PERIOD_MIN, PERIOD_MAX, PERIOD_STEP)

# BLS — flatten first so slow trends don't pollute the box-search
print("\nFlattening lightcurve for BLS (window=401)...")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    flat_lc = lc.flatten(window_length=401)

print("Running BLS periodogram (0.5–15 days)...")
bls = flat_lc.to_periodogram(method="bls", period=period_grid, frequency_factor=500)

bls_best_period = bls.period_at_max_power.value
bls_max_power   = float(bls.max_power.value)

# Compute BLS signal-detection-efficiency (SDE): how many sigma above the
# periodogram noise floor the peak sits.  SDE > ~7 is typically considered
# a credible detection threshold; < 5 is noise.
bls_power_arr = bls.power.value
bls_sde = (bls_max_power - np.median(bls_power_arr)) / np.std(bls_power_arr)

# Flag edge-of-grid peaks — BLS often piles power at period boundaries
bls_at_edge = (
    bls_best_period < PERIOD_MIN * 1.02 or
    bls_best_period > PERIOD_MAX * 0.98
)

fig, ax = plt.subplots(figsize=(10, 4))
bls.plot(ax=ax)
ax.axvline(bls_best_period, color="tomato", linewidth=1.5, linestyle="--",
           label=f"Peak: {bls_best_period:.4f} d")
ax.set_title("HD 16467 – BLS Periodogram (box-shaped eclipse search)")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_bls.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_bls.png")

# Lomb-Scargle — on the unflattened (just normalized) lightcurve
print("Running Lomb-Scargle periodogram (0.5–15 days)...")
ls = lc.to_periodogram(
    method="lombscargle",
    minimum_period=PERIOD_MIN,
    maximum_period=PERIOD_MAX,
)

ls_best_period = ls.period_at_max_power.value
ls_max_power   = float(ls.max_power.value)

# LS signal-detection-efficiency: peak power vs. periodogram noise floor.
# SDE > 7 is the same threshold used for BLS detections.
ls_power_arr = ls.power.value
ls_sde = (ls_max_power - np.median(ls_power_arr)) / np.std(ls_power_arr)

fig, ax = plt.subplots(figsize=(10, 4))
ls.plot(ax=ax)
ax.axvline(ls_best_period, color="steelblue", linewidth=1.5, linestyle="--",
           label=f"Peak: {ls_best_period:.4f} d")
ax.set_title("HD 16467 – Lomb-Scargle Periodogram (sinusoidal variation search)")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_ls.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_ls.png")

# ── 6. Comparison table ───────────────────────────────────────────────────────
print("\n── Periodogram Comparison ──────────────────────────────────────────────")
print(f"  {'Method':<12}  {'Peak period (d)':>16}  {'SDE':>8}  {'Edge?':>6}")
print(f"  {'-'*12}  {'-'*16}  {'-'*8}  {'-'*6}")
print(f"  {'BLS':<12}  {bls_best_period:>16.4f}  {bls_sde:>8.1f}  {'YES' if bls_at_edge else 'no':>6}")
print(f"  {'Lomb-Scargle':<12}  {ls_best_period:>16.4f}  {ls_sde:>8.1f}  {'no':>6}")
print("  (SDE = signal-detection-efficiency; >7 is a credible detection threshold)")
print("────────────────────────────────────────────────────────────────────────")

# Decide which dominates using SDE > 7 and edge-artifact check.
bls_significant = bls_sde > 7 and not bls_at_edge
ls_significant  = ls_sde > 7

periods_agree = abs(bls_best_period - ls_best_period) / min(bls_best_period, ls_best_period) < 0.05

# ── 7. Phase-folded plots (one per method) ────────────────────────────────────
# BLS fold
t0_bls = bls.transit_time_at_max_power.value
folded_bls = flat_lc.fold(period=bls_best_period, epoch_time=t0_bls)

fig, ax = plt.subplots(figsize=(10, 5))
folded_bls.scatter(ax=ax, s=2, alpha=0.3, label="Individual cadences")
folded_bls.bin(bins=100).plot(ax=ax, color="tomato", linewidth=2, label="Binned")
ax.set_title(
    f"HD 16467 – BLS Phase-fold  |  P = {bls_best_period:.4f} d\n"
    "(flat-bottomed dip at phase 0 would indicate eclipse)"
)
ax.set_xlabel("Phase (days)")
ax.set_ylabel("Normalized Flux")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_folded_bls.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_folded_bls.png")

# LS fold
folded_ls = lc.fold(period=ls_best_period)

fig, ax = plt.subplots(figsize=(10, 5))
folded_ls.scatter(ax=ax, s=2, alpha=0.3, label="Individual cadences")
folded_ls.bin(bins=100).plot(ax=ax, color="steelblue", linewidth=2, label="Binned")
ax.set_title(
    f"HD 16467 – LS Phase-fold  |  P = {ls_best_period:.4f} d\n"
    "(smooth sinusoid would indicate rotation or ellipsoidal modulation)"
)
ax.set_xlabel("Phase (days)")
ax.set_ylabel("Normalized Flux")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "hd16467_folded_ls.png", dpi=150)
plt.close(fig)
print("Saved plots/hd16467_folded_ls.png")

# ── 8. Plain-English summary ──────────────────────────────────────────────────
flux_std     = np.std(flux_arr)
flux_amp     = np.percentile(flux_arr, 95) - np.percentile(flux_arr, 5)
is_flat      = flux_amp < 0.003   # < 0.3% peak-to-trough is effectively quiet

# Characterise lightcurve behaviour
if is_flat:
    lc_character = "flat — no obvious variability above the noise floor"
elif flux_amp > 0.01:
    lc_character = "clearly variable (>1% amplitude)"
else:
    lc_character = "mildly variable (<1% amplitude)"

# Signal type heuristic using proper significance thresholds
if bls_at_edge and not ls_significant:
    dominant_signal = "no significant periodic signal (BLS peak is a grid-edge artifact)"
    shape_note = (
        f"The BLS peaked at {bls_best_period:.4f} d, right at the edge of the search grid — "
        "a typical noise artifact when no real box-shaped signal exists. "
        f"The LS SDE is also low ({ls_sde:.1f}), confirming no credible sinusoidal signal. "
        "This star appears photometrically quiet in TESS data."
    )
elif bls_significant and ls_significant and periods_agree:
    dominant_signal = "eclipse-like (both methods agree on the same period)"
    shape_note = (
        "The folded lightcurve should show a dip near phase 0. "
        "Check hd16467_folded_bls.png for a flat-bottomed eclipse profile."
    )
elif bls_significant and not ls_significant:
    dominant_signal = f"eclipse candidate (BLS SDE={bls_sde:.1f}, LS SDE={ls_sde:.1f})"
    shape_note = (
        "BLS detects a box-shaped periodic dip not well described by a sinusoid. "
        "Check hd16467_folded_bls.png — a flat-bottomed dip would support an eclipse."
    )
elif ls_significant and not bls_significant:
    dominant_signal = f"sinusoidal modulation (LS SDE={ls_sde:.1f}, BLS SDE={bls_sde:.1f})"
    shape_note = (
        "The LS phase-fold likely shows a smooth wave — consistent with stellar "
        "rotation or ellipsoidal tidal modulation, not sharp eclipses."
    )
else:
    dominant_signal = "no strongly significant periodic signal detected"
    shape_note = (
        "Both periodograms may be responding to noise or low-level "
        "instrumental systematics rather than astrophysical variability."
    )

# Companion contamination note
# TESS pixels are ~21 arcsec; the IDS AB separation is ~3 arcsec — well within one pixel.
companion_note = (
    "HD 16467 is a visual double with ~3 arcsec separation (IDS 02334+0301 AB). "
    "TESS pixels are 21 arcsec wide, so both components fall inside the aperture. "
    "Any detected signal is a blend of both stars. If variability is present, "
    "the true amplitude of the variable component is higher than measured here "
    "by a factor of (F_A + F_B) / F_variable."
)

print("\n══ Plain-English Summary ══════════════════════════════════════")
print(f"  Target          : HD 16467 (IDS 02334+0301 AB, visual binary)")
print(f"  Sectors used    : {n_sectors}  ({chosen_author})")
print(f"  Time baseline   : {time_span:.1f} days")
print(f"  Flux amplitude  : {flux_amp * 100:.3f}%  (5th–95th pct)")
print(f"  Flux std dev    : {flux_std * 100:.3f}%")
print()
print(f"  (a) Lightcurve character: {lc_character}")
print()
print(f"  (b) Dominant signal type: {dominant_signal}")
print(f"      {shape_note}")
print()
print(f"  (c) Binary companion: {companion_note}")
print("═══════════════════════════════════════════════════════════════")
