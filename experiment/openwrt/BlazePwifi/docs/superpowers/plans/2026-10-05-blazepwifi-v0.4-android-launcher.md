# BlazePwifi v0.4.0 Android Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the v0.3 BlazeRental menu activity with a real Launcher3-derived HOME launcher that gates the app drawer and managed apps on server-authoritative rental time.

**Architecture:** Vendor the exact Launcher3 o-mr1 baseline, preserve its license/provenance, and build BlazeRentalLauncher as a derivative with rental logic isolated under `com.blazesystems.blazerental`. Keep Launcher3 workspace/all-apps internals intact except for explicit policy hooks; Device Owner enforcement and server sync remain separate services/controllers.

**Tech Stack:** Launcher3 o-mr1 commit `5605dd10845b2ed841cadaf3dddcb0205c057c60`, Java, Android support libraries 27.1.1, Android DevicePolicyManager, LockTask, NotificationListenerService, WindowManager overlay, JUnit/UIAutomator.

**Spec:** `experiment/openwrt/BlazePwifi/docs/superpowers/specs/2026-10-05-blazepwifi-v0.4-launcher-design.md`

## Global Constraints

- Production package: `com.blazesystems.blazerental`.
- Preserve Launcher3 Apache-2.0 attribution and exact upstream commit.
- Preserve the v0.3.0 Android project until v0.4 passes its production gate.
- No paid time is minted locally; lease remains server-authoritative.
- Managed QR mode is strongest; manual-installed mode remains labeled lower-security.
- Physical Power-button interception is not an admin dependency.
- A recovery/bootloader wipe is not claimed to be preventable.
- The app remains a real HOME launcher with a genuine swipe-up All Apps drawer.

## Review Focus

- Lease expires while an allowed app is foregrounded: return to BlazeRental and lock the drawer without extra time.
- Inventory includes Settings/installers/system packages: sensitive packages stay hidden in Rental Mode unless authenticated admin/unrestricted mode permits them.
- Device reboots while offline: cached monotonic lease fails closed after expiry and last valid signed policy survives.
- Notification/overlay access is absent: rental enforcement still works and diagnostics show the missing capability.
- Admin gesture/password is brute-forced: lock admin entry temporarily without breaking customer rental operation.

---

### Task 1: Preserve Launcher3 upstream and create the BlazeRentalLauncher baseline

**Files:**
- Create in `BlazingSystems/Forked-Projects`: `android/Launcher3-o-mr1/UPSTREAM.md`, original `LICENSE`, and imported upstream tree at commit `5605dd10845b2ed841cadaf3dddcb0205c057c60`.
- Create: `experiment/openwrt/BlazePwifi/android/BlazeRentalLauncher/` from the same exact upstream tree.
- Create: `android/BlazeRentalLauncher/BLAZE_UPSTREAM.md`.
- Test: `tests/v04_launcher_baseline.sh`.

**Interfaces:**
- Produces a reproducible Launcher3 source baseline that compiles before rental modifications.
- Consumes no earlier v0.4 task.

- [ ] **Step 1: Write the failing provenance test.**
  Assert exact upstream commit text, Apache-2.0 license, Launcher3 source tree, and baseline application metadata.

- [ ] **Step 2: Run `sh tests/v04_launcher_baseline.sh`.**
  Expected: FAIL because BlazeRentalLauncher does not exist.

- [ ] **Step 3: Import the exact upstream tree.**
  Use Git fetch/read-tree in a one-shot import workflow/branch rather than recreating thousands of files manually. Record repository, branch, commit and license.

- [ ] **Step 4: Compile the unmodified historical baseline.**
  Start with JDK 8 and the Gradle/AGP versions required by upstream `build.gradle`; do not begin rental modifications until `assembleAospDebug` succeeds.

- [ ] **Step 5: Run provenance test and baseline compile.**
  Expected: PASS and an upstream-equivalent debug APK.

- [ ] **Step 6: Commit.**
  `chore(blazepwifi): import Launcher3 o-mr1 baseline`

---

### Task 2: Add BlazeRental launcher identity and pure rental state model

**Files:**
- Modify: `android/BlazeRentalLauncher/build.gradle` and manifest/application IDs.
- Create: `src/com/blazesystems/blazerental/RentalState.java`.
- Create: `RentalPolicy.java`.
- Create: `RentalPolicyStore.java`.
- Test: `tests/src/com/blazesystems/blazerental/RentalStateTest.java`.
- Test: `RentalPolicyTest.java`.

**Interfaces:**
- Produces `RentalState.isPaid(long monotonicNowMs)`.
- Produces `RentalPolicy.isPackageAllowed(String packageName)`.
- Produces `launcherMode` values `rental` or `unrestricted`.
- Persists policy revision and last valid signed policy.

