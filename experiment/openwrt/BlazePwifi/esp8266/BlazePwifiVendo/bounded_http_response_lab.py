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


_CPP_MULTI_CHAR_PUNCTUATORS = tuple(
    sorted(
        (
            ">>=", "<<=", "->*", "...", "<=>", "++", "--", "->", ".*", "::",
            "&&", "||", "<=", ">=", "==", "!=", "+=", "-=", "*=", "/=",
            "%=", "^=", "&=", "|=", "<<", ">>", "##",
        ),
        key=len,
        reverse=True,
    )
)


def _cpp_token_sequence(source):
    """Tokenize the extracted C++ function without losing literal payloads."""
    tokens = []
    index = 0

    while index < len(source):
        if source[index].isspace():
            index += 1
            continue

        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            while (
                newline >= 0
                and newline > index
                and source[newline - 1] == "\\"
            ):
                newline = source.find("\n", newline + 1)
            index = len(source) if newline < 0 else newline + 1
            continue

        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            if end < 0:
                raise ValueError("unterminated C++ block comment")
            index = end + 2
            continue

        raw_prefix = next(
            (
                prefix
                for prefix in ("u8R", "uR", "UR", "LR", "R")
                if source.startswith(prefix + '"', index)
            ),
            None,
        )
        if raw_prefix is not None:
            quote_index = index + len(raw_prefix)
            open_paren = source.find("(", quote_index + 1)
            if open_paren < 0:
                raise ValueError("malformed C++ raw string literal")
            delimiter = source[quote_index + 1 : open_paren]
            if (
                len(delimiter) > 16
                or any(char.isspace() or char in "()\\" for char in delimiter)
            ):
                raise ValueError("invalid C++ raw string delimiter")
            terminator = ")" + delimiter + '"'
            end = source.find(terminator, open_paren + 1)
            if end < 0:
                raise ValueError("unterminated C++ raw string literal")
            end += len(terminator)
            tokens.append(("literal", source[index:end]))
            index = end
            continue

        literal_prefix = None
        quote = None
        quote_index = None
        for prefix in ("u8", "u", "U", "L", ""):
            candidate = index + len(prefix)
            if (
                candidate < len(source)
                and source.startswith(prefix, index)
                and source[candidate] in ("'", '"')
            ):
                literal_prefix = prefix
                quote = source[candidate]
                quote_index = candidate
                break
        if literal_prefix is not None:
            start = index
            index = quote_index + 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == quote:
                    index += 1
                    tokens.append(("literal", source[start:index]))
                    break
                index += 1
            else:
                raise ValueError("unterminated C++ quoted literal")
            continue

        char = source[index]
        if char.isalpha() or char == "_":
            start = index
            index += 1
            while index < len(source) and (
                source[index].isalnum() or source[index] == "_"
            ):
                index += 1
            tokens.append(("identifier", source[start:index]))
            continue

        if char.isdigit() or (
            char == "." and index + 1 < len(source) and source[index + 1].isdigit()
        ):
            start = index
            index += 1
            while index < len(source) and (
                source[index].isalnum() or source[index] in "_'."
            ):
                index += 1
            tokens.append(("number", source[start:index]))
            continue

        punctuator = next(
            (
                item
                for item in _CPP_MULTI_CHAR_PUNCTUATORS
                if source.startswith(item, index)
            ),
            None,
        )
        if punctuator is None:
            tokens.append(("punct", char))
            index += 1
        else:
            tokens.append(("punct", punctuator))
            index += len(punctuator)

    return tuple(tokens)


def _normalize_cpp_function(source, name):
    """Compare C++ tokens, preserving strings/chars and ignoring comments."""
    return _cpp_token_sequence(extract_function(source, name))


def _board_parity_problem(sources):
    """Return a readable mismatch when the two bounded readers drift."""
    missing = [board for board in BOARDS if board not in sources]
    if missing:
        return "missing board source(s): " + ", ".join(missing)

    normalized = {
        board: _normalize_cpp_function(
            sources[board], "readBoundedControllerResponse"
        )
        for board in BOARDS
    }
    if normalized["ESP8266"] != normalized["ESP32"]:
        return "ESP8266/ESP32 readBoundedControllerResponse bodies differ"
    return None


def verify_board_parity(sources):
    problem = _board_parity_problem(sources)
    if problem:
        raise AssertionError(problem)
    print("BOUNDED_HTTP_RESPONSE_BOARD_PARITY_PASS")


