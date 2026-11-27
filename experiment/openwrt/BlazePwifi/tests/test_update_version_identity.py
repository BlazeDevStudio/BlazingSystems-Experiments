#!/usr/bin/env python3
"""Update packages must report the same version that their runtime will read."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools/build-update-bundle.sh"
RUNTIME_VERSION = "openwrt/rootfs/usr/share/blazepwifi/VERSION"


class UpdateVersionIdentityChecks(unittest.TestCase):
    def build(self, source, output, temporary):
        shell = shutil.which("sh")
        self.assertIsNotNone(shell, "POSIX sh is required to exercise the real update builder")
        environment = os.environ.copy()
        environment["TMPDIR"] = temporary.as_posix()
        return subprocess.run([shell, BUILDER.as_posix(), source.as_posix(), output.as_posix()],
                              capture_output=True, text=True, env=environment)

    def test_checkout_runtime_matches_declared_version(self):
        self.assertEqual((ROOT / RUNTIME_VERSION).read_text().strip(),
                         (ROOT / "VERSION").read_text().strip(),
                         "runtime identity differs from the declared source version")

    def test_drift_or_missing_runtime_version_is_refused_before_output(self):
        for runtime in ("0.5.2", None):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "source"
                version = source / RUNTIME_VERSION
                version.parent.mkdir(parents=True)
                (source / "VERSION").write_text("0.5.3\n")
                if runtime is not None:
                    version.write_text(runtime + "\n")
                output = Path(directory) / "output"
                temporary = Path(directory) / "temporary"
                temporary.mkdir()
                result = self.build(source, output, temporary)
                self.assertNotEqual(result.returncode, 0, "invalid version identity was packaged")
                self.assertFalse(output.exists(), "refused package created output before validation")
                self.assertIn("runtime VERSION", result.stderr)

    @unittest.skipIf(os.name == "nt", "actual archive build requires POSIX metadata tools; checked in Linux CI")
    def test_real_generated_archive_preserves_declared_version_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            temporary = Path(directory) / "temporary"
            temporary.mkdir()
            result = self.build(ROOT, output, temporary)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = (ROOT / "VERSION").read_text().strip()
            bundle = output / f"BlazePwifi-v{expected}-update.tar.gz"
            recorded_sha = Path(str(bundle) + ".sha256").read_text().split()[0]
            self.assertEqual(hashlib.sha256(bundle.read_bytes()).hexdigest(), recorded_sha)
            with tarfile.open(bundle, "r:gz") as archive:
                release = dict(line.split("=", 1) for line in
                               archive.extractfile("release.env").read().decode().splitlines())
                runtime = archive.extractfile("payload/usr/share/blazepwifi/VERSION").read()
                self.assertEqual(release["VERSION"], expected)
                self.assertEqual(runtime.decode().strip(), expected,
                                 "generated update ships a different runtime version")
                entries = [line.split("\t") for line in
                           archive.extractfile("manifest.tsv").read().decode().splitlines()]
                version_entries = [entry for entry in entries if entry[2] == "/usr/share/blazepwifi/VERSION"]
                self.assertEqual(len(version_entries), 1)
                self.assertEqual(version_entries[0][0], hashlib.sha256(runtime).hexdigest())


if __name__ == "__main__":
    unittest.main()
