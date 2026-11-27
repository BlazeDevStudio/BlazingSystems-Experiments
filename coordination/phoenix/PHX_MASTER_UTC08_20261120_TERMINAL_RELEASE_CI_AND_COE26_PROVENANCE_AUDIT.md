# PHX-MASTER UTC08 — terminal RELEASE CI and COE #26 provenance audit

**Timestamp:** 2026-11-20T08:07:14Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** `coordination/phoenix/`, architecture/interface contracts, cross-repository provenance and integration matrix only  
**Execution constraint:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.

## 1. Read-first evidence and exact refs

Re-read the uploaded Master directive, latest `README_FIRST`, BLAZE-COMMS/1 protocol, Experiments `AGENTS.md`, control-plane issue #172, cleanup issue #266, current PR #288, current ownership manifest, role PRs/CI, COE main and integration PR #26.

| Ref | Exact live SHA / state |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` (comparison-only) |
| Master branch at audit start | `ff3a4e961d45bbfaf40c23ff8f4e34d5299a19de` |
| Experiments PR #288 | OPEN / DRAFT, base `main@f4e8a891...`, 121 changed paths at audit start, all under `coordination/phoenix/` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT, `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows queued / zero jobs |

The current #172 body still contains older role-head pins (including a stale #288 head and the earlier #323 head). The live branch/PR APIs and this UTC08 report supersede those older body pins. The existing issue body was not replaced; the new BLAZE-COMMS checkpoint carries the exact refresh.

## 2. Terminal exact-head CI reconciliation

### HARDWARE #327

