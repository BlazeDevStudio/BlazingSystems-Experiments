#!/usr/bin/env bash
set -euo pipefail
ROOT="${GITHUB_WORKSPACE:-$(cd "$(dirname "$0")/../../.." && pwd)}"
# Video-specific smoke is independent of Android 35's collapsed incoming
# CallStyle notification. It uses a foreground receiver's genuine Answer.
source "$ROOT/experiment/apps/LAN-Messenger/tool/android_dual_lan_smoke.sh"
LAN_MESSENGER_SCENARIO=video python3 "$ROOT/.github/scripts/lan-messenger/dual_android_call_ui.py"
echo "PASS: dual decoded camera video, PiP expand and remote-hangup PiP close" >>"$GITHUB_STEP_SUMMARY"
