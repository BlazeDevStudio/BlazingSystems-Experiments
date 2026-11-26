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

from firmware_source_extract import extract_braced, extract_function, has_empty_string_assignment, mask_non_code


BLAZEPWIFI = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": BLAZEPWIFI / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def _poll_call_matches(source: str):
    # Match the literal argument in source, but accept it only when the call
    # identifier itself is code rather than a comment/string decoy.
    pattern = re.compile(r'\bpost\s*\(\s*"poll"\s*\)')
    masked = mask_non_code(source)
    return [
        match for match in pattern.finditer(source)
        if masked[match.start():match.start() + 4] == "post"
    ]


def _coin_post_matches(source: str):
    pattern = re.compile(r'\bpost\s*\(\s*"coin"\s*\)')
    masked = mask_non_code(source)
    return [
        match for match in pattern.finditer(source)
        if masked[match.start():match.start() + 4] == "post"
    ]


def poll_guard_locations(source: str):
    loop = extract_function(source, "void loop()")
    masked_loop = mask_non_code(loop)
    if _coin_post_matches(loop):
        raise AssertionError("automatic coin POST remains in loop before authenticated receipt contract approval")
    if re.search(r"\bclearPending\s*\(", masked_loop):
        raise AssertionError("pending coin disposition remains active in loop before authenticated receipt contract approval")
    condition = re.search(
        r"if\s*\(\s*WiFi\.status\(\)\s*==\s*WL_CONNECTED\s*&&\s*"
        r"millis\(\)\s*-\s*lastPoll\s*>\s*1500\s*\)",
        masked_loop,
    )
    if not condition:
        raise AssertionError("missing bounded synchronous poll condition")
    brace = masked_loop.find("{", condition.end())
    poll_block = extract_braced(loop, brace)
    masked_poll_block = mask_non_code(poll_block)
    loop_poll_matches = _poll_call_matches(loop)
    poll_matches = _poll_call_matches(poll_block)
    if len(loop_poll_matches) != len(poll_matches):
        raise AssertionError("synchronous poll request exists outside the bounded guarded block")
    if not poll_matches:
        raise AssertionError("missing synchronous poll request")

    # Until CORE publishes an authenticated poll/configuration contract, the
    # response must be explicitly discarded and no remote config may be applied
    # anywhere in this loop. This closes a transient relay-enable window between
    # the pre-poll and post-poll deny calls.
    for match in poll_matches:
        prefix = masked_poll_block[max(0, match.start() - 32):match.start()]
        suffix = masked_poll_block[match.end():]
        if not re.search(r"\(\s*void\s*\)\s*$", prefix):
            raise AssertionError("poll response must be explicitly discarded until authenticated contract approval")
        if not re.match(r"\s*;", suffix):
            raise AssertionError("poll response must not be consumed before post-poll deny")
    if re.search(r"\bapplyRemoteConfig\s*\(", masked_loop):
        raise AssertionError("remote configuration must remain unapplied until authenticated contract approval")

    first_pre_guard = -1
    last_post_guard = -1
    for index, match in enumerate(poll_matches):
        previous_end = 0 if index == 0 else poll_matches[index - 1].end()
        next_start = (
            poll_matches[index + 1].start()
            if index + 1 < len(poll_matches)
            else len(poll_block)
        )
        pre_guard = masked_poll_block.rfind(
            "denyRemoteControl();", previous_end, match.start()
        )
        if pre_guard < 0:
            raise AssertionError(
                f"coin intake is not denied before blocking poll request {index + 1}"
            )
        post_guard = masked_poll_block.find(
            "denyRemoteControl();", match.end(), next_start
        )
        if post_guard < 0:
            raise AssertionError(
                f"post-poll deny guard is missing for request {index + 1}"
            )
        if index == 0:
            first_pre_guard = pre_guard
        last_post_guard = post_guard

    global_last_poll = brace + poll_matches[-1].start()
    sample = masked_loop.find("digitalRead(runCoinPin)")
    if sample < 0 or sample <= global_last_poll:
        raise AssertionError(
            "coin input sampling moved before/inside the blocking poll sequence"
        )
    return loop, first_pre_guard, poll_matches[0].start(), last_post_guard

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
int pendingPulses = 0;
std::string pendingNonce;
std::string pendingTarget;

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
        pendingPulses = 3;
        pendingNonce = "pending-nonce";
        pendingTarget = "pending-target";

        applyOutputs();
        if (relayLevelHigh != runRelayActiveHigh) return 10;

        denyRemoteControl();
        if (controllerEnabled || coinEnabled || relayEnabled ||
            ledEnabled || insertMode || !activeTarget.empty()) return 11;

        // Hold the state through a simulated 3500 ms synchronous HTTP wait.
        if (relayLevelHigh == runRelayActiveHigh) return 12;
        if (pendingPulses != 3 || pendingNonce != "pending-nonce" ||
            pendingTarget != "pending-target") return 13;
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


