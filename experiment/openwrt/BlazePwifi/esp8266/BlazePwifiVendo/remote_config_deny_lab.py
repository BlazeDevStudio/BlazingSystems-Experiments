#!/usr/bin/env python3
"""Source-extracted deny-only guard for the dormant remote-config entrypoint."""
from pathlib import Path
import re
import subprocess
import tempfile

from firmware_source_extract import extract_function, has_empty_string_assignment, mask_non_code

BLAZEPWIFI = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": BLAZEPWIFI / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def assert_source_contract(source: str, board: str) -> None:
    masked_source = mask_non_code(source)
    if len(re.findall(r"\bapplyRemoteConfig\s*\(", masked_source)) != 1:
        raise AssertionError(f"{board}: remote-config sentinel must remain definition-only")
    for helper in ("jsonString", "jsonTrue", "jsonInt"):
        if re.search(rf"\b{helper}\s*\(", masked_source):
            raise AssertionError(f"{board}: unauthenticated {helper} parser remains")
    if "remoteRevision" in masked_source:
        raise AssertionError(f"{board}: dormant remote revision state remains")
    apply_fn = extract_function(source, "void applyRemoteConfig(")
    masked_apply = mask_non_code(apply_fn)
    body_start = masked_apply.find("{")
    body_end = masked_apply.rfind("}")
    body = masked_apply[body_start + 1:body_end]
    if re.sub(r"\s+", "", body) != "(void)response;denyRemoteControl();":
        raise AssertionError(f"{board}: remote-config entrypoint is not deny-only")


def harness(write_fn: str, outputs_fn: str, deny_fn: str, apply_fn: str) -> str:
    return r"""
#include <iostream>
#include <string>
using String = std::string;
constexpr int HIGH = 1;
constexpr int LOW = 0;

bool controllerEnabled = true;
bool coinEnabled = true;
bool relayEnabled = true;
bool ledEnabled = true;
bool insertMode = true;
bool fsReady = true;
bool configStoreReady = true;
bool pendingReady = false;
bool runRelayActiveHigh = true;
bool runLedActiveHigh = true;
int runRelayPin = 26;
int runLedPin = 2;
int relayLevel = -1;
int ledLevel = -1;
std::string activeTarget = "target-00112233";

void digitalWrite(int pin, int level) {
    if (pin == runRelayPin) relayLevel = level;
    if (pin == runLedPin) ledLevel = level;
}

""" + write_fn + "\n" + outputs_fn + "\n" + deny_fn + "\n" + apply_fn + r"""

int main() {
    const String responses[] = {
        "",
        "{\"enabled\":1,\"coin_enabled\":1,\"relay_enabled\":1,\"led_enabled\":1}",
        "{\"config_revision\":99,\"coin_pin\":0,\"relay_pin\":0,\"led_pin\":0}"
    };
    for (int polarity = 0; polarity < 2; ++polarity) {
        for (const auto &response : responses) {
            controllerEnabled = true;
            coinEnabled = true;
            relayEnabled = true;
            ledEnabled = true;
            insertMode = true;
            fsReady = true;
            pendingReady = false;
            activeTarget = "target-00112233";
            runRelayActiveHigh = (polarity != 0);
            runLedActiveHigh = (polarity != 0);
            relayLevel = -1;
            ledLevel = -1;

            applyRemoteConfig(response);

            if (controllerEnabled || coinEnabled || relayEnabled ||
                ledEnabled || insertMode || !activeTarget.empty()) return 10;
            if (relayLevel != (runRelayActiveHigh ? LOW : HIGH)) return 11;
            if (ledLevel != (runLedActiveHigh ? LOW : HIGH)) return 12;
            if (!fsReady || pendingReady) return 13;
        }
    }
    std::cout << "REMOTE_CONFIG_DENY_PASS 6/6 payload-polarity cases\n";
    return 0;
}
"""


def compile_and_run(source: str, expect_success: bool, label: str) -> None:
    with tempfile.TemporaryDirectory(prefix="phx-remote-config-deny-") as temp:
        cpp = Path(temp) / "remote_config.cpp"
        binary = Path(temp) / "remote_config"
        cpp.write_text(source, encoding="utf-8")
        compiled = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             str(cpp), "-o", str(binary)],
            text=True, capture_output=True,
        )
        if compiled.returncode:
            raise AssertionError(
                f"{label}: C++ compile failed:\n{compiled.stdout}\n{compiled.stderr}"
            )
        result = subprocess.run([str(binary)], text=True, capture_output=True)
        if expect_success and result.returncode:
            raise AssertionError(
                f"{label}: safe-state test failed ({result.returncode}): "
                f"{result.stdout}{result.stderr}"
            )
        if not expect_success and result.returncode == 0:
            raise AssertionError(f"{label}: fail-open mutation escaped")


def verify_board(board: str, path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    assert_source_contract(source, board)
    write_fn = extract_function(source, "void writeLogical(")
    outputs_fn = extract_function(source, "void applyOutputs()")
    deny_fn = extract_function(source, "void denyRemoteControl()")
    apply_fn = extract_function(source, "void applyRemoteConfig(")

    required = (
        "controllerEnabled=false;",
        "coinEnabled=false;",
        "relayEnabled=false;",
        "ledEnabled=false;",
        "insertMode=false;",
        "applyOutputs();",
    )
    compact_deny = re.sub(r"\s+", "", mask_non_code(deny_fn))
    for token in required:
        if token not in compact_deny:
            raise AssertionError(f"{board}: deny function missing {token}")
    if not has_empty_string_assignment(deny_fn, "activeTarget"):
        raise AssertionError(f"{board}: active target is not cleared")

    safe = harness(write_fn, outputs_fn, deny_fn, apply_fn)
    compile_and_run(safe, True, f"{board} deny-only response handling")
    masked_apply = mask_non_code(apply_fn)
    mutation_at = masked_apply.find("denyRemoteControl();")
    if mutation_at < 0:
        raise AssertionError(f"{board}: deny-call mutation anchor missing")
    mutated_apply = apply_fn[:mutation_at] + "(void)response;" + apply_fn[mutation_at + len("denyRemoteControl();"):]
    mutated = harness(write_fn, outputs_fn, deny_fn, mutated_apply)
    compile_and_run(mutated, False, f"{board} missing-deny mutation")
    print(f"REMOTE_CONFIG_DENY_PASS {board}")
    print(f"REMOTE_CONFIG_MISSING_DENY_MUTATION_REJECTED {board}")


def main() -> None:
    for board, path in SKETCHES.items():
        if not path.is_file():
            raise SystemExit(f"missing sketch: {path}")
        verify_board(board, path)
    print("REMOTE_CONFIG_DENY_SIMULATED_ONLY=1")
    print("PHYSICAL_RELAY_ACCEPTANCE=0")
    print("PHYSICAL_POWER_CUT_ACCEPTANCE=0")


if __name__ == "__main__":
    main()
