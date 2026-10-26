# PHX-L-VERIFY 2026-10-26 UTC01 — setup-portal synchronous Wi-Fi verification sampling gap (P0 design QA)

**Status:** source-transcribed host risk reproduced, **not fixed**. Draft #193 stacked on draft #179; neither merged. No Codex, source patch, firmware flashing, hardware, money, signing, migration, or release. **PRODUCTION NO-GO.**

## Exact source and CI authority

- Repository `BlazingSystems/BlazingSystems-Experiments`; QA branch `phoenix/light-verify-target-bound-relay-20261025`, reviewed head `adb6ba2c94ade371e22cbd257e3c81eb041e782b`. ESP8266 source Git blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`; ESP32 blob `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`. Both unchanged by this documentation update.
- `main@9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`; development comparison-only `blazepwifi-v0.6.0-audit-foundation@2c2c1613f4ff5470bd53c23c91767050f936d8c7`. No approved Phoenix integration base; PR #30 closed without merge.
- Prior exact-head [Full #40251619331](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40251619331) **COMPLETED FAILURE** (validate job `121344609447`: 13/15 GPIO cases PASS, two genuine config-authentication / cold-reboot rollback RED **on each board**; handover PASS; ESP8266 and ESP32 Arduino jobs SUCCESS). [Native #40251619324](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40251619324) **COMPLETED SUCCESS**. Full is NOT GREEN; the previous two REDs are not caused by this host QA.

## Distinct P0 candidate — setup portal stalls loop before coin sample

- Both firmware `loop()` functions call `web.handleClient()` **before** `digitalRead(runCoinPin)`. The `/save` handler calls `verifyWifi()` after receiving a POST, before any `applyOutputs()` relay-inhibit step. Both `verifyWifi()` functions disconnect Wi-Fi, `delay(150)`, and may block in a 12,000ms / 250ms retry loop (ESP8266 additionally yields). This is separate from previously documented synchronous `post("poll")` and flash-write sampling windows.
- If relay output was logically ON entering `web.handleClient()`, no output change is commanded during the Wi-Fi verification loop. A transient input edge entirely within the blocking window is not sampled by the later coin-edge detector. Whether the real relay remains electrically energized and an actual acceptor consumes a coin is **unverified**.
- No claim that a 12s delay was measured: it is a source-coded upper-bound timeout, and actual handler duration/transport may differ. No actual HTTP, network, GPIO, LittleFS, customer money, or physical coin acceptance was exercised.

## Executed bounded evidence (host reference only)

- Disposable C++17 manually source-transcribed loop-order model; `g++ -std=c++17 -Wall -Wextra -Werror -O2` compile **PASS**. **12/12 expected scenario observations PASS**, **6 modeled relay-ON missed-edge cases** (150ms, 500ms, 12.15s per board). Two unblocked pulse controls record one event; relay-OFF and held-input controls distinguish non-loss cases. Zero harness failures. This is **not** compiling the Arduino sketches or actual source extraction.
- Local evidence `/mnt/data/phx_verify_utc01/phx_verify_utc01_portal_blocking_evidence.zip` SHA256 `ba79f4f6d4b5ac4cf173ce0cf3993ada4af75520287428a673a79050f0fe93d5`. Harness `fcffed380295ce3c1b8cdacc16bb30203b79d12689acb065bf5b6d70f3c29101`; log `7cedbbed18e5f45814e45d48702a27b303fd60503aa78294e1e8c1179a5c5689`. Conversation-local ZIP, **not** GitHub Actions artifact and not published to repository.

## Decision request / next exact action

MASTER/CORE plus the authorized electrical owner must define a setup-portal admission contract: authenticate the administrative action; inhibit new coin acceptance **before** any blocking Wi-Fi operation only when no pulse or unsettled group is in progress; preserve the pending durable journal and existing event identity; reject/retry instead of cutting power mid-accepted pulse; and rearm only after authenticated config and stable idle. Then VERIFY should add a real-source extracted C++ regression around `web.handleClient()` + `verifyWifi()` for both sketches, capture tracked RED, propose minimal reversible source patch and require exact-head Full/native/Arduino CI plus independent isolated hardware waveform acceptance before integration. No change to CORE financial or APPS code.

P0 #31/#32/#34/#43, independent monotonic witness, 150 physical cuts, 30+ device 24h soak, reversible migration, permanent signing, actual relay/pulse-edge acceptance, and paid ACK protocol all remain **PRODUCTION NO-GO**.
