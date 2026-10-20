import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_build import validate_lock, validate_props


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


if __name__ == "__main__":
    unittest.main()
