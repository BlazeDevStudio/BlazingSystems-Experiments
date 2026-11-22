#!/usr/bin/env python3
"""Source-extracted regression for fail-closed coin-intake inhibition before blocking poll.

This is a host simulation. It compiles the actual applyOutputs() and
denyRemoteControl() bodies from both sketches against a tiny GPIO boundary,
checks both relay polarities, and rejects unsafe source-order/state mutations.
It does not claim electrical or physical hardware acceptance.
"""
from pathlib import Path
import re
import subprocess
import tempfile


BLAZEPWIFI = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": BLAZEPWIFI / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def extract_braced(source: str, brace_at: int) -> str:
    if brace_at < 0 or source[brace_at] != "{":
        raise AssertionError("expected opening brace")
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    pos = brace_at
    while pos < len(source):
        ch = source[pos]
        nxt = source[pos + 1] if pos + 1 < len(source) else ""
        if line_comment:
            if ch in "\r\n":
                line_comment = False
            pos += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                pos += 2
            else:
                pos += 1
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            pos += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            pos += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            pos += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            pos += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[brace_at:pos + 1]
        pos += 1
    raise AssertionError("unclosed C++ block")


def extract_function(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise AssertionError(f"missing function: {signature}")
    brace = source.find("{", start + len(signature))
    if brace < 0:
        raise AssertionError(f"missing body: {signature}")
    return source[start:brace] + extract_braced(source, brace)


def poll_guard_locations(source: str):
    loop = extract_function(source, "void loop()")
    condition = re.search(
        r"if\s*\(\s*WiFi\.status\(\)\s*==\s*WL_CONNECTED\s*&&\s*"
        r"millis\(\)\s*-\s*lastPoll\s*>\s*1500\s*\)",
        loop,
    )
    if not condition:
        raise AssertionError("missing bounded synchronous poll condition")
    brace = loop.find("{", condition.end())
    poll_block = extract_braced(loop, brace)
    poll_at = poll_block.find('post("poll")')
    if poll_at < 0:
        raise AssertionError("missing synchronous poll request")
    pre_guard = poll_block.rfind("denyRemoteControl();", 0, poll_at)
    post_guard = poll_block.find("denyRemoteControl();", poll_at + len('post("poll")'))
    if pre_guard < 0:
        raise AssertionError("coin intake is not denied before blocking poll")
    if post_guard < 0:
        raise AssertionError("post-poll deny guard is missing")
    global_poll = condition.start() + brace + 1 + poll_at
    sample = loop.find("digitalRead(runCoinPin)")
    if sample < 0 or sample <= global_poll:
        raise AssertionError("coin input sampling moved before/inside blocking poll")
    return loop, pre_guard, poll_at, post_guard


def make_harness(apply_fn: str, deny_fn: str) -> str:
    return r"""
#include <string>
#include <iostream>

bool controllerEnabled = true;
bool coinEnabled = true;
bool relayEnabled = true;
bool ledEnabled = true;
bool insertMode = true;
bool fsReady = true;
bool pendingReady = false;
bool runRelayActiveHigh = true;
bool runLedActiveHigh = true;
int runRelayPin = 4;
int runLedPin = 5;
bool relayLevelHigh = false;
bool ledLevelHigh = false;
std::string activeTarget = "target-12345678";

void writeLogical(int pin, bool on, bool activeHigh) {
    const bool levelHigh = (on == activeHigh);
    if (pin == runRelayPin) relayLevelHigh = levelHigh;
    if (pin == runLedPin) ledLevelHigh = levelHigh;
}

""" + apply_fn + "\n" + deny_fn + r"""

int main() {
    for (int polarity = 0; polarity < 2; ++polarity) {
        controllerEnabled = true;
        coinEnabled = true;
        relayEnabled = true;
        ledEnabled = true;
        insertMode = true;
        fsReady = true;
        pendingReady = false;
        runRelayActiveHigh = (polarity != 0);
        runLedActiveHigh = (polarity != 0);

        applyOutputs();
        if (relayLevelHigh != runRelayActiveHigh) return 10;

        denyRemoteControl();
        if (controllerEnabled || coinEnabled || relayEnabled ||
            ledEnabled || insertMode || !activeTarget.empty()) return 11;

        // Hold the state through a simulated 3500 ms synchronous HTTP wait.
        if (relayLevelHigh == runRelayActiveHigh) return 12;
    }
    std::cout << "POLL_INTAKE_GPIO_POLARITY_PASS 2/2\n";
    return 0;
}
"""


def compile_and_run(apply_fn: str, deny_fn: str, expect_success: bool, label: str):
    with tempfile.TemporaryDirectory(prefix="phx-poll-inhibit-") as temp:
        source = Path(temp) / "poll_inhibit.cpp"
        binary = Path(temp) / "poll_inhibit"
        source.write_text(make_harness(apply_fn, deny_fn), encoding="utf-8")
        compile_result = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             str(source), "-o", str(binary)],
            text=True, capture_output=True,
        )
        if compile_result.returncode != 0:
            raise AssertionError(
                f"{label}: C++ harness compile failed:\n{compile_result.stdout}\n{compile_result.stderr}"
            )
        run_result = subprocess.run([str(binary)], text=True, capture_output=True)
        if expect_success and run_result.returncode != 0:
            raise AssertionError(
                f"{label}: safe-state harness failed ({run_result.returncode}): "
                f"{run_result.stdout}{run_result.stderr}"
            )
        if not expect_success and run_result.returncode == 0:
            raise AssertionError(f"{label}: fail-open mutation was not detected")
        return run_result


