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


## Final docs-head validation — 2026-11-26 UTC01

The final handover/PR head at the time of this validation was `b737164310937e4782b7cc5f75ad825b9bcf42df` (parent #352 `0e984e267b3a8fb10c314800d1a7f120806354b7`, compare 19 ahead / 0 behind).

- Quarantine [#45739536022](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45739536022), job `139640847937`: **PASS**. Both ESP8266 and ESP32 report `COIN_PULSE_CAPTURE_PASS 18/18`; 17 fail-open mutations are rejected per board; modular fixture/ISR guard, JSON grammar boundary, EEPROM config-read recovery and boot-polarity checks pass.
- Relay [#45739536099](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45739536099), jobs `139640848810` / `139640849106`: **PASS / PASS**. C++ token normalizer 14/14, bounded HTTP response 8/8, both-board parity and 10/10 parity mutations pass.
- Full [#45739536013](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45739536013), validation job `139640950883`: **FAIL** at inherited `Missing poll signature check`. All 14/14 firmware target jobs and Android PASS; production import/signing, update, simulation and candidate jobs are skipped.

The focused workflow logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0` and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`. No hardware acceptance is claimed.

## Superseded by UTC02 stack reconciliation

On 2026-11-26 UTC02, #352 advanced to `a1720e1724a15b5254d9dd1ee57e6212259a4896`, with prior #352 `0e984e267b3a8fb10c314800d1a7f120806354b7` as first parent and #349 `1a2ecf5fa8c8c20a0095ac898c1bff254280ad27` as second parent. The current #353 branch is being advanced with the reconciled #352 head as its second parent. The UTC01 statement that #353 was ahead of the prior #352 head was accurate at that time and is superseded by the UTC02 ancestry.

New exact-head CI must be read from the resulting UTC02 #352 and #353 commits; UTC01 CI remains historical and is not transferred to the new heads.
