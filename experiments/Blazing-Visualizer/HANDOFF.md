# Blazing Visualizer — current handoff

Updated 2026-10-22 Asia/Manila — ChatGPT direct GitHub continuation after owner follow-up.

## Branch / changes actually pushed
- Repository: BlazingSystems/BlazingSystems-Experiments, branch `blazing-visualizer`, draft PR #133. Main remains untouched.
- **47635172ca422f9156b28db15db48135cfcab1c8**: Practice settings moved into the per-track serialized Project. Practice controls save speed, spelling, instrument transposition, register, A/B endpoints and enablement, and restore playback speed/loop on selection; added host regression for roundtrip and legacy decoding.
- **f1fbaf41af255b56bd08087420c3c69fd8009995**: Separate persisted Library and Queue; request READ_MEDIA_AUDIO API33+ / READ_EXTERNAL_STORAGE up to API32, MediaStore auto-discovery and refresh, manual SAF import retention; Media3 insert/move/sort operations without using setQueue for edits; Queue long-press drag and play-next; simplified header; explicit MP4 orientation labels and a live composition preview.
- **1b9428f2a27893b28edd4559117623e5b2d4053d**: automatic sequential background Basic Pitch analysis for discovered/imported library, current-track priority through cancellation, existing content-hash/model/parameter cache, decoded PCM cleanup and a size-bounded cache compaction.
- **8775af84df291cf84e8b2a9c6ca24ff71a1180f3**: Lo/Lo2/Mid/Mid2/Hi/Hi2 note-range routing with optional MIDI limits and displayed octave/Hz conversions; deterministic pitch-specific piano glow/sparks, global/piano intensity and scene palette persistence/pack validation; host test for note bands and serialization.
- **84148e2a28594a4950147ab84babf8fd89e687c7**: explicitly check microphone permission inside MicrophoneCapture before AudioRecord allocation; CI lint regression fix (pending CI confirmation).
- **6a87eb3024c700f2584eeb9002428ce438faebf6**: RECORD_AUDIO microphone tuner, monophonic YIN with silence/confidence gating and sliding-window frequency median, guitar string guidance, calibration, player pause, lifecycle/dismiss release; added sine-wave/quiet-input test.

## Verification: state at this handoff
- Last verified baseline (before 2026-10-22 owner iteration): workflow 39727215485 and 39727210670 succeeded on 2c2acf3a, with earlier 45 host tests and API26/API36 device evidence. **Those results do not certify any new source changes.**
- On commit 8775af84, CI run 39729708429 reported successful Android host/build job; its device jobs were cancelled by a newer commit and cannot be counted as device passes.
- Latest original candidate 6a87eb30, CI workflow **39730334534**, did compile Kotlin/test Kotlin and assembleDebug, but **FAILED :app:lintDebug**, 1 error: MicrophoneCapture.kt:20 MissingPermission on AudioRecord constructor (log, 2026-10-22T05:56:16Z). Source fix adds explicit Context.checkSelfPermission before creating recorder and handles revocation; new runs 39731005020 and 39731012634 started for commit 84148e2a and remained in progress at last check. The parallel workflow **39730338818** had not yet concluded at the time of this check. Full host/lint/API26/API36 green status is NOT claimed. Check https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/workflows/blazing-visualizer.yml?query=branch%3Ablazing-visualizer
- Existing, previously verified APK is ONLY preview 1, https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.1/Blazing-Visualizer-preview-1.apk, SHA256 ba86f7b48b9b751d3d1399611dc1cd8e2d20cfdc26ce92cb14322ec4d9e5ffb3, 31605136 bytes, **does not include the 2026-10-22 changes**. Verified through the existing GitHub Release API listing. Debug signing only.

## Known remaining owner requests / verification requirements
1. Implement actual long-press on-canvas element move/resize with handles, reset and layouts. Existing sliders only are not equivalent.
2. Independent export-layout editor and explicit follow/fit-vs-independent choice; the new output preview alone is not that feature.
3. Verify all new 2026-10-22 features end to end, including actual physical-device MediaStore permission / revoke behavior, queue drag and sorting preserving playing position, and realistic background analysis memory/performance. CI compiling alone does not prove runtime behavior.
4. Review foreground/background PCM race on rapid track switching, ensure current-track decoded files are protected from background cleanup, and independently test cache resumability.
5. Measure YIN harmonics/strong interference/octave errors and smoothing on instrument recordings; current sine synthetic test is narrow. Compare against annotated recordings and document cents error/outlier rates.
6. Check piano effects on real chords with precise note-onset triggers and zero-intensity pixels, and preview/MP4 parity. Recheck global palette's impact on legacy spectrum settings.
7. Conduct new API26/API36 instrumentation, then physical arm64 testing, preview release 2 packaging/signing continuity and actual release APK download verification.
8. Production signing and release are NOT approved by evidence until acceptance tests pass. Main must not be merged until owner approves.

