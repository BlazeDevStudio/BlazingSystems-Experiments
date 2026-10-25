#!/bin/sh
# PHX-L-CORE: source test and 3 canonical docs synchronized in one Git tree for RED CI.
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
. "$BP_CONTROLLER_LIB"
bp_member_init
# Positive signed member tests require an explicit admin-enabled controller.
bp_controller_ensure softtimer-01
bp_controller_set softtimer-01 1 1 1 1 -1 -1 -1 1 1 1 40 400 6

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
  . "$BP_CONTROLLER_LIB"
  bp_member_init
  bp_controller_ensure softtimer-01
  bp_controller_set softtimer-01 1 1 1 1 -1 -1 -1 1 1 1 40 400 6
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


# PHX-L-CORE P0 #31: MASTER #172 controller-disable NEW paid-admission
# contract, TEST FIRST. These requests invoke the actual signed Vendo CGI
# and actual bp_controller_set writer used by authenticated admin CGI, but
# NOT the admin HTTP/session/CSRF path. All financial state is private /tmp.
# Each case has its own state: never erase a paid-state-uncertain marker.
phx_ctl_fresh_state() {
  phx_ctl_slot="$1"
  export BP_STATE="$T/ctl-state-$phx_ctl_slot" BP_RUN="$T/ctl-run-$phx_ctl_slot"
  mkdir -p "$BP_STATE" "$BP_RUN" "$BP_STATE/targets"
  unset BP_MEMBERS BP_MEMBER_EVENTS BP_MEMBER_REVISION
  . "$BP_LIB"
  . "$PHX_REAL_MEMBER"
  . "$BP_CONTROLLER_LIB"
  bp_member_init
  bp_controller_ensure softtimer-01
  # The fixture explicitly authorizes normal positive controller payments.
  # Negative cases below still invoke real bp_controller_set disable.
  bp_controller_set softtimer-01 1 1 1 1 -1 -1 -1 1 1 1 40 400 6
}
phx_ctl_config() {
  bp_controller_set softtimer-01 "$1" "$2" 1 1 -1 -1 -1 1 1 1 40 400 6
}
phx_ctl_digest() {
  sha256sum "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION" "$BP_ACCOUNTS" |
    sha256sum | awk '{print $1}'
}
phx_ctl_setup_coin() {
  phx_ctl_device=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  phx_ctl_target=1122334455667788
  phx_ctl_now="$(date +%s)"
  printf '%s\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.50\t\n' \
    "$phx_ctl_device" > "$BP_ACCOUNTS"
  printf '%s\taa:bb:cc:dd:ee:ff\t%s\t%s\tsofttimer-01\thotspot\n' \
    "$phx_ctl_device" "$phx_ctl_target" "$((phx_ctl_now+600))" \
    > "$BP_TARGET_DIR/softtimer-01.tsv"
}
phx_ctl_failures=0
phx_ctl_i=0
for phx_ctl_action in member_bank member_restore member_transfer coin; do
  phx_ctl_i=$((phx_ctl_i+1))
  phx_ctl_fresh_state "$phx_ctl_i"
  phx_ctl_nonce="10000000000002d$phx_ctl_i"
  phx_ctl_event="ddddddddddddddddddddddddddddddd$phx_ctl_i"
  if [ "$phx_ctl_action" = coin ]; then
    phx_ctl_setup_coin
    phx_ctl_target_arg="$phx_ctl_target"
    phx_ctl_amount=1
  else
    phx_ctl_user="phxctluser$phx_ctl_i"
    bp_member_lock
    bp_member_create "$phx_ctl_user" "Controller disabled test" 'fixture-pass-123' fixture >/dev/null
    if [ "$phx_ctl_action" = member_restore ] || [ "$phx_ctl_action" = member_transfer ]; then
      bp_member_balance_change "$phx_ctl_user" add 600 fixture "ctl-fund-$phx_ctl_i" >/dev/null
    fi
    if [ "$phx_ctl_action" = member_transfer ]; then
      bp_member_create phxctldest "Controller destination" 'fixture-pass-456' fixture >/dev/null
    fi
    bp_member_unlock
    phx_ctl_hash="$(printf '%s' "$(bp_member_line "$phx_ctl_user")" | cut -f6)"
    phx_ctl_proof="$(proof_for "$phx_ctl_hash" "$phx_ctl_nonce")"
    case "$phx_ctl_action" in
      member_bank) phx_ctl_amount=30; phx_ctl_target_arg="$phx_ctl_user:$phx_ctl_event:$phx_ctl_proof" ;;
      member_restore) phx_ctl_amount=0; phx_ctl_target_arg="$phx_ctl_user:$phx_ctl_event:$phx_ctl_proof" ;;
      member_transfer) phx_ctl_amount=30; phx_ctl_target_arg="$phx_ctl_user>phxctldest:$phx_ctl_event:$phx_ctl_proof" ;;
    esac
  fi
  # Real admin controller backend disables before the NEW signed request.
  phx_ctl_config 0 1
  phx_ctl_before="$(phx_ctl_digest)"
  phx_ctl_reply="$(call_vendo "$phx_ctl_action" "$phx_ctl_nonce" "$phx_ctl_amount" "$phx_ctl_target_arg")"
  if ! printf '%s' "$phx_ctl_reply" | grep -Fq '"ok":false' ||
     [ "$(phx_ctl_digest)" != "$phx_ctl_before" ]; then
    echo "PHX-L-CORE CONTROLLER_DISABLED_RED: $phx_ctl_action fresh signed paid ACK/mutation after admin disable: $phx_ctl_reply" >&2
    phx_ctl_failures=$((phx_ctl_failures+1))
  else
    echo "PHX-L-CORE CONTROLLER_DISABLED_PASS: $phx_ctl_action rejected after controller disable"
  fi