def remove_first_code_token(source: str, token: str) -> str:
    masked = mask_non_code(source)
    start = masked.find(token)
    if start < 0:
        raise AssertionError(f"missing code token for mutation: {token}")
    return source[:start] + source[start + len(token):]


def verify_board(name: str, path: Path):
    source = path.read_text(encoding="utf-8")
    loop, pre_guard, poll_at, post_guard = poll_guard_locations(source)
    if not (pre_guard < poll_at < post_guard):
        raise AssertionError(f"{name}: invalid poll guard order")

    apply_fn = extract_function(source, "void applyOutputs()")
    deny_fn = extract_function(source, "void denyRemoteControl()")
    deny_code = mask_non_code(deny_fn)
    apply_code = mask_non_code(apply_fn)
    required = (
        "controllerEnabled=false;",
        "coinEnabled=false;",
        "relayEnabled=false;",
        "insertMode=false;",
        "applyOutputs();",
    )
    for token in required:
        if token not in deny_code:
            raise AssertionError(f"{name}: denyRemoteControl missing {token!r}")
    if not has_empty_string_assignment(deny_fn, "activeTarget"):
        raise AssertionError(f"{name}: denyRemoteControl does not clear active target")
    if "bool accepting=controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady;" not in apply_code:
        raise AssertionError(f"{name}: relay acceptance predicate changed unexpectedly")
    if "if(relayEnabled)" not in apply_code or "writeLogical(runRelayPin,false,runRelayActiveHigh)" not in apply_code:
        raise AssertionError(f"{name}: relay-off GPIO branch is not explicit")

    compile_and_run(apply_fn, deny_fn, True, f"{name} safe pre-poll state")

    # Failure injection: remove all four actuation-deny assignments. The
    # source-extracted GPIO model must detect that the relay stays energized.
    mutated_deny = deny_fn
    for token in ("controllerEnabled=false;", "coinEnabled=false;",
                  "relayEnabled=false;", "insertMode=false;"):
        mutated_deny = remove_first_code_token(mutated_deny, token)
    compile_and_run(apply_fn, mutated_deny, False, f"{name} deny-state mutation")

    # Failure injection: remove the pre-poll guard while retaining the
    # post-poll guard. The source-order assertion must reject this regression.
    mutated_loop = loop
    loop_start = mutated_loop.find("void loop()")
    pre_guard_global = loop_start + mask_non_code(mutated_loop[loop_start:]).find("denyRemoteControl();")
    if pre_guard_global < loop_start:
        raise AssertionError(f"{name}: pre-poll guard not found for mutation")
    mutated_loop = mutated_loop[:pre_guard_global] + mutated_loop[pre_guard_global + len("denyRemoteControl();"):]
    try:
        poll_guard_locations(mutated_loop)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: missing pre-poll guard mutation was not rejected")

    # Failure injection: a poll request outside the bounded guarded block
    # must be rejected, not hidden by the first guarded site.
    poll_matches = _poll_call_matches(loop)
    poll_at = poll_matches[0].start() if poll_matches else -1
    sample_at = mask_non_code(loop).find("digitalRead(runCoinPin)", poll_at)
    if poll_at < 0 or sample_at < 0:
        raise AssertionError(f"{name}: cannot place unguarded second-poll mutation")
    mutated_loop = loop[:sample_at] + '    post("poll");\n    ' + loop[sample_at:]
    try:
        poll_guard_locations(mutated_loop)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: unguarded second-poll mutation was not rejected")

    # Failure injection: reintroducing an automatic coin POST must be rejected.
    mutated_loop = loop.replace("delay(2);", 'post("coin");\n    delay(2);', 1)
    try:
        poll_guard_locations(mutated_loop)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: automatic coin POST mutation was not rejected")

    # Failure injection: clearing a pending event without an authenticated
    # receipt/disposition contract must be rejected.
    mutated_loop = loop.replace("delay(2);", "clearPending();\n    delay(2);", 1)
    try:
        poll_guard_locations(mutated_loop)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: pending clear mutation was not rejected")

    print(f"POLL_INTAKE_GUARD_PASS {name}")
    print(f"PENDING_COIN_POST_MUTATION_REJECTED {name}")
    print(f"PENDING_CLEAR_MUTATION_REJECTED {name}")
    print(f"POLL_INTAKE_DENY_MUTATION_REJECTED {name}")
    print(f"POLL_PREPOLL_ORDER_MUTATION_REJECTED {name}")


