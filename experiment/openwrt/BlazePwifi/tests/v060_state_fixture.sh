#!/bin/sh
# Synthetic prepaid/identity backup+restore integrity tests; NEVER live state.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
TOOL="$ROOT/tools/state-fixture.py"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT INT TERM
SRC="$T/synthetic"
SNAP="$T/offdevice-test-snapshot"
RESTORED="$T/recovered-new"
mkdir -p "$SRC/etc/blazepwifi/state/targets" "$SRC/etc/blazepwifi/portal" "$SRC/etc/config"
printf 'BLAZE-SYNTHETIC-FIXTURE-ONLY\n' > "$SRC/.blaze-fixture-only"
printf "config main 'main'\n option billing 'fixture-only'\n" > "$SRC/etc/config/blazepwifi"
printf 'fake-device-0001\t3600\t0\n' > "$SRC/etc/blazepwifi/state/accounts.tsv"
printf 'fake-voucher-0001\tunused\t600\n' > "$SRC/etc/blazepwifi/state/vouchers.tsv"
printf 'fake-member-0001\t2400\n' > "$SRC/etc/blazepwifi/state/members.tsv"
printf 'fake-event-0001\tcredited\t300\n' > "$SRC/etc/blazepwifi/state/member-events.tsv"
printf 'fake-identity-0001\tsecret-DONT-PRINT\n' > "$SRC/etc/blazepwifi/state/rental-devices.tsv"
printf 'fake-device-0001\tactive\n' > "$SRC/etc/blazepwifi/state/targets/fake-0001"
printf 'fake-admin\tverifier-DONT-PRINT\n' > "$SRC/etc/blazepwifi/state/admin-users.tsv"
printf '<h1>synthetic portal</h1>\n' > "$SRC/etc/blazepwifi/portal/index.html"
printf 'synthetic-TLS-certificate\n' > "$SRC/etc/uhttpd.crt"
printf 'synthetic-TLS-key-DONT-PRINT\n' > "$SRC/etc/uhttpd.key"
chmod 600 "$SRC/etc/blazepwifi/state/"*.tsv "$SRC/etc/uhttpd.key" "$SRC/etc/config/blazepwifi"

python3 "$TOOL" snapshot --root "$SRC" --output "$SNAP" >"$T/log"
python3 "$TOOL" verify --backup "$SNAP" >>"$T/log"
python3 "$TOOL" restore --backup "$SNAP" --output "$RESTORED" >>"$T/log"
diff -rq "$SRC" "$RESTORED" >"$T/differences"
[ ! -s "$T/differences" ] || { cat "$T/differences" >&2; exit 1; }
[ "$(stat -c '%a' "$RESTORED/etc/blazepwifi/state/accounts.tsv")" = 600 ]
[ "$(stat -c '%a' "$RESTORED/etc/uhttpd.key")" = 600 ]
if grep -q 'DONT-PRINT' "$T/log"; then
  echo "Synthetic test secrets leaked into operator logs" >&2
  exit 1
fi

# Fail closed if overwriting previous snapshots or restored state.
if python3 "$TOOL" snapshot --root "$SRC" --output "$SNAP" >"$T/reject" 2>&1; then
  echo "Snapshot overwrite allowed" >&2; exit 1
fi
if python3 "$TOOL" restore --backup "$SNAP" --output "$RESTORED" >"$T/reject" 2>&1; then
  echo "Restore overwrote existing state" >&2; exit 1
fi

# Live/system/unknown filesystem roots and symlink escape are not permitted.
mkdir -p "$T/no-marker"
if python3 "$TOOL" snapshot --root "$T/no-marker" --output "$T/bad" >"$T/reject" 2>&1; then
  echo "Unmarked root accepted" >&2; exit 1
fi
if python3 "$TOOL" snapshot --root / --output "$T/bad" >"$T/reject" 2>&1; then
  echo "Host root was accepted" >&2; exit 1
fi
ln -s /etc/passwd "$SRC/etc/blazepwifi/state/link-escape"
if python3 "$TOOL" snapshot --root "$SRC" --output "$T/bad-link" >"$T/reject" 2>&1; then
  echo "Symlink escape was accepted" >&2; exit 1
fi
[ ! -e "$T/bad-link" ]
rm "$SRC/etc/blazepwifi/state/link-escape"

# Any changed paid-account record or injected extra file invalidates backup.
printf 'DUPLICATE-CREDIT\n' >> "$SNAP/files/etc/blazepwifi/state/accounts.tsv"
if python3 "$TOOL" verify --backup "$SNAP" >"$T/reject" 2>&1; then
  echo "Modified paid account silently verified" >&2; exit 1
fi
if python3 "$TOOL" restore --backup "$SNAP" --output "$T/bad-restore" >"$T/reject" 2>&1; then
  echo "Invalid paid account restored" >&2; exit 1
fi
[ ! -e "$T/bad-restore" ]
python3 -m py_compile "$TOOL"
echo "BlazePwifi synthetic fixture snapshot: complete data, perms, SHA-256, refusal, tampering and no-secret-log checks passed"
