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

echo 'BlazePwifi centralized SoftTimer member checks passed'
