#!/usr/bin/env python3
"""Keep the 700-line coin-pulse lab split into readable fixture, contract and runner modules.

This guard checks source ownership boundaries only; the executable behavior tests
remain in coin_pulse_capture_lab.py and the board-specific firmware sketches.
"""
from __future__ import annotations

import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "coin_pulse_capture_lab.py"
FIXTURES = HERE / "coin_pulse_capture_lab_fixtures.py"
CONTRACTS = HERE / "coin_pulse_capture_lab_contracts.py"


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

if imported_from(runner_tree, "coin_pulse_capture_lab_fixtures") != {"CPP"}:
    fail("runner must import only CPP from the fixture module")
if imported_from(runner_tree, "coin_pulse_capture_lab_contracts") != {
    "FUNCTION_SPECS", "FUNCTION_INDEX_BY_NAME", "MUTATIONS"
}:
    fail("runner must import the source contract and mutation matrix")
if {"CPP", "FUNCTION_SPECS", "FUNCTION_INDEX_BY_NAME", "MUTATIONS"} & assigned_names(runner_tree):
    fail("runner still owns an inline fixture or contract table")

fixture_names = assigned_names(fixture_tree)
if "CPP" not in fixture_names:
    fail("fixture module does not own CPP")
cpp = literal_assignment(fixture_tree, "CPP")
if not isinstance(cpp, str) or "@@FUNCTIONS@@" not in cpp:
    fail("CPP fixture lost its exact-source insertion point")
for marker in ("COIN_PULSE_CAPTURE_PASS", "SIMULATED_ONLY=1",
               "PHYSICAL_COIN_PULSE_ACCEPTANCE=0",
               "PHYSICAL_RELAY_ACCEPTANCE=0",
               "PHYSICAL_POWER_CUT_ACCEPTANCE=0"):
    if marker not in cpp:
        fail(f"CPP fixture lost evidence marker: {marker}")

specs = literal_assignment(contract_tree, "FUNCTION_SPECS")
mutation_names = tuple_first_strings(contract_tree, "MUTATIONS")
if not isinstance(specs, tuple) or len(specs) != 11:
    fail("FUNCTION_SPECS must retain all 11 production helper anchors")
if len({item[0] for item in specs}) != len(specs):
    fail("FUNCTION_SPECS contains duplicate helper names")
if len({item[1] for item in specs}) != len(specs):
    fail("FUNCTION_SPECS contains duplicate signatures")
if len(mutation_names) != 16:
    fail("MUTATIONS must retain all 16 fail-open mutation cases")
if len(set(mutation_names)) != len(mutation_names):
    fail("MUTATIONS contains duplicate identifiers")
if "FUNCTION_INDEX_BY_NAME" not in assigned_names(contract_tree):
    fail("contract module does not own the helper index")
if "len(FUNCTION_INDEX_BY_NAME) != len(FUNCTION_SPECS)" not in contract_source:
    fail("contract module lost duplicate-name validation")
if "len({signature for _, signature in FUNCTION_SPECS})" not in contract_source:
    fail("contract module lost duplicate-signature validation")
if "CPP.replace(\"@@FUNCTIONS@@\"" not in runner_source:
    fail("runner no longer composes the exact-source fixture")
if "for name, helper_name, old, new, expected in MUTATIONS" not in runner_source:
    fail("runner no longer executes the complete mutation matrix")

print("COIN_PULSE_CAPTURE_LAB_MODULE_BOUNDARIES_PASS")
print(f"FUNCTION_SPECS={len(specs)} MUTATIONS={len(mutations)}")
