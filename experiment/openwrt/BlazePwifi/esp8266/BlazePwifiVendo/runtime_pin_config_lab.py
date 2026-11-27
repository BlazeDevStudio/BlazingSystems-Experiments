#!/usr/bin/env python3
"""Board-aware GPIO role validation for both deny-only Vendo sketches.

Host-only source extraction and failure injection. This does not probe physical
GPIO levels, board straps, relay contacts, or wiring.
"""
from pathlib import Path
import subprocess
import tempfile

from firmware_source_extract import extract_braced, extract_function, mask_non_code

ROOT = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_source_contract(board: str, source: str) -> tuple[str, str]:
    masked_source = mask_non_code(source)
    legacy_at = masked_source.find("struct LegacyPendingRecord")
    parse_at = masked_source.find("bool parseGpioNumber(")
    require(0 <= legacy_at < parse_at,
            f"{board}: LegacyPendingRecord must precede helpers for Arduino prototype generation")
    parse_fn = extract_function(source, "bool parseGpioNumber(")
    valid_fn = extract_function(source, "bool validRuntimePins(")
    parse_code = mask_non_code(parse_fn)
    valid_code = mask_non_code(valid_fn)

    require("if(!text || !*text) return false;" in parse_code,
            f"{board}: numeric GPIO parser must reject an empty value")
    require("if(*cursor<'0'||*cursor>'9') return false;" in parse_fn,
            f"{board}: numeric GPIO parser must reject non-decimal characters")
    require("value=parsed;" in parse_code, f"{board}: parsed GPIO result is not returned")

    for token in (
        "coinPin!=relayPin",
        "coinPin!=ledPin",
        "relayPin!=ledPin",
        "coinPin>=6&&coinPin<=11",
        "relayPin>=6&&relayPin<=11",
        "ledPin>=6&&ledPin<=11",
    ):
        require(token in valid_code, f"{board}: runtime GPIO validator missing {token!r}")

    if board == "ESP8266":
        require("coinPin>16" in valid_code and "relayPin>16" in valid_code and "ledPin>16" in valid_code,
                "ESP8266: GPIO range must remain 0..16")
        strap_guard = "coinPin==0||coinPin==2||coinPin==15||relayPin==0||relayPin==2||relayPin==15||ledPin==0||ledPin==2||ledPin==15"
        require(strap_guard in valid_code,
                "ESP8266: ROM boot-strap GPIO0/GPIO2/GPIO15 must not be assigned to runtime roles")
        require("coinPin==16" in valid_code,
                "ESP8266: coin GPIO16 must be rejected because INPUT_PULLUP is unavailable")
        configure = mask_non_code(extract_function(source, "void configureRuntimePins("))
        require("pinMode(runCoinPin,INPUT_PULLUP)" in "".join(configure.split()),
                "ESP8266: coin-input pull-up assumption changed; revisit GPIO16 capability guard")
        coin_max, output_max = 16, 16
        defaults = ("cfg.coinPin=4;", "cfg.insertLedPin=14;", "cfg.relayPin=5;")
    else:
        require("coinPin>33" in valid_code and "relayPin>33" in valid_code and "ledPin>33" in valid_code,
                "ESP32: GPIO roles must use pull-up-capable/output-capable GPIO 0..33")
        strap_guard = "coinPin==0||coinPin==2||coinPin==5||coinPin==12||coinPin==15||relayPin==0||relayPin==2||relayPin==5||relayPin==12||relayPin==15||ledPin==0||ledPin==5||ledPin==12||ledPin==15"
        require(strap_guard in "".join(valid_code.split()),
                "ESP32: strapping pins must be excluded from coin/relay and non-default LED roles")
        coin_max, output_max = 33, 33
        defaults = ("cfg.coinPin=27;", "cfg.insertLedPin=2;", "cfg.relayPin=26;")

    setup = mask_non_code(extract_function(source, "void setup()"))
    setup_guard = setup.find("if(!validRuntimePins(cfg.coinPin,cfg.relayPin,cfg.insertLedPin))")
    configure_at = setup.find("configureRuntimePins(")
    require(0 <= setup_guard < configure_at,
            f"{board}: persisted GPIO config must be checked before any output pin setup")
    fallback = setup[setup_guard:configure_at]
    for token in defaults:
        require(token in fallback, f"{board}: invalid stored GPIO config lacks safe default {token!r}")
    if board == "ESP32":
        require("configStoreValid=false;" in fallback,
                "ESP32: invalid stored GPIO config must keep station/poll disabled")

    portal = extract_function(source, "void setupPortal()")
    save_marker = 'web.on("/save",HTTP_POST,[](){'
    save_at = portal.find(save_marker)
    require(save_at >= 0, f"{board}: setup save handler missing")
    save_open = portal.find("{", save_at)
    save_raw = extract_braced(portal, save_open)
    save_block = mask_non_code(save_raw)
    parse_calls = (
        f'parseGpioNumber(web.arg("coin").c_str(),{coin_max},coinPin)',
        f'parseGpioNumber(web.arg("led").c_str(),{output_max},ledPin)',
        f'parseGpioNumber(web.arg("relay").c_str(),{output_max},relayPin)',
    )
    for call in parse_calls:
        require(call in save_raw, f"{board}: setup save handler missing {call!r}")
    require(save_block.count("parseGpioNumber(") >= 3,
            f"{board}: GPIO parser calls must be executable code")
    role_guard = save_block.find("validRuntimePins(coinPin,relayPin,ledPin)")
    invalid_response = save_block.find("web.send(400,")
    invalid_return = save_block.find("return;", invalid_response)
    wifi_verify = save_block.find("verifyWifi(")
    persist = max(save_block.find("saveCfg()"), save_block.find("saveConfig()"))
    require(0 <= role_guard < invalid_response < invalid_return < wifi_verify < persist,
            f"{board}: invalid GPIO must return before Wi-Fi side effects and persistence")
    for field in ("coin", "led", "relay"):
        require(f'web.arg("{field}").toInt()' not in save_raw,
                f"{board}: pin {field} still uses permissive toInt parsing")
    for token in ("cfg.coinPin=coinPin;", "cfg.insertLedPin=ledPin;", "cfg.relayPin=relayPin;"):
        require(token in save_block, f"{board}: validated local GPIO value is not persisted: {token}")
    return parse_fn, valid_fn


