#!/bin/sh
# SHADOW-0666. Real installed script, synthetic v1 account/member/rental data.
# It must never write paid state, emit secrets, or authorize migration.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/v2_shadow.sh"
CONFIG="$ROOT/openwrt/rootfs/etc/config/blazepwifi"
T="$(mktemp -d /tmp/blaze-v2-shadow-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
printf 'BLAZE-SHADOW-READ-ONLY-FIXTURE\n' > "$T/.blaze-shadow-fixture-only"
chmod 700 "$T"
chmod 600 "$T/.blaze-shadow-fixture-only"
# Existing synthetic equivalent of the installed global financial lock. The
# read-only observer MUST NOT create its own file or make unsafe lock usable.
mkdir -m 700 "$T/run"
: > "$T/run/paid-financial.lock"
chmod 600 "$T/run/paid-financial.lock"
[ "$(grep -c "option v2_shadow_diagnostics '0'" "$CONFIG")" -eq 1 ]
# Synthetic identities and secrets are intentionally sensitive test markers:
# none may appear in operator-visible diagnostics, successful or failed.
printf '%s\t250\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.1.1.2\tsecretReceipt\n' \
 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' > "$T/accounts.tsv"
printf '%s\t180\t0\t0\t0\t0\tbb:bb:cc:dd:ee:ff\t10.1.1.3\tsecretReceipt2\n' \
 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' >> "$T/accounts.tsv"
printf 'alice\tAlice\t1\tsha256i\tPrivateSalt\tPrivateHash\t4096\t200\t1\t100\tfixture\n' > "$T/members.tsv"
printf 'bob\tBob\t1\tsha256i\tPrivateSalt2\tPrivateHash2\t4096\t0\t1\t100\tfixture\n' >> "$T/members.tsv"
printf 'dev01\tPrivateDeviceSecret\t999999\tTerminal 1\t100\n' > "$T/rental-devices.tsv"
# MIG-0736: the paid financial source set must include the global revision
# and BOTH receipt histories; original observer examined only balances.
printf '1\n' > "$T/member-revision"
printf 'fixture:event:1\t100\talice\tadd\t10\t10\tfixture\t\n' > "$T/member-events.tsv"
paid_rental_event="r:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
printf '%s\tdev01\t999999\t100\tp:2\n' "$paid_rental_event" > "$T/rental-events.tsv"
chmod 600 "$T/"*.tsv "$T/member-revision"
# The negative missing-file cases need a deterministic snapshot sentinel; a
# bare sha256sum would itself exit 1 before proving fail-closed behavior.
snapshot() {
  for name in accounts.tsv members.tsv rental-devices.tsv member-revision member-events.tsv rental-events.tsv; do
    if [ -f "$T/$name" ]; then
      sha256sum "$T/$name"
    else
      printf 'MISSING\t%s\n' "$name"
    fi
  done
}
baseline="$(snapshot)"
fixture() { BLAZE_V2_SHADOW_FIXTURE=1 BP_V2_SHADOW_TEST_ROOT="$T" sh "$SCRIPT" "$@"; }
refuse() {
  old="$(snapshot)"
  if fixture status >"$T/stdout" 2>"$T/stderr"; then
    echo "unsafe v2 shadow input was accepted: $1" >&2
    exit 1
  fi
  [ ! -s "$T/stdout" ] || { echo 'refusal emitted incomplete snapshot' >&2;exit 1; }
  [ "$(snapshot)" = "$old" ] || { echo 'refusal altered paid data' >&2;exit 1; }
  grep -q 'SHADOW BLOCKED' "$T/stderr"
}
result="$(fixture status)"
printf '%s\n' "$result" | grep -Fqx 'status=NON_AUTHORITATIVE_READ_ONLY'
printf '%s\n' "$result" | grep -Fqx 'wallet_accounts=2'
printf '%s\n' "$result" | grep -Fqx 'member_accounts=2'
printf '%s\n' "$result" | grep -Fqx 'rental_devices=1'
printf '%s\n' "$result" | grep -Fqx 'payment_write_authorized=0'
printf '%s\n' "$result" | grep -Fqx 'migration_authorized=0'
[ "$(snapshot)" = "$baseline" ]
# MIG-0735: no fake quiescence when a real paid writer holds this lock.
# This exercises the exact installed lock pathname, a separate process, and
# denial with zero balances/leases modified and no partial status output.
(
  exec 9< "$T/run/paid-financial.lock"
  flock -x 9 || exit 1
  : > "$T/writer-held"
  while [ ! -f "$T/release-writer" ]; do sleep 0.05; done
) &
writer_pid=$!
tries=0
while [ ! -f "$T/writer-held" ] && [ "$tries" -lt 100 ]; do
  sleep 0.05
  tries=$((tries+1))
