#!/usr/bin/env bash
# Two real Android peers. Force-stop one DURING a connected call; fail unless
# the survivor autonomously ends the call after its bounded reconnect grace.
set -euo pipefail
ROOT="$GITHUB_WORKSPACE"
python3 -m py_compile "$ROOT/.github/scripts/lan-messenger/dual_android_call_ui.py"
source "$ROOT/experiment/apps/LAN-Messenger/tool/android_dual_lan_smoke.sh"
LAN_MESSENGER_SCENARIO=peer-process-death python3 "$ROOT/.github/scripts/lan-messenger/dual_android_call_ui.py"
echo "PASS: process-death -> bounded orphan-call cleanup -> peer offline" >>"$GITHUB_STEP_SUMMARY"
