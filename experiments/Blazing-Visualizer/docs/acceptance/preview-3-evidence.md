# Preview 3 execution and review evidence

Updated 23 October 2026 (Asia/Manila). The owner approved continued development, feature-branch updates and preview publication. Main and the existing Preview 2 release remain intact; tracing stays deferred.

## Candidate and verification

- Integration `e54f0db378d65d168e192f5439f0aec0294b727d` reconciled published Preview 2 plus checkpoint branch `blazing-visualizer-notes-motion`.
- Actions `39894731415`, build job `120222407687`: clean JDK17/SDK36 host tests, lint and both APK assemblies succeeded. Downloaded host XML reports contain 104 tests, zero failures/errors/skips. API26/API36 jobs were cancelled when the review regressions were pushed; this is not a full passing matrix.
- Regression source `216037b3b2d0c3733ffb2f969902abfc800d76fe`, Actions `39895368547`: image replacement and live configured-window/response tests. The host run compiled and executed 107 tests: exactly the three new behavioral regressions failed (image override, long live window, live attack/release); all other tests passed. Both device jobs were skipped by the failed host gate. This confirms the reported defects before fixes.
- The fix candidate gives explicit assets precedence, retains a 6615-sample live history, and applies capture-time response smoothing. Same-instance motion seeking and recorded bank settings/seek-order tests also strengthen verification. Green verification and the full device matrix are pending. Preview 3 is not yet verified or published. Use HANDOFF.md for the final release checkpoint.

## Fresh read-only review

An independent reviewer compared `48c229e` through `e54f0db` against the mobile/motion spec and plan. No files were edited or tests run by the reviewer. Two actionable findings entered the fix pass:

1. Explicit editor image replacements lost to retained Avee internal/composition sources. Regression: replace either source with a green PNG and inspect the resulting pixels. Preserve original raw metadata while giving the explicit asset priority.
2. Live Spectrum2 ignored response smoothing and permanently zero-padded windows above4096 samples. Regressions: retain a full300ms capture history and distinguish fast/slow attack and release using capture timestamps.

The reviewer found no further concrete issue in composition-cycle guards, whole-composite fitting, same-instance drawing state, analytical source-time motion or normal narrow-phone control access. That is review evidence, not proof of physical-device parity.

Deferred minor: JSON boolean `mirrorSamples: true` is not interpreted as the numeric mirror flag. No actual exported fixture established prevalence. Maximum-size correlation banks make cold seeks expensive; phone latency remains unmeasured. Real exported Avee fixtures and physical ARM64/microphone testing remain necessary, along with unimplemented shader/measure/temporal-effect parity.

Ruling: use original bounded approximations for modern Avee effects and report partial compatibility. The inspected upload is an unofficial modified APK; no source code, APK or artwork is redistributed. Cost if wrong: some imported presets will still differ, explicitly reported rather than marketed as full compatibility.

Ruling: preserve the owner's main-canvas mic workflow and earlier accepted playback behavior. Monitoring can continue while playback runs, and capture time drives animation even with no playing track. Selecting another playback track exits monitoring. Cost if wrong: speaker playback may be heard by the mic; the toggle lets the owner stop monitoring.