- [ ] **Step 1: Write failing JUnit tests.**
  Cover expired/paid monotonic lease, unrestricted mode, sensitive package forced-hide, stale policy not replacing newer revision, malformed policy rejection.

- [ ] **Step 2: Run targeted tests.**
  Expected: FAIL because rental state classes do not exist.

- [ ] **Step 3: Implement minimal pure-Java state/policy classes.**
  Keep Android framework calls out so these tests remain local and deterministic.

- [ ] **Step 4: Run tests.**
  Expected: PASS.

- [ ] **Step 5: Commit.**
  `feat(blazerental): add launcher rental state model`

---

### Task 3: Port enrollment, signed lease sync and Device Owner services

**Files:**
- Create under `src/com/blazesystems/blazerental/`: `Hmac.java`, `LeaseClient.java`, `RentalPolicyClient.java`, `BlazeDeviceAdminReceiver.java`, `BlazeDeviceAdminService.java`, `BlazeBootReceiver.java`, `RentalAlarmReceiver.java`.
- Modify manifest for HOME, Device Admin, boot, notification service and overlay declarations.
- Test: `LeaseProtocolTest.java`.
- Gate: `tests/v04_android_source.sh`.

**Interfaces:**
- Produces authenticated `sync()`, `coinStart()`, `policyPatch(expectedRevision,...)`, inventory/capabilities reporting and managed policy application.
- Consumes the v0.4 server response fields defined in the server/admin plan; until that plan lands, fixture JSON pins the contract.

- [ ] **Step 1: Write failing protocol fixture tests.**
  Verify signature canonicalization, expired lease handling, stale revision response, one-time enrollment fixture, policy signature rejection.

- [ ] **Step 2: Run tests.**
  Expected: FAIL.

- [ ] **Step 3: Port proven v0.3 crypto/enrollment/lease logic.**
  Preserve monotonic lease and per-device secret behavior; add v0.4 revisioned policy fields without breaking v0.3 compatibility.

- [ ] **Step 4: Add managed-policy service hooks.**
  HOME/LockTask/status-bar/user/debug/install restrictions derive from `RentalPolicy`, not UI state.

- [ ] **Step 5: Run unit/source tests and assemble debug APK.**
  Expected: PASS.

- [ ] **Step 6: Commit.**
  `feat(blazerental): port managed lease and policy services`

---

### Task 4: Build the three fixed Launcher workspace pages

**Files:**
- Create: `ui/RentalSystemPageController.java`.
- Create: `RentalPageView.java`, `QuickControlsPageView.java`, `NotificationsPageView.java`.
- Modify the Launcher workspace integration point to install exactly three fixed BlazeRental system pages.
- Create resources under `res/layout/blaze_*.xml`, strings/icons under `res/`.
- Test: `RentalSystemPageControllerTest.java`.
- Instrumentation: `BlazeSystemPagesTest.java`.

**Interfaces:**
- Consumes `RentalState` and `RentalPolicy`.
- Produces fixed non-removable pages 0/1/2 and refresh methods for rental, quick-control and notification state.

- [ ] **Step 1: Write tests for exactly three fixed pages and immutable customer editing.**
  Include low-resolution presence assertions.

- [ ] **Step 2: Run tests.**
  Expected: FAIL.

- [ ] **Step 3: Implement fixed system pages as Launcher-owned workspace pages.**
  They are not ordinary customer widgets and reject drag/remove/resize.

- [ ] **Step 4: Bind Page 1 to remaining time/Insert Coin/Add Time.**
  Insert Coin delegates only to authenticated `LeaseClient.coinStart()`.

- [ ] **Step 5: Run unit/instrumentation build.**
  Expected: PASS.

- [ ] **Step 6: Commit.**
  `feat(blazerental): add fixed rental launcher pages`

---

### Task 5: Gate the real app drawer and filter allowed applications

**Files:**
- Modify the narrowest Launcher3 All Apps transition hook.
- Modify the All Apps model/container filtering hook.
- Create: `LauncherAccessController.java`.
- Test: `LauncherAccessControllerTest.java`.
- Instrumentation: `BlazeAllAppsGateTest.java`.

**Interfaces:**
- Consumes `RentalState`, `RentalPolicy`.
- Produces `canOpenAllApps()`, `filterLaunchablePackages(...)`, and launch authorization shared by icons, notifications and deep shortcuts.

- [ ] **Step 1: Write failing tests.**
  Expired rental rejects drawer; paid rental allows; unrestricted always allows; sensitive/hidden packages filtered; allowed launch passes.

