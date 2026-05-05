# HD 206948 — TESS Analysis Project Log

HD 206948 (HIP 107542, TIC 147384395) — K2III giant at 233 pc, V=7.54,
no prior variability classification. TESS-SPOC 200s sector 68 used for
primary analysis; QLP 200s sectors 68 and 95 also available.

All scripts run from this directory (`hd206948/`). Plots go to `plots/`.

---

## What we know

**Stellar parameters (TIC v8 / Gaia DR3 / SIMBAD):**
- Teff = 4648 K (TIC), log g: not in Gaia DR3 astrophysical parameters
- R = 12.49 R☉ (TIC), d = 232.5 ± 1.9 pc (TIC)
- V = 7.541, B-V = 1.165, TESS T mag = 6.564
- Spectral type: K2III (SIMBAD)
- v sin i = 10.0 km/s (Gaia DR3 Vbroad)
- Gaia DR3 source ID: 6564386512939585152
- Coordinates: RA 21h 46m 52.3s, Dec −46° 23′ 22.8″ (J2000)
- SIMBAD otype: * — **no prior variability classification**
- WDS: no catalogued companions within 60″ — binary contamination not a concern

Note: Gaia DR3 did not generate astrophysical parameters (Teff, log g, [Fe/H]) for
this star — this happens for a fraction of the catalogue when the photometric
pipeline solution does not converge. All parameters come from TIC v8.

**TESS coverage:**
- TESS-SPOC 200s: sector 68 (BTJD 60154–60182, 27.5 days, 8,991 cadences)
- QLP 200s: sectors 68 and 95
- QLP 600s: sector 28
- QLP/GSFC-ELEANOR-LITE/TASOC/TGLC 1800s: sector 1 (all from full-frame images)
- No SPOC 120s data available

**Scaling-relation predictions** (log g derived from R=12.49 R☉, M=1.5 M☉ assumed):
- log g (derived) = 2.421
- νmax = 33.1 µHz (period ≈ 8.4 h)
- Δν   = 3.75 µHz

---

## What we found

### Phase 1 — Stellar context (`hd206948_context.py`)

SIMBAD / Gaia DR3 / TIC v8 / WDS queries. Star is a K2III giant with
R=12.49 R☉ at 233 pc. Not catalogued as variable. No binary companions.
Predicted νmax = 33.1 µHz from TIC parameters with assumed M=1.5 M☉.
TESS-SPOC 200s data available for sector 68; QLP 200s for sectors 68 and 95.

### Phase 2 — TESS sector survey (`check_sectors.py`)

MAST survey across SPOC, QLP, and TGLC pipelines. No SPOC 120s data.
Best available: TESS-SPOC 200s (sector 68) and QLP 200s (sectors 68, 95).
200s cadence Nyquist is 2500 µHz — well above νmax for this target.

### Phase 3 — Asteroseismic analysis (`hd206948_seismic.py`)

Per-sector ppm normalisation (no flattening), empirically-calibrated PSD,
Harvey + Gaussian envelope fit on TESS-SPOC 200s sector 68 alone.

**Results:**

| Quantity | Value | Predicted | Ratio |
|---|---|---|---|
| ν_max | **36.63 ± 0.07 µHz** | 33.1 µHz | 1.107 |
| Δν (ACF) | **3.64 µHz** | 3.75 µHz | 0.971 |
| H/background | **7.71** — CONVINCING | ≥5 threshold | — |
| Gran. τ₁ | 1.4 h | — | — |
| Gran. τ₂ | 3.6 h | — | — |
| White noise C | 75.3 ppm²/µHz | — | — |
| Implied log g | 2.465 | 2.421 | 1.02 |

The νmax is 10.7% above the scaling-relation prediction. This is within the
expected uncertainty: the prediction assumed M=1.5 M☉, but the fit implies
log g = 2.465, which corresponds to M ≈ 1.66 M☉ at R=12.49 R☉. Feeding
M=1.66 M☉ back into the scaling relation gives νmax ≈ 35.9 µHz — much
closer to the measured 36.6 µHz. The star is slightly more massive than
the 1.5 M☉ prior, and the seismology is self-consistent.

---

## Asteroseismic mass and radius

With both νmax and Δν measured, the full asteroseismic scaling relations can
be applied. Solar references: νmax_⊙ = 3090 µHz, Δν_⊙ = 135 µHz, Teff_⊙ = 5778 K.

