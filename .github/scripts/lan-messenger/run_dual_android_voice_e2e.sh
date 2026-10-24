#!/usr/bin/env bash
# Called inside reactivecircus/android-emulator-runner, so both AVDs remain alive
# throughout discovery, real user-interface Answer, WebRTC and hangup tests.
set -euo pipefail
ROOT="$GITHUB_WORKSPACE"
python3 -m py_compile "$ROOT/.github/scripts/lan-messenger/dual_android_call_ui.py"
# Source the network test in THIS shell. Its EXIT trap owns the second AVD;
# executing in a subshell would kill emulator-5556 before the call begins.
source "$ROOT/experiment/apps/LAN-Messenger/tool/android_dual_lan_smoke.sh"
LAN_MESSENGER_SCENARIO=background-first python3 "$ROOT/.github/scripts/lan-messenger/dual_android_call_ui.py"
echo "PASS: dual Android LAN discovery plus foreground voice call UI test."
echo "Android two-emulator voice call and Answer: PASS" >>"$GITHUB_STEP_SUMMARY"
