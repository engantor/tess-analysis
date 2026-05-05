"""
Shared utilities for HD 206948 asteroseismic analysis.

Harvey background model, empirically-calibrated PSD, and lightcurve
loading. Copied from hd16467/seismic_utils.py with updated target
constants and a p0_override hook in fit_harvey_model.
"""

import warnings
import numpy as np
from scipy.optimize import curve_fit
from scipy.ndimage import uniform_filter1d
from astropy.timeseries import LombScargle
from astropy.stats import sigma_clip
import lightkurve as lk

# µHz → cycles/day conversion
UDAY = 86400e-6   # 1 µHz = 0.0864 c/d

# Scaling-relation predictions for HD 206948 (K2III, TIC R=12.49 R☉, Teff=4648 K)
# log g derived from R and M=1.5 M☉ assumed: log g = 4.438 + log10(1.5) - 2*log10(12.49) = 2.421
PRED_NMAX    = 33.1   # µHz
PRED_DELTANU = 3.75   # µHz


# ── Harvey model functions ──────────────────────────────────────────────────
def harvey(nu, sigma, tau_s):
    """One-sided Harvey granulation profile.
    nu in µHz, tau_s in s. Returns PSD in ppm²/µHz."""
    x = 2.0 * np.pi * nu * tau_s * 1e-6
    return 4.0 * sigma**2 * tau_s * 1e-6 / (1.0 + x**2)**2


def gauss_env(nu, H, nu_max, sigma_env):
    """Gaussian oscillation envelope. nu in µHz."""
    return H * np.exp(-0.5 * ((nu - nu_max) / sigma_env)**2)


def full_model(nu, s1, t1, s2, t2, H, nm, se, C):
    """Full Harvey + Gaussian envelope + white noise model."""
    return harvey(nu, s1, t1) + harvey(nu, s2, t2) + gauss_env(nu, H, nm, se) + C


def log10_model(nu, s1, t1, s2, t2, H, nm, se, C):
    """Full model in log10-power space (used for fitting)."""
    return np.log10(np.maximum(full_model(nu, s1, t1, s2, t2, H, nm, se, C), 1e-10))


