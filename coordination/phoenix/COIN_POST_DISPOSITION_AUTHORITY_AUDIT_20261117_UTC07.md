# PHX-MASTER — Coin POST disposition authority and migration audit

**Snapshot:** 2026-11-17T07:35:46Z  
**Role:** PHX-MASTER  
**Disposition:** BLOCKED / DRAFT / PRODUCTION NO-GO  
**Scope:** Master-owned coordination, architecture contracts, source/destination provenance and evidence reconciliation only. No subsystem source, QA harness, COE runtime, payment state, secret, hardware or private registry was changed.

## 1. Exact refs re-read

| Ref | Exact SHA / state |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master draft PR #288 before this audit | `c121d651919c4099390d0a78c4cc0e8179e0c3ca` |
| HARDWARE draft PR #315 | `4afc7c8bd8ea410049f1da7bc962bfc989b4ba1b` |
| Separate HARDWARE draft PR #316 | `888e6941e3a7a81641682c23d937f97d8117d2ea` |
| Earlier HARDWARE draft PR #283 | `a87567291e80006f3f30cea81fc20e8b299b95e8` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration draft PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 remains open/draft on `phoenix/master-coordination`, based on Experiments `main`. The role routing manifest remains `DRAFT_REVIEW_ONLY`; its source_ref is the historical/default main snapshot, not a blanket authorization to import newer owner branches.

## 2. Exact Hardware source/destination blob and mode comparison

The commit trees were fetched recursively at the exact #315 and COE #26 heads; neither tree response was truncated.

| File | Current #315 source blob | COE #26 destination blob | Mode | Size (bytes) |
|---|---|---|---|---:|
| ESP8266 `BlazePwifiVendo.ino` | `e47d392e5fd3724c414e4ec50b3cb74658047c31` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | `100644 / 100644` | `41851 / 18394` |
| ESP32 `BlazePwifiVendo32.ino` | `5de92f01990bd551e4c9dd063ff0eb0572a301e8` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | `100644 / 100644` | `41595 / 18505` |

Neither source/destination pair is byte-identical.

