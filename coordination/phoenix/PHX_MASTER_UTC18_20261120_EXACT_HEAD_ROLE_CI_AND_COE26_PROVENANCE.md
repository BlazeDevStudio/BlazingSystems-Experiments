
# PHX-MASTER UTC18 — exact-head role/CI and COE #26 provenance

**As of:** 2026-11-20T18:06:08Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX. GitHub connector and ordinary source/metadata inspection only. No subsystem source edits, no worker delegation, no merge/release/flash/secret provisioning/financial migration/physical tests.

## Authority and live refs

- Master instruction: uploaded 00_MASTER_PROJECT_PHOENIX(1).txt; latest Library README_FIRST 20261114-191926 and COMMUNICATION_PROTOCOL 20261114-191925.
- Experiments AGENTS.md blob: `d8777e3b58efc41caa5aa3c969c932aee9103d5f`.
- Canonical cloud artifact policy blob in BlazeDevStudio/BlazingSystems main: `5e503925750c4e511314e4b7624579d82f60aae2`; cloud storage handover blob: `a15f14cb3baf46424b820e1a921462794422f06b`.
- Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; legacy development `aad3aade72c1156eecba1fed30907c6d0283b2c5`; active v0.6 audit foundation `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Master branch before this documentation update: `cf134056e7a2bef95c6a2b0727cad81e46e4de8a`; PR #288 OPEN / DRAFT / UNMERGED, base main, 129 changed paths all under coordination/phoenix/**. No PR-triggered Master workflow run returned.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration PR #26 OPEN / DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows QUEUED / zero jobs.
- Cleanup issue #266 OPEN; 0/7 role checkboxes complete. Master cleanup remains incomplete.

## Exact role PR / CI reconciliation

| Role | Exact PR heads | Exact CI |
|---|---|---|
| MASTER | #288 `cf134056e7a2bef95c6a2b0727cad81e46e4de8a` | No PR-triggered run; full Master suite NOT RUN. |
| CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS. Separate Blaze Production Continuation owns CORE. |
| RENTAL | #240 `a7d113fb8ae3f0c5e838e64d31cae7a154e37b56`; #287 `a4fffd01c8fb1818c32a53522e0590c1dc8a77cd`; #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | #240 [40910311141](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40910311141) / [40910311159](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40910311159) SUCCESS; #287 [43754089203](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43754089203) SUCCESS; #289 [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) / [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) SUCCESS. |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS; its owned #291 negative-selftest still fails. |
| HARDWARE | #323 `988904e8bcd058b62a9fac4aa6319a9b7c5b2470` → #326 `58c558fb6a237935214621adc3dee65a10fe1a51` → #327 docs `9bef8c1e7dcbde9e8987f14a1a874de1d7d11514`; source/test `d4f7df4e8d286fcc52bbb4a38af9aa9aff4ad3c1` | Quarantine [44786785385](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786785385) SUCCESS; relay [44786785413](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786785413) SUCCESS; Full [44786785416](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786785416) FAILURE at QA-owned Missing poll signature check. 13 firmware targets + Android SUCCESS; downstream production gates SKIPPED. |
| QA | #267 `ff5367990c2d27b8ebbb822ee208251af0c890e2`; #279 `8f476ef05893193325ef3d1f65a35e144ae7a568`; #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #267 [41452247439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/41452247439) SUCCESS; #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS; #279 and #292 no PR-triggered runs returned. |
| RELEASE | #291 docs `1b42e70544f142ca2fa54878638abb2c090235ca`, base #242 `734b89d9e7792247e8376335c3f3685500ab3f89`; #242 `734b89d9e7792247e8376335c3f3685500ab3f89` | #291 Full [44786500311](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786500311) 26 SUCCESS / 0 FAILURE / 4 production jobs SKIPPED; compatibility [44786500186](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786500186) SUCCESS; Windows [44786500129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786500129) FAILURE in PISONET-owned negative-selftest.ps1 because $buildWorkflow is unset. #242 [40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) SUCCESS. |

### Ownership and same-hour deconfliction

- HARDWARE #327 remains the #323 → #326 → #327 child chain. Its UTC17 checkpoint asks Master to refresh the active-head entry. No rebase/retarget/merge was performed.
- QA owns the stale positive poll-signature fixture; HARDWARE owns firmware and board-local labs.
- RELEASE has already posted its UTC18 lock (issue comment #7047140251) and is IN_PROGRESS on OpenWrt compiler provenance. Master did not duplicate that work.
- #291 contains 26 paths: 21 RELEASE, three CORE-owned handover paths and two PISONET-owned tests. CORE/PISONET must review their own paths. No ownership transfer.
- CORE remains with the separate Blaze Production Continuation automation. No competing CORE implementation was started.

## COE #26 exact source/destination provenance

- Experiments #327 source tree: `d46355267f991cfaae68fc37fa5f6e176fa1c269`, 2,443 entries, not truncated.
- COE #26 destination tree: `8a7d4cf81d7227118b876c1138dd2da12345fefa`, 286 entries, not truncated.
- Source ESP8266 sketch blob `a1f12edc3d0a2ce93641c3ae2ef1e0e258dbbdaa`; destination `c8be98f72596681e36a3ad1f8939bf8046c96887`. Different.
- Source ESP32 sketch blob `ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7`; destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`. Different.
- Source board directories contain 36 files including 33 Python labs/helpers; COE Hardware contains four files and zero Python labs. Source has three scoped Hardware workflows; destination has one generic hardware-ci.yml.
- Source hardening fixture blob `41211b2c110ab409f6d9d1812ef12fda73b13211`; destination fixture `f921c56cecc19cab1989507b9b4ade1f45dac54e`. Different.
- Current source sketches no longer contain the old positive response_sig / |poll| marker implementation; COE destination sketches still contain response_sig extraction and positive poll-signature calculation. This is an explicit source/destination behavior mismatch, not just a naming difference.
- Source BlazePwifi LICENSE and destination Pisowifi/LICENSE match at `1ee55b94183417be977ca287cd7391f9a6f7e721`. Source root NOTICE.md blob `f6d92cd21465312be5993631fe26977219be0fb9` is absent from COE. Hardware-specific LICENSE/NOTICE scope remains unresolved.
- COE Pisowifi/SOURCE_INTAKE.json blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f` is schema 8 and pins historical source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00`, only for Pisowifi rootfs: 61 original files, 61 recovered, 47 byte-identical, 14 locally derived, zero unrecovered, two unchanged tests.
- COE Pisowifi/MIGRATION_MAP.md blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` begins NO-GO FOR SHOP INSTALL and maps Pisowifi only. Neither file establishes Hardware migration provenance.
- OWNERSHIP_ROUTES.json remains `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, 11 routes, source ref Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, destination #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, PHX-MASTER target null.

