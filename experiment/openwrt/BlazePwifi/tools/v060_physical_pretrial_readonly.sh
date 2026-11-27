#!/bin/sh
# HWPRE-0683: Linux/OpenWrt physical scratch pretrial OBSERVATION ONLY.
# No mount/unmount/flash/powercut/coin/payment action; never production proof.
set -eu
blocked() {
    echo 'HWPRE-0683 BLOCKED: unsafe or unverified disposable lab scratch; no hardware action authorized' >&2
    exit 9
}
[ "$#" -eq 3 ] || blocked
ROOT="$1"
SOURCE="$2"
SCRATCH="$3"
HERE="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
GUARD="$HERE/v060_lab_storage_preflight.sh"
[ -r "$GUARD" ] || blocked
[ -r /proc/self/mountinfo ] || blocked
# OpenWrt /tmp alone is volatile and does not establish crash persistence.
# The named source must actually be a block-special device, not a text file,
# socket, FIFO, char device, or a symlink to customer / overlay storage.
[ -b "$SOURCE" ] && [ ! -L "$SOURCE" ] || blocked
# The existing guard validates *actual* /proc/self/mountinfo, both exact
# mountpoints, private 0700 synthetic root, 0600 fixture marker and backing
# filesystem. It offers no user-provided mount-table or test override.
if ! GATE="$(sh "$GUARD" "$ROOT" "$SOURCE" "$SCRATCH" 2>/dev/null)"; then
    blocked
fi
printf '%s\n' "$GATE" | grep -Fqx 'physical_powercut_verified=0' || blocked
printf '%s\n' "$GATE" | grep -Fqx 'customer_install_authorized=0' || blocked

# Read-only, local and deliberately NON-CERTIFYING. Keep private per-device
# details on the operator's own offline system; do not commit actual records.
printf '%s\n' 'HWPRE-0683 PREFLIGHT_ONLY: isolated mount and block source observed in current Linux mount namespace'
printf 'architecture=%s\n' "$(uname -m)"
printf 'kernel_release=%s\n' "$(uname -r)"
printf '%s\n' "$GATE"
printf '%s\n' 'scratch_medium_disposable_owner_verified=0'
printf '%s\n' 'offdevice_power_controller_authenticated=0'
printf '%s\n' 'actual_hardware_powercuts_completed=0'
printf '%s\n' 'physical_powercut_verified=0'
printf '%s\n' 'financial_migration_authorized=0'
printf '%s\n' 'production_release_authorized=0'
printf '%s\n' 'customer_install_authorized=0'
printf '%s\n' 'HWPRE-0683: no power interruption, disk write, external evidence upload, customer payment or ACK was performed'
