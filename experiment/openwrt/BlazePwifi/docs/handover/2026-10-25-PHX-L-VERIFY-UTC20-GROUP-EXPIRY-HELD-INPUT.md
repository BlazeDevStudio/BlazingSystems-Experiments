# PHX-L-VERIFY UTC20 — Held-active coin input at group expiry (host QA; NO-GO)

**UTC:** 2026-10-25T20Z. **Branch:** phoenix/light-verify-target-bound-relay-20261025. **Pre-report SHA:** 9cdb4cc3dd494bd2729aec6a9980eeeb378c4138. **NO CODEX; no production source change, merge, flashing, payment, keys or release.**

## Source and authority

Control plane #172, issue #177, P0 hardware #34 and witness #43 reviewed; parent #179, child #193, separate #150/#183 remain unmerged. Main `9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`; comparison-only development `ad662ddfffd483864daaf5bca3f16368877a2113`. Both source blobs: ESP8266 `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`, ESP32 `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`.

## Executed bounded test

Both sketches' `loop()` include `if(pendingPulses && !pendingReady && millis()-lastEdge>runPulseGroupMs)` followed by `pendingReady=true; lastSend=0; applyOutputs();` without checking the currently active input level. `applyOutputs()` requires `!pendingReady` for relay ON. A held active input can therefore coincide with a relay ON→OFF transition at timeout, even without a new electrical edge. This is a **source-logic and timing finding**, not a demonstrated lost coin: long-held input may represent a stuck line; physical acceptance policy and actual acceptor waveform must be established before choosing a mitigation.

C++17 **manually source-transcribed** host fixture modeled both boards' group expiry and output predicate. Compiled `g++ -std=c++17 -O2 -Wall -Wextra -Werror -pedantic` and ran: **20/20 checks matched**, **6 held-input ON→OFF transitions**, zero harness failures. Controls: pre-expiry, exact boundary, idle, no pending, already ready, controller disabled, uint32 timer wraparound. **Not** a full extracted Arduino `loop()` build, real GPIO, real relay, actual coin slot, flash durability or financial credit.

Local evidence: `group_timeout.cpp` SHA256 `3d329e8d4df40474d26064185e0c1f6cc93c2fbe55ea40c6d59a9b92153d56a7`; `results.txt` SHA256 `51909755f9983207e6f95e2f61fa782cd2a02d502348c5d62fdf6ab609ac16a8`; evidence ZIP SHA256 `7c6593349863d8d81fe64b0be48f8a8b4f28cb57898284cb1139482dcea7b57e` (conversation-local only).

## Exact-head CI and required decision

Pre-report #193 HEAD `9cdb4cc3dd494bd2729aec6a9980eeeb378c4138`: Full [#40228334969](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40228334969) **COMPLETED FAILURE**, validate job `121274528655`: 13 PASS + 2 existing config-auth/cold-reboot RED per board, both actual ESP Arduino compile jobs SUCCESS, 13 downstream skips; Native [#40228334959](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40228334959) **COMPLETED SUCCESS**. Neither demonstrates a group-timeout correction.

**MASTER/CORE review:** Determine whether a sustained active coin line should delay group expiry, whether a bounded maximum-high timeout and stuck-input quarantine is required, and how to preserve already journaled pulses while preventing new intake. Require owner-approved noncustomer oscilloscope/logic-analyzer waveform and relay/acceptor-power telemetry before accepting electrical behavior. Test long pulses, stuck line, debounce, group timeout, reset and interrupted power with recorded monotonic timestamps. No speculative firmware patch until policy/bench decision.

**PRODUCTION NO-GO:** #31/#32 financial authority, #43 independent monotonic witness, #34 physical relay/pulse/150 cuts/30-device 24h soak, reversible migration, permanent signing and release approval all outstanding.