def harness(parse_fn: str, valid_fn: str, board: str) -> str:
    if board == "ESP8266":
        cases = r"""
    if (!validRuntimePins(4,5,14)) return 10;
    if (validRuntimePins(4,4,14)) return 11;
    if (validRuntimePins(4,5,5)) return 12;
    if (validRuntimePins(4,14,14)) return 13;
    if (validRuntimePins(6,5,14) || validRuntimePins(4,11,14) || validRuntimePins(4,5,10)) return 14;
    if (validRuntimePins(-1,5,14) || validRuntimePins(4,17,14) || validRuntimePins(4,5,17)) return 15;
    if (validRuntimePins(0,5,14) || validRuntimePins(2,5,14) || validRuntimePins(15,5,14)) return 17;
    if (validRuntimePins(4,0,14) || validRuntimePins(4,2,14) || validRuntimePins(4,15,14)) return 18;
    if (validRuntimePins(4,5,0) || validRuntimePins(4,5,2) || validRuntimePins(4,5,15)) return 19;
    if (validRuntimePins(16,5,14)) return 20;
    if (!validRuntimePins(4,16,14)) return 21;
    if (!validRuntimePins(4,5,16)) return 22;
"""
    else:
        cases = r"""
    if (!validRuntimePins(27,26,2)) return 10;
    if (validRuntimePins(27,27,2)) return 11;
    if (validRuntimePins(27,26,26)) return 12;
    if (validRuntimePins(2,26,2)) return 13;
    if (validRuntimePins(6,26,2) || validRuntimePins(27,11,2) || validRuntimePins(27,26,10)) return 14;
    if (validRuntimePins(-1,26,2) || validRuntimePins(34,26,2) || validRuntimePins(27,34,2) || validRuntimePins(27,26,39)) return 15;
    if (validRuntimePins(0,26,33) || validRuntimePins(2,26,33) || validRuntimePins(5,26,33) || validRuntimePins(12,26,33) || validRuntimePins(15,26,33)) return 17;
    if (validRuntimePins(27,0,33) || validRuntimePins(27,2,33) || validRuntimePins(27,5,33) || validRuntimePins(27,12,33) || validRuntimePins(27,15,33)) return 18;
    if (validRuntimePins(27,26,0) || validRuntimePins(27,26,5) || validRuntimePins(27,26,12) || validRuntimePins(27,26,15)) return 19;
"""
    return r"""
#include <iostream>
""" + parse_fn + "\n" + valid_fn + r"""
int main() {
    int value=-1;
    if (!parseGpioNumber("0", 16, value) || value!=0) return 1;
    if (!parseGpioNumber("16", 16, value) || value!=16) return 2;
    if (parseGpioNumber("", 16, value)) return 3;
    if (parseGpioNumber("-1", 16, value)) return 4;
    if (parseGpioNumber("1x", 16, value)) return 5;
    if (parseGpioNumber("0/", 16, value)) return 6;
    if (parseGpioNumber("17", 16, value)) return 7;
    if (parseGpioNumber("999999999999999999999999", 16, value)) return 8;
    int unchanged=77;
    if (parseGpioNumber("999999999999999999999999", 16, unchanged) || unchanged!=77) return 16;
    if (!parseGpioNumber("33", 33, value) || value!=33) return 9;
""" + cases + r"""
    std::cout << "RUNTIME_GPIO_CONFIG_PASS """ + board + r"""\\n";
    return 0;
}
"""


