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
REPRODUCIBLE_HELPER = ROOT / ".github/scripts/verify_esp32_reproducible_build.py"
SYMBOL_HELPER = ROOT / ".github/scripts/inspect_esp32_elf_symbols.py"
SYMBOL_TEST = ROOT / ".github/scripts/test_inspect_esp32_elf_symbols.py"
HARDWARE_SOURCE_SHA = "369007bcbc684a0923a586e991f3aa0667cda105"
HARDWARE_SKETCH_PATH = (
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
)
HARDWARE_SKETCH_BLOB = "1458f32881d3b340f1101dd0215618b54c1b688b"
CHECKOUT_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
ARDUINO_SETUP_SHA = "b3cda96fddef6af6c56b4c5efb5c47e2357935db"


def fail(message: str) -> int:
    print(f"PHX-RELEASE-ESP32-COMPAT-RED: {message}", file=sys.stderr)
    return 1


def check_application_image_verifier(workflow_content: str) -> list[str]:
    errors: list[str] = []
    invocations = (
        'python3 .github/scripts/verify_esp32_application_image.py '
        '--output-dir "$first_output_dir" --sketch-name "BlazePwifiVendo32"',
        'python3 .github/scripts/verify_esp32_application_image.py '
        '--output-dir "$second_output_dir" --sketch-name "BlazePwifiVendo32"',
    )
    if any(workflow_content.count(invocation) != 1 for invocation in invocations):
        errors.append("compatibility workflow must verify each clean-build application image exactly once")
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



