# Handover Log — 2026-10-05 — v0.5 Launcher Architecture Milestone

## Successful change

BlazeRental v0.5 implementation resumed on branch `blazepwifi-v0.5.0-implementation`.

The first launcher milestone replaces the destructive v0.4 three-page workspace strategy with a Launcher3 custom-left Blaze surface while preserving the normal home workspace.

## Completed

- BlazePwifi version: 0.5.0.
- Android versionCode: 50000; versionName: 0.5.0.
- Application branding renamed to BlazeRental.
- Approved LCM icon added as launcher icon.
- Added `LauncherAccessController.canUseDevice()`.
- Added `BlazeLeftPanel` with Rental and Notifications surfaces.
- Custom-left callback blocks scroll to normal Home while unpaid.
- Paid/unrestricted state permits normal Launcher3 Home and All Apps.
- Launcher long-press behavior now follows the same access gate.
- Clear All notification support added.
- Daily-driver `USE DEVICE AS IS` is selectable during initial setup without server enrollment.
- Old external Google feed overlay disabled to avoid gesture conflict.

## Key commits

- `f3a857a3a197ddd63cf22edcc2b65b2752d5b1f0` — version 0.5.0
- `8c26c43e6248bc55857ed4c7cd2ee572a2fd867e` — Android version
- `8f28388e94bcdadbbd15ba9c041d7d3812f76aeb` — BlazeRental branding
- `3d68e1ed8fa7c0bd2a7749031465c3b449b6073a` — LCM icon
- `0bb5b02eac46f68e9a2bd018b9a8fe0aa3ac9264` — access gate
- `456b1b4377984762a41483e4e5e47860ffc31ccd` — Clear All notifications
- `edf48583682b5668608e1370eedd066f8ce2974a` — local unrestricted mode
- `a8a83474f40fc5ca1a194f116d1b7af2ef676890` — BlazeLeftPanel
- `e68d4fcfc03d5b91ab7ae6f385c8643d2b56dc21` — preserve normal workspace
- `3addd4bf49a372e60225337701e410b5ced34b73` — custom-left integration
- `b9e27088f492f957f30fa8a524acdda68a12e3d6` — unpaid gate enforcement
- `753811909031aabfc167cdd8fa02058bd1469f2f` — paid Launcher3 interactions
- `c85fa6462023f1971cfcdc36c8d7d4472eddd13d` — daily-driver initial setup

## Validation state

Source changes are committed but the exact v0.5 candidate has **not yet passed CI/emulator validation**. Treat this milestone as implementation-complete, validation-pending.

## Known risks to audit

- Launcher3 custom-content gesture behavior must be proven in emulator.
- Existing v0.4 emulator test still targets the old three-page pager and must be replaced/extended for v0.5.
- Paid-to-unpaid expiry must snap back to Blaze gate reliably.
- QR scanner aspect ratio/native admin polish remains to be completed.
- Release workflow/artifact names are still v0.4-oriented and must be updated before publishing v0.5.

## Next action

Create v0.5 source/emulator tests, finish QR/admin UX, then implement the Management Console/portal 0.5 modules.

## Audit & Reconcile prompt

```text
@GitHub Audit and reconcile BlazePwifi v0.5 launcher development.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md and the newest docs/handover log.
2. Work from branch blazepwifi-v0.5.0-implementation.
3. Inspect the commits listed in the v0.5 launcher milestone; do not assume they compile or behave correctly.
4. Verify BlazeLeftPanel uses Launcher3 custom-left content without deleting normal user workspace pages.
5. Verify unpaid state cannot scroll into Home, open All Apps, launch shortcuts/apps, or bypass through launcher gestures.
6. Verify paid/unrestricted state restores normal Launcher3 Home, hotseat, page indicator, app drawer and allowed app launching.
7. Verify Notifications is adjacent to the BlazeRental page and Clear All works.
8. Verify first-setup daily-driver mode works without BlazePwifi enrollment.
9. Run source/unit/build/emulator gates and record exact SHA/run/artifact evidence; fix regressions before continuing.
10. Update PROJECT_HANDOVER.md and add a new dated handover log after the next meaningful success/failure, including a fresh Audit & Reconcile prompt.
```
