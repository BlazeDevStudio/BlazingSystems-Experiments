# PHX-L-VERIFY UTC19 — Live coin-input polarity flip can synthesize a software edge (P0 QA; no production)

**Time:** 2026-10-25T19Z / 2026-10-26 Manila. **Scope:** draft #193 stacked on unmerged draft #179; no approved Phoenix integration base. **NO CODEX / NO MERGE / NO FLASH / NO FINANCIAL ACTIVITY.**

## Authority and source pins

- Live control plane [#172](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/172), pulse risk [#177](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/177), physical gate [#34](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/34), independent witness [#43](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/43); PR #179/#193/#150/#183, four canonical handover/policy files reviewed.
- Default `main=9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`; comparison-only development `blazepwifi-v0.6.0-audit-foundation=ad662ddfffd483864daaf5bca3f16368877a2113`; pre-report #193 HEAD `f4fd66756f673ae3e6f818fd63f46197c8ddca24`.
- ESP8266 sketch Git blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`; ESP32 sketch `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`.

## New independent finding

Both sketches' actual `applyRemoteConfig()` guard rejects **relay/LED** polarity changes, GPIO rebinds and aliases, but does **not** reject a live `coin_active_low` change. A positive `config_revision` updates `runCoinActiveLow` without resetting `lastCoin`, re-arming the physical input or requiring idle confirmation. Both `loop()` functions then compute `active=runCoinActiveLow?!raw:raw` and accept an `active && !lastCoin` edge. Thus, an unchanged idle HIGH with active-low→active-high, or unchanged idle LOW with active-high→active-low, can request a coin journal entry without an electrical transition, when the other software admission conditions are permissive. This is **separate** from prior unauthenticated revision and disabled-relay journaling reports.

## Executed host QA

- Strict C++17 manually source-transcribed `applyRemoteConfig` functions for each board; Arduino String/GPIO/relay, clock and journal-edge sampling modeled. Compiler `g++ -std=c++17 -O2 -Wall -Wextra -Werror -pedantic` **SUCCESS**.
- **14/14 expected observations matched; 4 new phantom-edge/relay-eligible states** (two polarity directions per board); **2 previously known disabled-controller/relay-OFF journal requests** reproduced as consistency controls; eight non-phantom controls; zero harness failures.
- Independently inspected both exact Git blobs: the remote guard lacks coin-polarity comparison, while both loop edge gates use `runCoinActiveLow` and `!lastCoin`.
- Harness SHA256 `feddb94789d38b7ba9b039d0b1cd7aa2113631e7c56988c57533318284b70429`; results SHA256 `2ac9a3ce3fda13967da1d719dbd8eae27212c20f356536116ce1c7d0b0a2d73a`; local ZIP SHA256 `aa950daff34508cdfadc5702c2a619e2c4757df5861c0e08c4cb78d609fb7520` (not uploaded as a GitHub artifact).
- **Evidence boundary:** source-transcribed host simulation, not Arduino `loop()` execution, physical GPIO, real coin acceptor, flash journal persistence, actual server credit, signature validation, or hardware power interruption.

## Exact-head CI and decision

Pre-report #193 HEAD `f4fd66756f673ae3e6f818fd63f46197c8ddca24`: [Full #40223984614](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40223984614) **COMPLETED FAILURE**: 15 success, 1 validate failure, 13 skipped; validate `121261596961` has 13 existing PASS + 2 config-auth/cold-reboot RED per board. Both ESP8266 and ESP32 Arduino build jobs **SUCCESS**. [Native #40223984705](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40223984705) **COMPLETED SUCCESS**. These do **not** validate a correction for this finding.

**MASTER/CORE review requested:** Disallow live coin-input polarity change until authenticated board-specific reprovisioning with policy epoch, forced intake OFF, stable idle observation and deliberate edge-state re-arm. Preserve all already-journaled events; do not discard customer money on uncertainty. Add extracted-source RED then guarded GREEN on both boards only after interface decision, plus noncustomer electrical bench validation. Keep PR #193 DRAFT and stacked; PR #30 remains CLOSED UNMERGED; no integration-base inference.

**PRODUCTION NO-GO:** #31/#32 finance, #43 independent monotonic witness, #34 physical relay/pulse and 150 power cuts/30 real clients 24h, reversible migration, permanent signing and owner release authorization unverified. No Codex, keys, customer devices, flashing, payment records, merge or release.
