#!/bin/sh
# TRUST-0695: negative-only, no live hardware, no finance operations.
set -eu
BASE="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
SCANNER="$BASE/tools/v060_trust_capability_inventory.sh"
[ -r "$SCANNER" ] || exit 1
sh -n "$SCANNER"
TMP="$(mktemp -d /tmp/blaze-trust-0695-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
chmod 700 "$TMP"
ROOT="$TMP/root"
mkdir -p "$ROOT/dev" "$ROOT/sys/class/tpm/tpm0" "$ROOT/sys/class/tpm/tpm1" \
    "$ROOT/sys/class/tpm/tpm2" "$ROOT/sys/class/block"
MARKER="$ROOT/.blaze-trust-synthetic-only"
printf '%s\n' BLAZE-TRUST-SYNTHETIC-ONLY > "$MARKER"
chmod 600 "$MARKER"

refuse_fixture() {
    label=$1
    shift
    rc=0
    BLAZE_TRUST_TEST_FIXTURE=1 sh "$SCANNER" "$@" >"$TMP/out" 2>"$TMP/err" || rc=$?
    [ "$rc" -eq 64 ] && [ ! -s "$TMP/out" ] || {
        echo "TRUST-0695 incorrect fixture admission: $label ($rc)" >&2
        exit 1
    }
}

run_blocked() {
    label=$1
    target=$2
    rc=0
    BLAZE_TRUST_TEST_FIXTURE=1 sh "$SCANNER" --fixture-root "$ROOT" "$target" >"$TMP/out" 2>"$TMP/err" || rc=$?
    [ "$rc" -eq 2 ] && [ ! -s "$TMP/err" ] || {
        echo "TRUST-0695 incorrectly authorized $label ($rc)" >&2
        exit 1
    }
    # No false positive production gate, even with candidate hardware.
    for expected in '"schema":"BLAZE_TRUST_CAPABILITY_V1"' \
        '"evidence_mode":"synthetic"' \
        '"independent_witness_verified":false' \
        '"decision":"BLOCKED_UNVERIFIED_TRUST_ROOT"' \
        '"paid_ack_authorized":false' \
        '"financial_migration_authorized":false' \
        '"physical_powercut_verified":false' \
        '"customer_install_authorized":false'; do
        grep -Fq "$expected" "$TMP/out" || {
            echo "TRUST-0695 missing fail-closed flag for $label" >&2
            exit 1
        }
    done
}

run_blocked absent generic
grep -Fq '"tpm_node_observed":false' "$TMP/out"
grep -Fq '"tpm2_candidate":false' "$TMP/out"
grep -Fq '"rpmb_candidate":false' "$TMP/out"

# Device index matching: tpm1 metadata cannot turn tpm0 into TPM2.
: > "$ROOT/dev/tpm0"
printf '1\n' > "$ROOT/sys/class/tpm/tpm0/tpm_version_major"
printf '2\n' > "$ROOT/sys/class/tpm/tpm1/tpm_version_major"
run_blocked 'mismatched TPM version index' x86_64
grep -Fq '"tpm_node_observed":true' "$TMP/out"
grep -Fq '"tpm2_candidate":false' "$TMP/out"

# Matching TPM1 index is a candidate only, not a trust witness.
: > "$ROOT/dev/tpm1"
run_blocked 'matching TPM2 index' x86_64
grep -Fq '"tpm2_candidate":true' "$TMP/out"
rm "$ROOT/dev/tpm1"
# tpmrmN must also match tpmN.
: > "$ROOT/dev/tpmrm2"
printf '2\n' > "$ROOT/sys/class/tpm/tpm2/tpm_version_major"
run_blocked 'tpmrm2 paired index' x86_64
grep -Fq '"tpm2_candidate":true' "$TMP/out"
rm "$ROOT/dev/tpmrm2" "$ROOT/dev/tpm0"

# A symlinked fake hardware file or symlinked version must never count.
ln -s /dev/null "$ROOT/dev/tpm0"
run_blocked 'symlink fake hardware node' generic
grep -Fq '"tpm_node_observed":false' "$TMP/out"
rm "$ROOT/dev/tpm0"
: > "$ROOT/dev/tpm0"
rm "$ROOT/sys/class/tpm/tpm0/tpm_version_major"
ln -s "$ROOT/sys/class/tpm/tpm1/tpm_version_major" "$ROOT/sys/class/tpm/tpm0/tpm_version_major"
run_blocked 'symlink TPM version' x86_64
grep -Fq '"tpm2_candidate":false' "$TMP/out"
rm "$ROOT/sys/class/tpm/tpm0/tpm_version_major"
printf 'bogus\n' > "$ROOT/sys/class/tpm/tpm0/tpm_version_major"
run_blocked 'unknown TPM major' x86_64
grep -Fq '"tpm2_candidate":false' "$TMP/out"

