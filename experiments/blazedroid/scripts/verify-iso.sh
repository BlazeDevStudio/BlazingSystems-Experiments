#!/usr/bin/env bash
# Structural checks only. This does NOT prove a functioning Android boot or installer.
set -euo pipefail
[[ $# -eq 1 && -s "$1" ]] || { echo "ISO missing or empty" >&2; exit 1; }
command -v xorriso >/dev/null || { echo "xorriso missing" >&2; exit 1; }
report="$(xorriso -indev "$1" -report_el_torito plain 2>&1)" || { echo "$report" >&2; exit 1; }
grep -qi 'El Torito' <<< "$report" || { echo "No El Torito catalog detected" >&2; exit 1; }
grep -Eqi 'EFI|UEFI' <<< "$report" || { echo "No EFI boot entry detected" >&2; exit 1; }
echo "ISO optical structure and EFI boot catalog present (boot NOT tested)."
