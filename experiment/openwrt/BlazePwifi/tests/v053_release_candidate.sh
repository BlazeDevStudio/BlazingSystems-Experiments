#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
WF="$ROOT/../../../.github/workflows/blazepwifi-build.yml"
GRADLE="$ROOT/android/BlazeRentalLauncher/build.gradle"
VERSION="$(cat "$ROOT/VERSION")"

[ "$VERSION" = "0.5.3" ]
! printf '%s' "$VERSION" | grep -q -- '-dev'
grep -Fq 'versionCode 50300' "$GRADLE"
grep -Fq 'versionName "0.5.3"' "$GRADLE"
! grep -Fq 'versionCode 50294' "$GRADLE"
! grep -Fq 'versionName "0.5.3-dev.5"' "$GRADLE"

# Rescue must remain the exact frozen v0.5.2 application source, but Android
# must accept it after production 50300.
grep -Fq 'bf2992977fe8504d21b107df02826032c31d3a62' "$WF"
grep -Fq 'RESCUE_VERSION_CODE=50301' "$WF"
grep -Fq '0.5.2-rescue-for-$VERSION' "$WF"

# Development artifacts remain neutral/current; this branch is a candidate,
# not a production tag or signing operation.
grep -Fq 'name: BlazePwifi-android-current' "$WF"
grep -Fq 'name: BlazePwifi-current-update' "$WF"
grep -Fq 'name: BlazePwifi-current-candidate-gate' "$WF"

# Frozen production lineage/recovery records must still exist.
test -s "$ROOT/SIGNING_RECOVERY.md"
test -s "$ROOT/releases/0.5.2/README.md"
test -s "$ROOT/docs/handover/2026-10-06-v052-production-lineage2-released.md"

# Standalone is reference-only. RC1 must not introduce a release workflow that
# writes into the standalone profile tree.
! grep -R "profiles/standalone-rental" "$ROOT/../../../.github/workflows" 2>/dev/null | grep -q "v053"

echo "v0.5.3 production-candidate identity contracts passed"
