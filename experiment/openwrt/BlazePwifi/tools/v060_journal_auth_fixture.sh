#!/bin/sh
# LEDGER-0636: synthetic signed controller envelope, NOT production signing.
# ROOT CONTROLLER SEQ EVENT OP SUBJECT TARGET UNITS NOW HMAC_SHA256_HEX
# This guard is *only* for a /tmp fixture, not the installed OpenWrt runtime.
# A production implementation needs constant-time verify, protected key storage
# and target-specific fsync/dirsync. This lab helper uses openssl CLI and is
# intentionally not shipped with openwrt/rootfs.
set -eu
[ "$#" -eq 10 ] || { echo "invalid signed fixture arguments" >&2; exit 2; }
root="$1"; controller="$2"; seq="$3"; event="$4"; op="$5"
subject="$6"; target="$7"; units="$8"; clock="$9"
shift 9
signature="$1"
root="$(CDPATH= cd -P "$root" 2>/dev/null && pwd -P)" ||
    { echo "invalid sandbox root" >&2; exit 2; }
case "$root" in /tmp/*|/var/tmp/*) ;; *) echo "synthetic sandbox only" >&2; exit 2;; esac
[ -f "$root/.blaze-v2-fixture-only" ] && [ ! -L "$root/.blaze-v2-fixture-only" ] &&
    grep -qx 'BLAZE-V2-SYNTHETIC-ONLY' "$root/.blaze-v2-fixture-only" ||
    { echo "synthetic root marker required" >&2; exit 2; }
for name in "$controller" "$subject"; do
    printf '%s\n' "$name" | LC_ALL=C grep -Eq '^[A-Za-z][A-Za-z0-9_.-]{0,31}$' ||
        { echo "invalid controller/account name" >&2; exit 2; }
done
if [ "$target" != '-' ]; then
    printf '%s\n' "$target" | LC_ALL=C grep -Eq '^[A-Za-z][A-Za-z0-9_.-]{0,31}$' ||
        { echo "invalid destination" >&2; exit 2; }
fi
case "$op" in AM|SM|TM|LR) ;; *) echo "invalid paid operation" >&2; exit 2;; esac
case "$seq:$units:$clock" in *[!0-9:]*|'') echo "invalid numeric envelope" >&2; exit 2;; esac
case "$seq" in 0*|'') echo "noncanonical controller sequence" >&2; exit 2;; esac
[ "$seq" -gt 0 ] 2>/dev/null && [ "$seq" -le 100000000 ] 2>/dev/null &&
[ "$units" -gt 0 ] 2>/dev/null && [ "$units" -le 31536000 ] 2>/dev/null &&
[ "$clock" -ge 0 ] 2>/dev/null && [ "$clock" -le 2000000000 ] 2>/dev/null ||
    { echo "numeric envelope out of range" >&2; exit 2; }
[ "$event" = "$controller:$seq" ] ||
    { echo "receipt ID does not bind controller sequence" >&2; exit 2; }
printf '%s\n' "$signature" | LC_ALL=C grep -Eq '^[a-f0-9]{64}$' ||
    { echo "signature is not canonical lowercase HMAC-SHA256" >&2; exit 2; }

# Keys are fake local sandbox material and never appear in stdout. Reject a
# symlinked, hardlinked, group-readable or malformed controller key registry.
keys="$root/controller-keys.tsv"
[ -f "$keys" ] && [ -r "$keys" ] && [ ! -L "$keys" ] ||
    { echo "missing fixture key registry" >&2; exit 3; }
[ "$(stat -c '%a' "$keys" 2>/dev/null)" = 600 ] &&
[ "$(stat -c '%h' "$keys" 2>/dev/null)" = 1 ] ||
    { echo "fixture registry not private regular file" >&2; exit 3; }
secret="$(awk -F '\t' -v controller="$controller" '
  NF!=2 || $1 !~ /^[A-Za-z][A-Za-z0-9_.-]*$/ ||
    length($1)>32 || $2 !~ /^[a-f0-9]{64}$/ {invalid=1}
  $1==controller {found++; secret=$2}
  END {if (invalid || found!=1) exit 4; print secret}
' "$keys")" || { echo "ambiguous or malformed fixture key registry" >&2; exit 3; }
[ "${#secret}" -eq 64 ] || { echo "no controller key" >&2; exit 3; }
command -v openssl >/dev/null 2>&1 ||
    { echo "OpenSSL synthetic verifier missing: no authenticated operations" >&2; exit 3; }

# Canonical, domain-separated, tab-delimited fields are all validated to
# exclude tabs/newlines. HMAC prevents a different enrolled controller,
# destination, amount, timestamp or sequence from forging the same envelope.
# NOTE: openssl -macopt hexkey exposes *synthetic* key material in argv.
# This mechanism is not allowed to authorize production coin credits.
expected="$(printf 'BLAZE-V2-AUTH-FIXTURE/1\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$controller" "$seq" "$event" "$op" "$subject" "$target" "$units" "$clock" |
    openssl dgst -sha256 -mac HMAC -macopt "hexkey:$secret" -r 2>/dev/null |
    awk '{print $1}')" || { echo "synthetic HMAC verification failed" >&2; exit 3; }
[ "${#expected}" -eq 64 ] && [ "$signature" = "$expected" ] ||
    { echo "authenticated controller envelope mismatch" >&2; exit 5; }
unset secret
exec sh "$(dirname "$0")/v060_journal_fixture.sh" \
    "$root" "$controller" "$seq" "$event" "$op" "$subject" "$target" "$units" "$clock"
