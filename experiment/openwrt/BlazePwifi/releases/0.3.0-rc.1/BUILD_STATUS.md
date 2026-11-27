# BlazePwifi 0.3.0-rc.1 build status

Release gate: CI build and packaging validation.

Mandatory build targets:
- Ruijie RG-EW1200G Pro v1.1
- x86_64 BIOS and UEFI
- Orange Pi Zero 3
- Orange Pi One
- Orange Pi PC
- ESP8266 controller
- ESP32 controller
- BlazeRental Android APK

Optional Orange Pi targets are attached only when their own build succeeds.

The release remains a release candidate. CI success means build-validated, not physically field-proven. Exact hardware still requires boot/recovery, GPIO/electrical, captive-client, brownout and sustained-load testing before production deployment.