- [ ] **Step 2: Run tests.**
  Expected: FAIL.

- [ ] **Step 3: Add one All Apps transition gate.**
  Do not replace the real drawer with another custom button list.

- [ ] **Step 4: Add model/container filtering and shared launch authorization.**
  Prevent deep-shortcut/app-info routes from bypassing policy.

- [ ] **Step 5: Run tests and instrumentation.**
  Expected: PASS.

- [ ] **Step 6: Commit.**
  `feat(blazerental): gate Launcher3 app drawer by rental policy`

---

### Task 6: Add native on-device administrator and QR binding

**Files:**
- Create: `BlazeAdminActivity.java`.
- Create admin sections for Dashboard, Apps, Binding, Rental, Security, Notifications/Quick Controls, Diagnostics.
- Create: `AdminGestureController.java`, `AdminSession.java`, `QrEnrollmentScannerActivity.java`.
- Add TailAdmin-inspired native theme/resources.
- Test: `AdminGestureControllerTest.java`, `AdminSessionTest.java`.
- Instrumentation: `BlazeAdminUiTest.java`.

**Interfaces:**
- Consumes policy store/client and launcher access controller.
- Produces authenticated local policy edits via compare-and-set, QR binding, app allow/hide UI, secret gesture configuration and `Use device as is`.

- [ ] **Step 1: Write failing tests.**
  Default secret long-press gesture, wrong-password lockout, admin timeout, unrestricted transition, stale revision conflict.

- [ ] **Step 2: Run tests.**
  Expected: FAIL.

- [ ] **Step 3: Implement admin entry/session security.**
  No physical Power-button dependency.

- [ ] **Step 4: Implement native dashboard sections and app inventory toggles.**
  Package IDs may appear as technical detail but are not the primary editing workflow.

- [ ] **Step 5: Implement QR scanner binding.**
  QR carries server endpoint plus short-lived enrollment credential only.

- [ ] **Step 6: Run unit/instrumentation tests.**
  Expected: PASS.

- [ ] **Step 7: Commit.**
  `feat(blazerental): add on-device rental administration`

---

### Task 7: Add notifications, safe quick controls and floating timer

**Files:**
- Create: `BlazeNotificationListener.java`, `NotificationRepository.java`.
- Create: `QuickControlController.java`.
- Create: `FloatingTimerService.java`.
- Modify fixed pages to consume these controllers.
- Test: `NotificationRepositoryTest.java`, `QuickControlControllerTest.java`, `FloatingTimerPolicyTest.java`.

**Interfaces:**
- Consumes package launch authorization and rental policy.
- Produces mirrored notifications, safe quick-control capability list and overlay timer behavior.

- [ ] **Step 1: Write failing tests.**
  Notification tap cannot launch blocked package; missing notification/overlay access degrades safely; dangerous Settings-intent controls are absent; timer toggle obeys operator policy.

- [ ] **Step 2: Run tests.**
  Expected: FAIL.

- [ ] **Step 3: Implement notification listener/repository and Page 3 rendering.**
  Dismiss where allowed; launch only through `LauncherAccessController`.

- [ ] **Step 4: Implement capability-safe Page 2 controls.**
  Hide unsupported/dangerous controls rather than opening unrestricted Settings.

- [ ] **Step 5: Implement small draggable floating timer.**
  Core lease enforcement does not depend on overlay permission.

- [ ] **Step 6: Run tests/build.**
  Expected: PASS.

- [ ] **Step 7: Commit.**
  `feat(blazerental): add notifications quick controls and timer overlay`

---

### Task 8: Complete Android emulator production gate

**Files:**
- Create/update: `.github/workflows/blazerental-v04-emulator.yml`.
- Create: `simulation/android_v04_audit.sh`.
- Create helper test apps only if needed under `android/testapps/`.

**Interfaces:**
- Consumes complete v0.4 Android launcher plus deterministic server fixture.
- Produces screenshots, UIAutomator dumps, audit JSON and green/red evidence consumed by release work.

- [ ] **Step 1: Add emulator assertions.**
  Locked three pages; drawer blocked; lease unlock; allowed/hidden filtering; secret admin; wrong-password lockout; QR/manual bind; notifications; overlay when permitted; reboot; expiry while another app foreground; unrestricted mode; return to Rental Mode.

- [ ] **Step 2: Run emulator workflow.**
  Expected: any missing v0.4 behavior fails.

- [ ] **Step 3: Fix Android defects only with reproducing assertions first.**

- [ ] **Step 4: Run complete Android unit + emulator suite.**
  Expected: PASS.

- [ ] **Step 5: Commit.**
  `test(blazerental): pass v0.4 launcher emulator gate`
