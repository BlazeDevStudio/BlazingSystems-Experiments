# Blazing Visualizer handoff

Updated 23 October 2026 (Asia/Manila). Continue this existing Android app; do not restart or overwrite concurrent work.

## Preview 4 continuation: validation in progress

Latest checkpoint `b06753140bcc8b5f476edfebd4e4c1b5ea9866f1`, [run39962875776](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39962875776): clean host XML confirms118 tests/20 suites with zero failures/errors/skips; lint and both APK assemblies pass. API36 passes30 general cases plus1 independent permission case. API26 passes its permission case and25 general cases, then reaches the25-minute limit while creating the color-video input for `readerUsesSourceTimeAndReturnsRotatedBoundedFrames`. Its partial logs show the fixture encoder started, but no EOS/stop or reader progress. No assertion failed; the remaining5 cases are unverified. Publisher39962875773 correctly blocked release. Fixed original synthetic red/green videos at rotation0/90 replace this live test setup next; production decoder/EGL code and all existing assertions are retained. Complete exact-source checks must pass again before release.

The unreleased `1879d577d5cbd626fd1ddf993cd975fcc9b0eac7` implements the approved mixed-media/fast-notes plan: multi-select audio/video, one synchronized Media3 video background, source-time video in MP4 output, silent-video support, and temporary bounded note estimates before whole-file Basic Pitch finishes. It is not yet a verified release.

Its original validation `39920860762` passed 118 host tests, lint/APK and API26, but API36 failed the existing EGL target-survival test. The publisher correctly blocked Preview4. Fresh review also found collapsed audio timestamps and truncated video duration when video audio starts late, has gaps, or ends early.

Test checkpoint `5bed678f93484ee6dc4d389d1883e533876095aa` adds real delayed/gapped/short-audio MP4 regressions, an old-analysis-cache rejection case and inactive/idempotent EGL close coverage. Run39933760214 stalled in host runtime initialization. Diagnostic checkpoint `d85594426a4f064af350832dd4b8bb110074fc40`, run39936432159, compiled both APKs and observed the three timing assertions, stale-cache assertion and both EGL assertions fail on API36. API26 additionally exposed its framework extractor reporting the fixture's initial timestamp as zero. The publisher was explicitly disabled for that diagnostic checkpoint. See [Preview 4 evidence](docs/acceptance/preview-4-evidence.md) and the [mixed-media plan](docs/superpowers/plans/2026-10-23-mixed-media-fast-notes.md).

The fix candidate preserves chunk source timestamps in both original/analysis PCM with bounded silence insertion, overlap trimming and video-tail padding. Legacy PCM and analysis caches are invalidated without changing content identities. Decoding now uses the existing Media3 extractor, matching playback's container timeline across Android versions. EGL targets share display ownership, release only their own context/surface and tolerate repeated close. Complete host/lint/APK validation and publication are restored; device checks and final release remain pending.

Next: finish source-time PCM and shared EGL ownership fixes, revalidate clean host/lint/APK plus API26/API36, inspect native artifacts, then publish a separately versioned Preview4 with the retained signer. The existing verified download below remains Preview3 until those checks pass. No local JDK/Android SDK was available in the Windows continuation workspace; builds run in GitHub Actions.

## Current APK: Preview 3, published and verified

- Direct download: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.3/Blazing-Visualizer-preview-3.apk
- Release: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazing-visualizer-v1.0.0-preview.3
- Exact release source: `b9db4c115b5fc42905b7ede9e844a67c2f76acf2`. App versionCode 3 / versionName 1.0.0-preview.3.
- Full validation: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39897614925 . Clean JDK17 / SDK36 host tests, lint and both APK assemblies passed. Downloaded XML confirms 108 host tests, zero failures/errors/skips. API26 and API36 each passed 19 general native/UI cases plus their independent fresh-permission flow.
- Build job 120231570299; API26 job 120232736456; API36 job 120232736501. Real native JSON/PNG/MP4 evidence was retained and inspected, including spatial-chord, rhythm and radial frames, graph exports and source/audio alignment.
- Publisher: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39897614942 . Job120231570274 verified package/version, APK Signature Scheme v2, retained signer, both ABIs and downloaded identical release bytes.
- APK size 31,834,700 bytes. SHA256: `2fa101ecf699a03198ce37d9125d8c3a263ed31c533df0f717738ff614d444da`. The root session independently downloaded the public URL, checked SHA256SUMS, ZIP integrity and equality to the CI APK.
- Retained public debug-only certificate SHA256: `64f9fbd13d72bb5ef88bccdc4602a487fea21fb73a13298b93a0f2b1f6c2109c`. Preview 3 can update Preview 2 in place. Preview 1 had a different key: export wanted presets before a one-time uninstall/reinstall. Never use this public preview identity for production.

ChatGPT file URLs fail on the owner's phone. Deliver direct GitHub Releases APK URLs. Keep existing release assets/tags intact; the next APK needs a separately versioned Preview 4 release.

## Repository and working scope

Repo: `BlazingSystems/BlazingSystems-Experiments`; project: `experiments/Blazing-Visualizer`; development branch: `blazing-visualizer`; draft PR133: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/133 . Main remains untouched. Backup branch `blazing-visualizer-notes-motion` also preserves this iteration.

