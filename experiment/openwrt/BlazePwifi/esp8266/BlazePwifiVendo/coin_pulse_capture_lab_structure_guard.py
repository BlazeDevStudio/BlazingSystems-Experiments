#!/usr/bin/env python3
"""Enforce small, ordered, byte-preserving modules for the coin-pulse C++ fixture.

This is a source-ownership guard. The executable C++ scenario and mutation
contracts remain in the existing runner and board sketches.
"""
from __future__ import annotations

import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
RUNNER = HERE / "coin_pulse_capture_lab.py"
FIXTURES = HERE / "coin_pulse_capture_lab_fixtures.py"
CONTRACTS = HERE / "coin_pulse_capture_lab_contracts.py"
ISR_SELECTOR = HERE / "coin_pulse_capture_lab_isr.py"
SECTION_SPECS = (
    ("coin_pulse_capture_lab_fixture_runtime", "CPP_RUNTIME", "#include <cstdint>"),
    ("coin_pulse_capture_lab_fixture_poll", "CPP_POLL", "static bool runDrainCapture"),
    ("coin_pulse_capture_lab_fixture_gates", "CPP_GATES", "static bool runDeniedGates"),
    ("coin_pulse_capture_lab_fixture_faults", "CPP_FAULTS", "static bool runPulseLimitBoundary"),
    ("coin_pulse_capture_lab_fixture_edges", "CPP_EDGES", "static bool runMissedPulseAfterBlockingPost"),
    ("coin_pulse_capture_lab_fixture_entry", "CPP_ENTRY", "int main()"),
)


def fail(message: str) -> None:
    raise SystemExit(f"COIN_PULSE_CAPTURE_MODULE_BOUNDARY_FAIL: {message}")


def parse(path: Path) -> tuple[str, ast.Module]:
    if not path.is_file():
        fail(f"required module is missing: {path.name}")
    source = path.read_text(encoding="utf-8")
    try:
        return source, ast.parse(source, filename=str(path))
    except SyntaxError as error:
        fail(f"{path.name} has invalid Python syntax: {error}")
        raise AssertionError("unreachable")


def imported_from(tree: ast.Module, module: str) -> set[str]:
    return {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == module
        for alias in node.names
    }


def assigned_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
            targets = [node.target]
        for target in targets:
            names.update(item.id for item in ast.walk(target) if isinstance(item, ast.Name))
    return names


