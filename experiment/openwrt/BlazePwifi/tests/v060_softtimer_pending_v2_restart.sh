#!/bin/sh
# PAY-0716: cross-process .NET controller pending state to C native journal.
# Disposable synthetic /tmp only: no production controller keys or migration.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
REPO="$(CDPATH= cd -- "$ROOT/../../.." && pwd)"
PROJ="$REPO/experiment/windows/BlazePisonet-SoftTimer/tests/V2PendingSequenceLab/V2PendingSequenceLab.csproj"
SIGNER="$REPO/experiment/windows/BlazePisonet-SoftTimer/tests/V2NativeEnvelopeContract/V2NativeEnvelopeContract.csproj"
T="$(mktemp -d /tmp/blaze-v2-pending-XXXXXX)"
N="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
trap 'rm -rf "$T" "$N"' EXIT HUP INT TERM
umask 077
chmod 700 "$T" "$N"
printf 'BLAZE-V2-PENDING-SYNTHETIC-ONLY\n' >"$T/.blaze-v2-pending-synthetic-only"
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' >"$N/.blaze-v2-fixture-only"
command -v dotnet >/dev/null
command -v cc >/dev/null
dotnet build "$PROJ" -c Release --nologo -warnaserror >"$T/build.log" 2>&1 ||
  { cat "$T/build.log" >&2; exit 1; }
dotnet build "$SIGNER" -c Release --nologo -warnaserror >"$T/signer-build.log" 2>&1 ||
  { cat "$T/signer-build.log" >&2; exit 1; }
APP="${PROJ%/*}/bin/Release/net8.0/V2PendingSequenceLab.dll"
EMIT="${SIGNER%/*}/bin/Release/net8.0/V2NativeEnvelopeContract.dll"
test -s "$APP"
test -s "$EMIT"
cc -std=c11 -Wall -Wextra -Werror -O2 -DBLAZE_FIXTURE_ONLY \
  "$ROOT/tools/v060_journal_authority_native.c" -lcrypto -o "$N/native"
key=3333333333333333333333333333333333333333333333333333333333333333
printf 'ctrlOne\t%s\n' "$key" >"$N/controller-keys.tsv"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' >"$N/ledger.tsv"
checksum="$(sha256sum "$N/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$checksum" >>"$N/ledger.tsv"
chmod 600 "$T/.blaze-v2-pending-synthetic-only" "$N/.blaze-v2-fixture-only" \
  "$N/controller-keys.tsv" "$N/ledger.tsv"
lab() { dotnet "$APP" "$@"; }
deny() {
  if "$@" >"$T/refuse.stdout" 2>"$T/refuse.stderr"; then
    echo 'PAY-0716 unexpectedly accepted unsafe controller state' >&2; exit 1
  fi
  [ ! -s "$T/refuse.stdout" ] || exit 1
}
hash_state() { sha256sum "$T/sequence.state" | cut -d' ' -f1; }
balance() { awk -F '\t' -v u="$1" '$1=="A"&&$2==u {print $3}' "$N/ledger.tsv"; }
# Missing state MUST NEVER reset to sequence zero.
deny lab --pending "$T"
[ "$(lab --init "$T" ctrlOne)" = INITIALIZED ]
deny lab --init "$T" ctrlOne
[ "$(lab --pending "$T")" = EMPTY ]
initial="$(hash_state)"
# Pre-commit failure: no new sequence allocated and no pending event.
deny env BLAZE_V2_PENDING_FAULT=before-rename dotnet "$APP" \
  --reserve "$T" AM alice - 40 1000
[ "$initial" = "$(hash_state)" ]
[ "$(lab --pending "$T")" = EMPTY ]
# Committed reservation whose response to sender was lost.
deny env BLAZE_V2_PENDING_FAULT=after-rename dotnet "$APP" \
  --reserve "$T" AM alice - 40 1000
req="$(lab --pending "$T")"
[ "$req" = 'ctrlOne 1 AM alice - 40 1000' ]
[ "$(lab --reserve "$T" AM alice - 40 1000)" = "$req" ]
reserved="$(hash_state)"
deny lab --reserve "$T" AM alice - 41 1000
deny lab --reserve "$T" AM bob - 40 1000
deny lab --reserve "$T" TM alice bob 40 1000
deny lab --reserve "$T" AM alice - 40 1001
[ "$reserved" = "$(hash_state)" ]
# Another dotnet process signs exact persisted pending sequence and payload.
set -- $req
signed="$(dotnet "$EMIT" --emit "$@" "$key")"
set -- $signed
[ "$#" -eq 9 ]
native_ack="$("$N/native" "$N" "$@" --authenticated-ack)"
expected_ack="$(dotnet "$EMIT" --ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 "$key")"
[ "$native_ack" = "$expected_ack" ]
[ "$(printf '%s' "$native_ack" | awk -F '\t' '{print NF}')" -eq 7 ]
[ "$(balance alice)" = 140 ]
# PAY-0717: raw/fabricated/journal-replayed response MUST NOT clear pending.
deny lab --ack "$T" 1 AM alice - 40 1000 "$(printf 'COMMIT\t140')"
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$(printf 'COMMIT\t140')" "$key"
deny lab --ack-auth "$T" 1 AM alice - 41 1000 "$native_ack" "$key"
deny lab --ack-auth "$T" 2 AM alice - 40 1000 "$native_ack" "$key"
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$native_ack" \
  4444444444444444444444444444444444444444444444444444444444444444
