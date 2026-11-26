# PHX-HARDWARE UTC01 — PR #353 / #352 ancestry reconciliation

Observed: 2026-11-26 UTC01  
Role: PHX-HARDWARE  
Repository: BlazeDevStudio/BlazingSystems-Experiments  
Child PR: #353 (OPEN / DRAFT / UNMERGED)  
Parent PR: #352 (OPEN / DRAFT / UNMERGED)

## Exact refs and comparison

- Parent #352 branch `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`: `0e984e267b3a8fb10c314800d1a7f120806354b7`.
- Child #353 branch `phoenix/hw-board-conditional-isr-selector-20261125-utc17` before reconciliation: `dc9cf634248ecc23f51f1477bd1769d63d3fe5ea`.
- Child's captured base: `6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec`.
- Common merge base: `6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec`.
- Parent delta: 11 commits, 13 changed paths.
- Child delta: 17 commits, 7 changed paths.
- Overlapping paths were limited to the two PHX-HARDWARE workflows and `coin_pulse_capture_lab_structure_guard.py`.

## Reconciliation

Merge commit [`82e65038`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/82e6503890632249c54e9cd9a93180a5e7c52aa6) has parents, in order:

1. Prior child #353 head `dc9cf634248ecc23f51f1477bd1769d63d3fe5ea`.
2. Current parent #352 head `0e984e267b3a8fb10c314800d1a7f120806354b7`.

The merged tree preserves the parent's six-section C++ fixture modularization and the child's dedicated board-ISR selector module. Both focused workflow path filters now include the ISR selector file and the child branch. The merged structure guard checks both module boundaries and workflow triggers.

The first merged guard contained a literal-name typo (`selectorPath` was emitted as a Python variable). Relay run [#45738996559](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45738996559), job `139639076774`, reproduced the NameError. It was corrected in [`61ed2fc3`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/61ed2fc3e056a1b497dff57009f0e4c624095e32) by pinning the literal selector path. The branch update was fast-forward-only with the exact prior head supplied; no force-push, rebase, retarget or PR merge was used.

## Exact-head validation

- Current child head at handover creation: `61ed2fc3e056a1b497dff57009f0e4c624095e32`.
- Parent #352 head: `0e984e267b3a8fb10c314800d1a7f120806354b7`.
- Compare parent to child: 19 ahead / 0 behind; merge base is the current parent head.
- PR #353: OPEN / DRAFT / UNMERGED; mergeable was reported true after ancestry reconciliation.

Source/test commit: [`4f361e03`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4f361e032c30faa368105775e3646c570f9760a8). It changes the host coin-pulse lab runner, adds `coin_pulse_capture_lab_isr.py`, updates the structural guard and workflow paths. No production `.ino`, GPIO/relay behavior, CGI producer, controller API, finance, replay, signer, witness, migration or release workflow was changed.

- Full run [#45739237060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45739237060), validation job `139639974333`: FAILED at inherited `Missing poll signature check`. Static/security/config/template preflight steps completed before the failure.
- Quarantine run [#45739236986](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45739236986), job `139639881746`: IN PROGRESS at handover creation.
- Relay run [#45739236813](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45739236813), source job `139639881015`: IN PROGRESS; ESP32 boot-polarity job `139639881256`: PASS.
- Earlier failed merged-head runs are retained as integration-debug evidence; they are not final acceptance.

Focused exact-head status is pending until the two current jobs complete. No physical hardware evidence is produced by these host labs.

## Release classification

- Host fixture / ISR selector: SIMULATED; exact-head focused CI pending.
- Firmware targets: Full validation is blocked at the inherited poll-signature gate; remaining build jobs are separate from physical acceptance.
- Coin pulse, relay electrical recovery, LittleFS power-cut durability, 150 power cuts, 30-device / 24-hour soak: NOT TESTED.
- HARDWARE ACCEPTED: NO.
- PRODUCTION READY: NO.

Next: finish exact-head Quarantine/Relay runs on the current branch head, then re-read Master/CORE/QA contract decisions before any authenticated response or active v0.6 firmware changes.
