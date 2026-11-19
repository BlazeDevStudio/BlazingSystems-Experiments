#!/usr/bin/env python3
"""Guard the release-owned exact-source ESP32 3.3.13/4.0.0 compatibility workflow."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/phx-release-esp32-core-compatibility.yml"
HARDWARE_SOURCE_SHA = "0e5514adb0088649eca8bec9df6215faa50b556c"
HARDWARE_SKETCH_PATH = (
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
)
HARDWARE_SKETCH_BLOB = "c29483f0761ca6e2db0573bd12d6bfa502f12434"
CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
ARDUINO_SETUP_SHA = "b3cda96fddef6af6c56b4c5efb5c47e2357935db"


def fail(message: str) -> int:
    print(f"PHX-RELEASE-ESP32-COMPAT-RED: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if not WORKFLOW.is_file():
        return fail("missing exact-source ESP32 core compatibility workflow")

    content = WORKFLOW.read_text(encoding="utf-8")
    required = (
        HARDWARE_SOURCE_SHA,
        HARDWARE_SKETCH_PATH,
        HARDWARE_SKETCH_BLOB,
        'esp32_core: ["3.3.13", "4.0.0"]',
        'arduino-cli core install "esp32:esp32@\u0024{{ matrix.esp32_core }}"',
        "arduino-cli compile --fqbn esp32:esp32:esp32",
        "hardware-source/",
        "persist-credentials: false",
        "contents: read",
        "cancel-in-progress: false",
        "workflow_dispatch:",
        "pull_request:",
        '"draft/softtimer-future-release-signing-pipeline-20261029"',
    )
    missing = [value for value in required if value not in content]
    if missing:
        return fail("compatibility workflow is missing required contract values: " + ", ".join(missing))

    if content.count(f"ref: {HARDWARE_SOURCE_SHA}") != 1:
        return fail("hardware source must be checked out exactly once at the pinned commit")
    if content.count(f'EXPECTED_SOURCE_SHA: "{HARDWARE_SOURCE_SHA}"') != 1:
        return fail("workflow must independently assert the pinned hardware source HEAD")
    if content.count(f'EXPECTED_SKETCH_BLOB: "{HARDWARE_SKETCH_BLOB}"') != 1:
        return fail("workflow must independently assert the exact sketch Git blob")
    if content.count("persist-credentials: false") != 2:
        return fail("both checkouts must disable persisted credentials")

    success_marker = (
        "PHX-ESP32-COMPATIBILITY-PASS: core=%s source=%s "
        "sketch_blob=%s binary_sha256=%s"
    )
    if success_marker not in content:
        return fail("workflow must emit the per-core build provenance marker")
    if '"$${{ matrix.esp32_core }}"' in content:
        return fail("build marker adds a second dollar before the matrix expression; Bash treats it as a positional parameter")
    if '"${{ matrix.esp32_core }}"' not in content:
        return fail("build marker must print the matrix core without shell positional expansion")

    pin_guard_path = ROOT / ".github/scripts/test_release_artifact_action_pins.py"
    if not pin_guard_path.is_file():
        return fail("missing immutable-action pin guard")
    pin_guard = pin_guard_path.read_text(encoding="utf-8")
    workflow_marker = '".github/workflows/phx-release-esp32-core-compatibility.yml": {'
    start = pin_guard.find(workflow_marker)
    if start < 0:
        return fail("immutable-action pin guard does not include the compatibility workflow")
    end = pin_guard.find("    },", start)
    if end < 0:
        return fail("compatibility workflow action-pin entry is malformed")
    pin_entry = pin_guard[start:end]
    if '"actions/checkout": 2' not in pin_entry or '"arduino/setup-arduino-cli": 1' not in pin_entry:
        return fail("compatibility workflow action-pin counts are not 2 checkout + 1 Arduino setup")

    action_refs = re.findall(
        r"(?m)^\s*-\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)",
        content,
    )
    expected = {
        "actions/checkout": (CHECKOUT_SHA, 2),
        "arduino/setup-arduino-cli": (ARDUINO_SETUP_SHA, 1),
    }
    found: dict[str, list[str]] = {}
    for name, ref in action_refs:
        found.setdefault(name, []).append(ref)
    if set(found) != set(expected):
        return fail(f"unexpected external actions: {sorted(set(found) ^ set(expected))}")
    for name, (sha, count) in expected.items():
        refs = found.get(name, [])
        if len(refs) != count or any(ref != sha or not re.fullmatch(r"[0-9a-f]{40}", ref) for ref in refs):
            return fail(f"{name} must use {count} immutable invocation(s) at {sha}; found {refs}")

    forbidden = (
        "actions/upload-artifact",
        "contents: write",
        "gh release",
        "esptool",
        "espflash",
        "${{ secrets.",
    )
    present = [value for value in forbidden if value in content]
    if present:
        return fail("compatibility workflow must remain read-only/build-only: " + ", ".join(present))

    print(
        "PHX-RELEASE-ESP32-COMPAT-PASS: exact hardware source, sketch blob, "
        "read-only permissions, immutable actions and 3.3.13/4.0.0 matrix"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