**Disposition:** COE #26 remains FROZEN. No copy, move, overwrite, cherry-pick, rebase, staging, route promotion or migration.

## Storage, cleanup, and execution limits

- AGENTS.md requires the canonical private Drive registry, artifact manifest and sync ledger before artifact creation. The authorized Drive connector is not exposed in this execution surface; Library search found older registry snapshots and a checkpoint that references v11, not the canonical v11 file or newer corrections. None was substituted. No Drive artifact/folder was created.
- Cloud Artifact Policy says GitHub is source authority and Drive transfers require exact readback/size/SHA256. The cloud storage handover records full Git bundles as BLOCKED when network/checkout access is absent.
- Cleanup issue #266 remains OPEN, 0/7 complete. No broad cleanup/deletion was claimed.
- Full Master Python suite NOT RUN; this was GitHub source/tree/metadata and Actions-log inspection plus bounded static checks, not a local test-suite pass.

## Next actions

1. PHX-QA replaces the positive response_sig / |poll| string assertions with source-linked negative/default-deny tests for ESP8266 and ESP32, then reruns Full at the exact test SHA.
2. PHX-PISONET fixes the unset $buildWorkflow in its own negative-selftest.ps1 and reviews its two #291 paths.
3. PHX-RELEASE continues its current compiler-provenance audit and obtains CORE/PISONET owner review of inherited paths.
4. Registry custodian provides authorized v11 + artifact manifest + sync ledger access; repository administrator verifies effective protected branch enforcement.
5. Keep COE #26 frozen until exact source/test/license/notice/owner/CI acceptance.

**PRODUCTION NO-GO:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
