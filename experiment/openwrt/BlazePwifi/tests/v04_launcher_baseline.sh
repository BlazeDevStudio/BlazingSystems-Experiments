#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TARGET="$ROOT/android/BlazeRentalLauncher"
UPSTREAM_COMMIT="5605dd10845b2ed841cadaf3dddcb0205c057c60"

fail() { echo "FAIL: $*" >&2; exit 1; }

[ -d "$TARGET" ] || fail "BlazeRentalLauncher baseline is missing"
[ -f "$TARGET/BLAZE_UPSTREAM.md" ] || fail "BLAZE_UPSTREAM.md is missing"
[ -f "$TARGET/LICENSE" ] || fail "Launcher3 Apache-2.0 LICENSE is missing"
[ -f "$TARGET/build.gradle" ] || fail "Launcher3 build.gradle is missing"
[ -f "$TARGET/src/com/android/launcher3/Launcher.java" ] || fail "Launcher3 source tree is incomplete"
[ -f "$TARGET/AndroidManifest.xml" ] || fail "Launcher3 AndroidManifest.xml is missing"

grep -Fq "$UPSTREAM_COMMIT" "$TARGET/BLAZE_UPSTREAM.md" || fail "wrong/missing upstream commit"
grep -Fq "https://github.com/amirzaidi/Launcher3" "$TARGET/BLAZE_UPSTREAM.md" || fail "wrong/missing upstream repository"
grep -Fq "Apache License" "$TARGET/LICENSE" || fail "LICENSE is not Apache-2.0 text"
grep -Fq "applicationId 'amirz.rootless.nexuslauncher'" "$TARGET/build.gradle" || fail "baseline app metadata no longer matches upstream"

echo "PASS: Launcher3 o-mr1 provenance baseline is present and pinned."
