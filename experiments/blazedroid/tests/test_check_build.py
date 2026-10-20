import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_build import validate_lock, validate_props, verify_upstream_xml


class BuildGateTests(unittest.TestCase):
    def write(self, contents):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path = Path(self.tmp.name) / "input"
        path.write_text(contents)
        return path

    def test_accepts_android_16(self):
        validate_props(self.write("ro.build.version.release=16\nro.build.version.sdk=36\n"))

    def test_rejects_downgraded_android(self):
        with self.assertRaises(ValueError):
            validate_props(self.write("ro.build.version.release=13\nro.build.version.sdk=33\n"))

    def test_rejects_missing_build_props(self):
        with self.assertRaises(ValueError):
            validate_props(self.write("# no version properties\n"))

    def test_lock_sane(self):
        validate_lock(Path(__file__).resolve().parents[1] / "foundation.lock.json")

    def test_refuses_gapps_without_permission(self):
        lock = json.loads((Path(__file__).resolve().parents[1] / "foundation.lock.json").read_text())
        lock["gapps"] = "included"
        with self.assertRaises(ValueError):
            validate_lock(self.write(json.dumps(lock)))

    def test_upstream_manifest_matches_android_16_and_installer(self):
        lock = json.loads((Path(__file__).resolve().parents[1] / "foundation.lock.json").read_text())
        default = b'<manifest><remote name="aosp" revision="refs/tags/android-16.0.0_r4"/></manifest>'
        installer = (
            '<manifest><project path="bootable/aaropa" '
            'revision="' + lock["installer_commit"] + '"/></manifest>'
        ).encode()
        verify_upstream_xml(default, installer, lock)

    def test_refuses_older_upstream_android(self):
        lock = json.loads((Path(__file__).resolve().parents[1] / "foundation.lock.json").read_text())
        default = b'<manifest><remote name="aosp" revision="refs/tags/android-13.0.0_r77"/></manifest>'
        installer = (
            '<manifest><project path="bootable/aaropa" '
            'revision="' + lock["installer_commit"] + '"/></manifest>'
        ).encode()
        with self.assertRaises(ValueError):
            verify_upstream_xml(default, installer, lock)


if __name__ == "__main__":
    unittest.main()
