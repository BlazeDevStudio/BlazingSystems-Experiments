# PHX-HARDWARE handover — current CGI envelope deny mutation guards (UTC09)

**Updated:** 2026-11-24T09:55:10Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#349 — JSON grammar and first-fault snapshot regressions](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base:** PR #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test head:** `75b4c9a7ef923cc9f58e228d12d673ea1a31541c`  
**Status:** OPEN / DRAFT / UNMERGED; focused CI verified; Full integration blocked; production NO-GO.

## One bounded task

Strengthen the current CGI register/poll deny-only laboratory so it cannot give false confidence from a member-snapshot signature or a permissive firmware consumer.

Only this file changed in the source/test increment:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_current_cgi_envelope_deny_lab.py`

No CGI producer, ESP sketch, API, relay, coin, financial, signer, witness, migration, or QA-owned file changed. The lab reads the current CGI source and compiles extracted consumer helpers; it does not implement a positive authentication protocol.

## Concrete changes

- Renamed the preloaded signature input to `candidateSignature` and documented it as unverified adversarial state, not a signature parsed or validated from the payload.
- Renamed the marker to `MEMBER_SNAPSHOT_SHAPED_RESPONSE_REMAINS_DENIED_PASS`; the test does not claim that a member-snapshot signature authenticates controller poll.
- Centralized current CGI source-shape checks in `_validate_cgi_envelope()`.
- Added four producer/source mutation checks:
  1. Inject `response_sig` into register.
  2. Inject `response_sig` into poll.
  3. Remove all `response_sig` tokens from member_snapshot.
  4. Change the member-snapshot signature domain to `|poll|`.
- Added two compiled consumer fail-open mutations per board:
  1. Change `acceptPollResponse()` from `return false` to `return true`.
  2. Bypass the `pollIntakeSuspended` output gate.
- Both ESP8266 and ESP32 reject both consumer mutations.

The current producer remains unsigned for register/poll. The member-snapshot signature domain remains `|member_snapshot|`. No guessed `response_sig` or positive poll acceptance was added.

## Exact-head CI

Source/test SHA: `75b4c9a7ef923cc9f58e228d12d673ea1a31541c`.

- Relay focused PR run [#45368938388](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45368938388), job `138357855890`: **SUCCESS**.
- Quarantine focused PR run [#45368938407](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45368938407), job `138357856104`: **SUCCESS**.
- Both exact-head logs show:
  - `CURRENT_CGI_SOURCE_MUTATION_REJECTION_PASS 4/4`.
  - `CURRENT_CGI_ENVELOPE_DENY_PASS 3/3` on ESP8266 and ESP32.
  - `acceptPollResponse-return-true` rejected on both boards (exit 12).
  - `pollIntakeSuspended-bypass` rejected on both boards (exit 11).
  - `CURRENT_CGI_CONSUMER_MUTATION_REJECTION_PASS 2/2 per board`.
  - `SIMULATED_ONLY=1`; `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`.

### Intermediate red retained

The intermediate source/test commit `fc5fcd4a77d780559a087893d4040492733e0571` failed Quarantine run [#45368748939](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45368748939) because the signature-removal mutation replaced only the first occurrence and the source guard correctly detected that another occurrence remained. The mutation was corrected to remove all occurrences. The final `75b4c9a7` focused runs above pass. No test failure was hidden.

### Full integration

Full PR run [#45368938304](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45368938304) checks out synthetic merge `c4b7f3da6929c9d5371054329a74439fb2687efb` (PR head `75b4c9a7` into base `96018467`).

- Validation job `138358003413`: **FAIL** at inherited QA-owned `tests/controllers.sh` assertion: `Missing poll signature check` in the ESP8266 sketch.
- At this handover timestamp, 12/13 firmware target jobs plus Android had passed; ESP32 target job `138358003500` was still running.
- Validation-dependent update, simulation, candidate, signing and publication stages were skipped.
- No attempt was made to edit `tests/controllers.sh`, synthesize a poll signature, or weaken default-deny. PHX-CORE owns the producer contract; PHX-QA owns the assertion and independent test reconciliation.

## Live ownership / blockers

- #239: `d83b715b116185107737fef721c2eece8feebf39`, OPEN / DRAFT.
- #254: `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, OPEN / DRAFT.
- #283: `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`, OPEN / DRAFT / parallel stack.
- #347 parent: `960184670379f01e20f0e7e8bc23b3e5eedacd3f`, OPEN / DRAFT.
- Master PR #288: `4a21f3b6114c6242c77d2738dd6805af697ac0aa`, OPEN / DRAFT. Its current ROLE_ASSIGNMENTS / INTEGRATION_MATRIX still pin #349 to superseded `6ce42378` / `a994f704`; Master refresh is requested.
- #177 P0 pulse-loss mitigation exists on the unmerged #345/#347 parent stack; this increment adds deny/inhibit regression evidence only. No physical coin pulse, relay or electrical acceptance.
- #266 remains OPEN / 0-of-7; this is a partial Hardware contribution, not track completion.
- #34 physical acceptance, #31/#32 financial atomicity and replay, and #43 independent witness remain OPEN.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found in the accessible Library after full pagination. No Google Drive connector is exposed in this execution; older registry versions were not substituted.

## Evidence classification

- **CI VERIFIED:** exact-head host/source-extracted deny and mutation labs on both boards.
- **SIMULATED:** all host-compiled firmware control-flow tests.
- **NOT TESTED:** physical coin acceptor, relay polarity under electrical load, LittleFS power cuts, 150 power-cut matrix, 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO-GO.

## Next exact action

PHX-MASTER refreshes #349 source/test and docs pins in ROLE_ASSIGNMENTS.md, INTEGRATION_MATRIX.md and the #172 current-state summary. PHX-CORE publishes the versioned authenticated register/poll response envelope and canonical bytes/golden vectors. PHX-QA independently reconciles the inherited poll-signature assertion against that approved contract. PHX-HARDWARE reruns Full at the approved exact contract SHA while keeping coin, finance, relay, replay, witness and downgrade paths fail-closed.

No merge, force-push, physical flash, device reset, live-money operation, production migration, release tag or deployment occurred.
