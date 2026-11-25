# PHX-HARDWARE UTC04 — shared C++ fixture prefix containment

**Updated:** 2026-11-25T04:50:45.448Z  
**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 contribution; shared test-runner safety  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** #349 OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hw-json-array-primitive-guard-20261124-utc00  
**Base PR:** #347 at 960184670379f01e20f0e7e8bc23b3e5eedacd3f

## Source change

Source/test commit: [f591cb85ba032e4f2c30e5008c71de9ce8d17f2e](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f591cb85ba032e4f2c30e5008c71de9ce8d17f2e)

Files changed:
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_fixture_runner.py
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_fixture_runner_contract_lab.py

The shared runner already validated the C++ fixture stem. It did not validate the separate tempfile prefix passed to tempfile.TemporaryDirectory. Because tempfile joins the prefix to its selected temporary root, an absolute or separator-bearing prefix can escape the runner's default temporary directory. This was a shared-helper containment defect, not a production firmware defect.

Added _validate_prefix(prefix), called before TemporaryDirectory:
- rejects non-string, "." and "..";
- rejects NUL, slash and backslash;
- rejects POSIX absolute paths and Windows drive-qualified prefixes using PureWindowsPath;
- keeps the valid empty prefix supported.

The contract suite now checks eight invalid-prefix classes, proves rejection happens before temporary-directory creation, file writes and subprocess execution, and verifies empty-prefix compatibility. The printed contract marker is 11/11.

No production .ino, CGI producer, shared wire API, financial logic, coin admission, relay actuation, signer, witness, migration or COE destination was changed.

## Test-first history

- Initial test-only commit f919e22: invalid test harness because subprocess.run was not given successful mock results; Quarantine/Relay failed before reaching the intended ValueError assertions. This is not counted as product RED.
- Corrected test-only commit 612300a: mock compiler/program calls return successful results if the prefix guard is absent.
- Expected RED: Quarantine push [#45548811482](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45548811482), job 138984773424, fails eight subtests with "ValueError not raised"; Relay push [#45548811690](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45548811690), job 138984774331, fails the same missing-guard contract.
- Corrected source/test: [f591cb85](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f591cb85ba032e4f2c30e5008c71de9ce8d17f2e).

## Exact-source CI

Quarantine:
- Push [#45549009733](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45549009733), job 138985407294: PASS.
- PR [#45549018310](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45549018310), job 138985434992: PASS.
- Logs show CPP_FIXTURE_RUNNER_CONTRACT_PASS 11/11, both-board dual-store labs PASS, and explicit SIMULATED_ONLY / physical acceptance flags zero.

Relay:
- Push [#45549009693](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45549009693), jobs 138985407353 and 138985407712: PASS.
- PR [#45549018245](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45549018245), jobs 138985434857 and 138985435158: PASS.
- Existing ESP8266/ESP32 output polarity, poll-inhibit, CGI denial and bounded HTTP response checks passed; physical relay and power-cut flags remain zero.

Full:
- Push [#45549009680](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45549009680), validation job 138985508616: FAIL at inherited "Missing poll signature check".
- PR [#45549018383](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45549018383), validation job 138985535915: same FAIL.
- Both exact-source runs completed 14/14 target/platform + Android build jobs successfully; 12 validation-dependent simulation, update, signing, candidate and publication stages were skipped.

## Stack and source-audit notes

- PR #239 remains OPEN / DRAFT; Phase A denial is preserved.
- PR #254 remains OPEN / DRAFT; ControllerAuthV1Lab is explicitly non-actuating and not wired. Current header supports Mbed TLS 2.x/3.x only; Mbed TLS 4 needs a separately reviewed PSA adapter.
- PR #283 remains OPEN / DRAFT at 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30. Revalidation of owner comment 6883020442: clearPending is reached only after verified append, but quarantinePending has no active callsite; real LittleFS power-loss lifecycle remains unaccepted. Current main CGI register/poll/coin producer still lacks response_sig; do not invent one.
- PR #340 remains OPEN / DRAFT and its base SHA 88581eef... is behind current #283 head 4dd0b01b...; Master must reconcile stack ancestry. No rebase or retarget was performed.
- PR #349 remains OPEN / DRAFT / UNMERGED, based on #347 at 960184670379f01e20f0e7e8bc23b3e5eedacd3f.
- COE main remains a6513ab4...; COE #26 remains OPEN / DRAFT / frozen at b382d233... . No COE migration or source promotion was performed.

## Status and next action

- Shared runner prefix containment: CI VERIFIED.
- Host/source-extracted tests: SIMULATED / CI VERIFIED.
- Local independent execution: NOT RUN.
- Physical coin/relay/electrical recovery, 150 power cuts, 30-device 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release signoff: NOT ACCEPTED.
- #266 global cleanup checklist remains 0/7; this is one bounded Hardware contribution, not global completion.
- Private Google Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json was not accessible through the available connectors or Library search; no older registry was substituted.

**Next exact action:** PHX-MASTER refreshes #349 pins and reconciles #340/#283 stack ancestry; PHX-CORE publishes the approved authenticated register/poll contract and golden vectors; PHX-QA independently reconciles the inherited signature assertion. PHX-HARDWARE revalidates live heads before the next owned task.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**