def compile_and_run(code: str, expect_success: bool, label: str) -> None:
    with tempfile.TemporaryDirectory(prefix="phx-runtime-gpio-") as directory:
        cpp = Path(directory) / "runtime_gpio.cpp"
        binary = Path(directory) / "runtime_gpio"
        cpp.write_text(code, encoding="utf-8")
        compiled = subprocess.run(
            ["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
             "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
             str(cpp), "-o", str(binary)],
            text=True, capture_output=True,
        )
        if compiled.returncode:
            raise AssertionError(f"{label}: compile failed:\\n{compiled.stdout}{compiled.stderr}")
        result = subprocess.run([str(binary)], text=True, capture_output=True)
        if expect_success and result.returncode:
            raise AssertionError(f"{label}: failed ({result.returncode}): {result.stdout}{result.stderr}")
        if not expect_success and result.returncode == 0:
            raise AssertionError(f"{label}: unsafe mutation survived")


def expect_rejected(parse_fn: str, valid_fn: str, board: str, label: str, mutated: str) -> None:
    code = harness(parse_fn, mutated, board)
    compile_and_run(code, False, f"{board} {label}")
    print(f"RUNTIME_GPIO_MUTATION_REJECTED {board} {label}")


def verify_board(board: str, path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    parse_fn, valid_fn = assert_source_contract(board, source)

    save_marker = 'web.on("/save",HTTP_POST,[](){'
    save_at = source.find(save_marker)
    save_open = source.find("{", save_at)
    save_raw = extract_braced(source, save_open)
    missing_invalid_return = save_raw.replace("return;", "", 1)
    require(missing_invalid_return != save_raw,
            f"{board}: invalid-GPIO early-return mutation anchor missing")
    mutated_source = source.replace(save_raw, missing_invalid_return, 1)
    try:
        assert_source_contract(board, mutated_source)
    except AssertionError:
        print(f"RUNTIME_GPIO_MUTATION_REJECTED {board} invalid-config-return-removed")
    else:
        raise AssertionError(f"{board}: invalid GPIO handler can fall through into Wi-Fi/persistence")

    compile_and_run(harness(parse_fn, valid_fn, board), True, f"{board} runtime GPIO policy")
    print(f"RUNTIME_GPIO_POLICY_PASS {board}")

    duplicate_mutation = valid_fn.replace("coinPin!=relayPin && ", "", 1)
    require(duplicate_mutation != valid_fn, f"{board}: duplicate-pin mutation anchor missing")
    expect_rejected(parse_fn, valid_fn, board, "duplicate-role-guard-removed", duplicate_mutation)

    flash_mutation = valid_fn.replace(
        "if((coinPin>=6&&coinPin<=11)||(relayPin>=6&&relayPin<=11)||(ledPin>=6&&ledPin<=11)) return false;",
        "",
        1,
    )
    require(flash_mutation != valid_fn, f"{board}: flash-pin mutation anchor missing")
    expect_rejected(parse_fn, valid_fn, board, "flash-pin-guard-removed", flash_mutation)

    if board == "ESP8266":
        strap_guard = "if(coinPin==0||coinPin==2||coinPin==15||relayPin==0||relayPin==2||relayPin==15||ledPin==0||ledPin==2||ledPin==15) return false;"
        strap_mutation = valid_fn.replace(strap_guard, "", 1)
        require(strap_mutation != valid_fn, "ESP8266: boot-strap mutation anchor missing")
        expect_rejected(parse_fn, valid_fn, board, "boot-strap-guard-removed", strap_mutation)
        pullup_mutation = valid_fn.replace("if(coinPin==16) return false;", "", 1)
        require(pullup_mutation != valid_fn, "ESP8266: GPIO16 INPUT_PULLUP mutation anchor missing")
        expect_rejected(parse_fn, valid_fn, board, "GPIO16-INPUT_PULLUP-guard-removed", pullup_mutation)
        print("RUNTIME_GPIO_CAPABILITY_PASS ESP8266 coin16=DENY relay16=ALLOW led16=ALLOW")

    digit_mutation = parse_fn.replace("if(*cursor<'0'||*cursor>'9') return false;", "if(false) return false;", 1)
    require(digit_mutation != parse_fn, f"{board}: digit-parser mutation anchor missing")
    compile_and_run(harness(digit_mutation, valid_fn, board), False, f"{board} nonnumeric-parser mutation")

    overflow_guard = "if(parsed>maximum/10 || (parsed==maximum/10 && digit>maximum%10)) return false;"
    overflow_mutation = parse_fn.replace(overflow_guard, "if(false && maximum<0) return false;", 1)
    require(overflow_mutation != parse_fn, f"{board}: decimal-overflow mutation anchor missing")
    compile_and_run(harness(overflow_mutation, valid_fn, board), False, f"{board} decimal-overflow mutation")
    print(f"RUNTIME_GPIO_MUTATION_REJECTED {board} decimal-overflow-guard-removed")

    if board == "ESP32":
        strap_guard = (
            "  if(coinPin==0||coinPin==2||coinPin==5||coinPin==12||coinPin==15||\n"
            "     relayPin==0||relayPin==2||relayPin==5||relayPin==12||relayPin==15||\n"
            "     ledPin==0||ledPin==5||ledPin==12||ledPin==15) return false;\n"
        )
        strap_mutation = valid_fn.replace(strap_guard, "", 1)
        require(strap_mutation != valid_fn, "ESP32: boot-strap mutation anchor missing")
        expect_rejected(parse_fn, valid_fn, board, "boot-strap-guard-removed", strap_mutation)
        output_mutation = valid_fn.replace("relayPin>33", "relayPin>39", 1)
        require(output_mutation != valid_fn, "ESP32: output-capability mutation anchor missing")
        expect_rejected(parse_fn, valid_fn, board, "input-only-relay-guard-removed", output_mutation)

    print(f"RUNTIME_GPIO_FAILURE_INJECTION_PASS {board}")


def main() -> None:
    for board, path in SKETCHES.items():
        if not path.is_file():
            raise SystemExit(f"missing sketch: {path}")
        verify_board(board, path)
    print("RUNTIME_GPIO_CONFIG_SIMULATED_ONLY=1")
    print("PHYSICAL_GPIO_OR_RELAY_ACCEPTANCE=0")


if __name__ == "__main__":
    main()
