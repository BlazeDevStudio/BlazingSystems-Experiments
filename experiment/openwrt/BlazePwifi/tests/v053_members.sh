#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"

cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo vendokey;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *'get blazepwifi.main.member_kdf_rounds') echo 1024;;
  *'get blazepwifi.main.member_event_history') echo 256;;
  *) exit 1;;
esac
UCI
chmod +x "$T/bin/uci"

export PATH="$T/bin:$PATH"
export BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_AUTH_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export SERVER_PORT=4455 REMOTE_ADDR=10.0.0.50

. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_MEMBER_LIB"
bp_member_init

bp_member_lock
bp_member_create alice "Alice Member" 'alpha123' test >/dev/null
bp_member_create bob "Bob Member" 'beta1234' test >/dev/null
bp_member_create nolabel "" 'nolabel99' test >/dev/null
bp_member_unlock

# Optional empty labels must not shift tab fields or corrupt auth/balance/password operations.
NO_LABEL_LINE="$(bp_member_line nolabel)"
[ "$(printf '%s' "$NO_LABEL_LINE" | cut -f2)" = "" ]
[ "$(printf '%s' "$NO_LABEL_LINE" | cut -f3)" = 1 ]
[ "$(printf '%s' "$NO_LABEL_LINE" | cut -f4)" = sha256i ]
bp_member_verify_password nolabel 'nolabel99'
bp_member_lock
bp_member_balance_change nolabel add 120 test "" >/dev/null
bp_member_set_password nolabel 'nolabel-new99' test >/dev/null
bp_member_patch nolabel "Now Labeled" @keep test >/dev/null
bp_member_unlock
bp_member_verify_password nolabel 'nolabel-new99'
[ "$(printf '%s' "$(bp_member_line nolabel)" | cut -f8)" -eq 120 ]
[ "$(printf '%s' "$(bp_member_line nolabel)" | cut -f2)" = "Now Labeled" ]

ALICE_LINE="$(bp_member_line alice)"
ALICE_HASH="$(printf '%s' "$ALICE_LINE" | cut -f6)"
ALICE_SALT="$(printf '%s' "$ALICE_LINE" | cut -f5)"
ALICE_ROUNDS="$(printf '%s' "$ALICE_LINE" | cut -f7)"
[ -n "$ALICE_HASH" ] && [ -n "$ALICE_SALT" ] && [ "$ALICE_ROUNDS" -ge 1024 ]

VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
call_vendo() {
  action="$1"; nonce="$2"; pulses="$3"; target="$4"
  sig="$(printf '%s|%s|%s|%s|%s|%s|%s' vendokey "$action" softtimer-01 "$nonce" "$pulses" "$target" vendokey | sha256sum | awk '{print $1}')"
  printf 'action=%s&id=softtimer-01&nonce=%s&pulses=%s&target=%s&sig=%s' "$action" "$nonce" "$pulses" "$target" "$sig" | REQUEST_METHOD=POST sh "$VENDO"
}
proof_for() {
  hash="$1"; nonce="$2"
  printf '%s|%s|%s|%s' "$hash" "$nonce" softtimer-01 vendokey | sha256sum | awk '{print $1}'
}

OUT="$(call_vendo member_snapshot 1000000000000001 0 '')"
echo "$OUT" | grep -q '"ok":true'
echo "$OUT" | grep -q '"username":"alice"'
echo "$OUT" | grep -q '"salt":"'
echo "$OUT" | grep -q '"rounds":1024'
echo "$OUT" | grep -q '"response_sig":"'
! echo "$OUT" | grep -q '"hash":'
! echo "$OUT" | grep -Fq "$ALICE_HASH"

AUTH_NONCE=1000000000000002
AUTH_PROOF="$(proof_for "$ALICE_HASH" "$AUTH_NONCE")"
OUT="$(call_vendo member_auth "$AUTH_NONCE" 0 "alice:$AUTH_PROOF")"
echo "$OUT" | grep -q '"ok":true'
echo "$OUT" | grep -q '"username":"alice"'

BANK_EVENT=11111111111111111111111111111111
BANK_NONCE=1000000000000003
BANK_PROOF="$(proof_for "$ALICE_HASH" "$BANK_NONCE")"
OUT="$(call_vendo member_bank "$BANK_NONCE" 600 "alice:$BANK_EVENT:$BANK_PROOF")"
echo "$OUT" | grep -q '"result_seconds":600'
echo "$OUT" | grep -q '"banked_seconds":600'
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" -eq 600 ]

