# PHX-L-VERIFY UTC18 — setup portal GPIO provisioning admission (P0; review only)

**Scope:** draft PR #193 stacked on unmerged #179; no production source changes, flash, customer transactions, merge or release. 2026-10-25T18Z / 2026-10-26 Manila. NO CODEX.

## Exact source and previous CI

- Pre-report PR #193 literal HEAD `1a0d51d73d26206a14d286270031dafc17680d99`.
- ESP8266 sketch blob `a64dd08ecb4eaa71da3b29b43d86ffa8a58df5b5`; ESP32 sketch blob `7b2d3a9c9c0ea076992265bdf1113a6db75a350f`.
- Prior exact-head [Full #40219037493](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40219037493) **COMPLETED FAILURE**, validate job `121246731723` 13 existing checks pass / 2 config-authentication and cold-reboot rollback RED **per board**. Both ESP Arduino compile jobs SUCCESS. [Native #40219037492](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40219037492) SUCCESS. CI is not safety green.

## New bounded executed QA

Both source `web.on("/save", HTTP_POST,...)` handlers check Wi-Fi credentials but then assign `web.arg("coin").toInt()`, `web.arg("led").toInt()`, `web.arg("relay").toInt()` directly into persistent configuration, save it and reboot **without validating GPIO capability, role or pin alias**. Both `setup()` paths subsequently use persisted values in `configureRuntimePins()`, which calls `pinMode` for coin/relay/LED without admission validation. This bypasses the *live remote reconfiguration* alias guard. ESP32 also permits saving polarity changes through the portal.

Independently compiled strict C++17 (`-std=c++17 -O2 -Wall -Wextra -Werror -pedantic`) **manually source-transcribed** /save GPIO assignments and actual `configureRuntimePins` operation ordering with Arduino/Web/GPIO mocks. **16/16 expected observations MATCH; 12/16 conservative test-policy-invalid assignments were saved, followed by a modeled reboot and pinMode on those exact values.** Two positive controls per board remained valid. Negatives include aliases, empty/non-numeric form fields converting to GPIO0, negative/out-of-range values, ESP8266 boot-strapping pin and ESP32 input-only/flash-reserved output pins.

Harness SHA256 `ffb3960be4352be6b60f45205eceea39866a058f609a63919b338599111a934c`; results SHA256 `adae6a08bc6fd918f43ee64a6da1d39274ad4f4c9e8ca13b8cb6e498916587b5`; local evidence ZIP SHA256 `bf9e5bd9868995ac4d9ebbdf276f1bb3c3963451851bf2d9fc14d194c4682526`. The conservative allowed-pin lists are **test policy only**, not an approved board pinout. Wi-Fi verification was assumed successful. This is **not actual ESP binary, HTTP, EEPROM/NVS, boot ROM, electrical relay, flash/power-cut or payment execution**.

## Decision requested from MASTER/CORE

Test-first: introduce a reviewed **board-specific GPIO role/capability and alias validator**, invoked at **all three** trust boundaries: portal /save **before persistence**, persisted config **before any startup GPIO call**, and remote policy admission. Reject unsafe pin sets atomically without losing an existing pending journal. Preserve old-polarity-first OFF behavior, require explicit operator reprovision for physical rebind and prohibit accepting money until trusted policy/witness and physical proof. Do not silently promote a test-only pin allowlist into production.

**NEXT EXACT ACTION:** MASTER/CORE approve the pin-capability contract, then VERIFY adds an extracted-source regression for portal save + cold-start GPIO admission, demonstrates RED before bounded firmware fix, and reruns exact-head Full/Native. No firmware source patch in this checkpoint.

**PRODUCTION NO-GO:** #31/#32/#34/#43 remain open; authenticated event-bound ACK, independent monotonic witness, reversible migration, permanent signing, real coin/relay and 150 physical power cuts / 30-device 24h soak not verified.