done
[ -f "$T/writer-held" ] || { echo 'MIG-0735 lock holder failed' >&2; exit 1; }
refuse active-financial-writer
: > "$T/release-writer"
wait "$writer_pid"
rm "$T/writer-held" "$T/release-writer"

# No creation/repair: missing, linked, aliased, broad-mode and unsafe
# parent directory all fail closed without leaking paid identifiers.
mv "$T/run/paid-financial.lock" "$T/lock.saved"
refuse absent-global-money-lock
[ ! -e "$T/run/paid-financial.lock" ]
mv "$T/lock.saved" "$T/run/paid-financial.lock"
ln -s "$T/run/paid-financial.lock" "$T/run/link-alias"
mv "$T/run/paid-financial.lock" "$T/lock.saved"
mv "$T/run/link-alias" "$T/run/paid-financial.lock"
refuse symlink-global-money-lock
rm "$T/run/paid-financial.lock"
mv "$T/lock.saved" "$T/run/paid-financial.lock"
ln "$T/run/paid-financial.lock" "$T/hardlink-alias"
refuse hardlinked-global-money-lock
rm "$T/hardlink-alias"
chmod 666 "$T/run/paid-financial.lock"
refuse world-writable-global-money-lock
chmod 600 "$T/run/paid-financial.lock"
chmod 750 "$T/run"
refuse insecure-lock-parent-directory
chmod 700 "$T/run"
printf 'PENDING\n' > "$T/paid-v2-cutover-intent"
refuse staged-v2-financial-cutover
rm "$T/paid-v2-cutover-intent"
ln -s "$T/missing-cutover" "$T/paid-v2-cutover-intent"
refuse dangling-v2-cutover-intent
rm "$T/paid-v2-cutover-intent"
[ "$(fixture status | grep -Fc 'status=NON_AUTHORITATIVE_READ_ONLY')" -eq 1 ]
[ "$(snapshot)" = "$baseline" ]
if printf '%s\n' "$result" | grep -Eiq 'Private|secretReceipt|alice|dev01|aaaaaaaa'; then
 echo 'SHADOW LEAK: financial identities or key material in diagnostics' >&2;exit 1
fi
# Refuse direct nonfixture invocation and any attempt to use a money operation.
if BLAZE_V2_SHADOW_FIXTURE=1 BP_V2_SHADOW_TEST_ROOT=/etc sh "$SCRIPT" status >"$T/stdout" 2>"$T/stderr"; then
 echo 'arbitrary live state override accepted' >&2;exit 1
fi
if fixture credit >"$T/stdout" 2>"$T/stderr"; then
 echo 'paid write command accidentally supported' >&2;exit 1
fi

# SHADOW-0667: fail closed for source inode aliasing or permissions that
# would compromise the reliability/private handling of v1 financial data.
# All mutations in this section are disposable fixture metadata only.
for name in accounts.tsv members.tsv rental-devices.tsv member-revision member-events.tsv rental-events.tsv; do
  ln "$T/$name" "$T/linked-source"
  refuse "hardlinked-$name"
  rm "$T/linked-source"
  chmod 640 "$T/$name"
  refuse "group-readable-$name"
  chmod 600 "$T/$name"
done
chmod 750 "$T"
refuse group-accessible-state-directory
chmod 700 "$T"
chmod 777 "$T"
refuse world-writable-state-directory
chmod 700 "$T"
[ "$(snapshot)" = "$baseline" ]
[ "$(fixture status | grep -Fc 'status=NON_AUTHORITATIVE_READ_ONLY')" -eq 1 ]

cp -p "$T/accounts.tsv" "$T/a.good"
printf '%s\t20\t0\t0\t0\t0\t\t\t\n' 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' >> "$T/accounts.tsv"
refuse duplicate-account
cp -p "$T/a.good" "$T/accounts.tsv"
printf 'bad\t1\n' >> "$T/accounts.tsv"
refuse truncated-account
cp -p "$T/a.good" "$T/accounts.tsv"

