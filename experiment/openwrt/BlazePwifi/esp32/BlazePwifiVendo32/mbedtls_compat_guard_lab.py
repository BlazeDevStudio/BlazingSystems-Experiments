#!/usr/bin/env python3
"""Source-extracted Mbed TLS 3/4 selector and failure-path lab.

This validates the firmware's preprocessor selection and hexDigest control flow
with deliberately small API stubs. It is not a substitute for pinned Arduino
ESP32 builds against the real Mbed TLS packages.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import sys

BLAZEPWIFI_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BLAZEPWIFI_ROOT / "esp8266/BlazePwifiVendo"))
from firmware_lab_source import extract_function, mask_non_code

SKETCH = Path(__file__).with_name("BlazePwifiVendo32.ino")
UNSUPPORTED_ERROR = (
    "Unsupported Mbed TLS major version: "
    "BlazePwifi ESP32 supports 3.x and 4.x only"
)


def extract_selector(source: str) -> str:
    # Ignore directive-shaped text in comments and literals while keeping the
    # original source lines available for the returned selector block.
    masked_source = mask_non_code(source)
    if len(masked_source) != len(source):
        raise RuntimeError("selector lexical mask changed source offsets")

    lines = source.splitlines()
    code_lines = masked_source.splitlines()
    if len(code_lines) != len(lines):
        raise RuntimeError("selector lexical mask changed source line count")

    starts = [
        i for i, line in enumerate(code_lines)
        if line.strip() == "#if MBEDTLS_VERSION_MAJOR == 4"
    ]
    if len(starts) < 2:
        raise RuntimeError("expected header selector and hexDigest version branch")
    start = starts[0]
    depth = 0
    for i in range(start, len(code_lines)):
        stripped = code_lines[i].strip()
        if stripped.startswith(("#if ", "#ifdef ", "#ifndef ")):
            depth += 1
        elif stripped == "#endif":
            depth -= 1
            if depth == 0:
                block = "\n".join(lines[start:i + 1])
                required = (
                    "#if MBEDTLS_VERSION_MAJOR == 4",
                    "#include <psa/crypto.h>",
                    "#elif MBEDTLS_VERSION_MAJOR == 3",
                    "#include <mbedtls/sha256.h>",
                    "#else",
                    f'#error "{UNSUPPORTED_ERROR}"',
                    "#endif",
                )
                missing = [token for token in required if token not in block]
                if missing:
                    raise RuntimeError(
                        "firmware selector no longer matches the reviewed contract: "
                        + ", ".join(missing)
                    )
                return block
    raise RuntimeError("unterminated Mbed TLS selector")


def write_stub_headers(root: Path) -> None:
    (root / "mbedtls").mkdir()
    (root / "psa").mkdir()
    (root / "mbedtls" / "version.h").write_text(
        "#pragma once\n"
        "#ifndef MBEDTLS_VERSION_MAJOR\n"
        "#define MBEDTLS_VERSION_MAJOR 0\n"
        "#endif\n",
        encoding="utf-8",
    )
    (root / "mbedtls" / "sha256.h").write_text(
        textwrap.dedent(r"""
            #pragma once
            #define PHX_SELECTED_LEGACY 1
            typedef struct { int unused; } mbedtls_sha256_context;
            extern int phx_starts_status;
            extern int phx_update_status;
            extern int phx_finish_status;
            extern int phx_free_calls;
            inline void mbedtls_sha256_init(mbedtls_sha256_context*) {}
            inline int mbedtls_sha256_starts(mbedtls_sha256_context*, int) {
              return phx_starts_status;
            }
            inline int mbedtls_sha256_update(mbedtls_sha256_context*,
                                             const unsigned char*, size_t) {
              return phx_update_status;
            }
            inline int mbedtls_sha256_finish(mbedtls_sha256_context*,
                                             unsigned char* output) {
              if (phx_finish_status == 0) {
                for (size_t i = 0; i < 32; ++i) output[i] = 0xAB;
              }
              return phx_finish_status;
            }
            inline void mbedtls_sha256_free(mbedtls_sha256_context*) {
              ++phx_free_calls;
            }
        """).strip() + "\n",
        encoding="utf-8",
    )
    (root / "psa" / "crypto.h").write_text(
        textwrap.dedent(r"""
            #pragma once
            #include <cstddef>
            #include <cstdint>
            #define PHX_SELECTED_PSA 1
            using psa_status_t = int32_t;
            #define PSA_SUCCESS 0
            #define PSA_ERROR_GENERIC_ERROR (-132)
            #define PSA_ALG_SHA_256 1
            extern int phx_psa_init_status;
            extern int phx_psa_hash_status;
            extern size_t phx_psa_digest_length;
            extern int phx_psa_hash_calls;
            inline psa_status_t psa_crypto_init() {
              return phx_psa_init_status;
            }
            inline psa_status_t psa_hash_compute(
                int, const uint8_t*, size_t, uint8_t* output,
                size_t output_size, size_t* output_length) {
              ++phx_psa_hash_calls;
              if (phx_psa_hash_status != PSA_SUCCESS) {
                return phx_psa_hash_status;
              }
              const size_t count = output_size < 32 ? output_size : 32;
              for (size_t i = 0; i < count; ++i) output[i] = 0xAB;
              *output_length = phx_psa_digest_length;
              return PSA_SUCCESS;
            }
        """).strip() + "\n",
        encoding="utf-8",
    )
    (root / "esp_system.h").write_text("#pragma once\n", encoding="utf-8")


def harness(selector: str, digest_function: str, major: int) -> str:
    prelude = r"""
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