done

# coin_enabled=0 is a separate physical coin-intake gate even while enabled=1.
phx_ctl_fresh_state coin-disabled
phx_ctl_setup_coin
phx_ctl_config 1 0
phx_ctl_before="$(phx_ctl_digest)"
phx_ctl_reply="$(call_vendo coin 10000000000002ee 1 "$phx_ctl_target")"
if ! printf '%s' "$phx_ctl_reply" | grep -Fq '"ok":false' ||
   [ "$(phx_ctl_digest)" != "$phx_ctl_before" ]; then
  echo "PHX-L-CORE CONTROLLER_COIN_DISABLED_RED: coin_enabled=0 accepted signed coin: $phx_ctl_reply" >&2
  phx_ctl_failures=$((phx_ctl_failures+1))
else
  echo 'PHX-L-CORE CONTROLLER_COIN_DISABLED_PASS: disabled coin intake rejected'
fi

# Disable while a genuine signed bank request is paused BEFORE its real
# member writer lock. The controller writer does not use member.lock today.
phx_ctl_fresh_state controller-race
bp_member_lock
bp_member_create phxctlrace "Controller race" 'fixture-pass-123' fixture >/dev/null
bp_member_unlock
phx_ctl_nonce=10000000000002ef
phx_ctl_event=eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
phx_ctl_hash="$(printf '%s' "$(bp_member_line phxctlrace)" | cut -f6)"
phx_ctl_proof="$(proof_for "$phx_ctl_hash" "$phx_ctl_nonce")"
export PHX_REACHED="$T/ctl-lock-reached" PHX_RELEASE="$T/ctl-lock-release"
rm -f "$PHX_REACHED" "$PHX_RELEASE"
export BP_MEMBER_LIB="$T/member-race-wrapper.sh"
call_vendo member_bank "$phx_ctl_nonce" 30 \
  "phxctlrace:$phx_ctl_event:$phx_ctl_proof" > "$T/ctl-lock-reply" &
phx_ctl_pid=$!
phx_ctl_wait=0
while [ ! -f "$PHX_REACHED" ] && [ "$phx_ctl_wait" -lt 100 ]; do
  sleep 0.05
  phx_ctl_wait=$((phx_ctl_wait+1))
done
if [ ! -f "$PHX_REACHED" ]; then
  : > "$PHX_RELEASE"
  wait "$phx_ctl_pid" 2>/dev/null || :
  echo 'PHX-L-CORE CONTROLLER_RACE_SETUP_INVALID: signed CGI never reached member lock' >&2
  exit 2
fi
export BP_MEMBER_LIB="$PHX_REAL_MEMBER"
phx_ctl_config 0 1
phx_ctl_before="$(phx_ctl_digest)"
: > "$PHX_RELEASE"
wait "$phx_ctl_pid" || :
phx_ctl_reply="$(cat "$T/ctl-lock-reply")"
if ! printf '%s' "$phx_ctl_reply" | grep -Fq '"ok":false' ||
   [ "$(phx_ctl_digest)" != "$phx_ctl_before" ]; then
  echo "PHX-L-CORE CONTROLLER_LOCK_RACE_RED: signed bank paid after controller_set disable: $phx_ctl_reply" >&2
  phx_ctl_failures=$((phx_ctl_failures+1))
