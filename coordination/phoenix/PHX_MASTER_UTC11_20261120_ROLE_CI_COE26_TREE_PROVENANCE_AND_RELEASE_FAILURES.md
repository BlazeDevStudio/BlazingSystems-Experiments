# PHX-MASTER UTC11 — exact owner-head CI, COE #26 tree provenance, and release failures

**Audit time:** 2026-11-20 11:13:56Z  
**Role:** PHX-MASTER — master coordination, architecture/interface contracts, cross-repository provenance and integration matrices only.  
**Execution boundary:** Strict NO CODEX. No Codex application, CLI, API, agent, workflow or delegation. No subsystem source, COE destination, payment, signing, hardware or release action.

## 1. Exact starting refs and scope

This audit started from Experiments PR #288 / branch phoenix/master-coordination at 1c9eba9d8af0fdf8eef04e239c4f31516743c30f, against main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b. The branch and PR heads matched at readback; PR #288 was OPEN / DRAFT. This update is limited to coordination/phoenix/.

| Ref | Exact HEAD | Branch API protection |
|---|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b | protected=false; required-check enforcement off |
| v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 | protected=false; required-check enforcement off |
| v0.6 audit-foundation comparison ref | 2fbd2475e9f54878c316fa7cea2f228386b0e859 | protected=false; required-check enforcement off |
| phoenix/master-coordination | 1c9eba9d8af0fdf8eef04e239c4f31516743c30f | protected=false; required-check enforcement off |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | protected=false; required-check enforcement off |

The v0.5.3 and v0.6 refs remain distinct; do not collapse them into one development branch label. Effective organization-level admission controls are not established by these branch API results.

## 2. Current owner PRs and exact-head CI

| Role | PR / exact current HEAD | Exact-head CI evidence | Disposition / owner boundary |
|---|---|---|---|
| PHX-CORE | #252 / c82705f2de865c89ab733b10efa84f26f56a5cc4 | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS | Scoped CI only. The separate active CORE continuation retains all CORE source ownership; this run did not touch CORE. |
| PHX-RENTAL | #289 / 68928774d0d7cf65adb26bc6b54199a3159d066c | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229), [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS | Scoped CI only; native Device Owner acceptance remains unproven. |
| PHX-PISONET | #255 / d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS | Scoped CI only. PISONET owns the two PISONET paths present in RELEASE #291. |
| PHX-QA | #290 / 5c29d15994cee1279058f1eca12f2a3180704292 | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS | This run does not invoke NativeComInterfaceHandleLab. |
| PHX-QA | #292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head PR workflow run returned | NOT CI-VERIFIED at this exact head. |
| PHX-HARDWARE | #327 / 89442ce681df965b16c80f73055236a0d842fe0c; base #326 / 58c558fb6a237935214621adc3dee65a10fe1a51 | [Quarantine #44722725391](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44722725391) PASS; [relay/output #44722725315](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44722725315) PASS; [Full #44722725399](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44722725399) FAIL | Full validation fails at Controller protocol parity: “Missing poll signature check” in the ESP8266 sketch. This is the QA-owned stale positive fixture; do not weaken the firmware's default-deny behavior. |
| PHX-RELEASE | #291 / b883662b4faebe05973c9a8bf7ff7ac54d978496 | [Windows #44724653086](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44724653086) FAIL; [ESP32 compatibility #44724652962](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44724652962) FAIL; [Full #44724653108](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44724653108) CANCELLED | See the exact failure analysis below. No signing or publishing occurred. |

### HARDWARE #327 — current Full failure

The two focused jobs are terminal PASS at the current #327 head. The Full run's validation job fails at “Controller protocol parity” because the inherited check still requires a poll-signature marker in the ESP8266 sketch. The job log names the source path and exits 1. The other 13 firmware/platform target jobs and Android build completed successfully; downstream validation/simulation and production sign/publish gates were skipped after the validation failure. This does not establish physical relay, pulse, power-cut or device-soak acceptance. QA must replace the stale positive-presence assertion with source-linked negative/default-deny behavior tests. Hardware remains owner of its firmware and labs.

