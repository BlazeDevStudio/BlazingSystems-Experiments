# PHX-HARDWARE handover — output-enable lab uses the shared lexical extractor

**Date:** 2026-11-20 UTC14  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Exact source/test HEAD:** `dc9af45eaa33713713473cfa1ea8ab051769286f`

## Selected task

Cleanup-first #266 audit found that `output_enable_sequence_lab.py` retained a local regex + raw brace counter even though the Hardware-owned `firmware_lab_source.py` already provides a lexical-aware C/C++ extractor. A brace inside a quoted literal could terminate the extracted production function early. That creates a false-confidence risk in a safety-relevant lab that checks relay/LED OFF-latch ordering before enabling GPIO output mode.

## Test-first reproduction

- Test-only RED commit: [`3b13d2c9e5c088940c1559976f77a6546fecffe6`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3b13d2c9e5c088940c1559976f77a6546fecffe6).
- Exact PR run [#44754625028](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44754625028), job `136351001423`, checked out the literal RED SHA and failed as expected at `Verify OFF latch is preloaded before output enable`: `OUTPUT_EXTRACTOR_FAIL: non-code brace truncated target()`.
- The fixture contains an ordinary string brace, a C++ raw-string brace, and braces in line/block comments. The old counter stops at the ordinary string's `}`.

## Correction

- Removed the local regex/brace-counting implementation.
- Reused `from firmware_lab_source import extract_function as extract` for both `writeLogical()` and `configureRuntimePins()`.
- Retained the lexical fixture in the lab so future changes cannot silently remove this guard.
- The fixture requires the extracted function to include the code after the literal/comment braces and exclude the following function.

No production `.ino`, pin assignment, runtime state machine, persistence schema, CORE API, coin/finance path, QA-owned validation, or Release-owned workflow was changed.

## Exact-head validation

- Focused Relay Output Polarity PR [#44755257204](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44755257204), job `136353175658`: **SUCCESS** at exact source/test SHA `dc9af45eaa33713713473cfa1ea8ab051769286f`. Literal checkout SHA passed; log contains `OUTPUT_EXTRACTOR_LEXICAL_FIXTURE_PASS`; the output-enable lab and its existing active-high/active-low and unsafe-order mutations passed.
- ESP32 boot-polarity job `136353175346` in the same run: **SUCCESS**.
- Focused Quarantine/Byte Readback PR [#44755261300](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44755261300), job `136353192635`: **SUCCESS** at the same exact SHA.
- Full BlazePwifi PR [#44755257665](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44755257665): validation job `136353373364` **FAILED** at QA-owned Controller protocol parity with `Missing poll signature check` in the ESP8266 controller sketch. All 14 target/Android build jobs completed **SUCCESS** (ESP8266, ESP32, Android, Ruijie, Orange Pi targets and x86-64). Downstream simulations, update bundle, signing, candidate gate and publishing were skipped. This is not Full validation acceptance.

## Evidence classification and limitations

- Shared extractor lexical regression: **CI VERIFIED**.
- Output sequencing and fault-injection host labs: **SIMULATED / CI VERIFIED**.
- ESP8266/ESP32 and target build jobs: **CI VERIFIED**.
- Physical relay polarity, coin acceptor pulse conditioning, electrical recovery, 150 power cuts and 30-device/24-hour soak: **NOT TESTED**.
- Durable financial replay/migration, protected signer/witness and independent release signoff: **NOT ESTABLISHED**.
- **PRODUCTION NO-GO.**

## Coordination

- PHX-QA owns the inherited positive poll-signature parity assertion. Do not restore a fabricated positive response marker or weaken default-deny admission to make Full green.
- PHX-MASTER owns `coordination/phoenix/ROLE_ASSIGNMENTS.md`; its active #327 head snapshot is stale and needs reconciliation to the live PR head after this handover commit.
- PHX-HARDWARE retains ownership of this lab and its firmware source. No parallel #239/#254/#283 stack was modified.

## Next exact action

PHX-QA should replace the stale positive poll-signature assertion with source-exact default-deny validation and rerun Full. PHX-MASTER should refresh the canonical #327 head and preserve the #326 parent ancestry. PHX-HARDWARE should continue the next bounded ESP32/ESP8266 task only after revalidating all active heads.
