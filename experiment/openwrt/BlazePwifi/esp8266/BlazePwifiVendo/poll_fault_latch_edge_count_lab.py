#!/usr/bin/env python3
"""Source-extracted characterization of the V1 first-fault pulseEdges lower bound.

This lab executes the real two-board sample/latch/output/admission functions with
host stubs for Arduino GPIO/time and write-once V1 persistence. It does not model
flash physics, ISR timing on silicon, or financial settlement.
"""
from pathlib import Path
import hashlib
import subprocess
import tempfile

from firmware_lab_source import extract_function, find_repo_root

ROOT = find_repo_root(Path(__file__))
BOARDS = (
    (
        "ESP8266",
        ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    ),
    (
        "ESP32",
        ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
    ),
)

PRELUDE = r"""
#include <cstdint>
#include <iostream>
#include <string>

using String = std::string;
static constexpr int HIGH = 1;
static constexpr int LOW = 0;

uint32_t fakeNow = 1000;
uint32_t coinEdgeSequence = 0;
uint32_t lastHandledCoinEdgeSequence = 0;
uint32_t lastEdge = 0;
uint16_t runDebounceMs = 40;
uint8_t pendingPulses = 1;

bool lastCoin = false;
bool fsReady = true;
bool journalRecoveryRequired = false;
bool pendingReady = true;
bool insertMode = true;
bool pendingPostAttempted = false;
bool outputPolarityKnown = true;
bool pinConfigSafe = true;
bool controllerEnabled = true;
bool coinEnabled = true;
bool ledEnabled = true;
bool relayEnabled = true;
bool pollIntakeSuspended = false;
bool runLedActiveHigh = true;
bool runRelayActiveHigh = true;

int runLedPin = 14;
int runRelayPin = 5;
int ledLevel = HIGH;
int relayLevel = HIGH;

String activeTarget = "target-01";
String pendingNonce = "nonce12345678";
String pendingTarget = "target-01";

bool backupMarkerPresent = false;
bool littleFsMarkerPresent = false;
uint32_t backupPulseEdges = 0;
uint32_t littleFsPulseEdges = 0;
unsigned backupWriteAttempts = 0;
unsigned littleFsWriteAttempts = 0;

struct SerialStub {
    void println(const char *) {}
} Serial;

uint32_t millis() {
    return fakeNow;
}

uint32_t snapshotCoinEdgeSequence() {
    return coinEdgeSequence;
}

void digitalWrite(int pin, int level) {
    if (pin == runRelayPin) relayLevel = level;
    if (pin == runLedPin) ledLevel = level;
}

bool writePollFaultBackup(uint32_t pulseEdges) {
    ++backupWriteAttempts;
    if (!backupMarkerPresent) {
        backupMarkerPresent = true;
        backupPulseEdges = pulseEdges;
    }
    return true;
}

bool writePollPulseFaultMarker(uint32_t pulseEdges) {
    ++littleFsWriteAttempts;
    if (!littleFsMarkerPresent) {
        littleFsMarkerPresent = true;
        littleFsPulseEdges = pulseEdges;
    }
    return true;
}

String freshNonce() {
    return "nonce12345678";
}

bool savePending() {
    return true;
}

void resetScenario(bool activeHigh) {
    fakeNow = 1000;
    coinEdgeSequence = 0;
    lastHandledCoinEdgeSequence = 0;
    lastEdge = 0;
    runDebounceMs = 40;
    pendingPulses = 1;

    lastCoin = false;
    fsReady = true;
    journalRecoveryRequired = false;
    pendingReady = true;
    insertMode = true;
    pendingPostAttempted = false;
    outputPolarityKnown = true;
    pinConfigSafe = true;
    controllerEnabled = true;
    coinEnabled = true;
    ledEnabled = true;
    relayEnabled = true;
    pollIntakeSuspended = false;
    runLedActiveHigh = activeHigh;
    runRelayActiveHigh = activeHigh;

    runLedPin = 14;
    runRelayPin = 5;
    ledLevel = activeHigh ? HIGH : LOW;
    relayLevel = activeHigh ? HIGH : LOW;

    activeTarget = "target-01";
    pendingNonce = "nonce12345678";
    pendingTarget = "target-01";

    backupMarkerPresent = false;
    littleFsMarkerPresent = false;
    backupPulseEdges = 0;
    littleFsPulseEdges = 0;
    backupWriteAttempts = 0;
    littleFsWriteAttempts = 0;
}

int runScenario(bool activeHigh) {
    resetScenario(activeHigh);

    // Positive control: a valid pending batch is eligible before the fault.
    if (!canAttemptCoinPost()) return 10;

    // One already-pending pulse plus one unassignable ISR edge forms the
    // first-fault snapshot. The real latch must persist that value to both
    // write-once V1 stores and turn both outputs off.
    coinEdgeSequence = 1;
    sampleCoinPulseEdge(true);
    const int offLevel = activeHigh ? HIGH : LOW;
    if (!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
        !backupMarkerPresent || !littleFsMarkerPresent ||
        backupPulseEdges != 2 || littleFsPulseEdges != 2 ||
        backupWriteAttempts != 1 || littleFsWriteAttempts != 1 ||
        relayLevel != offLevel || ledLevel != offLevel ||
        canAttemptCoinPost()) {
        return 11;
    }
    std::cout << "POLL_FAULT_FIRST_LATCH_PASS board=BOARD_NAME polarity="
              << (activeHigh ? "active-high" : "active-low")
              << " snapshot=2" << std::endl;

    // A later ISR edge is observed and consumed while the sticky deny is
    // already set. V1 remains the first-fault snapshot, not a live counter.
    coinEdgeSequence = 2;
    sampleCoinPulseEdge(true);
    if (lastHandledCoinEdgeSequence != 2 ||
        backupWriteAttempts != 1 || littleFsWriteAttempts != 1 ||
        backupPulseEdges != 2 || littleFsPulseEdges != 2 ||
        !journalRecoveryRequired || insertMode || !activeTarget.empty() ||
        relayLevel != offLevel || ledLevel != offLevel ||
        canAttemptCoinPost()) {
        return 12;
    }
    std::cout << "POLL_FAULT_SECOND_ISR_LOWER_BOUND_REPRODUCED board=BOARD_NAME polarity="
              << (activeHigh ? "active-high" : "active-low")
              << " first_fault_snapshot=2 later_edges=1 known_minimum=3"
              << " marker_unchanged=1 admission_denied=1 outputs_off=1"
              << std::endl;
    return 0;
}

int main() {
    int result = runScenario(true);
    if (result != 0) return result;
    result = runScenario(false);
    if (result != 0) return result;
    std::cout << "POLL_FAULT_SECOND_ISR_LAB=PASS board=BOARD_NAME" << std::endl;
    return 0;
}
"""

