#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM

# Execute the actual installer preflight in a disposable root; no /etc or
# customer files are used and the installer does not reach its write phase.
check_state(){
    ( eval "$(sed -n '/^RENTAL_BASE=/,/^TOKEN_FILE=/p' "$ROOT/install.sh" |
        sed "1s|^RENTAL_BASE=.*|RENTAL_BASE='$T/hub'|")" )
}

check_state || { echo 'FAIL: fresh installer state refused' >&2; exit 1; }
mkdir -p "$T/hub/state"
if check_state >/dev/null 2>&1; then
    echo 'FAIL: partial existing installer state accepted' >&2; exit 1
fi
for f in devices.tsv enroll.tsv policy.tsv events.tsv; do : > "$T/hub/state/$f"; done
check_state || { echo 'FAIL: complete existing installer state refused' >&2; exit 1; }
rm "$T/hub/state/devices.tsv"
if check_state >/dev/null 2>&1; then
    echo 'FAIL: installer recreated missing paid authority' >&2; exit 1
fi
test ! -e "$T/hub/state/devices.tsv" || {
    echo 'FAIL: installer preflight modified paid authority' >&2; exit 1;
}
: > "$T/hub/state/devices.tsv"
rm "$T/hub/state/enroll.tsv"
ln -s "$T/hub/state/devices.tsv" "$T/hub/state/enroll.tsv"
if check_state >/dev/null 2>&1; then
    echo 'FAIL: installer accepted symlinked token authority' >&2; exit 1
fi
echo 'Standalone rental installer state preflight PASS'
