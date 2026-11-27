#!/usr/bin/env python3
"""Source-extracted, fail-closed pending-journal persistence failure tests."""
from pathlib import Path
import re
import subprocess
import tempfile

from firmware_source_extract import extract_function

BLAZEPWIFI = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": BLAZEPWIFI / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_source_contract(source: str) -> str:
    function = extract_function(source, "bool persistPendingSequence(")

    backup_remove_guard = re.compile(
        r'if\s*\(\s*LittleFS\.exists\(\s*"/pending\.bak"\s*\)\s*&&\s*'
        r'!LittleFS\.remove\(\s*"/pending\.bak"\s*\)\s*\)\s*\{\s*'
        r'Serial\.println\(\s*"[^"]+"\s*\)\s*;\s*return\s+false\s*;\s*\}'
    )
    require(len(backup_remove_guard.findall(function)) == 2,
            "both stale-backup and post-promotion cleanup failures must log and abort")

    dat_backup_guard = re.compile(
        r'if\s*\(\s*LittleFS\.exists\(\s*"/pending\.dat"\s*\)\s*&&\s*'
        r'!LittleFS\.rename\(\s*"/pending\.dat"\s*,\s*"/pending\.bak"\s*\)\s*'
        r'\)\s*\{\s*Serial\.println\(\s*"[^"]+"\s*\)\s*;\s*'
        r'return\s+false\s*;\s*\}'
    )
    require(dat_backup_guard.search(function) is not None,
            "canonical-to-backup rename failure must log and abort before promotion")

    promote_guard = re.compile(
        r'if\s*\(\s*!LittleFS\.rename\(\s*"/pending\.new"\s*,\s*"/pending\.dat"\s*\)\s*\)'
    )
    require(promote_guard.search(function) is not None,
            "new journal promotion result must be checked")

    restore_guard = re.compile(
        r'if\s*\(\s*!LittleFS\.exists\(\s*"/pending\.dat"\s*\)\s*&&\s*'
        r'LittleFS\.exists\(\s*"/pending\.bak"\s*\)\s*&&\s*'
        r'!LittleFS\.rename\(\s*"/pending\.bak"\s*,\s*"/pending\.dat"\s*\)\s*\)\s*\{\s*'
        r'Serial\.println\(\s*"[^"]+"\s*\)\s*;\s*\}'
    )
    require(restore_guard.search(function) is not None,
            "backup restore failure must be visible and must not publish RAM state")

    write_pos = function.find("f.write(")
    flush_pos = function.find("f.flush()")
    short_write_pos = function.find("if(n!=sizeof(state))")
    first_backup_cleanup = function.find('LittleFS.remove("/pending.bak")')
    require(write_pos >= 0 and flush_pos > write_pos,
            "new journal bytes must be written before flush")
    require(short_write_pos > flush_pos and first_backup_cleanup > short_write_pos,
            "short-write refusal must precede every backup mutation")

    state_pos = function.find("pendingSequenceState=state;")
    last_backup_cleanup = function.rfind('LittleFS.remove("/pending.bak")')
    return_true_pos = function.rfind("return true;")
    require(last_backup_cleanup >= 0 and state_pos > last_backup_cleanup,
            "RAM authority must not advance before backup cleanup succeeds")
    require(return_true_pos > state_pos,
            "success must be returned only after RAM authority is updated")
    require(function.count('LittleFS.remove("/pending.bak")') == 2,
            "no unguarded backup deletion may remain")
    return function


def mutate_function(source: str, old: str, new: str, occurrence: int = 1) -> str:
    function = extract_function(source, "bool persistPendingSequence(")
    require(function.count(old) >= occurrence,
            f"missing persistence mutation anchor: {old}")
    pieces = function.split(old)
    changed = old.join(pieces[:occurrence]) + new + old.join(pieces[occurrence:])
    start = source.find(function)
    require(start >= 0, "could not locate persistPendingSequence source span")
    return source[:start] + changed + source[start + len(function):]


