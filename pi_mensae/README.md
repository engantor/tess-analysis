# Pi Mensae — Transit Detection

**Target:** Pi Mensae (HD 39091), a Sun-like G0V dwarf at ~18 pc, V=5.65. It hosts two known planets: Pi Men b, a ~10 MJup companion on a wide eccentric orbit, and Pi Men c, a 4.5 R⊕ super-Earth discovered in TESS Sector 1 photometry (Huang et al. 2018, ApJL 867 L39).

**What was measured:** The transit of Pi Mensae c was recovered from TESS SPOC Sector 1 photometry using a Box Least Squares (BLS) periodogram on a Savitzky-Golay flattened lightcurve (window_length=901).

**Result:** Period at maximum BLS power = **6.266 days** (published: 6.27 d). The phase-folded lightcurve shows the expected flat-bottomed transit dip near phase 0, confirming the detection. This is a reproduction of the published result, not a new discovery.

**Method:** Standard transit-search pipeline. Normalize → Savitzky-Golay flatten → BLS periodogram over 1–20 days at 0.001-day resolution → fold on best period. This is the textbook approach; it works because Pi Men c is a well-known, relatively deep (~0.1%) transit and the star is bright (Tmag ≈ 4.8).

**Limitation:** The same SG flattening that makes this work for transit searches destroys asteroseismic signals in red giants — see `hd16467/README.md` for the full explanation of why giants require a completely different pipeline.

## Run

```bash
cd pi_mensae/
python pi_mensae.py
```

Plots go to `pi_mensae/plots/`.
