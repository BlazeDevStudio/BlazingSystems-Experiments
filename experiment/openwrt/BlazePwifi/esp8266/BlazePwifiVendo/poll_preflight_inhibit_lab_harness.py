"""Deterministic C++ host harness builders and mutation runners for poll denial."""
from pathlib import Path
import re
import json
import subprocess
import tempfile

__all__ = [
    "compile_and_run",
    "compile_blocking_poll_and_run",
    "expect_poll_guard_mutation_rejected",
    "remove_first_code_token",
]

from firmware_source_extract import mask_non_code
from poll_preflight_inhibit_lab_contract import poll_guard_locations

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
    for (int relayPolarity = 0; relayPolarity < 2; ++relayPolarity) {
        for (int ledPolarity = 0; ledPolarity < 2; ++ledPolarity) {
            controllerEnabled = true;
            coinEnabled = true;
            relayEnabled = true;
            ledEnabled = true;
            insertMode = true;
            fsReady = true;
            pendingReady = false;
            runRelayActiveHigh = (relayPolarity != 0);
            runLedActiveHigh = (ledPolarity != 0);
            pendingPulses = 3;
            pendingNonce = "pending-nonce";
            pendingTarget = "pending-target";

            applyOutputs();
            if (relayLevelHigh != runRelayActiveHigh ||
                ledLevelHigh != runLedActiveHigh) return 10;

            denyRemoteControl();
            if (controllerEnabled || coinEnabled || relayEnabled ||
                ledEnabled || insertMode || !activeTarget.empty()) return 11;

            // Hold both independent OFF levels through a simulated 3500 ms HTTP wait.
            if (relayLevelHigh == runRelayActiveHigh ||
                ledLevelHigh == runLedActiveHigh) return 12;
            if (pendingPulses != 3 || pendingNonce != "pending-nonce" ||
                pendingTarget != "pending-target") return 13;
        }
    }
    std::cout << "POLL_INTAKE_GPIO_POLARITY_PASS 4/4\n";
    return 0;
}
"""

def make_blocking_poll_harness(
    apply_fn: str, deny_fn: str, poll_block: str, response_body: str = ""
) -> str:
    """Execute the extracted poll block against a deterministic HTTP wait/result."""
    template = r"""
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
bool pendingReady = false;
bool runRelayActiveHigh = true;
bool runLedActiveHigh = true;
int runRelayPin = 4;
int runLedPin = 5;
int runCoinPin = 6;
bool relayLevelHigh = false;
bool ledLevelHigh = false;
std::string activeTarget = "target-12345678";
int pendingPulses = 3;
std::string pendingNonce = "pending-nonce";
std::string pendingTarget = "pending-target";

int wifiFailures = 0;
unsigned long nowMs = 2000;
unsigned long lastPoll = 0;
int pollCalls = 0;
bool invalidPollAction = false;
bool inPollWait = false;
bool coinLineActive = false;
int coinSamplesDuringWait = 0;
int coinSamplesAfterWait = 0;
int pulseSamples = 0;
int coinPulseTicks = 0;
int acceptedPulseTicks = 0;
bool unsafeRelayDuringWait = false;
bool unsafeAdmissionDuringWait = false;
bool pendingEvidenceChangedDuringWait = false;
bool unsafeOutputWrite = false;
std::string pollResponse = __PHX_RESPONSE_LITERAL__;

void writeLogical(int pin, bool on, bool activeHigh) {
    const bool levelHigh = (on == activeHigh);
    if (pin == runRelayPin) {
        relayLevelHigh = levelHigh;
        if (on) unsafeOutputWrite = true;
    }
    if (pin == runLedPin) {
        ledLevelHigh = levelHigh;
        if (on) unsafeOutputWrite = true;
    }
}

unsigned long millis() { return nowMs; }

int digitalRead(int pin) {
    if (pin == runCoinPin) {
        if (inPollWait) ++coinSamplesDuringWait;
        else {
            ++coinSamplesAfterWait;
            if (coinLineActive) ++pulseSamples;
        }
    }
    return coinLineActive ? LOW : HIGH;
}

// RED fixture: this stub returns immediately, so the new 3500 ms assertion
// must fail until the modeled blocking wait and pulse injection are implemented.
String post(const String &action) {
    ++pollCalls;
    if (action != "poll") {
        invalidPollAction = true;
        return "";
    }

    const unsigned long waitStarted = nowMs;
    inPollWait = true;
    for (int elapsed = 0; elapsed < 3500; ++elapsed) {
        nowMs = waitStarted + static_cast<unsigned long>(elapsed + 1);
        coinLineActive = (elapsed >= 1600 && elapsed < 1680);
        if (coinLineActive) {
            ++coinPulseTicks;
            if (relayLevelHigh == runRelayActiveHigh || coinEnabled ||
                insertMode || controllerEnabled) {
                ++acceptedPulseTicks;
            }
        }
        if (relayLevelHigh == runRelayActiveHigh ||
            ledLevelHigh == runLedActiveHigh) {
            unsafeRelayDuringWait = true;
        }
        if (controllerEnabled || coinEnabled || relayEnabled ||
            ledEnabled || insertMode) {
            unsafeAdmissionDuringWait = true;
        }
        if (pendingPulses != 3 || pendingNonce != "pending-nonce" ||
            pendingTarget != "pending-target") {
            pendingEvidenceChangedDuringWait = true;
        }
    }
    coinLineActive = false;
    inPollWait = false;
    return pollResponse;
}
"""
    template = template.replace("__PHX_RESPONSE_LITERAL__", json.dumps(response_body))
    return template + apply_fn + chr(10) + deny_fn + r"""
