#!/usr/bin/env python3
"""Run source-extracted pending-journal recovery checks for both boards."""
from pathlib import Path
import subprocess
import tempfile

from firmware_source_extract import extract_function
from pending_recovery_promotion_lab_contract import (
    assert_source_contract,
    expect_rejected,
    mutate_load,
    require,
)


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
