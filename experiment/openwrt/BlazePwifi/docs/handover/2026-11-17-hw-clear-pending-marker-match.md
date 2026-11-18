# PHX-HARDWARE — exact pending-clear evidence fence

**Date:** 2026-11-17 UTC09  
**Branch:** `phoenix/hardware-clear-pending-marker-match-20261117`  
**Base:** PR #315 exact HEAD `84fe6b790139d147f330f13a40b3ae3e89a7042d`  
**Source commits:** ESP32 `0750633062aa5ed6b82cd4fc7ccc05833c2f7288`; ESP8266 `ab055040395500763a17541af2ff2183c0b39fe4`  
**Status:** DRAFT / SIMULATED / CI PENDING / PRODUCTION NO-GO

## Why this change exists

The previous `clearPending()` rejected multiple journal candidates but did not reject zero candidates. An orphan `/pending.attempt` marker with no pending journal could therefore be removed and reported as a successful clear. The marker was the only remaining durable evidence of an ambiguous coin POST attempt.

## Required invariant

Pending evidence may be cleared only when all of these conditions hold:

1. LittleFS is mounted and recovery is not already required.
2. `pendingAttemptMarkerMatches()` confirms the attempt marker binds the current RAM pulse count, nonce and target.
3. Exactly one of `/pending.dat`, `/pending.new`, `/pending.bak` exists.
4. That candidate passes the existing bounded record validator and matches the attempt marker's complete record (including checksum).
5. The pending journal removal is verified before the attempt marker is removed and verified last.

Any failure latches `journalRecoveryRequired`, leaves RAM state intact, and preserves all remaining evidence.

## Reproduction and local verification

The test-first RED used the exact old `clearPending()` body from parent PR #315 HEAD `84fe6b790139d147f330f13a40b3ae3e89a7042d`, with `fsReady=true`, `journalRecoveryRequired=false`, an attempted pending RAM event, and only `/pending.attempt` present. The old function returned success, deleted the marker, zeroed the pulse count, and left recovery false.

The patched function passed a local C++ fake-filesystem harness, 7/7:

- orphan marker only: deny, preserve marker and RAM;
- exactly one matching pending record plus marker: clear pending first, then marker;
- duplicate pending candidates: deny, preserve all;
- mismatched pending record: deny, preserve all;
- mismatched attempt marker: deny, preserve all;
- pending deletion failure: preserve marker and RAM, latch recovery;
- marker deletion failure: preserve marker, latch recovery.

This host harness is **SIMULATED**, not a repository QA suite or physical flash test. QA owns the canonical `tests/` directory and must add independent exact-source regression cases.

## Scope and boundaries

Only the ESP32 and ESP8266 firmware-owned `clearPending()` implementations changed. No shared API, financial server, schema, migration, signing, QA test, release workflow, destination COE firmware, or hardware configuration changed. `coinPostDispositionVerified()` and `acceptPollResponse()` remain default-deny. No coin admission is authorized.

## Required review and next action

- **PHX-QA:** add the listed negative/positive cases to the canonical pending-clear lab and run the exact PR head.
- **PHX-MASTER:** confirm the additional deletion precondition is consistent with Architecture Contracts §2.3.1 and §6.6.
- **PHX-CORE:** no receipt contract is assumed or changed; pending authenticated event-bound receipt/disposition work remains CORE-owned.

New exact-head GitHub Actions results are pending. The parent PR #315 focused quarantine job [#44054778537](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054778537) passed, but its Full workflow [#44054768998](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054768998) failed at QA-owned Controller protocol parity. That failure remains an integration blocker and must not be represented as green.

Physical flash/power-cut acceptance, 150 power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain NOT TESTED/BLOCKED. **PRODUCTION NO-GO.**


## Follow-up: exact-one pending candidate required before POST marker (2026-11-17 UTC10)

A second source audit found that **markPendingPostAttempt()** accepted any matching candidate among **/pending.dat**, **/pending.new**, and **/pending.bak**. It did not reject a second conflicting, duplicate, or corrupt candidate. Although normal boot recovery already denies multiple candidates, the dispatch boundary must independently reject an ambiguous journal set before writing the one-shot marker and sending a coin POST.

