#!/usr/bin/env python3
"""Structural and byte-preservation guard for the poll-response lab split.

The embedded C++ programs are fixture data, not Python runner logic. Keep the
runner small and the four fixture payloads byte-identical during extraction.
"""
import ast
import importlib.util
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


# The current CGI-envelope lab is another consumer of the shared runner.
# Keep it free of local subprocess/tempfile lifecycle code as well.
CURRENT_CGI_LAB_PATH = HERE / "poll_current_cgi_envelope_deny_lab.py"
if not CURRENT_CGI_LAB_PATH.is_file():
    raise AssertionError("CURRENT_CGI_LAB_MISSING")
current_cgi_tree = ast.parse(
    CURRENT_CGI_LAB_PATH.read_text(encoding="utf-8")
)
current_cgi_runner_imports = {
    alias.name
    for node in current_cgi_tree.body
    if isinstance(node, ast.ImportFrom)
    and node.module == "cpp_fixture_runner"
    for alias in node.names
}
if current_cgi_runner_imports != {"run_cpp_fixture"}:
    raise AssertionError("CURRENT_CGI_LAB_SHARED_RUNNER_IMPORT_MISSING")

current_cgi_direct_imports = {
    alias.name.split(".")[0]
    for node in current_cgi_tree.body
    if isinstance(node, ast.Import)
    for alias in node.names
}
if {"subprocess", "tempfile"} & current_cgi_direct_imports:
    raise AssertionError("CURRENT_CGI_LAB_LOCAL_PROCESS_RUNNER_REMAINS")

current_cgi_direct_calls = [
    node for node in ast.walk(current_cgi_tree)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Attribute)
    and isinstance(node.func.value, ast.Name)
    and node.func.value.id in {"subprocess", "tempfile"}
]
if current_cgi_direct_calls:
    raise AssertionError("CURRENT_CGI_LAB_LOCAL_PROCESS_CALL_REMAINS")

if not any(
    isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "run_cpp_fixture"
    for node in ast.walk(current_cgi_tree)
):
    raise AssertionError("CURRENT_CGI_LAB_SHARED_RUNNER_CALL_MISSING")
print("CURRENT_CGI_SHARED_RUNNER_GUARD_PASS")


# The bounded HTTP-response lab must use the same bounded process runner.
BOUNDED_HTTP_LAB_PATH = HERE / "bounded_http_response_lab.py"
if not BOUNDED_HTTP_LAB_PATH.is_file():
    raise AssertionError("BOUNDED_HTTP_LAB_MISSING")
bounded_http_tree = ast.parse(
    BOUNDED_HTTP_LAB_PATH.read_text(encoding="utf-8")
)
bounded_http_runner_imports = {
    alias.name
    for node in bounded_http_tree.body
    if isinstance(node, ast.ImportFrom)
    and node.module == "cpp_fixture_runner"
    for alias in node.names
}
if bounded_http_runner_imports != {"run_cpp_fixture"}:
    raise AssertionError("BOUNDED_HTTP_LAB_SHARED_RUNNER_IMPORT_MISSING")

bounded_http_direct_imports = {
    alias.name.split(".")[0]
    for node in bounded_http_tree.body
    if isinstance(node, ast.Import)
    for alias in node.names
}
if {"subprocess", "tempfile"} & bounded_http_direct_imports:
    raise AssertionError("BOUNDED_HTTP_LAB_LOCAL_PROCESS_RUNNER_REMAINS")

bounded_http_direct_calls = [
    node for node in ast.walk(bounded_http_tree)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Attribute)
    and isinstance(node.func.value, ast.Name)
    and node.func.value.id in {"subprocess", "tempfile"}
]
if bounded_http_direct_calls:
    raise AssertionError("BOUNDED_HTTP_LAB_LOCAL_PROCESS_CALL_REMAINS")

if not any(
    isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "run_cpp_fixture"
    for node in ast.walk(bounded_http_tree)
):
    raise AssertionError("BOUNDED_HTTP_LAB_SHARED_RUNNER_CALL_MISSING")
print("BOUNDED_HTTP_SHARED_RUNNER_GUARD_PASS")

runner_lines = len(runner_source.splitlines())
if runner_lines > 330:
    raise AssertionError(f"POLL_RESPONSE_RUNNER_NOT_COMPACT: {runner_lines} lines")
print("POLL_RESPONSE_SHARED_RUNNER_PASS")
print(f"POLL_RESPONSE_FIXTURE_BOUNDARY_PASS 4/4; RUNNER_LINES={runner_lines}")
