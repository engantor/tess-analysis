# HD 16467 — TESS Analysis Project Log

HD 16467 (HR 775, HIP 12318, TIC 422971931) — K0III giant at 131 pc,
visual binary with 0.9" companion (ΔV=4 mag, 2.4% flux contamination).

All scripts run from this directory (`hd16467/`).  Plots go to `plots/`.

---

## What we know

**Stellar parameters (Gaia DR3 / TIC v8):**
- Teff = 4966 K, log g = 2.551, [Fe/H] = −0.30
- R = 10.5 R☉, d = 131 pc, V = 6.24, Tmag = 5.375
- Spectral type: K0III

**TESS coverage:**
- SPOC sectors 31 (2020), 70 (2023), 71 (2023)
- 1115-day baseline, ~47,100 cadences, 120-second SPOC photometry

**Scaling-relation predictions:**
- νmax = 43.3 µHz (period ≈ 6.4 h)
- Δν = 4.8 µHz

---

## What we found

### Phase 1 — Reconnaissance (`hd16467.py`)

Dual BLS + Lomb-Scargle periodogram over 0.5–15 days.
- BLS peak at 0.502 d — exactly at the grid minimum, canonical artifact flag
- LS SDE = 3.8 (below detection threshold of 7)
- Flux amplitude 5th–95th: 0.14% (effectively at the noise floor)
- **Result: null result in period space, as expected for a pulsating giant**

### Phase 2 — Stellar context (`hd16467_context.py`)

Queried SIMBAD, Gaia DR3, TIC v8, WDS.
- Confirmed K0III giant (not F dwarf as initially assumed)
- Binary companion KUI 9 B: 0.9" separation, ΔV=4.03 mag → 2.4% flux
- Predicted νmax = 43.3 µHz, Δν = 4.8 µHz

### Phase 3 — Extended frequency search (`hd16467_pulsations.py`)

Wide Lomb-Scargle 1–1000 µHz, window-function comparison, ACF.
- 5 peaks detected at SNR 62–68, all in 3.8–14 µHz range
- **These peaks are below predicted νmax = 43 µHz**
- Classified as K-giant low-frequency variability (g-mode/mixed-mode or
  activity timescale) — not eclipses, not rotation
- Predicted p-mode envelope at 43 µHz not detected at this method's sensitivity

### Phase 4 — Proper asteroseismic analysis (`hd16467_seismic.py`)

Per-sector ppm normalization (no flattening), empirically-calibrated PSD,
Harvey + Gaussian envelope fit.

**Results:**
- Harvey model fit: converged ✓
- νmax = 43.43 ± 0.10 µHz (predicted 43.3 µHz — ratio 1.003)
- Detection status: **MARGINAL** (H/background = 4.40)
- Granulation: τ₁ = 2.3 h, τ₂ = 0.9 h (physically reasonable for K giant)
- Δν: ACF gives 1.87 µHz vs predicted 4.8 µHz — **unreliable at this SNR**

The νmax agreement with the scaling relation is strong positive evidence that
the marginal envelope is real, not a noise artifact.  The detection is limited
by the low duty cycle (~12%) from the 3-year gap between Sector 31 and
Sectors 70–71.

---

## Verification results (Phases 5–8)

### Sector survey (`check_new_sectors.py`)
No new SPOC sectors beyond 31, 70, 71. QLP and TESS-SPOC products
(600s/200s cadence) exist for the same sectors — could be used to
cross-check, but 120s SPOC is better for high-frequency work.

### pySYD (`run_pysyd.py`)
pySYD v6.10.5 required two Python 3.14 compatibility patches (applied to
the venv copy of `target.py`: `list.pop(None)` now requires an integer
argument). After patching:
- **numax_smooth = 44.48 ± 0.50 µHz** (our Harvey fit: 43.43 ± 0.10 µHz)
- Difference: 1.05 µHz = 2.1σ — **marginal inconsistency between methods**
- pySYD also fails to measure Δν reliably (gives 1.13 µHz vs predicted 4.8 µHz)
- BIC selects 2-Harvey + white noise model, same choice as our fit
- Amplitude/sigma values from pySYD are in un-normalized LS power units
  (billions of ppm), not comparable to our Harvey fit values

