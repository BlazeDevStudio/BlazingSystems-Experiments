#!/usr/bin/env python3
"""PHX-HARDWARE exact-source coin pulse, bounded-batch overflow, target-drift, post-finalization and ISR-unobserved edge safety lab.

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
from cpp_fixture_runner import run_cpp_fixture

from firmware_lab_source import extract_function, mask_non_code
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


def main():
    verify_shared_extractor()
    failures = []
    for board, sketch in BOARDS:
        try:
            source = sketch.read_text(encoding="utf-8")
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
            result = compile_and_run(functions)
            if result.returncode:
                failures.append(f"{board} exact-source failure: {result.stderr or result.stdout}")
                continue
            if "COIN_PULSE_CAPTURE_PASS 17/17" not in result.stdout:
                failures.append(f"{board} missing pass marker: {result.stdout}")
                continue
            print(f"{board}_COIN_PULSE_CAPTURE_PASS 17/17")
            for name, helper_name, old, new, expected in MUTATIONS:
                index = FUNCTION_INDEX_BY_NAME.get(helper_name)
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
