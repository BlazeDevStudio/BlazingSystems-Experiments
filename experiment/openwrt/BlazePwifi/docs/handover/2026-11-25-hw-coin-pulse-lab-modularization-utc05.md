# PHX-HARDWARE UTC05 — coin-pulse capture lab modularization

**Updated:** 2026-11-25T05:45:00Z  
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
- Quarantine workflow wiring: `205e7da46bdf7fdeaded8cca5d4baf7e9370f006`.
- Relay workflow wiring / test-only head: `0ea76673aec1bf25ebe9f6c4ae4f7d8731874262`.
- C++ fixture extraction: `07d86fe2188a86bc8900891b68864c103dcdfa6f`.
- Contract/mutation extraction: `88993094f3aac805996388e16e2236b6bf63567b`.
- Runner reduction: `8966829d9295bcbc8bfbaf7b23e5f5228af8b6d8`.
- Guard count correction (16 cases): `cbc570ce08280645858f3b25f7fba3f076421ae9`.
- Guard AST correction (read mutation identifiers without evaluating string-concatenation expressions): `4a24af066e1f96c995c65569234886fc414dfc8b`.

**Current source/test/guard SHA:** `4a24af066e1f96c995c65569234886fc414dfc8b` (before this handover-only successor).

## Test-first / CI state

The boundary guard was wired before the fixture and contract modules existed, so the test-only head is expected to fail at the missing-module boundary. The first source split exposed two guard-oracle corrections: the mutation matrix contains 16 cases, not 14, and its first mutation uses string concatenation, so the guard must inspect AST tuple identifiers rather than `ast.literal_eval` the full tuple.

Exact Quarantine/Relay runs for the test-only and intermediate source heads were still in progress at the time of this handover write. Do not count those as PASS. Final exact-head Quarantine/Relay and Full results will be appended after terminal readback; Full remains independently subject to the inherited CORE/QA poll-signature contract.

## Scope boundary

This is Hardware-owned test/lab modularization only. No production ESP8266/ESP32 `.ino`, pin mapping, ISR, pulse capture, relay actuation, CGI producer, shared API, financial logic, signer, witness, migration, QA-owned assertion, COE destination or release workflow was changed.

Evidence is host-source SIMULATED / CI VERIFIED only when exact-head runs pass. Local independent execution is not claimed here. Physical coin pulse, relay/electrical recovery, LittleFS/EEPROM power-loss, 150 controlled cuts, and 30-device/24-hour soak remain NOT TESTED. **HARDWARE ACCEPTED: NO. PRODUCTION NO-GO.**

## Next exact action

Re-read PR #349 and the stacked #239/#254/#283/#340 heads, then inspect terminal exact-head Quarantine/Relay logs for the module-boundary guard and all 17/17 pulse scenarios plus 16 mutation rejections. Reconcile Full only through the CORE-authenticated producer contract and independent QA; do not invent `response_sig` or weaken deny-default.
