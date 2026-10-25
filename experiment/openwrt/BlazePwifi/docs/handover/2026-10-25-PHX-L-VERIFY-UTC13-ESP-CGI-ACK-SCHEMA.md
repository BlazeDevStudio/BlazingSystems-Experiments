# PHX-L-VERIFY UTC13 — ESP ↔ CGI coin ACK schema compatibility (NO CODEX, draft-only)
Date: 2026-10-25T13Z. Owner: PHX-L-VERIFY. Decision: **REVIEW REQUIRED; PRODUCTION NO-GO**.

## Source provenance
- Draft stacked PR #193, pre-report head `8da4b8319ef584b210cc8e01a23ea0d777aab67d`, stacked on unmerged draft #179; not integrated into development.
- Actual CGI `openwrt/rootfs/www/blazepwifi/cgi-bin/vendo` Git blob `db58041c0575ad0a1101d99cb85403e03c8dcb22`.
- Actual ESP8266 sketch blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`; ESP32 blob `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`.
- Firmware `post()` returns HTTP response bodies for positive status; `loop()` invokes `clearPending(true)` on substring `"ok":true` for pending coin.
- CGI ordinary fresh response: `ok,duplicate,credited_cents,credit_cents,target_nonce`; duplicate response same field names. Rental response: `ok,duplicate,rental,lease_until,received_pulses,received_cents,target_nonce`.
- CGI computes ordinary coin receipt identity from controller ID, request event nonce, target and pulses but does **not** return that receipt/event identity or a signed terminal ACK in those coin response JSON bodies.

## Bounded independent execution
Local read-only Python3 source-transcribed CGI JSON-template compatibility probe, not a running CGI invocation:
- Four cases: ordinary fresh/duplicate, rental fresh/duplicate.
- 24/24 assertions passed (6 per case): JSON parses, target matches two different pending-event nonce identities, no event nonce/receipt/signature fields, required proposed binding fields incomplete, old firmware substring accepts, and responses cannot distinguish the two event nonces.
- Fixture SHA-256 `3f345d7cbece8d2140b52dca01dd86e7323f62a02720f21164c2c5f73a9dac71`.
- Captured result SHA-256 `cf7c1954c5d2d4b68d6698df01c7e374e3af1bdfefa23a26203da81b65a810f9`.
- This is **schema compatibility evidence**, not proof of a forged server ACK, actual double credit, signed CGI execution, real hardware or electrical relay behavior.

## Exact-head CI reconciliation
At pre-report #193 head `8da4b8319ef584b210cc8e01a23ea0d777aab67d`:
- Full #40195274873 **COMPLETED FAILURE** (15 success, 1 validate failure, 13 skipped). Validate job #121175008645: ESP8266/ESP32 each `CHECKS 15 FAILED 2`, specifically `untrusted_positive_revision_cannot_enable_coin` and `cold_reboot_older_positive_revision_cannot_enable_coin`. Both ESP compiler jobs successful.
- Native #40195274874 **COMPLETED SUCCESS**.
- No new source fix or source GREEN claimed.

## Requested MASTER + CORE contract review before implementation
1. CORE owns server-side canonical terminal ACK format and actual cryptographic signature/verification and durable witness semantics; specify stable controller/event/target/pulses/receipt identity, terminal outcome, duplicate idempotency, and canonical encoding.
2. VERIFY owns firmware strict typed JSON parsing with duplicate-key rejection, full binding to exact pending journal, HTTP status validation, and fail-closed retry/quarantine on missing, conflicting, unverifiable or nonterminal ACK.
3. Preserve existing pending journal and inhibit intake on ambiguous response; never silently clear pending on HTTP errors, nested `ok`, or text substring matches.
4. Any signed terminal ACK requires a genuine server-side signing contract; a local `signature_valid` fixture flag is not cryptographic evidence.
5. Cross-component test-first RED/GREEN, exact-head CI, Arduino builds and independent review before guarded source integration. Do not merge, flash, sign or release unilaterally.

## Release boundary
Production NO-GO: configuration authenticity/rollback RED, independent monotonic witness #43, paid finance #31/#32, physical #34, 150 physical power cuts, 30-device 24h soak, electrical relay/coin edge, reversible migration and permanent signing all unresolved. No customer devices, payments, private keys or firmware flashing used.
