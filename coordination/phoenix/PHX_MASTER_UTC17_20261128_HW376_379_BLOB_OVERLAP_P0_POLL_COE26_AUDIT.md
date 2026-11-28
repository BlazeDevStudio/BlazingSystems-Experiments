# PHX-MASTER UTC17 — HARDWARE ancestry/blob reconciliation, P0 poll order and COE #26 hold

**Observed UTC:** 2026-11-28T17:42:33Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repository provenance only.  
**Task ID:** none supplied by a GitHub task issue; none invented.  
**Audit input:** `phoenix/master-coordination@15fdc676ca922f371f34ca014c91dc392ee2a60a`.  
**Disposition:** BLOCKED / PRODUCTION NO-GO. Strict NO CODEX.

## 1. Live refs and coordination state

| Ref | Exact SHA |
|---|---|
| Experiments `main` (default) | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| active v0.6 audit foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master `phoenix/master-coordination` | `15fdc676ca922f371f34ca014c91dc392ee2a60a` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

- CONTROL PLANE [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) last Master checkpoint is UTC16 comment #7242694574. No 2026-11-28 UTC17 Master message existed before this run.
- Cleanup [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN / 0-of-7. P0 [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) remains OPEN.
- Master PR [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) is OPEN / DRAFT / UNMERGED at `15fdc676...`, base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, 719 ahead / 1 behind, 275 changed paths all under `coordination/phoenix/`. No PR-triggered workflow run exists for this Master head.
- Ownership manifest unchanged: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`.

## 2. HARDWARE #376–#379 exact ancestry and blobs

| PR | Exact current head | Base | State |
|---|---|---|---|
| #376 | `0f5968b232f411943c4be3a4d4911a0da4f83fff` | #356 at `0ea32d31` | OPEN / DRAFT |
| #377 | `95ace1236c2b3e4816515c372edd4853ceeed064` | #374 at `cfb19ed5` | OPEN / DRAFT |
| #378 | `3f67ba41dc3e087f868d3c57f6604e69f7a0e17b` | #377 branch at `95e54790` | OPEN / DRAFT / mergeable=false |
| #379 | `5ac75dbb53bc36abc161fb276b6e7e80534e9b28` | #378 at `3f67ba41` | OPEN / DRAFT |

### #376 vs #377
- Changed-file counts: 8 vs 14; four shared paths.
- Compare DIVERGED 290 ahead / 36 behind, merge base active v0.6 `2fbd2475`.
- Exact shared blobs: `PROJECT_HANDOVER.md` differs (`0fbbd392` / `0550730a`); `CHANGE_LEDGER.md` differs (`c609a4aa` / `fea23f49`); `CURRENT_STATE.md` differs (`2cd7af2b` / `be9c89f4`); the UTC16 #376/#377 reconciliation note matches (`79df6029`).

### #377 vs #378
- Compare DIVERGED 4 ahead / 2 behind, merge base `95e54790`; #378 base is two commits behind current #377.
- Four shared paths all differ: `PROJECT_HANDOVER.md` (`0550730a` / `14111131`), `CHANGE_LEDGER.md` (`fea23f49` / `117cae8f`), `CURRENT_STATE.md` (`be9c89f4` / `43e93d22`), `poll_preflight_inhibit_lab_cases.py` (`ef91b15f` / `02f965ff`).

### #378 vs #379
- #379 is four commits ahead of #378.
- Four shared paths all differ: `PROJECT_HANDOVER.md` (`14111131` / `ae7b72af`), `CHANGE_LEDGER.md` (`117cae8f` / `23d09251`), `CURRENT_STATE.md` (`43e93d22` / `fb4889a1`), `poll_preflight_inhibit_lab_cases.py` (`02f965ff` / `9b4afb22`).

**Owner action:** HARDWARE must reconcile #378 against current #377, preserve append-only history, then refresh #379's child base and exact-head CI. No Master rebase, force-push, merge or source edit.

### Exact-head CI
- #376: focused [#46164674619](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164674619), Mbed 3/3 [#46164674611](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164674611), Full [#46164674737](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164674737) PASS; signing/publication skipped.
- #377: Poll [#46164676430](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164676430) and Mbed 3/3 [#46164676331](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164676331) PASS; Native [#46164676365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164676365) FAIL PAY-0745; Full [#46164676426](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164676426) FAIL Controller parity after 14/14 target jobs PASS.
- #378: Poll [#46162754701](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162754701) and Mbed 3/3 [#46162754714](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162754714) PASS; Full [#46162754741](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162754741) CANCELLED; Native NOT RUN.
- #379: Poll [#46167474941](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46167474941) and Mbed 3/3 [#46167474965](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46167474965) PASS; Full [#46167474925](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46167474925) FAIL Controller parity after 14/14 target jobs PASS; Native NOT RUN.

The #377 Native failure is `synthetic-native`, step `PAY-0745 durable Vendo pending sequence and corruption contract`. Full failures are in `validate / Controller protocol parity`; downstream update, simulation, signing and publication jobs skip.

**Stale PR text:** #376's body says head `22ff6eb0`, but API head is `0f5968b2`; #377's body says `95e54790`, but API head is `95ace123`. #379's body says no final-docs-head run appeared, but three exact runs exist on `5ac75dbb`. HARDWARE owns these handover/description corrections.

## 3. Active v0.6 P0 poll-order recheck

At active branch `2fbd2475e9f54878c316fa7cea2f228386b0e859`:
- ESP8266 blob `12c4bb82b6fddafe813674a0b5f692c1d3634073`: timeout line 263, synchronous poll line 354, first `digitalRead(runCoinPin)` line 357.
- ESP32 blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d`: timeout line 230, synchronous poll line 314, first coin sample line 318.

Source inspection confirms poll-before-first-sample on both boards; this is not physical pulse testing. The #377 deny-only wrapper does not fix active v0.6 or establish durable pulse retention. P0 #177 remains OPEN.

## 4. Cross-role controller response contract

- CORE #252 head `c82705f2...`: controller library blob `1a820416...` builds a controller object with `config_revision`; Vendo CGI blob `16eb4105...` nests it under top-level `controller` and adds `config_auth` with `admission_allowed:false`.
- #376's `applyRemoteConfig(r)` reads flat root-level fields and does not consume the nested envelope or verify `config_auth`.
- #377 discards poll response and reapplies deny; #379 is a test/authority guard and adds no consumer.

**Decision:** CORE owns the canonical versioned authenticated wire contract; HARDWARE owns a consumer only after review; QA verifies semantic fail-closed behavior at the same exact SHA. No field guessing, decoy `config_revision`, invented `response_sig`, or positive admission. Coin and relay remain DENIED.

## 5. Other role CI
- CORE #252 build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS.
- RENTAL #289 build [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and native auth [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS.
- RENTAL #328 build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL; API21/23 smoke, native auth/installer and APK identity PASS.
- PISONET #255 Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; QA #290 Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS.
- QA #292 and RELEASE #291: no exact-head workflow run returned; RELEASE #291 is non-mergeable. CORE remains owner-only.

## 6. COE #26 staging review
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; PR #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, branch `integration/ecosystem-nonproprietary-candidate-20261111`, 205 changed files.
- Five candidate workflows remain CANCELLED: [#43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [#43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [#43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557), [#43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [#43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632).
- This run re-read the 205-path inventory: four `Hardware/` paths and four in-scope PisoWiFi legal paths. The prior exact audit at this unchanged head remains baseline: 61/61 runtime blob/mode matches; actual 46 identical / 15 derived vs declared 47 / 14; 15 derived tests vs 14 map rows; missing `voucher_txn_journal.sh`; stale `run_focus.sh` and `member_txn_journal.sh` hashes; four in-scope legal artifacts exact; destination branch pin stale.
- **No staging, copy, move, destination write or migration proposal.** #26 remains FROZEN.

## 7. Governance, registry and test limitations
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, Master target null. Seven bounded in-memory assertions PASS; this is not `verify_coordination.py`.
- Root AGENTS.md, README_FIRST, BLAZE-COMMS/1, Cloud Artifact Policy and Cloud Storage Recovery Handover were read. A 10-page / 1,000-entry Library inventory and exact-name search found v3–v7 snapshots and a 2026-11-09 checkpoint, but not canonical private v11 or newer corrections. No Google Drive connector/action is exposed; no older registry substituted and no private IDs/data copied.
- Automation inventory shows active PHX-HARDWARE continuation `Blaze Hourly Production Development`; exact CORE title `Blaze Production Continuation` was not exposed. CORE remained read-only; no competing task was started or modified.
- Branch-protection detail endpoint returned 403; effective enforcement is UNKNOWN.
- Master Python suite, `verify_coordination.py`, and Master GitHub Actions NOT RUN. No authenticated non-Codex local checkout is available. Route assertions are in-memory; firmware line checks are source inspection, not repository tests or hardware acceptance.

## 8. Next actions
1. HARDWARE: reconcile #378 with current #377, preserve append-only history, refresh #376/#377/#379 handovers and rerun exact-head Poll/Mbed/Native/Full.
2. QA: replace PAY-0745 source-shape checks with semantic corruption/default-deny tests and resolve Controller parity at the same exact SHA.
3. CORE: publish canonical versioned authenticated controller envelope; no shared schema change without review.
4. COE owner: correct 47/14 summary, add missing voucher map row, refresh two hashes and destination branch pin before staging.
5. Registry custodian: provide private v11/newer corrections through authorized Drive access.
6. Repository administrator: provide authenticated non-Codex checkout and verify effective branch protection.

**Final:** BLOCKED / PRODUCTION NO-GO. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, flashing, physical tests, payment operations, financial migration or customer cutover occurred.
