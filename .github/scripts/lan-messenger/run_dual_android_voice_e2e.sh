#!/usr/bin/env bash
# Called inside reactivecircus/android-emulator-runner, so both AVDs remain alive
# throughout discovery, real user-interface Answer, WebRTC and hangup tests.
set -euo pipefail
ROOT="$GITHUB_WORKSPACE"
python3 -m py_compile "$ROOT/.github/scripts/lan-messenger/dual_android_call_ui.py"
bash "$ROOT/experiment/apps/LAN-Messenger/tool/android_dual_lan_smoke.sh"
python3 "$ROOT/.github/scripts/lan-messenger/dual_android_call_ui.py"
echo "PASS: dual Android LAN discovery plus foreground voice call UI test."
echo "Android two-emulator voice call and Answer: PASS" >>"$GITHUB_STEP_SUMMARY"
