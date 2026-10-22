# Blazing Visualizer

An Android music player and visualizer with an Avee-style Library / Visualizer / Queue workflow and offline polyphonic note detection.

- Local music playback and background controls using Media3.
- Bundled Spotify Basic Pitch model; note wheel, chord links, keyboard and piano-roll guides.
- Practice at 0.5–1.5× without changing pitch; A/B loop, written-instrument display transposition, editable note estimates, MIDI and CSV.
- Editable image, text, spectrum, shape, waveform, particle, glow and note layers. Attributed Avee DSP provides the spectrum and circle path foundation.
- Import/export self-contained `.blazeviz` preset packs. Avee JSON/ZIP conversion is partial and shows a compatibility report before accepting it.
- MP4 export with original-speed audio: H.264 + AAC, 30 fps, 720p/1080p, landscape/portrait/square.
- Automatic MediaStore library discovery after music access is allowed, independent sortable/drag-reorderable Queue, and cached background note preparation.
- Long-press visualizer arrangement with move/resize handles; export follows and auto-fits the preview or uses its own arrangement.
- Per-layer Lo/Lo2/Mid/Mid2/Hi/Hi2 routing, independent piano-key glow/sparks and colors, global/piano intensity and a global palette.
- Original Harmonic flow, Orbital voices and Wave garden graph presets; optional equations are off by default. Graph views display up to 12 simultaneous pitches; Practice retains the complete note detection.
- Microphone/YIN tuner with A4 calibration, cents/confidence and guitar-string guidance. Capture stops when the sheet closes or the app backgrounds; resume explicitly.

## Build

Use JDK 17, Android SDK platform 36 and build-tools 36.0.0. Android 8.0 / API 26 is the minimum. The APK includes arm64-v8a and x86_64 native libraries.

```sh
./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
./gradlew :app:connectedDebugAndroidTest
```

The debug APK is `app/build/outputs/apk/debug/app-debug.apk`. CI uploads it under **Blazing-Visualizer-preview-APK**. Preview 2 uses the public debug-only identity described in [config/README.md](config/README.md); future preview updates retain it. Preview 1's ephemeral CI identity requires a one-time uninstall/reinstall; export wanted BlazeViz presets first. Production signing and store publication are separate release work.

CI runs `MusicPermissionTest` alone on a fresh install (with `freshAudioPermission=true`), then the general native suite with `notClass=com.blazingsystems.visualizer.MusicPermissionTest`. On an already granted local install the standalone denial test skips; reset app permissions before exercising it independently.

## Use

Allow music access to fill Library automatically, or open files with the music button. Queue is separate: add tracks, choose Play next, long press to reorder, or sort by title/artist. Notes prepare in the background; the selected track takes priority.

Choose **Harmonic compass** for the note wheel, or one of the three graph presets. Tap **Practice** to follow or correct notes; its selections and loops are saved per track. The pencil opens layers, note bands, colors and effects. Turn on **Include math equations** only if wanted. Hold the canvas to arrange, drag a layer to move it and its white corner to resize; tap Done to save. Rotation ends an active preview arrangement before fitting it to the new viewport.

The share/export icon offers landscape, portrait and square with dimensions and an output preview. Choose **Follow preview · auto fit** or **Separate arrangement**, then arrange the export frame independently. Tuner listens through the microphone and pauses playback. Imported presets and attached images are stored locally.

Note estimates are suggestions, especially on dense mixes. Corrections are separate from raw model results and survive reopening a project. Replacing the contents behind a file URI clears stale corrections and requires fresh analysis before export. MIDI always exports sounding concert pitch.

Analysis length is limited by the device heap, up to 30 minutes. Video settings are checked by the device encoder, and unsupported codecs return a visible error. Offline core features require no account or server. The app requests no Internet permission.

## Verification and provenance

See [execution record](docs/acceptance/execution-record.md), [third-party notices](THIRD_PARTY_NOTICES.md), and the [design](docs/superpowers/specs/2026-10-22-blazing-visualizer-design.md). Instrumentation checks independent Python model/postprocessor parity, onset accuracy on synthetic and CC0 recorded-flute fixtures, deterministic GL rendering, real playback/looping, Compose flows, all six export presets, clip duration and cancellation. Physical-device performance and mixed-song transcription are not established by these fixtures.

The supplied reference recording's math was checked separately in [reference-video-math.md](docs/acceptance/reference-video-math.md). Its video tracing/Bezier conversion idea is deliberately deferred until the improved non-video-renderer APK is delivered.

Reference fixtures can be regenerated with Python 3.11, `tools/requirements-reference.txt`, `tools/build_acceptance_fixtures.py`, and `tools/reference_analyze.py --upstream <pinned-basic-pitch-checkout>`.