else
  echo 'PHX-L-CORE CONTROLLER_LOCK_RACE_PASS: disable-before-writer-lock denied'
fi

# Previously committed receipts may be replayed read-only after disable;
# this is not permission for a NEW mutation, nor physical witness evidence.
for phx_ctl_replay_action in member_bank coin; do
  phx_ctl_fresh_state "replay-$phx_ctl_replay_action"
  phx_ctl_nonce=10000000000002f1
  if [ "$phx_ctl_replay_action" = coin ]; then
    phx_ctl_setup_coin
    phx_ctl_amount=1
    phx_ctl_target_arg="$phx_ctl_target"
  else
    bp_member_lock
    bp_member_create phxctlreplay "Controller replay" 'fixture-pass-123' fixture >/dev/null
    bp_member_unlock
    phx_ctl_hash="$(printf '%s' "$(bp_member_line phxctlreplay)" | cut -f6)"
    phx_ctl_proof="$(proof_for "$phx_ctl_hash" "$phx_ctl_nonce")"
    phx_ctl_amount=30
    phx_ctl_target_arg="phxctlreplay:ffffffffffffffffffffffffffffffff:$phx_ctl_proof"
  fi
  phx_ctl_first="$(call_vendo "$phx_ctl_replay_action" "$phx_ctl_nonce" "$phx_ctl_amount" "$phx_ctl_target_arg")"
  if ! printf '%s' "$phx_ctl_first" | grep -Fq '"ok":true'; then
    echo "PHX-L-CORE CONTROLLER_REPLAY_SETUP_INVALID: $phx_ctl_replay_action $phx_ctl_first" >&2
    exit 2
  fi
  phx_ctl_config 0 1
  phx_ctl_before="$(phx_ctl_digest)"
  if [ "$phx_ctl_replay_action" = member_bank ]; then
    phx_ctl_target_arg="phxctlreplay:ffffffffffffffffffffffffffffffff:replay"
    phx_ctl_nonce=10000000000002f2
  fi
  phx_ctl_reply="$(call_vendo "$phx_ctl_replay_action" "$phx_ctl_nonce" "$phx_ctl_amount" "$phx_ctl_target_arg")"
  if ! printf '%s' "$phx_ctl_reply" | grep -Fq '"ok":true' ||
     [ "$(phx_ctl_digest)" != "$phx_ctl_before" ] ||
     { [ "$phx_ctl_replay_action" = member_bank ] &&
       ! printf '%s' "$phx_ctl_reply" | grep -Fq '"replayed":true'; } ||
     { [ "$phx_ctl_replay_action" = coin ] &&
       ! printf '%s' "$phx_ctl_reply" | grep -Fq '"duplicate":true'; }; then
    echo "PHX-L-CORE CONTROLLER_REPLAY_FAIL: $phx_ctl_replay_action $phx_ctl_reply" >&2
    exit 1
  fi
  echo "PHX-L-CORE CONTROLLER_REPLAY_PASS: $phx_ctl_replay_action immutable committed receipt"
done
[ "$phx_ctl_failures" -eq 0 ] || exit 1


