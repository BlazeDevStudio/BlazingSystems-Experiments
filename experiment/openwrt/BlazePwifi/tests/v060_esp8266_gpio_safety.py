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
            "bp_esp8266_vendo_pins_safe(nextCoin,nextRelay,nextLed)",
            "bp_esp8266_vendo_pins_safe(cfg.coinPin,cfg.relayPin,cfg.insertLedPin)",
        ):
            self.assertIn(fragment, text, f"missing runtime GPIO guard: {fragment}")
        self.assertRegex(text, r"if\s*\(!bp_esp8266_vendo_pins_safe\(coinPin,relayPin,ledPin\)\)")
        self.assertIn('web.send(400,"text/plain","Unsafe ESP8266 GPIO selection', text)
        self.assertIn("controllerEnabled=false", text)
        self.assertIn("coinEnabled=false", text)
        self.assertIn("relayEnabled=false", text)
        # The same guarded predicate now controls the relay and coin intake.
        self.assertIn("if(bp_esp8266_coin_can_accept(", text)
        self.assertIn("active && !lastCoin && millis()-lastEdge>runDebounceMs", text)
        self.assertIn("runCoinPin=savedPinsSafe?cfg.coinPin:4", text)
        self.assertIn("runRelayPin=savedPinsSafe?cfg.relayPin:5", text)
        self.assertIn("runLedPin=savedPinsSafe?cfg.insertLedPin:14", text)
        # No externally supplied value may be directly copied to a GPIO field.
        for unsafe in ("cfg.coinPin=web.arg", "cfg.relayPin=web.arg", "cfg.insertLedPin=web.arg"):
            self.assertNotIn(unsafe, text)
        self.assertIn("writeLogical(runRelayPin,false,runRelayActiveHigh)", text)

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

    def test_energized_relay_requires_creditable_coin_target_and_capacity(self):
        # P0 source-boundary regression; no relay board or coin hardware here.
        # Coin intake already checks target/cap, but the OUTPUT relay previously
        # did not, so an acceptor could swallow a coin that cannot be journaled.
        text = self.src
        self.assertIn('#include "v060_esp8266_coin_acceptance.h"', text)
        match = re.search(r"void applyOutputs\(\)\s*\{(.*?)\n\}", text, re.DOTALL)
        self.assertIsNotNone(match, "physical relay update not found")
        body = match.group(1)
        self.assertIn("bp_esp8266_coin_can_accept(", body)
        for required in ("bp_pending_sequence_hex_token(activeTarget.c_str(),8,32)", "pendingTarget==activeTarget",
                         "pendingPulses", "relayEnabled"):
            self.assertIn(required, body, f"relay accepts without {required}")
        # Before the next loop iteration or HTTP poll, shut the relay on the
        # twentieth stored pulse. This cannot prove physical switching delay.
        loop = text.split("void loop()", 1)[1]
        self.assertIn("bp_pending_sequence_hex_token(activeTarget.c_str(),8,32)", loop,
                      "coin intake must refuse the same malformed target as its flash journal")
        stored = loop.split("pendingPulses++;", 1)[1].split("lastCoin=active;", 1)[0]
        self.assertIn("applyOutputs();", stored, "relay cutoff cannot wait for the next poll")

    def test_coin_relay_compiled_truth_table(self):
        # Verify the EXACT standalone predicate included by the shipped .ino.
        header = HEADER.parent / "v060_esp8266_coin_acceptance.h"
        self.assertTrue(header.is_file(), "missing firmware-linked relay accounting gate")
        code = r"""
#include "v060_esp8266_coin_acceptance.h"
#include "v060_pending_sequence.h"
#include <cassert>
int main() {
    auto can = [](bool controller, bool coin, bool relay, bool window,
                  bool disk, bool queued, bool target, bool same, unsigned count) {
        return bp_esp8266_coin_can_accept(controller,coin,relay,window,disk,
                                           queued,target,same,count);
    };
    assert(can(true,true,true,true,true,false,
               bp_pending_sequence_hex_token("deadbeef",8,32),true,0));
    assert(!can(true,true,true,true,true,false,
                bp_pending_sequence_hex_token("bad-token",8,32),true,0));
    assert(!can(true,true,true,true,true,false,
                bp_pending_sequence_hex_token("xyz",8,32),true,0));
    assert(can(true,true,true,true,true,false,true,true,0));
    assert(can(true,true,true,true,true,false,true,true,1));
    assert(can(true,true,true,true,true,false,true,true,19));
    assert(!can(true,true,true,true,true,false,true,true,20)); // cannot save more
    assert(!can(true,true,true,true,true,false,true,true,21));
    assert(!can(true,true,true,true,true,false,false,true,0)); // no target nonce
    assert(!can(true,true,true,true,true,false,false,false,3));
    assert(!can(true,true,true,true,true,false,true,false,3)); // changed target
    assert(!can(true,true,true,true,true,true,true,true,1));   // replay pending
    assert(!can(true,true,true,true,false,false,true,true,0)); // flash unavailable
    assert(!can(true,true,true,false,true,false,true,true,0)); // window expired
    assert(!can(true,true,false,true,true,false,true,true,0));
    assert(!can(true,false,true,true,true,false,true,true,0));
    assert(!can(false,true,true,true,true,false,true,true,0));
}
"""
        with tempfile.TemporaryDirectory(prefix="blaze-esp8266-relay-") as temp:
            src = Path(temp) / "relay.cpp"
            binary = Path(temp) / "relay"
            src.write_text(code, encoding="utf-8")
            subprocess.run(["g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
                            "-pedantic", "-I", str(header.parent),
                            "-I", str(ROOT / "esp/libraries/BlazePendingSequence/src"), str(src),
                            "-o", str(binary)], check=True, capture_output=True, text=True)
            subprocess.run([str(binary)], check=True, capture_output=True, text=True)

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
