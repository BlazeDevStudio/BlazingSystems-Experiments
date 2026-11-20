#!/usr/bin/env python3
"""Guard exact-source ESP32 3.3.13/4.0.0 qualification and app-image identity."""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/phx-release-esp32-core-compatibility.yml"
HELPER = ROOT / ".github/scripts/verify_esp32_application_image.py"
HARDWARE_SOURCE_SHA = "9ef753a38226fcdf56b0903680a5110348027110"
HARDWARE_SKETCH_PATH = (
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
)
HARDWARE_SKETCH_BLOB = "33081c5094ffdd19d935fc888d52ae01ff23325b"
CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
ARDUINO_SETUP_SHA = "b3cda96fddef6af6c56b4c5efb5c47e2357935db"


def fail(message: str) -> int:
    print(f"PHX-RELEASE-ESP32-COMPAT-RED: {message}", file=sys.stderr)
    return 1


def check_application_image_verifier(workflow_content: str) -> list[str]:
    errors: list[str] = []
    invocation = (
        'python3 .github/scripts/verify_esp32_application_image.py '
        '--output-dir "$output_dir" --sketch-name "BlazePwifiVendo32"'
    )
    if workflow_content.count(invocation) != 1:
        errors.append("compatibility workflow must invoke the exact ESP32 application-image verifier exactly once")
    unsafe_selector = (
        'binary="$(find "$output_dir" -maxdepth 1 -type f -name \'*.bin\' -print -quit)"'
    )
    if unsafe_selector in workflow_content:
        errors.append("compatibility workflow still hashes the first arbitrary .bin instead of the sketch application image")
    if not HELPER.is_file():
        errors.append("missing release-owned ESP32 application-image verifier")
        return errors

    spec = importlib.util.spec_from_file_location("verify_esp32_application_image", HELPER)
    if spec is None or spec.loader is None:
        errors.append("cannot load ESP32 application-image verifier")
        return errors
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        errors.append(f"ESP32 application-image verifier cannot be imported: {exc}")
        return errors

    helper_content = HELPER.read_text(encoding="utf-8")
    marker_fields = (
        "PHX-ESP32-APP-IMAGE-PASS:",
        "filename=",
        "size_bytes=",
        "sha256=",
    )
    if any(value not in helper_content for value in marker_fields):
        errors.append("application-image verifier must emit filename, byte length and SHA-256")

    def expect_rejected(label: str, directory: Path, sketch_name: str = "BlazePwifiVendo32") -> None:
        try:
            module.inspect_application_image(directory, sketch_name)
        except (OSError, ValueError):
            return
        errors.append(f"application-image verifier accepted invalid case: {label}")

    with tempfile.TemporaryDirectory(prefix="phx-app-image-positive-") as temporary:
        directory = Path(temporary)
        payload = b"synthetic-esp32-application-image-v1"
        (directory / "bootloader.bin").write_bytes(b"bootloader")
        (directory / "partitions.bin").write_bytes(b"partition-table")
        (directory / "boot_app0.bin").write_bytes(b"boot-app")
        (directory / "BlazePwifiVendo32.ino.bin").write_bytes(payload)
        try:
            filename, size, digest = module.inspect_application_image(directory, "BlazePwifiVendo32")
            if filename != "BlazePwifiVendo32.ino.bin":
                errors.append(f"application-image verifier selected unexpected file: {filename}")
            if size != len(payload):
                errors.append(f"application-image verifier reported wrong byte length: {size}")
            if digest != hashlib.sha256(payload).hexdigest():
                errors.append("application-image verifier reported a digest that does not match the sketch application bytes")
        except Exception as exc:
            errors.append(f"application-image verifier rejected the valid synthetic image: {exc}")

    with tempfile.TemporaryDirectory(prefix="phx-app-image-missing-") as temporary:
        directory = Path(temporary)
        (directory / "bootloader.bin").write_bytes(b"bootloader")
        (directory / "partitions.bin").write_bytes(b"partition-table")
        expect_rejected("missing application image", directory)

    with tempfile.TemporaryDirectory(prefix="phx-app-image-wrong-name-") as temporary:
        directory = Path(temporary)
        (directory / "OtherSketch.ino.bin").write_bytes(b"wrong-sketch")
        expect_rejected("wrong sketch application filename", directory)

    with tempfile.TemporaryDirectory(prefix="phx-app-image-ambiguous-") as temporary:
        directory = Path(temporary)
        (directory / "BlazePwifiVendo32.ino.bin").write_bytes(b"expected")
        (directory / "OtherSketch.ino.bin").write_bytes(b"second-app")
        expect_rejected("multiple sketch application candidates", directory)

    with tempfile.TemporaryDirectory(prefix="phx-app-image-empty-") as temporary:
        directory = Path(temporary)
        (directory / "BlazePwifiVendo32.ino.bin").write_bytes(b"")
        expect_rejected("empty application image", directory)

    with tempfile.TemporaryDirectory(prefix="phx-app-image-symlink-") as temporary:
        root = Path(temporary)
        directory = root / "output"
        directory.mkdir()
        cached = root / "cached.ino.bin"
        cached.write_bytes(b"cached-payload")
        (directory / "BlazePwifiVendo32.ino.bin").symlink_to(cached)
        expect_rejected("symlinked application image", directory)

    with tempfile.TemporaryDirectory(prefix="phx-app-image-hardlink-") as temporary:
        root = Path(temporary)
        directory = root / "output"
        directory.mkdir()
        cached = root / "cached-payload.bin"
        cached.write_bytes(b"cached-payload")
        try:
            os.link(cached, directory / "BlazePwifiVendo32.ino.bin")
        except (OSError, NotImplementedError) as exc:
            errors.append(f"test environment cannot create hard-link negative control: {exc}")
        else:
            expect_rejected("hard-linked application image", directory)

    with tempfile.TemporaryDirectory(prefix="phx-app-image-output-link-") as temporary:
        root = Path(temporary)
        real_directory = root / "real-output"
        real_directory.mkdir()
        (real_directory / "BlazePwifiVendo32.ino.bin").write_bytes(b"application")
        alias = root / "output-link"
        alias.symlink_to(real_directory, target_is_directory=True)
        expect_rejected("symlinked output directory", alias)

    if errors:
        return errors
    print("PHX-ESP32-APP-IMAGE-TESTS-PASS: exact candidate, filename, size, SHA-256, missing, wrong-name, ambiguous, empty, symlink and hard-link controls")
    return errors


