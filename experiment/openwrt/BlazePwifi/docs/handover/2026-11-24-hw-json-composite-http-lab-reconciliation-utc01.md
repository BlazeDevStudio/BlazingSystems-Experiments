# PHX-HARDWARE UTC01 — JSON composite and bounded HTTP lab reconciliation

**Observed:** 2026-11-24 UTC01  
**Role:** PHX-HARDWARE  
**Task:** #177 / #266 / #349  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent PR:** #347, exact base `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test HEAD:** `8fdb4894cbed5072dd62f09b0e5cb44775ad2d36`  
**PR:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349), OPEN / DRAFT / UNMERGED

## Work completed

The parser implementation in commit `e3aa052a973edd78a2db00e7278f44adf6226cec` replaces delimiter-only nested JSON skipping in both ESP8266 and ESP32 sketches with bounded recursive composite grammar validation (maximum composite depth 16). It validates array/object separators, object keys and colons, primitive termination, trailing delimiters and matching closing characters. The parser remains structural only; it does not grant controller or financial authority.

Two test-harness defects found by exact-head CI were corrected:

1. `bounded_http_response_lab.py`: the status-deny mutation now uses `((void)statusCode, false)`, retaining a warning-clean parameter use while removing the status predicate. This allows the fail-open mutant to compile under `-Werror` and be rejected by its expected exit code. Commit `eb5c4b093e79032d8bf55512f4a5d2902c1c5814`.
2. `request_digest_failure_lab.py`: the extracted production `post()` now receives the real `readBoundedControllerResponse()` helper and its source constant; the minimal HTTP stub implements `getSize()`. This fixes a missing declaration in the digest fixture. Commit `8fdb4894cbed5072dd62f09b0e5cb44775ad2d36`.

An intermediate assembly revision `fc7168bdde7c3c19953f21b0ca54fb7403607e21` had over-escaped the Python regex/newline literals; the next commit `8fdb489` corrected those source strings. No production `.ino` sketch changed during this UTC01 follow-up.

## Exact CI evidence at source/test HEAD `8fdb489`

- Quarantine [run #45308531038](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45308531038), job `138158182677`: **PASS**.
  - ESP8266 and ESP32 nested JSON composite grammar: 5/5 valid accepted, 6/6 malformed rejected; the 3 failure mutations rejected on both boards.
  - Bounded HTTP response: 3/3 mutations rejected per board; `BOUNDED_HTTP_RESPONSE_BOTH_BOARDS_PASS`.
  - Request digest failure: empty/short/non-hex digest dispatches zero HTTP requests; valid 64-character hex digest dispatches one request, both boards PASS.
  - Existing poll, quarantine, EEPROM/config-read and boot-deny labs passed; logs explicitly retain `SIMULATED_ONLY=1` and physical acceptance flags at zero.
- Relay [run #45308531479](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45308531479), jobs `138158183823` and `138158184151`: **PASS**.
  - Coin-pulse capture 17/17 per board; poll-response fail-closed 11/11, strict root JSON 13/13, coin POST ACK root status 4/4 and disposition default-deny 4/4 per board.
  - Poll-window, relay-output and ESP32 boot-polarity checks passed; nested composite and bounded HTTP mutation markers passed.
- Full build push [run #45308523811](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45308523811): **terminal FAILURE**.
  - All 13 firmware target jobs passed (ESP8266, ESP32, x86_64, Ruijie and the configured Orange Pi matrix); Android also passed.
  - Validation job `138158172309` failed at the inherited `Missing poll signature check` in the ESP8266 sketch.
  - Twelve downstream simulation/update/signing/candidate/publication jobs were skipped.
- Full PR event [run #45308530954](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45308530954): validation job `138158191392` also failed the same controller protocol parity assertion; remaining target jobs were still completing at handover time. Do not count this as a Full pass.

## Contract and ownership boundary

Current main CGI producer `experiment/openwrt/BlazePwifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo`, blob `2e3a1430d08cc6606429a042df3b5848f53c7267`, returns register/ping and poll payloads without `response_sig`. Existing response signatures are emitted for member snapshot/member operations, not for the register/poll envelope. PHX-CORE owns the authenticated producer contract and golden vectors; PHX-QA owns the inherited parity assertion. Hardware must not invent a positive legacy signature or weaken default-deny.

The #177 poll-intake mitigation already present in the #347 parent stack remains source-extracted/simulated: the acceptor is inhibited before synchronous poll I/O, ISR edge deltas are reconciled, and unresolved edges latch fail-closed fault evidence. This activation changed test infrastructure only, not production sketch behavior.

## Current repository/stack state

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Master coordination PR #288: `ca12b1ae9c10c78f2f2ec3f19e50b013881046f9`.
- Protected DRAFT stack remains open/unmerged: #239 `d83b715b`, #254 `84c442a4`, #283 `4dd0b01b`, #345 `ca72497e`, #347 `96018467`, #348 `c1882689`, #349 current source/test `8fdb489`.
- COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE #26 remains OPEN / DRAFT / FROZEN. No COE source was migrated or promoted.
- Cleanup-first #266 remains 0/7 complete; no ownership checklist was changed.
- Repository rename is confirmed: the historical `BlazingSystems/BlazingSystems-Experiments` endpoint resolves to canonical `BlazeDevStudio/BlazingSystems-Experiments`.
- Private Drive registry `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not accessible through the available connectors or Library search. No older registry was substituted.

## Evidence classification and next action

- Nested parser, bounded HTTP and digest failure labs: **CI VERIFIED / SIMULATED** at exact source/test SHA `8fdb489`.
- Firmware target builds: **CI VERIFIED** in the terminal Full push run; integration validation still fails.
- Physical coin acceptor, relay/electrical recovery, LittleFS power-loss, 150 controlled power cuts and 30-device 24-hour soak: **NOT TESTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

**Next exact action:** PHX-CORE publishes the authenticated register/poll envelope, canonical bytes and golden vectors; PHX-QA reconciles `Missing poll signature check`; PHX-MASTER refreshes the #349 source/test/docs pins. Hardware then reruns Full integration on the approved exact stack without changing fail-closed admission.
