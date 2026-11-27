#!/bin/sh
# Run a tiny local Git-history integration test for handover freshness.
# Verifies both correct acceptance and that stale docs CANNOT silently pass.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM

P="$TMP/experiment/openwrt/BlazePwifi"
mkdir -p "$P/tests" "$P/docs/handover" "$P/openwrt/rootfs/usr/lib/blazepwifi"
cp "$ROOT/tests/handover_gate.sh" "$P/tests/handover_gate.sh"
printf '## AUTHORITATIVE LIVE LINKS\n' > "$P/PROJECT_HANDOVER.md"
printf '## NEXT EXACT ACTION\n' > "$P/docs/handover/CURRENT_STATE.md"
printf '## 2026-10-08 — initial\n' > "$P/docs/handover/CHANGE_LEDGER.md"
printf '## Mandatory continuous transaction log\n' > "$P/docs/handover/HANDOVER_POLICY.md"
printf '# baseline source\n' > "$P/openwrt/rootfs/usr/lib/blazepwifi/demo.sh"
git -C "$TMP" init -q -b main
git -C "$TMP" config user.name 'handover-ci'
git -C "$TMP" config user.email 'handover-ci@example.invalid'
git -C "$TMP" add .
git -C "$TMP" commit -qm 'initial source and fully synced handover'

# 1. Exact co-committed source/handover baseline must pass.
sh "$P/tests/handover_gate.sh"

# 2. A new source commit without handover MUST fail closed.
printf '# billable source change\n' >> "$P/openwrt/rootfs/usr/lib/blazepwifi/demo.sh"
git -C "$TMP" add .
git -C "$TMP" commit -qm 'source updated without live handover'
if sh "$P/tests/handover_gate.sh" > "$TMP/stale.log" 2>&1; then
    echo 'handover regression: stale docs were falsely accepted' >&2
    exit 1
fi
grep -q 'source/workflow changes newer than' "$TMP/stale.log" ||
    { cat "$TMP/stale.log" >&2; echo 'handover regression: wrong failure reason' >&2; exit 1; }

# 3. Updating only the root handover must NOT bypass current/ledger checks.
printf 'Root updated\n' >> "$P/PROJECT_HANDOVER.md"
git -C "$TMP" add .
git -C "$TMP" commit -qm 'root handover updated only'
if sh "$P/tests/handover_gate.sh" > "$TMP/partial.log" 2>&1; then
    echo 'handover regression: partial handover accepted' >&2
    exit 1
fi

# 4. Updating live state AND ledger restores a valid checkpoint.
printf 'Source commit reconciled\n' >> "$P/docs/handover/CURRENT_STATE.md"
printf 'Source commit and test recorded\n' >> "$P/docs/handover/CHANGE_LEDGER.md"
git -C "$TMP" add .
git -C "$TMP" commit -qm 'sync live state and ledger'
sh "$P/tests/handover_gate.sh"

echo 'Handover gate history tests passed: fresh / stale blocked / partial blocked / fully resynced'
