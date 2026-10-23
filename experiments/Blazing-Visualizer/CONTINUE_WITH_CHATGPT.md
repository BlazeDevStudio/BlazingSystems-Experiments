# Continue Blazing Visualizer with ChatGPT and GitHub

Use ChatGPT, connected GitHub tools and GitHub Actions directly. Do not launch Codex/cloud coding-agent tasks or require Codex credits.

Repository: https://github.com/BlazingSystems/BlazingSystems-Experiments
Branch: blazing-visualizer
Project: experiments/Blazing-Visualizer
PR: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/133

Read HANDOFF.md first, then README.md, docs/acceptance/preview-3-evidence.md and the latest design/plan. HANDOVER.md and older review files are historical baselines. Inspect recent commits and resume unfinished work; do not recreate the application. Keep all implemented playback, offline Basic Pitch analysis, Practice, note corrections, presets and MP4 export. Keep upstream license notices.

Owner's 2026-10-22 requests:
1. Simplify redundant header/status content.
2. Request READ_MEDIA_AUDIO on API33+, READ_EXTERNAL_STORAGE through API32; automatically scan MediaStore after grant and on library refresh. Preserve manual file import and graceful denial.
3. Make Queue independent of Library; long-press drag ordering, play-next and sorting must update Media3's real playlist without restarting the current track.
4. Automatically preanalyze imported/discovered tracks, prioritize the current track, serialize inference, cache by content hash/model/parameters, resume on next library load and avoid unbounded PCM storage or freezing playback.
5. Reproduce and fix Practice settings disappearing after Save or sheet dismissal. Persist speed, spelling, instrument transposition, register and track-specific A/B looping. Restore player behavior as well as UI.
6. Assign each layer a note range: All or Lo/Lo2/Mid/Mid2/Hi/Hi2, with editable MIDI/octave/Hz boundaries. The 2 means an intermediate range, not loudness. Keep polyphonic chords.
7. Long-press to arrange, then move/resize elements with visible selection handles, saved layouts and reset.
8. Let export follow/fit the preview or use an independently arranged export layout. Make the choice explicit while customizing.
9. Explicit Portrait/Landscape/Square selection, dimensions and a composition preview before MP4 export.
10. Make piano highlights/glow/sparks belong to actual active pitches only, including real chords. Research SeeMusic-style note-impact glow/particles rather than lighting the whole strip.
11. Global animation-intensity control plus independent piano intensity. Zero removes decorative effects. Use the same deterministic renderer for preview and export.
12. Microphone toggle for external instruments/music feeds the SAME main visualizer in real time, including simultaneous estimated notes when feasible. No separate guitar-tuner window. Keep permission and background/exit capture release. Musical playback can continue during monitoring; selecting a new playback track exits monitoring. Precise single-note frequency/cents uses YIN; mixed music remains an estimate.
13. Research primary YIN/autocorrelation tuner sources, silence/noise rejection, harmonic mistakes, smoothing and calibration. Use monophonic tuning for individual strings while keeping Basic Pitch for polyphonic recorded music; measure changes rather than claiming perfect transcription.
14. Independent element colors and optional global palette, persisted and round-tripped through native presets and applied to MP4 output.
15. Reference recording: Screen_Recording_20261022_145348_Facebook.mp4. Its musical visuals suggest animated graph cursors, Lissajous chord curves, orbit markers, wave panels and note-impact glow. Read docs/acceptance/reference-video-math.md for the fact check. Implement original note-derived visuals, not the video's artwork/audio. Keep equations OFF by default with an explicit checkbox to include them. MIDI A4 is 69, while the video's piano-key index is 49; equal temperament and just intonation are different. A circle needs quadrature, not x=sin(t), y=sin(t).
16. The last video-to-graph tracing/Bezier idea is LAST PRIORITY. First finish and deliver the other features/APK WITHOUT the video renderer. Do not let tracing delay this release.

Routine design, implementation, testing, branch updates and preview publication are approved. Do not repeatedly ask to continue. Work directly in source in reviewable commits. Reproduce reported bugs and verify meaningful regressions. Keep main and previous releases intact.

Build using JDK17, SDK36/build-tools36.0.0:
./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
./gradlew :app:connectedDebugAndroidTest

Use GitHub Actions if local build tools are unavailable. Never claim a test or feature is complete without actual evidence. Preserve existing evidence as a historical baseline, not proof of future changes. Publish only a clearly labeled new preview after relevant checks pass, with a verified GitHub Releases direct APK URL. ChatGPT file download URLs fail on the owner's phone.

Before ending each pass update HANDOFF.md with exact commits, completed features, tests/CI evidence, failures, remaining requests, relevant files, next actions and release/signing details. Push source plus handoff so scratch cleanup or exhausted credits cannot erase progress.

Latest owner steering: close modern Avee phone workflow, real .viz interoperability rather than renamed native scenes, continuous next-song/repeat playback, no bottom blank strip in optimized exports, substantially closer motion. Keep editable note-wheel idle text; only show it with no notes. Unknown chords display every simultaneous note. Do not market Spectrum2 strongest-bar indices as named note detection. Preview 3 is published from b9db4c115b5fc42905b7ede9e844a67c2f76acf2: 108 host tests, lint/build and API26/API36 passed. Its direct APK is https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.3/Blazing-Visualizer-preview-3.apk . Read HANDOFF.md for evidence and remaining compatibility work. Do not replace this tag/asset; use Preview 4 for the next APK.

Report briefly: changed, verified, pending, and the working APK link when available.