# PHX-L-CORE P0 #31 / MASTER #172: REAL signed Vendo heartbeat currently
# auto-ensures an absent controller entry as ENABLED (coin_enabled=1).
# Force controller-registry loss/torn rows after a genuine ADMIN DISABLE
# and verify every fresh signed paid event fails closed. Private /tmp only.
# Keep first enrollment separate: an unknown ID must not automatically
# become paid-enabled just because it holds a controller request signature.
phx_reg_failures=0
phx_reg_index=0
for phx_reg_case in \
  missing-bank missing-coin empty-coin torn-bank torn-coin first-enrollment-bank; do
  phx_reg_index=$((phx_reg_index+1))
  phx_ctl_fresh_state "registry-$phx_reg_index"
  phx_reg_nonce="$(printf '10000000000003%02x' "$phx_reg_index")"
  phx_reg_event="$(printf '%032x' "$((8000+phx_reg_index))")"
  case "$phx_reg_case" in
    *-bank)
      phx_reg_user="phxreg$phx_reg_index"
      bp_member_lock
      bp_member_create "$phx_reg_user" "Registry guard" 'fixture-pass-123' fixture >/dev/null
      bp_member_unlock
      phx_reg_hash="$(printf '%s' "$(bp_member_line "$phx_reg_user")" | cut -f6)"
      phx_reg_proof="$(proof_for "$phx_reg_hash" "$phx_reg_nonce")"
      phx_reg_op=member_bank
      phx_reg_count=30
      phx_reg_target="$phx_reg_user:$phx_reg_event:$phx_reg_proof"
      ;;
    *-coin)
      phx_ctl_setup_coin
      phx_reg_op=coin
      phx_reg_count=1
      phx_reg_target="$phx_ctl_target"
      ;;
  esac
  # Start with an actual disabled controller revision > 1. For first
  # enrollment there is deliberately no prior disabled revision.
  if [ "$phx_reg_case" != first-enrollment-bank ]; then
    phx_ctl_config 0 0
    phx_reg_old_rev="$(printf '%s' "$(bp_controller_line softtimer-01)" | cut -f15)"
    [ "$phx_reg_old_rev" -ge 2 ] || {
      echo 'PHX-L-CORE CONTROLLER_REGISTRY_SETUP_INVALID: no prior disable' >&2; exit 2;
    }
  fi
  case "$phx_reg_case" in
    missing-*) rm -f "$BP_CONTROLLERS" ;;
    empty-*) : > "$BP_CONTROLLERS" ;;
    torn-*) printf 'softtimer-01\t1\t1\n' > "$BP_CONTROLLERS" ;;
    first-enrollment-*) rm -f "$BP_CONTROLLERS" ;;
  esac
  phx_reg_before="$(phx_ctl_digest)"
  phx_reg_reply="$(call_vendo "$phx_reg_op" "$phx_reg_nonce" "$phx_reg_count" "$phx_reg_target")"
  phx_reg_after="$(phx_ctl_digest)"
  phx_reg_row="$(bp_controller_line softtimer-01)"
  phx_reg_enabled="$(printf '%s' "$phx_reg_row" | cut -f2)"
  phx_reg_coins="$(printf '%s' "$phx_reg_row" | cut -f3)"
  if ! printf '%s' "$phx_reg_reply" | grep -Fq '"ok":false' ||
     [ "$phx_reg_before" != "$phx_reg_after" ] ||
     { [ "$phx_reg_case" != torn-bank ] &&
       [ "$phx_reg_case" != torn-coin ] &&
       [ "$phx_reg_enabled:$phx_reg_coins" = "1:1" ]; }; then
    echo "PHX-L-CORE CONTROLLER_REGISTRY_RED: $phx_reg_case auto-admitted fresh signed paid event after lost/torn/unknown registry: $phx_reg_reply" >&2
    phx_reg_failures=$((phx_reg_failures+1))
  else
    echo "PHX-L-CORE CONTROLLER_REGISTRY_PASS: $phx_reg_case denied fresh signed coin/bank"
  fi
done

# Explicit authenticated admin enable remains the positive control. It
# is not equivalent to automatic re-enrollment on signed heartbeat.
phx_ctl_fresh_state registry-explicit-enabled
bp_member_lock
bp_member_create phxregpositive "Registry enabled" 'fixture-pass-123' fixture >/dev/null
bp_member_unlock
phx_ctl_config 1 1
phx_reg_nonce=10000000000003f0
phx_reg_event=88888888888888888888888888888880
phx_reg_hash="$(printf '%s' "$(bp_member_line phxregpositive)" | cut -f6)"
phx_reg_proof="$(proof_for "$phx_reg_hash" "$phx_reg_nonce")"
phx_reg_reply="$(call_vendo member_bank "$phx_reg_nonce" 30 \
  "phxregpositive:$phx_reg_event:$phx_reg_proof")"
if ! printf '%s' "$phx_reg_reply" | grep -Fq '"ok":true' ||
   [ "$(printf '%s' "$(bp_member_line phxregpositive)" | cut -f8)" != 30 ] ||
   [ "$(awk -F '\t' -v e="$phx_reg_event" '$1==e {n++} END {print n+0}' "$BP_MEMBER_EVENTS")" != 1 ]; then
  echo "PHX-L-CORE CONTROLLER_REGISTRY_SETUP_INVALID: explicit admin enable denied: $phx_reg_reply" >&2
  exit 2
fi
echo 'PHX-L-CORE CONTROLLER_REGISTRY_PASS: explicit admin enable admits exactly one new signed paid event'
[ "$phx_reg_failures" -eq 0 ] || exit 1


