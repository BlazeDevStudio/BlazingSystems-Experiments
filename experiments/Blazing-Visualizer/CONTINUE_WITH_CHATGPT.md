# Continue Blazing Visualizer with ChatGPT and GitHub

Use ChatGPT, connected GitHub tools and GitHub Actions directly. Do not launch Codex/cloud coding-agent tasks or require Codex credits.

Repository: https://github.com/BlazingSystems/BlazingSystems-Experiments
Branch: `blazing-visualizer`
Project: `experiments/Blazing-Visualizer`
PR: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/133

Read `HANDOFF.md`, `README.md`, `docs/acceptance/preview-6-evidence.md` and `docs/plans/2026-10-24-playback-pcm-notes.md` first. `HANDOVER.md`, Preview 3/4/5 evidence and older reviews are historical. Inspect recent commits and resume; do not recreate the app. Preserve playback, offline Basic Pitch analysis, Practice, corrections, presets, layouts, MP4 export and upstream license notices.

## Latest owner feedback and active repair

The owner confirmed Preview 5 still shows no visualization on their phone. Preview 6 is now published and independently verified, but owner-phone confirmation remains pending. It uses actual playback PCM → bounded DSP → canvas, with a one-tap measurements-only diagnostic report and cached resampler coefficients. Published source `a718e2a45e798038885a9c52f38a89b5a2f623e5`; validation `40085323906` and publisher `40085323837` succeeded. Host 129/24 suites; API26/API36 each 31 general + 1 permission case, all zero failures/errors/skips. Read `docs/acceptance/preview-6-evidence.md` and current HANDOFF first.

Direct APK: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.6/Blazing-Visualizer-preview-6.apk — 31,900,372 bytes; SHA-256 `14e67d1225e76e3bcfefaa73ceaf3ae0d9d1dc6245b7624dd8f7e06d0577f532`. It updates Preview 2/3/4/5 in place. If still blank, play a track, open **Check visualizer**, wait for its local check, choose **Copy report**, then inspect the pasted measurements before guessing another fix. Supplied songs/excerpts/PCM must remain local, strictly for testing; never upload them into GitHub/CI. Earlier successful emulator checks below are historical, not owner-phone acceptance.

## Historical Preview 4 checkpoint

Preview 4 adds mixed audio/video selection, source video behind the existing visualizer through one Media3 session, source-time video export, silent-video support and independent bounded quick note feedback. Quick estimates never become verified analysis, saved note edits or export note data. Detailed results replace them when ready.

The candidate also preserves delayed/gapped audio and longer video tails in original/analysis PCM, trims overlaps, versions incompatible PCM/analysis caches and fixes shared EGL ownership across preview/export. The decoder uses the existing Media3 1.8 extractor. A fixed original synthetic MP4 replaces an API 26 writer-dependent timing fixture. Read the evidence before interpreting intermediate failures.

The renderer handles a seek before its decoder's first output format. It keeps Media3's normal position/sink reset, then releases only the same existing decoder if that early reset retained it. The next render restores fresh codec-specific data through normal initialization. Android documents CSD loss after an early flush. Later seeks use normal Media3 flushing. The existing valid fixture and seek assertions remain unchanged; the first-red-frame regression passes on both API 26 and API 36.

Final exact-source CI: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40009120574 — `success`.
Publisher: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40009120823 — job `120604608420`, `success`.
Published source: `72c94336eca8cdc4190224248b4f8082209aa516`.
Host: `118` tests / `20` suites, failures/errors/skips `0 / 0 / 0`; lint/APK `passed` in build job `120604607048`. API 26 `passed 30 general cases plus one fresh-permission case, with zero failures/errors/skips`; API 36 `passed 30 general cases plus one fresh-permission case, with zero failures/errors/skips`.
Verified direct APK: `https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.4/Blazing-Visualizer-preview-4.apk`.
Final-source CI APK bytes / SHA-256: `31,867,604` / `9026659db4866793fc963297d69ac357c4eb26069e74432d63a4874f289e860f`.

Preview 3 remains available at its original tag/asset, source `b9db4c115b5fc42905b7ede9e844a67c2f76acf2`. Its 108 host tests and API 26/36 results are historical. Keep all older releases intact; never overwrite a published tag or APK.

Latest owner priorities are mixed media and startup responsiveness, then genuine Avee preset interoperability, phone validation and production hardening. Preserve the native presets they like. Source-video backgrounds are now requested; the separate video-to-graph tracing/Bezier idea remains **last** and must not delay player improvements. Equations stay off by default.

Routine design, implementation, testing, branch updates and preview publication are approved. Do not repeatedly ask to continue. Reconcile remote heads, use expected-SHA leases for updates and make reviewable commits. Keep main and all previous releases intact. Do not rely on uncommitted scratch files surviving a reload.

## Owner's earlier requirements — preserve implemented behavior

