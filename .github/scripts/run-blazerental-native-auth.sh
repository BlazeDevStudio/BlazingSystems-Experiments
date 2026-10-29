#!/usr/bin/env bash
# Runs only the seven PHX-RENTAL source-linked security regressions in a
# disposable Android API 27 emulator; invoked explicitly by Bash because
# android-emulator-runner calls the script through /bin/sh.
set -euo pipefail
mkdir -p rental-auth-results
sdk="$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
test "$sdk" = 27
printf 'Emulator API level: %s\n' "$sdk" | tee rental-auth-results/emulator.txt

# The action launched Android SDK utilities on JDK17. Legacy AGP 3.1.3,
# Gradle 4.4.1, and the connected AndroidTest task require JDK8.
test -n "${JAVA_HOME_8_X64:-}"
export JAVA_HOME="$JAVA_HOME_8_X64"
export PATH="$JAVA_HOME/bin:$PATH"
java -version 2>&1 | tee rental-auth-results/instrumentation-java.txt
java -version 2>&1 | grep -Eq 'version "1\.8\.'

(
  cd "$TARGET"
  ANDROID_HOME=/tmp/blazerental-sdk27 ANDROID_SDK_ROOT=/tmp/blazerental-sdk27 \
    "/opt/gradle-${GRADLE_VERSION}/bin/gradle" --no-daemon --stacktrace \
    "-Pandroid.testInstrumentationRunnerArguments.class=${TEST_CLASS}" \
    connectedAospDebugAndroidTest
) 2>&1 | tee rental-auth-results/connected.log

python3 - <<'PY'
import glob
import os
import sys
import xml.etree.ElementTree as ET

root = os.environ["TARGET"]
reports = sorted(set(
    glob.glob(os.path.join(root, "build", "outputs", "androidTest-results", "connected", "**", "*.xml"), recursive=True)
    + glob.glob(os.path.join(root, "build", "outputs", "androidTest-results", "connected", "*.xml"))
))
expected = {
    "invalidCoinSignatureCannotAlterPaidLease",
    "responseSuppliedSigningKeyCannotAuthorizeStatus",
    "legitimateSignedStatusStillExtendsLease",
    "staleSignedRevisionCannotAlterLeaseOrCoinWindow",
    "sameRevisionSignedRefreshExtendsLeaseWithoutPolicyRewrite",
    "wildcardSameRevisionSurvivesInventoryChange",
    "explicitSameRevisionCannotBecomeWildcard",
}
tests = {}
for path in reports:
    xml = ET.parse(path).getroot()
    for case in xml.iter("testcase"):
        if case.get("classname", "").endswith("LeaseSyncAuthBeforeCommitTest"):
            name = case.get("name")
            if name in tests:
                sys.exit("FAIL: duplicate native security testcase: " + name)
            tests[name] = case

print("JUnit XML reports:", reports)
print("Observed native rental security tests:", sorted(tests))
if set(tests) != expected:
    sys.exit("FAIL: exact seven native security cases not executed")
for name, case in tests.items():
    if case.findall("failure") or case.findall("error") or case.findall("skipped"):
        sys.exit("FAIL: native security test failed/skipped: " + name)

with open("rental-auth-results/results.txt", "w") as out:
    out.write("EMULATOR API 27 / ALL SEVEN SECURITY TESTS PASSED\n")
    for name in sorted(expected):
        out.write("PASS " + name + "\n")
print("EMULATOR API 27 / 7/7 native tests PASS")
PY