# PHX-L-CORE P0 / MASTER UTC22: real sourced controller_set may rename an
# ENABLED registry row, then report failure because durability sync returned
# an error. A fresh signed Vendo payment MUST fail closed after ambiguous
# admin persistence, even though the new row is locally visible.
# Private /tmp per-case fixture; no real filesystem powercut or money.
phx_sync_failures=0
phx_sync_i=0
for phx_sync_action in member_bank coin; do
  phx_sync_i=$((phx_sync_i+1))
  phx_ctl_fresh_state "controller-sync-$phx_sync_i"
  phx_ctl_config 0 0 || {
    echo "PHX-L-CORE CONTROLLER_SYNC_SETUP_INVALID: cannot disable prior to fault" >&2
    exit 2
  }
  phx_sync_nonce="$(printf '10000000000004%02x' "$phx_sync_i")"
  if [ "$phx_sync_action" = coin ]; then
    phx_ctl_setup_coin
    phx_sync_target="$phx_ctl_target"
    phx_sync_pulses=1
  else
    phx_sync_user="phxsync$phx_sync_i"
    bp_member_lock
    bp_member_create "$phx_sync_user" "Controller sync failure fixture" 'fixture-pass-123' fixture >/dev/null
    bp_member_unlock
    phx_sync_event="$(printf '%032x' "$((9000+phx_sync_i))")"
    phx_sync_hash="$(printf '%s' "$(bp_member_line "$phx_sync_user")" | cut -f6)"
    phx_sync_proof="$(proof_for "$phx_sync_hash" "$phx_sync_nonce")"
    phx_sync_target="$phx_sync_user:$phx_sync_event:$phx_sync_proof"
    phx_sync_pulses=30
  fi
  # The hook is on the REAL controller.sh writer call, not Vendo's new
  # process: it proves the admin sync was reached and whether the enabled
  # row was visible after mv. The CGI uses the unchanged real common.sh.
  export PHX_SYNC_CALLED="$BP_RUN/sync-called"
  export PHX_SYNC_POSTMV="$BP_RUN/sync-postmv-enabled-visible"
  bp_durable_sync() {
    : > "$PHX_SYNC_CALLED"
    phx_sync_visible="$(printf '%s' "$(bp_controller_line softtimer-01)" | cut -f2)"
    [ "$phx_sync_visible" != 1 ] || : > "$PHX_SYNC_POSTMV"
    return 74
  }
  phx_sync_admin_rc=0
  if phx_ctl_config 1 1; then
    phx_sync_admin_rc=0
  else
    phx_sync_admin_rc=$?
  fi
  # Restore the original unmodified production source function before
  # driving the separate signed CGI process.
  . "$BP_LIB"
  if [ "$phx_sync_admin_rc" -ne 8 ] || [ ! -f "$PHX_SYNC_CALLED" ]; then
    echo "PHX-L-CORE CONTROLLER_SYNC_SETUP_INVALID: real admin writer did not report injected sync EIO ($phx_sync_admin_rc)" >&2
    exit 2
  fi
  if [ -f "$PHX_SYNC_POSTMV" ]; then
    echo "PHX-L-CORE CONTROLLER_SYNC_POSTMV_OBSERVED: $phx_sync_action enabled policy locally visible during injected EIO"
  fi
  phx_sync_before="$(phx_ctl_digest)"
  phx_sync_reply="$(call_vendo "$phx_sync_action" "$phx_sync_nonce" "$phx_sync_pulses" "$phx_sync_target")"
  if ! printf '%s' "$phx_sync_reply" | grep -Fq '"ok":false' ||
     [ "$(phx_ctl_digest)" != "$phx_sync_before" ]; then
    echo "PHX-L-CORE CONTROLLER_SYNC_POSTMV_RED: $phx_sync_action fresh signed money accepted after failed admin controller enable durability sync: $phx_sync_reply" >&2
    phx_sync_failures=$((phx_sync_failures+1))
  else
    echo "PHX-L-CORE CONTROLLER_SYNC_POSTMV_PASS: $phx_sync_action fresh signed money denied after ambiguous controller sync"
  fi
done
[ "$phx_sync_failures" -eq 0 ] || exit 1


