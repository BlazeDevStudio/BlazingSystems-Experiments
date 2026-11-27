#!/bin/sh
# MIG-0623. Off-device POSIX/BusyBox *synthetic fixture only*, NOT installed.
# Usage: sh v060_journal_fixture.sh ROOT CONTROLLER SEQ EVENT OP SUBJECT TARGET UNITS NOW
# OP: AM (add member seconds), SM (subtract), TM (transfer), LR (rental lease).
# Single snapshot contains balances + authenticated-sequence PLACEHOLDERS + receipts.
# Prototype has NO authenticating endpoint and NO power-loss fsync guarantee.
set -e
[ "$#" -eq 9 ] || { echo "invalid fixture arguments" >&2; exit 2; }
root="$1"; controller="$2"; seq="$3"; event="$4"; op="$5"
subject="$6"; target="$7"; units="$8"; now="$9"
root="$(CDPATH= cd -P "$root" 2>/dev/null && pwd -P)" || exit 2
case "$root" in /tmp/*|/var/tmp/*) ;; *) echo "fixture requires /tmp sandbox" >&2; exit 2;; esac
[ -f "$root/.blaze-v2-fixture-only" ] && [ ! -L "$root/.blaze-v2-fixture-only" ] ||
  { echo "missing synthetic sentinel" >&2; exit 2; }
grep -qx 'BLAZE-V2-SYNTHETIC-ONLY' "$root/.blaze-v2-fixture-only" ||
  { echo "invalid synthetic sentinel" >&2; exit 2; }
# Only an explicitly marked private /tmp laboratory workspace may opt in
# to the compiled file+parent-directory fsync helper. It is NOT rootfs code.
if [ -n "${BLAZE_V2_ATOMIC_BIN:-}" ]; then
  case "$root" in /tmp/blaze-v2-atomic-*) ;; *)
    echo "native durability helper only allowed in synthetic atomic fixture" >&2; exit 2;; esac
  [ "$BLAZE_V2_ATOMIC_BIN" = "$root/native-fixture" ] &&
    [ -f "$BLAZE_V2_ATOMIC_BIN" ] && [ ! -L "$BLAZE_V2_ATOMIC_BIN" ] &&
    [ -x "$BLAZE_V2_ATOMIC_BIN" ] ||
    { echo "untrusted native fixture helper path" >&2; exit 2; }
fi
ledger="$root/ledger.tsv"
[ -f "$ledger" ] && [ ! -L "$ledger" ] ||
  { echo "not an ordinary synthetic ledger" >&2; exit 2; }
for name in "$controller" "$subject"; do
  printf '%s\n' "$name" | grep -Eq '^[A-Za-z][A-Za-z0-9_.-]{0,31}$' ||
    { echo "invalid name" >&2; exit 2; }
done
if [ "$target" != '-' ]; then
  printf '%s\n' "$target" | grep -Eq '^[A-Za-z][A-Za-z0-9_.-]{0,31}$' ||
    { echo "invalid target" >&2; exit 2; }
fi
case "$seq:$units:$now" in *[!0-9:]*|'') echo "invalid numerics" >&2; exit 2;; esac
# The receipt's sequence is serialized as an ordinary decimal integer.
# Accepting 01 and writing 1 with event controller:01 would create a ledger
# whose own receipt-consistency check rejects every subsequent operation.
case "$seq" in 0*|'') echo "noncanonical controller sequence" >&2; exit 2;; esac
[ "$seq" -gt 0 ] 2>/dev/null && [ "$seq" -le 100000000 ] 2>/dev/null &&
[ "$units" -gt 0 ] 2>/dev/null && [ "$units" -le 31536000 ] 2>/dev/null &&
[ "$now" -ge 0 ] 2>/dev/null && [ "$now" -le 2000000000 ] 2>/dev/null ||
  { echo "numeric range refused" >&2; exit 2; }
case "$op" in AM|SM|TM|LR) ;; *) echo "invalid operation" >&2; exit 2;; esac
[ "$event" = "$controller:$seq" ] ||
  { echo "event must bind to controller+sequence" >&2; exit 2; }
[ "$op" != TM ] || [ "$subject" != "$target" ] ||
  { echo "self-transfer refused" >&2; exit 2; }
[ "$(wc -c < "$ledger")" -le 2097152 ] ||
  { echo "fixture size limit" >&2; exit 2; }

# Lock file remains in place between invocations (never unlink a live lock).
exec 8>"$root/.v2-write-lock"
flock -n 8 || { echo "busy; retry exact same transaction" >&2; exit 8; }
# The checksum footer is in the same file as all monetary balances and receipts.
# It detects accidental corruption, not tampering by someone with write access.
footer="$(tail -n 1 "$ledger")"
case "$footer" in
  H"$(printf '\t')"*) recorded="$(printf '%s\n' "$footer" | cut -f2)" ;;
  *) echo "missing integrity footer" >&2; exit 9 ;;
esac
printf '%s\n' "$recorded" | grep -Eq '^[a-f0-9]{64}$' ||
  { echo "malformed integrity footer" >&2; exit 9; }
calculated="$(sed '$d' "$ledger" | sha256sum | cut -d' ' -f1)" || exit 9
[ "$recorded" = "$calculated" ] ||
  { echo "synthetic ledger SHA-256 mismatch (fail-closed)" >&2; exit 9; }
# Strictly temp-only and private, no production filesystem paths.
umask 077
tmp="$root/v2-next-$$"
status="$root/.v2-status-$$"
trap 'rm -f "$tmp" "$status"' EXIT HUP INT TERM
digest="$(printf '%s|%s|%s|%s|%s|%s|%s|%s|%s' "$controller" "$seq" "$event" "$op" "$subject" "$target" "$units" "$now" v2 | sha256sum | cut -d' ' -f1)" ||
  exit 3
[ -n "$digest" ] || exit 3

if ! awk -F '\t' -v OFS='\t' \
  -v ctl="$controller" -v q="$seq" -v eid="$event" -v fingerprint="$digest" \
  -v mode="$op" -v src="$subject" -v dst="$target" -v add="$units" -v clock="$now" \
  -v response="$status" '
  function fail(message) { failure=message }
  NR==1 {
    if (NF!=2 || $1!="V" || $2!="2") fail("unsupported journal version")
    next
  }
  {
    if ($1=="A" && NF==3 && $2 ~ /^[A-Za-z][A-Za-z0-9_.-]*$/ && $3 ~ /^[0-9]+$/) {
      if ($2 in bank) fail("duplicate account")
      bank[$2]=$3+0; a_count++
    } else if ($1=="L" && NF==3 && $2 ~ /^[A-Za-z][A-Za-z0-9_.-]*$/ && $3 ~ /^[0-9]+$/) {
      if ($2 in lease) fail("duplicate rental")
      lease[$2]=$3+0; l_count++
    } else if ($1=="C" && NF==3 && $2 ~ /^[A-Za-z][A-Za-z0-9_.-]*$/ && $3 ~ /^[0-9]+$/) {
      if ($2 in upper) fail("duplicate controller")
      upper[$2]=$3+0; c_count++
    } else if ($1=="R" && NF==6 && $2 ~ /^[A-Za-z][A-Za-z0-9_.-]*$/ &&
               $3 ~ /^[0-9]+$/ && $4 ~ /^[A-Za-z][A-Za-z0-9_.-]*:[0-9]+$/ &&
               $5 ~ /^[a-f0-9]{64}$/ && $6 ~ /^[0-9]+(:[0-9]+)?$/) {
      ++receipt_count; rc[receipt_count]=$2; rs[receipt_count]=$3+0
      ri[receipt_count]=$4; rh[receipt_count]=$5; rr[receipt_count]=$6
      received[$2]++
    } else if ($1=="H" && NF==2 && $2 ~ /^[a-f0-9]{64}$/ && !footer_seen) {
      footer_seen=1
    } else fail("malformed journal record")
    if (footer_seen && $1!="H") fail("data following integrity footer")
  }
  END {
    if (NR<2 || !footer_seen || failure!="" || a_count>512 || l_count>512 || c_count>128 ||
        receipt_count>1024) {
      print "REJECT", (failure!="" ? failure : "journal bounds exceeded") > response
      exit 2
    }
    # All historic receipts must belong to retained controller epochs.
    for (i=1; i<=receipt_count; ++i) {
      key=rc[i]
      if (!(key in upper) || rs[i]>upper[key] || rs[i]<=upper[key]-8 ||
          ri[i] != key ":" sprintf("%.0f",rs[i])) {
        print "REJECT", "receipt consistency invalid" > response
        exit 2
      }
    }
    high=(ctl in upper ? upper[ctl] : 0)
    for (i=1; i<=receipt_count; ++i)
      if (rc[i]==ctl && rs[i]==q) {
        if (ri[i]==eid && rh[i]==fingerprint) {
          print "REPLAY", rr[i] > response
          exit 0
        }
        print "REJECT", "sequence payload collision" > response
        exit 2
      }
    if (q<=high) {
      print "REJECT", "stale transaction sequence" > response
      exit 2
    }
    if (q!=high+1) {
      print "REJECT", "out-of-order transaction sequence" > response
      exit 2
    }
    if (!(ctl in upper) && c_count>=128) {
      print "REJECT", "controller limit" > response
      exit 2
    }
    # All balance, lease, high-water and receipt data are materialized together.
    if (mode=="AM" || mode=="SM" || mode=="TM") {
      if (!(src in bank)) {
        print "REJECT", "unknown account" > response
        exit 2
      }
      if (mode=="AM") bank[src]+=add
      if (mode=="SM") {
        if (bank[src]<add) {
          print "REJECT", "insufficient prepaid time" > response
          exit 2
        }
        bank[src]-=add
      }
      if (mode=="TM") {
        if (!(dst in bank) || bank[src]<add) {
          print "REJECT", "invalid transfer" > response
          exit 2
        }
        bank[src]-=add; bank[dst]+=add
      }
      result=sprintf("%.0f",bank[src])
    } else if (mode=="LR") {
      if (!(src in lease)) {
        print "REJECT", "unknown rental device" > response
        exit 2
      }
      base=(lease[src]>clock ? lease[src] : clock)
      lease[src]=base+add
      result=sprintf("%.0f",lease[src])
    } else {
      print "REJECT", "unknown operation" > response
      exit 2
    }
    upper[ctl]=q
    print "V","2"
    for (key in bank) print "A",key,sprintf("%.0f",bank[key])
    for (key in lease) print "L",key,sprintf("%.0f",lease[key])
    for (key in upper) print "C",key,sprintf("%.0f",upper[key])
    for (i=1;i<=receipt_count;++i)
      if (!(rc[i]==ctl && rs[i]<=q-8))
        print "R",rc[i],sprintf("%.0f",rs[i]),ri[i],rh[i],rr[i]
    print "R",ctl,sprintf("%.0f",q),eid,fingerprint,result
    print "COMMIT",result > response
  }
' "$ledger" > "$tmp"; then
  echo "transaction rejected or corrupt synthetic journal" >&2
  exit 9
fi
read_result="$(cat "$status" 2>/dev/null || true)"
case "$read_result" in
  REPLAY*)
    printf '%s\n' "$read_result"
    exit 0 ;;
  COMMIT*)
    # Integrity footer belongs to the same atomic candidate snapshot.
    next_hash="$(sha256sum "$tmp" | cut -d' ' -f1)" || exit 69
    printf 'H\t%s\n' "$next_hash" >> "$tmp" || exit 69
    # Fault injection tests are intentionally sandbox-only.
    case "$BLAZE_TEST_FAULT" in
      before-rename|receipt-eio) echo "injected precommit I/O error" >&2; exit 70 ;;
    esac
    chmod 600 "$tmp" || exit 69
    if [ -n "${BLAZE_V2_ATOMIC_BIN:-}" ]; then
      # Off-device syscall-backed simulated journal commit. Exactly one
      # snapshot holds balances, controller floor and replay receipt.
      # A post-rename/dirsync EIO must be reported as UNCERTAIN, never ACK.
      durable_reply="$("$BLAZE_V2_ATOMIC_BIN" "$root" "v2-next-$$" ledger.tsv)" ||
        { echo "native synthetic durability commit failed / uncertain" >&2; exit 72; }
      [ "$durable_reply" = COMMITTED ] ||
        { echo "native synthetic durability ACK invalid" >&2; exit 72; }
    else
      mv "$tmp" "$ledger" || exit 71
      # Backwards-compatible synthetic fixture path; not fsync verified.
      sync || exit 72
    fi
    case "$BLAZE_TEST_FAULT" in
      after-rename-before-ack) echo "injected lost ACK after rename" >&2; exit 73 ;;
    esac
    printf '%s\n' "$read_result"
    exit 0 ;;
  *) echo "invalid journal status / rejected transaction" >&2; exit 9 ;;
esac
