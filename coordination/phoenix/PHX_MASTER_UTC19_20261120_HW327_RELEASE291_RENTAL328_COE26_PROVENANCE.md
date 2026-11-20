# PHX-MASTER UTC19 — exact-head role, CI and COE Hardware provenance

**Audit time:** 2026-11-20T19:35Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts and cross-repository migration provenance only.  
**Disposition:** DRAFT REVIEW ONLY · COE #26 FROZEN · PRODUCTION NO-GO.

## 1. Exact repository and branch references

- Experiments default branch: main @ f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Current development branch: blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859. The older v0.5.3 branch is legacy, not the current development reference.
- Master branch before this coordination-only update: phoenix/master-coordination @ c4827bafa2e36802e76c85ec5b958be594ba8ae0.
- Existing Phoenix Master PR #288: OPEN / DRAFT / UNMERGED; base main @ f4e8a891aed8af86d5fd315d28750a0ac3a7372b. The pre-update 130 changed paths were all under coordination/phoenix/. Exact-head PR workflow query returned no runs.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration PR #26: OPEN / DRAFT / UNMERGED, head b382d233ff06c8791b1028bed3c617cc7b670d12, base main @ a6513ab4412b4c014eee2863e45cbe32d06cb243, 205 changed files, five workflows QUEUED / zero jobs.
- OWNERSHIP_ROUTES.json: blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No route or ownership-manifest change.

## 2. Current role PR and exact-head CI snapshot

| Role / PR | Current head and base | Exact CI disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Run #42698139210 PASS (scoped). CORE remains with the separate Blaze Production Continuation owner. |
| RENTAL #240 | a7d113fb8ae3f0c5e838e64d31cae7a154e37b56 | Runs #40910311141 and #40910311159 PASS (scoped). |
| RENTAL #287 | a4fffd01c8fb1818c32a53522e0590c1dc8a77cd | Run #43754089203 PASS (scoped). |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Runs #43653329229 and #43653329235 PASS (scoped). |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070; base #289 @ 68928774d0d7cf65adb26bc6b54199a3159d066c | APK identity #44782114384 PASS; API21/API23 emulator smoke #44782114393 PASS; shared BlazePwifi build #44782114390 FAIL. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Run #42462978704 PASS (scoped). |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Run #43633486963 PASS (scoped). |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered run returned. |
| HARDWARE #327 | 1a631567eb0c14c12a114f592685f44cc414466f; base #326 @ 58c558fb6a237935214621adc3dee65a10fe1a51 | Relay/output #44805083239 PASS; quarantine #44805083039 IN PROGRESS; BlazePwifi build #44805083043 IN PROGRESS. No current-head Full result yet. |
| RELEASE #291 | docs head bcb71b4c797215c0980677b40a1e91860fd13f49; source/test parent 05d7b1efeb40820e5800553f96d678666d08bac2; base #242 @ 734b89d9e7792247e8376335c3f3685500ab3f89 | BlazePwifi build #44799798801 PASS; ESP32 compatibility #44799798721 PASS; Windows #44799798699 FAIL at PISONET-owned negative-selftest.ps1 because $buildWorkflow is uninitialized. Publisher skipped. |

### HARDWARE #327 head transition

The live #327 head advanced after its UTC18 checkpoint. Current PR metadata is authoritative: 1a631567eb0c14c12a114f592685f44cc414466f, branch phoenix/hardware-prepoll-edge-abort-20261119, base #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. The new head adds the post-drain ISR-edge rollover regression. Its recursive tree is complete (2,444 entries); the ESP32 sketch remains blob ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7, ESP8266 remains a1f12edc3d0a2ce93641c3ae2ef1e0e258dbbdaa, and the inherited hardening fixture remains 41211b2c110ab409f6d9d1812ef12fda73b13211.

The previous docs head f2fddc18b30e64f12071d3566c8505001dd31a74 Full run #44795789137 failed at the QA-owned “Missing poll signature check” assertion. That is historical for the previous head, not a terminal result for current head 1a631567. QA still owns replacing positive response_sig / |poll| string-presence assertions with source-linked negative/default-deny tests. HARDWARE retains firmware ownership; do not add a positive poll-admission path to satisfy the obsolete fixture.

### RELEASE #291 ownership split

The accumulated 26-path PR diff is exactly 21 RELEASE-owned .github paths, three CORE-owned BlazePwifi handover/ledger/state paths, and two PISONET-owned SoftTimer ReleaseSigning test paths. CORE must review its PROJECT_HANDOVER.md, CHANGE_LEDGER.md and CURRENT_STATE.md; PISONET must review/fix its own negative-selftest.ps1 and PublisherMockCli.ps1; RELEASE retains its workflow and packaging scope. No ownership transfers by inclusion in the diff.

The #291 compatibility run labels its source as 76eca0915943 and verifies the unchanged ESP32 sketch blob ae0da8e2. Current #327 has since advanced to test head 1a631567, while that sketch blob remains unchanged. The compatibility PASS therefore supports the pinned sketch blob, not the newly added #327 host-lab commit.

### RENTAL #328 inherited build blockers

#328 changes six Rental-owned paths only. Its APK identity and API21/API23 smoke checks pass. Its shared BlazePwifi build fails for two separately logged reasons:

