# Avee Player 1.2.252 AudioProvider schema inspection

The user-provided APK was examined as a ZIP archive without executing code.
Its exact size was 16,090,488 bytes. It contains third-party mod markers
(`E_l_a_Mods.xml` and `assets/El_a credit.xml`) and is not an authenticated
official Avee binary. Do not commit or redistribute bundled copyrighted assets.

## Observations
18 packaged JSON resources expose `compositions[].elements[]`. Observed element
types include AudioProvider, Image, Bars, AppLogo, BlurEffect, MotionBlurEffect,
Particles, Text, RgbSplitEffect, and MirrorEffect.

An AudioProvider uses e.g. `sampleProvider=Spectrum2` with `sampleOutCount`,
`lowerHz/higherHz`, `hzLinearFactor`, `smooth`, `filterRadius`,
`filterStrength`, `beatSmooth`, `lowerFreqMagnitude` and `outputMultiplier`.
These are settings of a frame-reactive FFT/spectrum system, **not** proof of an
Avee real-time polyphonic note-to-MIDI recognition algorithm.

## Original-code compatibility increment
Avee JSON imports now preserve safe AudioProvider scalar fields within a
serializable BlazeViz Scene, and the original FFT visual renderer uses imported
frequency range, linearity, sample count, spectral filtering and gains on each
frame. Native built-in presets are unchanged; the same renderer feeds preview
and MP4. Blur is represented as a glow; complex motion blur is explicitly an
approximation. Avee's original app-specific logo is intentionally excluded.

## Remaining limitations
This is not 1:1 Avee .viz compatibility. Multiple offscreen compositions,
custom shader/mask paths, fonts, animations, advanced audio DSP and binary .viz
encodings are not faithfully reproduced. Import remains guarded by archive
size, safe paths and decoded-image limits. A user-exported, permissioned .viz
fixture is needed to demonstrate actual format compatibility.
