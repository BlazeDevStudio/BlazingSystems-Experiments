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
# PAY-0718: independently provisioned synthetic server ACK key registry.
# Command MAC key is 33..; ACK MAC key 55..; a revoked fixture key is 66...
server_key=5555555555555555555555555555555555555555555555555555555555555555
revoked_key=6666666666666666666666666666666666666666666666666666666666666666
rotated_key=7777777777777777777777777777777777777777777777777777777777777777
printf 'serverA\tctrlOne\tactive\t%s\nserverOld\tctrlOne\trevoked\t%s\n' \
  "$server_key" "$revoked_key" >"$N/server-ack-keys.tsv"
cp "$N/server-ack-keys.tsv" "$T/trusted-server-ack-keys.tsv"
chmod 600 "$N/server-ack-keys.tsv" "$T/trusted-server-ack-keys.tsv"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' >"$N/ledger.tsv"
checksum="$(sha256sum "$N/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$checksum" >>"$N/ledger.tsv"
chmod 600 "$T/.blaze-v2-pending-synthetic-only" "$N/.blaze-v2-fixture-only" \
  "$N/controller-keys.tsv" "$N/ledger.tsv" "$N/server-ack-keys.tsv"
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
native_ack="$("$N/native" "$N" "$@" --server-ack-v2)"
expected_ack="$(dotnet "$EMIT" --server-ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 serverA "$server_key")"
[ "$native_ack" = "$expected_ack" ]
# ACKV2 adds server KEY_ID, hence eight canonical fields (not ACKV1 seven).
[ "$(printf '%s' "$native_ack" | awk -F '\t' '{print NF}')" -eq 8 ]
[ "$(balance alice)" = 140 ]
# PAY-0718: no unsigned or controller-key ACK fallback is accepted.
legacy="$(dotnet "$EMIT" --ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 "$key")"
deny lab --ack "$T" 1 AM alice - 40 1000 "$(printf 'COMMIT\t140')"
deny lab --ack-auth "$T" 1 AM alice - 40 1000 "$legacy" "$key"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$(printf 'COMMIT\t140')"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$legacy"
deny lab --ack-server "$T" 1 AM alice - 41 1000 "$native_ack"
deny lab --ack-server "$T" 2 AM alice - 40 1000 "$native_ack"
forged_controller="$(dotnet "$EMIT" --server-ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 serverA "$key")"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$forged_controller"
fake_other="$(dotnet "$EMIT" --server-ack-fixture ctrlOther 1 AM alice - 40 1000 COMMIT 140 serverA "$server_key")"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$fake_other"
fake_amount="$(dotnet "$EMIT" --server-ack-fixture ctrlOne 1 AM alice - 41 1000 COMMIT 140 serverA "$server_key")"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$fake_amount"
fake_target="$(dotnet "$EMIT" --server-ack-fixture ctrlOne 1 TM alice bob 40 1000 COMMIT 140 serverA "$server_key")"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$fake_target"
fake_timestamp="$(dotnet "$EMIT" --server-ack-fixture ctrlOne 1 AM alice - 40 1001 COMMIT 140 serverA "$server_key")"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$fake_timestamp"
fake_result="$(printf '%s' "$native_ack" | sed 's/\t140\t/\t141\t/')"
[ "$fake_result" != "$native_ack" ]
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$fake_result"
fake_outcome="$(printf '%s' "$native_ack" | sed 's/ACKV2\tCOMMIT\t/ACKV2\tREPLAY\t/')"
[ "$fake_outcome" != "$native_ack" ]
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$fake_outcome"
fake_unknown="$(dotnet "$EMIT" --server-ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 serverUnknown "$server_key")"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$fake_unknown"
fake_revoked="$(dotnet "$EMIT" --server-ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 serverOld "$revoked_key")"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$fake_revoked"
# Rotation/revocation changes cannot silently clear a persisted pending payment.
cp "$T/trusted-server-ack-keys.tsv" "$T/trust-original"
printf 'serverA\tctrlOne\trevoked\t%s\nserverNew\tctrlOne\tactive\t%s\n' \
 "$server_key" "$rotated_key" > "$T/trusted-server-ack-keys.tsv"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$native_ack"
printf 'serverA\tctrlOne\tactive\t%s\nserverNew\tctrlOne\tactive\t%s\n' \
 "$server_key" "$rotated_key" > "$T/trusted-server-ack-keys.tsv"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$native_ack"
