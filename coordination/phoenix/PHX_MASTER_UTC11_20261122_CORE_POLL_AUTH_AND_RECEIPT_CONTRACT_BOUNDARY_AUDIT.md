# PHX-MASTER UTC11 — CORE poll-auth and coin-receipt contract boundary audit

**Checkpoint:** 2026-11-22T11:08:00Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** `coordination/phoenix/` only; all subsystem source and COE destination refs are read-only  
**Execution:** Strict NO CODEX. Connected GitHub reads and bounded static source assertions only.  
**Disposition:** OPEN / DRAFT / UNMERGED; PRODUCTION NO-GO.

## 1. Exact live repository references

- Experiments `main`: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Current v0.6 audit/development candidate ref: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Legacy branch literally named `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`. Do not conflate the two branch names.
- PHX-MASTER branch before this update: `phoenix/master-coordination@c907a34a242b41b98f8d1137547b6812d98f8178`.
- COE `main`: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT / FROZEN.
- Machine-readable `OWNERSHIP_ROUTES.json`: `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`.
- Cleanup issue #266 remains OPEN, 0/7 tracks complete.
- PR #288 before this update: OPEN / DRAFT / UNMERGED, 166 changed paths, all under `coordination/phoenix/`; no PR-triggered workflows and no combined status entries.

## 2. CORE producer: current controller response is nested, authenticated, and deny-only

CORE PR #252 is OPEN / DRAFT / UNMERGED at `c82705f2de865c89ab733b10efa84f26f56a5cc4`.

Exact source blobs:
- `controller.sh`: `1a820416051a7af5462841b191b02630aa87781f`.
- Vendo CGI: `16eb4105c15569dfd77b19a276ee05a25768083e`.
- Response-auth test: `26ed968c9b19ef00e4687da40b71bed94df74f01`.
- Dedicated workflow: `1b22086d491cf39402c70f7d24523e08d882eb2e`.

The current `bp_controller_lab_response_v1` producer uses domain `blazepwifi-controller-response-v1`, HMAC via `bp_rental_hmac`, and a canonical tuple bound to action, controller ID, request nonce, policy revision/hash, insert bit, target nonce and expiry. Its nested `config_auth` object includes `admission_allowed:false` and `signature`.

- `register|ping` returns `config_auth` nested beside the controller object.
- `poll` returns legacy top-level `insert` / target / expiry fields plus nested `config_auth`; the source comment explicitly says new hardware must ignore legacy `insert` as authority and observe `admission_allowed=false`.
- Separate member snapshot/auth/mutation replies also contain `response_sig` fields. Those member-operation signatures are not a top-level poll authorization response and must not be substituted for it.

The source-linked response-auth test validates `reply["config_auth"]` and contains nine adversarial host cases. The dedicated workflow is configured to run that test, but the exact-head run list for #252 contains only the general `BlazePwifi build` run; its validation log has no `v060_controller_response_auth_v1.py` or `PHX-G-CFG-AUTH` marker. Therefore this test is present in source but NOT verified as executed by exact-head CI.

## 3. Hardware consumers: deliberately fail-closed

HARDWARE #327 is OPEN / DRAFT / UNMERGED at `21315a8ad024b1e5341bf3e2b3998c67d23d5f34`:
- ESP8266 sketch blob `c2aa71963eaa0288721f0bb13cff771aaaabc42f`.
- ESP32 sketch blob `7ffb7b534c7163678726902946a17b04992950a0`.

At the ESP8266 source, `coinPostDispositionVerified()` returns false; `acceptPollResponse()` sets `insertMode=false`, clears `activeTarget`, and returns false. The pending event and one-shot attempt marker remain protected. This is a deliberate deny-only state, not a missing implementation that Master may patch.

HARDWARE #340 is a separate OPEN / DRAFT / UNMERGED child of #283 at `20c5889fc4ceeb95ab0b05c7c11952704caff36b`:
- ESP8266 sketch blob `fdd4e45b2346957ce5f55ae529734854e4c78c7f`.
- ESP32 sketch blob `6a6b1c826872af9f21721fb82cbc5754785c7888`.

Its register/ping path is discovery only; its poll path calls `denyRemoteControl()` before and after the request and ignores all response fields. Its Full candidate CI passes, but it does not implement positive poll admission.

HARDWARE #341 remains a separate child of #339 at final docs head `a655d0b5c144535a3ad8e48009fc4498318ff5e3`, source/test SHA `56ce713088fb5dccda5fb5434416fc5b6c75388a`. It is a host-lab lexical fixture port, not a firmware authentication change.

## 4. COE #26 destination consumer is a legacy, incompatible candidate

At exact COE #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`:
- ESP8266 sketch blob: `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- ESP32 sketch blob: `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- `Hardware/tests/test_firmware_hardening.sh` blob: `f921c56cecc19cab1989507b9b4ade1f45dac54e`.

Both destination sketches read top-level `response_sig` and derive the legacy `|register|` / `|poll|` keyed-SHA256 tuple. The destination hardening test explicitly requires `response_sig`, `|register|`, and `|poll|`. That is not the current CORE #252 nested `config_auth` response contract. COE #26 has five queued workflows and zero jobs, so there is no destination CI evidence resolving this mismatch.

This is a source-identity and interface incompatibility finding, not a runtime claim. Do not copy or promote the COE #26 firmware/test blobs as if they were compatible with the current CORE producer.

## 5. COE #45 receipt contract is separate from poll authentication

