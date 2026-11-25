# PHX-HARDWARE — active-high coin / active-low relay poll-drain cross-product

**Checkpoint:** 2026-11-24T23:49:00Z  
**Role:** PHX-HARDWARE  
**Tasks:** #172 / #177 / #266 / PR #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test commit:** [`353231c60fe09e4694fa73e3a3a1e64c5d21353d`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/353231c60fe09e4694fa73e3a3a1e64c5d21353d)

## Selected owned task

The #177 source-extracted poll-drain regression already exercised active-high and active-low coin inputs and relay polarities separately. The post-drain ISR rollover scenario did not combine an **active-high coin input** with an **active-low acceptor relay**. This cross-product matters because the RISING-edge input path and active-low physical output-off level must remain independent.

## Concrete test change

Only this Hardware-owned lab file changed:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_edge_race_contracts.py`

- Added a post-drain ISR rollover scenario using `with_active_low_relay(post_drain_rollover_main(active_low=False))`.
- Requires the active-high coin input to attach the RISING ISR, prevents the synchronous HTTP poll after a pulse arrives during drain, preserves the two-edge rollover fault, and asserts the active-low relay's **physical OFF level is HIGH** (`relayLevelHigh`).
- Added a wrong-ISR-polarity failure injection; it must exit 56 instead of accepting the poll.
- No production `.ino`, CGI producer, shared CORE contract, finance, signer, witness, migration, Release workflow or COE destination was changed.

## Exact-source CI

All focused runs checked out source/test SHA `353231c60fe09e4694fa73e3a3a1e64c5d21353d`.

- Quarantine PR [run #45512634485](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512634485), job `138863962314`: **SUCCESS**. Logs explicitly show:
  - ESP8266 `POLL_POST_DRAIN_ACTIVE_HIGH_COIN_ACTIVE_LOW_RELAY_OFF_LEVEL_PASS`
  - ESP8266 wrong-ISR-polarity mutation rejected (expected exit 56)
  - ESP32 `POLL_POST_DRAIN_ACTIVE_HIGH_COIN_ACTIVE_LOW_RELAY_OFF_LEVEL_PASS`
  - ESP32 wrong-ISR-polarity mutation rejected (expected exit 56)
- Quarantine push [run #45512622906](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512622906), job `138863927042`: **SUCCESS**.
- Relay PR [run #45512634525](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512634525): **SUCCESS**; jobs `138863961055` / `138863961368` passed.
- Relay push [run #45512622888](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512622888): **SUCCESS**; jobs `138863926693` / `138863926947` passed.

## Full integration result

- Exact-source Full [run #45512634648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512634648): **FAILURE**. Validation job `138863963444` fails at the inherited `tests/controllers.sh` assertion **`Missing poll signature check`**. All `14/14` firmware/platform and Android build jobs completed SUCCESS; release/simulation/signing/publication dependents were skipped.
- The previous docs-head Full [run #45502304116](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45502304116) is also terminal **FAILURE**, not pending: validation job `138828592534` failed at the same assertion; all 13 firmware targets plus Android (14/14) completed SUCCESS.

CORE owns the authenticated register/poll response contract. QA owns independent reconciliation of the inherited assertion. Do not synthesize `response_sig`, weaken the assertion or enable positive poll/coin admission.

## Other live stack audits

- #239 Phase A deny: OPEN / DRAFT / UNMERGED at `d83b715b116185107737fef721c2eece8feebf39`.
- #254 ControllerAuthV1Lab: OPEN / DRAFT / UNMERGED at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; helper remains non-actuating/unwired; ESP32 core 4.0.0 compatibility and Full validation remain blockers.
- #283 parallel sketches: OPEN / DRAFT / UNMERGED at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`. The original unconditional-clear lead is not present at that head: failed quarantine append returns false before `clearPending()`; `quarantinePending()` remains definition-only with no active callsite. Current main CGI register/poll still lack the approved `response_sig`. Physical LittleFS torn-write/power-loss recovery remains NOT TESTED.
- #349 remains the child of #347; no retarget, rebase, cross-stack cherry-pick or merge.

## Release and evidence status

- #266 remains OPEN / **0-of-7** role tracks complete; this is one bounded Hardware test contribution.
- #177 remains OPEN / P0; host regression coverage does not certify physical coin capture.
- #31 durable accounting/member transfers, #32 rental lease/receipt atomicity, #43 independent freshness witness and #34 physical acceptance remain open blockers.
- 150 controlled power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, durable accounting/replay, reversible v1-to-v2 migration and independent QA/Release acceptance remain NOT TESTED or NOT ACCEPTED.
- Local independent execution: **NOT RUN**. GitHub Actions is the reported source of CI evidence.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the accessible Library; no Google Drive connector surfaced. No older registry was substituted.

**Status:** SIMULATED / CI VERIFIED (source-extracted host tests and build jobs only).  
**HARDWARE ACCEPTED:** NO.  
**PRODUCTION READY:** NO-GO.

## BLAZE-COMMS/1

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261124T23-ACTIVE-HIGH-COIN-ACTIVE-LOW-RELAY",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-CORE", "PHX-QA"],
  "type": "PROGRESS",
  "priority": "P1",
  "task_id": "#172/#177/#266/#349",
  "repository": "BlazeDevStudio/BlazingSystems-Experiments",
  "branch": "phoenix/hw-json-array-primitive-guard-20261124-utc00",
  "base_sha": "960184670379f01e20f0e7e8bc23b3e5eedacd3f",
  "source_test_sha": "353231c60fe09e4694fa73e3a3a1e64c5d21353d",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_edge_race_contracts.py"
  ],
  "status": "VERIFIED",
  "evidence": [
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/353231c60fe09e4694fa73e3a3a1e64c5d21353d",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512634485",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512622906",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512634525",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512622888",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45512634648",
    "POLL_POST_DRAIN_ACTIVE_HIGH_COIN_ACTIVE_LOW_RELAY_OFF_LEVEL_PASS on ESP8266 and ESP32",
    "wrong ISR polarity rejected with expected exit 56 on both boards",
    "Full validation failed at inherited Missing poll signature check; 14/14 build jobs succeeded"
  ],
  "blockers": [
    "CORE authenticated register/poll response contract and golden vectors remain outstanding",
    "QA must reconcile the inherited poll-signature assertion without weakening deny-default",
    "150 power cuts, 30-device/24-hour soak and physical electrical pulse/relay recovery remain NOT TESTED",
    "Protected anti-rollback signer/witness, durable accounting/replay and v1-to-v2 migration remain NOT ACCEPTED",
    "Independent QA and Release signoff remain pending",
    "Private Google Drive registry v11 is unavailable through the current connector surface"
  ],
  "next_action": "CORE publishes the versioned authenticated register/poll contract; QA independently reconciles the assertion; Master refreshes its #349 pins; Hardware revalidates live heads before the next owned task.",
  "updated_utc": "2026-11-24T23:49:00Z"
}
```
