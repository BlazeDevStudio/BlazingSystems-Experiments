# PHX-MASTER UTC09 — live role-head, terminal CI and COE #26 exact-source reconciliation

**Disposition:** MASTER-ONLY · PR #288 OPEN/DRAFT · COE #26 FROZEN · PRODUCTION NO-GO  
**Audit start:** phoenix/master-coordination@129aa462322fb0bff2aedec524f42bb829fd7f4b  
**Base:** Experiments main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**Scope:** coordination/phoenix/, architecture/interface contracts, cross-repository provenance and integration matrices. No subsystem source, tests, workflows, route manifest or COE destination files were changed.

## 1. Live instruction and branch readback

Read the uploaded 00_MASTER_PROJECT_PHOENIX(1).txt, README_FIRST, BLAZE-COMMS/1, current Experiments AGENTS.md, README.md, Cloud Artifact Policy, Cloud Storage Recovery Handover, issue #172, cleanup issue #266, PR #288, current Master coordination documents and ownership route manifest.

- Experiments default main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Active audit/development reference: blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Legacy v0.5.3 development: blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master PR #288: phoenix/master-coordination@129aa462322fb0bff2aedec524f42bb829fd7f4b, base main@f4e8a891..., OPEN/DRAFT, 123 changed paths, all under coordination/phoenix/.
- COE default main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration PR #26: b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN/DRAFT, 205 changed paths, five workflows queued and zero jobs.
- OWNERSHIP_ROUTES.json: blob e4db324315a1b3543fec17a148fbf960170fcb29; DRAFT_REVIEW_ONLY; PHX-MASTER target null.
- Issue #266 remains OPEN; the broad Master duplicate/dead-code inventory is incomplete, so its Master cleanup checkbox remains unchecked.
- Experiments AGENTS.md blob d8777e3b58efc41caa5aa3c969c932aee9103d5f; README.md blob feb909e3f74ffb7b5b22df50399ccd127ada3b95; Cloud Artifact Policy blob 5e503925750c4e511314e4b7624579d82f60aae2; Cloud Storage Recovery Handover blob a15f14cb3baf46424b820e1a921462794422f06b.

## 2. Current role PR heads and exact-head CI

| Role | Current PR / head | Exact-head CI | Disposition |
|---|---|---|---|
| CORE | #252 c82705f2de865c89ab733b10efa84f26f56a5cc4 | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS | Scoped only; separate CORE continuation retains all implementation ownership. |
| RENTAL | #289 68928774d0d7cf65adb26bc6b54199a3159d066c | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS | Scoped CI only; no physical Device Owner acceptance. |
| PISONET | #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS | Scoped Windows CI only; native COM bench remains unverified. |
| HARDWARE | #327 8246afb3d65c5af631dba35d45ef68e114269287; base #326 58c558fb6a237935214621adc3dee65a10fe1a51 | Quarantine [#44707526434](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44707526434) FAIL; relay/output [#44707526640](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44707526640) FAIL; Full [#44707526487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44707526487) FAIL | New exact-head focused lab failures plus QA-owned poll-signature fixture failure; firmware must remain default-deny. |
| QA | #290 5c29d15994cee1279058f1eca12f2a3180704292; #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS but does not invoke NativeComInterfaceHandleLab; #292 has no exact-head run | Native COM and independent backend acceptance remain unverified. |
| RELEASE | #291 f1126706a79a03e69e1374b12e86caae3260be6a | Full [#44706677338](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44706677338) PASS for non-production build/simulation; compatibility [#44706677394](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44706677394) FAIL; Windows [#44706677279](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44706677279) FAIL | Parser checks now pass; strict image reproducibility still fails. PISONET owns the failing negative-selftest path. |

### HARDWARE #327 — newly exposed exact-head failures

The current docs/PR head advanced beyond the previous UTC07 handover. The exact current runs show:

- Quarantine #44707526434, job 136190721506: FAIL. The ESP8266 mutation named missing-transition-edge-ack was not rejected; the ESP32 exact-source case reports that an existing prior journal fault was treated as a safe ingress transition. The log also records NVS_NAMESPACE_OPEN_FAILURE_NOT_HANDLED with 13 reads / 1 write and NVS_BOOT_STRING_READ_ERROR_TRUSTED_POLARITY for ssid.
- Relay/output #44707526640, job 136190722166: FAIL on source-output-polarity; the ESP32 boot-polarity subjob passes, but the shared poll-fault/coin-pulse checks reproduce the prior-journal-fault and missing-transition-edge-ack failures.
- Full #44707526487: the validate job fails at the inherited QA-owned Missing poll signature check. All 13 firmware/platform target jobs and Android completed successfully; downstream simulation/signing/publishing remain skipped.

These are source-extracted CI/lab findings, not physical evidence. PHX-HARDWARE must investigate the current exact-head regressions; PHX-QA still owns the stale positive poll-signature assertion. Master changed no Hardware source or test.

### RELEASE #291 — parser regression superseded by actual reproducibility failure

Current head f1126706... runs the compatibility jobs past the POSIX nm parser and into the actual two-clean-build image comparator:

- ESP32 core 3.3.13: 1,044,096-byte images; 72 differing bytes across ranges 176-184, 186-207, 9665, 9667-9668, 9670-9671, 761836-761838 and 1044063-1044095.
- ESP32 core 4.0.0: 1,098,176-byte images; 69 differing bytes across ranges 176-207, 9711, 9713-9714, 9716-9717 and 1098143-1098175.

Both include app_desc.app_elf_sha256 and derived checksum/appended SHA differences; additional bytes remain in image content. The root cause is not established. Preserve strict byte-for-byte comparison; do not normalize or suppress differences.

