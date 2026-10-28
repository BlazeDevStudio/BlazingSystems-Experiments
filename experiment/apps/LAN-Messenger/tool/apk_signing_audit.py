"""Audit APK certificate continuity without exposing private signing keys.

Usage:
  python3 tool/apk_signing_audit.py --self-test
  python3 tool/apk_signing_audit.py --apksigner /path/to/apksigner \
      --out build/app/outputs/flutter-apk/SIGNING-PROVENANCE.json \
      build/app/outputs/flutter-apk/app-*-release.apk

No private keys, passwords, application data or device identifiers are read.
The optional LAN_EXPECTED_SIGNER_SHA256 environment variable is a PUBLIC
certificate fingerprint, *not* a secret. Pin it only after the signing key
has been persistently provisioned.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path

# APK Build Tools 36 and earlier: "Signer #1 certificate ..."
# APK Build Tools 37: "V2 Signer: certificate ..." or "V3.0 Signer: ..."
# Also accept Android's signer-minSdkVersion form. Never match public-key
# fingerprints or use a scheme label alone as a certificate identity.
PATTERN = re.compile(
    r"(?im)^[ \t]*(?:(?:Signer[ \t]+(?:#[0-9]+|\([^)]*\))[ \t]+)"
    r"|(?:V[0-9]+(?:\.[0-9]+)?[ \t]+Signer[ \t]*:[ \t]*))"
    r"certificate[ \t]+SHA-256[ \t]+digest[ \t]*:[ \t]*"
    r"([0-9a-fA-F:]+)[ \t]*$"
)


def normalize_digest(text: str) -> str:
    value = re.sub(r"[:\s]", "", text).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("Expected exactly 32 bytes of public SHA-256 fingerprint")
    return value


def parse_signers(output: str) -> list[str]:
    found = []
    for match in PATTERN.finditer(output):
        found.append(normalize_digest(match.group(1)))
    if not found:
        raise ValueError("apksigner certificate digest is missing")
    return sorted(set(found))


def self_test() -> None:
    fingerprint = "a1" * 32
    second = "b2" * 32
    # Real apksigner labels differ across Android Build Tools versions.
    # Confirm the old numbered format, SDK-range format, and new
    # signature-scheme-labeled versions all produce the same identity.
    prefixes = [
        "Signer #1 certificate SHA-256 digest: ",
        "Signer (minSdkVersion=24, maxSdkVersion=35) certificate SHA-256 digest: ",
        "V2 Signer: certificate SHA-256 digest: ",
        "V3.0 Signer: certificate SHA-256 digest: ",
    ]
    for prefix in prefixes:
        assert parse_signers(prefix + fingerprint.upper()) == [fingerprint]
        assert parse_signers(prefix + ":".join(["A1"] * 32)) == [fingerprint]
    both_schemes = (
        prefixes[2] + fingerprint + "\n" + prefixes[3] + fingerprint
    )
    assert parse_signers(both_schemes) == [fingerprint]
    conflicting = prefixes[2] + fingerprint + "\n" + prefixes[3] + second
    assert parse_signers(conflicting) == sorted([fingerprint, second])
    # Public-key digest is not the APK's signing-certificate digest.
    try:
        parse_signers("V2 Signer: public key SHA-256 digest: " + fingerprint)
        raise AssertionError("Accepted a public-key digest as a certificate")
    except ValueError:
        pass
    assert normalize_digest(":".join(["a1"] * 32)) == fingerprint
    for invalid in ["", "a1", "this-is-not-a-digest"]:
        try:
            normalize_digest(invalid)
            raise AssertionError("Accepted an invalid fingerprint")
        except ValueError:
            pass
    try:
        parse_signers("Verified using v2 scheme (APK Signature Scheme v2): true")
        raise AssertionError("Accepted an unsigned APK certificate report")
    except ValueError:
        pass
    print("PASS: all SDK signer labels, conflicting signers and negative checks")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--apksigner", default="apksigner")
    p.add_argument("--out", default="SIGNING-PROVENANCE.json")
    p.add_argument("apks", nargs="*")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.apks:
        p.error("Supply one or more actual compiled APKs")

    expected_raw = os.environ.get("LAN_EXPECTED_SIGNER_SHA256", "").strip()
    require_pinned = os.environ.get("LAN_REQUIRE_PINNED_SIGNER", "0") == "1"
    expected = normalize_digest(expected_raw) if expected_raw else None
    if require_pinned and expected is None:
        raise ValueError("Production signing gate requires a pinned public signer fingerprint")

    rows = []
    signing_sets = set()
    for path in sorted(set(args.apks)):
        apk = Path(path)
        if not apk.is_file() or apk.stat().st_size <= 0:
            raise ValueError(f"Missing or empty APK: {apk}")
        result = subprocess.run(
            [args.apksigner, "verify", "--verbose", "--print-certs", str(apk)],
            check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        signers = parse_signers(result.stdout + "\n" + result.stderr)
        if len(signers) != 1:
            raise ValueError(f"{apk.name} has {len(signers)} different signing certificates")
        signing_sets.add(signers[0])
        rows.append({"apk": apk.name, "signer_sha256": signers[0]})
    if len(signing_sets) != 1:
        raise ValueError("Different ABIs use different signing certificates")
    actual = next(iter(signing_sets))
    if expected is not None and actual != expected:
        raise ValueError(
            f"APK signer mismatch: got {actual}; expected pinned {expected}")
    report = {
        "schema": 1,
        "at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "certificate_sha256": actual,
        "pin_configured": expected is not None,
        "pin_matched": bool(expected is not None and actual == expected),
        # Certificate pinning proves identity MATCH only. The current Flutter
        # runner still uses ephemeral developer signing and has no authenticated
        # provenance of a persistent private release keystore.
        "release_signing_certified": False,
        "signing_key_provenance": "unverified",
        "upgrade_continuity_certified": False,
        "warning": (
            None if expected else
            "Unpinned developer preview signer: signature continuity across "
            "fresh CI runners and previous APKs is NOT established."
        ),
        "apk_signers": rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Signer SHA-256: {actual}")
    print(f"Public signing provenance: {out}")
    if not expected:
        print("WARNING: no pinned signing certificate; not upgrade-safe or production-certified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