COE CORE PR #45 is OPEN / DRAFT / UNMERGED at `9d76a134c1f6512aa40c20ec4d247306a71a8cce`:
- Contract blob: `cadc8057976f8a5ebb8c0e2af3bedbea7425d1f8`.
- Golden vectors blob: `ff4c7be5b779abbd0315bb8917297e2875cdfb4a`.
- Test blob: `20458f793b00b563b526fbabbcf86a80f4d78770`.

The document explicitly labels this `CONTRACT CANDIDATE / TEST VECTORS ONLY / RUNTIME DENY`. It defines a separate `blazepwifi-coin-receipt-v1` HMAC-SHA256 domain/key and event-bound receipt fields. It is not the controller register/poll response contract and must not reuse the existing `response_sig` construction.

Exact-head CI run [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) ran `coin_receipt_contract_v1.py` and logged `COIN_RECEIPT_V1_GOLDEN_PASS`. This verifies golden-vector logic only; it does not prove server/firmware runtime integration, key custody, durable receipt acceptance or physical behavior.

## 6. Exact-head CI reconciliation

| Role / PR | Exact-head evidence | Disposition |
|---|---|---|
| CORE #252 | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) general build PASS; dedicated response-auth test marker absent | Scoped build PASS; auth test NOT CI-VERIFIED |
| HARDWARE #327 | [Quarantine #45007220029](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45007220029) PASS; [Relay #45007220186](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45007220186) PASS; [Full #45007220017](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45007220017) FAIL at inherited `Missing poll signature check` | 14 target/platform jobs PASS; downstream candidate/signing/publication skipped |
| HARDWARE #339 | [Quarantine #44986635350](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635350) PASS; [Full #44986635417](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635417) FAIL at the same inherited gate | Owner source remains untouched |
| HARDWARE #340 | [Full #44983396262](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396262) PASS; six focused/full workflows PASS | Candidate CI only; consumer remains deny-only; signing/publication skipped |
| HARDWARE #341 | [Quarantine #45014156653](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45014156653) PASS; [Full #45014156658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45014156658) FAIL at inherited `Missing poll signature check` | 14 target/platform jobs PASS; simulations/candidate/signing/publication skipped |
| RENTAL #328 | APK identity #44782114384 and API21/API23 #44782114393 PASS; Full #44782114390 FAIL | Mbed TLS compatibility and handover freshness remain blocked |
| PISONET #255 | [Windows synthetic #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS | Native COM/device acceptance NOT TESTED |
| QA #290 / #292 | #290 Windows #43633486963 PASS; #292 has zero PR-triggered runs and stale base | QA owns current-base replay and fixture correction |
| RELEASE #291 | ESP32 compatibility #44894604453 PASS; Full #44894604464 and Windows #44894604466 FAIL | Mandatory handover freshness; publisher skipped |
| COE RELEASE #35 | Shared [#45014129009](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45014129009): 180 tests PASS / 2 intentional skips, then 10/10 profiles fail closed without approved site ULA /48. Sandbox [#45014128980](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45014128980): 33 host preflight tests PASS, then Bubblewrap absent / exit 125. | Release blocked |
| COE integration #26 | Five workflows QUEUED / zero jobs | FROZEN |
| COE CORE #45 | [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) golden receipt test PASS | Contract vectors only |
| PHX-MASTER #288 | No PR-triggered workflows; no combined status entries | Master suite NOT RUN |

## 7. Bounded static audit execution

Twelve assertions against the exact remote source blobs and one exact CI log were executed in this activation: **12/12 PASS**. They checked the CORE domain/deny field, nested `config_auth`, test source, Hardware deny-only consumers, COE #26 legacy consumer/test, COE #45 candidate status, and the exact golden-vector run marker.

These are source-inspection assertions, not firmware, product, CI or hardware tests. No product test was executed locally by Master. The full Master Python suite remains NOT RUN because no authenticated checkout/test workspace was established.

## 8. Master disposition and next owner actions

1. **CORE:** publish the canonical versioned controller register/poll response contract and exact producer golden vectors; ensure the dedicated `PHX-CORE-G` workflow executes on the exact #252 head. Separately publish/approve the coin receipt producer semantics; do not conflate the two domains.
2. **HARDWARE:** keep #327/#340/#341 deny-only until CORE's contract and QA's independent vectors agree. No Master source edit or test bypass.
3. **QA:** replace the inherited positive legacy poll-signature fixture with source-linked negative/default-deny tests now; only add positive vectors after the producer/consumer contract is approved.
4. **COE integration owner:** keep #26 frozen; any destination consumer change must be a separate owner-reviewed reimplementation with exact source/test/license/NOTICE provenance and exact-head CI.
5. **COE CORE:** retain #45 as contract-only until runtime implementation, key custody and durable receipt verification are independently evidenced.
6. **Registry custodian:** provide authorized access to private Drive v11 and newer corrections. Library search did not locate the canonical v11 file, and no Google Drive connector was exposed in this execution environment.
7. **PHX-MASTER:** run the full coordination suite when an authenticated checkout/test workspace is available.

No route promotion, staging, copy, move, overwrite, cherry-pick, rebase, merge, destination edit, release, signer provisioning, hardware flash, payment operation or physical test occurred. Keep production NO-GO until the independent signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, independent QA/native acceptance, 150 real power cuts, 30-device 24-hour soak and owner-authorized release gates are independently evidenced.