int main() {
    for (int relayPolarity = 0; relayPolarity < 2; ++relayPolarity) {
        for (int ledPolarity = 0; ledPolarity < 2; ++ledPolarity) {
            controllerEnabled = true;
            coinEnabled = true;
            relayEnabled = true;
            ledEnabled = true;
            insertMode = true;
            fsReady = true;
            pendingReady = false;
            runRelayActiveHigh = (relayPolarity != 0);
            runLedActiveHigh = (ledPolarity != 0);
            activeTarget = "target-12345678";
            pendingPulses = 3;
            pendingNonce = "pending-nonce";
            pendingTarget = "pending-target";
            nowMs = 2000;
            lastPoll = 0;
            pollCalls = 0;
            invalidPollAction = false;
            inPollWait = false;
            coinLineActive = false;
            coinSamplesDuringWait = 0;
            coinSamplesAfterWait = 0;
            pulseSamples = 0;
            coinPulseTicks = 0;
            acceptedPulseTicks = 0;
            unsafeRelayDuringWait = false;
            unsafeAdmissionDuringWait = false;
            pendingEvidenceChangedDuringWait = false;

            applyOutputs();
            if (relayLevelHigh != runRelayActiveHigh ||
                ledLevelHigh != runLedActiveHigh) return 10;
            // The initial state is intentionally energized to prove that the
            // extracted pre-poll deny removes it. Only later writes are unsafe.
            unsafeOutputWrite = false;

            const unsigned long started = millis();
""" + poll_block + r"""
            if (pollCalls != 1 || invalidPollAction) return 13;
            if (millis() - started != 3500) {
                std::cerr << "BLOCKING_POLL_WAIT_RED elapsed_ms="
                          << (millis() - started) << " expected=3500" << std::endl;
                return 14;
            }
            if (lastPoll != millis()) return 15;
            if (coinPulseTicks != 80) return 16;
            if (coinSamplesDuringWait != 0) return 17;
            const int rawAfterWait = digitalRead(runCoinPin);
            if (rawAfterWait != HIGH || coinSamplesAfterWait != 1 ||
                pulseSamples != 0) return 18;
            if (acceptedPulseTicks != 0 || unsafeRelayDuringWait ||
                unsafeAdmissionDuringWait) return 19;
            if (pendingEvidenceChangedDuringWait || pendingPulses != 3 ||
                pendingNonce != "pending-nonce" ||
                pendingTarget != "pending-target") return 20;
            if (controllerEnabled || coinEnabled || relayEnabled ||
                ledEnabled || insertMode || !activeTarget.empty()) return 21;
            if (relayLevelHigh == runRelayActiveHigh ||
                ledLevelHigh == runLedActiveHigh) return 22;
            if (unsafeOutputWrite) return 23;
        }
    }
    std::cout << "BLOCKING_POLL_WAIT_PASS 3500ms pulse_ticks=80 samples_during_wait=0 accepted=0 polarity_combinations=4" << std::endl;
    std::cout << "POLL_RESPONSE_OUTCOME_PASS body_bytes=" << pollResponse.size() << " outputs_never_reenabled=1" << std::endl;
    return 0;
}
"""

def compile_blocking_poll_and_run(
    apply_fn: str, deny_fn: str, poll_block: str,
    expect_success: bool, label: str, response_body: str = "",
):
    with tempfile.TemporaryDirectory(prefix="phx-blocking-poll-") as temp:
        source = Path(temp) / "blocking_poll.cpp"
        binary = Path(temp) / "blocking_poll"
        source.write_text(
            make_blocking_poll_harness(apply_fn, deny_fn, poll_block, response_body),
            encoding="utf-8",
        )
        compile_result = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             str(source), "-o", str(binary)],
            text=True, capture_output=True,
        )
        if compile_result.returncode != 0:
            raise AssertionError(
                f"{label}: C++ harness compile failed:\\n"
                f"{compile_result.stdout}\\n{compile_result.stderr}"
            )
        run_result = subprocess.run([str(binary)], text=True, capture_output=True)
        if expect_success and run_result.returncode != 0:
            raise AssertionError(
                f"{label}: blocking-poll harness failed "
                f"({run_result.returncode}): {run_result.stdout}{run_result.stderr}"
            )
        if not expect_success and run_result.returncode == 0:
            raise AssertionError(f"{label}: fail-open poll-block mutation survived")
        if run_result.stdout.strip():
            print(run_result.stdout.strip())
        if run_result.stderr.strip():
            print(run_result.stderr.strip())
        if not expect_success:
            print(f"{label}: mutation rejected (exit {run_result.returncode})")
        return run_result

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
        if run_result.stdout.strip():
            print(run_result.stdout.strip())
        if not expect_success:
            print(f"{label}: mutation rejected (exit {run_result.returncode})")
        return run_result

def remove_first_code_token(source: str, token: str) -> str:
    masked = mask_non_code(source)
    start = masked.find(token)
    if start < 0:
        raise AssertionError(f"missing code token for mutation: {token}")
    return source[:start] + source[start + len(token):]

def expect_poll_guard_mutation_rejected(
    name: str,
    loop: str,
    pattern: str,
    replacement: str,
    label: str,
    expected_fragment: str,
):
    mutated, count = re.subn(pattern, replacement, loop, count=1)
    if count != 1:
        raise AssertionError(f"{name}: could not create {label} mutation")
    try:
        poll_guard_locations(mutated)
    except AssertionError as exc:
        if expected_fragment not in str(exc):
            raise AssertionError(
                f"{name}: {label} mutation failed for an unexpected reason: {exc}"
            ) from exc
    else:
        raise AssertionError(f"{name}: {label} mutation was not rejected")
    print(f"POLL_GUARD_CONTROL_FLOW_MUTATION_REJECTED {name} {label}")
