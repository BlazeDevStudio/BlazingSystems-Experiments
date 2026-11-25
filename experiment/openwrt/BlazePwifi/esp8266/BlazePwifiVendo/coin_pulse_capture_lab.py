#!/usr/bin/env python3
"""PHX-HARDWARE exact-source coin pulse, ISR counter rollover, bounded-batch overflow, target-drift, post-finalization and ISR-unobserved edge safety lab.

Compiles production coinLineIdle(), canStartPoll(), applyOutputs(),
coinLineQuietAfterInhibit(), beginPollWindow(), latchPollPulseFault(),
quarantineCoinIngressTransition(), and sampleCoinPulseEdge() from both ESP sketches.
It also checks that pin reconfiguration does not silently advance the ISR baseline.
Only the two persistence backends
are fault-injected. The failed-save path checks all four dual-store outcomes,
the unresolved pulse identity, and logical relay/LED OFF before either store is
called. The companion dual-store lab separately extracts the real persistence
helpers. Host C++ uses fake GPIO/time/storage only; no physical acceptance is
claimed.
"""
from pathlib import Path
import re
from cpp_fixture_runner import run_cpp_fixture

from firmware_lab_source import (
    extract_function,
    extract_functions,
    mask_active_cpp_code,
    mask_non_code,
)
from coin_pulse_capture_lab_fixtures import CPP
from coin_pulse_capture_lab_contracts import (
    FUNCTION_SPECS,
    FUNCTION_INDEX_BY_NAME,
    MUTATIONS,
)

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
)



def _condition_board_gate(source, board):
    if board not in ("ESP8266", "ESP32"):
        raise RuntimeError(f"unsupported board for conditional coinEdgeISR selection: {board}")

    # Only rewrite the one exact board gate used by both current sketches.
    # Padding keeps all source offsets stable for the active-code mask.
    masked = mask_non_code(source)
    directive = re.compile(
        r"(?m)^[ \t]*#[ \t]*if[ \t]+defined[ \t]*\([ \t]*ESP8266[ \t]*\)[ \t]*(?=\r?$)"
    )
    matches = list(directive.finditer(masked))
    if len(matches) != 1:
        raise RuntimeError(
            f"{board} expected exactly one literal #if defined(ESP8266) board gate, "
            f"found {len(matches)}"
        )

    match = matches[0]
    replacement = "#if 1" if board == "ESP8266" else "#if 0"
    width = match.end() - match.start()
    if len(replacement) > width:
        raise RuntimeError(f"{board} board gate is too narrow for offset-preserving selection")
    return source[:match.start()] + replacement.ljust(width) + source[match.end():]


def _active_board_isr_definition(source, board):
    definitions = extract_functions(source, "coinEdgeISR")
    if len(definitions) < 2:
        raise RuntimeError(
            f"{board} expected at least two conditional coinEdgeISR definitions, found {len(definitions)}"
        )

    # First select the definition compiled for this board. Attributes on
    # inactive #if/#else definitions do not affect the generated image and
    # must not make an otherwise valid active ISR fail this contract.
    conditioned_source = _condition_board_gate(source, board)
    active_mask = mask_active_cpp_code(conditioned_source)
    active = [
        (offset, body)
        for offset, body in definitions
        if active_mask[offset:offset + len(body)].strip()
    ]
    if len(active) != 1:
        raise RuntimeError(
            f"{board} expected exactly one active coinEdgeISR definition, found {len(active)}"
        )

    active_offset, active_body = active[0]
    active_prefix = active_body.split("{", 1)[0]
    if "ICACHE_RAM_ATTR" in active_prefix:
        raise RuntimeError(
            f"{board} active coinEdgeISR still uses deprecated ICACHE_RAM_ATTR; use IRAM_ATTR"
        )
    if "IRAM_ATTR" not in active_prefix:
        raise RuntimeError(f"{board} active coinEdgeISR must use IRAM_ATTR")
    return active_offset, active_body


def extract_board_coin_edge_isr(source, board):
    return _active_board_isr_definition(source, board)[1]


def mutate_active_isr_attribute(source, board):
    active_offset, active_body = _active_board_isr_definition(source, board)
    mutated_body = active_body.replace(
        "IRAM_ATTR coinEdgeISR",
        "ICACHE_RAM_ATTR coinEdgeISR",
        1,
    )
    if mutated_body == active_body:
        raise RuntimeError(f"{board} could not inject deprecated ISR attribute into active branch")
    return source[:active_offset] + mutated_body + source[active_offset + len(active_body):]

