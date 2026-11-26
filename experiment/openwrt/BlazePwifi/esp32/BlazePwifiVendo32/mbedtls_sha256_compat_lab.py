#!/usr/bin/env python3
"""Fail-closed ESP32 runtime-pin and Mbed TLS 3/4 SHA-256 source contract.

The companion workflow compiles the packaged Vendo source twice per pinned
Arduino core and retains only application binaries plus provenance. This lab
is source-extracted; it is not cryptographic runtime or physical acceptance.
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


def validate_runtime_pin_setup(source: str) -> None:
    helper = mask_non_code(
        extract_function(source, "void configureRuntimePins(int coinPin,int relayPin,int ledPin)")
    )
    required = (
        "if(runLedPin!=ledPin) writeLogical(runLedPin,false,runLedActiveHigh);",
        "if(runRelayPin!=relayPin) writeLogical(runRelayPin,false,runRelayActiveHigh);",
        "runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;",
        "pinMode(runCoinPin,INPUT_PULLUP)",
        "pinMode(runRelayPin,OUTPUT)",
        "pinMode(runLedPin,OUTPUT)",
        "writeLogical(runRelayPin,false,runRelayActiveHigh)",
        "writeLogical(runLedPin,false,runLedActiveHigh)",
    )
    for token in required:
        require(token in helper, f"runtime pin helper missing safe-order token: {token}")
    old_led = helper.find("if(runLedPin!=ledPin)")
    old_relay = helper.find("if(runRelayPin!=relayPin)")
    assign = helper.find("runCoinPin=coinPin;")
    input_mode = helper.find("pinMode(runCoinPin,INPUT_PULLUP)")
    output_off = helper.find("writeLogical(runRelayPin,false,runRelayActiveHigh)", input_mode)
    require(0 <= old_led < assign and 0 <= old_relay < assign < input_mode < output_off,
            "old outputs must be forced OFF before pin reassignment and new output setup")

    setup = mask_non_code(extract_function(source, "void setup()"))
    pin_call = setup.find("configureRuntimePins(runCoinPin,runRelayPin,runLedPin)")
    deny_call = setup.find("denyRemoteControl()", pin_call + 1)
    ap_call = setup.find("setupPortal()", deny_call + 1)
    connect_call = setup.find("connectSta()", ap_call + 1)
    require(0 <= pin_call < deny_call < ap_call < connect_call,
            "runtime pins and deny must precede setup AP and station/network work")
    print("RUNTIME_PIN_SETUP_FAIL_CLOSED_PASS")


def validate_mbedtls_provider(source: str) -> None:
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

    digest = mask_non_code(extract_function(source, "String hexDigest(const String &s)"))
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
        require(token in digest, f"hexDigest missing fail-closed/provider token: {token}")
    init_at = digest.find("if(psa_crypto_init()!=PSA_SUCCESS) return String();")
    compute_at = digest.find("psa_hash_compute(")
    require(0 <= init_at < compute_at,
            "PSA crypto must initialize successfully before SHA-256 computation")
    print("MBEDTLS_SHA256_PROVIDER_FAIL_CLOSED_PASS")

    valid = extract_function(source, "bool validSha256Hex(const String &digest)")
    for token in (
        "digest.length()!=64",
        "for(size_t i=0;i<64;i++)",
        "c>='0'&&c<='9'",
        "c>='a'&&c<='f'",
        "c>='A'&&c<='F'",
    ):
        require(token in valid, f"validSha256Hex missing validation: {token}")
    print("SHA256_HEX_OUTPUT_VALIDATION_PASS")

    signed = mask_non_code(extract_function(
        source,
        "String signedBody(const String &action",
    ))
    digest_at = signed.find("String digest=hexDigest(base);")
    deny_at = signed.find("if(!validSha256Hex(digest)) return String();")
    return_at = signed.find("return", deny_at + 1)
    require(0 <= digest_at < deny_at < return_at,
            "signedBody must validate the digest before constructing a request")
    print("SIGNED_BODY_INVALID_DIGEST_DENY_PASS")

    post_source = extract_function(
        source,
        "String post(const String &action",
    )
    post = mask_non_code(post_source)
    action_guard = re.search(
        r'if\s*\(\s*action\s*!=\s*"register"\s*&&\s*action\s*!=\s*"poll"\s*\)',
        post_source,
    )
    require(action_guard is not None, "post must allow only register and poll actions")
    allowlist_at = post.find("if(action!=")
    deny_return_at = post.find("return", allowlist_at)
    key_guard_at = post.find("if(cfg.key.isEmpty() || cfg.id.isEmpty()) return")
    body_at = post.find("String body=signedBody(")
    empty_at = post.find("if(!body.length()) return")
    begin_at = post.find("h.begin(client,url)")
    send_at = post.find("h.POST(body)")
    require(0 <= allowlist_at < deny_return_at < key_guard_at < body_at < empty_at < begin_at < send_at,
            "post must deny unsupported actions and missing key/id before signing or network I/O")
    require("h.POST(signedBody(" not in post_source,
            "post must not construct/send the signed body inside HTTPClient::POST")
    print("POST_ACTION_AND_EMPTY_SIGNATURE_DENY_PASS")


def validate_source(source: str) -> None:
    failures = []
    for label, check in (
        ("RUNTIME_PIN_SETUP", validate_runtime_pin_setup),
        ("MBEDTLS_PROVIDER", validate_mbedtls_provider),
    ):
        try:
            check(source)
        except AssertionError as exc:
            failures.append(f"{label}: {exc}")
            print(f"BASELINE_FAIL {label}: {exc}")
    if failures:
        raise AssertionError("; ".join(failures))


def expect_rejected(label: str, mutated_source: str) -> None:
    try:
        validate_source(mutated_source)
    except (AssertionError, ValueError):
        print(f"MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe mutation was not rejected: {label}")


def main() -> None:
    if not SKETCH.is_file():
        raise SystemExit(f"missing ESP32 sketch: {SKETCH}")
    source = SKETCH.read_text(encoding="utf-8")
    validate_source(source)
    print("ESP32_RUNTIME_PIN_AND_MBEDTLS_SOURCE_CONTRACT_PASS")

    runtime_helper = extract_function(
        source, "void configureRuntimePins(int coinPin,int relayPin,int ledPin)"
    )
    expect_rejected("missing-runtime-pin-helper", source.replace(runtime_helper, "", 1))
    expect_rejected(
        "setup-pins-after-deny",
        source.replace(
            "configureRuntimePins(runCoinPin,runRelayPin,runLedPin);denyRemoteControl();",
            "denyRemoteControl();configureRuntimePins(runCoinPin,runRelayPin,runLedPin);",
            1,
        ),
    )
    expect_rejected(
        "missing-old-relay-off-before-pin-change",
        source.replace(
            "if(runRelayPin!=relayPin) writeLogical(runRelayPin,false,runRelayActiveHigh);",
            "",
            1,
        ),
    )
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
        re.sub(r"(?m)^\s*#error[^\n]*$", "/* mutation: unsupported major is not rejected */", source, count=1),
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
        "missing-key-provisioning-deny",
        source.replace(
            'if(cfg.key.isEmpty() || cfg.id.isEmpty()) return "";',
            "/* mutation: missing key/id accepted */",
            1,
        ),
    )
    expect_rejected(
        "missing-register-poll-action-allowlist",
        re.sub(
            r'if\s*\(\s*action\s*!=\s*"register"\s*&&\s*action\s*!=\s*"poll"\s*\)',
            "if(false)",
            source,
            count=1,
        ),
    )
    print("SIMULATED_ONLY=1")
    print("TARGET_BUILD_REQUIRED=1")
    print("COIN_ADMISSION_ENABLED=0")


if __name__ == "__main__":
    main()
