#!/usr/bin/env python3
"""Bounded validation for fixed-size ESP8266 EEPROM configuration strings."""
from pathlib import Path
import re
import subprocess
import tempfile

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


def expect_rejected(label: str, mutated: str) -> None:
    try:
        assert_source_contract(mutated)
    except AssertionError:
        print(f"EEPROM_CONFIG_MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe config-validation mutation accepted: {label}")



def move_helpers_before_legacy_struct(source: str) -> str:
    match = re.search(
        r"size_t boundedStringLength[\\s\\S]*?bool configV1StringsTerminated[\\s\\S]*?\\r?\\n}\\r?\\n",
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
        source.replace(r"value[i]=='\0'", r"value[i]=='X'", 1),
    )
    expect_rejected(
        "unbounded-ap-password-length",
        source.replace(
            "boundedStringLength(cfg.apPass,sizeof(cfg.apPass))",
            "strlen(cfg.apPass)",
            1,
        ),
    )

    with tempfile.TemporaryDirectory(prefix="phx-eeprom-config-") as directory:
        cpp = Path(directory) / "config_integrity.cpp"
        binary = Path(directory) / "config_integrity"
        cpp.write_text(cxx_harness(source), encoding="utf-8")
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
        print(result.stdout.strip())
    print("EEPROM_CONFIG_SOURCE_CONTRACT_PASS")
    print("EEPROM_CONFIG_FAILURE_INJECTION_PASS 3/3")


if __name__ == "__main__":
    main()
