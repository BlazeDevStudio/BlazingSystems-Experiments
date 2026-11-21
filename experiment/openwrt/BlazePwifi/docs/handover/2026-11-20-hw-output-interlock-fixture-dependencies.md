# PHX-HARDWARE — restore host-lab fixtures for the ISR-aware output gate

**Date:** 2026-11-20 UTC13  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test HEAD:** `3d8277d862c07b18a234589b6f1844f3d538ad93`

## Selected task

Restore exact-source host-lab compilation and regression coverage after the current `applyOutputs()` implementation gained an ISR sequence-snapshot dependency. Several hardware-owned fixtures extracted the real function but did not declare `coinEdgeSequence`, `lastHandledCoinEdgeSequence`, or `snapshotCoinEdgeSequence()`. The isolated poll-release output fixture also depended on `resetState()` from the default test main and left the poll-drain injection hook unused under `-Werror`.

This was a confirmed test-fixture integration defect, not a production-sketch compile failure.

## Changes — six Hardware-owned lab files only

1. `esp8266/BlazePwifiVendo/relay_output_polarity_lab.py` — added idle ISR sequence state and deterministic counter reset for the output-gate polarity scenarios.
2. `esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py` — added sequence state to the poll-response parser fixture and its separate pulse-window fixture; resets the counters for each window scenario.
3. `esp8266/BlazePwifiVendo/poll_window_drain_lab.py` — added an idle sequence stub because this timing-only fixture does not inject ISR edges.
4. `esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py` — made the isolated release-edge main self-contained, reset only its required state, attach the extracted coin ISR, and explicitly mark the unrelated drain hook unused. Both LED-write and relay-write edge injection cases remain active.
5. `esp32/BlazePwifiVendo32/journal_mount_failclosed_lab.py` — added idle sequence state and reset it per mount scenario.
6. `esp32/BlazePwifiVendo32/pending_journal_recovery_lab.py` — added idle sequence state and resets it across pending-load and pending-clear cases.

The fixtures that actually inject ISR edges continue to use the extracted ISR and sequence state; the idle stubs are limited to tests whose subject is parsing, mount, journal, timing, or output polarity rather than asynchronous edge delivery.

## Commit sequence

- `94e7e5782d05c611fc6bc7158b8dfaa1c6be2a1b` — output-polarity fixture
- `54dea71345e3a44a74c507a8ce30deb49a5f0985` — poll-response fixture
- `518f3589d6c881c31b89c9a1140b2340af783939` — poll-drain fixture
- `d73d936b8bec71d700184a5fd411f238733eb6dc` — poll-response window fixture
- `360d15c8c08c4ea1054b023979d659f1380c554f` — standalone poll-release interlock fixture
- `f2ece9b1a9670db7acb3b330d3eba1362d6ab307` — journal-mount fixture
- `3d8277d862c07b18a234589b6f1844f3d538ad93` — pending-journal fixture

The exact compare from the prior branch head `e6502a1f28da926095d4872b95d88ad43a2a01ec` is 7 commits ahead / 0 behind and changes only the six lab paths above. No `.ino`, shared API, finance, QA-owned `tests/`, Release workflow, COE or migration file changed in this task.

## Test-first evidence

### RED — fixture dependency failures reproduced

