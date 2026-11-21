# PHX-MASTER UTC00 — exact-head refresh, Hardware fixture split, and COE #26 provenance

**Timestamp:** 2026-11-21T00:51:23Z  
**Role:** PHX-MASTER — architecture, coordination, cross-repository provenance, integration matrix  
**Disposition:** DRAFT REVIEW ONLY · COE #26 FROZEN · PRODUCTION NO-GO  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow, or delegation.

## 1. Live control plane and source refs

- Master directive `00_MASTER_PROJECT_PHOENIX(1).txt`, latest accessible `README_FIRST(20261114-191926).md`, `COMMUNICATION_PROTOCOL(20261114-191925).md`, Experiments `AGENTS.md`, Cloud Artifact Policy, and Storage Recovery Handover were re-read.
- Experiments default `main`: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Active development `blazepwifi-v0.6.0-audit-foundation`: `2fbd2475e9f54878c316fa7cea2f228386b0e859`. Legacy `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master `phoenix/master-coordination`: `21551fedaf945eab26702aebf02da2e6b3ea07e9`; PR #288 base `main@f4e8a891...`, OPEN / DRAFT / UNMERGED, 140 changed paths, all under `coordination/phoenix/`. No Master PR-triggered CI or submitted review was found.
- COE default `main`: `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT / UNMERGED, 205 changed paths.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, source ref main, destination PR #26, PHX-MASTER target `null`.
- CORE implementation remains with the separate **Blaze Production Continuation** automation. No worker source branch or destination source tree was changed.

## 2. HARDWARE #327 — exact current source/test and CI

Current active chain was re-read: #320 `b2b41a3d...` → #322 `50d93e0d...` → #323 `988904e8...` → #326 `58c558fb6a237935214621adc3dee65a10fe1a51` → #327.

