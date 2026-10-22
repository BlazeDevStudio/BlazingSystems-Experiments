# COIN-20261022-BOUNDED — ESP pending-payment record corruption safety

**Status:** bounded source fix, synthetic native ASan test PASS. **Priority:** P1 hardware controller robustness, with P0 implications for coin acknowledgment availability. **Not hardware acceptance.**

## Scope and root cause

The exact same `esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h` library is consumed by both `esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` and `esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` when reading persistent pending coin/event sequence structures and prior legacy records.

Previously `bp_pending_sequence_hex_token(const char *s, size_t min_len, size_t max_len)` called unbounded `strlen(s)`, despite accepting tokens from binary flash storage in `nonce[17]` and `target[33]`. A complete record with coherent FNV-1a checksum but omitted NUL in both arrays could make `strlen` read past the end of the allocated `BpPendingSequence`, before rejection. FNV checksum is an accidental corruption check, **not a signature**; do not infer attacker authentication.

## Actual reproducible evidence

- Isolated branch `fix/coin-20261022-pending-token-bounds` from v0.6 audit base `72987a376d66b2a9027a0685e9681fc5cd45b674`.
- Synthetic C test `tests/v060_vendo_pending_bounds.c` commit `8b1a8fb2bba9afe600b5bb7e58ca5c8f2b173209` constructs a wholly fictional pending coin record with coherent checksum but missing NUL across both fixed token fields. Allocates the object at a heap boundary and invokes the **real** header `bp_pending_sequence_valid()` under AddressSanitizer.
- Test integrated in existing `tests/v060_vendo_pending_sequence.sh` at `a34582dc2ea78981cf2013a90e1a53b5a6d0cd3f`, plus targeted workflow `.github/workflows/blazepwifi-v060-pending-bounds.yml` at `a84f1bfb345c24af8e5cc8c407ffa3ec39d88a9c`.
- [RED Actions #39742533424](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39742533424) exact pre-fix `a84f1bfb345c24af8e5cc8c407ffa3ec39d88a9c` **FAILED as expected**, real ASan `heap-buffer-overflow`, stack trace `strlen` → `bp_pending_sequence_hex_token` → `bp_pending_sequence_valid`; exit 1.
- Fix `esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h` commit `cec012e96b0a91cfe6f529bbdca71ab22e348594`: scan at most `max_len + 1` bytes for required NUL, enforce upper bound 32, then validate each hex character. No struct layout, wire format, amount, pulse, ACK, cryptography, stored migration or GPIO changed.
- [GREEN Actions #39742761893](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39742761893) at exact `cec012e96b0a91cfe6f529bbdca71ab22e348594` **COMPLETED SUCCESS**: existing reserve/commit pending sequence tests PASS, corrupted record rejected within bounds under ASan.

## Safety contract and remaining tests

The helper now reads only within the known `nonce[17]` and `target[33]` record field limits (16/32 hex chars plus NUL). Bad records fail closed; valid same-wire-format pending reservations and commits retain their behavior. A malformed stored record was never a valid paid acknowledgment, so refusing it is safer than attempting recovery by guessing a nonce.

**Not proven:** hardware flash behavior, real torn-write probabilities, arbitrary overwrite/replay protection, untrusted firmware signature, exact-once server-paid transaction or independent protected witness. Existing account/rental P0 #31/#32/#43/#34 and v0.6 production gates remain open. Firmware can only be installed on isolated owner test hardware after an appropriately reviewed, signed/verified release and actual brownout/coin/ACK tests.

**Next exact action:** check exact PR-merge-tree Full firmware compilation for ESP8266 and ESP32, the existing `v060_vendo_pending_sequence.sh` under supported compiler/toolchains, and follow up on controller persistent ACK semantics. Do not merge if source changed unexpectedly or any mandatory CI fails; do not deploy to live machines.
