# PHX-MASTER UTC13 — exact owner heads, terminal CI, and COE #26 provenance

**Date:** 2026-11-20 UTC13  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repository provenance and integration matrix only  
**Execution boundary:** no Codex application, CLI, API, agent, workflow or delegation; no subsystem source edits.

## 1. Live control-plane snapshot

This audit re-read issue #172, cleanup issue #266, repository AGENTS.md, the uploaded Master directive, README_FIRST, BLAZE-COMMS/1, the existing Master PR and route manifest, role PRs/CI, COE main/#26, and the accessible Library inventory.

| Ref | Exact value at this read |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| v0.5.3 development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| v0.6 comparison-only | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch at audit start | `phoenix/master-coordination@52b7c023ea414e2df504e943425a9d0957c8c2d9` |
| Master PR #288 | OPEN / DRAFT, head `52b7c023...`, base `main@f4e8a891...`, 127 existing changed paths, all under `coordination/phoenix/` |
| COE default branch | `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT / frozen, head `b382d233ff06c8791b1028bed3c617cc7b670d12`, base `main@a6513ab...` |
| Issue #172 / #266 | Both OPEN; Master cleanup checkbox remains incomplete |

`OWNERSHIP_ROUTES.json` was read from the current Master branch and remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`, destination PR #26 pinned, PHX-MASTER target `null`. It is a review map, not a copy/move command.

## 2. Exact role PR heads and CI

| Role | PR / exact head | Exact-head evidence at this read |
|---|---|---|
| PHX-CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped. CORE remains exclusively with the separate active CORE continuation. |
| PHX-RENTAL | #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) SUCCESS, scoped. |
| PHX-PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped. |
| PHX-HARDWARE | #254 `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9` | [#44683629378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629378) focused header PASS; [#44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) Full FAIL (ESP32 compile and mandatory handover freshness). Separate draft; not the active #327 child. |
| PHX-HARDWARE | #327 `85c54fea5136da182b173c4d89900b22cf61d2b5`, child of #326 `58c558fb6a237935214621adc3dee65a10fe1a51` | [#44742512534](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44742512534) relay/output PASS; [#44742512577](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44742512577) quarantine PASS; [#44742512729](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44742512729) Full FAIL at Controller protocol parity / QA-owned `Missing poll signature check`. All 13 firmware targets and Android passed; downstream simulations/signing/publishing skipped. |
| PHX-QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, scoped; native `NativeComInterfaceHandleLab` not invoked. |
| PHX-QA | #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run returned. |
| PHX-RELEASE | #291 `dcb905333c8963fb139eeeefa72471738c874fb8`, based on #242 `734b89d9e7792247e8376335c3f3685500ab3f89` | [Windows #44746554630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746554630) FAIL at PISONET-owned `negative-selftest.ps1` (`$buildWorkflow` is unset); [ESP32 compatibility #44746554825](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746554825) IN_PROGRESS; [BlazePwifi Full #44746554633](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746554633) IN_PROGRESS. No terminal pass is claimed. |

### #291 cross-role diff boundary

The live #291 changed-file list contains 26 paths. Twenty-one are Release workflow/tooling paths; five are owned outside RELEASE:

- CORE product handover paths: `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`, `docs/handover/CHANGE_LEDGER.md`, and `docs/handover/CURRENT_STATE.md`.
- PISONET SoftTimer test paths: `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/PublisherMockCli.ps1` and `negative-selftest.ps1`.

The Windows failure log confirms the negative-selftest path is still failing because `$buildWorkflow` is not initialized. CORE and PISONET retain ownership and must review/approve their own paths. RELEASE must not treat their presence in its accumulated diff as a transfer of ownership. PHX-MASTER changed none of them.

At the previous #291 head `cfd301f1...`, the Full build run [#44746263315](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746263315) failed in the new checksum-path test. The subsequent Release commit `dcb90533...` changes only `.github/scripts/write_build_provenance.py`; current exact-head compatibility and Full runs are still in progress. Do not mark this fix verified until those exact-head runs terminate.

## 3. Fresh exact-tree COE #26 comparison

The source tree was read at HARDWARE #327 head `85c54fea...`; the destination tree was read at COE #26 head `b382d233...`. Both recursive trees were complete and not truncated.

| Measure | Experiments #327 source | COE #26 destination |
|---|---:|---:|
| Recursive tree entries | 2,438 | 286 |
| Board-local Python lab/helper files | 24 | 0 |
| Hardware workflows | 3 scoped PHX-HARDWARE workflows | 1 generic `hardware-ci.yml` |
| Hardware test identity | Source-extracted Python labs | One generic `Hardware/tests/test_firmware_hardening.sh` (`f921c56c...`) |

Exact firmware blobs:

| File | Source #327 | Destination #26 | Result |
|---|---|---|---|
| ESP8266 sketch | `3ff575f5cd879c021407849578854b74a2d460bd` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different |
| ESP32 sketch | `849a2c63d75bbbcda58e1a0a7fc55e7c047ea26e` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different |

The three source workflows are `phx-hardware-poll-edge-latch.yml`, `phx-hardware-quarantine-byte-readback.yml`, and `phx-hardware-relay-output-polarity.yml`; the destination generic workflow is not equivalent evidence of invocation parity.

License/notice review:

- Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` have the same MIT blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Source repository-root `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` is absent from COE #26.
- COE #26 has no root `NOTICE.md`, `Hardware/LICENSE`, or `Hardware/NOTICE.md`. The sibling Pisowifi license does not independently establish Hardware subtree notice scope.

**Disposition:** COE #26 remains five workflows QUEUED / zero jobs. Exact firmware blobs, lab/test identity, workflow invocation, and notice scope remain unaccepted. No file was copied, moved, staged, overwritten, cherry-picked, rebased, or route-promoted. The route manifest remains unchanged.

## 4. Governance, storage and test limitations

- Branch API reports `protected=false` for Experiments `main` and `phoenix/master-coordination`; repository rulesets endpoint returned `[]`. Classic branch-protection read returned HTTP 403. Effective organization-level enforcement is therefore **unverified**, not assumed absent or present.
- The exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced. Library search found only older v3–v7 registry snapshots plus older artifact-manifest/sync-ledger records; none was substituted. No Google Drive connector was exposed. No private identifiers or registry contents were copied into public GitHub.
- Master PR #288 has no workflow runs on its exact current head.
- The full Master Python suite was NOT RUN; no authenticated local checkout/test environment was available in this execution. Remote CI outcomes above are GitHub Actions readbacks. Tree/blob comparisons are source inspection, not tests or physical acceptance.

## 5. Owner actions / next gate

1. **PHX-QA:** replace the stale positive `response_sig` / `|poll|` assertion with source-linked negative/default-deny tests; rerun HARDWARE #327 Full at exact head.
2. **PHX-PISONET:** fix and own `negative-selftest.ps1` and review both PISONET paths in #291.
3. **PHX-CORE:** review the three product handover paths in #291; CORE implementation remains with the separate active continuation.
4. **PHX-RELEASE:** complete exact-head compatibility/Full runs after `dcb90533...`; keep non-Release paths owner-approved and do not claim the checksum change until CI is terminal.
5. **COE integration owner:** keep #26 frozen until per-file blob/mode, licensing/NOTICE, imported test identity, workflow invocation and exact-destination CI are independently reconciled.
6. **Registry custodian / repository administrator:** restore authorized v11/newer-correction access and provide effective protected-branch evidence.
7. **PHX-MASTER:** run the complete coordination suite when an authenticated checkout is available; continue Master-only matrix and provenance work.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, flash, real-payment action, secret provisioning, physical test or financial migration was performed.