The owner wants modern Avee familiarity and useful preset interoperability, phone controls, continuous playback, playable note following, and MP4 export. Preserve the existing native presets they like. Routine implementation, feature-branch updates, checks and preview publication are approved; do not repeatedly ask to continue or launch paid Codex tasks. Reconcile remote heads and update refs with expected-SHA leases. Do not rely on uncommitted scratch files surviving a reload.

Portable non-Codex continuation prompt: [CONTINUE_WITH_CHATGPT.md](CONTINUE_WITH_CHATGPT.md).

## Implemented and reconciled

- MediaStore music permissions/discovery, manual import, separate drag-reorder/sort/play-next queue and playlists. Repeat-all, repeat and shuffle settings persist; real end-of-track and last-to-first transitions are tested.
- Compact reachable phone actions, visible Songs/Playlists navigation, thumbnail preset grid and fullscreen viewing. A requested source has priority over stale old-media updates.
- Per-track Practice speed, written transposition, spelling/register, A/B looping, corrections and MIDI/CSV export persist. Basic Pitch preparation runs automatically, caches results and prioritizes the current track. Decoded audio ownership and cold-start persistence are guarded.
- Per-layer Lo/Lo2/Mid/Mid2/Hi/Hi2 or custom MIDI ranges, independent piano/global intensity and colors. Only active pitches light their keys. Long-press move/resize, preview-following or separate export layouts, explicit portrait/landscape/square and optimized note/keyboard reflow exist. Custom separate layouts remain preserved.
- Note-wheel idle text is editable and appears only with no notes. Unknown chord sets display all simultaneous note classes in fitted rows; exact-set chord templates avoid guessing from missing tones.
- The mic toggle feeds the SAME canvas, with up to six conservative simultaneous spectral pitches and precise monophonic YIN when applicable. Capture time animates the canvas even without a playing track. Playback may continue while monitoring; selecting another track exits monitoring. Background/exit/disable releases capture. It is not a separate tuner window and does not save or upload microphone audio.
- Five optional motion presets add luminous trails, projected chord axes, shared-cursor progressive wave reveal/reset, fixed rhythm gates with a sweeping hand, and settled radial contours. Speed/trail/camera/subdivision controls are editable. Original native/graph presets remain. Equations default OFF.
- Avee plain JSON and JSON-in-ZIP .viz imports retain original metadata and referenced composition passes rather than flattening. Paired segments preserve independent colors and signed heights. Common image tint/aspect/circle/blend and bounded effects are supported. Explicit image replacements override retained sources. Configured Spectrum2 correlation/response feeds bars in preview/export; mic input retains up to 300ms PCM and applies capture-time smoothing. Native pack round trips retain original metadata.

Key files: `tuning/LiveNoteTracker.kt`, `tuning/LiveSpectrum2.kt`, `tuning/MicrophoneCapture.kt`, `avee/Spectrum2Analyzer.kt`, `audio/AudioRepository.kt`, `packs/VisualizerPack.kt`, `render/AveeScenePainter.kt`, `render/MotionGeometry.kt`, `render/MathCurvePainter.kt`, `render/SceneLayouts.kt`, `ui/PresetChooserSheet.kt`, `ui/AveeShell.kt`, `ui/StudioModel.kt`.

## Verification history and remaining work

[Preview 3 execution/review evidence](docs/acceptance/preview-3-evidence.md) records the independent review, real RED-to-GREEN tests, failed intermediate runs and corrected Android test ownership/timing. App product code is edcd8ad; b9db4c1 changed test/CI evidence handling and docs. Both built APKs are byte-identical. The former evidence tar contained an unknown-package error because Gradle uninstalled the app; current CI preserves the APK after the second instrumentation run and validates required tar members.

Compatibility remains PARTIAL. Safe measure expressions, dynamic text tokens, custom shaders/masks/fonts, exact temporal feedback blur/beat gain, older Spectrum/binary variants and Avee .viz re-export are incomplete. Unknown/raw fields survive native packs; that does not mean they are rendered. Numeric mirror flags work; JSON boolean mirror handling is a deferred minor. Maximum-size frequency banks make cold seeks expensive; physical timing is unmeasured. Next, use a genuine permissioned exported .viz fixture and a physical phone to measure actual interoperability and responsiveness.

The inspected Avee 1.2.252 upload is unofficially modified. Functional/schema observations and original implementations are permitted; do not redistribute its APK, code or artwork. A prior narrow DEX audit found Spectrum2's arbitrary-frequency bank and response controls; its strongest-bar index is not a named-note detector. Static inspection is not proof of official runtime parity. Reference geometry is an original interpretation, not the author's production project/stems or literal lesson choreography. See [audio/schema limits](docs/acceptance/avee-1252-audio-profile.md), [reference math fact check](docs/acceptance/reference-video-math.md) and [motion observations](docs/acceptance/2026-10-23-mobile-and-motion.md).

Emulator/synthetic results do not establish physical ARM64 audio focus, mic latency, dense-song transcription or full modern Avee parity. Overlapping harmonics, octave doublings, percussion and closely spaced low notes remain ambiguous. Keep these limits explicit; benchmark before claiming more accurate or faster detection.

**Video-to-graph tracing/Bezier rendering stays LAST and is excluded from Preview 3.** Deliver and refine the improved player first. Earlier verified Preview 2 remains available at its own release tag/source 48c229e; its evidence is historical, not proof of newer code.
