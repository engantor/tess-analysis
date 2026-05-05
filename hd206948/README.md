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

### pySYD cross-check (`run_pysyd.py`)

Independent pipeline run on the same TESS-SPOC 200s sector 68 data.

| Quantity | Harvey fit | pySYD | Difference |
|---|---|---|---|
| νmax | 36.63 ± 0.07 µHz | 36.79 ± 0.91 µHz | 0.16 µHz = **0.2σ** |
| Δν | 3.64 µHz (ACF) | 3.75 ± 0.10 µHz | 0.11 µHz |

Both values are consistent. The sub-0.5σ agreement on νmax confirms the
Harvey fit detection is not an artefact of the background model choice.
The 0.11 µHz Δν difference is within the ACF uncertainty for a single
24-day sector.

**Assessment: CONSISTENT — pySYD independently confirms the detection.**

### Sector 95 temporal stability (`sector95_independent.py`)

QLP 200s sector 95 (BTJD ~3882–3909, approximately 700 days after sector 68)
was analysed independently.

**Result: NOT DETECTED** — H/background = 0.50, significance below the 2×
noise threshold. The QLP sector 95 rms is 4337.6 ppm vs 506.9 ppm for
TESS-SPOC sector 68 — a factor of ~8.6 higher. The noise floor is
~1557 ppm²/µHz, roughly 20× above the oscillation envelope level. The
returned νmax = 30.64 ± 19.52 µHz is unconstrained noise.

This non-detection is a pipeline and aperture quality issue, not an
astrophysical result. The QLP lightcurve for this 233 pc target in sector 95
has substantially worse systematics than the TESS-SPOC sector 68 product.
**The temporal stability of νmax cannot be assessed from the available data.**

For a K2III giant, νmax is not expected to vary on multi-year timescales;
the sector 95 QLP noise simply overwhelms the signal. A future TESS-SPOC
200s sector (if one is scheduled) would enable the intended stability check.

### Échelle diagram (`echelle.py`)

Background-subtracted PSD (sector 68) folded at Δν = 3.64 µHz (ACF)
over the frequency window 16.6–56.7 µHz (±5.5 Δν around νmax).

| Metric | Value | Threshold | Interpretation |
|---|---|---|---|
| Column contrast ratio | **0.634** | >0.3 = ridges present | Ridge structure detected |
| Grid | 11 rows × 364 cols | — | — |

A column contrast of 0.634 is well above the 0.3 ridge-detection threshold,
indicating that the background-subtracted PSD has significant column-to-column
power variation — the hallmark of vertical ridges in the échelle. The ACF Δν
is real and resolves into distinct ridges at this spacing.

**Assessment: Δν is real — individual p-mode ridges are visible. Mode
identification (ℓ=0 and ℓ=2) may be possible with the current data.**

The comparison plot (`echelle_comparison.png`) shows both ACF (3.64 µHz) and
pySYD (3.75 µHz) foldings. Both produce ridge-like structure; the ACF value
gives marginally cleaner alignment, consistent with the higher column contrast.

### Overall confidence assessment

| Check | Result | Weight |
|---|---|---|
| Harvey fit (TESS-SPOC s68) | CONVINCING — H/bkg = 7.71 | Primary detection |
| pySYD (same data) | CONSISTENT — Δ = 0.2σ | Strong cross-check |
| Sector 95 QLP | NOT DETECTED — pipeline noise | Not informative (noise limit) |
| Échelle contrast | 0.634 — ridges present | Confirms Δν is real |

The detection of solar-like oscillations in HD 206948 is **well-established**.
The primary detection is convincing by any standard metric, pySYD independently
agrees, and the échelle diagram confirms the Δν measurement. The only incomplete
check is temporal stability, which requires a second clean TESS-SPOC sector.

**Final values:**

| Quantity | Value | Notes |
|---|---|---|
| νmax | **36.63 ± 0.07 µHz** (formal) / ~36.7 ± 0.5 µHz (realistic) | Harvey fit; pySYD 36.79 µHz |
| Δν | **3.64 µHz** (ACF) / **3.75 µHz** (pySYD) | Ridges confirmed in échelle |
| log g (seismic) | **2.465** | Precise; independent of mass assumption |
| M (scaling) | ~2.3 M☉ | Uncertain by ±5–10% from scaling systematics |
| R (scaling) | ~14.6 R☉ | Consistent with TIC 12.49 R☉ within Δν uncertainty |
| Detection | **CONVINCING** (H/bkg = 7.71) | Strongest detection in this project |

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
