#!/usr/bin/env python3
"""Run bounded EEPROM configuration validation and legacy migration checks."""
from config_storage_integrity_lab_contract import (
    SKETCH,
    assert_source_contract,
    expect_rejected,
    move_helpers_before_legacy_struct,
)
from config_storage_integrity_lab_harness import compile_and_run, cxx_harness

def main() -> None:
    source = SKETCH.read_text(encoding="utf-8")
    assert_source_contract(source)
    expect_rejected(
        "arduino-prototype-order",
        move_helpers_before_legacy_struct(source),
    )
    expect_rejected(
        "current-config-validation-removed",
        source.replace("configStringsTerminated(cfg)", "true", 1),
    )
    expect_rejected(
        "legacy-config-validation-removed",
        source.replace("configV1StringsTerminated(oldCfg)", "true", 1),
    )
    expect_rejected(
        "nul-terminator-comparison-removed",
        source.replace("value[i]=='\\0'", "value[i]=='X'", 1),
    )
    expect_rejected(
        "unbounded-ap-password-length",
        source.replace(
            "boundedStringLength(cfg.apPass,sizeof(cfg.apPass))",
            "strlen(cfg.apPass)",
            1,
        ),
    )

    print(compile_and_run(cxx_harness(source), "config_integrity"))
    print("EEPROM_CONFIG_SOURCE_CONTRACT_PASS")
    print("EEPROM_CONFIG_FAILURE_INJECTION_PASS 5/5")

if __name__ == "__main__":
    main()
