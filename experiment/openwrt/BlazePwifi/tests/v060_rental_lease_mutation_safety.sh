#!/bin/sh
# RENT-0648: real rental library paid add/expiry with synthetic EIO, no live data.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rental-mutations-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init
clock="$(bp_now)"
printf 'dev01\tfictional-token-1\t%s\tFictional Phone\t1000\n' "$((clock+300))" > "$BP_RENTAL_DEVICES"
printf 'dev02\tfictional-token-2\t%s\tOther Phone\t1000\n' "$((clock+1200))" >> "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
lease() { awk -F '\t' -v d="$1" '$1==d {print $3;exit}' "$BP_RENTAL_DEVICES"; }
sha() { sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1; }

# Active paid time must not be silently destroyed by a one-click admin expire.
before="$(sha)"
set +e
bp_rental_lease_expire dev01 > "$T/denied" 2>&1
rc=$?
set -e
[ "$rc" -eq 6 ] || { echo "unconfirmed paid expiry accepted ($rc)" >&2;exit 1; }
[ "$(sha)" = "$before" ] && [ ! -e "$BP_PAID_UNCERTAIN" ]
[ "$(lease dev02)" = "$((clock+1200))" ]

# New time addition successfully writes both lease and audit before ACK.
added="$(bp_rental_lease_add dev01 120)"
[ "$added" -eq "$((clock+420))" ] || { echo "incorrect synthetic lease addition" >&2;exit 1; }
[ "$(lease dev01)" = "$added" ]
grep -q "$(printf '\tlease_add$')" "$BP_RENTAL_EVENTS"
[ ! -e "$BP_PAID_UNCERTAIN" ]

# File replacement failed after pending marker: never emit newly credited
# expiry and never let the next paid operation proceed automatically.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */rental-devices.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
before="$(sha)"
set +e
bp_rental_lease_add dev01 60 > "$T/failed-write" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] || { echo "rental add storage EIO falsely acknowledged ($rc)" >&2;exit 1; }
[ "$(sha)" = "$before" ]
[ -f "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/mv";hash -r 2>/dev/null || true
set +e
bp_rental_lease_add dev01 60 >"$T/denied-retry" 2>&1
rc=$?
set -e
[ "$rc" -eq 9 ] || { echo "ambiguous rental add wasn't quarantined ($rc)" >&2;exit 1; }
[ "$(lease dev02)" = "$((clock+1200))" ]

# Clear an invented marker ONLY within isolated synthetic /tmp test.
rm "$BP_PAID_UNCERTAIN"
# Failure of event append AFTER paid lease changed: no ACK and marker held.
set +e
(
  bp_rental_event_log() { return 8; }
  bp_rental_lease_add dev01 30 >"$T/failed-audit" 2>&1
)
rc=$?
set -e
[ "$rc" -eq 8 ] || { echo "rental add audit EIO falsely acknowledged ($rc)" >&2;exit 1; }
[ -f "$BP_PAID_UNCERTAIN" ]
set +e
bp_rental_lease_expire dev01 CONFIRM_FORFEIT >"$T/denied-retry" 2>&1
rc=$?
set -e
[ "$rc" -eq 9 ] || { echo "pending audit did not block paid time forfeiture ($rc)" >&2;exit 1; }

rm "$BP_PAID_UNCERTAIN"
# Explicit confirmed forfeiture succeeds and records how many seconds were
# canceled, with no unrelated device changes.
before_other="$(lease dev02)"
expired="$(bp_rental_lease_expire dev01 CONFIRM_FORFEIT)"
[ "$expired" -le "$(bp_now)" ]
[ "$(lease dev02)" = "$before_other" ]
grep -q 'confirmed_forfeit_seconds:' "$BP_RENTAL_EVENTS"
[ ! -e "$BP_PAID_UNCERTAIN" ]

# Actually expired leases can still be closed normally with no override.
closed="$(bp_rental_lease_expire dev01)"
[ "$closed" -le "$(bp_now)" ]
[ "$(lease dev02)" = "$before_other" ]

ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
grep -Fq 'confirm_forfeit="$(bp_param confirm_forfeit)"' "$ADMIN"
grep -Fq 'paid rental time remains; explicit CONFIRM_FORFEIT authorization required' "$ADMIN"
grep -Fq 'rental time addition storage failed; operator reconciliation required' "$ADMIN"
echo 'RENT-0648 PASS: normal add/expire, no implicit live paid time forfeiture, explicitly confirmed audit, rename/receipt EIO quarantined, no false ACK'
echo 'NOT production: OpenWrt v1 rental leases/audit use separate TSVs; real v2 crash-atomic signed journal, migration and hardware acceptance missing'
