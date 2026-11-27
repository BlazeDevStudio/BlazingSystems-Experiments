#!/bin/sh
# v0.6 Android security source contract. Tests what is checked, not hardware TLS.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
ANDROID="$ROOT/android/BlazeRentalLauncher/src/com/blazesystems/blazerental/LeaseClient.java"
CGI="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
HTML="$ROOT/openwrt/rootfs/www/blazepwifi/admin.html"
[ -s "$ANDROID" ] && [ -s "$CGI" ] && [ -s "$HTML" ]
grep -Fq 'ManagedPolicyController.isDeviceOwner(context)' "$ANDROID"
grep -Fq 'Managed BlazeRental requires a pinned HTTPS server certificate' "$ANDROID"
grep -Fq 'if (!(connection instanceof HttpsURLConnection)) {' "$ANDROID"
grep -Fq 'certificateMatches(expectedPin, chain[0])' "$ANDROID"
grep -Fq 'certificateMatches(expectedPin, peer[0])' "$ANDROID"
# Extract the exact pin guard. The formerly unconditional
# "if (expectedPin.length() == 0) return;" must not appear.
! grep -Fq 'if (expectedPin.length() == 0) return;' "$ANDROID"
awk '
  /final String expectedPin = RentalLeaseStore.serverCertSha256/ {inside=1}
  inside && /if \(expectedPin.length\(\) == 0\)/ {empty=1}
  inside && /if \(ManagedPolicyController.isDeviceOwner\(context\)\)/ {owner=1}
  inside && /throw new CertificateException/ {throws++}
  inside && /if \(!\(connection instanceof HttpsURLConnection\)\)/ {end=1;exit}
  END {if (!inside || !empty || !owner || throws<1 || !end) exit 1}
' "$ANDROID"
# Backend managed QR requires pinned local admin TLS and verified APK SHA.
grep -Fq '[ -n "$cert_pin" ] || bp_fail "Device Owner provisioning requires the local pinned admin certificate"' "$CGI"
grep -Fq 'checksum="$(bp_admin_sha256_b64url "$apk_sha")"' "$CGI"
grep -Fq 'generateBindingQr()' "$HTML"
grep -Fq 'generateProvisioningQr()' "$HTML"
echo 'PASS: Device Owner TLS pin required; manual APK fallback remains explicit and QR setup modes are separate'