### RELEASE #291 — current failures supersede earlier terminal labels

1. Windows run #44724653086: handover and package-parity self-test passed. The PISONET-owned tests/ReleaseSigning/negative-selftest.ps1 then failed because $buildWorkflow is unset. The #291 changed-file list includes both PublisherMockCli.ps1 and negative-selftest.ps1 under the PISONET-owned SoftTimer tree. PISONET must own or explicitly approve that correction; PHX-MASTER and RELEASE must not silently take over those paths.
2. ESP32 compatibility run #44724652962: the 6 synthetic ELF section parser tests and 10 synthetic section-comparison tests pass, then both core legs fail importing verify_esp32_source_date_epoch from .github/scripts/test_verify_esp32_source_date_epoch.py (ModuleNotFoundError). This is an exact-head RELEASE test/import-path failure before the current two-core image comparison completes. Do not relabel it as a new reproducibility result. The earlier byte-difference finding remains historical evidence and still requires a fresh exact-head comparison after this import failure is corrected.
3. Full run #44724653108: ESP8266 and ESP32 compile jobs passed, but validation and Android were cancelled; downstream simulations, candidate gate, sign handoff and publish jobs were cancelled or skipped. This is NOT a Full PASS and provides no signing/publishing evidence.

RELEASE owns its ELF tooling and import-path correction. PISONET owns the SoftTimer negative self-test. The role boundary is preserved.

## 3. Exact current #327 → COE #26 tree and blob comparison

Source: Experiments #327 exact head 89442ce681df965b16c80f73055236a0d842fe0c, tree 50caee5c635b7e2289afb1fe7ec9dcf6e7105ed1.  
Destination: COE integration PR #26 exact head b382d233ff06c8791b1028bed3c617cc7b670d12, tree 8a7d4cf81d7227118b876c1138dd2da12345fefa.  
Both recursive Git trees were complete and not truncated: 2,435 source entries and 286 destination entries.

| Item | Exact source #327 | Exact destination #26 | Result |
|---|---|---|---|
| ESP8266 sketch | experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino — blob 3ff575f5cd879c021407849578854b74a2d460bd | Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino — blob c8be98f72596681e36a3ad1f8939bf8046c96887 | Different |
| ESP32 sketch | experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino — blob 849a2c63d75bbbcda58e1a0a7fc55e7c047ea26e | Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino — blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | Different |
| Board-local Python labs/helpers | 25 total across ESP8266 and ESP32 | 0 Hardware Python files | No exact test import |
| Hardware tests | 25 source Python labs/helpers | One generic shell test: Hardware/tests/test_firmware_hardening.sh, blob f921c56cecc19cab1989507b9b4ade1f45dac54e | Not equivalent |
| Scoped Hardware workflows | Three: poll-edge latch f1dfa7fd37630d8ab5e32681eb92f67ba4c6dc05; quarantine byte readback 3ad7d6e40b6c9a48e55357ac39bf74d8c4b8d275; relay/output polarity 9fee8f85dcd775713aa2c49f87f7e0b7f3b32e04 | One generic hardware-ci.yml, blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 | Not workflow parity |
| Project MIT license | experiment/openwrt/BlazePwifi/LICENSE, blob 1ee55b94183417be977ca287cd7391f9a6f7e721 | Pisowifi/LICENSE, same blob 1ee55b94183417be977ca287cd7391f9a6f7e721 | Exact sibling match only |
| Root NOTICE | Source root NOTICE.md, blob f6d92cd21465312be5993631fe26977219be0fb9 | No root NOTICE.md | Missing destination notice |
| Hardware-specific license/notice | No separate Hardware license file in source tree | No Hardware/LICENSE or Hardware/NOTICE.md | Scope remains unresolved |