cp -p "$T/members.tsv" "$T/m.good"
printf 'alice\tDuplicate\t1\tsha256i\tx\ty\t4096\t0\t1\t100\tfixture\n' >> "$T/members.tsv"
refuse duplicate-member
cp -p "$T/m.good" "$T/members.tsv"

cp -p "$T/rental-devices.tsv" "$T/r.good"
printf 'dev01\tOtherSecret\t100\tduplicate\t10\n' >> "$T/rental-devices.tsv"
refuse duplicate-rental
cp -p "$T/r.good" "$T/rental-devices.tsv"
printf 'dev02\tOtherSecret\tbogus\tinvalid-lease\t10\n' >> "$T/rental-devices.tsv"
refuse invalid-rental
cp -p "$T/r.good" "$T/rental-devices.tsv"

# MIG-0746: source-admission must never interpret unbounded digit strings,
# signed-32-bit overflow, or zero-padded monetary values as safe v1 funds.
# Test ALL current monetary/lease/time columns; restore exact fixtures after
# each failure and assert no six-file paid state writes or partial stdout.
numeric_bad() {
  file="$1"; column="$2"; replacement="$3"; why="$4"
  cp -p "$T/$file" "$T/mig0746.good"
  awk -F '\t' -v OFS='\t' -v col="$column" -v val="$replacement" '
    NR==1 {$col=val} {print}
  ' "$T/mig0746.good" > "$T/mig0746.new"
  chmod 600 "$T/mig0746.new"
  mv "$T/mig0746.new" "$T/$file"
  refuse "$why"
  cp -p "$T/mig0746.good" "$T/$file"
  rm "$T/mig0746.good"
}
for col in 2 3 4 6; do
  numeric_bad accounts.tsv "$col" 2147483648 "wallet-over-int32-field-$col"
done
numeric_bad accounts.tsv 2 0001 wallet-noncanonical-leading-zero
numeric_bad accounts.tsv 3 999999999999999999999999 wallet-unbounded-expiry
numeric_bad members.tsv 8 2147483648 member-bank-over-int32
numeric_bad members.tsv 8 0001 member-bank-leading-zero
numeric_bad members.tsv 10 2147483648 member-updated-over-int32
numeric_bad rental-devices.tsv 3 2147483648 rental-lease-over-int32
numeric_bad rental-devices.tsv 3 0001 rental-lease-leading-zero
numeric_bad rental-devices.tsv 5 2147483648 rental-lastseen-over-int32
[ "$(fixture status | grep -Fc 'status=NON_AUTHORITATIVE_READ_ONLY')" -eq 1 ]
[ "$(snapshot)" = "$baseline" ]

# MIG-0736: these files cannot silently disappear from a purportedly
# safe migration source. Every case must refuse without altering balances,
# leases, member receipts, controller event history or account identifiers.
for name in member-revision member-events.tsv rental-events.tsv; do
  mv "$T/$name" "$T/$name.saved"
  refuse "missing-$name"
  mv "$T/$name.saved" "$T/$name"
done

printf 'bogus\n' > "$T/member-revision"
refuse corrupted-global-member-revision
printf '0\n' > "$T/member-revision"
refuse member-row-ahead-of-global
printf '2147483647\n' > "$T/member-revision"
refuse overflowing-member-revision
printf '1\n' > "$T/member-revision"

cp -p "$T/member-events.tsv" "$T/events.good"
printf 'bad\t100\talice\tadd\t10\n' >> "$T/member-events.tsv"
refuse truncated-member-event
cp -p "$T/events.good" "$T/member-events.tsv"
printf 'fixture:event:1\t100\talice\tadd\t10\t10\tfixture\t\n' >> "$T/member-events.tsv"
refuse duplicate-member-event
cp -p "$T/events.good" "$T/member-events.tsv"
# MIG-0743: a 10-digit paid amount may exceed signed 32-bit bounds even
# though earlier read-only source parsing accepted it as digits.
printf 'tampered:event:2\t100\talice\tadd\t2147483648\t2147483648\tfixture\t\n' >> "$T/member-events.tsv"
refuse overflow-member-paid-receipt
cp -p "$T/events.good" "$T/member-events.tsv"
printf 'tampered:event:2\t100\talice\ttransfer\t-2147483648\t10\tfixture\t100:bob:0\n' >> "$T/member-events.tsv"
refuse underflow-member-paid-delta
cp -p "$T/events.good" "$T/member-events.tsv"

