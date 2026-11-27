#!/bin/sh
# HWPRE-0683: negative-only safe pretrial test; never invokes live power control.
set -eu
HERE="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
SCRIPT="$HERE/tools/v060_physical_pretrial_readonly.sh"
GUARD="$HERE/tools/v060_lab_storage_preflight.sh"
[ -r "$SCRIPT" ] && [ -r "$GUARD" ] || exit 1
sh -n "$SCRIPT"
TEMP="$(mktemp -d /tmp/blaze-v2-native-hwpretest-XXXXXX)"
trap 'rm -rf "$TEMP"' EXIT HUP INT TERM
chmod 700 "$TEMP"
printf '%s\n' 'BLAZE-V2-SYNTHETIC-ONLY' > "$TEMP/.blaze-v2-fixture-only"
chmod 600 "$TEMP/.blaze-v2-fixture-only"
SCRATCH=/mnt/blaze-v2-lab-media-hwpretest

reject() {
    label="$1"
    shift
    if sh "$SCRIPT" "$@" > "$TEMP/out" 2> "$TEMP/err"; then
        echo "HWPRE-0683 failed open on $label" >&2
        exit 1
    fi
    grep -Fq 'HWPRE-0683 BLOCKED:' "$TEMP/err" || {
        echo "HWPRE-0683 missing redacted refusal on $label" >&2
        exit 1
    }
    [ ! -s "$TEMP/out" ] || {
        echo "HWPRE-0683 emitted false acceptance on $label" >&2
        exit 1
    }
}
reject 'no parameters'
reject 'unsafe source path' /etc /dev/null "$SCRATCH"
reject 'nonblock char device' "$TEMP" /dev/null "$SCRATCH"
reject 'another char device' "$TEMP" /dev/zero "$SCRATCH"
reject 'nonexistent source' "$TEMP" /dev/blaze-this-device-does-not-exist "$SCRATCH"
reject 'regular source' "$TEMP" "$TEMP/.blaze-v2-fixture-only" "$SCRATCH"
ln -s /dev/null "$TEMP/link-device"
reject 'symlink device' "$TEMP" "$TEMP/link-device" "$SCRATCH"
rm "$TEMP/link-device"
# Even a named synthetic fixture without a real verified mount fails closed.
# No test case should ever create a bind mount, power-cycle or run a payment.
[ "$(cat "$TEMP/.blaze-v2-fixture-only")" = BLAZE-V2-SYNTHETIC-ONLY ]
[ "$(stat -c '%a' "$TEMP/.blaze-v2-fixture-only")" = 600 ]
grep -Fq 'physical_powercut_verified=0' "$SCRIPT"
grep -Fq 'customer_install_authorized=0' "$SCRIPT"
grep -Fq 'financial_migration_authorized=0' "$SCRIPT"
echo 'HWPRE-0683 PASS: nonblock/symlink/missing/live source and unsafe fixture are rejected without a hardware action'
echo 'HWPRE-0683: positive physical scratch mount check deliberately requires actual owner-authorized equipment and is NOT run in CI'
echo 'PHYSICAL_POWER_CUT_VERIFIED=0; CUSTOMER_INSTALL_AUTHORIZED=0'
