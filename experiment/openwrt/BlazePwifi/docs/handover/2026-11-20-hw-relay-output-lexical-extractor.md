# PHX-HARDWARE — relay output lab lexical extractor cleanup

**Date:** 2026-11-20 UTC (scheduled UTC16 activation; final evidence observed through 17:01:49Z)  
**Role:** PHX-HARDWARE  
**Task:** #177 / cleanup-first #266 / active child PR #327  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Stack:** #323 → #326 → #327; #327 base is #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `f08ed2db264df8e478f4c65edfe0d8270122241b`  
**PR state:** OPEN / DRAFT / UNMERGED. No retarget, rebase, force-push, merge, or release.

## Selected owned task

The Hardware-owned `relay_output_polarity_lab.py` still had a private regex/raw-brace function extractor even though the stack already contained the shared lexical-aware `firmware_lab_source.extract_function`. The local parser counted braces in ordinary strings, C++ raw strings, line comments, and block comments as C++ structure. Because this lab extracts production `writeLogical()` and `applyOutputs()` bodies for relay-polarity checks, truncation could invalidate the test's source-exactness.

This is a test-harness defect, not a demonstrated runtime firmware defect.

## Changes

Only this source/test file changed in this task:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/relay_output_polarity_lab.py`

- Removed the local `re.search` + raw-brace counter and its now-unused `re` import.
- Delegated extraction to the existing shared `firmware_lab_source.extract_function`.
- Added four regression fixtures: ordinary string brace, C++ raw-string brace, line-comment brace, and block-comment brace.
- Kept the existing source-exact `writeLogical()` / `applyOutputs()` compilation, active-high/active-low OFF checks, admission-inhibit matrix, independent LED/relay enable checks, and existing polarity/poll-inhibit mutation builds.
- No ESP8266/ESP32 sketch, relay behavior, coin behavior, API, finance, journal format, schema, signing, or release workflow changed.

The test-only RED commit temporarily added the fixtures against the old local parser. The GREEN commit removes that parser entirely, so the final branch has one shared extractor and retains the missing-function error behavior from the shared helper.

## Exact evidence

### RED — defect reproduced

- Test-only commit: `de6946bdbc5eb7abd4f02ac88eb4d35051ea2caf`
- Relay workflow: [#44778206360](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44778206360)
- Job: `136433587963` (`source-output-polarity`)
- Result: expected FAILURE at the new regression assertion.
- Exact log: `RELAY_OUTPUT_EXTRACTOR_FAIL: non-code brace truncated target(): ordinary string, C++ raw string, line comment, block comment`
- Literal checkout SHA verified as `de6946bdbc5eb7abd4f02ac88eb4d35051ea2caf`.

### GREEN — shared extractor

- Source/test commit: `f08ed2db264df8e478f4c65edfe0d8270122241b`
- Relay workflow: [#44778503745](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44778503745)
  - Job `136434632380` (`source-output-polarity`): SUCCESS.
  - Job `136434632049` (`esp32-boot-polarity`): SUCCESS.
  - Exact log markers: `RELAY_OUTPUT_LEXICAL_EXTRACTOR_PASS 4/4`; `ESP8266: RELAY_OUTPUT_POLARITY_PASS 48/48 scenarios`; `ESP32: RELAY_OUTPUT_POLARITY_PASS 48/48 scenarios`.
  - Existing output-gate mutations remain rejected.
  - Parent poll-drain, fault-inhibit, pulse-capture, timeline, response-fail-closed and poll-edge mutation suites also passed in the exact-head job.
- Quarantine workflow: [#44778503562](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44778503562)
  - Job `136434631401`: SUCCESS.
  - Exact log markers: `JOURNAL_MOUNT_LEXICAL_EXTRACTOR_PASS 4/4`; `MOUNT_SOURCE_LAB_PASS 8/8 source-extracted scenarios` on both boards; `PHX-HARDWARE: 16/16 fake-LittleFS mount/relay scenarios PASS`.
  - The quarantine lab remains simulated; actual devices were not tested.

### Full build — overall NO-GO

- Exact source/test SHA: `f08ed2db264df8e478f4c65edfe0d8270122241b`
- Full workflow: [#44778503709](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44778503709)
- Validation job `136434800668`: FAILURE at the inherited QA-owned `Missing poll signature check` assertion in the ESP8266 sketch.
- All 14 firmware/Android target jobs completed SUCCESS: ESP8266, ESP32, Android, x86-64, Ruijie, and the listed Orange Pi targets.
- Downstream simulations, update bundle, signed-APK import, pre-release, signing handoff, release publication and candidate gate were SKIPPED after validation failed.
- Do not add an ad-hoc `response_sig`, relax firmware default-deny, or infer poll authorization from `ok:true`.

## Status and limitations

- Shared extractor regression: **CI VERIFIED**.
- Relay polarity / poll / journal host labs: **SIMULATED** and **CI VERIFIED**.
- Physical relay contacts, coin acceptor, pulse conditioning, electrical recovery and real LittleFS durability: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30 devices / 24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer / independent witness: **NOT ESTABLISHED**.
- Financial v1→v2 migration and durable accounting/replay: **NOT TESTED / NOT ESTABLISHED**.
- Independent QA and release signoff: **PENDING**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed connected-file surface in this activation. No older registry snapshot was substituted and no private provenance data was copied into GitHub.

## Coordination / next exact actions

1. **PHX-QA:** replace the inherited positive poll-signature presence assertion with source-exact negative/default-deny tests; wait for PHX-CORE's approved authenticated register/poll and event-bound receipt contract before adding positive vectors.
2. **PHX-CORE:** publish canonical response bytes, versioned/domain-separated signature contract and golden vectors.
3. **PHX-MASTER:** refresh the Hardware active-head entry in `coordination/phoenix/ROLE_ASSIGNMENTS.md` and #172 to the latest #327 head after this handover commit; preserve #323 → #326 → #327 ancestry.
4. **PHX-HARDWARE:** revalidate live branch/stack and choose one new owned, reversible firmware/lab task on the next activation.
5. Keep all physical acceptance, signer/witness, finance migration, release and deployment gates closed until independently evidenced and approved.

No Codex was used. No physical flashing, reset, live money, production migration, merge, signing, release tag, or deployment was performed.
