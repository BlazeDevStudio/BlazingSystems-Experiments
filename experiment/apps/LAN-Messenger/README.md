# LAN Messenger (BlazingSystems) — v0.3.3 call-liveness hotfix preview

**Release candidate source:** built from v0.3.0 follow-up fixes. This remains a
field-test preview, **not production-certified**. Review the companion
`RELEASE_NOTES_v0.3.3-preview.1.md` for exact claims and blockers.

**Independent project:** a clean-room LAN messenger, file sender, and audio intercom influenced by SHAREit's ease of file sharing, not its proprietary code or assets.

## First-run experience

1. Install the same app on two Windows/Android devices.
2. Connect both to the same reachable private LAN (Ethernet and Wi-Fi may be mixed).
3. Open LAN Messenger on both devices. Both appear under **Nearby devices** automatically.
4. Tap a device to open its conversation. Send texts, images, and arbitrary files there, or tap the phone button to call. Incoming files are accepted automatically within safety limits; calls still require Answer.

No internet, account, phone number, pairing code, scanning, server, or IP configuration is needed. First-run OS permissions and Windows Firewall approval may still be required. An optional Android foreground service keeps the connection alive with an ongoing notification, but OS battery policies can still stop it. Calls in the background and Bluetooth helmets require hands-on verification.

## Developer guide

```sh
flutter create --platforms=android,windows --project-name lan_messenger .
python3 tool/prepare_platforms.py
flutter pub get
flutter analyze
flutter test
flutter run -d windows  # or a connected Android device
```

GitHub Actions compiles release-mode Android APKs (debug-key signed, not permanent production signing) and a portable Windows release ZIP; it also runs Flutter analysis/tests and Android emulator install/launch checks. **These are developer previews, not field-tested production installers.**

## Implemented in source

- IPv4 multicast (`239.42.61.77:39823`) plus LAN broadcast announcements every 4s, peer identities persist through missed broadcasts; peers appear offline after a 35s presence window and authenticated reachability checks run.
- P2P local HTTP listener on an ephemeral TCP port, advertised through the discovery packet.
- X25519 shared secret + HKDF-SHA256 + AES-256-GCM for chat, call signaling, file offers, and encrypted file chunks. Device ID is SHA-256 of its static X25519 public key; no external PKI or cloud relay.
- Text messaging, photos and files as persistent conversation bubbles, file picker within the conversation, open-file action, automatic receive with 512 MB per-file / four-concurrent-transfer limits, chunked transfers, retries, SHA-256 check, and app-private `Received` folder.
- One-to-one audio/video calling via WebRTC using **LAN host candidates only**, no public STUN or TURN. Native background-only Answer/Decline via Windows Win32 toast or optional Android system overlay/CallStyle notification; video PiP is an ongoing-call feature.
- Experimental LAN group chat (3–8 members) with local history, and 3–4-person group voice/video mesh. Each participant must accept an invitation; one camera/microphone capture is reused across links for a group session.
- Large touch targets, readable text, automatic hostname-based device name, optional rename (e.g. PC-03), clear declined/connection feedback, incoming-call alert sound, unanswered-call timeout.

## Limitations / known issues

