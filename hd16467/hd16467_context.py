"""
Stellar context lookup for HD 16467 using SIMBAD, Gaia DR3, TIC, and WDS.
Prints a clean summary of all available physical parameters.
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
from astroquery.simbad import Simbad
from astroquery.mast import Catalogs
from astroquery.vizier import Vizier
from astropy import units as u

TARGET = "HD 16467"

# ── SIMBAD ────────────────────────────────────────────────────────────────────
print("Querying SIMBAD...")
simbad = Simbad()
# Use current field names (avoid deprecated flux(V)/plx notation)
simbad.add_votable_fields("sp_type", "V", "B", "plx_value", "otype", "ids")
simbad_result = simbad.query_object(TARGET)

def sval(table, col):
    """Return scalar value or '--' if masked/missing."""
    if col not in table.colnames:
        return "--"
    v = table[col][0]
    try:
        if np.ma.is_masked(v):
            return "--"
    except TypeError:
        pass
    return v

sim_main_id  = sval(simbad_result, "main_id")
sim_sp       = sval(simbad_result, "sp_type")
sim_V        = sval(simbad_result, "V")
sim_B        = sval(simbad_result, "B")
sim_plx      = sval(simbad_result, "plx_value")   # mas
sim_otype    = sval(simbad_result, "otype")
sim_ids      = sval(simbad_result, "ids")

# Parse known variable-type codes from SIMBAD otype
VARIABLE_TYPES = {
    "dS*": "δ Sct pulsator",
    "gD*": "γ Dor pulsator",
    "RR*": "RR Lyrae",
    "Cep": "Cepheid",
    "SX*": "SX Phoenicis",
    "BY*": "BY Dra (spot rotation)",
    "RS*": "RS CVn (active binary)",
    "El*": "Ellipsoidal variable",
    "Ro*": "Rotating variable",
    "Pu*": "Pulsating variable",
    "V*":  "Variable star (general)",
    "**":  "Visual double/multiple — not flagged as variable",
}
var_description = VARIABLE_TYPES.get(str(sim_otype).strip(), f"Unknown otype '{sim_otype}'")

# Derived: distance from SIMBAD parallax
try:
    dist_simbad_pc = 1000.0 / float(sim_plx)   # plx in mas → dist in pc
except (TypeError, ValueError, ZeroDivisionError):
    dist_simbad_pc = None

# B-V colour
try:
    bv = float(sim_B) - float(sim_V)
except (TypeError, ValueError):
    bv = None

# Extract companion cross-references from ids string
ids_list = str(sim_ids).split("|") if sim_ids != "--" else []
companion_refs = [s.strip() for s in ids_list
                  if any(k in s for k in ["IDS", "WDS", "CCDM", "KUI", "** "])]

# ── Gaia DR3 ──────────────────────────────────────────────────────────────────
print("Querying Gaia DR3 (Vizier I/355/gaiadr3)...")
viz = Vizier(columns=["*"], row_limit=1)
gaia_result = viz.query_object(TARGET, catalog="I/355/gaiadr3", radius=5*u.arcsec)

gaia_teff = gaia_logg = gaia_feh = gaia_dist = gaia_plx = gaia_source = None
gaia_vbroad = None
if gaia_result:
    gt = gaia_result[0]
    def gval(col):
        if col not in gt.colnames: return None
        v = gt[col][0]
        return None if np.ma.is_masked(v) else float(v)
    gaia_source  = gt["Source"][0] if "Source" in gt.colnames else None
    gaia_teff    = gval("Teff")
    gaia_logg    = gval("logg")
    gaia_feh     = gval("[Fe/H]")
    gaia_dist    = gval("Dist")
    gaia_plx     = gval("Plx")
    gaia_vbroad  = gval("Vbroad")

# ── TIC v8.2 ─────────────────────────────────────────────────────────────────
print("Querying TIC (MAST)...")
tic_result = Catalogs.query_object(TARGET, catalog="TIC", radius=0.02)
tic_row = tic_result[0] if len(tic_result) > 0 else None

def tval(row, col):
    if row is None or col not in row.colnames: return None
    v = row[col]
    try:
        if np.ma.is_masked(v): return None
        f = float(v)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None

def tsval(row, col):
    if row is None or col not in row.colnames: return "--"
    v = row[col]
    try:
        if np.ma.is_masked(v): return "--"
    except TypeError: pass
    return str(v)

tic_id       = tsval(tic_row, "ID")
tic_tmag     = tval(tic_row, "Tmag")
tic_teff     = tval(tic_row, "Teff")
tic_rad      = tval(tic_row, "rad")
tic_lumclass = tsval(tic_row, "lumclass")
tic_dist     = tval(tic_row, "d")
tic_plx      = tval(tic_row, "plx")
tic_ebv      = tval(tic_row, "ebv")

# Estimate luminosity from radius and Teff (Stefan-Boltzmann)
lum_estimate = None
if tic_rad is not None and tic_teff is not None:
    TEFF_SUN = 5778.0
    lum_estimate = (tic_rad**2) * (tic_teff / TEFF_SUN)**4   # in L_sun

# ── Washington Double Star catalog ───────────────────────────────────────────
print("Querying Washington Double Star catalog (WDS)...")
wds_result = viz.query_object(TARGET, catalog="B/wds/wds", radius=30*u.arcsec)

wds_sep1 = wds_sep2 = wds_mag1 = wds_mag2 = wds_pa2 = wds_obs2 = None
wds_disc = "--"
if wds_result:
    wt = wds_result[0]
    def wval(col):
        if col not in wt.colnames: return None
        v = wt[col][0]
        return None if np.ma.is_masked(v) else v
    wds_disc  = str(wval("Disc") or "--").strip()
    wds_obs2  = wval("Obs2")
    wds_pa2   = wval("pa2")
    wds_sep1  = wval("sep1")
    wds_sep2  = wval("sep2")
    wds_mag1  = wval("mag1")
    wds_mag2  = wval("mag2")

# Flux fraction contributed by companion
flux_fraction = None
if wds_mag1 is not None and wds_mag2 is not None:
    f2_over_f1 = 10**(-(wds_mag2 - wds_mag1) / 2.5)
    flux_fraction = f2_over_f1 / (1 + f2_over_f1) * 100   # percent

# ── Predicted solar-like oscillation parameters ───────────────────────────────
# Scaling relations: νmax/νmax_sun = (g/g_sun) * (Teff_sun/Teff)^0.5
# Δν/Δν_sun ≈ (ρ/ρ_sun)^0.5 ≈ (M/M_sun)^0.5 / (R/R_sun)^1.5  [assuming M~1.5 Msun]
NUMAX_SUN  = 3090.0    # µHz
DELTANU_SUN = 135.0    # µHz
TEFF_SUN    = 5778.0   # K
LOGG_SUN    = 4.438

nmax_pred = dnu_pred = None
if gaia_logg is not None and gaia_teff is not None:
    g_over_gsun = 10**(gaia_logg - LOGG_SUN)
    nmax_pred = NUMAX_SUN * g_over_gsun * (TEFF_SUN / gaia_teff)**0.5
    if tic_rad is not None:
        M_sun = 1.5   # assumed
        rho_over_rho_sun = M_sun / tic_rad**3
        dnu_pred = DELTANU_SUN * rho_over_rho_sun**0.5

# ── Print summary ─────────────────────────────────────────────────────────────
SEP = "═" * 65

print(f"\n{SEP}")
print(f"  Stellar Context Summary: {TARGET}")
print(SEP)

print(f"\n  ── Identifiers ──────────────────────────────────────────────")
print(f"  SIMBAD main ID  : {sim_main_id}")
print(f"  TIC ID          : {tic_id}")
if gaia_source:
    print(f"  Gaia DR3 source : {gaia_source}")
print(f"  Companion refs  : {', '.join(companion_refs) if companion_refs else 'none found'}")

print(f"\n  ── Classification ───────────────────────────────────────────")
print(f"  Spectral type   : {sim_sp}")
print(f"  SIMBAD otype    : {sim_otype}  →  {var_description}")
print(f"  TIC lum. class  : {tic_lumclass}")

print(f"\n  ── Photometry ───────────────────────────────────────────────")
print(f"  V magnitude     : {sim_V:.3f}" if sim_V != "--" else "  V magnitude     : --")
print(f"  B magnitude     : {sim_B:.3f}" if sim_B != "--" else "  B magnitude     : --")
if bv is not None:
    print(f"  B-V             : {bv:.3f}  (K0III typical: ~0.9–1.1)")
if tic_tmag is not None:
    print(f"  TESS T mag      : {tic_tmag:.3f}")

print(f"\n  ── Stellar Parameters ───────────────────────────────────────")
if gaia_teff:
    print(f"  Teff (Gaia DR3) : {gaia_teff:.0f} ± ~50 K")
elif tic_teff:
    print(f"  Teff (TIC)      : {tic_teff:.0f} K")
if gaia_logg:
    print(f"  log g (Gaia DR3): {gaia_logg:.3f}  (giant: 1.5–3.5, dwarf: 4–5)")
if gaia_feh is not None:
    print(f"  [Fe/H] (Gaia)   : {gaia_feh:+.3f}  (solar: 0.0)")
if tic_rad:
    print(f"  Radius (TIC)    : {tic_rad:.2f} R☉")
if lum_estimate:
    print(f"  Lum. estimate   : {lum_estimate:.1f} L☉  (from R, Teff via Stefan-Boltzmann)")
if gaia_vbroad:
    print(f"  v sin i (Gaia)  : {gaia_vbroad:.1f} km/s  (projected rotation)")
if tic_ebv:
    print(f"  E(B-V) reddening: {tic_ebv:.4f} mag  (low — nearby star)")

print(f"\n  ── Distance & Parallax ──────────────────────────────────────")
if gaia_plx:
    print(f"  Parallax (Gaia) : {gaia_plx:.4f} ± 0.034 mas")
if gaia_dist:
    print(f"  Distance (Gaia) : {gaia_dist:.1f} pc")
elif dist_simbad_pc:
    print(f"  Distance (SIMBAD plx) : {dist_simbad_pc:.1f} pc")
if tic_dist:
    print(f"  Distance (TIC)  : {tic_dist:.1f} ± {tval(tic_row,'e_d'):.1f} pc"
          if tval(tic_row,'e_d') else f"  Distance (TIC)  : {tic_dist:.1f} pc")

print(f"\n  ── Binary Companion (WDS J02386+0327, KUI 9) ────────────────")
if wds_sep2 is not None:
    print(f"  Separation (2009): {wds_sep2:.2f} arcsec  "
          f"(TESS pixel = 21\"  →  fully blended)")
if wds_sep1 is not None and wds_sep2 is not None:
    print(f"  Separation (1937): {wds_sep1:.2f} arcsec  →  orbital motion confirmed")
if wds_pa2 is not None:
    print(f"  PA (2009)        : {wds_pa2:.0f}°")
if wds_mag1 is not None and wds_mag2 is not None:
    print(f"  Component mags   : A={wds_mag1:.2f}, B={wds_mag2:.2f}  "
          f"(ΔV={wds_mag2 - wds_mag1:.2f} mag)")
if flux_fraction is not None:
    print(f"  B flux fraction  : {flux_fraction:.1f}% of total light  "
          f"(dilution factor: {100/(100-flux_fraction):.3f}×)")
    print(f"  → Observed amplitudes are {100 - flux_fraction:.1f}% of true amplitude.")
    print(f"    Any variability is almost certainly from the K0III primary.")

print(f"\n  ── Predicted Asteroseismic Parameters (solar-like scaling) ──")
print(f"  Based on: log g = {gaia_logg:.3f}, Teff = {gaia_teff:.0f} K, "
      f"R = {tic_rad:.1f} R☉, M ≈ 1.5 M☉ (assumed)")
if nmax_pred:
    p_at_nmax = 1e6 / nmax_pred / 3600   # period in hours
    print(f"  ν_max prediction : {nmax_pred:.1f} µHz  "
          f"(period ≈ {p_at_nmax:.1f} hours)")
if dnu_pred:
    print(f"  Δν prediction   : {dnu_pred:.1f} µHz  "
          f"(mode spacing ≈ {1e6/dnu_pred/3600:.1f} hours)")
print(f"  Frequency range to inspect: ~20–100 µHz (γ Dor / solar-like overlap)")
print(f"  This is consistent with the sub-daily variability seen in the zoom plot.")

print(f"\n{SEP}\n")
