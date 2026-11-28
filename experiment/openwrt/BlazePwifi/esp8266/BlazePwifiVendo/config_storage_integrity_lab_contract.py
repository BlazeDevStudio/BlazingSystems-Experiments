#!/usr/bin/env python3
"""Source-level contract checks for fixed-size ESP8266 EEPROM configuration."""
from pathlib import Path
import re

from firmware_source_extract import extract_braced, extract_function, mask_non_code

BLAZEPWIFI = Path(__file__).resolve().parents[2]
SKETCH = BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"

CONFIG_FIELDS = ("ssid", "pass", "server", "key", "id", "apPass")
LEGACY_FIELDS = ("ssid", "pass", "server", "key", "id")

def extract_struct(source: str, name: str) -> str:
    masked = mask_non_code(source)
    match = re.search(rf"\bstruct\s+{re.escape(name)}\s*\{{", masked)
    if not match:
        raise AssertionError(f"missing struct {name}")
    opening = masked.find("{", match.start())
    block = extract_braced(source, opening)
    return source[match.start():opening + len(block)] + ";"
def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
def assert_source_contract(source: str) -> None:
    masked_source = mask_non_code(source)
    legacy_struct_at = masked_source.find("struct LegacyPendingRecord")
    bounded_helper_at = masked_source.find("size_t boundedStringLength(")
    require(0 <= legacy_struct_at < bounded_helper_at,
            "LegacyPendingRecord must precede helper definitions for Arduino prototype generation")
    config = mask_non_code(extract_struct(source, "Config"))
    legacy = mask_non_code(extract_struct(source, "ConfigV1"))
    for field in CONFIG_FIELDS:
        require(
            re.search(rf"\bchar\s+{field}\s*\[", config) is not None,
            f"Config fixed-size field missing: {field}",
        )
    for field in LEGACY_FIELDS:
        require(
            re.search(rf"\bchar\s+{field}\s*\[", legacy) is not None,
            f"ConfigV1 fixed-size field missing: {field}",
        )

    length_fn_source = extract_function(source, "size_t boundedStringLength(")
    length_fn = mask_non_code(length_fn_source)
    require("if(!value) return capacity;" in length_fn, "bounded length must reject a null pointer")
    require(
        re.search(r"for\s*\(\s*size_t\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*capacity\s*;", length_fn) is not None,
        "bounded length must stop at the supplied capacity",
    )
    require("return capacity;" in length_fn, "unterminated input must return the capacity sentinel")
    require("strlen(" not in length_fn, "bounded length must not call unbounded strlen")
    require(r"value[i]=='\0'" in length_fn_source, "bounded length must stop at the first NUL byte")

    config_validator = mask_non_code(extract_function(source, "bool configStringsTerminated("))
    legacy_validator = mask_non_code(extract_function(source, "bool configV1StringsTerminated("))
    for field in CONFIG_FIELDS:
        token = rf"boundedStringLength\s*\(\s*value\.{field}\s*,\s*sizeof\s*\(\s*value\.{field}\s*\)\s*\)\s*<\s*sizeof\s*\(\s*value\.{field}\s*\)"
        require(re.search(token, config_validator) is not None,
                f"Config validator does not bound-check {field}")
    for field in LEGACY_FIELDS:
        token = rf"boundedStringLength\s*\(\s*value\.{field}\s*,\s*sizeof\s*\(\s*value\.{field}\s*\)\s*\)\s*<\s*sizeof\s*\(\s*value\.{field}\s*\)"
        require(re.search(token, legacy_validator) is not None,
                f"ConfigV1 validator does not bound-check {field}")

    load = mask_non_code(extract_function(source, "void loadCfg()"))
    write_result_checks = re.findall(r"if\s*\(\s*!\s*saveCfg\s*\(\s*\)\s*\)", load)
    require(len(write_result_checks) == 2,
            "loadCfg must check both migration and defaults persistence results")
    current_guard = re.search(
        r"if\s*\(\s*cfg\.magic\s*==\s*MAGIC\s*&&\s*configStringsTerminated\s*\(\s*cfg\s*\)\s*&&\s*"
        r"boundedStringLength\s*\(\s*cfg\.apPass\s*,\s*sizeof\s*\(\s*cfg\.apPass\s*\)\s*\)\s*>=\s*8\s*\)\s*return\s*;",
        load,
    )
    require(current_guard is not None,
            "current EEPROM config must be fully bounded-validated before acceptance")
    legacy_guard = re.search(
        r"if\s*\(\s*oldCfg\.magic\s*==\s*MAGIC_V1\s*&&\s*configV1StringsTerminated\s*\(\s*oldCfg\s*\)\s*\)",
        load,
    )
    require(legacy_guard is not None,
            "legacy EEPROM config must be bounded-validated before migration")
    first_copy = load.find("strlcpy(")
    require(legacy_guard.start() < first_copy,
            "legacy string copies must remain after the bounded validation guard")
    require("strlen(" not in load,
            "loadCfg must not use unbounded strlen on raw EEPROM bytes")

    store_ready = re.search(r"\bbool\s+configStoreReady\s*=\s*false\s*;", masked_source)
    require(store_ready is not None, "EEPROM readiness state must default to denied")
    checked_class_match = re.search(
        r"\bclass\s+CheckedEEPROMClass\s*:\s*public\s+EEPROMClass\s*\{",
        masked_source,
    )
    require(checked_class_match is not None,
            "ESP8266 EEPROM wrapper must expose a checked begin path")
    checked_open = masked_source.find("{", checked_class_match.start())
    checked_class = mask_non_code(extract_braced(source, checked_open))
    require("new (std::nothrow) uint8_t[aligned]" in checked_class,
            "EEPROM allocation must be checked without throwing")
    require("if(!_data)" in checked_class and "_size=aligned;" in checked_class,
            "EEPROM buffer and size must be validated before access")
    require("if(!ESP.flashRead(address,_data,_size))" in checked_class,
            "EEPROM flash read failure must be reported")
    require("delete[] _data;" in checked_class and "_data=nullptr;" in checked_class,
            "failed EEPROM initialization must release and clear the buffer")
    require("CheckedEEPROMClass configEeprom;" in masked_source,
            "firmware must use the checked EEPROM instance")

    begin_fn = mask_non_code(extract_function(source, "bool beginConfigStore()"))
    require("if(configStoreReady) return true;" in begin_fn,
            "EEPROM begin helper must reuse a confirmed ready state")
    require("configStoreReady=configEeprom.beginChecked(sizeof(Config));" in begin_fn and
            "return configStoreReady;" in begin_fn,
            "EEPROM checked begin result must be retained and returned")

    save = mask_non_code(extract_function(source, "bool saveCfg()"))
    save_begin = save.find("if(!beginConfigStore()) return false;")
    save_put = save.find("configEeprom.put(0,cfg);")
    save_commit = save.find("if(!configEeprom.commit()){")
    save_deny = save.find("configStoreReady=false;", save_commit)
    require(0 <= save_begin < save_put < save_commit < save_deny,
            "saveCfg must initialize storage before writing and invalidate readiness on commit failure")

    load = mask_non_code(extract_function(source, "void loadCfg()"))
    load_begin = load.find("if(!beginConfigStore()){")
    load_defaults = load.find("defaults();", load_begin)
    load_return = load.find("return;", load_defaults)
    first_read = load.find("configEeprom.get(")
    require(0 <= load_begin < load_defaults < load_return < first_read,
            "loadCfg must default and return before any EEPROM read when begin fails")
    require("EEPROM.begin(" not in load,
            "loadCfg must use the checked begin helper, not an unchecked direct begin")
    require(re.search(r"\\bEEPROM\\s*\\.\\s*(?:begin|get|put|commit)\\s*\\(", masked_source) is None,
            "firmware must not bypass the checked EEPROM wrapper")

    outputs = mask_non_code(extract_function(source, "void applyOutputs()"))
    require("bool accepting=configStoreReady && controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady;" in outputs,
            "relay/LED admission must remain denied when EEPROM is unavailable")

    connect = mask_non_code(extract_function(source, "void connectSta()"))
    connect_guard = connect.find("if(!configStoreReady || !strlen(cfg.ssid)) return;")
    connect_wifi = connect.find("WiFi.begin(")
    require(0 <= connect_guard < connect_wifi,
            "connectSta must not use config loaded from an unavailable EEPROM store")

    loop = mask_non_code(extract_function(source, "void loop()"))
    require(re.search(
        r"WiFi\.status\(\)!=WL_CONNECTED\s*&&\s*configStoreReady\s*&&\s*strlen\(cfg\.ssid\)",
        loop,
    ) is not None, "automatic reconnect must require a valid EEPROM store")
    require(re.search(
        r"WiFi\.status\(\)==WL_CONNECTED\s*&&\s*configStoreReady\s*&&\s*millis\(\)-lastPoll>1500",
        loop,
    ) is not None, "poll POST must require a valid EEPROM store")

def expect_rejected(label: str, mutated: str) -> None:
    try:
        assert_source_contract(mutated)
    except AssertionError:
        print(f"EEPROM_CONFIG_MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe config-validation mutation accepted: {label}")
def move_helpers_before_legacy_struct(source: str) -> str:
    match = re.search(
        r"size_t boundedStringLength[\s\S]*?bool configV1StringsTerminated[\s\S]*?\r?\n}\r?\n",
        source,
    )
    if not match:
        raise AssertionError("bounded helper block missing for ordering mutation")
    block = match.group(0)
    without = source[:match.start()] + source[match.end():]
    at = without.find("struct LegacyPendingRecord")
    if at < 0:
        raise AssertionError("LegacyPendingRecord mutation anchor missing")
    return without[:at] + block + without[at:]
