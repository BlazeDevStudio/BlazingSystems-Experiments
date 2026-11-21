# PHX-MASTER UTC14 — exact-head stack, terminal CI, and COE #26 provenance

**Date:** 2026-11-20 · **Audit checkpoint:** 2026-11-20T15:01:11.521Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repository provenance, integration matrix, release gates only  
**Execution boundary:** strict NO CODEX; no Codex app, CLI, API, agent, workflow, delegation, or parallel worker. No subsystem source edits.

## 1. Live control-plane and repository refs

| Ref | Exact value at this read |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development branch | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| v0.6 audit foundation | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` (comparison-only) |
| Master branch at audit start | `phoenix/master-coordination@962e1179aae8f49551f151bf4721e1524f690c38` |
| Master PR #288 | OPEN / DRAFT, base `main@f4e8a891...`, 128 paths at start, all under `coordination/phoenix/` |
| COE default branch | `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`, base COE main |
| Issue #172 / #266 | Both OPEN; Master cleanup checkbox remains intentionally unchecked |

The existing `OWNERSHIP_ROUTES.json` blob is `e4db324315a1b3543fec17a148fbf960170fcb29`. Its 11 routes still declare `DRAFT_REVIEW_ONLY`, source Experiments main, destination PR #26, and PHX-MASTER target `null`. Ten static manifest assertions passed in this readback. This is not the full repository test suite and does not authorize a copy/move.

## 2. Current role PRs and exact-head CI

| Role | Current PR / head | Exact-head evidence | Current disposition |
|---|---|---|---|
| CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS | Scoped CI only. CORE implementation remains with its separate owner/continuation; Master did not start competing work. |
| RENTAL | #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229), [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) SUCCESS | Scoped CI only; no native Device Owner acceptance. |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS | Scoped CI only; PISONET retains all SoftTimer source/test ownership. |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS | Scoped; native COM lab was not invoked. |
| QA | #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run returned | NOT CI-VERIFIED. |
| HARDWARE | #327 docs/PR head `a2388aedc611e831f339a87555450bd5554fa781`; source/test commit `dc9af45eaa33713713473cfa1ea8ab051769286f` | Relay [#44756633455](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44756633455) PASS; Quarantine [#44756634091](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44756634091) PASS; Full [#44756633635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44756633635) FAIL | Focused host CI only; Full validation blocked by QA-owned legacy positive poll-signature assertion. Physical acceptance NOT TESTED. |
| RELEASE | #291 docs/PR head `fbe1ca6183aa37fadf125b0e8c07a884e80789be`; source/test commit `0db99526477dd81f94d3f446165f90fc90defdbe` | Compatibility [#44753364998](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44753364998) PASS on ESP32 core 3.3.13 and 4.0.0; Full [#44753364967](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44753364967) 26 success / 0 failed / 4 skipped; Windows [#44753364863](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44753364863) FAIL | Non-production Full build/simulation passed; production import/sign/publish skipped; Windows remains blocked in PISONET-owned test. |

### 2.1 HARDWARE child-stack ancestry

The active stack is unchanged and parent identities match the live PR metadata:

| PR | Head | Base |
|---|---|---|
| #322 | `50d93e0de3d682550b6f02fb43484e76ad9c7e08` | #320 head `b2b41a3d6ce7887b9624137c966f58462895d3fa` |
| #323 | `988904e8bcd058b62a9fac4aa6319a9b7c5b2470` | #322 head `50d93e0de3d682550b6f02fb43484e76ad9c7e08` |
| #326 | `58c558fb6a237935214621adc3dee65a10fe1a51` | #323 head `988904e8bcd058b62a9fac4aa6319a9b7c5b2470` |
| #327 | `a2388aedc611e831f339a87555450bd5554fa781` | #326 head `58c558fb6a237935214621adc3dee65a10fe1a51` |

No rebase, force-push, merge, parent replacement, or source ownership change was performed. Separate Hardware drafts #239/#254/#283 remain separate; #254 focused header CI [#44683629378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629378) passes while Full [#44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) fails. #283's scoped quarantine [#44219099309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099309) and build [#44219099256](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099256) pass, but it is not the active child stack or an integration approval.

### 2.2 QA poll fixture mismatch

The exact source fixture `experiment/openwrt/BlazePwifi/tests/v05_firmware_hardening_test.sh` is blob `41211b2c110ab409f6d9d1812ef12fda73b13211`. It requires `response_sig` and literal `|poll|` in both sketches. Current firmware intentionally keeps positive poll admission dormant; those string markers are not an approved signed response-envelope contract. The exact docs-head Full run #44756633635 fails at `Missing poll signature check` in the ESP8266 sketch. All 14 firmware/platform target and Android jobs passed; validation failure caused simulations, update bundle, signing and publishing to be skipped.

**Owner split:** QA must replace the positive marker assertion with source-linked negative/default-deny tests for both boards. HARDWARE owns firmware. Do not add a synthetic positive signature producer, weaken firmware deny behavior, or authorize coin intake to satisfy the inherited fixture.

### 2.3 RELEASE #291 terminal correction and cross-role paths

The latest docs-head run #44753364967 is terminal, not in progress: 26 jobs succeeded, zero failed, and four production import/sign/publish jobs were skipped. Both pinned ESP32 compatibility legs passed in #44753364998. Windows #44753364863 completed handover successfully, then failed in `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1` because `$buildWorkflow` is unset; the publisher job was skipped.

The accumulated #291 diff contains 26 paths: 21 RELEASE paths, three CORE-owned product-handover files (`experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`, `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md`, `experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md`), and two PISONET-owned tests (`PublisherMockCli.ps1`, `negative-selftest.ps1`). CORE and PISONET retain their paths. Their presence in the accumulated RELEASE diff is not an ownership transfer. No Master or Release edit to those paths occurred in this activation.

## 3. COE #26 exact source/destination provenance

Source tree: Experiments #327 `a2388aedc611e831f339a87555450bd5554fa781`. Destination tree: COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`. Both recursive Git trees are complete and not truncated.

