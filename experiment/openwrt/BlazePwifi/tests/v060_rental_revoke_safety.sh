#!/bin/sh
# RENT-0647: test the real rental lease revoke function on fictional /tmp data.
# NO live credits, devices, enrollment tokens, or signing material.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rental-revoke-XXXXXX)"
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
now="$(bp_now)"
entry() { printf '%s\t%s\t%s\t%s\t%s\n' "$1" "synthetic-secret-$1" "$2" "Fictional Phone" "$now"; }
entry dev01 "$((now+3600))" > "$BP_RENTAL_DEVICES"
entry dev02 1000 >> "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
cat > "$BP_RENTAL_POLICY" <<'POLICY'
dev01	synthetic-policy
dev02	synthetic-policy
POLICY
before="$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_POLICY")"
refuse() {
  want="$1"; shift
  set +e
  bp_rental_device_revoke "$@" > "$T/error" 2>&1
  rc=$?
  set -e
  if [ "$rc" -ne "$want" ]; then
    echo "wrong refusal status: wanted $want, saw $rc for $*" >&2
    cat "$T/error" >&2
    exit 1
  fi
}
# Live paid time must be preserved, including all policy/binding records.
refuse 6 dev01
[ "$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_POLICY")" = "$before" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
[ "$(cut -f3 "$BP_RENTAL_DEVICES" | head -n1)" = "$((now+3600))" ]

# PAY-0782: exercise a real synthetic payment in the gap after revocation
# preflight but before it acquires the shared paid writer lock. Revocation
# must reread paid time under that lock rather than delete freshly purchased
# seconds from another authorized transaction.
bp_paid_begin() {
  (
    . "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
    bp_rental_lease_add dev02 600 >/dev/null
  ) || return 8
  . "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
  bp_paid_begin
}
refuse 6 dev02
[ "$(bp_rental_device_line dev02 | cut -f3)" -gt "$now" ] || {
  echo 'PAY-0782 concurrent purchased time missing' >&2; exit 1;
}
[ ! -e "$BP_PAID_UNCERTAIN" ] || {
  echo 'PAY-0782 read-only refusal left uncertainty' >&2; exit 1;
}
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_rental_device_write dev02 synthetic-secret-dev02 1000 'Fictional Phone' "$now"

# Expired non-paid lease may be revoked; unrelated active and expired
# leases, audit and policy records must be left intact.
bp_rental_device_revoke dev02
[ -z "$(bp_rental_device_line dev02)" ]
[ -n "$(bp_rental_device_line dev01)" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
grep -q "$(printf '\trevoke$')" "$BP_RENTAL_EVENTS" || {
  echo 'successful revoke missing audit event' >&2;exit 1;
}
[ "$(cut -f1 "$BP_RENTAL_POLICY")" = dev01 ]

# Cannot delete a device if the authoritative lease store is duplicated
# or incomplete. Never "repair" malformed live financial data by deleting.
entry dev01 "$((now+3600))" >> "$BP_RENTAL_DEVICES"
broken="$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)"
refuse 8 dev01
[ "$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)" = "$broken" ]
sed '$d' "$BP_RENTAL_DEVICES" > "$T/clean"
cp "$T/clean" "$BP_RENTAL_DEVICES"

# Simulate settlement on a fictional disposable device only.
bp_rental_device_write dev01 synthetic-secret-dev01 1000 "Fictional Phone" "$now"
# Failed first rename must not return a revocation ACK and must
# retain marker for authenticated operator reconciliation.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */rental-devices.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
before="$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)"
refuse 8 dev01
[ "$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)" = "$before" ]
[ -f "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/mv";hash -r 2>/dev/null || true
refuse 9 dev01
[ -n "$(bp_rental_device_line dev01)" ]

# Synthetic-only clearing of a fictional quarantine to test a second
# crash point; NEVER clear paid-state-uncertain on actual devices this way.
rm "$BP_PAID_UNCERTAIN"
(
  bp_rental_event_log() { return 8; }
  set +e
  bp_rental_device_revoke dev01 > "$T/event-error" 2>&1
  rc=$?
  set -e
  [ "$rc" -eq 8 ] || { echo "missing audit ACK incorrectly succeeded ($rc)" >&2;exit 1; }
)
[ -f "$BP_PAID_UNCERTAIN" ]
[ -z "$(bp_rental_device_line dev01)" ]
refuse 9 dev01

# UI error strings are important for a non-technical shop owner.
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
grep -Fq 'rental has active paid time; settle or transfer it before revoking' "$ADMIN"
grep -Fq 'rental revocation storage failed; operator reconciliation required' "$ADMIN"
grep -Fq 'paid state uncertain; operator reconciliation required' "$ADMIN"

echo 'RENT-0647 PASS: paid rental time cannot be revoked; expired device cleanly removed; failed rename/audit quarantined and retries refused'
echo 'NOT production certified: multi-file v1 removal still needs authenticated atomic journal, source-migration and physical powercut acceptance'
