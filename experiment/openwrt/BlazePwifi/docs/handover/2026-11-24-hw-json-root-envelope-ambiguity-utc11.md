# PHX-HARDWARE — strict poll JSON root-envelope regression

**Date:** 2026-11-24 (UTC11)  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Role:** `PHX-HARDWARE`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base:** PR #349 stacked on #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test commit:** `083bc6405634c154e491f3b13e2b5ab0ef70df9c`  
**PR:** [#349 — JSON grammar and first-fault snapshot regressions](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED

## Scope and changes

This increment is test-only. It does not alter either production `.ino` sketch, the CGI producer, the controller protocol, coin/relay admission, accounting, signing, witness, migration, or release behavior.

Updated:

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_json_array_primitive_lab_fixtures.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_json_array_primitive_lab.py`

The source-extracted parser regression now locks down two strict root-envelope properties on both ESP8266 and ESP32:

1. Duplicate root `ok` status keys are denied (2/2 cases).
2. Trailing non-whitespace data, including a second JSON object, is denied (3/3 cases); trailing JSON whitespace remains accepted (1/1 control).

Two fail-open mutations are injected per board:

- Remove the duplicate-root-key guard and relax the final `found == 1` condition.
- Remove the end-of-input check.

Both mutations are rejected on both boards. The existing JSON primitive grammar (9 valid / 16 invalid), composite-depth boundary (16 accepted / 17 rejected), and prior poll-response fail-closed cases remain in the same lab. The workflow already watches both changed lab paths; no workflow change was needed.

## Exact-head CI evidence — source/test SHA `083bc6405634c154e491f3b13e2b5ab0ef70df9c`

- Quarantine push [run #45382551771](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45382551771), job `138405016370`: **PASS**.
- Quarantine pull-request [run #45382562621](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45382562621), job `138405055908`: **PASS**.
- Relay output polarity [run #45382562525](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45382562525): **PASS**; source-output job `138405055927`, ESP32 boot-polarity job `138405055535`.
- Both board logs emit:
  - `POLL_JSON_DUPLICATE_ROOT_STATUS_DENY_PASS 2/2`
  - `POLL_JSON_TRAILING_DATA_DENY_PASS 3/3 WHITESPACE_ACCEPTED=1`
  - `MUTATION_REJECTED allow-duplicate-root-status expected_exit=91`
  - `MUTATION_REJECTED accept-trailing-json-data expected_exit=93`
  - `POLL_JSON_ROOT_ENVELOPE_PASS duplicate=2/2 trailing=3/3; mutations=2/2 rejected`
- Full integration [run #45382562582](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45382562582): **FAIL** at validation job `138405163009`, inherited `tests/controllers.sh` assertion `Missing poll signature check`. All 14/14 target/platform jobs, including Android and both ESP sketches, completed **PASS**. Update bundle, simulations, candidate, signing, production handoff and publication stages were **SKIPPED**.

An initial source/test attempt at `298004ef` failed because the new trailing-whitespace fixture double-escaped C++ control characters. The fixture was corrected in `2aea4267` and the existing JSON-string escape fixture restored in `083bc640`; the final exact-head runs above pass. The failed attempt is retained as history, not represented as final evidence.

## Evidence classification and limits

- Parser regression: **CI VERIFIED** (source-extracted host C++ simulation).
- Physical coin acceptor, relay contacts/polarity, pulse electrical behavior, LittleFS power-loss durability, power-cut recovery, and 30-device soak: **NOT TESTED**.
- `SIMULATED_ONLY=1`; `PHYSICAL_POWER_CUT_VERIFIED=0`; `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

This parser test is not controller authentication. The current register/poll producer contract still lacks an approved authenticated `response_sig` envelope. Hardware will not invent a signature, reinterpret member-endpoint signatures, or weaken default-deny to satisfy the inherited QA assertion.

## Coordination and next action

- **PHX-MASTER:** refresh `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md` from the old #349 pins to source/test SHA `083bc6405634c154e491f3b13e2b5ab0ef70df9c` and the final docs head; reconcile the current root README's historical `BlazingSystems` links with the verified `BlazeDevStudio` owner.
- **PHX-CORE:** publish the approved authenticated register/poll response envelope, canonical bytes, and golden vectors.
- **PHX-QA:** reconcile `Missing poll signature check` against that approved contract without weakening negative/default-deny tests.
- **PHX-HARDWARE:** rerun full integration against the approved contract SHA; continue only source-level safe regression work until then.

No merge, force-push, physical flashing, device reset, production migration, live-money operation, signing, release tagging, or deployment occurred. Production remains **NO-GO**.
