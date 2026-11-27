#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$ROOT/tools/BlazeRental-QR-Setup.template.html"
B="$ROOT/tools/build-rental-qr-tool.py"
Q="$ROOT/ui/vendor/qrcode/qrcode.js"
[ -f "$T" ] && [ -f "$B" ] && [ -f "$Q" ]
grep -q 'PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME' "$T"
grep -q 'PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM' "$T"
grep -q 'PROVISIONING_ADMIN_EXTRAS_BUNDLE' "$T"
grep -q 'server_cert_sha256' "$T"
grep -q 'https://192.168.1.1:8443' "$T"
grep -q 'PROVISIONING_WIFI_SSID' "$T"
grep -q '__APK_CHECKSUM__' "$T"
grep -q '__QRCODE_JS__' "$T"
grep -q 'server-cert-sha256' "$ROOT/tools/make-provisioning.py"
echo "BlazeRental PC QR tool source checks passed"
