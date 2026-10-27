# PHX-L-VERIFY UTC10 — persisted startup GPIO admission QA (NO CODEX / NO PRODUCTION)

**Time:** 2026-10-25T10Z. **Branch:** `phoenix/light-verify-target-bound-relay-20261025` (draft PR #193, stacked on unmerged #179). **Classification:** EXECUTED HOST MODEL / REVIEW REQUIRED / PHYSICAL NOT VERIFIED / PRODUCTION NO-GO.

## Exact source and boundary
ESP8266 `esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` Git blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`; ESP32 `esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` Git blob `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`. Both `setup()` functions load persisted configuration, assign runtime GPIOs from persisted `cfg`, and invoke `configureRuntimePins`. The identical current `configureRuntimePins` body drives outputs OFF using old polarity, then invokes `pinMode` for coin/relay/LED without validating board capabilities or rejecting aliases. This differs from already-tested **live remote reconfiguration** guards: persisted **boot-time** configuration is a separate trust boundary.

## Independently executed bounded fixture
Compiled a manually source-transcribed **literal `configureRuntimePins()` function body** with mocked `pinMode` and `digitalWrite`, `g++ -std=c++17 -Wall -Wextra -Werror -pedantic -O2`. Twelve scenarios, six per board, all executed with **zero harness errors**. Two normal controls invoked the expected three `pinMode` calls. **Ten modeled unsafe GPIO configurations also invoked all three `pinMode` calls** (five per board), rather than being rejected.

ESP8266 modeled cases: relay GPIO6 (flash), coin GPIO9 (flash), coin/relay alias, coin GPIO16 with `INPUT_PULLUP` (nonstandard internal pull-up), LED GPIO11 (flash). ESP32 modeled cases: relay GPIO34 (input-only), LED GPIO35 (input-only), relay GPIO6 (flash), coin/relay alias, negative coin GPIO. The ESP32 persisted preference uses a signed integer for coin pin, so the negative case is a relevant possible stored value. For ESP8266 the modeled pins are all representable in the persisted uint8 fields.

**Fixture source SHA256:** `7711e2399e85f42aec35184c9a6c9f00c252a5b63a1abf67ad3462f47be02238`. **Result text SHA256:** `7d9c6f4b86cf4e31cdd2c4fff801a274d6dfa3f9a2ffa057c14cb62d79990067`. The fixture and results were retained in the QA working container; the GitHub report records exact reproduction parameters but does not claim the local fixture is a GitHub CI artifact.

## Interpretation and limitations
This is a **source-transcribed host GPIO-call trace**, not an ESP electrical measurement, not a real boot, not a flash/strap pin test, and not a proof that invalid values actually occur on customer devices. It demonstrates that `configureRuntimePins` itself contains no board capability/alias admission gate, while the actual startup code passes persisted pins to that function. The model's board restrictions are a conservative test subset, **not a complete approved pin capability table**. Whether a particular ESP32 module exposes flash/PSRAM GPIO differs by module; real board-specific policy is required.

**Next:** MASTER+VERIFY review board-specific allowed pins, reserved/strapping/input-only rules, GPIO16 pull-up requirements, persisted configuration integrity, and a fail-closed startup policy *before* any source correction. Test-first startup fixtures should exercise real `setup()`/load paths and reject invalid persisted GPIOs before output mode. Keep existing old-polarity-first OFF protections. No firmware implementation, payment authority, signing, merge, flashing, or release was changed.

## CI baseline (not this fixture)
Exact PR #193 `1cb7c5423b8fb951e5d7ca7902a513b1340cd774`: Full run #40182545422 **COMPLETED FAILURE** (validate job 121136717672: 13 PASS + 2 pre-existing config-auth/reboot RED per board; both Arduino compile jobs SUCCESS). Native run #40182545420 **SUCCESS**. No source or hardware fix is claimed. P0 #31/#32/#43/#34, 150 physical power cuts, 30-client/24h soak, independent witness, reversible migration, signing and electrical coin/relay acceptance remain **PRODUCTION NO-GO**.
