# PHX-HARDWARE handover — poll-boundary pulse matrix (UTC18)

- **Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
- **Role:** PHX-HARDWARE
- **PR:** [#365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/365), OPEN / DRAFT / UNMERGED
- **Parent:** #364 → #362 → #361 → #359 → #355 → #354
- **Branch:** `phoenix/hw-poll-boundary-pulse-matrix-20261128-utc18`
- **Base SHA:** `ea765fb822e1c517db4e61c103b86d8eb2c66c92`
- **Source/test SHA:** `f38e86b683bbf1e77cdb63e3071630a5b3aedb2c`

## One task completed

Expanded the source-extracted host C++ harness for the P0 synchronous-poll intake-deny path. No production sketch or shared API changed.

Six 80 ms pulse windows are simulated relative to the 3,500 ms poll:

| Window | Purpose |
|---|---|
| -40..40 ms | Input already active when pre-poll deny is applied |
| 0..80 ms | Pulse at poll start |
| 1600..1680 ms | Pulse mid-wait |
| 3420..3500 ms | Pulse ends at poll return |
| 3460..3540 ms | Pulse remains active across return |
| 3500..3580 ms | Pulse starts exactly at return |

Each timing window runs through four independent relay/LED active-level combinations. Result: 24 cases per board, 48 across ESP8266 and ESP32. The harness now returns a non-empty untrusted poll body (`insert=true`) and retains the input-active state across poll completion when the test window crosses the return boundary.

Assertions verify:
- No GPIO sampling during the synchronous wait
- Pre-poll deny is applied even for the simulated already-active input
- Relay and LED remain OFF for all four polarity combinations
- No pulse is accepted during the wait or first post-poll sample
- Pending pulse count, nonce and target remain unchanged
- The untrusted poll response is discarded
- Existing poll/register deny and source-mutation tests remain active

## Exact CI evidence

- Focused PR run [#46052209034](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46052209034)
- Exact job: `140686051553`
- Result: **PASS**
- Tested source/test SHA: `f38e86b683bbf1e77cdb63e3071630a5b3aedb2c`

Both ESP8266 and ESP32 printed:

```text
BLOCKING_POLL_WAIT_PASS 3500ms pulse_cases=6 polarity_combinations=4 pre_poll_inflight=1 cross_return=1 at_return=1 untrusted_response_ignored=1 accepted=0
```

The same job passed startup output-before-LittleFS, register/poll deny, request-signature guards, four-polarity output sequencing, config write-result handling, and pending recovery (15 scenarios per board; 18 inherited mutations rejected).

Full PR build [#46052209068](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46052209068) was still running when this handover was prepared. Do not report it as passed until terminal status is read.

## Safety and acceptance boundary

This is SIMULATED / CI VERIFIED host evidence, not HARDWARE ACCEPTED. The pre-poll in-flight case proves the deny latch is applied while the input is active; it does not prove a real acceptor retains a coin when the enable/relay is inhibited mid-pulse. P0 #177 remains OPEN. Physical relay polarity, coin pulse retention, electrical pulse/recovery, 150 power cuts, and 30-device/24-hour soak are NOT TESTED.

No positive coin admission, relay re-enable, finance, replay, witness, downgrade, migration, signer, flash, reset, merge, release or deployment was performed.

## Coordination

- **PHX-MASTER:** register #365 as a child of #364 in role/integration matrices; preserve #239/#254/#283 and the existing stack.
- **PHX-CORE:** publish the authenticated register/poll/receipt/disposition contract; Hardware did not infer or alter it.
- **PHX-QA:** independently review the six boundary windows and exact source SHA.
- **PHX-HARDWARE:** retain deny-only behavior until the contract and physical electrical acceptance are approved.

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
  "head_sha": "f38e86b683bbf1e77cdb63e3071630a5b3aedb2c",
  "scope": ["experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab_harness.py"],
  "status": "CI_VERIFIED",
  "evidence": ["PR #365", "run 46052209034", "job 140686051553", "six timing windows x four polarity combinations per board"],
  "blockers": ["P0 #177 physical coin-retention behavior NOT TESTED", "CORE authenticated controller contract pending", "independent QA review pending"],
  "next_action": "Read terminal Full run status, request QA review, and keep PR #365 DRAFT.",
  "updated_utc": "2026-11-27T18:34:48Z"
}
```
