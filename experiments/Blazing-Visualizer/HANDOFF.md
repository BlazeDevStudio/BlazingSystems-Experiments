# Blazing Visualizer handoff

Updated 24 October 2026 (Asia/Manila). Continue this existing Android app; do not restart or overwrite concurrent work.

## Current owner report: Preview 5 is still blank; Preview 6 repair in progress

The owner explicitly tested Preview 5 and reported that visualization is still blank. Treat the phone issue as unresolved despite successful emulator checks. Do not tell them the fix is confirmed on their phone. Three supplied MP3s are strictly local test inputs; never commit or upload them, excerpts or decoded PCM.

Preview 5 release source `96c5d3d0bec6f5fad20eb753fea9afdca5d3f8ee`, full validation `40053385999`, publisher `40053386012`. Host122/21suites and API26/API36 each31general+1permission passed. It removed repeated quick-decoder cancellation and completed conflated frame evaluation. Actual local production DSP emits notes for all three supplied files; the first15seconds produced319frames each, with313/180/133 active-note frames for beats/piano/vocals. This is not phone display evidence.

Current work: observe PCM consumed by the existing Media3 audio sink, bounded background DSP, source-time/partial-write/generation protection, exact cached resampler kernels, live fallback for an empty unedited detailed result, and one-tap Check visualizer reporting sound/notes/canvas without audio or filenames. Generated MP3 native tests require playback PCM and actual canvas pixels. See [active plan](docs/plans/2026-10-24-playback-pcm-notes.md). Preview6 needs full verification and a separately versioned release; owner-phone confirmation or a copied check report remains necessary.

The Preview4 sections below are historical evidence and do not prove the owner's reported problem is resolved.

## Preview 4: mixed media and faster initial note feedback

Status: **Published and independently verified**. Full validation [40009120574](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40009120574) and publisher [40009120823](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40009120823) passed on the exact release source.

The implementation adds multiple audio/video imports into one Library and Queue. Video plays behind the visualizer through the existing Media3 session, sharing its audio, pause, seek and Practice speed. Selecting audio-only media removes the video background. MP4 export composites source-time video behind the scene and keeps one audio track. Videos without audio are supported without invented detected notes.

A bounded independent decoder publishes temporary source-time FFT/YIN note estimates before whole-file hashing, decoding and Basic Pitch analysis finish. Requests follow the current source/time window, reject obsolete results and retain a bounded frame cache. Detailed analysis takes precedence when ready. Quick estimates never become saved corrections, verified analysis results, MIDI/CSV data or final MP4 note data; exports still require detailed preparation.

Review found two timeline defects in the first mixed-media implementation: concatenated audio moved delayed/gapped sound and notes early, and short audio truncated the exportable video duration. The candidate preserves timestamps in original PCM and analysis mono, inserts silence in bounded cancellable blocks, trims overlaps and pads longer video tails. PCM timeline version 1 and analysis-key version 3 reject earlier incompatible caches while preserving content hashes and project identity. The existing Media3 1.8 extractor supplies the same container timeline interpretation as playback.

The EGL fix gives live preview/export targets shared display ownership, closes only each target's own context/surface, preserves another current target and makes repeated close safe. Native assertions cover the observed target-survival and inactive-close failures.

The release also handles a seek before the decoder's first output format. It preserves Media3's normal position/sink reset, then releases the same decoder if that early reset kept it alive; the next render configures a fresh decoder with codec-specific data. Android documents that an early flush can lose this setup data. Later seeks retain normal flushing. The valid AVCC fixtures, requested seek positions, default codec-adapter policy and existing pixel/timing assertions are unchanged. The exact-source native regression passes on both API 26 and API 36.

## Preview 4 release verification