The sibling Pisowifi/LICENSE match does not independently establish notice/license scope for the Hardware subtree. Test identities, import completeness, dependency closure, workflow parity, rollback and behavior equivalence remain unproven.

### COE #26 destination CI and adjacent candidates

COE main remains a6513ab4412b4c014eee2863e45cbe32d06cb243. Integration #26 remains OPEN/DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12. Its five workflows are all QUEUED with zero jobs: #43096752609, #43096752632, #43096752800, #43096752563 and #43096752557. There is no destination acceptance.

Adjacent candidates remain separate and unassigned:
- COE #35 head 7b9706d898fb5f36c6ed96504aefd04dc59bdc1b: case guard #44617783021 PASS; ImageBuilder sandbox #44617781877 FAIL; shared Hardware/Contracts #44617782050 FAIL.
- COE #48 head 8286548e395366f2332830025fed00ceebdfb24a: Stage 5 #44643670696 PASS; case guard #44643670679 PASS; shared Hardware/Contracts #44643670685 FAIL.
- COE #49 head aeb8ff11b2f5db9a5f86280ab62ab988245f3919: Stage 5.1 #44646341873 PASS; case guard #44646341992 PASS; shared Hardware/Contracts #44646341922 FAIL.

#48 and #49 are not based on COE main or #26 and have no route in the ownership manifest. #49 remains audit-only; HARDWARE declined implementation ownership. No source blob, license, test, workflow or file was copied, moved, staged, rebased or cherry-picked.

## 4. Routing, cleanup and registry status

The current ownership manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, with PHX-MASTER destination null. No route or ownership was promoted.

Issue #266 remains OPEN. The Master cleanup checkbox remains unchecked because the broader duplicate/dead-code inventory is not complete; this activation performed coordination/provenance review only, not source cleanup or mass movement.

The private Google Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections could not be read through the available Library/connector surface. No Google Drive connector was exposed in the connected tool list, and exact-title Library search did not return the requested v11 file. No older registry snapshot was substituted. No private Drive IDs or contents were disclosed. The repository AGENTS.md storage policy was read; no archive or new Drive artifact was created.

## 5. Test execution and limits

- Executed: exact GitHub PR/branch metadata readback, current-head Actions status/job/log inspection, and complete recursive source/destination tree retrieval with exact blob comparisons.
- Owner-run CI: the role-specific run URLs above. These are not Master test executions.
- NOT RUN: coordination/phoenix/verify_coordination.py and the Master unittest suite. A local shallow Git clone was attempted against the exact Master branch but failed with “Could not resolve host: github.com”; therefore no local Python suite result is claimed.
- No Master-specific Actions run was surfaced for this branch. Source/tree inspection is not a test pass.
- Branch API reports protected=false and required-check enforcement off for Experiments main, both development refs, Master, and COE main. Administrator must establish and independently verify effective protected admission.

## 6. Next owner actions

1. PHX-QA: replace the stale positive poll-signature fixture with source-linked negative/default-deny assertions; rerun the exact #327 Full workflow without relaxing firmware behavior.
2. PHX-RELEASE: repair the missing verify_esp32_source_date_epoch import/module path, then rerun both exact-core section and byte-comparison jobs.
3. PHX-PISONET: correct and test the uninitialized $buildWorkflow in its own negative-selftest.ps1; RELEASE must not edit PISONET-owned files.
4. PHX-RELEASE: after the import failure is fixed, rerun the exact current-source two-core reproducibility comparison; keep the comparator byte-for-byte fail-closed.
5. COE integration owner and source owners: keep #26 frozen until exact source/license/import/test/workflow provenance and destination CI are accepted.
6. Repository administrator: enable required review/check admission and re-read the effective ruleset/branch-protection state.
7. Registry custodian: restore authorized read access to private v11 and newer corrections.
8. PHX-MASTER: rerun the coordination suite when an authenticated checkout/runtime is available; preserve CORE ownership with the separate CORE continuation.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified.