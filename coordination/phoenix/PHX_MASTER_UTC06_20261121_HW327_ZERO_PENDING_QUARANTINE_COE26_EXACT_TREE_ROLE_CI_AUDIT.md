# PHX-MASTER UTC06 — exact Hardware quarantine correction, RELEASE pin invalidation, and COE #26 migration audit

**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repo migration provenance
**Audit time:** 2026-11-21T06:00:51Z
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow, or delegation.
**Disposition:** BLOCKED / PR #288 OPEN-DRAFT / COE #26 FROZEN / PRODUCTION NO-GO.

## 1. Live control-plane and exact repository identities

- Control plane: [Experiments issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172). Latest PHX-MASTER checkpoint at audit start was UTC05 comment [#7058209076](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7058209076). No current-date UTC06 PHX-MASTER message ID existed before this work.
- Cleanup gate: [issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266), OPEN, 0/7 checked. Master cleanup inventory remains incomplete; no broad deletion or mass rename.
- Experiments refs: main f4e8a891aed8af86d5fd315d28750a0ac3a7372b; active v0.6 development blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859; legacy v0.5.3 development aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master branch at audit start: phoenix/master-coordination@6fd4d40b979ed0eac87794a7d8cf3d50d904b514.
- [Phoenix Master PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288): OPEN / DRAFT / UNMERGED; base main f4e8a891...; 147 changed paths at audit start, all under coordination/phoenix; no PR-triggered Actions runs.
- COE refs: main a6513ab4412b4c014eee2863e45cbe32d06cb243; [integration PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / FROZEN.
- Exact route manifest: [OWNERSHIP_ROUTES.json](OWNERSHIP_ROUTES.json), blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, source ref main f4e8a891..., destination candidate #26 b382d233..., PHX-MASTER target null. It is not a copy/move authorization.

The current Experiments AGENTS.md, README, the uploaded Master directive, README_FIRST, BLAZE-COMMS/1, current Master coordination documents, and the v0.6 handover policy were re-read. The canonical PROJECT_HANDOVER.md and CURRENT_STATE.md still contain older historical checkpoint sections; live source and exact-head Actions evidence takes precedence under the handover policy. The canonical handover freshness gate is currently failing on Rental and Release branches.

## 2. HARDWARE #327 — new zero-pending quarantine fail-closed correction

Current [HARDWARE PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327):

- Docs/PR head: a873042c2a59a2197e4b4457c18dc75da12a0d02.
- Exact source/test commit: 3292d2a1e207da4241189952eec0e97255a48475.
- Base #326: 58c558fb6a237935214621adc3dee65a10fe1a51.
- The source/test-to-docs comparison is 5 commits ahead / 0 behind; only the new zero-pending quarantine handover document is added after the tested source tree.

### Defect and correction

The source-extracted lab injected a contradictory state: RAM had zero pending pulses while a durable one-shot POST-attempt marker still represented a four-pulse event. The previous quarantine helper returned early on zero pulses, before latching journal recovery. The corrected ESP8266 and ESP32 helpers:

1. Set journalRecoveryRequired=true.
2. Emit an operator-reconciliation diagnostic.
3. Deny the inconsistent disposition.
4. Return without appending a quarantine record or clearing pending/attempt evidence.

This is the correct fail-closed treatment of durable evidence. It is not a normal valid quarantine path and it does not create positive poll or coin admission.

### Exact test and CI evidence

- Test-only RED commit 8b7311b28a4e35ddac1bd9208df40eb6f9721bb2: Quarantine run [#44872068887](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872068887), job 136748590678, expected SOURCE_QUARANTINE_FAIL scenario=2.
- Source fix 3292d2a1e207da4241189952eec0e97255a48475: Quarantine [#44872148862](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872148862), job 136748836404, PASS 36/36; Relay/output [#44872148854](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872148854), jobs 136748836217 / 136748836417, PASS.
- Current docs head a873042c...: Quarantine [#44873105133](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44873105133), job 136751791395, PASS; Relay/output [#44873105198](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44873105198), jobs 136751791490 / 136751791742, PASS.
- Current Full build [#44873105141](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44873105141), validation job 136751791968, FAIL at the QA-owned Missing poll signature check in the ESP8266 sketch. All 15 target/platform jobs completed SUCCESS; downstream simulations, update bundle, signing and publication jobs were skipped.

**Evidence tier:** source-extracted simulation / focused CI verified only. Physical relay, coin selector, flash durability, power-cut recovery and native acceptance remain NOT TESTED.

## 3. RELEASE #291 — previous compatibility PASS is stale for current Hardware tip

Current RELEASE PR #291 is f06ac4df2f61b9c39a03a6ff6009b32948b94778, base #242 734b89d9e7792247e8376335c3f3685500ab3f89.

The Release-owned test blob is e6d1308ad8be08405da74dbd8dd8a1e47b63842f; workflow blob is 3597b451887e1b612ddea3d383093bba734bbc0d. Both pin:

- Hardware source commit 268ca9bde6d3710b418134ffd328060250fad42f.
- ESP32 sketch blob 09c02d589ae15b0c8a4f2a3bbcdee20c41d2cb79.

The old compatibility run [#44862405800](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862405800) completed 3/3 for that immutable old pin. It remains valid for the old pin only.

**New exact-source finding:** comparing the old Release pin 268ca9... to current Hardware source/test 3292d2a... gives 11 commits ahead / 0 behind and includes changes to both ESP32 and ESP8266 production sketches, the quarantine test, firmware lab extractor, and poll-loop lab. The current ESP32 sketch blob is 7ffb7b534c7163678726902946a17b04992950a0, not the Release pin 09c02d...; current ESP8266 sketch blob is c2aa71963eaa0288721f0bb13cff771aaaabc42f.

Therefore the previous UTC05 statement that the 15/15 ESP32 compile directory was identical to the Release pin is superseded for the current Hardware tip. That parity was valid for the older 0f4cf65... source/test snapshot, not the new 3292d2a... source/test commit.

Other current #291 results:

- Full [#44862406950](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862406950): FAIL at canonical handover freshness.
- Windows [#44862405809](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862405809): FAIL at the same freshness gate; Windows build and publisher skipped.

**Next owner action:** RELEASE must refresh its exact Hardware source SHA and sketch blob pin to the approved current #327 source/test, then rerun ESP32 core 3.3.13 and 4.0.0 compatibility, reproducibility, and image identity checks. Master does not edit Release workflow/test files.

## 4. COE #26 — complete exact recursive tree, blob, test and license comparison

Exact source: Experiments Hardware #327 PR head a873042c..., tree dffd123ba73018d0303eb10f8d22c34422c85790, 2,463 entries / 1,884 blobs, truncated=false.

Exact destination: COE #26 b382d233..., tree 8a7d4cf81d7227118b876c1138dd2da12345fefa, 286 entries / 207 blobs, truncated=false.

| Routed path | Source files | Destination files | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 → Hardware/esp32 | 16 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 → Hardware/esp8266 | 26 | 1 | 0 | 1 | 25 | 0 |
| QA tests → Pisowifi/tests | 47 | 19 | 1 | 3 | 43 | 15 |

Exact sketch identities:

- ESP32 source experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino blob 7ffb7b534c7163678726902946a17b04992950a0; COE Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266 source experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino blob c2aa71963eaa0288721f0bb13cff771aaaabc42f; COE Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino blob c8be98f72596681e36a3ad1f8939bf8046c96887.

Additional findings:

- 30 board-local Python labs/helpers exist in the source ESP32/ESP8266 trees; COE Hardware contains zero Python files.
- Three scoped source workflows (phx-hardware-poll-edge-latch.yml, phx-hardware-quarantine-byte-readback.yml, phx-hardware-relay-output-polarity.yml) are not present as equivalent destination workflows; COE has one generic hardware-ci.yml.
- Source Pisowifi LICENSE blob and COE Pisowifi LICENSE blob match exactly: 1ee55b94183417be977ca287cd7391f9a6f7e721.
- Source root NOTICE exists as f6d92cd21465312be5993631fe26977219be0fb9; COE root NOTICE is absent. Hardware-specific LICENSE and NOTICE are also absent. The matching Pisowifi license does not resolve Hardware license/NOTICE scope.
- Source firmware includes durable attempt-marker and journal-recovery state; the COE board copies do not contain the same state. Destination retains older format-on-mount-failure and unconditional quarantine-clear behavior. These are static source findings, not an observed physical/customer incident.

COE #26 still has five workflows QUEUED / zero jobs. No candidate-head destination CI has executed.

**Decision:** keep COE #26 FROZEN. No staging, copying, moving, overwriting, cherry-picking, rebasing, or route promotion.

## 5. Other live role and destination CI

| Owner / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 SUCCESS, scoped. CORE remains with its separate owner. |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK identity #44782114384 PASS; API21/API23 #44782114393 PASS; shared build #44782114390 FAIL at handover freshness and ESP32 core 4.0.0 missing mbedtls/sha256.h. |
| RENTAL #240 / #287 / #289 | a7d113fb... / a4fffd01... / 68928774... | #240 runs #40910311159/#40910311141 PASS; #287 #43754089203 PASS; #289 #43653329229/#43653329235 PASS. These do not override #328's newer shared-build failure. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows #42462978704 SUCCESS, scoped. Physical COM/PnP/race acceptance NOT TESTED. |
| QA #267 / #279 / #290 / #292 | ff536799... / 8f476ef0... / 5c29d159... / 75a3f66d... | #267 #41452247439 SUCCESS; #279 no PR-triggered runs; #290 #43633486963 SUCCESS but native COM lab not invoked; #292 no PR-triggered runs and historical base b1ca02e... |
| COE RELEASE #35 | 9a20f90b7abc9dced9f545733d59801d746bf088 | Case collision #44870760313 PASS; profile #44870760442 FAIL for all 10 profiles because approved site-scoped RFC 4193 ULA /48 is not configured; sandbox #44870760338 FAIL exit 125 because Bubblewrap is not installed in the trusted runner path. |
| COE RELEASE #44 | 582fd5d5e83e36b36546ac28534740298ba94af4 | Case collision #44390136296 PASS; shared/profile #44390136309 PASS; sandbox #44390136327 FAIL. This installation-identity candidate is not site-prefix authority. |

Exact #35 logs show all ten profiles fail with “An approved site-scoped RFC 4193 ULA /48 is required”. The sandbox log explicitly reports RELEASE-BLOCKED: bubblewrap is not installed on this runner and exits 125. These are correct fail-closed gates: do not invent a prefix, install privileged dependencies, or add an unsandboxed fallback.

## 6. Governance, access and test limitations

- Current branch API reads for Experiments main, active v0.6 development, legacy v0.5.3 development, Master branch, and COE main all report protected=false; required status-check enforcement is off. Organization-level ruleset enforcement was not independently verified.
- The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in the authorized Library search. No Google Drive connector is exposed in this runtime. Older registry snapshots were not substituted; no Drive artifact was created.
- The local exact-head Git clone failed because github.com DNS could not resolve. The full Master Python coordination suite was NOT RUN.
- Master exact-head Actions inventory returned no runs. The listed role Actions are real hosted runs at their stated exact commits.
- Git tree/blob comparison is source inspection, not a test execution.
- Cleanup issue #266 remains OPEN, 0/7 checked. The broader duplicate/dead-code inventory is incomplete; no files were deleted or mass-renamed.
- CORE source and canonical product handover were not touched. No parallel CORE implementation was performed.

## 7. Required next owner actions

1. **PHX-QA:** replace the inherited positive poll-signature fixture only after CORE publishes the approved authenticated poll-response and event-bound receipt contract. Preserve negative/default-deny tests; do not weaken Hardware denial.
2. **PHX-CORE:** publish the authoritative authenticated register/poll/receipt contract and refresh canonical PROJECT_HANDOVER/CURRENT_STATE under its separate owner.
3. **PHX-RELEASE:** update #291's stale Hardware source/test SHA and sketch blob pin to current #327 source/test 3292d2a...; rerun both ESP32 cores and reproducibility/image checks. Resolve its own handover gate without editing CORE/PISONET paths.
4. **Site/network authority:** provide the real approved site-scoped ULA /48 for COE #35.
5. **Runner/infrastructure owner:** provision Bubblewrap in the trusted runner image and verify the unprivileged namespace; no privileged install or unsandboxed fallback.
6. **PHX-RENTAL / Hardware / Release owners:** resolve the inherited Mbed TLS 4 header/toolchain incompatibility without cross-role firmware edits.
7. **COE integration owners:** keep #26 frozen until exact per-file provenance, source/test import identity, license/NOTICE applicability, pinned toolchain, and destination CI are independently accepted.
8. **Repository administrator:** establish and verify protected branch/ruleset enforcement before any future trusted release admission.

## 8. Safety disposition

No subsystem source branch was changed. No destination file was staged or copied. No merge, release, signing, secret provisioning, hardware flash, real-payment operation, physical test, or financial migration occurred.

Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and explicit owner-authorized release gates remain mandatory.

**PRODUCTION NO-GO.**
