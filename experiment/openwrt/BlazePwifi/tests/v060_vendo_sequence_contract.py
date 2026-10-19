from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h").read_text(encoding="utf-8")
FIRMWARE = [
    ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
]

for source in FIRMWARE:
    text = source.read_text(encoding="utf-8")
    assert "#include <v060_pending_sequence.h>" in text
    assert "BpPendingSequence pendingSequenceState;" in text
    assert "bp_pending_sequence_reserve" in text
    assert "bp_pending_sequence_commit" in text
    assert "bp_pending_sequence_abandon" in text
    assert "pendingReady=r.sequence!=0" in text or "pendingReady=r.sequence!=0;" in text
    assert "if(any) return false;" in text, f"{source.name}: corrupt persisted state must halt startup"
    assert "LittleFS.format()" not in text and "LittleFS.begin(true)" not in text
    assert "clearPending(true)" in text and "clearPending(false)" in text

assert "uint64_t sequence;" in HEADER
assert "s->sequence == s->acked_sequence + 1" in HEADER
assert "pulses < s->pulses" in HEADER
assert "bp_pending_sequence_commit" in HEADER and "bp_pending_sequence_abandon" in HEADER
# PAY-0783: the shared sequence header is a local Arduino library.
# Core package installation alone does not put it on either sketch's include path.
# Both board builds must explicitly admit the checked-in library directory.
WORKFLOW = (ROOT.parents[2] / ".github/workflows/blazepwifi-build.yml").read_text(encoding="utf-8")
for fqbn in ("esp8266:esp8266:nodemcuv2", "esp32:esp32:esp32"):
    lines = [line.strip() for line in WORKFLOW.splitlines() if f"arduino-cli compile --fqbn {fqbn} " in line]
    assert len(lines) == 1, f"{fqbn}: expected exactly one compile command"
    assert "--libraries experiment/openwrt/BlazePwifi/esp/libraries " in lines[0], f"{fqbn}: local sequence library missing from Arduino compile path"

print("Vendo sequence contract source checks passed")
