# BlazePisonet SoftTimer v0.4.0

Central BlazePwifi member-authority release.

## BlazePwifi-managed members

SoftTimer can now use **BlazePwifi Admin → Pisonet Members** as the authoritative member database.

When **Manage Pisonet members centrally in BlazePwifi** is enabled:

- member creation/editing, enable/disable, password reset, deletion and authoritative banked-time adjustment belong to BlazePwifi Admin;
- SoftTimer shows a synchronized central member cache but does not create/edit central accounts locally;
- existing standalone/local SoftTimer members are preserved and are not silently overwritten or deleted;
- disabling central authority returns the station to its existing local-member behavior.

This feature requires the BlazePwifi **v0.5.3-dev.3 member API line** or a later compatible build. BlazePwifi v0.5.2 production remains intentionally unchanged/frozen.

## Credential and protocol safety

- BlazePwifi does **not** send its stored member password verifier/hash to SoftTimer.
- Member metadata synchronization contains username, label, enabled state, KDF salt/rounds, banked balance, revision and timestamps.
- The member enters the password on the station.
- SoftTimer derives the verifier transiently and sends only a request-nonce/controller-bound proof.
- The request itself is also protected by the existing signed BlazePwifi controller/Vendo channel.
- Plaintext member passwords are not stored in the SoftTimer cache or returned by BlazePwifi.

## Authoritative banked time

- RESTORE removes the authoritative banked balance at BlazePwifi before adding the confirmed result to the local PC timer.
- BANK sends the exact frozen local balance to BlazePwifi and clears local time only after BlazePwifi confirms it.
- Duplicate/retried BANK/RESTORE events are idempotent.
- Central member transfers are managed in BlazePwifi Admin so the central ledger remains the only balance authority.

## Crash and network recovery

v0.4.0 adds a durable pending-member transaction journal.

If Windows, SoftTimer, the network or BlazePwifi fails while a member balance operation is in flight:

- the local countdown is frozen;
- the customer station remains locked;
- new coin pulses are rejected while the balance is uncertain;
- the pending event ID survives restart;
- SoftTimer automatically asks BlazePwifi whether that exact controller-bound event already committed;
- an already-committed event can be replay-confirmed without storing the member password;
- if the server never received the original event, the member can re-enter the password and retry the **same event ID**;
- the local timer is changed only after the central result is conclusively known.

This closes the crash window where the same paid time could otherwise exist both on the PC and in a central member account.

## Existing SoftTimer features retained

- selectable COM ports and exact USB-RS232 identity binding;
- VID/PID family, manual COM, auto-compatible, any-port and legacy COM1 modes;
- internal PC timer;
- external timer-board mode;
- Blaze Pisonet Timer Wi-Fi/LAN bridge;
- standard one-coinslot/one-PC mode;
- centralized one-coinslot/many-PC mode;
- BlazePwifi coin/controller integration;
- native Windows Setup EXE;
- watchdog and native startup integration;
- kiosk keyboard/mouse controls and administrator recovery path;
- floating active-time panel;
- warning audio and three-window shop schedules.

## Validation boundary

Windows CI must pass warnings-as-errors compilation, self-contained EXE publishing, native Setup EXE creation, real silent installation, Task Scheduler integration verification, uninstall and cleanup.

The paired BlazePwifi branch must also pass its member protocol tests and existing full validation matrix before this integration is considered mergeable. Physical USB-RS232, timer-board, coinslot and multi-PC hardware remain real-device validation targets.
