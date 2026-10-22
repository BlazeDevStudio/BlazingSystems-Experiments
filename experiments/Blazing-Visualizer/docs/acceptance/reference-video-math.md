# Reference video: musical mathematics review

Reviewed 2026-10-22 against the supplied 464.7-second recording. Timestamps below refer to that recording and are approximate visual locations, not timestamps in the original social posts. The review inspected the four contact sheets, the ten supplied detail frames, and selected individual frames. It does not establish the exact audio-generation code, source assets, or production provenance.

**Delivery order: graph/video conversion is LAST and DEFERRED.** Release a usable preview of the musical visualizer without the video renderer before implementing pixel thresholding, contour tracing, curve fitting, video-frame filling, or synchronized video conversion. The verified geometry below is future design evidence, not authorization to implement that stage now.

## Timestamped findings

“True” includes the conditions stated in the correction column. “Approximate” means a useful simplification or an incomplete mapping. “Wrong” identifies a specific inconsistency or calculation. “Unverifiable” means the recording does not supply the evidence needed to establish the claim.

| Recording time | Visible statement or feature | Verdict | Correction or condition |
| --- | --- | --- | --- |
| 00:35 | Piano frequency formula with reference index 49 | True, conditional | `440 × 2^((n − 49)/12)` uses standard piano key numbering, with A0 = key 1. For MIDI numbering, A4 = 69 and the reference index must be 69. Both assume twelve-tone equal temperament and A4 = 440 Hz. [P1, P2] |
| 01:04–01:05 | Unison drawn as a circle; printed `x = sin(t), y = sin(t)`; one detail frame reads 1.001:1 | Wrong as written | The printed equal-phase equations give a diagonal line. Equal amplitudes with a quarter-cycle phase difference give a circle. A 1.001:1 ratio is slight detuning rather than exact unison. [P3] |
| 01:15 | Fifth header 3.008:2; printed `x = sin(2t), y = sin(3t)` | Approximate; internally inconsistent | The equations describe exact 3:2, while the header describes a detuned ratio. 3.008:2 is 4.61 cents above the just fifth and 6.57 cents above the equal-tempered fifth. It may be intentional detuning during animation, but that is not established by the frame. [P1, P4; numerical calculation] |
| 01:25–01:35 | 5:4 major third and 15:8 major seventh | True for just intonation | These are valid just intervals. They are not the exact equal-tempered piano intervals. The major-second detail at 01:30 also shows a detuned 9.019:8 header above the exact equations `x = sin(8t), y = sin(9t)`. [P4] |
| 01:30 | Each note of the scale assigned a shape | Approximate | This is an authored mapping relative to a reference note. Phase, amplitude, projection, and trail length also affect the visible shape. Transposition preserves frequency ratios. [P3; consequence of the equations] |
| 01:45–01:48 | Three-note 4:5:6 chord and three sinusoidal coordinates | True, conditional | 4:5:6 is a just major triad. Its three-coordinate curve is a valid representation, but the spatial projection is a design choice. Displayed detuning values and the actual coordinate equations must agree. [P4, P5] |
| 01:55–02:05 | Gmaj7 ratio 8:10:12:15; coordinates use only 8, 10, and 15 | Ratio true; equation incomplete | The four ratios describe a just major-seventh chord. The printed three-coordinate formula omits the 12-frequency fifth. Include the fourth voice through an explicit projection or mixture, or label that three-voice representation Gmaj7(no5). [P4; ratio interpretation] |
| 02:15 | Orbit frequencies `N = 4, 6, 8, 12, 16, 24`, denominator 16; alignment every eight beats | True as an authored model | With aligned starting phases, the common recurrence is `16 / gcd(N) = 8` beats. “Music of the spheres” is a metaphor here; these arbitrary rates are not evidence of real planetary periods. Kepler's third law relates period and semimajor axis through `T² ∝ a³`. [P6; recurrence calculation] |
| 02:25–02:36 | Increasing hit rate becomes pitch; approximately 20 Hz transition | Approximate | Rapid regular repetition can produce pitch. About 20 Hz is a perceptual transition, not a universal switch for every waveform and listener. 55, 110, 220, and 440 Hz correspond to A1–A4 under A440 tuning. [P1, P2, P7] |
| 02:36 | Doubling speed raises pitch one octave | True with time scaling | For `s(2t)`, every frequency doubles. Doubling only the trigger rate while retaining the duration and internal frequencies of each hit changes repetition pitch without doubling every partial within the hit. [Consequence of time scaling] |
| 02:45–03:25 | 3:2 and 4:5:6 polyrhythms accelerated into intervals/chords | True, conditional | Preserve exact relative event rates while changing their common multiplier. Rounded displayed Hz values can differ slightly from an exact ratio. The listener's percept also depends on the repeated hit waveform. [P4, P7; recurrence calculation] |
| 04:40 | `sin(2π × 39t)` described as 39 cycles per second | True | This is a 39 Hz sine when `t` is seconds. Subsequent nonlinear shaping such as `tanh` changes the spectrum, so the shaped output is no longer a pure sine. [Direct evaluation of the equation] |
| 04:45 and 07:25 | Falling-frequency kick synthesis | Approximate; phase correction required | An exponential frequency descent is a reasonable model. A time-varying frequency must be integrated into phase. Do not implement `sin(2π f(t)t)` as though its instantaneous frequency were `f(t)`. See the explicit formula below. The review does not establish the author's actual synthesis code. [P8] |
| 04:55 and 07:35 | Noise multiplied by a decaying envelope for clap/hat | True with omitted onset conditions | Gate each envelope at its onset; an unrestricted exponential extends backward and grows before the hit. Filtering and envelope shape affect the timbre. [P8, P9; gated-envelope construction] |
| 06:25 | “0 samples, 0 recordings” | Unverifiable | This is an on-screen production claim. The recording does not establish the absence of recorded sources, the origin of the voice, or exact procedural audio provenance. Do not repeat it as a verified fact. |
| 06:45–07:05 | Pixel boundaries, cubic Bézier curves, and odd/even crossing fill | Valid pipeline; implementation deferred | Four points define a cubic Bézier segment. De Casteljau uses three rounds of interpolation, totaling six linear interpolations. Even–odd filling is valid for closed compound paths, including holes, with consistent handling of vertices and tangencies. Thresholding and curve-fitting tolerance affect fidelity. [P10, P11] |
| 07:15 | `6,955 frames × 181 curves = 1,259,297 curves` | Wrong arithmetic; claimed total unverifiable | The stated product is **1,258,855**. Per-frame curve counts visibly vary, so the actual total requires summing those counts. A rounded average might explain the discrepancy but does not make the displayed equality exact. [Direct arithmetic and visual observation] |

