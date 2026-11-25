"""Keep strict poll-JSON regression logic split by protocol responsibility.

This structural guard runs before the source-extracted parser lab. It prevents
the orchestration module from becoming a second monolithic test contract.
"""
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
}

orchestrator = ORCHESTRATOR.read_text(encoding="utf-8")
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