class String {
 public:
  String() = default;
  explicit String(const char* value) : value_(value ? value : "") {}
  const char* c_str() const { return value_.c_str(); }
  size_t length() const { return value_.length(); }
  const std::string& value() const { return value_; }
 private:
  std::string value_;
};
"""
    if major == 3:
        tests = r"""
int phx_starts_status = 0;
int phx_update_status = 0;
int phx_finish_status = 0;
int phx_free_calls = 0;
int main() {
  const String input("payload");
  String ok = hexDigest(input);
  std::string expected;
  for (int i = 0; i < 32; ++i) expected += "ab";
  if (ok.length() != 64 || ok.value() != expected) return 10;
  if (phx_free_calls != 1) return 11;

  phx_starts_status = -1;
  String startsFail = hexDigest(input);
  if (startsFail.length() != 0 || phx_free_calls != 2) return 12;

  phx_starts_status = 0;
  phx_update_status = -1;
  String updateFail = hexDigest(input);
  if (updateFail.length() != 0 || phx_free_calls != 3) return 13;

  phx_update_status = 0;
  phx_finish_status = -1;
  String finishFail = hexDigest(input);
  if (finishFail.length() != 0 || phx_free_calls != 4) return 14;
  return 0;
}
"""
    else:
        tests = r"""
