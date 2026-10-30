"""Preview packaging must preserve bytes and refuse missing inputs."""
import hashlib
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_preview import prepare_preview


class PreviewPackagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.iso = self.base / "BlazeDroid-16.0.0-x86_64-PREVIEW.iso"
        self.output = self.base / "release-assets"
        self.manifest = self.base / "resolved-manifest.xml"
        self.manifest.write_text("<manifest/>")
        self.overlay_digest = self.base / "blazedroid-overlay-SHA256SUMS"
        self.overlay_digest.write_text("test-overlay-digest  device/blazedroid/x86_64/blazedroid_x86_64.mk\n")

    def test_refuse_missing_iso(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            prepare_preview(self.iso, self.output, self.manifest, max_asset_bytes=8)

    def test_small_image_is_single_download(self):
        data = b"ISO bytes test fixture"
        self.iso.write_bytes(data)
        prepare_preview(self.iso, self.output, self.manifest, max_asset_bytes=100)
        self.assertEqual((self.output / self.iso.name).read_bytes(), data)
        self.assertEqual(list(self.output.glob("*.part*")), [])
        self.assertIn(hashlib.sha256(data).hexdigest(), (self.output / "SHA256SUMS").read_text())

    def test_large_image_splits_into_reconstructable_parts(self):
        data = b"0123456789ABCDEFxyz"
        self.iso.write_bytes(data)
        prepare_preview(self.iso, self.output, self.manifest, max_asset_bytes=8)
        parts = sorted(self.output.glob(self.iso.name + ".part*"))
        self.assertEqual(len(parts), 3)
        self.assertEqual(b"".join(p.read_bytes() for p in parts), data)
        self.assertTrue(all(p.stat().st_size <= 8 for p in parts))
        self.assertIn(hashlib.sha256(data).hexdigest() + "  " + self.iso.name,
                      (self.output / "SHA256SUMS").read_text())
        self.assertIn("PREVIEW", (self.output / "PREVIEW_NOTES.md").read_text())
        self.assertEqual((self.output / self.manifest.name).read_text(), "<manifest/>")
        self.assertEqual((self.output / self.overlay_digest.name).read_text(), self.overlay_digest.read_text())

    def test_refuse_missing_local_product_provenance(self):
        self.iso.write_bytes(b"ISO bytes test fixture")
        self.overlay_digest.unlink()
        with self.assertRaises(FileNotFoundError):
            prepare_preview(self.iso, self.output, self.manifest, max_asset_bytes=100)

    def test_refuse_wrong_filename(self):
        wrong = self.base / "android13.iso"
        wrong.write_bytes(b"fake")
        with self.assertRaises(ValueError):
            prepare_preview(wrong, self.output, self.manifest, max_asset_bytes=8)


if __name__ == "__main__":
    unittest.main()