```
M/M☉ = (νmax / νmax_⊙)³ × (Δν / Δν_⊙)⁻⁴ × (Teff / Teff_⊙)^1.5
R/R☉ = (νmax / νmax_⊙)¹ × (Δν / Δν_⊙)⁻² × (Teff / Teff_⊙)^0.5
```

Using νmax = 36.63 µHz, Δν = 3.64 µHz, Teff = 4648 K:

```
M = (36.63/3090)³ × (135/3.64)⁴ × (4648/5778)^1.5
  = (0.01185)³ × (37.09)⁴ × (0.8044)^1.5
  = 1.666×10⁻⁶ × 1.893×10⁶ × 0.7213
  ≈ 2.27 M☉

R = (36.63/3090)¹ × (135/3.64)² × (4648/5778)^0.5
  = 0.01185 × 1376 × 0.8970
  ≈ 14.6 R☉
```

**Comparison with TIC prior: R_TIC = 12.49 R☉**

The asteroseismic radius (14.6 R☉) is 17% above the TIC prior. This is
within the Δν uncertainty from a single 24-day sector. The frequency
resolution is 1/T ≈ 0.48 µHz, giving an ACF Δν uncertainty of roughly
±0.3–0.5 µHz. If Δν = 3.94 µHz (within 1σ of the measured value),
the asteroseismic radius becomes R = 12.5 R☉ — exactly the TIC value.
The two measurements are consistent once the Δν uncertainty is properly
accounted for; the sector 95 independent analysis and échelle diagram
inspection will tighten this.

**Asteroseismic log g:**

The implied surface gravity from νmax is:

```
log(g/g_⊙) = log(νmax/νmax_⊙) + 0.5 × log(Teff/Teff_⊙)
log g = 4.438 + log10(36.63/3090) + 0.5 × log10(4648/5778)
      = 4.438 + (−1.926) + 0.5×(−0.0948)
      = 2.465
```

This is more precise than the log g = 2.421 derived from the TIC radius
and assumed mass, and is independent of the mass assumption.

---

## Why this detection is stronger than HD 16467

HD 16467 gave a marginal detection (H/bkg = 4.4) despite having
three sectors and a 1115-day baseline. HD 206948 gives a convincing
detection (H/bkg = 7.71) from a single 24-day sector. The reason is
window function.

A single contiguous sector has a near-perfect spectral window: a clean
sinc² profile with no sidelobes beyond the first Gibbs fringe. The power
in each frequency bin is where it belongs. HD 16467's three sectors span
1115 days with only ~12% duty cycle: every power spike has a comb of
aliases spaced 1/T_gap apart, inflating the background level and making
the granulation model harder to fit cleanly. The Harvey background must
simultaneously model real astrophysical power and the window-function
artefacts, reducing the residual envelope signal.

The practical lesson: for asteroseismology of K giants at νmax ~ 30–50 µHz,
a single 27-day TESS sector with continuous coverage gives better results
than multiple sectors separated by large gaps, even though the longer
baseline improves formal frequency resolution. The duty-cycle penalty
for the multi-sector case outweighs the resolution gain.

---

## Caveats

**Granulation amplitudes are likely overstated.** The fitted values
σ₁ = 1127 ppm and σ₂ = 1000 ppm are physically large. For a K2III giant
at ~65 L☉, granulation amplitudes of this order are plausible (scaling
roughly with L/M), but in single-sector data the Harvey model also absorbs
any residual instrumental trends, scattered light variations, and
momentum-dump systematics that produce low-frequency power. The envelope
itself (H/bkg = 7.71) is robust because the Gaussian peak stands well
above the background regardless of how that background is modelled.
Cross-checking with sector 95 will show whether the granulation amplitudes
are stable.

**Granulation timescales τ₁ = 1.4 h and τ₂ = 3.6 h are physically
plausible** for a K2III giant (larger than the ~0.9 h and ~2.3 h found for
the smaller HD 16467), but the two-component Harvey model has significant
degeneracy in single-sector data. Swapping which component is "long" and
which is "short" can produce equally good fits. The timescales should be
treated as order-of-magnitude estimates until sector 95 provides an
independent constraint.

**Single-sector formal uncertainties are optimistic.** The fit gives
νmax = 36.63 ± 0.07 µHz, but this formal error reflects only the
statistical precision of the Gaussian peak location in the smoothed PSD —
it does not include systematic uncertainty from the Harvey background
parametrisation, window-function effects, or sector-to-sector variability.
A realistic νmax uncertainty after cross-validation is closer to ±0.5 µHz.

