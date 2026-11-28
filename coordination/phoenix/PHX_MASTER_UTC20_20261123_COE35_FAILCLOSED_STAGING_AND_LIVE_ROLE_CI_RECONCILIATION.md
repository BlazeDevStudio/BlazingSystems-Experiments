# PHX-MASTER UTC20 — COE #35 fail-closed overlay staging, live role CI, branch ancestry, and migration hold

**Observed:** 2026-11-23T20:38:16Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** #172 / #266 / #288 / #347 / #291 / COE #26 / COE #35  
**Scope:** `coordination/phoenix/` only  
**Execution:** Strict NO CODEX. GitHub connector reads/writes and ordinary JavaScript static checks only.  
**Disposition:** Coordination evidence refreshed; COE #26 remains frozen; production remains **NO-GO**.

## 1. Exact repository state

| Reference | Exact value |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development branch | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Comparison-only v0.6 branch | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| PHX-MASTER branch at audit start | `ee3e0497faa519a49cc6ccd975f32479604dbf04` |
| PHX-MASTER parent | `88cf6a42fef138b0a3ddc9b723e3fe4dba63eca7` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Ownership manifest | `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` |

PR #288 remains OPEN / DRAFT / UNMERGED. Its current 191 changed paths are all under `coordination/phoenix/`; no out-of-scope path is present. Master PR Actions have zero runs at the audited head. The PR description is 83,836 characters and was preserved; this update is recorded in the PR conversation rather than replacing or truncating the description.

The recursive trees are complete and non-truncated: Experiments main 2,340 entries; Master branch 2,533; COE #26 286; COE main 3. The ownership manifest has 11 routes, `DRAFT_REVIEW_ONLY`, and the PHX-MASTER target remains `null`.

## 2. New RELEASE-owned COE #35 correction — source fix verified, release still blocked