def check_reproducible_build_verifier(workflow_content: str) -> list[str]:
    errors: list[str] = []
    if not REPRODUCIBLE_HELPER.is_file():
        return ["missing release-owned ESP32 reproducible-build verifier"]

    spec = importlib.util.spec_from_file_location("verify_esp32_reproducible_build", REPRODUCIBLE_HELPER)
    if spec is None or spec.loader is None:
        return ["cannot load ESP32 reproducible-build verifier"]
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        return [f"ESP32 reproducible-build verifier cannot be imported: {exc}"]

    expected_name = "BlazePwifiVendo32.ino.bin"

    with tempfile.TemporaryDirectory(prefix="phx-reproducible-identical-") as temporary:
        root = Path(temporary)
        first_dir = root / "first"
        second_dir = root / "second"
        first_dir.mkdir()
        second_dir.mkdir()
        payload = b"same-source-same-toolchain-deterministic-image"
        first = first_dir / expected_name
        second = second_dir / expected_name
        first.write_bytes(payload)
        second.write_bytes(payload)
        try:
            filename, size, digest = module.compare_application_images(
                first, second, "BlazePwifiVendo32"
            )
            if filename != expected_name:
                errors.append(f"reproducibility verifier returned unexpected filename: {filename}")
            if size != len(payload):
                errors.append(f"reproducibility verifier returned wrong byte length: {size}")
            if digest != hashlib.sha256(payload).hexdigest():
                errors.append("reproducibility verifier returned an incorrect matching-image digest")
        except Exception as exc:
            errors.append(f"reproducibility verifier rejected identical images: {exc}")

    with tempfile.TemporaryDirectory(prefix="phx-reproducible-different-bytes-") as temporary:
        root = Path(temporary)
        first = root / "first" / expected_name
        second = root / "second" / expected_name
        first.parent.mkdir()
        second.parent.mkdir()
        first.write_bytes(b"same-length-A")
        second.write_bytes(b"same-length-B")
        try:
            module.compare_application_images(first, second, "BlazePwifiVendo32")
        except ValueError as exc:
            if "first_differences=" not in str(exc) or "sha256" not in str(exc):
                errors.append("different-byte rejection must report both SHA-256 values and first differing offsets")
        except Exception as exc:
            errors.append(f"different-byte case raised an unexpected exception: {exc}")
        else:
            errors.append("reproducibility verifier accepted different same-length application images")

    with tempfile.TemporaryDirectory(prefix="phx-reproducible-size-mismatch-") as temporary:
        root = Path(temporary)
        first = root / "first" / expected_name
        second = root / "second" / expected_name
        first.parent.mkdir()
        second.parent.mkdir()
        first.write_bytes(b"short")
        second.write_bytes(b"longer")
        try:
            module.compare_application_images(first, second, "BlazePwifiVendo32")
        except ValueError:
            pass
        except Exception as exc:
            errors.append(f"size-mismatch case raised an unexpected exception: {exc}")
        else:
            errors.append("reproducibility verifier accepted different image lengths")

    with tempfile.TemporaryDirectory(prefix="phx-reproducible-symlink-") as temporary:
        root = Path(temporary)
        first = root / "first" / expected_name
        second = root / "second" / expected_name
        first.parent.mkdir()
        second.parent.mkdir()
        outside = root / "outside.bin"
        outside.write_bytes(b"outside-image")
        first.symlink_to(outside)
        second.write_bytes(b"outside-image")
        try:
            module.compare_application_images(first, second, "BlazePwifiVendo32")
        except (OSError, ValueError):
            pass
        except Exception as exc:
            errors.append(f"symlink case raised an unexpected exception: {exc}")
        else:
            errors.append("reproducibility verifier accepted a symlinked image")

    with tempfile.TemporaryDirectory(prefix="phx-reproducible-hardlink-") as temporary:
        root = Path(temporary)
        first = root / "first" / expected_name
        second = root / "second" / expected_name
        first.parent.mkdir()
        second.parent.mkdir()
        cached = root / "cached.bin"
        cached.write_bytes(b"hard-linked-image")
        try:
            os.link(cached, first)
        except (OSError, NotImplementedError) as exc:
            errors.append(f"test environment cannot create hard-link negative control: {exc}")
        else:
            second.write_bytes(b"hard-linked-image")
            try:
                module.compare_application_images(first, second, "BlazePwifiVendo32")
            except (OSError, ValueError):
                pass
            except Exception as exc:
                errors.append(f"hard-link case raised an unexpected exception: {exc}")
            else:
                errors.append("reproducibility verifier accepted a hard-linked image")

    with tempfile.TemporaryDirectory(prefix="phx-reproducible-wrong-name-") as temporary:
        root = Path(temporary)
        first = root / "first" / "wrong.bin"
        second = root / "second" / expected_name
        first.parent.mkdir()
        second.parent.mkdir()
        first.write_bytes(b"same")
        second.write_bytes(b"same")
        try:
            module.compare_application_images(first, second, "BlazePwifiVendo32")
        except (OSError, ValueError):
            pass
        except Exception as exc:
            errors.append(f"wrong-name case raised an unexpected exception: {exc}")
        else:
            errors.append("reproducibility verifier accepted an incorrectly named application image")

    compile_prefix = 'arduino-cli compile --clean --fqbn esp32:esp32:esp32 --build-path "$build_dir"'
    if workflow_content.count(compile_prefix) != 2:
        errors.append("compatibility workflow must perform exactly two clean builds with the same build path")
    if workflow_content.count('--output-dir "$first_output_dir"') != 2:
        errors.append("compatibility workflow must preserve the first build in its own output directory")
    if workflow_content.count('--output-dir "$second_output_dir"') != 2:
        errors.append("compatibility workflow must preserve the second build in its own output directory")
    if workflow_content.count('"$sketch_dir"') != 2:
        errors.append("both reproducibility builds must compile the same exact sketch directory")
    if workflow_content.count("python3 .github/scripts/verify_esp32_application_image.py") != 2:
        errors.append("both build outputs must pass the exact application-image verifier")
    compare_invocation = (
        'python3 .github/scripts/verify_esp32_reproducible_build.py '
        '--first "$first_output_dir/BlazePwifiVendo32.ino.bin" '
        '--second "$second_output_dir/BlazePwifiVendo32.ino.bin" '
        '--sketch-name "BlazePwifiVendo32"'
    )
    if workflow_content.count(compare_invocation) != 1:
        errors.append("compatibility workflow must compare the two exact sketch application images once")
    if workflow_content.count('".github/scripts/verify_esp32_reproducible_build.py"') != 2:
        errors.append("reproducibility helper must be included in both workflow path filters")


    helper_source = REPRODUCIBLE_HELPER.read_text(encoding="utf-8")
    for marker in (
        "ESP_APP_DESC_MAGIC_WORD",
        "ESP_APP_DESC_APP_ELF_SHA256_OFFSET",
        "difference_ranges=",
        "classification=",
    ):
        if marker not in helper_source:
            errors.append(f"reproducibility verifier is missing ESP32 image diagnostic marker: {marker}")

    def synthetic_esp32_image(elf_sha: bytes, app_magic: int = 0xABCD5432) -> bytes:
        if len(elf_sha) != 32:
            raise ValueError("synthetic ELF SHA must be exactly 32 bytes")
        image = bytearray(32 + 256)
        image[0] = 0xE9
        image[1] = 1
        image[24:28] = (0x3F400020).to_bytes(4, "little")
        image[28:32] = (256).to_bytes(4, "little")
        image[32:36] = app_magic.to_bytes(4, "little")
        image[176:208] = elf_sha
        return bytes(image)

    def expect_classification(
        label: str,
        first_payload: bytes,
        second_payload: bytes,
        expected_classification: str,
        required_fragments: tuple[str, ...] = (),
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="phx-reproducible-esp-desc-") as temporary:
            root = Path(temporary)
            first = root / "first" / expected_name
            second = root / "second" / expected_name
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(first_payload)
            second.write_bytes(second_payload)
            try:
                module.compare_application_images(first, second, "BlazePwifiVendo32")
            except ValueError as exc:
                message = str(exc)
                if f"classification={expected_classification}" not in message:
                    errors.append(
                        f"{label}: expected classification {expected_classification}; got {message}"
                    )
                for fragment in required_fragments:
                    if fragment not in message:
                        errors.append(f"{label}: diagnostic omitted {fragment}")
            except Exception as exc:
                errors.append(f"{label}: unexpected diagnostic exception: {exc}")
            else:
                errors.append(f"{label}: reproducibility verifier accepted different images")

    elf_sha_a = bytes(range(32))
    elf_sha_b = bytes(reversed(range(32)))
    expect_classification(
        "only ESP app ELF SHA field differs",
        synthetic_esp32_image(elf_sha_a),
        synthetic_esp32_image(elf_sha_b),
        "ESP_APP_DESC_APP_ELF_SHA256_ONLY",
        (
            "difference_ranges=['176-207']",
            "differing_bytes=32",
            f"app_elf_sha256_first={elf_sha_a.hex()}",
            f"app_elf_sha256_second={elf_sha_b.hex()}",
        ),
    )

    image_a = bytearray(synthetic_esp32_image(elf_sha_a))
    image_b = bytearray(image_a)
    image_b[240] ^= 0x01
    expect_classification(
        "non-descriptor application content differs",
        bytes(image_a),
        bytes(image_b),
        "OTHER_IMAGE_CONTENT_DIFF",
        ("difference_ranges=['240-240']", "differing_bytes=1"),
    )

    expect_classification(
        "invalid ESP app descriptor magic is not classified as ELF-SHA-only",
        synthetic_esp32_image(elf_sha_a),
        synthetic_esp32_image(elf_sha_a, app_magic=0x12345678),
        "UNCLASSIFIED_IMAGE_DIFF",
        ("difference_ranges=['32-35']",),
    )


    def synthetic_segmented_image(elf_sha: bytes) -> bytes:
        if len(elf_sha) != 32:
            raise ValueError("synthetic ELF SHA must be exactly 32 bytes")
        first_segment_size = 10000
        second_segment_size = 64
        first_data_start = 32
        second_header_start = first_data_start + first_segment_size
        second_data_start = second_header_start + 8
        segments_end = second_data_start + second_segment_size
        checksum_offset = ((segments_end // 16) + 1) * 16 - 1
        image = bytearray(checksum_offset + 1 + 32)
        image[0] = 0xE9
        image[1] = 2
        image[23] = 1
        image[24:28] = (0x3F400020).to_bytes(4, "little")
        image[28:32] = first_segment_size.to_bytes(4, "little")
        image[first_data_start:second_header_start] = b"\xA5" * first_segment_size
        image[second_header_start:second_header_start + 4] = (0x3F800000).to_bytes(4, "little")
        image[second_header_start + 4:second_data_start] = second_segment_size.to_bytes(4, "little")
        image[second_data_start:segments_end] = b"\x5A" * second_segment_size
        image[32:36] = (0xABCD5432).to_bytes(4, "little")
        image[176:208] = elf_sha
        image[checksum_offset] = 0xEF
        image[checksum_offset + 1:checksum_offset + 33] = bytes(range(32))
        return bytes(image)

    def expect_layout_diff(
        label: str,
        first_payload: bytes,
        second_payload: bytes,
        required_fragments: tuple[str, ...],
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="phx-reproducible-layout-") as temporary:
            root = Path(temporary)
            first = root / "first" / expected_name
            second = root / "second" / expected_name
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(first_payload)
            second.write_bytes(second_payload)
            try:
                module.compare_application_images(first, second, "BlazePwifiVendo32")
            except ValueError as exc:
                message = str(exc)
                for fragment in required_fragments:
                    if fragment not in message:
                        errors.append(f"{label}: diagnostic omitted {fragment}: {message}")
            except Exception as exc:
                errors.append(f"{label}: unexpected diagnostic exception: {exc}")
            else:
                errors.append(f"{label}: reproducibility verifier accepted different images")

    segmented = synthetic_segmented_image(elf_sha_a)
    segment_mutation = bytearray(segmented)
    for changed_offset in (9714, 9716, 9717):
        segment_mutation[changed_offset] ^= 0x01
    expect_layout_diff(
        "actual drift offsets map to the ESP image segment",
        segmented,
        bytes(segment_mutation),
        (
            "difference_ranges=['9714-9714', '9716-9717']",
            "difference_regions_first=",
            "segment[0]_data",
            "load_addr=0x3f400020",
            "checksum_offset=10111",
        ),
    )

    second_segment_mutation = bytearray(segmented)
    second_segment_mutation[10043] ^= 0x01
    expect_layout_diff(
        "second segment data is mapped independently",
        segmented,
        bytes(second_segment_mutation),
        ("segment[1]_data", "load_addr=0x3f800000"),
    )

    checksum_mutation = bytearray(segmented)
    checksum_mutation[10111] ^= 0x01
    expect_layout_diff(
        "ESP image checksum byte is classified separately",
        segmented,
        bytes(checksum_mutation),
        ("10111-10111:image_checksum",),
    )

    appended_hash_mutation = bytearray(segmented)
    appended_hash_mutation[10112] ^= 0x01
    expect_layout_diff(
        "appended ESP image SHA is classified separately",
        segmented,
        bytes(appended_hash_mutation),
        ("10112-10112:appended_sha256",),
    )

    if errors:
        return errors
    print(
        "PHX-ESP32-REPRODUCIBILITY-TESTS-PASS: identical, changed bytes, "
        "size mismatch, symlink, hard-link, wrong filename and two-clean-build workflow"
    )
    return errors

def check_elf_symbol_inspector(workflow_content: str) -> list[str]:
    errors: list[str] = []
    if not SYMBOL_HELPER.is_file():
        errors.append("missing release-owned ESP32 ELF symbol inspector")
    if not SYMBOL_TEST.is_file():
        errors.append("missing release-owned ESP32 ELF symbol regression suite")

    for relative_path in (
        ".github/scripts/inspect_esp32_elf_symbols.py",
        ".github/scripts/test_inspect_esp32_elf_symbols.py",
    ):
        if workflow_content.count(f'"{relative_path}"') != 2:
            errors.append(f"{relative_path} must appear in both compatibility workflow path filters")

    test_step = "      - name: Test release-owned ESP32 ELF symbol inspector"
    if workflow_content.count(test_step) != 1:
        errors.append("compatibility workflow must run the ELF symbol inspector test step exactly once")
    if workflow_content.count("python3 .github/scripts/test_inspect_esp32_elf_symbols.py") != 1:
        errors.append("compatibility workflow must invoke the ELF symbol regression suite exactly once")
    if workflow_content.count("python3 .github/scripts/test_phx_release_esp32_core_compatibility.py") != 1:
        errors.append("compatibility workflow must run its exact-source static contract guard exactly once")

    required_workflow_values = (
        'local nm_path="$compiler_path/xtensa-esp32-elf-nm"',
        'if [ ! -x "$nm_path" ]',
        '"$nm_path" --version',
        "--format=posix --print-size --numeric-sort --defined-only",
        'python3 .github/scripts/inspect_esp32_elf_symbols.py',
        '--section ".flash.rodata"',
        '--nm-output "$first_output_dir/elf-symbols.txt"',
        '--nm-output "$second_output_dir/elf-symbols.txt"',
    )
    for value in required_workflow_values:
        if value not in workflow_content:
            errors.append(f"compatibility workflow is missing exact ELF symbol provenance step: {value}")
    if workflow_content.count("python3 .github/scripts/inspect_esp32_elf_symbols.py") != 2:
        errors.append("both preserved ELF files must be mapped to symbols exactly once")

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
        "arduino-cli compile --clean --fqbn esp32:esp32:esp32",
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

    reproducibility_errors = check_reproducible_build_verifier(content)
    if reproducibility_errors:
        for error in reproducibility_errors:
            print(f"PHX-RELEASE-ESP32-REPRODUCIBILITY-RED: {error}", file=sys.stderr)
        return 1

    symbol_errors = check_elf_symbol_inspector(content)
    if symbol_errors:
        for error in symbol_errors:
            print(f"PHX-RELEASE-ESP32-ELF-SYMBOL-RED: {error}", file=sys.stderr)
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