def verify_board_parity_mutations(sources):
    """Prove each fail-closed reader invariant is protected by the parity guard."""
    mutations = (
        (
            "status-deny",
            "statusCode<200 || statusCode>=300 ||",
            "statusCode<200 ||",
        ),
        ("unknown-length-deny", "responseBytes<0 ||", ""),
        (
            "declared-size-cap",
            "responseBytes>MAX_CONTROLLER_RESPONSE_BYTES ||",
            "",
        ),
        ('transfer-encoding-deny', 'h.hasHeader("Transfer-Encoding")', "false"),
        (
            "exact-length-readback",
            "if((int)body.length()!=responseBytes) return String();",
            "",
        ),
    )

    for board in BOARDS:
        source = sources[board]
        helper = extract_function(source, "readBoundedControllerResponse")
        if source.count(helper) != 1:
            raise AssertionError(
                f"{board}: bounded reader must have one exact source occurrence"
            )
        for label, old, new in mutations:
            if helper.count(old) != 1:
                raise AssertionError(
                    f"{board}: expected one parity mutation anchor for {label}"
                )
            mutated_helper = helper.replace(old, new, 1)
            mutated_sources = dict(sources)
            mutated_sources[board] = source.replace(helper, mutated_helper, 1)
            problem = _board_parity_problem(mutated_sources)
            if problem is None:
                raise AssertionError(
                    f"{board}: board parity accepted {label} drift"
                )
            print(
                f"{board}: BOUNDED_HTTP_RESPONSE_BOARD_PARITY_MUTATION_REJECTED "
                f"{label}"
            )

    print("BOUNDED_HTTP_RESPONSE_BOARD_PARITY_MUTATIONS_PASS 10/10")


def verify_board_parity_normalizer_contract():
    """Guard C++ token parity, literal payloads and comment-insensitive formatting."""
    compact = r"""
String readBoundedControllerResponse(HTTPClient &h, int statusCode) {
  if(statusCode<200 || statusCode>=300) return String();
  return String();
}
"""
    formatted = r"""
String readBoundedControllerResponse ( HTTPClient & h , int statusCode )
{
    if ( statusCode < 200 || statusCode >= 300 ) return String ( ) ;
    return String ( ) ;
}
"""
    equivalent = {"ESP8266": compact, "ESP32": formatted}
    if _board_parity_problem(equivalent) is not None:
        raise AssertionError("whitespace-only C++ formatting must not break board parity")

    literal_baseline = r"""
String readBoundedControllerResponse(HTTPClient &h, int statusCode) {
  if (h.hasHeader("Transfer-Encoding")) return String();
  return String();
}
"""
    literal_drift = literal_baseline.replace(
        '"Transfer-Encoding"', '"Transfer - Encoding"'
    )
    if _board_parity_problem({"ESP8266": literal_baseline, "ESP32": literal_drift}) is None:
        raise AssertionError("string-literal whitespace must remain significant")

    token_baseline = r"""
String readBoundedControllerResponse(HTTPClient &h, int statusCode) {
  return String();
}
"""
    token_drift = token_baseline.replace("return String()", "returnString()")
    if _board_parity_problem({"ESP8266": token_baseline, "ESP32": token_drift}) is None:
        raise AssertionError("C++ token boundaries must remain significant")

    comment_left = token_baseline.replace(
        "return String();", "return String(); // ESP8266-only note"
    )
    comment_right = token_baseline.replace(
        "return String();", "return String(); // ESP32-only note"
    )
    if _board_parity_problem({"ESP8266": comment_left, "ESP32": comment_right}) is not None:
        raise AssertionError("comments must not create a false board-parity mismatch")

    raw_left = r"""
String readBoundedControllerResponse(HTTPClient &h, int statusCode) {
  return R"cfg(alpha beta)cfg";
}
"""
    raw_right = raw_left.replace("alpha beta", "alpha  beta")
    if _board_parity_problem({"ESP8266": raw_left, "ESP32": raw_right}) is None:
        raise AssertionError("raw-string contents must remain significant")

    escaped_left = r"""
String readBoundedControllerResponse(HTTPClient &h, int statusCode) {
  return "alpha\tbeta";
}
"""
    escaped_right = escaped_left.replace(r"\t", " ")
    if _board_parity_problem({"ESP8266": escaped_left, "ESP32": escaped_right}) is None:
        raise AssertionError("escaped string contents must remain significant")

    char_left = r"""
String readBoundedControllerResponse(HTTPClient &h, int statusCode) {
  return '\t';
}
"""
    char_right = char_left.replace(r"\t", " ")
    if _board_parity_problem({"ESP8266": char_left, "ESP32": char_right}) is None:
        raise AssertionError("character literal contents must remain significant")

    print("BOUNDED_HTTP_RESPONSE_TOKEN_NORMALIZER_PASS 8/8")



def verify():
    verify_board_parity_normalizer_contract()
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