- PR/docs head: `d9072ce36e87a4bb1b9f1f5f888478a3c35fe236`
- Source/test anchor: `726981b49fb415fd10b764cbb8c386a00fcdbcf1`
- Base: #326 `58c558fb6a237935214621adc3dee65a10fe1a51`
- [Quarantine #44697742089](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697742089): PASS.
- [Relay/output #44697742266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697742266): PASS.
- [Full #44697742114](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697742114): FAIL. The validation job stops at the QA-owned `Missing poll signature check` in `tests/controllers.sh`. All 13 firmware/platform target jobs and Android passed, but downstream simulations, update/signing and publication were skipped.

The poll consumer remains default-deny. QA must replace the obsolete positive/presence assertion with source-linked negative behavior checks; firmware must not be weakened.

### RELEASE #291

- Current PR head: `df189b079a89f52b6152e613f5f5a32817c05f04`
- Parser-test commit: `e6e9a7f42ac2a551509a1e70e95fc5be449830b5`
- Workflow commit: `e359d9e5a28adea6b6604ccdf038a555ab4bdf2a`
- [ESP32 compatibility #44697909618](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697909618): FAIL on both core jobs. Exact failing test: `test_accepts_posix_nm_row_without_size_field`; the parser raises `ValueError: malformed POSIX nm row at line 1`. This parser regression stops the current run before a new two-core build/reproducibility comparison.
- [BlazePwifi Full #44697909628](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697909628): SUCCESS for the non-production build/simulation path. Production signed-APK import, sign handoff, prerelease publication and release publication were skipped.
- [Windows #44697909649](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697909649): FAIL in PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is unset; publisher skipped.

The previous completed comparison [#44692255708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44692255708) mapped prior non-descriptor ESP32 differences into `.flash.rodata`. Those differences remain unresolved. The current parser test failure is not a successful reproducibility result and does not clear the gate. RELEASE owns the parser/ELF workflow; PISONET owns the Windows self-test. No cross-role fix was made.

### Other exact-head role evidence

| Role / PR | Exact head | Current evidence | Limitation |
|---|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS | Scoped DENY-only; CORE implementation remains with separate automation |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229), [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS | Scoped CI, no physical device acceptance |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS | Scoped Windows CI; native COM bench unverified |
| HARDWARE #254 | `84c442a46ee2ee48ab733b10ff0f54edbc09ba9` | [Focused #44683629378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629378) PASS; [Full #44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) FAIL | ESP32 core 4.0.0 lacks `mbedtls/sha256.h`; separate non-actuating candidate |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS | Does not invoke `NativeComInterfaceHandleLab` |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head run | Not CI-verified |

## 3. COE #26 destination review — no migration

Exact source tree inspected at HARDWARE source/test commit `726981b49fb415fd10b764cbb8c386a00fcdbcf1`; exact destination tree inspected at COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.

| Item | Experiments source | COE #26 destination | Finding |
|---|---|---|---|
| ESP8266 sketch | `b956bc031df32ef69350dec368eaa91073b5a638` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different blob |
| ESP32 sketch | `1458f32881d3b340f1101dd0215618b54c1b688b` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different blob |
| Board-specific Python lab/helper files | 25 (16 ESP8266, 9 ESP32) | One generic `Hardware/tests/test_firmware_hardening.sh` | Import/test identity incomplete |
| Hardware CI workflows | Three scoped Phoenix workflows | One generic `hardware-ci.yml` | Workflow parity not established |
| License | Source `BlazePwifi/LICENSE` blob `1ee55b94183417be977ca287cd7391f9a6f7e721` | `Pisowifi/LICENSE` has the same blob | Same MIT text exists at sibling path, but no explicit `Hardware/LICENSE` |
| Notice | Source root `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` | No root `NOTICE.md` or `Hardware/NOTICE.md` | Notice scope incomplete |

The presence of `Pisowifi/LICENSE` is not treated as automatic proof that the Hardware subtree's source/notice obligations are explicitly covered. Destination CI remains five queued workflows / zero jobs. The exact route manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER destination `null`. No source was copied, moved, overwritten, rebased, cherry-picked or staged.

COE #49 remains unassigned/audit-only at `aeb8ff11b2f5db9a5f86280ab62ab988245f3919`; its host Stage 5.1 and case checks pass, but shared ESP32 CI fails. HARDWARE declined implementation ownership; there is no route from #49 to #26.

## 4. Governance and execution limits

- Experiments branch refs: `main@f4e8a891...`, `blazepwifi-v0.5.3-development@aad3aade...`, `blazepwifi-v0.6.0-audit-foundation@2fbd2475...`.
- Branch list metadata reports `protected=false` for inspected refs; repository rulesets returned an empty list. The direct branch-protection endpoint returned HTTP 403 to this integration, so effective organization-level protection is not independently established.
- No Master-specific workflow run was returned for the audit-start Master head. The full Master Python suite was NOT RUN. A local Git clone attempt failed because the container could not resolve `github.com`; no test result is inferred from tree inspection.
- The private Google Drive v11 registry and newer corrections remain inaccessible: no Google Drive connector is exposed in this execution surface, and exact Library search did not return the requested v11 file. No older registry snapshot was substituted; no private registry contents or IDs are included here.

## 5. Next owner actions

1. **PHX-QA:** replace the stale poll-signature presence check with source-linked negative/default-deny behavior tests at current #327 source/test SHA; do not weaken firmware.
2. **PHX-RELEASE:** fix the three-field POSIX `nm` parser regression, preserve fail-closed byte comparison, then rerun exact-source compatibility on both cores.
3. **PHX-PISONET:** initialize and validate `$buildWorkflow` in its own negative self-test; RELEASE must not edit PISONET-owned files.
4. **PHX-HARDWARE:** preserve the current default-deny poll/relay behavior; await independent QA review and real hardware evidence.
5. **COE integration owner:** keep #26 frozen until exact source blobs, license/notice scope, test identities, workflow parity and destination CI are independently accepted.
6. **Registry custodian / repository administrator:** restore authorized v11 access and independently establish effective protected-branch controls.

**Decision:** PR #288 remains OPEN/DRAFT. Issue #266 remains OPEN; the Master cleanup checkbox remains unchecked. COE #26 remains frozen. **PRODUCTION NO-GO.** No merge, release, flash, secret provisioning, payment mutation or physical test was performed.