| Item | Experiments source | COE destination | Result |
|---|---|---|---|
| Recursive entries | 2,440 | 286 | Different scope |
| Board-local Python labs/helpers | 25 | 0 | No destination Hardware Python test identities |
| Hardware workflows | 3 scoped PHX-HARDWARE workflows | 1 generic `hardware-ci.yml` | Not invocation parity |
| ESP8266 sketch | `a1f12edc3d0a2ce93641c3ae2ef1e0e258dbbdaa` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different blob |
| ESP32 sketch | `ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different blob |
| Source hardening fixture | `v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` | `Hardware/tests/test_firmware_hardening.sh` blob `f921c56cecc19cab1989507b9b4ade1f45dac54e` | Different test identity |
| BlazePwifi MIT license | `1ee55b94183417be977ca287cd7391f9a6f7e721` | `Pisowifi/LICENSE` same blob | Sibling match only |
| Source root NOTICE | `f6d92cd21465312be5993631fe26977219be0fb9` | Root NOTICE absent | Missing |
| Hardware license/notice | — | `Hardware/LICENSE` and `Hardware/NOTICE.md` absent | Scope unresolved |

The source workflows are `phx-hardware-poll-edge-latch.yml`, `phx-hardware-quarantine-byte-readback.yml`, and `phx-hardware-relay-output-polarity.yml`. The generic destination workflow does not establish equivalent test invocation. The matching sibling Pisowifi MIT license does not independently establish Hardware subtree license/notice scope.

COE #26 still has five workflows QUEUED / zero jobs. Separate candidate readbacks: #31 case guard and Hardware/shared CI PASS but ImageBuilder sandbox FAIL; #35 case guard PASS but ImageBuilder and Hardware/shared CI FAIL; #48 Stage 5 and case guard PASS but Hardware/shared CI FAIL and no PHX owner route; #49 Stage 5.1 and case guard PASS but Hardware/shared CI FAIL and PHX-HARDWARE declined implementation ownership; #45 shell suite and case guard PASS. #48 remains unassigned/audit-only; #49 remains audit-only. Neither has a route in the manifest.

**Decision:** COE #26 remains FROZEN. No copy, move, overwrite, cherry-pick, rebase, staging, route promotion, or migration. Exact source/test/license/workflow provenance and destination CI acceptance remain incomplete.

## 4. Governance, storage, and execution limitations

- The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not accessible. The full Library listing contained 1,422 items and surfaced older v3–v7 snapshots, but not v11. No Google Drive connector is exposed in this runtime; no older snapshot was substituted and no private contents or IDs were copied into public GitHub.
- Repository `AGENTS.md`, the public Cloud Artifact Policy and Storage Recovery Handover were read. The policy requires a private registry read before mirror work and says to report BLOCKED if Drive access is unavailable.
- Branch metadata reports `protected=false`, repository rulesets returned an empty list, and classic branch-protection reads returned HTTP 403. Effective organization-level enforcement is **UNKNOWN**, not proven absent or present.
- Master PR #288 has no workflow runs on its audited head. A local authenticated clone was attempted and failed with `Could not resolve host: github.com`; the full Master Python suite was NOT RUN. Remote subsystem CI results above are GitHub Actions readbacks, not Master tests, physical hardware acceptance, or production approval.
- Issue #172's existing body was 64,790 characters at read time, near GitHub's issue-body limit. It was not rewritten or truncated; one new BLAZE-COMMS/1 checkpoint is used instead.

## 5. Master decisions and next owner actions

1. **PHX-QA:** replace the inherited positive poll-signature assertion with source-linked negative/default-deny tests; rerun HARDWARE #327 Full at the exact source/test SHA.
2. **PHX-PISONET:** fix and own `negative-selftest.ps1`'s unset `$buildWorkflow`; review its two owned paths in #291.
3. **PHX-RELEASE / CORE:** reconcile the three CORE handover paths in #291 with CORE's owner before integration; retain RELEASE ownership of its workflow/tooling and handover freshness.
4. **PHX-HARDWARE:** preserve the current focused lexical-extractor improvements and exact #322→#323→#326→#327 stack; no firmware relaxation to satisfy the old fixture.
5. **COE integration owner:** keep #26 frozen; do not claim integration/license/test parity until per-file source, license, import, test identity, workflow and destination-CI acceptance is complete.
6. **Repository administrator:** provide effective protected-branch admission evidence.
7. **Registry custodian:** restore authorized access to private v11 and newer corrections.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, hardware flash, real-payment action, physical test, or financial migration was performed.
