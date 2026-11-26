#!/usr/bin/env python3
"""Fail-closed controller request signing and action guard for both Vendo boards.

This is a source-extracted static regression with mutation checks. It proves
that invalid local request configuration is refused before HTTP dispatch; it
does not prove server authentication, cryptographic runtime behavior, or
physical hardware acceptance.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
HELPERS = ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo"
sys.path.insert(0, str(HELPERS))
from firmware_source_extract import extract_function, mask_non_code  # noqa: E402

SKETCHES = {
    "ESP8266": ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

CREDENTIAL_GUARD = {
    "ESP8266": "if(!strlen(cfg.key) || !strlen(cfg.id)) return String();",
    "ESP32": "if(cfg.key.isEmpty() || cfg.id.isEmpty()) return String();",
}
POST_CREDENTIAL_GUARD = {
    "ESP8266": 'if(!strlen(cfg.key) || !strlen(cfg.id)) return "";',
    "ESP32": 'if(cfg.key.isEmpty() || cfg.id.isEmpty()) return "";',
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def edit_function(source: str, signature: str, old: str, new: str) -> str:
    function = extract_function(source, signature)
    require(old in function, f"mutation anchor missing in {signature}: {old}")
    changed = function.replace(old, new, 1)
    return source.replace(function, changed, 1)


def assert_contract(board: str, source: str) -> None:
    signed = extract_function(source, "String signedBody(")
    post = extract_function(source, "String post(")
    signed_code = mask_non_code(signed)
    post_code = mask_non_code(post)

    signed_guard = signed_code.find(CREDENTIAL_GUARD[board])
    nonce_at = signed_code.find("String n=")
    base_at = signed_code.find("String base=")
    digest_at = signed_code.find("String digest=hexDigest(base);")
    digest_check = signed_code.find("if(!validSha256Hex(digest)) return String();")
    require(0 <= signed_guard < nonce_at < base_at < digest_at < digest_check,
            f"{board}: signedBody must reject empty key/ID and invalid digest before serialization")

    validator_raw = extract_function(source, "bool validSha256Hex(")
    validator = mask_non_code(validator_raw)
    for token in (
        "if(digest.length()!=64) return false;",
        "for(size_t i=0;i<64;i++){",
        "char c=digest[i];",
    ):
        require(token in validator, f"{board}: SHA-256 digest validator missing {token!r}")
    validator_compact = re.sub(r"\s+", "", validator_raw)
    for token in ("c>='0'&&c<='9'", "c>='a'&&c<='f'", "c>='A'&&c<='F'"):
        require(token in validator_compact,
                f"{board}: SHA-256 digest validator missing hex range {token!r}")

    signed_compact = re.sub(r"\s+", "", signed)
    require('&sig="+digest;' in signed_compact,
            f"{board}: serialized request must use the validated digest")

    post_compact = re.sub(r"\s+", "", post)
    require('if(action!="register"&&action!="poll")return"";' in post_compact,
            f"{board}: post must allow only register and poll")
    post_compact_code = re.sub(r"\s+", "", post_code)
    action_at = post_compact_code.find("action!=")
    post_guard = post_compact_code.find(re.sub(r"\s+", "", POST_CREDENTIAL_GUARD[board]))
    wifi_at = post_compact_code.find("WiFi.status()")
    body_at = post_compact_code.find("Stringbody=signedBody(action,pulses,target,forcedNonce);")
    body_check = post_compact_code.find("if(!body.length())return")
    client_at = post_compact_code.find("WiFiClientclient;")
    begin_at = post_compact_code.find("h.begin(client,url)")
    send_at = post_compact_code.find("h.POST(body)")
    require(0 <= action_at < post_guard < wifi_at < body_at < body_check < client_at < begin_at < send_at,
            f"{board}: action, credentials and nonempty body must be checked before HTTP dispatch")
    require("h.POST(signedBody(" not in post_compact,
            f"{board}: HTTP must send only the already-validated body")


def expect_rejected(board: str, label: str, source: str) -> None:
    try:
        assert_contract(board, source)
    except AssertionError:
        print(f"REQUEST_AUTH_MUTATION_REJECTED {board} {label}")
        return
    raise AssertionError(f"{board}: unsafe request mutation survived: {label}")


def verify_board(board: str, path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    assert_contract(board, source)
    print(f"REQUEST_AUTH_CONTRACT_PASS {board}")

    key_guard = CREDENTIAL_GUARD[board]
    expect_rejected(
        board, "missing-signedBody-credential-guard",
        edit_function(source, "String signedBody(", key_guard, ""),
    )
    expect_rejected(
        board, "missing-post-action-allowlist",
        edit_function(source, "String post(", 'if(action!="register" && action!="poll") return "";', ""),
    )
    expect_rejected(
        board, "missing-post-credential-guard",
        edit_function(source, "String post(", POST_CREDENTIAL_GUARD[board], ""),
    )
    expect_rejected(
        board, "key-only-guard-does-not-reject-empty-ID",
        edit_function(source, "String signedBody(", key_guard,
                      "if(!strlen(cfg.key)) return String();" if board == "ESP8266"
                      else "if(cfg.key.isEmpty()) return String();"),
    )
    expect_rejected(
        board, "ID-only-guard-does-not-reject-empty-key",
        edit_function(source, "String signedBody(", key_guard,
                      "if(!strlen(cfg.id)) return String();" if board == "ESP8266"
                      else "if(cfg.id.isEmpty()) return String();"),
    )
    expect_rejected(
        board, "missing-digest-validation",
        edit_function(source, "String signedBody(",
                      "if(!validSha256Hex(digest)) return String();", ""),
    )
    expect_rejected(
        board, "missing-empty-body-guard",
        edit_function(source, "String post(", 'if(!body.length()) return "";', ""),
    )
    expect_rejected(
        board, "unvalidated-http-payload",
        edit_function(source, "String post(", "h.POST(body)",
                      "h.POST(signedBody(action,pulses,target,forcedNonce))"),
    )
    expect_rejected(
        board, "digest-validator-length-bypass",
        edit_function(source, "bool validSha256Hex(",
                      "if(digest.length()!=64) return false;",
                      "if(digest.length()!=0) return false;"),
    )


def main() -> int:
    failures = []
    for board, path in SKETCHES.items():
        try:
            verify_board(board, path)
        except Exception as exc:
            failures.append(f"{board}: {exc}")
            print(f"REQUEST_AUTH_CONTRACT_FAIL {board}: {exc}")
    if failures:
        raise SystemExit(1)
    print("REQUEST_AUTH_CONTRACT_ALL_BOARDS_PASS")
    return 0


if __name__ == "__main__":
    main()