COE [PR #35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35) remains OPEN / DRAFT / UNMERGED, based on #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.

| Evidence | SHA / result |
|---|---|
| Test-only regression | `77408bbd3578a0d4c5965c19ed43ad4ff0eab687` |
| Source correction / source-test SHA | `daf08616ec001dae7013a8f029894153f597e1ae` |
| Final PR/docs HEAD | `a91b46c43222e328d7a195179d1c105b5811e548` |

**Defect and correction:** the final permission-normalization pass used `os.walk(staging_dir)` without an `onerror` callback. A subtree scan error could therefore be silently ignored while staging appeared successful. The correction re-raises the original scan error from the walk callback. The regression first demonstrated the swallowed `PermissionError`; no firmware bytes, financial behavior, manifest schema, ULA policy, network configuration, or shared interface changed.

**Exact source/test evidence:**
- Expected RED [#45256840088](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45256840088): 204 tests, one expected failure and two intentional skips; the injected `PermissionError` was swallowed before the fix.
- Shared [#45256991175](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45256991175): 204 packaging/tool tests PASS / two intentional skips; 10/10 appliance profiles fail closed because approved site-scoped RFC 4193 ULA /48 authority is missing; board compiles skipped.
- Sandbox [#45256991158](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45256991158): 40/40 host preflight PASS; Bubblewrap unavailable / exit 125; namespace and mandatory sandbox packaging tests skipped.
- Case collision [#45256991157](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45256991157): PASS.

**Final docs-head evidence:**
- Shared [#45257165703](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45257165703): 204 PASS / two intentional skips; 10/10 profile admissions fail closed for missing ULA /48; ESP32/ESP8266 compile jobs skipped.
- Sandbox [#45257165711](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45257165711): 40/40 host-preflight PASS; Bubblewrap unavailable; namespace and mandatory sandbox packaging tests skipped.
- Case collision [#45257165626](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45257165626): PASS.

**Important staging limit:** the fix does not automatically roll back a partially created staging directory after a traversal error. Such a directory must be treated as tainted and not reused. No ImageBuilder sandbox execution completed and no appliance binary was produced. The ULA authority and Bubblewrap runner are independent blockers; green packaging tests do not override either.

## 3. Current role PR / CI matrix

| Role / candidate | Exact head(s) | Exact-head CI | Interpretation |
|---|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS | Scoped build only; no independent durable-finance or witness acceptance. CORE source remains owner-reserved. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [APK #44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) PASS; [API #44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; [Build #44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL | Build fails at mandatory handover freshness and ESP32 Mbed TLS include; APK/API success is not full integration acceptance. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Windows #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS | Synthetic Windows CI only; native COM adapter / serial bench acceptance remains unverified. |
| HARDWARE #347 | Docs `5260d433ca440ddb7526ec08519b00a7e6620eb5`; firmware source `275057aa28375223a32da099420f52696d9b667c`; test/lab `fc1bfe86e51e1446712915c69087dca5be8e0763` | [Quarantine #45253005056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45253005056) PASS; [Relay #45253003611](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45253003611) PASS; [Full #45253005102](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45253005102) FAIL | Full fails at QA-owned `Missing poll signature check`; 14/14 target/platform builds pass, 12 dependent stages skip. Focused host labs are not physical acceptance. |
| QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | [#290 Windows #43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; #292 has zero PR-triggered runs | #290 workflow does not invoke `NativeComInterfaceHandleLab`; native suites remain NOT EXECUTED. #292 base is stale relative to current Master. |
| RELEASE #291 | Docs `c5a566fd04a59a3c4a4bbbaa9524f8a9b97e6b7d`; code/workflow `98ba3af1fe76128b331f93a4cf3543087cc0919b` | [ESP32 compatibility #45209288305](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288305) 3/3 PASS; [Full #45209288533](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288533) FAIL; [Windows #45209288746](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288746) FAIL | Compatibility is scoped to the exact ESP32 sketch blob only. Full/Windows fail at CORE-owned handover freshness. |
| COE RELEASE #35 | Docs `a91b46c43222e328d7a195179d1c105b5811e548`; source/test `daf08616ec001dae7013a8f029894153f597e1ae` | Final docs-head Shared/Sandbox/Case runs above | Packager traversal fix is verified; ULA and Bubblewrap remain blocked. Independent QA review pending. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [Overlay/Shell #44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) PASS; [Case #44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS | Contract-vector candidate only; not live financial acceptance. |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | [Stage 5.1 #44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) PASS; [Case #44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; [Shared #44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL | ESP32 Shared Contracts compile failure remains; separate candidate, not #26 integration proof. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs | OPEN / DRAFT / FROZEN; no staging or migration. |

## 4. Handover authority conflict — CORE decision required

The current evidence still disagrees about the canonical development line:
- Control-plane issue #172 lists `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Main-branch `PROJECT_HANDOVER.md` blob `f86c0ae9b14853963b8a9b835e1100eb5178d1a6` says the default-branch handover is historical and points to `blazepwifi-v0.6.0-audit-foundation`.
- The v0.5.3 handover blob `0430f421f705451b2c94cf9a97d2cf02398e9657` is dated 2026-10-06 and identifies v0.5.3-dev.1; the expected `docs/handover/CURRENT_STATE.md` is absent at that ref.
- The v0.6 branch is `2fbd2475e9f54878c316fa7cea2f228386b0e859`; its handover/current-state files are present, but this does not authorize Master to relabel the canonical development branch.

**Disposition:** unresolved source-of-truth conflict. PHX-CORE must confirm the active development branch and refresh its own handover; Master did not modify CORE source or handover files.

## 5. COE #26 migration and routing hold

The current source/destination refs and complete tree counts remain unchanged from the prior row-level audit. The earlier per-file audit remains the applicable evidence: 61 mapped runtime rows; computed 46 identical / 15 derived versus recorded 47 / 14; 15 derived tests versus 14 mapped; omitted `voucher_txn_journal.sh`; stale `run_focus.sh` and `member_txn_journal.sh` blob IDs; 33/61 historical source blobs still match current Experiments main, 20 differ and 8 are absent; NOTICE / third-party license counterparts remain incomplete.

Because the source main, COE #26 candidate, and manifest pins have not changed, no new move is proposed. The manifest remains 11 routes / `DRAFT_REVIEW_ONLY` / PHX-MASTER target `null`. No destination file was staged, copied, moved, overwritten, rebased, cherry-picked or promoted.

## 6. Architecture and coordination static checks

- Master recursive tree: 2,533 entries, non-truncated.
- Existing Master report files: 106; existing INDEX links: 106 unique, zero duplicate, dangling or unindexed links. This report raises both totals to 107.
- Current architecture document has 87 top-level §6 headings through §6.91. Four historical duplicate numbers remain: §6.9, §6.10, §6.11 and §6.25. No renumbering was performed because inbound historical references and consumers have not been completely inventoried.
- The current #288 diff has 191 paths, all under `coordination/phoenix/`; this update adds one report path and changes only six existing Master-owned documents.
- Main, development and COE main branch metadata report `protected=false`; repository ruleset lists are empty. Effective administrator-enforced protection remains unverified.

These are GitHub tree/blob and JavaScript static inspections. They are not a Python test-suite execution.

## 7. Tests, access, and explicit limitations

- Master PR Actions: zero runs at the audited starting HEAD.
- Full Master Python suite, `verify_coordination.py`, `test_architecture_contracts.py`, and migration validators: **NOT RUN**. No authenticated local checkout was available; a direct Git network attempt failed DNS resolution. No result is represented as PASS.
- Canonical private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced through an authorized Drive connector. The ChatGPT Library contains an older checkpoint that references the canonical registry plus older registry/manifest snapshots; none was substituted as the current registry. No private Drive contents or identifiers are reproduced here.
- Cleanup #266 remains OPEN / 0-of-7. No cleanup checkbox is claimed complete.

## 8. Next owner actions

1. **PHX-QA:** independently reconcile the #347 `Missing poll signature check` against the approved CORE register/poll producer contract; do not add a firmware signature merely to satisfy an unapproved assertion.
2. **PHX-CORE:** confirm the canonical development branch and provide the approved authenticated register/poll contract plus site-scoped ULA authority.
3. **PHX-RELEASE:** ensure a failed overlay walk cannot leave a reusable partial staging directory; retain the source/test evidence and rerun only after QA review.
4. **PHX-INFRA / COE owner:** provide an authorized disposable runner with working unprivileged Bubblewrap namespaces; no privileged helper or unsandboxed fallback.
5. **COE integration owner:** correct the #26 intake summary, derived-test map, stale blobs, import/license/NOTICE gaps before requesting staging review.
6. **Registry custodian:** restore authorized access to canonical private v11 and newer corrections.
7. **Repository owner / human runner:** verify branch protection and run the complete Master suite on an authenticated checkout at the exact resulting SHA.

**Production:** **NO-GO**. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates remain independently unverified.

No merge, release, signing, secret provisioning, firmware flashing, physical test, real-payment operation, customer cutover, or financial migration occurred.