BANK_NONCE2=1000000000000004
OUT="$(call_vendo member_bank "$BANK_NONCE2" 600 "alice:$BANK_EVENT:replay")"
echo "$OUT" | grep -q '"result_seconds":600'
echo "$OUT" | grep -q '"banked_seconds":600'
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" -eq 600 ]
[ "$(awk -F '\t' -v e="$BANK_EVENT" '$1==e {c++} END{print c+0}' "$BP_MEMBER_EVENTS")" -eq 1 ]

# The same event ID cannot be reused for a different member/source/action.
set +e
bp_member_balance_change bob add 60 softtimer:other "$BANK_EVENT" >/dev/null
COLLISION_RC=$?
set -e
[ "$COLLISION_RC" -eq 5 ]
[ "$(printf '%s' "$(bp_member_line bob)" | cut -f8)" -eq 0 ]

RESTORE_EVENT=22222222222222222222222222222222
RESTORE_NONCE=1000000000000005
RESTORE_PROOF="$(proof_for "$ALICE_HASH" "$RESTORE_NONCE")"
OUT="$(call_vendo member_restore "$RESTORE_NONCE" 0 "alice:$RESTORE_EVENT:$RESTORE_PROOF")"
echo "$OUT" | grep -q '"result_seconds":600'
echo "$OUT" | grep -q '"banked_seconds":0'
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" -eq 0 ]

RESTORE_NONCE2=1000000000000006
OUT="$(call_vendo member_restore "$RESTORE_NONCE2" 0 "alice:$RESTORE_EVENT:replay")"
echo "$OUT" | grep -q '"replayed":true'
echo "$OUT" | grep -q '"result_seconds":600'
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" -eq 0 ]
[ "$(awk -F '\t' -v e="$RESTORE_EVENT" '$1==e {c++} END{print c+0}' "$BP_MEMBER_EVENTS")" -eq 1 ]

BANK2_EVENT=33333333333333333333333333333333
BANK2_NONCE=1000000000000007
BANK2_PROOF="$(proof_for "$ALICE_HASH" "$BANK2_NONCE")"
OUT="$(call_vendo member_bank "$BANK2_NONCE" 600 "alice:$BANK2_EVENT:$BANK2_PROOF")"
echo "$OUT" | grep -q '"banked_seconds":600'

TRANSFER_EVENT=44444444444444444444444444444444
TRANSFER_NONCE=1000000000000008
TRANSFER_PROOF="$(proof_for "$ALICE_HASH" "$TRANSFER_NONCE")"
OUT="$(call_vendo member_transfer "$TRANSFER_NONCE" 300 "alice>bob:$TRANSFER_EVENT:$TRANSFER_PROOF")"
echo "$OUT" | grep -q '"result_seconds":300'
echo "$OUT" | grep -q '"source_banked_seconds":300'
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" -eq 300 ]
[ "$(printf '%s' "$(bp_member_line bob)" | cut -f8)" -eq 300 ]

TRANSFER_NONCE2=1000000000000009
OUT="$(call_vendo member_transfer "$TRANSFER_NONCE2" 300 "alice>bob:$TRANSFER_EVENT:replay")"
echo "$OUT" | grep -q '"replayed":true'
echo "$OUT" | grep -q '"result_seconds":300'
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" -eq 300 ]
[ "$(printf '%s' "$(bp_member_line bob)" | cut -f8)" -eq 300 ]
[ "$(awk -F '\t' -v e="$TRANSFER_EVENT" '$1==e {c++} END{print c+0}' "$BP_MEMBER_EVENTS")" -eq 1 ]

grep -Fq 'Pisonet Members' "$ROOT/openwrt/rootfs/www/blazepwifi/admin.html"
grep -Fq 'BlazeMembers' "$ROOT/openwrt/rootfs/www/blazepwifi/admin/members.js"
grep -Fq 'member_password)' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
grep -Fq 'member_snapshot)' "$VENDO"
[ "$(grep -c '^  coin)' "$VENDO")" -eq 1 ]
[ "$(grep -c '^  member_snapshot)' "$VENDO")" -eq 1 ]
[ "$(grep -c 'unknown vendo action' "$VENDO")" -eq 1 ]
! grep -Fq '\${BP_AUTH_MUST_CHANGE' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
! grep -Fq '"hash":"%s"' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"

