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
    require('strcmp(chosen,"/pending.dat")!=0' in raw,
            "fallback selection must be explicit")
    require('LittleFS.exists("/pending.dat")' in raw,
            "canonical/fallback ambiguity must be detected")
    require('LittleFS.rename(chosen,"/pending.dat")' in raw,
            "fallback promotion must target the canonical journal")
    require("candidateCount > 1" in masked,
            "coexisting journal candidates must fail closed before candidate selection")
    multiple_candidates, multiple_end = extract_if_block(
        raw, r"if\s*\(\s*candidateCount\s*>\s*1\s*\)", "multiple-journal-candidates"
    )
    require_deny_block(multiple_candidates, "multiple-journal-candidates")
    first_candidate_read = raw.find('readPendingFile("/pending.dat"')
    require(first_candidate_read >= 0 and multiple_end < first_candidate_read,
            "multiple-candidate denial must precede every journal read/promotion")

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
        r"if\s*\(\s*strcmp\s*\(\s*chosen",
        "fallback-promotion",
    )
    conflict, _ = extract_if_block(
        promote,
        r"if\s*\(\s*LittleFS\.exists\s*\(",
        "canonical-fallback-conflict",
    )
    require_deny_block(conflict, "canonical-fallback-conflict")

    rename_failure, _ = extract_if_block(
        promote,
        r"if\s*\(\s*!\s*LittleFS\.rename\s*\(",
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


def mutate_load(source: str, old: str, new: str) -> str:
    load = extract_function(source, "bool loadPending()")
    require(old in load, f"missing mutation anchor in loadPending: {old}")
    changed = load.replace(old, new, 1)
    start = source.find(load)
    require(start >= 0, "could not locate loadPending source span")
    return source[:start] + changed + source[start + len(load):]


def expect_rejected(label: str, mutated: str) -> None:
    try:
        assert_source_contract(mutated)
    except AssertionError:
        print(f"PENDING_RECOVERY_MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe pending-recovery mutation accepted: {label}")


def cxx_harness(load_function: str) -> str:
    template_path = Path(__file__).with_name("pending_recovery_promotion_lab_harness.hpp")
    template = template_path.read_text(encoding="utf-8")
    marker = "/*__LOAD_PENDING_FUNCTION__*/"
    require(template.count(marker) == 1,
            "C++ harness template must contain exactly one loadPending insertion marker")
    return template.replace(marker, load_function, 1)

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
            mutate_load(source, 'if(LittleFS.exists("/pending.dat"))',
                        "if(false)"),
        )
        expect_rejected(
            f"{board}-multiple-candidates-not-denied",
            mutate_load(source, "if(candidateCount > 1){", "if(candidateCount > 2){"),
        )
        expect_rejected(
            f"{board}-rename-result-ignored",
            mutate_load(source, 'if(!LittleFS.rename(chosen,"/pending.dat"))',
                        'if(LittleFS.rename(chosen,"/pending.dat"))'),
        )
        expect_rejected(
            f"{board}-canonical-evidence-deleted",
            mutate_load(source, 'if(strcmp(chosen,"/pending.dat")!=0){',
                        'if(strcmp(chosen,"/pending.dat")!=0){LittleFS.remove("/pending.dat");'),
        )
        expect_rejected(
            f"{board}-filesystem-not-denied",
            mutate_load(source, "fsReady=false;", "fsReady=true;"),
        )
        expect_rejected(
            f"{board}-pending-hold-not-latched",
            mutate_load(source, "pendingReady=true;", "pendingReady=false;"),
        )
        expect_rejected(
            f"{board}-ram-state-published-before-promotion",
            mutate_load(source, 'if(strcmp(chosen,"/pending.dat")!=0){',
                        'pendingSequenceState=r;\n  if(strcmp(chosen,"/pending.dat")!=0){'),
        )
        expect_rejected(
            f"{board}-empty-journal-write-result-ignored",
            mutate_load(source, "if(!persistPendingSequence(pendingSequenceState))",
                        "if(persistPendingSequence(pendingSequenceState))"),
        )
        expect_rejected(
            f"{board}-legacy-migration-result-ignored",
            mutate_load(source, "if(legacy && !persistPendingSequence(r))",
                        "if(legacy && persistPendingSequence(r))"),
        )

        output = compile_and_run(cxx_harness(load), board.lower())
        require("PENDING_RECOVERY_PROMOTION_PASS scenarios=15" in output,
                f"{board} C++ failure-injection harness did not complete")
        print(f"{board}: {output}")

    print("PENDING_RECOVERY_PROMOTION_LAB_PASS boards=ESP8266,ESP32 mutations_rejected=18")


if __name__ == "__main__":
    main()
