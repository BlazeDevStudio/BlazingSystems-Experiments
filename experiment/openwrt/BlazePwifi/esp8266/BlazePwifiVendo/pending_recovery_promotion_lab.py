#!/usr/bin/env python3
"""Fail-closed ESP pending-journal recovery promotion checks for both boards."""
from pathlib import Path
import re
import subprocess
import tempfile

from firmware_source_extract import extract_braced, extract_function, mask_non_code

BLAZEPWIFI = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": BLAZEPWIFI / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_if_block(function: str, pattern: str, label: str) -> tuple[str, int]:
    masked = mask_non_code(function)
    match = re.search(pattern, function)
    require(match is not None, f"missing {label} guard")
    opening = masked.find("{", match.end())
    require(opening >= 0, f"{label} guard has no body")
    block = extract_braced(function, opening)
    return block, opening + len(block)


def require_deny_block(block: str, label: str) -> None:
    masked = mask_non_code(block)
    for token in ("fsReady=false;", "pendingReady=true;", "return false;"):
        require(token in masked, f"{label} must set {token}")


def assert_source_contract(source: str) -> None:
    raw = extract_function(source, "bool loadPending()")
    masked = mask_non_code(raw)

    require('LittleFS.remove("/pending.dat")' not in raw,
            "recovery must not delete an existing canonical journal")
    require("pendingSequenceState=r;" in masked,
            "valid recovered state must be published after promotion succeeds")

    no_candidate, _ = extract_if_block(
        raw, r"if\s*\(\s*!\s*chosen\s*\)", "no-valid-candidate"
    )
    no_candidate_masked = mask_non_code(no_candidate)
    require(re.search(r"if\s*\(\s*any\s*\)", no_candidate_masked) is not None,
            "existing invalid journal files must not be treated as an empty journal")
    any_block, _ = extract_if_block(
        no_candidate, r"if\s*\(\s*any\s*\)", "invalid-candidate"
    )
    require_deny_block(any_block, "invalid-candidate")

    empty_write, _ = extract_if_block(
        no_candidate,
        r"if\s*\(\s*!\s*persistPendingSequence\s*\(\s*pendingSequenceState\s*\)\s*\)",
        "initial-empty-journal-write",
    )
    require_deny_block(empty_write, "initial-empty-journal-write")

    promote, promote_end = extract_if_block(
        raw,
        r"if\s*\(\s*strcmp\s*\(\s*chosen\s*,\s*\"/pending\.dat\"\s*\)\s*!=\s*0\s*\)",
        "fallback-promotion",
    )
    conflict, _ = extract_if_block(
        promote,
        r"if\s*\(\s*LittleFS\.exists\s*\(\s*\"/pending\.dat\"\s*\)\s*\)",
        "canonical-fallback-conflict",
    )
    require_deny_block(conflict, "canonical-fallback-conflict")

    rename_failure, _ = extract_if_block(
        promote,
        r"if\s*\(\s*!\s*LittleFS\.rename\s*\(\s*chosen\s*,\s*\"/pending\.dat\"\s*\)\s*\)",
        "fallback-rename-result",
    )
    require_deny_block(rename_failure, "fallback-rename-result")

    state_position = masked.find("pendingSequenceState=r;")
    require(state_position > promote_end,
            "RAM journal state must not be published before fallback promotion succeeds")

    legacy_failure, _ = extract_if_block(
        raw,
        r"if\s*\(\s*legacy\s*&&\s*!\s*persistPendingSequence\s*\(\s*r\s*\)\s*\)",
        "legacy-journal-migration",
    )
    require_deny_block(legacy_failure, "legacy-journal-migration")


def expect_rejected(label: str, mutated: str) -> None:
    try:
        assert_source_contract(mutated)
    except AssertionError:
        print(f"PENDING_RECOVERY_MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe pending-recovery mutation accepted: {label}")


