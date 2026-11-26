#!/usr/bin/env python3
"""Prove ESP configuration persistence fails closed across partial NVS writes and reboot."""
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
    successes = [m.start() for m in re.finditer(r"web\.send\s*\(\s*200\s*,", portal)]
    require(len(successes) >= 2, f"{save_name} route must retain GET and save-success responses")
    success = successes[-1]
    restart = portal.find("ESP.restart()", success)
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
    global_source = mask_non_code(source)
    require(re.search(r"\bbool\s+configStoreValid\s*=\s*true", global_source) is not None,
            "ESP32 must track whether the persisted configuration is valid")
    require(re.search(r"\bbool\s+preferencesReady\s*=\s*false", global_source) is not None,
            "ESP32 must track whether Preferences.begin succeeded")

    raw_defaults = extract_function(source, "void useSafeConfigDefaults(")
    defaults = mask_non_code(raw_defaults)
    require("cfg=Config();" in defaults and 'cfg.server="10.0.0.1";' in raw_defaults and
            'cfg.id="vendo-01";' in raw_defaults and "cfg.apPass=String(b);" in raw_defaults,
            "invalid configuration recovery must use documented safe defaults and a fresh setup password")

    raw_load = extract_function(source, "void loadConfig(")
    load = mask_non_code(raw_load)
    begin = raw_load.find('preferencesReady=prefs.begin("blazevendo",false)')
    marker = re.search(
        r"if\s*\(\s*prefs\.isKey\s*\(\s*\"cfgvalid\"\s*\)\s*&&\s*!\s*"
        r"prefs\.getBool\s*\(\s*\"cfgvalid\"\s*,\s*false\s*\)\s*\)",
        raw_load,
    )
    first_read_positions = [
        raw_load.find(token) for token in
        ("prefs.getString(", "prefs.getInt(", "prefs.getUInt(")
        if raw_load.find(token) >= 0
    ]
    require(begin >= 0, "loadConfig must check Preferences.begin")
    require(marker is not None and begin < marker.start(),
            "loadConfig must check the validity marker after opening Preferences")
    require(bool(first_read_positions) and marker.start() < min(first_read_positions),
            "cfgvalid must be checked before reading any persisted configuration fields")
    require(load.count("configStoreValid=false") >= 2,
            "Preferences-open and invalid-marker paths must mark the configuration invalid")
    require(raw_load.count("useSafeConfigDefaults()") >= 2,
            "both invalid-storage paths must discard partial fields and use safe defaults")
    require(re.search(r"if\s*\(\s*!\s*preferencesReady\s*\)\s*\{", load) is not None,
            "Preferences.begin failure must return before field reads")
    require(load.count("return;") >= 2,
            "invalid-storage paths must return before reading partial fields")

    raw_save = extract_function(source, "bool saveConfig(")
    save = mask_non_code(raw_save)
    require(re.search(r"configStoreValid\s*=\s*false", save) is not None,
            "saveConfig must deny network use while a new configuration is being persisted")
    require(re.search(
        r"if\s*\(\s*!\s*preferencesReady\s*\)\s*\{\s*preferencesReady\s*=\s*prefs\.begin\s*\(",
        save,
    ) is not None, "saveConfig must retry Preferences.begin for setup recovery")
    invalid_marker = raw_save.find('prefs.putBool("cfgvalid",false)')
    valid_marker = raw_save.find('prefs.putBool("cfgvalid",true)')
    first_data = min(
        raw_save.find(token) for token in
        ('prefs.putString("ssid"', 'prefs.putInt("coinpin"', 'prefs.putBool("coinlow"',
         'prefs.putUInt("debounce"')
    )
    last_data = raw_save.rfind('prefs.putUInt("groupms"')
    require(invalid_marker >= 0 and invalid_marker < first_data,
            "saveConfig must persist cfgvalid=false before changing any configuration field")
    require(valid_marker > last_data,
            "saveConfig must publish cfgvalid=true only after every configuration write")
    require(re.search(
        r"if\s*\(\s*prefs\.putBool\s*\(\s*\"cfgvalid\"\s*,\s*false\s*\)\s*==\s*0\s*\)\s*return\s+false\s*;",
        raw_save,
    ) is not None, "failure to invalidate the old marker must stop before field writes")
    require(re.search(r"if\s*\(\s*!\s*ok\s*\)\s*return\s+false\s*;", save) is not None,
            "any field-write failure must leave the validity marker false")
    require(re.search(
        r"if\s*\(\s*prefs\.putBool\s*\(\s*\"cfgvalid\"\s*,\s*true\s*\)\s*==\s*0\s*\)\s*return\s+false\s*;",
        raw_save,
    ) is not None, "failure to publish the final valid marker must fail the save")
    require(save.rfind("configStoreValid=true") > valid_marker,
            "network use may resume only after the final valid marker succeeds")

    expected = {"putString": 6, "putInt": 3, "putBool": 5, "putUInt": 2}
    for method, count in expected.items():
        calls = len(re.findall(rf"\bprefs\.{method}\s*\(", save))
        checked = len(re.findall(rf"\bif\s*\(\s*prefs\.{method}\s*\(", save))
        require(calls == count and checked == count,
                f"all {count} Preferences.{method} writes must be checked; found {checked}/{calls}")

    connect = mask_non_code(extract_function(source, "void connectSta("))
    require(re.search(r"if\s*\(\s*!\s*configStoreValid\s*\|\|\s*cfg\.ssid\.isEmpty\s*\(\s*\)\s*\)", connect) is not None,
            "connectSta must not register or connect using an invalid partial configuration")
    loop = mask_non_code(extract_function(source, "void loop("))
    require(re.search(r"if\\s*\\(\\s*!\\s*configStoreValid\\s*\\)\\s*\\{\\s*delay\\s*\\(\\s*2\\s*\\)\\s*;\\s*return\\s*;\\s*\\}", loop) is not None,
            "invalid configuration must return from loop before reconnect or polling")
    require("if(WiFi.status()!=WL_CONNECTED" in loop,
            "network reconnect condition must remain compatible with the shared poll guard")
    require("if(WiFi.status()==WL_CONNECTED" in loop,
            "controller poll condition must remain compatible with the shared poll guard")
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
    defaults = extract_function(source, "void useSafeConfigDefaults(")
    load = extract_function(source, "void loadConfig(")
    save = extract_function(source, "bool saveConfig(")
    return r"""
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
using String = std::string;
struct Config {
    String ssid, pass, server, key, id, apPass;
    int coinPin = 27, insertLedPin = 2, relayPin = 26;
    bool coinActiveLow = true, relayActiveHigh = true, ledActiveHigh = true;
    uint16_t coinDebounceMs = 40, pulseGroupMs = 400;
};
bool configStoreValid = true;
bool preferencesReady = false;
uint32_t esp_random() { return 0x12345678UL; }
struct FakeSerial { void println(const char *) {} };
FakeSerial Serial;
struct FakePreferences {
    bool begin_ok = true;
    bool marker_exists = false;
    bool marker_value = false;
    std::map<std::string, std::string> values;
    std::string fail_key;
    int fail_occurrence = 0;
    int begin_calls = 0;
    int writes = 0;
    int data_writes = 0;
    int data_reads = 0;
    int cfgvalid_calls = 0;
    std::map<std::string, int> seen;
    void reset() {
        begin_ok = true; marker_exists = false; marker_value = false;
        values.clear(); fail_key.clear(); fail_occurrence = 0;
        begin_calls = 0; writes = 0; data_writes = 0; data_reads = 0;
        cfgvalid_calls = 0; seen.clear();
    }
    bool begin(const char *, bool) { ++begin_calls; return begin_ok; }
    bool isKey(const char *key) const {
        if (std::string(key) == "cfgvalid") return marker_exists;
        return values.count(key) != 0;
    }
    bool getBool(const char *key, bool fallback) {
        if (std::string(key) == "cfgvalid" && marker_exists) return marker_value;
        ++data_reads; return fallback;
    }
    String getString(const char *key, const char *fallback) {
        ++data_reads;
        auto it = values.find(key);
        return it == values.end() ? String(fallback) : it->second;
    }
    int getInt(const char *key, int fallback) {
        ++data_reads;
        auto it = values.find(key);
        return it == values.end() ? fallback : std::stoi(it->second);
    }
    uint32_t getUInt(const char *key, uint32_t fallback) {
        ++data_reads;
        auto it = values.find(key);
        return it == values.end() ? fallback : static_cast<uint32_t>(std::stoul(it->second));
    }
    size_t result(const char *key, size_t bytes) {
        ++writes;
        std::string name(key);
        int occurrence = ++seen[name];
        if (name == "cfgvalid") ++cfgvalid_calls; else ++data_writes;
        if (fail_key == name && (fail_occurrence == 0 || fail_occurrence == occurrence)) return 0;
        return bytes;
    }
    size_t putString(const char *key, const String &value) {
        size_t n = result(key, value.size() + 1);
        if (n) values[key] = value;
        return n;
    }
    size_t putInt(const char *key, int32_t value) {
        size_t n = result(key, sizeof(value));
        if (n) values[key] = std::to_string(value);
        return n;
    }
    size_t putUInt(const char *key, uint32_t value) {
        size_t n = result(key, sizeof(value));
        if (n) values[key] = std::to_string(value);
        return n;
    }
    size_t putBool(const char *key, bool value) {
        size_t n = result(key, sizeof(value));
        if (n) {
            if (std::string(key) == "cfgvalid") {
                marker_exists = true; marker_value = value;
            } else values[key] = value ? "1" : "0";
        }
        return n;
    }
};
Config cfg{};
FakePreferences prefs;
""" + defaults + "\n" + load + "\n" + save + r"""

int main() {
    // A durable false marker means the previous multi-key save was interrupted.
    prefs.reset(); prefs.marker_exists = true; prefs.marker_value = false;
    prefs.values["ssid"] = "partial-ssid"; prefs.values["server"] = "10.99.0.1";
    prefs.values["coinpin"] = "99"; prefs.values["appass"] = "partial-ap-pass";
    configStoreValid = true; preferencesReady = false; cfg = Config(); loadConfig();
    if (configStoreValid || !preferencesReady || !cfg.ssid.empty() ||
        cfg.server != "10.0.0.1" || cfg.id != "vendo-01" || cfg.coinPin != 27) return 1;
    if (prefs.data_reads != 0 || prefs.data_writes != 0 || cfg.apPass.size() < 8) return 2;
    std::cout << "ESP32_INVALID_CONFIG_MARKER_DEFAULTS_PASS\n";

    // A missing marker is a pre-upgrade legacy configuration and remains readable.
    prefs.reset(); prefs.values["ssid"] = "legacy-ssid"; prefs.values["pass"] = "legacy-pass";
    prefs.values["server"] = "10.0.0.2"; prefs.values["key"] = "legacy-key";
    prefs.values["id"] = "legacy-id"; prefs.values["appass"] = "legacy-ap-pass";
    prefs.values["coinpin"] = "4"; configStoreValid = false; preferencesReady = false;
    cfg = Config(); loadConfig();
    if (!configStoreValid || !preferencesReady || cfg.ssid != "legacy-ssid" ||
        cfg.server != "10.0.0.2" || cfg.coinPin != 4) return 3;
    std::cout << "ESP32_LEGACY_CONFIG_WITHOUT_MARKER_COMPAT_PASS\n";

    // Preferences.open failure is denied; the setup-save path may retry later.
    prefs.reset(); prefs.begin_ok = false; configStoreValid = true; preferencesReady = false;
    cfg = Config(); loadConfig();
    if (configStoreValid || preferencesReady || !cfg.ssid.empty() ||
        cfg.server != "10.0.0.1" || prefs.data_reads != 0) return 4;
    prefs.begin_ok = true; cfg.apPass = "setup-pass";
    if (!saveConfig() || prefs.begin_calls != 2 || !prefs.marker_value || !configStoreValid) return 5;
    std::cout << "ESP32_PREFERENCES_BEGIN_FAILURE_RETRY_PASS\n";

    const char *keys[] = {
        "ssid", "pass", "server", "key", "id", "appass", "coinpin", "ledpin",
        "relaypin", "coinlow", "relayhi", "ledhi", "debounce", "groupms"
    };
    for (const char *key : keys) {
        prefs.reset(); prefs.marker_exists = true; prefs.marker_value = true;
        prefs.fail_key = key; prefs.fail_occurrence = 1;
        preferencesReady = true; configStoreValid = true; cfg = Config(); cfg.apPass = "setup-pass";
        if (saveConfig()) return 6;
        if (prefs.data_writes != 14 || !prefs.marker_exists || prefs.marker_value || configStoreValid) return 7;
        if (prefs.cfgvalid_calls != 1) return 8;
    }

    // If the old marker cannot be invalidated, no configuration field may be changed.
    prefs.reset(); prefs.marker_exists = true; prefs.marker_value = true;
    prefs.fail_key = "cfgvalid"; prefs.fail_occurrence = 1;
    preferencesReady = true; configStoreValid = true; cfg = Config(); cfg.apPass = "setup-pass";
    if (saveConfig() || prefs.data_writes != 0 || !prefs.marker_value || configStoreValid) return 9;

    // If the final valid marker cannot be written, the stored marker remains false.
    prefs.reset(); prefs.marker_exists = true; prefs.marker_value = true;
    prefs.fail_key = "cfgvalid"; prefs.fail_occurrence = 2;
    preferencesReady = true; configStoreValid = true; cfg = Config(); cfg.apPass = "setup-pass";
    if (saveConfig() || prefs.data_writes != 14 || prefs.marker_value || configStoreValid) return 10;
    if (prefs.cfgvalid_calls != 2) return 11;

    prefs.reset(); prefs.marker_exists = true; prefs.marker_value = true;
    preferencesReady = true; configStoreValid = false; cfg = Config(); cfg.apPass = "setup-pass";
    if (!saveConfig()) return 12;
    if (prefs.data_writes != 14 || prefs.cfgvalid_calls != 2 || !prefs.marker_value || !configStoreValid) return 13;
    std::cout << "ESP32_CONFIG_VALIDITY_LATCH_FAILURE_MATRIX_PASS fields=14 marker_failures=2\n";
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
            "if(configStoreValid && WiFi.status()==WL_CONNECTED",
            "if(WiFi.status()==WL_CONNECTED",
            1,
        ),
        assert_esp32,
    )
    print("CONFIG_PERSISTENCE_WRITE_RESULT_PASS ESP8266+ESP32")


if __name__ == "__main__":
    main()