# PHX-L-CORE P0 #31: a killed admin writer does not return through the
# bp_controller_set error path. Its shared fd4 lock is released by the OS,
# so a DIFFERENT signed CGI must still see a fail-closed runtime barrier.
# This tests process exit, NOT a physical powercut or post-reboot recovery.
phx_ctl_fresh_state controller-worker-exit
phx_ctl_config 0 0
phx_crash_user=phxsynccrash
bp_member_lock
bp_member_create "$phx_crash_user" "Controller worker crash" 'fixture-pass-123' fixture >/dev/null
bp_member_unlock
phx_crash_nonce=10000000000004f0
phx_crash_event=ddddddddddddddddddddddddddddddd0
phx_crash_hash="$(printf '%s' "$(bp_member_line "$phx_crash_user")" | cut -f6)"
phx_crash_proof="$(proof_for "$phx_crash_hash" "$phx_crash_nonce")"
phx_crash_target="$phx_crash_user:$phx_crash_event:$phx_crash_proof"
phx_crash_before="$(phx_ctl_digest)"
export PHX_CRASH_REACHED="$BP_RUN/controller-worker-exit-reached"
export PHX_CRASH_AFTER_RENAME="$BP_RUN/controller-worker-exit-enabled-visible"
(
  bp_durable_sync() {
    : > "$PHX_CRASH_REACHED"
    phx_visible="$(printf '%s' "$(bp_controller_line softtimer-01)" | cut -f2)"
    [ "$phx_visible" != 1 ] || : > "$PHX_CRASH_AFTER_RENAME"
    exit 77
  }
  phx_ctl_config 1 1
) > "$T/controller-worker-exit-output" 2>&1 &
phx_worker_pid=$!
phx_worker_rc=0
wait "$phx_worker_pid" || phx_worker_rc=$?
if [ "$phx_worker_rc" -ne 77 ] ||
   [ ! -f "$PHX_CRASH_REACHED" ] ||
   [ ! -f "$PHX_CRASH_AFTER_RENAME" ]; then
  echo "PHX-L-CORE CONTROLLER_WORKER_EXIT_SETUP_INVALID: no real post-rename worker exit $phx_worker_rc" >&2
  exit 2
fi
phx_crash_reply="$(call_vendo member_bank "$phx_crash_nonce" 30 "$phx_crash_target")"
phx_crash_after="$(phx_ctl_digest)"
if ! printf '%s' "$phx_crash_reply" | grep -Fq '"ok":false' ||
   [ "$phx_crash_after" != "$phx_crash_before" ] ||
   [ -n "$(bp_member_event_line "$phx_crash_event")" ]; then
  echo "PHX-L-CORE CONTROLLER_WORKER_EXIT_RED: paid ACK after admin exited post-rename before durable sync: $phx_crash_reply" >&2
  exit 1
fi
# No unrelated retry is permitted to accidentally remove a pending
# controller-write barrier; explicit operator recovery is separate.
phx_retry_rc=0
phx_ctl_config 1 1 || phx_retry_rc=$?
if [ "$phx_retry_rc" -ne 8 ] ||
   [ "$(phx_ctl_digest)" != "$phx_crash_before" ]; then
  echo "PHX-L-CORE CONTROLLER_WORKER_EXIT_RED: admin retry erased unsafe barrier" >&2
  exit 1
fi
echo 'PHX-L-CORE CONTROLLER_WORKER_EXIT_PASS: admin process exit after rename keeps separate signed CGI and retry fail-closed'



# PHX-L-CORE P0 #31/#43 T16/T18 TEST-FIRST: the controller can remain
# legitimately enabled while a separately committed financial ledger and
# receipt corpus are restored to an older, individually well-formed snapshot.
# A new signed transport nonce for the SAME paid event must not create a
# second paid ACK or mutation. This is a synthetic /tmp rollback, not flash
# or proof of an independent witness. The earlier commit really succeeded.
phx_ctl_fresh_state finance-ledger-rollback-bank
bp_member_lock
bp_member_create phxfinance "Financial rollback fixture" 'fixture-pass-123' fixture >/dev/null
bp_member_unlock
phx_finance_event=abababababababababababababababab
phx_finance_first_nonce=10000000000006a0
phx_finance_retry_nonce=10000000000006a1
phx_finance_hash="$(printf '%s' "$(bp_member_line phxfinance)" | cut -f6)"
cp "$BP_MEMBERS" "$T/finance-older-members.tsv"
cp "$BP_MEMBER_EVENTS" "$T/finance-older-events.tsv"
cp "$BP_MEMBER_REVISION" "$T/finance-older-revision"
phx_finance_first_proof="$(proof_for "$phx_finance_hash" "$phx_finance_first_nonce")"
phx_finance_first_reply="$(call_vendo member_bank "$phx_finance_first_nonce" 30 \
  "phxfinance:$phx_finance_event:$phx_finance_first_proof")"
