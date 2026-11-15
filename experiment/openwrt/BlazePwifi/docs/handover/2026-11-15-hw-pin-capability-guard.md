# PHX-HARDWARE handover — board pin capability guard

**Date:** 2026-11-15 Asia/Manila  
**Role:** PHX-HARDWARE  
**Task:** unsafe/colliding ESP runtime GPIO assignments  
**Branch:** `phoenix/hardware-pin-capability-guard-20261115`  
**Stack base:** DRAFT #294 at `8cbd4ecec6fcc4a5b0c758c300de986abee5cf40`  
**Classification:** DRAFT / LAB ONLY / PRODUCTION NO-GO

## Proven defect

Both sketches accepted remote pin numbers by numeric range only. ESP32 therefore
accepted flash-connected GPIO 6–11, input-only GPIO 34–39 for relay/LED outputs,
and unimplemented numbers such as GPIO20. ESP8266 accepted flash GPIO 6–11 and
GPIO16 for an `INPUT_PULLUP` coin input. Both boards also accepted the same GPIO
for coin, relay, and/or LED. The setup portal persisted the same unsafe values
without validation.

## Bounded correction

- Board-specific `validInputPullupPin`, `validOutputPin`, and
  `runtimePinsSafe` predicates name the capability rules in one place.
- Remote configuration is evaluated as one distinct pin triplet. An invalid
  triplet is not applied; `pinConfigSafe=false` keeps relay and LED outputs
  denied until a later valid signed configuration arrives.
- Unsafe stored configuration starts on known board defaults with outputs still
  denied, preserving setup access without energizing the acceptor.
- The setup portal rejects unsafe/colliding pins before Wi-Fi verification or
  any persistent write.
- No shared router schema, finance code, receipt handling, or response-signature
  contract changed.

## Verification

`tests/v060_esp_pin_capability_guard.py` extracts and compiles the actual three
pin predicates from each sketch. It injects flash-reserved pins, ESP32
input-only/unimplemented pins, ESP8266 GPIO16 coin input, pairwise collisions,
and valid controls. It also checks that remote, startup, output, and setup-save
paths are wired to the named guard.

At handover creation, exact-head GitHub Actions are **NOT RUN / PENDING**.
Test source and successful commits are not evidence of test passage.

## Explicit limits

- No firmware was flashed; physical GPIO behavior, boot-strapping, relay
  polarity, electrical recovery, coin pulses, power cuts, and soak are
  **NOT TESTED**.
- Existing pending-coin acknowledgement remains insufficiently bound and is
  still MASTER/CORE-owned.
- DRAFT only. No merge, deployment, customer money, release, or hardware
  acceptance.