# PHX-L-CORE P0: signed CGI must recheck recipient.enabled under the
# member writer lock. A distinct authorized admin writer can disable the
# recipient after the original pre-lock check, while the transfer waits.
# This is a bounded interprocess race on private fixture files, not hardware.
bp_member_lock
bp_member_create racealice 'Race source' 'racepass123' fixture >/dev/null
bp_member_create racebob 'Race target' 'racepass456' fixture >/dev/null
bp_member_balance_change racealice add 600 fixture race-funding-0001 >/dev/null
bp_member_unlock
RACE_NONCE=10000000000000ff
RACE_EVENT=55555555555555555555555555555555
RACE_HASH="$(printf '%s' "$(bp_member_line racealice)" | cut -f6)"
RACE_PROOF="$(proof_for "$RACE_HASH" "$RACE_NONCE")"
export PHX_REAL_MEMBER="$BP_MEMBER_LIB"
export PHX_REACHED="$T/transfer-lock-reached" PHX_RELEASE="$T/transfer-lock-release"
cat > "$T/member-race-wrapper.sh" <<'PHXWRAPPER'
. "$PHX_REAL_MEMBER"
bp_member_lock() {
  # Preserve the production lock semantics, with one deterministic wait
  # inserted just before taking the lock: pre-lock checks already ran.
  : > "$PHX_REACHED"
  n=0
  while [ ! -f "$PHX_RELEASE" ] && [ "$n" -lt 100 ]; do
    sleep 0.05
    n=$((n+1))
  done
  [ -f "$PHX_RELEASE" ] || return 1
  mkdir -p "$BP_RUN" || return 1
  exec 7>"$BP_RUN/member.lock" || return 1
  flock -w 10 7 || { exec 7>&-; return 1; }
  [ ! -e "$BP_STATE/paid-state-uncertain" ] ||
    { bp_member_unlock; return 9; }
}
PHXWRAPPER
export BP_MEMBER_LIB="$T/member-race-wrapper.sh"
call_vendo member_transfer "$RACE_NONCE" 30 "racealice>racebob:$RACE_EVENT:$RACE_PROOF" > "$T/race-output" &
race_pid=$!
n=0
while [ ! -f "$PHX_REACHED" ] && [ "$n" -lt 100 ]; do
  sleep 0.05
  n=$((n+1))
done
if [ ! -f "$PHX_REACHED" ]; then
  : > "$PHX_RELEASE"
  wait "$race_pid" 2>/dev/null || :
  echo 'PHX-L-CORE RACE SETUP FAIL: signed request never reached member lock' >&2
  exit 2
fi
# Concurrent admin mutation uses the real member store and its real locks.
bp_member_lock
bp_member_patch racebob @keep 0 fixture >/dev/null
bp_member_unlock
: > "$PHX_RELEASE"
wait "$race_pid" || :
response="$(cat "$T/race-output")"
if ! printf '%s' "$response" | grep -Fq '"ok":false' ||
   [ "$(printf '%s' "$(bp_member_line racealice)" | cut -f8)" != 600 ] ||
   [ "$(printf '%s' "$(bp_member_line racebob)" | cut -f8)" != 0 ] ||
   [ "$(printf '%s' "$(bp_member_line racebob)" | cut -f3)" != 0 ] ||
   [ -n "$(bp_member_event_line "$RACE_EVENT")" ]; then
  echo "PHX-L-CORE P0 RED: disabled destination received transfer after check-to-lock race: $response" >&2
  exit 1
fi
echo 'PHX-L-CORE PASS: REAL signed Vendo rejects transfer when destination disabled while waiting on member lock'