def verify_source_extractor_decoy_regressions():
    # A source guard must select real definitions, not comments or literals.
    cases = {
        "block-comment decoy": (
            "/* void loop() { fake_poll(); } */\\n"
            "void loop() { actual_poll(); }\\n"
        ),
        "string-literal decoy": (
            'const char *note = "void loop() { quoted_decoy(); }";\\n'
            "void loop() { actual_poll(); }\\n"
        ),
        "raw-string brace": (
            'void loop() { const char *payload = R"tag( } " // /* { )tag"; '
            "actual_poll(); }\\n"
        ),
    }
    for label, source in cases.items():
        try:
            extracted = extract_function(source, "void loop()")
        except AssertionError as exc:
            raise AssertionError(f"{label}: source extractor failed: {exc}") from exc
        if "actual_poll();" not in extracted:
            raise AssertionError(
                f"{label}: source extractor selected a non-code decoy or truncated the function"
            )


    poll_source = r'''
void loop() {
    // post("poll"); denyRemoteControl(); post("coin"); clearPending(true);
    const char *note = "post(\"poll\"); post(\"coin\"); clearPending(true);";
    if (WiFi.status() == WL_CONNECTED && millis() - lastPoll > 1500) {
        denyRemoteControl();
        (void)post("poll");
        denyRemoteControl();
    }
    digitalRead(runCoinPin);
}
'''
    poll_guard_locations(poll_source)
    # Failure injection: both response consumption and independent remote-config
    # application must be rejected until the authenticated contract is approved.
    unsafe_poll_source = poll_source.replace(
        '        (void)post("poll");',
        '        String response = post("poll");\n        applyRemoteConfig(response);',
    )
    try:
        poll_guard_locations(unsafe_poll_source)
    except AssertionError:
        pass
    else:
        raise AssertionError("poll-response consumption mutation was not rejected")
    unsafe_config_source = poll_source.replace(
        '        (void)post("poll");',
        '        (void)post("poll");\n        applyRemoteConfig(staleResponse);',
    )
    try:
        poll_guard_locations(unsafe_config_source)
    except AssertionError:
        pass
    else:
        raise AssertionError("remote-config application mutation was not rejected")
    print("POLL_RESPONSE_USE_MUTATION_REJECTED")
    print("POLL_REMOTE_CONFIG_MUTATION_REJECTED")
    if not has_empty_string_assignment('void f() { activeTarget = ""; }', "activeTarget"):
        raise AssertionError("empty-target assignment was not recognized")
    if has_empty_string_assignment('void f() { /* activeTarget = ""; */ }', "activeTarget"):
        raise AssertionError("comment-only empty-target decoy was accepted")

def main():
    verify_source_extractor_decoy_regressions()
    for name, path in SKETCHES.items():
        if not path.is_file():
            raise SystemExit(f"missing sketch: {path}")
        verify_board(name, path)
    print("POLL_INTAKE_GUARD_SIMULATED_ONLY=1")
    print("PHYSICAL_COIN_RELAY_ACCEPTANCE=0")
    print("PHYSICAL_POWER_CUT_ACCEPTANCE=0")


if __name__ == "__main__":
    main()
