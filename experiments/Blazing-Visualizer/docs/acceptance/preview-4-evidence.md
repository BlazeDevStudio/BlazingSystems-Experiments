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