def cxx_harness(load_function: str) -> str:
    return r"""
#include <cstdint>
#include <cstring>
#include <iostream>

struct BpPendingSequence {
    uint32_t sequence;
    uint8_t pulses;
    char nonce[17];
    char target[33];
};

class String {
public:
    String() = default;
    String(const char *value) : value_(value ? value : "") {}
private:
    const char *value_ = "";
};

struct FakeLittleFS {
    bool dat = false;
    bool fresh = false;
    bool backup = false;
    bool failRename = false;
    int renameCalls = 0;

    bool exists(const char *path) const {
        if (std::strcmp(path, "/pending.dat") == 0) return dat;
        if (std::strcmp(path, "/pending.new") == 0) return fresh;
        if (std::strcmp(path, "/pending.bak") == 0) return backup;
        return false;
    }

    bool rename(const char *from, const char *to) {
        ++renameCalls;
        if (failRename) return false;
        bool *source = slot(from);
        bool *destination = slot(to);
        if (!source || !destination || !*source || *destination) return false;
        *source = false;
        *destination = true;
        return true;
    }

private:
    bool *slot(const char *path) {
        if (std::strcmp(path, "/pending.dat") == 0) return &dat;
        if (std::strcmp(path, "/pending.new") == 0) return &fresh;
        if (std::strcmp(path, "/pending.bak") == 0) return &backup;
        return nullptr;
    }
} LittleFS;

struct FakeSerial {
    void println(const char *) {}
} Serial;

bool fsReady = true;
bool pendingReady = false;
uint8_t pendingPulses = 0;
uint32_t lastSend = 99;
BpPendingSequence pendingSequenceState{};
String pendingNonce;
String pendingTarget;
const char *selectedPath = nullptr;
bool selectedLegacy = false;
bool persistOk = true;
int persistCalls = 0;

bool readPendingFile(const char *path, BpPendingSequence &state, bool &legacy) {
    if (!LittleFS.exists(path) || !selectedPath ||
        std::strcmp(path, selectedPath) != 0) return false;
    state.sequence = 9;
    state.pulses = 3;
    std::strcpy(state.nonce, "AABBCCDDEEFF0011");
    std::strcpy(state.target, "00112233");
    legacy = selectedLegacy;
    return true;
}

void bp_pending_sequence_init(BpPendingSequence *state) {
    std::memset(state, 0, sizeof(*state));
}

bool persistPendingSequence(const BpPendingSequence &) {
    ++persistCalls;
    if (!persistOk) return false;
    LittleFS.dat = true;
    return true;
}

""" + load_function + r"""

static void resetState() {
    LittleFS = FakeLittleFS{};
    fsReady = true;
    pendingReady = false;
    pendingPulses = 0;
    lastSend = 99;
    pendingSequenceState = BpPendingSequence{};
    pendingNonce = String();
    pendingTarget = String();
    selectedPath = nullptr;
    selectedLegacy = false;
    persistOk = true;
    persistCalls = 0;
}

int main() {
    resetState();
    LittleFS.dat = true;
    selectedPath = "/pending.dat";
    if (!loadPending() || !fsReady || !pendingReady ||
        pendingSequenceState.sequence != 9 || LittleFS.renameCalls != 0) return 1;

    resetState();
    LittleFS.fresh = true;
    selectedPath = "/pending.new";
    if (!loadPending() || !fsReady || !pendingReady ||
        pendingSequenceState.sequence != 9 || !LittleFS.dat ||
        LittleFS.fresh || LittleFS.renameCalls != 1) return 2;

    resetState();
    LittleFS.backup = true;
    selectedPath = "/pending.bak";
    if (!loadPending() || !fsReady || !pendingReady ||
        pendingSequenceState.sequence != 9 || !LittleFS.dat ||
        LittleFS.backup || LittleFS.renameCalls != 1) return 3;

    resetState();
    LittleFS.dat = true;
    LittleFS.fresh = true;
    selectedPath = "/pending.new";
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.dat || !LittleFS.fresh ||
        pendingSequenceState.sequence != 0 || LittleFS.renameCalls != 0) return 4;

    resetState();
    LittleFS.dat = true;
    LittleFS.backup = true;
    selectedPath = "/pending.bak";
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.dat || !LittleFS.backup ||
        pendingSequenceState.sequence != 0 || LittleFS.renameCalls != 0) return 5;

    resetState();
    LittleFS.fresh = true;
    selectedPath = "/pending.new";
    LittleFS.failRename = true;
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.fresh || LittleFS.dat ||
        pendingSequenceState.sequence != 0 || LittleFS.renameCalls != 1) return 6;

    resetState();
    LittleFS.backup = true;
    selectedPath = "/pending.bak";
    LittleFS.failRename = true;
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.backup || LittleFS.dat ||
        pendingSequenceState.sequence != 0 || LittleFS.renameCalls != 1) return 7;

    resetState();
    LittleFS.dat = true;
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.dat || pendingSequenceState.sequence != 0) return 8;

    resetState();
    if (!loadPending() || !fsReady || !LittleFS.dat ||
        pendingSequenceState.sequence != 0 || persistCalls != 1) return 9;

    resetState();
    persistOk = false;
    if (loadPending() || fsReady || !pendingReady ||
        LittleFS.dat || persistCalls != 1) return 10;

    resetState();
    LittleFS.dat = true;
    selectedPath = "/pending.dat";
    selectedLegacy = true;
    persistOk = false;
    if (loadPending() || fsReady || !pendingReady ||
        pendingSequenceState.sequence != 9 || !LittleFS.dat ||
        persistCalls != 1) return 11;

    std::cout << "PENDING_RECOVERY_PROMOTION_PASS scenarios=11 rename_failures=2 ambiguous_preservation=2\n";
    return 0;
}
"""


