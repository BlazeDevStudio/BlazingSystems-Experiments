# PHX-MASTER UTC07 — poll-deny fixture and release handover reconciliation

**Date:** 2026-11-19  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance  
**Task:** #172 / #266 / #288 / #327 / #291 / COE #26  
**Disposition:** Master documentation update only; subsystem source untouched; migration BLOCKED; PRODUCTION NO-GO.

## 1. Live authority and deduplication

- Experiments default branch main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Experiments development/audit branch blazepwifi-v0.6.0-audit-foundation: 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Legacy development branch blazepwifi-v0.5.3-development: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master branch before this update: b44df280cd93a4a8893d5e486e9564d56a913489; parent of this report's commit is the exact remote head read at activation start.
- Existing Master PR #288: OPEN / DRAFT, base main at f4e8a891; pre-update changed paths: 97, all under coordination/phoenix/.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243; integration PR #26: OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12.
- Issue #172 had no PHX-MASTER-20261119T07 checkpoint before this activation. The existing PR #288 Master checkpoint comment is updated in place; one new UTC07 control-plane checkpoint is posted.
- Cleanup issue #266 remains OPEN. Ownership manifest OWNERSHIP_ROUTES.json is unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER destination null.

## 2. Hardware #327 — exact source/test and failing Full gate

Current PR/docs head: 31f5d727f0f61128694b9b0c4b92af8e4b6afa52; source/test commit: c37338439eec23c54a2e4a5f9c9c538d08f182cf; base #326: 58c558fb6a237935214621adc3dee65a10fe1a51.

Current sketch blobs:
- ESP8266: 1b32cb90be11da79ba7ea1155f128aee9e495dd2, 67,300 bytes.
- ESP32: c29483f0761ca6e2db0573bd12d6bfa502f12434, 61,807 bytes.

### Exact CI

| Run | Job(s) | Result |
|---|---|---|
| [Quarantine #44478447580](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447580) | 135404563994 | PASS |
| [Relay/output #44478447647](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447647) | 135404564309 / 135404565326 | PASS |
| [Full PR #44478447410](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447410) | validation 135404563869 | FAIL |

All 13 firmware/platform targets and Android passed in Full. Downstream simulations, update bundle, signing, candidate and publishing jobs were skipped.

### Root cause is a test-contract mismatch

- controllers.sh blob f7896647713d6bf8034ff48ed19b6383e4dedea0 invokes the legacy v05_firmware_hardening_test.sh.
- Legacy fixture blob 41211b2c110ab409f6d9d1812ef12fda73b13211 positively requires response_sig, |register| and |poll| strings; the Full job fails on the |poll| assertion.
- Both current board sketches keep acceptPollResponse() and coinPostDispositionVerified() fail-closed. The source has a post("poll") request, but no positive |poll| response-signature authorization token.
- Focused quarantine actually executes poll_response_failclosed_lab.py blob 69dbddee4133588940f4c5b53817401db531a8a4: 11/11 fail-closed cases per board, 13/13 strict-root-JSON cases per board, 4/4 coin POST root-status and 4/4 coin-disposition default-deny cases per board.
- Relay/output run #44478447647 reports ESP32 boot-polarity unknown/legacy profile remains INPUT, local polarity readback PASS, active-high/active-low OFF preload PASS and remote polarity authority DENIED.

**Decision:** QA replaces only the obsolete positive-presence assertion with source-exact negative/default-deny behavior tests and keeps the fail-closed lab in Full validation. Do not add fake tokens or relax firmware. All this evidence is simulated CI; physical relay/coin/power-cut acceptance is NOT TESTED.

## 3. RELEASE #291 — branch/progress discrepancy and handover gate

Live PR and branch head: 3ef73265abd52bf44273584afc406382c2805b1d, base 734b89d9e7792247e8376335c3f3685500ab3f89.

The PHX-RELEASE UTC07 progress comment reports b8f4e3619a8c84b4e81d8bb24ba3da02825fa9e6. That commit object exists but the branch and PR refs remain at 3ef73265; the commit changes only .github/PHX_RELEASE_HANDOVER.md. It is not accepted as the current branch head or evidence that the reported script/workflow scope is pushed.

- Windows release [#44479756135](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756135), handover job 135408844761: FAIL; build/publish skipped.
- BlazePwifi [#44479756093](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756093), validation job 135408938465: FAIL at tests/handover_gate.sh. Log says .github/workflows/blazepwifi-build.yml is newer than experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md; last checkpoint c0b5f3731e1db81faf275bf8f32a757f7d52f3d2.
- ESP32 core compatibility [#44479756113](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756113): PASS.

**Next:** RELEASE pushes the intended branch changes, updates product PROJECT_HANDOVER/CURRENT_STATE/CHANGE_LEDGER after workflow changes, and reruns exact-head CI. Master does not edit RELEASE or CORE handover files.

## 4. COE #26 migration hold and sibling stack

COE #26 remains at b382d233... on main a6513ab4.... Five workflows are QUEUED and each returns zero jobs:
- case collision #43096752609
- Windows SoftTimer #43096752632
- Hardware/shared #43096752800
- Rental #43096752563
- Pisowifi #43096752557

Current COE #35 head 5047af8b5a8296e06294bbda6bf42a6baea2294d pins Arduino CLI 1.6.0, ESP8266 3.1.2 and ESP32 3.3.13. Shared/firmware #44465377784 and case #44465377781 PASS; sandbox #44465377807 fails closed. These pins do not flow into #26.

COE #44 head 582fd5d5e83e36b36546ac28534740298ba94af4 is diverged 15 ahead / 25 behind current #35. Shared #44390136309 and case #44390136296 pass; sandbox #44390136327 fails closed. RELEASE owns history-preserving reconciliation.

COE #45 head 9d76a134c1f6512aa40c20ec4d247306a71a8cce has synthetic receipt-v1 runs #44295049727 and #44295049903 passing; it is not Master-v2 adoption or financial authority.

Hardware source/destination sketch blobs differ; source has nine Python labs plus a helper while #26 has one generic positive-presence shell test. Hardware/LICENSE and Hardware/NOTICE.md remain absent at #26. No staging, copy, move, overwrite, cherry-pick, rebase or merge is proposed.

## 5. Governance, access and verification

- Branch objects for main/development/Master/COE main report protected=false; Experiments and COE rulesets endpoints return empty arrays. Effective required checks/protection require administrator verification.
- Experiments AGENTS.md was read; COE root AGENTS.md returns 404.
- Private Google Drive registry v11 and newer corrections are not accessible through the current connected tools. The available Library search did not locate v11; no older snapshot was substituted and no private registry content/identifier was published.
- Local source/provenance assertions: 9/9 PASS.
- Master Python suite: NOT RUN; no local checkout. Master PR #288 Actions: no runs returned.
- Physical hardware/native acceptance, real power cuts and 30-device/24-hour soak: NOT TESTED.

## 6. Next exact owner actions

1. PHX-QA: replace the obsolete positive poll-presence check, retain the fail-closed source lab in Full, and independently review #327 at source/test SHA c3733843....
2. PHX-RELEASE: reconcile the b8f4 progress commit with the actual #291 branch, update product handover/current state/change ledger after workflow changes, rerun exact-head CI, and keep #44/#35 reconciliation owner-scoped.
3. COE integration owner: unblock all five #26 workflows and complete exact blob/mode/license/test/toolchain provenance before any staging proposal.
4. Repository administrator: verify branch protections and required checks.
5. Registry custodian: restore authorized read-only v11 and newer-correction access.

**PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.
