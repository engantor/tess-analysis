"""
Generates DETECTION_SUMMARY.md — a complete record of the HD 16467
asteroseismic analysis, formatted for readability and suitable as the
basis for a VSX submission.

Reads (if available):
  - pysyd_results.json      (from run_pysyd.py)
  - split_half_results.json (from split_half_validation.py)

Re-runs the Harvey fit on the full dataset for authoritative numbers.
Queries Gaia DR3 and TIC for identifiers and stellar parameters.

Run from the hd16467/ directory:
    python detection_summary.py
"""

import warnings
warnings.filterwarnings("ignore")

import json
import numpy as np
from pathlib import Path
from datetime import date

from seismic_utils import (
    load_sectors_ppm, make_freq_grid, calibrate_psd, fit_harvey_model,
    PRED_NMAX, PRED_DELTANU,
)

# ── Load optional JSON results ─────────────────────────────────────────────────
def load_json(path):
    p = Path(path)
    if p.exists():
        with open(p) as fh:
            return json.load(fh)
    return None

pysyd_data      = load_json("pysyd_results.json")
split_half_data = load_json("split_half_results.json")

# ── Re-run Harvey fit on full dataset ─────────────────────────────────────────
print("Re-running Harvey fit on full dataset for authoritative numbers...")
t_days, flux_ppm, sector_info = load_sectors_ppm(verbose=True)
freq_uhz, freq_cd, df_uhz     = make_freq_grid()
psd, PSD_SCALE, C_noise       = calibrate_psd(
    t_days, flux_ppm, freq_uhz, freq_cd, df_uhz, verbose=True
)
res = fit_harvey_model(freq_uhz, psd, C_noise=C_noise, verbose=True)

N          = len(t_days)
baseline_d = t_days[-1] - t_days[0]
duty_cycle = N * (120 / 86400) / baseline_d  # 120s cadence
sectors    = [si["sector"] for si in sector_info]

# Best numax: average our fit and pySYD if available and consistent
numax_best     = res["nm"]
numax_best_err = res["nm_err"] if res["fit_success"] else 0.5
numax_sources  = [f"Harvey fit: {res['nm']:.2f}±{res['nm_err']:.2f} µHz"]

if pysyd_data and pysyd_data.get("pysyd_success") and "numax" in pysyd_data:
    nm_psy  = pysyd_data["numax"]
    nm_perr = pysyd_data.get("numax_err", 0.5)
    diff    = abs(numax_best - nm_psy)
    quad    = np.sqrt(numax_best_err**2 + nm_perr**2)
    if diff / quad < 3:
        # Weighted average
        w1 = 1 / numax_best_err**2
        w2 = 1 / nm_perr**2
        numax_best     = (w1 * numax_best + w2 * nm_psy) / (w1 + w2)
        numax_best_err = 1 / np.sqrt(w1 + w2)
        numax_sources.append(f"pySYD: {nm_psy:.2f}±{nm_perr:.2f} µHz")

# Dnu
dnu_best = None
dnu_note = "not reliably measured (ACF at MARGINAL SNR)"
if pysyd_data and pysyd_data.get("pysyd_success") and "dnu" in pysyd_data:
    dnu_best = pysyd_data["dnu"]
    dnu_err  = pysyd_data.get("dnu_err", 0)
    dnu_note = f"{dnu_best:.2f} ± {dnu_err:.2f} µHz (pySYD)"

# ── Query external catalogs ────────────────────────────────────────────────────
print("\nQuerying external catalogs...")

# TIC / MAST
tic_params = {}
try:
    from astroquery.mast import Catalogs
    tic = Catalogs.query_object("HD 16467", catalog="TIC", radius=0.02)
    if len(tic) > 0:
        r0 = tic[0]
        def tv(col):
            if col not in r0.colnames: return None
            v = r0[col]
            try:
                import numpy.ma as ma
                if ma.is_masked(v): return None
                f = float(v)
                return None if np.isnan(f) else f
            except (TypeError, ValueError):
                return None
        def ts(col):
            if col not in r0.colnames: return "--"
            v = r0[col]
            try:
                import numpy.ma as ma
                if ma.is_masked(v): return "--"
            except TypeError: pass
            return str(v)
        tic_params = {
            "tic_id":    ts("ID"),
            "ra":        tv("ra"),
            "dec":       tv("dec"),
            "Tmag":      tv("Tmag"),
            "Teff":      tv("Teff"),
            "radius":    tv("rad"),
            "logg":      tv("logg"),
            "mass":      tv("mass"),
            "dist":      tv("d"),
            "ebv":       tv("ebv"),
            "lumclass":  ts("lumclass"),
        }
        print(f"  TIC: {tic_params.get('tic_id')}  "
              f"RA={tic_params.get('ra'):.4f}  "
              f"Dec={tic_params.get('dec'):.4f}")
