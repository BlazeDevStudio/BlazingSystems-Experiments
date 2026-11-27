# PHX-MASTER — live exact-head follow-up

**Updated:** 2026-11-18T17:39:33Z  
**Role:** PHX-MASTER · **Task:** #172 / #266 / #288 / COE #26  
**Status:** BLOCKED · **Release decision:** PRODUCTION NO-GO  
**Scope:** `coordination/phoenix/` only

## 1. Exact repository and coordination state

| Item | Live ref / state |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments current development branch | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch | `phoenix/master-coordination@97c895b699533ec4fd552f433c54210f808eb944` before this follow-up |
| Master PR #288 | OPEN / DRAFT, base main, 84 paths; all 84 are under `coordination/phoenix/` |
| COE default branch | `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; 205 changed paths; five workflows QUEUED / zero jobs |
| Ownership manifest | `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`; `DRAFT_REVIEW_ONLY`; PHX-MASTER target remains null |

The Experiments README and root AGENTS.md were read. COE README was read; COE root AGENTS.md returned 404. Cleanup issue #266 remains OPEN and contains an older 2026-10-31 source snapshot; its checklist is not proof of current cleanup completion. No mass cleanup or subsystem source edit was made.

## 2. HARDWARE — current child #326 and parent stack

- #323 remains the parent candidate at `988904e8bcd058b62a9fac4aa6319a9b7c5b2470`, based on #322 at `50d93e0de3d682550b6f02fb43484e76ad9c7e08`.
- Child #326 current PR/docs head is `58c558fb6a237935214621adc3dee65a10fe1a51`; its latest source/test commit is `28e13fc82a250821e815fd84b5fd61f1769e7106`.
- Exact source blobs at the source/test commit: ESP8266 `a4345f0a8338fdf4d921a7851fc2d537d582a42a`; ESP32 `921a3ef4b7f06e199b957ec33421460154109a8f`; source-extracted pulse lab `e6dfe3f5fdc0fea38357e7c3f87e1904179d6415`.

### What the new lab actually verifies

The lab extracts and compiles production `coinLineIdle()`, `canStartPoll()`, `applyOutputs()`, `coinLineQuietAfterInhibit()`, `beginPollWindow()`, `latchPollPulseFault()` and `sampleCoinPulseEdge()` from both sketches. Only the two persistence backends are fault-injected. It checks eight top-level scenarios and rejects six source mutations per board, including a missing edge latch, ignored save failure, missing persistent latch and missing output inhibit. The source prints `SIMULATED_ONLY=1` and explicitly sets physical coin, relay and power-cut acceptance to zero.

Both firmware paths set the recovery latch, disable insert mode, clear the active target and call `applyOutputs()` before attempting the NVS/EEPROM and LittleFS markers. **If both marker stores fail, the code explicitly establishes current-boot denial only; reboot durability is NOT established.** The same-chip NVS/EEPROM fallback is not an independent anti-rollback witness, financial ledger entry or receipt.

### Current-head PR workflows

| Run | Result | Evidence |
|---|---|---|
| Quarantine/readback | SUCCESS | [44358712365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712365) |
| Relay/output polarity | SUCCESS | [44358712238](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712238) |
| Full BlazePwifi build | FAILURE | [44358712823](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712823) |

All three runs report PR head `58c558fb...`. The Full run checked out merge ref `7588d9e` and failed in validation at the inherited QA-owned `Missing poll signature check` assertion in the ESP8266 sketch. All 14 firmware/platform targets and Android completed successfully; downstream simulation, update, candidate, signing and publishing jobs were skipped. This is not Full acceptance. Do not add a synthetic signature or weaken firmware default-deny; PHX-QA owns replacing the positive-presence fixture with negative behavior tests, while CORE owns the producer/consumer contract.

Other open Hardware candidates remain separate: #317 `fce915c1...`, #321 `4c54d629...`, #322 `50d93e0d...`, #324 `8e7f0220...`, and #325 `f66b45ec...`. Their focused labs pass, but their Full builds fail at the same QA-owned poll-signature fixture. #325 is on a separate cleanup base. No canonical stack has been selected or composed; do not infer that one candidate's focused PASS transfers to another SHA.

## 3. RELEASE — current candidate and infrastructure gate

- Experiments #291 is `691ed55dbe39a79a88eac45f6eebff81cee5e628`; [44353380470](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44353380470) passed its scoped Windows build/handover. Privileged publisher was skipped.
- COE #31 parent is `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. COE #35 child is `36036c412d39e026d3c30c3e365efb9b188d769b`, OPEN / DRAFT.
- COE #35 shared/hardware validation [44358536870](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44358536870) SUCCESS: 102 tests, two intentional skips, both ESP compile jobs and all ten appliance profiles succeeded. Case-collision [44358536865](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44358536865) SUCCESS.
- Mandatory sandbox [44358536882](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44358536882) FAILS CLOSED: 13/13 host-preflight tests pass, then the runner reports bubblewrap is not installed and exits 125. Namespace and packaging steps are skipped. No privileged install or unsandboxed fallback is permitted.
- COE #44 remains a separate, nonmergeable Release candidate at `1736b379f790896f6a744ad2f3ac3c5f1f5de3bc`, based on stale parent `0b01594d...`; its shared packaging run [44294927062](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294927062) fails an outdated Bubblewrap-workflow expectation. PHX-RELEASE must reconcile it against the current #35 parent; Master did not edit it.