| Item | Final evidence |
|---|---|
| Exact published source | `72c94336eca8cdc4190224248b4f8082209aa516` |
| Version | versionCode 4 / versionName `1.0.0-preview.4` |
| Full validation | [40009120574](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40009120574), final conclusion `success` |
| Host XML | `118` tests / `20` suites; failures/errors/skips `0 / 0 / 0`; build job `120604607048` |
| Lint and APK assembly | `passed` (build job `120604607048`) |
| API 26 | job `120607479743`; `1` independent fresh-permission case(s), `30` general cases; `passed, zero failures/errors/skips` |
| API 36 | job `120607479619`; `1` independent fresh-permission case(s), `30` general cases; `passed, zero failures/errors/skips` |
| Inspected native evidence | `Both native XML/permission reports, quick-note/model/export/alignment JSON, source-video and motion PNGs, and retained MP4s inspected; see Preview 4 evidence` |
| Publisher | [40009120823](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40009120823), job `120604608420`, conclusion `success` |
| Direct APK | [Download Preview 4](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.4/Blazing-Visualizer-preview-4.apk) |
| Release | [Preview 4 release](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazing-visualizer-v1.0.0-preview.4) |
| Final-source CI APK bytes / SHA-256 | `31,867,604` / `9026659db4866793fc963297d69ac357c4eb26069e74432d63a4874f289e860f` |
| Public-download check | `Root downloaded the public APK and SHA256SUMS, verified ZIP integrity, size/hash and exact CI byte equality` |

Separately versioned release: `blazing-visualizer-v1.0.0-preview.4` / `Blazing-Visualizer-preview-4.apk`. Publisher verified package/version, APK Signature Scheme v2, retained signer and both ABIs. Root independently checked published SHA256SUMS, ZIP integrity and equality to CI bytes.

Retained public debug-only certificate SHA-256: `64f9fbd13d72bb5ef88bccdc4602a487fea21fb73a13298b93a0f2b1f6c2109c`. Preview 4 can update Preview 2/3 in place. Preview 1 used a different key: export wanted presets before its one-time uninstall/reinstall. Never use this public preview identity for production.

ChatGPT file URLs fail on the owner's phone. Deliver direct GitHub Releases APK URLs. Keep all older release assets/tags intact. This remains a preview, with production signing/store publication and physical-phone validation unfinished.

## Verified Preview 3 historical baseline

- [Direct Preview 3 APK](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.3/Blazing-Visualizer-preview-3.apk) / [release](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazing-visualizer-v1.0.0-preview.3).
- Exact source `b9db4c115b5fc42905b7ede9e844a67c2f76acf2`; versionCode 3 / `1.0.0-preview.3`.
- [Full validation 39897614925](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39897614925): clean JDK 17 / SDK 36 host/lint/APK checks; 108 host tests, zero failures/errors/skips; API 26/36 each passed 19 general native/UI cases plus an independent fresh-permission flow. Jobs: build `120231570299`, API 26 `120232736456`, API 36 `120232736501`.
- Native JSON/PNG/MP4 evidence was inspected, including spatial-chord, rhythm and radial frames, graph exports and source/audio alignment. [Publisher 39897614942](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39897614942), job `120231570274`, checked package/version, signer, both ABIs and downloaded identical release bytes.
- APK 31,834,700 bytes; SHA-256 `2fa101ecf699a03198ce37d9125d8c3a263ed31c533df0f717738ff614d444da`. The root session independently verified its direct URL, SHA256SUMS, ZIP integrity and equality to the CI APK.

Preview 2 remains available at its own tag/source `48c229e`. Historical results establish those versions only.

## Repository, authorization and priorities

Repository: `BlazingSystems/BlazingSystems-Experiments`; project: `experiments/Blazing-Visualizer`; branch: `blazing-visualizer`; draft [PR 133](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/133). Main remains untouched. `blazing-visualizer-notes-motion` preserves an earlier iteration; the separate host-diagnostics branch cannot publish previews.

The owner wants modern Avee familiarity and useful preset interoperability, phone controls, continuous playback, playable note following and MP4 export. Preserve the native presets they like. Latest priorities are mixed media and initial note responsiveness, then genuine preset interoperability and production hardening. **Video-to-graph tracing/Bezier conversion remains last.** It is separate from the source-video backgrounds now requested.

Routine design, implementation, branch updates, checks and preview publication are approved. Do not repeatedly ask to continue or launch paid Codex/cloud coding-agent tasks. Reconcile remote heads and use expected-SHA leases for ref updates. Keep source and evidence in reviewable commits; do not rely on scratch files surviving a reload. Portable continuation: [CONTINUE_WITH_CHATGPT.md](CONTINUE_WITH_CHATGPT.md).

## Existing behavior to preserve

