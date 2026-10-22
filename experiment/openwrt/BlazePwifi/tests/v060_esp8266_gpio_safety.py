#!/usr/bin/env python3
"""ESP8266 NodeMCU hardware coin/relay/LED GPIO fail-closed contract.

This is a host-side policy test, NOT evidence of actual electrical validation.
It deliberately checks the real .ino integration and compiles the same header
that the firmware uses, so a disconnected helper cannot create false GREEN.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKETCH = ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
HEADER = ROOT / "esp8266/BlazePwifiVendo/v060_esp8266_gpio_safety.h"
PORTABLE = r"""
#include "v060_esp8266_gpio_safety.h"
#include <cassert>
int main() {
    const int permitted[] = {4, 5, 12, 13, 14};
    for (int pin=0; pin<=16; ++pin) {
        bool allow=false;
        for (int good:permitted) if (pin==good) allow=true;
        assert(bp_esp8266_vendo_pin_supported(pin)==allow);
    }
    assert(!bp_esp8266_vendo_pin_supported(-1));
    assert(!bp_esp8266_vendo_pin_supported(255));
    assert(bp_esp8266_vendo_pins_safe(4,5,14));
    assert(bp_esp8266_vendo_pins_safe(13,12,14));
    assert(!bp_esp8266_vendo_pins_safe(0,5,14));  // boot strap
    assert(!bp_esp8266_vendo_pins_safe(2,5,14));  // boot strap/onboard LED
    assert(!bp_esp8266_vendo_pins_safe(4,15,14)); // boot strap
    assert(!bp_esp8266_vendo_pins_safe(4,6,14));  // SPI flash
    assert(!bp_esp8266_vendo_pins_safe(4,11,14)); // SPI flash
    assert(!bp_esp8266_vendo_pins_safe(16,5,14)); // special RTC GPIO
    assert(!bp_esp8266_vendo_pins_safe(1,5,14));  // UART TX
    assert(!bp_esp8266_vendo_pins_safe(3,5,14));  // UART RX
    assert(!bp_esp8266_vendo_pins_safe(4,4,14));
    assert(!bp_esp8266_vendo_pins_safe(4,5,4));
    assert(!bp_esp8266_vendo_pins_safe(4,5,5));
    assert(!bp_esp8266_vendo_pins_safe(14,14,14));
    assert(!bp_esp8266_vendo_pins_safe(255,5,14));
    // An unsafe stored EEPROM wiring verdict must remain sticky despite
    // individually allowed remote overrides; only local correction + reboot clears it.
    assert(bp_esp8266_vendo_remote_pins_safe(false,4,5,14));
    assert(!bp_esp8266_vendo_remote_pins_safe(true,4,5,14));
    assert(!bp_esp8266_vendo_remote_pins_safe(false,0,5,14));
    assert(!bp_esp8266_vendo_remote_pins_safe(false,4,4,14));
    return 0;
}
"""


class Esp8266PinSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SKETCH.read_text(encoding="utf-8")

    def test_real_firmware_uses_pin_guard_at_all_boundaries(self):
        text = self.src
        self.assertIn('#include "v060_esp8266_gpio_safety.h"', text)
        for fragment in (
            "bp_esp8266_vendo_pins_safe(coinPin,relayPin,ledPin)",
            "bp_esp8266_vendo_remote_pins_safe(bootPinsRejected,nextCoin,nextRelay,nextLed)",
            "bp_esp8266_vendo_pins_safe(cfg.coinPin,cfg.relayPin,cfg.insertLedPin)",
        ):
            self.assertIn(fragment, text, f"missing runtime GPIO guard: {fragment}")
        self.assertRegex(text, r"if\s*\(!bp_esp8266_vendo_pins_safe\(coinPin,relayPin,ledPin\)\)")
        self.assertIn('web.send(400,"text/plain","Unsafe ESP8266 GPIO selection', text)
        self.assertIn("controllerEnabled=false", text)
        self.assertIn("coinEnabled=false", text)
        self.assertIn("relayEnabled=false", text)
        self.assertIn("if(controllerEnabled && coinEnabled && relayEnabled && !bootPinsRejected && insertMode && fsReady", text)
        self.assertIn("runCoinPin=savedPinsSafe?cfg.coinPin:4", text)
        self.assertIn("runRelayPin=savedPinsSafe?cfg.relayPin:5", text)
        self.assertIn("runLedPin=savedPinsSafe?cfg.insertLedPin:14", text)
        # No externally supplied value may be directly copied to a GPIO field.
        for unsafe in ("cfg.coinPin=web.arg", "cfg.relayPin=web.arg", "cfg.insertLedPin=web.arg"):
            self.assertNotIn(unsafe, text)
        self.assertIn("writeLogical(runRelayPin,false,runRelayActiveHigh)", text)

    def test_unsafe_saved_pin_boot_cannot_be_reenabled_remotely(self):
        # The EEPROM verdict must survive a safe-looking server pin override.
        # Host source-contract test, not evidence of a real device latch.
        text = self.src
        self.assertIn("bool bootPinsRejected=false;", text)
        self.assertIn("bootPinsRejected=!savedPinsSafe;", text)
        remote = re.search(
            r"void applyRemoteConfig\(const String&r\)\{(.*?)\n\}",
            text, re.DOTALL,
        )
        self.assertIsNotNone(remote, "real remote-configuration function not found")
        self.assertIn(
            "bp_esp8266_vendo_remote_pins_safe(bootPinsRejected,nextCoin,nextRelay,nextLed)",
            remote.group(1),
            "valid remote GPIO must not override unsafe persisted boot wiring",
        )
        self.assertIn("bool accepting=controllerEnabled && coinEnabled && !bootPinsRejected", text)
        self.assertIn("if(controllerEnabled && coinEnabled && relayEnabled && !bootPinsRejected", text)
        self.assertEqual(text.count("bootPinsRejected="), 2,
                         "boot interlock must not silently clear during a poll")

    def test_output_latch_inactive_before_enabling_output_mode(self):
        # Source-order safety proof only, NOT an oscilloscope/relay-polarity test.
        match = re.search(
            r"void configureRuntimePins\([^)]*\)\s*\{(.*?)\n\}",
            self.src, re.DOTALL,
        )
        self.assertIsNotNone(match, "GPIO reconfiguration function not found")
        body = match.group(1)
        assigned = "runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;"
        self.assertIn(assigned, body)
        # Earlier deassertions may refer to OLD output pins and don't protect
        # NEW relay/LED GPIOs. Require preloading after pin assignment.
        configuring = body.split(assigned, 1)[1]
        for signal, polarity in (
            ("runRelayPin", "runRelayActiveHigh"),
            ("runLedPin", "runLedActiveHigh"),
        ):
            off = f"writeLogical({signal},false,{polarity})"
            output = f"pinMode({signal},OUTPUT)"
            self.assertIn(off, configuring)
            self.assertIn(output, configuring)
            self.assertLess(
                configuring.index(off), configuring.index(output),
                f"{signal}: inactive GPIO latch must be selected before OUTPUT",
            )

    def test_compiled_policy_blocks_boot_and_flash_gpios(self):
        self.assertTrue(HEADER.is_file(), "missing firmware-shipped safety header")
        with tempfile.TemporaryDirectory(prefix="blaze-esp8266-gpio-") as temp:
            src = Path(temp) / "policy.cpp"
            binary = Path(temp) / "policy"
            src.write_text(PORTABLE, encoding="utf-8")
            subprocess.run([
                "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-I", str(HEADER.parent), str(src), "-o", str(binary)
            ], check=True, capture_output=True, text=True)
            subprocess.run([str(binary)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
