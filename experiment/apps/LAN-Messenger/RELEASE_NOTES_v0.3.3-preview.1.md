# LAN Messenger v0.3.3 Preview 1 — Windows crash mitigation and orphan-call liveness

**Development preview:** no physical Windows crash regression has yet been cleared.
Candidate Flutter version 0.3.3+16. The complete source/build SHA and
successful CI run must be pinned before distributing testing binaries.

## Field report
Windows minimized/in another app: accepted an Android call, rendered remote
video briefly, froze, then the Windows process exited unexpectedly. Android
kept the call screen active despite its reconnect timer.

## Source-level corrections
- Use encrypted call-ID-specific liveness probes every 5 seconds after
  WebRTC becomes connected. Two authenticated "no such call" responses
  close a stale session promptly; repeated unreachable responses mark the
  peer offline and start the configured 15/30/60/120/300 second grace from
  the FIRST missed response (default 60). No repeated retry can extend it.
- Preserve WebRTC media during transient connection failure. A healthy
  signaling probe alone cannot cancel grace while ICE remains disconnected.
- Older clients not supporting call-probe accept authenticated ping fallback:
  detects a dead process but **cannot prove the remote app still has
  that exact call**. To get full symmetric crash detection BOTH
  Windows and Android must install this hotfix.
- Guard Windows compact PiP-style window opening/restoring from overlapping
  async callbacks and stale call IDs. Preserve user-triggered Expand during
  an in-progress transition. Avoid changing native Win32 taskbar styles while
  a live Flutter/WebRTC texture is mounted.

## Verification and restrictions
- Exact-head Android/Windows Flutter analysis and regression tests, Windows
  runner, Android APK build/install, and dual-emulator WebRTC/PiP must pass.
- Physical Windows video, remote frames, random process exit and cold
  restart survival remain **unverified**. If Windows still exits, collect
  Reliability Monitor / Event Viewer Application Error faulting module,
  exception code and AppCrash info. This source patch is NOT evidence of
  fixing an unidentified native crash.
- Use real phone/PC pair: start call with Windows minimized, answer on Android,
  verify live frames, minimize/restore, and force-kill the PC only on test
  call. Confirm Android marks peer offline after approximately two missed
  probes then ends the call by configured deadline.
- Windows developer installer unsigned; Android developer key may differ
  from previously installed builds. Back up app-private data before
  uninstalling; choose ARM64/ARM32 APK matched to OS ABI.
- Existing constraints remain: no automatic NAT traversal, no long-file
  transfer restart-safe resume, and unknown-peer file receive security
  policy pending review. This is not production certified.
