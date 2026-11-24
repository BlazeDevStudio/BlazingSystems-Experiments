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
TREE_SHA = "d" * 40
OPENWRT_ROOTFS = "experiment/openwrt/BlazePwifi/openwrt/rootfs"
OPENWRT_LINUX_AGENT = "experiment/openwrt/BlazePwifi/linux-agent"
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
        path = args[2][5:]
        digest = TREE_SHA if path in {OPENWRT_ROOTFS, OPENWRT_LINUX_AGENT} else BLOB_SHA
        return SimpleNamespace(returncode=0, stdout=digest + "\n", stderr="")
    if args[:3] == ["git", "ls-files", "--others"] and len(args) == 5:
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    if args[:3] == ["git", "cat-file", "-t"] and len(args) == 4:
        object_type = "tree" if args[3] == TREE_SHA else "blob"
        return SimpleNamespace(returncode=0, stdout=object_type + "\n", stderr="")
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

    def test_openwrt_source_inputs_include_overlay_and_target_specific_helpers(self):
        base = "experiment/openwrt/BlazePwifi"
        ruijie_files, ruijie_trees = provenance._openwrt_source_inputs("ruijie")
        self.assertEqual(
            set(ruijie_files),
            {f"{base}/build/build-openwrt-image.sh", f"{base}/VERSION"},
        )
        self.assertEqual(set(ruijie_trees), {OPENWRT_ROOTFS})

        x86_files, x86_trees = provenance._openwrt_source_inputs("x86_64")
        self.assertTrue(
            {
                f"{base}/build/prepare-tabler.sh",
                f"{base}/tools/verify-firmware-gzip.py",
            }.issubset(set(x86_files))
        )
        self.assertEqual(set(x86_trees), {OPENWRT_ROOTFS})

        sbc_files, sbc_trees = provenance._openwrt_source_inputs("orangepi_zero3")
        self.assertTrue(
            {
                f"{base}/build/prepare-tabler.sh",
                f"{base}/tools/verify-firmware-gzip.py",
            }.issubset(set(sbc_files))
        )
        self.assertEqual(set(sbc_trees), {OPENWRT_ROOTFS, OPENWRT_LINUX_AGENT})

    def test_openwrt_manifest_records_exact_overlay_git_tree(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        result = provenance.write_provenance(args, env=self.env)
        self.assertEqual(
            result["source"]["trees"],
            [{"path": OPENWRT_ROOTFS, "git_tree": TREE_SHA}],
        )

    def test_openwrt_source_tree_rejects_untracked_inputs_before_manifest_publication(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        checksum_path = self.artifact / "SHA256SUMS"
        original_checksums = checksum_path.read_bytes()
        original_run = provenance._run

        def report_untracked(command, **kwargs):
            values = [str(part) for part in command]
            if values[:3] == ["git", "ls-files", "--others"]:
                return f"{OPENWRT_ROOTFS}/untracked-overlay.conf"
            return original_run(command, **kwargs)

        with patch.object(provenance, "_run", side_effect=report_untracked):
            with self.assertRaisesRegex(
                provenance.ProvenanceError,
                "untracked source tree input",
            ):
                provenance.write_provenance(args, env=self.env)

        self.assertFalse((self.artifact / "BUILD-PROVENANCE.json").exists())
        self.assertEqual(checksum_path.read_bytes(), original_checksums)

    def test_openwrt_source_tree_rejects_tracked_drift_before_manifest_publication(self):
        work = self.openwrt_fixture()
        args = provenance.build_args(
            kind="openwrt",
            target="ruijie",
            artifact_dir=self.artifact,
            imagebuilder_workdir=work,
        )
        checksum_path = self.artifact / "SHA256SUMS"
        original_checksums = checksum_path.read_bytes()

        def report_tracked_drift(command, **kwargs):
            values = [str(part) for part in command]
            if values == ["git", "diff", "--quiet", "HEAD", "--", OPENWRT_ROOTFS]:
                return SimpleNamespace(
                    returncode=1,
                    stdout="",
                    stderr="synthetic tracked source-tree drift",
                )
            return fake_run(command, **kwargs)

        with patch.object(provenance.subprocess, "run", side_effect=report_tracked_drift):
            with self.assertRaisesRegex(
                provenance.ProvenanceError,
                "source tree differs from exact HEAD worktree content",
            ):
                provenance.write_provenance(args, env=self.env)

        self.assertFalse((self.artifact / "BUILD-PROVENANCE.json").exists())
        self.assertEqual(checksum_path.read_bytes(), original_checksums)

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


    def test_arduino_provenance_excludes_compiler_generated_build_outputs_from_source_blobs(self):
        self.arduino_fixture()
        generated = (
            self.artifact
            / "source"
            / "BlazePwifiVendo"
            / "build"
            / "esp32.esp32.esp32"
            / "compiled-output.bin"
        )
        generated.parent.mkdir(parents=True)
        generated.write_bytes(b"synthetic compiler output, not source")
        write_checksums(self.artifact)
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
        self.assertNotIn(
            "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/build/esp32.esp32.esp32/compiled-output.bin",
            paths,
        )
        source_tree = result["toolchain"]["source_tree"]
        self.assertTrue(source_tree["staged_copy_verified"])
        self.assertEqual(source_tree["generated_build_output_file_count"], 1)


    def test_new_provenance_json_removes_temp_after_keyboard_interrupt_before_publish(self):
        directory_fd = os.open(
            self.artifact,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        target = self.artifact / "BUILD-PROVENANCE.json"
        try:
            with patch.object(provenance.os, "fsync", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    provenance._write_new_json(
                        target,
                        {"schema": "blaze.phx-release.build-provenance/test"},
                        directory_fd=directory_fd,
                    )
            self.assertFalse(target.exists())
            self.assertEqual(
                list(self.artifact.glob(".BUILD-PROVENANCE.*")),
                [],
                "KeyboardInterrupt before publication must not leave an untracked sidecar",
            )
        finally:
            os.close(directory_fd)

    def test_checksum_writer_removes_temp_after_system_exit_before_replace(self):
        target = self.artifact / "SHA256SUMS"
        original = b"old-digest  old-payload.bin\\n"
        target.write_bytes(original)
        directory_fd = os.open(
            self.artifact,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            with patch.object(provenance.os, "fsync", side_effect=SystemExit(23)):
                with self.assertRaises(SystemExit) as raised:
                    provenance._write_checksums(
                        target,
                        self.artifact,
                        {"new-payload.bin": {"sha256": "a" * 64}},
                        directory_fd=directory_fd,
                    )
            self.assertEqual(raised.exception.code, 23)
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(
                list(self.artifact.glob(".SHA256SUMS.*")),
                [],
                "SystemExit before replacement must not leave an untracked sidecar",
            )
        finally:
            os.close(directory_fd)




    def test_new_provenance_json_removes_published_target_after_directory_fsync_failure(self):
        directory_fd = os.open(
            self.artifact,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        target = self.artifact / "BUILD-PROVENANCE.json"
        fsync_calls = 0

        def fail_directory_sync_after_publication(_fd):
            nonlocal fsync_calls
            fsync_calls += 1
            if fsync_calls == 2:
                raise OSError("injected directory fsync failure")
            return None

        try:
            with patch.object(
                provenance.os,
                "fsync",
                side_effect=fail_directory_sync_after_publication,
            ):
                with self.assertRaisesRegex(
                    OSError,
                    "injected directory fsync failure",
                ):
                    provenance._write_new_json(
                        target,
                        {"schema": "blaze.phx-release.build-provenance/test"},
                        directory_fd=directory_fd,
                    )
            self.assertFalse(
                target.exists(),
                "failed directory durability after publication must not leave a manifest that blocks retry",
            )
            self.assertEqual(
                list(self.artifact.glob(".BUILD-PROVENANCE.*")),
                [],
                "failed publication must not leave an untracked temporary sidecar",
            )
            self.assertEqual(
                fsync_calls,
                3,
                "cleanup of a published target must itself be directory-synced",
            )
        finally:
            os.close(directory_fd)


    def assert_open_cleanup_preserves_primary_after_close_interruption(self, operation):
        real_open = os.open
        real_fstat = os.fstat
        real_close = os.close
        opened_fds = []
        close_calls = []

        def tracked_open(path, flags, *args, **kwargs):
            descriptor = real_open(path, flags, *args, **kwargs)
            opened_fds.append(descriptor)
            return descriptor

        def interrupted_fstat(descriptor):
            if len(opened_fds) >= 2 and descriptor == opened_fds[-1]:
                raise RuntimeError("injected primary traversal failure")
            return real_fstat(descriptor)

        def close_then_interrupt(descriptor):
            close_calls.append(descriptor)
            real_close(descriptor)
            if len(close_calls) == 1:
                raise RuntimeError("injected cleanup close interruption")

        supported = set(os.supports_dir_fd)
        supported.add(tracked_open)
        try:
            with patch.object(provenance.os, "open", new=tracked_open), patch.object(
                provenance.os, "supports_dir_fd", supported
            ), patch.object(
                provenance.os, "fstat", side_effect=interrupted_fstat
            ), patch.object(
                provenance.os, "close", side_effect=close_then_interrupt
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "injected primary traversal failure"
                ) as raised:
                    operation()

            self.assertEqual(len(opened_fds), 2)
            self.assertEqual(len(close_calls), 2)
            self.assertEqual(set(close_calls), set(opened_fds))
            if callable(getattr(raised.exception, "add_note", None)):
                self.assertTrue(
                    any(
                        "RuntimeError" in note
                        for note in getattr(raised.exception, "__notes__", [])
                    ),
                    "cleanup interruption should be recorded on the primary exception",
                )
            for descriptor in opened_fds:
                with self.subTest(descriptor=descriptor):
                    with self.assertRaises(OSError):
                        real_fstat(descriptor)
        finally:
            # Reap any descriptor left open by the pre-fix implementation.
            for descriptor in opened_fds:
                try:
                    real_close(descriptor)
                except OSError:
                    pass

    def test_regular_file_open_attempts_all_closes_after_cleanup_interruption(self):
        parent = self.root / "cleanup-interrupt-regular-parent"
        parent.mkdir()
        payload = parent / "payload.bin"
        payload.write_bytes(b"release-provenance-cleanup")
        self.assert_open_cleanup_preserves_primary_after_close_interruption(
            lambda: provenance._open_regular(payload)
        )

    def test_directory_open_attempts_all_closes_after_cleanup_interruption(self):
        directory = self.root / "cleanup-interrupt-directory-parent" / "child"
        directory.mkdir(parents=True)
        self.assert_open_cleanup_preserves_primary_after_close_interruption(
            lambda: provenance._open_directory(directory, "test directory")
        )

    def assert_descriptors_closed_after_interrupt(self, operation, interrupt_type):
        real_open = os.open
        real_fstat = os.fstat
        opened_fds = []

        def tracked_open(path, flags, *args, **kwargs):
            descriptor = real_open(path, flags, *args, **kwargs)
            opened_fds.append(descriptor)
            return descriptor

        def interrupted_fstat(descriptor):
            if len(opened_fds) >= 2 and descriptor == opened_fds[-1]:
                raise interrupt_type("injected directory traversal interruption")
            return real_fstat(descriptor)

        supported = set(os.supports_dir_fd)
        supported.add(tracked_open)
        with patch.object(provenance.os, "open", new=tracked_open), patch.object(
            provenance.os, "supports_dir_fd", supported
        ), patch.object(provenance.os, "fstat", side_effect=interrupted_fstat):
            with self.assertRaises(interrupt_type):
                operation()

        self.assertGreaterEqual(len(opened_fds), 2)
        for descriptor in opened_fds:
            with self.subTest(descriptor=descriptor):
                with self.assertRaises(OSError):
                    real_fstat(descriptor)

    def test_regular_file_traversal_closes_parent_and_child_fds_on_keyboard_interrupt(self):
        parent = self.root / "interrupt-regular-parent"
        parent.mkdir()
        payload = parent / "payload.bin"
        payload.write_bytes(b"descriptor-cleanup")
        self.assert_descriptors_closed_after_interrupt(
            lambda: provenance._open_regular(payload),
            KeyboardInterrupt,
        )

    def test_directory_traversal_closes_parent_and_child_fds_on_system_exit(self):
        directory = self.root / "interrupt-directory-parent" / "child"
        directory.mkdir(parents=True)
        self.assert_descriptors_closed_after_interrupt(
            lambda: provenance._open_directory(directory, "test directory"),
            SystemExit,
        )


    def assert_regular_reader_cleanup_after_file_close_error(
        self,
        operation_name: str,
        *,
        fail_read: bool,
    ) -> None:
        target = self.root / f"{operation_name}-close-error.bin"
        target.write_bytes(b"release-provenance-descriptor-cleanup")
        fd, before, parent_fd, leaf = provenance._open_regular(target)
        real_close = os.close
        real_fstat = os.fstat
        real_read = os.read
        close_calls = []

        def close_then_report_error(descriptor):
            close_calls.append(descriptor)
            real_close(descriptor)
            if descriptor == fd:
                raise OSError("injected file descriptor close failure")

        def read_with_optional_failure(descriptor, size):
            if fail_read and descriptor == fd:
                raise OSError("injected provenance read failure")
            return real_read(descriptor, size)

        operation = getattr(provenance, operation_name)
        primary_message = "cannot read" if operation_name == "_read_regular" else "cannot hash"
        try:
            with patch.object(
                provenance, "_open_regular", return_value=(fd, before, parent_fd, leaf)
            ), patch.object(
                provenance.os, "close", side_effect=close_then_report_error
            ), patch.object(
                provenance.os, "read", side_effect=read_with_optional_failure
            ):
                if fail_read:
                    with self.assertRaisesRegex(
                        provenance.ProvenanceError, primary_message
                    ) as raised:
                        operation(target)
                    self.assertTrue(
                        any(
                            "injected file descriptor close failure" in note
                            for note in getattr(raised.exception, "__notes__", [])
                        ),
                        "the close failure must remain attached to the primary read/hash error",
                    )
                else:
                    with self.assertRaisesRegex(
                        provenance.ProvenanceError, "could not close"
                    ) as raised:
                        operation(target)
                    self.assertIn(
                        "injected file descriptor close failure",
                        str(raised.exception),
                    )
        finally:
            # A failing implementation may skip the parent close. Reap any
            # descriptor still open so this regression never leaks test FDs.
            for descriptor in (fd, parent_fd):
                try:
                    real_fstat(descriptor)
                except OSError:
                    continue
                real_close(descriptor)

        self.assertEqual(
            close_calls,
            [fd, parent_fd],
            "both the file and pinned parent descriptors must receive one close attempt",
        )
        for descriptor in (fd, parent_fd):
            with self.subTest(descriptor=descriptor):
                with self.assertRaises(OSError):
                    real_fstat(descriptor)

    def test_regular_read_preserves_primary_error_and_closes_parent_after_close_failure(self):
        self.assert_regular_reader_cleanup_after_file_close_error(
            "_read_regular", fail_read=True
        )

    def test_regular_hash_preserves_primary_error_and_closes_parent_after_close_failure(self):
        self.assert_regular_reader_cleanup_after_file_close_error(
            "_hash_regular", fail_read=True
        )

    def test_regular_read_reports_close_only_failure_after_closing_parent(self):
        self.assert_regular_reader_cleanup_after_file_close_error(
            "_read_regular", fail_read=False
        )

    def test_regular_hash_reports_close_only_failure_after_closing_parent(self):
        self.assert_regular_reader_cleanup_after_file_close_error(
            "_hash_regular", fail_read=False
        )



    def assert_regular_reader_preserves_primary_error_after_cleanup_interruptions(
        self, operation_name: str
    ) -> None:
        target = self.root / f"{operation_name}-cleanup-interruptions.bin"
        target.write_bytes(b"release-provenance-primary-read-failure")
        fd, before, parent_fd, leaf = provenance._open_regular(target)
        real_close = os.close
        real_fstat = os.fstat
        real_read = os.read
        close_calls: list[int] = []

        def close_then_interrupt(descriptor: int) -> None:
            close_calls.append(descriptor)
            real_close(descriptor)
            if descriptor == fd:
                raise KeyboardInterrupt("injected file descriptor cleanup interruption")
            if descriptor == parent_fd:
                raise SystemExit("injected parent-directory cleanup interruption")

        def read_with_primary_failure(descriptor: int, size: int) -> bytes:
            if descriptor == fd:
                raise OSError("injected primary read failure")
            return real_read(descriptor, size)

        operation = getattr(provenance, operation_name)
        primary_message = "cannot read" if operation_name == "_read_regular" else "cannot hash"
        try:
            with patch.object(
                provenance, "_open_regular", return_value=(fd, before, parent_fd, leaf)
            ), patch.object(
                provenance.os, "close", side_effect=close_then_interrupt
            ), patch.object(
                provenance.os, "read", side_effect=read_with_primary_failure
            ):
                with self.assertRaises(BaseException) as raised:
                    operation(target)

            self.assertIsInstance(
                raised.exception,
                provenance.ProvenanceError,
                "cleanup interruptions must not replace the primary read/hash failure",
            )
            self.assertIn(primary_message, str(raised.exception))
            self.assertEqual(
                close_calls,
                [fd, parent_fd],
                "both descriptors must receive one close attempt after cleanup interruptions",
            )
            if callable(getattr(raised.exception, "add_note", None)):
                notes = getattr(raised.exception, "__notes__", [])
                self.assertTrue(any("KeyboardInterrupt" in note for note in notes))
                self.assertTrue(any("SystemExit" in note for note in notes))
        finally:
            # The failing implementation may leave descriptors open. Reap only
            # descriptors that remain live, using the unpatched close function.
            for descriptor in (fd, parent_fd):
                try:
                    real_fstat(descriptor)
                except OSError:
                    continue
                real_close(descriptor)

    def test_regular_read_preserves_primary_error_when_cleanup_interrupts(self):
        self.assert_regular_reader_preserves_primary_error_after_cleanup_interruptions(
            "_read_regular"
        )

    def test_regular_hash_preserves_primary_error_when_cleanup_interrupts(self):
        self.assert_regular_reader_preserves_primary_error_after_cleanup_interruptions(
            "_hash_regular"
        )

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BuildProvenanceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(f"RELEASE-PROVENANCE-PASS: {result.testsRun} tests")
        raise SystemExit(0)
    raise SystemExit(1)
