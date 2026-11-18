#!/usr/bin/env python3
"""Source-extracted regression for fail-closed pending-journal removal.

Compiles the production clearPending()/quarantinePending() bodies from both
ESP sketches against a failure-injectable fake LittleFS. SIMULATED only.
"""
from pathlib import Path
import subprocess
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)


def extract_function(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise SystemExit(f"expected exactly one production function {signature!r}")
    start = source.index(signature)
    brace = source.find("{", start)
    if brace < 0:
        raise SystemExit(f"missing function body for {signature!r}")
    depth = 0
    quote = None
    escaped = False
    for index in range(brace, len(source)):
        char = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise SystemExit(f"unterminated function {signature!r}")


def compile_and_run(board: str, clear_fn: str, quarantine_fn: str, temp: Path) -> None:
    cpp = textwrap.dedent(r"""
        #include <cassert>
        #include <cstdint>
        #include <cstdlib>
        #include <iostream>
        #include <set>
        #include <string>

        using String = std::string;

        bool outputsOn = true;
        struct FakeLittleFS {
          std::set<std::string> files;
          std::string failPath;
          int failMode = 0; // 1: return false/keep; 2: return true/keep; 3: delete/return false
          int removeCalls = 0;
          bool sawOutputsOnAtAccess = false;
          bool exists(const char *path) {
            if (outputsOn) sawOutputsOnAtAccess = true;
            return files.count(path) != 0;
          }
          bool remove(const char *path) {
            if (outputsOn) sawOutputsOnAtAccess = true;
            ++removeCalls;
            const std::string key(path);
            if (key == failPath) {
              if (failMode == 2) return true;
              if (failMode == 3) { files.erase(key); return false; }
              return false;
            }
            return files.erase(key) != 0;
          }
        } LittleFS;

        bool fsReady = true;
        uint8_t pendingPulses = 5;
        bool pendingReady = false;
        String pendingNonce = "nonce-1234567890";
        String pendingTarget = "target-1234567890";
        uint32_t lastSend = 900;
        bool controllerEnabled = true;
        bool coinEnabled = true;
        bool relayEnabled = true;
        bool insertMode = true;
        bool appendOk = true;

        struct FakeSerial {
          template<class T> void println(const T &) {}
        } Serial;

        void applyOutputs() {
          outputsOn = controllerEnabled && coinEnabled && relayEnabled &&
                      insertMode && fsReady && !pendingReady;
        }
        bool appendQuarantineRecord(const String &) { return appendOk; }

        @@CLEAR_FUNCTION@@

        @@QUARANTINE_FUNCTION@@

        static void reset() {
          LittleFS = FakeLittleFS{};
          LittleFS.files.insert("/pending.dat");
          LittleFS.files.insert("/pending.new");
          LittleFS.files.insert("/pending.bak");
          fsReady = true;
          pendingPulses = 5;
          pendingReady = false;
          pendingNonce = "nonce-1234567890";
          pendingTarget = "target-1234567890";
          lastSend = 900;
          controllerEnabled = coinEnabled = relayEnabled = insertMode = true;
          outputsOn = true;
          appendOk = true;
        }

        static void expectHeld(const char *scenario) {
          if (LittleFS.sawOutputsOnAtAccess || pendingPulses != 5 || !pendingReady ||
              pendingNonce != "nonce-1234567890" ||
              pendingTarget != "target-1234567890" || outputsOn) {
            std::cerr << "FAIL " << scenario << ": outputs were ON during filesystem access or pending state was cleared\n";
            std::exit(1);
          }
        }

        static void expectCleared(const char *scenario) {
          if (LittleFS.sawOutputsOnAtAccess || pendingPulses != 0 || pendingReady || !pendingNonce.empty() ||
              !pendingTarget.empty() || lastSend != 0 ||
              LittleFS.exists("/pending.dat") ||
              LittleFS.exists("/pending.new") ||
              LittleFS.exists("/pending.bak")) {
            std::cerr << "FAIL " << scenario << ": successful clear left state behind\n";
            std::exit(1);
          }
        }

        int main() {
          reset();
          LittleFS.failPath = "/pending.dat";
          LittleFS.failMode = 1;
          if (clearPending()) return 10;
          expectHeld("dat remove failure");

          reset();
          LittleFS.failPath = "/pending.new";
          LittleFS.failMode = 1;
          if (clearPending()) return 11;
          if (LittleFS.exists("/pending.dat") || !LittleFS.exists("/pending.new"))
            return 12;
          expectHeld("new remove failure after dat removal");

          reset();
          LittleFS.failPath = "/pending.bak";
          LittleFS.failMode = 1;
          if (clearPending()) return 13;
          if (LittleFS.exists("/pending.dat") || LittleFS.exists("/pending.new") ||
              !LittleFS.exists("/pending.bak")) return 14;
          expectHeld("bak remove failure after earlier removals");

          reset();
          LittleFS.failPath = "/pending.dat";
          LittleFS.failMode = 2;
          if (clearPending()) return 15;
          if (!LittleFS.exists("/pending.dat")) return 16;
          expectHeld("remove returned true but candidate remained");

          reset();
          LittleFS.failPath = "/pending.dat";
          LittleFS.failMode = 3;
          if (clearPending()) return 17;
          if (LittleFS.exists("/pending.dat")) return 18;
          expectHeld("ambiguous false return after deletion");

          reset();
          fsReady = false;
          if (clearPending()) return 19;
          if (LittleFS.removeCalls != 0) return 20;
          expectHeld("filesystem unavailable");

          reset();
          if (!clearPending()) return 21;
          expectCleared("all candidate removals verified");

          reset();
          LittleFS.files.clear();
          if (!clearPending()) return 22;
          expectCleared("all candidates already absent");

          reset();
          LittleFS.failPath = "/pending.new";
          LittleFS.failMode = 1;
          if (quarantinePending("window expired")) return 23;
          expectHeld("quarantine append committed but pending removal failed");

          reset();
          appendOk = false;
          if (quarantinePending("window expired")) return 24;
          if (LittleFS.removeCalls != 0) return 25;
          expectHeld("quarantine append failure");

          reset();
          if (!quarantinePending("window expired")) return 26;
          expectCleared("quarantine append and pending cleanup succeed");

          std::cout << "PENDING_CLEAR_REMOVE_READBACK=PASS 11/11; SIMULATED ONLY\n";
          return 0;
        }
    """)
    cpp = cpp.replace("@@CLEAR_FUNCTION@@", clear_fn)
    cpp = cpp.replace("@@QUARANTINE_FUNCTION@@", quarantine_fn)
    source_file = temp / f"{board.lower()}_pending_clear.cpp"
    binary = temp / f"{board.lower()}_pending_clear"
    source_file.write_text(cpp, encoding="utf-8")
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(source_file), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary)], check=True)
    print(f"{board}: pending removal failures retained RAM state and denied outputs")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="phx-pending-clear-") as directory:
        temp = Path(directory)
        for board, path in BOARDS:
            if not path.is_file():
                raise SystemExit(f"{board}: missing sketch {path}")
            source = path.read_text(encoding="utf-8")
            clear_fn = extract_function(source, "bool clearPending")
            quarantine_fn = extract_function(source, "bool quarantinePending")
            compile_and_run(board, clear_fn, quarantine_fn, temp)
    print("PENDING_CLEAR_REMOVE_READBACK=PASS (SIMULATED; no physical filesystem touched)")


if __name__ == "__main__":
    main()
