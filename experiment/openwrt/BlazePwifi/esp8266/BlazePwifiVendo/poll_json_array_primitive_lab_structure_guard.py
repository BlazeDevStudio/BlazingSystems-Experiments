"""Keep strict poll-JSON regression logic split by protocol responsibility.

This structural guard runs before the source-extracted parser lab. It prevents
the orchestration module from becoming a second monolithic test contract.
"""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORCHESTRATOR = HERE / "poll_json_array_primitive_lab.py"

MODULES = {
    "root-envelope": (
        "poll_json_array_primitive_lab_root_contracts.py",
        "verify_root_envelope_contracts",
        ("duplicate_guard", "final_guard"),
    ),
    "composite": (
        "poll_json_array_primitive_lab_composite_contracts.py",
        "verify_composite_contracts",
        ("depth_guard", "separator"),
    ),
    "primitive": (
        "poll_json_array_primitive_lab_primitive_contracts.py",
        "verify_primitive_contracts",
        ("leading_zero_guard", "fraction_guard", "exponent_guard"),
    ),
    "utf8-string": (
        "poll_json_array_primitive_lab_utf8_contracts.py",
        "verify_utf8_contracts",
        ("minimumSecond", "maximumSecond", "bypass-invalid-utf8-deny"),
    ),
}

orchestrator = ORCHESTRATOR.read_text(encoding="utf-8")
fixture_path = HERE / "poll_json_array_primitive_lab_fixtures.py"
try:
    fixture_tree = ast.parse(
        fixture_path.read_text(encoding="utf-8"),
        filename=str(fixture_path),
    )
except SyntaxError as error:
    raise AssertionError(f"fixture module has invalid Python syntax: {error}") from error

parser_functions = None
for node in fixture_tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "PARSER_FUNCTIONS"
        for target in node.targets
    ):
        parser_functions = ast.literal_eval(node.value)
        break
if (
    not isinstance(parser_functions, tuple)
    or "pollJsonSkipUtf8Continuation" not in parser_functions
):
    raise AssertionError("source extractor must include the UTF-8 validator helper")
response_lab_source = (
    HERE / "poll_response_failclosed_lab.py"
).read_text(encoding="utf-8")
if (
    '"pollJsonSkipUtf8Continuation", "pollJsonSkipString"' not in response_lab_source
):
    raise AssertionError(
        "poll-response fixture must extract the UTF-8 validator before string parsing"
    )
for name, (filename, function, anchors) in MODULES.items():
    path = HERE / filename
    if not path.is_file():
        raise AssertionError(f"{name}: missing contract module {filename}")
    module = path.read_text(encoding="utf-8")
    if f"def {function}(" not in module:
        raise AssertionError(f"{name}: missing {function} entry point")
    if function not in orchestrator:
        raise AssertionError(f"{name}: orchestrator does not call {function}")
    for anchor in anchors:
        if anchor not in module:
            raise AssertionError(f"{name}: expected contract anchor {anchor!r} missing")

for anchor in ("duplicate_guard", "depth_guard", "leading_zero_guard", "control_guard"):
    if anchor in orchestrator:
        raise AssertionError(f"orchestrator still owns inline mutation logic: {anchor}")

print("POLL_JSON_LAB_MODULE_BOUNDARY_PASS root-envelope=1 composite=1 primitive=1")
