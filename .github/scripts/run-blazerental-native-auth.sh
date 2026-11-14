#!/usr/bin/env bash
# Runs seven status-auth and four installer-result regressions in a
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
    "-Pandroid.testInstrumentationRunnerArguments.class=${TEST_CLASS},com.blazesystems.blazerental.BlazeRentalUpdateFailureTest" \
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
expected_auth = {
    "invalidCoinSignatureCannotAlterPaidLease",
    "responseSuppliedSigningKeyCannotAuthorizeStatus",
    "legitimateSignedStatusStillExtendsLease",
    "staleSignedRevisionCannotAlterLeaseOrCoinWindow",
    "sameRevisionSignedRefreshExtendsLeaseWithoutPolicyRewrite",
    "wildcardSameRevisionSurvivesInventoryChange",
    "explicitSameRevisionCannotBecomeWildcard",
}
expected_installer = {
    "failedInstallerClearsPendingButPreservesDiagnosis",
    "validUserConfirmationDoesNotClearPending",
    "missingConfirmationIntentTerminatesPending",
    "staleFailureCannotClearNewerInstallAttempt",
}
expected = {
    "LeaseSyncAuthBeforeCommitTest": expected_auth,
    "BlazeRentalUpdateFailureTest": expected_installer,
}
actual = {name: {} for name in expected}
for path in reports:
    root = ET.parse(path).getroot()
    for case in root.iter("testcase"):
        classname = case.get("classname", "")
        for name, cases in actual.items():
            if classname == "com.blazesystems.blazerental." + name:
                method = case.get("name")
                if method in cases:
                    sys.exit("FAIL: duplicate native test: " + name + "." + str(method))
                cases[method] = case
                break

print("JUnit XML reports:", reports)
for suite, wanted in expected.items():
    found = actual[suite]
    print("Observed", suite, "tests:", sorted(found))
    if set(found) != wanted:
        sys.exit("FAIL: incorrect native case set for " + suite)
    for name, case in found.items():
        if case.findall("failure") or case.findall("error") or case.findall("skipped"):
            sys.exit("FAIL: native test failed/skipped: " + suite + "." + name)

total = sum(len(v) for v in expected.values())
with open("rental-auth-results/results.txt", "w") as out:
    out.write("EMULATOR API 27 / " + str(total) + "/" + str(total)
              + " AUTH AND INSTALLER RESULT TESTS PASSED\n")
    for suite in sorted(expected):
        for name in sorted(expected[suite]):
            out.write("PASS " + suite + "." + name + "\n")
print("EMULATOR API 27 / 7/7 auth + 4/4 installer native tests PASS")

PY
