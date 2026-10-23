# Avee 1.2.252 comparison — verified vs unknown

This comparison records the earlier importer/FFT baseline. The Preview 3 composition and configured Spectrum2 increment, with its remaining limits, is described in [avee-1252-audio-profile.md](avee-1252-audio-profile.md) and [preview-3-evidence.md](preview-3-evidence.md). Refer to HANDOFF.md for actual release verification.

Owner-provided reference: `Avee Player v1.2.252 (Premium).apk`. It is an **unofficially modified** distribution, indicated by `E_l_a_Mods.xml` and `libpairipcore.so`. It is inspected locally for interoperability research only, not committed, executed, repackaged or redistributed.

## Confirmed static structure

ZIP contains 1,891 entries including three `classes*.dex` archives. Strings exposed by the first DEX include `AudioProvider`, `Bars`, `Spectrum`, `Spectrum2`, `RoundBars`, `SharpBars`, `Waveform`, `BlurEffect`, `MotionBlurEffect`, and `RgbSplitEffect`. This is **type-name evidence, not proof** of their precise JSON serialization or behavior. No proprietary algorithm, code or art was copied.

Official Avee FAQ: `https://aveeplayer.com/` documents that `.viz` files created with Avee 1.2.83 onward are compatible **within Avee**, but does not publish a complete current schema. Open AveePlayer 1.0.34 (`https://github.com/jhedev96/AveeOpenPlayer`) is Apache-2.0 source and documents FFT-derived visualizer spectra with additional processing. It is **not** source for the proprietary behavior of modern 1.2.252.

## Blazing implementation and honesty limits

- We use Media3/ExoPlayer for playback and automatic library scanning.
- `AveeSpectrumAnalyzer` produces a Hann-windowed 2048-point FFT, RMS and waveform for immediate musical reactive layers. It **does not** output correctly named MIDI notes. `AudioFeatures` samples the decoded audio at the player's source clock. UI updates are paced by Media3 ticker.
- Separately, bundled Basic Pitch TFLite models infer polyphonic MIDI notes, asynchronously/cached; `YinTuner` estimates one incoming note from a microphone. **Do not call FFT beat responsiveness “more accurate note identification.”**
- The Avee importer now maps obvious element names (`Bars/Spectrum/Spectrum2/RoundBars/SharpBars` to spectrum, `Waveform` to waveform, `BlurEffect/MotionBlurEffect` to simplified blur) and continues to warn about DSP, blend, shader and image incompatibilities.
- Numeric/string color values, array or space-separated position/scale, and JSON boolean visibility are handled explicitly. Unsupported elements trigger compatibility report rather than falsely claiming full fidelity.
- This repository does **not** yet have a verified 1.2.252-exported `.viz` fixture. APK alone is not an importable .viz fixture, so modern preset round-trip and visual fidelity remain **unverified**. Importer enhancement must be measured with an actual authorized .viz from Avee, including embedded images.
- Existing Blazing visualizer presets and the native `.blazeviz` format are unchanged.

## Remaining engineering

1. Obtain a representative non-copyright-infringing exported Avee .viz fixture from owner or create one with a licensed Avee install; record its container type, schema and actual images; add golden importer test.
2. Probe real 1.2.252 UI on an Android device/emulator rather than inferring UI from an APK or old source. Compare one-handed navigation, queue/repeat, library sort, edit sheets, presets and export.
3. For music responsiveness compare attack latency (peak response in ms), spectral-frequency resolution and RMS hold, and pitch transcription against labeled WAVs. Preserve independent audio-reactive FFT and Basic Pitch note detection; do not mix their metrics.
4. Distinguish exact parity from approximate rendering in imported-preset dialogs and package release notes.