# MIG-0744: this is the actual member-transfer receipt layout emitted by
# installed member.sh: from_balance:recipient:to_balance. A historical paid
# event for a deleted user/unknown transfer recipient is not safely
# importable from the six-file source set, even if its 8 TSV columns and
# amount are otherwise valid. Healthy legacy transfer remains admissible.
printf 'fixture:transfer:valid\t100\talice\ttransfer\t-4\t4\tfixture\t196:bob:4\n' >> "$T/member-events.tsv"
[ "$(fixture status | grep -Fc 'status=NON_AUTHORITATIVE_READ_ONLY')" -eq 1 ]
cp -p "$T/events.good" "$T/member-events.tsv"

# MIG-0745: real v1 zero-bank delete and later create can reuse a username
# while the previously paid receipt is retained. A current username alone
# must NOT make that old credit an admissible v2 identity. Model the new
# account revision as well so a rejection cannot be attributed to stale
# revision metadata. Every refusal must leave all six paid sources unchanged.
cp -p "$T/members.tsv" "$T/members.epoch.good"
printf '3\n' > "$T/member-revision"
awk -F '\t' 'BEGIN{OFS="\t"} $1=="alice" {$9=3} {print}' "$T/members.epoch.good" > "$T/members.tsv"
chmod 600 "$T/members.tsv"
printf 'admin:2:alice\t101\talice\tdelete\t0\t0\tfixture\t\n' >> "$T/member-events.tsv"
printf 'admin:3:alice\t102\talice\tcreate\t0\t0\tfixture\t\n' >> "$T/member-events.tsv"
refuse deleted-and-recreated-paid-username
# Even if the nonfinancial delete audit was trimmed, a remaining create
# that appears AFTER an older paid receipt must refuse.
cp -p "$T/events.good" "$T/member-events.tsv"
printf 'admin:3:alice\t102\talice\tcreate\t0\t0\tfixture\t\n' >> "$T/member-events.tsv"
refuse old-paid-event-before-recreated-create
cp -p "$T/members.epoch.good" "$T/members.tsv"
printf '1\n' > "$T/member-revision"
cp -p "$T/events.good" "$T/member-events.tsv"
# A historical transfer DESTINATION is also a financial identity reference,
# not merely an arbitrary current member with the matching name.
printf 'fixture:transfer:reused-target\t100\talice\ttransfer\t-4\t4\tfixture\t196:bob:4\n' >> "$T/member-events.tsv"
printf 'admin:2:bob\t101\tbob\tdelete\t0\t0\tfixture\t\n' >> "$T/member-events.tsv"
printf 'admin:3:bob\t102\tbob\tcreate\t0\t0\tfixture\t\n' >> "$T/member-events.tsv"
refuse reused-transfer-destination
cp -p "$T/events.good" "$T/member-events.tsv"
# Retained nonfinancial lifecycle rows without ANY paid reference for that
# member must not invalidate otherwise healthy six-file source diagnostics.
printf 'admin:2:bob\t101\tbob\tdelete\t0\t0\tfixture\t\n' >> "$T/member-events.tsv"
printf 'admin:3:bob\t102\tbob\tcreate\t0\t0\tfixture\t\n' >> "$T/member-events.tsv"
[ "$(fixture status | grep -Fc 'status=NON_AUTHORITATIVE_READ_ONLY')" -eq 1 ]
cp -p "$T/events.good" "$T/member-events.tsv"

