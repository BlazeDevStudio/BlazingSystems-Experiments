import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_build import validate_blazedroid_props


class PreviewIdentityTests(unittest.TestCase):
    def run_prop(self, content):
        with tempfile.TemporaryDirectory() as root:
            f = Path(root) / "build.prop"
            f.write_text(content)
            validate_blazedroid_props(f)

    def test_accepts_genuine_blazedroid_image_identity(self):
        self.run_prop(
            "ro.build.version.release=16\n"
            "ro.build.version.sdk=36\n"
            "ro.blazedroid.version=16.0.0\n"
            "ro.blazedroid.channel=preview\n"
        )

    def test_refuses_generic_android_iso_renamed_blazedroid(self):
        with self.assertRaises(ValueError):
            self.run_prop("ro.build.version.release=16\nro.build.version.sdk=36\n")

    def test_refuses_false_preview_identity(self):
        with self.assertRaises(ValueError):
            self.run_prop(
                "ro.build.version.release=16\nro.build.version.sdk=36\n"
                "ro.blazedroid.version=16.0.0\n"
                "ro.blazedroid.channel=production\n"
            )


if __name__ == "__main__":
    unittest.main()
