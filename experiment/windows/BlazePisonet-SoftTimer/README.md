# BlazePisonet SoftTimer

**BlazePisonet SoftTimer** is a clean-room Windows Pisonet timer and kiosk controller inspired by the useful operating principles of legacy ASApp-style timer software, rebuilt for the Blaze ecosystem.

SoftTimer does **not** contain or redistribute the original ASApp binaries, source code, licensing logic, artwork, passwords, or proprietary resources. The implementation is based on observed behavior, supplied user documentation, and independent Windows/.NET code.

## Release line

Current: **v0.4.0**

Primary target: Windows 10/11 x64.

## Core operating modes

### Timer source

1. **Internal PC Timer** — direct coinslot -> serial/USB-RS232 -> SoftTimer. SoftTimer owns the countdown.
2. **External Timer Board** — compatible timer board -> serial/USB-RS232 -> SoftTimer. The hardware board owns active/idle state and SoftTimer owns Windows enforcement.
3. **Blaze Pisonet Timer** — SoftTimer pairs to the existing Blaze ESP8266 timer over Wi-Fi/LAN and follows its remaining-time state.

### Coin topology

1. **Standard 1:1** — one coinslot/timer per PC.
2. **Centralized Coordinator** — one coinslot on a coordinator PC serves many SoftTimer stations over LAN/Wi-Fi.
3. **Centralized Station** — a client PC requests the coordinator's coin window and receives signed/idempotent time-credit events.

Timer source and coin topology are intentionally independent.

## COM-port redesign

SoftTimer has no COM1 requirement.

It enumerates the serial devices currently visible to Windows and supports:

- exact physical-device binding;
- USB VID/PID and serial-number identity where available;
- PnP device identity;
- device-family matching;
- manual COM selection;
- automatic USB-RS232 preference;
- any available serial port;
- optional legacy COM1 behavior.

If Windows moves the same USB-RS232 adapter from `COM7` to `COM12`, exact-device mode can rediscover it by identity instead of requiring Device Manager renaming.

Supported modem-control inputs include DSR, CTS, carrier-detect and ring events. DTR and RTS are configurable outputs. Pulse debounce and minimum/maximum pulse widths are configurable.

## Blaze Pisonet Timer integration

The existing ESP timer remains the timer authority. SoftTimer does not replace its:

- local countdown;
- coin input;
- relay control;
- TM1637 display;
- buzzer/chimes;
- EEPROM persistence;
- local sales counters.

The current compatibility bridge can discover and monitor existing Blaze Pisonet Timer web interfaces without requiring a firmware rewrite. The Windows lock state follows the timer's current remaining time. A future tiny `/api/v1/status` compatibility endpoint can replace HTML compatibility parsing if/when the firmware receives that non-breaking addition.

## BlazePwifi integration

SoftTimer speaks the existing BlazePwifi Vendo/controller signing contract:

- controller heartbeat/polling;
- SHA-256 signed requests using the existing `vendo_key` contract;
- target-nonce coin windows;
- optional forwarding of local serial coin pulses into an active BlazePwifi target window.

BlazePwifi core accounting remains authoritative for BlazePwifi clients. SoftTimer local paid-time state remains authoritative for its Windows station unless explicitly bridged.

## Centralized Pisonet

The Windows-native centralized mode uses:

- a shared pairing key;
- HMAC-SHA256 request authentication;
- request timestamp validation;
- nonce replay rejection;
- a single active coin window with queued stations;
- unique credit event IDs;
- station-side duplicate-event rejection.

This allows one USB-RS232 coinslot to serve multiple Windows PCs almost wirelessly across the local network.

Existing Blaze Pisonet Master/Slave hardware can continue doing its own centralized routing. In that deployment each SoftTimer station simply pairs to its own Blaze timer/slave, so the ESP code base does not need to be replaced.

## Customer lock / anti-bypass layer

SoftTimer includes a Windows kiosk layer with:

- borderless topmost lock surfaces on all monitors;
- low-level keyboard filtering while locked;
- mouse confinement to the primary kiosk screen while locked;
- blocking of Windows keys, Alt+Tab, Alt+F4, Ctrl+Esc and Ctrl+Shift+Esc;
- optional Task Manager and Registry Editor policies;
- optional logoff and Windows power-UI restrictions;
- configurable blocked-process termination while locked;
- optional website blocking through managed hosts entries;
- watchdog/recovery process;
- paid-time state persistence;
- idle-shutdown policy;
- high-volume/repetitive-input safety trigger;
- local member accounts with PBKDF2-hashed passwords and banked time;
- floating active-time panel with optional member BANK / LOGOUT;
- configurable low-time warning threshold and optional WAV warning audio;
- three editable shop schedule windows with overnight/day selection, lock and shutdown actions;
- member banked-time transfer;
- optional BlazePwifi-authoritative Pisonet member accounts with signed metadata sync;
- nonce-bound member authentication proofs without distributing reusable password hashes;
- crash-consistent BANK/RESTORE reconciliation with a durable pending-event journal.

`Ctrl+Alt+Delete` is intentionally left to the Windows Secure Attention Sequence. After returning from the secure screen, pressing **Home** during the short secret window opens the timed SoftTimer administrator login.

There is **no universal/default administrator password**. The operator creates one before SoftTimer can be enabled.

## State and recovery

Configuration and state live under:

`%ProgramData%\BlazeSystems\BlazePisonetSoftTimer`

Paid time is stored with atomic replacement plus a backup file. Central credit events are stored by ID to make retransmission idempotent.

The installer creates clearly named scheduled tasks:

- `BlazePisonet SoftTimer`
- `BlazePisonet SoftTimer Watchdog`

Unlike the legacy reference software, SoftTimer does not disguise its recovery task as a Microsoft component.

## First installation

1. Download `BlazePisonet-SoftTimer-Setup-v0.4.0.exe` from the GitHub Release.
2. Run the Setup EXE as administrator.
3. Complete the normal Windows installer. No PowerShell/BAT/CMD setup step is required.
4. Set an administrator password on first run.
5. Select the timer source and coin topology.
6. For serial hardware, rescan and test the real Device Manager port.
7. Prefer **Bind Exact Device** for USB-RS232 adapters.
8. Enable SoftTimer only after hardware testing.

The release also contains an optional portable EXE-only ZIP. Use the Setup EXE for normal installations because it creates the startup/watchdog integration and Windows uninstall entry.

See [docs/INTEGRATION.md](docs/INTEGRATION.md), [docs/ASAPP-BEHAVIOR-MAP.md](docs/ASAPP-BEHAVIOR-MAP.md), and [docs/SECURITY.md](docs/SECURITY.md).

## Validation boundary

A successful GitHub Windows build validates compilation and packaging. Pisonet deployments still require physical testing of the exact USB-RS232 adapter, modem-control wiring, timer board, power-loss behavior, multi-monitor lock behavior, and actual coin pulses before unattended commercial use.
