#!/usr/bin/env python3
# Hardware-owned test-only coverage addition to existing DRAFT PR #317.
# Final exact-head CI is re-triggered after the handover index synchronization and result recording.
"""Source-exact GPIO polarity lab for the ESP32 and ESP8266 output gate.

Uses the shared lexical-aware C/C++ extractor to compile the production
writeLogical() and applyOutputs() bodies from both sketches. It verifies
active-high and active-low OFF levels, every admission inhibit, and independent
LED/relay enable switches. Mutation builds reject parser and output-gate regressions.

Host simulation only: it does not measure relay contacts, board pins, driver
polarity, wiring, or coin-acceptor behavior.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from firmware_lab_source import extract_function

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def extract(source, name):
    return extract_function(source, name)


def verify_lexical_extractor_regression():
    cases = (
        ("ordinary string", '  const char *value = "}";'),
        ("C++ raw string", '  const char *value = R"tag(} )tag";'),
        ("line comment", "  // }"),
        ("block comment", "  /* } */"),
    )
    failures = []
    for label, statement in cases:
        fixture = (
            "void target(){\n"
            + statement
            + "\n  return;\n}\nvoid after(){ return; }\n"
        )
        extracted = extract(fixture, "target")
        if "return;" not in extracted or "void after()" in extracted:
            failures.append(label)
    if failures:
        raise SystemExit(
            "RELAY_OUTPUT_EXTRACTOR_FAIL: non-code brace truncated target(): "
            + ", ".join(failures)
        )
    print("RELAY_OUTPUT_LEXICAL_EXTRACTOR_PASS 4/4")


verify_lexical_extractor_regression()


STUBS = r"""
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <map>
#include <string>

struct String {
  std::string value;
  String(const char *text = "") : value(text) {}
  size_t length() const { return value.size(); }
};

static constexpr int HIGH = 1;
static constexpr int LOW = 0;
std::map<int, int> gpioLevels;
void digitalWrite(int pin, int level) { gpioLevels[pin] = level; }

bool pinConfigSafe = true;
bool controllerEnabled = true;
bool coinEnabled = true;
bool relayEnabled = true;
bool ledEnabled = true;
bool insertMode = true;
bool fsReady = true;
bool journalRecoveryRequired = false;
bool pendingReady = false;
bool pollIntakeSuspended = false;
// This polarity lab has no ISR injection; keep the source edge guard idle.
// Poll-loop labs separately inject edges at the GPIO write boundaries.
volatile uint32_t coinEdgeSequence = 0;
uint32_t lastHandledCoinEdgeSequence = 0;
uint32_t snapshotCoinEdgeSequence() { return coinEdgeSequence; }
bool outputPolarityKnown = true; // unrelated output tests model a validated local profile
bool runRelayActiveHigh = true;
bool runLedActiveHigh = true;
int runRelayPin = 26;
int runLedPin = 2;
String activeTarget("target-01");

int failures = 0;
int scenarios = 0;

void resetState() {
  gpioLevels.clear();
  pinConfigSafe = true;
  controllerEnabled = true;
  coinEnabled = true;
  relayEnabled = true;
  ledEnabled = true;
  insertMode = true;
  fsReady = true;
  journalRecoveryRequired = false;
  pendingReady = false;
  pollIntakeSuspended = false;
  coinEdgeSequence = 0;
  lastHandledCoinEdgeSequence = 0;
  outputPolarityKnown = true;
  runRelayActiveHigh = true;
  runLedActiveHigh = true;
  runRelayPin = 26;
  runLedPin = 2;
  activeTarget = String("target-01");
}

bool matchesLevel(int pin, bool activeHigh, bool shouldBeActive) {
  const auto found = gpioLevels.find(pin);
  if (found == gpioLevels.end()) return false;
  const int expected = shouldBeActive
      ? (activeHigh ? HIGH : LOW)
      : (activeHigh ? LOW : HIGH);
  return found->second == expected;
}

void checkBoth(bool relayActive, bool ledActive, const char *label) {
  ++scenarios;
  if (!matchesLevel(runRelayPin, runRelayActiveHigh, relayActive)) {
    ++failures;
    std::cerr << "GPIO_POLARITY_FAIL " << label << " relay level\n";
  }
  if (!matchesLevel(runLedPin, runLedActiveHigh, ledActive)) {
    ++failures;
    std::cerr << "GPIO_POLARITY_FAIL " << label << " LED level\n";
  }
}

void denyPinConfig() { pinConfigSafe = false; }
void denyController() { controllerEnabled = false; }
void denyCoin() { coinEnabled = false; }
void denyInsertMode() { insertMode = false; }
void denyTarget() { activeTarget = String(""); }
void denyFilesystem() { fsReady = false; }
void denyRecovery() { journalRecoveryRequired = true; }
void denyPending() { pendingReady = true; }
void denyPollWindow() { pollIntakeSuspended = true; }