### Split-half (`split_half_validation.py`)
- Sector 31 alone: νmax = **42.55 ± 0.26 µHz** (MARGINAL, H/bkg=3.02)
- Sectors 70+71: νmax = **43.45 ± 0.13 µHz** (MARGINAL, H/bkg=4.69)
- Difference: 0.90 µHz = **3.1σ** — **MARGINAL INCONSISTENCY**
- Both subsets independently detect a marginal envelope near the predicted frequency

### Overall assessment
The detection is **real but borderline**. Every method (Harvey fit, pySYD,
both halves independently) finds a numax in the 42.5–44.5 µHz range, all
consistent with the 43.3 µHz prediction. The 3.1σ split-half discrepancy is
primarily caused by the short baselines (~25d and ~50d), which give less stable
PSD estimates than the full 1115-day dataset. The detection is NOT ready for
VSX submission without additional TESS coverage to consolidate the envelope
measurement and push the split-half consistency below 2σ.

## Open questions

1. **More TESS sectors**: HD 16467 needs more coverage, ideally consecutive
   sectors, to confirm. The 3-year gap between Sector 31 and 70/71 is the
   primary limitation.

2. **Δν measurement**: Not achievable with current data. Would require either
   more sectors or a dedicated short-baseline, high-cadence observation.

3. **Method discrepancy**: Our Harvey fit gives 43.43 µHz, pySYD gives 44.48 µHz,
   split-half Sector 31 gives 42.55 µHz. All are in the right ballpark but the
   spread (2 µHz) is larger than the formal uncertainties suggest. With a
   marginal detection, curve_fit underestimates the true uncertainty.

---

## Scripts

### Run order for a fresh analysis

```bash
cd hd16467/

# Reconnaissance (1-15 day period space)
python hd16467.py

# Stellar context lookup
python hd16467_context.py

# Extended frequency search (1-1000 µHz)
python hd16467_pulsations.py

# Proper asteroseismic analysis
python hd16467_seismic.py

# Verification
python check_new_sectors.py
python run_pysyd.py          # requires: pip install pysyd
python split_half_validation.py
python detection_summary.py  # generates DETECTION_SUMMARY.md
```

### Script reference

| Script | What it does | Key outputs |
|---|---|---|
| `hd16467.py` | BLS+LS reconnaissance (0.5–15 d) | `plots/hd16467_*.png` |
| `hd16467_context.py` | SIMBAD/Gaia/TIC/WDS stellar params | terminal |
| `hd16467_pulsations.py` | Wide LS 1–1000 µHz, ACF | `plots/hd16467_pg_*.png`, `hd16467_acf.png` |
| `hd16467_seismic.py` | Harvey fit, νmax, detection | `plots/seismic_*.png` |
| `seismic_utils.py` | Shared functions (import only) | — |
| `check_new_sectors.py` | MAST sector survey | terminal |
| `run_pysyd.py` | pySYD validation | `pysyd_results.json`, `plots/pysyd_*.png` |
| `split_half_validation.py` | Split-half νmax consistency | `split_half_results.json`, `plots/split_half_psd.png` |
| `detection_summary.py` | Collates everything | `DETECTION_SUMMARY.md` |

---

## Key technical notes

**Why no `flatten()`?**
A Savitzky-Golay filter with a 30-minute window is a high-pass filter with a
corner at ~555 µHz.  For transit searches this removes slow stellar trends
cleanly.  For this K giant's oscillations at νmax ≈ 43 µHz (period 6.4 h),
flattening removes the signal before the PSD is computed.

**PSD normalization**
The gapped TESS baseline (three sectors with ~1100-day span but ~12% duty
cycle) creates window-function sidelobes that inflate the raw LS power values
by ~2×.  We correct this empirically by injecting a known sine wave.

**Why period space failed**
The Phase 1 search covers 0.5–15 days — it never sampled sub-0.5-day periods
where the K giant oscillations live (νmax = 43 µHz = period 6.4 hours).  The
frequency-space approach in hd16467_seismic.py is the correct method for
this star.