# PHX-L-CORE P0 #31 MASTER review: initial signed source proof may become
# invalid when an authorized member admin disables/resets its credentials
# BETWEEN that check and the member writer lock. Test the real CGI shell
# with real bp_member_patch/bp_member_set_password under real locks.
# The fixture-only hook above pauses at this exact boundary; no device/coin.
bp_member_lock
bp_member_patch racebob @keep 1 fixture >/dev/null
bp_member_unlock
for phx_revoke in disabled password_reset; do
  rm -f "$PHX_REACHED" "$PHX_RELEASE"
  case "$phx_revoke" in
    disabled)
      phx_nonce=10000000000000e1
      phx_event=66666666666666666666666666666661
      ;;
    password_reset)
      phx_nonce=10000000000000e2
      phx_event=66666666666666666666666666666662
      ;;
  esac
  phx_hash="$(printf '%s' "$(bp_member_line racealice)" | cut -f6)"
  phx_proof="$(proof_for "$phx_hash" "$phx_nonce")"
  phx_alice_before="$(printf '%s' "$(bp_member_line racealice)" | cut -f8)"
  phx_bob_before="$(printf '%s' "$(bp_member_line racebob)" | cut -f8)"
  call_vendo member_transfer "$phx_nonce" 40 \
    "racealice>racebob:$phx_event:$phx_proof" > "$T/transfer-source-$phx_revoke" &
  phx_pid=$!
  n=0
  while [ ! -f "$PHX_REACHED" ] && [ "$n" -lt 100 ]; do
    sleep 0.05
    n=$((n+1))
  done
  if [ ! -f "$PHX_REACHED" ]; then
    : > "$PHX_RELEASE"
    wait "$phx_pid" 2>/dev/null || :
    echo "PHX-L-CORE REPRO INVALID: $phx_revoke never reached locked boundary" >&2
    exit 2
  fi
  # Real admin updates use the unchanged production member module.
  bp_member_lock
  case "$phx_revoke" in
    disabled)
      bp_member_patch racealice @keep 0 fixture >/dev/null
      ;;
    password_reset)
      bp_member_set_password racealice 'revoked-pass-2026' fixture >/dev/null
      ;;
  esac
  bp_member_unlock
  : > "$PHX_RELEASE"
  wait "$phx_pid" || :
  phx_response="$(cat "$T/transfer-source-$phx_revoke")"
  if ! printf '%s' "$phx_response" | grep -Fq '"ok":false' ||
     [ "$(printf '%s' "$(bp_member_line racealice)" | cut -f8)" != "$phx_alice_before" ] ||
     [ "$(printf '%s' "$(bp_member_line racebob)" | cut -f8)" != "$phx_bob_before" ] ||
     [ -n "$(bp_member_event_line "$phx_event")" ]; then
    echo "PHX-L-CORE P0 SOURCE-PROOF RED: $phx_revoke after initial proof was paid-ACKed or changed balances: $phx_response" >&2
    exit 1
  fi
  if [ "$phx_revoke" = disabled ]; then
    bp_member_lock
    bp_member_patch racealice @keep 1 fixture >/dev/null
    bp_member_unlock
  fi
done
echo 'PHX-L-CORE PASS: REAL signed Vendo refuses new transfer after source disable/password reset at lock handoff'


# P0 #31: Revalidation protects NEW paid operations; it must not destroy
# idempotent ACKs for transactions already durably RECEIPTED before source
# account revocation. Real signed CGI, real admin writer, /tmp fixture.
export BP_MEMBER_LIB="$PHX_REAL_MEMBER"
phx_paid_event=77777777777777777777777777777771
phx_paid_nonce=10000000000000e3
phx_paid_hash="$(printf '%s' "$(bp_member_line racealice)" | cut -f6)"
phx_paid_proof="$(proof_for "$phx_paid_hash" "$phx_paid_nonce")"
phx_paid_response="$(call_vendo member_transfer "$phx_paid_nonce" 10 \
  "racealice>racebob:$phx_paid_event:$phx_paid_proof")"
printf '%s' "$phx_paid_response" | grep -Fq '"ok":true' || {
  echo "PHX-L-CORE REPLAY SETUP INVALID: fresh signed transfer rejected: $phx_paid_response" >&2
  exit 2
}
phx_paid_a="$(printf '%s' "$(bp_member_line racealice)" | cut -f8)"
phx_paid_b="$(printf '%s' "$(bp_member_line racebob)" | cut -f8)"
[ "$phx_paid_a:$phx_paid_b" = "590:10" ] || {
  echo "PHX-L-CORE REPLAY SETUP INVALID: unexpected committed balances $phx_paid_a:$phx_paid_b" >&2
  exit 2
}
bp_member_lock
bp_member_patch racealice @keep 0 fixture >/dev/null
bp_member_unlock
phx_replayed_response="$(call_vendo member_transfer 10000000000000e4 10 \
  "racealice>racebob:$phx_paid_event:replay")"
