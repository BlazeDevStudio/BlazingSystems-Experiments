#!/usr/bin/env python3
"""Structural and byte-preservation guard for the poll-response lab split.

The embedded C++ programs are fixture data, not Python runner logic. Keep the
runner small and the four fixture payloads byte-identical during extraction.
"""
import ast
import importlib.util
import subprocess
from unittest.mock import patch

import cpp_fixture_runner as shared_runner
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "poll_response_failclosed_lab.py"
FIXTURE_PATH = HERE / "poll_response_failclosed_lab_fixtures.py"
EXPECTED_FNV1A64 = {
    "STUBS": "8d23424dc58cf900",
    "MAIN": "00e8ea1d021d8c2f",
    "WINDOW_STUBS": "936f01b6daf04b8e",
    "WINDOW_MAIN": "d54f6e31c6e19567"
}

def fnv1a64(data):
    value = 14695981039346656037
    for byte in data:
        value ^= byte
        value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"

runner_source = RUNNER_PATH.read_text(encoding="utf-8")
runner_tree = ast.parse(runner_source)
shared_runner_imports = {
    alias.name
    for node in runner_tree.body
    if isinstance(node, ast.ImportFrom)
    and node.module == "cpp_fixture_runner"
    for alias in node.names
}
if shared_runner_imports != {"run_cpp_fixture"}:
    raise AssertionError("POLL_RESPONSE_SHARED_RUNNER_IMPORT_MISSING")

direct_imports = {
    alias.name.split(".")[0]
    for node in runner_tree.body
    if isinstance(node, ast.Import)
    for alias in node.names
}
if {"subprocess", "tempfile"} & direct_imports:
    raise AssertionError("POLL_RESPONSE_LOCAL_PROCESS_RUNNER_REMAINS")

direct_process_calls = [
    node for node in ast.walk(runner_tree)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Attribute)
    and isinstance(node.func.value, ast.Name)
    and node.func.value.id in {"subprocess", "tempfile"}
]
if direct_process_calls:
    raise AssertionError("POLL_RESPONSE_LOCAL_PROCESS_CALL_REMAINS")

required = set(EXPECTED_FNV1A64)
imports = {
    alias.name
    for node in runner_tree.body
    if isinstance(node, ast.ImportFrom)
    and node.module == "poll_response_failclosed_lab_fixtures"
    for alias in node.names
}
if imports != required:
    raise AssertionError("POLL_RESPONSE_FIXTURE_IMPORT_MISSING_OR_INCOMPLETE")

inline_assignments = set()
for node in runner_tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                inline_assignments.add(target.id)
if inline_assignments & required:
    raise AssertionError("POLL_RESPONSE_INLINE_FIXTURE_REMAINS")

if not FIXTURE_PATH.is_file():
    raise AssertionError("POLL_RESPONSE_FIXTURE_MODULE_MISSING")

spec = importlib.util.spec_from_file_location("_phx_poll_response_fixtures", FIXTURE_PATH)
if spec is None or spec.loader is None:
    raise AssertionError("POLL_RESPONSE_FIXTURE_MODULE_UNLOADABLE")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

fixture_tree = ast.parse(FIXTURE_PATH.read_text(encoding="utf-8"))
assigned = {
    target.id
    for node in fixture_tree.body
    if isinstance(node, ast.Assign)
    for target in node.targets
    if isinstance(target, ast.Name)
}
if not required.issubset(assigned):
    raise AssertionError("POLL_RESPONSE_FIXTURE_EXPORTS_INCOMPLETE")

for name, expected in EXPECTED_FNV1A64.items():
    value = getattr(module, name, None)
    if not isinstance(value, str):
        raise AssertionError(f"POLL_RESPONSE_FIXTURE_NOT_TEXT: {name}")
    actual = fnv1a64(value.encode("utf-8"))
    if actual != expected:
        raise AssertionError(f"POLL_RESPONSE_FIXTURE_BYTE_DRIFT: {name} {actual} != {expected}")

runner_lines = len(runner_source.splitlines())
if runner_lines > 330:
    raise AssertionError(f"POLL_RESPONSE_RUNNER_NOT_COMPACT: {runner_lines} lines")
