#!/usr/bin/env python3
"""Source-extracted denial test for the ESP quarantine-clear HTTP handler.

This is a host simulation of the exact handler body, not a physical-device test.
It verifies that repeated unauthenticated POSTs return 403 and never delete the
quarantine evidence, whether the log currently exists or not.
"""
from pathlib import Path
import subprocess
import tempfile
import textwrap

PROJECT = Path(__file__).resolve().parents[2]
SOURCES = {
    "ESP32": PROJECT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
    "ESP8266": PROJECT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
}
MARKER = 'web.on("/quarantine/clear",HTTP_POST,[](){'

def extract_handler(source: str, board: str) -> str:
    if source.count(MARKER) != 1:
        raise SystemExit(f"{board}: expected exactly one POST /quarantine/clear route")
    start = source.index(MARKER)
    opening = source.index("{", start)
    depth = 0
    quote = None
    escaped = False
    closing = -1
    for index in range(opening, len(source)):
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
                closing = index
                break
    if closing < 0:
        raise SystemExit(f"{board}: unterminated quarantine-clear handler")
    terminator = source.find(");", closing)
    if terminator < 0:
        raise SystemExit(f"{board}: missing route terminator")
    route = source[start:terminator + 2]
    if "HTTP_POST" not in route:
        raise SystemExit(f"{board}: route is not POST-only")
    return source[opening + 1:closing]

def compile_and_run(board: str, body: str, temp: Path) -> None:
    cpp = textwrap.dedent("""
        #include <cassert>
        #include <string>
        struct FakeWeb {
          int status = 0;
          std::string content_type;
          std::string response;
          void send(int code, const char *type, const char *body) {
            status = code;
            content_type = type;
            response = body;
          }
        };
        struct FakeLittleFS {
          bool present = true;
          int remove_calls = 0;
          bool exists(const char *) const { return present; }
          bool remove(const char *) {
            ++remove_calls;
            present = false;
            return true;
          }
        };
        FakeWeb web;
        FakeLittleFS LittleFS;
        bool fsReady = true;
        int main() {
          auto handler = []() {
    """) + textwrap.indent(body, "    ") + textwrap.dedent("""
          };
          for (int present = 0; present <= 1; ++present) {
            LittleFS.present = (present == 1);
            LittleFS.remove_calls = 0;
            for (int attempt = 0; attempt < 3; ++attempt) {
              web.status = 0;
              handler();
              assert(web.status == 403);
              assert(web.content_type == "text/plain");
              assert(web.response.find("authenticated reconciliation") != std::string::npos);
              assert(LittleFS.remove_calls == 0);
              assert(LittleFS.present == (present == 1));
            }
          }
          return 0;
        }
    """)
    source = temp / f"{board.lower()}_quarantine_clear.cpp"
    binary = temp / f"{board.lower()}_quarantine_clear"
    source.write_text(cpp, encoding="utf-8")
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary)], check=True)
    print(f"{board}: 6 repeated POST attempts denied; quarantine file unchanged")

def main() -> None:
    with tempfile.TemporaryDirectory(prefix="phx-quarantine-clear-") as directory:
        temp = Path(directory)
        for board, path in SOURCES.items():
            if not path.is_file():
                raise SystemExit(f"{board}: missing source {path}")
            source = path.read_text(encoding="utf-8")
            body = extract_handler(source, board)
            compile_and_run(board, body, temp)
    print("QUARANTINE_CLEAR_DENY_LAB=PASS (SIMULATED; no physical filesystem touched)")

if __name__ == "__main__":
    main()