using Mutator = void (*)();
static const Mutator denyCases[] = {
  denyPinConfig, denyController, denyCoin, denyInsertMode, denyTarget,
  denyFilesystem, denyRecovery, denyPending, denyPollWindow
};
static const char *denyNames[] = {
  "unsafe GPIO config", "controller disabled", "coin disabled",
  "insert mode disabled", "missing target", "filesystem unavailable",
  "journal recovery required", "pending event exists", "poll intake suspended"
};
"""

MAIN = r"""
int main() {
  for (int relayHigh = 0; relayHigh <= 1; ++relayHigh) {
    for (int ledHigh = 0; ledHigh <= 1; ++ledHigh) {
      resetState();
      runRelayActiveHigh = relayHigh != 0;
      runLedActiveHigh = ledHigh != 0;
      applyOutputs();
      checkBoth(true, true, "positive admission");

      for (size_t i = 0; i < sizeof(denyCases) / sizeof(denyCases[0]); ++i) {
        resetState();
        runRelayActiveHigh = relayHigh != 0;
        runLedActiveHigh = ledHigh != 0;
        denyCases[i]();
        applyOutputs();
        checkBoth(false, false, denyNames[i]);
      }

      resetState();
      runRelayActiveHigh = relayHigh != 0;
      runLedActiveHigh = ledHigh != 0;
      relayEnabled = false;
      applyOutputs();
      checkBoth(false, true, "relay output disabled");

      resetState();
      runRelayActiveHigh = relayHigh != 0;
      runLedActiveHigh = ledHigh != 0;
      ledEnabled = false;
      applyOutputs();
      checkBoth(true, false, "LED output disabled");
    }
  }

  if (failures != 0 || scenarios != 48) {
    std::cerr << "GPIO_POLARITY_FAILED scenarios=" << scenarios
              << " failures=" << failures << "\n";
    return 1;
  }
  std::cout << "RELAY_OUTPUT_POLARITY_PASS 48/48 scenarios\n";
  std::cout << "ACTIVE_HIGH_AND_ACTIVE_LOW_OFF_LEVELS_VERIFIED=1\n";
  std::cout << "POLL_INHIBIT_LOGICAL_OFF_VERIFIED=1\n";
  std::cout << "PHYSICAL_RELAY_POLARITY_VERIFIED=0\n";
  return 0;
}
"""


def compile_and_run(board, source, variant):
    write_logical = extract(source, "writeLogical")
    apply_outputs = extract(source, "applyOutputs")

    if variant == "invert-write-logical":
        expected = "(on==activeHigh)?HIGH:LOW"
        if expected not in write_logical:
            raise RuntimeError(board + ": writeLogical mapping changed; review lab")
        write_logical = write_logical.replace(
            expected, "(on==activeHigh)?LOW:HIGH", 1
        )
    elif variant == "remove-poll-inhibit":
        expected = " && !pollIntakeSuspended"
        if expected not in apply_outputs:
            raise RuntimeError(board + ": poll inhibit expression changed; review lab")
        apply_outputs = apply_outputs.replace(expected, "", 1)

    code = STUBS + "\n" + write_logical + "\n" + apply_outputs + "\n" + MAIN
    with tempfile.TemporaryDirectory(prefix="phx-relay-polarity-") as folder:
        cpp = Path(folder) / "relay_output.cpp"
        binary = Path(folder) / "relay_output"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            raise RuntimeError(
                board + " " + variant + " compile failed:\n" + built.stderr[-4000:]
            )
        return subprocess.run(
            [str(binary)], capture_output=True, text=True, timeout=10
        )


def main():
    for board, path in BOARDS.items():
        source = path.read_text(encoding="utf-8")
        normal = compile_and_run(board, source, "normal")
        if normal.returncode != 0:
            raise RuntimeError(
                board + " production source failed:\n" +
                normal.stdout + normal.stderr
            )
        print(board + ": " + normal.stdout.strip())

        for mutation in ("invert-write-logical", "remove-poll-inhibit"):
            injected = compile_and_run(board, source, mutation)
            if injected.returncode == 0 or "GPIO_POLARITY_FAIL" not in injected.stderr:
                raise RuntimeError(
                    board + ": mutation was not detected: " + mutation
                )
            print(board + ": MUTATION_REJECTED " + mutation)

    print("PHX-HARDWARE: source-exact active-high/active-low output gate verified")
    print("SIMULATED_ONLY=1")
    print("PHYSICAL_RELAY_POLARITY_VERIFIED=0")
    print("PHYSICAL_POWER_CUT_VERIFIED=0")
    print("FINANCIAL_PRODUCTION_AUTHORIZED=0")


if __name__ == "__main__":
    main()
