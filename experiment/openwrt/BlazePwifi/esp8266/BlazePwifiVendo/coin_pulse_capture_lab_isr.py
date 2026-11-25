#!/usr/bin/env python3
"""Board-specific C++ preprocessor selection and mutation contracts for the coin ISR lab.

This module owns only the board-conditioned ISR selector. The main runner
keeps pulse scenarios and persistence mutations separate from preprocessor
branch selection so each contract can be inspected and changed independently.
"""
import re

from firmware_lab_source import extract_functions, mask_active_cpp_code, mask_non_code

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
