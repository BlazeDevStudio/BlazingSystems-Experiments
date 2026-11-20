#!/usr/bin/env python3
"""Regression guard: quarantine workflow runs each hardware lab once, in its owned step."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
WORKFLOW = ROOT / ".github" / "workflows" / "phx-hardware-quarantine-byte-readback.yml"
COIN_PULSE_LAB = (
    Path(__file__).resolve().parent / "coin_pulse_capture_lab.py"
)
SELF_COMMAND = (
    "python3 experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/"
    "boot_polarity_workflow_wiring_lab.py"
)
BOOT_POLARITY_COMMAND = (
    "python3 experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/"
    "esp8266_boot_polarity_lab.py"
)
CONFIG_READ_FAILURE_COMMAND = (
    "python3 experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/"
    "config_load_read_failure_lab.py"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_nested_config_runner(coin_pulse_source: str) -> None:
    require(
        "config_load_read_failure_lab.py" not in coin_pulse_source,
        "coin-pulse lab must not rerun the workflow-owned config-read lab",
    )


def main() -> None:
    require(WORKFLOW.is_file(), "hardware quarantine workflow is missing")
    require(COIN_PULSE_LAB.is_file(), "coin-pulse lab is missing")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    coin_pulse_source = COIN_PULSE_LAB.read_text(encoding="utf-8")
    lines = workflow.splitlines()

    for command, label in (
        (SELF_COMMAND, "workflow-wiring guard"),
        (BOOT_POLARITY_COMMAND, "ESP8266 boot-polarity lab"),
        (CONFIG_READ_FAILURE_COMMAND, "ESP8266 config-read failure lab"),
    ):
        matches = [line for line in lines if command in line]
        require(len(matches) == 1, f"{label} must be invoked exactly once")
        require(not matches[0].lstrip().startswith("#"), f"{label} invocation is commented out")

    assert_no_nested_config_runner(coin_pulse_source)
    injected_duplicate = (
        coin_pulse_source
        + '\nsubprocess.run([sys.executable, "config_load_read_failure_lab.py"], check=True)\n'
    )
    try:
        assert_no_nested_config_runner(injected_duplicate)
    except AssertionError:
        print("MUTATION_REJECTED nested-config-read-lab-runner")
    else:
        raise AssertionError("nested config-read lab mutation was not rejected")

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
    print("ESP8266_CONFIG_READ_FAILURE_WORKFLOW_WIRING=PASS")
    print("ESP8266_CONFIG_READ_FAILURE_RUN_ONCE=PASS")


if __name__ == "__main__":
    main()
