# Blazing Visualizer

An Android local media player and visualizer with an Avee-style Library / Visualizer / Queue workflow and offline polyphonic note estimates.

- Mixed local audio/video imports, one Media3 playback session and background controls. Video appears behind the visualizer and follows pause, seek and Practice speed; audio-only media removes the background.
- An early video seek recreates a decoder that has not produced its first output format, preserving codec setup and the requested source position; later seeks retain normal Media3 flushing.
- Live source-time note estimates from PCM consumed by the existing playback audio sink, with a bounded file-decoder fallback while whole-file Basic Pitch analysis prepares. Nonempty detailed results and explicit edits take precedence; an empty unedited result leaves live estimates available. Temporary feedback is kept out of saved corrections and final exports.
- Bundled Spotify Basic Pitch model; note wheel, chord links, keyboard and piano-roll guides. Videos without audio play/export without fabricated detected notes.
- Practice at 0.5–1.5× without changing pitch; A/B loop, written-instrument display transposition, editable note estimates, MIDI and CSV.
- Editable image, text, spectrum, shape, waveform, particle, glow and note layers. Attributed Avee DSP supplies the spectrum and circle-path foundation.
- Import/export self-contained `.blazeviz` packs. Avee JSON/ZIP import remains partial and presents a compatibility report.
- MP4 export with source-time video behind the scene and original-speed audio: H.264 + AAC, 30 fps, 720p/1080p, landscape/portrait/square. Timestamp gaps and longer video tails remain on the media timeline.
- Automatic MediaStore music discovery after access is allowed, an independent sortable/drag-reorderable Queue, playlists and cached background note preparation.
- Long-press move/resize arrangement; export follows/fits the preview or uses its own arrangement.
- Per-layer Lo/Lo2/Mid/Mid2/Hi/Hi2 routing, actual-pitch piano-key glow/sparks, independent colors and global/piano intensity.
- Original Harmonic flow, Orbital voices and Wave garden presets plus five optional motion presets: trails, spatial chords, shared-cursor reveal, rhythm gates and radial contours. Equations are off by default. Graphs display up to 12 simultaneous pitches; Practice retains complete detailed note detection.
- Main-canvas microphone toggle with conservative simultaneous estimates and precise single-note YIN readings. Capture time drives animation independently of playback; background/disable/exit releases capture.

Current verified download: [Preview 6 APK](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.6/Blazing-Visualizer-preview-6.apk). It can update Preview 2/3/4/5 in place. Host, lint/APK and API26/API36 checks passed, and the public APK matches CI bytes. The owner reported Preview 5 still blank; Preview 6 owner-phone confirmation remains pending. See [Preview 6 evidence](docs/acceptance/preview-6-evidence.md) and [HANDOFF.md](HANDOFF.md).

## Build

Use JDK 17, Android SDK platform 36 and build-tools 36.0.0. Android 8.0 / API 26 is the minimum. The APK includes arm64-v8a and x86_64 native libraries.

```sh
./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
./gradlew :app:connectedDebugAndroidTest
```

The debug APK is `app/build/outputs/apk/debug/app-debug.apk`; CI uploads **Blazing-Visualizer-preview-APK**. Preview 6 is versionCode 6 / `1.0.0-preview.6` and retains Preview 2/3/4/5's public debug-only identity from [config/README.md](config/README.md). Preview 1 used a different key and requires a one-time uninstall/reinstall; export wanted BlazeViz presets first. Production signing/store publication remain separate work.

CI separates bounded host tests, lint and both APK assemblies, then validates API 26 and API 36. `MusicPermissionTest` runs independently on a fresh install with `freshAudioPermission=true`; the general native suite excludes that class. On an already-granted local install, reset permissions to exercise denial independently.

## Use

Allow music access to discover audio in Library, or use the open-media action to select one or more audio/video documents. Video backgrounds appear automatically for a selected video. Queue stays independent: add tracks, choose Play next, drag to reorder or sort by title/artist. Background note preparation prioritizes selection. Quick estimates can animate the visualizer before detailed analysis finishes; Practice corrections, MIDI/CSV and final MP4 notes use detailed results.

