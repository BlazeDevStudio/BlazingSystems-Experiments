# PHX-HARDWARE handover — shared lexical extractor in host labs

**Updated UTC:** 2026-11-20T07:47:42.104Z
**Role:** PHX-HARDWARE
**Task:** #177 / #266 / PR #327
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`
**Exact source/test commit:** `726981b49fb415fd10b764cbb8c386a00fcdbcf1`
**PR state:** OPEN / DRAFT / UNMERGED

## Change

Two hardware-owned host labs duplicated a naive brace-counting source extractor:

- `esp32/BlazePwifiVendo32/coin_post_gate_lab.py`
- `esp32/BlazePwifiVendo32/pending_attempt_marker_lab.py`

The duplicated scanners counted braces without masking comments and C/C++ literals. That could truncate or misidentify a production helper if a comment, ordinary string, character literal, or raw string contained braces.

Both labs now reuse the existing shared `firmware_lab_source.py` lexical parser:

- `extract_function()` for actual function definitions.
- `extract_block()` for the `PendingRecord` structure.
- The old local `extract()` implementations were removed.

The shared helper already has source-offset-preserving lexical handling and is exercised by the existing `coin_pulse_capture_lab.py` extractor regressions. The two updated labs still compile and exercise the actual ESP8266 and ESP32 production helpers. Existing failure-injection scenarios were retained unchanged.

No runtime `.ino`, pin map, persistence format, CORE API, finance path, QA-owned test path, or Release-owned workflow was changed.

## Exact-head CI evidence

All runs below checked out source/test SHA `726981b49fb415fd10b764cbb8c386a00fcdbcf1`.

- Quarantine/readback push [run #44697304673](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697304673), job `136157030226`: **SUCCESS**. Logs include `PENDING_ATTEMPT_MARKER_PASS 28/28` for each board (56/56 total), `COIN_POST_GATE_PASS 10/10` per board, `COIN_POST_DISPOSITION_DISPATCH_PASS 7/7` per board, and rejection of the event-bound-authentication bypass mutation (exit 11). Poll-window and existing safety mutation suites also passed.
- Quarantine/readback PR [run #44697312845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697312845), job `136157056717`: **SUCCESS**.
- Relay/output polarity PR [run #44697312882](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697312882): jobs `136157056494` and `136157056676` **SUCCESS**.
- Full BlazePwifi PR [run #44697312866](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697312866): validation job `136157057324` **FAILED** at the QA-owned controller parity assertion `Missing poll signature check`. This hardware change did not invent a positive signature or weaken default-deny. Other target jobs were still running at the time this handover was written; no Full PASS is claimed.

## Evidence classification and blockers

- Shared extractor and both hardware labs: **SIMULATED / CI VERIFIED**.
- Actual LittleFS/NVS/EEPROM durability, physical coin acceptor, relay/electrical behavior, 150 power cuts, and 30-device/24-hour soak: **NOT TESTED**.
- **HARDWARE ACCEPTED:** not established.
- **PRODUCTION READY:** NO-GO.

PHX-QA owns the stale positive poll-signature fixture. PHX-CORE owns the authenticated register/poll and event-bound receipt contract. PHX-MASTER owns the canonical assignment/head index. PHX-RELEASE owns core-version reproducibility. No other role's source was changed.

The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed Drive/Library connector surface in this activation. No older registry snapshot was substituted and no private content was copied to GitHub.

## BLAZE-COMMS/1 checkpoint

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261120T07-SHARED-LEXICAL-EXTRACTOR",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-QA", "PHX-CORE", "PHX-RELEASE"],
  "type": "PROGRESS",
  "priority": "P2",
  "task_id": "#172/#177/#266/#327",
  "repository": "BlazeDevStudio/BlazingSystems-Experiments",
  "branch": "phoenix/hardware-prepoll-edge-abort-20261119",
  "base_sha": "58c558fb6a237935214621adc3dee65a10fe1a51",
  "source_test_sha": "726981b49fb415fd10b764cbb8c386a00fcdbcf1",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/coin_post_gate_lab.py",
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/pending_attempt_marker_lab.py"
  ],
  "status": "VERIFIED",
  "evidence": [
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697304673",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697312845",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697312882"
  ],
  "blockers": [
    "Full BlazePwifi validation fails at QA-owned Missing poll signature check",
    "Physical hardware acceptance and production durability gates remain NOT TESTED",
    "Private v11 Drive registry unavailable through exposed connector"
  ],
  "next_action": "PHX-QA repairs the stale poll-signature fixture with source-exact default-deny tests; PHX-MASTER refreshes the canonical #327 head; PHX-HARDWARE revalidates the stack before the next owned change.",
  "updated_utc": "2026-11-20T07:47:42.104Z"
}
```