1. Simplify redundant header/status content and keep phone controls reachable.
2. Request `READ_MEDIA_AUDIO` on API 33+ and `READ_EXTERNAL_STORAGE` through API 32; scan MediaStore after grant/refresh, preserve manual import and graceful denial.
3. Keep Queue independent of Library. Drag ordering, Play next and sorting update Media3's real playlist without restarting the current track; preserve continuous next-track, last-to-first, repeat and shuffle behavior.
4. Automatically prepare imported/discovered tracks; prioritize selection, serialize inference, cache by content/model/parameters and avoid unbounded temporary PCM or freezing playback. Preserve source-time alignment and reject obsolete results.
5. Persist per-track Practice speed, spelling, written-instrument transposition, register and A/B loops, restoring player behavior as well as UI.
6. Give layers All, Lo/Lo2/Mid/Mid2/Hi/Hi2 or custom MIDI/octave/Hz ranges. The 2 means an intermediate range, not loudness. Keep polyphonic chords.
7. Long-press arrangement needs move/resize handles, saved layouts and reset.
8. Export can follow/fit preview placement or use an explicitly separate arrangement; preserve custom separate layouts.
9. Show portrait/landscape/square choices, dimensions and a composition preview before export; avoid a blank bottom strip in optimized layouts.
10. Piano glow/sparks belong to active pitches, including actual chords; do not light the whole keyboard. Continue measured SeeMusic-style note-impact refinement.
11. Keep global animation intensity and independent piano intensity. Zero removes decorative effects. Preserve deterministic preview/export drawing.
12. Microphone input feeds the same main canvas, with conservative simultaneous estimates and precise monophonic YIN when applicable. Playback may continue. New track selection exits monitoring; background/disable/exit releases capture. No separate tuner window or saved/uploaded microphone audio.
13. Use primary YIN/autocorrelation sources, silence/noise rejection, calibration and measured tests. Keep Basic Pitch for recorded polyphonic music; avoid perfect-transcription claims.
14. Preserve independent layer colors and optional global palette through native-pack round trips and MP4 output.
15. Preserve editable note-wheel idle text, shown only with no notes. Unknown chords display all simultaneous note classes. Spectrum2's strongest-bar index is not named-note detection.
16. Preserve original note-derived motion inspired by `Screen_Recording_20261022_145348_Facebook.mp4`, not its artwork/audio or purported production stems. See `docs/acceptance/reference-video-math.md`: MIDI A4 is 69; piano-key index 49 is different; equal temperament and just intonation differ; a circle needs quadrature. Equations default off.
17. The historical request to deliver the earlier APK without a video renderer does not cancel the later explicit mixed-media/background-video request. Graph tracing/Bezier conversion stays last priority.

## Evidence and release rules

Build with JDK 17, SDK 36 and build-tools 36.0.0:

```sh
./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
./gradlew :app:connectedDebugAndroidTest
```

Use GitHub Actions when local tools are unavailable. The Windows continuation workspace had no local JDK/Android SDK. Full release checks need clean host XML, lint, both APKs, API 26/36 permission/general suites, inspected native artifacts and exact-source validation. Diagnostic-only checkpoints deliberately omitted gates and cannot publish previews.

Keep historical failures factual. The first Preview 4 implementation failed API 36 EGL survival. Native RED checkpoint `d855944` reproduced source-time/cache/EGL defects on API 36; API 26's generated timing input failed its setup check and was replaced by a fixed independently checked synthetic asset. Host runs stalled without identifying a worker cause; independent diagnostic `39959477936` later passed unchanged source, 118 tests/20 suites. Do not claim that an infrastructure cause was diagnosed/fixed. Candidate `df3d0164` passed host tests but failed lint on a platform seek constant; `b0675314` uses the existing compatible-extractor constant. Final verification must refer to the final source.

Later candidate `b0675314`, full run `39962875776`, passed 118 host tests/20 suites, lint/APKs and API 36's 30 general plus one permission case. API 26 passed permission and recorded 25 general status-0 results, then timed out while `readerUsesSourceTimeAndReturnsRotatedBoundedFrames` was creating its input with the live H.264 encoder. No full general XML/acceptance tar or exact blocked call was available. Publisher `39962875773` rejected that incomplete run. Do not claim a production frame-reader failure or all-API success for it.

Fixture-only `5073c272` changed test inputs/loader and evidence: fixed original silent red/green videos at rotation 0/90 replace the live generator, preserving all color/time/rotation/composition assertions. Production encoder coverage remains in the six-size matrix, four-second export and background-video export. Run `39968524056` passed all API 26 tests; API 36 passed 29/30 general cases and failed only the first red-frame wait after the initial paused seek to 100 ms. Decoder configuration was followed almost immediately by a flush and missing SPS/PPS/no-frame logs. Publisher `39968524038` blocked release. The valid assets and regression remain unchanged in released `72c94336`; full run `40009120574` passed and publisher `40009120823` released Preview 4. The earlier 5073 results are historical.

Publish only a separately versioned, clearly labeled preview after checks pass. Retain Preview 2/3's public debug-only signer; never use it for production. Verify package/version, v2 signature, certificate, both ABIs, APK size, SHA256SUMS and equality between CI and a fresh direct-download copy. ChatGPT file URLs fail on the owner's phone; deliver a GitHub Releases direct APK URL. Never overwrite an earlier tag/asset.

Before ending each pass, update `HANDOFF.md` with exact source, changes, tests/jobs, observed failures, remaining requests, release/signing details and next steps. Push source and handoff so scratch cleanup or exhausted credits cannot erase progress.

## Remaining limits and next work

Avee interoperability is partial. Safe expressions, dynamic text, custom shaders/masks/fonts, exact temporal feedback blur/beat gain, older formats and `.viz` re-export remain incomplete. Preserved metadata is not rendered parity. Use a genuine permissioned exported `.viz` fixture and physical phone next; keep dense-song transcription and physical ARM64/microphone latency claims unverified until measured.

Real stem separation is research only: `docs/acceptance/2026-10-23-stem-separation-research.md` proposes a measured offline vocals/accompaniment pilot, reference engines and quality/performance gates. No model/runtime was added and no songs were uploaded. Frequency ranges are not isolated drums/piano/vocals. Production signing/store distribution are also unfinished. Video tracing remains last.

Report briefly: changed, verified, pending and the working direct APK link when available.
