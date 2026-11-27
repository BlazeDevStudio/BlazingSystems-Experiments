#!/bin/sh
# Fail closed when the canonical handover, live state or change ledger
# predates a meaningful BlazePwifi/Windows/BlazeRental source change.
# This gate does NOT claim the prose is correct; it makes omissions visible.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
TOP="$(CDPATH= cd -- "$ROOT/../../.." && pwd)"
cd "$TOP"
P=experiment/openwrt/BlazePwifi
W=experiment/windows/BlazePisonet-SoftTimer
HANDOVER="$P/PROJECT_HANDOVER.md"
CURRENT="$P/docs/handover/CURRENT_STATE.md"
LEDGER="$P/docs/handover/CHANGE_LEDGER.md"
POLICY="$P/docs/handover/HANDOVER_POLICY.md"

for f in "$HANDOVER" "$CURRENT" "$LEDGER" "$POLICY"; do
    [ -s "$f" ] || { echo "handover gate: missing or empty $f" >&2; exit 1; }
done
grep -Fq '## AUTHORITATIVE LIVE LINKS' "$HANDOVER" ||
    { echo "handover gate: PROJECT_HANDOVER has no current entrypoint" >&2; exit 1; }
grep -Fq '## NEXT EXACT ACTION' "$CURRENT" ||
    { echo "handover gate: CURRENT_STATE has no precise next action" >&2; exit 1; }
grep -Fq '## 2026-' "$LEDGER" ||
    { echo "handover gate: CHANGE_LEDGER has no dated entries" >&2; exit 1; }
grep -Fq '## Mandatory continuous transaction log' "$POLICY" ||
    { echo "handover gate: mandatory handover policy missing" >&2; exit 1; }

# Full history is essential. A shallow checkout can incorrectly report
# the latest handover to be the only visible commit and conceal changes.
[ "$(git rev-parse --is-shallow-repository)" = false ] ||
    { echo "handover gate: fetch-depth: 0 is mandatory" >&2; exit 1; }

for doc in "$HANDOVER" "$CURRENT" "$LEDGER"; do
    checkpoint="$(git log -1 --format=%H HEAD -- "$doc")"
    [ -n "$checkpoint" ] || {
        echo "handover gate: no committed history for $doc" >&2
        exit 1
    }
    # List the changes made *after* this doc's last update. The checkpoint
    # commit itself is accepted; source and handover can be co-committed.
    pending="$(git diff --name-only "$checkpoint" HEAD -- "$P" "$W" .github/workflows |
        awk -v p="$P" -v w="$W" '
          index($0, p "/docs/handover/") == 1 {next}
          $0 == p "/PROJECT_HANDOVER.md" {next}
          index($0, p "/") == 1 || index($0, w "/") == 1 {print; next}
          $0 ~ /^\.github\/workflows\/(blazepwifi|blazerental|blazepisonet)/ {print}
        ')"
    if [ -n "$pending" ]; then
        echo "handover gate: source/workflow changes newer than $doc" >&2
        echo "handover gate: last checkpoint commit $checkpoint" >&2
        printf '%s\n' "$pending" >&2
        echo "handover gate: update the live record and exact evidence AFTER the code change; do not bypass this check" >&2
        exit 1
    fi
done

echo "BlazePwifi mandatory continuous handover freshness gate passed"
