# Preview 4 validation and review

Continuation on 23 October 2026 (Asia/Manila), from `1879d577d5cbd626fd1ddf993cd975fcc9b0eac7`.

## Observed failures before fixes

- [Integrated validation 39920860762](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39920860762): host tests, lint and both APK assemblies passed (job120305471066). API26 passed one fresh-permission case and 25 general cases (job120307637716).
- API36 job120307637851 passed the permission flow but failed `VideoBackgroundNativeTest.closingOneEglTargetKeepsTheOtherTargetUsable`: expected green255, actual150. Immediately preceding graphics logs report `error null ctx` for clear/read operations. This is an observed native regression, not a skipped check.
- [Publisher 39920860729](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39920860729) rejected that exact source because validation failed; no Preview4 release was published.

## Review and scope

The fresh review found that full decoding appends samples without source timestamps, unlike the quick-preview path. Delayed audio and timestamp gaps can shift detailed notes/export audio early, and a shorter audio track can truncate the analyzed/exportable video duration. Native delayed/gapped/short-audio regressions were added before the fix. Both PCM and analysis cache compatibility were addressed.

The existing mixed-media design and plan remain the scope. Fix shared EGL display ownership, retain source-time PCM including silence, then run clean host/lint/APK and API26/API36 checks. Keep the existing Preview2/3 signing identity and publish Preview4 only from successful exact-source validation. Physical-phone performance, full Avee interoperability, instrument separation and video tracing remain unverified or deferred.

## Completion status

The implementation and host/lint/APK checks are complete at `b06753140bcc8b5f476edfebd4e4c1b5ea9866f1`. Native API 26/API 36 checks, artifact inspection and publication remain pending; no device or release success is claimed yet.

## Diagnostic checkpoints

- `5bed678f93484ee6dc4d389d1883e533876095aa`, run39933760214: compilation reached `:app:testDebugUnitTest` at09:46:44UTC but produced no result before cancellation at10:04:50UTC. This was a stalled host run, not an observed test assertion failure. Its tiny report artifact contains only an empty binary output file, so it cannot identify a stuck test.
- `d85594426a4f064af350832dd4b8bb110074fc40`, run39936432159: explicitly non-publishable diagnostic checkpoint. Host/lint were omitted only in this RED checkpoint; publication was disabled. Assembly job120357305820 passed. API36 job120358914562 observed all three timeline assertions fail (1.2s video truncated to371519us, shifted leading audio, lost second-segment position), the stale analysis cache assertion, and both EGL assertions. Its following playback case aborted in RenderThread after the broken EGL cleanup. API26 job120358914576 observed the stale cache and inactive-close failures; its three timing cases stopped at fixture verification because the platform extractor reported firstPTS0 rather than300000. Those setup failures are not claimed as timing REDs.
- Independent diagnostic branch `blazing-visualizer-host-diagnostics` at `ea41404ef463fafee9fa1fd61295784b6157efc5`, run39936968259, also stalled at the first Robolectric class. Its timeout dumped only the Gradle wrapper, so it did not establish the test-worker cause. Follow-up461f12e/run39959477936 adds worker jcmd dumps and Robolectric SDK transfer logging. No diagnostic branch can publish a preview.
- The release candidate must restore all host/lint/APK checks and the publisher. The complete workflow is split into named bounded stages so a future host stall cannot remain opaque or run indefinitely.

Host diagnostic2 run39959477936 passed unchanged application source: 118 tests in 20 XML suites, zero failures/errors, about 14 seconds of execution. SDK28/33 runtime downloads completed quickly; the watcher captured no worker stack because the tests finished between ticks. The earlier host stall remains unexplained. It is not claimed as an application defect or a fixed infrastructure cause.

## Fix candidate

Source-time PCM is written in cancellable 2,048-frame silence blocks around delayed/gapped audio, with overlapping frames trimmed and longer video tails retained. The same samples feed the 22,050 Hz analysis resampler. PCM timelineVersion 1 and analysis-key v3 reject earlier concatenated caches while retaining original content hashes/project identities. Native assertions now inspect both PCM streams.

