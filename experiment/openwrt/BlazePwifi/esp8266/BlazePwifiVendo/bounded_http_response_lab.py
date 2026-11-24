#!/usr/bin/env python3
"""Source-exact bounded HTTP response allocation guard for both ESP controllers.

Only known-length 2xx bodies at or below 1024 bytes may be materialized as a
String. Unknown/chunked, oversized and non-2xx responses are denied before
HTTPClient::getString(). This is host simulation, not hardware acceptance.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from firmware_lab_source import extract_function, mask_active_cpp_code

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

STUBS = r"""
#include <string>
#include <iostream>
using String = std::string;

class HTTPClient {
 public:
  HTTPClient(int size, const String &body) : size_(size), body_(body) {}
  int getSize() { return size_; }
  String getString() { ++getStringCalls; return body_; }
  int getStringCalls = 0;
 private:
  int size_;
  String body_;
};
"""

MAIN = r"""
int main() {
  const String boundary(1024, 'x');
  HTTPClient exact(1024, boundary);
  if (readBoundedControllerResponse(exact, 200) != boundary ||
      exact.getStringCalls != 1) return 61;

  HTTPClient created(13, "created");
  if (readBoundedControllerResponse(created, 201) != "created" ||
      created.getStringCalls != 1) return 62;

  HTTPClient empty(0, "");
  if (readBoundedControllerResponse(empty, 204) != "" ||
      empty.getStringCalls != 1) return 63;

  HTTPClient oversized(1025, String(1025, 'y'));
  if (readBoundedControllerResponse(oversized, 200) != "" ||
      oversized.getStringCalls != 0) return 64;

  HTTPClient unknown(-1, "chunked-or-unknown");
  if (readBoundedControllerResponse(unknown, 200) != "" ||
      unknown.getStringCalls != 0) return 65;

  HTTPClient serverError(512, "server error");
  if (readBoundedControllerResponse(serverError, 500) != "" ||
      serverError.getStringCalls != 0) return 66;

  HTTPClient redirect(512, "redirect");
  if (readBoundedControllerResponse(redirect, 302) != "" ||
      redirect.getStringCalls != 0) return 67;

  HTTPClient informational(512, "informational");
  if (readBoundedControllerResponse(informational, 199) != "" ||
      informational.getStringCalls != 0) return 68;

  std::cout << "BOUNDED_CONTROLLER_HTTP_RESPONSE_PASS allowed=3 denied=5\n";
  return 0;
}
"""


def compile_and_run(code, board, label):
    with tempfile.TemporaryDirectory(prefix="phx-http-bound-") as folder:
        cpp = Path(folder) / f"{label}.cpp"
        binary = Path(folder) / label
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30,
        )
        if built.returncode:
            raise RuntimeError(
                f"{board}: {label} compile failed:\n{built.stderr[-3000:]}"
            )
        return subprocess.run(
            [str(binary)], capture_output=True, text=True, timeout=10,
        )


def expect_mutation_rejected(code, board, label, expected_exit):
    result = compile_and_run(code, board, label)
    if result.returncode != expected_exit:
        raise AssertionError(
            f"{board}: {label} mutation expected exit {expected_exit}, "
            f"got {result.returncode}; stdout={result.stdout}; stderr={result.stderr}"
        )
    print(f"{board}: MUTATION_REJECTED {label} expected_exit={expected_exit}")


def verify():
    for board, path in BOARDS.items():
        source = path.read_text(encoding="utf-8")
        constant = re.search(
            r"static\s+const\s+int\s+MAX_CONTROLLER_RESPONSE_BYTES\s*=\s*1024\s*;",
            source,
        )
        if not constant:
            raise AssertionError(
                f"{board}: missing exact 1024-byte response bound"
            )

        helper = extract_function(source, "readBoundedControllerResponse")
        post = mask_active_cpp_code(extract_function(source, "post"))
        if post.count("readBoundedControllerResponse(h,code)") != 1:
            raise AssertionError(
                f"{board}: post() must call the bounded reader exactly once"
            )
        if "getString(" in post:
            raise AssertionError(
                f"{board}: post() must not read an unbounded body directly"
            )

        prefix = constant.group(0) + "\n" + helper + "\n"
        baseline = compile_and_run(STUBS + prefix + MAIN, board, "baseline")
        if baseline.returncode:
            raise AssertionError(
                f"{board}: bounded-response baseline failed "
                f"(exit={baseline.returncode}; stdout={baseline.stdout}; "
                f"stderr={baseline.stderr})"
            )

        mutations = (
            (
                "missing-size-limit",
                "responseBytes>MAX_CONTROLLER_RESPONSE_BYTES",
                "false",
                64,
            ),
            (
                "missing-unknown-length-deny",
                "responseBytes<0",
                "false",
                65,
            ),
            (
                "missing-status-deny",
                "statusCode<200 || statusCode>=300",
                "false",
                66,
            ),
        )
        for label, old, new, expected_exit in mutations:
            if helper.count(old) != 1:
                raise AssertionError(
                    f"{board}: expected one mutation anchor for {label}"
                )
            mutant = helper.replace(old, new, 1)
            expect_mutation_rejected(
                STUBS + prefix.replace(helper, mutant, 1) + MAIN,
                board,
                label,
                expected_exit,
            )

        print(
            f"{board}: BOUNDED_HTTP_RESPONSE_PASS "
            "allowed=3 denied=5 mutations=3/3"
        )

    print("BOUNDED_HTTP_RESPONSE_BOTH_BOARDS_PASS")


if __name__ == "__main__":
    verify()
