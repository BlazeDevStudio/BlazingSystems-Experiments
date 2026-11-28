# PHX-MASTER UTC00 — Hardware EEPROM recovery, ULA site scope and role CI freshness

**Run identity:** 2026-11-19T00:34Z  
**Role:** PHX-MASTER only  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Master branch before this commit:** `phoenix/master-coordination@3c1ecc3242a84414ce93931e66a0bc4c1bcc588e`  
**Control plane:** issue #172; cleanup-first issue #266  
**Master PR:** #288 OPEN / DRAFT, base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**COE:** main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`  
**Scope:** `coordination/phoenix/` and architecture/integration contracts only. No Codex, no subsystem source edits, no migration.

## Executive result

This run corrects two Master coordination records against live source and exact-head CI:

1. The previous ESP8266 full-image EEPROM read hazard in Hardware #327 is now corrected in source and source-extracted failure-injection tests. Both focused workflows pass. Full validation remains blocked by QA's inherited positive poll-signature assertion.
2. COE #44's first-boot ULA implementation now has stronger exact-head evidence (109 tests, 2 sandbox-only skips; 10/10 profile staging), but its per-install random prefix still does not satisfy the same-site shared-prefix requirement in architecture §6.9.

The role matrix and audit summary are refreshed. No source-owner branch was changed, no migration was proposed, and production remains NO-GO.

## 1. Exact repository and Master refs