1. The handover gate reports that experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md is stale relative to source/workflow changes; the canonical PROJECT_HANDOVER.md, CHANGE_LEDGER.md and CURRENT_STATE.md are CORE-owned. CORE must coordinate the canonical handover refresh; Master and Rental must not take over those files.
2. The #328 branch's ESP32 sketch is blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d and unconditionally includes mbedtls/sha256.h. Its ESP32 core 4.0.0 build fails because that legacy header is unavailable. Current #327 source blob ae0da8e2 has the Mbed TLS major-version guard. Hardware owns the firmware baseline; RELEASE owns toolchain qualification; Rental must not repair firmware in its six-file app PR.

## 3. Exact COE #26 source/destination audit

The complete recursive source tree at current #327 head 1a631567 has 2,444 entries; the complete destination tree at COE #26 head b382d233 has 286. The source Hardware subtree contains 25 board-local Python labs/helpers; destination Hardware contains zero Python lab/helper identities. Source has three scoped Hardware workflows; destination has one generic hardware-ci.yml.

| Artifact | Experiments #327 source blob | COE #26 destination blob |
|---|---|---|
| ESP32 sketch | ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 |
| ESP8266 sketch | a1f12edc3d0a2ce93641c3ae2ef1e0e258dbbdaa | c8be98f72596681e36a3ad1f8939bf8046c96887 |
| Firmware hardening test | 41211b2c110ab409f6d9d1812ef12fda73b13211 | f921c56cecc19cab1989507b9b4ade1f45dac54e |

License/notice comparison:

- experiment/openwrt/BlazePwifi/LICENSE and COE Pisowifi/LICENSE are byte-identical at blob 1ee55b94183417be977ca287cd7391f9a6f7e721.
- Experiments root NOTICE.md exists at blob f6d92cd21465312be5993631fe26977219be0fb9; COE root NOTICE.md is absent.
- COE Hardware/LICENSE and Hardware/NOTICE.md are absent. The PR description's broad “licensing conflict resolved” statement does not establish Hardware subtree notice/license closure.

### Source-confirmed Hardware behavior difference

Current Experiments #327 source is fail-closed:

- ESP32 mounts LittleFS with auto-format disabled; ESP8266 mounts without formatting on failure. Mount failure latches recovery-required state and disables coin intake.
- Both source sketches keep acceptPollResponse deny-only (return false). applyRemoteConfig appears only as a definition, with no callsite in either source sketch.
- Source /quarantine/clear returns HTTP 403.
- Both source quarantinePending implementations require a matching durable attempt marker and successful appendQuarantineRecord before clearing pending evidence; failed append retains pending evidence and latches recovery-required state.

COE #26 destination sketches are not equivalent:

- ESP32 uses LittleFS.begin(true); ESP8266 explicitly calls LittleFS.format() after a mount failure.
- Both destination sketches initialize sigOk=true and only verify response_sig inside a non-empty controller-key branch. An empty key skips verification while leaving sigOk true; destination register/poll callsites also invoke applyRemoteConfig.
- Destination quarantinePending performs best-effort append and then calls clearPending even when open/write/flush success is not established.
- Destination /quarantine/clear deletes the log and returns HTTP 200.

These are static source findings, not a claim of an observed customer or physical incident. The destination's positive signature/poll fixture is not acceptance evidence for the current deny-only source. COE #26 remains FROZEN until exact per-file provenance, complete tests/imports, license/NOTICE scope, toolchain pins, owner review and destination CI are independently satisfied. No copy, move, overwrite, cherry-pick, rebase, staging or route promotion occurred.

## 4. Cleanup, governance and private registry access

- Cleanup issue #266 remains OPEN with seven role checkboxes and zero checked; Master cleanup inventory is incomplete.
- main and current development branch metadata report protected=false. Classic branch-protection reads return 403 and repository rulesets are empty; effective organization-level protection remains UNVERIFIED.
- Exact Library title search did not locate BLAZE_PROJECT_REGISTRY_v11_20261027.json or newer corrections. The accessible Library surfaced older v3-v7 registry snapshots and a v2 production checkpoint; none was substituted. No Google Drive connector is exposed in the current tool surface. No private registry content or identifiers are published.
- Container git ls-remote failed because github.com DNS could not resolve. No authenticated local checkout was available; the complete PHX-MASTER Python suite was NOT RUN. This report distinguishes live source/tree inspection and hosted role CI from actual Master-suite execution.
- No physical hardware test, flash, payment operation, signing, secret provisioning, merge, release or production migration was performed.

## 5. Next owner actions

1. PHX-QA: replace the inherited positive poll-signature fixture with source-linked negative/default-deny tests, then run Full on the latest exact #327 head.
2. PHX-HARDWARE: complete the in-progress exact-head quarantine/build runs and preserve deny-only firmware behavior.
3. PHX-CORE: refresh its canonical PROJECT_HANDOVER.md / CHANGE_LEDGER.md / CURRENT_STATE.md only through its own continuation; coordinate the #328 handover freshness gate.
4. PHX-HARDWARE + PHX-RELEASE: reconcile the old #328 ESP32 source baseline with the current #327 Mbed TLS 3/4-qualified sketch; do not change Rental-owned files.
5. PHX-PISONET: fix the unset $buildWorkflow in its own negative-selftest.ps1.
6. PHX-RELEASE: retain release workflow ownership and obtain CORE/PISONET review of its inherited 26-path diff.
7. COE integration owner: keep #26 frozen and produce exact Hardware file/test/license/NOTICE provenance before any migration proposal.
8. Registry custodian and repository administrator: restore authorized v11/newer-correction access and independently verify effective branch protection.

**PRODUCTION NO-GO** remains mandatory until an independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates have independently verified evidence.
