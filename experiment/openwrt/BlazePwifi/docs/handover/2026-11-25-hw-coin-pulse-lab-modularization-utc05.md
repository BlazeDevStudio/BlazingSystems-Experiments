# PHX-HARDWARE UTC05 — coin-pulse capture lab modularization

**Updated:** 2026-11-25T05:55:30Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Issue:** [#177 — preserve coin-line edges during synchronous poll](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`

## Scope and reason

The Hardware-owned `coin_pulse_capture_lab.py` had grown to 698 lines and mixed a 450+ line C++ fake-GPIO/time/storage fixture, production-helper signature anchors, a 16-case fail-open mutation matrix, and the Python runner. This made it difficult to review the actual firmware contracts separately from harness mechanics.

The lab is now separated into three explicit responsibilities:

- `coin_pulse_capture_lab_fixtures.py` owns only the exact C++ host fixture (`CPP`).
- `coin_pulse_capture_lab_contracts.py` owns the 11 production helper/signature anchors, helper index and all 16 mutation cases.
- `coin_pulse_capture_lab.py` is now a 179-line runner: extract the actual helpers from both sketches, compose the fixture, run 17 positive/control scenarios, and reject each mutation.

A new `coin_pulse_capture_lab_structure_guard.py` checks the module boundary, literal fixture markers, 11 helper anchors, all 16 unique mutation identifiers, and the runner's fixture/mutation callsites. The Quarantine and Relay workflows invoke this guard before the pulse-capture lab.

## Exact commits

- Test-only boundary guard: `96ee89e51c7f8594482333df52faafda3c9eaa32`.
- Quarantine workflow wiring: `205e7da46bdf7fdeaded8cca5d4baf7e9370f0062`.
- Relay workflow wiring / test-only head: `0ea76673aec1bf25ebe9f6c4ae4f7d8731874262`.
- C++ fixture extraction: `07d86fe2188a86bc8900891b68864c103dcdfa6f`.
- Contract/mutation extraction: `88993094f3aac805996388e16e2236b6bf63567b`.
- Runner reduction: `8966829d9295bcbc8bfbaf7b23e5f5228af8b6d8`.
- Guard count correction (16 cases): `cbc570ce08280645858f3b25f7fba3f076421ae9`.
- Guard AST correction (read mutation identifiers without evaluating string-concatenation expressions): `4a24af066e1f96c995c65569234886fc414dfc8b`.
- Guard summary correction (use parsed mutation identifiers): `61689ab4764018f3b913303b4bf508f1d04a88af`.

**Exact source/test/guard SHA:** `61689ab4764018f3b913303b4bf508f1d04a88af`.  
**This handover is a documentation-only successor; the final docs commit is recorded by GitHub after this update.**

## Preservation evidence

The original C++ fixture was compared directly with the extracted module: **20,442 characters, byte-for-byte identical**. The 11-entry `FUNCTION_SPECS` block (1,123 characters) and 16-case mutation matrix (3,778 characters) were also compared exactly and are unchanged. The orchestrator shrank from 698 to 179 lines.

No scenario, helper signature, mutation replacement, board source or production behavior was changed.

## Test-first and exact-head CI

**Expected RED**

- Relay [#45555485240](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45555485240), job `139006398089`: failed at the intended missing fixture-module boundary.
- Quarantine [#45555485248](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45555485248), job `139006397965`: same expected missing-module boundary.

The intermediate guard-oracle defects were not hidden:
- Relay [#45555607772](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45555607772), job `139006799571`: simulation markers were checked in the wrong module.
- Docs-head Quarantine [#45555939106](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45555939106), job `139007869402`, and Relay [#45555939169](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45555939169), job `139007870254`: guard summary referenced a removed local variable. Both guard-only defects were corrected before final focused acceptance.

**Final source/test/guard SHA `61689ab`**

- Quarantine [#45556456992](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45556456992), job `139009562490`: **PASS**. The dual-store fault-injection lab, EEPROM config-read failure/recovery lab, module guard, poll-drain pulse lab and boot-polarity deny lab all passed.
- Relay [#45556456991](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45556456991), jobs `139009562838` and `139009563150`: **PASS**. The module guard passed; `FUNCTION_SPECS=11 MUTATIONS=16`; ESP8266 and ESP32 coin-pulse capture each passed `17/17`; output polarity, poll-drain, remote-config and bounded HTTP response guards passed.
- Exact log markers: `COIN_PULSE_CAPTURE_LAB_MODULE_BOUNDARIES_PASS`, `ESP8266_COIN_PULSE_CAPTURE_PASS 17/17`, `ESP32_COIN_PULSE_CAPTURE_PASS 17/17`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

**Full integration**

- Full [#45556456990](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45556456990), validation job `139009651784`: **FAIL** at inherited QA-owned `Missing poll signature check`.
- 13 firmware/platform build jobs plus Android: **14/14 PASS**.
- Production import, simulations, update bundle, candidate gate, signing handoff and publication: **SKIPPED** after validation failure.

Full CI failure is not a reason to invent a producer signature or weaken deny-default. CORE owns the authenticated register/poll response contract; QA owns independent assertion reconciliation.

## #283 audit readback

Current PR #283 head remains OPEN / DRAFT / UNMERGED. Both current sketches have `quarantinePending()` as a definition-only function (one occurrence each); append failure returns false without `clearPending()`, and the clear call is reached only after successful append. No active callsite exists, so the lifecycle is not considered integrated.

The current main CGI `register|ping` and `poll` envelopes contain no `response_sig`. Member snapshot/auth/mutation endpoints use distinct signature domains; they are not a substitute for poll-response authentication. Both sketches explicitly ignore current register/poll fields and deny remote control. Hardware remains deny-only pending CORE/QA approval.

## Scope boundary and release gates

This is Hardware-owned test/lab modularization only. No production ESP8266/ESP32 `.ino`, pin mapping, ISR, pulse capture, relay actuation, CGI producer, shared API, financial logic, signer, witness, migration, QA-owned assertion, COE destination or release workflow was changed.

Evidence is **SIMULATED / CI VERIFIED** only. Local independent execution was NOT RUN. Physical coin pulse, relay/electrical recovery, LittleFS/EEPROM power-loss, 150 controlled cuts, and 30-device/24-hour soak remain **NOT TESTED**. Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release signoff remain **NOT ACCEPTED**.

**HARDWARE ACCEPTED: NO. PRODUCTION NO-GO.**

## Next exact action

Re-read the live #349/#347/#340/#283/#254/#239 heads. Ask Master to reconcile the #340 base snapshot against current #283 ancestry. CORE must publish the authenticated register/poll producer contract; QA must independently reconcile the inherited signature assertion without weakening deny-default. Continue Hardware-owned source work only on a new unblocked task; do not claim physical acceptance from these host labs.
