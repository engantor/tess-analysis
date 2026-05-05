# Epsilon Eridani — Stellar Rotation Period

**Target:** Epsilon Eridani (HD 22049, ε Eri), a young K2V dwarf at ~3.2 pc, V=3.73. It is one of the closest stars to the Sun and is known to host a wide-orbit giant planet (ε Eri b, ~1 MJup). The star is young (~400–800 Myr) and magnetically active, with large starspots that modulate its brightness as it rotates.

**What was measured:** The stellar rotation period from starspot modulation, using three TESS SPOC sectors stitched together to maximise the baseline.

**Result:** Period at maximum Lomb-Scargle power = **11.178 days** (published: 11.2 ± 0.1 d, Fröhlich et al. 2007). The phase-folded lightcurve shows clean sinusoidal modulation at ~0.5% amplitude from the rotating starspots. This is consistent with the star's young age and fast rotation relative to the Sun (25 days).

**Why not a transit search?** Epsilon Eridani b is a wide-orbit companion (~3.4 AU) and almost certainly does not transit. The star's activity and spot modulation make the Lomb-Scargle periodogram — sensitive to sinusoidal signals — more appropriate than BLS, which requires the flat-bottomed dip shape of a transit.

**Method:** Download all available SPOC sectors → stitch → normalize → Lomb-Scargle periodogram over 1–30 days → fold on peak period. The rotation period is the dominant periodic signal and emerges cleanly from a single periodogram.

## Run

```bash
cd eps_eridani/
python epsilon_eridani.py
```

Plots go to `eps_eridani/plots/`.
