#!/usr/bin/env python3
"""Offline QR pages embed the unmodified owner-supplied brand artwork."""
import base64
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ARTWORK_SHA256 = "c4e61f370a1a9541722f4fcee522cec8d20c3c9e2917fc1a32286f4870193690"
BUILDERS = (
    ("build-binding-qr-tool.py", "BlazeRental-Binding-QR.template.html"),
    ("build-rental-qr-tool.py", "BlazeRental-QR-Setup.template.html"),
)


class PageArtwork(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.viewports = []

    def handle_starttag(self, tag, attributes):
        if tag == "image":
            self.images.append(dict(attributes))
        elif tag == "svg":
            self.viewports.append(dict(attributes))


class RentalQrBrandingChecks(unittest.TestCase):
    def build(self, builder, template, legacy=False, apk_url="https://example.invalid/rental.apk"):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            apk = folder / "fixture.apk"
            apk.write_bytes(b"synthetic checksum input only")
            output = folder / "qr.html"
            template_path = ROOT / "tools" / template
            if legacy:
                template_path = folder / "legacy.html"
                template_path.write_text(
                    '<h1>Legacy custom template</h1><script>__QRCODE_JS__</script>'
                    '<script>const APK_URL="__APK_URL__", APK_CHECKSUM="__APK_CHECKSUM__";</script>',
                    encoding="utf-8",
                )
            arguments = [sys.executable, str(ROOT / "tools" / builder),
                         "--template", str(template_path),
                         "--qrcode-js", str(ROOT / "ui/vendor/qrcode/qrcode.js"),
                         "--out", str(output)]
            if builder == "build-rental-qr-tool.py":
                arguments += ["--apk", str(apk), "--apk-url", apk_url]
            result = subprocess.run(arguments, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return output.read_text(encoding="utf-8")

    def test_both_pages_embed_the_exact_original_artwork(self):
        artwork = (ROOT / "tools/BlazeSystems-Logo-V2.png").read_bytes()
        self.assertEqual(hashlib.sha256(artwork).hexdigest(), ARTWORK_SHA256)
        for builder, template in BUILDERS:
            with self.subTest(builder=builder):
                html = self.build(builder, template)
                page = PageArtwork()
                page.feed(html)
                self.assertEqual(len(page.viewports), 1, "page must show the existing horizontal logo panel")
                viewport = page.viewports[0]
                self.assertEqual(viewport.get("viewbox"), "16 26 246 114")
                self.assertEqual(viewport.get("role"), "img")
                self.assertEqual(viewport.get("aria-label"), "Blaze Systems")
                self.assertEqual(len(page.images), 1, "logo viewport must contain the supplied artwork")
                image = page.images[0]
                self.assertEqual((image.get("width"), image.get("height")), ("278", "175"))
                self.assertTrue(image["href"].startswith("data:image/png;base64,"))
                embedded = base64.b64decode(image["href"].split(",", 1)[1], validate=True)
                self.assertEqual(embedded, artwork, "embedded artwork was altered")
                self.assertNotIn("__BLAZE_SYSTEMS_LOGO__", html)
                self.assertNotIn("__QRCODE_JS__", html)

    def test_custom_templates_without_brand_marker_still_build(self):
        for builder, template in BUILDERS:
            with self.subTest(builder=builder):
                html = self.build(builder, template, legacy=True)
                self.assertIn("<h1>Legacy custom template</h1>", html)
                self.assertNotIn("__QRCODE_JS__", html)

    def test_valid_apk_url_containing_logo_marker_is_preserved(self):
        html = self.build("build-rental-qr-tool.py", "BlazeRental-QR-Setup.template.html",
                          apk_url="https://example.invalid/__BLAZE_SYSTEMS_LOGO__.apk")
        self.assertTrue('const APK_URL="https://example.invalid/__BLAZE_SYSTEMS_LOGO__.apk"' in html,
                        "logo substitution changed the valid APK download URL")


if __name__ == "__main__":
    unittest.main()
