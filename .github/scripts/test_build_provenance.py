#!/usr/bin/env python3
"""Negative and positive tests for release artifact provenance sidecars."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_REAL_SUBPROCESS_RUN = subprocess.run

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
    if args[:4] == ["git", "ls-tree", "-r", "-z"]:
        return _REAL_SUBPROCESS_RUN(command, **kwargs)
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
    if args[:3] == ["arduino-cli", "compile", "--show-properties=expanded"]:
        compiler_path = Path(sys.executable).resolve()
        return SimpleNamespace(
            returncode=0,
            stdout=(
                f"compiler.path={compiler_path.parent}{os.sep}\n"
                f"compiler.c.cmd={compiler_path.name}\n"
                f"compiler.cpp.cmd={compiler_path.name}\n"
            ),
            stderr="",
        )
    if len(args) == 2 and args[1] == "--version" and Path(args[0]).resolve() == Path(sys.executable).resolve():
        return SimpleNamespace(
            returncode=0,
            stdout="GNU test compiler 12.2.0\n",
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
        toolchain_name = (
            "openwrt-toolchain-25.12.5-ramips-mt7621_gcc-14.3.0_musl.Linux-x86_64.tar.zst"
        )
        (work / "sha256sums").write_text(
            f"{checksum(archive)}  {archive.name}\n"
            f"{'d' * 64}  {toolchain_name}\n",
            encoding="utf-8",
        )
        return work

    def arduino_fixture(self, target="esp8266"):
        project = provenance.ROOT / "experiment/openwrt/BlazePwifi"
        sketch_name = "BlazePwifiVendo" if target == "esp8266" else "BlazePwifiVendo32"
        sketch_root = project / target / sketch_name
        staged_source = self.artifact / "source"
        staged_source.mkdir()
        shutil.copytree(sketch_root, staged_source / sketch_name)
        shutil.copytree(project / "esp" / "libraries", staged_source / "libraries")
        shutil.copyfile(project / "esp" / "REBUILD.md", staged_source / "README.md")
        sketch_file = sketch_root / f"{sketch_name}.ino"
        shutil.copyfile(sketch_file, self.artifact / f"{sketch_name}.ino")
        (self.artifact / f"{sketch_name}.ino.bin").write_bytes(b"synthetic-not-firmware")
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

    def test_openwrt_manifest_records_upstream_toolchain_reference_without_claiming_compilation(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        result = provenance.write_provenance(args, env=self.env)
        reference = result["toolchain"]["upstream_toolchain"]
        self.assertEqual(
            reference["archive"],
            "openwrt-toolchain-25.12.5-ramips-mt7621_gcc-14.3.0_musl.Linux-x86_64.tar.zst",
        )
        self.assertEqual(reference["sha256"], "d" * 64)
        self.assertEqual(reference["gcc_version"], "14.3.0")
        self.assertEqual(reference["libc_abi"], "musl")
        self.assertEqual(
            reference["checksum_catalog_sha256"],
            checksum(work / "sha256sums"),
        )
        self.assertFalse(reference["archive_downloaded"])
        self.assertFalse(reference["compiler_invoked"])
        self.assertIsNone(result["toolchain"]["compiler_version"])
        self.assertIn("does not invoke", result["toolchain"]["compiler_version_note"])

    def test_openwrt_toolchain_reference_parses_target_slug_and_eabi_abi(self):
        archive = (
            "openwrt-toolchain-25.12.5-sunxi-cortexa7_gcc-14.3.0_musl_eabi.Linux-x86_64.tar.zst"
        )
        reference = provenance._openwrt_toolchain_reference(
            {archive: "e" * 64},
            version="25.12.5",
            openwrt_target="sunxi/cortexa7",
            checksum_catalog_sha256="f" * 64,
        )
        self.assertEqual(reference["gcc_version"], "14.3.0")
        self.assertEqual(reference["libc_abi"], "musl_eabi")
        self.assertEqual(reference["archive"], archive)

    def test_openwrt_toolchain_reference_rejects_missing_ambiguous_and_invalid_entries(self):
        with self.assertRaisesRegex(provenance.ProvenanceError, "exactly one"):
            provenance._openwrt_toolchain_reference(
                {},
                version="25.12.5",
                openwrt_target="ramips/mt7621",
                checksum_catalog_sha256="f" * 64,
            )
        ambiguous = {
            "openwrt-toolchain-25.12.5-ramips-mt7621_gcc-14.3.0_musl.Linux-x86_64.tar.zst": "a" * 64,
            "openwrt-toolchain-25.12.5-ramips-mt7621_gcc-14.2.0_musl.Linux-x86_64.tar.zst": "b" * 64,
        }
        with self.assertRaisesRegex(provenance.ProvenanceError, "exactly one"):
            provenance._openwrt_toolchain_reference(
                ambiguous,
                version="25.12.5",
                openwrt_target="ramips/mt7621",
                checksum_catalog_sha256="f" * 64,
            )
        malformed = {
            "openwrt-toolchain-25.12.5-ramips-mt7621_gcc-14.3.0_musl.Linux-x86_64.tar.zst": "not-a-digest"
        }
        with self.assertRaisesRegex(provenance.ProvenanceError, "SHA-256"):
            provenance._openwrt_toolchain_reference(
                malformed,
                version="25.12.5",
                openwrt_target="ramips/mt7621",
                checksum_catalog_sha256="f" * 64,
            )

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
            libraries=self.artifact / "source" / "libraries",
        )
        result = provenance.write_provenance(args, env=self.env)
        self.assertEqual(result["toolchain"]["arduino_cli_version"], "1.6.0")
        self.assertEqual(result["toolchain"]["board_core"], "esp8266:esp8266@3.1.2")
        self.assertEqual(result["toolchain"]["fqbn"], "esp8266:esp8266:nodemcuv2")
        self.assertEqual(result["toolchain"]["compiler_version"], "GNU test compiler 12.2.0")
        self.assertEqual(result["toolchain"]["compiler_c_version"], "GNU test compiler 12.2.0")
        self.assertEqual(result["toolchain"]["compiler_c_binary"], Path(sys.executable).resolve().name)
        self.assertEqual(result["toolchain"]["compiler_cpp_binary"], Path(sys.executable).resolve().name)
        self.assertEqual(
            result["toolchain"]["compiler_version_source"],
            "arduino-cli compile --show-properties=expanded and compiler --version",
        )
        self.assertTrue(any(x["path"].endswith("BlazePwifiVendo.ino") for x in result["source"]["paths"]))

    def test_arduino_provenance_rejects_missing_cpp_compiler_property(self):
        self.arduino_fixture()
        args = provenance.build_args(
            kind="esp8266",
            target="esp8266",
            artifact_dir=self.artifact,
            core_package="esp8266:esp8266",
            core_version="3.1.2",
            fqbn="esp8266:esp8266:nodemcuv2",
            sketch="experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
            libraries=self.artifact / "source" / "libraries",
        )
        original_run = provenance._run

        def missing_cpp_properties(command, **kwargs):
            values = [str(part) for part in command]
            if values[:3] == ["arduino-cli", "compile", "--show-properties=expanded"]:
                compiler_path = Path(sys.executable).resolve()
                return (
                    f"compiler.path={compiler_path.parent}{os.sep}\n"
                    f"compiler.c.cmd={compiler_path.name}\n"
                )
            return original_run(command, **kwargs)

        with patch.object(provenance, "_run", side_effect=missing_cpp_properties):
            with self.assertRaisesRegex(provenance.ProvenanceError, "compiler.cpp.cmd"):
                provenance.write_provenance(args, env=self.env)

    def test_arduino_provenance_reuses_compile_library_search_paths(self):
        workflow = (
            provenance.ROOT / ".github/workflows/blazepwifi-build.yml"
        ).read_text(encoding="utf-8")
        cases = (
            (
                "Record exact-source ESP8266 artifact provenance",
                "--libraries experiment/openwrt/BlazePwifi/dist/esp8266/source/libraries",
            ),
            (
                "Record exact-source ESP32 artifact provenance",
                "--libraries experiment/openwrt/BlazePwifi/dist/esp32/source/libraries",
            ),
        )
        for step_name, expected in cases:
            with self.subTest(step=step_name):
                marker = f"- name: {step_name}"
                start = workflow.index(marker)
                next_step = workflow.find("\n      - ", start + len(marker))
                block = workflow[start:next_step if next_step >= 0 else len(workflow)]
                self.assertIn(expected, block)

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
            libraries=self.artifact / "source" / "libraries",
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


    def test_regular_file_open_rejects_parent_symlink_swap_race(self):
        parent = self.root / "race-parent"
        parent.mkdir()
        target = parent / "payload.bin"
        target.write_bytes(b"inside-original")
        moved_parent = self.root / "moved-parent"
        swapped = False
        real_open = os.open

        def swap_then_open(path, flags, *args, **kwargs):
            nonlocal swapped
            value = os.fspath(path)
            if not swapped and (
                value == str(target)
                or (value == parent.name and kwargs.get("dir_fd") is not None)
            ):
                parent.rename(moved_parent)
                parent.symlink_to(moved_parent, target_is_directory=True)
                swapped = True
            return real_open(path, flags, *args, **kwargs)

        try:
            with patch.object(provenance.os, "open", side_effect=swap_then_open) as patched_open:
                with patch.object(
                    provenance.os,
                    "supports_dir_fd",
                    {patched_open, provenance.os.stat},
                ):
                    with self.assertRaises(provenance.ProvenanceError):
                        provenance._hash_regular(target)
            self.assertTrue(swapped, "the deterministic parent-directory swap must execute")
        finally:
            if parent.is_symlink():
                parent.unlink()
            if moved_parent.exists():
                moved_parent.rename(parent)

    def test_payload_change_after_manifest_snapshot_is_rejected_before_checksum_rewrite(self):
        work = self.openwrt_fixture()
        checksum_path = self.artifact / "SHA256SUMS"
        original_checksums = checksum_path.read_bytes()
        payload_path = self.artifact / "ruijie-sysupgrade.bin"
        original_payload_digest = checksum(payload_path)
        original_write = provenance._write_new_json

        def write_manifest_then_mutate(path, manifest, *, directory_fd):
            original_write(path, manifest, directory_fd=directory_fd)
            payload_path.write_bytes(b"mutated-after-manifest-snapshot")

        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        with patch.object(
            provenance, "_write_new_json", side_effect=write_manifest_then_mutate
        ):
            with self.assertRaisesRegex(
                provenance.ProvenanceError,
                "artifact payload changed during provenance admission",
            ):
                provenance.write_provenance(args, env=self.env)

        self.assertEqual(
            checksum_path.read_bytes(),
            original_checksums,
            "failed admission must not rewrite SHA256SUMS to bless changed payload bytes",
        )
        manifest = __import__("json").loads(
            (self.artifact / "BUILD-PROVENANCE.json").read_text(encoding="utf-8")
        )
        recorded = next(
            entry for entry in manifest["files"]
            if entry["path"] == "ruijie-sysupgrade.bin"
        )
        self.assertEqual(recorded["sha256"], original_payload_digest)


    def test_artifact_parent_swap_after_validation_cannot_redirect_manifest_write(self):
        original_artifact = self.artifact
        parent = self.root / "artifact-parent"
        parent.mkdir()
        self.artifact = parent / "artifact"
        self.artifact.mkdir()
        work = self.openwrt_fixture()

        moved_parent = self.root / "artifact-parent-original"
        external_parent = self.root / "artifact-parent-external"
        external_parent.mkdir()
        external_artifact = external_parent / "artifact"
        external_artifact.mkdir()
        original_checksums = (self.artifact / "SHA256SUMS").read_bytes()
        original_source_context = provenance._source_context
        swapped = {"value": False}

        def source_context_then_swap(environment, source_paths):
            result = original_source_context(environment, source_paths)
            parent.rename(moved_parent)
            parent.symlink_to(external_parent, target_is_directory=True)
            swapped["value"] = True
            return result

        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        try:
            with patch.object(
                provenance, "_source_context", side_effect=source_context_then_swap
            ):
                with self.assertRaises(provenance.ProvenanceError):
                    provenance.write_provenance(args, env=self.env)

            self.assertTrue(swapped["value"], "the deterministic parent swap must execute")
            self.assertFalse(
                (external_artifact / "BUILD-PROVENANCE.json").exists(),
                "a replaced artifact parent must never redirect provenance output",
            )
            self.assertFalse(
                (external_artifact / "SHA256SUMS").exists(),
                "a replaced artifact parent must never redirect checksum output",
            )
            self.assertFalse(
                (moved_parent / "artifact" / "BUILD-PROVENANCE.json").exists(),
                "a changed artifact path must fail before publishing provenance",
            )
            self.assertEqual(
                (moved_parent / "artifact" / "SHA256SUMS").read_bytes(),
                original_checksums,
            )
        finally:
            self.artifact = original_artifact


    def test_artifact_inventory_rejects_external_hardlink(self):
        work = self.openwrt_fixture()
        outside = self.root / "outside-artifact-payload.bin"
        outside_bytes = b"operator-owned external content"
        outside.write_bytes(outside_bytes)
        linked = self.artifact / "linked-outside.bin"
        os.link(outside, linked)
        write_checksums(self.artifact)

        checksum_path = self.artifact / "SHA256SUMS"
        original_checksums = checksum_path.read_bytes()
        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )

        with self.assertRaisesRegex(
            provenance.ProvenanceError,
            "hard-linked artifact file is not admitted",
        ):
            provenance.write_provenance(args, env=self.env)

        self.assertEqual(checksum_path.read_bytes(), original_checksums)
        self.assertFalse((self.artifact / "BUILD-PROVENANCE.json").exists())
        self.assertEqual(outside.read_bytes(), outside_bytes)

    def test_no_unused_path_reopening_inventory_wrappers_remain(self):
        """Keep one descriptor-pinned inventory API instead of dead path wrappers."""
        self.assertFalse(hasattr(provenance, "_inventory"))
        self.assertFalse(hasattr(provenance, "_verify_checksum_manifest"))


    def test_checksum_manifest_rejects_noncanonical_path_aliases(self):
        digest = "a" * 64
        canonical = f"{digest}  ./nested/payload.bin\n".encode("utf-8")
        self.assertEqual(
            provenance._parse_checksum_text(canonical, "SHA256SUMS"),
            {"nested/payload.bin": digest},
        )

        for name in (
            "nested/./payload.bin",
            "nested//payload.bin",
            "nested/",
            "././nested/payload.bin",
            "C:/Windows/System32/kernel32.dll",
            "C:relative/payload.bin",
            "z:/payload.bin",
        ):
            with self.subTest(name=name):
                raw = f"{digest}  {name}\n".encode("utf-8")
                with self.assertRaisesRegex(
                    provenance.ProvenanceError,
                    "unsafe checksum path",
                ):
                    provenance._parse_checksum_text(raw, "SHA256SUMS")


    def test_checksum_manifest_rejects_line_boundary_characters(self):
        invalid_characters = (
            "\\",
            "\n",
            "\r",
            "\x00",
            "\v",
            "\f",
            "\x1c",
            "\x1d",
            "\x1e",
            "\x85",
            "\u2028",
            "\u2029",
        )
        for character in invalid_characters:
            with self.subTest(character=repr(character)):
                with self.assertRaisesRegex(
                    provenance.ProvenanceError,
                    "unsafe checksum path",
                ):
                    provenance._normalize_checksum_path(
                        f"nested{character}payload.bin"
                    )



    def test_run_passes_bounded_timeout(self):
        completed = SimpleNamespace(returncode=0, stdout="tool 1.0\n", stderr="")
        with patch.object(
            provenance.subprocess, "run", return_value=completed
        ) as runner:
            self.assertEqual(provenance._run(["tool", "--version"]), "tool 1.0")
        self.assertEqual(runner.call_args.kwargs.get("timeout"), 120)

    def test_run_timeout_is_reported_as_provenance_error(self):
        timeout = provenance.subprocess.TimeoutExpired(
            ["tool", "--version"], timeout=120
        )
        with patch.object(provenance.subprocess, "run", side_effect=timeout):
            with self.assertRaisesRegex(
                provenance.ProvenanceError,
                "command timed out after 120s",
            ):
                provenance._run(["tool", "--version"])


    def test_arduino_provenance_records_all_staged_compile_inputs_by_git_blob(self):
        self.arduino_fixture()
        args = provenance.build_args(
            kind="esp8266",
            target="esp8266",
            artifact_dir=self.artifact,
            core_package="esp8266:esp8266",
            core_version="3.1.2",
            fqbn="esp8266:esp8266:nodemcuv2",
            sketch="experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
            libraries=self.artifact / "source" / "libraries",
        )
        result = provenance.write_provenance(args, env=self.env)
        paths = {entry["path"] for entry in result["source"]["paths"]}
        required = {
            "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
            "experiment/openwrt/BlazePwifi/esp/libraries/BlazePendingSequence/library.properties",
            "experiment/openwrt/BlazePwifi/esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h",
            "experiment/openwrt/BlazePwifi/esp/REBUILD.md",
            "experiment/openwrt/BlazePwifi/tools/package-vendo-source.py",
        }
        self.assertTrue(required.issubset(paths), f"missing exact Git source blobs: {sorted(required - paths)}")
        self.assertTrue(result["toolchain"]["source_tree"]["staged_copy_verified"])
        self.assertGreaterEqual(result["toolchain"]["source_tree"]["library_file_count"], 2)

    def test_arduino_provenance_rejects_staged_sketch_tree_drift_before_manifest(self):
        self.arduino_fixture()
        staged = self.artifact / "source" / "BlazePwifiVendo" / "BlazePwifiVendo.ino"
        staged.write_bytes(staged.read_bytes() + b"\\n// staged-only change\\n")
        write_checksums(self.artifact)
        checksum_path = self.artifact / "SHA256SUMS"
        before = checksum_path.read_bytes()
        args = provenance.build_args(
            kind="esp8266",
            target="esp8266",
            artifact_dir=self.artifact,
            core_package="esp8266:esp8266",
            core_version="3.1.2",
            fqbn="esp8266:esp8266:nodemcuv2",
            sketch="experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
            libraries=self.artifact / "source" / "libraries",
        )
        with self.assertRaisesRegex(
            provenance.ProvenanceError,
            "staged Arduino sketch tree differs from exact source",
        ):
            provenance.write_provenance(args, env=self.env)
        self.assertEqual(checksum_path.read_bytes(), before)
        self.assertFalse((self.artifact / "BUILD-PROVENANCE.json").exists())

    def test_arduino_provenance_rejects_staged_library_tree_drift_before_manifest(self):
        self.arduino_fixture()
        staged = (
            self.artifact
            / "source"
            / "libraries"
            / "BlazePendingSequence"
            / "src"
            / "v060_pending_sequence.h"
        )
        staged.write_bytes(staged.read_bytes() + b"\\n// staged-only change\\n")
        write_checksums(self.artifact)
        checksum_path = self.artifact / "SHA256SUMS"
        before = checksum_path.read_bytes()
        args = provenance.build_args(
            kind="esp8266",
            target="esp8266",
            artifact_dir=self.artifact,
            core_package="esp8266:esp8266",
            core_version="3.1.2",
            fqbn="esp8266:esp8266:nodemcuv2",
            sketch="experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
            libraries=self.artifact / "source" / "libraries",
        )
        with self.assertRaisesRegex(
            provenance.ProvenanceError,
            "staged Arduino library tree differs from exact source",
        ):
            provenance.write_provenance(args, env=self.env)
        self.assertEqual(checksum_path.read_bytes(), before)
        self.assertFalse((self.artifact / "BUILD-PROVENANCE.json").exists())



if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BuildProvenanceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(f"RELEASE-PROVENANCE-PASS: {result.testsRun} tests")
        raise SystemExit(0)
    raise SystemExit(1)
