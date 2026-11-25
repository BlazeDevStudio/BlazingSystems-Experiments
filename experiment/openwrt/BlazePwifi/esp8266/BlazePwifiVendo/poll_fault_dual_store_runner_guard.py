#!/usr/bin/env python3
"""Require the dual-store lab to use the shared bounded C++ fixture runner.

Python subprocess/tempfile remain valid for the external-CWD and root-sentinel
self-tests; only C++ compilation/execution must be centralized.
"""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE / "poll_fault_dual_store_lab.py"
tree = ast.parse(LAB.read_text(encoding="utf-8"))

runner_imports = {
    alias.name
    for node in tree.body
    if isinstance(node, ast.ImportFrom)
    and node.module == "cpp_fixture_runner"
    for alias in node.names
}
if runner_imports != {"run_cpp_fixture"}:
    raise AssertionError("POLL_FAULT_SHARED_RUNNER_IMPORT_MISSING")

functions = {
    node.name: node
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

helper = functions.get("_compile_and_run")
if helper is None:
    raise AssertionError("POLL_FAULT_SHARED_RUNNER_HELPER_MISSING")

helper_calls = [
    node for node in ast.walk(helper)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "run_cpp_fixture"
]
if len(helper_calls) != 1:
    raise AssertionError("POLL_FAULT_SHARED_RUNNER_CALL_MISSING")

timeout_values = {
    keyword.arg: keyword.value.value
    for keyword in helper_calls[0].keywords
    if keyword.arg in {"compile_timeout", "run_timeout"}
    and isinstance(keyword.value, ast.Constant)
}
if timeout_values != {"compile_timeout": 30, "run_timeout": 10}:
    raise AssertionError("POLL_FAULT_SHARED_RUNNER_BOUNDS_CHANGED")

required_callers = (
    "run",
    "run_esp32_missing_commit_mutation",
    "run_esp32_precommit_persistence_mutation",
    "run_first_fault_snapshot_overwrite_mutation",
)
for name in required_callers:
    function = functions.get(name)
    if function is None:
        raise AssertionError(f"POLL_FAULT_EXPECTED_CALLER_MISSING: {name}")
    calls = [
        node for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_compile_and_run"
    ]
    if len(calls) != 1:
        raise AssertionError(f"POLL_FAULT_CALLER_NOT_USING_SHARED_RUNNER: {name}")

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue
    func = node.func
    if not (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "subprocess"
        and func.attr == "run"
        and node.args
    ):
        continue
    command = node.args[0]
    if (
        isinstance(command, ast.List)
        and command.elts
        and isinstance(command.elts[0], ast.Constant)
        and command.elts[0].value == "g++"
    ):
        raise AssertionError("POLL_FAULT_DIRECT_CPP_COMPILER_CALL_REMAINS")


SOURCE_CONTRACTS = HERE / "poll_fault_dual_store_lab_source_contracts.py"
if not SOURCE_CONTRACTS.is_file():
    raise AssertionError("POLL_FAULT_SOURCE_CONTRACT_MODULE_MISSING")

source_tree = ast.parse(SOURCE_CONTRACTS.read_text(encoding="utf-8"))
source_functions = {
    node.name: node
    for node in source_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
expected_source_tests = (
    "test_external_cwd_invocation",
    "test_repo_root_requires_both_board_sentinels",
    "test_unknown_board_identifier_fails_closed",
    "test_extractors",
    "test_constants_extract_only_active_declarations",
)
missing_source_tests = [
    name for name in expected_source_tests if name not in source_functions
]
if missing_source_tests:
    raise AssertionError(
        "POLL_FAULT_SOURCE_CONTRACT_FUNCTIONS_MISSING: "
        + ",".join(missing_source_tests)
    )
if any(name in functions for name in expected_source_tests):
    raise AssertionError("POLL_FAULT_SOURCE_CONTRACTS_STILL_IN_ORCHESTRATOR")

runner_imports = {
    alias.name
    for node in tree.body
    if isinstance(node, ast.ImportFrom)
    and node.module == "poll_fault_dual_store_lab_source_contracts"
    for alias in node.names
}
if runner_imports != {"run_source_contracts"}:
    raise AssertionError("POLL_FAULT_SOURCE_CONTRACT_IMPORT_MISSING")

source_runner = source_functions.get("run_source_contracts")
if source_runner is None:
    raise AssertionError("POLL_FAULT_SOURCE_CONTRACT_ORCHESTRATOR_MISSING")
source_calls = [
    node.func.id
    for node in ast.walk(source_runner)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
]
for name in expected_source_tests:
    if source_calls.count(name) != 1:
        raise AssertionError(
            f"POLL_FAULT_SOURCE_CONTRACT_CALL_COUNT: {name}={source_calls.count(name)}"
        )

main_calls = [
    node for node in ast.walk(tree)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "run_source_contracts"
]
if len(main_calls) != 1:
    raise AssertionError("POLL_FAULT_SOURCE_CONTRACT_ORCHESTRATOR_CALL_MISSING")

for node in tree.body:
    if isinstance(node, ast.Import):
        imported = {alias.name.split(".")[0] for alias in node.names}
    elif isinstance(node, ast.ImportFrom):
        imported = {(node.module or "").split(".")[0]}
    else:
        continue
    if imported.intersection({"subprocess", "tempfile"}):
        raise AssertionError("POLL_FAULT_SOURCE_TEST_PROCESS_OWNERSHIP_NOT_EXTRACTED")

if any(
    isinstance(node, ast.ImportFrom)
    and node.module == "poll_fault_dual_store_lab"
    for node in source_tree.body
):
    raise AssertionError("POLL_FAULT_SOURCE_CONTRACT_CIRCULAR_IMPORT")

print("POLL_FAULT_SOURCE_CONTRACT_BOUNDARY_PASS")

print("POLL_FAULT_SHARED_RUNNER_STRUCTURE_PASS")
