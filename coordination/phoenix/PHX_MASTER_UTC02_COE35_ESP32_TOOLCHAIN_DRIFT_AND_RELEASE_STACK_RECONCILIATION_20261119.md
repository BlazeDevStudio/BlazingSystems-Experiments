# PHX-MASTER UTC02 — COE #35 ESP32 toolchain drift and release-stack reconciliation

**Checkpoint:** 2026-11-19T02:38:20Z  
**Task:** PHX-MASTER-UTC02-COE35-ESP32-TOOLCHAIN-DRIFT  
**Disposition:** coordination-only; PR #288 OPEN/DRAFT; COE #26 OPEN/DRAFT; migration BLOCKED; PRODUCTION NO-GO.  
**Scope:** coordination/phoenix only. No subsystem source, test, workflow, or destination files changed.

## Exact refs

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Current development label v0.6.0: 2fbd2475e9f54878c316fa7cea2f228386b0e859 (1,876 ahead / 22 behind main).
- Older v0.5.3: aad3aade72c1156eecba1fed30907c6d0283b2c5 (0 ahead / 293 behind).
- Master before this commit: 0a777c3c13231a172683c47bd60ce4af2ad9f9fa.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243; #26: b382d233ff06c8791b1028bed3c617cc7b670d12.
- COE #31: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b; #35: 4843580ec9d901fda523bbf4c29f69e3745c698a; #44: 582fd5d5e83e36b36546ac28534740298ba94af4; #45: 9d76a134c1f6512aa40c20ec4d247306a71a8cce.
- OWNERSHIP_ROUTES.json unchanged: e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER destination null.

## P0 — exact source/destination and toolchain mismatch

| Sketch | Exact blob | Size |
|---|---|---:|
| Experiments #327 source | ef498761e46d37134730dd41de1cc322d5d443e8 | 59,117 bytes |
| COE #35 destination | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | 18,505 bytes |

These are different blobs. Both contain mbedtls/sha256.h; source also includes nvs.h and string.h, absent from the destination.

- Source #327 run [#44439616677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439616677), ESP32 job 135276906877: installed esp32:esp32 3.3.13 and compiled successfully.
- COE #35 run [#44443780617](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44443780617), ESP32 job 135290899476: installed esp32:esp32 4.0.0 and failed at line 6 because mbedtls/sha256.h was not found; artifact upload skipped.
- Both workflows use unpinned arduino-cli core install esp32:esp32. Source workflow blob 2cd6ce83b01c65fd78df091e502b68bf4fd277dc; destination workflow blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793.

This proves unpinned toolchain drift across the two exact-head runs. It does not prove the source sketch is compatible with 4.0.0 or that the destination is otherwise equivalent.

**Owners:** PHX-RELEASE pins exact Arduino CLI and ESP32/ESP8266 core versions, FQBN and build options; PHX-HARDWARE owns firmware compatibility/source changes; PHX-QA independently verifies both exact SHAs with the same pinned toolchain. The only observed successful source ESP32 core is 3.3.13; RELEASE may pin that baseline or coordinate a reviewed 4.0.0 port. Master chooses neither and changes no workflow or firmware.

## Current release CI

- COE #35 shared #44443780617: validation PASS, ESP8266 compile PASS, ESP32 compile FAIL under 4.0.0.
- Case #44443780675: PASS.
- Mandatory sandbox #44443780613: 14/14 host-preflight tests PASS, then missing bwrap; fail-closed exit 125; sandbox packaging skipped. No fallback.
- Parent #31: shared #44222517238 PASS; case #44222517258 PASS; sandbox #44222517263 FAIL.
- COE #44: shared #44390136309 PASS; case #44390136296 PASS; sandbox #44390136327 FAIL closed.

## Release stack and destination

Current #35 → #44 comparison is DIVERGED: #44 is 15 ahead / 16 behind #35; merge base 1a5be48d2845781b0b07bad39a37f8440cea4d4. The earlier 15/13 count is stale. RELEASE owns history-preserving reconciliation; Master did not merge, rebase or cherry-pick.

#44's random-per-install ULA still does not prove the §6.9 same-site shared-prefix authority. CORE must define site identity; QA must test same-site/different-site/reboot/upgrade/restore. COE #26 remains at b382d233ff06c8791b1028bed3c617cc7b670d12 with five queued workflows / zero jobs: #43096752609, #43096752632, #43096752800, #43096752563, #43096752557. No destination staging or migration proposal was made.

## Role and CI matrix

| Role | Exact candidate | Current evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | #42698139210 PASS, scoped; separate CORE continuation owns implementation |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | #43653329235 / #43653329229 PASS, scoped |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | #42462978704 PASS, scoped; native COM bench absent |
| HARDWARE #327 | 094564122f19c9e97157bb615bf9bae409f822a7 | Quarantine #44439616778 PASS; relay #44439616678 PASS; Full #44439616677 FAIL at QA positive poll-signature fixture |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 #43633486963 PASS; #292 no runs |
| RELEASE #291 | fe940216e9e250b5df48c633b669ef3dd34fb299 | BlazePwifi #44440710888 PASS; Windows #44440710823 FAIL: $buildWorkflow unset in negative-selftest.ps1 |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | #44295049727 / #44295049903 PASS; receipt-v1 not adopted into Master-v2 |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five queued / zero jobs; no destination acceptance |

Latest PHX-RELEASE UTC02 checkpoint: #6997687205. Latest PHX-HARDWARE checkpoint: UTC01 #6997133261. No PHX-MASTER UTC02 checkpoint existed before this run.

## Governance and limits

- Cleanup #266 remains OPEN; its body retains historical 2026-10-31 pins.
- Branch objects report protected=false for Experiments main, v0.5.3, v0.6.0, Master and COE main. Both rulesets endpoints return []; classic branch-protection reads return 403. Admin verification remains required.
- Experiments AGENTS.md, README_FIRST, COMMUNICATION_PROTOCOL, Master prompt and current Master coordination docs were read. COE root AGENTS.md remains unavailable (404 in prior live read).
- Private Drive v11 registry and newer corrections were not found in the accessible Library; snapshots stop at v7. No Google Drive connector is exposed. No older registry was substituted; no private contents/IDs published.
- Master Python suite NOT RUN; no Master CI runs returned. Physical hardware, flashing, real power cuts, native acceptance and 30-device soak NOT TESTED.

## Next actions

1. RELEASE: pin toolchains and reconcile #44/#35 without force-push.
2. HARDWARE: resolve ESP32 core compatibility in its own branch; preserve default-deny.
3. QA: independently verify pinned builds and replace positive poll-signature fixture with negative tests.
4. COE integration: complete blob/license/NOTICE/import/test provenance and unblock #26 workflows.
5. CORE: define site ULA authority and receipt-v1/v2 mapping; separate CORE continuation retains implementation.
6. Repository admin: verify protections.
7. Registry custodian: restore authorized private v11/newer-correction access.

**PRODUCTION NO-GO** remains until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.
