# PHX-MASTER UTC23 — receipt-v1 contract and Hardware #327 EEPROM reconciliation

**Run identity:** 2026-11-18T23:40Z–23:54Z  
**Role:** PHX-MASTER only  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Master branch before commit:** phoenix/master-coordination at f16e17683cea47aee9bc48e96cf5b8b9ab16f780  
**Control plane:** issue #172; cleanup issue #266  
**Master PR:** #288 OPEN / DRAFT, base main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**COE:** main at a6513ab4412b4c014eee2863e45cbe32d06cb243; integration PR #26 at b382d233ff06c8791b1028bed3c617cc7b670d12  
**Scope:** coordination/phoenix only. No Codex app, CLI, API, agent or workflow was used.

## Executive result

This run completed two source-grounded Master audits:

1. COE CORE PR #45 introduces a synthetic HMAC receipt-v1 contract candidate, but its schema is not compatible by simple field substitution with Master architecture §1.2. It is not part of COE #26. CORE and QA must approve a versioned bridge before adoption.
2. Hardware PR #327 has now corrected the ESP8266 full-image EEPROM read/recovery failure in source and failure-injection tests. The exact source/test head passes both focused workflows. Full validation still fails at the inherited QA-owned positive poll-signature assertion. A newer docs-only PR head has fresh focused runs in progress and Full queued, so that latest PR head is not yet CI-verified.

No source-owner branch was modified. No migration, copy, move, merge, rebase, release, signing, flashing, physical test or payment operation was performed.

## 1. Live refs and role ownership

| Ref | Exact SHA / state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| PHX-MASTER PR #288 before this commit | f16e17683cea47aee9bc48e96cf5b8b9ab16f780, OPEN / DRAFT |
| Experiments v0.5.3-development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Experiments v0.6.0-audit-foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |
| Routing manifest | e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER destination null |

The current role pins and CI are recorded in INTEGRATION_MATRIX.md and ROLE_ASSIGNMENTS.md. CORE remains owned by the separate Blaze Production Continuation; this run made no CORE changes and started no competing worker.

## 2. COE #45 — receipt-v1 contract review

COE PR #45 is OPEN / DRAFT at 9d76a134c1f6512aa40c20ec4d247306a71a8cce, based on d0830332 rather than COE #26. Its exact-head [focus suite #44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) passed and logs include COIN_RECEIPT_V1_GOLDEN_PASS; [case-collision #44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) passed.

The candidate defines canonical ASCII name/value lines with LF, fixed ordering, HMAC-SHA256, event-derived receipt_id, account_id_hash, ledger_epoch, ledger_sequence, issued_at/expires_at, disposition/reason, pulse_count, centavo delta/total, key_version and stable retry bytes.

Master §1.2 instead documents a v2-style example using event_id, protocol_version, target, amount_centavos, seconds_granted, timestamp_utc, nonce, signature and replayed. No approved version negotiation or field mapping exists. target_nonce is not a direct target mapping; credit_delta_centavos is not a direct seconds_granted mapping; receipt_id/event_id and HMAC/signature are not interchangeable. New ledger/account fields have no approved Master-v2 mapping. **COE #45 is a contract candidate, not an adopted Master interface and not an import into #26.**

Test source inspection found remaining gaps: no uint32/uint64 upper-bound assertions for key_version, ledger_sequence, timestamps or centavo values; account_id_hash syntax is checked but not derived from an approved identity; no approved clock-skew policy; no production parser/consumer; and the three vectors do not cover every allowed reason or malformed, duplicate, missing, unknown and reordered input. CORE must define the version bridge and authorities; QA must add parser-level boundary and negative vectors. Runtime remains deny-only.

## 3. Hardware #327 — current exact-head reconciliation

Live PR #327 is OPEN / DRAFT / UNMERGED, base #326 at 58c558fb6a237935214621adc3dee65a10fe1a51.

- Live PR head at audit time: 3046c74d19ee1040996860a66cbdcb850acdbe14 (one docs-only handover sync after the source/test head).
- Exact source/test head: 6b52d63f889a9567303f9f2de464c743c1991f0c.
- Firmware correction: 40cfc0799a6e65e4a724e8ccbe6baa0f5f51de54.
- The correction adds status-bearing full-image ESP.flashRead, EEPROM RAM-image restoration and configImageReadVerified gating. loadCfg no longer treats an unreadable image as erased defaults; saveCfg/writePollFaultBackup require a verified image and revalidate after reopen.

