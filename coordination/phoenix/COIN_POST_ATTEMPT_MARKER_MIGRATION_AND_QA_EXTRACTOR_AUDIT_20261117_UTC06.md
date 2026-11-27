# PHX-MASTER — Coin POST attempt-marker migration and QA extractor audit

**Snapshot:** 2026-11-17T06:35:30Z  
**Role:** PHX-MASTER  
**Disposition:** BLOCKED / DRAFT / PRODUCTION NO-GO  
**Scope:** coordination/phoenix/, architecture contract, source-to-destination provenance and evidence reconciliation only. No subsystem source, QA harness, destination code, firmware, payment state, or private registry was changed.

## 1. Exact repository and candidate refs

| Ref | Exact SHA / state |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master draft PR #288 before this commit | `7616a3d5de69f4e6d7d9905fc91d0c7500bdfd68` |
| HARDWARE draft PR #315 | `c1db0a567500302921c0561bcd31446f12767372` |
| Separate HARDWARE draft PR #316 | `888e6941e3a7a81641682c23d937f97d8117d2ea` |
| QA draft PR #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration draft PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 remains open/draft, base `main`, with 47 changed files; all 47 are under `coordination/phoenix/`. `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, with source_ref pinned to Experiments main and destination pinned to COE PR #26. The newer HARDWARE #315 branch is a separate owner-controlled candidate, not a new source_ref in that manifest. No relocation is authorized.

## 2. Exact firmware blob and mode comparison