if ! printf '%s' "$phx_replayed_response" | grep -Fq '"ok":true' ||
   ! printf '%s' "$phx_replayed_response" | grep -Fq '"replayed":true' ||
   [ "$(printf '%s' "$(bp_member_line racealice)" | cut -f8)" != "$phx_paid_a" ] ||
   [ "$(printf '%s' "$(bp_member_line racebob)" | cut -f8)" != "$phx_paid_b" ] ||
   [ "$(printf '%s' "$(bp_member_line racealice)" | cut -f3)" != 0 ] ||
   [ "$(awk -F '\t' -v e="$phx_paid_event" '$1==e {n++} END {print n+0}' "$BP_MEMBER_EVENTS")" != 1 ]; then
  echo "PHX-L-CORE P0 REPLAY FAIL: committed transfer was lost, duplicated, or re-ACKed inconsistently after sender revocation: $phx_replayed_response" >&2
  exit 1
fi
echo 'PHX-L-CORE PASS: signed committed transfer receipt replay after sender disable is idempotent'


# PHX-L-CORE P0 #31: real signed member_bank/member_restore CGI
# source-proof-to-member-lock revocation test, using only synthetic /tmp state.
# The CGI is deliberately unchanged in this TEST-FIRST commit. Its pre-lock
# auth check must not authorize NEW money mutation after admin disable/reset.
# The first RED run exposed a fixture mistake: an expected bad payment can
# leave a fail-closed paid-state-uncertain marker. Sharing that same synthetic
# ledger across cases confounds later races and receipt-replay setup. Each
# case must start from its own fresh private state, never clear quarantine.
phx_br_fresh_state() {
  phx_br_slot="$1"
  export BP_STATE="$T/br-state-$phx_br_slot" BP_RUN="$T/br-run-$phx_br_slot"
  mkdir -p "$BP_STATE" "$BP_RUN"
  unset BP_MEMBERS BP_MEMBER_EVENTS BP_MEMBER_REVISION
  . "$BP_LIB"
  . "$PHX_REAL_MEMBER"
  bp_member_init
}
phx_br_failed=0
export BP_MEMBER_LIB="$PHX_REAL_MEMBER"
phx_br_n=0
for phx_br_action in member_bank member_restore; do
  for phx_br_revoke in disabled password_reset; do
    phx_br_n=$((phx_br_n+1))
    phx_br_fresh_state "$phx_br_n"
    phx_br_user="phxbruser$phx_br_n"
    phx_br_event="8888888888888888888888888888888$phx_br_n"
    phx_br_nonce="10000000000001a$phx_br_n"
    bp_member_lock
    bp_member_create "$phx_br_user" "PHX bank restore fixture" 'fixture-pass-123' fixture >/dev/null
    if [ "$phx_br_action" = member_restore ]; then
      bp_member_balance_change "$phx_br_user" add 600 fixture "phx-br-fund-$phx_br_n" >/dev/null
    fi
    bp_member_unlock
    phx_br_before="$(printf '%s' "$(bp_member_line "$phx_br_user")" | cut -f8)"
    phx_br_hash="$(printf '%s' "$(bp_member_line "$phx_br_user")" | cut -f6)"
    phx_br_proof="$(proof_for "$phx_br_hash" "$phx_br_nonce")"
    rm -f "$PHX_REACHED" "$PHX_RELEASE"
    export BP_MEMBER_LIB="$T/member-race-wrapper.sh"
    if [ "$phx_br_action" = member_bank ]; then
      phx_br_seconds=30
    else
      phx_br_seconds=0
    fi
    call_vendo "$phx_br_action" "$phx_br_nonce" "$phx_br_seconds" \
      "$phx_br_user:$phx_br_event:$phx_br_proof" > "$T/bank-restore-$phx_br_n" &
    phx_br_pid=$!
    phx_br_wait=0
    while [ ! -f "$PHX_REACHED" ] && [ "$phx_br_wait" -lt 100 ]; do
      sleep 0.05
      phx_br_wait=$((phx_br_wait+1))
    done
    if [ ! -f "$PHX_REACHED" ]; then
      : > "$PHX_RELEASE"
      wait "$phx_br_pid" 2>/dev/null || :
      echo "PHX-L-CORE BANK_RESTORE SETUP INVALID: $phx_br_action/$phx_br_revoke did not reach member writer lock" >&2
      exit 2
    fi
    # Parent retains the genuine member.sh lock and real admin mutation.
    export BP_MEMBER_LIB="$PHX_REAL_MEMBER"
    bp_member_lock
    if [ "$phx_br_revoke" = disabled ]; then
      bp_member_patch "$phx_br_user" @keep 0 fixture >/dev/null
    else
      bp_member_set_password "$phx_br_user" 'new-fixture-pass-123' fixture >/dev/null
    fi
    bp_member_unlock
    : > "$PHX_RELEASE"
    wait "$phx_br_pid" || :
    phx_br_response="$(cat "$T/bank-restore-$phx_br_n")"
    phx_br_after="$(printf '%s' "$(bp_member_line "$phx_br_user")" | cut -f8)"
    if ! printf '%s' "$phx_br_response" | grep -Fq '"ok":false' ||
       [ "$phx_br_before" != "$phx_br_after" ] ||
       [ -n "$(bp_member_event_line "$phx_br_event")" ]; then
      echo "PHX-L-CORE P0 BANK_RESTORE_SOURCE_PROOF_RED: $phx_br_action/$phx_br_revoke new money mutation survived admin revocation (before=$phx_br_before after=$phx_br_after): $phx_br_response" >&2
      phx_br_failed=$((phx_br_failed+1))
    else
      echo "PHX-L-CORE BANK_RESTORE_SOURCE_PROOF_PASS: $phx_br_action/$phx_br_revoke denied under lock"
    fi
  done
