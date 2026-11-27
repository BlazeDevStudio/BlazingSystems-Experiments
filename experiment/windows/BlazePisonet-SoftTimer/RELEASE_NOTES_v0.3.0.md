# BlazePisonet SoftTimer v0.3.0

ASApp usability-parity and schedule-enforcement release.

## New customer/runtime behavior

- Adds an ASApp-style floating active-time panel while paid time is running.
- The active timer panel shows remaining time, changes to warning color near expiry, and can expose **BANK / LOGOUT** for member accounts.
- Member users can move the currently running balance into their local hashed account and immediately return the station to the locked state.
- Adds configurable low-time warning threshold and optional custom WAV warning sound.
- Warning audio fires once when a countdown crosses the configured warning threshold and resets when time is replenished above it.
- External timer-board mode does not fake second-by-second low-time warnings because the board only exposes active/idle state.

## Scheduling

- Adds a proper three-window schedule editor matching the useful ASApp model.
- Each schedule supports:
  - enable/disable;
  - start/end time;
  - selected days;
  - overnight windows;
  - customer lock;
  - scheduled shutdown policy;
  - station message.
- Fixes overnight windows so a 22:00 → 07:00 schedule remains associated with the day it started after midnight.
- Fixes scheduled shutdown so it no longer depends on unrelated idle/zero-time/unusual-input shutdown toggles.
- Shutdown policy now schedules the real Windows shutdown first and provides a Cancel path that calls Windows shutdown abort.

## Member management

- Exposes the already-supported member time-transfer engine in the management UI.
- Adds operator-side **BANK CURRENT PAID TIME**.
- Adds transfer of banked minutes from one member account to another with source-account password verification.
- Plaintext member passwords are still never stored.

## Existing hardware/integration behavior retained

- No COM1 requirement.
- Exact USB-RS232 identity binding plus VID/PID family, manual COM, auto-compatible, any-port and legacy COM1 modes.
- Configurable DSR/CTS/carrier/ring inputs and DTR/RTS outputs.
- Internal PC timer.
- External timer-board mode.
- Blaze Pisonet Timer Wi-Fi/LAN bridge.
- Standard one-coinslot/one-PC mode.
- Centralized one-coinslot/many-PC coordinator/station mode.
- BlazePwifi signed Vendo/controller integration.
- Native EXE installer and EXE-managed Windows startup integration.
- Keyboard/mouse kiosk restrictions, Task Manager/Registry policies, watchdog and Ctrl+Alt+Delete → return → Home admin path.

## Validation boundary

GitHub Windows CI validates compilation, self-contained EXE publishing, native Setup EXE creation, installation, native Task Scheduler integration verification, uninstall and cleanup.

Physical certification still requires the actual USB-RS232 adapter, modem-control wiring, timer board, coinslot pulse widths, real Windows image, power-loss behavior and centralized multi-PC hardware.
