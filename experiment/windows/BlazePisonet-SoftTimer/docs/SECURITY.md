# Security model

BlazePisonet SoftTimer is intended for PCs owned/administered by the Pisonet operator. Do not deploy kiosk restrictions on a machine you are not authorized to manage.

## Admin credentials

There is no default/master password. The operator must create an administrator password before enabling SoftTimer. Password verification uses PBKDF2-SHA256 with per-install salt.

Member passwords are also PBKDF2-hashed.

## Secure Attention Sequence

Windows owns `Ctrl+Alt+Delete`; SoftTimer does not attempt to intercept or spoof it. The secret admin path is:

1. customer lock is active;
2. operator opens the Windows secure screen using Ctrl+Alt+Delete;
3. operator returns to the desktop;
4. SoftTimer arms a short window;
5. Home opens the timed SoftTimer administrator login.

## Windows policies

Task Manager, Registry Editor, logoff and power UI restrictions are reversible and applied only while the customer lock is active. Administrator maintenance releases those policies.

The uninstaller also clears SoftTimer-managed policy values and hosts-file markers.

## Watchdog

The watchdog is intentionally visible as `BlazePisonet.SoftTimer.Watchdog.exe`. Scheduled tasks use Blaze names. Nothing pretends to be a Microsoft component.

The admin Exit command creates a short maintenance marker so the watchdog does not immediately restart the application.

## Centralized protocol

Peer requests use:

- HMAC-SHA256;
- shared pairing key;
- timestamp freshness;
- random nonce;
- nonce replay cache;
- body hash;
- unique credit event IDs;
- station-side event-id deduplication.

The release installer creates a local-subnet-only firewall rule for the centralized port.

## BlazePwifi

SoftTimer reuses the existing BlazePwifi controller-signature contract instead of introducing a bypass around the accounting system.

## Known v0.1.0 limits

- This is the first build-validated line and still requires physical USB-RS232/timer-board testing.
- Website blocking uses the Windows hosts file and cannot block every DNS-over-HTTPS/VPN scenario.
- Advanced ASApp-era features such as rich promo scheduling, full unusual-mouse analysis, and audio/wallpaper animation editing will be expanded after hardware stability is proven.