| Board | Current HARDWARE #315 source blob | COE #26 destination blob | Source / destination mode |
|---|---|---|---|
| ESP8266 | `35bc5b20a3121a7b5dbe0b201dcbbf5d67fda595` (40,984 bytes) | `c8be98f72596681e36a3ad1f8939bf8046c96887` (18,394 bytes) | `100644 / 100644` |
| ESP32 | `5b4484443846c5ec916cdee4125dbd8aa1d3e556` (40,728 bytes) | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` (18,505 bytes) | `100644 / 100644` |

Neither pair is byte-identical. These are different implementations and histories; do not overwrite either side or treat the target as a completed source migration.

## 3. P0 — current source has a durable one-shot POST marker; COE candidate does not

At current #315 source, both sketches persist `/pending.attempt` bound to the pending pulse count, nonce, and target before the first `post("coin")`. The implementation flushes/closes and reads the marker back through the bounded PendingRecord validator. The boot path treats matching, malformed, mismatched, truncated, and orphan markers as a reconciliation hold. Unknown/timeout replies do not trigger automatic replay. Pending data is removed before the attempt marker; a marker-removal failure leaves an orphan marker that blocks the next boot.

Source locations independently inspected:
- ESP8266 `markPendingPostAttempt()`: lines 169–227; boot marker reconciliation: lines 230–272; marker-last removal: lines 869–875; dispatch gate: lines 1082–1086.
- ESP32 `markPendingPostAttempt()`: lines 177–235; boot marker reconciliation: lines 238–280; marker-last removal: lines 326–332; dispatch gate: lines 1019–1023.

COE #26 destination sketches have **zero** `/pending.attempt`, `pendingPostAttempted`, and `markPendingPostAttempt()` references. They therefore do not contain this one-shot reboot/replay fence. This is a financial-integrity migration blocker even if the poll/configuration differences below are separately repaired.

The source-owned `pending_attempt_marker_lab.py` blob is `bb964c34c62726e0261ea15702b82e14850383a2`. It covers unattempted eligibility, one-shot behavior, post-reboot denial, mismatched/corrupt/truncated/orphan markers, open/write/readback failures, RAM-only pending denial, delete ordering, and partial-clear failures. The exact focused CI log reports 19/19 source-extracted cases per board (38/38 total); this is fake-LittleFS host simulation, not physical flash/power-cut acceptance.

## 4. Existing P0 mismatches remain in COE #26

### 4.1 Remote configuration is still response-authorized

In both current #315 source sketches, `applyRemoteConfig(` occurs once (the dormant function definition only); `acceptPollResponse()` defaults `signatureOk=false`. The owner handover explicitly keeps the mutator dormant pending a separate configuration-authentication contract and CORE/QA vectors.

In each COE #26 destination sketch:
- `applyRemoteConfig(` occurs three times (definition plus register and poll call sites);
- `bool sigOk=true` occurs twice;
- keyless positive register/poll responses can reach the mutator because verification is conditional on a configured key.

A register/poll admission signature does not bind the complete returned configuration object. Do not reuse it as configuration authorization.

### 4.2 Quarantine evidence can still be deleted by the destination

At current #315 source ESP8266, POST `/quarantine/clear` returns HTTP 403 with an explicit preserve/reconcile message and does not remove `/quarantine.log`. At COE #26 ESP8266, the same route removes `/quarantine.log` and returns HTTP 200. The current #315 ESP32/ESP8266 owner behavior is deny/no-delete; the COE staging still exposes the destructive behavior.

No request was sent and no file was deleted during this audit.

## 5. Test identity and licensing/import completeness

The current #315 source tree includes dedicated hardware-owned labs for the pending-attempt marker, pending journal recovery, pending write/readback, quarantine readback, mount fail-closed, coin POST gate, poll-response fail-closed, keyless-authority RED, and register-config fail-closed. The COE #26 Hardware subtree has only `Hardware/tests/test_firmware_hardening.sh` (blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`). That script checks string presence, brace balance, nonce text, and a synthetic SHA-256 construction; it does not import the current source marker labs or assert keyless configuration denial, quarantine HTTP 403/no-delete, or reboot marker behavior.

No Hardware-scoped LICENSE/NOTICE file is present under COE `Hardware/`. The source product has `experiment/openwrt/BlazePwifi/LICENSE` blob `1ee55b94183417be977ca287cd7391f9a6f7e721`; the absence of a Hardware-local notice is a scope/provenance question for the integration owner, not a finding of infringement. No license conclusion is inferred.

## 6. Exact-head CI and QA extractor failure

- Focused #315 run [44030492133](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44030492133), job `133860976524`: **SUCCESS** at exact PR head `c1db0a567500302921c0561bcd31446f12767372`. It reports 34/34 source-extracted host scenarios, attempt marker 19/19 per board (38/38 total), and the other focused fake-LittleFS/poll/register suites. Physical coin acceptor verified = 0; actual flash/power cuts NOT TESTED.
- Full #315 run [44030492146](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44030492146), validation job `133861082663`: **FAILURE** at the same exact PR head. The job log reports undeclared `pendingPostAttempted`, `acceptPollResponse()`, and `markPendingPostAttempt()` in both extracted board harnesses. ESP32, ESP8266, Android, and returned platform build jobs passed; validation did not. Signing, production import, candidate simulation and publish jobs were skipped.
- The failing QA-owned extractor at base `556adc20ef0cfd355089aff3b979c0169af79bdd` is blob `b11f34d8bb5e492a793ca34b23e930c267fb961e`; it contains no `acceptPollResponse()`, `pendingPostAttempted`, or `markPendingPostAttempt()` extraction/declaration. This is the confirmed harness mismatch. PHX-MASTER did not modify QA-owned tests.
- COE #26 has eight workflow records at exact head `b382d233...`; all eight remain QUEUED with no conclusion (runs 43096752609, 43096752632, 43096752800, 43096752563, 43096752557, 43096746202, 43096746248, 43096746194).
- Master #288 has no PR-triggered workflow runs returned for its current head.

## 7. Current role/CI snapshot

| Role | Current draft | Exact head | Bounded CI observation |
|---|---|---|---|
| MASTER | #288 | `7616a3d5...` | No PR-triggered runs |
| CORE | #252 | `c82705f2...` | Run 42698139210 SUCCESS (scoped) |
| RENTAL | #289 | `68928774...` | Runs 43653329235 and 43653329229 SUCCESS (scoped) |
| PISONET | #255 | `d01fd164...` | Run 42462978704 SUCCESS (scoped) |
| HARDWARE | #315 | `c1db0a56...` | Focused SUCCESS; Full validation FAILURE |
| HARDWARE (separate) | #316 | `888e6941...` | Focused SUCCESS; Full validation FAILURE; keep separate pending owner reconciliation |
| QA | #292 | `75a3f66d...` | No PR-triggered runs; base is stale relative to current Master |
| RELEASE | #291 | `2c4edff2...` | Run 43744993487 SUCCESS; publisher job SKIPPED |
| COE integration | #26 | `b382d233...` | Eight queued workflows; no conclusion |

These scoped results do not establish combined integration, independent QA, hardware acceptance, or release readiness.

## 8. Required owner actions

1. **PHX-QA:** update the canonical source extractor/harness to include the exact current state and helper dependencies (`pendingPostAttempted`, `samePendingRecord()`, `markPendingPostAttempt()`, `acceptPollResponse()`) for both boards; reproduce the current failure and rerun Full validation at the current #315 SHA. Keep the QA-owned files on the QA branch.
2. **PHX-CORE:** review the marker-before-network semantics, server receipt idempotency, and operator reconciliation for power loss after marker commit but before request transmission.
3. **PHX-HARDWARE:** continue owning #315 and provide exact-head evidence; do not compose #316 without an explicit owner decision.
4. **COE integration owner:** keep #26 draft; reconcile the exact firmware blobs, import the corresponding negative tests only after owner review, resolve license/notice scope, and obtain completed exact-head CI before proposing a move.
5. **Registry custodian:** restore authorized access to the canonical private Drive v11 registry and newer corrections. No substitute Library checkpoint was treated as canonical and no private registry contents were published.

## 9. Execution classification and production gate

**Performed:** live GitHub issue/PR/branch/tree/file inspection; exact source/destination blob and mode comparison; exact-head Actions metadata/job/log inspection; bounded source assertions; Master-owned documentation/contract update.  
**CI executed by GitHub:** focused #315 host/fake-LittleFS labs passed; Full #315 validation failed as described.  
**Not performed:** local clone or Master Python suite (clone failed because the runtime could not resolve github.com), physical flash, native coin/relay tests, 150 real power cuts, 30-device/24-hour soak, protected signer provisioning, independent anti-rollback witness, real payment, or financial migration.

**PRODUCTION NO-GO remains mandatory** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak, and owner-authorized release gates all have independently verified evidence.
