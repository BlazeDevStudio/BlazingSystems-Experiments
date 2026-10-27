# LAN Messenger v0.3.1 — Preview candidate 1

**Build identity:** Flutter `0.3.1+14`. Builds must be produced from this
branch's exact source SHA by `.github/workflows/lan-messenger.yml`; never
reuse or relabel a v0.3.0 binary as v0.3.1.

## Included since v0.3.0 Preview 1

- Android: remove legacy duplicate call overlay, separate PiP capability
  from notification permission, restore the active call upon expansion,
  and explicitly close an already-open PiP window on hangup.
- Android/Windows: stabilize video track attachment and remote decoded-frame
  reporting, guard native teardown; Windows compact-call Open returns to
  live call instead of the conversation.
- Windows: minimize unexpected remote-input errors; restore compact window
  as soon as a call ends rather than holding its last frame during media disposal.
- Add configurable 15/30/60/120/300-second disconnect grace (default 60),
  preserving call media during transient WebRTC disconnection.
- File transfer: retry within the configured grace and query encrypted
  receiver chunk status after a lost acknowledgment. Completed receipts
  remain **in memory only** and do not survive app restart.
- Manually specified RFC1918 unicast discovery peers for existing routed LANs.
  **Does not traverse NAT, client isolation, or captive Pisowifi networks
  without an actual permitted return route.**

## Verification and rollout requirements

- Android and Windows builds, Flutter unit tests, Android emulator install,
  and dual-emulator live video/PiP plus notification Answer must pass
  on the **same exact v0.3.1 source SHA** before calling this candidate
  cloud-verified. A passing build alone is not acceptance.
- Live physical Windows/Android audio/video, OEM PiP/notifications,
  long file-transfer disconnect/recovery, Windows blank feed and sporadic
  process termination, and multi-subnet routing/isolation need field tests.
- Production signing, identity/chat storage migration, storage-concurrency
  audit PR #205 and file reception controls are not integrated/cleared.
- Android CI APKs are development-signed. Installing an incompatible key may
  require uninstalling; uninstalling deletes app-private chats/files.
- Windows portable ZIP must be fully extracted; no production-signature
  trust assertion or signed Windows installer is provided by this build.

## Current disposition

Preview only; do not merge/tag as production or overwrite prior stable assets.
Use Actions artifacts and SHA256SUMS from this exact-head build for limited
testing. Pending gates must stay visible in any handout.
