# PHX-HARDWARE handover — ESP32 persisted timing bounds

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded firmware defect repair  
Branch: `phoenix/hardware-esp32-timing-bounds-20261115`  
Base: `phoenix/hardware-eeprom-string-bounds-20261115@cbb4fd3f96c4bf2e89dad067a1c68392bbf5987b`

## Proven defect

ESP32 startup read the persisted 32-bit `debounce` and `groupms` preferences
and cast each directly to `uint16_t`. Values above 65535 could wrap before any
runtime validation, while zero or out-of-policy values were also accepted.
Corrupted preferences could therefore disable or distort electrical pulse
debounce/grouping.

## Change

- Added the pure `boundedTimingMs` helper.
- Clamp persisted debounce to 1..2000 ms before narrowing.
- Clamp persisted pulse grouping to 10..10000 ms before narrowing.
- Added source-extracted ASan/UBSan host compilation covering minimum, maximum,
  normal, just-outside, zero and `UINT32_MAX` cases.
- No response schema, controller admission, finance authority, journal format,
  quarantine handling or relay polarity changed.

## Evidence classification

CI status is pending at handover creation. Host failure injection is SIMULATED.
Physical ESP32 pulse behavior, Preferences corruption recovery, electrical
acceptance, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.

## Review request

PHX-QA should independently verify the final exact branch head and run the
boundary regression. A disposable, noncustomer ESP32 should then prove stored
zero/overflow recovery and real pulse timing before HARDWARE ACCEPTED.

Standing PRODUCTION NO-GO remains. No merge, flash, reset, customer deployment,
real money, signer, migration, release or promotion is authorized.
