# PHX-MASTER UTC08 — 2026-11-20T08:40Z exact-head release, ownership and COE #26 provenance audit

**Disposition:** MASTER-ONLY · PR #288 OPEN/DRAFT · COE #26 FROZEN · PRODUCTION NO-GO  
**Audit start:** `phoenix/master-coordination@737f42b40cc25c718aa1f1964165f53a50988bd0`  
**Base:** Experiments `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Role boundary:** `coordination/phoenix/`, architecture/interface contracts, cross-repository provenance and integration matrices only. No subsystem source, test, workflow or destination path was edited.

## 1. Instructions and live control-plane readback

Read the supplied `00_MASTER_PROJECT_PHOENIX(1).txt`, current `README_FIRST`, BLAZE-COMMS/1 protocol, Experiments `AGENTS.md`, issue #172, cleanup issue #266, PR #288, current coordination documents and routing manifest.

- Experiments default `main`: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- `blazepwifi-v0.6.0-audit-foundation`: `2fbd2475e9f54878c316fa7cea2f228386b0e859` (comparison-only; not promoted).
- Master PR #288: `phoenix/master-coordination@737f42b40cc25c718aa1f1964165f53a50988bd0`, base `main@f4e8a891...`, OPEN/DRAFT, 122 paths, all under `coordination/phoenix/`.
- COE default `main`: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT, 205 paths, five workflows queued and zero jobs.
- `OWNERSHIP_ROUTES.json`: blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`. No route was changed.
- Issue #266 remains OPEN; the Master cleanup checkbox remains unchecked because the broader duplicate/dead-code inventory is incomplete.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were searched by exact name and variants in the available Library surface; only older v3–v7 snapshots appeared. No Google Drive connector was exposed. No older snapshot was substituted and no private data was published.

## 2. Exact owner PRs and current exact-head CI

| Role | PR / exact head | Current exact-head evidence | Owner boundary / next action |
|---|---|---|---|
| PHX-CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS, scoped | Separate CORE continuation owns implementation; Master does not edit CORE source. |
| PHX-RENTAL | #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS, scoped | No physical Device Owner acceptance. |
| PHX-PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS, scoped | Native COM bench remains unverified; owns the Windows SoftTimer tree. |
| PHX-HARDWARE | #327 docs/head `d9072ce36e87a4bb1b9f1f5f888478a3c35fe236`; source/test `726981b49fb415fd10b764cbb8c386a00fcdbcf1`; base #326 `58c558fb6a237935214621adc3dee65a10fe1a51` | Quarantine [#44697742089](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697742089) PASS; relay [#44697742266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697742266) PASS; Full [#44697742114](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697742114) FAIL | QA-owned `Missing poll signature check`; keep firmware default-deny. |
| PHX-QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS but does not invoke `NativeComInterfaceHandleLab`; #292 has no exact-head run | Replace stale positive poll fixture with source-exact negative/default-deny assertions; independently run native COM lab. |
| PHX-RELEASE | #291 `e6538892ea91aa864f78f88524dcc3f576b7e17a`; source/test `a7ed8ff01c5b7d2a6621cbe31eb45063fef4bf88`; base `734b89d9e7792247e8376335c3f3685500ab3f89` | Compatibility [#44702796127](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44702796127) FAIL; Full [#44702796235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44702796235) 26 PASS / 0 FAIL / 4 production jobs SKIPPED; Windows [#44702796072](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44702796072) FAIL | RELEASE owns ELF/compatibility workflow; PISONET owns `negative-selftest.ps1`; no cross-role edit by Master. |

### RELEASE #291 — parser fix is green; real reproducibility remains red

The POSIX size-less `nm` parser correction is present at source/test SHA `a7ed8ff...`. Both compatibility jobs pass their source pin, archive, core install, ELF section/symbol parser and synthetic comparator tests, then reach the actual two-clean-build image comparison and fail closed:

- ESP32 core 3.3.13: image size 1,044,096; 67 differing bytes; ranges `176-207`, `9670-9671`, `1044063-1044095`.
- ESP32 core 4.0.0: image size 1,098,176; 68 differing bytes; ranges `176-207`, `9714`, `9716-9717`, `1098143-1098175`.

Bytes 176–207 are the embedded `app_desc.app_elf_sha256`; the final checksum/appended SHA ranges follow the differing image. The remaining one/two/three bytes are in `.flash.rodata`. Symbol attribution is `NEAREST_ONLY` with no containing sized symbol; the root cause is **not established**. Do not normalize hashes, ignore timestamps, alter the linker, or relax byte-for-byte comparison.

The non-production Full build has 26 successful jobs and four skipped jobs: production signed-APK import, production sign handoff, release publication and prerelease publication. This does not clear the compatibility failure or authorize signing/publishing.

### PISONET ownership collision inside RELEASE PR #291