def compile_and_run(functions):
    program = CPP.replace("@@FUNCTIONS@@", "\n\n".join(functions))
    return run_cpp_fixture(
        program,
        prefix="phx-coin-pulse-capture-",
        stem="coin_pulse_capture",
        extra_flags=("-pedantic", "-O2"),
        context="coin pulse capture lab",
    )

def verify_shared_extractor():
    probe = (
        "bool sample() {\n"
        '  const char *brace = "}";\n'
        "  // }\n"
        "  /* { */\n"
        "  return brace[0] == '}';\n"
        "}\n"
        "bool after() { return false; }\n"
    )
    expected = probe.split("\nbool after", 1)[0]
    actual = extract_function(probe, "sample")
    if actual != expected:
        raise RuntimeError("shared extractor truncated at a C++ comment/literal brace")
    attribute_probe = (
        "void ICACHE_RAM_ATTR marked() {\n"
        "  /* } */\n"
        "}\n"
        "void IRAM_ATTR next() { return; }\n"
    )
    expected_marked = attribute_probe.split("\nvoid IRAM_ATTR next", 1)[0]
    if extract_function(attribute_probe, "marked") != expected_marked:
        raise RuntimeError("shared extractor failed post-return ICACHE_RAM_ATTR function")
    if extract_function(attribute_probe, "next") != "void IRAM_ATTR next() { return; }":
        raise RuntimeError("shared extractor failed post-return IRAM_ATTR function")

    # Exercise C++ raw strings, escaped ordinary strings, and phase-2 line
    # splicing in both comment openers and closers. Braces in these non-code
    # regions must not terminate the extracted production function.
    lexical_probe = (
        "bool lexical() {\n"
        '  const char *raw = u8R"tag( } // /* { )tag";\n'
        '  const char *escaped = "quote: \\" }";\n'
        "  const char brace = '}';\n"
        "  /" + "\\" + "\n" + "/ split line-comment opener { }\n"
        "  // continued line-comment \\" + "\n" + "  { }\n"
        "  /* split block-comment closer *" + "\\" + "\n" + "/\n"
        "  return raw[0] == ' ' && escaped[0] == 'q' && brace == '}';\n"
        "}\n"
        "bool afterLexical() { return false; }\n"
    )
    expected_lexical = lexical_probe.split("\nbool afterLexical", 1)[0]
    actual_lexical = extract_function(lexical_probe, "lexical")
    if actual_lexical != expected_lexical:
        raise RuntimeError("shared extractor mishandled raw strings or phase-2 comment splicing")
    masked_lexical = mask_non_code(lexical_probe)
    if len(masked_lexical) != len(lexical_probe) or masked_lexical.count("\n") != lexical_probe.count("\n"):
        raise RuntimeError("shared extractor mask changed source offsets or newline positions")
    if "\\" + "\n" not in lexical_probe or lexical_probe.count("\n") < 8:
        raise RuntimeError("phase-2 fixture did not contain physical backslash-newline pairs")

    # Prove this fixture would catch the former raw-brace counting strategy.
    start = lexical_probe.index("bool lexical()")
    opening = lexical_probe.index("{", start)
    depth = 0
    legacy_end = None
    for position in range(opening, len(lexical_probe)):
        if lexical_probe[position] == "{":
            depth += 1
        elif lexical_probe[position] == "}":
            depth -= 1
            if depth == 0:
                legacy_end = position + 1
                break
    if legacy_end is None or lexical_probe[start:legacy_end] == expected_lexical:
        raise RuntimeError("raw-string fixture does not reject the legacy brace counter")

    print("SHARED_EXTRACTOR_COMMENT_LITERAL_BRACE_PASS")
    print("SHARED_EXTRACTOR_RAW_STRING_PHASE2_PASS")
    print("SHARED_EXTRACTOR_ISR_ATTRIBUTE_ORDER_PASS")



def verify_configure_runtime_pins_preserves_edge_baseline(source):
    body = extract_function(source, "configureRuntimePins")
    if "lastHandledCoinEdgeSequence=snapshotCoinEdgeSequence();" in body:
        raise RuntimeError("configureRuntimePins discards unhandled ISR edge baseline after attaching the coin ISR")
    if body.count("quarantineCoinIngressTransition();") != 2:
        raise RuntimeError("configureRuntimePins must quarantine ingress on both pin-attachment branches")