done

# Already COMMITTED receipts must remain idempotently replayable after
# revocation; replay is not a fresh paid mutation and must not re-credit.
for phx_br_replay_action in member_bank member_restore; do
  phx_br_n=$((phx_br_n+1))
  phx_br_fresh_state "$phx_br_n"
  phx_br_user="phxbruser$phx_br_n"
  phx_br_event="9999999999999999999999999999999$phx_br_n"
  phx_br_nonce="10000000000001b$phx_br_n"
  bp_member_lock
  bp_member_create "$phx_br_user" "PHX receipt replay fixture" 'fixture-pass-123' fixture >/dev/null
  if [ "$phx_br_replay_action" = member_restore ]; then
    bp_member_balance_change "$phx_br_user" add 600 fixture "phx-br-fund-$phx_br_n" >/dev/null
    phx_br_seconds=0
  else
    phx_br_seconds=30
  fi
  bp_member_unlock
  phx_br_hash="$(printf '%s' "$(bp_member_line "$phx_br_user")" | cut -f6)"
  phx_br_proof="$(proof_for "$phx_br_hash" "$phx_br_nonce")"
  phx_br_first="$(call_vendo "$phx_br_replay_action" "$phx_br_nonce" "$phx_br_seconds" \
    "$phx_br_user:$phx_br_event:$phx_br_proof")"
  if ! printf '%s' "$phx_br_first" | grep -Fq '"ok":true'; then
    echo "PHX-L-CORE BANK_RESTORE REPLAY SETUP INVALID: $phx_br_replay_action $phx_br_first" >&2
    exit 2
  fi
  phx_br_committed="$(printf '%s' "$(bp_member_line "$phx_br_user")" | cut -f8)"
  bp_member_lock
  bp_member_patch "$phx_br_user" @keep 0 fixture >/dev/null
  bp_member_unlock
  phx_br_replay="$(call_vendo "$phx_br_replay_action" "10000000000001c$phx_br_n" "$phx_br_seconds" \
    "$phx_br_user:$phx_br_event:replay")"
  if ! printf '%s' "$phx_br_replay" | grep -Fq '"ok":true' ||
     ! printf '%s' "$phx_br_replay" | grep -Fq '"replayed":true' ||
     [ "$(printf '%s' "$(bp_member_line "$phx_br_user")" | cut -f8)" != "$phx_br_committed" ] ||
     [ "$(awk -F '\t' -v e="$phx_br_event" '$1==e {n++} END {print n+0}' "$BP_MEMBER_EVENTS")" != 1 ]; then
    echo "PHX-L-CORE P0 BANK_RESTORE_REPLAY_FAIL: $phx_br_replay_action $phx_br_replay" >&2
    exit 1
  fi
  echo "PHX-L-CORE BANK_RESTORE_REPLAY_PASS: $phx_br_replay_action committed receipt remains idempotent after disable"
done

[ "$phx_br_failed" -eq 0 ] || exit 1

echo 'BlazePwifi centralized SoftTimer member checks passed'