if ! printf '%s' "$phx_finance_first_reply" | grep -Fq '"ok":true' ||
   [ "$(printf '%s' "$(bp_member_line phxfinance)" | cut -f8)" != 30 ] ||
   [ "$(awk -F '\t' -v e="$phx_finance_event" '$1==e {n++} END {print n+0}' "$BP_MEMBER_EVENTS")" != 1 ]; then
  echo "PHX-L-CORE FINANCE_LEDGER_ROLLBACK_SETUP_INVALID: initial signed payment not durably visible: $phx_finance_first_reply" >&2
  exit 2
fi
# Only the financial files are rolled back: controller policy remains
# enabled and the older financial snapshot remains structurally valid.
cp "$T/finance-older-members.tsv" "$BP_MEMBERS"
cp "$T/finance-older-events.tsv" "$BP_MEMBER_EVENTS"
cp "$T/finance-older-revision" "$BP_MEMBER_REVISION"
[ "$(printf '%s' "$(bp_member_line phxfinance)" | cut -f8)" = 0 ] &&
[ -z "$(bp_member_event_line "$phx_finance_event")" ] || {
  echo 'PHX-L-CORE FINANCE_LEDGER_ROLLBACK_SETUP_INVALID: old snapshot not restored' >&2
  exit 2
}
phx_finance_before="$(phx_ctl_digest)"
phx_finance_retry_proof="$(proof_for "$phx_finance_hash" "$phx_finance_retry_nonce")"
phx_finance_retry_reply="$(call_vendo member_bank "$phx_finance_retry_nonce" 30 \
  "phxfinance:$phx_finance_event:$phx_finance_retry_proof")"
if printf '%s' "$phx_finance_retry_reply" | grep -Fq '"ok":true' ||
   [ "$(phx_ctl_digest)" != "$phx_finance_before" ]; then
  echo "PHX-L-CORE FINANCE_LEDGER_ROLLBACK_RED: previously committed signed event re-ACKed or re-credited after old valid financial snapshot restored: $phx_finance_retry_reply" >&2
  phx_finance_rollback_failures=1
else
  echo 'PHX-L-CORE FINANCE_LEDGER_ROLLBACK_PASS: previously committed event not re-ACKed after old valid financial snapshot'
  phx_finance_rollback_failures=0
fi

# PHX-L-CORE P0 #31 TEST-FIRST: BP_RUN is volatile. This is a simulated
# tmpfs/runtime-directory reset after a real sourced controller writer
# post-rename failure, NOT a router reboot or physical power interruption.
# New signed paid admissions must stay blocked even if controllers.tsv still
# contains a locally visible enabled row. No independent witness exists yet.
phx_recovery_failures=0
[ -f "$BP_RUN/controller-update-unsettled" ] &&
[ "$(printf '%s' "$(bp_controller_line softtimer-01)" | cut -f2)" = 1 ] || {
  echo 'PHX-L-CORE CONTROLLER_COLD_RUNTIME_SETUP_INVALID: no ambiguous enabled row and runtime barrier' >&2
  exit 2
}
rm -rf "$BP_RUN"
mkdir -p "$BP_RUN"
phx_recovery_before="$(phx_ctl_digest)"
phx_recovery_reply="$(call_vendo member_bank "$phx_crash_nonce" 30 "$phx_crash_target")"
if ! printf '%s' "$phx_recovery_reply" | grep -Fq '"ok":false' ||
   [ "$(phx_ctl_digest)" != "$phx_recovery_before" ]; then
  echo "PHX-L-CORE CONTROLLER_COLD_RUNTIME_RED: signed member_bank accepted after simulated BP_RUN loss: $phx_recovery_reply" >&2
  phx_recovery_failures=$((phx_recovery_failures+1))
else
  echo 'PHX-L-CORE CONTROLLER_COLD_RUNTIME_PASS: signed member_bank denied after simulated BP_RUN loss'
fi

# Independent second path: injected sync EIO, locally visible enabled row,
# then simulated loss of runtime barrier before a new signed coin request.
phx_ctl_fresh_state cold-runtime-coin
phx_ctl_setup_coin
phx_ctl_config 0 0
bp_durable_sync() { return 74; }
phx_recovery_admin_rc=0
phx_ctl_config 1 1 || phx_recovery_admin_rc=$?
. "$BP_LIB"
if [ "$phx_recovery_admin_rc" -ne 8 ] ||
   [ ! -f "$BP_RUN/controller-update-unsettled" ] ||
   [ "$(printf '%s' "$(bp_controller_line softtimer-01)" | cut -f2)" != 1 ]; then
  echo 'PHX-L-CORE CONTROLLER_COLD_RUNTIME_SETUP_INVALID: coin sync fault not established' >&2
  exit 2