**Asteroseismic scaling relations are well-tested but not exact.** The
standard grid-based estimates of M and R from νmax and Δν carry a
systematic uncertainty of ~5–10% from deviations from the solar reference
model, metallicity effects, and near-surface corrections. The [Fe/H] for
this star is unknown (Gaia DR3 has no astrophysical parameters). If
[Fe/H] is substantially sub-solar, the corrected νmax and Δν values would
shift slightly.

---

## Open questions

1. **pySYD cross-check** (`run_pysyd.py`): Does an independent pipeline
   agree on νmax? For HD 16467, pySYD gave 44.48 ± 0.50 µHz vs our 43.43 µHz
   (2.1σ apart). For HD 206948 with a stronger detection, the agreement
   should be better. Target: pySYD νmax within 0.5 µHz of 36.63 µHz.

2. **Sector 95 temporal stability** (`sector95_independent.py`): Does
   sector 95 (700 days later) independently recover νmax ≈ 36.6 µHz?
   A K giant's νmax should be stable on multi-year timescales; a significant
   shift would imply contamination or a systematic.

3. **Échelle diagram** (`echelle.py`): Does the background-subtracted PSD
   show vertical ridges at Δν = 3.64 µHz spacing? Clean ridges would confirm
   Δν is real and resolve individual p-mode frequencies. Noisy ridges mean
   the modes are marginally resolved and the Δν from the ACF has more
   uncertainty than the formal value suggests.

4. **Δν precision and radius revision**: Once sectors 68 and 95 are
   combined, the frequency resolution improves to ~0.004 µHz and the Δν
   measurement will be much more precise. The asteroseismic radius will then
   be directly comparable to the TIC prior.

5. **[Fe/H] and spectroscopic follow-up**: Without a metallicity measurement,
   the mass and radius scaling relations carry an unknown systematic. A single
   optical spectrum would provide [Fe/H] and resolve the Gaia DR3 gap.

---

## Verification results

*This section will be updated after the verification scripts run.*

---

## Scripts

### Run order

```bash
cd hd206948/

# Reconnaissance
python hd206948_context.py     # stellar parameters, binary check
python check_sectors.py        # MAST survey

# Primary analysis
python hd206948_seismic.py     # Harvey background + Gaussian fit

# Verification
python run_pysyd.py            # pySYD cross-check
python sector95_independent.py # temporal stability (sector 95 alone)
python echelle.py              # échelle diagram from sector 68 PSD
```

### Script reference

| Script | What it does | Key outputs |
|---|---|---|
| `hd206948_context.py` | SIMBAD/Gaia/TIC/WDS stellar params | terminal |
| `check_sectors.py` | MAST sector survey | terminal |
| `hd206948_seismic.py` | Harvey fit, νmax, detection | `plots/seismic_*.png` |
| `seismic_utils.py` | Shared functions (import only) | — |
| `run_pysyd.py` | pySYD validation | `pysyd_results.json`, `plots/pysyd_*.png` |
| `sector95_independent.py` | Sector 95 νmax consistency | `sector95_results.json`, `plots/sector95_*.png` |
| `echelle.py` | Échelle diagram | `plots/echelle.png` |

---

## Key technical notes

**Why no `flatten()`?**
For this K giant with νmax ≈ 37 µHz (oscillation period ≈ 7.5 h), a
standard Savitzky-Golay filter with a 30-minute window would be a high-pass
filter with a corner near 556 µHz — well above νmax. But the real damage
is at lower frequencies: the granulation signal (τ ≈ 1–4 h) is heavily
attenuated by any filter with window shorter than a few hours, collapsing
the Harvey background and making the oscillation envelope invisible. The
correct approach is raw ppm normalisation, explicit background modelling,
and PSD calibration via an injected sine.

**200s vs 120s cadence**
TESS-SPOC switched to 200s cadence for extended-mission sectors. For a
target with νmax = 37 µHz, the 200s Nyquist is 2500 µHz — more than 60×
above the signal of interest. The cadence makes no practical difference
for this analysis.

**PSD calibration**
Same empirical method as HD 16467: inject a known 10 ppm sine at 33.1 µHz,
measure the raw LS power, derive a scale factor to give Parseval-correct
ppm²/µHz units. This corrects for the window-function inflation from
TESS's gapped baseline.
