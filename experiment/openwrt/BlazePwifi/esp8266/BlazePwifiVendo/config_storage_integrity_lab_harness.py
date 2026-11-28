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


def _replace_fixture_marker(template: str, marker: str, replacement: str) -> str:
    if template.count(marker) != 1:
        raise AssertionError(
            f"runtime fixture marker must occur exactly once: {marker}"
        )
    return template.replace(marker, replacement, 1)


RUNTIME_FIXTURE_MARKERS = (
    "/* PHX_CONFIG_STRUCTS */",
    "/* PHX_CONFIG_CONSTANTS */",
    "/* PHX_CONFIG_HELPERS */",
    "/* PHX_CONFIG_RUNTIME_FUNCTIONS */",
)


def render_runtime_fixture(template: str, replacements) -> str:
    """Render required source fragments and reject every unresolved PHX marker."""
    for marker, replacement in replacements:
        template = _replace_fixture_marker(template, marker, replacement)
    if "PHX_CONFIG_" in template:
        raise AssertionError("unresolved runtime fixture template marker")
    return template


def expect_runtime_fixture_rejected(
    template: str,
    replacements,
    label: str,
    expected_error: str,
) -> None:
    """Require malformed templates to fail for the expected reason."""
    try:
        render_runtime_fixture(template, replacements)
    except AssertionError as exc:
        if expected_error not in str(exc):
            raise AssertionError(
                f"{label}: rejected for an unexpected reason: {exc}"
            ) from exc
        return
    raise AssertionError(f"{label}: unsafe runtime fixture template was accepted")


def loadcfg_runtime_harness(source: str) -> str:
    """Render the standalone C++ fixture with source-extracted firmware declarations."""
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
        extract_function(source, "bool beginConfigStore()"),
        extract_function(source, "bool saveCfg("),
        extract_function(source, "void loadCfg()"),
    ))
    template_path = Path(__file__).with_name("config_loadcfg_runtime_fixture.cpp.in")
    template = template_path.read_text(encoding="utf-8")
    replacements = (
        (RUNTIME_FIXTURE_MARKERS[0], structs),
        (RUNTIME_FIXTURE_MARKERS[1], constants),
        (RUNTIME_FIXTURE_MARKERS[2], helpers),
        (RUNTIME_FIXTURE_MARKERS[3], runtime_functions),
    )
    return render_runtime_fixture(template, replacements)



def compile_and_run_result(source: str, label: str):
    """Compile the extracted runtime path and return its exact process result."""
    with tempfile.TemporaryDirectory(prefix="phx-eeprom-network-") as directory:
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
                "network-gate harness compilation failed:\n" + (exc.stderr or exc.stdout)
            ) from exc
        return subprocess.run([str(binary)], capture_output=True, text=True)


def connectsta_runtime_harness(source: str) -> str:
    """Execute the real connectSta() body against deterministic fake network I/O."""
    connect_sta = extract_function(source, "void connectSta()")
    return r"""
#include <cstdint>
#include <cstdio>
#include <cstring>

static const int WL_CONNECTED = 3;
struct Config { char ssid[33]; char pass[65]; };
Config cfg{};
bool configStoreReady = false;
int wifiFailures = 7;
int post_calls = 0;
int deny_calls = 0;
uint32_t fake_millis = 0;

struct FakeWiFi {
    int state = WL_CONNECTED;
    int begin_calls = 0;
    void begin(const char *, const char *) { ++begin_calls; }
    int status() const { return state; }
} WiFi;

uint32_t millis() { return fake_millis; }
void delay(uint32_t value) { fake_millis += value; }
void yield() {}
int post(const char *action) {
    if (std::strcmp(action, "register") != 0) return -1;
    ++post_calls;
    return 0;
}
void denyRemoteControl() { ++deny_calls; }

@@CONNECT_STA@@

static void reset_case(bool ready, int wifi_state) {
    configStoreReady = ready;
    WiFi.state = wifi_state;
    WiFi.begin_calls = 0;
    post_calls = 0;
    deny_calls = 0;
    wifiFailures = 7;
    fake_millis = 0;
}

int main() {
    std::strcpy(cfg.ssid, "fixture-ssid");
    std::strcpy(cfg.pass, "fixture-pass");

    reset_case(false, WL_CONNECTED);
    std::puts("CONFIG_STORE_UNAVAILABLE_PRECONDITION_READY");
    connectSta();
    if (WiFi.begin_calls != 0 || post_calls != 0 || deny_calls != 0 ||
        wifiFailures != 7) return 10;
    std::puts("CONFIG_STORE_UNAVAILABLE_NETWORK_DENY_PASS");

    reset_case(true, WL_CONNECTED);
    cfg.ssid[0] = 0;
    std::puts("CONFIG_STORE_EMPTY_SSID_PRECONDITION_READY");
    connectSta();
    if (WiFi.begin_calls != 0 || post_calls != 0 || deny_calls != 0) return 11;
    std::puts("CONFIG_STORE_EMPTY_SSID_DENY_PASS");

    std::strcpy(cfg.ssid, "fixture-ssid");
    reset_case(true, 0);
    std::puts("CONFIG_STORE_READY_DISCONNECTED_PRECONDITION_READY");
    connectSta();
    if (WiFi.begin_calls != 1 || post_calls != 0 || deny_calls != 0 ||
        wifiFailures != 7 || fake_millis < 12000) return 20;
    std::puts("CONFIG_STORE_READY_DISCONNECTED_NO_REGISTER_PASS");

    reset_case(true, WL_CONNECTED);
    connectSta();
    if (WiFi.begin_calls != 1 || post_calls != 1 || deny_calls != 1 ||
        wifiFailures != 0) return 30;
    std::puts("CONFIG_STORE_READY_CONNECTED_REGISTER_PASS");
    return 0;
}
""".replace("@@CONNECT_STA@@", connect_sta)