fi
rm -rf "$BP_RUN"
mkdir -p "$BP_RUN"
phx_recovery_before="$(phx_ctl_digest)"
phx_recovery_reply="$(call_vendo coin 10000000000005f0 1 "$phx_ctl_target")"
if ! printf '%s' "$phx_recovery_reply" | grep -Fq '"ok":false' ||
   [ "$(phx_ctl_digest)" != "$phx_recovery_before" ]; then
  echo "PHX-L-CORE CONTROLLER_COLD_RUNTIME_RED: signed coin accepted after simulated BP_RUN loss: $phx_recovery_reply" >&2
  phx_recovery_failures=$((phx_recovery_failures+1))
else
  echo 'PHX-L-CORE CONTROLLER_COLD_RUNTIME_PASS: signed coin denied after simulated BP_RUN loss'
fi

# Restore a formerly valid enabled registry snapshot after a real successful
# admin disable. This is a synthetic OLD VALID SNAPSHOT rollback, NOT an
# actual flash recovery or proof of a durable independent revision witness.
for phx_recovery_action in member_bank coin; do
  phx_ctl_fresh_state "valid-snapshot-rollback-$phx_recovery_action"
  if [ "$phx_recovery_action" = coin ]; then
    phx_ctl_setup_coin
    phx_recovery_target="$phx_ctl_target"
    phx_recovery_pulses=1
  else
    bp_member_lock
    bp_member_create phxrollback "Controller rollback fixture" 'fixture-pass-123' fixture >/dev/null
    bp_member_unlock
    phx_recovery_nonce=10000000000005f1
    phx_recovery_hash="$(printf '%s' "$(bp_member_line phxrollback)" | cut -f6)"
    phx_recovery_proof="$(proof_for "$phx_recovery_hash" "$phx_recovery_nonce")"
    phx_recovery_target="phxrollback:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeef:$phx_recovery_proof"
    phx_recovery_pulses=30
  fi
  phx_recovery_snapshot="$T/old-valid-controller-$phx_recovery_action.tsv"
  cp "$BP_CONTROLLERS" "$phx_recovery_snapshot"
  phx_recovery_old_rev="$(printf '%s' "$(bp_controller_line softtimer-01)" | cut -f15)"
  phx_ctl_config 0 0
  phx_recovery_new_rev="$(printf '%s' "$(bp_controller_line softtimer-01)" | cut -f15)"
  [ "$phx_recovery_new_rev" -gt "$phx_recovery_old_rev" ] || {
    echo 'PHX-L-CORE CONTROLLER_ROLLBACK_SETUP_INVALID: disable did not advance revision' >&2
    exit 2
  }
  cp "$phx_recovery_snapshot" "$BP_CONTROLLERS"
  [ "$(printf '%s' "$(bp_controller_line softtimer-01)" | cut -f2)" = 1 ] || {
    echo 'PHX-L-CORE CONTROLLER_ROLLBACK_SETUP_INVALID: old enabled snapshot not restored' >&2
    exit 2
  }
  phx_recovery_before="$(phx_ctl_digest)"
  if [ "$phx_recovery_action" = coin ]; then phx_recovery_nonce=10000000000005f2; fi
  phx_recovery_reply="$(call_vendo "$phx_recovery_action" "$phx_recovery_nonce" "$phx_recovery_pulses" "$phx_recovery_target")"
  if ! printf '%s' "$phx_recovery_reply" | grep -Fq '"ok":false' ||
     [ "$(phx_ctl_digest)" != "$phx_recovery_before" ]; then
    echo "PHX-L-CORE CONTROLLER_VALID_ROLLBACK_RED: $phx_recovery_action accepted after previously disabled registry was rolled back: $phx_recovery_reply" >&2
    phx_recovery_failures=$((phx_recovery_failures+1))
  else
    echo "PHX-L-CORE CONTROLLER_VALID_ROLLBACK_PASS: $phx_recovery_action denied after old enabled snapshot rollback"
  fi
done
[ "$phx_recovery_failures" -eq 0 ] || exit 1

echo 'BlazePwifi centralized SoftTimer member checks passed'
