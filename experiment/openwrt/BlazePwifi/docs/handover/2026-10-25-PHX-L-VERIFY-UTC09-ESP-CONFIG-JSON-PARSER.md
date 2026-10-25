# PHX-L-VERIFY UTC09 — ESP configuration JSON integer parser ambiguity QA

Status: **SOURCE-TRANSCRIBED HOST QA EXECUTED / REVIEW_REQUIRED / NO CODEX / PRODUCTION NO-GO**. Date 2026-10-25T09Z. Owner: PHX-L-VERIFY. No firmware, finance, signing, CI workflow, merge or hardware changes.

## Exact baseline and independent CI classification

DRAFT child PR #193 on unmerged DRAFT #179, initial literal PR HEAD `9badbf9b2d724e21a9ceb7b20f6f938b516db377`; source Git blobs ESP8266 `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`, ESP32 `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`. Previous documentation-head Full #40178347880: **FAILED**, 15 successful, one failed validate job `121124142031`, 13 skipped; both ESP Arduino compiler jobs SUCCESS. Validation log confirms **13 PASS / 2 existing auth/reboot RED per board**, mandatory handover PASS. Native #40178347859 SUCCESS. These existing security REDs remain unresolved and were NOT retested/fixed by this audit.

## New bounded executed fixture

Manually transcribed the complete real `jsonInt(const String&,const String&,int)` function body separately from each exact Git sketch, normalizing line endings, into a C++17 host shim providing Arduino `String` operations `indexOf`, `length`, `substring`, `toInt`, and `isDigit`. Built both with `g++ -std=c++17 -Wall -Wextra -Werror -pedantic`; compilation and execution succeeded. No network, actual board, relay, signed receipt, production credentials, or money involved.

**12 cases per board; 5 strict expectations matched, 7 strict expectations not met; 24 executed comparisons total.** Expected-strict means proposed defensive parser semantics, NOT a currently approved protocol. Normal compact JSON, ASCII-space-after-colon, missing key, negative integer, and empty-value fallback matched. Unexpected behavior on **both** boards:
- Valid JSON whitespace before colon: returns default rather than integer.
- Valid JSON tab or newline after colon: returns default rather than integer.
- Nested object containing an earlier `config_revision`: returns nested value (99) instead of top-level (7).
- Duplicate `config_revision` keys: accepts first value (9) rather than rejecting ambiguity.
- Invalid decimal `7.5`: accepts integer prefix 7 rather than rejecting.
- Invalid suffix `7junk`: accepts integer prefix 7 rather than rejecting.

This is an **actual-function source-transcribed host model**. It does not demonstrate remote exploitation, server emission of these formats, acceptance of a signed response, or physical relay operation. Existing config replies are not independently authenticated; these parser ambiguities could additionally complicate a future signed-receipt canonicalization contract.

## Required MASTER review (no source correction yet)

Define a single authenticated, typed, unambiguous configuration envelope and parse contract for both boards. Require exactly one top-level integer `config_revision`, reject duplicate keys, nested-shadow matches, fractional/suffixed tokens and invalid types, define legal whitespace, bounded length, identity/target/epoch/digest binding, and verify receipt before any configuration or GPIO mutation. Use fail-closed relay handling on parse/auth/persistence uncertainty. An isolated ArduinoJson/other parser change must NOT be assumed safe without flash/RAM budget, compiler checks and tests. Independent durable revision highwater and #43 witness remain separate.

**Evidence limitations:** The local executable/source fixture is downloadable from the QA conversation, not stored as a GitHub CI artifact. No GitHub CI success claimed for this new audit. This report documents independent local execution and invites test-first review only.

## Hard gates

No PR merged; development branch comparison-only; #30 closed unmerged. No electrical coin acceptor/relay edge, flash interruption, 150 physical cuts, 30-device 24-hour soak, off-device monotonic witness #43, migration, paid finance #31/#32, permanent signing or release acceptance. **PRODUCTION NO-GO.**
