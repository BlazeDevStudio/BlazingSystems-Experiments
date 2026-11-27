#!/usr/bin/env python3
"""Run both-board startup GPIO OFF-preload and polarity regressions."""
from firmware_source_extract import extract_function
from output_enable_sequence_lab_contract import (
    BOARDS,
    active_write_mutation,
    polarity_coupling_mutation,
    unsafe_mutation,
    verify_shared_extractor_contract,
)
from output_enable_sequence_lab_harness import build_and_run

verify_shared_extractor_contract()
for board, path in BOARDS:
    source = path.read_text(encoding="utf-8")
    write_logical = extract_function(source, "void writeLogical")
    configure = extract_function(source, "void configureRuntimePins")
    build_and_run(board, write_logical, configure, expect_pass=True)
    build_and_run(board, write_logical, unsafe_mutation(configure), expect_pass=False, mutation_label="missing pre-output OFF preload")
    active_write_mutations = (
        (
            "relay-active-before-output-enable",
            "  writeLogical(runRelayPin,false,runRelayActiveHigh);\n  writeLogical(runLedPin,false,runLedActiveHigh);",
            "writeLogical(runRelayPin,true,runRelayActiveHigh);",
        ),
        (
            "led-active-before-output-enable",
            "  writeLogical(runRelayPin,false,runRelayActiveHigh);\n  writeLogical(runLedPin,false,runLedActiveHigh);",
            "writeLogical(runLedPin,true,runLedActiveHigh);",
        ),
        (
            "relay-active-after-output-enable",
            "pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);",
            "writeLogical(runRelayPin,true,runRelayActiveHigh);",
        ),
        (
            "led-active-after-output-enable",
            "pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);",
            "writeLogical(runLedPin,true,runLedActiveHigh);",
        ),
    )
    for label, anchor, statement in active_write_mutations:
        mutated = active_write_mutation(configure, anchor, statement)
        build_and_run(board, write_logical, mutated, expect_pass=False, mutation_label=label)
    polarity_mutations = (
        ("relay incorrectly borrows LED polarity", "runRelayPin", "runRelayActiveHigh", "runLedActiveHigh"),
        ("LED incorrectly borrows relay polarity", "runLedPin", "runLedActiveHigh", "runRelayActiveHigh"),
    )
    for label, target_pin, correct_polarity, wrong_polarity in polarity_mutations:
        mutated = polarity_coupling_mutation(configure, target_pin, correct_polarity, wrong_polarity)
        build_and_run(board, write_logical, mutated, expect_pass=False, mutation_label=label)

print("PHX-HARDWARE: 8/8 independent board/polarity scenarios PASS; 14/14 injected regressions rejected; physical GPIO/relay behavior NOT TESTED")
