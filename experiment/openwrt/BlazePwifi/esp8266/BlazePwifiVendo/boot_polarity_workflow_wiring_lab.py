#!/usr/bin/env python3
"""Regression guard: the quarantine workflow must execute the ESP8266 cold-boot polarity lab."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
WORKFLOW = ROOT / ".github" / "workflows" / "phx-hardware-quarantine-byte-readback.yml"
SELF_COMMAND = (
    "python3 experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/"
    "boot_polarity_workflow_wiring_lab.py"
)
BOOT_POLARITY_COMMAND = (
    "python3 experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/"
    "esp8266_boot_polarity_lab.py"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    require(WORKFLOW.is_file(), "hardware quarantine workflow is missing")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    lines = workflow.splitlines()

    for command, label in (
        (SELF_COMMAND, "workflow-wiring guard"),
        (BOOT_POLARITY_COMMAND, "ESP8266 boot-polarity lab"),
    ):
        matches = [line for line in lines if command in line]
        require(len(matches) == 1, f"{label} must be invoked exactly once")
        require(not matches[0].lstrip().startswith("#"), f"{label} invocation is commented out")

    require("set -euo pipefail" in workflow,
            "multi-lab quarantine step must fail fast")
    require("continue-on-error: true" not in workflow,
            "hardware safety labs must not be allowed to fail silently")
    for marker in (
        'echo "SIMULATED_ONLY=1"',
        'echo "PHYSICAL_POWER_CUT_VERIFIED=0"',
        'echo "FINANCIAL_PRODUCTION_AUTHORIZED=0"',
    ):
        require(marker in workflow, f"production-readiness boundary marker missing: {marker}")

    print("ESP8266_BOOT_POLARITY_WORKFLOW_WIRING=PASS")


if __name__ == "__main__":
    main()
