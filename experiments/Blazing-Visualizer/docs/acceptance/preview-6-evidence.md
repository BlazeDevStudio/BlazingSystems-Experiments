# Preview 6: playback PCM and phone diagnostics

The owner explicitly reported that Preview 5 is still blank on their phone. Successful emulator results for Preview 4/5 did not resolve that report. Preview 6 changes live input to PCM consumed by the existing Media3 audio sink and adds a local diagnostic report. Owner-phone confirmation remains pending.

## Source and scope

- Published source: `a718e2a45e798038885a9c52f38a89b5a2f623e5`.
- Version: versionCode 6 / `1.0.0-preview.6`.
- Validation: [40085323906](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40085323906).
- Publisher: [40085323837](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40085323837).
- Main and all previous release tags/assets remain intact.

The sink observer copies only bytes accepted by the delegate, including repeated partial interleaved writes, and subtracts Media3's stream offset to recover source time. Conversion, resampling and note estimation run on a bounded background worker. Source changes, seeks, resets, dropped packets and profile changes invalidate old features. The existing file decoder remains a fallback when current playback features are unavailable.

An empty, unedited detailed result no longer suppresses live estimates. Explicit note edits remain authoritative, including deliberate deletion of every note. Saved analysis, corrections and final export note data remain independent of temporary live estimates.

The resampler caches exact integer-phase coefficients of the existing 64-tap filter. Reference tests compare the old uncached calculation, irregular chunk/tail behavior, unusual phase churn and alias rejection. The audio sink and PCM hub have regression tests for consumed-byte/timestamp handling and stale generation rejection.

## Verification results

Exact-source validation and publication both succeeded. Build job `120846964454` passed host tests, lint and both APK assemblies. Downloaded host artifact `12556248687` has 129 tests in 24 XML suites, with zero failures/errors/skips; ZIP SHA-256 `2f1a566a1285477722f16f79892bd652552f914e82932b4e61f403961b0270fe` matches artifact metadata.

| Native evidence | API26 | API36 |
|---|---:|---:|
| Successful job | 120848212855 | 120848212849 |
| General tests | 31 | 31 |
| Independent fresh-permission tests | 1 | 1 |
| Failures / errors / skips | 0 / 0 / 0 | 0 / 0 / 0 |
| Playback PCM chunks / feature frames | 326 / 180 | 328 / 181 |
| First / second chord coverage | 1.0 / 1.0 | 1.0 / 1.0 |
| Colored canvas pixels | 121 | 118 |
| Empty detailed result kept live notes | true | true |
| Seek version after backward seek | 4 | 4 |

Actual XML/permission reports, MP3 JSON and canvas PNGs were downloaded and inspected from artifacts `12557610206` (API26) and `12557361417` (API36). Both images visibly show A/C#/E and highlighted piano keys. The full MP3 tests passed, including the subsequent dialog, clipboard-copy and URI/filename-redaction assertions. These are synthetic emulator results; the owner-phone outcome is still unconfirmed.

## Published APK

[Direct Preview 6 APK](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.6/Blazing-Visualizer-preview-6.apk). Release `422665053` targets the exact source above. Publisher job `120846964336` verified package/version, both ABIs and APK Signature Scheme v2 with the retained certificate SHA-256 `64f9fbd13d72bb5ef88bccdc4602a487fea21fb73a13298b93a0f2b1f6c2109c`, then downloaded byte-identical public assets.

The independent local public download also exactly matched the CI APK: 31,900,372 bytes, SHA-256 `14e67d1225e76e3bcfefaa73ceaf3ae0d9d1dc6245b7624dd8f7e06d0577f532`. ZIP integrity passed all 222 members; manifest, version 6, arm64-v8a/x86_64, bundled model and signer were checked. Only complete verified files were copied into local outputs; older outputs/releases remain intact.

The generated native MP3 is an original 16-second stereo fixture with a silent intro and a chord change. The test opens the visualizer before starting playback, gates detailed analysis, checks note coverage, requires playback PCM reception, exercises an empty detailed cache and a backward seek, checks colored pixels from the actual canvas and copies the diagnostic report without exposing the source URI or filename.

An earlier candidate, `59cf2211706f676b9d5cf7c8917458b8ca406fef`, passed host tests but failed lint because the new PCM constants required Media3 API opt-in. Scoped annotations were added in `f16b5486`; its full checks must pass before publication.

Both attempts of `f16b5486` run `40066386802` then hit the existing 12-minute host timeout. The last logged test boundary was AveeCompositionTest; no finalized XML report or worker thread dump established where or why the process was stuck. Both 212-byte incomplete host artifacts coexist, so there was no artifact-name conflict. Candidate `8e020213` changes only workflow diagnostics and the plan: per-test start/end lines and bounded Java thread/SDK-state snapshots before the same timeout. App behavior, tests and assertions are unchanged from `f16b5486`.

The diagnostic run `40068140984` passed 129 host tests in 24 suites with zero failures/errors/skips, then failed lint on a direct StateFlow value read inside the new check dialog. Its host results do not establish the cause of the earlier stalls. Candidate `a718e2a4` changes that single line to Compose state collection so audio reception updates reactively, without suppressing the lint check.

## Private music checks

The three supplied songs are strictly local test inputs. No songs, excerpts or decoded PCM are committed, uploaded to CI or bundled in the APK. The production DSP probe runs locally on 15-second PCM inputs and emits measurements only. Local DSP success does not establish Android playback, display latency or transcription accuracy on the owner's phone.

The downloaded exact-source probe artifact `12556238764` from run `40085323906` was verified against ZIP SHA-256 `dba61707e7855d4b5896a450f0898180eb7924bd7ea52d61ed6caf27314baa93`. Its production class archive SHA-256 is `3dbafd899a3df2a1ea3bb0bcd5091fe6e48ec459083ac09ff2a4b8ae8564513a`. It ran locally with verified Java 17 on the first 15 seconds of each 44.1kHz stereo input.

| Local test | Feature frames | Frames with notes | Resampling ms, baseline → Preview 6 | Total ms, baseline → Preview 6 |
|---|---:|---:|---:|---:|
| A: mixed beats | 319 | 313 | 2488 → 342 | 4899 → 5086 |
| B: piano | 319 | 180 | 2777 → 370 | 5948 → 3771 |
| C: vocals | 319 | 133 | 3484 → 406 | 6594 → 4480 |

Active-frame counts, maximum RMS and the measured pitch set near five seconds matched the adjacent old-code baseline. The baseline took 7.28–8.58 times as long to resample these clips; total time improved for B/C but was slightly worse for A. These are single fresh-JVM measurements including JIT and OS scheduling, not a phone performance or transcription-accuracy claim. Only anonymous measurements are recorded; private audio and PCM remain outside the repository.

## Phone follow-up

If Preview 6 remains blank while a track plays, open the playback menu, choose **Check visualizer**, wait for the local file check, then choose **Copy report** and paste it into the chat. The report contains build/device details and audio/note/canvas measurements; it includes no audio, filenames or file addresses. This evidence is needed to locate the remaining phone-specific failure without guessing from another emulator pass.
