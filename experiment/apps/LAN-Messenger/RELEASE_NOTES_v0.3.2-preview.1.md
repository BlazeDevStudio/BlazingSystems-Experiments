# LAN Messenger v0.3.2 Preview 1 — Five-pass corrective build

**Developer preview, not certified for safety-critical communication or production.**
Flutter app version **0.3.2+15**. CI binaries are development-signed;
Windows installer is unsigned. Do not uninstall an earlier version without
backing up app-private chats, received files and device identity.

## Five-pass source audit and correction

1. **Baseline reconciliation:** anchored on published v0.3.1 source,
   integrity-corrective PR #227 and exact-head CI. No historic code or
   previous artifact was misrepresented as v0.3.2.
2. **Encrypted file-transfer integrity:** restored serialized chunk writes
   and recoverable local JSON; additionally reject conflicting retransmitted
   offers that reuse an active transfer ID, and serialize destination-name
   allocation across distinct concurrent transfers. New tests exercise
   the actual local encrypted HTTP receiver.
3. **Android PiP controls:** remove custom "Open conversation" PiP action
   which changed Dart state without expanding the Android OS tile; use
   Android's own tap-to-expand. Active call notification is explicitly
   labeled "Return to live call".
4. **Windows/Android remote video callbacks:** reject non-video/empty
   native streams, attach actual remote video tracks to fallback stream,
   and dispose fallback resources after late/end-of-call callbacks.
   Structural regression tests prevent the previous regressions.
5. **Architecture and compilation:** Flutter 0.3.2+15, readme/release
   contract and exact-SHA Android+Windows CI. Binaries MUST be taken
   only from the exact successful source commit, not relabeled v0.3.1.

## Supported and limited behavior

- Local encrypted peer-to-peer chat, files, WebRTC voice/video on a
  reachable LAN, Android system PiP, Windows compact call view.
- Reconnect grace 15/30/60/120/300 seconds (default 60). Disconnected
  retains an existing media session; WebRTC Failed is terminal without
  negotiated ICE restart.
- Interrupted large-file transfer can query authenticated receiver offset
  and retry within grace, but **not after both apps restart**. Completion
  receipts are volatile and crash/reboot durability remains unimplemented.
- Manual private IPv4 LAN seeds require routable L3 paths and firewall
  ingress/egress; no automatic NAT traversal, captive-client bypass,
  or off-LAN relay is claimed.
- Unknown authenticated LAN peers can still automatically send files with
  the current default, subject to size and concurrency limits. PR #207
  receive-policy security review remains outstanding.

## Acceptance and installation

Check source-specific CI tests, Android install, two Android emulator
foreground/background call and decoded video PiP, Windows launch/tray
and app packaging before field testing. Those tests do not replace
real Windows-to-Android camera, voice, OEM notification/PiP, headset,
memory-pressure, high-volume file interruptions or cross-subnet trials.

Choose one Android APK matching the phone ABI (usually ARM64); Windows
portable ZIP must be extracted fully; installer is unsigned and user-level.
The same application ID and developer signing caveats apply: upgrading
older preview builds can fail due to a differing Android signing key.
Uninstall deletes app-private state.

The GitHub release must be published as a prerelease only after exact
SHA and a completed-success Actions run are confirmed. Published v0.3.1
artifacts and existing PRs must remain unchanged.
