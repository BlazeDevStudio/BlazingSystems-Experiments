# BlazePwifi 0.3.0-rc.1

This release candidate expands BlazePwifi into capability-aware Lite, Standard, and Full deployments.

Highlights:
- hardened admin authentication, lockout, sessions, CSRF and role-aware operations;
- safe configurable network/controller settings with rollback;
- compact Lite portal editor plus richer Standard/Full administration;
- static portal template gallery;
- ESP8266 and ESP32 controller firmware;
- libgpiod Orange Pi controller agent;
- OpenWrt image builds for priority Orange Pi boards and successful additional variants;
- x86_64 BIOS and UEFI images;
- BlazeRental Android DPC/companion APK with QR provisioning artifacts and functional manual APK enrollment;
- server-authoritative rental leases and one-time enrollment.

## Validation boundary

CI build success means build-validated, not physically field-proven. Exact hardware still needs boot/recovery/electrical/brownout/client testing before production deployment.

BlazeRental's factory-reset QR Device Owner mode is stronger than normal APK installation, but the project does not claim resistance to bootloader/recovery reflashing or privileged hardware/OEM service paths.