int phx_psa_init_status = PSA_SUCCESS;
int phx_psa_hash_status = PSA_SUCCESS;
size_t phx_psa_digest_length = 32;
int phx_psa_hash_calls = 0;
int main() {
  const String input("payload");
  String ok = hexDigest(input);
  std::string expected;
  for (int i = 0; i < 32; ++i) expected += "ab";
  if (ok.value() != expected || phx_psa_hash_calls != 1) return 20;

  phx_psa_init_status = PSA_ERROR_GENERIC_ERROR;
  String initFail = hexDigest(input);
  if (initFail.length() != 0 || phx_psa_hash_calls != 1) return 21;

  phx_psa_init_status = PSA_SUCCESS;
  phx_psa_hash_status = PSA_ERROR_GENERIC_ERROR;
  String hashFail = hexDigest(input);
  if (hashFail.length() != 0 || phx_psa_hash_calls != 2) return 22;

  phx_psa_hash_status = PSA_SUCCESS;
  phx_psa_digest_length = 31;
  String lengthFail = hexDigest(input);
  if (lengthFail.length() != 0 || phx_psa_hash_calls != 3) return 23;
  return 0;
}
"""
    return (
        prelude
        + '#include <mbedtls/version.h>\n'
        + selector
        + '\n#include <esp_system.h>\n'
        + '#if MBEDTLS_VERSION_MAJOR == 3\n'
          '#ifndef PHX_SELECTED_LEGACY\n#error "Mbed TLS 3 must select the legacy SHA header"\n#endif\n'
          '#ifdef PHX_SELECTED_PSA\n#error "Mbed TLS 3 must not select PSA"\n#endif\n'
          '#elif MBEDTLS_VERSION_MAJOR == 4\n'
          '#ifndef PHX_SELECTED_PSA\n#error "Mbed TLS 4 must select PSA"\n#endif\n'
          '#ifdef PHX_SELECTED_LEGACY\n#error "Mbed TLS 4 must not select the legacy SHA header"\n#endif\n'
          '#endif\n'
        + digest_function
        + '\n'
        + tests
    )


def compile_and_run(cxx: str, root: Path, major: int,
                    selector: str, digest_function: str) -> None:
    cpp = root / f"major_{major}.cpp"
    binary = root / f"major_{major}"
    cpp.write_text(harness(selector, digest_function, major), encoding="utf-8")
    result = subprocess.run(
        [cxx, "-std=c++17", "-Wall", "-Wextra", "-I", str(root),
         f"-DMBEDTLS_VERSION_MAJOR={major}", str(cpp), "-o", str(binary)],
        text=True, capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Mbed TLS {major} selector compile failed:\n"
            f"{result.stdout}\n{result.stderr}"
        )
    run = subprocess.run([str(binary)], text=True, capture_output=True)
    if run.returncode != 0:
        raise RuntimeError(
            f"Mbed TLS {major} digest behavior failed with exit "
            f"{run.returncode}:\n{run.stdout}\n{run.stderr}"
        )
    print(f"MBEDTLS_MAJOR_{major}_SELECTOR_AND_DIGEST_PASS")


def reject_unsupported(cxx: str, root: Path, major: int, selector: str) -> None:
    cpp = root / f"unsupported_{major}.cpp"
    cpp.write_text(
        '#include <mbedtls/version.h>\n'
        + selector
        + '\nint main() { return 0; }\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [cxx, "-std=c++17", "-I", str(root),
         f"-DMBEDTLS_VERSION_MAJOR={major}", "-c", str(cpp),
         "-o", str(root / f"unsupported_{major}.o")],
        text=True, capture_output=True,
    )
    if result.returncode == 0 or UNSUPPORTED_ERROR not in result.stderr:
        raise RuntimeError(
            f"unsupported Mbed TLS {major} was not rejected by the production guard:\n"
            f"{result.stdout}\n{result.stderr}"
        )
    print(f"MBEDTLS_UNSUPPORTED_MAJOR_{major}_REJECTED")



def verify_shared_lexical_extractor():
    fixture = (
        'String lexicalProbe(){\n'
        '  const char *ordinary = "}";\n'
        '  const char *raw = R"tag({ })tag";\n'
        '  // } line-comment decoy\n'
        '  /* { block-comment decoy */\n'
        '  return ordinary;\n'
        '}'
    )
    extracted = extract_function(fixture, "lexicalProbe")
    if extracted != fixture:
        raise RuntimeError(
            "shared lexical extractor did not preserve a function with comment/literal brace decoys"
        )

def verify_selector_extraction_ignores_comment_decoys() -> None:
    selector = (
        "#if MBEDTLS_VERSION_MAJOR == 4\n"
        "#include <psa/crypto.h>\n"
        "#elif MBEDTLS_VERSION_MAJOR == 3\n"
        "#include <mbedtls/sha256.h>\n"
        "#else\n"
        f'#error "{UNSUPPORTED_ERROR}"\n'
        "#endif\n"
    )
    # This complete but inactive selector-shaped block is deliberately placed
    # inside a comment. A line-only directive scan must not accept it.
    decoy_selector = selector.replace(
        "#include <psa/crypto.h>\n",
        "#define PHX_SELECTOR_COMMENT_DECOY 1\n"
        "#include <psa/crypto.h>\n",
        1,
    )
    comment_decoy = "/*\n" + decoy_selector + "*/\n"
    digest_branch = "#if MBEDTLS_VERSION_MAJOR == 4\n#endif\n"

    extracted = extract_selector(comment_decoy + selector + digest_branch)
    if "PHX_SELECTOR_COMMENT_DECOY" in extracted:
        raise AssertionError("selector extractor accepted a comment-only preprocessor decoy")
    if extracted != selector.rstrip("\n"):
        raise AssertionError("selector extractor did not return the first active selector block")
    print("MBEDTLS_SELECTOR_COMMENT_DECOY_REJECTED 1/1")


def main() -> int:
    verify_selector_extraction_ignores_comment_decoys()
    verify_shared_lexical_extractor()
    cxx = shutil.which("c++") or shutil.which("g++")
    if not cxx:
        raise RuntimeError("C++ compiler unavailable; refusing to skip selector test")
    source = SKETCH.read_text(encoding="utf-8")
    selector = extract_selector(source)
    digest_function = extract_function(source, "hexDigest")
    if digest_function.count("#if MBEDTLS_VERSION_MAJOR == 4") != 1:
        raise RuntimeError("hexDigest must contain exactly one Mbed TLS 4 branch")
    if digest_function.count("#elif MBEDTLS_VERSION_MAJOR == 3") != 1:
        raise RuntimeError("hexDigest must contain exactly one Mbed TLS 3 branch")
    if "MBEDTLS_VERSION_MAJOR >=" in source:
        raise RuntimeError("broad Mbed TLS fallback guard reintroduced")
    if UNSUPPORTED_ERROR not in source:
        raise RuntimeError("unsupported-major diagnostic missing from firmware")

    with tempfile.TemporaryDirectory(prefix="phx-mbedtls-") as temp:
        root = Path(temp)
        write_stub_headers(root)
        compile_and_run(cxx, root, 3, selector, digest_function)
        compile_and_run(cxx, root, 4, selector, digest_function)
        reject_unsupported(cxx, root, 2, selector)
        reject_unsupported(cxx, root, 5, selector)

    print("STUB_API_ONLY=1")
    print("EXACT_ESP32_CORE_3_3_13_BUILD_REQUIRED=1")
    print("MBEDTLS_COMPATIBILITY_GUARD_LAB_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"MBEDTLS_COMPATIBILITY_GUARD_LAB_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
