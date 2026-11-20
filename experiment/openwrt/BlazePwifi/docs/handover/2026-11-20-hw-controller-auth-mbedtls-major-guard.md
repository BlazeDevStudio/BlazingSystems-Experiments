# PHX-HARDWARE narrow handover — ControllerAuthV1Lab Mbed TLS compatibility fence

- Date: 2026-11-20 UTC04
- Role: PHX-HARDWARE
- Repository: `BlazeDevStudio/BlazingSystems-Experiments`
- Branch: `phoenix/hardware-core252-deny-consumer-20261030`
- PR: [#254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/254), OPEN / DRAFT / UNMERGED
- Base: PR #239 at `d83b715b116185107737fef721c2eece8feebf39`
- Source commit: `66aa3f13f4cc0c5a89fafa76328a900969ff3563`

## One bounded engineering task

The ESP32-only, non-actuating `ControllerAuthV1Lab.h` used legacy `mbedtls_sha256_*` calls but did not state or enforce its Mbed TLS major-version boundary. The existing focused workflow installs Ubuntu `libmbedtls-dev 2.28.8`; the Master compatibility audit records the ESP32 Arduino core 4.0.0 path as Mbed TLS 4. The helper is not included by the application sketch.

Changes in the source commit:

1. `hex64` now scans at most 65 bytes (64 lowercase hex characters plus NUL), instead of an unbounded `strlen` scan.
2. `mbedtls/version.h` is checked before legacy headers. Unknown majors and Mbed TLS 4+ produce an explicit compile-time error requiring a separately reviewed PSA Crypto adapter.
3. The maintainer guide distinguishes host mbedTLS 2.28.8 compilation from ESP32 target compatibility and documents that this lab helper must not be integrated into the Mbed TLS 4 target.

No application intake, GPIO, relay, coin admission, response format, CORE contract, key material, financial schema, QA-owned test or Release-owned workflow changed.

## Evidence

- Focused GitHub Actions [#44672761914](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44672761914), job `136077345950`: SUCCESS. Actual header compiled with Ubuntu `libmbedtls-dev 2.28.8`; five synthetic deny cases passed.
- Local ASan failure injection: fake Mbed TLS 3 include set compiled; valid, short, invalid-hex and 65-byte unterminated digest cases passed 4/4.
- Local unsupported-target failure injection: synthetic Mbed TLS 4 version header caused the intended explicit `#error` before legacy SHA headers were included.
- Full workflow [#44672762223](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44672762223), validation job `136077426038`: FAILED at the expected handover freshness gate. Log states source/workflow changes were newer than `PROJECT_HANDOVER.md`, last checkpoint `4054fbccd9b2a4ad0e5fe7cfca5a27aa629eed84`. This docs-only successor is intended to satisfy the gate; a new exact-head Full result is still required.

## Limits and next actions

- The Mbed TLS 4 path is explicitly rejected; no PSA Crypto adapter is implemented.
- The helper remains lab-only and is not wired into firmware intake.
- PHX-QA should add an independent regression for a 65-byte unterminated digest and verify both supported majors.
- PHX-RELEASE should add an exact ESP32 core 4.0.0 negative compile check only after coordinating ownership; this Hardware change does not edit release workflows.
- PHX-CORE / PHX-MASTER still own the canonical authenticated response, protected witness and coin receipt contracts.

**Classification:** focused CI VERIFIED for the host Mbed TLS 2.28.8 build; local failure injection SIMULATED; target Mbed TLS 4 intentionally NOT TESTED beyond compile-time guard; HARDWARE ACCEPTED: NO; PRODUCTION READY: NO-GO. No merge, flash, deployment, live money or release action.
