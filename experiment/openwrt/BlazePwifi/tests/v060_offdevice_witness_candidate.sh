#!/bin/sh
# WITNESS-0738: actual SQLite FULL-sync cross-process durable candidate.
# Private /tmp data and synthetic key ONLY; no target, network or ACKP1.
set -eu
SRC="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)/tools/v060_offdevice_witness_candidate.py"
LAB="$(mktemp -d /tmp/blaze-witness0738-XXXXXXXX)" || exit 1
trap 'rm -rf "$LAB"' EXIT HUP INT TERM
chmod 700 "$LAB"; umask 077
printf 'BLAZE-WITNESS-CANDIDATE-NOT-HARDWARE-ATTESTED\n' >"$LAB/.witness-candidate-only"
printf '%064d\n' 0 | sed 's/0/1/g' >"$LAB/secret.hex"
chmod 600 "$LAB/.witness-candidate-only" "$LAB/secret.hex"
A="$(printf '%064d' 0 | tr 0 a)"
B="$(printf '%064d' 0 | tr 0 b)"
C="$(printf '%064d' 0 | tr 0 c)"
N1=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
N2=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
N3=cccccccccccccccccccccccccccccccc
sign() {
  python3 - "$@" <<'PY'
import sys,hmac,hashlib
msg=("BLAZE-WITNESS-CANDIDATE/1\t"+"\t".join(sys.argv[1:])+"\n").encode("ascii")
print(hmac.new(bytes.fromhex("11"*32),msg,hashlib.sha256).hexdigest())
PY
}
run() {
  cmd="$1"; shift
  auth="$(sign "$cmd" "$@")"
  python3 "$SRC" "$LAB" "$cmd" "$@" "$auth"
}
assert_json() {
  expected="$1"; shift
  # WITNESS-0740: independently verify ALL candidate transaction replies
  # against their exact request; preserve merged WITNESS-0739 STATUS/1 MAC.
  python3 -c '
import json,sys,hashlib,hmac
j=json.loads(sys.stdin.read())
expected,command=sys.argv[1:3]
args=sys.argv[3:]
assert j["state"]==expected,(j,expected)
assert j["schema"]=="BLAZE-WITNESS-CANDIDATE/1"
request=("BLAZE-WITNESS-CANDIDATE/1\t"+command+"\t"+"\t".join(args)+"\n").encode("ascii")
request_hash=hashlib.sha256(request).hexdigest()
assert j["request_sha256"]==request_hash,"response not bound to request"
mac=j.pop("response_mac")
serialized=json.dumps(j,sort_keys=True,separators=(",",":")).encode("ascii")
key=bytes.fromhex("11"*32)
if command=="status":
    assert j["reply_schema"]=="BLAZE-WITNESS-CANDIDATE-STATUS/1"
    assert j["response_challenge"]==args[1],"stale status challenge"
    payload=b"BLAZE-WITNESS-CANDIDATE-STATUS/1\n"+serialized+b"\n"
else:
    assert j["reply_schema"]=="BLAZE-WITNESS-CANDIDATE-TRANSACTION-REPLY/1"
    assert "response_challenge" not in j
    payload=(b"BLAZE-WITNESS-CANDIDATE-TRANSACTION-REPLY/1\t"+
             request_hash.encode("ascii")+b"\t"+serialized+b"\n")
expected_mac=hmac.new(key,payload,hashlib.sha256).hexdigest()
assert hmac.compare_digest(mac,expected_mac),"unauthenticated transaction reply"
for field in ("paid_ack_authorized","independent_monotonic_witness_verified",
              "financial_migration_authorized","customer_install_authorized"):
    assert j[field] is False,(field,j)
' "$expected" "$@"
}
deny() {
  name="$1"; shift
  rc=0
  "$@" >"$LAB/out" 2>"$LAB/err" || rc=$?
  [ "$rc" -ne 0 ] && [ ! -s "$LAB/out" ] &&
    grep -Fq 'NO PAID ACK' "$LAB/err" || {
      echo "WITNESS-0738 FAIL: $name unexpectedly accepted" >&2; exit 1
    }
}
crash() {
  stage="$1"; shift
  rc=0
  BLAZE_WITNESS0738_TEST_FAULT="$stage" run "$@" >"$LAB/out" 2>"$LAB/err" || rc=$?
  [ "$rc" -eq 73 ] && [ ! -s "$LAB/out" ] || {
    echo "WITNESS-0738 FAIL: fault $stage did not crash safely (rc=$rc)" >&2; exit 1
  }
}
run init device01 1 1 "$A" | assert_json GENESIS_CANDIDATE_ONLY init device01 1 1 "$A"
deny genesis-reset run init device01 1 1 "$A"
run status device01 "$N3" | assert_json OBSERVED_CANDIDATE_ONLY status device01 "$N3"
# A captured authenticated status is NOT valid for another challenge; a
# tampered paid gate or floor is NOT protected by the original MAC.
run status device01 "$N1" > "$LAB/status-first.json"
python3 - "$LAB/status-first.json" "$N1" "$N3" <<'PY'
import json,sys,hashlib,hmac
old=json.load(open(sys.argv[1],encoding="utf8"))
def check(reply, nonce):
    if reply.get("response_challenge") != nonce:
        return False
    supplied=reply.get("response_mac")
    body={k:v for k,v in reply.items() if k!="response_mac"}
    msg=(b"BLAZE-WITNESS-CANDIDATE-STATUS/1\n" +
         json.dumps(body,sort_keys=True,separators=(",",":")).encode() + b"\n")
    return isinstance(supplied,str) and hmac.compare_digest(
        supplied,hmac.new(bytes.fromhex("11"*32),msg,hashlib.sha256).hexdigest())
