# PHX-HARDWARE — output-enable OFF preload (2026-11-18 UTC)

**Scope:** draft child PR #321, stacked on draft #317. No merge, flash, release, deployment, financial admission, or live-device change.

## Defect

Both Vendo sketches enabled relay and LED GPIO drivers with `pinMode(..., OUTPUT)` before setting the logical OFF latch. For active-low wiring, the default LOW latch can briefly energize an output during setup or reassignment.

## Correction

Both `configureRuntimePins()` implementations now:
1. disable any replaced outputs;
2. configure the coin input;
3. preload logical OFF for relay and LED;
4. enable the output drivers;
5. confirm logical OFF after mode change.

No pin validation, polarity flag, journal, poll, receipt, or admission semantics changed.

## Test-first evidence

- RED source commit: `8efc4308d5c205976838092bbb746ce6f2c56113`.
  The dedicated workflow run #44226524555 failed exactly at **Verify OFF latch is preloaded before output enable**.
- GREEN firmware commits: `b3b3a16b381ff9453f030dd1ebf15177e2775aac` (ESP8266) and `37748a5404109844d2bad88688b8a039982b5c87` (ESP32).
- GREEN focused exact-head run #44293694248, job 134765119664:
  - output polarity mutation lab passed;
  - new output-enable sequence regression passed for both boards and both polarities;
  - parent poll-drain and pulse-capture labs passed;
  - quarantine byte-readback run #44293694297 passed.

The new source-extracted C++17 lab rejects an injected removal of the pre-enable OFF writes. These are host-simulated GPIO-call-order checks, **not** proof of physical relay contact state, electrical polarity, coin pulse behavior, or power-cut durability.

## Remaining gates

Physical wiring/relay acceptance, power-cut campaigns, 30-device soak, signed controller admission, durable receipt/replay contract, QA review, release signing, and production deployment remain blocked. **PRODUCTION NO-GO.**
