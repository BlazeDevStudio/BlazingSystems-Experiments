#!/usr/bin/env python3
"""Run bounded EEPROM configuration validation and legacy migration checks."""
from config_storage_integrity_lab_contract import (
    SKETCH,
    assert_source_contract,
    expect_rejected,
    move_helpers_before_legacy_struct,
)
from pathlib import Path

from config_storage_integrity_lab_harness import (
    RUNTIME_FIXTURE_MARKERS,
    compile_and_run,
    cxx_harness,
    expect_runtime_fixture_rejected,
    loadcfg_runtime_harness,
    render_runtime_fixture,
)

def verify_runtime_fixture_template_contract() -> None:
    template_path = Path(__file__).with_name("config_loadcfg_runtime_fixture.cpp.in")
    template = template_path.read_text(encoding="utf-8")
    replacements = tuple(
        (marker, "// PHX fixture segment rendered")
        for marker in RUNTIME_FIXTURE_MARKERS
    )

    rendered = render_runtime_fixture(template, replacements)
    if "PHX_CONFIG_" in rendered:
        raise AssertionError("valid runtime fixture retained an unresolved marker")

    rejected = 0
    for marker in RUNTIME_FIXTURE_MARKERS:
        expect_runtime_fixture_rejected(
            template.replace(marker, "", 1),
            replacements,
            f"missing:{marker}",
            "must occur exactly once",
        )
        rejected += 1
        expect_runtime_fixture_rejected(
            template + "\n" + marker,
            replacements,
            f"duplicate:{marker}",
            "must occur exactly once",
        )
        rejected += 1

    expect_runtime_fixture_rejected(
        template + "\n/* PHX_CONFIG_UNKNOWN */",
        replacements,
        "unresolved-marker",
        "unresolved runtime fixture template marker",
    )
    rejected += 1
    if rejected != 9:
        raise AssertionError(f"unexpected runtime fixture mutation count: {rejected}")
    print(f"EEPROM_RUNTIME_TEMPLATE_FAILURE_INJECTION_PASS {rejected}/9")


def main() -> None:
    source = SKETCH.read_text(encoding="utf-8")
    assert_source_contract(source)
    verify_runtime_fixture_template_contract()
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

    expect_rejected(
        "migration-commit-result-ignored",
        source.replace(
            'if(!saveCfg()) Serial.println("CRITICAL: EEPROM configuration migration write failed; retrying on next boot.");',
            "saveCfg();",
            1,
        ),
    )
    expect_rejected(
        "defaults-commit-result-ignored",
        source.replace(
            'if(!saveCfg()) Serial.println("CRITICAL: EEPROM defaults write failed; setup remains available.");',
            "saveCfg();",
            1,
        ),
    )


    expect_rejected(
        "eeprom-begin-result-ignored",
        source.replace(
            "configStoreReady=configEeprom.beginChecked(sizeof(Config));",
            "EEPROM.begin(sizeof(Config)); configStoreReady=true;",
            1,
        ),
    )
    expect_rejected(
        "loadcfg-begin-failure-fallthrough",
        source.replace("if(!beginConfigStore()){", "if(false){", 1),
    )
    expect_rejected(
        "savecfg-skips-begin-check",
        source.replace(
            "if(!beginConfigStore()) return false;",
            "/* begin guard removed */",
            1,
        ),
    )
    expect_rejected(
        "connectsta-uses-uninitialized-config",
        source.replace(
            "if(!configStoreReady || !strlen(cfg.ssid)) return;",
            "if(!strlen(cfg.ssid)) return;",
            1,
        ),
    )
    expect_rejected(
        "reconnect-uses-uninitialized-config",
        source.replace(
            "&& configStoreReady && strlen(cfg.ssid)",
            "&& strlen(cfg.ssid)",
            1,
        ),
    )
    expect_rejected(
        "poll-uses-uninitialized-config",
        source.replace(
            "WiFi.status()==WL_CONNECTED && configStoreReady && millis()-lastPoll>1500",
            "WiFi.status()==WL_CONNECTED && millis()-lastPoll>1500",
            1,
        ),
    )
    expect_rejected(
        "output-enable-without-config-store",
        source.replace(
            "bool accepting=configStoreReady && controllerEnabled",
            "bool accepting=controllerEnabled",
            1,
        ),
    )


    expect_rejected(
        "eeprom-sector-limit-removed",
        source.replace(
            "if(requested==0 || requested>kFlashSectorBytes) return false;",
            "if(false) return false;",
            1,
        ),
    )
    expect_rejected(
        "eeprom-allocation-failure-ignored",
        source.replace("if(!_data){", "if(false){", 1),
    )
    expect_rejected(
        "eeprom-flash-read-failure-ignored",
        source.replace(
            "if(!ESP.flashRead(address,_data,_size)){",
            "if(false){",
            1,
        ),
    )

    print(compile_and_run(cxx_harness(source), "config_integrity"))
    print(compile_and_run(loadcfg_runtime_harness(source), "config_loadcfg_runtime"))
    print("EEPROM_CONFIG_SOURCE_CONTRACT_PASS")
    print("EEPROM_CONFIG_FAILURE_INJECTION_PASS 17/17")

if __name__ == "__main__":
    main()
