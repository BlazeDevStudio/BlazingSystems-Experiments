## PHX-HARDWARE UTC20 — 2026-11-27 UTC20 — EEPROM validation CI verified; ESP8266 target compile correction in progress

**Role:** PHX-HARDWARE · **Task:** #177 / #355 · **PR:** OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hw-poll-preflight-lab-modules-20261127-utc18 · **Current docs HEAD before this update:** 6495ab4bcd5d7af5e526c12c3b68a133a5d9cf7b  
**Source/test SHA:** 93e850db847760f51a4470c4bda1c46bfc730278 · **Firmware fix:** 106aabb007b7b4c2aee1978645d07214cf668e87.

### Verified task result

The new bounded EEPROM config guard is source-extracted and sanitizer-tested. Exact focused run [#45893204086](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893204086), job 140160658946, PASS: current arrays 6/6 and legacy arrays 5/5 reject unterminated values; 3/3 unsafe source mutations rejected.

### New target-build blocker

Full run [#45893204180](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893204180) failed its handover freshness gate because this source/test SHA followed the previous checkpoint. Separately, its ESP8266 compile job 140160838218 failed:

BlazePwifiVendo.ino:106:38: error: 'LegacyPendingRecord' does not name a type

The bounded helper block was inserted before LegacyPendingRecord. Arduino's sketch prototype generation now places the legacyPendingChecksum(const LegacyPendingRecord &) prototype before the type declaration. This is a source ordering/build failure, not a test failure. Move the helper block after the LegacyPendingRecord declaration and add a source-order regression assertion. No behavior change is intended.

Native synthetic [#45893204123](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893204123), job 140160659781, remains FAIL at QA-owned active clearPending(true/false) assertion. Do not add a callsite without CORE's authenticated disposition contract.

### Next exact action

Move the bounded helpers below LegacyPendingRecord, assert the declaration ordering in the lab, then rerun focused and ESP8266 target builds at the exact source SHA. Keep the candidate deny-only. Physical acceptance remains NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