The Windows run installs and verifies .NET SDK 8.0.425 and passes PackageParity self-tests, release concurrency, immutable action pin and checkout credential checks. It then fails in PISONET-owned experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1 because $buildWorkflow is unset. The publisher and downstream signing/build jobs are skipped. PISONET owns this path; Master did not edit it.

The non-production Full run succeeds for its build/simulation jobs, while production signed-APK import, sign handoff and publishing are skipped. This is not a release approval.

## 3. COE candidate status

| Candidate | Exact head / base | Current CI | Decision |
|---|---|---|---|
| #26 integration | b382d233ff06c8791b1028bed3c617cc7b670d12 / main a6513ab... | Five workflows queued, zero jobs | FROZEN; no destination acceptance. |
| #35 ImageBuilder | 7b9706d898fb5f36c6ed96504aefd04dc59bdc1b / #31 59ed44d... | Case guard [#44617783021](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617783021) PASS; sandbox [#44617781877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617781877) FAIL closed because bubblewrap is absent; shared [#44617782050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617782050) FAIL | Ten appliance profiles require an approved site-scoped RFC4193 ULA /48; ESP32 compile was skipped. |
| #49 INTERCON Stage 5.1 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 / #48 8286548e... | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) PASS; case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared Hardware [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL | ESP8266 compile passes; ESP32 fails because mbedtls/sha256.h is missing under core 4.0.0. PHX-HARDWARE explicitly declined implementation ownership and ACKed audit-only. No manifest route exists. |

## 4. Fresh exact-source comparison: HARDWARE #327 versus COE #26

Fetched complete recursive Git trees at the exact current candidate refs:

- Experiments #327 tree: 3ddffcb9e4542a3cc73aa3e4efe382ff954a390b (2,432 entries; not truncated).
- COE #26 tree: 8a7d4cf81d7227118b876c1138dd2da12345fefa (286 entries; not truncated).

| Item | Experiments #327 | COE #26 | Result |
|---|---|---|---|
| ESP8266 sketch | 3ff575f5cd879c021407849578854b74a2d460bd | c8be98f72596681e36a3ad1f8939bf8046c96887 | Different blobs |
| ESP32 sketch | cc2dc4dada46f8447321168f12aae90cdd46fd5e | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | Different blobs |
| Board-local Python lab files | 24 | 0 under Hardware/ | No exact test identity/import |
| Hardware CI workflows | 3 scoped workflows | 1 generic hardware-ci.yml | Not equivalent |
| Product MIT license | experiment/openwrt/BlazePwifi/LICENSE blob 1ee55b94183417be977ca287cd7391f9a6f7e721 | Pisowifi/LICENSE same blob | Sibling license exact-match only |
| Root notice | source NOTICE.md blob f6d92cd21465312be5993631fe26977219be0fb9 | no root NOTICE.md | Missing destination notice |
| Hardware-specific notice/license | source subtree has no separate Hardware license file | Hardware/LICENSE and Hardware/NOTICE.md absent | Scope not established |

The destination has one generic Hardware shell test and zero Hardware Python lab files. Source workflow identities are phx-hardware-poll-edge-latch.yml, phx-hardware-quarantine-byte-readback.yml and phx-hardware-relay-output-polarity.yml; these three are absent from COE #26. The identical Pisowifi MIT file does not independently establish the license/notice scope for Hardware.

This is a read-only provenance audit. No copy, move, cherry-pick, rebase, staging, route promotion or migration was performed. The route manifest remains pinned to source main f4e8a891... and candidate #26 b382d233..., DRAFT_REVIEW_ONLY. COE #48/#49 remain outside the manifest.

## 5. Governance, private registry and test execution

- Experiments main branch API reports protected=false; repository rulesets endpoint returned an empty list. Branch-protection details endpoint returned 403, so effective organization-level enforcement remains UNKNOWN.
- The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not present in the available Library inventory; only older v3-v7 snapshots were exposed. No general Google Drive connector was available. No older snapshot was substituted and no private registry contents or IDs were published.
- Local git ls-remote failed because the container could not resolve github.com. Full Master Python suite and Master Actions were NOT RUN.
- A separate local static check of the exact route-manifest readback passed 8/8 assertions: schema, source ref, destination candidate, review-only status, single coordination-only Master route, unique source routes, manual-copy denial and no COE #48/#49 routes. This is not the repository test suite.
- No Codex app, CLI, API, agent or workflow was used. CORE implementation ownership remained with its separate continuation owner.

## 6. Exact next actions

1. PHX-HARDWARE: investigate the current #327 exact-head prior-journal-fault, NVS namespace-open and transition-edge failures; publish an updated source/test SHA and rerun focused CI.
2. PHX-QA: replace the stale positive poll-signature fixture with source-exact negative/default-deny assertions; rerun #327 Full without weakening firmware.
3. PHX-PISONET: fix the unset $buildWorkflow variable in its own negative-selftest.ps1 path and coordinate the existing cross-role file in #291.
4. PHX-RELEASE: preserve both reproducible-build outputs and linker maps; attribute the remaining ESP32 image differences; keep the strict comparator fail-closed.
5. COE integration owner: keep #26 frozen until per-file source/destination blobs, license/notice scope, dependency/import completeness, test identities, workflow parity and completed destination CI are independently verified.
6. Repository administrator: establish and verify protected release admission controls.
7. Registry custodian: restore authorized access to private v11 and newer corrections.
8. PHX-MASTER: run the full coordination suite when an authenticated local checkout/network path is available; keep issue #266 cleanup incomplete until the broader duplicate/dead-code inventory is finished.

No subsystem source or test branch was changed. No merge, release, signing, secret provisioning, flashing, physical test, payment operation, financial migration or customer cutover occurred.

**PRODUCTION NO-GO** remains mandatory pending an independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, a 30-device/24-hour soak and owner-authorized release gates.
