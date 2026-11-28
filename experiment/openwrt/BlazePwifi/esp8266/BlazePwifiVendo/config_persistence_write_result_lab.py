#!/usr/bin/env python3
"""Run fail-closed ESP configuration persistence checks for both boards."""
from config_persistence_write_result_lab_contract import (
    ESP8266,
    ESP32,
    assert_esp8266,
    assert_esp32,
    expect_rejected,
)
from config_persistence_write_result_lab_harness import (
    compile_and_run,
    eeprom_harness,
    preferences_harness,
)
from checked_eeprom_begin_lab import main as checked_eeprom_begin_main


def main() -> None:
    esp8266 = ESP8266.read_text(encoding="utf-8")
    esp32 = ESP32.read_text(encoding="utf-8")
    assert_esp8266(esp8266)
    assert_esp32(esp32)

    print(compile_and_run(eeprom_harness(esp8266), "eeprom_failure"))
    print(compile_and_run(preferences_harness(esp32), "preferences_failure"))

    expect_rejected(
        "eeprom-begin-result-ignored",
        esp8266.replace(
            "configStoreReady=configEeprom.beginChecked(sizeof(Config));",
            "configEeprom.beginChecked(sizeof(Config)); configStoreReady=true;",
            1,
        ),
        assert_esp8266,
    )
    expect_rejected(
        "eeprom-save-skips-begin-check",
        esp8266.replace(
            "if(!beginConfigStore()) return false;",
            "/* begin guard removed */",
            1,
        ),
        assert_esp8266,
    )
    expect_rejected(
        "eeprom-commit-result-ignored",
        esp8266.replace(
            "if(!configEeprom.commit()){",
            "configEeprom.commit(); if(false){",
            1,
        ),
        assert_esp8266,
    )
    expect_rejected(
        "eeprom-commit-failure-keeps-store-ready",
        esp8266.replace(
            "if(!configEeprom.commit()){\n    configStoreReady=false;",
            "if(!configEeprom.commit()){\n    configStoreReady=true;",
            1,
        ),
        assert_esp8266,
    )
    expect_rejected(
        "eeprom-web-handler-ignores-failure",
        esp8266.replace("if(!saveCfg())", "if(false)", 1),
        assert_esp8266,
    )
    expect_rejected(
        "preferences-write-result-ignored",
        esp32.replace(
            'if(prefs.putString("ssid",cfg.ssid)==0) ok=false;',
            'prefs.putString("ssid",cfg.ssid);',
            1,
        ),
        assert_esp32,
    )
    expect_rejected(
        "preferences-web-handler-ignores-failure",
        esp32.replace("if(!saveConfig())", "if(false)", 1),
        assert_esp32,
    )
    expect_rejected(
        "invalid-config-marker-ignored",
        esp32.replace(
            'if(prefs.isKey("cfgvalid") && !prefs.getBool("cfgvalid",false))',
            "if(false)",
            1,
        ),
        assert_esp32,
    )
    expect_rejected(
        "network-connect-ignores-config-validity",
        esp32.replace(
            "if(!configStoreValid || cfg.ssid.isEmpty())",
            "if(cfg.ssid.isEmpty())",
            1,
        ),
        assert_esp32,
    )
    expect_rejected(
        "controller-poll-ignores-config-validity",
        esp32.replace(
            "if(!configStoreValid){ delay(2); return; }",
            "if(false){ delay(2); return; }",
            1,
        ),
        assert_esp32,
    )
    print("CONFIG_PERSISTENCE_WRITE_RESULT_PASS ESP8266+ESP32")
    # CheckedEEPROMClass allocator and flash-read failure paths run in this CI entrypoint.
    checked_eeprom_begin_main()


if __name__ == "__main__":
    main()