- **Preview code has not been tested with physical Android and Windows pairs.** Real device voice/video calling, the Windows native crash and discovery stability remain unverified.
- Android foreground service supports continued network listening while active; a force-stop still terminates it. Incoming-call notifications/lock-screen answer behavior and battery optimizations remain to be tested. This is not a system dialer.
- Received files remain in app-private storage. Tapping an attachment requests the OS to open it. On Android this is not an explicit save/export-to-Downloads operation. Do not uninstall expecting these files to survive.
- Local chat history is cached on the device in app-private storage (not encrypted at rest). Group chat and small group calling are experimental; push-to-talk broadcast, directory transfers, off-LAN calls, and network-crossing discovery are not implemented.
- Discovery fails if local networks block multicast and broadcast, client/AP isolation is enabled, VLANs cannot route between each other, or OS firewalls block incoming traffic. The first Windows inbound connection may trigger a firewall prompt.
- **Security qualification:** transfer content is encrypted against passive LAN observers. Device names are self-declared, first contact is **not independently authenticated**, and no key-verification UI exists. First-contact impersonation and malicious LAN peers are still possible. Cryptographic implementation and protocol need third-party review before production.
- Transfers are limited to individual files by the configured receive cap (512 MiB default) with sequential 64KiB chunks and no restart-safe resume; sending a directory as a directory and high-performance bulk transfer optimization are not implemented.
- CI builds release-mode binaries using non-production signing and validates emulator launch. It does not guarantee headset/background audio, Windows firewall traversal, USB sound device routing, full incoming call negotiation, or physical network acceptance.

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
4. **Data safety**: no auto-open of arbitrary received files; validate integrity and sanitized destination; files from any discovered LAN Messenger peer auto-save to the app-private Received folder (not executed); calls still require consent. Limit this mode to trusted LANs.

## License / distribution

This is original preview source, not a SHAREit fork. Dependencies retain their separate upstream licenses. Consult their respective upstream license files prior to distribution.

## v0.2.1 test priorities

- Regression tests: authenticated peer messaging and chunked automatic file delivery survive stale discovery state.
- Check Windows call crash against updated teardown guards. `call-diagnostics.log` in application support data records call stages, but native crashes need Windows Event Viewer evidence.
- Verify Android call dialog flow no longer produces Flutter `_dependents.isEmpty`.
- Test video calling only on authorized devices with working cameras.
- Auto-receive is intended for trusted LANs, with individual files limited to 512 MiB and up to four simultaneous inbound transfers. Do not expose TCP ports on public networks.

## v0.2.1 field-feedback fixes

- Android Flutter red-screen: avoid popping active dialogs synchronously in widget life-cycle; delay disposal of dialog TextField controller until its transition ends. Needs hardware regression testing.
- File error `403`: retain known cryptographic identities across missed UDP presence broadcasts; allow authenticated first-contact HTTP introductions (reply metadata is only self-declared). Auto-receive up to a configurable 512 MB default limit; protect filename and content integrity.
- Stability: ping previously seen peers concurrently, refresh presence via authenticated requests and direct unicast announcements. No router setup required on a non-isolated LAN.
- Calling: serialized teardown and error log (`call-diagnostics.log` in app storage), WebRTC audio + optional camera video in one calling interface. Windows forced native close still requires reproduction logs.
- Four synthesized, license-free tones (voice, video, message, file) generated with `python tool/generate_assets.py`.
- Windows tray icon and close-to-tray behavior; full exit through tray menu, optional startup at sign-in. Settings control file reception, tones and background behavior.
- Android opt-in foreground service attempts to keep discovery, chat and receiving available; it requires Android's notification and service permissions. Microphone/video background support varies by OS and is not production-tested.

Build from a clean clone: first run `python tool/generate_assets.py` before `flutter create` and `flutter pub get`. GitHub Actions does this automatically.

## v0.3.0 development acceptance

- Incoming call **foreground**: in-app Answer/Decline only. **Windows minimized/tray**: separate small draggable Win32 toast near the taskbar clock, not a Flutter child popup. **Android background**: opt-in system overlay (Display over other apps) and CallStyle notification fallback; notification Answer is delivered to Flutter after a matching incoming offer is ready. Android video PiP is for connected video, not a ringing audio call.
- The Android emulator smoke includes a HOME → Answer Activity resume with a deliberately stale call ID and a repeated tap; this checks for native Activity termination, **not** a real call.
- Group camera/mic is captured once and shared across room peer connections, then released on leave. Group video previews the local camera and remote participant streams as available. Group chat uses authenticated LAN peers, with no central server.
- **Unverified:** answering between physical Windows/Android devices, OS-specific camera/audio permission edge cases, minimized Windows toast behavior in a running game, and 3–4 person synchronized voice/video quality. These require real-device field testing; passing CI cannot replace it.
