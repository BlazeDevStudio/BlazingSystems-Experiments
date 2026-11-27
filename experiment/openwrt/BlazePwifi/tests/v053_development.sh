#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
WF="$ROOT/../../../.github/workflows/blazepwifi-build.yml"
GRADLE="$ROOT/android/BlazeRentalLauncher/build.gradle"
ADMIN="$ROOT/android/BlazeRentalLauncher/src/com/blazesystems/blazerental/BlazeAdminActivity.java"

case "$(cat "$ROOT/VERSION")" in
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
grep -Fq 'appVersionName()' "$ADMIN"

# Current development artifacts must never masquerade as the frozen v0.5.2 release.
grep -Fq 'name: BlazePwifi-android-current' "$WF"
grep -Fq 'name: BlazePwifi-current-update' "$WF"
grep -Fq 'name: BlazePwifi-current-candidate-gate' "$WF"
grep -Fq 'BlazeRental-$VERSION-ci.apk' "$WF"
grep -Fq 'BlazeRental-$VERSION-release-unsigned.apk' "$WF"

# Rollback for the development line is anchored to the exact frozen v0.5.2
# application candidate, then raised above current versionCode as a forward install.
grep -Fq 'bf2992977fe8504d21b107df02826032c31d3a62' "$WF"
grep -Fq 's/versionCode 50200/versionCode 50299/' "$WF"
grep -Fq '0.5.2-rescue-for-$VERSION' "$WF"

# The permanent v0.5.2 production identity/recovery material remains preserved.
test -s "$ROOT/SIGNING_RECOVERY.md"
test -s "$ROOT/releases/0.5.2/README.md"
test -s "$ROOT/docs/handover/2026-10-06-v052-production-lineage2-released.md"

echo "v0.5.3 development identity and v0.5.2 preservation contracts passed"