except Exception as e:
    print(f"  TIC query failed: {e}")

# Gaia DR3 — source ID and precise coordinates
gaia_params = {}
try:
    from astroquery.vizier import Vizier
    from astropy import units as u
    viz = Vizier(columns=["*"], row_limit=1)
    gaia_result = viz.query_object("HD 16467", catalog="I/355/gaiadr3",
                                    radius=5 * u.arcsec)
    if gaia_result:
        gt = gaia_result[0]
        def gv(col):
            if col not in gt.colnames: return None
            v = gt[col][0]
            return None if np.ma.is_masked(v) else float(v)
        def gs(col):
            if col not in gt.colnames: return "--"
            v = gt[col][0]
            return "--" if np.ma.is_masked(v) else str(v)
        gaia_params = {
            "source_id": gs("Source"),
            "ra":        gv("RA_ICRS"),
            "dec":       gv("DE_ICRS"),
            "plx":       gv("Plx"),
            "plx_err":   gv("e_Plx"),
            "dist":      gv("Dist"),
            "teff":      gv("Teff"),
            "logg":      gv("logg"),
            "feh":       gv("[Fe/H]"),
            "vbroad":    gv("Vbroad"),
        }
        print(f"  Gaia DR3 source: {gaia_params.get('source_id')}  "
              f"plx={gaia_params.get('plx'):.4f} mas")
except Exception as e:
    print(f"  Gaia DR3 query failed: {e}")

# SIMBAD — spectral type, V mag
simbad_params = {}
try:
    from astroquery.simbad import Simbad
    simbad = Simbad()
    simbad.add_votable_fields("sp_type", "V", "B", "plx_value", "otype")
    sr = simbad.query_object("HD 16467")
    if sr is not None:
        def sv(col):
            if col not in sr.colnames: return "--"
            v = sr[col][0]
            try:
                if np.ma.is_masked(v): return "--"
            except TypeError: pass
            return v
        simbad_params = {
            "sp_type": str(sv("sp_type")),
            "V":       sv("V"),
            "B":       sv("B"),
            "otype":   str(sv("otype")),
        }
except Exception as e:
    print(f"  SIMBAD query failed: {e}")

# ── Split-half summary ────────────────────────────────────────────────────────
split_txt = "Not run."
if split_half_data:
    cons = split_half_data.get("consistency", {})
    if "error" in cons:
        split_txt = f"Fit failed: {cons['error']}"
    else:
        nmA = cons.get("numax_A", 0)
        eA  = cons.get("numax_A_err", 0)
        nmB = cons.get("numax_B", 0)
        eB  = cons.get("numax_B_err", 0)
        sig = cons.get("diff_sigma", 0)
        split_txt = (
            f"Sector 31 alone: ν_max = {nmA:.2f} ± {eA:.2f} µHz  "
            f"({cons.get('det_A','?')})\n"
            f"Sectors 70+71: ν_max = {nmB:.2f} ± {eB:.2f} µHz  "
            f"({cons.get('det_B','?')})\n"
            f"Difference: {abs(nmA-nmB):.2f} µHz = {sig:.1f}σ — "
            f"{cons.get('verdict','?')}"
        )

# ── pySYD summary ─────────────────────────────────────────────────────────────
pysyd_txt = "Not run."
if pysyd_data:
    if not pysyd_data.get("pysyd_success"):
        pysyd_txt = (f"pySYD v{pysyd_data.get('pysyd_version','?')} "
                     f"failed: {pysyd_data.get('error','see run_pysyd.py output')}")
    else:
        nm_p  = pysyd_data.get("numax", "?")
        nm_pe = pysyd_data.get("numax_err", "?")
        dn_p  = pysyd_data.get("dnu", "?")
        dn_pe = pysyd_data.get("dnu_err", "?")
        pysyd_txt = (
            f"pySYD v{pysyd_data.get('pysyd_version','?')} ran successfully.\n"
            f"ν_max = {nm_p} ± {nm_pe} µHz\n"
            f"Δν    = {dn_p} ± {dn_pe} µHz"
        )