def verify_fixture_routes_edges_through_production_isr():
    if "++coinEdgeSequence" in CPP or "coinEdgeSequence++" in CPP:
        raise RuntimeError(
            "coin pulse fixture bypasses the production coinEdgeISR() by incrementing "
            "the volatile sequence directly"
        )
    helper = extract_function(CPP, "emitCoinEdges")
    if not helper or "coinEdgeISR();" not in helper:
        raise RuntimeError("coin pulse fixture must route emitted edges through coinEdgeISR()")
    scenarios = (
        "runMissedPulseAfterBlockingPost",
        "runMissedPulseDuringBlockingWork",
        "runMultipleUnobservedEdges",
        "runSingleObservedEdge",
        "runIngressTransitionCases",
        "runIsrSequenceWraparound",
    )
    for scenario in scenarios:
        scenario_body = extract_function(CPP, scenario)
        if "emitCoinEdges(" not in scenario_body:
            raise RuntimeError(
                f"{scenario} must inject edges through the extracted production ISR"
            )


def verify_board_specific_isr_selection(source, board):
    definitions = extract_functions(source, "coinEdgeISR")
    if len(definitions) < 2:
        raise RuntimeError(f"{board} expected at least two conditional coinEdgeISR definitions, found {len(definitions)}")

    # The selector must ignore an inactive decoy even when it appears before
    # the real board branches. A position-based [0]/[1] choice is not safe.
    probe = (
        "#if 0\n"
        "void IRAM_ATTR coinEdgeISR(){ ++disabledDecoy; }\n"
        "#endif\n"
        "#if defined(ESP8266)\n"
        "void IRAM_ATTR coinEdgeISR(){ ++esp8266Edges; }\n"
        "#else\n"
        "void IRAM_ATTR coinEdgeISR(){ ++esp32Edges; }\n"
        "#endif\n"
    )
    selected = extract_board_coin_edge_isr(probe, board)
    expected = "++esp8266Edges;" if board == "ESP8266" else "++esp32Edges;"
    if expected not in selected or "disabledDecoy" in selected:
        raise RuntimeError(f"{board} lab selected an inactive or wrong conditional coinEdgeISR branch")

    mutated = mutate_active_isr_attribute(probe, board)
    if mutated.count("ICACHE_RAM_ATTR coinEdgeISR") != 1:
        raise RuntimeError(f"{board} deprecated-attribute injection did not mutate exactly one active ISR")
    if mutated.count("IRAM_ATTR coinEdgeISR") != 2:
        raise RuntimeError(f"{board} deprecated-attribute injection changed an inactive ISR")

    # Unknown preprocessor branches are conservatively considered possible.
    # If one adds a second candidate ISR, selection must fail closed.
    ambiguous = probe + (
        "#if PHX_UNKNOWN_BOARD_MACRO\n"
        "void IRAM_ATTR coinEdgeISR(){ ++unknownBoardEdges; }\n"
        "#endif\n"
    )
    try:
        extract_board_coin_edge_isr(ambiguous, board)
    except RuntimeError as error:
        if "exactly one active" not in str(error):
            raise RuntimeError(f"{board} ambiguous ISR branch failed for the wrong reason: {error}") from error
    else:
        raise RuntimeError(f"{board} selector accepted an ambiguous unknown-macro ISR branch")

    # Directive-shaped text inside comments and raw strings must not count as
    # a second board gate. This proves the gate search uses the lexical mask.
    decoy_prefix = (
        "/*\n#if defined(ESP8266)\n*/\n"
        'const char *gateText = R"PHX(\n#if defined(ESP8266)\n)PHX";\n'
    )
    decoy_selected = extract_board_coin_edge_isr(decoy_prefix + probe, board)
    if expected not in decoy_selected or "disabledDecoy" in decoy_selected:
        raise RuntimeError(f"{board} selector counted a comment/raw-string board-gate decoy")
    print(f"{board}_BOARD_GATE_COMMENT_RAW_STRING_DECOYS_IGNORED")

    # A second real board gate is ambiguous; fail closed instead of selecting
    # whichever definition happens to appear first.
    duplicate_gate = probe + (
        "#if defined(ESP8266)\n"
        "void IRAM_ATTR coinEdgeISR(){ ++duplicateGateEdges; }\n"
        "#endif\n"
    )
    try:
        extract_board_coin_edge_isr(duplicate_gate, board)
    except RuntimeError as error:
        if "expected exactly one literal #if defined(ESP8266) board gate" not in str(error):
            raise RuntimeError(
                f"{board} duplicate board gate failed for the wrong reason: {error}"
            ) from error
    else:
        raise RuntimeError(f"{board} selector accepted duplicate board gates")
    print(f"{board}_DUPLICATE_BOARD_GATE_REJECTED")

    print(f"{board}_ACTIVE_ISR_BRANCH_SELECTION_PASS")