## Frequency, tuning, and phase contracts

Use a single tuning mode and frequency state to drive audio, ratio labels, equations, and geometry. Keep intentional detuning distinct from both exact just intonation and equal temperament.

For twelve-tone equal temperament, with semitone offset `s` above A4:

```text
f(s) = 440 × 2^(s/12) Hz
f_piano(n) = 440 × 2^((n − 49)/12) Hz, A0 = key 1
f_MIDI(m) = 440 × 2^((m − 69)/12) Hz, A4 = MIDI 69
cents(f2, f1) = 1200 × log2(f2/f1)
```

The frequency formulas follow [P1, P2]. The following comparisons are calculated from those formulas and the just ratios in [P4]. Ratios are higher frequency divided by lower frequency.

| Interval | Just ratio | Twelve-tone equal-tempered ratio | Convenient normalized comparison |
| --- | --- | --- | --- |
| Major second | 9/8 = 1.125 | 2^(2/12) ≈ 1.122462 | 9:8 versus 8.979696:8 |
| Major third | 5/4 = 1.25 | 2^(4/12) ≈ 1.259921 | 5:4 versus 5.039684:4 |
| Perfect fifth | 3/2 = 1.5 | 2^(7/12) ≈ 1.498307 | 3:2 versus 2.996614:2 |
| Major seventh | 15/8 = 1.875 | 2^(11/12) ≈ 1.887749 | 15:8 versus 15.101989:8 |
| Octave | 2/1 | 2^(12/12) = 2 | 2:1 in both systems |

A two-voice Lissajous model should expose its phase convention:

```text
x(t) = Ax × sin(2π fx t + φx)
y(t) = Ay × sin(2π fy t + φy)
```

Equal frequencies and equal phases produce a line. Equal amplitudes and a phase difference of ±π/2 produce a circle. Intermediate phase differences generally produce ellipses. [P3]

An exact rational frequency ratio permits a closed trajectory. A small departure causes drift relative to the short, simple-ratio loop. Non-octave equal-tempered ratios are irrational in the ideal mathematical model and do not yield an exactly closed finite-period trajectory. Decimal detuning values are themselves rational if interpreted exactly, but can have a much longer recurrence; do not describe every detuned decimal ratio as never closing.

## Time, polyrhythm, and kick sweep

Keep seconds, beats, and visual slowdown explicit. At tempo `B` beats per minute, `beat(t) = t × B/60`. A visualization can display a slowed phase while reporting the true audio frequency, provided the scale is labeled.

For event rates `ri = k × ni`, where the `ni` are positive integers and all streams start together, the common recurrence is `1 / (k × gcd(n1, n2, …))`. The orbit example has `k = 1/16` per beat and greatest common divisor 2, giving eight beats.

