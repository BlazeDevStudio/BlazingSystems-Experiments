#!/bin/sh
# PAY-0780 / #32: exercise the real installed v1 rental coin writer at the
# receipt-corpus size boundary. All state is disposable and synthetic.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-pay0780-XXXXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -m 700 "$BP_STATE" "$BP_RUN"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
export BP_STATE BP_RUN BP_RENTAL_DEVICES BP_RENTAL_EVENTS
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf '600' || printf ''; }
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init
printf 'dev01\tfake-secret\t0\tSynthetic Device\t0\n' > "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"

# A valid nonfinancial receipt corpus has exactly ONE byte less room than
# the payment record needs. Old code accepted and ACKed, permanently making
# subsequent paid receipt scans fail their own hard size ceiling.
python3 - "$BP_RENTAL_EVENTS" <<'PY'
import hashlib
from pathlib import Path
import sys

path = Path(sys.argv[1])
limit = 4190208
digest = hashlib.sha256(b"rental|controller01|nonce01|target01").hexdigest()
paid = f"r:{digest}\tdev01\t124056\t123456\tp:1\n".encode("ascii")
target = limit - len(paid) + 1
prefix = b"a:capacity-pad\tdev01\t"
suffix = b"\t123456\tadmin\n"
with path.open("wb") as out:
    for i in range(60000):
        out.write(f"a:{i}\tdev01\tunrelated-audit-record\t123456\tadmin\n".encode("ascii"))
    remaining = target - out.tell() - len(prefix) - len(suffix)
    assert remaining > 0
    out.write(prefix + b"x" * remaining + suffix)
assert path.stat().st_size == target
PY
bp_rental_paid_receipt_snapshot "r:unmatched" >"$T/preflight"
[ ! -s "$T/preflight" ]
before="$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")"
rc=0
bp_rental_apply_coin dev01 controller01 nonce01 target01 1 >"$T/rejected" 2>"$T/err" || rc=$?
[ "$rc" -ne 0 ] && [ ! -s "$T/rejected" ] || {
  echo "PAY-0780 FAIL: oversized paid receipt was acknowledged (rc=$rc)" >&2
  exit 1
}
[ "$before" = "$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")" ] &&
[ ! -e "$BP_STATE/paid-state-uncertain" ] || {
  echo 'PAY-0780 FAIL: quota refusal mutated lease/receipt or quarantined clean state' >&2
  exit 1
}

# Remove exactly one padding byte: now payment reaches, but never exceeds,
# the old signed receipt scan ceiling. Its lost-ACK replay must still work.
python3 - "$BP_RENTAL_EVENTS" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
data = path.read_bytes()
suffix = b"\t123456\tadmin\n"
assert data.endswith(suffix)
index = len(data) - len(suffix) - 1
assert data[index:index + 1] == b"x"
path.write_bytes(data[:index] + data[index + 1:])
PY
[ "$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)" = "$(printf 'credited\t124056')" ]
[ "$(wc -c < "$BP_RENTAL_EVENTS")" -eq 4190208 ]
[ "$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)" = "$(printf 'duplicate\t124056')" ]
before="$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")"
rc=0
bp_rental_apply_coin dev01 controller02 nonce02 target02 1 >"$T/full" 2>"$T/fullerr" || rc=$?
[ "$rc" -ne 0 ] && [ ! -s "$T/full" ] &&
[ "$before" = "$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")" ] &&
[ ! -e "$BP_STATE/paid-state-uncertain" ] || {
  echo 'PAY-0780 FAIL: full corpus caused another paid mutation/ACK' >&2
  exit 1
}
echo 'PAY-0780 PASS: real installed rental writer refuses overflow before lease and preserves exact-fit credit/replay.'
echo 'NOT ATOMIC: separate v1 lease and receipt writes, independent witness and physical acceptance still pending.'
