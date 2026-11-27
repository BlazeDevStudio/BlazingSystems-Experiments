# BlazePisonet SoftTimer v0.2.0

Native-installer and kiosk-hardening release.

## Release format

- Adds a normal Windows `BlazePisonet-SoftTimer-Setup-v0.2.0.exe` installer.
- No PowerShell installer/uninstaller is required or shipped as the normal installation path.
- Setup installs the application EXE and watchdog EXE, creates Start Menu/optional desktop shortcuts, creates clearly named automatic logon tasks, and adds the default local-subnet centralized-Pisonet firewall rule.
- Windows Settings / Installed apps provides the normal EXE uninstaller.
- A portable EXE-only ZIP remains available for diagnostics and controlled deployments.
- CI now installs the generated Setup EXE on a Windows runner, verifies both installed EXEs and startup tasks, then uninstalls it before release.

## Runtime improvements

- Implements the existing `LockMouseToScreen` security setting instead of leaving it dormant.
- While the customer lock is active, the mouse is confined to the primary kiosk screen while normal SoftTimer buttons remain usable.
- Mouse confinement is always released when entering administrator maintenance, disabling SoftTimer, or exiting cleanly.
- Preserves the Windows Secure Attention Sequence: Ctrl+Alt+Delete remains Windows-controlled, and Home after returning from the secure screen opens the timed administrator login path.
- Existing keyboard restrictions, Task Manager/Registry policies, process blocking, watchdog recovery, member-time banking, serial identity binding, centralized Pisonet, Blaze Pisonet wireless pairing, and BlazePwifi integration remain intact.

## Hardware model

SoftTimer still has no COM1 requirement. It supports exact USB-RS232 identity, VID/PID/device-family matching, manual COM selection, automatic compatible-device selection, any available serial port, and optional legacy COM1 mode.

## Deployment boundary

The installer and Windows binaries are CI build/smoke-test validated. Commercial deployment still requires physical testing of the exact USB-RS232 adapter, DSR/CTS/DCD/RI signal behavior, DTR/RTS wiring, timer-board polarity, coinslot pulse width, Windows image, power-loss recovery, and centralized multi-PC network.
