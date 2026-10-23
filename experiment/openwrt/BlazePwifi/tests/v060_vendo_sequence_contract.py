from pathlib import Path
import subprocess
import tempfile

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
    restore = text.split("bool loadPending(){", 1)[1].split('Serial.println("Recovered unacknowledged coin event from flash.")', 1)[0]
    assert "if(!bp_pending_promote_recovered(LittleFS, chosen)) return false;" in restore, (
        f"{source.name}: startup must abort on restore rename/remove failure"
    )
    assert restore.index("bp_pending_promote_recovered(LittleFS, chosen)") < restore.index("pendingSequenceState=r;"), (
        f"{source.name}: do not mark event recovered before durable path promotion"
    )

assert "uint64_t sequence;" in HEADER
assert "s->sequence == s->acked_sequence + 1" in HEADER
assert "pulses < s->pulses" in HEADER
assert "bp_pending_sequence_commit" in HEADER and "bp_pending_sequence_abandon" in HEADER
# PAY-0783: the shared sequence header is a local Arduino library.
# Core package installation alone does not put it on either sketch's include path.
# Both board builds must compile the shipped sketch and local library copies.
WORKFLOW = (ROOT.parents[2] / ".github/workflows/blazepwifi-build.yml").read_text(encoding="utf-8")
for target, sketch, fqbn in (
    ("esp8266", "BlazePwifiVendo", "esp8266:esp8266:nodemcuv2"),
    ("esp32", "BlazePwifiVendo32", "esp32:esp32:esp32"),
):
    lines = [line.strip() for line in WORKFLOW.splitlines() if f"arduino-cli compile --fqbn {fqbn} " in line]
    assert len(lines) == 1, f"{fqbn}: expected exactly one compile command"
    source = f"experiment/openwrt/BlazePwifi/dist/{target}/source"
    assert f"--libraries {source}/libraries " in lines[0], f"{fqbn}: local sequence library missing from Arduino compile path"
    assert lines[0].endswith(f" {source}/{sketch}"), f"{fqbn}: shipped sketch missing from Arduino compile path"

# CTRL-RESTORE: exercise the production shared promotion helper with a fake
# LittleFS filesystem and injected remove / rename failures on the host.
with tempfile.TemporaryDirectory(prefix="blaze-vendo-recovery-") as tmp:
    exe = Path(tmp) / "pending-recovery"
    subprocess.run(
        ["c++", "-std=c++11", "-Wall", "-Wextra", "-Werror", "-O2",
         str(ROOT / "tests/v060_vendo_recovery_promote.cpp"), "-o", str(exe)],
        check=True,
    )
    subprocess.run([str(exe)], check=True)

print("Vendo sequence contract source checks passed")
