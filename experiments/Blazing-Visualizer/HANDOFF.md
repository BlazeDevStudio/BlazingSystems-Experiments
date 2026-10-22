# Blazing Visualizer — current handoff

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