# ── Lightcurve loading ──────────────────────────────────────────────────────
def load_sectors_ppm(identifier="HD 206948", author="TESS-SPOC", sector_filter=None,
                     exptime=None, verbose=True):
    """
    Download SPOC lightcurves, normalize each sector to ppm relative to its
    own median, and apply 5-sigma clipping.

    sector_filter : list of int or None
        If provided, keep only sectors in this list.

    Returns
    -------
    t_days    : ndarray — concatenated, sorted timestamps (BTJD days)
    flux_ppm  : ndarray — concatenated flux in ppm
    info      : list of dicts with 'sector', 'n', 'rms' per sector
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kwargs = dict(mission="TESS", author=author)
        if exptime is not None:
            kwargs["exptime"] = exptime
        search = lk.search_lightcurve(identifier, **kwargs)
        lc_collection = search.download_all()

    sectors_t, sectors_f, info = [], [], []
    for lc in lc_collection:
        if sector_filter is not None and lc.sector not in sector_filter:
            continue
        lc = lc.remove_nans()
        med = float(np.nanmedian(lc.flux.value))
        ppm = np.array(1e6 * (lc.flux.value / med - 1.0), dtype=np.float64)
        clipped = sigma_clip(ppm, sigma=5, maxiters=3, masked=True)
        good = ~np.array(clipped.mask, dtype=bool)
        sectors_t.append(lc.time.value[good])
        sectors_f.append(ppm[good])
        rms = float(ppm[good].std())
        info.append({'sector': lc.sector, 'n': int(good.sum()), 'rms': rms})
        if verbose:
            print(f"  Sector {lc.sector}: {good.sum()} cadences, ppm rms={rms:.1f}")

    if not sectors_t:
        raise ValueError(f"No sectors loaded for {identifier} "
                         f"(filter={sector_filter})")

    t_days   = np.concatenate(sectors_t)
    flux_ppm = np.concatenate(sectors_f)
    idx = np.argsort(t_days)
    return t_days[idx], flux_ppm[idx], info


# ── Frequency grid ──────────────────────────────────────────────────────────
def make_freq_grid(F_MIN=0.5, F_MAX=300.0, df=0.01):
    """Return (freq_uhz, freq_cd, df_uhz) for the standard frequency grid."""
    N = int((F_MAX - F_MIN) / df) + 1
    freq_uhz = np.linspace(F_MIN, F_MAX, N)
    freq_cd  = freq_uhz * UDAY
    df_uhz   = float(freq_uhz[1] - freq_uhz[0])
    return freq_uhz, freq_cd, df_uhz


# ── PSD calibration ─────────────────────────────────────────────────────────
def calibrate_psd(t_days, flux_ppm, freq_uhz, freq_cd, df_uhz,
                  nu_cal=43.0, A_cal=10.0, verbose=True):
    """
    Compute an empirically-calibrated PSD in ppm²/µHz.

    Injects a known sine wave (amplitude A_cal ppm at nu_cal µHz) into the
    actual time array, measures the raw LS power at that frequency, and derives
    a scale factor so the injected signal gives the Parseval-correct peak
    A_cal²/(2×df_uhz).  This accounts for window-function inflation from the
    gapped TESS data.

    Returns
    -------
    psd       : ndarray — calibrated PSD in ppm²/µHz
    PSD_SCALE : float   — the multiplicative scale factor applied
    C_noise   : float   — median PSD in 200-300 µHz (astrophysical background floor)
    """
    nu_cal_cd = nu_cal * UDAY
    f_cal     = flux_ppm + A_cal * np.sin(2 * np.pi * nu_cal_cd * t_days)

    power_base = LombScargle(t_days, flux_ppm).power(freq_cd, normalization="psd")
    power_cal  = LombScargle(t_days, f_cal).power(freq_cd, normalization="psd")

    diff = power_cal - power_base
    m_cal = (freq_uhz >= nu_cal - 3) & (freq_uhz <= nu_cal + 3)
    peak_raw     = float(diff[m_cal].max())
    expected_psd = A_cal**2 / (2.0 * df_uhz)
    PSD_SCALE    = expected_psd / peak_raw

    if verbose:
        print(f"  Injected A={A_cal} ppm at {nu_cal} µHz: "
              f"raw peak={peak_raw:.2f}, expected={expected_psd:.0f} ppm²/µHz "
              f"→ scale={PSD_SCALE:.6f}")

    psd = power_base * PSD_SCALE

    m_noise = (freq_uhz >= 200) & (freq_uhz <= 300)
    C_noise = float(np.median(psd[m_noise]))
    if verbose:
        print(f"  Noise floor (200-300 µHz): {C_noise:.2f} ppm²/µHz")

    return psd, PSD_SCALE, C_noise


# ── Harvey model fit ────────────────────────────────────────────────────────
def fit_harvey_model(freq_uhz, psd, C_noise=None, nu_pred=PRED_NMAX,
                     fit_range=(1.0, 200.0), smooth_bins=50, verbose=True,
                     p0_override=None, numax_bounds=(5, 150)):
    """
    Fit Harvey₁ + Harvey₂ + Gaussian oscillation envelope + white noise to
    the PSD.  Fitting is done in log10-power space over fit_range µHz.

    Parameters
    ----------
    freq_uhz  : array of frequencies in µHz
    psd       : array of calibrated PSD values in ppm²/µHz
    C_noise   : float or None — white noise initial guess (uses 200-300 µHz
                median if None)
    nu_pred   : predicted nu_max (µHz) — used as initial guess centre
    fit_range : (lo, hi) µHz for the fitting window
    smooth_bins : number of bins for uniform_filter1d before fitting

    Returns
    -------
    result dict with keys:
        popt        : list of 8 fitted parameters [s1,t1,s2,t2,H,nm,se,C]
        perr        : list of 1-sigma uncertainties (0 if fit failed)
        fit_success : bool
        significance: H / background_at_numax
        det_label   : 'CONVINCING', 'MARGINAL', or 'NOT DETECTED'
        gran_bkg    : granulation background at nu_max
        (s1,t1,s2,t2,H,nm,se,C named individually)
    """
    psd_smooth = uniform_filter1d(psd, size=smooth_bins)

    if C_noise is None:
        m_n = (freq_uhz >= 200) & (freq_uhz <= 300)
        C_noise = float(np.median(psd_smooth[m_n]))

    # Data-driven initial guesses
    psd_at_2  = float(psd_smooth[np.argmin(np.abs(freq_uhz - 2.0))])
    psd_at_20 = float(psd_smooth[np.argmin(np.abs(freq_uhz - 20.0))])
    psd_at_43 = float(psd_smooth[np.argmin(np.abs(freq_uhz - nu_pred))])

    tau1_init = 1e5                                               # ~28 h
    s1_init   = min(np.sqrt(max(psd_at_2, 1.0) / (4 * tau1_init * 1e-6)), 2000.0)
    tau2_init = 3000.0                                            # ~50 min
    s2_init   = 100.0

    gran_at_43_est = harvey(nu_pred, s1_init, tau1_init) + harvey(nu_pred, s2_init, tau2_init)
    H_init = max(psd_at_43 - gran_at_43_est - C_noise, 0.01 * C_noise)

    p0 = [s1_init, tau1_init, s2_init, tau2_init, H_init, nu_pred, 8.0, C_noise]
    if p0_override is not None:
        p0 = list(p0_override)
    bounds_lo = [1,    5000,  1,   100,   0,    numax_bounds[0],  1,   0.1]
    bounds_hi = [3000, 5e6, 1000, 5e5, 5e7,    numax_bounds[1], 50, 5000]

    if verbose:
        ratio = psd_at_2 / psd_at_20 if psd_at_20 > 0 else 0
        print(f"  PSD(2µHz)/PSD(20µHz) = {ratio:.1f}")
        print(f"  Initial guesses: σ₁={s1_init:.0f} ppm, τ₁={tau1_init:.0f} s, "
              f"σ₂={s2_init:.0f} ppm, τ₂={tau2_init:.0f} s")
        print(f"    H={H_init:.1f} ppm²/µHz, ν_max={nu_pred} µHz, "
              f"σ_env=8.0 µHz, C={C_noise:.2f} ppm²/µHz")

    # Clamp initial guesses to bounds
    for i, (p, lo, hi) in enumerate(zip(p0, bounds_lo, bounds_hi)):
        if not (lo <= p <= hi):
            if verbose:
                print(f"  ⚠  p0[{i}]={p:.1f} outside [{lo},{hi}] — clamping")
            p0[i] = float(np.clip(p, lo, hi))

    m_fit = (freq_uhz >= fit_range[0]) & (freq_uhz <= fit_range[1])
    nu_f  = freq_uhz[m_fit]
    lpsd  = np.log10(np.maximum(psd_smooth[m_fit], 1e-10))

    popt = list(p0)
    pcov = np.zeros((8, 8))
    fit_success = False
    try:
        popt, pcov = curve_fit(log10_model, nu_f, lpsd, p0=p0,
                               bounds=(bounds_lo, bounds_hi),
                               maxfev=30000, method="trf")
        fit_success = True
        if verbose:
            print("  Harvey model fit converged ✓")
    except Exception as e:
        if verbose:
            print(f"  Harvey fit failed: {e}\n  Using initial guesses.")

    perr = np.sqrt(np.abs(np.diag(pcov))).tolist() if fit_success else [0.0] * 8
    s1f, t1f, s2f, t2f, Hf, nmf, sef, Cf = popt

    if verbose:
        tag = 'converged' if fit_success else 'FAILED, using p0'
        print(f"\n  Fitted parameters (fit={tag}):")
        print(f"    σ₁={s1f:.1f}±{perr[0]:.1f} ppm, τ₁={t1f:.0f}±{perr[1]:.0f} s "
              f"({t1f/3600:.1f} h)")
        print(f"    σ₂={s2f:.1f}±{perr[2]:.1f} ppm, τ₂={t2f:.0f}±{perr[3]:.0f} s "
              f"({t2f/3600:.1f} h)")
        print(f"    H={Hf:.2f}±{perr[4]:.2f} ppm²/µHz, "
              f"ν_max={nmf:.2f}±{perr[5]:.2f} µHz, "
              f"σ_env={sef:.2f}±{perr[6]:.2f} µHz")
        print(f"    C={Cf:.3f}±{perr[7]:.3f} ppm²/µHz")

    gran_bkg     = harvey(nmf, s1f, t1f) + harvey(nmf, s2f, t2f) + Cf
    significance = Hf / gran_bkg if gran_bkg > 0 else 0.0

    if significance >= 5:
        det_label = "CONVINCING"
    elif significance >= 2:
        det_label = "MARGINAL"
    else:
        det_label = "NOT DETECTED"

    return {
        "popt":         popt,
        "perr":         perr,
        "fit_success":  fit_success,
        "significance": significance,
        "det_label":    det_label,
        "gran_bkg":     gran_bkg,
        "s1": s1f, "t1": t1f,
        "s2": s2f, "t2": t2f,
        "H":  Hf,  "nm": nmf,
        "se": sef, "C":  Cf,
        "s1_err": perr[0], "t1_err": perr[1],
        "s2_err": perr[2], "t2_err": perr[3],
        "H_err":  perr[4], "nm_err": perr[5],
        "se_err": perr[6], "C_err":  perr[7],
    }
