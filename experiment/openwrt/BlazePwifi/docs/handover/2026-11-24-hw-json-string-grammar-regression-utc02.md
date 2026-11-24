# PHX-HARDWARE UTC02 — JSON string grammar regression coverage

**Observed:** 2026-11-24 UTC02  
**Role:** PHX-HARDWARE  
**Task:** #177 / #266 / #349  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent #347 exact base:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test HEAD:** `7c14c2600fbf4c10e591286a2eca786d5cf5e548`  
**PR:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349), OPEN / DRAFT / UNMERGED

## Work completed

Extended the Hardware-owned source-extracted JSON parser lab to cover JSON string grammar on both ESP8266 and ESP32. Production parser code was not changed in this follow-up; the parser remains the implementation introduced by `e3aa052a973edd78a2db00e7278f44adf6226cec`.

Added one valid escaped-string case covering quote, backslash, backspace, form feed, newline, carriage return, tab and a four-hex Unicode escape. Added six malformed strings: unsupported escape, short Unicode escape, non-hex Unicode escape, unescaped control character, unterminated string and dangling escape.

The lab now reports **6/6 valid and 12/12 malformed composite/string cases** on each board. It also injects three string-parser fail-open mutations (accept raw control, accept unsupported escape, accept non-hex Unicode escape) and rejects all three per board. Existing array-primitive, array-separator and object-separator mutations remain.

## Exact commits and test harness correction

- Parser implementation in both sketches: `e3aa052a973edd78a2db00e7278f44adf6226cec`.
- First string-regression addition: `efb69bb84ec4a185a169ad24c45a6626ee36b024`.
- Exact-head CI exposed a test-only unsupported-escape mutation-anchor mismatch in Quarantine run [#45310487197](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45310487197), job `138164689604`. The raw-control mutation passed; the harness then stopped because its over-escaped text anchor did not match the extracted production branch. This was not a firmware parser failure.
- The mutation anchor now locates the single unsupported-escape branch structurally; marker counts were corrected in `7c14c2600fbf4c10e591286a2eca786d5cf5e548`. No test failure was hidden or relabelled.

## Exact CI evidence at source/test HEAD `7c14c2600fbf4c10e591286a2eca786d5cf5e548`

- Quarantine [run #45310725411](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45310725411), job `138165490856`: **PASS**. Both boards report 6/6 valid and 12/12 malformed; array/object separator and primitive-terminator mutations rejected; all three string fail-open mutations rejected. Existing source quarantine scenarios 36/36 per board and coin-pulse capture 17/17 per board pass. Logs retain `SIMULATED_ONLY=1` and physical acceptance flags at zero.
- Relay [run #45310725456](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45310725456), jobs `138165491208` and `138165491432`: **PASS**. Both board parser suites report 6/6 valid and 12/12 malformed; all six parser mutation cases per board are rejected. Coin-pulse capture 17/17 per board; relay/output and boot-polarity host labs pass. Logs retain physical acceptance flags at zero.
- Full BlazePwifi [run #45310725430](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45310725430): validation job `138165606759` **FAILED** at inherited `Missing poll signature check` in `tests/controllers.sh`. Firmware target jobs were still completing at the time this handover was prepared; no Full pass or downstream release acceptance is claimed. The assertion remains QA-owned and its producer/consumer contract remains CORE-owned.

## Master coordination / stale parent observation

Master's UTC01 checkpoint [comment](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7119457152) describes the **#347 parent** primitive scanner as missing the closing array delimiter. This is accurate for the #347 parent, but the stacked #349 child adds `r[p]!=']'` to both `pollJsonSkipPrimitive()` implementations. Current #349 ESP8266 and ESP32 source blobs were read back and the exact-source regression removes that delimiter as a fail-open mutation; both boards reject the mutation. Master should refresh ROLE_ASSIGNMENTS / INTEGRATION_MATRIX to distinguish #347 parent from #349 child rather than treating the parent's finding as unresolved in #349.

## Ownership and safety boundary

- Current main CGI register/poll producer still does not emit the approved authenticated `response_sig` envelope. PHX-CORE owns the producer contract and golden vectors; PHX-QA owns the inherited parity assertion. Hardware did not invent a positive signature or weaken default-deny.
- No financial/ledger/COE/Release source, production GPIO behavior, admission rule, signer, witness, migration or updater was changed.
- #266 remains OPEN and 0/7 cleanup checkboxes complete.
- COE #26 remains FROZEN; no source was copied or promoted.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the authorized Library surface; no Google Drive connector is exposed in this runtime. No older registry was substituted.

## Evidence classification and next action

- JSON parser grammar and string regressions: **SIMULATED / CI VERIFIED** at exact source/test SHA `7c14c2600fbf4c10e591286a2eca786d5cf5e548`.
- Firmware target builds: pending final Full run readback; no integration pass inferred from focused host labs.
- Physical coin acceptor, relay/electrical recovery, LittleFS power-loss, 150 controlled power cuts and 30-device 24-hour soak: **NOT TESTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

**Next exact action:** PHX-MASTER refreshes the #349 source/test/docs pin and distinguishes its corrected child parser from #347's parent state; PHX-CORE publishes the approved authenticated register/poll envelope and canonical golden vectors; PHX-QA reconciles `Missing poll signature check` against that approved contract. Hardware then reruns Full integration on the approved exact stack without relaxing default-deny.
