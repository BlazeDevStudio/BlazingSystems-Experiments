"""OpenSSL-independent publisher verifier tests; these run on Windows too."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import publisher_signature as p

class PublisherStaticTests(unittest.TestCase):
    def test_url_public_https(self):
        self.assertTrue(p._valid_url("https://example.org/releases/v1"))

    def test_url_rejects_untrusted_targets(self):
        for url in ("http://example.org/x", "https://localhost/x", "https://192.168.1.1/x", "https://[::1]/x", "https://example.local/x", "https://user:pass@example.org/x", "https://example.org:8080/x", "https://example.org/x#fragment"):
            with self.subTest(url=url):
                self.assertFalse(p._valid_url(url))

    def test_digest_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"test.bin"
            file.write_bytes(b"Synthetic bytes only")
            self.assertEqual(p._digest_regular(file,1024),hashlib.sha256(file.read_bytes()).hexdigest())

    def test_digest_rejects_oversized_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"test.bin"
            file.write_bytes(b"X"*101)
            with self.assertRaises(ValueError):
                p._digest_regular(file,100)

    def test_digest_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"real.bin"
            target.write_bytes(b"bytes")
            link=Path(tmp)/"linked.bin"
            try:
                link.symlink_to(target)
            except (OSError,NotImplementedError):
                self.skipTest("Symlinks unavailable")
            with self.assertRaises(ValueError):
                p._digest_regular(link,100)

    def test_empty_pins_fail_closed(self):
        result=p.verify(artifact="missing",signature="missing",public_key="missing",expected_artifact_sha256="",trusted_key_sha256="",trusted_openssl_sha256="",upstream_release_url="https://example.org/releases/v1")
        self.assertFalse(result["audit_complete"])
        self.assertFalse(result["component_auth_gate_satisfied"])

    def test_publisher_identity_and_license_not_claimed(self):
        result=p.verify(artifact="missing",signature="missing",public_key="missing",expected_artifact_sha256="",trusted_key_sha256="",trusted_openssl_sha256="",upstream_release_url="https://example.org/releases/v1")
        self.assertFalse(result["publisher_identity_independently_verified"])
        self.assertFalse(result["license_verified"])

if __name__=="__main__":
    unittest.main()
