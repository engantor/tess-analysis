"""
Survey MAST for all available TESS lightcurves of HD 206948 across
SPOC, QLP, and TGLC pipelines.  Prints a table and assesses whether
asteroseismology is feasible.

Run from the hd206948/ directory:
    python check_sectors.py
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import lightkurve as lk

TARGET    = "HD 206948"
# Will be supplemented with TIC ID once known
IDENTIFIERS = [TARGET]
PIPELINES   = ["SPOC", "QLP", "TGLC"]

# Additional identifiers (populated after SIMBAD lookup by context script;
# add HIP / TIC here if check_sectors.py is run standalone)
# e.g. IDENTIFIERS += ["HIP 107584", "TIC 123456789"]

print(f"Querying MAST for all TESS lightcurves of {TARGET}...")
print(f"Identifiers tried: {IDENTIFIERS}\n")

# ── Collect all search results ────────────────────────────────────────────────
all_rows = []   # list of dicts

for ident in IDENTIFIERS:
    try:
        result = lk.search_lightcurve(ident, mission="TESS")
    except Exception as e:
        print(f"  Search failed for {ident!r}: {e}")
        continue
    if result is None or len(result) == 0:
        print(f"  No results for {ident!r}")
        continue
    print(f"  {ident!r}: {len(result)} product(s) found")

    for i in range(len(result)):
        row    = result.table[i]
        author = str(row.get("author", "?"))
        sector = int(row.get("sequence_number", 0))
        exptime= float(row.get("exptime", 0))
        t_min  = float(row.get("t_min", 0))
        t_max  = float(row.get("t_max", 0))

        key = (author, sector)
        if any(r["_key"] == key for r in all_rows):
            continue   # deduplicate across identifier aliases

        # Estimated cadence count from time span and exposure time
        # t_min/t_max are in BTJD (days); exptime in seconds
        span_s = (t_max - t_min) * 86400.0
        n_est  = int(round(span_s / exptime)) if exptime > 0 else 0

        all_rows.append({
            "_key":   key,
            "author": author,
            "sector": sector,
            "exptime":exptime,
            "t_min":  t_min,
            "t_max":  t_max,
            "n_est":  n_est,
        })

# Sort by sector, then author
all_rows.sort(key=lambda r: (r["sector"], r["author"]))

# ── Summary table ─────────────────────────────────────────────────────────────
print()
if not all_rows:
    print("No TESS lightcurves found for any identifier.")
    print("Either the star is not observed by TESS or the name was not matched.")
    print("Try running with the TIC ID directly, e.g. lk.search_lightcurve('TIC XXXXXXX')")
else:
    hdr = (f"{'Pipeline':<8}  {'Sector':>6}  {'Cadence(s)':>10}  "
           f"{'T_start (BTJD)':>14}  {'T_stop (BTJD)':>13}  "
           f"{'Duration(d)':>11}  {'N_cadences':>10}")
    print(hdr)
    print("-" * len(hdr))

    # Group by pipeline for summary
    by_author = {}
    for r in all_rows:
        by_author.setdefault(r["author"], []).append(r)

    for r in all_rows:
        dur = r["t_max"] - r["t_min"]
        print(f"{r['author']:<8}  {r['sector']:>6}  {r['exptime']:>10.0f}  "
              f"{r['t_min']:>14.2f}  {r['t_max']:>13.2f}  "
              f"{dur:>11.1f}  {r['n_est']:>10,}")

    print()

    # ── Per-pipeline counts ───────────────────────────────────────────────────
    print("Pipeline summary:")
    for author in sorted(by_author.keys()):
        rows   = by_author[author]
        sectors= sorted(set(r["sector"] for r in rows))
        cadences = [r["exptime"] for r in rows]
        print(f"  {author:<8}: {len(rows)} sector(s) — "
              f"sectors {sectors}, "
              f"cadence(s) {sorted(set(int(c) for c in cadences))} s")

    # ── Total SPOC baseline ───────────────────────────────────────────────────
    spoc_rows = by_author.get("SPOC", [])
    if spoc_rows:
        spoc_120 = [r for r in spoc_rows if abs(r["exptime"] - 120) < 10]
        if spoc_120:
            t_earliest = min(r["t_min"] for r in spoc_120)
            t_latest   = max(r["t_max"] for r in spoc_120)
            baseline   = t_latest - t_earliest
            total_cad  = sum(r["n_est"] for r in spoc_120)
            # Duty cycle: total cadences * 120s / baseline in seconds
            duty = total_cad * 120.0 / (baseline * 86400) * 100 if baseline > 0 else 0
            print(f"\n  SPOC 120s baseline: {baseline:.0f} days "
                  f"(sectors {[r['sector'] for r in spoc_120]})")
            print(f"  Total cadences    : ~{total_cad:,}")
            print(f"  Duty cycle        : ~{duty:.0f}%")

    # ── Asteroseismology feasibility assessment ───────────────────────────────
    print(f"\n{'─' * 68}")
    print("Feasibility assessment:")

    total_sectors = len(all_rows)
    spoc_120_sectors = [r for r in all_rows
                        if r["author"] == "SPOC" and abs(r["exptime"] - 120) < 10]

    if not spoc_120_sectors:
        print("  ✗ No SPOC 120s data found.")
        qlp_rows_all = by_author.get("QLP", [])
        if qlp_rows_all:
            print(f"  QLP data available ({len(qlp_rows_all)} sector(s), "
                  f"cadence ~600s) — marginal for high-νmax targets.")
        else:
            print("  No QLP data either.  Asteroseismology is NOT feasible.")
    else:
        n = len(spoc_120_sectors)
        total_n = sum(r["n_est"] for r in spoc_120_sectors)
        if n == 1:
            print(f"  ~ {n} SPOC 120s sector — minimal baseline.")
            print(f"    Single sector gives ~25 days; sufficient for marginal νmax detection")
            print(f"    if the sector is contiguous, but Δν will be unreliable.")
        elif n >= 3:
            # Check for gaps
            spoc_120_sectors_sorted = sorted(spoc_120_sectors, key=lambda r: r["sector"])
            sectors_nums = [r["sector"] for r in spoc_120_sectors_sorted]
            gaps = [sectors_nums[i+1] - sectors_nums[i]
                    for i in range(len(sectors_nums)-1)]
            max_gap = max(gaps) if gaps else 0
            if max_gap > 5:
                print(f"  ✓ {n} SPOC 120s sectors — good coverage but large gaps "
                      f"(max gap: {max_gap} sectors = ~{max_gap*27:.0f} days).")
                print(f"    Low duty cycle will inflate PSD window function — "
                      f"calibration injection required (see hd16467 approach).")
            else:
                print(f"  ✓ {n} SPOC 120s sectors — good baseline, "
                      f"sectors roughly consecutive (max gap: {max_gap}).")
        else:
            print(f"  ~ {n} SPOC 120s sectors — adequate for a first attempt.")

        print(f"  Total SPOC 120s cadences: ~{total_n:,}")

        # TGLC note
        tglc = by_author.get("TGLC", [])
        if tglc:
            print(f"  TGLC (PSF photometry) available for "
                  f"{len(tglc)} sector(s) — useful cross-check for crowded fields.")

        # QLP note
        qlp = by_author.get("QLP", [])
        if qlp:
            qlp_600 = [r for r in qlp if abs(r["exptime"] - 600) < 60]
            qlp_200 = [r for r in qlp if abs(r["exptime"] - 200) < 30]
            if qlp_200:
                print(f"  QLP 200s data available ({len(qlp_200)} sector(s)) — "
                      f"secondary cadence check.")
            if qlp_600:
                print(f"  QLP 600s data available ({len(qlp_600)} sector(s)) — "
                      f"coarser cadence, adequate for νmax < 800 µHz.")

print()
