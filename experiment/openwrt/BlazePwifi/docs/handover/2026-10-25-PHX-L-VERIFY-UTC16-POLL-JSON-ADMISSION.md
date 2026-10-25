# PHX-L-VERIFY UTC16 supplement — untrusted poll JSON can open coin relay (HOST QA, NO CODEX)

**Status:** REQUEST_REVIEW / P0 / PRODUCTION NO-GO. **Scope:** ESP8266/ESP32 Vendo poll parsing only. No firmware source patch, no financial backend changes, no flashing, no merge.

## Exact provenance

- Source branch `phoenix/light-verify-target-bound-relay-20261025` at `58218f1919f6364f40120824eba76625bbfc3522` before this report; parent draft #179 remains unmerged.
- ESP8266 sketch Git blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`; ESP32 `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`.
- Literal `jsonTrue()` searches for `"insert":true` or `"insert":1` anywhere in response; `jsonString()` returns first `"target_nonce":"..."` anywhere. Neither parses a complete top-level JSON object or rejects duplicate keys.
- Both `loop()` functions set `insertMode=jsonTrue(r,"insert")` and `activeTarget=jsonString(r,"target_nonce")` BEFORE `applyRemoteConfig(r)`. The latter returns early on missing/nonpositive revision; it does not revoke the newly assigned poll state. Initial controller/coin/relay flags are `true`. `applyOutputs()` can energize relay if LittleFS ready, target nonempty, no pending event, and remaining gates allow it.

## Independently executed bounded test

C++17 `g++ -std=c++17 -O2 -Wall -Wextra -Werror -pedantic` test-only String shim with **manually source-transcribed literal** `jsonString`/`jsonTrue` functions, 11 cases per board. **22/22 parser observations match**, 16 cases with `insertMode && target` despite structurally invalid, ambiguous, nested, duplicate, or unauthenticated/absent-revision response. Cases include nested true overriding top-level false; duplicate insert; nested target; duplicate target; numeric 1; missing/zero revision; malformed `trueBAD`. False-insert and missing-target negative controls PASS. The valid-top-level positive control is only structurally valid, NOT authenticated.

Test source SHA256 `ebe8d867533bbd76d903191ce527300b1d4e5531ba66787b5cf10ebecf6df18a`; result log SHA256 `a189cbb8d354a9d7a5bbaae9c85c9ed1210d2aeef729062b64c73c14474efe62`. Evidence ZIP is attached to the ChatGPT conversation, **not** GitHub.

**Interpretation:** `relay_possible` is a boolean host-model projection from actual parser output plus source predicates, **not observed GPIO voltage, actual signed HTTP reply, actual firmware binary, accepted coin, credit, or hardware test**. This supplements, does not replace, prior configuration-auth/reboot RED and ACK parser reports. The remote poll transport is HTTP, so absent authenticated device-bound response verification is a material unresolved trust boundary.

## CI and release gate

Exact prior docs HEAD `58218f1919f6364f40120824eba76625bbfc3522`: [Full #40209685075](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40209685075) COMPLETED **FAILURE**, validate `121218405897` HND-0700 and CI-0701 PASS, both boards `CHECKS 15 FAILED 2` for existing `untrusted_positive_revision_cannot_enable_coin` and `cold_reboot_older_positive_revision_cannot_enable_coin`; ESP8266 and ESP32 compile SUCCESS; [Native #40209685248](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40209685248) COMPLETED SUCCESS. No exact-head green for any successor is asserted.

## Review request

MASTER/CORE: define a strict authenticated, device-bound, monotonic, replay-resistant **poll admission receipt** (separate from terminal coin ACK) with canonical JSON schema, target binding, protected revision freshness and cold-start recovery. VERIFY should deny coin intake for unverified/malformed/duplicate/nested fields; preserve already journaled money for authenticated reconciliation. Do not treat plain JSON parse success or a positive config revision as authorization. No production integration destination approved; #31/#32/#43/#34, physical relay/edge acceptance, 150 cuts, 30-device soak, signer, migration remain NO-GO.
