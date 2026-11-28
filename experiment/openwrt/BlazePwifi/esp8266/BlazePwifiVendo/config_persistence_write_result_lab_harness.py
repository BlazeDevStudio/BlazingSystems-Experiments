"""Native C++ fault-injection harnesses for ESP config persistence."""
from pathlib import Path
import subprocess
import tempfile

from firmware_source_extract import extract_function


def compile_and_run_result(source: str, label: str):
    """Compile a native fixture and return its process result for exact failure checks."""
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
        return subprocess.run([str(exe)], check=False, capture_output=True, text=True)


def compile_and_run(source: str, label: str) -> str:
    result = compile_and_run_result(source, label)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, result.args, output=result.stdout, stderr=result.stderr
        )
    return result.stdout.strip()


def eeprom_harness(source: str) -> str:
    begin = extract_function(source, "bool beginConfigStore()")
    save = extract_function(source, "bool saveCfg(")
    return r"""
#include <cstddef>
#include <iostream>
struct Config { int marker; };
struct FakeCheckedEEPROM {
    bool begin_result = false;
    bool commit_result = false;
    int begin_calls = 0;
    int put_calls = 0;
    int commit_calls = 0;
    bool beginChecked(size_t size) {
        ++begin_calls;
        return size == sizeof(Config) && begin_result;
    }
    void put(int address, const Config &value) {
        (void)address; (void)value; ++put_calls;
    }
    bool commit() { ++commit_calls; return commit_result; }
};
bool configStoreReady = false;
Config cfg{};
FakeCheckedEEPROM configEeprom;
""" + begin + "\n" + save + r"""
int main() {
    configEeprom.begin_result = false;
    if (saveCfg()) return 1;
    if (configStoreReady || configEeprom.begin_calls != 1 ||
        configEeprom.put_calls != 0 || configEeprom.commit_calls != 0) return 2;
    std::cout << "ESP8266_EEPROM_BEGIN_FAILURE_NO_WRITE_PASS\n";

    configEeprom.begin_result = true;
    configEeprom.commit_result = false;
    if (saveCfg()) return 3;
    if (configStoreReady || configEeprom.begin_calls != 2 ||
        configEeprom.put_calls != 1 || configEeprom.commit_calls != 1) return 4;
    std::cout << "ESP8266_EEPROM_COMMIT_FAILURE_PROPAGATED_PASS\n";

    configEeprom.commit_result = true;
    if (!saveCfg()) return 5;
    if (!configStoreReady || configEeprom.begin_calls != 3 ||
        configEeprom.put_calls != 2 || configEeprom.commit_calls != 2) return 6;
    if (!beginConfigStore() || configEeprom.begin_calls != 3) return 7;
    std::cout << "ESP8266_EEPROM_COMMIT_SUCCESS_AND_READY_REUSE_PASS\n";
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