def verify_board(name: str, path: Path):
    source = path.read_text(encoding="utf-8")
    loop, pre_guard, poll_at, post_guard = poll_guard_locations(source)
    if not (pre_guard < poll_at < post_guard):
        raise AssertionError(f"{name}: invalid poll guard order")

    apply_fn = extract_function(source, "void applyOutputs()")
    deny_fn = extract_function(source, "void denyRemoteControl()")
    required = (
        "controllerEnabled=false;",
        "coinEnabled=false;",
        "relayEnabled=false;",
        "insertMode=false;",
        "applyOutputs();",
    )
    for token in required:
        if token not in deny_fn:
            raise AssertionError(f"{name}: denyRemoteControl missing {token!r}")
    if not re.search(r'activeTarget\s*=\s*""', deny_fn):
        raise AssertionError(f"{name}: denyRemoteControl does not clear active target")
    if "bool accepting=controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady;" not in apply_fn:
        raise AssertionError(f"{name}: relay acceptance predicate changed unexpectedly")
    if "if(relayEnabled)" not in apply_fn or "writeLogical(runRelayPin,false,runRelayActiveHigh)" not in apply_fn:
        raise AssertionError(f"{name}: relay-off GPIO branch is not explicit")

    compile_and_run(apply_fn, deny_fn, True, f"{name} safe pre-poll state")

    # Failure injection: remove all four actuation-deny assignments. The
    # source-extracted GPIO model must detect that the relay stays energized.
    mutated_deny = deny_fn
    for token in ("controllerEnabled=false;", "coinEnabled=false;",
                  "relayEnabled=false;", "insertMode=false;"):
        mutated_deny = mutated_deny.replace(token, "", 1)
    compile_and_run(apply_fn, mutated_deny, False, f"{name} deny-state mutation")

    # Failure injection: remove the pre-poll guard while retaining the
    # post-poll guard. The source-order assertion must reject this regression.
    mutated_loop = loop
    loop_start = mutated_loop.find("void loop()")
    pre_guard_global = loop_start + mutated_loop[loop_start:].find("denyRemoteControl();")
    if pre_guard_global < loop_start:
        raise AssertionError(f"{name}: pre-poll guard not found for mutation")
    mutated_loop = mutated_loop[:pre_guard_global] + mutated_loop[pre_guard_global + len("denyRemoteControl();"):]
    try:
        poll_guard_locations(mutated_loop)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: missing pre-poll guard mutation was not rejected")

    print(f"POLL_INTAKE_GUARD_PASS {name}")
    print(f"POLL_INTAKE_DENY_MUTATION_REJECTED {name}")
    print(f"POLL_PREPOLL_ORDER_MUTATION_REJECTED {name}")


def main():
    for name, path in SKETCHES.items():
        if not path.is_file():
            raise SystemExit(f"missing sketch: {path}")
        verify_board(name, path)
    print("POLL_INTAKE_GUARD_SIMULATED_ONLY=1")
    print("PHYSICAL_COIN_RELAY_ACCEPTANCE=0")
    print("PHYSICAL_POWER_CUT_ACCEPTANCE=0")


if __name__ == "__main__":
    main()
