# PHX-MASTER UTC20 — exact role CI, inherited Rental firmware baseline, and COE #26 revalidation

**Updated:** 2026-11-20T20:02:48Z  
**Role:** PHX-MASTER — architecture, coordination, ownership routing, and integration provenance  
**Disposition:** Coordination-only · PR #288 OPEN/DRAFT · COE #26 FROZEN · PRODUCTION NO-GO

## 1. Exact refs and authority

| Ref | Exact state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Legacy development | blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master before this audit | phoenix/master-coordination at be7a4e8e6fbacfd26e60fb6fc09a0322a2f84c8b |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12; 205 changed paths; five workflows QUEUED / zero jobs |
| Master PR #288 | OPEN / DRAFT / UNMERGED; base main at f4e8a891; 131 paths before this audit |
| OWNERSHIP_ROUTES.json | e4db324315a1b3543fec17a148fbf960170fcb29; DRAFT_REVIEW_ONLY; PHX-MASTER target null |
| Cleanup issue #266 | OPEN; seven checklist items remain unchecked |

The Master branch and PR #288 were read at the same exact head before writing. The route manifest was re-read and its blob remained unchanged. Master did not edit any subsystem source path or route.

## 2. RENTAL #328 — inherited ESP32 baseline mismatch confirmed

Current PR #328 is OPEN / DRAFT / UNMERGED at 0e0da62acd47c6a1ce287f8a30fc700d603fa070, based on RENTAL #289 at 68928774d0d7cf65adb26bc6b54199a3159d066c. Its six changed files are Rental Android/APK-contract paths; the ESP32 firmware sketch is not in the #328 diff.

Exact inherited firmware identity:

- #328 head and base #289 both contain ESP32 sketch blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d.
- That sketch unconditionally includes mbedtls/sha256.h.
- Current HARDWARE #327 source contains ESP32 sketch blob ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7. It includes mbedtls/version.h and selects PSA crypto for Mbed TLS 4, mbedtls/sha256.h for Mbed TLS 3, and rejects unsupported majors.

Exact #328 CI at its current head:

- APK identity run [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384): PASS.
- API21/API23 emulator smoke [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393): both jobs PASS.
- Shared BlazePwifi build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390): not green. The Mandatory handover freshness gate failed in job 136447688884; the ESP32 job 136447688964 failed at compile with “mbedtls/sha256.h: No such file or directory” under the ESP32 core 4.0.0 toolchain.

Ownership remains separate:

- RENTAL owns the six Android/APK paths and must not repair inherited firmware.
- CORE owns PROJECT_HANDOVER.md, CURRENT_STATE.md, and CHANGE_LEDGER.md freshness.
- HARDWARE owns the firmware baseline and source changes.
- RELEASE owns toolchain qualification/workflow evidence.

The required next step is owner-coordinated baseline selection and exact-source revalidation, not a Master or Rental firmware edit.

## 3. HARDWARE #327 — current exact-head CI

Current PR #327 docs/head is 4d651e918f71de2e69d1f3bcfe627c4f944c9c39; its source/test head is 1a631567eb0c14c12a114f592685f44cc414466f; base #326 is 58c558fb6a237935214621adc3dee65a10fe1a51.