- Music permissions/MediaStore discovery, manual import, separate drag-reorder/sort/play-next Queue and playlists; persisted repeat/shuffle; real next-track and last-to-first playback.
- Reachable phone actions, Songs/Playlists navigation, thumbnail preset grid and fullscreen. A requested source has priority over stale previous-media updates.
- Per-track Practice speed, written transposition, spelling/register, A/B loops, corrections and MIDI/CSV export. Background Basic Pitch preparation caches results, prioritizes selection and serializes inference; PCM leases and cold-start persistence remain guarded.
- Per-layer Lo/Lo2/Mid/Mid2/Hi/Hi2/custom routing, independent piano/global intensity and colors; only active pitches light keys. Long-press move/resize, preview-following/separate export layouts, explicit aspect choices and fitted note/keyboard reflow; preserve custom separate layouts.
- Editable note-wheel idle text appears only with no notes. Unknown chords display every simultaneous note class; exact-set templates avoid guessing missing tones.
- Main-canvas microphone input: up to six conservative simultaneous spectral pitches and precise monophonic YIN when appropriate. Capture time animates without playback; playback may continue; selecting another track exits monitoring; background/disable/exit releases capture. Microphone audio is not saved or uploaded.
- Existing native/graph presets and five optional motion presets: luminous trails, projected chord axes, shared-cursor wave reveal/reset, fixed rhythm gates/sweeping hand and settled radial contours. Motion controls remain editable; equations default off.
- Partial Avee JSON/JSON-in-ZIP `.viz` import retains metadata and referenced composition passes. Independent segment colors/signed heights, common image tint/aspect/circle/blend and bounded effects, explicit replacement images, configured Spectrum2 response in preview/export and native-pack round trips remain supported.

Key files: `audio/PcmDecoder.kt`, `audio/AudioRepository.kt`, `audio/QuickNotePreview.kt`, `analysis/AnalysisRepository.kt`, `playback/LibraryRepository.kt`, `playback/PlayerController.kt`, `playback/StartupSafeVideoRenderer.kt`, `playback/StartupSafeRenderersFactory.kt`, `render/SceneView.kt`, `render/GlTarget.kt`, `render/VideoFrameSource.kt`, `render/ScenePainter.kt`, `export/VideoExporter.kt`, `ui/StudioModel.kt`, `ui/AveeShell.kt`; preserve existing tuning, layout, pack and motion code.

## Validation history and limits

[Preview 4 evidence](docs/acceptance/preview-4-evidence.md) records real failures and corrections. Initial source `1879d577` passed 118 host tests, lint/build and API 26 in run `39920860762`, but API 36 exposed EGL target destruction; its publisher correctly blocked release. Checkpoint `d855944`, native diagnostic `39936432159`, reproduced API 36 delayed/gapped/short-audio, stale-cache and EGL assertions. API 26's generated timing input instead failed fixture verification because the old writer altered its first timestamp; do not relabel setup failures as timing REDs.

Both devices now receive one original synthetic 6,224-byte MP4: SHA-256 `4008faec8bd308183297363e538852aa263daf36d2e291514592855cb6f1ba67`. Independent container/packet checks establish audio first PTS 300,000 us, a gap from 439,319 to 739,319 us, audio end 925,079 us and video duration 1,200,000 us. The fixture is test-only generated green video/440 Hz sound.

Canceled host run `39933760214` left only an empty binary output file. Host diagnostic `39936968259` dumped the wrapper, not the worker. Follow-up diagnostic `39959477936` passed unchanged source: 118 tests/20 suites, zero failures/errors, about 14 seconds. SDK downloads were quick and no worker stack was captured between timer ticks. The earlier stall remains unexplained; do not claim a diagnosed or fixed cause. Named bounded host/lint/APK stages now keep future failures visible. Candidate `df3d0164` passed host checks but failed lint on a platform seek constant; `b0675314` qualifies the existing compatible-extractor constant. Neither earlier run proves final device GREEN.