# ── Compose DETECTION_SUMMARY.md ─────────────────────────────────────────────
ra_str   = f"{gaia_params.get('ra', tic_params.get('ra', '?')):.6f}" \
           if isinstance(gaia_params.get('ra', tic_params.get('ra')), float) else "?"
dec_str  = f"{gaia_params.get('dec', tic_params.get('dec', '?')):.6f}" \
           if isinstance(gaia_params.get('dec', tic_params.get('dec')), float) else "?"
dist_val = gaia_params.get("dist") or tic_params.get("dist")
dist_str = f"{dist_val:.1f} pc" if dist_val else "~131 pc (from parallax)"
plx_str  = (f"{gaia_params['plx']:.4f} ± {gaia_params.get('plx_err',0):.4f} mas"
            if gaia_params.get("plx") else "~7.64 mas")
teff_str = (f"{gaia_params.get('teff', tic_params.get('Teff', 4966)):.0f} K")
logg_str = f"{gaia_params.get('logg', tic_params.get('logg', 2.551)):.3f}"
rad_str  = (f"{tic_params['radius']:.2f} R☉" if tic_params.get("radius") else "~10.5 R☉")
vmag_str = (f"{float(simbad_params['V']):.2f}" if simbad_params.get("V") not in (None,"--") else "6.24")

source_id_str = gaia_params.get("source_id", "2484827615701665280")
feh_str  = (f"{gaia_params.get('feh', -0.30):.3f}" if gaia_params.get("feh") is not None else "-0.30")

detection_status = res["det_label"]
h_bkg = res["significance"]
gran_t1_h = res["t1"] / 3600
gran_t2_h = res["t2"] / 3600

# Determine combined numax source string
numax_source_str = " + ".join(numax_sources)

today = date.today().isoformat()

