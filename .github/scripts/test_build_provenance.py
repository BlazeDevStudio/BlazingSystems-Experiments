#!/usr/bin/env python3
"""Negative and positive tests for release artifact provenance sidecars."""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import write_build_provenance as provenance
except Exception as exc:  # The test-first commit must fail before the helper exists.
    print(f"RELEASE-PROVENANCE-RED: release helper is absent or unimportable: {exc}", file=sys.stderr)
    raise SystemExit(1)

SOURCE_SHA = "a" * 40
BLOB_SHA = "b" * 40
ENV = {
    "GITHUB_SHA": SOURCE_SHA,
    "PHX_SOURCE_HEAD_SHA": SOURCE_SHA,
    "PHX_SOURCE_BASE_SHA": "",
    "GITHUB_REPOSITORY": "BlazeDevStudio/BlazingSystems-Experiments",
    "GITHUB_REF": "refs/heads/phoenix/release-publisher-isolation-20261115",
    "GITHUB_WORKFLOW": "BlazePwifi build",
    "GITHUB_WORKFLOW_REF": "BlazeDevStudio/BlazingSystems-Experiments/.github/workflows/blazepwifi-build.yml@refs/heads/phoenix/release-publisher-isolation-20261115",
    "GITHUB_WORKFLOW_SHA": "c" * 40,
    "GITHUB_RUN_ID": "44477700001",
    "GITHUB_RUN_ATTEMPT": "1",
    "RUNNER_OS": "Linux",
    "RUNNER_ARCH": "X64",
}


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checksums(root: Path) -> None:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        rows.append(f"{checksum(path)}  {path.relative_to(root).as_posix()}")
    (root / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")


def build_manifest(root: Path, target: str = "ruijie", paid: str = "0") -> None:
    (root / "BUILD-MANIFEST.txt").write_text(
        "\n".join(
            [
                "BlazePwifi version: 0.5.3",
                "OpenWrt version: 25.12.5",
                f"Target: {target}",
                "OpenWrt target: ramips/mt7621",
                "Profile: ruijie_rg-ew1200g-pro-v1.1",
                "Capability: lite",
                "Generated: 2026-11-19T07:00:00Z",
                f"Paid authority installed preview: {paid}",
                "Paid v2 commit/replay authorized: 0",
                "Customer install authorized: 0",
                "",
            ]
        ),
        encoding="utf-8",
    )


def fake_run(command, **kwargs):
    args = [str(part) for part in command]
    if args[:3] == ["git", "rev-parse", "HEAD"]:
        return SimpleNamespace(returncode=0, stdout=SOURCE_SHA + "\n", stderr="")
    if args[:2] == ["git", "rev-parse"] and len(args) == 3 and args[2].startswith("HEAD:"):
        return SimpleNamespace(returncode=0, stdout=BLOB_SHA + "\n", stderr="")
    if args[:3] == ["git", "diff", "--quiet"]:
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    if args == ["arduino-cli", "version"]:
        return SimpleNamespace(returncode=0, stdout="arduino-cli Version: 1.6.0 Commit: test\n", stderr="")
    if args == ["arduino-cli", "core", "list"]:
        return SimpleNamespace(
            returncode=0,
            stdout=(
                "ID              Installed Latest Name\n"
                "esp32:esp32     3.3.13    3.3.13 ESP32 Arduino\n"
                "esp8266:esp8266 3.1.2     3.1.2  ESP8266\n"
            ),
            stderr="",
        )
    if args == ["zstd", "--version"]:
        return SimpleNamespace(returncode=0, stdout="*** Zstandard CLI v1.5.6 ***\n", stderr="")
    if args == ["curl", "--version"]:
        return SimpleNamespace(returncode=0, stdout="curl 8.14.1 test-build\n", stderr="")
    if args == ["make", "--version"]:
        return SimpleNamespace(returncode=0, stdout="GNU Make 4.3\n", stderr="")
    raise AssertionError(f"Unexpected subprocess command: {args}")


class BuildProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifact = self.root / "artifact"
        self.artifact.mkdir()
        self.env = dict(ENV)
        self.patcher = patch.object(provenance.subprocess, "run", side_effect=fake_run)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def openwrt_fixture(self, paid="0"):
        (self.artifact / "ruijie-sysupgrade.bin").write_bytes(b"synthetic-not-firmware")
        build_manifest(self.artifact, paid=paid)
        write_checksums(self.artifact)
        work = self.root / "imagebuilder-work"
        work.mkdir()
        archive = work / "openwrt-imagebuilder-25.12.5-ramips-mt7621.Linux-x86_64.tar.zst"
        archive.write_bytes(b"synthetic-imagebuilder-archive")
        (work / "sha256sums").write_text(
            f"{checksum(archive)}  {archive.name}\n", encoding="utf-8"
        )
        return work

    def arduino_fixture(self):
        (self.artifact / "source").mkdir()
        (self.artifact / "source" / "BlazePwifiVendo.ino").write_text(
            "void setup() {}\\nvoid loop() {}\\n", encoding="utf-8"
        )
        (self.artifact / "BlazePwifiVendo.ino.bin").write_bytes(b"synthetic-not-firmware")
        write_checksums(self.artifact)

    def test_openwrt_manifest_records_exact_source_and_archive_digest(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        result = provenance.write_provenance(args, env=self.env)
        self.assertEqual(result["source"]["commit"], SOURCE_SHA)
        self.assertEqual(result["toolchain"]["imagebuilder_version"], "25.12.5")
        self.assertEqual(
            result["toolchain"]["imagebuilder_archive_sha256"],
            checksum(work / "openwrt-imagebuilder-25.12.5-ramips-mt7621.Linux-x86_64.tar.zst"),
        )
        self.assertFalse(result["release_state"]["production_authorized"])
        self.assertTrue((self.artifact / "BUILD-PROVENANCE.json").is_file())
        self.assertIn("BUILD-PROVENANCE.json", (self.artifact / "SHA256SUMS").read_text())

    def test_arduino_manifest_records_observed_cli_core_and_sketch(self):
        self.arduino_fixture()
        args = provenance.build_args(
            kind="esp8266",
            target="esp8266",
            artifact_dir=self.artifact,
            core_package="esp8266:esp8266",
            core_version="3.1.2",
            fqbn="esp8266:esp8266:nodemcuv2",
            sketch="experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
        )
        result = provenance.write_provenance(args, env=self.env)
        self.assertEqual(result["toolchain"]["arduino_cli_version"], "1.6.0")
        self.assertEqual(result["toolchain"]["board_core"], "esp8266:esp8266@3.1.2")
        self.assertEqual(result["toolchain"]["fqbn"], "esp8266:esp8266:nodemcuv2")
        self.assertTrue(any(x["path"].endswith("BlazePwifiVendo.ino") for x in result["source"]["paths"]))

    def test_corrupt_existing_checksums_fail_without_mutating_artifact(self):
        self.openwrt_fixture()
        (self.artifact / "ruijie-sysupgrade.bin").write_bytes(b"changed")
        before = (self.artifact / "SHA256SUMS").read_bytes()
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=self.root / "imagebuilder-work",
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)
        self.assertEqual((self.artifact / "SHA256SUMS").read_bytes(), before)
        self.assertFalse((self.artifact / "BUILD-PROVENANCE.json").exists())

    def test_symlink_in_artifact_tree_is_rejected(self):
        self.openwrt_fixture()
        outside = self.root / "outside.bin"
        outside.write_bytes(b"outside")
        (self.artifact / "escape.bin").symlink_to(outside)
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=self.root / "imagebuilder-work",
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)

    def test_paid_preview_is_not_admitted_as_standard_artifact(self):
        work = self.openwrt_fixture(paid="1")
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)

    def test_wrong_official_imagebuilder_digest_is_rejected(self):
        work = self.openwrt_fixture()
        sums = work / "sha256sums"
        sums.write_text("0" * 64 + "  openwrt-imagebuilder-25.12.5-ramips-mt7621.Linux-x86_64.tar.zst\n")
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)

    def test_duplicate_imagebuilder_archives_are_rejected(self):
        work = self.openwrt_fixture()
        (work / "openwrt-imagebuilder-25.12.5-duplicate.tar.zst").write_bytes(b"duplicate")
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)

    def test_existing_provenance_is_never_overwritten(self):
        work = self.openwrt_fixture()
        target = self.artifact / "BUILD-PROVENANCE.json"
        target.write_text("owner data\n", encoding="utf-8")
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)
        self.assertEqual(target.read_text(encoding="utf-8"), "owner data\n")

    def test_invalid_or_mismatched_source_sha_is_rejected(self):
        self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=self.root / "imagebuilder-work",
        )
        env = dict(self.env, GITHUB_SHA="not-a-commit")
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=env)

    def test_arduino_core_mismatch_is_rejected(self):
        self.arduino_fixture()
        args = provenance.build_args(
            kind="esp8266", target="esp8266", artifact_dir=self.artifact,
            core_package="esp8266:esp8266", core_version="3.1.3",
            fqbn="esp8266:esp8266:nodemcuv2",
            sketch="experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)


    def test_source_worktree_must_match_exact_head_blob(self):
        source = self.root / "tracked.py"
        source.write_text("modified worktree source\\n", encoding="utf-8")

        def dirty_run(command, **kwargs):
            args = [str(part) for part in command]
            if args == ["git", "diff", "--quiet", "HEAD", "--", "tracked.py"]:
                return SimpleNamespace(returncode=1, stdout="", stderr="tracked.py")
            return fake_run(command, **kwargs)

        with patch.object(provenance, "ROOT", self.root), patch.object(
            provenance.subprocess, "run", side_effect=dirty_run
        ):
            with self.assertRaisesRegex(
                provenance.ProvenanceError,
                "source path differs from exact HEAD",
            ):
                provenance._source_context(self.env, ["tracked.py"])



    def test_pull_request_manifest_records_exact_head_and_base(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        env = dict(
            self.env,
            GITHUB_REF="refs/pull/291/merge",
            GITHUB_HEAD_REF="phoenix/release-publisher-isolation-20261115",
            GITHUB_BASE_REF="blazepwifi-v0.6.0-audit-foundation",
            PHX_SOURCE_HEAD_SHA="d" * 40,
            PHX_SOURCE_BASE_SHA="e" * 40,
        )
        result = provenance.write_provenance(args, env=env)
        self.assertEqual(result["source"]["commit"], SOURCE_SHA)
        self.assertEqual(result["source"]["source_head_sha"], "d" * 40)
        self.assertEqual(result["source"]["source_base_sha"], "e" * 40)

    def test_push_manifest_uses_exact_commit_as_source_head(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        result = provenance.write_provenance(
            args,
            env=dict(self.env, PHX_SOURCE_HEAD_SHA=SOURCE_SHA, PHX_SOURCE_BASE_SHA=""),
        )
        self.assertEqual(result["source"]["source_head_sha"], SOURCE_SHA)
        self.assertIsNone(result["source"]["source_base_sha"])

    def test_malformed_pull_request_head_sha_is_rejected(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        env = dict(
            self.env,
            GITHUB_REF="refs/pull/291/merge",
            GITHUB_HEAD_REF="feature",
            GITHUB_BASE_REF="main",
            PHX_SOURCE_HEAD_SHA="not-a-commit",
            PHX_SOURCE_BASE_SHA="e" * 40,
        )
        with self.assertRaisesRegex(provenance.ProvenanceError, "PHX_SOURCE_HEAD_SHA"):
            provenance.write_provenance(args, env=env)

    def test_pull_request_base_ref_requires_valid_base_sha(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt", target="ruijie", artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        for base_sha in ("", "not-a-commit"):
            with self.subTest(base_sha=base_sha):
                env = dict(
                    self.env,
                    GITHUB_REF="refs/pull/291/merge",
                    GITHUB_HEAD_REF="feature",
                    GITHUB_BASE_REF="main",
                    PHX_SOURCE_HEAD_SHA="d" * 40,
                    PHX_SOURCE_BASE_SHA=base_sha,
                )
                with self.assertRaisesRegex(provenance.ProvenanceError, "PHX_SOURCE_BASE_SHA"):
                    provenance.write_provenance(args, env=env)

    def test_workflow_exports_pull_request_head_and_base_shas(self):
        workflow = (provenance.ROOT / ".github/workflows/blazepwifi-build.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "PHX_SOURCE_HEAD_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
            workflow,
        )
        self.assertIn(
            "PHX_SOURCE_BASE_SHA: ${{ github.event.pull_request.base.sha || '' }}",
            workflow,
        )

    def test_artifact_directory_rejects_symlinked_parent_component(self):
        real_parent = self.root / "real-artifact-parent"
        real_parent.mkdir()
        real_artifact = real_parent / "artifact"
        real_artifact.mkdir()
        original_artifact = self.artifact
        self.artifact = real_artifact
        try:
            work = self.openwrt_fixture()
        finally:
            self.artifact = original_artifact

        alias_parent = self.root / "artifact-parent-link"
        alias_parent.symlink_to(real_parent, target_is_directory=True)
        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=alias_parent / "artifact",
            imagebuilder_workdir=work,
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)
        self.assertFalse((real_artifact / "BUILD-PROVENANCE.json").exists())

    def test_imagebuilder_workdir_rejects_symlinked_parent_component(self):
        work = self.openwrt_fixture()
        alias_parent = self.root / "imagebuilder-parent-link"
        alias_parent.symlink_to(self.root, target_is_directory=True)
        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=alias_parent / "imagebuilder-work",
        )
        with self.assertRaises(provenance.ProvenanceError):
            provenance.write_provenance(args, env=self.env)
        self.assertFalse((self.artifact / "BUILD-PROVENANCE.json").exists())

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BuildProvenanceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(f"RELEASE-PROVENANCE-PASS: {result.testsRun} tests")
        raise SystemExit(0)
    raise SystemExit(1)
