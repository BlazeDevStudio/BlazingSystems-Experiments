# PHX-L-VERIFY UTC14 — relay inhibition versus pulse journal admission (REVIEW REQUIRED)

- **Date:** 2026-10-25T14Z (UTC); **role:** PHX-L-VERIFY; **NO CODEX / NO PRODUCTION**.
- **Repository/branch:** `BlazingSystems/BlazingSystems-Experiments`, stacked DRAFT PR #193 on DRAFT #179; literal source/docs pre-report HEAD `dbe99f9d0396a9549a3c7daeb3017cef62c4d3e9`. Development comparison-only `ad662ddfffd483864daaf5bca3f16368877a2113`; default main `9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`. No approved integration target.
- **Actual source Git blobs:** ESP8266 `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`; ESP32 `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`.
- **Previous literal exact-head CI:** [Full #40199621331](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40199621331) **COMPLETED FAILURE** (validate job `121188981318`, both board builds success; two existing config-auth/reboot RED per board), [Native #40199621325](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40199621325) **COMPLETED SUCCESS**. New docs-head CI must be classified separately.

## New independent executed QA

Both actual sketch `applyOutputs()` predicates include `controllerEnabled && coinEnabled` and relay-enabled selection; however, the coin-edge journal path inside `loop()` requires `insertMode && fsReady && activeTarget.length() && !pendingReady && active && !lastCoin && debounce`, **without checking controllerEnabled, coinEnabled or relayEnabled**.

Executed **strict C++17 -Wall -Wextra -Werror -pedantic -O2** host harness containing manually source-transcribed complete ESP8266 and ESP32 `loop()` bodies, renamed `loop8266`/`loop32`, with host String/WiFi/GPIO/time/journal stubs and a matching simplified `applyOutputs` relay predicate. **20/20 expected trace cases PASS** (10 each board, zero harness errors). Each board journaled an injected new active edge with relay OFF when `controllerEnabled=false`, `coinEnabled=false`, or `relayEnabled=false`. Normal authorized edge journaled. Controls for insertMode off, flash unavailable, absent target, pendingReady, no edge, debounce not elapsed showed no journal request.

- Harness SHA256: `b967d7865f35208a1bf5eb8fa4d08dc3e75f90ec32837826b1a3ada97a5cb18e`.
- Results SHA256: `fd7017307668444205f97690fbbff9684de7481675a1ed1dd773375cd7136d05`.
- Local reproducible evidence archive: `phx_verify_utc14_edge_admission.zip` (conversation attachment, **not** committed or a release artifact).

**Classification:** source-transcribed host-model **admission-policy mismatch candidate**, not a direct Arduino binary execution, actual LittleFS write, electrical relay test, paid CGI request/credit, physical pulse, or proof of production exploit. A pulse already in flight after relay shutdown may represent real money; do **not** silently discard it. The relayEnabled=false configuration may deliberately support externally powered acceptors. Review should distinguish *pre-disable already-accepted pulse* from *new unauthorized intake after disable*.

## MASTER/CORE decision request (no source change)

1. Define whether an edge arriving after controller/coin disable can be journaled only if a prior **authenticated, target-bound authorization window** was active when the physical pulse began. Distinguish ongoing pulse completion from fresh edge.
2. Define fail-safe response for an unexpected edge while relay OFF: preserve evidence/reconcile safely, never invent or silently drop a customer payment; do not immediately treat it as a new authorized payment.
3. CORE owns financial authority/ACK semantics; VERIFY may implement a bounded test-first firmware change only after reviewed policy. Keep existing config-auth/reboot REDs and ACK-schema RED unresolved.
4. Require actual source-linked tests, both Arduino compilers, independent artifacts, and physical relay/pulse edge testing before acceptance.

**No Codex, no source modification, no merge, no flash, no customer operation, no signing, no release. PRODUCTION NO-GO.**
