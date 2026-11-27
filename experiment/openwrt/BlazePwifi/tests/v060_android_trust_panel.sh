#!/bin/sh
# BlazeRental native on-device admin trust panel — source-only privacy contract.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
ADMIN="$ROOT/android/BlazeRentalLauncher/src/com/blazesystems/blazerental/BlazeAdminActivity.java"
TLS="$ROOT/android/BlazeRentalLauncher/src/com/blazesystems/blazerental/LeaseClient.java"
[ -s "$ADMIN" ] && [ -s "$TLS" ]
grep -Fq 'private void addBindingTrustPanel()' "$ADMIN"
grep -Fq 'RentalLeaseStore.serverCertSha256(this)' "$ADMIN"
grep -Fq 'ManagedPolicyController.isDeviceOwner(this)' "$ADMIN"
grep -Fq 'SHA-256 CERTIFICATE PIN INSTALLED' "$ADMIN"
grep -Fq 'MANAGED SYNC BLOCKED' "$ADMIN"
grep -Fq 'UNPINNED · lower security' "$ADMIN"
grep -Fq 'MANUAL INSTALL · lower bypass protection' "$ADMIN"
grep -Fq 'addBindingTrustPanel();' "$ADMIN"
grep -Fq 'Managed BlazeRental requires a pinned HTTPS server certificate' "$TLS"
# Scope the method body so a privileged scanner or other class is not confused
# with the read-only trust panel. A status UI must NEVER display binding keys.
awk '
  /private void addBindingTrustPanel\(\)/ {inside=1}
  inside && /private void showDashboard\(\)/ {exit}
  inside && /deviceSecret\(|enrollment\(|enrollment_token|secret\\s*\\+|HttpURLConnection|LeaseClient.post|setDeviceIdentity/ {bad=1}
  END {if (!inside || bad) exit 1}
' "$ADMIN"
echo 'PASS: native rental admin shows management/binding/TLS trust state without exposing enrollment secrets'
