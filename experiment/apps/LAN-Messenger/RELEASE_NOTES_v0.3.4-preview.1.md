# LAN Messenger v0.3.4 Preview 1 — Windows compact-video safety test

**PREVIEW ONLY. Windows Android-to-PC video freeze/crash remains physically unverified.**
Candidate Flutter version 0.3.4+17, updated from the immutable 0.3.3 Preview 1.
The published release must point to this exact source SHA and all six successful CI jobs.

## Changes from v0.3.3
- After switching into or out of compact video mode, wait for a completed Flutter frame
  before changing native Windows HWND size or topmost state. This lowers the chance
  of resizing the desktop engine while its WebRTC RTCVideoView is being replaced.
- Preserve session ID, closing and mounted checks; preserve deferred restore behavior
  for rapid Hang Up / Expand during compact-window opening.
- Add an independent two-Android process-death acceptance job. It verifies a real
  call on both ends before force-stopping the receiver without graceful Hang Up.
  An earlier exact-source test showed the caller displaying reconnect UI, ending
  the orphaned call and marking the peer Offline after 19.3 seconds.
- Add an opt-in local Windows Application Error event collector script
  `tool/windows_crash_report.ps1`. It summarizes faulting module, exception code,
  fault offset and UTC time only. No automatic uploads, registry changes or dumps.
  The Windows CI runs its synthetic parser self-test.

## Must still verify on real devices
- On the Windows PC start a video call while another app is in front; on Android
  answer, observe remote video frames, minimize/expand, hang up and try again.
  Check that Windows does not flash a frame and exit unexpectedly.
- If Windows still exits, open `perfmon /rel` or use the local crash-report script.
  Supply fault module and exception code for a native-level targeted correction.
  Windows cloud smoke tests do NOT exercise this specific two-platform video path.
- Install the preview on both peers for symmetric call-liveness checking. A device
  still running older builds has reduced call-specific heartbeat compatibility.

## Packaging and limitations
- Android per-ABI signed APKs require a matching CPU architecture; development
  signing keys may differ. An actual phone's "App not installed" still requires
  phone-specific package-installer evidence. Back up before uninstalling builds.
- Windows installer is unsigned testing software; portable build includes native
  runtime DLL dependencies. Verify checksums against SHA256SUMS.
- No verified router/VLAN hop discovery, restart-safe file resume, or external
  internet relay. This is not production certification.