def defined_functions(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def literal_assignment(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    fail(f"{name} must be a module-level literal assignment")
    raise AssertionError("unreachable")


def tuple_first_strings(tree: ast.Module, name: str) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            if not isinstance(node.value, ast.Tuple):
                fail(f"{name} must be a tuple")
            values = []
            for item in node.value.elts:
                if (
                    not isinstance(item, ast.Tuple)
                    or not item.elts
                    or not isinstance(item.elts[0], ast.Constant)
                    or not isinstance(item.elts[0].value, str)
                ):
                    fail(f"{name} entries must begin with a literal identifier")
                values.append(item.elts[0].value)
            return values
    fail(f"{name} must be a module-level tuple assignment")
    raise AssertionError("unreachable")


runner_source, runner_tree = parse(RUNNER)
fixture_source, fixture_tree = parse(FIXTURES)
contract_source, contract_tree = parse(CONTRACTS)

isr_selector_source, isr_selector_tree = parse(ISR_SELECTOR)
selector_imports = {
    "extract_board_coin_edge_isr",
    "mutate_active_isr_attribute",
    "verify_board_specific_isr_selection",
    "verify_inactive_isr_source_decoy_tolerance",
    "verify_runtime_interrupt_wiring",
}
if imported_from(runner_tree, "coin_pulse_capture_lab_isr") != selector_imports:
    fail("runner must import only the public board-ISR selector contracts")
if imported_from(isr_selector_tree, "firmware_lab_source") != {
    "extract_function", "extract_functions", "mask_active_cpp_code", "mask_non_code"
}:
    fail("ISR selector must use the shared firmware source parser")
selector_functions = {
    "_condition_board_gate",
    "_active_board_isr_definition",
    "extract_board_coin_edge_isr",
    "mutate_active_isr_attribute",
    "verify_board_specific_isr_selection",
    "verify_inactive_isr_source_decoy_tolerance",
    "verify_runtime_interrupt_wiring",
}
if not selector_functions.issubset(defined_functions(isr_selector_tree)):
    fail("ISR selector module does not own all six board-selection helpers")
if selector_functions & defined_functions(runner_tree):
    fail("runner still owns board-selection helpers")

if imported_from(runner_tree, "coin_pulse_capture_lab_fixtures") != {"CPP"}:
    fail("runner must import only CPP from the fixture assembler")
if imported_from(runner_tree, "coin_pulse_capture_lab_contracts") != {
    "FUNCTION_SPECS", "FUNCTION_INDEX_BY_NAME", "MUTATIONS"
}:
    fail("runner must import the source contract and mutation matrix")
if {"CPP", "FUNCTION_SPECS", "FUNCTION_INDEX_BY_NAME", "MUTATIONS"} & assigned_names(runner_tree):
    fail("runner still owns an inline fixture or contract table")

if assigned_names(fixture_tree) != {"CPP"}:
    fail("fixture assembler must own only the composed CPP value")
expected_imports = set()
sections = []
for module, constant, first_marker in SECTION_SPECS:
    section_source, section_tree = parse(HERE / f"{module}.py")
    if assigned_names(section_tree) != {constant}:
        fail(f"{module}.py must own only {constant}")
    value = literal_assignment(section_tree, constant)
    if not isinstance(value, str) or not value.startswith(first_marker):
        fail(f"{module}.py lost its ordered C++ section start marker")
    if len(section_source.splitlines()) > 150:
        fail(f"{module}.py exceeds the 150-line reviewability ceiling")
    if imported_from(fixture_tree, module) != {constant}:
        fail(f"fixture assembler must import only {constant} from {module}")
    expected_imports.add(constant)
    sections.append(value)

expected_assembly = """CPP = "".join((
    CPP_RUNTIME,
    CPP_POLL,
    CPP_GATES,
    CPP_FAULTS,
    CPP_EDGES,
    CPP_ENTRY,
))"""
if expected_assembly not in fixture_source:
    fail("fixture assembler changed the canonical section order")
if imported_from(fixture_tree, "coin_pulse_capture_lab_fixture_runtime") | imported_from(
    fixture_tree, "coin_pulse_capture_lab_fixture_poll"
) | imported_from(fixture_tree, "coin_pulse_capture_lab_fixture_gates") | imported_from(
    fixture_tree, "coin_pulse_capture_lab_fixture_faults"
) | imported_from(fixture_tree, "coin_pulse_capture_lab_fixture_edges") | imported_from(
    fixture_tree, "coin_pulse_capture_lab_fixture_entry"
) != expected_imports:
    fail("fixture assembler imports do not match the six declared sections")

cpp = "".join(sections)
if len(cpp) != 21445 or len(cpp.splitlines()) != 479:
    fail(f"assembled C++ fixture size drifted: chars={len(cpp)} lines={len(cpp.splitlines())}")
if not cpp.startswith("#include <cstdint>\n") or not cpp.endswith("return 0;\n}"):
    fail("assembled C++ fixture lost its original outer boundaries")
if cpp.count("@@FUNCTIONS@@") != 1:
    fail("assembled C++ fixture must retain exactly one production-helper insertion point")
if "COIN_PULSE_CAPTURE_PASS" not in cpp or "/18 top-level scenarios" not in cpp:
    fail("assembled C++ fixture lost the 18-scenario pass marker")
if "runIsrSequenceWraparound" not in cpp:
    fail("assembled C++ fixture lost the exact ISR rollover scenario")
for scenario in (
    "runDrainCapture", "runNoPulseControl", "runSaveFailureCase", "runSaveFailure",
    "runDeniedGates", "runInvalidPinConfig", "runPulseLimitBoundary",
    "runUnrepresentablePulseFault", "runUnrepresentablePulseCases",
    "runLatePulseAfterReady", "runMissedPulseAfterBlockingPost",
    "runMissedPulseDuringBlockingWork", "runMultipleUnobservedEdges",
    "runSingleObservedEdge", "runIngressTransitionCases", "runIsrSequenceWraparound",
):
    if cpp.count(f"static bool {scenario}(") != 1:
        fail(f"assembled C++ fixture must contain exactly one {scenario} definition")
if cpp.count("int main()") != 1:
    fail("assembled C++ fixture must contain exactly one main entry point")

for marker in (
    "SIMULATED_ONLY=1", "PHYSICAL_COIN_PULSE_ACCEPTANCE=0",
    "PHYSICAL_RELAY_ACCEPTANCE=0", "PHYSICAL_POWER_CUT_ACCEPTANCE=0",
):
    if marker not in runner_source:
        fail(f"runner lost evidence marker: {marker}")

specs = literal_assignment(contract_tree, "FUNCTION_SPECS")
mutation_names = tuple_first_strings(contract_tree, "MUTATIONS")
if not isinstance(specs, tuple) or len(specs) != 11:
    fail("FUNCTION_SPECS must retain all 11 production helper anchors")
if len({item[0] for item in specs}) != len(specs):
    fail("FUNCTION_SPECS contains duplicate helper names")
if len({item[1] for item in specs}) != len(specs):
    fail("FUNCTION_SPECS contains duplicate signatures")
if len(mutation_names) != 17:
    fail("MUTATIONS must retain all 17 fail-open mutation cases")
if "missing-isr-sequence-increment" not in mutation_names:
    fail("MUTATIONS must reject removal of the exact coin ISR sequence increment")
if len(set(mutation_names)) != len(mutation_names):
    fail("MUTATIONS contains duplicate identifiers")
if "FUNCTION_INDEX_BY_NAME" not in assigned_names(contract_tree):
    fail("contract module does not own the helper index")
if "len(FUNCTION_INDEX_BY_NAME) != len(FUNCTION_SPECS)" not in contract_source:
    fail("contract module lost duplicate-name validation")
if "len({signature for _, signature in FUNCTION_SPECS})" not in contract_source:
    fail("contract module lost duplicate-signature validation")
if 'CPP.replace("@@FUNCTIONS@@"' not in runner_source:
    fail("runner no longer composes the exact-source fixture")
if "for name, helper_name, old, new, expected in MUTATIONS" not in runner_source:
    fail("runner no longer executes the complete mutation matrix")


def workflow_event_block(source: str, event: str, next_event: str) -> str:
    start = source.find(f"  {event}:")
    end = source.find(f"\n  {next_event}:", start)
    if start < 0 or end < 0:
        fail(f"workflow is missing the {event} path-filter block")
    return source[start:end]


for workflow_name in (
    "phx-hardware-quarantine-byte-readback.yml",
    "phx-hardware-relay-output-polarity.yml",
):
    workflow_source = (REPO_ROOT / ".github" / "workflows" / workflow_name).read_text(encoding="utf-8")
    for event, next_event in (("push", "pull_request"), ("pull_request", "workflow_dispatch")):
        event_source = workflow_event_block(workflow_source, event, next_event)
        for module, _, _ in SECTION_SPECS:
            module_path = (
                "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/"
                f"{module}.py"
            )
            if f'      - "{module_path}"' not in event_source:
                fail(f"{workflow_name} {event} does not trigger for {module}.py")
        if f'      - "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/coin_pulse_capture_lab_isr.py"' not in event_source:
            fail(f"{workflow_name} {event} does not trigger for coin_pulse_capture_lab_isr.py")

print("COIN_PULSE_CAPTURE_LAB_MODULE_BOUNDARIES_PASS")
print(f"FIXTURE_SECTIONS={len(SECTION_SPECS)} FUNCTION_SPECS={len(specs)} MUTATIONS={len(mutation_names)} ISR_SELECTOR_HELPERS={len(selector_functions)}")