fake_other="$(dotnet "$EMIT" --ack-fixture ctrlOther 1 AM alice - 40 1000 COMMIT 140 "$key")"
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$fake_other" "$key"
fake_amount="$(dotnet "$EMIT" --ack-fixture ctrlOne 1 AM alice - 41 1000 COMMIT 140 "$key")"
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$fake_amount" "$key"
fake_target="$(dotnet "$EMIT" --ack-fixture ctrlOne 1 TM alice bob 40 1000 COMMIT 140 "$key")"
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$fake_target" "$key"
fake_timestamp="$(dotnet "$EMIT" --ack-fixture ctrlOne 1 AM alice - 40 1001 COMMIT 140 "$key")"
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$fake_timestamp" "$key"
fake_result="$(printf '%s' "$native_ack" | sed 's/\t140\t/\t141\t/')"
[ "$fake_result" != "$native_ack" ]
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$fake_result" "$key"
fake_outcome="$(printf '%s' "$native_ack" | sed 's/ACKV1\tCOMMIT\t/ACKV1\tREPLAY\t/')"
[ "$fake_outcome" != "$native_ack" ]
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$fake_outcome" "$key"
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "OK" "$key"
[ "$reserved" = "$(hash_state)" ]
[ "$(lab --ack-auth "$T" 1 AM alice - 40 1000 "$native_ack" "$key")" = ACKED ]
[ "$(lab --pending "$T")" = EMPTY ]
req="$(lab --reserve "$T" TM alice bob 30 1000)"
[ "$req" = 'ctrlOne 2 TM alice bob 30 1000' ]
set -- $req
signed="$(dotnet "$EMIT" --emit "$@" "$key")"
set -- $signed
# Journal post-rename but pre-dir-fsync uncertainty: NO ACK.
if BLAZE_V2_NATIVE_TEST_FAULT=after-rename-before-dir-fsync \
     "$N/native" "$N" "$@" --authenticated-ack >"$T/native-ack" 2>"$T/native-error"; then
  echo 'PAY-0716 uncertain journal incorrectly ACKed transfer' >&2; exit 1
fi
[ ! -s "$T/native-ack" ]
grep -Fq UNCERTAIN "$T/native-error"
[ "$(balance alice):$(balance bob)" = 110:230 ]
[ "$(lab --pending "$T")" = "$req" ]
[ "$(lab --reserve "$T" TM alice bob 30 1000)" = "$req" ]
native_ack="$("$N/native" "$N" "$@" --authenticated-ack)"
expected_ack="$(dotnet "$EMIT" --ack-fixture ctrlOne 2 TM alice bob 30 1000 REPLAY 110 "$key")"
[ "$native_ack" = "$expected_ack" ]
# A recorded receipt from the earlier transaction cannot ACK this transfer.
deny lab --ack-auth "$T" 2 TM alice bob 30 1000 "$fake_outcome" "$key"
[ "$(lab --ack-auth "$T" 2 TM alice bob 30 1000 "$native_ack" "$key")" = ACKED ]
[ "$(lab --pending "$T")" = EMPTY ]
[ "$(( $(balance alice) + $(balance bob) ))" -eq 340 ]
[ "$(lab --reserve "$T" AM alice - 5 1000)" = 'ctrlOne 3 AM alice - 5 1000' ]
# Corrupted persisted state blocks all new reservations instead of seq reuse.
cp "$T/sequence.state" "$T/good.state"
printf 'garbled\n' >>"$T/sequence.state"
deny lab --pending "$T"
deny lab --reserve "$T" AM alice - 5 1000
cp "$T/good.state" "$T/sequence.state"; chmod 600 "$T/sequence.state"
[ "$(lab --pending "$T")" = 'ctrlOne 3 AM alice - 5 1000' ]
deny lab --pending "/etc/blazepwifi/state"
mv "$T/.blaze-v2-pending-synthetic-only" "$T/hidden-marker"
deny lab --pending "$T"
mv "$T/hidden-marker" "$T/.blaze-v2-pending-synthetic-only"
[ "$(lab --pending "$T")" = 'ctrlOne 3 AM alice - 5 1000' ]
[ ! -e "$ROOT/openwrt/rootfs/usr/bin/V2PendingSequenceLab" ]
echo 'PAY-0716/PAY-0717 PASS: cross-process monotonic reserve, pending signed identity, C journal lost ACK/replay, collision, corruption and no reset'
echo 'NOT PRODUCTION: no provisioned production server ACK identity, flash powercut, Windows directory fsync, independent rollback witness or shipped v2 sender'