| Workflow | Run | Result |
|---|---:|---|
| Quarantine byte readback | [#44805905655](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44805905655) | PASS |
| Relay/output polarity | [#44805905517](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44805905517) | PASS |
| Full BlazePwifi build | [#44805905622](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44805905622) | FAIL |

The Full run's validation job 136529849827 failed in Controller protocol parity with “Missing poll signature check” in the ESP8266 sketch. All 14 firmware-target/Android jobs passed; downstream simulations, update bundle, signing and publishing were skipped after validation failed.

The inherited fixture blob is 41211b2c110ab409f6d9d1812ef12fda73b13211 and still requires positive response_sig / |poll| markers. Current firmware is intentionally deny-only. QA owns replacing that stale positive string-presence assertion with source-linked negative/default-deny tests. HARDWARE retains firmware and lab ownership. Do not add a synthetic positive marker or re-enable poll admission to satisfy the fixture.

## 4. RELEASE #291 — exact current CI and cross-owner paths

Current PR #291 docs head is bcb71b4c797215c0980677b40a1e91860fd13f49; source/test head is 05d7b1efeb40820e5800553f96d678666d08bac2; base #242 is 734b89d9e7792247e8376335c3f3685500ab3f89.

| Workflow | Run | Result |
|---|---:|---|
| BlazePwifi Full | [#44799798801](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44799798801) | PASS; production import/sign/publish jobs skipped |
| ESP32 core compatibility | [#44799798721](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44799798721) | PASS, 3/3 jobs |
| Windows SoftTimer | [#44799798699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44799798699) | FAIL |

The compatibility matrix labels its tested source 76eca0915943 and the same ESP32 sketch blob ae0da8e2 used by current #327. This supports that sketch blob under the two pinned ESP32 cores; it does not test the newer #327 host-lab tree. The Windows build-windows job 136508751830 fails because PISONET-owned negative-selftest.ps1 reads $buildWorkflow before initialization; publisher is skipped.

The accumulated 26-path #291 diff remains 21 RELEASE paths, three CORE-owned handover/ledger/state paths, and two PISONET-owned SoftTimer ReleaseSigning tests. CORE and PISONET must review their own paths. No ownership transfer occurred.

## 5. Other role PRs and CI

| Role / PR | Exact head | Existing scoped evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | #42698139210 PASS; separate CORE continuation retains ownership |
| RENTAL #240 | a7d113fb8ae3f0c5e838e64d31cae7a154e37b56 | #40910311141 and #40910311159 PASS |
| RENTAL #287 | a4fffd01c8fb1818c32a53522e0590c1dc8a77cd | #43754089203 PASS |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | #43653329229 and #43653329235 PASS |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | #42462978704 PASS |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | #43633486963 PASS |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered run returned |

These are scoped CI results, not blanket subsystem acceptance. The separate CORE continuation retains all CORE implementation and handover work; Master did not start competing work.

## 6. COE #26 — complete recursive-tree and provenance recheck

Both recursive trees are complete and not truncated:

| Metric | Experiments #327 docs head | COE #26 |
|---|---:|---:|
| Tree entries | 2,445 | 286 |
| Board-local Python labs/helpers | 25 | 0 |
| Scoped Hardware workflows | 3 | 1 generic |

Exact Hardware blob comparison:

| Artifact | Experiments source | COE destination |
|---|---|---|
| ESP32 sketch | ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 |
| ESP8266 sketch | a1f12edc3d0a2ce93641c3ae2ef1e0e258dbbdaa | c8be98f72596681e36a3ad1f8939bf8046c96887 |
| Hardening fixture | 41211b2c110ab409f6d9d1812ef12fda73b13211 | f921c56cecc19cab1989507b9b4ade1f45dac54e |

The source root NOTICE exists; COE root NOTICE is absent. The source BlazePwifi LICENSE blob 1ee55b94183417be977ca287cd7391f9a6f7e721 matches COE Pisowifi/LICENSE, but that sibling match does not resolve Hardware subtree notice/license scope. COE Hardware has no dedicated LICENSE or NOTICE file.

Five COE #26 workflows remain QUEUED / zero jobs. No copy, move, overwrite, cherry-pick, rebase, staging, or route promotion occurred. Keep #26 FROZEN until per-file provenance, test identity, license/NOTICE scope, owner approval and destination CI are satisfied at one exact candidate SHA.

## 7. Registry, execution and evidence limits

The complete available Library inventory contains 1,422 entries. It exposes registry snapshots v3-v7 and older artifact/sync records, but not the canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json or newer corrections. No Google Drive connector is exposed in this runtime. No older snapshot was substituted, and no private registry data or identifiers were published.

Twelve bounded static assertions passed: Master PR identity/state; current role PR heads; #328 owner-only changed paths and inherited sketch; source/destination sketch divergence; manifest status and Master target; UTC20 checkpoint deduplication; and cleanup checklist state.

A local authenticated checkout could not be established: git ls-remote failed because github.com DNS resolution was unavailable. The complete Master Python suite is therefore NOT RUN. GitHub Actions runs above were read from their exact run/job records; they are not local Master-suite results or physical acceptance.

No physical hardware test, flash, secret provisioning, signing, real-payment operation, migration, merge or release was performed.

## 8. Next owner actions

1. PHX-CORE: refresh canonical handover files through its separate continuation and coordinate the #328 freshness gate.
2. PHX-HARDWARE + PHX-RELEASE: reconcile the inherited #328 ESP32 blob with the current Mbed TLS 3/4-qualified source and prove both core legs at an explicitly pinned source SHA.
3. PHX-QA: replace the positive poll-signature fixture with source-linked negative/default-deny tests, then rerun Full on current #327.
4. PHX-PISONET: fix the uninitialized $buildWorkflow in its own negative-selftest.ps1.
5. PHX-RELEASE: retain its 21 owned paths and obtain CORE/PISONET review for the five inherited paths in #291.
6. COE integration owner: keep #26 frozen; complete Hardware file/test/license/NOTICE provenance and run destination CI.
7. Registry custodian: restore authorized v11 and newer-correction access.
8. Repository administrator: verify effective protected-branch enforcement.
9. PHX-MASTER: run the complete coordination suite after an authenticated checkout is available.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates have independently verified evidence.
