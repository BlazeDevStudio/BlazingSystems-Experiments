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

## Preview 3 original implementation

The candidate preserves the provider's safe scalar settings, original document and per-element metadata. Spectrum2 uses an independently written Goertzel correlation bank at configured frequencies, Hann windows, logarithmic/linear spacing and bounded detail filtering. Recorded analysis uses a finite, normalized capture-time response history so seeking and exporting do not depend on the previous render order. Native presets keep the existing FFT path.

Referenced offscreen composition passes replace flattening. Static nested segments, images, tint, aspect handling, circular clipping and common blend modes are rendered; blur, RGB split and mirror are bounded approximations. These changes are supported by synthetic data/pixel tests, not a claim of pixel parity with official Avee.

A read-only review found that microphone analysis ignored the provider's smoothing and padded every window above 4096 samples. The regressions reproduced both defects. The fix retains up to300ms of PCM across capture hops and applies response using elapsed capture time. Final green evidence is tracked in HANDOFF.md and preview-3-evidence.md.

## Remaining limitations

This is partial .viz compatibility. Measure expressions, custom shader/mask paths, exact fonts, temporal feedback blur, adaptive gain, older Spectrum variants, exact beat response and binary .viz encodings remain incomplete. Native pack export retains original metadata but is not an Avee .viz writer. Internal resource textures are procedural approximations; no source artwork is redistributed. Multiple AudioProviders are reported as an approximation. Archive paths, sizes, decoded images, composition counts, cycles and render buffers are bounded.

A genuine user-exported .viz fixture and comparison on a physical phone remain needed for realistic interoperability and responsiveness measurements. Maximum-size frequency banks make a cold seek more expensive than a cached streaming frame; no phone latency benchmark is claimed. Numeric mirror flags work; a JSON boolean flag is a known hardening follow-up without an exported fixture establishing prevalence.
