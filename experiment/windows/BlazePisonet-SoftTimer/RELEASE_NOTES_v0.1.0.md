# BlazePisonet SoftTimer v0.1.0

Initial build-validated release line.

## Highlights

- Clean-room Windows remake of the useful ASApp/Pisonet timer operating model.
- No COM1 requirement.
- Dynamic Device Manager COM enumeration.
- Exact USB-RS232 identity binding with PnP/VID/PID/serial metadata when available.
- Manual port, device-family, auto-compatible, any-port and legacy COM1 selection modes.
- Configurable DSR/CTS/carrier/ring coin input and DTR/RTS outputs.
- Internal PC Timer.
- External timer-board active-state mode.
- Existing Blaze Pisonet Timer discovery/pairing over Wi-Fi/LAN.
- Standard 1-coinslot/1-PC mode.
- Windows-native centralized coordinator/station mode for 1-coinslot/many-PC setups.
- HMAC-authenticated centralized peer protocol with nonce/timestamp replay protection.
- Unique time-credit event IDs and duplicate-event rejection.
- Existing BlazePwifi Vendo signing integration and optional coin forwarding.
- Multi-monitor topmost customer lock screen.
- Windows/Alt-Tab/Ctrl-Esc escape-key blocking while locked.
- Windows Secure Attention Sequence preserved; Home is the post-secure-screen admin secret.
- Reversible Task Manager, Registry Editor, logoff and power UI policies.
- Watchdog/recovery process and clearly named scheduled tasks.
- Atomic paid-time persistence.
- PBKDF2 administrator/member passwords; no universal default password.
- Local member time banking.
- Blaze dark navy/cyan/violet management UI.

## Deployment warning

GitHub CI validates the Windows build/package. Before commercial use, physically test the exact USB-RS232 adapter, timer-board signal polarity, coinslot pulse widths, power-loss recovery and lock-screen behavior on the intended Windows image.