- PR #327 branch `phoenix/hardware-prepoll-edge-abort-20261119`, base #326 `58c558fb...`.
- Latest PR/docs head: `cb362dc46521cd78fe1696cbbb1af7e246d90148`.
- Latest source/test commit: `177312434b60509638427cec79bf2d4e11d89d97`.
- Current handover blob: `c469820227c663f7e4ebd2d4b6d58c9241cae938`.
- The source/test split moves the host-lab runtime stubs and scenario builders into separate Python modules while retaining the 29-line import facade. The previous 779-line fixture module becomes 287-line runtime support + 499-line scenarios + 29-line facade; the 447-line runner and both production sketches remain unchanged.
- Focused exact-source CI: Quarantine push [#44845321371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845321371) PASS; Quarantine PR [#44845326974](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845326974) PASS; Relay/output PR [#44845327017](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845327017) PASS.
- Latest Full PR run [#44845752341](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845752341): validation FAILED; all 14 firmware/platform + Android jobs completed SUCCESS; simulations, signed-APK import, update bundle, signing, candidate and publication gates were skipped. This is not a Full pass.
- Exact failure attribution: `tests/controllers.sh` invokes the nested QA-routed `tests/v05_firmware_hardening_test.sh`; that nested script still requires positive `response_sig`, `|register|`, and `|poll|` markers. The log reports `Missing poll signature check` in the ESP8266 sketch. QA must replace this stale positive fixture with source-linked negative/default-deny assertions until CORE publishes an approved authenticated response contract. Do not add a positive poll path or weaken firmware denial.
- The current #327 PR description's leading head/source pins remain stale (older docs/source values); the latest handover and UTC00 Hardware checkpoint identify `cb362dc...` / `177312434...`. HARDWARE should refresh its PR description. Master does not edit Hardware-owned records.

## 3. RELEASE #291 — pinned-source scope, not a stale-artifact false alarm

- RELEASE #291 remains OPEN / DRAFT / UNMERGED at docs/PR head `35d5a221c3746fbebfc47dde56c3b6ad592dfa91`, base #242 `734b89d9e7792247e8376335c3f3685500ab3f89`. Release workflow/test source head is `5ccf617a43412dabeb11d101c67bd3affc0db471`.
- The compatibility workflow pins HARDWARE source/test `0f365dada855368ea3fdfb522768892cf23cc7ea` and ESP32 sketch blob `ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7`.
- Current HARDWARE source/test is now `177312434...`, two commits ahead. The exact compare reports only the host-lab fixture module split and its handover; no production `.ino` changed. The ESP32 sketch blob is byte-identical at both source commits: `ae0da8e...` (71,103 bytes).
- Current PR compatibility run [#44843256993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44843256993) completed 3/3 SUCCESS (ESP32 core 3.3.13, ESP32 core 4.0.0, provenance suite). This remains valid for the exact pinned firmware blob/source snapshot. It does **not** test the latest host-lab fixture refactor or prove a different branch tip was compiled. Do not call the old pin the current #327 source/test head; re-pin and rerun only if latest test-harness provenance is required.
- Full run [#44843257000](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44843257000) and Windows run [#44843256960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44843256960) fail at the canonical project handover freshness gate: source/workflow change `.github/workflows/blazepisonet-softtimer-release.yml` is newer than `PROJECT_HANDOVER.md`; last checkpoint `adcae8141e673dc2147fcad50521ef3a23084d71`. Full target builds passed, but validation stopped downstream gates; Windows build and publisher were skipped. The canonical handover owner/CORE coordination must refresh the record; RELEASE must not bypass it.

## 4. Other live owner PRs and exact-head CI

| Owner / PR | Exact live ref | Current CI / boundary |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Core lab [#42698124709](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698124709) and build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; CORE remains with separate automation. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070`, base #289 `68928774...` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; shared build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAILS at handover freshness and ESP32 core-4.0.0 missing `mbedtls/sha256.h`. Rental retains Android/APK ownership. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Native COM lab [#42462975460](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462975460) and Windows release [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; physical USB-RS232 adapter/PnP/race acceptance NOT TESTED. |
| QA #290 / #292 | `5c29d159...` / `75a3f66d...` | #290 Windows run [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS but does not invoke the new native COM lab. #292 is based on historical Master `b1ca02e...` and has zero PR-triggered runs; QA must replay/rebase and run exact-head CI. |
| COE RELEASE #35 | `580855b6a45a6d3cf506a6aa9320bc4782efc246` | Shared contracts run [#44820473859](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44820473859) FAILS at missing approved site-scoped ULA /48 authority; sandbox [#44820473769](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44820473769) FAILS because Bubblewrap is unavailable; case-collision [#44820473809](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44820473809) PASS. No ImageBuilder artifact. |
| COE RELEASE #44 | `582fd5d5e83e36b36546ac28534740298ba94af4` | Shared CI [#44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309) and case guard [#44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296) PASS; sandbox [#44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) FAILS because Bubblewrap is absent. Per-appliance ULA does not establish site-level prefix authority. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Pisowifi overlay/shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; no financial acceptance or activation authority. |

## 5. COE #26 — fresh exact-tree, blob, test, licence, and CI comparison

- Experiments source tree at HARDWARE source/test `177312434...`: 2,453 entries; COE #26 destination tree at `b382d233...`: 286 entries (both recursive trees complete, not truncated).
- Routed board subtrees: source ESP32 17 entries vs destination 2; source ESP8266 24 entries vs destination 2. Board-local Python labs/helpers: 28 source vs 0 destination.
- Routed QA tests: 47 source vs 19 destination. Relative path overlap: 4; exact blob identities: 1; same-path divergent blobs: 3; source-only: 43; destination-only: 15.
- Firmware sketch blobs differ: ESP32 source `ae0da8e2...` vs destination `3cc7ec54...`; ESP8266 source `a1f12edc...` vs destination `c8be98f7...`.
- Hardening tests differ: source `tests/v05_firmware_hardening_test.sh` blob `41211b2c...`; destination `Hardware/tests/test_firmware_hardening.sh` blob `f921c56c...`. Both still contain positive `response_sig`, `|register|`, and `|poll|` assertions conflicting with the current deny-only contract.
- Three source PHX-HARDWARE workflows are represented by one generic destination `hardware-ci.yml`; source/destination workflow behavior is not established as equivalent.
- Source Pisowifi LICENSE and destination `Pisowifi/LICENSE` are exact blob match `1ee55b94...`. Source root `NOTICE.md` blob `f6d92cd2...` exists; destination root NOTICE is absent. Applicability/scope remains unresolved, not a legal conclusion.
- COE #26 Actions API returns eight QUEUED runs across five distinct workflows; a sampled queued run has zero jobs. No destination CI execution occurred.
- The PR description still states 95% software release readiness; this is not supported by the current tree/CI/provenance evidence and must not be treated as an acceptance result.
- No file copy, move, overwrite, cherry-pick, rebase, route promotion, migration staging, merge, or destination edit occurred. Routing manifest remains DRAFT_REVIEW_ONLY and Master target null.

## 6. Governance, storage, and test limitations

- Control plane #172 remains OPEN. Cleanup #266 remains OPEN with 0/7 checkboxes complete.
- Experiments `AGENTS.md` blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f` was read at main and Master refs. Cloud Artifact Policy blob `5e503925750c4e511314e4b7624579d82f60aae2` and Storage Recovery Handover blob `a15f14cb3baf46424b820e1a921462794422f06b` were read. Policy requires the owner-private registry before artifact operations.
- No Google Drive connector is exposed in this runtime. Accessible Library search/list surfaced older registry snapshots (v3–v7) and a generic registry, not the requested private v11 file or newer corrections. No older snapshot was substituted; no Drive operation or private-record disclosure occurred. Registry access remains BLOCKED.
- Local `git ls-remote` failed because this runtime could not resolve `github.com`; full Master Python suite NOT RUN. GitHub tree/blob/CI inspection is not represented as local test execution.
- Branch metadata reports `protected=false`; repository rulesets endpoint returned an empty list, while effective organization-level protection remains unverified.
- No native hardware, power-cut, real-device, payment, signing, flash, or soak test was performed.

## 7. Required next actions

1. QA: replace the nested positive poll-signature fixture in `tests/v05_firmware_hardening_test.sh` with source-linked default-deny tests; rerun HARDWARE #327 Full.
2. HARDWARE: refresh #327 PR description with docs head `cb362dc...` and source/test `177312434...`; retain deny-only firmware.
3. RELEASE: keep the compatibility PASS scoped to exact pinned blob `ae0da8e...`; re-pin to `177312434...` only if current host-lab source/test provenance is required, then rerun exact-source matrix.
4. Canonical handover owner / CORE coordination: refresh `PROJECT_HANDOVER.md` after the exact PISONET release-workflow change; rerun RELEASE #291 Full/Windows and RENTAL #328 shared build.
5. COE integration: keep #26 frozen until exact source blobs, test identities, licences/notices, import completeness, and destination CI are accepted by owners.
6. Registry custodian: restore authorized v11/newer-correction access; repository administrator: independently verify effective branch protection.

**Production remains NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates remain mandatory.
