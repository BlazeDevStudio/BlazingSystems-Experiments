#!/usr/bin/env python3
"""Read-only APK installation-identity gate for the legacy BlazeRental launcher.

Does not sign, install, provision, modify devices, or infer physical compatibility.
Requires Android SDK aapt and apksigner on PATH (or explicit arguments).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

PACKAGE = "com.blazesystems.blazerental"
# Published BlazeRental-production-lineage2 certificate (v0.5.2 onward).
LINEAGE2_SHA256 = "1a18d58e1f95559689102071f56c93e9b9d2ea6be40e6f207006c98962a16a25"


class ContractError(ValueError):
    pass


def required_match(pattern, output, label):
    match = re.search(pattern, output, re.MULTILINE)
    if not match:
        raise ContractError("missing " + label + " in tool output")
    return match


def inspect_text(badging, signature, *, mode, min_api=21, minimum_version_code=50300,
                 required_abis=(), embedded_abis=()):
    """Validate captured SDK tool output; returns machine-readable observations."""
    package = required_match(r"^package: name='([^']+)' versionCode='(\d+)'", badging,
                             "package identity/versionCode")
    name, version_code = package.group(1), int(package.group(2))
    min_sdk = int(required_match(r"^sdkVersion:'(\d+)'", badging,
                                 "manifest minSdkVersion").group(1))
    expected_name = PACKAGE + (".debug" if mode == "debug" else "")
    if name != expected_name:
        raise ContractError("package %s is not expected %s" % (name, expected_name))
    if min_sdk > min_api:
        raise ContractError("minSdkVersion %s excludes required API %s" % (min_sdk, min_api))
    if version_code < minimum_version_code:
        raise ContractError("versionCode %s is below required floor %s" %
                            (version_code, minimum_version_code))

    # Android 5.x/6.x cannot verify an APK that is *only* signed with v2/v3.
    v1 = required_match(r"^Verified using v1 scheme \(JAR signing\): (true|false)$",
                        signature, "v1 signing result").group(1) == "true"
    if min_api < 24 and not v1:
        raise ContractError("API %s requires verified v1/JAR APK signing" % min_api)
    signer_count = int(required_match(r"^Number of signers: (\d+)$", signature,
                                      "signer count").group(1))
    if signer_count != 1:
        raise ContractError("expected exactly one APK signer; found %s" % signer_count)
    fingerprint = required_match(
        r"^Signer #1 certificate SHA-256 digest: ([0-9a-fA-F:]{64,95})$",
        signature, "certificate fingerprint").group(1).replace(":", "").lower()
    if len(fingerprint) != 64:
        raise ContractError("certificate digest is not a SHA-256 fingerprint")
    if mode == "production" and fingerprint != LINEAGE2_SHA256:
        raise ContractError("production signing certificate differs from Lineage 2")

    native_abis = sorted(set(embedded_abis))
    if native_abis and not set(required_abis).issubset(native_abis):
        missing = sorted(set(required_abis) - set(native_abis))
        raise ContractError("APK lacks native libraries for required ABI(s): " +
                            ", ".join(missing))
    return {"package": name, "versionCode": version_code, "minSdk": min_sdk,
            "v1SigningVerified": v1, "signerSha256": fingerprint,
            "embeddedNativeAbis": native_abis,
            "requiredAbis": sorted(set(required_abis)),
            "noNativeLibraries": not bool(native_abis),
            "note": "Static checks only; installation and runtime remain NOT EXECUTED"}


def sdk_output(command):
    try:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=False, timeout=90)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError("cannot execute required SDK tool: " + str(exc)) from exc
    if result.returncode:
        raise ContractError("SDK verification failed (%s): %s" %
                            (command[0], result.stderr.strip()[:800]))
    return result.stdout


def embedded_native_abis(apk):
    try:
        with zipfile.ZipFile(apk) as archive:
            return sorted({part.split("/")[1] for part in archive.namelist()
                           if part.startswith("lib/") and part.endswith(".so")
                           and len(part.split("/")) >= 3})
    except (OSError, zipfile.BadZipFile) as exc:
        raise ContractError("APK is not a readable ZIP archive: " + str(exc)) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--mode", choices=("debug", "production"), required=True)
    parser.add_argument("--min-api", type=int, default=21)
    parser.add_argument("--minimum-version-code", type=int, default=50300)
    parser.add_argument("--required-abi", action="append", default=[])
    parser.add_argument("--aapt", default="aapt")
    parser.add_argument("--apksigner", default="apksigner")
    args = parser.parse_args(argv)
    try:
        if not args.apk.is_file():
            raise ContractError("APK file not found: " + str(args.apk))
        if args.min_api < 21:
            raise ContractError("this audit targets the API 21+ Launcher3 lineage")
        badging = sdk_output([args.aapt, "dump", "badging", str(args.apk)])
        signature = sdk_output([args.apksigner, "verify", "--verbose", "--print-certs",
                                "--min-sdk-version", str(args.min_api), str(args.apk)])
        result = inspect_text(badging, signature, mode=args.mode, min_api=args.min_api,
                              minimum_version_code=args.minimum_version_code,
                              required_abis=args.required_abi,
                              embedded_abis=embedded_native_abis(args.apk))
        digest = hashlib.sha256()
        with args.apk.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        result["apkSha256"] = digest.hexdigest()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except ContractError as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
