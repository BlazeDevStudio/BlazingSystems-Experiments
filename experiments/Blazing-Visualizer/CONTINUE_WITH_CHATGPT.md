# Continue Blazing Visualizer with ChatGPT and GitHub

Use ChatGPT, connected GitHub tools and GitHub Actions directly. Do not launch Codex/cloud coding-agent tasks or require Codex credits.

Repository: https://github.com/BlazingSystems/BlazingSystems-Experiments
Branch: blazing-visualizer
Project: experiments/Blazing-Visualizer
PR: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/133

Read HANDOFF.md first, then HANDOVER.md, README.md, docs/acceptance/review.md and the latest design and plan. Inspect recent commits and resume unfinished work; do not recreate the application. Keep all implemented playback, offline Basic Pitch analysis, Practice, note corrections, presets and MP4 export. Keep upstream license notices.

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
12. Microphone mode for external instruments/music, with runtime permission, note/frequency/cents/confidence and guitar tuning guidance; pause playback to avoid feedback, release microphone on exit/background.
13. Research primary YIN/autocorrelation tuner sources, silence/noise rejection, harmonic mistakes, smoothing and calibration. Use monophonic tuning for individual strings while keeping Basic Pitch for polyphonic recorded music; measure changes rather than claiming perfect transcription.
14. Independent element colors and optional global palette, persisted and round-tripped through native presets and applied to MP4 output.

Routine design, implementation, testing, branch updates and preview publication are approved. Do not repeatedly ask to continue. Work directly in source in reviewable commits. Reproduce reported bugs and verify meaningful regressions. Keep main and previous releases intact.

Build using JDK17, SDK36/build-tools36.0.0:
./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
./gradlew :app:connectedDebugAndroidTest

Use GitHub Actions if local build tools are unavailable. Never claim a test or feature is complete without actual evidence. Preserve existing evidence as a historical baseline, not proof of future changes. Publish only a clearly labeled new preview after relevant checks pass, with a verified GitHub Releases direct APK URL. ChatGPT file download URLs fail on the owner's phone.

Before ending each pass update HANDOFF.md with exact commits, completed features, tests/CI evidence, failures, remaining requests, relevant files, next actions and release/signing details. Push source plus handoff so scratch cleanup or exhausted credits cannot erase progress.

Report briefly: changed, verified, pending, and the working APK link when available.