### Test-first and correction

- Test-only commit: [dbffa86](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/dbffa86cbbaa2edc7f454dd4e756f8f3216c2cfa).
- Expected RED: [focused run #44064000610](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064000610), job **133972839735**. The exact-source harness failed at **conflicting extra pending candidate denies POST marker** because the old helper found one matching **/pending.dat** and still created **/pending.attempt**.
- Firmware fix: [6100a74](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6100a74f8a94f314d99420917d51c28c75b5847d). Both boards now count all three candidate paths and require exactly one. The sole candidate must pass **readPendingFile()** and **samePendingRecord()** before the attempt marker can be written. Any missing, duplicate, conflicting, or corrupt candidate latches **journalRecoveryRequired** and denies dispatch.
- Positive recovery coverage: [f2bf146](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f2bf1465ddb95cc17a9d814cf68ba556000b9a8d) verifies a sole valid **/pending.new** or **/pending.bak** remains eligible after interrupted rotation; the exact-one rule does not incorrectly require **/pending.dat**.
- Final focused exact-head CI: [run #44064230539](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064230539), job **133973625675**, **SUCCESS** at **f2bf1465ddb95cc17a9d814cf68ba556000b9a8d**. The marker lab passed **28/28 per board (56/56 total)**. Inherited quarantine 23/23 per board, poll/config, poll-window, mount/output 14/14, boot recovery 32/32, pending clear 34/34, pending write/readback 22/22 per board, and coin POST gate 10/10 per board also passed.

### Evidence limits and next action

All results are exact-source C++ host tests with fake LittleFS. They are **SIMULATED / CI VERIFIED**, not physical flash or power-cut acceptance. The full BlazePwifi build at the final head is still being evaluated; no overall Full success is claimed. PHX-QA must repair the canonical controller extractor / stale poll-signature expectation and independently rerun Full validation. PHX-CORE/MASTER review remains required for the provisional one-shot marker contract. No financial receipt authority, coin admission, migration, hardware flash, or production permission is created by this fix.


## Final Full-workflow reconciliation (2026-11-17 UTC10)

At final PR HEAD **9f6a7141fa10cd5ed90f267f389cb6212e2e7d1a**, Full run [#44064436567](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064436567) completed with overall **FAILURE**.

- Validation job **133974480063 FAILED** in the inherited controller-parity check: it still requires an active poll signature in the ESP sketches. Master PR #288 at **8bffe20f4a0ff5b722766c42d7dd3f03e97bee78**, Architecture Contracts §6.3, keeps poll admission denied until PHX-CORE publishes the canonical producer/consumer contract and PHX-QA approves exact vectors. Do not re-enable the unapproved poll formula to satisfy this stale assertion.
- All **14 target/platform jobs completed SUCCESS**: ESP8266, ESP32, Android, x86_64, Ruijie, Orange Pi Zero 3, One, PC, Zero, Zero 2, Zero 2W, PC Plus, PC2 and One Plus.
- Production APK import, production sign handoff, update bundle, v0.4 browser/Android/x86/Orange Pi/Ruijie/ESP simulations, candidate gate and prerelease/release publishing were **SKIPPED**.
- Focused hardware lab [#44064436574](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064436574), job **133974328430**, remained **SUCCESS** at the same exact PR head: 28/28 pending-attempt marker cases per board (56/56 total), with inherited source-extracted hardware suites passing.

The Full run is not green. The target builds are CI evidence only; they do not establish physical flash durability, coin pulse acceptance, financial correctness or release readiness. No QA-owned file was changed.

## Follow-up: quarantine prefix integrity after append (2026-11-17 UTC22)

### Proven gap and test-first reproduction

The prior append verifier checked the resulting file size and byte-for-byte equality of the newly appended suffix, but it did not revalidate the already-existing quarantine-log prefix after the append operation. A same-size write fault could therefore alter an older record while leaving the new suffix exact; the old verifier would not detect that prefix change before quarantinePending() attempted to clear pending state.

- Test-only commit: [30a6d4c](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/30a6d4cc4f651735f592b0267f479e4b5481477f).
- Expected RED: [run #44192438813](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44192438813), job 134425056308: scenario 35 failed on both ESP32 and ESP8266 when the fake filesystem changed the first byte of the pre-existing log while preserving the appended suffix.

### Firmware correction

Source commit [9aca2ce](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9aca2cedbf34d42a0257482757682eca81e810f5) updates both sketches:

- inspectQuarantineLog() computes a CRC32 fingerprint while validating the complete existing log.
- After append, the verifier rereads the pre-existing prefix and compares its CRC32 before checking the appended suffix byte-for-byte.
- A prefix mismatch, short read, seek failure, size mismatch or suffix mismatch makes the append fail closed; quarantinePending() retains pending state and latches recovery.

CRC32 here is an accidental-corruption detector only. It is not cryptographic authentication, a protected witness, or proof of flash durability across power loss. The new guard adds a second linear read of the existing log (bounded by QUARANTINE_MAX_BYTES); target build and performance review remain required.

### Exact-head evidence

- Harness correction commits: [4259398](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4259398e3a7a745a20846318e78134b18f0b3663) and [e63df63](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/e63df63ff346897d470ee8c2de1951b135f792a2).
- Focused quarantine/readback [run #44193079025](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44193079025), job 134427284875, completed SUCCESS at exact test head e63df63ff346897d470ee8c2de1951b135f792a2: 36/36 source-extracted scenarios per board, 72/72 total; 12/12 safety helper parity; fail-open parity mutation rejected.
- Relay output [run #44193079017](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44193079017), job 134427284634, completed SUCCESS: 48/48 per board; polarity and poll-inhibit mutations rejected.
- Full PR build [run #44193079274](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44193079274) remains in progress at checkpoint. The separate push-triggered full run [#44193064334](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44193064334), validation job 134427394165, FAILED at the QA-owned legacy “Missing poll signature check”; do not restore positive poll admission to satisfy that stale fixture.

### Classification and next action

Focused evidence is SIMULATED / CI VERIFIED only. Physical LittleFS corruption, power-cut recovery, relay/coin acceptance, 150 controlled power cuts, and 30-device/24-hour soak remain NOT TESTED. No hardware acceptance or production readiness is claimed.

- PHX-QA: replace the obsolete positive poll-signature assertion with the approved default-deny expectation and independently rerun Full validation at the final exact head.
- PHX-MASTER: keep #317/#318/#283 stack selection under coordination; no cross-branch transplant is implied.
- PHX-HARDWARE: retain this bounded prefix-integrity guard and await exact target-build outcomes; do not enable coin dispatch or clear financial state without the CORE receipt/disposition contract.


## Follow-up: authoritative hardware stack selection (2026-11-18 UTC00)

**Disposition:** PHX-HARDWARE recommendation submitted to PHX-MASTER for ACK. This is a stack-selection proposal, not merge, release, or deployment authority. The update is documentation-only; no firmware or QA-owned test source changed.

### Recommended canonical sequence

`#314 → #315 → #317 → NEW child rebuilt from current #317 HEAD`

- **#314 → #315 → #317** is the recommended journal/quarantine/poll-inhibit lineage. #314 is the verified rotation-evidence parent; #315 adds the poll/quarantine fail-closed consolidation; #317 adds the exact pending-attempt marker match, exact-one pending-candidate rule, pending-record-first/attempt-marker-last clear, quarantine prefix+suffix readback, and the poll quiet-window/sample guard.
- The next child should be created from current #317 firmware source HEAD **`a166f91d6c790aa81ff98794038d76b39bc6562d`** only after PHX-MASTER ACK. It should carry the minimal ISR edge-sequence snapshot/fault-latch delta and its exact-source tests from #318. Suggested branch name: `phoenix/hardware-poll-edge-latch-on-317-20261118`.
- **Do not merge or cherry-pick the current #318 branch wholesale.** It is diverged from current #317 (51 commits ahead / 68 behind; compare status `diverged`; PR reports `mergeable=false`). Its base is the older #317 ancestor `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`, not the current #317 head.
- **#283 remains a parallel audit-only candidate**, not part of the canonical chain. It is main-based, lacks the pending-attempt marker and current poll-window/edge-latch sequence, and contains a QA-owned `tests/controllers.sh` modification that PHX-QA must review. Selectively port unique hardware fixes only after source-level reconciliation and QA review; never transplant the branch wholesale.
- **#239 → #254 remains a separate Phase-A / ControllerAuthV1Lab track.** #254 is a non-actuating configuration-authentication primitive, not a production signer, receipt authority, or permission to enable coin intake. #316 remains a separate poll-response fail-closed draft, not in the selected chain.

### Exact refs and source/test identities

| PR | Exact base | Current head | Source/test identity |
|---|---|---|---|
| #314 | `phoenix/hardware-clear-preflight-20261115` @ `6b8583b7b0b39314bce39666d1cdd0b8f84afe48` | `556adc20ef0cfd355089aff3b979c0169af79bdd` | Full run #43782088731 and quarantine-focused #43782088748 both PASS at exact head |
| #315 | PR #314 @ `556adc20ef0cfd355089aff3b979c0169af79bdd` | `84fe6b790139d147f330f13a40b3ae3e89a7042d` | Focused quarantine run #44054778537 / job 133941208330 PASS; Full #44054778555 / validation job 133941354361 FAIL at Controller protocol parity |
| #317 | PR #315 @ `84fe6b790139d147f330f13a40b3ae3e89a7042d` | `a166f91d6c790aa81ff98794038d76b39bc6562d` | Firmware source commit #9aca2ced; source/test follow-ups #4259398 and #e63df63. ESP32 blob `067c79405a6eb81a6c0b292b858191d3a131ed4f`; ESP8266 blob `2f6dce596368d74f51aa6ab6a66b6dde875511c1`; quarantine lab `789310363a1e5267c3cb4503b0273a6e5d633074`; poll-drain lab `c5da3bc6a4e8ad90b0757a656b97e7cb8e4e1d16`; pulse-capture lab `c0d07da8386d73b87a5fddcd68e0c838c0f50a33` |
| #318 | Older #317 base `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3` | `696e28ed4cd53b9189b78095b38aee973d774683` | ESP32 blob `7a24b1b643aa90c0056b5f7634d3c67e3ecb5a34`; ESP8266 blob `ebd1572cf82cd1c6ef2c5afbb7b4075533697440`; actual-loop lab `7068f5ec232440f50edc266dabecfb5be2c05c9e`; timeline guard `abb3cf918f9a07c6be870f9b2d819f206aa9752a`; workflow `6f37d08e1b1915b9147b8f0ec5f879bf6e245101` |
| #283 | main @ `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | `e8c6619ba97aa7ba1152e4c78b786842f7fa9180` | ESP32 blob `d86d94568c0de9a5be6648e8d83c219a9cc58c62`; ESP8266 blob `710572a1aae661cfa7ba3936f2170f921200150e`; append-readback lab `213d965875ef8cab6dd4ef4f0b8b64536a8a1388`; workflow `ba45c235be30c3992d273d6880cd43c2d9541d7c`; QA-owned controllers test blob `0f73e9024b98cfe5c6cc131f70a58cf50375d0fe` |
| #239 | `phoenix/light-verify-target-bound-relay-20261025` @ `7c156cb0e0dd4a2311de7e79c3ba7044037c0767` | `d83b715b116185107737fef721c2eece8feebf39` | Historical exact-head build #40815737447 and synthetic journal gate #40815737375 PASS |
| #254 | PR #239 @ `d83b715b116185107737fef721c2eece8feebf39` | `4054fbccd9b2a4ad0e5fe7cfca5a27aa629eed84` | Focused header lab #44019837617 / job 133826430041 PASS; Full #44019837616 / validation job 133826601985 PASS; non-actuating only |

### Exact current-head CI interpretation

- **#314:** Full target matrix and validation passed at `556adc20...` (run #43782088731); focused quarantine job #43782088748 passed.
- **#315:** Current head `84fe6b7...` has focused quarantine PASS, but Full run #44054778555 fails at QA-owned Controller protocol parity. All 14 target/platform jobs in that run passed; this does not make the overall workflow green.
- **#317:** Current head `a166f91...` has quarantine byte-readback run #44193392314 / job 134428369654 PASS and relay-output run #44193392313 / job 134428370250 PASS. Full run #44193392383 / validation job 134428525614 FAILS at Controller protocol parity; all 14 target/platform jobs passed. Poll-drain and post-poll pulse-capture labs exist in the branch, but no exact-current-head run for those two labs was observed in the latest action window.
- **#318:** Current head `696e28e...` poll-window lab #44180343686 / job 134382690530 PASS. Full run #44180343759 / validation job 134382856670 FAILS at Controller protocol parity; all 14 target/platform jobs passed. The focused lab extracts the real loop and simulates a pulse during the synchronous poll; it is not electrical proof.
- **#283:** Current head `e8c6619...` append-readback lab #44203456142 / job 134463233177 PASS. Full run #44203456152 has validation job 134463365181 PASS, 14 target builds PASS, and candidate gate PASS; production signing and publishing are skipped. This green result is not independent QA acceptance: the PR changes QA-owned `tests/controllers.sh`, and `littlefs_mount_failclosed_lab.py` plus `quarantine_clear_deny_lab.py` are not invoked by the current append-readback workflow.

### Revalidated #283 audit leads

- The previously reported unconditional `clearPending()` after a failed quarantine append is **not present** at current #283 HEAD: `quarantinePending()` returns immediately when `appendQuarantineRecord()` fails, before calling `clearPending()`.
- A distinct weakness remains in #283: `clearPending()` is still a void helper that clears RAM before checking/removing `/pending.dat`, `/pending.new`, and `/pending.bak`, and it does not verify removal. `quarantinePending()` has no active callsite in either sketch at this head, so this is a dormant helper risk, not an observed loop call.
- `response_sig` appears only in comments in the two #283 sketches; no active signature expectation is used to admit a poll response. Register/poll response data remains ignored and the branch stays default-deny.
- #317/#318 retain default-deny poll admission. The current main CGI producer does not publish the proposed `response_sig`; do not satisfy the QA parity failure by enabling unsigned/legacy positive poll admission. PHX-CORE must publish the canonical producer/consumer contract and PHX-QA must approve exact vectors first.

### Role boundary and blockers

- PHX-HARDWARE owns ESP32/ESP8266 firmware and hardware-specific source labs. PHX-QA owns canonical `tests/` and controller-parity assertions. PHX-CORE owns receipt/financial/poll producer contracts. PHX-MASTER owns the final stack selection and integration order.
- The current private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` is not available through the connected file-library surface. Only historical registry v5/v6/v7 and 2026-10-26 manifest/ledger snapshots were found. No Drive artifact upload, new folder, or new handover file was created; no private Drive IDs were copied into GitHub.
- The current root AGENTS.md and cloud policy keep Phoenix NO-GO. No positive coin admission, finance, relay, replay, witness, downgrade, signer, or production migration authority is granted.
- Physical acceptance remains NOT TESTED: 150 controlled power cuts, 30-device/24-hour soak, pulse-width/edge capture on real acceptors, relay/contact waveform, electrical pulse/recovery, and actual LittleFS flash durability.
- Durable accounting/replay, protected anti-rollback signer/witness, v1→v2 migration, target hardware acceptance, independent QA and release signoff remain BLOCKED/PENDING.

### Exact next actions

1. **PHX-MASTER:** ACK or revise the proposed `#314 → #315 → #317 → new ISR child` sequence. Do not treat the current #318 branch as mergeable.
2. **PHX-QA:** review #283's QA-owned `tests/controllers.sh` diff; wire the two uninvoked #283 labs if those source changes remain candidates; resolve the canonical Controller protocol parity assertion without weakening default-deny.
3. **PHX-CORE:** publish the canonical poll producer/consumer and event-bound receipt/disposition contract. Until then, positive poll admission and coin POST remain disabled.
4. **PHX-HARDWARE:** only after Master ACK, create a new child from current #317 firmware source HEAD and port the minimal #318 ISR edge-snapshot/fault-latch change plus its source-extracted lab. Re-run the exact full matrix and focused labs on that new head.
5. **Drive owner/authorized connector:** provide current private registry v11 and current manifest/ledger readback before any new artifact/folder or Drive mirror operation.

**Classification:** focused tests are SIMULATED / CI VERIFIED as listed; physical hardware acceptance is NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
