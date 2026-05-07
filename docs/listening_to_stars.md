# Listening to Stars

## An amateur's journey from looking for planets to measuring how stars ring

---

## A note before you start

This document tells the story of a project that started as a question — *how do I do real astronomy with free data?* — and ended up somewhere I didn't expect. We were going to look for planets. We ended up measuring the inside of a star.

I'm going to assume you know nothing. Not because I think you're not smart, but because the language astronomers use is genuinely impenetrable from the outside, and there's no good reason for that to stop you understanding what we did. Every time I introduce a term, I'll explain it. Every time I show a plot, I'll tell you how to read it. Every time I say something the size of a number, I'll give you a sense of what that number means.

If at any point you find yourself thinking *I don't get it*, that's almost always my fault, not yours. Take a breath, go back a paragraph, and we'll walk through it again.

Let's go.

---

## Part 1: The basic question

If you point a camera at a star and take a picture every two minutes for a month, what do you get?

You get a graph.

On the bottom axis, time. On the side, brightness. For most stars, the graph is a flat line, with a bit of fuzz from the camera's noise. The star is sitting there, doing star things, shining steadily.

But sometimes — *sometimes* — the line isn't flat. Sometimes it dips down briefly and comes back up, like someone briefly walked between you and the star. Sometimes it wobbles up and down with a regular rhythm. Sometimes it does something stranger.

That graph is called a **lightcurve** — literally, a curve made of light measurements over time. And lightcurves are the foundation of an astonishing amount of modern astronomy. If you can measure brightness over time, you can find planets going around stars (because the planet briefly blocks a tiny bit of the starlight when it passes in front). You can measure how fast a star spins (because dark sunspot-like patches rotate in and out of view). You can detect the star *vibrating* — and from the vibrations, work out what's happening deep inside it.

This document is about that last one. It's the most surprising and, I think, the most beautiful.

---

## Part 2: TESS — a satellite that takes a picture of the sky every two minutes

Most professional astronomy used to need a big telescope on a mountain, and a queue, and weather, and clouds. None of those are friendly to someone doing this as a hobby. But there are now space telescopes that take pictures continuously, send the data home, and *make all of it public*. Anyone can download it. You don't need permission. You don't need an account. You don't pay.

The one this project uses is called **TESS**, which stands for the **Transiting Exoplanet Survey Satellite**. NASA launched it in 2018 and it's been running ever since. It points its cameras at a patch of sky for about 27 days, takes a picture every two minutes (or every twenty seconds, or every ten minutes — different cadences exist), then rotates to the next patch and starts over.

Each 27-day patch is called a **sector**. As of writing, TESS has observed nearly the entire sky multiple times. Every star bright enough to be on its target list has a record — a pile of brightness measurements stretching back years. The data sits in an archive called **MAST** (the Mikulski Archive for Space Telescopes), and it is, again, free.

> **Why this matters.** If you have an internet connection and a laptop, you have a telescope. Everything in this document was done from a desk, with no special hardware, no special access, and no money spent on data.

---

## Part 3: What we actually want to find in a lightcurve

There are roughly four interesting things that can show up:

> **TRANSITS.** A planet passes in front of its star (from our viewing angle, anyway). For the few hours the planet is in the way, the star looks slightly dimmer — typically less than 1% dimmer, often much less. On a graph, this looks like a small U-shaped dip, repeated regularly every time the planet completes an orbit. This is how most known exoplanets were discovered.

> **ECLIPSES.** Same idea, but with two stars instead of a planet. If two stars orbit each other and we happen to be looking at them edge-on, each one passes in front of the other in turn. The dips are usually deeper and more dramatic than planet transits.

> **ROTATION.** If a star has dark patches on its surface — the equivalent of sunspots — and it spins, those patches rotate in and out of our line of sight, making the brightness wobble up and down with the rotation period.

> **PULSATION AND OSCILLATION.** The star itself is wobbling. Its surface is rising and falling. Its brightness is going up and down because the star is *physically* changing size or temperature in a rhythmic way.

The first three were what I expected to find. The fourth is what we ended up actually finding.

---

## Part 4: Pi Mensae — getting the equipment working

You don't start a project like this on a hard target. You start by checking that your gear actually works on something you already know the answer to. The astronomy version of this is reproducing a published result — pick a star where someone else has already done the analysis and confirmed what's going on, run your own pipeline on the same data, and check that you get the same answer.

The star I picked was **Pi Mensae**, in the southern constellation Mensa. It's a bright, sun-like star, about 60 light-years away. In 2018, professional astronomers found a small planet orbiting it — about twice the size of Earth, going round its star every 6.27 days. They found it the same way: a dip in the TESS lightcurve every 6.27 days.

So I downloaded the same TESS data, ran my own analysis, and looked for that dip.

### What the result looked like

[FIGURE: pi_mensae/plots/folded.png]
*Figure 1. Pi Mensae c — phase-folded lightcurve. The planet's transit shows up as the sharp dip near phase zero. Brightness on the vertical axis is normalised so 1.000 means "no transit happening."*

The plot above is called a **phase-folded lightcurve**. Here's how to read it.

The brightness data covers many orbits of the planet — many transits. Rather than showing all of them spread out across time, we *fold* them on top of each other. We say: "every 6.27 days the planet should transit; let's stack all those moments and see if there's a consistent dip when we line them up."

The horizontal axis is time relative to the predicted transit, in days. So zero is the moment the transit happens. Negative numbers are before the transit, positive after. The vertical axis is the star's brightness, normalised so that "no transit" equals 1.0.

If the planet weren't there, the line would just be flat fuzz. If the planet *is* there, you see exactly what's on the plot: a sharp dip right at zero — the moment the planet crosses in front of the star — and flat fuzz everywhere else.

The dip is small. Look at the vertical axis: it goes from about 0.99975 to 1.0005. The actual brightness drop is around 0.025% — a quarter of one tenth of one percent. This is what professional planet-hunting actually looks like. We're not seeing dramatic eclipses; we're seeing the planet equivalent of a moth briefly fluttering across a streetlight from a thousand miles away.

The fact that we recovered it cleanly meant the pipeline worked. Time to point it at something where the answer wasn't already known.

---

## Part 5: Epsilon Eridani — pivoting from planets to rotation

