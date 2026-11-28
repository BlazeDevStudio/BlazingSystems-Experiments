"""Deterministic C++ host harness builders and mutation runners for poll denial.

The blocking-poll fixture sweeps pulse windows at startup, mid-wait and the
exact poll-return boundary. A pulse still active after HTTP completion remains
active for the post-poll sample instead of being forced inactive by the stub.
"""
from pathlib import Path
import re
import subprocess
import tempfile

__all__ = [
    "compile_and_run",
    "compile_blocking_poll_and_run",
    "compile_poll_transport_outcome_matrix",
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

def make_blocking_poll_harness(apply_fn: str, deny_fn: str, poll_block: str) -> str:
    """Execute the actual extracted poll block with a deterministic host HTTP wait."""
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
bool pollStarted = false;
bool coinLineActive = false;
bool pulseActiveAtPrePollDisable = false;
int coinSamplesDuringWait = 0;
int coinSamplesAfterWait = 0;
int pulseSamples = 0;
int coinPulseTicks = 0;
int pulseStartMs = 1600;
int pulseEndMs = 1680;
int acceptedPulseTicks = 0;
bool lastCoin = false;
unsigned long lastEdge = 0;
unsigned long runDebounceMs = 40;
bool unsafeRelayDuringWait = false;
bool unsafeAdmissionDuringWait = false;
bool pendingEvidenceChangedDuringWait = false;

void writeLogical(int pin, bool on, bool activeHigh) {
    const bool levelHigh = (on == activeHigh);
    if (!pollStarted && pin == runRelayPin && !on && coinLineActive) {
        pulseActiveAtPrePollDisable = true;
    }
    if (pin == runRelayPin) relayLevelHigh = levelHigh;
    if (pin == runLedPin) ledLevelHigh = levelHigh;
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

// Deterministic host HTTP wait: inject a bounded pulse at the selected
// poll-relative offsets while the extracted production poll block is blocked.
String post(const String &action) {
    ++pollCalls;
    if (action != "poll") {
        invalidPollAction = true;
        return "";
    }

    pollStarted = true;
    const unsigned long waitStarted = nowMs;
    inPollWait = true;
    for (int elapsed = 0; elapsed < 3500; ++elapsed) {
        nowMs = waitStarted + static_cast<unsigned long>(elapsed + 1);
        coinLineActive = (elapsed >= pulseStartMs && elapsed < pulseEndMs);
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
    coinLineActive = (3500 >= pulseStartMs && 3500 < pulseEndMs);
    inPollWait = false;
    return "{\"ok\":true,\"insert\":true,\"target_nonce\":\"untrusted\"}";
}
""" + apply_fn + chr(10) + deny_fn + r"""
int main() {
    const int pulseStarts[] = {-40, 0, 1600, 3420, 3460, 3500};
    const int pulseEnds[] = {40, 80, 1680, 3500, 3540, 3580};
    const int pulseCases = sizeof(pulseStarts) / sizeof(pulseStarts[0]);
    for (int pulseCase = 0; pulseCase < pulseCases; ++pulseCase) {
        pulseStartMs = pulseStarts[pulseCase];
        pulseEndMs = pulseEnds[pulseCase];
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
            lastCoin = false;
            lastEdge = 0;
            nowMs = 2000;
            lastPoll = 0;
            pollCalls = 0;
            invalidPollAction = false;
            inPollWait = false;
            pollStarted = false;
            coinLineActive = false;
            pulseActiveAtPrePollDisable = false;
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

            coinLineActive = (pulseStartMs < 0 && pulseEndMs > 0);
            const unsigned long started = millis();
""" + poll_block + r"""
            if (pollCalls != 1 || invalidPollAction) return 13;
            if (millis() - started != 3500) {
                std::cerr << "BLOCKING_POLL_WAIT_RED elapsed_ms="
                          << (millis() - started) << " expected=3500" << std::endl;
                return 14;
            }
            if (lastPoll != millis()) return 15;
            int expectedPulseTicks = 0;
            for (int elapsed = 0; elapsed < 3500; ++elapsed) {
                if (elapsed >= pulseStartMs && elapsed < pulseEndMs) {
                    ++expectedPulseTicks;
                }
            }
            if (coinPulseTicks != expectedPulseTicks) return 16;
            if (coinSamplesDuringWait != 0) return 17;
            const bool pulseActiveAtReturn =
                (3500 >= pulseStartMs && 3500 < pulseEndMs);
            const int rawAfterWait = digitalRead(runCoinPin);
            if (rawAfterWait != (pulseActiveAtReturn ? LOW : HIGH) ||
                coinSamplesAfterWait != 1 ||
                pulseSamples != (pulseActiveAtReturn ? 1 : 0)) return 18;
            const bool activeAfterWait = (rawAfterWait == LOW);
            if (insertMode && fsReady && !pendingReady &&
                !activeTarget.empty() && activeAfterWait && !lastCoin &&
                millis() - lastEdge > runDebounceMs) {
                ++acceptedPulseTicks;
            }
            lastCoin = activeAfterWait;
            if (pulseActiveAtPrePollDisable !=
                    (pulseStartMs < 0 && pulseEndMs > 0)) return 23;
            if (acceptedPulseTicks != 0 || unsafeRelayDuringWait ||
                unsafeAdmissionDuringWait) return 19;
            if (pendingEvidenceChangedDuringWait || pendingPulses != 3 ||
                pendingNonce != "pending-nonce" ||
                pendingTarget != "pending-target") return 20;
            if (controllerEnabled || coinEnabled || relayEnabled ||
                ledEnabled || insertMode || !activeTarget.empty()) return 21;
            if (relayLevelHigh == runRelayActiveHigh ||
                ledLevelHigh == runLedActiveHigh) return 22;
            }
        }
    }
    std::cout << "BLOCKING_POLL_WAIT_PASS 3500ms pulse_cases=6 polarity_combinations=4 pre_poll_inflight=1 cross_return=1 at_return=1 untrusted_response_ignored=1 accepted=0" << std::endl;
    return 0;
}
"""

def compile_blocking_poll_and_run(
    apply_fn: str, deny_fn: str, poll_block: str,
    expect_success: bool, label: str,
):
    with tempfile.TemporaryDirectory(prefix="phx-blocking-poll-") as temp:
        source = Path(temp) / "blocking_poll.cpp"
        binary = Path(temp) / "blocking_poll"
        source.write_text(
            make_blocking_poll_harness(apply_fn, deny_fn, poll_block),
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
    source: str,
    pattern: str,
    replacement: str,
    label: str,
    expected_fragment: str,
):
    mutated, count = re.subn(pattern, replacement, source, count=1)
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


def make_poll_transport_outcome_harness(apply_fn: str, deny_fn: str, poll_block: str) -> str:
    """Run the extracted poll block against transport return and untrusted-body outcomes."""
    return r"""
#include <iostream>
#include <string>
using String = std::string;

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
int pendingPulses = 3;
std::string pendingNonce = "pending-nonce";
std::string pendingTarget = "pending-target";

unsigned long nowMs = 2000;
unsigned long lastPoll = 0;
int wifiFailures = 0;
int pollCalls = 0;
int outcomeMode = 0;
bool pollStarted = false;
bool invalidPollAction = false;
bool unsafeBeforePost = false;
bool unsafeDuringWait = false;
bool unsafeActiveWriteAfterPoll = false;
bool pendingEvidenceChanged = false;

void writeLogical(int pin, bool on, bool activeHigh) {
    const bool levelHigh = (on == activeHigh);
    if (pollStarted && on) unsafeActiveWriteAfterPoll = true;
    if (pin == runRelayPin) relayLevelHigh = levelHigh;
    if (pin == runLedPin) ledLevelHigh = levelHigh;
}

unsigned long millis() { return nowMs; }

String post(const String &action) {
    ++pollCalls;
    if (action != "poll") {
        invalidPollAction = true;
        return "";
    }

    pollStarted = true;
    if (relayLevelHigh == runRelayActiveHigh ||
        ledLevelHigh == runLedActiveHigh ||
        controllerEnabled || coinEnabled || relayEnabled ||
        ledEnabled || insertMode) {
        unsafeBeforePost = true;
    }

    // Mode 1 models HTTPClient.begin/connect failure before any wait.
    if (outcomeMode != 1) {
        const unsigned long waitStarted = nowMs;
        for (int elapsed = 0; elapsed < 3500; ++elapsed) {
            nowMs = waitStarted + static_cast<unsigned long>(elapsed + 1);
            if (relayLevelHigh == runRelayActiveHigh ||
                ledLevelHigh == runLedActiveHigh ||
                controllerEnabled || coinEnabled || relayEnabled ||
                ledEnabled || insertMode) {
                unsafeDuringWait = true;
            }
            if (pendingPulses != 3 || pendingNonce != "pending-nonce" ||
                pendingTarget != "pending-target") {
                pendingEvidenceChanged = true;
            }
        }
    }

    switch (outcomeMode) {
        case 0: return "{\"ok\":true,\"insert\":true,\"target_nonce\":\"untrusted\"}";
        case 1: return "";
        case 2: return "";
        case 3: return "{malformed";
        case 4: return "{\"ok\":false,\"error\":\"upstream\"}";
        default: return "";
    }
}
""" + apply_fn + "\n" + deny_fn + r"""
int main() {
    for (int outcome = 0; outcome < 5; ++outcome) {
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
                wifiFailures = 0;
                pollCalls = 0;
                outcomeMode = outcome;
                pollStarted = false;
                invalidPollAction = false;
                unsafeBeforePost = false;
                unsafeDuringWait = false;
                unsafeActiveWriteAfterPoll = false;
                pendingEvidenceChanged = false;

                applyOutputs();
                if (relayLevelHigh != runRelayActiveHigh ||
                    ledLevelHigh != runLedActiveHigh) return 10;
                const unsigned long started = millis();
""" + poll_block + r"""
                const unsigned long expectedWait = (outcome == 1) ? 0UL : 3500UL;
                if (pollCalls != 1 || invalidPollAction) return 13;
                if (millis() - started != expectedWait || lastPoll != millis()) return 14;
                if (unsafeBeforePost || unsafeDuringWait || unsafeActiveWriteAfterPoll) return 20;
                if (pendingEvidenceChanged || pendingPulses != 3 ||
                    pendingNonce != "pending-nonce" ||
                    pendingTarget != "pending-target") return 21;
                if (controllerEnabled || coinEnabled || relayEnabled ||
                    ledEnabled || insertMode || !activeTarget.empty()) return 22;
                if (relayLevelHigh == runRelayActiveHigh ||
                    ledLevelHigh == runLedActiveHigh) return 23;
            }
        }
    }
    std::cout << "POLL_TRANSPORT_OUTCOME_PASS outcomes=5 polarity_combinations=4 cases=20 immediate_begin_failure=1 timeout_empty=1 malformed=1 server_error=1 untrusted_insert=1" << std::endl;
    return 0;
}
"""


def compile_poll_transport_outcome_matrix(
    apply_fn: str,
    deny_fn: str,
    poll_block: str,
    expect_success: bool,
    label: str,
):
    with tempfile.TemporaryDirectory(prefix="phx-poll-outcomes-") as temp:
        source = Path(temp) / "poll_outcomes.cpp"
        binary = Path(temp) / "poll_outcomes"
        source.write_text(
            make_poll_transport_outcome_harness(apply_fn, deny_fn, poll_block),
            encoding="utf-8",
        )
        compile_result = subprocess.run(
            [ "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
              str(source), "-o", str(binary) ],
            text=True, capture_output=True,
        )
        if compile_result.returncode != 0:
            raise AssertionError(
                f"{label}: C++ harness compile failed:\n"
                f"{compile_result.stdout}\n{compile_result.stderr}"
            )
        run_result = subprocess.run([str(binary)], text=True, capture_output=True)
        if expect_success and run_result.returncode != 0:
            raise AssertionError(
                f"{label}: outcome harness failed ({run_result.returncode}): "
                f"{run_result.stdout}{run_result.stderr}"
            )
        if not expect_success and run_result.returncode == 0:
            raise AssertionError(f"{label}: transient response-actuation mutation survived")
        if run_result.stdout.strip():
            print(run_result.stdout.strip())
        if not expect_success:
            print(f"{label}: mutation rejected (exit {run_result.returncode})")
        return run_result
