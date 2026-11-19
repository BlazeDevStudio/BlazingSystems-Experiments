# PHX-MASTER UTC20 — live role CI and COE hardware/QA provenance refresh

**Observed:** 2026-11-19T20:56:53.125Z  
**Role:** PHX-MASTER · coordination-only  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Pre-change Master HEAD:** b6ee424b897701bf1c550076610203d45f1a13f2  
**Existing PR:** #288 OPEN / DRAFT · base main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**Disposition:** PRODUCTION NO-GO · migration review only

## 1. Live control-plane and branch refs

- Issue #172 and cleanup issue #266 were re-read. #266 remains OPEN; the broad Master duplicate/dead-code cleanup checkbox remains intentionally unchecked because the full inventory is not complete.
- The top of #172 still contains an obsolete Master pin, f57456c4...; the live branch endpoint and PR #288 both resolve to b6ee424b897701bf1c550076610203d45f1a13f2.
- Current default branch: main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Latest control-plane designation for current development: blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859. The older blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5 remains present but is legacy, not the active development reference.
- Master branch: phoenix/master-coordination@b6ee424b897701bf1c550076610203d45f1a13f2.
- COE default branch: main@a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration #26 remains OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12.
- COE hardware candidate #27 is a separate OPEN / DRAFT PR at 009f70cc2c2775039a5fb072c9d4fdedee76cfc7, also based on COE main; it is not part of #26.
- OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, PHX-MASTER target null. No route is a copy/move instruction.
- The four live branch objects checked (Experiments main, active development, Master, COE main) report protected=false; both repositories' rulesets endpoints return empty lists. Repository administrators must establish and independently verify branch protection and required checks.

## 2. Exact role PRs and current CI

| Role | PR / exact head | Current exact-head evidence |
|---|---|---|
| CORE | #252 · c82705f2de865c89ab733b10efa84f26f56a5cc4 | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS |
| RENTAL | #289 · 68928774d0d7cf65adb26bc6b54199a3159d066c | [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS |
| PISONET | #255 · d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS |
| HARDWARE | #327 · docs head 20c73090f8b3b819e4fb345c336f8e9275feeaaa; source/test head cbc5ae5b5dac865ca3afff6cc2ec9b0b17daec9c | [44612105093](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612105093) relay PASS; [44612105234](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612105234) quarantine PASS; [44612105221](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612105221) full validation FAIL |
| QA | #290 · 5c29d15994cee1279058f1eca12f2a3180704292 | [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS |
| QA | #292 · 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head workflow run returned; draft remains stale relative to current Master |
| RELEASE | #291 · 3bffd9d14de42abf2c2f6079632e0348127ad025 | [44612586795](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612586795) Windows FAIL; [44612586860](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612586860) ESP32 compatibility IN PROGRESS; [44612586896](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612586896) BlazePwifi build IN PROGRESS at last read |

### Hardware second-ISR result

The current #327 quarantine run [44612105234](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612105234), job 135871119969, executed poll_fault_latch_edge_count_lab.py (blob e01177b5534df00b5b988aa4b174aa24140d75c6). Logs show POLL_FAULT_SECOND_ISR_LAB=PASS for ESP8266 and ESP32, both active-high and active-low. The first-fault snapshot remains unchanged; later ISR activity is reported as a known lower bound; admission remains denied, outputs off and pending identity preserved. Repeated-latch and pending-identity-clear mutations were rejected on both boards.

This is a host simulation, not physical ISR/relay acceptance. The Full #327 run still fails at the QA-owned positive poll-marker fixture: v05_firmware_hardening_test.sh blob 41211b2c110ab409f6d9d1812ef12fda73b13211 expects response_sig, |register| and |poll| markers at lines 28–30. Current source consumers deliberately return false until CORE supplies the approved signed poll/receipt contract and QA approves vectors. QA must replace the obsolete positive-marker test with source-exact negative/default-deny assertions; do not weaken firmware to satisfy it.

### Release #291 current failure and ownership boundary

Current #291 head is 3bffd9d14de42abf2c2f6079632e0348127ad025. Windows run [44612586795](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612586795) fails in RELEASE-SIGN test fail-closed negative controls because PISONET-owned negative-selftest.ps1 references $buildWorkflow without initializing it (blob 8b69174bf519154e43f7e12e4a9fa2c0e75d350f). The publisher job is skipped. The ESP32 compatibility and BlazePwifi build runs were still in progress at the last read; no terminal result is claimed.

PR #291 contains PISONET-owned paths under experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/ and CORE-owned handover paths PROJECT_HANDOVER.md, docs/handover/CURRENT_STATE.md and CHANGE_LEDGER.md. The release role's own workflow/test work does not silently transfer ownership of those paths. PISONET must own the test fix; CORE must review/own its handover changes; RELEASE reruns its consumer workflow after owner corrections. Master made no changes to these paths.

## 3. COE #26 / #27 destination staging comparison

Source tree: current HARDWARE PR #327 docs head 20c73090f8b3b819e4fb345c336f8e9275feeaaa. Destination #26: b382d233ff06c8791b1028bed3c617cc7b670d12. Separate candidate #27: 009f70cc2c2775039a5fb072c9d4fdedee76cfc7.

