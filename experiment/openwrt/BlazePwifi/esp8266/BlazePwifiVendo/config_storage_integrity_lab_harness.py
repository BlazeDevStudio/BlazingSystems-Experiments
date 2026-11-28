#!/usr/bin/env python3
"""Native C++ sanitizer harness for EEPROM configuration validation."""
from pathlib import Path
import re
import subprocess
import tempfile

from config_storage_integrity_lab_contract import extract_struct
from firmware_source_extract import extract_function, mask_non_code

def compile_and_run(source: str, label: str) -> str:
    with tempfile.TemporaryDirectory(prefix="phx-eeprom-config-") as directory:
        cpp = Path(directory) / f"{label}.cpp"
        binary = Path(directory) / label
        cpp.write_text(source, encoding="utf-8")
        try:
            subprocess.run(
                [
                    "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                    str(cpp), "-o", str(binary),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise AssertionError(
                "sanitizer harness compilation failed:\n" + (exc.stderr or exc.stdout)
            ) from exc
        result = subprocess.run(
            [str(binary)],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

def cxx_harness(source: str) -> str:
    structs = extract_struct(source, "ConfigV1") + "\n" + extract_struct(source, "Config")
    helpers = "\n".join((
        extract_function(source, "size_t boundedStringLength("),
        extract_function(source, "bool configStringsTerminated("),
        extract_function(source, "bool configV1StringsTerminated("),
    ))
    return r"""
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
""" + structs + "\n" + helpers + r"""

static void fillTerminated(char *value, size_t capacity) {
    std::memset(value, 'X', capacity);
    if (capacity) value[capacity - 1] = '\0';
}
static void fillUnterminated(char *value, size_t capacity) {
    std::memset(value, 'X', capacity);
}
int main() {
    char lastTerminated[8];
    char unterminated[8];
    char empty[8] = {};
    fillTerminated(lastTerminated, sizeof(lastTerminated));
    fillUnterminated(unterminated, sizeof(unterminated));
    if (boundedStringLength(lastTerminated, sizeof(lastTerminated)) != 7) return 1;
    if (boundedStringLength(unterminated, sizeof(unterminated)) != 8) return 2;
    if (boundedStringLength(empty, sizeof(empty)) != 0) return 3;

    Config current{};
    fillTerminated(current.ssid, sizeof(current.ssid));
    fillTerminated(current.pass, sizeof(current.pass));
    fillTerminated(current.server, sizeof(current.server));
    fillTerminated(current.key, sizeof(current.key));
    fillTerminated(current.id, sizeof(current.id));
    fillTerminated(current.apPass, sizeof(current.apPass));
    if (!configStringsTerminated(current)) return 4;
    struct Field { char *value; size_t capacity; };
    Field currentFields[] = {
        {current.ssid, sizeof(current.ssid)}, {current.pass, sizeof(current.pass)},
        {current.server, sizeof(current.server)}, {current.key, sizeof(current.key)},
        {current.id, sizeof(current.id)}, {current.apPass, sizeof(current.apPass)}
    };
    for (const auto &field : currentFields) {
        fillUnterminated(field.value, field.capacity);
        if (configStringsTerminated(current)) return 5;
        fillTerminated(field.value, field.capacity);
    }

    ConfigV1 legacy{};
    fillTerminated(legacy.ssid, sizeof(legacy.ssid));
    fillTerminated(legacy.pass, sizeof(legacy.pass));
    fillTerminated(legacy.server, sizeof(legacy.server));
    fillTerminated(legacy.key, sizeof(legacy.key));
    fillTerminated(legacy.id, sizeof(legacy.id));
    if (!configV1StringsTerminated(legacy)) return 6;
    Field legacyFields[] = {
        {legacy.ssid, sizeof(legacy.ssid)}, {legacy.pass, sizeof(legacy.pass)},
        {legacy.server, sizeof(legacy.server)}, {legacy.key, sizeof(legacy.key)},
        {legacy.id, sizeof(legacy.id)}
    };
    for (const auto &field : legacyFields) {
        fillUnterminated(field.value, field.capacity);
        if (configV1StringsTerminated(legacy)) return 7;
        fillTerminated(field.value, field.capacity);
    }
    std::cout << "EEPROM_CONFIG_BOUNDED_VALIDATION_PASS current=6/6 legacy=5/5\n";
    return 0;
}
"""



def _extract_uint32_constant(source: str, name: str) -> str:
    masked = mask_non_code(source)
    match = re.search(
        rf"\bconst\s+uint32_t\s+{re.escape(name)}\s*=\s*[^;]+;",
        masked,
    )
    if not match:
        raise AssertionError(f"missing uint32_t constant: {name}")
    return source[match.start():match.end()]


def loadcfg_runtime_harness(source: str) -> str:
    """Execute the extracted EEPROM loadCfg/default/migration path against durable fake EEPROM."""
    structs = extract_struct(source, "ConfigV1") + "\n" + extract_struct(source, "Config")
    constants = "\n".join((
        _extract_uint32_constant(source, "MAGIC_V1"),
        _extract_uint32_constant(source, "MAGIC"),
    ))
    helpers = "\n".join((
        extract_function(source, "size_t boundedStringLength("),
        extract_function(source, "bool configStringsTerminated("),
        extract_function(source, "bool configV1StringsTerminated("),
    ))
    runtime_functions = "\n".join((
        extract_function(source, "void defaults()"),
        extract_function(source, "bool saveCfg("),
        extract_function(source, "void loadCfg()"),
    ))
    return r"""
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
using std::memset;
using std::strcpy;
""" + structs + "\n" + constants + r"""

Config cfg{};

struct FakeSerial {
    std::string last;
    void println(const char *value) { last = value; }
};
FakeSerial Serial;

size_t strlcpy(char *destination, const char *source, size_t capacity) {
    const size_t length = std::strlen(source);
    if (capacity != 0) {
        const size_t copied = std::min(length, capacity - 1);
        std::memcpy(destination, source, copied);
        destination[copied] = '\0';
    }
    return length;
}

struct FakeEEPROM {
    unsigned char durable[sizeof(Config)]{};
    unsigned char staged[sizeof(Config)]{};
    bool commit_ok = true;
    int begin_calls = 0;
    int get_calls = 0;
    int put_calls = 0;
    int commit_calls = 0;

    void begin(size_t size) { (void)size; ++begin_calls; }

    template <typename T>
    void get(int address, T &value) {
        (void)address;
        ++get_calls;
        std::memcpy(&value, durable, sizeof(T));
    }

    template <typename T>
    void put(int address, const T &value) {
        (void)address;
        ++put_calls;
        std::memcpy(staged, &value, sizeof(T));
    }

    bool commit() {
        ++commit_calls;
        if (!commit_ok) return false;
        std::memcpy(durable, staged, sizeof(durable));
        return true;
    }

    template <typename T>
    void seed(const T &value) {
        std::memset(durable, 0, sizeof(durable));
        std::memcpy(durable, &value, sizeof(T));
        std::memcpy(staged, durable, sizeof(durable));
        commit_ok = true;
        begin_calls = get_calls = put_calls = commit_calls = 0;
    }

    void resetCounters() {
        begin_calls = get_calls = put_calls = commit_calls = 0;
    }

    template <typename T>
    void readDurable(T &value) const {
        std::memcpy(&value, durable, sizeof(T));
    }
};
FakeEEPROM EEPROM;

void makeSetupPassword() {
    strlcpy(cfg.apPass, "fixture-pass-12", sizeof(cfg.apPass));
}

""" + helpers + "\n" + runtime_functions + r"""

static void fillField(char *value, size_t capacity, const char *text) {
    std::memset(value, 0, capacity);
    strlcpy(value, text, capacity);
}

static Config makeCurrent() {
    Config value{};
    value.magic = MAGIC;
    fillField(value.ssid, sizeof(value.ssid), "current-ssid");
    fillField(value.pass, sizeof(value.pass), "current-pass");
    fillField(value.server, sizeof(value.server), "10.0.0.2");
    fillField(value.key, sizeof(value.key), "current-key");
    fillField(value.id, sizeof(value.id), "current-id");
    fillField(value.apPass, sizeof(value.apPass), "current-ap-pass");
    value.coinPin = 4;
    value.insertLedPin = 14;
    value.relayPin = 5;
    value.coinActiveLow = 1;
    return value;
}

static ConfigV1 makeLegacy() {
    ConfigV1 value{};
    value.magic = MAGIC_V1;
    fillField(value.ssid, sizeof(value.ssid), "legacy-ssid");
    fillField(value.pass, sizeof(value.pass), "legacy-pass");
    fillField(value.server, sizeof(value.server), "10.0.0.3");
    fillField(value.key, sizeof(value.key), "legacy-key");
    fillField(value.id, sizeof(value.id), "legacy-id");
    value.coinPin = 12;
    value.insertLedPin = 13;
    value.relayPin = 15;
    value.coinActiveLow = 0;
    return value;
}

static bool isDefaults() {
    return cfg.magic == MAGIC && cfg.ssid[0] == '\0' &&
           std::strcmp(cfg.server, "10.0.0.1") == 0 &&
           std::strcmp(cfg.id, "vendo-01") == 0 &&
           std::strcmp(cfg.apPass, "fixture-pass-12") == 0 &&
           cfg.coinPin == 4 && cfg.insertLedPin == 14 && cfg.relayPin == 5;
}

int main() {
    Config current = makeCurrent();
    EEPROM.seed(current);
    cfg = Config{};
    loadCfg();
    if (cfg.magic != MAGIC || std::strcmp(cfg.ssid, "current-ssid") != 0 ||
        std::strcmp(cfg.apPass, "current-ap-pass") != 0 ||
        EEPROM.put_calls != 0 || EEPROM.commit_calls != 0) return 1;
    std::cout << "EEPROM_LOADCFG_CURRENT_ACCEPT_PASS\n";

    struct CurrentField { char *value; size_t capacity; };
    for (int field = 0; field < 6; ++field) {
        current = makeCurrent();
        CurrentField fields[] = {
            {current.ssid, sizeof(current.ssid)},
            {current.pass, sizeof(current.pass)},
            {current.server, sizeof(current.server)},
            {current.key, sizeof(current.key)},
            {current.id, sizeof(current.id)},
            {current.apPass, sizeof(current.apPass)}
        };
        std::memset(fields[field].value, 'X', fields[field].capacity);
        EEPROM.seed(current);
        cfg = Config{};
        loadCfg();
        if (!isDefaults() || EEPROM.put_calls != 1 || EEPROM.commit_calls != 1) return 2;
    }
    std::cout << "EEPROM_LOADCFG_CURRENT_UNTERMINATED_REJECT_PASS fields=6/6\n";

    ConfigV1 legacy = makeLegacy();
    EEPROM.seed(legacy);
    cfg = Config{};
    Serial.last.clear();
    loadCfg();
    if (cfg.magic != MAGIC || std::strcmp(cfg.ssid, "legacy-ssid") != 0 ||
        std::strcmp(cfg.pass, "legacy-pass") != 0 ||
        std::strcmp(cfg.server, "10.0.0.3") != 0 ||
        std::strcmp(cfg.key, "legacy-key") != 0 ||
        std::strcmp(cfg.id, "legacy-id") != 0 ||
        std::strcmp(cfg.apPass, "fixture-pass-12") != 0 ||
        cfg.coinPin != 12 || cfg.insertLedPin != 13 || cfg.relayPin != 15 ||
        cfg.coinActiveLow != 0 || EEPROM.put_calls != 1 || EEPROM.commit_calls != 1 ||
        Serial.last != "Migrated BlazePwifi Vendo v1 configuration.") return 3;
    Config persisted{};
    EEPROM.readDurable(persisted);
    if (persisted.magic != MAGIC || std::strcmp(persisted.ssid, "legacy-ssid") != 0 ||
        std::strcmp(persisted.apPass, "fixture-pass-12") != 0) return 4;
    std::cout << "EEPROM_LOADCFG_LEGACY_MIGRATION_PASS\n";

    struct LegacyField { char *value; size_t capacity; };
    for (int field = 0; field < 5; ++field) {
        legacy = makeLegacy();
        LegacyField fields[] = {
            {legacy.ssid, sizeof(legacy.ssid)},
            {legacy.pass, sizeof(legacy.pass)},
            {legacy.server, sizeof(legacy.server)},
            {legacy.key, sizeof(legacy.key)},
            {legacy.id, sizeof(legacy.id)}
        };
        std::memset(fields[field].value, 'X', fields[field].capacity);
        EEPROM.seed(legacy);
        cfg = Config{};
        loadCfg();
        if (!isDefaults() || EEPROM.put_calls != 1 || EEPROM.commit_calls != 1) return 5;
    }
    std::cout << "EEPROM_LOADCFG_LEGACY_UNTERMINATED_REJECT_PASS fields=5/5\n";

    legacy = makeLegacy();
    EEPROM.seed(legacy);
    EEPROM.commit_ok = false;
    cfg = Config{};
    Serial.last.clear();
    loadCfg();
    ConfigV1 durableLegacy{};
    EEPROM.readDurable(durableLegacy);
    if (EEPROM.commit_calls != 1 || EEPROM.put_calls != 1 ||
        durableLegacy.magic != MAGIC_V1 ||
        std::strcmp(durableLegacy.ssid, "legacy-ssid") != 0 ||
        Serial.last != "CRITICAL: EEPROM configuration migration write failed; retrying on next boot.") return 6;
    EEPROM.commit_ok = true;
    EEPROM.resetCounters();
    cfg = Config{};
    Serial.last.clear();
    loadCfg();
    Config retried{};
    EEPROM.readDurable(retried);
    if (retried.magic != MAGIC || std::strcmp(retried.ssid, "legacy-ssid") != 0 ||
        EEPROM.commit_calls != 1 ||
        Serial.last != "Migrated BlazePwifi Vendo v1 configuration.") return 7;
    std::cout << "EEPROM_LOADCFG_MIGRATION_COMMIT_FAILURE_RETRY_PASS\n";

    current = makeCurrent();
    std::memset(current.ssid, 'X', sizeof(current.ssid));
    EEPROM.seed(current);
    EEPROM.commit_ok = false;
    cfg = Config{};
    Serial.last.clear();
    loadCfg();
    Config stillInvalid{};
    EEPROM.readDurable(stillInvalid);
    if (EEPROM.commit_calls != 1 || stillInvalid.magic != MAGIC ||
        stillInvalid.ssid[sizeof(stillInvalid.ssid) - 1] != 'X' ||
        Serial.last != "CRITICAL: EEPROM defaults write failed; setup remains available.") return 8;
    EEPROM.commit_ok = true;
    EEPROM.resetCounters();
    cfg = Config{};
    Serial.last.clear();
    loadCfg();
    Config repaired{};
    EEPROM.readDurable(repaired);
    if (!isDefaults() || repaired.magic != MAGIC || repaired.ssid[0] != '\0' ||
        EEPROM.commit_calls != 1) return 9;
    std::cout << "EEPROM_LOADCFG_DEFAULT_COMMIT_FAILURE_RETRY_PASS\n";

    std::cout << "EEPROM_LOADCFG_RUNTIME_PASS current=1/1 current_invalid=6/6 legacy=1/1 legacy_invalid=5/5 commit_retry=2/2\n";
    return 0;
}
"""
