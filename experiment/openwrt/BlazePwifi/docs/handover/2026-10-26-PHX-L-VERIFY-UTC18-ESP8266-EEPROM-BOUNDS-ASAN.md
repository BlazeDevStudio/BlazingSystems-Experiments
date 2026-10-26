# PHX-L-VERIFY — 2026-10-26 UTC18: ESP8266 EEPROM unterminated-string QA

**Priority:** P1 memory-read/config integrity; **state:** independent host RED, MASTER/CORE review requested, no firmware correction authorized. **Release:** NO-GO. **NO CODEX.**

## Source identity and exact finding
- Repository `BlazingSystems/BlazingSystems-Experiments`, DRAFT PR #193 stacked on unmerged #179. Exact source baseline `e32cf158b8c320deefa209a97b4e5ce8b8410c4d`.
- ESP8266 `esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` Git blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`, lines 22–34: `Config.apPass[17]`. Lines 183–207: after `EEPROM.get(0,cfg)`, `if(cfg.magic==MAGIC && strlen(cfg.apPass)>=8) return;` without bounded NUL check.
- If a corrupt EEPROM image has 17 nonzero password bytes, `strlen` can read beyond `apPass` into subsequent pin bytes and beyond the Config allocation in the host reproduction. A magic match does not establish valid string termination, field integrity or trustworthy configuration.

## Executed evidence (isolated host, not ESP firmware)
- C++17 `-O1 -g -fsanitize=address -fno-omit-frame-pointer -Wall -Wextra -Werror -pedantic`, Config layout and literal source admission predicate transcribed into disposable host harness. No customer data, actual EEPROM, device, coin or network involved.
- **5/5 expected test outcomes PASS:** valid terminated 8-byte password accepted; short terminated password denied; wrong magic denied; unterminated password with `coinPin=0` incorrectly admitted by source predicate while bounded reference denies; fully nonzero isolated 288-byte Config causes **expected ASan heap-buffer-overflow read** in `source_admission`, exit code 1.
- The ASan result is specific to a heap-allocated host Config. The actual ESP `cfg` is a global object, so this is **not** proof of an observed ESP crash, actual hardware exploit, physical flash corruption, or coin/relay misbehavior. It is a bounded C-string validation defect requiring source-level correction and embedded testing.
- Reproduction package: `phx_verify_utc18_eeprom_bounds_evidence.zip` (conversation-local, not GitHub Actions artifact), SHA-256 `af44db0ec729668ef7a4fe89551114e1f96a8a0c0bebc43cd18c912d27f382cb`; harness SHA-256 `3c73d9c2e065575fc49c2e6a83120e4239a2325743a2ded6afe2da9b5f521811`; results SHA-256 `cd34af0b454872e5554644d57a4aaa7431abb0fca6d61ca7cae06852102edca3`.

## Exact prior CI and integration gate
- PR #193 literal source/docs HEAD `e32cf158b8c320deefa209a97b4e5ce8b8410c4d`: Full #40372956886 **COMPLETED FAILURE**, validation job 121748417375: two known untrusted-positive-config and older-revision cold-reboot REDs **per ESP board**; mandatory handover and ESP8266/ESP32 Arduino compilation SUCCESS. Native #40372956840 **COMPLETED SUCCESS**. This host finding does not fix the REDs.
- Current development comparison-only SHA `1890e522843d262c33a5109dcea11768896c2e5f`; four commits beyond 5a8 changed three canonical documentation files, no Phoenix firmware merge. #179/#193/#150/#183 remain draft/unmerged; owner-closed #30/#173 not revived.

## Bounded test-first decision
1. MASTER/CORE decide boot fail-closed behavior for invalid EEPROM strings and whether to preserve corrupt bytes for operator recovery; do not auto-migrate/erase uncertain configuration or enable relay.
2. Before a source correction, add real-source host tests for unterminated `apPass` and other fixed-width Config fields; verify EEPROM version/magic, GPIO pin admission and persistence ACK. Use bounded `memchr`/equivalent checks and explicit validity result, not silent `strlen` on raw storage.
3. Require exact-source Arduino builds, independent review and owner-approved noncustomer physical testing. Do not merge, flash, sign, use customer devices or commercialize.

**Hard gates remain:** #31/#32/#43/#34, authenticated controller/ACK, independent monotonic witness, 150 physical power cuts, 30-device 24h soak, reversible migration, permanent signing. **PRODUCTION NO-GO.**