print("POLL_RESPONSE_SHARED_RUNNER_PASS")
print(f"POLL_RESPONSE_FIXTURE_BOUNDARY_PASS 4/4; RUNNER_LINES={runner_lines}")


def verify_shared_runner_contract():
    """Exercise shared compile/run failure handling without launching child processes."""
    rejected = (True, False, 0, -1, float("inf"), float("nan"), "1", None)
    for value in rejected:
        try:
            shared_runner._validate_timeout("timeout", value)
        except ValueError:
            pass
        else:
            raise AssertionError("CPP_RUNNER_INVALID_TIMEOUT_ACCEPTED")

    for value in (0.001, 1, 2.5):
        shared_runner._validate_timeout("timeout", value)

    if shared_runner._diagnostic_tail(None) != "":
        raise AssertionError("CPP_RUNNER_NONE_DIAGNOSTIC_NOT_EMPTY")
    if shared_runner._diagnostic_tail("prefix" + "x" * 3500) != "x" * shared_runner.MAX_DIAGNOSTIC_TAIL_CHARS:
        raise AssertionError("CPP_RUNNER_TEXT_DIAGNOSTIC_NOT_BOUNDED")
    if shared_runner._diagnostic_tail(b"\xfftail") != "\ufffdtail":
        raise AssertionError("CPP_RUNNER_INVALID_UTF8_NOT_REPLACED")

    with patch.object(shared_runner.subprocess, "run") as process:
        try:
            shared_runner.run_cpp_fixture("int main() { return 0; }", prefix="phx-invalid-", stem="invalid", compile_timeout=0)
        except ValueError:
            pass
        else:
            raise AssertionError("CPP_RUNNER_ZERO_TIMEOUT_NOT_REJECTED")
        if process.called:
            raise AssertionError("CPP_RUNNER_SPAWNED_PROCESS_FOR_INVALID_TIMEOUT")

    failed_compile_dirs = []

    def failed_compile(command, **kwargs):
        source_path = Path(command[-3])
        failed_compile_dirs.append(source_path.parent)
        if not source_path.is_file():
            raise AssertionError("CPP_RUNNER_SOURCE_FILE_NOT_WRITTEN")
        return subprocess.CompletedProcess(command, 2, "", "compile-prefix" + "c" * 3500)

    with patch.object(shared_runner.subprocess, "run", side_effect=failed_compile) as process:
        try:
            shared_runner.run_cpp_fixture("int main() { return 0; }", prefix="phx-compile-fail-", stem="compile-fail")
        except RuntimeError as error:
            message = str(error)
        else:
            raise AssertionError("CPP_RUNNER_COMPILE_FAILURE_NOT_PROPAGATED")
        if process.call_count != 1:
            raise AssertionError("CPP_RUNNER_RAN_BINARY_AFTER_COMPILE_FAILURE")
    if "compile-prefix" in message or "c" * shared_runner.MAX_DIAGNOSTIC_TAIL_CHARS not in message:
        raise AssertionError("CPP_RUNNER_COMPILE_DIAGNOSTIC_NOT_BOUNDED")
    if failed_compile_dirs[0].exists():
        raise AssertionError("CPP_RUNNER_TEMP_DIR_LEAKED_AFTER_COMPILE_FAILURE")

    compile_timeout = subprocess.TimeoutExpired(["g++"], 1, output=b"o" * 3500, stderr=b"e" * 3500)
    with patch.object(shared_runner.subprocess, "run", side_effect=compile_timeout):
        try:
            shared_runner.run_cpp_fixture("int main() { return 0; }", prefix="phx-compile-timeout-", stem="compile-timeout")
        except RuntimeError as error:
            message = str(error)
        else:
            raise AssertionError("CPP_RUNNER_COMPILE_TIMEOUT_NOT_PROPAGATED")
    if "compile timed out" not in message or "o" * shared_runner.MAX_DIAGNOSTIC_TAIL_CHARS not in message or "e" * shared_runner.MAX_DIAGNOSTIC_TAIL_CHARS not in message:
        raise AssertionError("CPP_RUNNER_COMPILE_TIMEOUT_DIAGNOSTICS_MISSING")
    if "o" * (shared_runner.MAX_DIAGNOSTIC_TAIL_CHARS + 1) in message:
        raise AssertionError("CPP_RUNNER_COMPILE_TIMEOUT_DIAGNOSTIC_UNBOUNDED")

    runtime_timeout = subprocess.TimeoutExpired(["fixture"], 1, output=b"r" * 3500, stderr=b"s" * 3500)
    runtime_dirs = []

    def compile_then_timeout(command, **kwargs):
        if command[0] == "g++":
            runtime_dirs.append(Path(command[-3]).parent)
            return subprocess.CompletedProcess(command, 0, "", "")
        raise runtime_timeout

    with patch.object(shared_runner.subprocess, "run", side_effect=compile_then_timeout) as process:
        try:
            shared_runner.run_cpp_fixture("int main() { return 0; }", prefix="phx-run-timeout-", stem="run-timeout")
        except RuntimeError as error:
            message = str(error)
        else:
            raise AssertionError("CPP_RUNNER_EXECUTION_TIMEOUT_NOT_PROPAGATED")
        if process.call_count != 2:
            raise AssertionError("CPP_RUNNER_EXECUTION_TIMEOUT_CALL_COUNT")
    if "execution timed out" not in message or "r" * shared_runner.MAX_DIAGNOSTIC_TAIL_CHARS not in message or "s" * shared_runner.MAX_DIAGNOSTIC_TAIL_CHARS not in message:
        raise AssertionError("CPP_RUNNER_EXECUTION_TIMEOUT_DIAGNOSTICS_MISSING")
    if runtime_dirs[0].exists():
        raise AssertionError("CPP_RUNNER_TEMP_DIR_LEAKED_AFTER_EXECUTION_TIMEOUT")

    success_dirs = []

    def successful_run(command, **kwargs):
        if command[0] == "g++":
            source_path = Path(command[-3])
            success_dirs.append(source_path.parent)
            if source_path.name != "fixture.cpp" or not source_path.is_file():
                raise AssertionError("CPP_RUNNER_SUCCESS_SOURCE_PATH")
            if not all(flag in command for flag in ("-std=c++17", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter")):
                raise AssertionError("CPP_RUNNER_COMPILE_FLAGS_NOT_PRESERVED")
            if kwargs.get("timeout") != shared_runner.DEFAULT_COMPILE_TIMEOUT_SECONDS:
                raise AssertionError("CPP_RUNNER_COMPILE_TIMEOUT_DEFAULT_CHANGED")
            return subprocess.CompletedProcess(command, 0, "", "")
        if not success_dirs or not success_dirs[0].exists():
            raise AssertionError("CPP_RUNNER_TEMP_DIR_REMOVED_BEFORE_EXECUTION")
        if Path(command[0]).name != "fixture":
            raise AssertionError("CPP_RUNNER_BINARY_NAME_CHANGED")
        if kwargs.get("timeout") != shared_runner.DEFAULT_RUN_TIMEOUT_SECONDS:
            raise AssertionError("CPP_RUNNER_RUN_TIMEOUT_DEFAULT_CHANGED")
        return subprocess.CompletedProcess(command, 0, "fixture-pass", "")

    with patch.object(shared_runner.subprocess, "run", side_effect=successful_run) as process:
        result = shared_runner.run_cpp_fixture(
            "int main() { return 0; }",
            prefix="phx-runner-success-",
            stem="fixture",
            extra_flags=("-Wno-unused-parameter",),
        )
        if process.call_count != 2:
            raise AssertionError("CPP_RUNNER_SUCCESS_CALL_COUNT")
    if result.returncode != 0 or result.stdout != "fixture-pass":
        raise AssertionError("CPP_RUNNER_SUCCESS_RESULT_CHANGED")
    if success_dirs[0].exists():
        raise AssertionError("CPP_RUNNER_TEMP_DIR_NOT_CLEANED_AFTER_SUCCESS")

    print("CPP_FIXTURE_RUNNER_CONTRACT_PASS 6/6")


verify_shared_runner_contract()
