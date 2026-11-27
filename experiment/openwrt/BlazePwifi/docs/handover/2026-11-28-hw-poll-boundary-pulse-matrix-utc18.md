# PHX-HARDWARE handover — poll-boundary pulse matrix (UTC18)

- **Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
- **Role:** PHX-HARDWARE
- **PR:** [#365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/365), OPEN / DRAFT / UNMERGED
- **Branch:** `phoenix/hw-poll-boundary-pulse-matrix-20261128-utc18`
- **Parent chain:** #364 → #362 → #361 → #359 → #355 → #354
- **Base SHA:** `ea765fb822e1c517db4e61c103b86d8eb2c66c92`
- **Source/test SHA:** `f38e86b683bbf1e77cdb63e3071630a5b3aedb2c`
- **Tested docs/PR head:** `b94f16a08d85baf980eb471222b8479f491299a2`

## One task completed

Expanded the source-extracted host C++ harness for the P0 synchronous-poll intake-deny candidate. No production sketch, controller API, financial path, QA-owned assertion or release code changed.

Six 80 ms pulse windows are simulated relative to the 3,500 ms poll:

| Window | Purpose |
|---|---|
| -40..40 ms | Input already active when pre-poll deny is applied |
| 0..80 ms | Pulse at poll start |
| 1600..1680 ms | Pulse mid-wait |
| 3420..3500 ms | Ends exactly at poll return |
| 3460..3540 ms | Remains active across poll return |
| 3500..3580 ms | Starts exactly at poll return |

Each timing window runs through four independent relay/LED active-level combinations: 24 cases per board, 48 total. The stub returns a non-empty untrusted `insert=true` body and the source contract requires it to remain discarded. A pulse crossing poll return remains active for the first post-poll sample.

## Exact CI evidence

- Focused docs-head run [#46052478993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46052478993), job `140686930242`: **PASS**.
- Exact source/test SHA: `f38e86b683bbf1e77cdb63e3071630a5b3aedb2c`.
- Mbed TLS [#46052478997](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46052478997): source contract `140686931241`, Arduino core 3.3.13 `140686930962`, core 4.0.0 `140686931234`: **3/3 PASS**.
- Full [#46052478996](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46052478996): CI-0701 PASS; validation job `140687123327` **FAIL** at `experiment/openwrt/BlazePwifi/tests/controllers.sh:21`, `grep -q 'config_revision'`. This is the inherited v0.6/current-main parity assertion. ESP8266, ESP32, Android and all 13 firmware target jobs PASS; downstream update/simulation/signing/candidate/publication jobs skipped.
- Native PAY-0745: NOT RUN on #365.

The focused log on both boards reports:

```text
BLOCKING_POLL_WAIT_PASS 3500ms pulse_cases=6 polarity_combinations=4 pre_poll_inflight=1 cross_return=1 at_return=1 untrusted_response_ignored=1 accepted=0
```

The append-only ledger guard passed on the tested docs head with `base_bytes=1132798 appended_bytes=35643`.

## Critical scope boundary

The active `blazepwifi-v0.6.0-audit-foundation` branch remains at `2fbd2475e9f54878c316fa7cea2f228386b0e859` and was not modified. PR #365 is a test-only child of the unmerged deny-only candidate stack; it does not fix or mitigate the active branch's poll-before-first-sample race. The current active v0.6 source still performs synchronous `post("poll")` before the first `digitalRead(runCoinPin)` on both boards.

The pre-poll in-flight case proves only that the candidate deny latch is applied while the input is active. It does not prove that the physical acceptor retains a coin when inhibited mid-pulse. P0 #177 remains OPEN.

## Acceptance boundary

Status: SIMULATED / CI VERIFIED only. Physical acceptor/relay polarity, pulse retention, electrical pulse/recovery, 150 power cuts, and 30-device/24-hour soak are NOT TESTED. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.

No positive coin admission, relay re-enable, finance, replay, witness, downgrade, migration, signer, flash, reset, merge, release or deployment was performed.

## Coordination

- **PHX-MASTER:** add #365 to role/integration matrices without changing ownership; preserve #239/#254/#283 and the existing stack.
- **PHX-CORE:** publish authenticated register/poll/receipt/disposition semantics; Hardware did not infer or alter the contract.
- **PHX-QA:** independently review the six boundary vectors and reconcile the inherited `config_revision` parity assertion against the approved contract.
- **PHX-HARDWARE:** keep deny-only behavior; no positive admission until contract and physical electrical acceptance are approved.

## BLAZE-COMMS/1 checkpoint

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261127T18-POLL-BOUNDARY-PULSE-MATRIX",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-CORE", "PHX-QA"],
  "type": "PROGRESS",
  "priority": "P0",
  "task_id": null,
  "branch": "phoenix/hw-poll-boundary-pulse-matrix-20261128-utc18",
  "base_sha": "ea765fb822e1c517db4e61c103b86d8eb2c66c92",
  "source_test_sha": "f38e86b683bbf1e77cdb63e3071630a5b3aedb2c",
  "tested_docs_head": "b94f16a08d85baf980eb471222b8479f491299a2",
  "status": "CI_VERIFIED",
  "evidence": [
    "Focused #46052478993 job 140686930242 PASS",
    "Mbed #46052478997 jobs 140686931241/140686930962/140686931234 PASS 3/3",
    "Full #46052478996 validation job 140687123327 FAIL at tests/controllers.sh:21 config_revision; 13/13 firmware targets and Android PASS",
    "Active v0.6 branch 2fbd2475e9f54878c316fa7cea2f228386b0e859 unchanged; P0 #177 unresolved"
  ],
  "blockers": [
    "Physical coin retention during relay inhibit NOT TESTED",
    "Active v0.6 poll-before-first-sample race remains",
    "CORE authenticated controller contract pending",
    "Independent QA review pending"
  ],
  "next_action": "Request QA review and Master matrix registration; keep PR #365 DRAFT and coin/relay denied.",
  "updated_utc": "2026-11-27T18:51:31Z"
}
```
