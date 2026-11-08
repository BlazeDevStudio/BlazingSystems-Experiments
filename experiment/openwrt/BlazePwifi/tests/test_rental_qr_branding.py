#!/usr/bin/env python3
"""Check offline QR artwork and Device Owner download data."""
import base64
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ARTWORK_SHA256 = "c4e61f370a1a9541722f4fcee522cec8d20c3c9e2917fc1a32286f4870193690"
APK_FIXTURE = b"synthetic checksum input only"
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
    def build(self, builder, template, legacy=False, apk_url="https://example.invalid/rental.apk",
              qr_source=None):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            apk = folder / "fixture.apk"
            apk.write_bytes(APK_FIXTURE)
            output = folder / "qr.html"
            template_path = ROOT / "tools" / template
            qr_path = ROOT / "ui/vendor/qrcode/qrcode.js"
            if qr_source is not None:
                qr_path = folder / "qr.js"
                qr_path.write_text(qr_source, encoding="utf-8")
            if legacy:
                template_path = folder / "legacy.html"
                template_path.write_text(
                    '<h1>Legacy custom template</h1><script>__QRCODE_JS__</script>'
                    '<script>const APK_URL="__APK_URL__", APK_CHECKSUM="__APK_CHECKSUM__";</script>',
                    encoding="utf-8",
                )
            arguments = [sys.executable, str(ROOT / "tools" / builder),
                         "--template", str(template_path),
                         "--qrcode-js", str(qr_path),
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

    def test_apk_url_and_checksum_preserve_their_independent_values(self):
        expected_checksum = base64.urlsafe_b64encode(
            hashlib.sha256(APK_FIXTURE).digest()
        ).decode("ascii").rstrip("=")
        for url in (
            "https://example.invalid/__APK_CHECKSUM__/BlazeRental.apk",
            "https://example.invalid/BlazeRental.apk?ref=<test>&download=1",
        ):
            with self.subTest(url=url):
                html = self.build("build-rental-qr-tool.py", "BlazeRental-QR-Setup.template.html",
                                  apk_url=url)
                values = re.search(
                    r'const APK_URL=("(?:\\.|[^"\\])*"), APK_CHECKSUM=("(?:\\.|[^"\\])*");',
                    html,
                )
                self.assertIsNotNone(values, "Device Owner download constants are missing")
                self.assertEqual(json.loads(values.group(2)), expected_checksum)
                self.assertEqual(json.loads(values.group(1)), url)

    def test_qr_javascript_is_inserted_without_substitution(self):
        qr_source = 'const fixtureMarkers = ["__APK_URL__", "__APK_CHECKSUM__"];'
        html = self.build("build-rental-qr-tool.py", "BlazeRental-QR-Setup.template.html",
                          qr_source=qr_source)
        self.assertTrue(f"<script>{qr_source}</script>" in html,
                        "QR JavaScript marker text was changed")


if __name__ == "__main__":
    unittest.main()