The next target was **Epsilon Eridani**, a star about 10 light-years away — close, by stellar standards. It's slightly smaller and cooler than the Sun, and it's young, which means it's still spinning fast and has lots of magnetic activity. Eps Eri has a known planet, but the planet doesn't transit (we're not looking at it edge-on, so it never crosses in front of the star from our viewpoint). So a transit search was pointless.

But there was something else to look for: **rotation**.

Eps Eri has dark, magnetically-active regions on its surface — like sunspots but bigger. As the star rotates, those regions rotate into and out of our view, and the brightness wobbles up and down with the rotation period. From the wobble, you can directly measure how fast the star spins.

Predicted rotation period from the literature: about 11 days.

### How we measure rotation: thinking in waves instead of time

Here's where it gets interesting, because we have to introduce a new way of looking at data.

When you see brightness wobbling over time, you might think the obvious thing to do is look at the wobble and measure how long one cycle takes. And for very clean data, that works. But real data is messy. The wobbles are often subtle, hidden in noise, and there might be more than one rhythm at once. Trying to spot the period by eye is hopeless.

So instead, we do something almost magical called a **periodogram**. The idea is:

> *"Suppose the data has a 1-day cycle in it. How strong is that cycle?"*
> *"Suppose it has a 1.5-day cycle. How strong is that?"*
> *"Suppose it has a 2-day cycle… a 5-day cycle… an 11-day cycle?"*

We test thousands of possible cycle lengths, one by one, and for each one we compute how well the data is described by that cycle. The result is a graph: cycle length on the bottom, "strength of cycle" on the side. Wherever the graph has a tall peak, that's a real rhythm in the data.

It's like asking "what musical note is this hum?" by sliding a tuning fork through every possible note until one resonates. The resonating note is the answer.

If Eps Eri rotates with an 11-day period, the periodogram should have a tall peak at 11 days. It does. The peak comes in at almost exactly 11 days. Spinning at the predicted rate. Pipeline working again, on a different kind of measurement.

This is the moment in the project where I stopped just calibrating and started doing things where the answer wasn't fully known beforehand.

[FIGURE: eps_eridani/plots/eps_eri_periodogram.png]
*Figure 2. Lomb-Scargle periodogram for Epsilon Eridani. The horizontal axis is candidate rotation period in days; the vertical axis is the strength of that rhythm in the data. The tall spike near 11 days is the rotation peak — that's the star's spin period sticking up out of the noise. The smaller bumps to either side are aliases and harmonics of the same rhythm; the periodogram doesn't try to clean them up because the main peak is what we came for.*

To read a periodogram, you scan along the bottom looking for the tallest narrow peak. Tall means "this rhythm fits the data well." Narrow means "the data really does have just this one cycle, not a fuzzy range of nearby ones." Eps Eri's peak is both — tall, narrow, sitting right where decades of independent ground-based work said it should sit.

---

## Part 6: HD 16467 — the moment everything changed

I picked HD 16467 thinking it would be a fun **binary star** investigation. Binary stars are pairs of stars orbiting each other — extremely common in the universe, and HD 16467 was listed in catalogues as a known visual double. The plan was to look for whether the two stars eclipsed each other (a real eclipsing binary), or whether one of them was rotating, or maybe even pulsating in some interesting way.

Then we ran the script that pulled the star's basic information from the standard astronomical databases — its temperature, size, and so on — and the answer came back:

### **K0III**

That short string changed the project completely. Let me unpack it.

### The cosmic name tag system

Astronomers sort stars by two main things: temperature (which is closely related to colour) and luminosity (how much light they pump out). Combining the two gives you a label. The temperature is encoded by a letter — O, B, A, F, G, K, M — running from hottest to coolest. The Sun is a G2 star: middling temperature. Cooler than that you get K stars (orange) and M stars (red). The number after the letter just refines the temperature within the letter's range.

The luminosity bit is a Roman numeral. **V** means main-sequence — a normal, ordinary star fusing hydrogen in its core, like the Sun. **III** means **giant** — a star that has run out of hydrogen in its core, swelled up to many times its original size, and is now in a much later, much puffier phase of its life.

So **K0III** means: a moderately cool orange star, in its giant phase. Not a sun-like main sequence dwarf. Something completely different.

When the script reported HD 16467 was K0III, with a radius about 10 times the Sun's, I had to throw out the original plan. Eclipses, rotation, the kinds of variations we'd been hunting for — those are mostly things that happen on dwarf stars. Giant stars do something else entirely.

> **Giant stars *ring*.**

[FIGURE: hd16467/plots/hd16467_aperture.png]
*Figure 3. The TESS pixel cutout around HD 16467. The reddish square outlines the aperture mask used to sum up flux. Each TESS pixel is about 21 arcseconds on a side — enormous by ground-based standards. The catalogued visual binary companion sits inside that same aperture; the two stars are blended into a single pixel.*

#### Why a single TESS pixel can't separate the two stars

TESS's cameras are deliberately wide-angle. To photograph nearly the whole sky in two-minute snapshots they had to give up resolution: each pixel covers a 21 arcsecond patch. That's about 1/170th of the diameter of the full moon, but it's still vastly larger than the typical separation between members of a stellar binary. HD 16467's companion sits roughly 2.5 arcseconds from the primary — close enough that the two stars fall into the same TESS pixel, and far closer than TESS's optics can possibly resolve. From the spacecraft's point of view, "HD 16467" is one blurry point of light containing two physically separate stars.

That sounds like a problem for our analysis, and you'd be right to worry. If the two stars contributed comparable amounts of light, we wouldn't be able to tell which one was producing any wobble we saw. So before going further we needed to convince ourselves that what we eventually detected was coming from the K0III giant and not from the smaller dwarf companion.

Four pieces of evidence make that case:

1. **Frequency match.** The oscillation envelope we eventually measured sits at 43 µHz — exactly where scaling-relation theory predicts a 10-solar-radius giant should ring. If a sun-like dwarf were responsible, it would oscillate around 3000 µHz, two orders of magnitude higher than what we see.
2. **Granulation timescales.** The smooth, broad-band background in the spectrum has characteristic timescales of ~2 hours, again exactly what a 10-solar-radius giant should produce. A dwarf's granulation runs in minutes, not hours.
3. **Amplitude.** Solar-like oscillations on giants are hundreds to thousands of ppm. On dwarfs they're ones to tens of ppm. The signal we measured is far too loud to come from anything but a giant.
4. **Stellar type.** HD 16467 A is the K0III giant; the catalogued companion is several magnitudes fainter and a much smaller, denser star. Even if the companion were oscillating, it would contribute a tiny fraction of the total light, and its envelope would sit at completely different frequencies.

In other words, the physics is telling us — independently and consistently — that the signal in our spectrum comes from the giant. The blended pixel doesn't actually compromise the analysis.

---

## Part 7: Asteroseismology — listening to stars

The technique I'm about to describe is called **asteroseismology**. The word is built from "astro" (star) and "seismology" (the study of earthquakes — specifically, how the vibrations from earthquakes tell us about the inside of the Earth). Asteroseismology is exactly that, applied to stars: studying their vibrations to learn what's inside them.

Here's the picture.

### The bell

Imagine a bronze bell. Strike it. It rings. The note it makes — its pitch — depends on its size and how the metal is shaped. A small, tight bell rings high. A huge cathedral bell rings deep. Listen carefully and you can hear not just the main note, but a whole spectrum of harmonics — overtones layered on top of the fundamental. From those harmonics, an experienced ear can deduce the bell's shape, its thickness, even cracks invisible from the outside.

> **A star is a bell.**

### How a star gets struck

Inside a star, the surface is covered in giant cells of plasma — chunks of hot stuff rising from the depths, cooling, and sinking back down. This is called **convection**, and it's the same process that makes a pot of porridge bubble on the stove, except scaled up to the size of, well, a star. On the Sun, each convection cell is roughly the size of Texas. On HD 16467, which is ten times the Sun's size, each cell is bigger than the entire Earth's orbit.

All this constant boiling generates noise — pressure waves rumbling through the star's interior. Most of those waves dissipate. But some of them, with just the right wavelength, get *trapped* inside the star and bounce around like sound waves inside a bell. Those are the ones we can detect.

The trapped waves cause the surface of the star to rise and fall, very slightly, with a regular rhythm. As the surface rises and falls, the brightness goes up and down — by an absolutely tiny amount, often less than 0.01%, but TESS can see it.

So when we listen carefully to the brightness wobble of a star like HD 16467, we're not just seeing it spin. We're hearing it ring.

### Two things mixed together

It's worth being explicit about a subtlety. What we measure in the lightcurve is a single signal — brightness over time. But that signal is the sum of two completely different physical processes happening on the star at once.

The first is **granulation** — the bubbling. It's not periodic, it's not regular, but it does have a characteristic timescale. On a giant star, the bubbles take hours to rise and sink. So the brightness wobbles produced by granulation have a smooth, broad-band character, with most of the wobble happening on hour timescales.

The second is **oscillation** — the ringing. This *is* periodic. The star vibrates at specific frequencies, like a bell sounding specific notes. The ringing produces sharp, well-defined peaks in the spectrum, layered on top of the smooth bubbling background.

Most of the work in this project was figuring out how to separate those two contributions cleanly. The bubbling tells us about the surface. The ringing tells us about the interior. Both are interesting, but they're different kinds of evidence and need to be treated differently.

---

## Part 8: What we learned about HD 16467

### Looking at the lightcurve

The first thing to do with any star is just look at its raw brightness data. Here's what HD 16467's looks like.

[FIGURE: hd16467/plots/seismic_lc.png]
*Figure 4. HD 16467's full TESS lightcurve. The data exists in three sectors: one in 2020 and two in 2023, with a multi-year gap between them.*

The horizontal axis is time, in days, measured from a TESS-internal reference date. The vertical axis is brightness, expressed in **ppm** — *parts per million*. A ppm is a way of saying "very small fraction." 1 ppm is one millionth, or 0.0001%. So a wobble of ±1000 ppm means the star is changing brightness by about ±0.1% — a tenth of one percent.

You can see the data exists in two clumps: one chunk in 2020, then a big empty gap, then more data in 2023. Those are the different sectors TESS observed this star in. The gap is real — TESS just wasn't pointing at HD 16467 during those years.

The data itself is noisy-looking but bounded between roughly ±2000 ppm. Nothing dramatic jumps out. But zoom in…

[FIGURE: hd16467/plots/hd16467_zoom.png]
*Figure 5. HD 16467 zoomed to the first 10 days. Now the structured wobble is obvious. This is the star itself, ringing and bubbling, not random camera noise.*

Now we're looking at just the first 10 days of one sector. And there it is — clear, structured wobbling. Brightness rising and falling in patterns spread over hours. This is *not* random camera noise; it's much too structured for that. This is the star itself, doing something.

The wobble is small (about 0.1% peak-to-peak) but real, and it has texture. The dips and rises happen on timescales of hours, not days. There's no obvious clean repeating period — the pattern looks similar but not identical from one chunk to the next.

This is what stellar oscillation plus granulation looks like, mixed together, in a real lightcurve. The star is ringing on top of bubbling.

### Looking at the data inside-out

To make sense of the wobble, we use the same trick we used for Epsilon Eridani — we ask, *for every possible rhythm, how much of that rhythm is in the data?*

For asteroseismology, we don't think in periods (days per cycle). We think in **frequencies** (cycles per second). The unit is the **microhertz** — abbreviated **µHz** — which means "one millionth of a cycle per second." It sounds tiny, but at the scales we're working with, it's natural. A signal at 1 µHz cycles once every 11.6 days. A signal at 100 µHz cycles once every 167 minutes.

For a giant star like HD 16467, the trapped pressure waves should ring at frequencies somewhere around **40 to 50 µHz** — about one cycle every 6 hours.

This was a prediction, made before we ran the analysis. It comes from a piece of physics called the **scaling relation**, which says: the ringing frequency of a star depends on its size and temperature in a known way. Plug in HD 16467's size and temperature, and you get a predicted "note" of around 43 µHz.

[FIGURE: hd16467/plots/seismic_psd_full.png]
*Figure 6. HD 16467's full power spectrum, plotted on a log-log scale from 0.5 to 300 µHz. This is the panoramic view: you can see the broad background sloping down from low frequencies (granulation) and the flat noise floor at high frequencies (camera noise). Somewhere in between sits the oscillation envelope. The next plot zooms in on it.*

Then we ran the analysis. Here's what came back at the relevant scale.

[FIGURE: hd16467/plots/seismic_psd_numax.png]
*Figure 7. HD 16467 power spectrum, zoomed in on 10–150 µHz. The dotted green line marks the predicted ringing frequency at 43.3 µHz. The lump of power around 30–50 µHz is the star's oscillation envelope — the actual ringing.*

This plot shows what's called a **power spectrum**. On the horizontal axis, frequency in µHz. On the vertical axis, "power" — basically, how much of each frequency is present in the data. The dotted vertical green line marks the predicted note, at 43.3 µHz.

Now: what do you see?

Look at the lump in the data, peaking right around 43–46 µHz. **That's the star's ringing.** You're literally looking at the star's note.

It isn't a single sharp peak because the ringing isn't perfectly steady — the star is being struck by random convective bubbles, so different frequencies near the main note get excited at different times. The collective effect is a *bump* of power, called the **oscillation envelope**, centred on what's called **ν_max** (pronounced "new max"), the frequency where the power is greatest.

For HD 16467, ν_max came out at 43.4 µHz. The prediction was 43.3.

> **Why this matters.** That match is, frankly, ridiculous. Three different methods of analysing the same data all landed within 1 µHz of each other and within half a percent of the theoretical prediction. The probability of this being random noise is essentially zero. The star really is ringing at the frequency theory says it should.

### The fitted model — pulling the bell out of the bubbling

The next step is to fit a mathematical model to the spectrum that separates out the different physics happening at different frequencies. The model has four pieces, each one corresponding to a real physical process on the star.

[FIGURE: hd16467/plots/seismic_harvey_fit.png]
*Figure 8. The Harvey + Gaussian envelope fit to HD 16467's power spectrum. The black solid line is the total fitted model. The four dashed lines are the individual components: two granulation contributions (blue and orange — different bubble sizes), the Gaussian oscillation envelope (green — the actual ringing), and the white noise floor (red horizontal line). The grey scatter is the raw data; the darker grey curve is the lightly smoothed version we fit to.*

Read the plot from left to right.

**At low frequencies (the leftmost portion, below ~10 µHz)** the granulation background dominates. Granulation produces what physicists call a "Lorentzian" — a curve that's high and flat at low frequencies, then bends and rolls off at higher ones. The bend happens at a frequency that depends on the *timescale* of the underlying physical process. Big, slow bubbles produce Lorentzians that bend at low frequencies; small, fast bubbles bend higher up.

The first Lorentzian (the blue dashed curve) bends around 0.1 µHz, corresponding to a granulation timescale of about **2.3 hours**. That's the typical lifetime of the largest convection cells on this star. The second (orange) bends higher, around 0.4 µHz, corresponding to a timescale of about **0.9 hours** — smaller, faster convection cells, layered on top of the slow ones. Real giants have a hierarchy of cell sizes, and we're fitting two of them.

Are those numbers physically reasonable? Yes — and that's the test. On the Sun, granulation timescales are about 5–10 minutes. The Sun's convection cells are roughly Texas-sized. Convection theory says timescales should scale with the size of the cells, which scales with the size of the star. HD 16467 is ten times the Sun's radius, so its cells should be hundreds of times the Sun's, with timescales hundreds of times longer — hours, not minutes. The fit lands right where theory predicts.

**At intermediate frequencies (around 30–60 µHz)** the granulation has dropped enough that the oscillation envelope sticks up above it. That's the Gaussian (the green dashed bump). It's centred at ν_max = 43.4 µHz with a width of about 8 µHz. This is the star's "voice" — the resonant ringing of trapped pressure waves bouncing inside its interior.

**At high frequencies (above ~100 µHz)** even the small-cell granulation has rolled off, and what's left is the camera noise floor — a constant value across all frequencies, called the **white noise component**. The red horizontal dashed line shows it sitting at about 1 ppm²/µHz. White noise is purely instrumental — it's the camera doing camera things, no astrophysics involved.

**The total model** (the solid black curve) is the four components added together. The fact that this curve traces the smoothed data so closely — with no big residuals, no missing features, no surprises — is what tells us the model is *complete*. We can describe the entire spectrum, from low to high frequencies, with just two granulation timescales, one oscillation envelope, and one noise floor. That's the whole physics of the star, in four numbers.

### Cross-checking with pySYD

A homemade pipeline is only as good as the cross-checks you put it through. The professional standard for asteroseismic analysis is a Python tool called **pySYD** — the modern descendant of the SYD pipeline that was used to characterise tens of thousands of red giants from Kepler data. It runs the same Harvey-plus-Gaussian fit we wrote, but with a thoroughly tested codebase, automatic peak detection, and Monte Carlo uncertainty estimates.

We pointed pySYD at the same lightcurve and asked it to find ν_max from scratch — no help, no priors beyond a rough starting estimate. Its answer: **44.5 ± 0.5 µHz**. Our home-grown answer was 43.4 ± 0.1. The two agree to about 1σ.

[FIGURE: hd16467/plots/pysyd_global_fit.png]
*Figure 9. The standard pySYD diagnostic page for HD 16467. Each small panel shows a different aspect of the analysis: the lightcurve at top, the smoothed power spectrum, the Harvey background fit, the autocorrelation that gives Δν, and the échelle diagram. This single page is the kind of output professional asteroseismologists actually look at.*

Don't try to read every panel — even pros only spot-check. The bottom line is that all the panels agree with each other and with our independent fit. The signal is in the data; pySYD found it; our pipeline found it; we all agree where it is.

### Verifying the result independently — the split-half test

Once we had a candidate detection, we needed to make sure it was real. There are several standard checks; one of the most important is called the **split-half test**. The idea is simple: if the signal is genuine, splitting the data in half and analysing each half independently should give the same answer twice. If the result depends on which half of the data you look at, something is wrong.

[FIGURE: hd16467/plots/split_half_psd.png]
*Figure 10. Split-half consistency check. Left: the 2020 sector alone gives ν_max = 42.6 µHz. Right: the two 2023 sectors together give 43.4 µHz. Both halves independently find the same envelope at the predicted frequency, three years apart.*

On the left is sector 31 (the 2020 data); on the right is sectors 70 and 71 (the 2023 data). Both halves see a bump of power around 42–43 µHz. Both halves see it at the predicted frequency. The signal is stable across three years, exactly as solar-like oscillations should be.

Three independent methods, three sectors of data, three years apart — all pointing to the same ringing frequency. The detection is real.

### What "marginal" means and why it matters

For all that, the formal classification of the HD 16467 detection is **marginal**. The reason is a number called **H over background** — the height of the oscillation envelope divided by the surrounding noise level. For HD 16467, that came in at 4.4. The professional cutoff for "convincing single-target detection" is 5.

Why so close to the line? Because of the data itself. HD 16467's three sectors are spread across a 1115-day window — about three years — but TESS was only actually looking at the star for maybe 80 days total. The big gap *between* the sectors creates a kind of mathematical interference pattern that smears the spectrum slightly, diluting the height of the envelope.

The signal is real. The result is solid. It just isn't a slam-dunk on this dataset alone. With more sectors, especially consecutive ones, the H/background ratio would push past 5 and the detection would be uncontestable.

---

## Part 9: HD 206948 — the same technique, a stronger result

If HD 16467 was the discovery that the technique works, HD 206948 was the demonstration that it works convincingly.

HD 206948 is another K-type giant — slightly cooler than HD 16467 (K2III versus K0III), slightly bigger, slightly farther away. It's in the southern constellation Microscopium, visible from the southern hemisphere for half the year.

We picked it because it had no prior variability classification — nobody had specifically looked for ringing in its data — and because it had reasonable TESS coverage. The plan was the same as HD 16467: find ν_max, fit the spectrum, see what falls out.

The expected ringing frequency from the scaling relation, given HD 206948's size and temperature: about 33 µHz. (Lower than HD 16467 because HD 206948 is bigger, and bigger stars ring at lower frequencies, the same way bigger bells ring at lower notes.)

### What we found

[FIGURE: hd206948/plots/seismic_psd_numax.png]
*Figure 11. HD 206948 power spectrum, zoomed in on 5–100 µHz. The oscillation envelope around 30–40 µHz is sharper and more obvious than HD 16467's — a stronger detection from a single uninterrupted sector of data.*

[FIGURE: hd206948/plots/seismic_harvey_fit.png]
*Figure 12. HD 206948 power spectrum with Harvey background and Gaussian envelope fit. Same components as HD 16467 (two granulation Lorentzians, one Gaussian, one white-noise floor), but the envelope is taller relative to the background — H/background = 7.7 against HD 16467's 4.4.*

The fit worked beautifully. The oscillation envelope is sharper and more obvious than HD 16467's. The H/background ratio came in at **7.71** — well above the convincing-detection threshold.

The measured ν_max was 36.6 µHz. The predicted value was 33 µHz. The 10% difference looks bigger than it is — the prediction depended on assuming the star's mass, which we didn't actually know. If the real mass is about 1.66 times the Sun's mass instead of the 1.5 we assumed, the predicted value shifts up to about 36 µHz, almost exactly matching what we measured.

> **In other words: by measuring how the star rings, we *measured its mass*.**

### Why a single-sector result was stronger than a three-sector result

This was the surprise of the project. HD 16467 had three sectors of data, total baseline about three years. HD 206948 had one sector of data, total length about 27 days. By any normal logic, more data should give a better answer.

Except. The HD 16467 data had two big gaps in it — multi-year stretches where TESS wasn't looking. HD 206948's single sector was 27 *consecutive* days. No gaps.

Continuity matters more than total length, for this kind of measurement. A short, clean recording is better than a long, choppy one when what you're measuring is a wobbling pattern. The gaps in HD 16467's data made the spectrum messier, even though there was technically more total data.

This kind of insight — "your intuition about more being better is wrong, in this specific way" — is the sort of thing that comes out of actually doing the work rather than reading about it.

### The big result: mass and radius

When you have both ν_max (the centre of the ringing envelope) and another quantity called **Δν** (pronounced "delta new" — the spacing between individual notes within the envelope), you can derive both the mass and the radius of the star from first principles, using physics formulas that depend only on the measured frequencies and the star's temperature.

For HD 206948, we got both numbers cleanly. The result:

> **ASTEROSEISMIC MASS AND RADIUS OF HD 206948**
> **Mass:** about 1.66 solar masses (1.66 times the mass of our Sun)
> **Radius:** about 12 solar radii (12 times the Sun's radius)

The radius was important to check. Independent measurements (using **parallax** — how the star's apparent position shifts as Earth moves around the Sun) had previously estimated the radius at about 12.5 solar radii. Our asteroseismic measurement landed within 5% of that, even though the two methods rely on completely different physics. They agreed.

This is what real science feels like. Two ways of measuring the same thing, arriving at the same answer — that's not a coincidence, that's confirmation that both methods know what they're talking about.

### The échelle diagram — seeing individual notes

The final piece of evidence was the prettiest. Once you have Δν (the spacing between notes), you can do something called an **échelle diagram**. The name comes from the French for "ladder."

Here's the idea. Take the power spectrum. Cut it into strips, each Δν wide. Stack the strips on top of each other. If the ringing has *real, individual notes* — like the notes of a struck bell — they should line up vertically when you stack the strips. Real modes form clean ridges.

[FIGURE: hd206948/plots/echelle.png]
*Figure 13. HD 206948 échelle diagram. Each horizontal row is one Δν-wide slice of the power spectrum, stacked on top of the next. Brightness shows how much power is at each frequency. The vertical ridges are individual oscillation modes — the star's resolved notes. Contrast: 0.634 (well above the 0.3 threshold for "real modes").*

The échelle is one of those plots that takes a moment to click. The horizontal axis is **frequency modulo Δν** — that is, the residual when you divide each frequency by Δν and keep only the leftover. The vertical axis is the actual frequency, increasing upward. So as you go up the plot, you're moving through the oscillation envelope row by row, with each row covering one Δν of frequency space.

If the star really does ring at evenly-spaced frequencies — if the notes form a regular ladder, separated by exactly Δν — then every note will fall at the same horizontal position on every row. They line up into a vertical ridge. If the data is noise, there's no preferred horizontal position and the diagram looks like static.

Two things to notice in HD 206948's diagram. First, there are clearly defined vertical ridges, not random scatter. That's the smoking gun for *real* p-modes — the dominant family of acoustic oscillations in giant stars. Second, the stronger ridge corresponds to **ℓ = 0** modes (radial oscillations, where the whole star pulses in and out spherically), and the slightly fainter neighbouring ridge corresponds to **ℓ = 2** modes (quadrupolar oscillations, where opposite ends of the star bulge while the equator pinches). The horizontal *separation* between those two ridges — called the **small spacing** — is set by physics in the star's deep core. It's one of the few astronomical observables that probes the central regions directly.

For HD 206948, the ridges are there. The contrast measurement — basically, "how clearly do the ridges stand out?" — came in at 0.634, well above the threshold of 0.3 for "definitely real."

In plain terms: we didn't just hear HD 206948 ring. We resolved its individual notes. We can identify which is the fundamental, which are the harmonics. We can, in principle, use the relative spacings to probe the *core* of the star.

That's a striking thing to be able to do as an amateur. It's the same technique professional asteroseismologists use, on the same kind of data, applied to a star nobody had looked at before.

---

## Part 10: What this all amounted to

Let me restate the actual scientific findings, plainly.

We took TESS data — free, public, available to anyone — on two K-type giant stars that nobody had specifically looked at for stellar oscillations. Using a pipeline we built ourselves in Python, with open-source tools, we:

> **HD 16467.** Confirmed that HD 16467 rings at **43.4 ± 1 µHz**, exactly as theory predicts for its size and temperature, with granulation timescales of 2.3 and 0.9 hours, also consistent with theory. The detection is marginal but real, validated by multiple independent methods including split-half consistency across three years.

> **HD 206948.** Confirmed that HD 206948 rings at **36.6 µHz** with a clean Δν of 3.64 µHz, individual modes resolved in the échelle diagram. Derived an asteroseismic mass of 1.66 solar masses and a radius of 12 solar radii — both consistent with prior independent measurements. The detection is convincingly above the professional threshold.

Neither result is going to overturn modern astrophysics. But they are real, repeatable, defensible measurements — the same kind that go into professional asteroseismology papers. Both stars are now characterised in ways they weren't before this project started.

The repository — at *github.com/engantor/tess-analysis* — contains every script, every plot, the complete reasoning, and the documents that describe the methods. Anyone can take the work, reproduce it, build on it, or critique it.

That last bit is the point. Real science is reproducible.

---

## Part 11: How the code works

This chapter is for readers who want a sense of *the shape* of the analysis. You don't need to write Python to follow along. If you do, the patterns here are worth stealing — they're the result of getting the same problem wrong several times in a row and finally getting it right.

### Project layout

The repository is small enough that you can hold it in your head:

```
tess-analysis/
├── README.md
├── requirements.txt
├── pi_mensae/         # transit reproduction
├── eps_eridani/       # rotation
├── hd16467/           # asteroseismology, marginal
├── hd206948/          # asteroseismology, convincing
└── docs/              # this document
```

Each star gets its own subdirectory. Inside each, there's typically a `_context.py` script (database lookup), a main analysis script (`hd16467_seismic.py`, `hd206948_seismic.py`, etc.), a `seismic_utils.py` module that holds shared code, and a `plots/` folder where every figure lands. Results that future scripts depend on are saved as JSON. Result text that I want to read by eye lives in `README.md` files. The same conventions repeat from one star to the next, which is what made each new analysis cheaper to write than the last.

The whole thing runs in a Python virtual environment — `venv/` at the project root — with about a dozen packages pinned in `requirements.txt`. No global installs. The environment is reproducible: one `pip install -r requirements.txt` and you're running the same versions of everything I did.

### Pattern 1: The context lookup

Before I touch a star's lightcurve, I run a short script that queries every relevant database. For HD 16467 that's `hd16467_context.py`. The script asks SIMBAD for identifiers and spectral type, Gaia DR3 for temperature, surface gravity, and metallicity, the TESS Input Catalogue (TIC) for radius, and the Washington Double Star catalogue (WDS) for known companions. It then prints a summary, and — crucially — uses the stellar parameters to compute the *predicted* asteroseismic signature using scaling relations.

That last step matters. Predicting before measuring is the difference between confirming a signal and inventing one. The script writes out, for example, "ν_max prediction: 43.3 µHz" before any TESS data has been looked at. When the measurement comes in at 43.4 µHz, that's a real prediction matched, not a fudge factor.

The actual code is short — maybe thirty lines that matter. The pattern looks like this:

```python
from astroquery.simbad import Simbad
from astroquery.mast import Catalogs
from astroquery.vizier import Vizier

simbad = Simbad()
simbad.add_votable_fields("sp_type", "V", "B", "plx_value")
simbad_result = simbad.query_object("HD 16467")

tic_result  = Catalogs.query_object("HD 16467", catalog="TIC", radius=0.02)
gaia_result = Vizier(row_limit=1).query_object(
    "HD 16467", catalog="I/355/gaiadr3", radius=5*u.arcsec)
```

Each `astroquery` package handles a different astronomical database, but they all give back the same shape of object — an astropy `Table` with named columns. From there it's just `simbad_result["sp_type"][0]` and so on.

This is what I mean by *the shape* of the work. The whole "what do we know about this star?" problem reduces to a handful of queries against publicly-indexed catalogues, all reachable from a single Python script. There is no library, archive, or service involved that costs money or requires permission.

### Pattern 2: Loading TESS data

The package we use is called `lightkurve`. It abstracts MAST — the giant NASA archive that holds the TESS data — into three operations: search, download, plot.

```python
import lightkurve as lk

search = lk.search_lightcurve("HD 16467", mission="TESS", author="SPOC")
lc_collection = search.download_all()
```

That's it. After those two lines, `lc_collection` is a Python object containing every SPOC-pipeline lightcurve TESS has ever taken of HD 16467. You can index into it, plot it, iterate over its sectors. It's an enormous amount of NASA infrastructure exposed as a couple of method calls.

The `author="SPOC"` argument matters. TESS data exists in several pipeline flavours: SPOC (the official Science Processing Operations Center reduction), QLP (the Quick-Look Pipeline used for fainter targets), and TGLC (a custom pipeline that handles crowded fields better). SPOC is the gold standard for asteroseismology because it preserves the long-timescale variability we care about. The other pipelines apply detrending steps that can suppress exactly the kind of slow wobbles we're trying to measure. For HD 206948, SPOC didn't have all the sectors we wanted, so we used `TESS-SPOC`, the same processing applied to full-frame images. Picking the wrong pipeline silently destroys your science. This is the kind of thing that takes weeks to figure out the first time.

### Pattern 3: Lightcurve preparation

Once you have a lightcurve in memory, there's a temptation to "clean it up" — remove trends, smooth it, normalise it. Resist most of those impulses. The asteroseismic signal *is* the trend, in some sense. Anything that flattens the data flattens the signal too.

What we do instead, for each sector independently:

1. Drop NaN cadences (occasional dropouts where the spacecraft missed a measurement).
2. Compute the median flux for that sector.
3. Express each cadence as a fractional deviation from the median, in units of parts per million: `ppm = 1e6 * (flux / median - 1)`.
4. Apply a 5σ outlier clip to remove cosmic-ray hits and other bad cadences.

That's the entire preparation. No smoothing, no detrending, no `flatten()` call, no high-pass filter. The early version of the pipeline used `flatten()` because that's what you do for transit searches — it removes the slow stellar variability that obscures planet dips. When I ran that version on HD 16467, the asteroseismic signal disappeared. Of course it did: I had explicitly asked the code to remove it.

This is one of those lessons that doesn't generalise. The right preparation depends on what you're looking for. For transits, flatten. For oscillations, don't.

### Pattern 4: The power spectrum, computed honestly

The next step is converting the time series into a power spectrum. The mathematical workhorse is the **Lomb-Scargle periodogram**, implemented in `astropy.timeseries.LombScargle`. It handles the irregular spacing of TESS data (the gaps between sectors, the dropouts within sectors) gracefully.

```python
from astropy.timeseries import LombScargle
power = LombScargle(t_days, flux_ppm).power(freq_cd, normalization="psd")
```

That returns a number for each frequency — *some* number proportional to the power at that frequency. But what unit is it in? That's where I learnt the next painful lesson: the raw output is *not* in any physical unit. It's in arbitrary "Lomb-Scargle units" that depend on the data length, the number of points, the gaps, and the choice of normalisation.

For asteroseismology you need the answer in **ppm² per µHz**, and you need it to be quantitatively right, because you're going to compare its absolute value against theoretical predictions. The fix is calibration: inject a sine wave of known amplitude into the actual time array, run the same Lomb-Scargle, and figure out what scale factor turns the raw output into the right physical units.

```python
A_cal, nu_cal = 10.0, 43.0  # 10 ppm sine at 43 µHz
flux_with_injected = flux_ppm + A_cal * np.sin(2*np.pi*nu_cal_cd*t_days)
peak_raw = LombScargle(t_days, flux_with_injected).power(...).max()
expected_psd = A_cal**2 / (2.0 * df_uhz)
PSD_SCALE = expected_psd / peak_raw
```

After that, `psd = power_raw * PSD_SCALE` is genuinely in ppm²/µHz, and the peak heights mean what you think they mean. This calibration step is the single change that moved the project from "playing with data" to "doing science." Without it, the absolute amplitudes are guesses; with it, you can compare against literature values and they line up.

### Pattern 5: The Harvey + Gaussian fit

Now to extract physics from the spectrum. The model is

```
P(ν) = Harvey₁(σ₁, τ₁) + Harvey₂(σ₂, τ₂) + H · exp[-½((ν-ν_max)/σ_env)²] + C
```

— two Harvey Lorentzians for granulation, one Gaussian for the oscillation envelope, one constant for white noise. Eight parameters in total. We fit it with `scipy.optimize.curve_fit`:

```python
from scipy.optimize import curve_fit
popt, pcov = curve_fit(log10_model, nu_uhz, log10(psd_smoothed),
                       p0=initial_guesses, bounds=(lo, hi),
                       maxfev=30000, method="trf")
```

Two details that earn their keep. First, the fit is done in **log10 power space**, not linear. The spectrum spans several orders of magnitude — granulation can be 10⁵ ppm²/µHz at low frequencies and the noise floor is ~1 ppm²/µHz at high frequencies. Linear fitting gives all the weight to the loud low-frequency end and ignores the quiet high-frequency end where the envelope sits. Log fitting gives every decade equal weight.

Second, the **initial guesses matter enormously**. `curve_fit` is a local optimiser — it walks downhill from where you start it. If the starting point is bad enough, it converges to a local minimum that doesn't match any real physics. So we use the data itself to construct sensible starting values: read the PSD value at 2 µHz to estimate granulation amplitude, at the predicted ν_max to estimate envelope height, and so on. This is in `seismic_utils.fit_harvey_model`. Without these, the fit wanders off and reports nonsense.

The output is a parameter dictionary with `nm` (the fitted ν_max), `H` (envelope height), the granulation timescales `t1` and `t2`, and a "significance" — `H` divided by the granulation background at ν_max. We classify detections as **CONVINCING** (significance ≥ 5), **MARGINAL** (≥ 2), or **NOT DETECTED** (< 2). HD 16467 came in at 4.4. HD 206948 at 7.7.

### Pattern 6: Verification — three independent ways

A single fit isn't a result. A single fit cross-checked three ways is closer to one. Three cross-checks ran on the HD 16467 data:

**Split-half (`split_half_validation.py`).** Fit subset A (sector 31, 2020) and subset B (sectors 70+71, 2023) independently. Both gave ν_max within 1 µHz of each other. If the signal were random noise that happened to fluctuate above the threshold, you'd expect different halves of the data to find the bump in different places, or not at all. They didn't.

**pySYD (`run_pysyd.py`).** A complete second pipeline, written by professional asteroseismologists, run with no shared code. It parses the same lightcurve, runs its own Harvey fit, and reports its own ν_max. For HD 16467 it found 44.5 ± 0.5 µHz against our 43.4 ± 0.1 — agreement at the 1σ level. For HD 206948 it found 36.8 ± 0.9 µHz against our 36.6 ± 0.07 — agreement at well under 1σ.

**Échelle diagram (`echelle.py`).** A different test entirely: fold the spectrum modulo Δν and ask whether the resulting 2D image shows vertical ridges. For HD 206948, the column contrast came out at 0.634 — solidly above the 0.3 threshold for "real modes." This isn't a measurement of ν_max; it's a measurement of whether the *internal structure* of the envelope is consistent with real p-modes versus random fluctuations.

Each verification rules out a different failure mode. Together they leave very little room for the result to be wrong.

### Pattern 7: A modular utilities file

The reason the HD 206948 analysis was so much faster to build than the HD 16467 one is that almost all of HD 16467's machinery moved into a shared module — `seismic_utils.py`. Both stars import the same `load_sectors_ppm`, `make_freq_grid`, `calibrate_psd`, and `fit_harvey_model` functions. The differences live in star-specific overrides: HD 206948 needs different initial guesses (bigger star, slower granulation timescales) and a different ν_max search range. The shared module accepts those as keyword arguments.

If you wanted to apply this pipeline to a third K giant — say, HD 41597 — you would copy `hd206948_seismic.py`, change the target name and the predicted ν_max value, plug in the new size and temperature, and run it. The whole new analysis would be maybe 20 lines of editing, not a from-scratch rewrite. That's the test of whether your code is actually reusable.

### Git as a project log

Every meaningful step in this project corresponds to a single git commit with a descriptive message. Reading `git log --oneline` is the fastest way to reconstruct what happened:

```
HD 206948: échelle diagram — ridge structure confirmed (contrast 0.634)
HD 206948: pySYD validation — νmax consistent to 0.2σ
HD 206948: seismic analysis — CONVINCING detection at νmax = 36.6 µHz
HD 16467: split-half verification and detection summary
HD 16467: pySYD v6 validation — independent νmax cross-check
HD 16467: asteroseismic analysis with Harvey background fit
HD 16467: stellar context confirms K0III red giant, predicts νmax
Pi Mensae: reproduce transit detection of Pi Men c
```

Each line is a commit you can `git checkout` and run. Each commit's message is a one-line summary of what got added or changed, and what was learned. This is the project's permanent record — much more useful than any retrospective notes I could write.

### One step further

The pipeline is parameterised on a few inputs: target identifier, predicted ν_max, predicted Δν, and rough initial guesses for granulation timescales (which scale with stellar radius). Everything else is generic. Pointed at any reasonably bright K-type giant in the sky, it should produce a publishable-quality asteroseismic measurement in an evening.

There are *many* such giants that nobody has specifically looked at. The southern continuous viewing zone of TESS — a circular patch of sky around the south ecliptic pole that's covered every sector for an entire year — contains hundreds of bright giants with multi-sector data and no individual asteroseismic characterisation. The technique works. The pipeline is sitting in the repository. The next discovery is genuinely on the table.

---

## Part 12: A closing word

The reason any of this is worth writing down is that it shouldn't be esoteric. Science isn't a thing that happens behind walls, with permissions, with credentials. It's just a set of techniques applied carefully to data. The data is free. The techniques are well-described. The tools are open source.

What's needed is the patience to understand what you're doing and why, and the honesty to admit when the result doesn't quite hold up. Both of those are available to anyone.

If reading this made you curious about doing something similar — start with the lightkurve tutorial. Pick a star. Pull its data. Make a graph. See what's there. The first time you see a real signal in real data, even if someone else has already found it, is properly something.

And if you want to go further: the K giants of the southern sky are full of stars nobody's specifically looked at. The technique works. The pipeline is sitting in the repository. The next discovery is genuinely on the table.

Clear skies.

---

## Glossary

Every technical term used in this document, defined again in one place.

- **astroquery.** Python package wrapping queries to astronomical databases (SIMBAD, Gaia, TIC, WDS). Used for looking up stellar parameters before running a lightcurve analysis.
- **Asteroseismology.** Studying the inside of stars by measuring their surface vibrations.
- **ν_max ("new max").** The central frequency of a star's oscillation envelope. Tells you where the star is ringing most strongly. Related to size and surface gravity.
- **Δν ("delta new").** The frequency spacing between consecutive ringing notes. Related to the average density of the star.
- **Échelle diagram.** A way of plotting the power spectrum to reveal the regular spacing of oscillation modes. Real modes form vertical ridges.
- **Git.** Version control system used to track every meaningful change to the project's code. Each `commit` is a snapshot with a descriptive message; together they form the project's permanent log.
- **Granulation.** Convection cells boiling on a star's surface, producing brightness wobbles unrelated to oscillation.
- **JSON.** Lightweight text format used to pass numerical results between scripts in this project (e.g., `pysyd_results.json`, `split_half_results.json`).
- **K0III, K2III.** Spectral classifications. The letter and number describe temperature; the Roman numeral describes evolutionary stage. III means giant.
- **ℓ = 0, ℓ = 2.** Spherical-harmonic degree of an oscillation mode. ℓ = 0 modes are radial pulsations (the whole star pulses spherically). ℓ = 2 modes are quadrupolar (opposite poles bulge while the equator pinches). Both show up as ridges in the échelle diagram.
- **lightkurve.** Python package that wraps MAST, lets you search and download TESS lightcurves in a few lines of code. The on-ramp for any TESS-based project.
- **Lightcurve.** A graph of a star's brightness over time.
- **Lomb-Scargle periodogram.** The standard algorithm for computing a power spectrum from irregularly-sampled data — handles the gaps in TESS coverage gracefully.
- **MAST.** Mikulski Archive for Space Telescopes. Where TESS data lives, freely available.
- **µHz (microhertz).** Frequency unit. 1 µHz is one cycle per 11.6 days. 100 µHz is one cycle per 167 minutes.
- **Parallax.** How a star's apparent position shifts in the sky as Earth moves around the Sun. Used to measure stellar distances.
- **Periodogram.** A graph of "how strong each possible cycle length is in the data." Used to detect rotation, transits, and other periodic signals.
- **ppm (parts per million).** A unit for very small fractions. 1 ppm = 0.0001%. Used to express tiny brightness variations.
- **Power spectrum.** Same idea as a periodogram but typically plotted in frequency rather than period. Used for asteroseismology.
- **pySYD.** Standard professional-grade Python pipeline for asteroseismic analysis. Used as an independent cross-check on the home-grown fits.
- **Python.** General-purpose programming language used throughout the project. Every script is a `.py` file you can read top-to-bottom.
- **scipy.** Scientific computing library. Used here for `optimize.curve_fit` (fitting the Harvey + Gaussian model) and `signal.correlate` (autocorrelation for finding Δν).
- **Sector.** A 27-day stretch of TESS observations of one patch of sky.
- **SPOC.** The Science Processing Operations Center pipeline. The official, highest-quality way TESS data is reduced.
- **TESS.** Transiting Exoplanet Survey Satellite. NASA mission, launched 2018, surveys most of the sky.
- **Transit.** A planet passing in front of its star from our viewpoint, briefly dimming the starlight.
- **Virtual environment (venv).** A self-contained Python installation isolated from the system Python. Lets you pin specific package versions per-project. The project's `venv/` directory holds all dependencies.

---

## External sources and further reading

**The data**
- TESS mission overview: https://tess.mit.edu/
- MAST archive (where the raw data lives): https://mast.stsci.edu/
- Lightkurve documentation: https://docs.lightkurve.org/

**The science**
- Aerts, Christensen-Dalsgaard, Kurtz (2010), *Asteroseismology* — the standard textbook on the field.
- Chaplin & Miglio (2013), "Asteroseismology of Solar-Type and Red-Giant Stars" — an accessible review article.
- Hekker & Christensen-Dalsgaard (2017), *Astronomy and Astrophysics Review* — modern review of red giant seismology.
- Brown, Gilliland, Noyes & Ramsey (1991), *ApJ* — the foundational paper on stellar oscillation scaling relations.
- Kjeldsen & Bedding (1995), *A&A* — the relations linking oscillation amplitudes to stellar parameters.

**The catalogues we checked the stars against**
- HD-TESS catalogue: Hon et al. (2022), *MNRAS* — bright giant asteroseismology with TESS.
- TESS red giant catalogue: Mackereth et al. (2021), *MNRAS* — Southern Continuous Viewing Zone analysis.
- Zhou et al. (2024) — TESS-based survey of 8651 evolved stars.
- AAVSO Variable Star Index (VSX): https://www.aavso.org/vsx/
- SIMBAD: https://simbad.cds.unistra.fr/simbad/
- Gaia DR3 archive: https://gea.esac.esa.int/archive/

**Tools used**
- Python: https://python.org
- lightkurve: https://docs.lightkurve.org
- astropy: https://astropy.org
- astroquery: https://astroquery.readthedocs.io
- pySYD (Chontos et al. 2021): https://pysyd.readthedocs.io
- scipy: https://scipy.org

**Specific references**
- Pi Mensae c discovery: Huang et al. (2018), "TESS Discovery of a Transiting Super-Earth in the Pi Mensae System," *ApJL*.
- Epsilon Eridani rotation: Donahue, Saar & Baliunas (1996) — 11-day rotation period from chromospheric activity.
- DASCH long-period K-giant variables: Tang et al. (2010), *ApJL* 710, L77.

**The repository**
Complete project, with source code, plots, analysis documents and reproducibility notes:
*https://github.com/engantor/tess-analysis*