- [Relay/output PR run #44747804435](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44747804435), job `136327531551`, at `e6502a1`: extracted `applyOutputs()` did not compile because the polarity fixture lacked the ISR sequence symbols.
- [Quarantine PR run #44749590942](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44749590942), job `136333688806`, at `54dea713`: poll-response's nested window fixture lacked the same symbols.
- [Quarantine push run #44750404098](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44750404098), job `136336468486`, at `360d15c8`: journal-mount fixture lacked the new sequence dependency. The preceding relay run also exposed the release fixture's missing `resetState()` and unused drain-hook warning under `-Werror`.

### GREEN — exact source/test SHA `3d8277d862c07b18a234589b6f1844f3d538ad93`

- Quarantine push [#44750885975](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44750885975), job `136338151997`: **SUCCESS**.
- Quarantine PR [#44750892185](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44750892185), job `136338172586`: **SUCCESS**.
- Relay/output PR [#44750892290](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44750892290): source-output job `136338172298` and ESP32 boot-polarity job `136338172743`: **SUCCESS**.

The exact-head logs include:

- Quarantine source: 36/36 scenarios per board; pending-attempt marker 28/28 per board; journal mount 8/8 per board; pending journal 16/16 and pending clear 17/17 per board.
- Poll response: 11/11 fail-closed cases, 13/13 strict root-JSON cases, 4/4 coin-POST root-status cases and 4/4 default-deny disposition cases per board.
- Poll-window drain: 11/11 per board; short-debounce and unsafe-deadline rollover mutations rejected.
- Poll loop: 8/8 fault-marker scenarios and 7/7 existing guards; original #177 1501/1600/1680 timing marker passes; two ISR edges across UINT32 wrap remain count=2; both release-edge tests pass at the LED write and relay write; missing pre-poll inhibit, non-wrap-safe delta, constant-one delta, omitted sample, ignored journal latch and missing persistence mutations are rejected.
- Output polarity: 48/48 active-high/active-low scenarios; unsafe polarity/output-order mutations rejected.

All of the above is source-extracted host simulation / CI evidence. It is not physical relay, coin acceptor, flash durability, or power-cut acceptance.

## Full validation disposition

- Full push [#44750885733](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44750885733), validation job `136338279876`: **FAILED** at QA-owned `tests/controllers.sh` with `Missing poll signature check` in the ESP8266 sketch.
- Full PR [#44750892705](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44750892705), validation job `136338326665`: same **FAILED** assertion.
- The completed push run's 13 firmware/platform target jobs and Android build passed. Downstream simulations, update bundle, candidate gate, signing and publishing were skipped because validation failed.

Do not add an ad-hoc `response_sig`, weaken the default-deny controller, or change QA-owned assertions from this Hardware branch. PHX-CORE must publish the approved authenticated register/poll and event-bound receipt/disposition contract; PHX-QA owns the corresponding positive/negative validation change.

## Coordination and remaining blockers

- PHX-MASTER PR #288 is OPEN / DRAFT at `962e1179aae8f49551f151bf4721e1524f690c38`. Its current `ROLE_ASSIGNMENTS.md` still records an older #327 head (`b6304208...`); Master should refresh it to the live #327 head after this handover commit.
- #239 remains OPEN / DRAFT at `d83b715b116185107737fef721c2eece8feebf39`; #254 at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; parallel #283 at `830c355376380f9b5533d5cda2558beed41a593a`. No cherry-pick or stack rewrite was performed.
- #254's focused header run [#44683629378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629378) job `136112658441` passes; Full [#44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) fails ESP32 compilation because `mbedtls/sha256.h` is absent from the installed core and separately fails the mandatory handover freshness gate.
- At #283's exact head, the original unconditional-clear source pattern appears corrected: failed quarantine append returns before `clearPending()`, and append readback is present. However, `quarantinePending()` remains definition-only with no active callsite; `response_sig` remains comments only, and the main register/poll producer has no approved signature contract. This is audit-only; #283 was not changed.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not present in the accessible Files Library listing; no Google Drive connector was exposed. Do not substitute older registry snapshots.
- Physical coin/relay/electrical acceptance, 150 controlled power cuts, and 30-device 24-hour soak remain NOT TESTED. Protected anti-rollback witness, financial v1→v2 migration and durable accounting/replay remain unestablished.

## Evidence classification

- **SIMULATED:** all source-extracted host tests and mutation runs above.
- **CI VERIFIED:** the exact-head focused Quarantine and Relay/Output Actions runs listed above.
- **NOT TESTED:** physical devices, real coin acceptors, electrical pulses, relay contacts, power cuts, long soak and flash durability.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO.

## Next exact actions

1. PHX-QA: replace the inherited positive poll-signature presence assertion with source-exact default-deny tests until CORE's contract is approved; rerun Full at an exact SHA.
2. PHX-CORE: publish canonical authenticated register/poll and event-bound coin receipt/disposition bytes and golden vectors.
3. PHX-MASTER: refresh #327's exact head in `ROLE_ASSIGNMENTS.md` and reconcile the stacked ancestry without rebasing or force-pushing this branch.
4. PHX-HARDWARE: preserve the fixture dependency stubs and continue only after revalidating all live heads.

**Disposition:** scoped lab repair verified; PR #327 remains OPEN / DRAFT / UNMERGED; production remains NO-GO.