# RPMB presence is never authenticated counter/write durability evidence.
mkdir "$ROOT/sys/class/block/mmcblk0rpmb"
run_blocked 'RPMB advertised' orangepi
grep -Fq '"rpmb_candidate":true' "$TMP/out"

# A symlinked RPMB node must not appear as genuine fixture capability.
rmdir "$ROOT/sys/class/block/mmcblk0rpmb"
ln -s /tmp "$ROOT/sys/class/block/mmcblk0rpmb"
run_blocked 'symlinked RPMB entry' orangepi
grep -Fq '"rpmb_candidate":false' "$TMP/out"
rm "$ROOT/sys/class/block/mmcblk0rpmb"

# An honest leaf check still follows a symlinked parent. Refuse the fixture.
mv "$ROOT/dev" "$ROOT/dev-original"
ln -s "$TMP" "$ROOT/dev"
refuse_fixture 'symlinked dev ancestry' --fixture-root "$ROOT" x86_64
rm "$ROOT/dev"
mv "$ROOT/dev-original" "$ROOT/dev"

mv "$ROOT/sys/class/block" "$ROOT/sys/class/block-original"
ln -s "$ROOT/sys/class/block-original" "$ROOT/sys/class/block"
refuse_fixture 'symlinked RPMB parent' --fixture-root "$ROOT" orangepi
rm "$ROOT/sys/class/block"
mv "$ROOT/sys/class/block-original" "$ROOT/sys/class/block"

mv "$ROOT/sys/class/tpm" "$ROOT/sys/class/tpm-original"
ln -s "$ROOT/sys/class/tpm-original" "$ROOT/sys/class/tpm"
refuse_fixture 'symlinked TPM parent' --fixture-root "$ROOT" x86_64
rm "$ROOT/sys/class/tpm"
mv "$ROOT/sys/class/tpm-original" "$ROOT/sys/class/tpm"

# Synthetic mode is NEVER allowed to point at a real system root or symlink.
refuse_fixture 'system root' --fixture-root / generic
refuse_fixture 'device path' --fixture-root /dev x86_64
refuse_fixture 'missing synthetic marker' --fixture-root "$TMP" generic
mv "$MARKER" "$TMP/backup-marker"
refuse_fixture 'missing marker private root' --fixture-root "$ROOT" generic
mv "$TMP/backup-marker" "$MARKER"
printf 'not a synthetic fixture\n' > "$MARKER"
refuse_fixture 'incorrect marker' --fixture-root "$ROOT" generic
printf '%s\n' BLAZE-TRUST-SYNTHETIC-ONLY > "$MARKER"
mv "$MARKER" "$TMP/backup-marker"
ln -s "$TMP/backup-marker" "$MARKER"
refuse_fixture 'symlink marker' --fixture-root "$ROOT" generic
rm "$MARKER"
mv "$TMP/backup-marker" "$MARKER"
ln -s "$ROOT" "$TMP/link-root"
refuse_fixture 'symlink fixture root' --fixture-root "$TMP/link-root" generic
rm "$TMP/link-root"
rc=0
sh "$SCANNER" --fixture-root "$ROOT" generic >"$TMP/out" 2>"$TMP/err" || rc=$?
[ "$rc" -eq 64 ] && [ ! -s "$TMP/out" ] || {
    echo 'TRUST-0695 missing fixture env guard' >&2; exit 1
}
rc=0
sh "$SCANNER" unknown-device >"$TMP/out" 2>"$TMP/err" || rc=$?
[ "$rc" -eq 64 ] && [ ! -s "$TMP/out" ] || {
    echo 'TRUST-0695 unknown target accepted' >&2; exit 1
}

echo 'TRUST-0695 / TRUST-0728 PASS: synthetic ancestor and RPMB symlink refusal, TPM indices and paid-authority denial'
echo 'PHYSICAL_POWER_CUT_VERIFIED=0 CUSTOMER_INSTALL_AUTHORIZED=0'
