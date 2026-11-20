# ControllerAuthV1Lab — maintainer and integration boundary

**Scope:** PHX-HARDWARE / [draft PR #254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/254) (stacked on fail-closed [PR #239](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/239)). This is **LAB ONLY** and is not wired into the Vendo .ino application intake path. Neither a valid HMAC nor a digest match admits coins or energizes a relay.

## Mbed TLS compatibility boundary

`ControllerAuthV1Lab.h` intentionally supports Mbed TLS major versions 2 and 3 only because it calls the legacy `mbedtls_sha256_*` API. It now emits a compile-time error for an unknown major or Mbed TLS 4 before including the legacy SHA-256 header. The current ESP32 Arduino core 4.0.0 path uses Mbed TLS 4, so this lab header must not be integrated there; a PSA Crypto adapter is a separate, reviewed hardware change. The focused native workflow currently compiles against Ubuntu `libmbedtls-dev` 2.28.8, which is host-header evidence, not an ESP32 core compatibility build.

## Code reading order

1. `hex64(p, length)` validates an exact 64-byte lowercase-hex span without scanning for a terminator. The caller must provide at least `length` readable bytes from its strict parser.
2. `equal_fixed` compares exactly the requested byte length without a value-dependent early return.
3. `encode_sha256_hex` renders exactly 32 bytes in canonical lowercase hexadecimal, shared by both SHA256 and HMAC validation so decoding/debugging is not maintained twice.
4. `matches_policy_digest` verifies **the original serialized policy bytes**, including whitespace and field order; it receives both the digest pointer and exact digest length. Callers must not reserialize JSON before hashing.
5. `verify_mac` accepts an already-canonicalized message pointer plus exact byte length, and a signature pointer plus exact length. It does not call `strlen`, parse, authenticate or bind the fields itself.
6. `may_admit_coin_even_if_mac_valid` and `may_energize_relay_even_if_mac_valid` must remain `false`.

## Before integrating into a live controller

A strict, duplicate-rejecting parser must establish exact action, controller/device ID, outstanding request nonce, full policy bytes, signed target/window/expiry values and locally accepted revision. The existing [CORE PR #252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/252) `config_auth` v1 envelope is a **DENY-only** development contract; shared rollbackable keys do not prove independently protected cold-start freshness. Separately proposed [PR #283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) uses `response_sig` logic on another baseline: do not merge these formats or sketches without a verified producer/consumer wire-contract comparison and CORE + QA review.

Missing: protected revision witness, stable key custody, strict JSON integration, ESP8266 parity, real device provisioning, durable coin ACK/replay confirmation, electrical tests, physical relay-polarity acceptance and [#34](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/34) power-cut/soak evidence. **Production / money / flash = NO-GO.** Never log raw keys or customer state for troubleshooting.

## Reproduce the existing software-only header test

From the repository root on Ubuntu with `libmbedtls-dev` installed:

```sh
g++ -std=c++17 -Wall -Wextra -Werror -O2 \
  experiment/openwrt/BlazePwifi/tests/v060_controller_auth_header_native.cpp \
  -o /tmp/phx-hw-auth-test -lmbedtls -lmbedcrypto -lmbedx509
/tmp/phx-hw-auth-test
```

The [focused GitHub workflow](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/phoenix/hardware-core252-deny-consumer-20261030/.github/workflows/phx-hw-controller-auth-focused.yml) pins its checkout to the PR head SHA and also asserts Phase A relay/coin denial. A passing host test is not an Arduino build, hardware flash or customer field acceptance.

**Cleanup intent:** remove only the duplicate digest-to-hex loops and their stdio dependency, preserving identical lowercase output bytes, fixed-length comparisons and fail-closed functions. Independent tests and upstream interface changes belong to their owners.

## Exact-head verification record — 2026-11-17

The non-actuating helper cleanup from source commit `3692ddf889470da8a002e9a16bf0ac2f37f1a9d0` is now validated on its documentation-only successor `16de37a7f3a86e1ec7dbc424b6b2f43227421eee`.

- The compare from `3692ddf` to `16de37a` contains only the three canonical handover documents (`PROJECT_HANDOVER.md`, `CURRENT_STATE.md`, `CHANGE_LEDGER.md`); the helper, test and application source are unchanged.
- Focused native run [#43633345474](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633345474), job `132564650975`, completed successfully at exact SHA `16de37a`. It compiled the actual header against mbedTLS and passed 5/5 synthetic checks: signed response still denied, tampered signature denied, wrong device denied, wrong nonce denied, and invalid signature/empty key denied. Phase A deny guard passed.
- Full BlazePwifi run [#43633345561](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633345561) completed successfully at the same exact SHA. Validation job `132564700241`, ESP32 `132564700182`, ESP8266 `132564700146`, Android, returned target builds, v0.4 simulation jobs and update-bundle job all succeeded.
- The earlier full run [#43632185933](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43632185933) at source-only SHA `3692ddf` failed the mandatory handover freshness gate. That failure remains historical; the docs-only successor and the new exact-head Full run are the successful correction.

**Classification:** this isolated helper and its synthetic native test are **CI VERIFIED** at `16de37a`. They remain LAB ONLY and are not wired into application coin admission. Production signing, publish/release jobs were skipped; no key was provisioned, no GPIO/relay/coin path changed, and no physical hardware acceptance is claimed. Phase A remains DENY.

## Length-aware parser span hardening — 2026-11-20

The native lab exposed an out-of-bounds read when `hex64(const char *)` inspected byte 65 of a parser-owned 64-byte non-NUL-terminated digest span. The helper now requires explicit lengths for digest and signature spans and for canonical HMAC input. It validates exactly 64 digest/signature bytes and hashes/HMACs exactly the supplied byte counts; no terminator scan or `strlen` is used on parser-owned spans. The focused workflow compiles with AddressSanitizer and UndefinedBehaviorSanitizer so the regression remains visible.

This is a lab-only helper API change. It does not change CORE's producer contract, wire format, application intake, coin admission, GPIO or relay behavior. Both admission helpers remain hard-coded false.