assert check(old,sys.argv[2]),"fresh authenticated response rejected"
assert not check(old,sys.argv[3]),"replayed challenge accepted"
for key,bad in (("witness_revision",999),("paid_ack_authorized",True),
                ("pending_reconciliation",True),("witness_digest","0"*64)):
    altered=dict(old); altered[key]=bad
    assert not check(altered,sys.argv[2]),f"tampered {key} accepted"
PY
run prepare device01 1 1 "$A" 2 "$B" "$N1" | assert_json PREPARED_NOT_COMMITTED prepare device01 1 1 "$A" 2 "$B" "$N1"
run status device01 "$N3" | assert_json PENDING_RECONCILIATION status device01 "$N3"
deny conflicting-prepare run prepare device01 1 1 "$A" 2 "$C" "$N2"
deny mismatched-finalize run finalize device01 1 2 "$B" "$N2"
crash before_finalize_commit finalize device01 1 2 "$B" "$N1"
run status device01 "$N3" | assert_json PENDING_RECONCILIATION status device01 "$N3"
run finalize device01 1 2 "$B" "$N1" | assert_json FINALIZED_CANDIDATE_NO_PAID_ACK finalize device01 1 2 "$B" "$N1"
run finalize device01 1 2 "$B" "$N1" | assert_json ALREADY_FINALIZED_NO_PAID_ACK finalize device01 1 2 "$B" "$N1"
# A post-commit lost reply is NOT permission for an arbitrary second advance.
run prepare device01 1 1 "$A" 2 "$B" "$N1" | assert_json ALREADY_FINALIZED_NO_PAID_ACK prepare device01 1 1 "$A" 2 "$B" "$N1"
deny rollback-with-wrong-digest run prepare device01 1 1 "$A" 2 "$C" "$N2"
cp "$LAB/witness.sqlite3" "$LAB/saved-old-sqlite"
crash before_prepare_commit prepare device01 1 2 "$B" 3 "$C" "$N2"
run status device01 "$N3" | assert_json OBSERVED_CANDIDATE_ONLY status device01 "$N3"
crash after_prepare_commit prepare device01 1 2 "$B" 3 "$C" "$N2"
run status device01 "$N3" | assert_json PENDING_RECONCILIATION status device01 "$N3"
run prepare device01 1 2 "$B" 3 "$C" "$N2" | assert_json PREPARED_NOT_COMMITTED prepare device01 1 2 "$B" 3 "$C" "$N2"
crash after_finalize_commit finalize device01 1 3 "$C" "$N2"
run finalize device01 1 3 "$C" "$N2" | assert_json ALREADY_FINALIZED_NO_PAID_ACK finalize device01 1 3 "$C" "$N2"
run status device01 "$N3" | assert_json OBSERVED_CANDIDATE_ONLY status device01 "$N3"
deny old-revision run prepare device01 1 2 "$B" 3 "$A" "$N3"
deny other-epoch run prepare device01 2 3 "$C" 4 "$A" "$N3"
deny bad-auth python3 "$SRC" "$LAB" status device01 "$N3" "$A"
# No SQLite table, candidate cryptographic proof or file ACL makes the
# datastore physically antirollback. Demonstrate restore of an old candidate
# backup cannot result in a *positive* witness/paid admission.
cp "$LAB/saved-old-sqlite" "$LAB/witness.sqlite3"
chmod 600 "$LAB/witness.sqlite3"
run status device01 "$N3" | assert_json OBSERVED_CANDIDATE_ONLY status device01 "$N3"
# Deny privileged input and symlink redirection, rather than following it.
chmod 644 "$LAB/secret.hex"
deny publicly-readable-secret run status device01 "$N3"
chmod 600 "$LAB/secret.hex"
mv "$LAB/.witness-candidate-only" "$LAB/marker-real"
ln -s "$LAB/marker-real" "$LAB/.witness-candidate-only"
deny linked-operator-marker run status device01 "$N3"
rm "$LAB/.witness-candidate-only"
mv "$LAB/marker-real" "$LAB/.witness-candidate-only"
echo 'WITNESS-0739 PASS: challenge-authenticated no-ACK status; WITNESS-0738 SQLite durable prepare/finalize across process crashes, idempotent lost-ACK recovery, stale/duplicate/epoch conflict denial and owner-only files'
echo 'NOT AN INDEPENDENT WITNESS: restoring a whole old database is possible. Witness root, P-256 signing, hardware powercut, real paid authority and v0.6 release NOT authorized.'