cp "$T/trust-original" "$T/trusted-server-ack-keys.tsv"
# Bad registry, missing trust, symlink, or unprivate metadata fail closed.
printf 'not-a-registry\n' > "$T/trusted-server-ack-keys.tsv"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$native_ack"
cp "$T/trust-original" "$T/trusted-server-ack-keys.tsv"
mv "$T/trusted-server-ack-keys.tsv" "$T/trust-saved"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$native_ack"
ln -s "$T/trust-saved" "$T/trusted-server-ack-keys.tsv"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$native_ack"
rm "$T/trusted-server-ack-keys.tsv"
mv "$T/trust-saved" "$T/trusted-server-ack-keys.tsv"
chmod 644 "$T/trusted-server-ack-keys.tsv"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "$native_ack"
chmod 600 "$T/trusted-server-ack-keys.tsv"
deny lab --ack-server "$T" 1 AM alice - 40 1000 "OK"
[ "$reserved" = "$(hash_state)" ]
[ "$(lab --ack-server "$T" 1 AM alice - 40 1000 "$native_ack")" = ACKED ]
[ "$(lab --pending "$T")" = EMPTY ]
req="$(lab --reserve "$T" TM alice bob 30 1000)"
[ "$req" = 'ctrlOne 2 TM alice bob 30 1000' ]
set -- $req
signed="$(dotnet "$EMIT" --emit "$@" "$key")"
set -- $signed
# Journal post-rename but pre-dir-fsync uncertainty: NO ACK.
if BLAZE_V2_NATIVE_TEST_FAULT=after-rename-before-dir-fsync \
     "$N/native" "$N" "$@" --server-ack-v2 >"$T/native-ack" 2>"$T/native-error"; then
  echo 'PAY-0716 uncertain journal incorrectly ACKed transfer' >&2; exit 1
fi
[ ! -s "$T/native-ack" ]
grep -Fq UNCERTAIN "$T/native-error"
[ "$(balance alice):$(balance bob)" = 110:230 ]
[ "$(lab --pending "$T")" = "$req" ]
[ "$(lab --reserve "$T" TM alice bob 30 1000)" = "$req" ]
native_ack="$("$N/native" "$N" "$@" --server-ack-v2)"
expected_ack="$(dotnet "$EMIT" --server-ack-fixture ctrlOne 2 TM alice bob 30 1000 REPLAY 110 serverA "$server_key")"
[ "$native_ack" = "$expected_ack" ]
# A recorded receipt from the earlier transaction cannot ACK this transfer.
deny lab --ack-server "$T" 2 TM alice bob 30 1000 "$fake_outcome"
[ "$(lab --ack-server "$T" 2 TM alice bob 30 1000 "$native_ack")" = ACKED ]
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
# Server signing trust must be present BEFORE native mutation of seq3.
set -- $(lab --pending "$T")
signed="$(dotnet "$EMIT" --emit "$@" "$key")"
set -- $signed
ledger_before="$(sha256sum "$N/ledger.tsv")"
mv "$N/server-ack-keys.tsv" "$N/server-keys-saved"
if "$N/native" "$N" "$@" --server-ack-v2 >"$T/unsafe-out" 2>"$T/unsafe-err"; then
  echo 'PAY-0718 native committed without server trust' >&2; exit 1
fi
[ ! -s "$T/unsafe-out" ]
[ "$ledger_before" = "$(sha256sum "$N/ledger.tsv")" ]
mv "$N/server-keys-saved" "$N/server-ack-keys.tsv"
# The command key may NEVER double as the ACK server signing key.
cp "$N/server-ack-keys.tsv" "$N/server-keys-good"
printf 'serverA\tctrlOne\tactive\t%s\n' "$key" >"$N/server-ack-keys.tsv"
if "$N/native" "$N" "$@" --server-ack-v2 >"$T/unsafe-out" 2>"$T/unsafe-err"; then
  echo 'PAY-0718 native reused controller key for server ACK' >&2; exit 1
fi
[ "$ledger_before" = "$(sha256sum "$N/ledger.tsv")" ]
cp "$N/server-keys-good" "$N/server-ack-keys.tsv"
deny lab --pending "/etc/blazepwifi/state"
mv "$T/.blaze-v2-pending-synthetic-only" "$T/hidden-marker"
deny lab --pending "$T"
mv "$T/hidden-marker" "$T/.blaze-v2-pending-synthetic-only"
[ "$(lab --pending "$T")" = 'ctrlOne 3 AM alice - 5 1000' ]
[ ! -e "$ROOT/openwrt/rootfs/usr/bin/V2PendingSequenceLab" ]
echo 'PAY-0718 PASS: cross-process monotonic reserve, pending signed identity, C journal lost ACK/replay, collision, corruption and no reset'
echo 'NOT PRODUCTION: no public-verifiable provisioned server trust, flash powercut, Windows directory fsync, independent rollback witness or shipped v2 sender'
