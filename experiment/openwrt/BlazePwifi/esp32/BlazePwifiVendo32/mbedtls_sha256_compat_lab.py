#!/usr/bin/env python3
"""Static source guard for the ESP32 Mbed TLS 3/4 SHA-256 compatibility fence.

The full firmware workflow supplies the real Arduino-core compile. This lab
checks that the selected API is version-gated and that crypto failures cannot
produce or transmit an empty/invalid request signature. Mutation cases prove
the guard rejects removed fail-closed checks. It is not cryptographic or
physical-hardware acceptance evidence.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
SKETCH = ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_function(source: str, signature: str) -> str:
    start = source.find(signature)
    require(start >= 0, f"missing function: {signature}")
    brace = source.find("{", start + len(signature))
    require(brace >= 0, f"missing function body: {signature}")

    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    position = brace
    while position < len(source):
        char = source[position]
        next_char = source[position + 1] if position + 1 < len(source) else ""

        if line_comment:
            if char in "\r\n":
                line_comment = False
            position += 1
            continue
        if block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
                position += 2
            else:
                position += 1
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            position += 1
            continue
        if char == "/" and next_char == "/":
            line_comment = True
            position += 2
            continue
        if char == "/" and next_char == "*":
            block_comment = True
            position += 2
            continue
        if char in ("'", '"'):
            quote = char
            position += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:position + 1]
        position += 1

    raise AssertionError(f"unclosed function body: {signature}")


def validate_source(source: str) -> None:
    version_include = source.find("#include <mbedtls/version.h>")
    psa_branch = source.find("#if MBEDTLS_VERSION_MAJOR == 4")
    psa_include = source.find("#include <psa/crypto.h>")
    legacy_branch = source.find("#elif MBEDTLS_VERSION_MAJOR == 3")
    legacy_include = source.find("#include <mbedtls/sha256.h>")
    unsupported = source.find("#error \"Unsupported Mbed TLS major version: BlazePwifi ESP32 supports 3.x and 4.x only\"")
    require(version_include >= 0, "missing Mbed TLS version header")
    require(0 <= version_include < psa_branch < psa_include < legacy_branch < legacy_include < unsupported,
            "Mbed TLS 3/4 includes are not separated by the expected version guard")
    require(source.count("#include <mbedtls/sha256.h>") == 1,
            "legacy SHA header must appear exactly once inside the Mbed TLS 3 branch")
    require(source.count("#include <psa/crypto.h>") == 1,
            "PSA Crypto header must appear exactly once inside the Mbed TLS 4 branch")
    print("MBEDTLS_VERSION_GUARD_PASS")

    digest = extract_function(source, "String hexDigest(const String &s)")
    for token in (
        "if(psa_crypto_init()!=PSA_SUCCESS) return String();",
        "psa_hash_compute(",
        "PSA_ALG_SHA_256",
        "if(status!=PSA_SUCCESS || digestLength!=sizeof(out)) return String();",
        "#elif MBEDTLS_VERSION_MAJOR == 3",
        "mbedtls_sha256_starts(&c,0)",
        "mbedtls_sha256_update(",
        "mbedtls_sha256_finish(&c,out)",
        "mbedtls_sha256_free(&c)",
        "if(status!=0) return String();",
        'sprintf(buf+i*2,"%02x",out[i])',
        "buf[64]=0; return String(buf);",
    ):
        require(token in digest, f"hexDigest missing fail-closed/provider token: {token}")

    psa_init_at = digest.find("if(psa_crypto_init()!=PSA_SUCCESS) return String();")
    psa_compute_at = digest.find("psa_hash_compute(")
    require(0 <= psa_init_at < psa_compute_at,
            "PSA crypto must initialize successfully before SHA-256 computation")

    print("MBEDTLS_SHA256_PROVIDER_FAIL_CLOSED_PASS")

    valid = extract_function(source, "bool validSha256Hex(const String &digest)")
    for token in ("digest.length()!=64", "for(size_t i=0;i<64;i++)",
                  "c>='0'&&c<='9'", "c>='a'&&c<='f'", "c>='A'&&c<='F'"):
        require(token in valid, f"validSha256Hex missing validation: {token}")

    print("SHA256_HEX_OUTPUT_VALIDATION_PASS")

    signed = extract_function(
        source,
        'String signedBody(const String &action,const String &pulses,const String &target,const String &forcedNonce=""'
    )
    digest_at = signed.find("String digest=hexDigest(base);")
    deny_at = signed.find("if(!validSha256Hex(digest)) return String();")
    nonce_at = signed.find("lastSentNonce=n;")
    require(digest_at >= 0 and digest_at < deny_at < nonce_at,
            "signedBody must validate the digest before recording/sending its nonce")

    print("SIGNED_BODY_NONCE_GUARD_PASS")

    post = extract_function(
        source,
        'String post(const String &action,const String &pulses="0",const String &target="",const String &forcedNonce="")'
    )
    allowlist_at = post.find('if(action!="register" && action!="poll")')
    body_at = post.find("String body=signedBody(")
    empty_at = post.find('if(!body.length()) return "";')
    begin_at = post.find("h.begin(client,url)")
    send_at = post.find("h.POST(body)")
    require(0 <= allowlist_at < body_at < empty_at < begin_at < send_at,
            "post must deny non-register/poll actions and empty signatures before network I/O")
    print("POST_EMPTY_SIGNATURE_DENY_PASS")


def expect_rejected(label: str, mutated_source: str) -> None:
    try:
        validate_source(mutated_source)
    except AssertionError:
        print(f"MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe mutation was not rejected: {label}")


def main() -> None:
    if not SKETCH.is_file():
        raise SystemExit(f"missing ESP32 sketch: {SKETCH}")
    source = SKETCH.read_text(encoding="utf-8")
    validate_source(source)
    print("ESP32_MBEDTLS_SHA256_SELECTOR_PASS")
    print("ESP32_SIGNED_BODY_FAIL_CLOSED_PASS")

    expect_rejected(
        "missing-psa-crypto-init-failure-deny",
        source.replace(
            "if(psa_crypto_init()!=PSA_SUCCESS) return String();",
            "/* mutation: PSA initialization failure ignored */",
            1,
        ),
    )
    expect_rejected(
        "psa-hash-before-crypto-initialization",
        source.replace(
            "if(psa_crypto_init()!=PSA_SUCCESS) return String();",
            "",
            1,
        ).replace(
            "  );\n  if(status!=PSA_SUCCESS || digestLength!=sizeof(out)) return String();",
            "  );\n  if(psa_crypto_init()!=PSA_SUCCESS) return String();\n  if(status!=PSA_SUCCESS || digestLength!=sizeof(out)) return String();",
            1,
        ),
    )
    expect_rejected(
        "missing-unsupported-major-deny",
        source.replace(
            '#error "Unsupported Mbed TLS major version: BlazePwifi ESP32 supports 3.x and 4.x only"',
            "/* mutation: unsupported Mbed TLS major not rejected */",
            1,
        ),
    )

    expect_rejected(
        "missing-psa-status-and-length-check",
        source.replace(
            "if(status!=PSA_SUCCESS || digestLength!=sizeof(out)) return String();",
            "/* mutation: PSA result not checked */",
            1,
        ),
    )
    expect_rejected(
        "missing-legacy-status-check",
        source.replace("if(status!=0) return String();",
                       "/* mutation: legacy result not checked */", 1),
    )
    expect_rejected(
        "missing-invalid-digest-deny",
        source.replace("if(!validSha256Hex(digest)) return String();",
                       "/* mutation: invalid digest accepted */", 1),
    )
    expect_rejected(
        "missing-empty-request-deny",
        source.replace('if(!body.length()) return "";',
                       "/* mutation: empty request sent */", 1),
    )
    print("SIMULATED_ONLY=1")
    print("TARGET_BUILD_REQUIRED=1")
    print("COIN_ADMISSION_ENABLED=0")


if __name__ == "__main__":
    main()