The current source ESP8266 poll lab is `poll_response_failclosed_lab.py`, blob `84275ece076295387e468da25df506fda9ff3bfb`, mode `100644`. COE `Hardware/tests/` contains only `test_firmware_hardening.sh`, blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`, mode `100755`; it does not import this source lab or the current event-disposition cases.

## 3. P0 — current owner source intentionally denies every unapproved coin POST disposition

Both current #315 sketches contain the same `coinPostDispositionVerified(response, nonce, target, pulses)` function. It currently returns `false` unconditionally because the endpoint is plain HTTP and PHX-CORE has not published an approved event-bound signed receipt/disposition contract. This is an intentional fail-closed hold, not a completed receipt implementation.

The source call path is:

1. `markPendingPostAttempt()` writes, flushes/closes and reads back the attempt marker bound to the pending event.
2. Only after that preflight does the firmware send `post("coin")`.
3. The response is passed to `coinPostDispositionVerified()`.
4. Because verification currently returns false, firmware sets `journalRecoveryRequired=true`, keeps the pending evidence and attempt marker, applies the fail-closed outputs, and denies automatic replay.
5. Neither raw `ok:true`, raw `ok:false`, nested `receipt.ok:true`, empty body, HTTP error, timeout or an unauthenticated text reason is permitted to clear the pending event or authorize quarantine disposition.

The current source lab tests raw positive, raw negative, nested-positive and empty response cases as DENY. It also tests the poll/coin admission helpers. These are source-extracted host tests, not physical coin/flash evidence.

## 4. COE #26 remains materially behind the current source

At the exact destination blobs above, both COE sketches have:
- zero `coinPostDispositionVerified` references;
- zero `pendingPostAttempted`, `markPendingPostAttempt` or `/pending.attempt` references;
- three `applyRemoteConfig(` occurrences (definition plus response-driven call sites);
- two `bool sigOk=true` defaults.

The COE destination also retains the earlier response-driven remote-configuration and destructive quarantine-clear mismatches recorded in the UTC04/UTC05 audits. The destination Hardware test folder has one shell hardening script, not the source's current source-extracted marker, poll, register and disposition failure matrices.

No Hardware-local LICENSE/NOTICE was found in the candidate subtree during the prior exact-path review. License scope remains an owner/custodian question, not a legal conclusion. The PisoWiFi-only source-intake manifest does not prove Hardware import completeness.

**Migration decision:** keep COE #26 draft. Do not copy, overwrite, relocate, or promote either destination sketch. PHX-HARDWARE owns the firmware source; PHX-QA owns independent test verification; the COE integration owner owns destination staging; PHX-MASTER owns only this coordination/provenance record.

## 5. Exact-head CI and actual local tests

### HARDWARE #315

- Focused source-extracted run [44038469936](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44038469936), job [133886981567](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44038469936/job/133886981567): **SUCCESS** at exact head `4afc7c8...`.
- The log records coin POST disposition default-deny 4/4 per board, coin POST gate 10/10 per board, pending attempt marker 19/19 per board, and 34/34 source-extracted host scenarios. It explicitly reports `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.
- Full build [44038469823](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44038469823), validation job [133887096342](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44038469823/job/133887096342): **FAILURE**. The QA-owned poll-loop extractor omits `pendingPostAttempted`, `acceptPollResponse()`, `markPendingPostAttempt()`, `coinPostDispositionVerified()`, and `pollJsonTopLevelTrue()`. ESP8266/ESP32 and other listed target builds passed, but the full workflow is not green.
- Separate #316 remains open/draft: focused run 43972511337 success; full run 43972511250 failure. Do not compose or merge it independently.
- Earlier #283 run 43634101437 is a scoped success, not current-source acceptance.

### Other role CI, exact observed heads

| Role / PR | Exact head | Returned CI |
|---|---|---|
| CORE #252 | `c82705f2...` | 42698139210 SUCCESS |
| CORE #241 | `8aa2529a...` | 40813818877 FAILURE |
| CORE #248 | `a1f80f30...` | 40882042148 FAILURE |
| RENTAL #240 | `a7d113fb...` | 40910311141 and 40910311159 SUCCESS |
| RENTAL #287 | `a4fffd01...` | 43754089203 SUCCESS |
| RENTAL #289 | `68928774...` | 43653329235 and 43653329229 SUCCESS |
| PISONET #255 | `d01fd164...` | 42462978704 SUCCESS |
| QA #267 | `ff536799...` | 41452247439 SUCCESS |
| QA #279 | `8f476ef0...` | No workflow runs returned |
| QA #292 | `75a3f66d...` | No workflow runs returned |
| RELEASE #242 | `734b89d9...` | 40882814472 SUCCESS |
| RELEASE #291 | `2c4edff2...` | 43744993487 SUCCESS |
| COE #26 | `b382d233...` | Five integration workflows QUEUED |
| COE #29 | `d0830332...` | 43653906676 and 43653906675 SUCCESS |
| COE #28 | `b21b0461...` | 43632393888 SUCCESS |
| COE #30 | `4897348d...` | 43653415598 SUCCESS |

All listed successes are scoped software evidence, not combined acceptance.

### PHX-MASTER local test execution

The current branch's `verify_source_intake_manifest.py` blob `f85c3005ba907c726d8270f10e0451b381e2a544` and `test_verify_source_intake_manifest.py` blob `c4b097930bf5deaebe0bf186b515f140161c1c93` were fetched from the exact pre-change #288 head and executed in the ordinary Python test runtime: **11/11 tests passed**. This is the targeted source-intake suite only; the full Master suite and PR-triggered Master CI were not executed/returned.

## 6. Required event-bound coin receipt/disposition contract

PHX-CORE must publish a canonical contract before firmware can accept any coin POST result. At minimum, the signed/MACed, domain-separated receipt must bind protocol version/domain, controller identity, key version, unique event/receipt ID, event nonce, target nonce, pulse count, server ledger epoch/sequence, freshness/expiry, disposition enum and reason. The approved cryptographic construction and canonical serialization must be specified by the owner and backed by golden vectors; do not substitute an ad-hoc SHA-256 concatenation or reuse the poll/register admission signature.

Server processing must be idempotent for the same event ID and return the same authoritative receipt without duplicate credit. The controller must verify signature, identity, key version, event/target/pulse binding, freshness, sequence and disposition. An accepted receipt may clear pending state only after the authoritative receipt and resulting state are durably committed. A rejected receipt may transition to durable quarantine only after its authenticated negative disposition is persisted with reconciliation evidence. Any missing, malformed, unsigned, invalid, stale, mismatched, timed-out or ambiguous response keeps the attempt marker and journal-recovery hold; no automatic replay, credit, relay admission or evidence deletion is permitted.

This contract does not authorize remote configuration; configuration remains a separate authorization domain. The contract is a Master-level fail-closed requirement pending PHX-CORE design and independent PHX-QA review, not an implementation or production approval.

## 7. Registry, policy and physical-evidence limitations

The exact private Drive registry and newer corrections were not retrievable through the available connected tools; the exact-name Library search returned older snapshots only. No older registry was substituted, and no private contents were copied into this public report. The available tool surface exposed no general Google Drive file reader; Descript Drive media tools are not a substitute. The Cloud Artifact Policy and storage handover linked from root `AGENTS.md` also could not be retrieved through the available GitHub file reader. No Drive write or artifact claim was made.

Historical P0 issues #31, #32, #34 and #43 remain OPEN; coin pulse issue #177 remains OPEN. Protected signing/anti-rollback witness, crash-atomic financial state, reversible migration, independent QA, native acceptance, 150 real power cuts and 30-device/24-hour soak remain unverified. Production remains NO-GO.

## 8. Next owner actions

1. **PHX-CORE:** publish the event-bound authenticated coin receipt/disposition schema, idempotency rules, key/version/freshness semantics and positive/negative golden vectors.
2. **PHX-QA:** repair the canonical poll-loop extractor for the five missing dependencies; independently run both-board positive/negative disposition vectors at exact #315 head and verify durable hold behavior.
3. **PHX-HARDWARE:** keep the current default-deny hold; implement a verifier only after CORE contract approval and QA vectors. No owner source files were changed by Master.
4. **COE integration owner:** keep #26 draft; reconcile exact source/destination blobs, tests, import completeness, license scope and queued CI before proposing any move.
5. **Registry custodian:** restore authorized private Drive access and provide the current canonical registry plus newer corrections to the authorized worker.

No merge, release, signing, firmware flash, physical test, secret provisioning, real payment or production migration occurred.
