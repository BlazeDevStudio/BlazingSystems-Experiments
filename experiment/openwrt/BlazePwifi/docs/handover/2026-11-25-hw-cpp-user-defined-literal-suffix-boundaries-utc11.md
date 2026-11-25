# PHX-HARDWARE handover — C++ user-defined literal suffix boundaries

**Updated:** 2026-11-25 UTC11  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Control plane:** [Issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Hardware task:** [Issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [Issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** [`7da74f9d1768a42fc6c15be368eeddae29035d4f`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7da74f9d1768a42fc6c15be368eeddae29035d4f)

## Selected defect

The Hardware-owned C++ token normalizer emitted a string/character literal and its immediately adjacent user-defined suffix as separate tokens. Because whitespace is intentionally ignored, compact UDL forms and whitespace-separated literal-plus-identifier forms collapsed to the same token sequence:

- `u8"payload"_tag` vs `u8"payload" _tag`
- `R"cfg(payload)cfg"_tag` vs `R"cfg(payload)cfg" _tag`
- `'x'_tag` vs `'x' _tag`

This is a proven host-side parity-guard false negative, not a discovered production-sketch defect.

## Test-first evidence

Test-only commit [`92e58a83`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/92e58a8367c2e38015260ae625b9a89e263d82c3) added three UDL-boundary contracts.

- Quarantine RED [#45602565653](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45602565653), job `139164952617`: expected 3/3 failures; all 11 pre-existing tests passed before the new cases.
- Relay RED [#45602565679](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45602565679), job `139164953025`: same 3/3 expected failures; the prior poll/relay and fault-injection suites passed.

## Source correction

Source fix [`c3d82cca`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c3d82cca404dab8bfb7671abf27771f063073f97) adds `_scan_user_defined_literal_suffix()` and applies it immediately after ordinary, prefixed, character and raw string literal terminators. The suffix is consumed only when its identifier-start character is adjacent to the literal; whitespace-separated identifiers remain distinct. Contract summary was updated to 14/14 at final source/test SHA `7da74f9d...`.

Only the Hardware-owned host lexical normalizer and its contract lab changed. No production `.ino`, CGI producer, shared CORE API, relay actuation, coin admission, financial state, signer, witness, migration, COE destination or Release workflow changed.

## Exact source/test CI — SHA `7da74f9d1768a42fc6c15be368eeddae29035d4f`

- Quarantine [#45603111644](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603111644), job `139166862358`: **PASS**. `CPP_TOKEN_NORMALIZER_CONTRACT_PASS 14/14`; bounded HTTP board parity PASS; 10/10 parity mutations rejected; existing poll/coin/quarantine failure-injection suites passed for both board source fixtures.
- Relay [#45603111558](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603111558), jobs `139166861621` and `139166862022`: **PASS**. UDL contract 14/14; poll response fail-closed 11/11; strict root JSON 13/13; current CGI no-signature denial retained; bounded HTTP allowed 3 / denied 9 per board; board parity mutations 10/10 rejected.
- Full [#45603111622](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603111622), validation job `139166864322`: **FAIL** at inherited CORE/QA assertion `Missing poll signature check` in the ESP8266 sketch. All 13 firmware/platform targets plus Android completed **14/14 PASS**. Update bundle, simulations, candidate, signing and publication stages were skipped.

Focused results are host/source-extracted **SIMULATED / CI VERIFIED** only. Workflow logs explicitly retain physical acceptance flags at zero.

## Live stack and ownership boundaries

- #239 OPEN / DRAFT at `d83b715b116185107737fef721c2eece8feebf39`.
- #254 OPEN / DRAFT at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; supplied cleanup commit `3692ddf889470da8a002e9a16bf0ac2f37f1a9d0` is an ancestor (17 ahead, zero behind).
- #283 OPEN / DRAFT at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`.
- #340 still declares base `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`, while #283 is at `4dd0b01b...`; MASTER must reconcile ancestry. Hardware did not rebase or retarget.
- Rechecked #283 source: `quarantinePending()` returns false when append fails and reaches `clearPending()` only after append success; the helper remains definition-only. The current register/poll producer still lacks an approved `response_sig`; CORE owns the producer contract and QA owns independent assertion reconciliation.

## Release status

- Focused lexical/parity and source-extracted firmware labs: **CI VERIFIED / SIMULATED**.
- Local independent toolchain build: **NOT RUN**.
- Physical coin acceptor, relay/electrical recovery, LittleFS/EEPROM power-loss: **NOT TESTED**.
- 150 controlled power cuts; 30-device/24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 financial migration and independent QA/Release acceptance: **NOT ACCEPTED**.
- Private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json`: **NOT RECOVERED** through available connected sources; no older registry was substituted.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

## Next exact actions

1. PHX-MASTER refreshes #349 source/test and handover pins in Master-owned assignment/integration records, and reconciles #340/#283 ancestry.
2. PHX-CORE publishes the approved authenticated register/poll producer contract and canonical golden vectors.
3. PHX-QA independently reconciles the Full validation assertion without weakening deny-default.
4. PHX-HARDWARE revalidates all live heads and selects one new unblocked Hardware-owned task on the next actual activation.
