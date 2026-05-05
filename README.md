# TESS Lightcurve Analysis

Amateur asteroseismology and exoplanet analysis using publicly available
TESS photometry from the MAST archive.

## Stars analysed

| Star | Directory | Result |
|---|---|---|
| **Pi Mensae** (HD 39091) | [`pi_mensae/`](pi_mensae/) | Reproduced transit detection of Pi Men c — period 6.266 days, consistent with published value 6.27 d (Huang et al. 2018) |
| **Epsilon Eridani** (HD 22049) | [`eps_eridani/`](eps_eridani/) | Stellar rotation period 11.18 days from starspot modulation — consistent with literature value 11.2 ± 0.1 d |
| **HD 16467** (K0III giant) | [`hd16467/`](hd16467/) | Solar-like oscillation detection: **ν_max = 43.5 ± 1.0 µHz**, three independent methods agreeing, consistent with the K0III scaling-relation prediction to within 0.5% |
| **HD 206948** (K2III giant) | [`hd206948/`](hd206948/) | Solar-like oscillation detection: **ν_max = 36.63 ± 0.07 µHz**, CONVINCING detection (H/bkg = 7.71), single TESS-SPOC 200s sector |

The HD 206948 result is the strongest detection so far (H/bkg = 7.71 vs 4.4 for HD 16467).
See [`hd206948/README.md`](hd206948/README.md) for the full analysis.
The HD 16467 result is more thoroughly verified — see
[`hd16467/README.md`](hd16467/README.md) for the full project log and
[`hd16467/DETECTION_SUMMARY.md`](hd16467/DETECTION_SUMMARY.md) for the
formatted results including a draft VSX submission entry.

## How this project developed

It started as a transit search. The first script (`pi_mensae/pi_mensae.py`) reproduces
the Pi Mensae c transit using a standard BLS periodogram on a flattened
lightcurve — the textbook approach. The second script (`eps_eridani/epsilon_eridani.py`)
extends the method to rotation period detection.

The third target, HD 16467, was initially assumed to be an F-type dwarf. The
reconnaissance script found a null result in 0.5–15 day period space, which
looked like a dead end. Querying stellar catalogs revealed the truth: HD 16467
is a **K0III red giant** (Teff = 4966 K, log g = 2.55, R = 10.5 R☉). For a
giant, solar-like oscillations are expected at νmax ≈ 43 µHz — a 6.4-hour
period, well below the 12-hour floor of the period-space search, and on a
timescale that the flattening filter actively removes.

This forced a methodological pivot from period space to frequency space, from
BLS/LS periodograms to power spectral density analysis, and from simple peak
finding to fitting a physical background model (Harvey granulation + Gaussian
oscillation envelope). The result is a marginal but physically consistent
detection of solar-like oscillations in an ~131 pc K giant using three TESS
sectors of 120-second cadence photometry.

## Main result

```
HD 16467 (TIC 422971931, K0III, d=131 pc)
ν_max  =  43.5 ± 1.0 µHz  (predicted: 43.3 µHz from Gaia DR3 log g and Teff)
Ratio  =  1.004             (0.4% agreement with scaling relation)
Method =  Harvey background + Gaussian envelope fit, cross-checked with pySYD
          and split-half validation
Status =  MARGINAL detection (H/background = 4.4)
          — consistent across all three independent analyses
          — limited by duty cycle (3-year gap between Sector 31 and Sectors 70–71)
          — additional TESS sectors needed for a convincing detection
```

## Setup

```bash
git clone https://github.com/engantor/tess-analysis.git
cd tess-analysis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**pySYD note**: pySYD 6.10.5 has two compatibility bugs with Python 3.14 in
`target.py` (both in `frequency_spacing()`). If you're on Python 3.14, apply
these patches to your installed copy:

1. Line ~1752: `pl.pop(idx)` → `pl.pop(idx if idx is not None else -1)`
2. Same line: also guard against empty list with `if pl and pa:` around the pop

These are one-line fixes — see `hd16467/README.md` for details.

## Running the scripts

All scripts are run from their own subdirectory. Output plots go to
`<subdir>/plots/`.

```bash
source venv/bin/activate

# Pi Mensae transit detection
cd pi_mensae/
python pi_mensae.py

# Epsilon Eridani rotation period
cd eps_eridani/
python epsilon_eridani.py

# HD 16467 — run from the subdirectory
cd hd16467/
python hd16467.py            # reconnaissance
python hd16467_context.py    # stellar parameters
python hd16467_pulsations.py # extended frequency search
python hd16467_seismic.py    # asteroseismic analysis
python check_new_sectors.py  # MAST survey
python run_pysyd.py          # pySYD validation
python split_half_validation.py
python detection_summary.py  # generates DETECTION_SUMMARY.md

