# PHX-MASTER UTC21 — Hardware #327 drain-abort false-return audit

**Role:** PHX-MASTER  
**Scope:** `coordination/phoenix/`, architecture/interface contract, integration matrix, migration provenance only  
**No Codex:** confirmed  
**Disposition:** P0 owner correction required; PR #288 remains OPEN/DRAFT; production NO-GO

## Exact refs at the start of this Master update

| Ref | Exact SHA / state |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Current development/comparison branch | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Older development branch | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master branch / PR #288 head before this update | `943a13937ea0c29857fd4f53609533c21481cc34` |
| PR #288 | OPEN / DRAFT; base `main@f4e8a891...`; 88 changed paths, all under `coordination/phoenix/` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; 205 changed paths; five workflows QUEUED / zero jobs |
| Ownership manifest | `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`; `DRAFT_REVIEW_ONLY`; PHX-MASTER target null |

## 1. New P0 finding: the ISR edge fence is missing on the false-return path

Current Hardware stack: #323 `988904e8bcd058b62a9fac4aa6319a9b7c5b2470` → #326 `58c558fb6a237935214621adc3dee65a10fe1a51` → #327 current head `b346eba3ebee228abcff03456deb7889f2d39144`.

The current ESP8266 sketch blob is `4d73c5dc451c29f2ffd64a5cb2d230cc84a78ed5`; ESP32 sketch blob is `ada9723c5f07879775284eb128a986ac865394f7`.

At the exact #327 head, the relevant source structure is:

```cpp
bool beginPollWindow(){
  if(!canStartPoll()) return false;
  pollIntakeSuspended=true;
  applyOutputs();
  if(coinLineQuietAfterInhibit()) return true;
  pollIntakeSuspended=false;
  applyOutputs();
  return false;
}
```

The caller snapshots `coinEdgeSequence` before `beginPollWindow()`, but the after-drain snapshot/latch is inside `if(beginPollWindow())`. Therefore:
1. An ISR edge can arrive during the quiet-drain sample.
2. The edge can make `coinLineQuietAfterInhibit()` return false.
3. `beginPollWindow()` clears `pollIntakeSuspended` and reapplies outputs before returning false.
4. The caller never compares the ISR sequence on this path.
5. If the short pulse ends before the next ordinary `digitalRead()`, `sampleCoinPulseEdge(false)` cannot reconstruct the lost edge; no pending pulse or sticky marker is created by this path.

This is a source-level race reproduced by the new source-extracted test, not a confirmed physical coin/customer event.

## 2. Exact-head test evidence

PR #327 changes seven paths. The current poll-loop lab blob is `c3e34297e62c34e2a459203b33bcc29e14405fc8`; it adds `injectDuringDrainAbort` and expects the ISR edge to create a sticky recovery marker before poll/output release.

| Workflow | Exact run | Job | Result |
|---|---:|---:|---|
| Quarantine/readback | [44404536230](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44404536230) | `135156120858` | **FAIL** — ESP8266 exact-source test expected exit 0, got 25 |
| Relay/output | [44404536459](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44404536459) | `135156122573` | **FAIL** — same ESP8266 exit-25 false-return case |
| Full BlazePwifi build | [44404536187](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44404536187) | `135156123737` | **FAIL** — inherited QA-owned `Missing poll signature check` |

The failed focused logs do not reach `POLL_ABORTED_DRAIN_ISR_EDGE_PERSISTED_PASS`. They stop on the ESP8266 case; the new false-return scenario is therefore **not** claimed PASS on ESP32. Earlier checks in those jobs did pass before the new case: dual-store/read-error scenarios, pending-journal/readback, coin POST deny, poll-window drain, coin-pulse capture, output polarity and output-enable sequencing. ESP32 boot-polarity subjob `135156121872` completed SUCCESS.

The Full run completed all 13 firmware/platform target jobs and Android successfully. Its validation job failed at the inherited positive poll-signature assertion; update bundle, simulations, candidate gate, signing and publishing were skipped. This is not Full acceptance.

## 3. Required owner correction

**PHX-HARDWARE owns the firmware and hardware-owned lab.** Keep the intake/output inhibit asserted until the ISR sequence has been reconciled for both helper outcomes. Reconcile the edge immediately after the drain helper returns, regardless of true/false result. If the sequence advanced, latch unresolved ingress and persist the deny marker before any release or HTTP poll. Only dispatch poll when the helper is ready and the sequence is unchanged. Preserve default-deny behavior.