Candidate `b06753140bcc8b5f476edfebd4e4c1b5ea9866f1`, [run 39962875776](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39962875776), passed 118 host tests/20 suites with zero failures/errors/skips, lint and both APKs in build job `120445084228`. Its CI APK was 31,867,604 bytes, SHA-256 `aef597a3caeb0a4fc107d0a76c4cd98716645d60f01ea1b910c1d5698a067942`; those bytes are historical; the final release size and hash are recorded above. API 36 job `120448117500` passed 30 general cases and one independent permission case. Its inspected JSON/PNG/MP4 evidence includes all six export dimensions, model/renderer parity, source-video composition and a 497 ms first visible note on the gated synthetic 440 Hz emulator test. That timing is not a physical-phone guarantee.

API 26 job `120448117470` timed out after 25 minutes. Its permission case and 25 general status-0 results, including the PCM/cache/quick-preview cases, are recorded; no complete general XML or acceptance tar exists. The active case was `VideoBackgroundNativeTest.readerUsesSourceTimeAndReturnsRotatedBoundedFrames`, still generating its input with `OMX.google.h264.encoder`. The last output was a first MP4 sample; logs did not identify the exact blocked native call or establish a production reader failure. [Publisher 39962875773](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39962875773) correctly rejected the incomplete validation.

Fixture-only checkpoint `5073c2721c6bc529c6cec4a9edde0ab1cfd3a0b2` changed only test inputs/loader and evidence. Fixed original silent H.264 inputs preserve 320×180, 36 frames at 30 fps, 1.2-second duration, red before/green after 600 ms and 0/90-degree rotation. Each is 3,384 bytes: `color-video.mp4` SHA-256 `4f82fb70a78d3bbac0e15a55971b585a514fe471fd2dc9b405e05ec3bbd63e28`; rotated input `86999f39e940b7ea6a9bcbde00ce8e0ada102b51cfc10596ddaa9fa1ec75f096`. All reader, composition, seek and transition assertions remain; production encoding still runs through the six-size/four-second export matrix and background-video export.

In [5073 validation 39968524056](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39968524056), API 26 completed all tests. API 36 passed 29/30 general tests and failed only `pausedVideoSeeksWithTheSessionAndAudioRestoresAnOpaqueVisualizer` at line 82: the first red frame after pause/seek to 100 ms, before the later 800 ms seek. The decoder was configured at 14:33:53.315 UTC, sought at 53.359 and flushed at 53.380; emulator FFmpeg then reported missing SPS/PPS/no frame. The unchanged valid AVCC file decodes independently and stores SPS/PPS in its configuration. This observed early-startup/seek failure motivates the current renderer correction rather than easier fixture data or a longer wait. [Publisher 39968524038](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39968524038) blocked release. Final `72c94336` validation is recorded above; the earlier 5073 results remain historical.

See [Preview 3 evidence](docs/acceptance/preview-3-evidence.md) for its older independent review and evidence-handling corrections. Those results are historical, not proof of newer source.

Avee compatibility remains **partial**: safe measure expressions, dynamic text tokens, custom shaders/masks/fonts, exact temporal feedback blur/beat gain, older Spectrum/binary variants and `.viz` re-export are unfinished. Unknown fields surviving a pack does not mean they render. JSON boolean mirror handling remains deferred; maximum-size frequency banks can make cold seeks expensive. Use a genuine permissioned exported `.viz` fixture and physical phone to measure interoperability and responsiveness.

The inspected Avee 1.2.252 upload is unofficially modified. Functional/schema observations and original implementations are permitted; do not redistribute its APK, code or artwork. Spectrum2's strongest-bar index is not named-note detection. Static inspection is not official runtime parity. Reference geometry is an original interpretation, not the author's production project/stems or literal choreography. See [audio/schema limits](docs/acceptance/avee-1252-audio-profile.md), [math fact check](docs/acceptance/reference-video-math.md) and [motion observations](docs/acceptance/2026-10-23-mobile-and-motion.md).

Emulator/synthetic checks do not establish physical ARM64 audio focus, microphone latency, dense-song transcription, full modern Avee parity. Harmonics, octave doublings, percussion and closely spaced low notes remain ambiguous. Measure before claiming more accurate or faster detection. Source-video frame decoding is bounded and unsupported formats/sizes may fail visibly.

Real instrument separation is research only. [The offline pilot assessment](docs/acceptance/2026-10-23-stem-separation-research.md) proposes measured vocals/accompaniment experiments and comparison engines; no separation model/runtime or audio upload was added. Frequency bands are not isolated instruments. Continue preset/phone validation and production hardening before deferred graph tracing.