The existing Media3 1.8 `MediaExtractorCompat` is used for decoding and independent fixture-timestamp verification, preserving the same container edit-list interpretation as playback. This adds no dependency or copied parser. [Primary API/source](https://raw.githubusercontent.com/androidx/media/1.8.0/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/MediaExtractorCompat.java). Native cross-version results are recorded below.

The EGL fix owns one shared display reference across live targets, unbinds only the target being closed, avoids thread-wide release, and cleans partial initialization/idempotent close. A fresh narrow review found no actionable issue; native GREEN remains required.

The API26 fixture problem was traced separately to the Android8 writer: it stores the first-track offset in the first sample duration rather than writing a proper edit list. The runtime generator is replaced by a 6,224-byte original synthetic MP4, so both devices receive identical bytes. SHA256: `4008faec8bd308183297363e538852aa263daf36d2e291514592855cb6f1ba67`. Independent box parsing and FFmpeg packet timestamps confirm audio firstPTS300000us, gap439319–739319us, audio end925079us and video duration1200000us; both streams decode without errors. The first-timestamp assertion remains300000. This asset is test-only and contains generated green video/440Hz audio, not downloaded media.

Candidate `df3d01641b22259a722ee08967ef2b2e06c8383b`, run39961730951: host regression stage passed, but lint rejected the remaining platform `MediaExtractor.SEEK_TO_PREVIOUS_SYNC` constant at PcmDecoder.kt:58. The native jobs were skipped. The next checkpoint qualifies the equivalent `MediaExtractorCompat` constant rather than suppressing lint; no device GREEN is claimed for this failed candidate.

## Exact-source release validation

Candidate `b06753140bcc8b5f476edfebd4e4c1b5ea9866f1`, [full run 39962875776](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39962875776): build job `120445084228` passed the clean host regression stage, lint and both Android APK assemblies. The downloaded host artifact `12506460594` contains 118 tests in 20 XML suites, with zero failures, errors or skips. Its archive SHA-256 is `12f03fd2d4a6bf92feef3722914b80822ed5056aa3ef317821c00cc1f05c12ec`.

The independently downloaded CI APK artifact `12506236197` has valid ZIP contents and both `arm64-v8a` and `x86_64` libraries. APK size: 31,867,604 bytes. SHA-256: `aef597a3caeb0a4fc107d0a76c4cd98716645d60f01ea1b910c1d5698a067942`. These are CI bytes; public-release equivalence and signing verification remain pending.

API 36 job `120448117500` passed. Downloaded XML confirms 30 general tests, zero failures/errors/skips; its separate permission report confirms one passing fresh-permission test. The three PCM timing assertions, stale-analysis-cache rejection and both EGL lifecycle cases all pass. Archive SHA-256: `4006c29ea256185469352dd051e3693d1b1938f76e152adca6986c911ddc79db`.

The API 36 acceptance tar contains 17 members: seven PNGs, eight JSON reports, a four-second MP4 and its directory. Root inspected the actual source-video screenshot (green contained background with red foreground), spatial-chord/rhythm/radial frames and a decoded export frame. FFmpeg decoded the retained MP4 without errors. Native JSON confirms all six export dimensions and graph modes have one audio/video track, same-timestamp renderer replay, source/export best audio lag 0 us (correlation 0.9999356), and model maximum differences below 0.0001. Synthetic onset F1 is 0.9091 and the three-note flute fixture F1 is 1.0 at 50 ms tolerance; these are fixture results, not dense-song accuracy claims.

On the generated 440 Hz test, `quick-preview.json` records the first visible temporary note at 497 ms while neural analysis is deliberately gated. This demonstrates independence from full analysis on that emulator/fixture; it is not a physical-phone latency guarantee.

API 26 job `120448117470` reached the 25-minute job timeout. The independent permission case passed; partial instrumentation events contain 25 general status-0 results, including all three source-time PCM tests, quick preview and stale-analysis-cache rejection. No completed general XML or acceptance tar was produced. The remaining five cases are unverified on this checkpoint. Partial artifact `12507028421` is 72,732 bytes, SHA-256 `37a3791ccccfeccf7bf6cea7ef93f2f1f1569fd16afa2e0f1c72778805a64866`.

The active case is `VideoBackgroundNativeTest.readerUsesSourceTimeAndReturnsRotatedBoundedFrames`. Its log begins live `OMX.google.h264.encoder` fixture creation at 13:51:18 UTC and a first MP4 sample at 13:51:18.515. There is no encoder EOS/stop or retriever/decoder progress before cancellation at 14:09:49. SystemUI later restarts and the emulator logs slow HAL writes. This establishes an unfinished runtime fixture setup; it does not identify the exact blocking native call or prove a production frame-reader defect. No assertion failure was emitted.

[Publisher 39962875773](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39962875773) correctly rejected this incomplete run. The next correction replaces the live color-video generator with fixed original synthetic red/green MP4 inputs at rotation 0/90, preserving all existing reader/composition/seek/transition assertions. The production encoder remains exercised by the six-size export matrix and retained four-second export. Full exact-source validation is required again before publication.

Both replacement color fixtures are 3,384-byte original synthetic MP4s made with FFmpeg 7.1 color/concat filters and baseline H264, with rotation applied by stream copy. Independent box parsing and decoding of all 36 frames confirm one silent video track, Constrained Baseline profile 66/level 30, 320×180 at 30 fps, duration 1,200,000 us, first PTS 0, last PTS 1,166,666 us and red-to-green transition at 600,000 us. Rotation matrices are 0/90 degrees. SHA-256: `color-video.mp4` is `4f82fb70a78d3bbac0e15a55971b585a514fe471fd2dc9b405e05ec3bbd63e28`; `color-video-rotation90.mp4` is `86999f39e940b7ea6a9bcbde00ce8e0ada102b51cfc10596ddaa9fa1ec75f096`. These inputs are test-only and do not ship in the app APK.
