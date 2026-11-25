#!/usr/bin/env python3
"""Exact-source dual-store poll-fault persistence regression for ESP32 and ESP8266.

This host lab models the NVS and EEPROM APIs. It does not emulate flash physics,
power-loss timing, wear, or an independent physical witness.
"""
from pathlib import Path
import sys

from cpp_fixture_runner import run_cpp_fixture

from firmware_lab_source import find_repo_root
from poll_fault_dual_store_lab_fixtures import harness
from poll_fault_dual_store_lab_source_contracts import run_source_contracts

ROOT = find_repo_root(Path(__file__))
ESP32 = ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
ESP8266 = ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"

if "--root-probe" in sys.argv:
    if ESP32.is_file() and ESP8266.is_file():
        print("LAB_ROOT_EXTERNAL_CWD_PASS")
        raise SystemExit(0)
    print(f"LAB_ROOT_EXTERNAL_CWD_FAIL root={ROOT}", file=sys.stderr)
    raise SystemExit(1)


def _compile_and_run(program: str, *, board: str, label: str, prefix: str):
    """Compile and execute one C++ fixture with shared finite bounds."""
    return run_cpp_fixture(
        program,
        prefix=prefix,
        stem=label,
        compile_timeout=30,
        run_timeout=10,
        context=f"{board}: {label}",
    )


def run(board: str, path: Path):
    source = path.read_text(encoding="utf-8")
    program = harness(board, source)
    result = _compile_and_run(
        program,
        board=board,
        label="poll-fault",
        prefix="phx-poll-fault-",
    )
    if result.returncode:
        print(result.stdout or "", end="")
        print(result.stderr or "", file=sys.stderr, end="")
        raise AssertionError(
            f"{board}: poll fault baseline failed with exit {result.returncode}"
        )
    print(result.stdout, end="")
    required_markers = (
        f"POLL_FAULT_FIRST_LATCH_SNAPSHOT_STABLE_PASS board={board}",
    )
    if board == "ESP8266":
        required_markers += (
            "ESP8266_EEPROM_END_FAILURE_REBOOT_DENY_PASS",
            "ESP8266_EEPROM_REOPEN_FAILURE_REBOOT_DENY_PASS",
        )
    missing_markers = [marker for marker in required_markers if marker not in result.stdout]
    if missing_markers:
        raise AssertionError(
            "POLL_FAULT_REQUIRED_MARKERS_MISSING "
            f"board={board} markers={','.join(missing_markers)}"
        )


def run_esp32_missing_commit_mutation(path: Path):
    source = path.read_text(encoding="utf-8")
    needle = (
        "  if(nvs_commit(pollFaultNvsHandle)!=ESP_OK){\n"
        "    pollFaultBackupWriteFailed=true;\n"
        "    return false;\n"
        "  }\n"
    )
    if source.count(needle) != 1:
        raise AssertionError("ESP32 NVS commit call mutation anchor must occur exactly once")
    mutated_source = source.replace(
        needle,
        "  // MUTATION: deliberately omit nvs_commit; readback must not count as durable.\n",
        1,
    )
    program = harness("ESP32", mutated_source)
    result = _compile_and_run(
        program,
        board="ESP32",
        label="missing-commit",
        prefix="phx-nvs-commit-omission-",
    )
    expected = "POLL_FAULT_BACKUP_COMMIT_CALL_COUNT_FAIL board=ESP32 actual=0"
    if result.returncode != 61 or expected not in result.stderr:
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        raise AssertionError("omitted ESP32 nvs_commit was not rejected by the commit-count guard")
    print("MUTATION_REJECTED ESP32_NVS_COMMIT_OMITTED exit=61")


def run_esp32_precommit_persistence_mutation(path: Path):
    source = path.read_text(encoding="utf-8")
    program = harness("ESP32", source)
    needle = "NvsFlash::pending.assign(bytes,bytes+length);\n  return ESP_OK;"
    replacement = (
        "NvsFlash::pending.assign(bytes,bytes+length);\n"
        "  NvsFlash::durable.assign(bytes,bytes+length);\n"
        "  return ESP_OK;"
    )
    if program.count(needle) != 1:
        raise AssertionError("ESP32 NVS pre-commit mutation anchor must occur exactly once")
    mutated = program.replace(needle, replacement, 1)
    result = _compile_and_run(
        mutated,
        board="ESP32",
        label="precommit-persistence",
        prefix="phx-nvs-precommit-mutation-",
    )
    if result.returncode != 60 or "ESP32_NVS_SET_BLOB_DURABLE_BEFORE_COMMIT" not in result.stderr:
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        raise AssertionError("premature ESP32 NVS durability mutation was not rejected")
    print("MUTATION_REJECTED ESP32_NVS_SET_BLOB_PREMATURE_DURABILITY exit=60")




def run_first_fault_snapshot_overwrite_mutation(board: str, path: Path):
    """Prove the new first-latch regression rejects a writer that overwrites V1."""
    source = path.read_text(encoding="utf-8")
    if board == "ESP32":
        existing_guard = (
            "if(existing==ESP_OK) return true; // Any existing value, including malformed data, keeps the deny latch."
        )
        not_found_guard = "if(existing!=ESP_ERR_NVS_NOT_FOUND){"
        if source.count(existing_guard) != 1 or source.count(not_found_guard) != 1:
            raise AssertionError("ESP32 first-latch overwrite mutation anchors must be unique")
        mutated_source = source.replace(
            existing_guard,
            "if(existing==ESP_OK){ /* mutation: permit overwriting first-fault snapshot */ }",
            1,
        ).replace(
            not_found_guard,
            "if(existing!=ESP_ERR_NVS_NOT_FOUND && existing!=ESP_OK){",
            1,
        )
    else:
        existing_guard = (
            "for(size_t i=0;i<sizeof(existing);++i) if(existingBytes[i]!=0xFF) return true;"
        )
        if source.count(existing_guard) != 1:
            raise AssertionError("ESP8266 first-latch overwrite mutation anchor must be unique")
        mutated_source = source.replace(
            existing_guard,
            "for(size_t i=0;i<sizeof(existing);++i) (void)existingBytes[i];",
            1,
        )
    program = harness(board, mutated_source)
    result = _compile_and_run(
        program,
        board=board,
        label="first-fault-snapshot-overwrite",
        prefix="phx-first-latch-overwrite-mutation-",
    )
    expected = f"POLL_FAULT_FIRST_LATCH_SNAPSHOT_CHANGED board={board}"
    if result.returncode != 74 or expected not in result.stderr:
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        raise AssertionError(f"{board}: first-latch overwrite mutation was not rejected")
    print(f"MUTATION_REJECTED {board}_FIRST_LATCH_SNAPSHOT_OVERWRITE exit=74")


if __name__ == "__main__":
    run_source_contracts(Path(__file__).resolve(), ESP8266)
    run("ESP32", ESP32)
    run_first_fault_snapshot_overwrite_mutation("ESP32", ESP32)
    run_esp32_precommit_persistence_mutation(ESP32)
    run_esp32_missing_commit_mutation(ESP32)
    run("ESP8266", ESP8266)
    run_first_fault_snapshot_overwrite_mutation("ESP8266", ESP8266)