## 4. Other role and COE candidate reconciliation

| Owner | Current PR/head | Current bounded CI observation |
|---|---|---|
| CORE | Experiments #252 `c82705f2...`; COE #29 `d0830332...`; COE #45 `9d76a134...` | #252 [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; #29 [43653906676](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653906676) / [43653906675](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653906675) PASS; #45 [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) / [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) PASS |
| RENTAL | Experiments #289 `68928774...` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) / [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) PASS, scoped |
| PISONET | Experiments #255 `d01fd164...`; COE #28 `b21b0461...`; COE #30 `4897348d...` | #255 [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; #28 [43632393888](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43632393888) PASS; #30 [43653415598](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598) PASS; native COM acceptance remains unverified |
| QA | Experiments #290 `5c29d159...`; #292 `75a3f66d...`; COE #32 `29b6fe08...` | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS for Pisonet scope; #292 no runs returned and is nonmergeable; #32 [43653540607](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653540607) PASS |
| COE candidate | #27 `009f70cc...` | [43079646393](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646393) and [43079646264](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646264) PASS, candidate only |
| RELEASE parent | COE #31 `59ed44d0...` | Shared [44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) and case [44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) PASS; sandbox [44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) FAIL |

These are scoped candidate checks, not combined destination acceptance or production evidence. CORE remains read-only to PHX-MASTER; the separate CORE continuation retains implementation ownership.

## 5. Destination, registry and governance gates

COE #26 is unchanged at `b382d233ff06c8791b1028bed3c617cc7b670d12`, five queued workflows and zero jobs. The previous exact-tree audit remains applicable: source/destination firmware blobs differ, 17 source Hardware lab files are absent, the destination generic test has a different identity and positive poll-signature expectations, and license/NOTICE scope is incomplete. No copy, move, overwrite or migration is proposed.

The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections could not be read: no Google Drive connector is exposed, and a complete 1,422-item Library metadata scan found only registry snapshots v3–v7 and the older unversioned file. Those are not substitutes. No private identifiers or registry contents were copied to GitHub.

Experiments main, current development and COE main branch objects report `protected=false`; the two repository rulesets lists are empty. Master branch protection was not independently confirmed. No protection settings were changed. Repository administrator must configure and independently verify required protection and status checks.

## 6. Verification and next owner actions

- **Source inspection:** completed for current Master docs/manifest, current #326 source/test, #35 source/CI, #26 destination state and current role PR heads.
- **Actual CI:** the linked GitHub Actions runs above were inspected; their conclusions are scoped exactly as stated.
- **Master local suite:** NOT RUN. No local source checkout or local test execution was performed in this activation.
- **Physical tests:** NOT TESTED. No GPIO, relay, coin, power-cut or soak test was invoked.

Next actions:
1. **PHX-QA:** replace the stale positive poll-signature fixture with negative default-deny tests; independently review #326 at its current source/test SHA.
2. **PHX-HARDWARE:** continue the two-store failure/reboot-durability analysis on its owned branch; do not claim durability when both stores fail.
3. **PHX-RELEASE / infrastructure:** provide an authorized bubblewrap-capable runner; reconcile COE #44 against the current #35 parent.
4. **COE integration owner:** keep #26 blocked until exact per-file source blobs, licenses/notices, test identities, import completeness and same-SHA CI are independently reconciled.
5. **Repository administrator / registry custodian:** verify protections and restore authorized private v11/newer-correction access.

**PRODUCTION NO-GO:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
