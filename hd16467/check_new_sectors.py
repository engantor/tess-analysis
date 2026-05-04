"""
Check MAST for all available TESS lightcurves of HD 16467 / TIC 422971931
across SPOC, QLP, and TGLC pipelines.  Download any sectors not already
in the known set and show a summary table.

Run from the hd16467/ directory:
    python check_new_sectors.py
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import lightkurve as lk
from astropy.stats import sigma_clip
from pathlib import Path

# Sectors already analysed in hd16467_seismic.py
KNOWN_SPOC_SECTORS = {31, 70, 71}

IDENTIFIERS = ["TIC 422971931", "HD 16467", "HIP 12318"]
PIPELINES   = ["SPOC", "QLP", "TGLC"]

print("Querying MAST for all available TESS products...")
print(f"Identifiers tried: {IDENTIFIERS}\n")

# ── Collect all results ────────────────────────────────────────────────────────
all_rows = []   # list of dicts

for ident in IDENTIFIERS:
    try:
        result = lk.search_lightcurve(ident, mission="TESS")
    except Exception as e:
        print(f"  Search failed for {ident!r}: {e}")
        continue
    if len(result) == 0:
        continue

    for i in range(len(result)):
        row = result.table[i]
        author  = str(row.get("author", "?"))
        sector  = int(row.get("sequence_number", 0))
        exptime = float(row.get("exptime", 0))
        t_start = float(row.get("t_min",  0))
        t_stop  = float(row.get("t_max",  0))

        key = (author, sector)
        # Deduplicate across identifier attempts
        if any(r["_key"] == key for r in all_rows):
            continue

        all_rows.append({
            "_key":    key,
            "author":  author,
            "sector":  sector,
            "exptime": exptime,
            "t_start": t_start,
            "t_stop":  t_stop,
        })

# Sort by sector then author
all_rows.sort(key=lambda r: (r["sector"], r["author"]))

# ── Print summary table ───────────────────────────────────────────────────────
print(f"{'Pipeline':<8}  {'Sector':>6}  {'Cadence(s)':>10}  "
      f"{'T_start (BTJD)':>15}  {'T_stop (BTJD)':>14}  {'New?':>5}")
print("-" * 72)

new_spoc    = []
new_other   = []

for r in all_rows:
    is_new_spoc = (r["author"] == "SPOC"
                   and r["sector"] not in KNOWN_SPOC_SECTORS)
    is_new_other = (r["author"] != "SPOC")
    flag = "  NEW" if (is_new_spoc or is_new_other) else ""

    print(f"{r['author']:<8}  {r['sector']:>6}  {r['exptime']:>10.0f}  "
          f"{r['t_start']:>15.2f}  {r['t_stop']:>14.2f}{flag}")

    if is_new_spoc:
        new_spoc.append(r)
    elif is_new_other:
        new_other.append(r)

print()

# ── Flag anything new ─────────────────────────────────────────────────────────
if not new_spoc and not new_other:
    print("No new sectors found beyond the known set "
          f"(SPOC sectors {sorted(KNOWN_SPOC_SECTORS)}).")
else:
    if new_spoc:
        print(f"NEW SPOC sectors found: "
              f"{[r['sector'] for r in new_spoc]}")
    if new_other:
        print(f"Non-SPOC products available: "
              f"{[(r['author'], r['sector']) for r in new_other]}")

# ── Download new SPOC sectors if found ───────────────────────────────────────
if new_spoc:
    print(f"\nDownloading {len(new_spoc)} new SPOC sector(s)...")
    for r in new_spoc:
        print(f"  Downloading SPOC sector {r['sector']}...")
        try:
            sr = lk.search_lightcurve("TIC 422971931", mission="TESS",
                                       author="SPOC",
                                       sector=r["sector"])
            lc = sr.download()
            lc = lc.remove_nans()
            med  = float(np.nanmedian(lc.flux.value))
            ppm  = np.array(1e6 * (lc.flux.value / med - 1.0))
            clip = sigma_clip(ppm, sigma=5, maxiters=3, masked=True)
            good = ~np.array(clip.mask, dtype=bool)
            print(f"    Sector {r['sector']}: {good.sum()} cadences, "
                  f"rms={ppm[good].std():.1f} ppm")

            # Save to a simple two-column ASCII file for external tools
            out_path = Path(f"extra_sectors/sector_{r['sector']:03d}_spoc.dat")
            out_path.parent.mkdir(exist_ok=True)
            np.savetxt(out_path,
                       np.column_stack([lc.time.value[good], ppm[good]]),
                       header="time_btjd  flux_ppm",
                       fmt=["%.6f", "%.2f"])
            print(f"    Saved to {out_path}")
        except Exception as e:
            print(f"    Download failed for sector {r['sector']}: {e}")

    print("\nNote: re-run hd16467_seismic.py with an updated sector list "
          "to include new sectors in the full analysis.")

# ── Summary of TGLC/QLP availability ─────────────────────────────────────────
tglc_rows = [r for r in all_rows if r["author"] == "TGLC"]
qlp_rows  = [r for r in all_rows if r["author"] == "QLP"]
if tglc_rows:
    print(f"\nTGLC products available for sectors: "
          f"{[r['sector'] for r in tglc_rows]}")
    print("  TGLC uses PSF photometry — potentially cleaner for crowded fields.")
    print("  Consider running hd16467_seismic.py with author='TGLC' to compare.")
if qlp_rows:
    print(f"\nQLP products available for sectors: "
          f"{[r['sector'] for r in qlp_rows]}")
