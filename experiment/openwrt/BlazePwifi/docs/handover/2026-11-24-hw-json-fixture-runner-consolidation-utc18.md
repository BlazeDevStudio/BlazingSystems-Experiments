# PHX-HARDWARE handover — JSON fixture runner consolidation

**Checkpoint:** 2026-11-24 UTC18  
**Role:** PHX-HARDWARE  
**Task:** #172 / #177 / #266 / PR #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base:** PR #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test commit:** [`32c026538e737870ea8bb1e22143e438f9d61f7a`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/32c026538e737870ea8bb1e22143e438f9d61f7a)

## Selected bounded task

Cleanup-first consolidation of the strict JSON parser host lab's duplicate C++ compile/run implementation into the already-established shared fixture runner. No firmware behavior or shared response contract changed.

### Source change

Only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_json_array_primitive_lab.py` changed:

- Removed the local `subprocess` / `tempfile` compile-and-run implementation.
- Imported `run_cpp_fixture` from the sibling `cpp_fixture_runner.py`.
- Kept the same C++17 flags (`-Wall -Wextra -Werror -Wno-unused-parameter`), 30-second compile limit and 10-second execution limit.
- Preserved the returned process result and existing fixture/mutation expectations.
- Centralized timeout handling and bounded diagnostic-tail behavior in the shared helper.
- File size changed from 293 to 286 lines; GitHub reports 12 additions / 19 deletions.

The Relay workflow already invokes `poll_json_array_primitive_lab.verify` through `poll_response_failclosed_lab.py`; no workflow path or execution step was omitted.

No production `.ino`, CGI producer, shared API, financial ledger, signer, witness, migration or COE destination source changed.

## Exact-head CI

All following runs checked source/test SHA `32c026538e737870ea8bb1e22143e438f9d61f7a`.

### Focused workflows

- Relay Output Polarity LAB: [run #45456337527](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45456337527) — **SUCCESS**.
  - ESP32 boot-polarity job `138666667057` — PASS.
  - Source/output-polarity job `138666667690` — PASS.
- Quarantine Byte Readback LAB: [run #45456337640](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45456337640) — **SUCCESS**.
  - Quarantine-source job `138666667604` — PASS.

Relay exact logs include both-board strict JSON grammar results:

- Primitive grammar: valid 9/9, invalid 16/16; four mutations rejected on each board.
- Composite grammar: valid 6/6, invalid 12/12 on each board.
- Root duplicate-status and trailing-data denial: 2/2 and 3/3.
- Array/object separator, primitive terminator, depth cap, raw control character, unsupported escape, non-hex Unicode escape, leading zero, empty fraction/exponent and truncated literal mutations rejected.
- Current CGI register/poll responses without `response_sig` remain denied; response-positive consumer bypass mutations rejected.

Quarantine exact logs also passed the ESP8266/ESP32 fake-LittleFS, EEPROM/config-read recovery, pulse-capture and cold-boot output-polarity labs. These are host/source-extracted simulations.

### Full BlazePwifi build

[Run #45456337546](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45456337546) — **FAILURE**.

- Validation job `138666668745` failed at `tests/controllers.sh`: `Missing poll signature check` in the ESP8266 sketch.
- This is the existing CORE/QA producer-consumer contract mismatch; this cleanup did not modify the sketch or that assertion.
- All 13 firmware target jobs plus Android completed PASS (14/14).
- Candidate, simulation, signing and publication stages were skipped.

## Evidence classification and limits

- Shared fixture-runner integration: **CI VERIFIED**.
- JSON grammar and mutation rejection: **SIMULATED / CI VERIFIED**.
- Local independent test execution: **NOT RUN**.
- Physical coin pulse, relay/electrical recovery, power-cut and 30-device soak: **NOT TESTED**.
- Protected anti-rollback witness, durable accounting/replay and v1-to-v2 migration: **NOT ACCEPTED**.
- **PRODUCTION NO-GO.**

## Coordination / next exact action

- PHX-CORE must publish the approved versioned register/poll response contract and canonical vectors.
- PHX-QA must reconcile the inherited `Missing poll signature check` assertion without weakening deny-default.
- PHX-MASTER must refresh its own `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md` and architecture pins to this branch's source/test SHA and final docs head.
- PHX-HARDWARE must revalidate all live heads/assignments on the next activation before selecting another owned task.

The private Drive registry `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the connected Files Library, and no Google Drive connector was exposed in this run. No older registry was substituted.

No Codex, merge, force-push, flash, device reset, customer hardware test, live-money operation, production migration, signer provisioning, release tag or deployment occurred.