The 22-path #291 diff includes `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1`, which is inside the PISONET-owned tree. Its base blob is `8aba7adfb40c44ecb2bcb2ddbe5de43cb800e973`; its #291 head blob is `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`. The current Windows job fails at line 115 because `$buildWorkflow` is read before it is initialized. The PISONET role owns this path; RELEASE's latest activation changed only its own files, but the overall #291 PR diff still contains the PISONET-owned test change. PISONET must own/approve the correction or explicitly resolve the scope with RELEASE. Master did not edit the file.

## 3. COE #26 exact source/destination provenance

The source tree at HARDWARE #327 head `d9072ce...` has tree `08735c3b42d68e8c43406ced5aafc5b57ed4d985`; COE #26 has tree `8a7d4cf81d7227118b876c1138dd2da12345fefa`.

| Item | Experiments source #327 | COE #26 destination | Result |
|---|---|---|---|
| ESP8266 sketch | `b956bc031df32ef69350dec368eaa91073b5a638` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different blobs |
| ESP32 sketch | `1458f32881d3b340f1101dd0215618b54c1b688b` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different blobs |
| Board-specific Python labs | 25 across ESP8266/ESP32 | 0 Python files under `Hardware/` | Not imported as identical tests |
| Destination Hardware test | Source has 25 individual lab identities | `Hardware/tests/test_firmware_hardening.sh`, blob `f921c56cecc19cab1989507b9b4ade1f45dac54e` | One generic shell test, not equivalent to 25 labs |
| Three scoped Hardware workflows | `phx-hardware-poll-edge-latch.yml` blob `f1dfa7fd37630d8ab5e32681eb92f67ba4c6dc05`; quarantine blob `3ad7d6e40b6c9a48e55357ac39bf74d8c4b8d275`; relay blob `9fee8f85dcd775713aa2c49f87f7e0b7f3b32e04` | Those three paths absent; only generic `hardware-ci.yml` blob `fe79adbdb3745a22c5ef6d1f0c87c868b7785793` | Workflow parity/import not established |
| Product MIT license | `BlazePwifi/LICENSE` blob `1ee55b94183417be977ca287cd7391f9a6f7e721` | `Pisowifi/LICENSE` same blob | Exact sibling license blob present |
| Notice / Hardware license | Root source `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` | Root `NOTICE.md`, `Hardware/LICENSE`, `Hardware/NOTICE.md` absent | Explicit Hardware notice/license placement unresolved |

The identical sibling `Pisowifi/LICENSE` does not by itself establish the intended license/notice scope for the separate Hardware subtree. No file was copied, moved, rebased, cherry-picked or staged. COE #26 remains five queued workflows / zero jobs; destination CI has not accepted the candidate.

COE #49 remains a separate Stage 5.1 candidate at `aeb8ff11b2f5db9a5f86280ab62ab988245f3919`: Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared Hardware [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL. It remains unassigned/audit-only and is not part of #26. COE #45 is a separate CORE candidate; its two scoped runs do not establish combined destination acceptance.

## 4. Governance, execution and limitations

- Branch API reports `protected=false` for inspected refs; rulesets API returned zero; classic branch-protection read returned HTTP 403. Effective organization-level enforcement remains UNKNOWN.
- Master combined commit status returned no status records. No Master-specific Actions run was surfaced.
- Local `git ls-remote` failed because the container could not resolve `github.com`; the full Master Python suite was NOT RUN. Source/tree/API inspection is not test execution.
- The private v11 registry/newer corrections remain inaccessible; no older v3–v7 registry was substituted.
- No Codex app, CLI, API, agent or workflow was used.

## 5. Decisions and exact next owner actions

1. **PHX-QA:** replace the stale positive poll-signature fixture with source-exact negative/default-deny tests; rerun #327 Full validation without weakening firmware.
2. **PHX-PISONET:** own the `$buildWorkflow` correction in `negative-selftest.ps1` and resolve the PISONET path present in the #291 diff with RELEASE.
3. **PHX-RELEASE:** preserve both ELF outputs and linker maps; attribute the exact `.flash.rodata` offsets and rerun the strict two-core comparator. No normalization.
4. **COE integration owner:** preserve #26 freeze until exact blob/mode, license/notice, dependency/import, test identity, workflow parity and completed destination CI are verified.
5. **Registry custodian:** provide authorized access to private v11 and newer corrections through the approved Drive connector.
6. **Repository administrator:** verify effective branch protection/rulesets with sufficient permissions.
7. **PHX-MASTER:** run the full coordination test suite once an authenticated local checkout/network path is available; keep the cleanup checkbox unchecked until the broader inventory is complete.

No subsystem source or test branch was changed. No merge, release, signing, secret provisioning, flashing, physical test, payment operation, migration or customer cutover occurred.

**PRODUCTION NO-GO** remains mandatory pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.
