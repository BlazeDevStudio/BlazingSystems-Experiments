#!/usr/bin/env python3
"""Source-linked regression for single-line ESP quarantine evidence."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
]


def extract_function(text: str, signature: str) -> str:
    start = text.index(signature)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise AssertionError(f"unterminated {signature}")


sources = [path.read_text(encoding="utf-8") for path in SOURCES]
helpers = [
    extract_function(source, "String quarantineLogField(")
    for source in sources
]
assert helpers[0] == helpers[1], "ESP quarantine encoders diverged"

for source in sources:
    append = extract_function(source, "bool appendQuarantineRecord(")
    for token in (
        "quarantineLogField(pendingNonce,40)",
        "quarantineLogField(pendingTarget,80)",
        "quarantineLogField(reason,128)",
        "logNonce.c_str()",
        "logTarget.c_str()",
        "logReason.c_str()",
    ):
        assert token in append, f"missing encoded quarantine field use: {token}"
    assert "pendingTarget.c_str(), reason.c_str()" not in append

cpp = r'''
#include <cassert>
#include <cstddef>
#include <iostream>
#include <string>

class String {
 public:
  std::string value;
  String() = default;
  String(const char *text): value(text) {}
  explicit String(std::string text): value(std::move(text)) {}
  size_t length() const { return value.length(); }
  void reserve(size_t size) { value.reserve(size); }
  char operator[](size_t index) const { return value[index]; }
  String &operator+=(const char *text) { value += text; return *this; }
  String &operator+=(char c) { value += c; return *this; }
  void remove(size_t index) { value.erase(index); }
};
''' + helpers[0] + r'''

static void assertSingleLine(const String &value, size_t maximum) {
  assert(value.length() <= maximum);
  assert(value.value.find('\r') == std::string::npos);
  assert(value.value.find('\n') == std::string::npos);
  assert(value.value.find('\t') == std::string::npos);
}

int main() {
  String plain = quarantineLogField(String("plain text"), 40);
  assert(plain.value == "plain text");
  assertSingleLine(plain, 40);

  String hostile(std::string("A\nB\rC\tD\\E"));
  String encoded = quarantineLogField(hostile, 80);
  assert(encoded.value == "A\\nB\\rC\\tD\\\\E");
  assertSingleLine(encoded, 80);

  std::string controls("x");
  controls.push_back('\x01');
  controls += "y";
  controls.push_back('\x7f');
  String replaced = quarantineLogField(String(controls), 40);
  assert(replaced.value == "x?y?");
  assertSingleLine(replaced, 40);

  String longValue(std::string(30, 'X'));
  String bounded = quarantineLogField(longValue, 12);
  assert(bounded.value == "XXXXXXXXX...");
  assertSingleLine(bounded, 12);

  String tight = quarantineLogField(String("ab\ncd"), 4);
  assert(tight.value == "a...");
  assertSingleLine(tight, 4);

  String zero = quarantineLogField(String("hidden"), 0);
  assert(zero.value.empty());

  std::cout << "QUARANTINE_LOG_ENCODING_PASS 6/6 exact helper cases\n";
  return 0;
}
'''

with tempfile.TemporaryDirectory(prefix="phx-quarantine-log-") as tmp:
    source = Path(tmp) / "quarantine_log.cpp"
    binary = Path(tmp) / "quarantine_log"
    source.write_text(cpp, encoding="utf-8")
    subprocess.run(
        [
            "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
            "-fsanitize=address,undefined", str(source), "-o", str(binary),
        ],
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print("PHX-HARDWARE: quarantine log encoding PASS 6 cases x2 sketches")