# HD 206948 — run from the subdirectory
cd hd206948/
python hd206948_context.py   # stellar parameters
python check_sectors.py      # MAST survey
python hd206948_seismic.py   # asteroseismic analysis
python run_pysyd.py          # pySYD validation
python sector95_independent.py  # temporal stability check
python echelle.py            # échelle diagram
```

---

## Pi Mensae — Transit detection

Full documentation in [`pi_mensae/`](pi_mensae/).

Detects the transiting super-Earth **Pi Mensae c** (period ≈ 6.27 days) using
TESS SPOC photometry from the MAST archive.

**Result:** Period at maximum BLS power = **6.266 days** (expected ~6.27 d).
Phase-folded lightcurve shows the classic flat-bottomed transit dip near phase 0.

---

## Epsilon Eridani — Rotation period

Full documentation in [`eps_eridani/`](eps_eridani/).

Measures the **stellar rotation period** of Epsilon Eridani (~11.2 days) from
starspot modulation using a Lomb-Scargle periodogram on three stitched SPOC sectors.

**Result:** Period = **11.178 days** (published value: 11.2 ± 0.1 d,
Fröhlich et al. 2007). Phase-folded lightcurve shows clean sinusoidal modulation.

---

## HD 16467 — Solar-like oscillations (marginal)

Full documentation in [`hd16467/`](hd16467/).

**Background:** HD 16467 (HR 775, HIP 12318, TIC 422971931) is a K0III giant at
131 pc with a visual companion 0.9" away (ΔV = 4 mag, 2.4% flux contamination).
Stellar parameters from Gaia DR3: Teff = 4966 K, log g = 2.551, [Fe/H] = −0.30.
TIC v8: R = 10.5 R☉. Scaling-relation predictions: νmax = 43.3 µHz, Δν = 4.8 µHz.

**Development arc (8 scripts, 4 phases):**

1. *Reconnaissance* — BLS + Lomb-Scargle in period space. Null result; star is
   photometrically quiet at 0.14% amplitude in the 0.5–15 day range.
2. *Stellar context* — Catalog queries reveal the K0III classification, ruling
   out eclipse/rotation as the variability mechanism and predicting νmax = 43 µHz
   in the oscillation regime that the period-space search couldn't reach.
3. *Extended frequency search* — Wide LS periodogram 1–1000 µHz. Five peaks at
   3.8–14 µHz detected at SNR 62–68, below the p-mode envelope — consistent
   with g-mode/mixed-mode variability.
4. *Asteroseismic analysis* — Harvey background model fit to calibrated PSD,
   followed by pySYD and split-half validation.

**Key result:**

| Quantity | Value | Predicted | Source |
|---|---|---|---|
| ν_max | 43.43 ± 0.10 µHz | 43.3 µHz | Harvey fit |
| ν_max | 44.48 ± 0.50 µHz | 43.3 µHz | pySYD |
| ν_max (Sector 31) | 42.55 ± 0.26 µHz | 43.3 µHz | split-half |
| ν_max (Sec 70+71) | 43.45 ± 0.13 µHz | 43.3 µHz | split-half |
| Δν | not reliable | 4.8 µHz | — |
| Detection | MARGINAL (H/bkg = 4.4) | — | — |
| Gran. τ₁ | 2.3 h | — | Harvey fit |
| Gran. τ₂ | 0.9 h | — | Harvey fit |

---

## HD 206948 — Solar-like oscillations (convincing)

Full documentation in [`hd206948/`](hd206948/).

**Background:** HD 206948 (HIP 107542, TIC 147384395) is a K2III giant at 233 pc,
V=7.5, with no prior variability classification. TESS-SPOC 200s photometry is
available for sector 68; QLP 200s for sectors 68 and 95.

**Result:** CONVINCING detection (H/bkg = 7.71) from a single 24-day sector.

| Quantity | Value | Predicted |
|---|---|---|
| ν_max | **36.63 ± 0.07 µHz** | 33.1 µHz |
| Δν | **3.64 µHz** | 3.75 µHz |
| Detection | CONVINCING (H/bkg = 7.71) | — |
| Gran. τ₁ | 1.4 h | — |
| Gran. τ₂ | 3.6 h | — |

---

## Why `flatten()` is wrong for asteroseismology

The BLS/LS approach uses `lc.flatten(window_length=901)` — a Savitzky-Golay
high-pass filter. For transit searches this suppresses stellar trends correctly.
For a K giant with νmax = 43 µHz (period 6.4 h), a 30-minute filter window
removes almost all the granulation power (τ₁ ≈ 2.3 h) and attenuates the
oscillation envelope directly. The correct approach is no flattening: convert
to ppm, fit the background model explicitly, and calibrate the PSD via an
injected reference signal to correct for window-function inflation from TESS's
gapped multi-sector baseline.

---

## Acknowledgements

- **lightkurve** (Lightkurve Collaboration 2018, AJ 156 132) — TESS/Kepler
  data access via the MAST archive
- **astropy** (Astropy Collaboration 2013, 2018, 2022) — PSD computation,
  coordinate handling, sigma clipping
- **astroquery** (Ginsburg et al. 2019) — SIMBAD, Gaia DR3, TIC, WDS catalog
  queries
- **pySYD** (Chontos et al. 2021, arXiv:2108.00582) — independent asteroseismic
  pipeline for cross-validation
- **TESS mission** (Ricker et al. 2015) — photometry collected by NASA's
  Transiting Exoplanet Survey Satellite
- **MAST** (Mikulski Archive for Space Telescopes) — public data hosting
- **Gaia DR3** (Gaia Collaboration 2023) — stellar parameters (Teff, log g,
  [Fe/H], parallax)
- **TIC v8** (Stassun et al. 2019) — stellar radii, luminosity classes
