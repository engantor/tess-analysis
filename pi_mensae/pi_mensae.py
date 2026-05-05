import matplotlib
matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
import lightkurve as lk
from pathlib import Path

PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

# ── 1. Search MAST for Pi Mensae TESS lightcurves (SPOC) ─────────────────────
print("Searching MAST for Pi Mensae TESS SPOC lightcurves...")
search_result = lk.search_lightcurve("Pi Mensae", mission="TESS", author="SPOC")
print(f"\nAvailable sectors ({len(search_result)} results):")
print(search_result)

sectors = [r.exptime for r in search_result]  # just to iterate; print table covers it

# ── 2. Download the first sector ─────────────────────────────────────────────
print("\nDownloading sector 1 lightcurve...")
lc_collection = search_result[0].download()
lc = lc_collection

# ── 3. Remove NaNs and normalize ─────────────────────────────────────────────
lc = lc.remove_nans()
lc = lc.normalize()

# ── 4. Save raw lightcurve plot ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 4))
lc.plot(ax=ax, label="Raw (normalized)")
ax.set_title("Pi Mensae – Raw TESS Lightcurve (Sector 1, SPOC)")
ax.set_xlabel("Time (BTJD days)")
ax.set_ylabel("Normalized Flux")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "raw.png", dpi=150)
plt.close(fig)
print("Saved plots/raw.png")

# ── 5. Flatten stellar variability ───────────────────────────────────────────
print("\nFlattening stellar variability (window=901)...")
flat_lc, trend = lc.flatten(window_length=901, return_trend=True)

# ── 6. BLS periodogram ───────────────────────────────────────────────────────
print("Running BLS periodogram (1–20 days, 0.001-day steps)...")
period_grid = np.arange(1, 20, 0.001)
bls = flat_lc.to_periodogram(method="bls", period=period_grid, frequency_factor=500)

best_period = bls.period_at_max_power.value
print(f"\nPeriod at maximum BLS power: {best_period:.4f} days")
print(f"  (Expected ~6.27 days for Pi Mensae c)")

# ── 7. Fold and save phase-folded plot ───────────────────────────────────────
t0 = bls.transit_time_at_max_power.value
folded = flat_lc.fold(period=best_period, epoch_time=t0)

fig, ax = plt.subplots(figsize=(10, 5))
folded.scatter(ax=ax, s=2, alpha=0.4, label="Individual cadences")
folded.bin(bins=100).plot(ax=ax, color="tomato", linewidth=2, label="Binned (100 bins)")
ax.set_title(
    f"Pi Mensae c – Phase-folded Lightcurve\n"
    f"Period = {best_period:.4f} d  |  t₀ = {t0:.4f} BTJD"
)
ax.set_xlabel("Phase (days)")
ax.set_ylabel("Normalized Flux")
ax.legend()
fig.tight_layout()
fig.savefig(PLOTS_DIR / "folded.png", dpi=150)
plt.close(fig)
print("Saved plots/folded.png")
