#!/usr/bin/env python3
"""Source-extracted fail-closed Mbed TLS 3/4 SHA-256 contract for ESP32 Vendo.

This checks source structure and negative mutations only. GitHub Actions separately
compiles the packaged sketch against pinned Arduino ESP32 cores 3.3.13 and 4.0.0.
It is not a runtime cryptographic or physical hardware acceptance test.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SKETCH = ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def function_body(source, signature):
    start = source.find(signature)
    require(start >= 0, f"missing function signature: {signature}")
    opening = source.find("{", start)
    require(opening >= 0, f"missing function body: {signature}")
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening:index + 1]
    raise AssertionError(f"unterminated function body: {signature}")


def validate_source(source):
    ordered = (
        "#include <mbedtls/version.h>",
        "#if MBEDTLS_VERSION_MAJOR == 4",
        "#include <psa/crypto.h>",
        "#elif MBEDTLS_VERSION_MAJOR == 3",
        "#include <mbedtls/sha256.h>",
        "#else",
        "#error \"Unsupported Mbed TLS major version",
        "#endif",
    )
    positions = [source.find(token) for token in ordered]
    require(all(position >= 0 for position in positions), "missing Mbed TLS 3/4 provider selector")
    require(positions == sorted(positions), "Mbed TLS provider headers are not isolated by version")
    require(source.count("#include <mbedtls/sha256.h>") == 1, "legacy SHA header must occur once")
    require(source.count("#include <psa/crypto.h>") == 1, "PSA header must occur once")

    digest = function_body(source, "String hexDigest(const String &s)")
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
        'sprintf(buf+i*2,"%02x",out[i]);',
        "buf[64]=0; return String(buf);",
    ):
        require(token in digest, f"hexDigest missing fail-closed provider token: {token}")
    require(
        digest.find("psa_crypto_init()") < digest.find("psa_hash_compute("),
        "PSA provider must initialize before hashing",
    )

    valid = function_body(source, "bool validSha256Hex(const String &digest)")
    for token in (
        "digest.length()!=64",
        "for(size_t i=0;i<64;i++)",
        "c>='0'&&c<='9'",
        "c>='a'&&c<='f'",
        "c>='A'&&c<='F'",
    ):
        require(token in valid, f"digest validator missing token: {token}")

    signed = function_body(source, "String signedBody(const String &action")
    key_guard = signed.find("if(cfg.key.isEmpty() || cfg.id.isEmpty()) return String();")
    digest_call = signed.find("String digest=hexDigest(base);")
    digest_guard = signed.find("if(!validSha256Hex(digest)) return String();")
    request_return = signed.find("return \"action=\"")
    require(0 <= digest_call < digest_guard < request_return,
            "signedBody must validate the digest before request construction")
    require("cfg.key.isEmpty()" not in signed and "cfg.id.isEmpty()" not in signed,
            "Mbed TLS compatibility patch must preserve existing first-boot register request behavior")

    post = function_body(source, "String post(const String &action")
    body_call = post.find("String body=signedBody(")
    body_guard = post.find('if(!body.length()) return "";')
    begin_call = post.find("h.begin(client,url)")
    send_call = post.find("h.POST(body)")
    require(0 <= body_call < body_guard < begin_call < send_call,
            "post must reject an empty signed body before opening or sending HTTP")
    require("h.POST(signedBody(" not in post, "post must not send an unchecked digest inline")


def expect_rejected(label, mutated):
    try:
        validate_source(mutated)
    except AssertionError:
        print(f"MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe source mutation was accepted: {label}")


def main():
    source = SKETCH.read_text(encoding="utf-8")
    validate_source(source)
    print("MBEDTLS_3_4_SOURCE_CONTRACT_PASS")

    mutations = (
        ("missing-version-selector", source.replace("#include <mbedtls/version.h>", "", 1)),
        ("missing-psa-init-failure-deny", source.replace(
            "if(psa_crypto_init()!=PSA_SUCCESS) return String();", "psa_crypto_init();", 1)),
        ("missing-psa-status-length-check", source.replace(
            "if(status!=PSA_SUCCESS || digestLength!=sizeof(out)) return String();", "/* unchecked */", 1)),
        ("missing-legacy-status-check", source.replace(
            "if(status!=0) return String();", "/* unchecked */", 1)),
        ("missing-invalid-digest-deny", source.replace(
            "if(!validSha256Hex(digest)) return String();", "/* unchecked */", 1)),
        ("new-empty-key-bootstrap-deny", source.replace(
            "String n=forcedNonce.length()?forcedNonce:freshNonce();",
            "if(cfg.key.isEmpty() || cfg.id.isEmpty()) return String();\\n  String n=forcedNonce.length()?forcedNonce:freshNonce();", 1)),
        ("missing-empty-body-deny", source.replace(
            'if(!body.length()) return "";', "/* unchecked */", 1)),
        ("missing-unsupported-version-deny", source.replace(
            '#error "Unsupported Mbed TLS major version: BlazePwifi ESP32 supports 3.x and 4.x only"',
            "/* unsupported major accepted */", 1)),
    )
    for label, mutated in mutations:
        expect_rejected(label, mutated)

    print("SIMULATED_ONLY=1")
    print("TARGET_BUILD_REQUIRED=1")
    print("COIN_ADMISSION_ENABLED=0")


if __name__ == "__main__":
    main()