## Next exact actions
- Inspect the current CI run **39730334534 / 39730338818**; if Gradle failed, retrieve failing task and fix (do not assume compile or all tests are green). Re-run after changes.
- Finish on-canvas layout editing/export choices and add native regressions for Practice/queue, MediaStore, render and tuner lifecycle.
- When full host/lint/API26/API36 matrix passes on the same candidate, publish clearly labeled preview 2 with a verified direct Github Releases APK URL and checksum; do not claim a new APK until actually verified.
- Preserve upstream notices, Basic Pitch, deterministic renderer, Media3 playback, Project notes/edits, preset packs, MP4 export. Use GitHub tools/Actions directly, no Codex agent or main merge.

---
## Previous historical handoff

Updated 2026-10-22 (Asia/Manila). Resume this project; do not restart it.

## Source and released baseline
- Repository: BlazingSystems/BlazingSystems-Experiments
- Branch: blazing-visualizer; draft PR #133. Main has not been merged.
- Validated application source: 590150cc672007a3951b7d6f5366a532297be5ae.
- Preview publication workflow commit: e7423407ddc1ca7481e69b7861f3fb47d1bec669.
- Full source CI run 39717064004 succeeded, including host checks and API26/API36 device jobs.
- Published preview: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazing-visualizer-v1.0.0-preview.1
- Direct APK: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.1/Blazing-Visualizer-preview-1.apk
- Published CI APK SHA256: ba86f7b48b9b751d3d1399611dc1cd8e2d20cfdc26ce92cb14322ec4d9e5ffb3; 31,605,136 bytes.
- This is a different packaging/signing artifact from the earlier locally built ChatGPT copy (f315a0c0...). Use each artifact's own checksum.
- Debug preview; API26+, arm64-v8a and x86_64. Future CI builds need signing continuity checked before an in-place upgrade is promised.

## Current owner request
Owner liked preview 1 and requested the complete iteration list in CONTINUE_WITH_CHATGPT.md. That file is the portable ChatGPT+GitHub directive; it explicitly avoids launching Codex tasks.

## Investigation completed this pass
- Restored current source from GitHub after automated scratch cleanup.
- PracticeSheet uses rememberSaveable locals for spelling/transposition/register/loop. These leave composition when the sheet closes; Project does not persist Practice settings. This is the confirmed persistence root cause.
- ExportSheet already supports landscape/portrait/square in 720p/1080p, but labels only show ratios; make names and arrangement clearer.
- LibraryScreen and Queue currently both display StudioState.queue. LibraryRepository imports only selected documents; manifest has no music-storage permission.
- ScenePainter has pitch-specific key sets but hard-coded colors and no independent key effects. The owner's whole-strip-lighting report still needs a rendering regression; do not claim the exact device symptom reproduced yet.
- AnalysisRepository already caches by audio hash/model/parameters. Build on it; do not replace Basic Pitch with a monophonic tuner for whole songs.

## Not implemented yet at this checkpoint
All 14 iteration requests remain pending implementation/verification. A new APK has NOT been published for them.

## Working plan
1. Persist Practice controls and separate library from queue; implement permission-based MediaStore discovery, real queue rearrangement and serialized automatic preparation.
2. Add note-range routing, palette/intensity controls, precise per-key effects and preview/export layout editing.
3. Add measured YIN microphone tuning with permission/lifecycle handling.
4. Run host/build/lint and relevant device checks, review changes, publish preview 2, update this handoff with exact evidence.

## Research / established behavior
- Android audio permission: https://developer.android.com/about/versions/13/behavior-changes-13
- MediaStore: https://developer.android.com/training/data-storage/shared/media
- Microphone permission, raw input and lifecycle: https://developer.android.com/media/platform/mediarecorder
- YIN original paper: de Cheveigne and Kawahara, JASA 111(4), 1917–1930 (2002), DOI 10.1121/1.1458024.
- Visual reference: https://www.seemusicapp.com/seemusic (note-triggered lights/particles). Implement original drawing; do not copy assets.

See HANDOVER.md and docs/acceptance/review.md for original implementation details and historical limitations.
