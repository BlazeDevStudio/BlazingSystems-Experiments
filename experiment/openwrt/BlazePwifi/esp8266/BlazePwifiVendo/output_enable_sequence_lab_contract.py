"""Source-contract and mutation helpers for startup GPIO OFF sequencing."""
from pathlib import Path
import re

from firmware_source_extract import extract_function

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
)

def verify_shared_extractor_contract() -> None:
    """Ensure non-code decoys cannot shadow a real production definition."""
    fixture = r'''
// void configureRuntimePins(int pin) { unsafe(); }
const char *quoted = "void configureRuntimePins(int pin) { unsafe(); }";
const char *raw = R"phx(void configureRuntimePins(int pin) { unsafe(); })phx";
void configureRuntimePins(int pin) { pinMode(pin, OUTPUT); }
'''
    extracted = extract_function(fixture, "void configureRuntimePins")
    expected = "void configureRuntimePins(int pin) { pinMode(pin, OUTPUT); }"
    if extracted.strip() != expected:
        raise RuntimeError(
            "shared C/C++ extractor selected a comment/string decoy or lost the definition"
        )
    print("SOURCE_EXTRACTOR_PASS comments, quoted strings and raw strings ignored")

def unsafe_mutation(configure: str) -> str:
    # Remove only the two new-pin preloads; retain old-pin shutdown and the
    # post-enable OFF confirmation so the regression isolates the latch race.
    pattern = (
        r"(runCoinPin=coinPin;\s*runRelayPin=relayPin;\s*runLedPin=ledPin;)\s*"
        r"(?://[^\n]*\n\s*)?"
        r"writeLogical\(runRelayPin,false,runRelayActiveHigh\);\s*"
        r"writeLogical\(runLedPin,false,runLedActiveHigh\);"
    )
    mutated, count = re.subn(pattern, r"\1", configure, count=1)
    if count != 1:
        raise RuntimeError("could not inject missing pre-output OFF latch mutation")
    return mutated


def active_write_mutation(configure: str, anchor: str, statement: str) -> str:
    """Inject an active-level write at a precise startup boundary."""
    if anchor not in configure:
        raise RuntimeError(f"active-write mutation anchor missing: {anchor}")
    return configure.replace(anchor, anchor + "\n  " + statement, 1)


def polarity_coupling_mutation(configure: str, target_pin: str, correct_polarity: str, wrong_polarity: str) -> str:
    """Make one output incorrectly borrow the other output's polarity setting."""
    expected = f"writeLogical({target_pin},false,{correct_polarity});"
    replacement = f"writeLogical({target_pin},false,{wrong_polarity});"
    mutated, count = re.subn(re.escape(expected), replacement, configure)
    if count != 3:
        raise RuntimeError(
            f"expected exactly three OFF writes for {target_pin} (old-pin shutdown, preload, confirmation), found {count}"
        )
    return mutated
