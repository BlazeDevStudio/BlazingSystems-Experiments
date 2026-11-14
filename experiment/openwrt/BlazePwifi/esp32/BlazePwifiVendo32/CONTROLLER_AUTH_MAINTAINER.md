# ControllerAuthV1Lab — maintainer and integration boundary

**Scope:** PHX-HARDWARE / [draft PR #254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/254) (stacked on fail-closed [PR #239](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/239)). This is **LAB ONLY** and is not wired into the Vendo .ino application intake path. Neither a valid HMAC nor a digest match admits coins or energizes a relay.

## Code reading order

1. `hex64` rejects missing, non-lowercase or non-64-character digest strings (wire validation here is bounded; the upstream string pointer must be valid).
2. `equal_fixed` compares exactly the requested byte length without a value-dependent early return.
3. `encode_sha256_hex` renders exactly 32 bytes in canonical lowercase hexadecimal, shared by both SHA256 and HMAC validation so decoding/debugging is not maintained twice.
4. `matches_policy_digest` verifies **the original serialized policy bytes**, including whitespace and field order; callers must not reserialize JSON before hashing.
5. `verify_mac` accepts an already-canonicalized message and checks HMAC-SHA256 against the supplied lowercase signature. It does **not** parse, authenticate or bind the fields itself.
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
