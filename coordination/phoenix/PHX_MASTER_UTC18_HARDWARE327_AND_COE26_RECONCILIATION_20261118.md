# PHX-MASTER — Hardware #327 and COE #26 exact-head reconciliation

**Audit timestamp:** 2026-11-18T18:52Z  
**Role:** PHX-MASTER — coordination, architecture contracts, migration provenance, integration matrix only  
**Status:** OPEN / DRAFT / UNMERGED · **PRODUCTION NO-GO**

## 1. Authority and current repository pins

Read this activation: uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`; latest Library copies `README_FIRST(20261114-191926).md` and `COMMUNICATION_PROTOCOL(20261114-191925).md`; Experiments `AGENTS.md` blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`; repository README; current #172 and #266; Master #288 and routing manifest; role PRs and exact-head CI; COE main and #26. AGENTS-directed cloud policy blob `5e503925750c4e511314e4b7624579d82f60aae2` and storage handover blob `a15f14cb3baf46424b820e1a921462794422f06b` were also read.

| Ref | Exact SHA |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments v0.5.3 development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments v0.6.0 audit-foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch before this update | `1cc0d1ac45a9696349d369abff878022cad315e2` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

Master #288 is OPEN / DRAFT on `phoenix/master-coordination`, base main. The ownership manifest is unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER destination null. All Master edits in this activation are documentation-only under `coordination/phoenix/`.

## 2. Hardware #327 — Master source review

### Stack and exact refs

- PR #323 parent: `988904e8bcd058b62a9fac4aa6319a9b7c5b2470`, based on #322 `50d93e0de3d682550b6f02fb43484e76ad9c7e08`.
- PR #326 child: `58c558fb6a237935214621adc3dee65a10fe1a51`, based on #323.
- PR #327 current docs head: `0a26468022d25746fdc38525c0c0979da098f6d4`, based on #326. Exact source/test SHA: `e774420c3404141ffe4ec7b9c002c14d3c2286b8`.
- Current firmware blobs: ESP8266 `dde063b1f578fa66a52221b74643d8862a38957c`; ESP32 `ada9723c5f07879775284eb128a986ac865394f7`.

### Source behavior reviewed

1. Both sketches snapshot the ISR edge sequence before the quiet drain. Immediately after a successful `beginPollWindow()` and before synchronous `post("poll")`, they compare the sequence again. A drain-window edge is latched while intake remains inhibited; no poll HTTP request is sent; outputs are reapplied under the sticky deny and the next poll is deferred. This closes the source-level interval in which an ISR edge could otherwise remain only in RAM during the blocking HTTP wait.
2. Both sketches set the RAM-only `pollFaultBackupWriteFailed` latch on ambiguous NVS/EEPROM set/commit/reopen/readback failure. Subsequent same-boot calls return false instead of treating a dirty emulation buffer/cache as durable. A cold boot clears the RAM latch and checks the flash-backed marker.
3. If both the primary LittleFS marker and secondary NVS/EEPROM marker fail to reach durable storage, only current-boot denial is established. Reboot durability is NOT ESTABLISHED. The two stores are not an independent freshness/anti-rollback witness or durable financial ledger.

Master review found the ordering and ownership scope consistent with the stated fail-closed intent. This is a coordination review, not independent QA, source-owner approval, physical acceptance or merge approval.

### Exact CI and correction history

| Evidence | Result |
|---|---|
| Source/test SHA `e774420c...` quarantine [44373043845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043845) | PASS; both board dual-store labs and pre-poll edge race pass |
| Source/test SHA `e774420c...` relay/output [44373043958](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043958) | PASS; both board output/polarity and poll-window guards pass |
| Docs head `0a264680...` quarantine [44373742439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742439) | PASS |
| Docs head `0a264680...` relay/output [44373742382](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742382) | PASS |
| Docs head Full build [44373742348](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742348) | FAIL: validation job `135047376378` reports `Missing poll signature check`; Android job `135047377045` separately fails resolving legacy Gradle dependencies |

Intermediate source/test commit `fcb5c1ab...` failed quarantine compilation because the new test assertion used `pollFaultBackupBackupPresentOrCorrupt`. Hardware corrected the test-only symbol in `e774420c...`; exact-source focused runs then passed. Do not carry the intermediate harness failure forward as a current firmware defect.

Full validation still expects positive `response_sig` / `|poll|` strings despite current firmware intentionally denying poll response and coin disposition. QA must replace the positive fixture with negative default-deny tests; no synthetic positive signature or firmware relaxation is acceptable. The Android dependency failure is separate build-environment/dependency resolution work, not a hardware acceptance result.

## 3. COE #26 destination staging — exact comparison

Destination #26 remains OPEN / DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`.

| Item | Experiments #327 source | COE #26 destination | Assessment |
|---|---|---|---|
| ESP32 sketch | `ada9723c5f07879775284eb128a986ac865394f7` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different blobs |
| ESP8266 sketch | `dde063b1f578fa66a52221b74643d8862a38957c` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different blobs |
| Source board labs | 18 Python labs (11 ESP8266 + 7 ESP32) | None of the 18 present | Import incomplete |
| Destination generic test | — | `f921c56cecc19cab1989507b9b4ade1f45dac54e` | Different test identity; still requires positive `response_sig` and `|poll|` |
| Destination workflow | — | `pisowifi-ci.yml` blob `cf18705f13168e6848c8eaf80ac150287f07c202` | Runs Pisowifi source intake/tests; no Hardware test invocation |