Exact source/test evidence:
- [Quarantine/readback #44423903845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903845) PASS. The log proves first-read recovery with marker preservation, recovered-image cold-boot deny, marker-only recovery without commit, persistent read failure without commit, poll-drain abort continuity and pulse capture pass on both board-shaped harnesses.
- [Relay/output #44423903842](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903842) PASS. Both boards pass 48/48 relay-polarity scenarios and the poll/output-preload regressions.
- Source/test Full [PR #44423903891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903891) and [push #44423897080](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423897080) completed FAILURE at QA-owned Missing poll signature check. All 13 firmware/platform targets plus Android passed; simulation, update bundle, candidate, signing and publishing were skipped.
- The later docs-only head 3046c has focused runs [#44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021) and [#44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181) IN_PROGRESS and Full [#44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063) QUEUED at readback. Do not claim exact-head CI for 3046c yet.

The live PR body and the top handover pin still cite older c51271938; the current PR API head is 3046c. HARDWARE owns refreshing its PR description and top handover pin. The source/test fix is a host/fake-I/O result, not physical flash acceptance. Simultaneous LittleFS and EEPROM/NVS failure remains current-boot denial only; the stores share the same flash chip and are not an independent witness.

## 4. Exact migration provenance — COE #26 remains blocked

No destination move was proposed.

- Hardware #327 ESP8266 source tree: 14 files vs 1 in COE #26; the same-path sketch blob differs (d36e9684f714d4af0ccf01739acb716072d39065 vs c8be98f72596681e36a3ad1f8939bf8046c96887). ESP32: 13 source files vs 1 destination; sketch blobs differ (ef498761e46d37134730dd41de1cc322d5d443e8 vs 3cc7ec54b476943dc04a8d1af5e2df5fe054e422). There are 19 source board-lab Python files and zero COE Hardware Python labs.
- PISONET #255 vs COE #26: 68 source files vs 47 destination; 27 identical, 11 different, 30 source-only, 9 destination-only. Six production C# files differ: AppConfig.cs, AppController.cs, SerialHardware.cs, Storage.cs, TimerEngine.cs and WindowsNativeComPlatform.cs; the NativeSerialPinFaultLab Program.cs also differs. Separate COE #30 is 68 vs 48, with 26 identical, 12 different, 30 source-only and 10 destination-only; #30 is not #26.
- Experiments main BlazePwifi/tests vs COE #26 Pisowifi/tests: 38 source files vs 19 destination; 1 identical, 3 different, 34 source-only and 15 destination-only.
- Experiments root NOTICE exists while COE root NOTICE is absent. BlazePwifi/LICENSE and COE Pisowifi/LICENSE are byte-identical. COE Hardware/LICENSE and Hardware/NOTICE.md are absent. qrcode and TailAdmin vendor license/notice files match. Android Launcher and Tabler license files have no corresponding destination route. Neither mapped Pisonet tree has a Pisonet-scoped LICENSE or NOTICE.

All five COE #26 workflow job endpoints returned zero jobs. No destination CI execution exists for this candidate.

## 5. Branch authority and governance

Control-plane issue #172 calls v0.5.3-development the development line and v0.6.0-audit-foundation comparison-only. GitHub compare shows v0.5.3 is 293 commits behind main and 0 ahead; its branch handover is dated 2026-10-06. v0.6 is 1,876 ahead and 22 behind main, while its branch-local handover/policy still calls it active. No literal branch named development was present. The product owner must reconcile the conflicting handover before any branch promotion or migration source selection.

GitHub branch API reported protected=false for the checked Experiments main/development branches and COE main; the rulesets endpoint was empty. Repository admin must independently configure and verify required checks/protection.

Experiments root AGENTS.md was read. COE root AGENTS.md returned 404. AGENTS-linked Cloud Artifact Policy and Storage Handover could not be read through the exposed GitHub connector. Library search returned registry snapshots v3-v7 and a 2026-11-09 production checkpoint, but not private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json or newer corrections. No Google Drive connector is exposed; older snapshots were not substituted and no private registry contents were published.

Issue #172 body still contains an older Master head pin; live PR #288 metadata is authoritative. Cleanup issue #266 remains OPEN. The latest Master checkpoint on #172 before this run was UTC22; no current UTC23 PHX-MASTER checkpoint existed. The PHX-HARDWARE UTC23 checkpoint is comment #6995143780 and is not a Master checkpoint.

## 6. Verification and limits

- 10/10 local authoring assertions passed for the coordination document updates. These are authoring-time checks, not repository CI.
- Exact-head GitHub Actions were inspected for Hardware #327, COE #45, COE #44, Release #291, QA and the COE #26 queued workflows.
- Master PR #288 has no PR-triggered workflow runs returned.
- Full Master Python suite was NOT RUN.
- No physical hardware, GPIO/relay, coin-acceptor, power-cut, native acceptance, real payment or 30-device soak test was run.

## 7. Next exact owner actions

1. PHX-CORE: publish an approved, versioned mapping between Master §1.2 and COE receipt-v1, including field bounds, account identity derivation, key-version authority, ledger epoch/sequence authority and replay semantics.
2. PHX-QA: add parser-level malformed/boundary/replay vectors after the CORE mapping; replace the inherited positive poll-signature fixture with negative default-deny tests.
3. PHX-HARDWARE: refresh PR #327 description and top handover pin to live head 3046c74d; wait for exact docs-head focused and Full CI; preserve no-hardware/no-durability claims.
4. PHX-RELEASE/INFRA: provide an authorized bubblewrap-capable runner; COE #44 currently fails at the required bwrap availability check.
5. Repository admin and registry custodian: verify branch protection and restore authorized private Drive v11/newer-correction access.

**Production remains NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.

### UTC23 final CI readback — Hardware #327

The live #327 PR head remains 3046c74d19ee1040996860a66cbdcb850acdbe14; source/test head 6b52d63f889a9567303f9f2de464c743c1991f0c. The docs-head quarantine [44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021) and relay [44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181) completed PASS. Docs-head Full [44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063) completed FAILURE at QA-owned Missing poll signature check; all 13 firmware/platform targets plus Android passed, while downstream simulations, update bundle, signing and publishing were skipped. This supersedes the earlier in-progress/queued snapshot. PR body/top handover still cite stale c51271938; HARDWARE owns that refresh.

