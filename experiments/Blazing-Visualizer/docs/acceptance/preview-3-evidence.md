# Preview 3 execution and review evidence

Updated 23 October 2026 (Asia/Manila). The owner approved continued development, feature-branch updates and preview publication. Main and the existing Preview 2 release remain intact; tracing stays deferred.


## Published result

Preview 3 is verified and published from `b9db4c115b5fc42905b7ede9e844a67c2f76acf2`.

- Full Actions 39897614925: build120231570299, API26 120232736456 and API36 120232736501 all succeeded. Final host XML confirms 108 tests, zero failures/errors/skips. Each Android version passed 19 general tests and its separate fresh-permission flow. Both corrected playback cases passed.
- Both device archives contain 14 genuine native evidence files. Spatial-chord, rhythm and radial PNGs and the actual native export were inspected; keys highlight individual active pitches. All six export sizes and six math-mode encodes passed metadata/duration checks. Synthetic source/AAC correlation was 0.9999358 on API26 and0.9999356 on API36 with best lag 0us; these fixture measurements are not arbitrary-song accuracy claims. Optimized-layout placement and custom-layout preservation have separate host/UI coverage; the raw native sample renderer does not itself resolve UI export layout choices.
- Publisher 39897614942 / job 120231570274 succeeded. Package/version, retained certificate, v2 signature, archive structure and ABIs were verified; the released file was downloaded and compared byte for byte. Root independently downloaded the public link and SHA256SUMS and matched CI bytes.
- Direct APK: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.3/Blazing-Visualizer-preview-3.apk
- Size 31,834,700 bytes; SHA256 `2fa101ecf699a03198ce37d9125d8c3a263ed31c533df0f717738ff614d444da`. Same public debug-only signer as Preview 2. Product APK bytes at b9db4c1 are identical to edcd8ad; subsequent changes were tests/CI/docs.

The sections below preserve the actual intermediate failures and review decisions, rather than treating an earlier passing baseline as proof of the release.

## Candidate and verification

- Integration `e54f0db378d65d168e192f5439f0aec0294b727d` reconciled published Preview 2 plus checkpoint branch `blazing-visualizer-notes-motion`.
- Actions `39894731415`, build job `120222407687`: clean JDK17/SDK36 host tests, lint and both APK assemblies succeeded. Downloaded host XML reports contain 104 tests, zero failures/errors/skips. API26/API36 jobs were cancelled when the review regressions were pushed; this is not a full passing matrix.
- Regression source `216037b3b2d0c3733ffb2f969902abfc800d76fe`, Actions `39895368547`: image replacement and live configured-window/response tests. The host run compiled and executed 107 tests: exactly the three new behavioral regressions failed (image override, long live window, live attack/release); all other tests passed. Both device jobs were skipped by the failed host gate. This confirms the reported defects before fixes.
- Fix source `edcd8ad63f1d88511546664b367046c967f41fd9`, Actions `39895982129`, build `120226429608`: clean host/lint/debug and test APK assembly succeeded. Downloaded XML reports contain108 tests, zero failures/errors/skips. The three previously failing behavioral tests now pass, completing RED-to-GREEN verification. Same-instance motion seeking and recorded bank settings/seek-order tests pass as well. At that intermediate checkpoint the device matrix was still pending; see the final published result above. Use HANDOFF.md for the final release checkpoint.

## Fresh read-only review

An independent reviewer compared `48c229e` through `e54f0db` against the mobile/motion spec and plan. No files were edited or tests run by the reviewer. Two actionable findings entered the fix pass:

1. Explicit editor image replacements lost to retained Avee internal/composition sources. Regression: replace either source with a green PNG and inspect the resulting pixels. Preserve original raw metadata while giving the explicit asset priority.
2. Live Spectrum2 ignored response smoothing and permanently zero-padded windows above 4096 samples. Regressions: retain a full 300ms capture history and distinguish fast/slow attack and release using capture timestamps.

The reviewer found no further concrete issue in composition-cycle guards, whole-composite fitting, same-instance drawing state, analytical source-time motion or normal narrow-phone control access. That is review evidence, not proof of physical-device parity.

Deferred minor: JSON boolean `mirrorSamples: true` is not interpreted as the numeric mirror flag. No actual exported fixture established prevalence. Maximum-size correlation banks make cold seeks expensive; phone latency remains unmeasured. Real exported Avee fixtures and physical ARM64/microphone testing remain necessary, along with unimplemented shader/measure/temporal-effect parity.

Ruling: use original bounded approximations for modern Avee effects and report partial compatibility. The inspected upload is an unofficial modified APK; no source code, APK or artwork is redistributed. Cost if wrong: some imported presets will still differ, explicitly reported rather than marketed as full compatibility.

Ruling: preserve the owner's main-canvas mic workflow and earlier accepted playback behavior. Monitoring can continue while playback runs, and capture time drives animation even with no playing track. Selecting another playback track exits monitoring. Cost if wrong: speaker playback may be heard by the mic; the toggle lets the owner stop monitoring.

## Android 16 follow-up

At edcd8ad, API26 passed all19 general tests (plus the independent permission flow). API36 passed 17/19; source-speed and restored-loop assertions failed. The raw-controller speed test ran inside an Activity with a second StudioModel controller restoring per-track defaults. It is moved to the existing controller-only suite. The cold-loop test waited for duration metadata, which arrives before the deferred ready-state seek; logcat shows the 300ms seek arriving around assertion/teardown. It now waits for the actual requested speed and loop position before asserting. Neither assertion is removed or widened.

Artifact inspection also found that the successful API26 tar contained only `run-as: unknown package`: Gradle had uninstalled the app before extraction. The second instrumentation invocation now uses `android.injected.androidTest.leaveApksInstalledAfterRun=true`, as used by AndroidX upstream, and verifies required JSON/PNG files in a real tar before success. Earlier job success did not prove native screenshots were retained. Primary reference: https://android.googlesource.com/platform/frameworks/support/+/9e4716bac2232e13eb633984353a169d177a9b99/gradle.properties .

The final b9db4c1 run revalidated both versions and recovered real native visual evidence before publication. The app product code remains edcd8ad; this follow-up changes test isolation, condition waiting, CI evidence collection and documentation.

Final review fixes: explicit image override, long live window and capture-time smoothing regressions were observed RED at 216037b and GREEN at edcd8ad, with the complete 108-test suite green again at b9db4c1. Fresh read-only whole-branch review was performed before those focused fixes; no second review was substituted for their regression evidence.
