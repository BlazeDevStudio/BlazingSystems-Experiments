#!/usr/bin/env python3
"""Fail-closed Mbed TLS 3/4 SHA-256 selector guard for active-v0.6 ESP32.

This is a source-extracted contract test. The pinned Arduino-core workflow
performs the actual target compile twice and retains both application images.
It is not cryptographic runtime or physical-hardware acceptance evidence.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
HELPERS = ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo"
sys.path.insert(0, str(HELPERS))
from firmware_source_extract import extract_function, mask_non_code  # noqa: E402

SKETCH = ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_source(source: str) -> None:
    masked = mask_non_code(source)
    version_include = masked.find("#include <mbedtls/version.h>")
    psa_branch = masked.find("#if MBEDTLS_VERSION_MAJOR == 4")
    psa_include = masked.find("#include <psa/crypto.h>")
    legacy_branch = masked.find("#elif MBEDTLS_VERSION_MAJOR == 3")
    legacy_include = masked.find("#include <mbedtls/sha256.h>")
    unsupported = masked.find("#error")
    require(version_include >= 0, "missing Mbed TLS version header")
    require(
        0 <= version_include < psa_branch < psa_include < legacy_branch < legacy_include < unsupported,
        "Mbed TLS 3/4 headers are not isolated behind the expected version selector",
    )
    require(masked.count("#include <mbedtls/sha256.h>") == 1,
            "legacy SHA header must appear exactly once in the Mbed TLS 3 branch")
    require(masked.count("#include <psa/crypto.h>") == 1,
            "PSA Crypto header must appear exactly once in the Mbed TLS 4 branch")
    require(re.search(r"^\s*#\s*error\b", masked, re.MULTILINE) is not None,
            "unsupported Mbed TLS major versions must fail at compile time")
    print("MBEDTLS_VERSION_SELECTOR_PASS")

    digest = extract_function(source, "String hexDigest(const String &s)")
    digest_masked = mask_non_code(digest)
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
        "sprintf(buf+i*2,",
        "buf[64]=0; return String(buf);",
    ):
        require(token in digest_masked, f"hexDigest missing fail-closed/provider token: {token}")
    init_at = digest_masked.find("if(psa_crypto_init()!=PSA_SUCCESS) return String();")
    compute_at = digest_masked.find("psa_hash_compute(")
    require(0 <= init_at < compute_at,
            "PSA crypto must initialize successfully before SHA-256 computation")
    print("MBEDTLS_SHA256_PROVIDER_FAIL_CLOSED_PASS")

    valid = mask_non_code(extract_function(source, "bool validSha256Hex(const String &digest)"))
    for token in (
        "digest.length()!=64",
        "for(size_t i=0;i<64;i++)",
        "c>='0'&&c<='9'",
        "c>='a'&&c<='f'",
        "c>='A'&&c<='F'",
    ):
        require(token in valid, f"validSha256Hex missing validation: {token}")
    print("SHA256_HEX_OUTPUT_VALIDATION_PASS")

    signed = extract_function(
        source,
        'String signedBody(const String &action,const String &pulses,const String &target,const String &forcedNonce="")',
    )
    signed_masked = mask_non_code(signed)
    digest_at = signed_masked.find("String digest=hexDigest(base);")
    deny_at = signed_masked.find("if(!validSha256Hex(digest)) return String();")
    return_at = signed_masked.find("return", deny_at + 1)
    require(0 <= digest_at < deny_at < return_at,
            "signedBody must validate the digest before constructing a request")
    print("SIGNED_BODY_INVALID_DIGEST_DENY_PASS")

    post = extract_function(
        source,
        'String post(const String &action,const String &pulses="0",const String &target="",const String &forcedNonce="")',
    )
    post_masked = mask_non_code(post)
    allowlist = 'if(action!="register" && action!="poll") return "";'
    require(allowlist in post, "post must allow only register and poll actions")
    allowlist_at = post_masked.find("if(action==")
    body_at = post_masked.find("String body=signedBody(")
    empty_at = post_masked.find("if(!body.length()) return")
    begin_at = post_masked.find("h.begin(client,url)")
    send_at = post_masked.find("h.POST(body)")
    require(0 <= allowlist_at < body_at < empty_at < begin_at < send_at,
            "post must deny unsupported actions and empty signatures before network I/O")
    require("h.POST(signedBody(" not in post,
            "post must not construct/send the signed body inside HTTPClient::POST")
    print("POST_ACTION_AND_EMPTY_SIGNATURE_DENY_PASS")


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

    expect_rejected(
        "missing-psa-init-failure-deny",
        source.replace(
            "if(psa_crypto_init()!=PSA_SUCCESS) return String();",
            "psa_crypto_init();",
            1,
        ),
    )
    moved_init = source.replace(
        "if(psa_crypto_init()!=PSA_SUCCESS) return String();",
        "",
        1,
    ).replace(
        "  );\n  if(status!=PSA_SUCCESS || digestLength!=sizeof(out)) return String();",
        "  );\n  if(psa_crypto_init()!=PSA_SUCCESS) return String();\n"
        "  if(status!=PSA_SUCCESS || digestLength!=sizeof(out)) return String();",
        1,
    )
    expect_rejected("psa-hash-before-crypto-initialization", moved_init)
    expect_rejected(
        "missing-unsupported-major-deny",
        source.replace(
            '#error "Unsupported Mbed TLS major version: BlazePwifi ESP32 supports 3.x and 4.x only"',
            "/* mutation: unsupported major is not rejected */",
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
        source.replace(
            "if(status!=0) return String();",
            "/* mutation: legacy result not checked */",
            1,
        ),
    )
    expect_rejected(
        "missing-invalid-digest-deny",
        source.replace(
            "if(!validSha256Hex(digest)) return String();",
            "/* mutation: invalid digest accepted */",
            1,
        ),
    )
    expect_rejected(
        "missing-empty-request-deny",
        source.replace(
            'if(!body.length()) return "";',
            "/* mutation: empty request sent */",
            1,
        ),
    )
    expect_rejected(
        "missing-register-poll-action-allowlist",
        source.replace(
            'if(action!="register" && action!="poll") return "";',
            "/* mutation: action is unrestricted */",
            1,
        ),
    )
    print("SIMULATED_ONLY=1")
    print("TARGET_BUILD_REQUIRED=1")
    print("COIN_ADMISSION_ENABLED=0")


if __name__ == "__main__":
    main()