| Ref | Exact SHA / state |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Named development | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Older development branch still present | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master before this update | `3c1ecc3242a84414ce93931e66a0bc4c1bcc588e` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows queued / zero jobs |
| Ownership manifest | `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER target null |

PR #288 remains OPEN / DRAFT. Before this update it contained 91 changed paths, all under `coordination/phoenix/`.

## 2. Hardware #327 — full-image EEPROM read correction

Current PR #327 docs head: `3046c74d19ee1040996860a66cbdcb850acdbe14`.  
Exact source/test head: `6b52d63f889a9567303f9f2de464c743c1991f0c`.  
Firmware correction commit: `40cfc0799a6e65e4a724e8ccbe6baa0f5f51de54`.

The ESP8266 sketch now uses a status-bearing raw `ESP.flashRead` for the complete 544-byte EEPROM image, reconciles the emulation RAM buffer from the verified image before Config reads, and gates later configuration/poll-fault writes with `configImageReadVerified`. `loadCfg()` fails closed before defaults, migration or commit if the image read/restore fails.

The source-extracted `config_load_read_failure_lab.py` (blob `9da02102020e97360320cfa7bc1f39a184b20011`) executes production `loadCfg/saveCfg` against a fault-injected EEPROM model reproducing core 3.1.2's ignored `EEPROM.begin()` read status. The exact run logs show:
- `ESP8266_EEPROM_BEGIN_READ_FAIL_THEN_FULL_READ_RECOVER_MARKER_PRESERVED_PASS`
- `ESP8266_EEPROM_RECOVERED_IMAGE_COLD_BOOT_DENY_PASS`
- `ESP8266_EEPROM_FULL_READ_FAIL_MARKER_ONLY_RECOVERY_NO_COMMIT_PASS`
- `ESP8266_EEPROM_FULL_READ_PERSISTENT_FAILURE_NO_COMMIT_PASS`

Exact-head CI:
- Quarantine/readback [#44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021): PASS, job 135225761344.
- Relay/output [#44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181): PASS.
- Full [#44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063): FAIL at `tests/controllers.sh` / `Missing poll signature check`, a QA-owned positive-presence fixture incompatible with current deny-only behavior. All 13 firmware/platform target jobs plus Android succeeded; simulations, update bundle, candidate gate, signing and publishing were skipped.

**Decision:** mark the previous source-level full-image read finding corrected at this exact candidate; keep Full validation NOT ACCEPTED until QA replaces the positive fixture with negative default-deny behavior and independently reviews the same SHA. This is host/fake-I/O evidence only. No physical flash, real power cut or reboot acceptance is claimed. Both stores share the same flash device and are not an independent witness.

## 3. COE #44 — ULA implementation evidence and remaining site-scope gap

Current COE Release #44 head: `582fd5d5e83e36b36546ac28534740298ba94af4`, based on #35 at `1a5be48d2845781b0b07bad39a37f8440cea4d4f`.

The first-boot script generates a random 40-bit RFC 4193 global ID, validates the resulting /48, persists `network.globals.ula_prefix`, verifies the UCI section type, and uses scoped rollback. Exact shared CI [#44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309), job 135105225016, ran 109 packager tests with 2 sandbox-only skips and validated 10/10 profiles. The ULA first-boot, commit-failure rollback and wrong-section-type tests passed. Case guard [#44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296) passed.

Mandatory sandbox [#44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) failed closed because `bwrap` is absent after 14/14 host-preflight tests. No unsandboxed fallback was used.

**Remaining gap:** the implementation creates a random prefix per installation. It has no site-scoped assignment authority or shared site identity input, so two appliances independently installed at one site can receive different /48 prefixes. Architecture §6.9 still requires same-site sharing and cross-site uniqueness. PHX-CORE/COE must define authority; QA must test same-site, different-site, reboot, upgrade and restore. No static prefix fallback.

## 4. Role and CI reconciliation

| Role | Current PR head | Latest returned exact-head evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | #42698139210 success; no CORE source touched |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | #43653329235 and #43653329229 success |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | #42462978704 success |
| HARDWARE #327 | `3046c74d19ee1040996860a66cbdcb850acdbe14` | Focused PASS; Full FAIL at QA fixture |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No current-head run returned |
| RELEASE #291 | `fc2e55e447c6627afc89f38a9412bb5c517de991` | Shared #44427424398 fails CORE handover freshness; Windows #44427424289 handover gate fails, build/publish skipped |

RELEASE #291 pins Arduino CLI 1.6.0 and verifies its runtime version. Its current shared workflow fails because `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` is older than `.github/workflows/blazepwifi-build.yml`; the gate reports last checkpoint `c53687df6132c4ee158d08d6baad9d21f6ef45c3`. PHX-RELEASE correctly did not edit CORE-owned handovers. CORE must refresh its own PROJECT_HANDOVER/CURRENT_STATE/CHANGE_LEDGER; QA must review the action/toolchain pin and the skipped runtime paths.

COE #45 receipt-v1 tests remain green but no approved mapping to Master receipt-v2 exists. COE #35 shared/case checks pass while its mandatory sandbox remains blocked. COE #26 has five queued workflows and zero jobs.

## 5. Migration and governance

The ownership manifest remains DRAFT_REVIEW_ONLY and PHX-MASTER target null. This activation did not recompute per-file source/destination blob, mode, license, import or test-identity parity for COE #26; therefore no migration proposal is made and the destination remains blocked.

Branch-protection API reads returned 403 for Experiments main, named development and Master; repository rulesets returned `[]`. Effective branch protection is UNKNOWN, not independently verified disabled. COE root AGENTS.md returned 404. The AGENTS-linked cloud policy/storage handover paths were not readable through the connected GitHub surface. No Google Drive connector was exposed; the canonical private v11 registry and newer corrections were unavailable in Library search. No older registry snapshot was substituted; no private data was disclosed.

## 6. Tests and limitations

- Actual GitHub Actions inspected: Hardware #327 focused PASS / Full FAIL; COE #44 shared PASS / case PASS / sandbox FAIL; Release #291 shared and Windows handover FAIL; other role PR results as listed.
- Master-specific Python suite: NOT RUN.
- Master PR #288 CI: no runs returned.
- Physical hardware, flash, power-cut and 30-device soak: NOT TESTED.
- No source migration, merge, rebase, release, signing, secret provisioning or payment operation.

## 7. Next owner actions

1. **PHX-QA:** replace the positive poll-signature assertion with negative default-deny tests and independently review #327 exact source/test SHA `6b52d63f...`; run the exact combined candidate.
2. **PHX-CORE / COE:** define site-scoped ULA assignment authority and a versioned receipt-v1/v2 mapping; no Master contract adoption before tests.
3. **PHX-CORE:** refresh only its own handover records so Release's freshness gate can proceed.
4. **PHX-RELEASE / INFRA:** provide an authorized bubblewrap-capable runner; retain fail-closed behavior.
5. **COE integration owner:** keep #26 blocked until exact source/destination blobs, licenses, dependencies, tests and CI are compared at the proposed SHAs.
6. **Repository admin / registry custodian:** independently verify branch protections and restore authorized private v11/newer-correction access.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently evidenced.