printf 'fixture:orphan:credit\t100\tmissinguser\tadd\t10\t10\tfixture\t10\n' >> "$T/member-events.tsv"
refuse orphan-paid-member-credit
cp -p "$T/events.good" "$T/member-events.tsv"
printf 'fixture:orphan:transfer\t100\tmissinguser\ttransfer\t-4\t4\tfixture\t196:bob:4\n' >> "$T/member-events.tsv"
refuse orphan-transfer-source
cp -p "$T/events.good" "$T/member-events.tsv"
printf 'fixture:transfer:missing\t100\talice\ttransfer\t-4\t4\tfixture\t196:missinguser:4\n' >> "$T/member-events.tsv"
refuse orphan-transfer-destination
cp -p "$T/events.good" "$T/member-events.tsv"
printf 'fixture:transfer:invalid\t100\talice\ttransfer\t-4\t4\tfixture\t196:bob:2147483648\n' >> "$T/member-events.tsv"
refuse overflow-transfer-receipt-detail
cp -p "$T/events.good" "$T/member-events.tsv"
printf 'fixture:transfer:invalid\t100\talice\ttransfer\t-4\t4\tfixture\t196:bob:bogus\n' >> "$T/member-events.tsv"
refuse malformed-transfer-balance
cp -p "$T/events.good" "$T/member-events.tsv"

cp -p "$T/rental-events.tsv" "$T/rental-events.good"
printf 'r:fixture02\tdev01\t999999\t100\t\n' >> "$T/rental-events.tsv"
refuse unbound-paid-rental-receipt
cp -p "$T/rental-events.good" "$T/rental-events.tsv"
printf '%s\tdev01\t999999\t100\tp:2\n' "$paid_rental_event" >> "$T/rental-events.tsv"
refuse duplicate-paid-rental-receipt
cp -p "$T/rental-events.good" "$T/rental-events.tsv"
printf 'r:fixture03\tdev01\t999999\tnot-time\tp:2\n' >> "$T/rental-events.tsv"
refuse invalid-rental-receipt-timestamp
cp -p "$T/rental-events.good" "$T/rental-events.tsv"
# Current signed rental receipts are SHA256-lowercase, fixed 64 hex, and
# tied to an existing paid device. Readonly migration cannot import orphan
# or over-INT32 leases as apparently valid historic customer time.
printf 'r:short\tdev01\t999999\t100\tp:2\n' >> "$T/rental-events.tsv"
refuse short-rental-paid-event-identity
cp -p "$T/rental-events.good" "$T/rental-events.tsv"
printf 'r:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\tdev01\t999999\t100\tp:2\n' >> "$T/rental-events.tsv"
refuse noncanonical-uppercase-rental-event-identity
cp -p "$T/rental-events.good" "$T/rental-events.tsv"
printf 'r:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\tmissing-device\t999999\t100\tp:2\n' >> "$T/rental-events.tsv"
refuse orphan-paid-rental-device
cp -p "$T/rental-events.good" "$T/rental-events.tsv"
printf 'r:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\tdev01\t2147483648\t100\tp:2\n' >> "$T/rental-events.tsv"
refuse over-int32-paid-rental-lease
cp -p "$T/rental-events.good" "$T/rental-events.tsv"
printf 'r:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\tdev01\t999999\t2147483648\tp:2\n' >> "$T/rental-events.tsv"
refuse over-int32-paid-rental-timestamp
cp -p "$T/rental-events.good" "$T/rental-events.tsv"
[ "$(snapshot)" = "$baseline" ]

mv "$T/accounts.tsv" "$T/old-accounts"
ln -s "$T/old-accounts" "$T/accounts.tsv"
refuse symlink-money-store
rm "$T/accounts.tsv"; mv "$T/old-accounts" "$T/accounts.tsv"
printf 'PENDING\t100\n' > "$T/paid-state-uncertain"
refuse uncertain-payment
rm "$T/paid-state-uncertain"
rm "$T/.blaze-shadow-fixture-only"
refuse missing-marker

[ "$(snapshot)" = "$baseline" ] || {
  echo 'v2 shadow diagnostics unexpectedly changed final paid records' >&2; exit 1
}
[ ! -e "$T/v2-ledger.tsv" ] && [ ! -e "$T/v2-shadow-ledger" ]
echo 'MIG-0735 PASS: real installed read-only observer requires pre-existing safe money lock, rejects active writer, linked/missing/malformed locks, cutover and uncertainty; no money/secret/ACK output'
echo 'MIG-0736/0743/0744/0745/0746 PASS: readonly six-file money preflight rejects detected username reuse, oversized or noncanonical present balances/leases and corrupt receipts without source writes'
echo 'NOT PRODUCTION: no coherent financial migration or authenticated crash-atomic powercut ledger'
