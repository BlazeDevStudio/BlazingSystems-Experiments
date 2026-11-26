# PHX-HARDWARE UTC16 — blocking-poll wait harness

**Owner:** PHX-HARDWARE  
**Issue / draft:** [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) / [#354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354)  
**Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`  
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**Source/test SHA:** `145aac9607682071e2db05944a6f9db5aa06e524`  
**Status:** OPEN / DRAFT / UNMERGED · host simulation CI verified · physical acceptance NOT TESTED · PRODUCTION NO-GO.

## One bounded Hardware-owned change

The previous `poll_preflight_inhibit_lab.py` comment claimed a 3500 ms HTTP wait, but the old harness only invoked extracted `denyRemoteControl()` and immediately inspected outputs. It did not execute the poll block, advance time, or inject a coin pulse.

This change adds a second source-extracted C++ harness that executes the actual poll block from both board sketches. The stubbed `post("poll")` advances exactly 3500 simulated milliseconds and injects an 80 ms coin-line pulse while the loop is blocked. Every simulated millisecond it checks:
- relay and LED outputs remain logically OFF across all four independent relay/LED polarity combinations;
- controller, coin, relay, LED and insert admission flags remain denied;
- pending pulse count, nonce and target remain unchanged;
- no coin sample occurs while the synchronous call is blocked;
- the next sample happens after the injected pulse has ended and no coin pulse is accepted.

The harness also removes the pre-poll deny in a negative mutation and changes the relay OFF write to borrow LED polarity. Both must fail. This is a host simulation, not a physical GPIO or coin-acceptor test.

## Test-first history and exact evidence

- Initial fixture attempt `05be6faf86290de70cc10ea7e6cce8ecb1108f02`: focused [#45862503824](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45862503824), job `140056856073`, failed at C++ fixture compilation because of newline escaping, a split diagnostic literal and missing `wifiFailures` stub. **Excluded as test-authoring failure; not RED evidence.**
- Corrected fixture `f93cf9b80f7777f6b2aff31cc15b41ac005e1a14`: focused push [#45862737466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45862737466), job `140057673814`, and PR [#45862745148](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45862745148), job `140057700491`, compiled and failed at the intended assertion `BLOCKING_POLL_WAIT_RED elapsed_ms=0 expected=3500`.
- Final source/test SHA `145aac9607682071e2db05944a6f9db5aa06e524`: focused push [#45862938002](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45862938002), job `140058369164`, PASS; PR exact-source [#45862948688](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45862948688), job `140058405613`, PASS.
- Both ESP8266 and ESP32 logs report `BLOCKING_POLL_WAIT_PASS 3500ms pulse_ticks=80 samples_during_wait=0 accepted=0 polarity_combinations=4`.
- Both boards reject missing pre-poll deny and relay-OFF borrowing LED polarity during the wait (exit 19). Independent polarity mutations are also rejected (exit 12); deny-state mutation rejected (exit 11). The existing output-enable lab reports 8/8 board/polarity scenarios and 14/14 injected regressions rejected.
- The source sketches independently confirm `HTTPClient::setTimeout(3500)`: ESP8266 blob `b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9`; ESP32 blob `3edbe38da543ef118b287f3e04c1601692cfa99f`. Neither sketch was modified in this work item.

## Integrated gates and ownership boundaries

- Native [#45862948850](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45862948850), job `140058431258`, FAILS at QA-owned `tests/v060_vendo_sequence_contract.py:20`, which still requires active `clearPending(true/false)` callsites. The deny-only candidate intentionally preserves pending evidence and has no active disposition callsite. PHX-HARDWARE did not edit QA tests or weaken the safety boundary.
- Full [#45862948745](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45862948745), validation job `140058560211`, FAILS the mandatory handover freshness gate because the source/test commit postdated the previous canonical handover commits. This is a documentation-sync failure, not a firmware build result; a fresh Full run is required after this checkpoint. Target jobs were still running when this handover was written.
- PHX-QA must reconcile deny-only assertions; PHX-CORE must publish the authenticated register/poll and receipt/disposition contract; PHX-MASTER must refresh #354's branch pins in `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md`.
- Keep coin and relay admission denied. Do not consume unsigned poll fields, perform pending disposition, or enable a positive response consumer.

## Status boundaries

- Host/source-extracted behavior: **SIMULATED / CI VERIFIED**.
- Physical GPIO voltage/contact transient, real coin acceptor behavior, electrical pulse/recovery, LittleFS power-loss, 150 controlled power cuts, and 30-device/24-hour soak: **NOT TESTED**.
- **HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.**
- No flash/reset, live money, customer device, migration, signer, release tag, merge, or deployment.

## Provenance and rollback

The canonical `CHANGE_LEDGER.md` was successfully appended in this checkpoint after retrieving its large blob through Git Data. No history was truncated or replaced. The private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the connected runtime; no registry-derived migration or promotion occurred.

Rollback is limited to reverting this work item's source/test commits `05be6faf`, `f93cf9b8` and `145aac96` on this existing Hardware draft branch. Preserve the pre-existing #239, #254 and #283 branches and do not rebase or force-push.
