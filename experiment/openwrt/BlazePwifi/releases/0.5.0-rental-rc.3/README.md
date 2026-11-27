# BlazePwifi Standalone Rental Server v0.5.0-rental-rc.3

This release candidate is a focused **Windows OneClick installer hotfix** over rc.2.

## Fixed

On a router that had never been contacted by PuTTY before, `plink.exe -batch` correctly emitted the new SSH host-key fingerprint on stderr. Windows PowerShell 5.1 then promoted that stderr stream into a terminating `NativeCommandError` before the installer could show its GUI trust prompt.

rc.3 fixes the deployment path by wrapping every plink/pscp invocation, preserving strict PowerShell errors for script failures while explicitly capturing native stderr and exit codes.

The intended OneClick flow is now:

1. Double-click `Install-BlazePwifi-Rental.bat`.
2. Enter router IP/hostname, SSH user and password.
3. On first connection, review the SSH fingerprint in a GUI Yes/No dialog.
4. Click Yes.
5. The installer pins that fingerprint for the remaining SCP/SSH operations, uploads the bundle, installs Rental Standalone and opens `https://LocalIP/rental/`.

No manual PuTTY launch or host-key cache preparation is required.

## Architecture

All rc.2 Standalone Rental behavior remains:
- OpenWrt installer preserves network/wireless/firewall UCI configuration.
- Rental administration lives at `/rental/`.
- ESP8266/ESP32 retain the three finalized modes and one-local-slot default.
- Remote ESP coinslot binding remains supported.
- Explicit full BlazePwifi conversion remains available.

This remains an RC pending physical validation across the exact target hardware.