def verify_inactive_isr_source_decoy_tolerance(source, board):
    definitions = extract_functions(source, "coinEdgeISR")
    if len(definitions) < 2:
        raise RuntimeError(f"{board} expected both conditional coinEdgeISR definitions, found {len(definitions)}")

    decoy = (
        "#if 0\n"
        "void coinEdgeISR(){ ++disabledSourceDecoy; }\n"
        "#endif\n"
    )
    if decoy.count("\n") != 3:
        raise RuntimeError(f"{board} inactive ISR decoy must contain three physical directive line breaks")
    first_offset = definitions[0][0]
    mutated_source = source[:first_offset] + decoy + source[first_offset:]
    baseline = extract_board_coin_edge_isr(source, board)
    selected = extract_board_coin_edge_isr(mutated_source, board)
    if selected != baseline:
        raise RuntimeError(f"{board} inactive source decoy changed the selected ISR")

    # Exercise the complete board-selection contract against the mutated real
    # sketch, not only the small synthetic probe above.
    verify_board_specific_isr_selection(mutated_source, board)
    print(f"{board}_INACTIVE_ISR_SOURCE_DECOY_IGNORED")



def main():
    verify_shared_extractor()
    verify_fixture_routes_edges_through_production_isr()
    failures = []
    for board, sketch in BOARDS:
        try:
            source = sketch.read_text(encoding="utf-8")
            verify_board_specific_isr_selection(source, board)
            verify_inactive_isr_source_decoy_tolerance(source, board)
            verify_configure_runtime_pins_preserves_edge_baseline(source)
            functions = []
            for helper_name, expected_signature in FUNCTION_SPECS:
                body = extract_function(source, helper_name)
                if not body or not body.startswith(expected_signature):
                    failures.append(
                        f"{board} missing or mismatched helper signature {helper_name}"
                    )
                    break
                functions.append(body)
            if len(functions) != len(FUNCTION_SPECS):
                continue
            isr_body = extract_board_coin_edge_isr(source, board)
            legacy_mutation = mutate_active_isr_attribute(source, board)
            try:
                extract_board_coin_edge_isr(legacy_mutation, board)
            except RuntimeError as error:
                if "deprecated ICACHE_RAM_ATTR" not in str(error):
                    failures.append(
                        f"{board} deprecated ISR attribute mutation failed for the wrong reason: {error}"
                    )
                    continue
                print(f"{board}_MUTATION_REJECTED deprecated-isr-attribute")
            else:
                failures.append(f"{board} deprecated ISR attribute mutation was not rejected")
                continue
            functions.append(isr_body)
            result = compile_and_run(functions)
            if result.returncode:
                failures.append(f"{board} exact-source failure: {result.stderr or result.stdout}")
                continue
            if "COIN_PULSE_CAPTURE_PASS 18/18" not in result.stdout:
                failures.append(f"{board} missing pass marker: {result.stdout}")
                continue
            print(f"{board}_COIN_PULSE_CAPTURE_PASS 18/18")
            for name, helper_name, old, new, expected in MUTATIONS:
                index = (len(functions) - 1) if helper_name == "coinEdgeISR" else FUNCTION_INDEX_BY_NAME.get(helper_name)
                if index is None:
                    failures.append(f"{board} mutation references unknown helper {helper_name}")
                    break
                if old not in functions[index]:
                    failures.append(f"{board} missing mutation anchor {name}")
                    break
                mutated = list(functions)
                mutated[index] = mutated[index].replace(old, new, 1)
                injected = compile_and_run(mutated)
                if injected.returncode == 0 or expected not in injected.stderr:
                    failures.append(f"{board} mutation not rejected: {name}")
                    break
                print(f"{board}_MUTATION_REJECTED {name}")
        except Exception as error:
            failures.append(f"{board} lab error: {error}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("SIMULATED_ONLY=1")
    print("PHYSICAL_COIN_PULSE_ACCEPTANCE=0")
    print("PHYSICAL_RELAY_ACCEPTANCE=0")
    print("PHYSICAL_POWER_CUT_ACCEPTANCE=0")

# The quarantine workflow owns poll_loop_blocking_inhibit_lab.py as a separate step.
# Keep this entry point limited to the coin-pulse capture suite.
if __name__ == "__main__":
    main()
