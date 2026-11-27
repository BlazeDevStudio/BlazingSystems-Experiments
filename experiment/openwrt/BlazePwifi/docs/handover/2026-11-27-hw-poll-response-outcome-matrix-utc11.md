# PHX-HARDWARE — Poll response outcome matrix (UTC11)

**Date:** 2026-11-27  
**Role:** PHX-HARDWARE  
**Task:** P0 #177 / deny-only poll preflight regression coverage  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-poll-response-outcome-matrix-20261127-utc11`  
**Parent:** DRAFT PR #355 at `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`  
**Parent base:** PR #354 at `fc842342596786e072630179acfbbc4feeb2ba02`  
**Active v0.6 comparison baseline:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**Final source/test SHA:** `04ac3330c0123e581bf4f195ff5f1a5089b82ffb`

## Scope and reason

The current deny-only candidate explicitly discards `post("poll")` responses and disables coin/relay/LED state before and after the synchronous request. The previous source-extracted host harness represented only the empty `post()` response. That covered a transport-failure-like outcome but did not exercise a success-like positive body or detect a transient output enable between response handling and the post-poll deny.

This child adds that missing negative-only outcome coverage. It does not change firmware, shared APIs, coin admission, relay policy, pending disposition, finance, or migration.

## Exact code changes

1. `poll_preflight_inhibit_lab_harness.py`
   - The deterministic `post()` stub returns a fixture-injected response body.
   - The host output model records any relay or LED logical ON write after the initial energized precondition is reset.
   - The harness rejects transient ON writes even if a later post-poll deny turns the outputs OFF again.

2. `poll_preflight_inhibit_lab_cases.py`
   - Runs both an empty response (transport/HTTP failure representation) and an untrusted positive response body.
   - Injects a response consumer that briefly enables relay/LED before the post-poll deny; the harness rejects it on both boards.

## Commits

- `96b838da3c5ef8b3f43c1dc05988486be4790101` — first response-outcome harness change
- `285d508852bdd806597f8e99b37a566d01641696` — positive-response consumer failure injection
- `5aa139f57538e045d8656530ed4c59abcebbe9cd` — response-body fixture substitution
- `04ac3330c0123e581bf4f195ff5f1a5089b82ffb` — corrected newline escaping in mutation fixture

## Exact GitHub Actions evidence

- Initial PR-head focused run [#45989302533](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45989302533), job `140472769635`: **FAIL**. The Python mutation fixture emitted literal `\\n` sequences into generated C++, producing stray-backslash compiler errors. This was a test-fixture implementation error, not a firmware failure.
- Final source/test focused run [#45989512681](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45989512681), job `140473488721`, exact checkout `04ac3330c0123e581bf4f195ff5f1a5089b82ffb`: **PASS**.
  - ESP8266: empty body and 52-byte positive body ignored; transient-actuation mutation rejected (exit 23); missing pre-poll deny rejected (exit 19); relay/LED polarity and deny-state mutations rejected.
  - ESP32: same outcome matrix and mutation rejections.
  - Existing register, remote-config, request-auth, output-enable sequence, EEPROM/NVS validity, configuration-write and pending-journal labs passed.
  - Append-only ledger check: `CHANGE_LEDGER_APPEND_ONLY_PASS base_bytes=1132798 appended_bytes=16341`; seven append-only unit tests passed.
  - Explicit limitation lines: `POLL_INTAKE_GUARD_SIMULATED_ONLY=1`, `PHYSICAL_COIN_RELAY_ACCEPTANCE=0`, `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.
- Full [#45989512778](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45989512778), validation job `140473712696`: **FAIL at handover freshness** because canonical `PROJECT_HANDOVER.md` was not updated after the source/test changes. This final docs sync is now committed; a new exact-docs-head Full run is required. The prior run's target jobs were still in progress, so no aggregate target result is claimed.

## Safety and ownership

- No production sketch changed.
- No positive poll response is accepted.
- No automatic coin POST, retry, or pending clear was added.
- No CORE/QA/Master-owned file or shared contract was changed.
- Parent #355 and its #354 base remain OPEN / DRAFT / UNMERGED; no rebase, retarget, force-push, or merge was performed.
- Keep coin, relay, financial, replay, witness, and downgrade behavior fail-closed.

## Acceptance classification

Host/source-extracted tests: **SIMULATED**; focused exact-SHA Actions: **CI VERIFIED**; Full integration: **NOT YET VERIFIED** (previous run stopped at handover freshness); local board hardware: **NOT TESTED**; physical coin/relay/electrical acceptance: **NOT TESTED**; 150 power cuts / 30-device 24-hour soak: **NOT TESTED**. **HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.**

Private Google Drive registry `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not recovered through the exposed connector surface or Library search; no older snapshot was substituted.

## Next exact action

Recheck the exact docs-head focused and Full workflows. If Full reaches the known QA-owned controller/pending-disposition assertions, request QA's deny-only reconciliation and CORE's approved authenticated poll/receipt contract. Keep PR #360 DRAFT and unmerged.
