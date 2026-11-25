#!/usr/bin/env python3
"""Source-exact bounded HTTP response allocation guard for both ESP controllers.

Only known-length 2xx bodies at or below 1024 bytes with no Transfer-Encoding
header and exact Content-Length readback may be materialized as a String. Unknown/chunked, oversized and non-2xx
responses are denied before HTTPClient::getString(). This is host simulation,
not hardware acceptance.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import poll_response_failclosed_lab_structure_guard  # noqa: F401
from cpp_fixture_runner import run_cpp_fixture
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
  HTTPClient(int size, const String &body, bool transferEncoding = false)
      : size_(size), body_(body), transferEncoding_(transferEncoding) {}
  int getSize() { return size_; }
  bool hasHeader(const char *name) {
    ++hasHeaderCalls;
    return std::string(name) == "Transfer-Encoding" && transferEncoding_;
  }
  String getString() { ++getStringCalls; return body_; }
  int getStringCalls = 0;
  int hasHeaderCalls = 0;
 private:
  int size_;
  String body_;
  bool transferEncoding_;
};
"""

MAIN = r"""
int main() {
  const String boundary(1024, 'x');
  HTTPClient exact(1024, boundary);
  if (readBoundedControllerResponse(exact, 200) != boundary ||
      exact.getStringCalls != 1) return 61;

  HTTPClient created(7, "created");
  if (readBoundedControllerResponse(created, 201) != "created" ||
      created.getStringCalls != 1) return 62;

  HTTPClient empty(0, "");
  if (readBoundedControllerResponse(empty, 204) != "" ||
      empty.getStringCalls != 1) return 63;

  // A complete-looking JSON prefix is still incomplete when Content-Length
  // says more bytes were promised than HTTPClient actually returned.
  HTTPClient shortRead(12, R"({"ok":true})");
  if (readBoundedControllerResponse(shortRead, 200) != "" ||
      shortRead.getStringCalls != 1) return 71;

  HTTPClient overRead(10, R"({"ok":true})");
  if (readBoundedControllerResponse(overRead, 200) != "" ||
      overRead.getStringCalls != 1) return 72;

  // HTTPClient may still decode a chunked body when Content-Length is also
  // present. The declared size alone must never authorize getString().
  HTTPClient chunkedZero(0, "chunked-zero-body", true);
  if (readBoundedControllerResponse(chunkedZero, 200) != "" ||
      chunkedZero.getStringCalls != 0) return 69;

  HTTPClient chunkedSmall(1, "chunked-body-larger-than-one", true);
  if (readBoundedControllerResponse(chunkedSmall, 200) != "" ||
      chunkedSmall.getStringCalls != 0) return 70;

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

  std::cout << "BOUNDED_CONTROLLER_HTTP_RESPONSE_PASS allowed=3 denied=9\n";
  return 0;
}
"""


def compile_and_run(code, board, label):
    """Use the shared bounded runner; keep board/fixture context in failures."""
    return run_cpp_fixture(
        code,
        prefix="phx-http-bound-",
        stem=label,
        compile_timeout=30,
        run_timeout=10,
        context=f"{board}: {label}",
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
    sources = {
        board: path.read_text(encoding="utf-8")
        for board, path in BOARDS.items()
    }
    verify_board_parity(sources)
    verify_board_parity_mutations(sources)

    for board, path in BOARDS.items():
        source = sources[board]
        constant = re.search(
            r"static\s+const\s+int\s+MAX_CONTROLLER_RESPONSE_BYTES\s*=\s*1024\s*;",
            source,
        )
        if not constant:
            raise AssertionError(
                f"{board}: missing exact 1024-byte response bound"
            )

        helper = extract_function(source, "readBoundedControllerResponse")
        post_source = extract_function(source, "post")
        post = mask_active_cpp_code(post_source)
        if post.count("readBoundedControllerResponse(h,code)") != 1:
            raise AssertionError(
                f"{board}: post() must call the bounded reader exactly once"
            )
        if "getString(" in post:
            raise AssertionError(
                f"{board}: post() must not read an unbounded body directly"
            )
        compact_post = re.sub(r"\s+", "", post)
        compact_post_source = re.sub(r"\s+", "", post_source)
        collect_call = "h.collectHeaders(responseHeaders,1)"
        if (
            compact_post.count(collect_call) != 1
            or compact_post_source.count('constchar*responseHeaders[]={"Transfer-Encoding"};') != 1
            or compact_post.find(collect_call) > compact_post.find("h.POST(body)")
        ):
            raise AssertionError(
                f"{board}: Transfer-Encoding must be collected before POST"
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
                "((void)statusCode, false)",
                66,
            ),
            (
                "missing-transfer-encoding-deny",
                'h.hasHeader("Transfer-Encoding")',
                "false",
                69,
            ),
            (
                "missing-exact-content-length-readback",
                "if((int)body.length()!=responseBytes) return String();",
                "",
                71,
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
            "allowed=3 denied=9 mutations=5/5"
        )

    print("BOUNDED_HTTP_RESPONSE_BOTH_BOARDS_PASS")


if __name__ == "__main__":
    verify()