Choose **Harmonic compass**, a graph or a motion preset from the thumbnail grid. Fullscreen hides player chrome. The note wheel has editable idle text and shows every detected note class when no chord matches. Tap **Practice** to follow or correct detailed notes; settings and loops save per track. The pencil opens layers, note bands, colors and effects. Turn on **Include math equations** only if wanted. Hold the canvas to arrange, drag to move and use the white corner to resize; tap Done to save. Rotation ends an active preview arrangement before fitting the new viewport.

If live visualization stays idle while music plays, open the playback menu and choose **Check visualizer**. Wait for its local check, then choose **Copy report** to share build/device details and audio/note/canvas measurements. The report contains no audio, filenames or file addresses; it sends nothing automatically.

The export action offers landscape, portrait and square with dimensions and an output preview. Choose optimized layout, contain, cover or stretch; follow preview placement or use **Separate arrangement**. Video export uses source time and original speed even while Practice playback runs slower. Wait for detailed preparation before exporting. The microphone toggle listens on the same canvas while playback may continue; choosing another track exits monitoring. Imported presets and attached images stay local.

Note estimates are suggestions, especially on dense mixes. Corrections stay separate from raw model results and survive reopening. Replacing the contents behind a file URI clears stale corrections and requires fresh analysis. Older timeline caches are rebuilt for the corrected decoder. MIDI always exports sounding concert pitch. Frequency bands are not isolated instruments; no stem-separation feature is implemented.

Detailed audio analysis is limited by device heap, up to 30 minutes. Source-video frame decoding is bounded to 4,096 pixels per edge and about 8.8 megapixels. Encoder support varies; unsupported media/settings return visible errors. Performance on physical phones and accuracy on dense songs remain unverified. Core features work offline without an account/server; the app requests no Internet permission.

## Verification and provenance

Current Preview 6 validation and publication results are recorded in [Preview 6 evidence](docs/acceptance/preview-6-evidence.md). Owner-phone acceptance remains pending. Historical Preview 4 validation: [run 40009120574](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40009120574), status `success`; host `118` tests / `20` suites, failures/errors/skips `0 / 0 / 0`; API26/API36 each passed 30 general cases plus one fresh-permission case. Its successful emulator results did not resolve the later owner-phone blank-preview report.

The earlier `b0675314` candidate passed host/lint/build and API 36, but API 26 timed out while a test generated its color-video input. Fixture-only `5073c272` retained all assertions and passed API 26, while API 36 exposed an early seek before decoder output: the first red-frame assertion timed out with missing SPS/PPS logs. Both publishers correctly blocked release. The renderer correction keeps those valid inputs and assertions unchanged; the regression passes on both APIs in exact-source run `40009120574`.

[Preview 4 evidence](docs/acceptance/preview-4-evidence.md) records first-note feedback, stale-result rejection, silent/rotated video, layer composition, pause/seek and audio/video transitions, source-time exports, timeline/cache regressions and EGL lifecycle checks. [Preview 3 evidence](docs/acceptance/preview-3-evidence.md) and the [execution record](docs/acceptance/execution-record.md) are historical baselines. Preserve [third-party notices](THIRD_PARTY_NOTICES.md) and the [design](docs/superpowers/specs/2026-10-22-blazing-visualizer-design.md).

Existing instrumentation also checks independent Python model/postprocessor parity, synthetic/CC0-flute onset accuracy, deterministic GL, playback/loops, Compose flows, all six export presets, duration and cancellation. Synthetic/emulator results do not establish physical-phone latency, real-song accuracy or full Avee interoperability. Unsupported Avee expressions, shaders, masks, fonts, temporal effects and `.viz` re-export remain unfinished; retained raw metadata is not proof of rendering support.

[Instrument-separation research](docs/acceptance/2026-10-23-stem-separation-research.md) proposes a measured offline pilot; it adds no model, runtime or song upload. The [reference recording's math fact check](docs/acceptance/reference-video-math.md) remains separate from source-video playback. Video-to-graph tracing/Bezier conversion stays last priority.

Reference fixtures can be regenerated with Python 3.11, `tools/requirements-reference.txt`, `tools/build_acceptance_fixtures.py` and `tools/reference_analyze.py --upstream <pinned-basic-pitch-checkout>`.
