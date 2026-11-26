# PHX-HARDWARE UTC08 — ESP8266 controller request guard parity

**Task:** [P0 coin-pulse loss during synchronous poll #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)
**Control:** [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)
**Draft:** [PR #354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354)
**Role:** PHX-HARDWARE
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments` (repository ID `1389289885`)
**Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`
**Source commit:** `17950ceee07dfc68bf252d76a60ff47296c4cfcd`

## Proven source discrepancy

The active-v0.6 deny-only candidate already had ESP32 request guards but the ESP8266 sketch did not. ESP8266 `signedBody()` accepted empty key/ID and serialized the BearSSL digest without validating its 64-character hexadecimal form. ESP8266 `post()` had no action allowlist, no key/ID guard, no empty-body check, and passed `signedBody()` directly to `HTTPClient::POST`. This was a concrete cross-board fail-closed mismatch in Hardware-owned source; no CORE API change was needed.

## Implemented

- Added ESP8266 `validSha256Hex()` matching the existing ESP32 rule: exactly 64 hexadecimal characters.
- `signedBody()` now refuses an empty controller key or device ID, computes the existing BearSSL SHA-256 digest, rejects invalid digest output, and serializes only the validated digest.
- `post()` now permits only `register` and `poll`, requires nonempty key and ID, rejects an empty signed body before HTTP setup, and passes only the validated body to `HTTPClient::POST`.
- Request wire format, HMAC-like digest input construction, endpoint, timeout and BearSSL algorithm were not changed.
- No coin POST, remote config, relay enable, response consumption or pending disposition was added. The candidate remains deny-only.

## Test-first and exact-source evidence

- Test-only RED commit: `d13f282c257b50bdb4b59d53f1c735d7784ce949`.
- Expected RED [run #45787241292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45787241292), job `139797013376`: ESP8266 failed the missing request-auth/action guard contract; ESP32 passed its baseline and rejected nine injected regressions. Earlier matcher false positives are excluded.
- Focused GREEN push [run #45787375680](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45787375680), job `139797466705`: PASS. Both board contracts pass and nine mutations per board are rejected: missing signed-body credential guard, missing HTTP action allowlist, missing HTTP credential guard, key-only guard, ID-only guard, missing digest validation, missing empty-body guard, bypassed validated body, and digest-length bypass.
- Focused GREEN PR [run #45787384111](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45787384111), job `139797496182`: PASS.
- Native synthetic [run #45787384107](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45787384107), job `139797496443`: FAIL at QA-owned `tests/v060_vendo_sequence_contract.py` requiring active `clearPending(true/false)` callsites. The deny-only candidate intentionally has no active pending disposition callsite; Hardware did not edit QA-owned tests.
- Full [run #45787384199](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45787384199), validation job `139797731892`: FAIL at handover freshness because the source change had not yet been documented. Target jobs were still running at the last read. Rerun after this handover update; no Full PASS claimed.

## Acceptance boundaries

- Request-auth/action guard regression: SIMULATED / CI VERIFIED.
- ESP8266 and ESP32 physical request/auth behavior: NOT TESTED.
- Physical coin acceptor cutoff, relay polarity, electrical pulse/recovery, LittleFS power-loss: NOT TESTED.
- 150 controlled power cuts, 30-device / 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay, independent QA/release signoff: NOT ACCEPTED.
- HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## Cross-role requests

- **PHX-QA:** reconcile the native sequence assertion and controller parity checks with the deny-only candidate; do not require active pending disposition or unsigned `config_revision` consumption.
- **PHX-CORE:** publish the authenticated register/poll and event receipt/disposition contract before any positive response consumer or pending-event disposition is implemented.
- **PHX-MASTER:** update exact #354 head in `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md`; do not merge or rebase Hardware stacks without owner coordination.

**Next exact Hardware action:** rerun Full and ESP32 core 3.3.13/4.0.0 matrix at the final handover head; keep coin admission and relay actuation denied.
