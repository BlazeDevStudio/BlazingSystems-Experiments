# PHX-L-VERIFY — synchronous flash journal write / coin edge QA (UTC22 supplement, 2026-10-25)

**Status:** TEST-FIRST SOURCE-TRANSCRIBED HOST RED / MASTER+CORE REVIEW REQUIRED / PRODUCTION NO-GO. No Codex, production source change, hardware, customer data, keys, flashing, merge or release.

## Exact authority and source

Read live #172, #177/#34/#43, draft #179/#193/#150/#183 and four canonical handover/policy files. Main `9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`; development comparison-only `2c2c1613f4ff5470bd53c23c91767050f936d8c7` (not approved integration base). #193 pre-QA source/documentation HEAD `5efcd5e9460865f54c22e981a380a4d27a047e6b`, ESP8266 Git blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`, ESP32 blob `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`. No firmware source edit in this task.

The original `loop()` in each sketch samples the coin GPIO, detects a rising active edge, increments `pendingPulses`, then calls synchronous `savePending()` → `persistPendingSequence()` (LittleFS write/flush/rename), before setting `lastCoin=active`. The existing `applyOutputs()` guard is invoked after the write only for a full journal, flash failure, or pendingReady. Thus the relay can remain logically enabled during an otherwise successful synchronous flash reservation. This is distinct from the already-mitigated blocking HTTP poll.

## Independently executed bounded QA

Compiled two board-specific versions of a manually **source-transcribed coin-edge excerpt** with `g++ -std=c++17 -O2 -Wall -Wextra -Werror`. The fake `savePending()` advances a synthetic clock by 0, 60 or **180 ms**. Two active-low input pulses occur at 100–130 ms and 230–260 ms; debounce 40 ms. In the 180 ms case the second pulse falls entirely inside the mocked flash write. This **180 ms is hypothetical, not measured ESP LittleFS latency**.

- **18/18 expected host observations PASS** (9 per board), zero compiler errors.
- No-stall and 60 ms controls: 2 sampled edges and 2 journal-write requests per board.
- Hypothetical 180 ms write: 1 sampled edge, 1 journal-write request, second pulse overlaps the synchronous write, modeled relay logically ON. Both boards reproduce the same gap.
- Explicit fail-closed safety gate: **RED on both boards** (exit code 2), not a GREEN firmware fix.
- The fixture models only the coin-edge excerpt, not full Arduino execution, real LittleFS latency, actual electrical supply, a physical coin acceptor, or financial credit. A simulated pulse while relay logically ON is not proof that real acceptor power remains ON or that money was lost.

Local reproducible evidence archive: `phx_verify_utc22_flash_window_evidence.zip`, SHA-256 `ae336df34818d7b8fb4cec4b4cce83bd16c8fa9adb0d66e5e04663f47264fb64`; C++ harness SHA-256 `6c820142701cc4634966260a947d4d047fdec7094c87add9326d48b6881e85db`; ESP8266 and ESP32 output hashes `21024051f6988fa58e4acf432867b845a48b92e1a8544cf910d1836123bc36f8` and `ff07e2ba244901b6ed908b0b4d581f18740800a6d9e14508e458b02e1dba8c29`. The archive is attached to the ChatGPT run, **not** uploaded to GitHub; this report does not claim independently accessible GitHub artifacts.

## CI classification and next action

Exact pre-QA docs HEAD `5efcd5e9460865f54c22e981a380a4d27a047e6b`: Full [#40238267671](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40238267671) **COMPLETED FAILURE**, validate job `121304438629` with 13 PASS / 2 config-auth and cold-reboot RED **per board**; ESP8266/ESP32 Arduino builds SUCCESS. Native [#40238267630](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40238267630) **COMPLETED SUCCESS**. These existing failures are unrelated to the new host fixture. Subsequent documentation-only CI requires fresh exact-head classification.

**MASTER/CORE review:** obtain actual worst-case flash write/flush/rename latency distributions and independent coin GPIO/supply/relay waveforms on authorized noncustomer hardware before deciding if an admission inhibit around synchronous writes is necessary. Inhibiting a relay mid-pulse could itself lose coins; do not patch without an in-flight edge/power-window contract. Evaluate nonblocking capture and durable reservation ordering without relying on RAM-only pulse counts. Previously journaled payments must remain reconcilable; no unilateral source integration.

**Hard gates:** #31/#32 paid finance, #43 independent monotonic witness, #34 real 150 power cuts and 30-device 24-hour soak, reversible migration, permanent signing, real electrical acceptance remain OPEN. #193 stacked on unmerged #179; #150/#183 separate unmerged; #173 closed unmerged. **PRODUCTION NO-GO.**
