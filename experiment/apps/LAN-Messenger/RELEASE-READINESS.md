# LAN Messenger v0.2.5 — release acceptance and handover

Target permanent repository: BlazingSystems/BlazingSystems-Projects.

**Status: development preview. Do not yet transfer to Projects or mark production.**
Preserve build workflows, attribution, acceptance evidence, and app history.

## Features in the new video/share branch

- Active video calls detect cameras. Switch using the button when multiple
  are available, or double tap the draggable local preview.
- Remote aspect ratio changes with decoded frame orientation (portrait or landscape).
- Video previews are draggable, and the call can minimize into a draggable
  on-screen floating window without stopping the active call.
- During a video call, start screen capture with OS consent. WebRTC replaces
  the camera video sender with screen video; microphone stays in use.
- Android MediaProjection requires system consent for every session and a
  visible foreground service. Device makers may impose additional restrictions.
- Experimental Windows-only remote mouse clicks: viewer requests access,
  Windows owner manually accepts, permission is tied to the current call and
  actively shared display, and it expires after five minutes. Host can revoke.
  No keyboard commands, no unattended control, no Android input injection.
  Multiple-monitor Windows desktops deliberately reject pointer input.

## Release acceptance checklist

- [ ] Android and Windows CI pass format, analyze, unit tests, native release builds,
      signature/integrity checks and an actual emulator install/launch.
- [ ] Two Android phones: front/back camera switching and device rotation, including
      orientation changes from one remote peer during video call.
- [ ] Windows with multiple webcams: switching and safe handling of removal.
- [ ] Android 14+ and Windows screen share start, stop, denied permissions,
      network drops, and call hangup without leaving screen/mic capture active.
- [ ] Draggable local preview, floating minimized window, incoming call interruption,
      and orientation layout in portrait and landscape.
- [ ] Windows screen shared to Android: request/approve click control, deliberate
      click, denial, expiry, revoke, hangup, spoofed peer and offline transitions.
- [ ] 24h LAN endurance including Windows tray and Android background restrictions.
- [ ] Motorbike Wi-Fi/hotspot + Bluetooth helmet audio tested on real devices;
      do not use a preview for safety-critical riding communications.
- [ ] Permanent Android/Windows signing identity, upgrade/data migration,
      file integrity, vulnerability/security review, and launch documentation.

## Planned transfer

After hardware sign-off, tag the accepted source in Experiments and copy
the standalone LAN Messenger application into BlazingSystems-Projects with
a dedicated README and release workflows. Link both histories and do not
delete test evidence. Never announce completion solely from passing CI.
