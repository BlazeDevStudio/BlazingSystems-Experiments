#!/usr/bin/env python3
"""PHX-HARDWARE: execute actual board pin-capability predicates.

Host failure injection proves source policy only. It does not prove electrical
pin behavior, relay polarity, boot strapping, or physical hardware acceptance.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def source_function(source, name):
    match = re.search(r"\\bbool\\s+" + re.escape(name) + r"\\s*\\([^)]*\\)\\s*\\{", source)
    assert match, f"Missing production function {name}"
    depth = 0
    for pos in range(match.end() - 1, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():pos + 1]
    raise AssertionError(f"Unbalanced production function {name}")


failed = []
for chip, path in SOURCES.items():
    sketch = path.read_text(encoding="utf-8")
    helpers = "\n".join(source_function(sketch, name) for name in (
        "validInputPullupPin", "validOutputPin", "runtimePinsSafe"
    ))
    remote = sketch[sketch.index("void applyRemoteConfig"):sketch.index("String lastSentNonce")]
    outputs = sketch[sketch.index("void applyOutputs"):sketch.index("bool coinLineQuietAfterInhibit")]
    save = sketch[sketch.index('web.on("/save"'):sketch.index("web.begin()", sketch.index('web.on("/save"'))]
    setup = sketch[sketch.index("void setup(){"):sketch.index("void loop(){")]

    assert "pinConfigSafe=false" in remote
    assert remote.index("runtimePinsSafe") < remote.index("configureRuntimePins")
    assert "pinConfigSafe && controllerEnabled" in outputs
    assert save.index("runtimePinsSafe") < save.index("verifyWifi")
    assert "Settings were NOT saved" in save
    assert "using disabled safe defaults until corrected" in setup

    if chip == "ESP32":
        cases = [
            ("valid_defaults", (27, 26, 2), True),
            ("flash_coin", (6, 26, 2), False),
            ("input_only_coin", (34, 26, 2), False),
            ("input_only_relay", (27, 34, 2), False),
            ("nonexistent_gpio", (20, 26, 2), False),
            ("coin_relay_collision", (27, 27, 2), False),
            ("relay_led_collision", (27, 26, 26), False),
        ]
    else:
        cases = [
            ("valid_defaults", (4, 5, 14), True),
            ("flash_coin", (6, 5, 14), False),
            ("gpio16_no_pullup", (16, 5, 14), False),
            ("gpio16_output_ok", (4, 16, 14), True),
            ("coin_relay_collision", (4, 4, 14), False),
            ("relay_led_collision", (4, 5, 5), False),
        ]

    checks = []
    for label, pins, expected in cases:
        value = "true" if expected else "false"
        checks.append(
            f'  bool {label}=runtimePinsSafe({pins[0]},{pins[1]},{pins[2]})=={value};'
        )
    names = [label for label, _, _ in cases]
    print_expr = '<<" ".join([])'
    code = """#include <iostream>
""" + helpers + """
int main(){
""" + "\n".join(checks) + """
  std::cout""" + "".join(f'<<" {name}="<<{name}' for name in names) + '<<"\\n";\n' +            "  return (" + " && ".join(names) + ")?0:23;\n}\n"

    with tempfile.TemporaryDirectory(prefix="phx-hw-pin-guard-") as folder:
        cpp = Path(folder) / "test.cpp"
        binary = Path(folder) / "test"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30,
        )
        if built.returncode:
            print(chip, "COMPILE FAIL", built.stderr[-2400:])
            failed.append(chip)
            continue
        ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
        print(chip, "PASS" if ran.returncode == 0 else "FAIL", ran.stdout.strip())
        if ran.returncode:
            failed.append(chip)

if failed:
    sys.exit("PHX-HARDWARE pin capability guard failed: " + ",".join(failed))
print("PHX-HARDWARE: source-extracted pin capability guard PASS 2/2")
print("PHYSICAL_GPIO_VERIFIED=0")
print("FIRMWARE_FLASH_AUTHORIZED=0")