For a kick beginning at `t0`, let `u = t − t0` and gate the signal to zero for `u < 0`. One suitable exponential descent is:

```text
f(u) = f∞ + Δf × exp(−u/τf)
phase(u) = φ0 + 2π × [f∞u + Δf τf × (1 − exp(−u/τf))]
kick(u) = A(u) × sin(phase(u)), u ≥ 0
```

This follows by integrating frequency. In contrast, the derivative of `2π f(u)u` yields instantaneous frequency `f(u) + u f′(u)`. Web Audio's oscillator specification explicitly integrates its computed frequency, and its exponential target automation supplies the same family of decay curves. [P8]

## Sampling and aliasing caveat

Procedural audio still becomes discrete samples at the output sample rate. For sample rate `Fs`, the Nyquist frequency is `Fs/2`. Harmonics above that limit can fold into audible frequencies. Sawtooth and square waves, sharp pulse edges, and nonlinear shaping need appropriate bandlimiting, filtering, or oversampling; keeping only the fundamental below Nyquist is insufficient. Web Audio describes this requirement for sampled oscillators. [P8]

A screen trail sampled at display refresh rate is also not a literal measurement of a hundreds-of-hertz oscillator. Render a sampled analytical path or use an explicitly slowed phase for the visible orbit. Preserve the actual audio frequency in the state and labels.

## Deferred geometry contract

The observed future pipeline is thresholded pixels → boundaries → fitted curves → filled frames. It is a valid representation pipeline, not evidence that the source video was created from no visual assets. The pixel source, threshold, connectivity decisions, and fitting tolerance still matter.

A cubic Bézier segment is:

```text
B(u) = (1−u)^3 P0 + 3(1−u)^2 u P1 + 3(1−u)u^2 P2 + u^3 P3
0 ≤ u ≤ 1
lerp(A, B, u) = (1−u)A + uB
```

De Casteljau evaluates three first-round lerps, two second-round lerps, and one final lerp. The four-point segment model agrees with SVG's cubic commands. [P10]

The even–odd rule considers a point inside when a ray from it crosses the closed boundary an odd number of times. Use consistent endpoint handling; tangencies and rays through vertices must not create duplicate crossings. W3C explicitly notes tangent and coincident-ray cases. [P11]

The recording's total curve count cannot be verified without per-frame data. Compute a future implementation's total as `Σ frameCurveCount[j]`; report a rounded average with an approximation sign rather than an exact multiplication claim.

**Do not begin this renderer until the usable non-video-renderer preview has been delivered.** This document adds no renderer implementation and makes no claim that video conversion is complete.

## Primary references

These sources support the mathematical conditions and definitions. The recording itself supports only the observations listed in the timestamp table. Arithmetic and formula consequences are identified separately above.

- **P1 — UNSW, Note names, MIDI numbers and frequencies:** https://newt.phys.unsw.edu.au/music/notes.html
- **P2 — UCSD, Tamara Smyth, A Note on Pitch and Frequency:** https://musicweb.ucsd.edu/~trsmyth/am171/Note_on_Pitch.html
- **P3 — Durham University, Lissajous Figures:** https://dur.ac.uk/departments/academic/physics/labs/skills/oscilloscope/lissajou-figures/
- **P4 — Simon Fraser University, Handbook for Acoustic Ecology, Just Tuning:** https://www.sfu.ca/sonic-studio-webdav/handbook/Just_Tuning.html
- **P5 — UCSD, Miller Puckette, Pitches, Intervals, and Scales:** https://msp.ucsd.edu/syllabi/170.13f/course-notes/node4.html
- **P6 — NASA, Orbits and Kepler's Laws:** https://science.nasa.gov/solar-system/orbits-and-keplers-laws/
- **P7 — Simon Fraser University, Handbook for Acoustic Ecology, Pulse:** https://www.sfu.ca/sonic-studio-webdav/handbook/Pulse.html
- **P8 — W3C, Web Audio API Recommendation, oscillator phase and aliasing:** https://www.w3.org/TR/webaudio-1.0/#oscillatornode ; exponential target automation: https://www.w3.org/TR/webaudio-1.0/#dom-audioparam-settargetattime
- **P9 — UCSD, Tamara Smyth, ADSR Envelope:** https://musicweb.ucsd.edu/~trsmyth/sinusoids171/ADSR_Envelope.html
- **P10 — W3C, SVG 2, cubic Bézier path commands:** https://www.w3.org/TR/SVG2/paths.html#PathDataCubicBezierCommands
- **P11 — W3C, SVG 2, fill-rule:** https://www.w3.org/TR/SVG2/painting.html#FillRuleProperty
