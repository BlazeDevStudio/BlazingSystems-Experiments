# PHX-L-VERIFY 2026-10-26 UTC17 — ESP32 partial Preferences save / false acknowledgment host QA

**NO CODEX · TEST-ONLY · DRAFT / UNMERGED · PRODUCTION NO-GO.**

## Exact authority and CI
- Active control #172; issues #177/#34/#43; current draft #179/#193/#150/#183, all OPEN/DRAFT/UNMERGED. Development comparison-only `5a8fe3efbc4afb9ecf1260c4f09cf6903c26795a`; main `1719b625173ab33cbf90f0729716e43fce8759ed`. No MASTER-approved integration base.
- Prior #193 literal HEAD `838ea4e17fcd17ae8d1cacdf946189979eec249e`; Full [#40364768772](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40364768772) COMPLETED FAILURE (15 success/13 skipped/1 failed validate `121719467689`); native [#40364768829](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40364768829) COMPLETED SUCCESS.
- Validation job: mandatory handover PASS, ESP8266/ESP32 host output tests PASS, two real-source security RED cases **per board** (`untrusted_positive_revision_cannot_enable_coin`, `cold_reboot_older_positive_revision_cannot_enable_coin`); both Arduino compile jobs PASS. This is NOT a green Full CI.

## New bounded execution (distinct from prior generic unchecked-persistence finding)
- ESP32 source: `esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` Git blob `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`, lines 170–176 `saveConfig()` (13 independent unchecked `Preferences.put*()` calls). Lines 289–301 `/save` handler: line 300 calls `saveConfig(); web.send(200,...); delay(700); ESP.restart();` without a success predicate.
- Compiled and ran C++17 (`g++ -std=c++17 -Wall -Wextra -Werror -O0`) with **verbatim source-transcribed** `saveConfig()` and a disposable `Preferences` map test double. Injected exactly one failing `put*()` call for each of 13 keys; other 12 writes succeed. **13/13 injections** produced mixed persisted configuration (12 new values, 1 old value); **1/1 no-failure control** stored all 13 new values. No compile errors.
- Key matrix: `ssid, pass, server, key, id, coinpin, ledpin, relaypin, coinlow, relayhi, ledhi, debounce, groupms`. Every injected case was individually asserted and logged.
- Source-transcribed C++ SHA256 `259f9e09c2435de4ae4878558bce9bae63819ea21d9238f3e9d80a35a74929c9`; result text SHA256 `0fc6387b9787f1d9fbfb87a662ee6585ee5917b446bc7517fd307ca2510ad594`; conversation-local reproducible ZIP SHA256 `4249e34394a588fcc85cdb852accf4862113fed77be9e6e20143933062957122`. It contains source, output, README. **NOT** a GitHub Actions artifact.

## Interpretation and review request
This refines UTC12's generic unchecked persistence ACK risk: the **ESP32 13-key sequential write model** admits a mixed saved configuration after a single failure. The firmware's success/restart continuation is from **source inspection**, not execution of its HTTP handler. The test double does not prove real ESP32 NVS write ordering, crash behavior, or a physically observed failure; hardware behavior remains unverified.

**MASTER/CORE REQUEST_REVIEW (design only):** Require a versioned atomic configuration envelope, strict validation of all GPIO pin capabilities and aliases, integrity-protected durable revision floor, explicit verified write/read-back and error handling, fail-closed relay before any restart or ambiguous state, and an operator recovery procedure. Do not assume 13 independent successful `put*()` calls imply crash atomicity. No firmware fix, merge or flash without guarded review.

**Hard gates:** Real electrical coin relay/pulse edges, 150 isolated physical power cuts, 30-device 24-hour soak, off-device independent monotonic witness #43, reversible migration, production signing, paid finance #31/#32 and hardware #34 all NOT VERIFIED. PRODUCTION NO-GO.