GUARD = "if(!journalRecoveryRequired){\n      latchPollPulseFault"


def compile_and_run(program: str, folder: Path, name: str):
    source_path = folder / (name + ".cpp")
    binary_path = folder / name
    source_path.write_text(program, encoding="utf-8")
    compile_result = subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pedantic",
            "-O2",
            str(source_path),
            "-o",
            str(binary_path),
        ],
        text=True,
        capture_output=True,
    )
    if compile_result.returncode != 0:
        raise AssertionError(
            "C++ source-extraction harness failed to compile:\n"
            + compile_result.stdout
            + compile_result.stderr
        )
    return subprocess.run(
        [str(binary_path)],
        text=True,
        capture_output=True,
    )


def check_board(board: str, sketch_path: Path):
    source = sketch_path.read_text(encoding="utf-8")
    names = (
        "snapshotCoinEdgeSequence",
        "writeLogical",
        "applyOutputs",
        "latchPollPulseFault",
        "canAttemptCoinPost",
        "sampleCoinPulseEdge",
    )
    extracted = {name: extract_function(source, name) for name in names}
    sample = extracted["sampleCoinPulseEdge"]
    if sample.count(GUARD) != 1:
        raise AssertionError(
            board + ": expected exactly one sticky-latch guard in sampleCoinPulseEdge"
        )

    ordered_functions = "\n\n".join(extracted[name] for name in names)
    board_main = PRELUDE + "\n" + ordered_functions + "\n"
    board_main += r"""
int main() {
    int result = runScenario(true);
    if (result != 0) return result;
    result = runScenario(false);
    if (result != 0) return result;
    std::cout << "POLL_FAULT_SECOND_ISR_LAB=PASS board=BOARD_NAME" << std::endl;
    return 0;
}
""".replace("BOARD_NAME", board)

    with tempfile.TemporaryDirectory(prefix="phx-second-isr-" + board.lower() + "-") as temp:
        folder = Path(temp)
        baseline = compile_and_run(board_main, folder, "baseline")
        if baseline.returncode != 0:
            raise AssertionError(
                board + " baseline failed:\n" + baseline.stdout + baseline.stderr
            )
        print(baseline.stdout, end="")

        mutant_sample = sample.replace(
            GUARD,
            "if(true){\n      latchPollPulseFault",
            1,
        )
        mutant_functions = ordered_functions.replace(sample, mutant_sample, 1)
        mutant_program = PRELUDE + "\n" + mutant_functions + "\n"
        mutant_program += r"""
int main() {
    int result = runScenario(true);
    if (result != 0) return result;
    result = runScenario(false);
    if (result != 0) return result;
    std::cout << "POLL_FAULT_SECOND_ISR_LAB=PASS board=BOARD_NAME" << std::endl;
    return 0;
}
""".replace("BOARD_NAME", board)
        mutant = compile_and_run(mutant_program, folder, "mutant")
        if mutant.returncode != 12:
            raise AssertionError(
                board + " repeated-latch mutation was not rejected at the expected assertion:\n"
                + mutant.stdout
                + mutant.stderr
                + "exit="
                + str(mutant.returncode)
            )
        print("MUTATION_REJECTED SECOND_ISR_REPEATED_LATCH board=" + board)
        print(
            "SOURCE_FUNCTION_SHA256 board="
            + board
            + " sha256="
            + hashlib.sha256(sample.encode("utf-8")).hexdigest()
        )


def main():
    for board, sketch_path in BOARDS:
        check_board(board, sketch_path)
    print("POLL_FAULT_SECOND_ISR_LAB=PASS boards=2 simulated_only=1")


if __name__ == "__main__":
    main()