**PHX-QA owns independent verification.** On both ESP8266 and ESP32, inject an ISR edge during the final drain/abort sample and let the pulse end before the next ordinary loop sample. Assert no HTTP poll, sticky recovery deny, marker persistence before release, relay/LED logically OFF, active target cleared, no pending credit, timestamp deferred and no hot retry. Add a mutation that removes false-return reconciliation and must fail. Replace the inherited positive poll-signature fixture with negative/default-deny assertions; do not add fake signatures to firmware.

**PHX-RELEASE owns build environment.** Pin ESP8266 core 3.1.2 or assert the resolved core version, because the separate §6.31 EEPROM whole-image read-failure analysis depends on that implementation.

## 4. Separate P0 remains open: full-image EEPROM read failure

The marker-only raw flash read is status-bearing, but `loadCfg()` still calls `EEPROM.begin(544)`, checks only the reported length, then reads the Config buffer. ESP8266 core 3.1.2 logs and ignores a failed initial `flashRead()`; an erased-looking buffer can enter the default-config path and commit the full image before the later marker-only check. The current dual-store lab does not execute the full `loadCfg()` / default `saveCfg()` path. Preserve §6.31 and require a fail-first whole-image regression with a pre-existing marker and cold-boot assertion. This is a source-level hazard, not confirmed physical data loss.

## 5. Cross-repository provenance: COE #26 remains blocked

Exact current firmware blobs:

| Artifact | Experiments #327 | COE #26 |
|---|---|---|
| ESP8266 | `4d73c5dc451c29f2ffd64a5cb2d230cc84a78ed5` | `c8be98f72596681e36a3ad1f8939bf8046c96887` |
| ESP32 | `ada9723c5f07879775284eb128a986ac865394f7` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` |

The source tree has 18 ESP32/ESP8266 Python board labs; COE #26 has zero corresponding Hardware Python labs. Its generic test blob `f921c56cecc19cab1989507b9b4ade1f45dac54e` still requires positive `response_sig` and `|poll|` strings. Workflow blob `fe79adbdb3745a22c5ef6d1f0c87c868b7785793` invokes that generic shell test and Shared tests, not the source-extracted board labs. Five #26 workflows remain QUEUED with zero jobs.

The source project MIT LICENSE matches COE `Pisowifi/LICENSE`, but the intended scope over sibling `Hardware/` remains unresolved. Source root NOTICE exists; COE root NOTICE is absent. Vendor NOTICE parity does not resolve the project-root/Hardware scope. No destination file was changed, copied, moved, overwritten or rebased.

## 6. Other role reconciliation and governance

- CORE #252 `c82705f2...`: scoped CI [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS; CORE remains outside Master scope.
- RENTAL #289 `68928774...`: [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS.
- PISONET #255 `d01fd164...`: [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM acceptance not established.
- QA #290 `5c29d159...`: [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS for build/handover only; native COM lab not invoked. QA #292 `75a3f66d...` has no runs and a stale Master base.
- RELEASE #291 `4e05350d...`: [44401735467](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44401735467) and [44401735492](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44401735492) SUCCESS, scoped; privileged publishing is not evidenced.
- COE Release #44 `582fd5d5...`: shared [44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309) and case [44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296) SUCCESS; mandatory sandbox [44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) fails closed because bubblewrap is unavailable.
- Cleanup issue #266 remains OPEN with stale historical PR pins. Branch-protection/ruleset state remains an administrator verification item.
- The private Drive registry v11 and newer corrections remain unavailable through the exposed connector/Library. Older v3–v7 snapshots were not substituted. No private IDs or contents were published.
- The automation inventory exposed a PHX-HARDWARE hourly task, but not an enabled task with the exact title “Blaze Production Continuation.” CORE remained untouched regardless; no competing CORE work was started.

## 7. Verification and next step

**Source/tree inspection:** current PR #327 source, test, workflow, PR metadata and COE #26 destination blobs inspected.  
**Actual CI:** the three exact-head runs above completed with the stated failures/successes.  
**Master Python suite:** NOT RUN.  
**Master PR CI:** no runs returned.  
**Physical hardware / power-cut / 30-device soak:** NOT TESTED.

Next: PHX-HARDWARE fixes the false-return ISR reconciliation on the existing #327 branch; PHX-QA independently reruns the same corrected SHA on both boards and repairs the negative poll fixture. Master then refreshes the exact-head matrix and COE provenance. **PRODUCTION NO-GO.**