| Routed subtree | Current source files | COE #26 destination files | Identical | Divergent | Source-only |
|---|---:|---:|---:|---:|---:|
| ESP32 | 16 | 1 | 0 | 1 | 15 |
| ESP8266 | 20 | 1 | 0 | 1 | 19 |
| QA tests | 47 | 19 | 1 | 3 | 43 |

The ESP32 source sketch blob f89bc561b2093328286d7633da794667b2ab06de differs from COE #26/#27 blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422. The ESP8266 source blob 284f4337bc9e2aa4d78c61f0d7e4c4163ffb0a82 differs from destination blob c8be98f72596681e36a3ad1f8939bf8046c96887. Neither board sketch is byte-identical. The destination Hardware test blob f921c56cecc19cab1989507b9b4ade1f45dac54e is identical in #26 and #27; it is one generic shell test, not the source board-local lab set. It still checks for positive response_sig, |register| and |poll| markers and runs a pure SHA-256 format simulation; it does not verify the current source default-deny poll/disposition behavior or import the source labs.

The QA route has 47 source files (38 shell, 8 Python and one README) versus 19 destination shell files. One relative-path blob is identical; config.sh, integration.sh and security.sh diverge; 43 source files are absent and 15 destination files are extra. This is not complete test migration or equivalent test identity.

### Destination security discrepancies (static source inspection only)

At the exact #26 destination blobs:
- ESP32 calls LittleFS.begin(true); ESP8266 explicitly formats LittleFS after a mount failure. Current source does not format the journal on mount failure.
- Both destination sketches initialize sigOk=true and only verify response_sig when the controller key is nonempty. Empty-key responses therefore bypass that conditional verification path.
- Both allow successful register/poll responses to apply remote configuration.
- Both expose POST /quarantine/clear without an authenticated reconciliation guard.
- Both quarantine functions call clearPending() after the append attempt even if the append did not establish a successful durable write/readback.
- Current source coinPostDispositionVerified() and acceptPollResponse() return false until the approved CORE contract and QA vectors exist.

These are source/tree findings, not observed customer incidents. COE #27's two scoped CI passes ([43079646393](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646393), [43079646264](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646264)) do not establish equivalence and do not place #27 inside #26.

### License and notice scope

Experiments BlazePwifi/LICENSE and COE Pisowifi/LICENSE match at blob 1ee55b94183417be977ca287cd7391f9a6f7e721. The Experiments repository root NOTICE.md exists at f6d92cd21465312be5993631fe26977219be0fb9. COE root NOTICE.md, Hardware/LICENSE and Hardware/NOTICE.md are absent from the inspected destination trees. The Pisowifi license match does not by itself establish Hardware license/NOTICE scope. Licensing-owner review is required before any migration proposal.

### COE #26 CI queue and release dependencies

Direct Actions API readback shows eight #26 runs still queued across five unique workflows; three duplicate queue attempts exist (second Case-collision, Hardware/Shared and Pisowifi runs). All five unique runs have zero jobs. A separate candidate's scoped CI cannot substitute for executable CI on the combined #26 tree.

COE #35 exact-head shared validation [44586100929](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44586100929) ran 117 tests successfully (two intentional skips), then failed all ten appliance profiles because approved site-scoped RFC 4193 /48 authority is missing. Sandbox run [44586100962](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44586100962) passed 14/14 host preflight tests, then failed closed because Bubblewrap is absent. No profile or sandbox release acceptance is established.

## 4. Private registry and execution limits

The Experiments AGENTS.md, README_FIRST, 00_MASTER_PROJECT_PHOENIX directive, BLAZE-COMMS/1 protocol, current Master coordination docs, and public Cloud Artifact Policy / recovery handover were read. The cloud policy explicitly requires reporting BLOCKED if the Drive connector is unavailable.

No Google Drive connector is exposed in this runtime. A recursive Library listing exhausted 1,422 items; canonical BLAZE_PROJECT_REGISTRY_v11_20261027.json was not present. Older snapshots and a newer private checkpoint were not treated as the canonical current registry. No private registry contents or identifiers were copied into GitHub.

Master PR #288 has no exact-head Actions run. The full Master Python suite was NOT RUN. GitHub tree/blob inspection and the linked role CI runs are not a substitute for that suite. The second-ISR lab run is simulated-only; no physical hardware, power-cut or soak test was performed.

## 5. Disposition and next owner actions

- No copy, move, overwrite, rebase, cherry-pick, merge, route promotion, release, signing, secret provisioning, hardware flash, physical test or financial operation was performed.
- Keep COE #26 and #27 OPEN / DRAFT. Do not stage Hardware or QA migration until exact per-file blobs/modes, license/NOTICE scope, test identity/import completeness, Mbed TLS/toolchain compatibility and executable destination CI are reconciled.
- PHX-QA: replace the stale positive poll-marker fixture with negative/default-deny assertions and rerun #327 Full at exact current head 20c73090.
- PHX-PISONET: repair the uninitialized $buildWorkflow variable in its owned ReleaseSigning test; PHX-RELEASE reruns #291 after that owner correction. PHX-CORE reviews the three CORE-owned handover files in #291.
- COE integration/CORE: define approved site-scoped ULA /48 authority before packaging; PHX-INFRA provides an authorized Bubblewrap-capable runner.
- Repository administrators: configure and independently verify branch protections and required checks on Experiments main/development/Master and COE main.
- Registry custodian: restore authorized access to the canonical private v11 registry and newer corrections.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently evidenced.
