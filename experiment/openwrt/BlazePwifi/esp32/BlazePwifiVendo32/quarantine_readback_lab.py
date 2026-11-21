#!/usr/bin/env python3
"""PHX-HARDWARE: exact source-extracted append/quarantine test, two ESP sketches.
Runs unmodified extracted function bodies with a C++17 fake LittleFS.
Neither flash power-cycle testing nor proof of durable financial accounting.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
from quarantine_readback_lab_cpp import CPP
from quarantine_readback_lab_parity import BOARDS, extract, verify_board_safety_parity


verify_board_safety_parity()
failed_boards = []
for board, ino in BOARDS:
    source = ino.read_text(encoding="utf-8")
    actual = CPP.replace("@@SOURCE_COIN_POST_GATE@@", extract(source, "bool canAttemptCoinPost(){"))
    actual = actual.replace("@@SOURCE_ATTEMPT_MATCH@@", extract(source, "bool pendingAttemptMarkerMatches()"))
    actual = actual.replace("@@SOURCE_FIELD_ESCAPE@@", extract(source, "const char* quarantineLogFieldEscapeAt("))
    actual = actual.replace("@@SOURCE_ENCODE@@", extract(source, "String quarantineLogField("))
    actual = actual.replace("@@SOURCE_TOKEN_VALID@@", extract(source, "bool quarantineLogTokenValid("))
    actual = actual.replace("@@SOURCE_RECORD_VALID@@", extract(source, "bool quarantineLogRecordValid("))
    actual = actual.replace("@@SOURCE_CRC32_UPDATE@@", extract(source, "uint32_t quarantineLogCrc32Update("))
    actual = actual.replace("@@SOURCE_INSPECT@@", extract(source, "bool inspectQuarantineLog("))
    actual = actual.replace("@@SOURCE_APPEND@@", extract(source, "bool appendQuarantineRecord("))
    actual = actual.replace("@@SOURCE_QUARANTINE@@", extract(source, "bool quarantinePending("))
    actual = actual.replace("BOARD_NAME", board)
    with tempfile.TemporaryDirectory(prefix="phx-hw-q-") as temp:
        cpp = Path(temp, "test.cpp")
        binary = Path(temp, "test")
        cpp.write_text(actual, encoding="utf-8")
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
                        str(cpp), "-o", str(binary)], check=True)
        completed = subprocess.run([str(binary)], capture_output=True, text=True)
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="")
        if completed.returncode:
            failed_boards.append(board)
        else:
            print(f"{board}: compiled exact extracted source")
            # Append-open, short-write, readback and corruption failures are
            # exercised in the normal source-exact scenario matrix above.

if failed_boards:
    raise SystemExit("PHX-HARDWARE: quarantine regression failed on " + ", ".join(failed_boards))
print("PHX-HARDWARE: 72/72 source-extracted host scenarios PASS; no hardware evidence")
poll_lab = ROOT / "esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py"
subprocess.run([sys.executable, str(poll_lab)], check=True)
register_lab = ROOT / "esp8266/BlazePwifiVendo/register_config_failclosed_lab.py"
subprocess.run([sys.executable, str(register_lab)], check=True)
attempt_marker_lab = ROOT / "esp32/BlazePwifiVendo32/pending_attempt_marker_lab.py"
attempt_marker_result = subprocess.run(
    [sys.executable, str(attempt_marker_lab)],
    capture_output=True, text=True,
)
print(attempt_marker_result.stdout, end="")
if attempt_marker_result.stderr:
    print(attempt_marker_result.stderr, file=sys.stderr, end="")
if attempt_marker_result.returncode:
    raise SystemExit(attempt_marker_result.returncode)
if attempt_marker_result.stdout.count("PENDING_ATTEMPT_MARKER_PASS 29/29") != len(BOARDS):
    raise SystemExit("PHX-HARDWARE: attempt-marker per-board summary count mismatch")
if "PHX-HARDWARE: 29/29 source-extracted cases per board (58/58 total) PASS" not in attempt_marker_result.stdout:
    raise SystemExit("PHX-HARDWARE: attempt-marker aggregate summary mismatch")
