#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
L="$ROOT/android/BlazeRentalLauncher"
ACCESS="$L/src/com/blazesystems/blazerental/LauncherAccessController.java"
LEFT="$L/src/com/blazesystems/blazerental/BlazeLeftPanel.java"
PAGES="$L/src/com/blazesystems/blazerental/RentalSystemPages.java"
NOTIFY="$L/src/com/blazesystems/blazerental/RentalNotificationService.java"
ADMIN="$L/src/com/blazesystems/blazerental/BlazeAdminActivity.java"
LEASE="$L/src/com/blazesystems/blazerental/RentalLeaseStore.java"
NEXUS="$L/src/com/google/android/apps/nexuslauncher/NexusLauncher.java"
ACT="$L/src/com/google/android/apps/nexuslauncher/NexusLauncherActivity.java"
QR="$L/src/com/blazesystems/blazerental/QrEnrollmentScannerActivity.java"
MANIFEST="$L/AndroidManifest.xml"
GRADLE="$L/build.gradle"

case "$(cat "$ROOT/VERSION")" in
  0.5.0)
    grep -Fq 'versionCode 50000' "$GRADLE"
    grep -Fq 'versionName "0.5.0"' "$GRADLE"
    ;;
  0.5.1)
    grep -Fq 'versionCode 50100' "$GRADLE"
    grep -Fq 'versionName "0.5.1"' "$GRADLE"
    ;;
  0.5.2)
    grep -Fq 'versionCode 50200' "$GRADLE"
    grep -Fq 'versionName "0.5.2"' "$GRADLE"
    ;;
  0.5.3-dev.1)
    grep -Fq 'versionCode 50290' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.1"' "$GRADLE"
    ;;
  0.5.3-dev.2)
    grep -Fq 'versionCode 50291' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.2"' "$GRADLE"
    ;;
  0.5.3-dev.3)
    grep -Fq 'versionCode 50292' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.3"' "$GRADLE"
    ;;
  0.5.3-dev.4)
    grep -Fq 'versionCode 50293' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.4"' "$GRADLE"
    ;;
  0.5.3-dev.5)
    grep -Fq 'versionCode 50294' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.5"' "$GRADLE"
    ;;
  *) exit 1 ;;
esac
grep -Fq 'android:label="BlazeRental"' "$MANIFEST"
grep -Fq '@drawable/ic_launcher_blaze' "$MANIFEST"
test -s "$L/res/drawable/ic_launcher_blaze.xml"

grep -Fq 'boolean canUseDevice(Context context)' "$ACCESS"
grep -Fq 'return canUseDevice(context);' "$ACCESS"
grep -Fq 'class BlazeLeftPanel' "$LEFT"
grep -Fq 'return LauncherAccessController.canUseDevice(launcher);' "$LEFT"
grep -Fq 'BlazeLeftPanel.callbacks' "$NEXUS"
grep -Fq 'return true;' "$NEXUS"
grep -Fq 'moveToCustomContentScreen(false)' "$ACT"
grep -Fq 'enforceRentalLanding(0)' "$ACT"
grep -Fq 'public void finishBindingItems()' "$ACT"
grep -Fq 'getWorkspace().hasCustomContent()' "$ACT"
grep -Fq 'invalidateHasCustomContentToLeft()' "$ACT"
grep -Fq 'ManagedPolicyController.setLauncherForeground(true)' "$ACT"
grep -Fq 'ManagedPolicyController.setLauncherForeground(false)' "$ACT"
grep -Fq 'RentalLeaseStore.isAdminWindowActive(context) || launcherForeground' "$L/src/com/blazesystems/blazerental/ManagedPolicyController.java"

grep -Fq 'public static View createRentalPage' "$PAGES"
grep -Fq 'public static View createNotificationsPage' "$PAGES"
grep -Fq '"CLEAR ALL"' "$PAGES"
grep -Fq 'dismissAll()' "$NOTIFY"
grep -Fq 'MotionEvent.ACTION_MOVE' "$PAGES"
grep -Fq 'adminGesture.shouldTrigger' "$PAGES"
grep -Fq 'boolean policyChanged = allowed != lastCanUseDevice' "$LEFT"

grep -Fq 'USE DEVICE AS IS · NORMAL LAUNCHER' "$ADMIN"
grep -Fq 'setLocalLauncherMode' "$ADMIN"
grep -Fq 'adminLockDurationMs' "$LEASE"
grep -Fq 'admin_lock_level' "$LEASE"
grep -Fq 'now < previousElapsed' "$LEASE"

grep -Fq 'camera.setDisplayOrientation(90)' "$QR"
grep -Fq 'previewH > availableH' "$QR"
grep -Fq 'scanFrame' "$QR"

echo "BlazePwifi v0.5 launcher source contract passed"
