# PHX-HARDWARE handover — ESP8266 EEPROM fixed-string bounds

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded firmware defect repair  
Branch: `phoenix/hardware-eeprom-string-bounds-20261115`  
Base: `phoenix/hardware-setup-ap-route-isolation-20261115@cd8b3f9637f770fd609e2de41fc0d1adb299f105`

## Proven defect

`loadCfg()` accepted EEPROM data based on magic and called `strlen(cfg.apPass)`
before proving the fixed-size array had a NUL terminator. Other current and v1
configuration strings were likewise copied or later converted to `String`
without a bounded termination check. Corrupt EEPROM with a valid magic value
could therefore cause an out-of-bounds read before setup recovery.

## Change

- Added a small reusable bounded fixed-string predicate using `memchr`.
- Require every current configuration string to terminate within its field
  before accepting the record.
- Require every v1 string to terminate before migration.
- Replaced the unbounded setup-password length check with `strnlen`.
- Malformed current or legacy records are rejected and the existing generated
  setup defaults are saved; no coin journal, CORE API, relay policy, signature
  contract, or migration destination was changed.
- Added source-extracted host compilation with ASan/UBSan and corruption
  injection for all 11 fixed-size fields.

## Evidence classification

CI status is pending at handover creation. Host tests are SIMULATED and cannot
establish flash wear, EEPROM corruption behavior on a physical ESP8266, coin
electrical acceptance, power-cut durability, or production readiness.

## Review request

PHX-QA should verify the exact final branch head, confirm the validation precedes
all unbounded consumers and migration, and run a disposable noncustomer
ESP8266 EEPROM-corruption recovery test before HARDWARE ACCEPTED.

Standing NO-GO remains: no merge, flash, customer device, real money, signer,
migration, deployment, or release authorization.
