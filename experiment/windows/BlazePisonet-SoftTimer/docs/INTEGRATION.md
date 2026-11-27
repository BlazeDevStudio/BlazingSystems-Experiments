# Integration guide

## 1. Standard Pisonet: one coinslot / one PC

### Direct USB-RS232

`Coinslot -> USB-RS232 -> Windows PC -> BlazePisonet SoftTimer`

Select:

- Timer source: `InternalPcTimer`
- Coin topology: `StandardOneToOne`
- Serial selection: preferably `ExactDevice`

SoftTimer converts each accepted serial-control pulse to `SecondsPerCoin` and owns the countdown.

### External timer board

`Coinslot -> Allan/Piso timer board -> USB-RS232 -> SoftTimer`

Select:

- Timer source: `ExternalTimerBoard`
- configure the timer-active signal/polarity for the board.

The hardware timer remains authoritative; SoftTimer only enforces Windows access.

### Existing Blaze Pisonet Timer

`Coinslot -> Blaze ESP8266 Timer <-> Wi-Fi/LAN <-> SoftTimer PC`

Select `BlazePisonetTimer`, scan the local network, and pair the desired timer. SoftTimer follows the existing timer's remaining-time state. The ESP firmware remains responsible for physical timing/relay behavior.

## 2. Centralized Windows mode: one coinslot / many PCs

Coordinator:

- `CentralizedCoordinator`
- timer source `InternalPcTimer`
- USB-RS232 coinslot connected only to the coordinator
- set shared key and peer port.

Stations:

- `CentralizedStation`
- same shared key;
- coordinator URL points to the coordinator PC;
- unique station ID.

Flow:

1. Locked station requests the coin slot.
2. Coordinator places the station in its queue.
3. Only one station becomes READY at a time.
4. Coin pulse is accepted at the coordinator.
5. Coordinator creates a unique credit event and sends signed time to that station.
6. Station records the event ID before/with credit application; duplicates are ignored.

The default peer port is TCP 8765. The installer firewall rule is limited to the private local subnet.

## 3. Existing Blaze Pisonet Master/Slave system

Do not replace the current Master/Slave protocol merely to add SoftTimer.

Recommended deployment:

- keep one central coinslot on the existing Master;
- keep current Slave timers and local countdowns;
- pair each Windows SoftTimer instance to the Slave/timer belonging to that PC;
- SoftTimer then locks/unlocks Windows based on the already-routed timer state.

This is the least invasive almost-wireless integration.

## 4. BlazePwifi

SoftTimer uses the BlazePwifi Vendo/controller channel for heartbeat, optional coin forwarding, and—starting with the v0.5.3-dev.3 integration line—central Pisonet member authority.

Configuration requires:

- BlazePwifi Vendo URL, normally `http://SERVER:4455/cgi-bin/vendo`;
- controller ID;
- the current `vendo_key` shared secret;
- optional **Manage Pisonet members centrally in BlazePwifi**.

The base controller signing string remains:

`SHA256(secret|action|id|nonce|pulses|target|secret)`

### Central member authority

When enabled:

- create/edit/enable-disable/reset/delete members in **BlazePwifi Admin → Pisonet Members**;
- BlazePwifi owns the banked-time balance and monotonic member revision;
- SoftTimer keeps local-only members untouched but does not use them for central member login/balance operations;
- SoftTimer synchronizes signed member metadata snapshots;
- snapshots do not contain the stored member password verifier/hash;
- login/BANK/RESTORE use a nonce- and controller-bound password proof;
- BANK/RESTORE/TRANSFER mutations carry deterministic event IDs so a retry cannot apply time twice;
- if BlazePwifi cannot confirm a central member operation, SoftTimer fails closed and preserves local paid time instead of guessing the central balance;
- offline central member spending is intentionally disabled in this development line.

Standalone deployments can leave central member authority disabled and continue using the existing local member store.

Supported integration also retains:

- signed `ping`/`poll`;
- controller heartbeat;
- detection of an active target-bound coin window;
- optional forwarding of a SoftTimer serial coin pulse as the existing signed/idempotent BlazePwifi `coin` event.