COE #26 has five queued workflows / zero jobs: [43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632), [43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557). No exact-head combined Hardware destination CI has run.

### License and notice path audit

- Source project MIT `LICENSE` blob `1ee55b94183417be977ca287cd7391f9a6f7e721` matches COE `Pisowifi/LICENSE` exactly.
- Vendor qrcode LICENSE `150770c0fc2994865ccdbef6662735cc083e780d` matches the COE Pisowifi vendor path.
- Vendor TailAdmin LICENSE `cb92d4176b21b0594e5a6caf94d79340505e3d33` and NOTICE `f0425bbbe34c1227311098173b1eae0c3e2a807b` match their COE Pisowifi paths exactly.
- The vendor TailAdmin NOTICE is present and identical. The source project-root `NOTICE.md` was not found. COE root `LICENSE` / `NOTICE.md` and Hardware-scoped LICENSE / NOTICE are absent. Since COE `Hardware/` is a sibling of `Pisowifi/`, the intended license scope of `Pisowifi/LICENSE` over Hardware remains unresolved and needs owner/legal confirmation.

This corrects the prior broad UTC17 wording about NOTICE absence; it does not clear the Hardware license-scope gate.

**Decision:** no move/copy/overwrite/rebase/delete is proposed. Keep manifest review-only and destination blocked until owner-approved per-file source, license, mode, test identity, import completeness and exact-head CI mapping is independently reviewed.

## 4. Other role and release reconciliation

- CORE #252 `c82705f2...`: scoped run 42698139210 SUCCESS; no CORE source touched.
- RENTAL #289 `68928774...`: 43653329235 and 43653329229 SUCCESS, scoped.
- PISONET #255 `d01fd164...`: 42462978704 SUCCESS, scoped; native/physical COM acceptance not established.
- QA #290 `5c29d159...`: 43633486963 SUCCESS for build/handover, but workflow does not invoke NativeComInterfaceHandleLab. QA #292 `75a3f66d...` has no run and is based on stale Master `b1ca02e...` rather than current Master `1cc0d1ac...`.
- RELEASE #291 `691ed55d...`: 44353380470 SUCCESS, privileged publisher skipped. COE #35 `1a5be48d...`: shared 44370198378 and case 44370198334 SUCCESS; mandatory sandbox 44370198386 FAILS closed because bubblewrap is absent after 13/13 host preflight tests.

## 5. Governance and private registry access

Branch-object reads report `protected=false` for Experiments main, v0.5.3 development, v0.6.0 audit-foundation, Master and COE main; both rulesets endpoints are empty. Repository administrator action is required.

No Google Drive connector is exposed in the current tool surface. Library search found the Nov 9 production checkpoint referencing canonical registry v11 and older v3–v7 registry snapshots, but not the canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` or newer corrections. The accessible sync ledger/addendum are dated 2026-10-26; the canonical artifact manifest was not found. No older registry was substituted, no private Drive IDs/content were copied into public GitHub, and no sharing or file mutations occurred.

The current automation inventory exposed Master, Release and Hardware continuations but no enabled task with the exact title “Blaze Production Continuation.” CORE remained untouched per the user's explicit ownership instruction; no competing CORE worker or source edit was started.

## 6. Tests and classification

- GitHub exact-source focused CI: #327 quarantine and relay/output PASS on source/test SHA `e774420c...` and docs head `0a264680...`.
- GitHub Full validation: FAILED on docs head; stale positive poll-signature fixture and Android dependency resolution are separate failures.
- COE #26: five queued / zero jobs; no destination test execution.
- Master Python suite: NOT RUN; Master exact-head CI query returned no runs.
- Physical GPIO/relay/acceptor tests, 150 real power cuts and 30-device/24-hour soak: NOT TESTED.

Master documentation assertions are run during authoring; they are not the full repository Python suite or QA acceptance.

## 7. Next exact actions

1. PHX-QA: replace positive poll-signature check with negative default-deny cases; independently test Hardware #327 exact source/test SHA `e774420c...`; rebase/retest #292 against current Master.
2. PHX-HARDWARE: keep #327 draft; preserve current-boot-only limitation when both stores fail; do not claim reboot durability or physical acceptance.
3. PHX-CORE: review unresolved-ingress reconciliation semantics and the financial consequence of a dual-store marker loss; no ledger/API change requested from Master.
4. PHX-RELEASE / INFRA: resolve Android dependency reproducibility and provide an authorized bubblewrap-capable runner for COE #35; no unsandboxed fallback.
5. COE integration owner: prepare per-file Hardware import/license/test map and unblock #26 workflows before any destination change.
6. Repository administrator: configure and independently verify protected branches and required status checks.
7. Registry custodian: restore authorized Drive v11 and newer-correction access; do not send private IDs/content into public issue comments.

No Codex, subsystem source edit, merge, rebase, release, signing, secret provisioning, hardware flash, physical test or real-payment operation occurred.