def compile_and_run(source: str, label: str) -> str:
    with tempfile.TemporaryDirectory(prefix="phx-pending-recovery-") as directory:
        cpp = Path(directory) / f"{label}.cpp"
        exe = Path(directory) / label
        cpp.write_text(source, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run([str(exe)], check=True, capture_output=True, text=True)
        return result.stdout.strip()


def main() -> None:
    for board, sketch in SKETCHES.items():
        source = sketch.read_text(encoding="utf-8")
        assert_source_contract(source)
        load = extract_function(source, "bool loadPending()")

        expect_rejected(
            f"{board}-ambiguous-canonical-accepted",
            source.replace('if(LittleFS.exists("/pending.dat"))',
                           "if(false)", 1),
        )
        expect_rejected(
            f"{board}-rename-result-ignored",
            source.replace('if(!LittleFS.rename(chosen,"/pending.dat"))',
                           'if(LittleFS.rename(chosen,"/pending.dat"))', 1),
        )
        expect_rejected(
            f"{board}-canonical-evidence-deleted",
            source.replace('if(strcmp(chosen,"/pending.dat")!=0){',
                           'if(strcmp(chosen,"/pending.dat")!=0){LittleFS.remove("/pending.dat");', 1),
        )
        expect_rejected(
            f"{board}-filesystem-not-denied",
            source.replace("fsReady=false;", "fsReady=true;", 1),
        )
        expect_rejected(
            f"{board}-pending-hold-not-latched",
            source.replace("pendingReady=true;", "pendingReady=false;", 1),
        )
        expect_rejected(
            f"{board}-ram-state-published-before-promotion",
            source.replace('if(strcmp(chosen,"/pending.dat")!=0){',
                           'pendingSequenceState=r;\n  if(strcmp(chosen,"/pending.dat")!=0){', 1),
        )
        expect_rejected(
            f"{board}-empty-journal-write-result-ignored",
            source.replace("if(!persistPendingSequence(pendingSequenceState))",
                           "if(persistPendingSequence(pendingSequenceState))", 1),
        )
        expect_rejected(
            f"{board}-legacy-migration-result-ignored",
            source.replace("if(legacy && !persistPendingSequence(r))",
                           "if(legacy && persistPendingSequence(r))", 1),
        )

        output = compile_and_run(cxx_harness(load), board.lower())
        require("PENDING_RECOVERY_PROMOTION_PASS scenarios=11" in output,
                f"{board} C++ failure-injection harness did not complete")
        print(f"{board}: {output}")

    print("PENDING_RECOVERY_PROMOTION_LAB_PASS boards=ESP8266,ESP32 mutations_rejected=16")


if __name__ == "__main__":
    main()
