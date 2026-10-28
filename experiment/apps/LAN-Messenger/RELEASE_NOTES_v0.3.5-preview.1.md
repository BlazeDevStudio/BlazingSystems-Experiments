# LAN Messenger v0.3.5 Preview 1 — Original ConnectIT branding

**Preview only.** Exact physical Windows↔Android background video process-exit
regression remains unverified, and developer Android APK signing keys have
changed between previous previews.

## What's new
- Reuses **the owner's original ConnectIT logo** byte-for-byte, not a redraw.
  All 18 original SVG/PNG/adaptive/ICO assets are preserved under
  `assets/branding/connectit/`. The exact asset hashes are regression tested.
- App header displays ConnectIT icon while retaining LAN Messenger's
  existing offline LAN identity and transport behavior.
- Windows EXE native icon, tray icon and installer icon now use the original
  ConnectIT ICO. CI no longer synthesizes the unrelated chat-bubble icon.
- Android standard/adaptive launcher resources are generated from the exact
  original ConnectIT PNG/adaptive artwork on every build.
- Retains v0.3.4 safeguards: compact video waits for completed Flutter
  frames before native Windows HWND mutations; authenticated call-probe
  orphan cleanup; verified two-emulator force-stop recovery; crash-report
  collector for Windows Application Error events.

## Release gates and limitations
- All six exact-source GitHub Actions jobs must pass. Prior v0.3.4 success
  does not certify this rebadged native binary.
- On real Windows↔Android pair, test background incoming video, remote
  camera frames, compact window resizing/expansion, repeated Hang Up and
  process restart; if it still exits, inspect event fault module/exception.
- **Android signing continuity remains unresolved**: preview certs differ
  between builds. Do not assume installed v0.3.4 can upgrade in place.
  Preserve local history/identity before uninstalling a preview.
- The ConnectIT logo is visual branding only. ConnectIT Master/Seed,
  account login, SecureBind, internet relay, and five-hop networking remain
  separate unfinished functionality and are not enabled in this app.
- Windows installer is unsigned testing software; verify SHA256SUMS.
  No production certification or promise of NAT traversal/resumable 1GB
  file transfer.
