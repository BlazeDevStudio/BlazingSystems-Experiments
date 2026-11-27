#!/bin/sh
# TRUST-0695. Read-only discovery, NEVER a witness or an installation gate.
# Never opens TPM/MMC hardware, queries the network, or mutates financial state.
set -eu

usage() {
    printf '%s\n' 'Usage: sh v060_trust_capability_inventory.sh {x86_64|orangepi|ruijie|r281|generic}' >&2
    printf '%s\n' 'Synthetic test only: BLAZE_TRUST_TEST_FIXTURE=1 sh ... --fixture-root /tmp/blaze-trust-*/root TARGET' >&2
    exit 64
}

mode=live
root=
if [ "$#" -eq 1 ]; then
    target=$1
elif [ "$#" -eq 3 ] && [ "$1" = "--fixture-root" ]; then
    [ "${BLAZE_TRUST_TEST_FIXTURE:-0}" = 1 ] || usage
    mode=synthetic
    root=$2
    target=$3
    # Only explicit, private synthetic roots; no /, /sys, /dev or live overlay.
    # Physical canonical path comparison prevents symlink or ../ redirection.
    case "$root" in /tmp/blaze-trust-*/root) ;; *) usage ;; esac
    [ -d "$root" ] && [ ! -L "$root" ] || usage
    canonical="$(CDPATH= cd -P -- "$root" 2>/dev/null && pwd -P)" || usage
    [ "$canonical" = "$root" ] || usage
    marker="$root/.blaze-trust-synthetic-only"
    [ -f "$marker" ] && [ ! -L "$marker" ] || usage
    IFS= read -r proof < "$marker" || proof=
    [ "$proof" = 'BLAZE-TRUST-SYNTHETIC-ONLY' ] || usage
    # No synthetic device/sysfs ancestry may resolve outside the fixture.
    # A single leaf -L check is insufficient when its parent is a link.
    for parent in "$root/dev" "$root/sys" "$root/sys/class" \
        "$root/sys/class/tpm" "$root/sys/class/block" "$root/sys/block"; do
        [ ! -L "$parent" ] || usage
    done
else
    usage
fi

case "$target" in
    x86_64|orangepi|ruijie|r281|generic) ;;
    *) usage ;;
esac

# Fixed boolean output, no hardware model/serial, TPM EK, credential, UUID,
# private witness identity or real account information is returned.
tpm_node=false
tpm2_candidate=false
rpmb_candidate=false

# The version_major belongs to the same tpmN index as the corresponding
# character device, not arbitrarily to tpm0. tpmrmN uses the matching tpmN.
# A bounded list avoids enumerating arbitrary host paths on tiny OpenWrt boxes.
for idx in 0 1 2 3 4 5 6 7; do
    if [ "$mode" = synthetic ]; then
        # Fixture regular files are never evidence of actual hardware.
        node_ok=false
        for devpath in "$root/dev/tpm$idx" "$root/dev/tpmrm$idx"; do
            if [ -f "$devpath" ] && [ ! -L "$devpath" ]; then node_ok=true; fi
        done
    else
        node_ok=false
        if [ -c "/dev/tpm$idx" ] || [ -c "/dev/tpmrm$idx" ]; then node_ok=true; fi
    fi
    [ "$node_ok" = true ] || continue
    tpm_node=true
    major_file="$root/sys/class/tpm/tpm$idx/tpm_version_major"
    if [ "$mode" = synthetic ]; then
        # Synthetic sysfs is intentionally plain files, never symlink traversal.
        [ -f "$major_file" ] && [ ! -L "$major_file" ] || continue
        [ ! -L "$root/sys" ] && [ ! -L "$root/sys/class" ] &&
        [ ! -L "$root/sys/class/tpm" ] && [ ! -L "$root/sys/class/tpm/tpm$idx" ] || continue
    else
        [ -r "$major_file" ] || continue
    fi
    IFS= read -r major < "$major_file" || major=
    if [ "$major" = 2 ]; then tpm2_candidate=true; fi
done

# A sysfs RPMB class path is only a candidate: no proof that a key, usable
# monotonic write counter, separate rollback domain or kernel API is available.
for entry in "$root"/sys/class/block/mmcblk*rpmb "$root"/sys/block/mmcblk*rpmb; do
    if [ "$mode" = synthetic ]; then
        # A link to a live/foreign RPMB directory is not fixture evidence.
        [ ! -L "$entry" ] || continue
        { [ -d "$entry" ] || [ -f "$entry" ]; } || continue
    fi
    if [ -e "$entry" ]; then
        rpmb_candidate=true
        break
    fi
done

printf '{"schema":"BLAZE_TRUST_CAPABILITY_V1","target":"%s","evidence_mode":"%s","tpm_node_observed":%s,"tpm2_candidate":%s,"rpmb_candidate":%s,"independent_witness_verified":false,"paid_ack_authorized":false,"financial_migration_authorized":false,"customer_install_authorized":false,"physical_powercut_verified":false,"decision":"BLOCKED_UNVERIFIED_TRUST_ROOT"}\n' \
    "$target" "$mode" "$tpm_node" "$tpm2_candidate" "$rpmb_candidate"

# 2 is intentionally NOT a green installation gate, regardless of candidates.
exit 2
