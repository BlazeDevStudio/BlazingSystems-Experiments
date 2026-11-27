#!/bin/sh
# Legacy admin UI compatibility gate, updated for the v0.4 TailAdmin-based interface.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
W="$ROOT/openwrt/rootfs/www/blazepwifi"
ADMIN="$W/admin.html"
BUILD="$ROOT/build/build-openwrt-image.sh"

[ -f "$ADMIN" ] || { echo "missing BlazePwifi admin.html" >&2; exit 1; }
[ -f "$W/vendor/tailadmin/LICENSE" ] || { echo "missing TailAdmin license" >&2; exit 1; }
[ -f "$W/vendor/tailadmin/blaze-tailadmin.css" ] || { echo "missing local TailAdmin stylesheet" >&2; exit 1; }
[ -f "$W/vendor/qrcode/qrcode.js" ] || { echo "missing local QR encoder" >&2; exit 1; }
[ -f "$W/admin/core.js" ] || { echo "missing admin core module" >&2; exit 1; }
[ -f "$W/admin/rental.js" ] || { echo "missing rental admin module" >&2; exit 1; }
[ -f "$W/admin/controllers.js" ] || { echo "missing controller admin module" >&2; exit 1; }

grep -q '/vendor/tailadmin/blaze-tailadmin.css' "$ADMIN"
grep -q '/vendor/qrcode/qrcode.js' "$ADMIN"
grep -q 'Rental Devices' "$ADMIN"
grep -q 'Controllers' "$ADMIN"
grep -q 'System' "$ADMIN"
grep -q 'data-page="rentals"' "$ADMIN"
grep -q 'data-page="controllers"' "$ADMIN"
grep -q 'data-page="system"' "$ADMIN"
! grep -Eq 'https?://[^" ]+\.(css|js)' "$ADMIN"
grep -q 'MIT License' "$W/vendor/tailadmin/LICENSE"

grep -q 'rental_binding_qr' "$W/admin/rental.js"
grep -q 'rental_provisioning_qr' "$W/admin/rental.js"
grep -q 'Bind existing BlazeRental' "$ADMIN"
grep -q 'Provision factory-reset phone' "$ADMIN"
grep -q 'rental_policy_set' "$W/admin/rental.js"
grep -q 'rental_admin_password_set' "$W/admin/rental.js"
grep -q 'expected_revision' "$W/admin/rental.js"
grep -q 'Use device as is' "$W/admin/rental.js"
grep -q 'controller_set' "$W/admin/controllers.js"

# Every production image is built from the same local rootfs, so the UI remains
# offline-capable on constrained routers, x86 and supported Orange Pi targets.
grep -q 'FILES_DIR="$ROOT/openwrt/rootfs"' "$BUILD"
grep -q 'make image PROFILE="$PROFILE"' "$BUILD"
grep -q 'ruijie)' "$BUILD"
grep -q 'x86_64)' "$BUILD"
grep -q 'orangepi_zero3)' "$BUILD"

echo "BlazePwifi admin UI compatibility checks passed"
