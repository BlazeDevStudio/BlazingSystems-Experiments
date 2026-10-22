# Blazing Visualizer

An Android music player and visualizer with an Avee-style Library / Visualizer / Queue workflow and offline polyphonic note detection.

- Local music playback and background controls using Media3.
- Bundled Spotify Basic Pitch model; note wheel, chord links, keyboard and piano-roll guides.
- Practice at 0.5–1.5× without changing pitch; A/B loop, written-instrument display transposition, editable note estimates, MIDI and CSV.
- Editable image, text, spectrum, shape, waveform, particle, glow and note layers. Attributed Avee DSP provides the spectrum and circle path foundation.
- Import/export self-contained `.blazeviz` preset packs. Avee JSON/ZIP conversion is partial and shows a compatibility report before accepting it.
- MP4 export with original-speed audio: H.264 + AAC, 30 fps, 720p/1080p, landscape/portrait/square.

## Build

Use JDK 17, Android SDK platform 36 and build-tools 36.0.0. Android 8.0 / API 26 is the minimum. The APK includes arm64-v8a and x86_64 native libraries.

```sh
./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
./gradlew :app:connectedDebugAndroidTest
```

The debug APK is `app/build/outputs/apk/debug/app-debug.apk`. CI uploads it under **Blazing-Visualizer-preview-APK**. The preview uses debug signing; production signing and store publication are separate release work.

## Use

Open audio with the music button, then choose **Harmonic compass** from the preset chooser for the note wheel. Analysis runs on the device before the complete note guide is available. Tap **Practice** to follow or correct notes. The pencil opens layers and their properties. The share/export icon opens MP4 settings. Imported presets and attached images are stored locally.

Note estimates are suggestions, especially on dense mixes. Corrections are separate from raw model results and survive reopening a project. Replacing the contents behind a file URI clears stale corrections and requires fresh analysis before export. MIDI always exports sounding concert pitch.

Analysis length is limited by the device heap, up to 30 minutes. Video settings are checked by the device encoder, and unsupported codecs return a visible error. Offline core features require no account or server. The app requests no Internet permission.

## Verification and provenance

See [execution record](docs/acceptance/execution-record.md), [third-party notices](THIRD_PARTY_NOTICES.md), and the [design](docs/superpowers/specs/2026-10-22-blazing-visualizer-design.md). Instrumentation checks independent Python model/postprocessor parity, onset accuracy on synthetic and CC0 recorded-flute fixtures, deterministic GL rendering, real playback/looping, Compose flows, all six export presets, clip duration and cancellation. Physical-device performance and mixed-song transcription are not established by these fixtures.

Reference fixtures can be regenerated with Python 3.11, `tools/requirements-reference.txt`, `tools/build_acceptance_fixtures.py`, and `tools/reference_analyze.py --upstream <pinned-basic-pitch-checkout>`.
