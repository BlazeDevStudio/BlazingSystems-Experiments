#!/usr/bin/env python3
"""Prove setup configuration writes cannot be reported successful after storage failure."""
from pathlib import Path
import re
import subprocess
import tempfile

from firmware_source_extract import extract_function, mask_non_code

BLAZEPWIFI = Path(__file__).resolve().parents[2]
ESP8266 = BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
ESP32 = BLAZEPWIFI / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_rejected(label: str, source: str, validator) -> None:
    try:
        validator(source)
    except AssertionError:
        print(f"CONFIG_PERSISTENCE_MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe configuration persistence mutation accepted: {label}")


def require_failure_gate(source: str, save_name: str) -> None:
    portal = mask_non_code(extract_function(source, "void setupPortal("))
    match = re.search(
        rf"if\s*\(\s*!\s*{re.escape(save_name)}\s*\(\s*\)\s*\)\s*\{{([\s\S]*?)\}}",
        portal,
    )
    require(match is not None, f"setup route must branch on {save_name} failure")
    failure = match.group(1)
    require("denyRemoteControl()" in failure,
            f"{save_name} failure must keep controller outputs denied")
    require(re.search(r"web\.send\s*\(\s*500\s*,", failure) is not None,
            f"{save_name} failure must return an HTTP 500 response")
    require(re.search(r"\breturn\s*;", failure) is not None,
            f"{save_name} failure must stop the handler")
    require("ESP.restart()" not in failure,
            f"{save_name} failure must not reboot")
    success = portal.find("web.send(200")
    restart = portal.find("ESP.restart()")
    require(success > match.end() and restart > success,
            f"{save_name} success response/reboot must follow the failure gate")


def assert_esp8266(source: str) -> None:
    save = mask_non_code(extract_function(source, "bool saveCfg("))
    require(re.search(r"\bEEPROM\.put\s*\(\s*0\s*,\s*cfg\s*\)\s*;", save) is not None,
            "ESP8266 saveCfg must stage the current Config record")
    require(re.search(r"\breturn\s+EEPROM\.commit\s*\(\s*\)\s*;", save) is not None,
            "ESP8266 saveCfg must propagate EEPROM.commit()")
    load = mask_non_code(extract_function(source, "void loadCfg("))
    require(len(re.findall(r"if\s*\(\s*!\s*saveCfg\s*\(\s*\)\s*\)", load)) >= 2,
            "legacy migration and defaults paths must report failed persistence")
    require_failure_gate(source, "saveCfg")


def assert_esp32(source: str) -> None:
    save = mask_non_code(extract_function(source, "bool saveConfig("))
    require(re.search(r"\bbool\s+ok\s*=\s*true\s*;", save) is not None,
            "ESP32 saveConfig must aggregate all Preferences write results")
    expected = {"putString": 5, "putInt": 3, "putBool": 3, "putUInt": 2}
    for method, count in expected.items():
        calls = len(re.findall(rf"\bprefs\.{method}\s*\(", save))
        checked = len(re.findall(rf"\bif\s*\(\s*prefs\.{method}\s*\(", save))
        require(calls == count and checked == count,
                f"all {count} Preferences.{method} writes must be checked; found {checked}/{calls}")
    require(re.search(r"\breturn\s+ok\s*;", save) is not None,
            "ESP32 saveConfig must return aggregate write status")
    require_failure_gate(source, "saveConfig")


def compile_and_run(source: str, label: str) -> str:
    with tempfile.TemporaryDirectory(prefix="phx-config-persist-") as directory:
        cpp = Path(directory) / f"{label}.cpp"
        exe = Path(directory) / label
        cpp.write_text(source, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run([str(exe)], check=True, capture_output=True, text=True)
        return result.stdout.strip()


def eeprom_harness(source: str) -> str:
    save = extract_function(source, "bool saveCfg(")
    return r"""
#include <iostream>
struct Config { int marker; };
struct FakeEEPROM {
    bool commit_result = false;
    int put_calls = 0;
    int commit_calls = 0;
    void put(int address, const Config &value) {
        (void)address; (void)value; ++put_calls;
    }
    bool commit() { ++commit_calls; return commit_result; }
};
Config cfg{};
FakeEEPROM EEPROM;
""" + save + r"""
int main() {
    EEPROM.commit_result = false;
    if (saveCfg()) return 1;
    if (EEPROM.put_calls != 1 || EEPROM.commit_calls != 1) return 2;
    EEPROM.commit_result = true;
    if (!saveCfg()) return 3;
    if (EEPROM.put_calls != 2 || EEPROM.commit_calls != 2) return 4;
    std::cout << "ESP8266_EEPROM_COMMIT_FAILURE_PROPAGATED_PASS\n";
    return 0;
}
"""


def preferences_harness(source: str) -> str:
    save = extract_function(source, "bool saveConfig(")
    return r"""
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <string>
using String = std::string;
struct Config {
    String ssid, pass, server, key, id;
    int coinPin = 27, insertLedPin = 2, relayPin = 26;
    bool coinActiveLow = true, relayActiveHigh = true, ledActiveHigh = true;
    uint16_t coinDebounceMs = 40, pulseGroupMs = 400;
};
struct FakePreferences {
    std::string fail_key;
    int writes = 0;
    size_t result(const char *key, size_t bytes) {
        ++writes;
        return fail_key == key ? 0 : bytes;
    }
    size_t putString(const char *key, const String &value) {
        return result(key, value.size() + 1);
    }
    size_t putInt(const char *key, int32_t value) {
        (void)value; return result(key, sizeof(value));
    }
    size_t putUInt(const char *key, uint32_t value) {
        (void)value; return result(key, sizeof(value));
    }
    size_t putBool(const char *key, bool value) {
        (void)value; return result(key, sizeof(value));
    }
};
Config cfg{};
FakePreferences prefs;
""" + save + r"""
int main() {
    prefs.fail_key = "server";
    if (saveConfig()) return 1;
    if (prefs.writes != 13) return 2;
    prefs.fail_key.clear();
    prefs.writes = 0;
    if (!saveConfig()) return 3;
    if (prefs.writes != 13) return 4;
    std::cout << "ESP32_PREFERENCES_WRITE_FAILURE_PROPAGATED_PASS writes=13/13\n";
    return 0;
}
"""


def main() -> None:
    esp8266 = ESP8266.read_text(encoding="utf-8")
    esp32 = ESP32.read_text(encoding="utf-8")
    assert_esp8266(esp8266)
    assert_esp32(esp32)

    print(compile_and_run(eeprom_harness(esp8266), "eeprom_failure"))
    print(compile_and_run(preferences_harness(esp32), "preferences_failure"))

    expect_rejected(
        "eeprom-commit-result-ignored",
        esp8266.replace("return EEPROM.commit();", "EEPROM.commit(); return true;", 1),
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
    print("CONFIG_PERSISTENCE_WRITE_RESULT_PASS ESP8266+ESP32")
    

if __name__ == "__main__":
    main()