def main() -> int:
    if not WORKFLOW.is_file():
        return fail("missing exact-source ESP32 core compatibility workflow")

    content = WORKFLOW.read_text(encoding="utf-8")
    required = (
        HARDWARE_SOURCE_SHA,
        HARDWARE_SKETCH_PATH,
        HARDWARE_SKETCH_BLOB,
        'esp32_core: ["3.3.13", "4.0.0"]',
        'arduino-cli core install "esp32:esp32@\u0024{{ matrix.esp32_core }}"',
        "arduino-cli compile --fqbn esp32:esp32:esp32",
        "hardware-source/",
        "persist-credentials: false",
        "contents: read",
        "cancel-in-progress: false",
        "workflow_dispatch:",
        "pull_request:",
        '"draft/softtimer-future-release-signing-pipeline-20261029"',
    )
    missing = [value for value in required if value not in content]
    if missing:
        return fail("compatibility workflow is missing required contract values: " + ", ".join(missing))

    if content.count(f"ref: {HARDWARE_SOURCE_SHA}") != 1:
        return fail("hardware source must be checked out exactly once at the pinned commit")
    if content.count(f'EXPECTED_SOURCE_SHA: "{HARDWARE_SOURCE_SHA}"') != 1:
        return fail("workflow must independently assert the pinned hardware source HEAD")
    if content.count(f'EXPECTED_SKETCH_BLOB: "{HARDWARE_SKETCH_BLOB}"') != 1:
        return fail("workflow must independently assert the exact sketch Git blob")
    if content.count("persist-credentials: false") != 2:
        return fail("both checkouts must disable persisted credentials")

    application_errors = check_application_image_verifier(content)
    if application_errors:
        for error in application_errors:
            print(f"PHX-RELEASE-ESP32-APP-IMAGE-RED: {error}", file=sys.stderr)
        return 1

    pin_guard_path = ROOT / ".github/scripts/test_release_artifact_action_pins.py"
    if not pin_guard_path.is_file():
        return fail("missing immutable-action pin guard")
    pin_guard = pin_guard_path.read_text(encoding="utf-8")
    workflow_marker = '".github/workflows/phx-release-esp32-core-compatibility.yml": {'
    start = pin_guard.find(workflow_marker)
    if start < 0:
        return fail("immutable-action pin guard does not include the compatibility workflow")
    end = pin_guard.find("    },", start)
    if end < 0:
        return fail("compatibility workflow action-pin entry is malformed")
    pin_entry = pin_guard[start:end]
    if '"actions/checkout": 2' not in pin_entry or '"arduino/setup-arduino-cli": 1' not in pin_entry:
        return fail("compatibility workflow action-pin counts are not 2 checkout + 1 Arduino setup")

    action_refs = re.findall(
        r"(?m)^\s*(?:-\s*)?uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)",
        content,
    )
    expected = {
        "actions/checkout": (CHECKOUT_SHA, 2),
        "arduino/setup-arduino-cli": (ARDUINO_SETUP_SHA, 1),
    }
    found: dict[str, list[str]] = {}
    for name, ref in action_refs:
        found.setdefault(name, []).append(ref)
    if set(found) != set(expected):
        return fail(f"unexpected external actions: {sorted(set(found) ^ set(expected))}")
    for name, (sha, count) in expected.items():
        refs = found.get(name, [])
        if len(refs) != count or any(ref != sha or not re.fullmatch(r"[0-9a-f]{40}", ref) for ref in refs):
            return fail(f"{name} must use {count} immutable invocation(s) at {sha}; found {refs}")

    forbidden = (
        "actions/upload-artifact",
        "contents: write",
        "gh release",
        "esptool",
        "espflash",
        "\u0024{{ secrets.",
    )
    present = [value for value in forbidden if value in content]
    if present:
        return fail("compatibility workflow must remain read-only/build-only: " + ", ".join(present))

    print(
        "PHX-RELEASE-ESP32-COMPAT-PASS: exact hardware source, sketch blob, "
        "read-only permissions, immutable actions and 3.3.13/4.0.0 matrix"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
