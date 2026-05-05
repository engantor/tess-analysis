"""
Stellar context lookup for HD 206948 using SIMBAD, Gaia DR3, TIC v8, and WDS.
Prints a clean summary of all available physical parameters and predicts
solar-like oscillation frequencies from the scaling relations.

Run from the hd206948/ directory:
    python hd206948_context.py
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
from astroquery.simbad import Simbad
from astroquery.mast import Catalogs
from astroquery.vizier import Vizier
from astropy import units as u

TARGET = "HD 206948"

# ── SIMBAD ────────────────────────────────────────────────────────────────────
print("Querying SIMBAD...")
simbad = Simbad()
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

sim_main_id = sval(simbad_result, "main_id")
sim_sp      = sval(simbad_result, "sp_type")
sim_V       = sval(simbad_result, "V")
sim_B       = sval(simbad_result, "B")
sim_plx     = sval(simbad_result, "plx_value")   # mas
sim_otype   = sval(simbad_result, "otype")
sim_ids     = sval(simbad_result, "ids")

# Parse SIMBAD otype for known variable / object types
OTYPE_DESCRIPTIONS = {
    # Pulsating variables
    "dS*": "delta Sct pulsator",
    "gD*": "gamma Dor pulsator",
    "RR*": "RR Lyrae",
    "Cep": "Cepheid",
    "SX*": "SX Phoenicis",
    "LP*": "Long-period variable (Mira/SR)",
    "Mi*": "Mira variable",
    "sr*": "Semi-regular variable",
    "Pu*": "Pulsating variable (general)",
    # Activity / rotation
    "BY*": "BY Dra (spot rotation)",
    "RS*": "RS CVn (active binary)",
    "Ro*": "Rotating variable",
    "El*": "Ellipsoidal variable",
    # Generic
    "V*":  "Variable star (GCVS catalogued)",
    "**":  "Double/multiple star",
    "SB*": "Spectroscopic binary",
    "EB*": "Eclipsing binary",
    # Giants / sub-types
    "RG*": "Red giant branch star",
    "s*r": "Red supergiant",
    "HB*": "Horizontal branch star",
    "*":   "Star (no special classification)",
}
otype_str = str(sim_otype).strip()
otype_desc = OTYPE_DESCRIPTIONS.get(otype_str, f"otype code '{otype_str}' — check SIMBAD")

# Parse identifiers
ids_list = str(sim_ids).split("|") if sim_ids != "--" else []
ids_stripped = [s.strip() for s in ids_list]

def find_id(prefix):
    for s in ids_stripped:
        if s.startswith(prefix):
            return s
    return None

hip_id = find_id("HIP")
hr_id  = find_id("HR ")
hip_num = hip_id.replace("HIP", "").strip() if hip_id else None

# Binary/double-star refs in SIMBAD ids
companion_refs = [s for s in ids_stripped
                  if any(k in s for k in ["IDS ", "WDS ", "CCDM ", "** "])]

# Derived: distance from SIMBAD parallax
try:
    dist_simbad_pc = 1000.0 / float(sim_plx)
except (TypeError, ValueError, ZeroDivisionError):
    dist_simbad_pc = None

# B-V colour
try:
    bv = float(sim_B) - float(sim_V)
except (TypeError, ValueError):
    bv = None

# ── Gaia DR3 ──────────────────────────────────────────────────────────────────
print("Querying Gaia DR3 (Vizier I/355/gaiadr3)...")
viz = Vizier(columns=["*"], row_limit=1)
gaia_result = viz.query_object(TARGET, catalog="I/355/gaiadr3", radius=5*u.arcsec)

gaia_teff = gaia_logg = gaia_feh = gaia_dist = gaia_plx = gaia_source = None
gaia_vbroad = gaia_ra = gaia_dec = None
if gaia_result:
    gt = gaia_result[0]
    def gval(col):
        if col not in gt.colnames: return None
        v = gt[col][0]
        return None if np.ma.is_masked(v) else float(v)
    def gsval(col):
        if col not in gt.colnames: return None
        v = gt[col][0]
        return None if np.ma.is_masked(v) else str(v)
    gaia_source = gsval("Source")
    gaia_ra     = gval("RA_ICRS")   # deg
    gaia_dec    = gval("DE_ICRS")   # deg
    gaia_teff   = gval("Teff")
    gaia_logg   = gval("logg")
    gaia_feh    = gval("[Fe/H]")
    gaia_dist   = gval("Dist")
    gaia_plx    = gval("Plx")
    gaia_vbroad = gval("Vbroad")

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
tic_mass     = tval(tic_row, "mass")
tic_lumclass = tsval(tic_row, "lumclass")
tic_dist     = tval(tic_row, "d")
tic_plx      = tval(tic_row, "plx")
tic_ebv      = tval(tic_row, "ebv")
tic_e_d      = tval(tic_row, "e_d")

# Estimate luminosity from R and Teff
lum_estimate = None
TEFF_SUN = 5778.0
if tic_rad is not None and tic_teff is not None:
    lum_estimate = (tic_rad**2) * (tic_teff / TEFF_SUN)**4

# ── Washington Double Star catalog ───────────────────────────────────────────
print("Querying Washington Double Star catalog (WDS)...")
# Use a slightly generous radius since WDS positions can be slightly offset
wds_result = viz.query_object(TARGET, catalog="B/wds/wds", radius=60*u.arcsec)

wds_entries = []
if wds_result:
    wt = wds_result[0]
    for row_idx in range(len(wt)):
        def wval(col, idx=row_idx):
            if col not in wt.colnames: return None
            v = wt[col][idx]
            return None if np.ma.is_masked(v) else v
        entry = {
            "disc":   str(wval("Disc") or "--").strip(),
            "obs1":   wval("Obs1"),
            "obs2":   wval("Obs2"),
            "pa1":    wval("pa1"),
            "pa2":    wval("pa2"),
            "sep1":   wval("sep1"),
            "sep2":   wval("sep2"),
            "mag1":   wval("mag1"),
            "mag2":   wval("mag2"),
            "nobs":   wval("Nobs"),
        }
        # Compute flux fraction if both magnitudes present
        ff = None
        if entry["mag1"] is not None and entry["mag2"] is not None:
            try:
                f2 = 10**(-(float(entry["mag2"]) - float(entry["mag1"])) / 2.5)
                ff = f2 / (1 + f2) * 100
            except (TypeError, ValueError):
                pass
        entry["flux_fraction"] = ff
        wds_entries.append(entry)

# ── Predicted solar-like oscillation parameters ───────────────────────────────
# νmax scaling: νmax = νmax_sun * (g/g_sun) * (Teff_sun/Teff)^0.5
# Δν scaling:   Δν   = Δν_sun   * (M/Msun)^0.5 / (R/Rsun)^1.5
NUMAX_SUN   = 3090.0   # µHz
DELTANU_SUN = 135.0    # µHz
LOGG_SUN    = 4.438

nmax_pred = dnu_pred = None
# Use Gaia logg/Teff for the νmax prediction (most reliable).
# Gaia DR3 astrophysical parameters are only generated for a subset of stars;
# if missing, estimate log g from TIC radius + assumed mass via Stefan-Boltzmann.
teff_for_pred = gaia_teff or tic_teff
logg_for_pred = gaia_logg
logg_source   = "Gaia DR3"
rad_for_pred  = tic_rad
# Use TIC mass if available, else assume 1.5 Msun (typical bright giant)
mass_assumed  = tic_mass if tic_mass else 1.5

if logg_for_pred is None and tic_rad is not None:
    # log g = log g_sun + log(M/M_sun) - 2*log(R/R_sun)
    logg_for_pred = LOGG_SUN + np.log10(mass_assumed) - 2.0 * np.log10(tic_rad)
    logg_source   = f"derived from R={tic_rad:.2f} R☉, M={mass_assumed:.1f} M☉"

if logg_for_pred is not None and teff_for_pred is not None:
    g_over_gsun = 10**(logg_for_pred - LOGG_SUN)
    nmax_pred = NUMAX_SUN * g_over_gsun * (TEFF_SUN / teff_for_pred)**0.5
    if rad_for_pred is not None:
        dnu_pred = DELTANU_SUN * (mass_assumed / rad_for_pred**3)**0.5

# TESS cadence vs νmax feasibility note
tess_nyquist_120s = 1e6 / (2 * 120)   # ~4167 µHz — well above any giant νmax
tess_floor_30min  = 1e6 / (30 * 60)   # ~556 µHz — 30-min SG filter corner
sg_filter_period_h = (1e6 / nmax_pred / 3600) if nmax_pred else None

# ── Print summary ─────────────────────────────────────────────────────────────
SEP  = "═" * 68
SEP2 = "─" * 68

print(f"\n{SEP}")
print(f"  Stellar Context Summary: {TARGET}")
print(SEP)

# Identifiers
print(f"\n  ── Identifiers ──────────────────────────────────────────────────")
print(f"  SIMBAD main ID  : {sim_main_id}")
if hip_id:
    print(f"  Hipparcos       : {hip_id}")
if hr_id:
    print(f"  HR / Bright Star: {hr_id}")
print(f"  TIC ID          : {tic_id}")
if gaia_source:
    print(f"  Gaia DR3 source : {gaia_source}")
if companion_refs:
    print(f"  Double-star refs: {', '.join(companion_refs)}")
else:
    print(f"  Double-star refs: none found in SIMBAD ids")

# Coordinates
print(f"\n  ── Coordinates (J2000, Gaia DR3) ────────────────────────────────")
if gaia_ra is not None and gaia_dec is not None:
    # Convert decimal degrees to HMS/DMS
    ra_h  = int(gaia_ra / 15)
    ra_m  = int((gaia_ra / 15 - ra_h) * 60)
    ra_s  = ((gaia_ra / 15 - ra_h) * 60 - ra_m) * 60
    sign  = "+" if gaia_dec >= 0 else "-"
    dec_d = int(abs(gaia_dec))
    dec_m = int((abs(gaia_dec) - dec_d) * 60)
    dec_s = ((abs(gaia_dec) - dec_d) * 60 - dec_m) * 60
    print(f"  RA              : {gaia_ra:.6f}°  ({ra_h:02d}h {ra_m:02d}m {ra_s:05.2f}s)")
    print(f"  Dec             : {gaia_dec:+.6f}°  ({sign}{dec_d:02d}° {dec_m:02d}' {dec_s:04.1f}\")")
else:
    print(f"  Coordinates     : not available from Gaia DR3")

# Classification
print(f"\n  ── Classification ───────────────────────────────────────────────")
print(f"  Spectral type   : {sim_sp}")
print(f"  SIMBAD otype    : {sim_otype}  →  {otype_desc}")
print(f"  TIC lum. class  : {tic_lumclass}")
is_known_variable = otype_str in ("V*", "dS*", "gD*", "RR*", "Cep", "LP*",
                                   "Mi*", "sr*", "Pu*", "BY*", "RS*", "Ro*")
if is_known_variable:
    print(f"  *** NOTE: Star is catalogued as a variable in SIMBAD ***")

# Photometry
print(f"\n  ── Photometry ───────────────────────────────────────────────────")
if sim_V != "--":
    print(f"  V magnitude     : {float(sim_V):.3f}")
else:
    print(f"  V magnitude     : --")
if sim_B != "--":
    print(f"  B magnitude     : {float(sim_B):.3f}")
if bv is not None:
    print(f"  B-V             : {bv:.3f}  (K2III typical: ~1.0–1.2)")
if tic_tmag is not None:
    print(f"  TESS T mag      : {tic_tmag:.3f}")

# Stellar parameters
print(f"\n  ── Stellar Parameters ───────────────────────────────────────────")
if gaia_teff:
    print(f"  Teff (Gaia DR3) : {gaia_teff:.0f} K  (K2III typical: 4600–4900 K)")
elif tic_teff:
    print(f"  Teff (TIC)      : {tic_teff:.0f} K")
if gaia_logg is not None:
    print(f"  log g (Gaia DR3): {gaia_logg:.3f}  (giant: 1.5–3.5, dwarf: 4.0–5.0)")
if gaia_feh is not None:
    print(f"  [Fe/H] (Gaia)   : {gaia_feh:+.3f}  (solar: 0.0)")
if tic_rad is not None:
    print(f"  Radius (TIC)    : {tic_rad:.2f} R☉")
if tic_mass is not None:
    print(f"  Mass (TIC)      : {tic_mass:.2f} M☉")
else:
    print(f"  Mass (TIC)      : not available — assuming {mass_assumed:.1f} M☉ for scaling relations")
if lum_estimate is not None:
    print(f"  Lum. (S-B)      : {lum_estimate:.1f} L☉  (from R and Teff)")
if gaia_vbroad is not None:
    print(f"  v sin i (Gaia)  : {gaia_vbroad:.1f} km/s")
if tic_ebv is not None:
    print(f"  E(B-V)          : {tic_ebv:.4f} mag")

# Distance & parallax
print(f"\n  ── Distance & Parallax ──────────────────────────────────────────")
if gaia_plx is not None:
    print(f"  Parallax (Gaia) : {gaia_plx:.4f} mas")
if gaia_dist is not None:
    print(f"  Distance (Gaia) : {gaia_dist:.1f} pc")
elif dist_simbad_pc is not None:
    print(f"  Distance (SIMBAD plx): {dist_simbad_pc:.1f} pc")
if tic_dist is not None:
    if tic_e_d is not None:
        print(f"  Distance (TIC)  : {tic_dist:.1f} ± {tic_e_d:.1f} pc")
    else:
        print(f"  Distance (TIC)  : {tic_dist:.1f} pc")

# Binary companions (WDS)
print(f"\n  ── Binary Companions (WDS) ──────────────────────────────────────")
if not wds_entries:
    print(f"  No WDS entries within 60\" — no catalogued companions.")
    print(f"  → Binary contamination is not a known concern for this target.")
else:
    for i, e in enumerate(wds_entries):
        disc = e["disc"]
        print(f"  Entry {i+1}: WDS designator {disc}")
        if e["obs2"] is not None:
            print(f"    Last observed  : {e['obs2']}")
        if e["sep2"] is not None:
            print(f"    Separation     : {e['sep2']:.2f}\"  (TESS pixel ≈ 21\" — blended if <21\")")
        if e["sep1"] is not None and e["sep2"] is not None:
            if abs(float(e["sep2"]) - float(e["sep1"])) > 0.1:
                print(f"    First sep.     : {e['sep1']:.2f}\"  → separation has changed (orbital motion)")
            else:
                print(f"    First sep.     : {e['sep1']:.2f}\"  → no significant change")
        if e["pa2"] is not None:
            print(f"    PA (latest)    : {e['pa2']:.0f}°")
        if e["mag1"] is not None and e["mag2"] is not None:
            dm = float(e["mag2"]) - float(e["mag1"])
            print(f"    Component mags : A={float(e['mag1']):.2f}, B={float(e['mag2']):.2f}  "
                  f"(ΔV={dm:.2f} mag)")
        if e["flux_fraction"] is not None:
            ff = e["flux_fraction"]
            print(f"    B flux fraction: {ff:.1f}% of total  "
                  f"(dilution {100/(100-ff):.3f}×)")
            if e["sep2"] is not None and float(e["sep2"]) < 21.0:
                print(f"    *** CAUTION: companion within 1 TESS pixel — fully blended in photometry ***")
            else:
                print(f"    Companion may be resolved by TESS pixel-level centroiding.")

# Predicted solar-like oscillation parameters
print(f"\n  ── Predicted Solar-Like Oscillation Parameters ──────────────────")
mass_note = f"M={tic_mass:.2f} M☉ (TIC)" if tic_mass else f"M≈{mass_assumed:.1f} M☉ (assumed)"
if logg_for_pred is not None and teff_for_pred is not None:
    print(f"  log g used      : {logg_for_pred:.3f}  ({logg_source})")
    print(f"  Teff used       : {teff_for_pred:.0f} K")
    if rad_for_pred is not None:
        print(f"  Radius used     : {rad_for_pred:.2f} R☉ (TIC), {mass_note}")
else:
    print(f"  Insufficient parameters for scaling-relation prediction.")
    print(f"  Need Teff and log g (or radius + mass) — check Gaia / TIC coverage.")

if nmax_pred is not None:
    p_nmax_h = 1e6 / nmax_pred / 3600
    print(f"  ν_max (scaling) : {nmax_pred:.1f} µHz  (period ≈ {p_nmax_h:.1f} h)")
if dnu_pred is not None:
    print(f"  Δν   (scaling)  : {dnu_pred:.2f} µHz")

if nmax_pred is not None:
    print(f"\n  ── Observational Feasibility ────────────────────────────────────")
    if nmax_pred > tess_floor_30min:
        print(f"  ✓ ν_max ({nmax_pred:.1f} µHz) is well above the 30-min SG filter corner "
              f"({tess_floor_30min:.0f} µHz).")
        print(f"    Standard flattening is SAFE for this target — oscillations won't be filtered.")
    else:
        print(f"  ✗ ν_max ({nmax_pred:.1f} µHz) is BELOW the 30-min SG filter corner "
              f"({tess_floor_30min:.0f} µHz).")
        print(f"    Do NOT use lc.flatten() — use raw ppm normalisation as in hd16467_seismic.py.")
        print(f"    Oscillation period ≈ {p_nmax_h:.1f} h — 120s cadence is appropriate.")
    print(f"  TESS 120s Nyquist: {tess_nyquist_120s:.0f} µHz — well above ν_max for any giant.")
    print(f"  Recommended PSD search range: {max(0.5, nmax_pred/10):.1f}–"
          f"{min(500, nmax_pred*10):.0f} µHz")

print(f"\n{SEP}\n")
