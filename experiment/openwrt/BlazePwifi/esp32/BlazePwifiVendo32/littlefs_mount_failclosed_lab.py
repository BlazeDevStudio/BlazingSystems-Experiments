#!/usr/bin/env python3
"""Source-extracted host regression for fail-closed LittleFS mount failure.

Compiles the exact initPendingStore() bodies from both ESP sketches against a
fake LittleFS boundary. It proves mount failure does not request or call format,
does not load a pending journal, and leaves fsReady false. This is SIMULATED
host evidence only; it never accesses a physical filesystem or flash device.
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


def extract_function_body(source: str, signature: str, board: str) -> str:
    if source.count(signature) != 1:
        raise SystemExit(f"{board}: expected exactly one {signature!r}")
    start = source.index(signature)
    opening = source.find("{", start)
    if opening < 0:
        raise SystemExit(f"{board}: missing function body")

    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    index = opening
    while index < len(source):
        char = source[index]
        nxt = source[index + 1] if index + 1 < len(source) else ""

        if line_comment:
            if char == "\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 2
            else:
                index += 1
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char == "/" and nxt == "/":
            line_comment = True
            index += 2
            continue
        if char == "/" and nxt == "*":
            block_comment = True
            index += 2
            continue
        if char in ("'", '"'):
            quote = char
            index += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
        index += 1

    raise SystemExit(f"{board}: unterminated {signature!r}")


def harness(body: str) -> str:
    return textwrap.dedent("""
        #include <cassert>
        struct FakeLittleFS {
          bool mount_ok = false;
          bool last_format_on_fail = false;
          int begin_calls = 0;
          int format_calls = 0;
          bool begin(bool format_on_fail = false) {
            ++begin_calls;
            last_format_on_fail = format_on_fail;
            if (!mount_ok && format_on_fail) (void)format();
            return mount_ok;
          }
          bool format() {
            ++format_calls;
            mount_ok = true;
            return true;
          }
        } LittleFS;
        struct FakeSerial {
          void println(const char *) {}
        } Serial;
        bool fsReady = false;
        int load_pending_calls = 0;
        void loadPending() { ++load_pending_calls; }
        void initPendingStore() {
    """) + textwrap.indent(body, "  ") + textwrap.dedent("""
        }
        int main() {
          LittleFS.mount_ok = false;
          initPendingStore();
          assert(LittleFS.begin_calls == 1);
          assert(!LittleFS.last_format_on_fail);
          assert(LittleFS.format_calls == 0);
          assert(!fsReady);
          assert(load_pending_calls == 0);

          LittleFS.mount_ok = true;
          LittleFS.begin_calls = 0;
          LittleFS.last_format_on_fail = false;
          load_pending_calls = 0;
          initPendingStore();
          assert(LittleFS.begin_calls == 1);
          assert(!LittleFS.last_format_on_fail);
          assert(LittleFS.format_calls == 0);
          assert(fsReady);
          assert(load_pending_calls == 1);
          return 0;
        }
    """)


def compile_and_run(board: str, body: str, temp: Path, suffix: str) -> bool:
    source = temp / f"{board.lower()}_{suffix}.cpp"
    binary = temp / f"{board.lower()}_{suffix}"
    source.write_text(harness(body), encoding="utf-8")
    built = subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)],
        capture_output=True,
        text=True,
    )
    if built.returncode:
        if suffix.startswith("mutation"):
            return False
        raise SystemExit(f"{board}: compile failed:\n{built.stderr}")
    ran = subprocess.run([str(binary)], capture_output=True, text=True)
    return ran.returncode == 0


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="phx-littlefs-mount-") as directory:
        temp = Path(directory)
        for board, path in SOURCES.items():
            if not path.is_file():
                raise SystemExit(f"{board}: missing source {path}")
            source = path.read_text(encoding="utf-8")
            body = extract_function_body(source, "void initPendingStore()", board)
            if not compile_and_run(board, body, temp, "actual"):
                raise SystemExit(f"{board}: actual mount policy failed")

            begin_mutation = body.replace("LittleFS.begin()", "LittleFS.begin(true)", 1)
            if begin_mutation == body or compile_and_run(board, begin_mutation, temp, "mutation_begin_true"):
                raise SystemExit(f"{board}: begin(true) mutation was not rejected")

            format_mutation = body.replace(
                "fsReady=LittleFS.begin();",
                "fsReady=LittleFS.begin();\n  if(!fsReady) LittleFS.format();",
                1,
            )
            if format_mutation == body or compile_and_run(board, format_mutation, temp, "mutation_explicit_format"):
                raise SystemExit(f"{board}: explicit format mutation was not rejected")

            print(f"{board}: mount failure preserved; success loaded pending; 2 format mutations rejected")

    print("LITTLEFS_MOUNT_FAILCLOSED_LAB=PASS (SIMULATED; no physical flash touched)")


if __name__ == "__main__":
    main()
