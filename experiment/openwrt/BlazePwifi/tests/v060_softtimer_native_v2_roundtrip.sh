#!/bin/sh
# PAY-0715: C# SoftTimer-contract → real C HMAC/fsync native fixture roundtrip.
# OFF-DEVICE ONLY. No customer controller keys, account records or migrations.
# One canonical signed sequence across two languages; no v1 fallback.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
REPO="$(CDPATH= cd -- "$ROOT/../../.." && pwd)"
PROJ="$REPO/experiment/windows/BlazePisonet-SoftTimer/tests/V2NativeEnvelopeContract/V2NativeEnvelopeContract.csproj"
T="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
chmod 700 "$T"
command -v cc >/dev/null
command -v dotnet >/dev/null
dotnet build "$PROJ" -c Release --nologo -warnaserror >"$T/dotnet-build.txt" 2>&1 || {
  cat "$T/dotnet-build.txt" >&2; exit 1;
}
DLL="${PROJ%/*}/bin/Release/net8.0/V2NativeEnvelopeContract.dll"
[ -s "$DLL" ]
dotnet "$DLL" --selftest
cc -std=c11 -Wall -Wextra -Werror -O2 -DBLAZE_FIXTURE_ONLY \
  "$ROOT/tools/v060_journal_authority_native.c" -lcrypto -o "$T/native"
chmod 700 "$T/native"
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$T/.blaze-v2-fixture-only"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' > "$T/ledger.tsv"
sum="$(sha256sum "$T/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$sum" >> "$T/ledger.tsv"
key1=3333333333333333333333333333333333333333333333333333333333333333
key2=4444444444444444444444444444444444444444444444444444444444444444
printf 'ctrlOne\t%s\nctrlTwo\t%s\n' "$key1" "$key2" > "$T/controller-keys.tsv"
chmod 600 "$T/.blaze-v2-fixture-only" "$T/controller-keys.tsv" "$T/ledger.tsv"
balance() { awk -F '\t' -v u="$1" '$1=="A"&&$2==u {print $3;exit}' "$T/ledger.tsv"; }
hash() { sha256sum "$T/ledger.tsv" | cut -d' ' -f1; }
emit() { dotnet "$DLL" --emit "$@"; }
# Tokens originate in strict test-only ASCII/decimal allowlisted fixture.
# Word-splitting is intentional solely for the synthetic native CLI contract.
first="$(emit ctrlOne 1 AM alice - 40 1000 "$key1")"
set -- $first
[ "$#" -eq 9 ]
[ "$9" != "$key1" ]
[ "$("$T/native" "$T" "$@")" = "$(printf 'COMMIT\t140')" ]
stable="$(hash)"
[ "$("$T/native" "$T" "$@")" = "$(printf 'REPLAY\t140')" ]
[ "$(hash)" = "$stable" ]
# A correctly signed duplicate sequence with a different amount must fail.
collision="$(emit ctrlOne 1 AM alice - 41 1000 "$key1")"
set -- $collision
if "$T/native" "$T" "$@" > "$T/rejected" 2>"$T/reason"; then
  echo 'PAY-0715 accepted same-sequence amount collision' >&2; exit 1
fi
[ ! -s "$T/rejected" ] && [ "$(hash)" = "$stable" ]
grep -Fq 'controller sequence payload collision' "$T/reason"
second="$(emit ctrlOne 2 TM alice bob 30 1000 "$key1")"
set -- $second
if "$T/native" "$T" "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" \
  0000000000000000000000000000000000000000000000000000000000000000 \
  > "$T/rejected" 2>"$T/reason"; then
  echo 'PAY-0715 accepted unauthenticated native transfer' >&2; exit 1
fi
[ ! -s "$T/rejected" ] && [ "$(hash)" = "$stable" ]
# Before authority rename, no money or receipt must commit.
if BLAZE_V2_NATIVE_TEST_FAULT=before-rename "$T/native" "$T" "$@" >"$T/rejected" 2>"$T/reason"; then
  echo 'PAY-0715 precommit fsync fault emitted ACK' >&2; exit 1
fi
[ ! -s "$T/rejected" ] && [ "$(hash)" = "$stable" ]
# PAY-0773: the interrupted stage is ambiguous. An authentic .NET-signed
# retransmission must be denied while that file remains; only this isolated
# disposable fixture cleans its own staged bytes after verifying no ACK.
pending="$(find "$T" -maxdepth 1 -name '.v2-next-*' -type f -print -quit)"
[ -n "$pending" ] || { echo 'pre-rename fault left no native stage' >&2; exit 1; }
if "$T/native" "$T" "$@" > "$T/rejected" 2>"$T/reason"; then
  echo 'PAY-0773 SoftTimer signed transfer bypassed unresolved native stage' >&2; exit 1
fi
grep -Fq 'unfinished native stage requires operator reconciliation' "$T/reason"
[ ! -s "$T/rejected" ] && [ "$(hash)" = "$stable" ]
rm "$pending"
[ -z "$(find "$T" -maxdepth 1 -name '.v2-next-*' -print -quit)" ]
# After authority rename but before directory fsync, no paid ACK; exact
# retransmission must replay rather than duplicate balance or receipt.
if BLAZE_V2_NATIVE_TEST_FAULT=after-rename-before-dir-fsync "$T/native" "$T" "$@" >"$T/rejected" 2>"$T/reason"; then
  echo 'PAY-0715 uncertain transfer emitted ACK' >&2; exit 1
fi
[ ! -s "$T/rejected" ]
grep -Fq UNCERTAIN "$T/reason"
[ "$(balance alice):$(balance bob)" = '110:230' ]
committed="$(hash)"
[ "$("$T/native" "$T" "$@")" = "$(printf 'REPLAY\t110')" ]
[ "$committed" = "$(hash)" ]
[ "$(( $(balance alice) + $(balance bob) ))" -eq 340 ]
# Different authenticated controller/secret and independent sequence floor.
third="$(emit ctrlTwo 1 SM bob - 5 1000 "$key2")"
set -- $third
[ "$("$T/native" "$T" "$@")" = "$(printf 'COMMIT\t225')" ]
[ "$(balance alice):$(balance bob)" = 110:225 ]
[ "$(awk -F '\t' '$1=="C" && $2=="ctrlOne" {print $3}' "$T/ledger.tsv")" = 2 ]
[ "$(awk -F '\t' '$1=="C" && $2=="ctrlTwo" {print $3}' "$T/ledger.tsv")" = 1 ]
[ "$("$T/native" "$T" "$@")" = "$(printf 'REPLAY\t225')" ]
[ ! -e "$ROOT/openwrt/rootfs/usr/sbin/v2-native-fixture" ]
[ ! -e "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/v060_journal_authority_native.c" ]
echo 'PAY-0715 PASS: .NET8 SoftTimer fixture → C-native HMAC/fsync journal, authenticated COMMIT/REPLAY, collisions, lost ACK, independent controllers and transfer conservation'
echo 'NOT PRODUCTION: no signed SoftTimer shipping route, secure sequence store, v1 migration, target powercut or independent rollback witness'
