# Preview 4 validation and review

Continuation on 23 October 2026 (Asia/Manila), from `1879d577d5cbd626fd1ddf993cd975fcc9b0eac7`.

## Observed failures before fixes

- [Integrated validation 39920860762](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39920860762): host tests, lint and both APK assemblies passed (job120305471066). API26 passed one fresh-permission case and 25 general cases (job120307637716).
- API36 job120307637851 passed the permission flow but failed `VideoBackgroundNativeTest.closingOneEglTargetKeepsTheOtherTargetUsable`: expected green255, actual150. Immediately preceding graphics logs report `error null ctx` for clear/read operations. This is an observed native regression, not a skipped check.
- [Publisher 39920860729](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39920860729) rejected that exact source because validation failed; no Preview4 release was published.

## Review and scope

The fresh review found that full decoding appends samples without source timestamps, unlike the quick-preview path. Delayed audio and timestamp gaps can shift detailed notes/export audio early, and a shorter audio track can truncate the analyzed/exportable video duration. Native delayed/gapped/short-audio regressions are being added before the fix. Both PCM and analysis cache compatibility must be addressed.

The existing mixed-media design and plan remain the scope. Fix shared EGL display ownership, retain source-time PCM including silence, then run clean host/lint/APK and API26/API36 checks. Keep the existing Preview2/3 signing identity and publish Preview4 only from successful exact-source validation. Physical-phone performance, full Avee interoperability, instrument separation and video tracing remain unverified or deferred.

## Completion status

Pending: regression confirmation, implementation, full green validation, native artifact inspection, signing/hash verification, new release, and final handoff.

## Diagnostic checkpoints

- `5bed678f93484ee6dc4d389d1883e533876095aa`, run39933760214: compilation reached `:app:testDebugUnitTest` at09:46:44UTC but produced no result before cancellation at10:04:50UTC. This was a stalled host run, not an observed test assertion failure. Its tiny report artifact contains only an empty binary output file, so it cannot identify a stuck test.
- `d85594426a4f064af350832dd4b8bb110074fc40`, run39936432159: explicitly non-publishable diagnostic checkpoint. Host/lint were omitted only in this RED checkpoint; publication was disabled. Assembly job120357305820 passed. API36 job120358914562 observed all three timeline assertions fail (1.2s video truncated to371519us, shifted leading audio, lost second-segment position), the stale analysis cache assertion, and both EGL assertions. Its following playback case aborted in RenderThread after the broken EGL cleanup. API26 job120358914576 observed the stale cache and inactive-close failures; its three timing cases stopped at fixture verification because the platform extractor reported firstPTS0 rather than300000. Those setup failures are not claimed as timing REDs.
- Independent diagnostic branch `blazing-visualizer-host-diagnostics` at `ea41404ef463fafee9fa1fd61295784b6157efc5`, run39936968259, also stalled at the first Robolectric class. Its timeout dumped only the Gradle wrapper, so it did not establish the test-worker cause. Follow-up461f12e/run39959477936 adds worker jcmd dumps and Robolectric SDK transfer logging. No diagnostic branch can publish a preview.
- The release candidate must restore all host/lint/APK checks and the publisher. The complete workflow is split into named bounded stages so a future host stall cannot remain opaque or run indefinitely.

Host diagnostic2 run39959477936 passed unchanged application source: 118 tests in 20 XML suites, zero failures/errors, about 14 seconds of execution. SDK28/33 runtime downloads completed quickly; the watcher captured no worker stack because the tests finished between ticks. The earlier host stall remains unexplained. It is not claimed as an application defect or a fixed infrastructure cause.

## Fix candidate

Source-time PCM is written in cancellable2048-frame silence blocks around delayed/gapped audio, with overlapping frames trimmed and longer video tails retained. The same samples feed the22,050Hz analysis resampler. PCM timelineVersion1 and analysis-keyv3 reject earlier concatenated caches while retaining original content hashes/project identities. Native assertions now inspect both PCM streams.

The existing Media3 1.8 `MediaExtractorCompat` is used for decoding and independent fixture-timestamp verification, preserving the same container edit-list interpretation as playback. This adds no dependency or copied parser. Primary API/source: https://raw.githubusercontent.com/androidx/media/1.8.0/libraries/exoplayer/src/main/java/androidx/media3/exoplayer/MediaExtractorCompat.java . It is a proposed cross-version correction until the next native run confirms it.

The EGL fix owns one shared display reference across live targets, unbinds only the target being closed, avoids thread-wide release, and cleans partial initialization/idempotent close. A fresh narrow review found no actionable issue; native GREEN remains required.

The API26 fixture problem was traced separately to the Android8 writer: it stores the first-track offset in the first sample duration rather than writing a proper edit list. The runtime generator is replaced by a 6,224-byte original synthetic MP4, so both devices receive identical bytes. SHA256: `4008faec8bd308183297363e538852aa263daf36d2e291514592855cb6f1ba67`. Independent box parsing and FFmpeg packet timestamps confirm audio firstPTS300000us, gap439319–739319us, audio end925079us and video duration1200000us; both streams decode without errors. The first-timestamp assertion remains300000. This asset is test-only and contains generated green video/440Hz audio, not downloaded media.

Candidate `df3d01641b22259a722ee08967ef2b2e06c8383b`, run39961730951: host regression stage passed, but lint rejected the remaining platform `MediaExtractor.SEEK_TO_PREVIOUS_SYNC` constant atPcmDecoder.kt:58. The native jobs were skipped. The next checkpoint qualifies the equivalent `MediaExtractorCompat` constant rather than suppressing lint; no device GREEN is claimed for this failed candidate.
