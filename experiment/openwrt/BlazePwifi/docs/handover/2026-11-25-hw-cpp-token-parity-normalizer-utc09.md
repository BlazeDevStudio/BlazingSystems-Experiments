# PHX-HARDWARE handover — C++ token-aware board parity normalizer

**Updated:** 2026-11-25T09:40Z  
**Role:** PHX-HARDWARE  
**Repository:** \`BlazeDevStudio/BlazingSystems-Experiments\`  
**Control plane:** [Issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Hardware task:** [Issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [Issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/hw-json-array-primitive-guard-20261124-utc00\`  
**Base PR #347:** \`960184670379f01e20f0e7e8bc23b3e5eedacd3f\`  
**Source/test SHA:** \`9b20d0a6e520d78423250636b3ea0fe983b35294\`

## Selected task

Correct a confirmed false-negative and false-positive in the Hardware-owned ESP8266/ESP32 bounded-HTTP source-parity test. The prior normalizer removed all whitespace with \`re.sub(r"\\s+", "", ...)\`, which also removed whitespace inside C++ string/character/raw-string literals and merged adjacent identifier tokens. It also treated comment-only wording differences as source drift.

This is a host-test correctness and maintainability change only. It does not change controller runtime behavior.

## Test-first evidence

The test-only commit \`fec9453e203f3ddc74adb8cddd64075b4225a6be\` added mutation cases for:

- string-literal whitespace significance;
- C++ identifier/token boundary significance;
- comment-only differences being ignored.

Expected RED was reproduced on the exact test-only SHA:

- Quarantine [#45586353425](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45586353425), job \`139108835941\`: FAIL at \`string-literal whitespace must remain significant\`.
- Relay [#45586353358](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45586353358), job \`139108836723\`: FAIL at the same assertion.

The failure demonstrates that the prior whitespace-strip normalizer collapsed distinct C++ literal contents.

## Source correction

Commit [\`9b20d0a6\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9b20d0a6e520d78423250636b3ea0fe983b35294) replaces whitespace deletion with a bounded C++ token scanner:

- whitespace between tokens is ignored;
- identifier and punctuation token boundaries remain distinct;
- ordinary, escaped, character and raw-string literal payloads are preserved;
- line and block comments are ignored for runtime-source parity;
- malformed/unterminated literals and block comments fail closed.

The normalizer contract now covers eight checks: formatting equivalence, operator drift, string-literal whitespace, identifier-token boundaries, comment-only differences, raw strings, escaped strings and character literals.

## Exact-source CI evidence

All results below are on source/test SHA \`9b20d0a6e520d78423250636b3ea0fe983b35294\`.

- Quarantine [#45587094891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45587094891), job \`139111358382\`: **PASS**. Log markers: \`BOUNDED_HTTP_RESPONSE_TOKEN_NORMALIZER_PASS 8/8\`, \`BOUNDED_HTTP_RESPONSE_BOARD_PARITY_PASS\`, and \`BOUNDED_HTTP_RESPONSE_BOARD_PARITY_MUTATIONS_PASS 10/10\`.
- Relay [#45587106298](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45587106298), jobs \`139111393546\` and \`139111394133\`: **PASS**. Exact bounded-response check and board-parity mutation checks passed.
- Full BlazePwifi [#45587106766](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45587106766), validation job \`139111540259\`: **FAIL** at inherited \`Missing poll signature check\` in the ESP8266 sketch. All 14 firmware/platform build jobs plus Android completed successfully; dependent simulations, candidate, signing and publication stages were skipped.

The Full validation failure is not fixed here: the authenticated register/poll response contract belongs to PHX-CORE and independent assertion reconciliation belongs to PHX-QA. No comment/string sentinel or fake signature was added to make the gate pass.

## Scope and preservation

Only \`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/bounded_http_response_lab.py\` changed in the source/test correction.

No ESP8266/ESP32 production \`.ino\`, CGI producer, shared API, relay actuation, coin journal, financial state, signer, witness, migration, Release workflow or COE destination was changed.

The separate deny-only pre-poll mitigation remains in Hardware PR #340, a child of #283. This task does not retarget or alter #239, #254, #283, #340, #347, #348 or Master PR #288.

## Evidence classification and remaining blockers

- C++ parity-normalizer correction: **CI VERIFIED**.
- Board firmware behavior in host-extracted labs: **SIMULATED / CI VERIFIED ONLY**.
- Local full repository suite: **NOT RUN**.
- Physical coin acceptor, relay contacts, electrical recovery and LittleFS power-loss: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30-device / 24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release acceptance: **NOT ACCEPTED / PENDING**.
- Private \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\`: unavailable through the currently exposed connected sources; no older registry snapshot was substituted.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

## Next exact action

PHX-MASTER refreshes the #349 source/test and docs pins in its owner matrix. PHX-CORE publishes the approved authenticated register/poll response contract and golden vectors. PHX-QA independently reconciles the Full validation assertion without weakening deny-default. PHX-HARDWARE continues only after revalidating the live branch heads and selecting the next unblocked Hardware-owned task.

No flash/reset, physical power interruption, live money, production migration, secret provisioning, merge, tag, publication or deployment occurred.
