# PHX-HARDWARE UTC07 — exact Content-Length readback for bounded controller responses

**Updated:** 2026-11-25T07:28:38.617Z  
**Role:** PHX-HARDWARE  
**Issue scope:** #177 / cleanup-first #266  
**Existing DRAFT:** [PR #349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base:** PR #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** `4ba665b5c36b1828735242b35de4302d3e2f6068`  
**Status:** FOCUSED CI VERIFIED / FULL INTEGRATION FAILED AT CORE-OWNED POLL CONTRACT / SIMULATED ONLY / HARDWARE NOT TESTED / PRODUCTION NO-GO

## Defect and risk

Both ESP sketches' `readBoundedControllerResponse()` rejected non-2xx status, unknown or oversized Content-Length, and Transfer-Encoding before calling `HTTPClient::getString()`. It then returned the materialized String without verifying that the number of bytes returned equaled the declared Content-Length.

A source-extracted fake-HTTP case declared 12 bytes but returned the complete-looking 11-byte JSON body `{"ok":true}`. Before the fix, the helper returned that partial body instead of denying the framing mismatch. This is a transport-integrity defect even though the current poll/coin consumers remain deny-only and `coinPostDispositionVerified()` does not authorize paid disposition.

## Test-first evidence

- Test-only commit: [`42193df4`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/42193df4ad2b9c723da7182ec6be33b56cdda128).
- Exact RED: [Relay run #45566784443](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45566784443), job `139043401379`. The bounded-response baseline failed at the new short-read case with exit 71 on ESP8266, proving the missing check. The failure was before any source fix.

## Source correction

- [ESP8266 fix `3b6c001a`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3b6c001acc3dfc882bfc0e83df374dd706fda1bb): materialize the already size-bounded body, compare `(int)body.length()` to the declared response size, and return empty on any mismatch.
- [ESP32 parity `f86d5ee1`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f86d5ee14d7966dc6a343cedc8555ca0e6201cf1): same fail-closed behavior.
- [Lab mutation coverage `ce17ddd7`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ce17ddd72ff2dbdf45c3f4f43fc4505d34d8dabb): short and over-length mismatch cases plus a mutation removing the exact-length guard.
- [Summary correction `4ba665b5`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4ba665b5c36b1828735242b35de4302d3e2f6068): corrects the printed denial count to 9.

The existing 201 `created` fixture now declares its actual 7-byte body length. The 1024-byte accepted boundary, zero-byte 204 response, status handling, unknown-length denial, oversized denial and Transfer-Encoding denial remain covered.

## Exact final-source CI — SHA `4ba665b5`

- Quarantine [#45567810981](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45567810981), job `139046796944`: **PASS**.
- Relay [#45567811070](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45567811070), job `139046797538`: **PASS**.
- Both logs show ESP8266 and ESP32 `BOUNDED_HTTP_RESPONSE_PASS allowed=3 denied=9 mutations=5/5`; the `missing-exact-content-length-readback` mutation is rejected on both boards with expected exit 71.
- Full [#45567811125](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45567811125), validation job `139047035300`: **FAIL** at inherited `Missing poll signature check` in the ESP8266 sketch. Thirteen firmware/platform build jobs plus Android passed. Downstream simulations, update bundle, signing and publication stages were skipped.

## Scope boundary

Only the two Hardware-owned ESP controller sketches and `bounded_http_response_lab.py` changed for this task. No CGI producer, shared API, credit/ledger authority, coin admission, relay actuation, signer, witness, migration, COE destination or release workflow was changed. The controller response remains non-authoritative; no new positive poll/coin path was enabled.

## Current release blockers

- CORE must publish the approved authenticated register/poll response contract; current CGI register/poll envelopes still lack `response_sig`.
- QA must independently reconcile the inherited Full validation assertion without weakening deny-default.
- MASTER must reconcile the #340 base snapshot against current #283 ancestry.
- #239, #254 and #283 remain open, unmerged DRAFTs; #340 and #347 also remain separate stack candidates.
- Physical coin/relay/electrical recovery, EEPROM/LittleFS durability, 150 controlled power cuts, and 30-device/24-hour soak remain **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration, and independent QA/release acceptance remain **NOT ACCEPTED**.
- Private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not recovered through the available connected sources; no older registry snapshot was substituted.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

## Next exact action

MASTER refreshes the #349 role/CI pin and reconciles #340/#283 ancestry; CORE publishes the authenticated register/poll producer contract; QA reviews the corresponding assertion independently. PHX-HARDWARE keeps deny-default and, on the next activation, revalidates the live stack before choosing one new unblocked Hardware-owned task. No flash, device reset, live-money test, migration, merge or release is authorized by this handover.
