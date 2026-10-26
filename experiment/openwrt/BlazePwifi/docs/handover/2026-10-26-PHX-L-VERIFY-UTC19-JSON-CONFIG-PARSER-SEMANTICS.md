# PHX-L-VERIFY — 2026-10-26 UTC19 — valid JSON configuration parser semantics (HOST ONLY)

**BLAZE-COMMS/1 · NO CODEX · DRAFT/UNMERGED · PRODUCTION NO-GO.**

## Source and authority
Read control plane #172, #177, #34, #43 and four canonical handover/policy files. Main `1719b625173ab33cbf90f0729716e43fce8759ed`; development `1890e522843d262c33a5109dcea11768896c2e5f` comparison-only, NOT approved integration base. QA parent #179 `e5a9781ea5234b09501d5356cf966f9237ac8172`; child #193 prior head `aebef4ee5afddb165e5a73475591f5bca73365e2`; #150/#183 also OPEN DRAFT UNMERGED. #30/#173 closed unmerged.

Actual sketch Git blobs: ESP8266 `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`, ESP32 `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`. Their `jsonInt` searches for first literal `"key":` substring, not root JSON member, and `applyRemoteConfig` defaults absent `enabled`/`coin_enabled` to **1**.

## Previous exact-head CI
Full [#40382489181](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40382489181) **COMPLETED FAILURE** at `aebef4ee5afddb165e5a73475591f5bca73365e2`: 15 success, 13 skipped, failed validate job `121782808070`. Handover, prior poll/target-bound tests and both Arduino compilers PASS; each board 15 GPIO/config checks with **2 existing REDs**: `untrusted_positive_revision_cannot_enable_coin` and `cold_reboot_older_positive_revision_cannot_enable_coin`. Native [#40382489141](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40382489141) **SUCCESS**. No Full GREEN.

## One bounded independently executed QA
Source-transcribed both real `jsonInt` functions into disposable C++17 Arduino-String host shim, compiled strict `-Wall -Wextra -Werror -pedantic -fsanitize=address,undefined`. Python `json.loads` independently verified **10/10 valid JSON fixtures** and their root member values. C++ **20/20 expected parser assertions PASS**; **14/20** semantic mismatches versus JSON root-member interpretation across two boards. Valid `{"config_revision":9,"enabled" :0}` returns fallback **enabled=1**, despite root enabled=0; newline/tab before colon likewise. Valid `{"metadata":{"enabled":1},"config_revision":9,"enabled":0}` returns nested 1 instead of root 0. Same for `coin_enabled`. Valid `"config_revision" :9` falls back to 0 (fail-closed in exercised case); earlier nested revision 11 overrides root revision 9. Compact controls PASS.

**Conditional configuration safety defect**, distinct from but compounding existing unauthenticated revision REDs. NOT proof current CGI emits these JSON shapes or attacker controls responses. Arduino binary, authenticated CGI, physical relay/coin, EEPROM/NVS, paid state and power cuts NOT tested. Initial host compile failed only because disposable shim lacked left-hand `operator+`; fixed shim, not transcribed parser; full rerun passed. Do not classify harness compile as firmware RED.

Local evidence ZIP `phx_verify_utc19_json_parser_evidence.zip` SHA256 `b2cfef48e4b33c7479b186c572f1b4cd8f95fce10dd6e7ac3586a3f905a191a2` (conversation-local, NOT uploaded to GitHub). C++ SHA256 `3c879b02838be694d5e3882e2c3b8fcc8bf04cfda6e6fe4793ac8583640c5b21`; Python `3ee65495df4ed1e7aca07b9b676d30e8dc89af6164ade9789d4a56eb7c682ea0`. ZIP CRC verified.

## Decision and NEXT EXACT ACTION
Source/workflows unchanged. MASTER/CORE should verify server response shape and authenticated root-schema/witness contract, then authorize a **test-first real-sketch parser regression** for whitespace, nesting, duplicate/unknown keys, invalid types and default-deny. Do not silently change protocol or permit fallback enable. Any firmware change requires source CI and review; physical acceptance remains independent. Docs-only rollback is reverting this checkpoint on draft branch. No merging, flashing, customer hardware, paid records, keys, signing or release. #31/#32/#34/#43, 150 physical cuts, 30-device 24h soak, reversible migration and permanent signer remain PRODUCTION NO-GO.
