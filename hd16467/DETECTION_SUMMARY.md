# HD 16467 — Asteroseismic Detection Summary

Generated: 2026-05-04

---

## Identifiers

| Catalogue | Identifier |
|---|---|
| HD | HD 16467 |
| HIP | HIP 12318 |
| HR | HR 775 |
| TIC | 422971931 |
| Gaia DR3 source | 2503654874857069440 |
| WDS | J02386+0327 (KUI 9 AB) |

---

## Coordinates (J2000, Gaia DR3)

| | Value |
|---|---|
| RA | 39.653490° |
| Dec | 3.443235° |
| Distance | 130.9 pc |
| Parallax | 7.5374 ± 0.0337 mas |

---

## Stellar Parameters

| Parameter | Value | Source |
|---|---|---|
| Spectral type | K0III | SIMBAD |
| V magnitude | 6.24 | SIMBAD |
| TESS T mag | 5.375 | TIC v8 |
| Teff | 4966 K | Gaia DR3 |
| log g | 2.551 | Gaia DR3 |
| [Fe/H] | -0.298 | Gaia DR3 |
| Radius | 10.52 R☉ | TIC v8 |
| Luminosity class | GIANT | TIC v8 |
| E(B−V) | 0.0151 | TIC v8 |

---

## TESS Observations

| Parameter | Value |
|---|---|
| Sectors used | [31, 70, 71] (SPOC 120-second cadence) |
| Total cadences | 47,095 |
| Time baseline | 1114.9 days |
| Duty cycle | 5.9% |
| Flux rms | 434.9 ppm |

---

## Method

**Primary: Harvey background + Gaussian oscillation envelope fit** to the
empirically-calibrated power spectral density (PSD).

1. Per-sector flux normalization to ppm (no flattening — flattening would
   suppress the granulation and oscillation signals).
2. 5σ outlier clipping per sector.
3. PSD computed via astropy LombScargle with `normalization='psd'`, then
   calibrated by injecting a known sine wave (A = 10 ppm at 43 µHz) and
   scaling to the theoretically-expected Parseval peak. This corrects for
   window-function inflation from the gapped TESS baseline.
4. Smooth PSD (50-bin uniform filter) fit with:
   `P(ν) = Harvey₁(σ₁,τ₁) + Harvey₂(σ₂,τ₂) + H·exp[−½((ν−νmax)/σenv)²] + C`
   in log₁₀-power space using scipy.optimize.curve_fit (TRF algorithm).
5. Detection significance: H / (gran₁ + gran₂ + C) at νmax.

**Verification: pySYD** (Python SYD pipeline; Chontos et al. 2021)

pySYD v6.10.5 ran successfully.
ν_max = 44.48456674 ± 0.5002146510038383 µHz
Δν    = 1.133632500000001 ± 0.0 µHz

---

## Results

### Oscillation envelope

| Quantity | Value | Predicted | Ratio |
|---|---|---|---|
| ν_max | **43.48 ± 0.10 µHz** | 43.3 µHz | 1.004 |
| Δν | 1.13 ± 0.00 µHz (pySYD) | 4.8 µHz | — |
| Envelope height H | 18576 ppm²/µHz | — | — |
| Envelope width σ_env | 6.45 µHz | — | — |
| H / background | 4.40 | — | — |
| **Detection status** | **MARGINAL** | — | — |

*ν_max combined from: Harvey fit: 43.44±0.10 µHz + pySYD: 44.48±0.50 µHz*

### Granulation background

| Component | Amplitude σ (ppm) | Timescale τ |
|---|---|---|
| Gran 1 (deep convection) | 1389 | 8440 s (2.3 h) |
| Gran 2 (mesogranulation) | 784 | 3189 s (0.9 h) |
| White noise C | — | 47.39 ppm²/µHz |

Granulation timescales are consistent with expectations for a K giant
(τ ∼ hours, vs ∼ 5 minutes for the Sun): the star's large radius and low
surface gravity produce correspondingly large, slow convection cells.

---

## Comparison to Scaling Relations

Solar reference values: νmax,⊙ = 3090 µHz, Δν⊙ = 135 µHz, log g⊙ = 4.438,
Teff,⊙ = 5778 K.