def expect_rejected(label: str, mutated: str) -> None:
    try:
        assert_source_contract(mutated)
    except AssertionError:
        print(f"PENDING_PERSIST_MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe pending-persist mutation accepted: {label}")


def compile_and_run(function: str, label: str) -> str:
    template_path = Path(__file__).with_name("pending_persist_failure_lab_harness.hpp")
    template = template_path.read_text(encoding="utf-8")
    marker = "/*__PERSIST_PENDING_SEQUENCE_FUNCTION__*/"
    require(template.count(marker) == 1,
            "C++ harness must contain exactly one persistence insertion marker")
    harness = template.replace(marker, function, 1)

    with tempfile.TemporaryDirectory(prefix="phx-pending-persist-") as directory:
        cpp = Path(directory) / f"{label}.cpp"
        exe = Path(directory) / label
        cpp.write_text(harness, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run([str(exe)], check=True, capture_output=True, text=True)
        return result.stdout.strip()


def main() -> None:
    stale_cleanup = (
        '  if(LittleFS.exists("/pending.bak") && !LittleFS.remove("/pending.bak")){\n'
        '    Serial.println("CRITICAL: stale pending backup removal failed; preserving journal candidates.");\n'
        '    return false;\n'
        '  }'
    )
    final_cleanup = (
        '  if(LittleFS.exists("/pending.bak") && !LittleFS.remove("/pending.bak")){\n'
        '    Serial.println("CRITICAL: stale pending backup cleanup failed; denying intake.");\n'
        '    return false;\n'
        '  }'
    )
    dat_rotation = (
        '  if(LittleFS.exists("/pending.dat") && !LittleFS.rename("/pending.dat","/pending.bak")){\n'
        '    Serial.println("CRITICAL: canonical pending journal rotation failed; preserving candidates.");\n'
        '    return false;\n'
        '  }'
    )
    promotion = 'if(!LittleFS.rename("/pending.new","/pending.dat"))'
    restore = (
        '    if(!LittleFS.exists("/pending.dat") && LittleFS.exists("/pending.bak") &&\n'
        '       !LittleFS.rename("/pending.bak","/pending.dat")){\n'
        '      Serial.println("CRITICAL: pending backup restore failed; preserving journal candidates.");\n'
        '    }'
    )

    for board, sketch in SKETCHES.items():
        source = sketch.read_text(encoding="utf-8")
        function = assert_source_contract(source)

        expect_rejected(
            f"{board}-stale-backup-remove-result-ignored",
            mutate_function(source, stale_cleanup, '  LittleFS.remove("/pending.bak");'),
        )
        expect_rejected(
            f"{board}-canonical-backup-rename-result-ignored",
            mutate_function(source, dat_rotation, '  LittleFS.rename("/pending.dat","/pending.bak");'),
        )
        expect_rejected(
            f"{board}-promotion-result-inverted",
            mutate_function(source, promotion, 'if(LittleFS.rename("/pending.new","/pending.dat"))'),
        )
        expect_rejected(
            f"{board}-backup-cleanup-result-ignored",
            mutate_function(source, final_cleanup, '  LittleFS.remove("/pending.bak");'),
        )
        expect_rejected(
            f"{board}-backup-restore-result-inverted",
            mutate_function(source, restore, restore.replace(
                '!LittleFS.rename("/pending.bak","/pending.dat")',
                'LittleFS.rename("/pending.bak","/pending.dat")')),
        )
        expect_rejected(
            f"{board}-ram-state-published-before-cleanup",
            mutate_function(source, final_cleanup,
                            '  pendingSequenceState=state;\n'+final_cleanup),
        )

        output = compile_and_run(function, board.lower())
        require("PENDING_PERSIST_FAILURE_PASS scenarios=17" in output,
                f"{board} persistence failure-injection harness did not complete")
        print(f"{board}: {output}")

    print("PENDING_PERSIST_FAILURE_LAB_PASS boards=ESP8266,ESP32 mutations_rejected=12")


if __name__ == "__main__":
    main()
