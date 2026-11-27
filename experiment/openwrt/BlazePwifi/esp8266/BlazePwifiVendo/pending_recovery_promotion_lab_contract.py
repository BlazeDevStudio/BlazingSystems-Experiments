#!/usr/bin/env python3
"""Source-contract assertions and unsafe-mutation probes for pending recovery."""
import re

from firmware_source_extract import extract_braced, extract_function, mask_non_code


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_if_block(function: str, pattern: str, label: str) -> tuple[str, int]:
    masked = mask_non_code(function)
    match = re.search(pattern, function)
    require(match is not None, f"missing {label} guard")
    opening = masked.find("{", match.end())
    require(opening >= 0, f"{label} guard has no body")
    block = extract_braced(function, opening)
    return block, opening + len(block)


def require_deny_block(block: str, label: str) -> None:
    masked = mask_non_code(block)
    for token in ("fsReady=false;", "pendingReady=true;", "return false;"):
        require(token in masked, f"{label} must set {token}")


def assert_source_contract(source: str) -> None:
    raw = extract_function(source, "bool loadPending()")
    masked = mask_non_code(raw)

    require('LittleFS.remove("/pending.dat")' not in raw,
            "recovery must not delete an existing canonical journal")
    require("pendingSequenceState=r;" in masked,
            "valid recovered state must be published after promotion succeeds")
    require('strcmp(chosen,"/pending.dat")!=0' in raw,
            "fallback selection must be explicit")
    require('LittleFS.exists("/pending.dat")' in raw,
            "canonical/fallback ambiguity must be detected")
    require('LittleFS.rename(chosen,"/pending.dat")' in raw,
            "fallback promotion must target the canonical journal")
    require("candidateCount > 1" in masked,
            "coexisting journal candidates must fail closed before candidate selection")
    multiple_candidates, multiple_end = extract_if_block(
        raw, r"if\s*\(\s*candidateCount\s*>\s*1\s*\)", "multiple-journal-candidates"
    )
    require_deny_block(multiple_candidates, "multiple-journal-candidates")
    first_candidate_read = raw.find('readPendingFile("/pending.dat"')
    require(first_candidate_read >= 0 and multiple_end < first_candidate_read,
            "multiple-candidate denial must precede every journal read/promotion")

    no_candidate, _ = extract_if_block(
        raw, r"if\s*\(\s*!\s*chosen\s*\)", "no-valid-candidate"
    )
    no_candidate_masked = mask_non_code(no_candidate)
    require(re.search(r"if\s*\(\s*any\s*\)", no_candidate_masked) is not None,
            "existing invalid journal files must not be treated as an empty journal")
    any_block, _ = extract_if_block(
        no_candidate, r"if\s*\(\s*any\s*\)", "invalid-candidate"
    )
    require_deny_block(any_block, "invalid-candidate")

    empty_write, _ = extract_if_block(
        no_candidate,
        r"if\s*\(\s*!\s*persistPendingSequence\s*\(\s*pendingSequenceState\s*\)\s*\)",
        "initial-empty-journal-write",
    )
    require_deny_block(empty_write, "initial-empty-journal-write")

    promote, promote_end = extract_if_block(
        raw,
        r"if\s*\(\s*strcmp\s*\(\s*chosen",
        "fallback-promotion",
    )
    conflict, _ = extract_if_block(
        promote,
        r"if\s*\(\s*LittleFS\.exists\s*\(",
        "canonical-fallback-conflict",
    )
    require_deny_block(conflict, "canonical-fallback-conflict")

    rename_failure, _ = extract_if_block(
        promote,
        r"if\s*\(\s*!\s*LittleFS\.rename\s*\(",
        "fallback-rename-result",
    )
    require_deny_block(rename_failure, "fallback-rename-result")

    state_position = masked.find("pendingSequenceState=r;")
    require(state_position > promote_end,
            "RAM journal state must not be published before fallback promotion succeeds")

    legacy_failure, _ = extract_if_block(
        raw,
        r"if\s*\(\s*legacy\s*&&\s*!\s*persistPendingSequence\s*\(\s*r\s*\)\s*\)",
        "legacy-journal-migration",
    )
    require_deny_block(legacy_failure, "legacy-journal-migration")


def mutate_load(source: str, old: str, new: str) -> str:
    load = extract_function(source, "bool loadPending()")
    require(old in load, f"missing mutation anchor in loadPending: {old}")
    changed = load.replace(old, new, 1)
    start = source.find(load)
    require(start >= 0, "could not locate loadPending source span")
    return source[:start] + changed + source[start + len(load):]


def expect_rejected(label: str, mutated: str) -> None:
    try:
        assert_source_contract(mutated)
    except AssertionError:
        print(f"PENDING_RECOVERY_MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe pending-recovery mutation accepted: {label}")