```
Predicted νmax = νmax,⊙ × (g/g⊙) × (Teff,⊙/Teff)^0.5
             = 3090 × 10^(2.551−4.438) × (5778/4966)^0.5
             = 3090 × 0.01295 × 1.079
             = 43.3 µHz

Measured νmax = 43.48 ± 0.10 µHz
Ratio         = 1.004  (within 0.4%)
```

The measured ν_max is in excellent agreement with the scaling-relation
prediction based on independently-measured Gaia DR3 log g and Teff.

---

## Split-Half Consistency Check

Sector 31 alone: ν_max = 42.55 ± 0.26 µHz  (MARGINAL)
Sectors 70+71: ν_max = 43.45 ± 0.13 µHz  (MARGINAL)
Difference: 0.90 µHz = 3.1σ — MARGINAL INCONSISTENCY — warrants caution

---

## Binary Contamination Assessment

HD 16467 is a visual double (WDS J02386+0327, KUI 9 AB):
- Companion separation: 0.80–0.90 arcsec (orbital motion confirmed between 1937 and 2009)
- Component magnitudes: A = 6.35, B = 10.38 (ΔV = 4.03 mag)
- Companion B flux fraction: ~2.4% of total light

**TESS pixels are 21 arcsec wide** — both components are unresolved.
However, the 2.4% contamination from the companion is negligible for
the amplitude measurements. The asteroseismic signature is attributed
to the primary (K0III) based on:

1. ν_max = 43.5 µHz matches the K0III scaling-relation prediction
   (log g = 2.551, Teff = 4966 K) to within 0.4%.
2. Granulation timescales (τ₁ = 2.3 h, τ₂ = 0.9 h) are
   consistent with giant-branch convection, inconsistent with a dwarf companion.
3. The companion's predicted ν_max (~500–3000 µHz for a main-sequence dwarf)
   is well outside the detected frequency range, and its flux contribution
   is too small to produce detectable oscillations at the observed amplitude.

---

## Variability Classification

**SOLAR_OSC** — Solar-like oscillations on the red giant branch.

The photometric variability of HD 16467 is dominated by:
- Stochastic p-mode (pressure-mode) oscillations, driven by near-surface
  convection, centred at ν_max ≈ 43.5 µHz (period ≈ 6.4 hours).
- Two granulation components with timescales of 2.3 h and 0.9 h.

Peak-to-trough flux amplitude in the TESS bandpass: ~0.14%
(5th–95th percentile of the raw lightcurve).

---

## VSX Remarks Field (draft)

K0III giant (Teff=4966 K, log g=2.55, R≈10.5 R☉, d≈131 pc; Gaia DR3).
Solar-like oscillations detected in TESS SPOC photometry (Sectors 31, 70,
71; 1115-day baseline). Harvey + Gaussian envelope fit to the calibrated PSD
gives ν_max = 43.48 ± 0.10 µHz, consistent with the scaling-
relation prediction of 43.3 µHz (ratio 1.004). Granulation
background (τ₁ = 2.3 h, τ₂ = 0.9 h) consistent with giant
convection. Detection significance H/background = 4.40 (MARGINAL;
additional sectors would confirm). Visual binary companion (0.9", ΔV=4 mag,
2.4% flux) contributes negligible contamination. Δν not reliably measured
from current data.

---

## Caveats and Open Questions

1. **Detection is MARGINAL** (H/bkg = 4.40). The three available SPOC
   sectors have a low duty cycle (~5.9%) due to the 3-year gap
   between Sector 31 (2020) and Sectors 70–71 (2023). Window-function
   sidelobes from this gap dilute the envelope measurement. Additional
   consecutive TESS sectors would push the detection to CONVINCING.

2. **Δν is not reliably measured**. At MARGINAL significance the individual
   p-mode peaks are unresolved in the PSD, so the ACF Δν search is
   unreliable. pySYD's four-degree-of-freedom background fit may do better,
   but a clean Δν measurement likely requires more data.

3. **Mass and radius via asteroseismology** cannot be computed without a
   reliable Δν. With ν_max alone and the log g prior from Gaia, the stellar
   radius is self-consistently constrained to R ≈ 10–11 R☉ — consistent
   with the TIC value of 10.5 R☉.

4. **Which component varies?** Both stars are blended in TESS. The attribution
   to the K0III primary is robust (ν_max matches K giant prediction, not a
   dwarf), but high-resolution spectroscopy could confirm by measuring
   radial-velocity oscillations.
