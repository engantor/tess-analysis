import matplotlib
matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk
from pathlib import Path

PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

# ── 1. Search MAST: prefer SPOC, fall back to QLP ────────────────────────────
print("Searching MAST for Epsilon Eridani TESS SPOC lightcurves...")
search_result = lk.search_lightcurve("Epsilon Eridani", mission="TESS", author="SPOC")

if len(search_result) == 0:
    print("No SPOC data found, falling back to QLP...")
    search_result = lk.search_lightcurve("Epsilon Eridani", mission="TESS", author="QLP")
    if len(search_result) == 0:
        raise RuntimeError("No TESS lightcurves found for Epsilon Eridani on MAST.")

author_used = search_result.table["author"][0]
print(f"\nUsing author: {author_used}")
print(f"Available sectors ({len(search_result)} results):")
print(search_result)

# ── 2. Download all available sectors and stitch ─────────────────────────────
n_sectors = len(search_result)
print(f"\nDownloading {n_sectors} sector(s)...")
lc_collection = search_result.download_all()

if n_sectors > 1:
    print("Stitching sectors together...")
    lc = lc_collection.stitch()
else:
    lc = lc_collection[0]

# ── 3. Remove NaNs and normalize ─────────────────────────────────────────────
lc = lc.remove_nans()
lc = lc.normalize()

time_baseline = lc.time.value[-1] - lc.time.value[0]

# ── 4. Save raw lightcurve plot ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 4))
lc.plot(ax=ax, alpha=0.6, label=f"Normalized ({n_sectors} sector(s))")
ax.set_title(f"Epsilon Eridani – Raw TESS Lightcurve ({author_used}, {n_sectors} sector(s))")
ax.set_xlabel("Time (BTJD days)")
ax.set_ylabel("Normalized Flux")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "eps_eri_raw.png", dpi=150)
plt.close(fig)
print("Saved plots/eps_eri_raw.png")

# ── 5. Lomb-Scargle periodogram (1–30 days) ───────────────────────────────────
print("\nComputing Lomb-Scargle periodogram (1–30 days)...")
ls = lc.to_periodogram(method="lombscargle", minimum_period=1, maximum_period=30)

best_period = ls.period_at_max_power.value
print(f"\nPeriod at maximum LS power: {best_period:.4f} days")
print(f"  (Expected ~11.2 days – stellar rotation from spot modulation)")

# Save periodogram plot
fig, ax = plt.subplots(figsize=(10, 4))
ls.plot(ax=ax)
ax.axvline(best_period, color="tomato", linewidth=1.5, linestyle="--",
           label=f"Max power: {best_period:.3f} d")
ax.set_title("Epsilon Eridani – Lomb-Scargle Periodogram")
ax.set_xlabel("Period (days)")
ax.set_ylabel("Power")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "eps_eri_periodogram.png", dpi=150)
plt.close(fig)
print("Saved plots/eps_eri_periodogram.png")

# ── 6. Phase-fold on detected period ─────────────────────────────────────────
folded = lc.fold(period=best_period)

fig, ax = plt.subplots(figsize=(10, 5))
folded.scatter(ax=ax, s=2, alpha=0.3, label="Individual cadences")
folded.bin(bins=100).plot(ax=ax, color="steelblue", linewidth=2, label="Binned (100 bins)")
ax.set_title(
    f"Epsilon Eridani – Phase-folded Lightcurve\n"
    f"Period = {best_period:.4f} d  (stellar rotation)"
)
ax.set_xlabel("Phase (days)")
ax.set_ylabel("Normalized Flux")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "eps_eri_folded.png", dpi=150)
plt.close(fig)
print("Saved plots/eps_eri_folded.png")

# ── 7. Summary ────────────────────────────────────────────────────────────────
flux = lc.flux.value
amplitude = np.percentile(flux, 95) - np.percentile(flux, 5)

print("\n── Summary ──────────────────────────────────────────────────")
print(f"  Sectors used      : {n_sectors}")
print(f"  Author            : {author_used}")
print(f"  Time baseline     : {time_baseline:.1f} days")
print(f"  Detected period   : {best_period:.4f} days")
print(f"  Flux amplitude    : {amplitude * 100:.3f}%  (5th–95th percentile range)")
print("─────────────────────────────────────────────────────────────")
