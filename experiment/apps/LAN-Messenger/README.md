# LAN Messenger (BlazingSystems) — v0.2.0 source preview

**Independent project:** a clean-room LAN messenger, file sender, and audio intercom influenced by SHAREit's ease of file sharing, not its proprietary code or assets.

## First-run experience

1. Install the same app on two Windows/Android devices.
2. Connect both to the same reachable private LAN (Ethernet and Wi-Fi may be mixed).
3. Open LAN Messenger on both devices. Both appear under **Nearby devices** automatically.
4. Tap a device to open its conversation. Send texts, images, and arbitrary files there, or tap the phone button to call. A receiver must accept files and calls.

No internet, account, phone number, pairing code, scanning, server, or IP configuration is needed. First-run OS permissions and Windows Firewall approval may still be required. On Android, foreground use is necessary in this preview; the app is not a background/locked-screen telephone.

## Developer guide

```sh
flutter create --platforms=android,windows --project-name lan_messenger .
python3 tool/prepare_platforms.py
flutter pub get
flutter analyze
flutter test
flutter run -d windows  # or a connected Android device
```

GitHub Actions also generates an Android debug APK and Windows portable debug ZIP when the branch is pushed. **Artifacts are developer previews, not signed release installers.** No fabricated testing claims.

## Implemented in source

- IPv4 multicast (`239.42.61.77:39823`) plus LAN broadcast announcements every 4s, online peers age out after 14s.
- P2P local HTTP listener on an ephemeral TCP port, advertised through the discovery packet.
- X25519 shared secret + HKDF-SHA256 + AES-256-GCM for chat, call signaling, file offers, and encrypted file chunks. Device ID is SHA-256 of its static X25519 public key; no external PKI or cloud relay.
- Text messaging, photos and files as persistent conversation bubbles, file picker within the conversation, open-file action, acceptance dialog, chunked transfers, retries, SHA-256 check, and app-private `Received` folder.
- One-to-one audio calls with WebRTC using **LAN host candidates only**, no public STUN or TURN.
- Large touch targets, readable text, automatic hostname-based device name, optional rename (e.g. PC-03), clear declined/connection feedback, incoming-call alert sound, unanswered-call timeout.

## Limitations / known issues

- **Preview code has not been tested with physical Android and Windows pairs.** Neither voice calls nor seamless discovery are claimed as verified.
- Foreground-only on Android; calls won't reliably ring with the app stopped/sleeping. Native foreground services, notifications and Telecom integration remain future work.
- Received files remain in app-private storage. Tapping an attachment requests the OS to open it. On Android this is not an explicit save/export-to-Downloads operation. Do not uninstall expecting these files to survive.
- Local chat history is cached on the device in app-private storage (not encrypted at rest); groups, push-to-talk broadcast, directory transfers, off-LAN calls, and network-crossing discovery are not implemented.
- Discovery fails if local networks block multicast and broadcast, client/AP isolation is enabled, VLANs cannot route between each other, or OS firewalls block incoming traffic. The first Windows inbound connection may trigger a firewall prompt.
- **Security qualification:** transfer content is encrypted against passive LAN observers. Device names are self-declared, first contact is **not independently authenticated**, and no key-verification UI exists. First-contact impersonation and malicious LAN peers are still possible. Cryptographic implementation and protocol need third-party review before production.
- Transfers are limited to individual files of up to 1TB with sequential 64KiB chunks and no restart-safe resume; sending a directory as a directory and high-performance bulk transfer optimization are not implemented.
- CI builds Android and Windows debug previews. They do not guarantee headset/background audio, Windows firewall traversal, USB sound device routing, or physical network acceptance.

## Source layout

- `lib/src/protocol.dart`: wire constants, discovery parsing, path-safe incoming file names.
- `lib/src/identity.dart`: persisted key-pair and encrypted envelope helpers.
- `lib/src/node.dart`: LAN socket discovery, local HTTP requests, text, file transfer handling.
- `lib/src/intercom.dart`: offline WebRTC audio signaling and lifecycle.
- `lib/main.dart`: one-screen accessible Flutter UI.
- `tool/prepare_platforms.py`: patches generated Android/Windows runners.

## Attribution

Built for BlazingSystems. Shares feature goals with SHAREit and draws on public documentation for local discovery/file transfer. No SHAREit binary, branding, private API, or copyrighted UI assets are used. Refer to [LocalSend's open protocol](https://github.com/localsend/protocol) for an independently published design reference; no LocalSend code is bundled here.

## Focused acceptance checks for two real use cases

1. **PisoNet**: PC-01/PC-02 and Android admin on the same non-isolated LAN discover each other; admin taps PC-02, calls, PC answers, both sides hear two-way audio while a game is active; admin sends a photo and it appears inside PC-02's conversation history.
2. **Motorcycle backride**: both Android phones on a local hotspot or other supported direct Wi-Fi LAN, each paired with its own Bluetooth helmet headset; tap Call then Answer, test two-way voice with the screen on. Test audio route, screen-off/background survival and reconnection separately, as none is yet certified. Do not handle the phone while riding.
3. **Adverse network**: validate expected errors for AP/client isolation, segmented VLANs, Windows firewall, missing microphone permission, offline peer, rejected attachments and lost connectivity.
4. **Data safety**: no auto-open of arbitrary received files; validate integrity and sanitized destination; users must deliberately approve unexpected files and incoming calls.

## License / distribution

This is original preview source, not a SHAREit fork. Dependencies retain their separate upstream licenses. Consult their respective upstream license files prior to distribution.