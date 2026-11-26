#!/usr/bin/env python3
"""Regression tests for the pinned ESP32 compiler/toolchain lock and retained evidence."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import verify_esp32_toolchain_lock as verifier
except Exception as exc:
    print(f"PHX-ESP32-TOOLCHAIN-RED: verifier missing or unimportable: {exc}", file=sys.stderr)
    raise SystemExit(1)

LOCK_PATH = ROOT / ".github/locks/esp32-core-toolchains.json"
WORKFLOW_PATH = ROOT / ".github/workflows/phx-release-esp32-core-compatibility.yml"
INDEX_URL = (
    "https://raw.githubusercontent.com/espressif/arduino-esp32/"
    "8f6bee9761f7b15cce27b79cbd1ae199d0df2adf/package_esp32_index.json"
)
UPLOAD_SHA = "cf430e030ddbb5b0abf93d22962f4752f3646cd9"


def synthetic_fixture(root: Path):
    esp32_index = {
        "packages": [
            {
                "name": "esp32",
                "platforms": [
                    {
                        "name": "esp32",
                        "version": "4.0.0",
                        "archiveFileName": "esp32-core-4.0.0.zip",
                        "url": "https://example.invalid/esp32-core-4.0.0.zip",
                        "checksum": "SHA-256:" + "1" * 64,
                        "size": "100",
                        "toolsDependencies": [
                            {"packager": "esp32", "name": "esp-x32", "version": "2512"},
                            {"packager": "arduino", "name": "dfu-util", "version": "0.11.0-arduino5"},
                        ],
                    }
                ],
                "tools": [
                    {
                        "name": "esp-x32",
                        "version": "2512",
                        "systems": [
                            {
                                "host": "x86_64-pc-linux-gnu",
                                "archiveFileName": "esp-x32.tar.gz",
                                "url": "https://example.invalid/esp-x32.tar.gz",
                                "checksum": "SHA-256:" + "2" * 64,
                                "size": "200",
                            }
                        ],
                    }
                ],
            }
        ]
    }
    arduino_index = {
        "packages": [
            {
                "name": "arduino",
                "tools": [
                    {
                        "name": "dfu-util",
                        "version": "0.11.0-arduino5",
                        "systems": [
                            {
                                "host": "x86_64-linux-gnu",
                                "archiveFileName": "dfu-util.tar.gz",
                                "url": "https://example.invalid/dfu-util.tar.gz",
                                "checksum": "SHA-256:" + "3" * 64,
                                "size": "300",
                            }
                        ],
                    }
                ],
            }
        ]
    }
    esp32_bytes = (json.dumps(esp32_index, sort_keys=True) + "\n").encode()
    arduino_bytes = (json.dumps(arduino_index, sort_keys=True) + "\n").encode()
    esp32_path = root / "package_esp32_index.json"
    arduino_path = root / "package_index.json"
    esp32_path.write_bytes(esp32_bytes)
    arduino_path.write_bytes(arduino_bytes)

    lock = {
        "schema": "phx/arduino-esp32-toolchain-lock/v1",
        "source": {
            "url": INDEX_URL,
            "commit": "c" * 40,
            "git_blob_sha1": verifier.git_blob_sha1(esp32_bytes),
        },
        "arduino_cli": {"version": "1.6.0"},
        "cores": {
            "4.0.0": {
                "platform": {
                    "archive_file_name": "esp32-core-4.0.0.zip",
                    "url": "https://example.invalid/esp32-core-4.0.0.zip",
                    "checksum": "SHA-256:" + "1" * 64,
                    "size": "100",
                },
                "tools": [
                    {
                        "packager": "esp32",
                        "name": "esp-x32",
                        "version": "2512",
                        "host": "x86_64-pc-linux-gnu",
                        "archive": {
                            "archive_file_name": "esp-x32.tar.gz",
                            "url": "https://example.invalid/esp-x32.tar.gz",
                            "checksum": "SHA-256:" + "2" * 64,
                            "size": "200",
                        },
                    },
                    {
                        "packager": "arduino",
                        "name": "dfu-util",
                        "version": "0.11.0-arduino5",
                        "host": "x86_64-linux-gnu",
                        "archive": {
                            "archive_file_name": "dfu-util.tar.gz",
                            "url": "https://example.invalid/dfu-util.tar.gz",
                            "checksum": "SHA-256:" + "3" * 64,
                            "size": "300",
                        },
                    },
                ],
                "builtins": [
                    {"packager": "builtin", "name": "ctags", "version": "5.8-arduino12"}
                ],
            }
        },
    }
    packages = root / "packages"
    for relative in (
        "esp32/hardware/esp32/4.0.0",
        "esp32/tools/esp-x32/2512/bin",
        "arduino/tools/dfu-util/0.11.0-arduino5",
        "builtin/tools/ctags/5.8-arduino12",
    ):
        (packages / relative).mkdir(parents=True, exist_ok=True)
    for name in ("xtensa-esp32-elf-gcc", "xtensa-esp32-elf-objdump", "xtensa-esp32-elf-nm"):
        tool = packages / "esp32/tools/esp-x32/2512/bin" / name
        tool.write_text("synthetic tool\n", encoding="utf-8")
        tool.chmod(0o755)
    return lock, packages, esp32_path, arduino_path


class Esp32ToolchainLockTests(unittest.TestCase):
    def test_repository_lock_pins_both_supported_cores_and_archives(self):
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(lock["schema"], "phx/arduino-esp32-toolchain-lock/v1")
        self.assertEqual(lock["source"]["url"], INDEX_URL)
        self.assertRegex(lock["source"]["git_blob_sha1"], r"^[0-9a-f]{40}$")
        self.assertEqual(set(lock["cores"]), {"3.3.13", "4.0.0"})
        self.assertEqual(lock["arduino_cli"]["version"], "1.6.0")
        for version, core in lock["cores"].items():
            with self.subTest(core=version):
                self.assertTrue(core["platform"]["checksum"].startswith("SHA-256:"))
                self.assertTrue(core["tools"])
                for tool in core["tools"]:
                    self.assertTrue(tool["archive"]["url"])
                    self.assertTrue(tool["archive"]["checksum"].startswith("SHA-256:"))
                    self.assertTrue(tool["archive"]["archive_file_name"])
                self.assertTrue(core["builtins"])

    def test_git_blob_sha1_matches_git_object_format(self):
        payload = b"package index fixture\n"
        expected = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        self.assertEqual(verifier.git_blob_sha1(payload), expected)

    def test_synthetic_complete_toolchain_is_admitted(self):
        with tempfile.TemporaryDirectory(prefix="phx-esp32-lock-pass-") as temporary:
            root = Path(temporary)
            lock, packages, esp32_index, arduino_index = synthetic_fixture(root)
            result = verifier.verify_toolchain_lock(
                lock,
                "4.0.0",
                packages,
                esp32_index,
                arduino_index,
                "arduino-cli Version: 1.6.0 Commit: synthetic\n",
                "ID              Installed Latest Name\nesp32:esp32     4.0.0     4.0.0 ESP32 Arduino\n",
            )
            self.assertEqual(result["core_version"], "4.0.0")
            self.assertEqual(result["index"]["git_blob_sha1"], lock["index"]["git_blob_sha1"])
            self.assertEqual(len(result["tools"]), 2)

    def test_missing_tool_package_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="phx-esp32-lock-missing-") as temporary:
            root = Path(temporary)
            lock, packages, esp32_index, arduino_index = synthetic_fixture(root)
            shutil.rmtree(packages / "esp32/tools/esp-x32/2512")
            with self.assertRaisesRegex(ValueError, "esp-x32"):
                verifier.verify_toolchain_lock(
                    lock, "4.0.0", packages, esp32_index, arduino_index,
                    "arduino-cli Version: 1.6.0\n",
                    "ID Installed Latest Name\nesp32:esp32 4.0.0 4.0.0 ESP32 Arduino\n",
                )

    def test_changed_package_index_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="phx-esp32-lock-index-") as temporary:
            root = Path(temporary)
            lock, packages, esp32_index, arduino_index = synthetic_fixture(root)
            esp32_index.write_bytes(esp32_index.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "index blob"):
                verifier.verify_toolchain_lock(
                    lock, "4.0.0", packages, esp32_index, arduino_index,
                    "arduino-cli Version: 1.6.0\n",
                    "ID Installed Latest Name\nesp32:esp32 4.0.0 4.0.0 ESP32 Arduino\n",
                )

    def test_manifest_retains_both_build_hashes_and_ci_only_disposition(self):
        with tempfile.TemporaryDirectory(prefix="phx-esp32-manifest-") as temporary:
            root = Path(temporary)
            lock, packages, esp32_index, arduino_index = synthetic_fixture(root)
            verified = verifier.verify_toolchain_lock(
                lock, "4.0.0", packages, esp32_index, arduino_index,
                "arduino-cli Version: 1.6.0 Commit: synthetic\n",
                "ID Installed Latest Name\nesp32:esp32 4.0.0 4.0.0 ESP32 Arduino\n",
            )
            output = root / "output"
            first = output / "first"
            second = output / "second"
            first.mkdir(parents=True)
            second.mkdir()
            first_bin = first / "BlazePwifiVendo32.ino.bin"
            second_bin = second / "BlazePwifiVendo32.ino.bin"
            first_elf = first / "BlazePwifiVendo32.ino.elf"
            second_elf = second / "BlazePwifiVendo32.ino.elf"
            first_bin.write_bytes(b"synthetic-identical-image")
            second_bin.write_bytes(b"synthetic-identical-image")
            first_elf.write_bytes(b"synthetic-identical-elf")
            second_elf.write_bytes(b"synthetic-identical-elf")
            manifest = verifier.capture_manifest(
                verified,
                lock,
                packages,
                esp32_index,
                arduino_index,
                output,
                "a" * 40,
                "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
                "b" * 40,
                "1795605463",
                "esp32:esp32:esp32",
                first_bin,
                second_bin,
                first_elf,
                second_elf,
                runner_env={"ImageOS": "ubuntu24", "ImageVersion": "synthetic"},
                command_runner=lambda command: "synthetic version output",
            )
            self.assertTrue(manifest["build"]["binary_identical"])
            self.assertTrue(manifest["build"]["elf_identical"])
            self.assertFalse(manifest["release_state"]["production_authorized"])
            self.assertEqual(manifest["evidence_class"], "HOSTED_CI_ONLY")
            self.assertTrue((output / "provenance/package_esp32_index.json").is_file())
            self.assertTrue((output / "provenance/package_index.json").is_file())
            self.assertIn("toolchain-provenance.json", (output / "SHA256SUMS").read_text())

    def test_workflow_pins_index_and_retains_artifact_evidence(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn(INDEX_URL, workflow)
        self.assertIn("python3 .github/scripts/verify_esp32_toolchain_lock.py --phase verify", workflow)
        self.assertIn("python3 .github/scripts/verify_esp32_toolchain_lock.py --phase capture", workflow)
        self.assertIn(f"actions/upload-artifact@{UPLOAD_SHA}", workflow)
        self.assertIn("retention-days: 14", workflow)
        for path in (
            '".github/locks/esp32-core-toolchains.json"',
            '".github/scripts/verify_esp32_toolchain_lock.py"',
            '".github/scripts/test_esp32_toolchain_lock.py"',
        ):
            self.assertEqual(workflow.count(path), 2, path)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Esp32ToolchainLockTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(f"PHX-ESP32-TOOLCHAIN-LOCK-PASS: {result.testsRun} tests")
        raise SystemExit(0)
    raise SystemExit(1)