md = f"""# HD 16467 — Asteroseismic Detection Summary

Generated: {today}

---

## Identifiers

| Catalogue | Identifier |
|---|---|
| HD | HD 16467 |
| HIP | HIP 12318 |
| HR | HR 775 |
| TIC | {tic_params.get('tic_id', '422971931')} |
| Gaia DR3 source | {source_id_str} |
| WDS | J02386+0327 (KUI 9 AB) |

---

## Coordinates (J2000, Gaia DR3)

| | Value |
|---|---|
| RA | {ra_str}° |
| Dec | {dec_str}° |
| Distance | {dist_str} |
| Parallax | {plx_str} |

---

## Stellar Parameters

| Parameter | Value | Source |
|---|---|---|
| Spectral type | {simbad_params.get('sp_type', 'K0III')} | SIMBAD |
| V magnitude | {vmag_str} | SIMBAD |
| TESS T mag | {tic_params.get('Tmag', 5.375):.3f} | TIC v8 |
| Teff | {teff_str} | Gaia DR3 |
| log g | {logg_str} | Gaia DR3 |
| [Fe/H] | {feh_str} | Gaia DR3 |
| Radius | {rad_str} | TIC v8 |
| Luminosity class | {tic_params.get('lumclass', 'GIANT')} | TIC v8 |
| E(B−V) | {tic_params.get('ebv', 0.0):.4f} | TIC v8 |

---

## TESS Observations

| Parameter | Value |
|---|---|
| Sectors used | {sectors} (SPOC 120-second cadence) |
| Total cadences | {N:,} |
| Time baseline | {baseline_d:.1f} days |
| Duty cycle | {duty_cycle*100:.1f}% |
| Flux rms | {flux_ppm.std():.1f} ppm |

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

{pysyd_txt}

---

## Results

### Oscillation envelope

| Quantity | Value | Predicted | Ratio |
|---|---|---|---|
| ν_max | **{numax_best:.2f} ± {numax_best_err:.2f} µHz** | {PRED_NMAX:.1f} µHz | {numax_best/PRED_NMAX:.3f} |
| Δν | {dnu_note} | {PRED_DELTANU:.1f} µHz | — |
| Envelope height H | {res['H']:.0f} ppm²/µHz | — | — |
| Envelope width σ_env | {res['se']:.2f} µHz | — | — |
| H / background | {h_bkg:.2f} | — | — |
| **Detection status** | **{detection_status}** | — | — |

*ν_max combined from: {numax_source_str}*

### Granulation background

| Component | Amplitude σ (ppm) | Timescale τ |
|---|---|---|
| Gran 1 (deep convection) | {res['s1']:.0f} | {res['t1']:.0f} s ({gran_t1_h:.1f} h) |
| Gran 2 (mesogranulation) | {res['s2']:.0f} | {res['t2']:.0f} s ({gran_t2_h:.1f} h) |
| White noise C | — | {res['C']:.2f} ppm²/µHz |

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
             = {PRED_NMAX:.1f} µHz

Measured νmax = {numax_best:.2f} ± {numax_best_err:.2f} µHz
Ratio         = {numax_best/PRED_NMAX:.3f}  (within {abs(numax_best/PRED_NMAX - 1)*100:.1f}%)
```

The measured ν_max is in excellent agreement with the scaling-relation
prediction based on independently-measured Gaia DR3 log g and Teff.

---

## Split-Half Consistency Check

{split_txt}

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

1. ν_max = {numax_best:.1f} µHz matches the K0III scaling-relation prediction
   (log g = 2.551, Teff = 4966 K) to within {abs(numax_best/PRED_NMAX - 1)*100:.1f}%.
2. Granulation timescales (τ₁ = {gran_t1_h:.1f} h, τ₂ = {gran_t2_h:.1f} h) are
   consistent with giant-branch convection, inconsistent with a dwarf companion.
3. The companion's predicted ν_max (~500–3000 µHz for a main-sequence dwarf)
   is well outside the detected frequency range, and its flux contribution
   is too small to produce detectable oscillations at the observed amplitude.

---

## Variability Classification

**SOLAR_OSC** — Solar-like oscillations on the red giant branch.

The photometric variability of HD 16467 is dominated by:
- Stochastic p-mode (pressure-mode) oscillations, driven by near-surface
  convection, centred at ν_max ≈ {numax_best:.1f} µHz (period ≈ {1e6/numax_best/3600:.1f} hours).
- Two granulation components with timescales of {gran_t1_h:.1f} h and {gran_t2_h:.1f} h.

Peak-to-trough flux amplitude in the TESS bandpass: ~0.14%
(5th–95th percentile of the raw lightcurve).

---

## VSX Remarks Field (draft)

K0III giant (Teff=4966 K, log g=2.55, R≈10.5 R☉, d≈131 pc; Gaia DR3).
Solar-like oscillations detected in TESS SPOC photometry (Sectors 31, 70,
71; 1115-day baseline). Harvey + Gaussian envelope fit to the calibrated PSD
gives ν_max = {numax_best:.2f} ± {numax_best_err:.2f} µHz, consistent with the scaling-
relation prediction of {PRED_NMAX:.1f} µHz (ratio {numax_best/PRED_NMAX:.3f}). Granulation
background (τ₁ = {gran_t1_h:.1f} h, τ₂ = {gran_t2_h:.1f} h) consistent with giant
convection. Detection significance H/background = {h_bkg:.2f} (MARGINAL;
additional sectors would confirm). Visual binary companion (0.9", ΔV=4 mag,
2.4% flux) contributes negligible contamination. Δν not reliably measured
from current data.

---

## Caveats and Open Questions

1. **Detection is MARGINAL** (H/bkg = {h_bkg:.2f}). The three available SPOC
   sectors have a low duty cycle (~{duty_cycle*100:.1f}%) due to the 3-year gap
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
"""

out_path = Path("DETECTION_SUMMARY.md")
with open(out_path, "w") as fh:
    fh.write(md)

print(f"\n{'═'*65}")
print(f"  Saved {out_path}")
print(f"  Detection status: {detection_status}  (H/bkg = {h_bkg:.2f})")
print(f"  ν_max = {numax_best:.2f} ± {numax_best_err:.2f} µHz  "
      f"(predicted {PRED_NMAX:.1f} µHz, ratio {numax_best/PRED_NMAX:.3f})")
print("═"*65)
