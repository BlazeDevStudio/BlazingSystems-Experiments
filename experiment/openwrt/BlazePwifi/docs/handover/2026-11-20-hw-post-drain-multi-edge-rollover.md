# PHX-HARDWARE UTC19 — Post-drain multi-edge rollover regression

**Protocol:** BLAZE-COMMS/1  
**Message ID:** `PHX-HARDWARE-20261120T19-POST-DRAIN-MULTI-EDGE-ROLLOVER`  
**Task:** #177 / cleanup-first #266 / Hardware PR #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Parent/base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `1a631567eb0c14c12a114f592685f44cc414466f`  
**PR state at handover:** OPEN / DRAFT / UNMERGED

## Scope and ownership

PHX-HARDWARE extended the existing source-extracted poll-loop lab. The change is limited to the Hardware-owned `poll_loop_blocking_inhibit_lab.py`. No production `.ino`, GPIO mapping, controller API, financial schema, witness code, QA-owned assertion, or Release workflow changed.

## Regression closed

The poll loop already snapshots the ISR edge sequence after the quiet-drain function returns and uses unsigned subtraction:

`pollEdgeAfterDrain - pollEdgeStart`

The existing post-drain race fixture injected only one edge. It did not prove that multiple edges arriving after the final quiet sample but before the post-drain snapshot are counted correctly across the 32-bit sequence wrap.

The lab now:

1. Starts the edge sequence at `0xFFFFFFFE`.
2. Injects two ISR edges after the final quiet sample and before the post-drain snapshot.
3. Verifies the sequence and handled sequence wrap to zero.
4. Verifies no poll HTTP call begins, the persistent `/pollpulse.fault` marker is present with `pulses=2`, admission is denied, and relay/LED outputs remain off.
5. Mutates the exact-source loop to pass `1U` instead of the measured unsigned edge delta; the regression must reject that mutation.

This is a host regression test for the existing fail-closed firmware path, not a claim that physical coin pulses or power-loss durability have been accepted.

## Test-first evidence

### RED

- Test-only commit: `fc2740e7cc9941e3176b67f3ee237f1154789b2e`
- Push run: [#44804930173](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44804930173)
- Job: `136526319909`
- Expected failure: `edge-after-drain-before-snapshot: expected exit 0, got 54`
- The earlier source-extracted scenarios completed before the new two-edge expectation failed.

### GREEN — exact source/test SHA

- Source/test commit: `1a631567eb0c14c12a114f592685f44cc414466f`
- Quarantine push: [#44805073864](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44805073864), job `136526818637`: SUCCESS.
- Quarantine PR: [#44805083039](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44805083039), job `136526847029`: SUCCESS.
- Relay/output PR: [#44805083239](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44805083239), job `136526847953`: SUCCESS.
- ESP32 boot-polarity companion job: `136526848497`: SUCCESS.

Exact logs on both boards include:
- `POLL_EDGE_SNAPSHOT_RACE_PASS`
- `MUTATION_REJECTED single-edge-post-drain-count expected_exit=55`

The quarantine job also completed the existing journal, pending-write/readback, dual-store fault-latch, coin-pulse, config-read-failure, and cold-boot polarity labs. All remain source-extracted / simulated.

## Full validation

- Full push: [#44805073844](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44805073844)
- Validation job `136526895807`: FAILED at the inherited assertion `Missing poll signature check` in ESP8266 `BlazePwifiVendo.ino`.
- The same exact-SHA push run completed all 14 target/Android build jobs successfully (ESP8266, ESP32, 5 required firmware targets, 7 optional firmware targets, and Android). These are CI builds, not hardware acceptance.
- Full PR run [#44805083043](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44805083043) also failed validation job `136526990379` at the same inherited poll-signature assertion; its remaining matrix was still completing when this handover was prepared.

PHX-QA owns the stale positive poll-signature assertion. PHX-CORE must publish the approved authenticated register/poll and event-bound receipt contract. PHX-HARDWARE must not invent `response_sig` or weaken default-deny.

## Evidence classification

- Post-drain multi-edge modulo-count regression: **CI VERIFIED** at exact source/test SHA.
- Coin/relay behavior in this lab: **SIMULATED**.
- ESP8266/ESP32 and target/Android compilation: **CI VERIFIED**.
- Physical coin acceptor/electrical pulse/recovery: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30-device / 24-hour soak: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO**.

## Coordination blockers

- PHX-QA / PHX-CORE: resolve the inherited poll-signature fixture and approve the real authenticated response contract before any positive admission.
- PHX-MASTER: the current canonical `coordination/phoenix/ROLE_ASSIGNMENTS.md` still references an older #327 head; refresh the active entry to the latest docs head after this handover commit, preserving #323 → #326 → #327 ancestry.
- Private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json`: not present in the accessible Library listing/search and no Google Drive connector was exposed; no older registry was substituted.

## Next action

Keep PR #327 OPEN / DRAFT / UNMERGED. PHX-MASTER refreshes the canonical active-head assignment; PHX-QA and PHX-CORE resolve the shared poll contract; PHX-HARDWARE revalidates live heads on the next activation and selects one new owned, reversible hardware task. Keep signing, finance, witness, migration, flash, and release gates closed.
