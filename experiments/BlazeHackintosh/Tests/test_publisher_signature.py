"""Local OpenSSL-backed synthetic Ed25519 acceptance and tampering tests."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publisher_signature import verify, _digest_regular, LIMITS

OPENSSL = shutil.which("openssl")


@unittest.skipUnless(OPENSSL, "OpenSSL CLI required for real detached-signature test")
class PublisherSignatureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.artifact = root / "sample.kext.zip"
        self.artifact.write_bytes(b"synthetic component fixture; NOT a real kext\n")
        self.private = root / "private.pem"
        self.public = root / "public.pem"
        self.signature = root / "sample.sig"
        self._cmd("genpkey", "-algorithm", "ED25519", "-out", str(self.private))
        self._cmd("pkey", "-in", str(self.private), "-pubout", "-out", str(self.public))
        self.sign()
        self.artifact_pin = self.sha(self.artifact)
        self.key_pin = self.sha(self.public)
        self.openssl_pin = self.sha(Path(OPENSSL))
        self.url = "https://example.org/releases/v1.0"

    def _cmd(self, *args):
        subprocess.run([OPENSSL, *args], check=True, capture_output=True)

    def sign(self):
        self._cmd("pkeyutl", "-sign", "-inkey", str(self.private),
                  "-rawin", "-in", str(self.artifact), "-out", str(self.signature))

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def check(self, **overrides):
        args = dict(artifact=self.artifact, signature=self.signature, public_key=self.public,
                    expected_artifact_sha256=self.artifact_pin,
                    trusted_key_sha256=self.key_pin,
                    trusted_openssl_sha256=self.openssl_pin,
                    upstream_release_url=self.url, openssl=OPENSSL)
        args.update(overrides)
        return verify(**args)

    def test_valid_real_ed25519_signature_passes_with_scope_limit(self):
        result = self.check()
        self.assertTrue(result["audit_complete"], result)
        self.assertTrue(result["ed25519_signature_verified"])
        self.assertTrue(result["openssl_binary_hash_verified"])
        self.assertFalse(result["openssl_runtime_dependencies_verified"])
        self.assertFalse(result["publisher_identity_independently_verified"])
        self.assertFalse(result["license_verified"])
        self.assertFalse(result["component_auth_gate_satisfied"])

    def test_modified_artifact_rejected(self):
        self.artifact.write_bytes(b"modified")
        self.assertFalse(self.check()["audit_complete"])

    def test_replaced_signature_rejected(self):
        self.signature.write_bytes(os.urandom(64))
        self.assertFalse(self.check()["audit_complete"])

    def test_wrong_key_pin_rejected(self):
        self.assertFalse(self.check(trusted_key_sha256="0" * 64)["audit_complete"])

    def test_wrong_artifact_pin_rejected(self):
        self.assertFalse(self.check(expected_artifact_sha256="0" * 64)["audit_complete"])

    def test_missing_key_pin_rejected(self):
        self.assertFalse(self.check(trusted_key_sha256="")["audit_complete"])

    def test_untrusted_http_url_rejected(self):
        self.assertFalse(self.check(upstream_release_url="http://example.org/releases/v1")["audit_complete"])

    def test_credentials_in_url_rejected(self):
        self.assertFalse(self.check(upstream_release_url="https://u:p@example.org/v1")["audit_complete"])

    def test_localhost_url_rejected(self):
        self.assertFalse(self.check(upstream_release_url="https://localhost/release")["audit_complete"])

    def test_symlink_signature_rejected(self):
        link = Path(self.tmp.name) / "link.sig"
        try:
            link.symlink_to(self.signature)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not supported by this runner")
        self.assertFalse(self.check(signature=link)["audit_complete"])

    def test_missing_openssl_binary_pin_rejected(self):
        self.assertFalse(self.check(trusted_openssl_sha256="")["audit_complete"])

    def test_wrong_openssl_binary_pin_rejected(self):
        result = self.check(trusted_openssl_sha256="0" * 64)
        self.assertFalse(result["audit_complete"])
        self.assertFalse(result["openssl_binary_hash_verified"])
        self.assertIn("OpenSSL executable SHA-256 pin mismatch", str(result["errors"]))

    def test_openssl_executable_symlink_rejected(self):
        link = Path(self.tmp.name) / "openssl-link"
        try:
            link.symlink_to(OPENSSL)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not supported")
        self.assertFalse(self.check(openssl=str(link))["audit_complete"])

    def test_external_tool_pin_cannot_be_replaced_by_artifact_pin(self):
        self.assertFalse(self.check(trusted_openssl_sha256=self.artifact_pin)["audit_complete"])

    def test_missing_openssl_rejected(self):
        self.assertFalse(self.check(openssl=str(Path(self.tmp.name) / "missing-openssl"))["audit_complete"])

    def test_wrong_publisher_key_rejected(self):
        wrong = Path(self.tmp.name) / "wrong-private.pem"
        wrong_public = Path(self.tmp.name) / "wrong-public.pem"
        self._cmd("genpkey", "-algorithm", "ED25519", "-out", str(wrong))
        self._cmd("pkey", "-in", str(wrong), "-pubout", "-out", str(wrong_public))
        self.assertFalse(self.check(public_key=wrong_public,
                                    trusted_key_sha256=self.sha(wrong_public))["audit_complete"])

    def test_rsa_key_type_rejected_before_signature_verification(self):
        rsa = Path(self.tmp.name) / "rsa-private.pem"
        rsa_public = Path(self.tmp.name) / "rsa-public.pem"
        self._cmd("genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(rsa))
        self._cmd("pkey", "-in", str(rsa), "-pubout", "-out", str(rsa_public))
        result = self.check(public_key=rsa_public, trusted_key_sha256=self.sha(rsa_public))
        self.assertFalse(result["audit_complete"])
        self.assertIn("not Ed25519", str(result["errors"]))

    def test_pem_with_extra_material_rejected(self):
        self.public.write_bytes(self.public.read_bytes() + b"UNEXPECTED EXTRA CONTENT\n")
        result = self.check(trusted_key_sha256=self.sha(self.public))
        self.assertFalse(result["audit_complete"])

    def test_empty_signature_rejected(self):
        self.signature.write_bytes(b"")
        self.assertFalse(self.check()["audit_complete"])

    def test_oversized_signature_rejected_before_external_verification(self):
        self.signature.write_bytes(b"X" * 65)
        result = self.check()
        self.assertFalse(result["audit_complete"])
        self.assertIn("exactly 64", str(result["errors"]))

    def test_short_signature_rejected(self):
        self.signature.write_bytes(b"X" * 63)
        self.assertFalse(self.check()["audit_complete"])

    def test_private_ip_url_rejected(self):
        for url in ("https://192.168.1.1/release", "https://[::1]/release",
                    "https://10.0.0.5:443/release", "https://example.local/release"):
            with self.subTest(url=url):
                self.assertFalse(self.check(upstream_release_url=url)["audit_complete"])

    def test_artifact_digest_is_streamed_not_loaded_entirely(self):
        import publisher_signature
        original = publisher_signature._read_regular
        calls = []
        def guarded(path, maximum):
            calls.append(str(path))
            self.assertNotEqual(Path(path), self.artifact)
            return original(path, maximum)
        with patch.object(publisher_signature, "_read_regular", side_effect=guarded):
            result = self.check()
        self.assertTrue(result["audit_complete"], result)
        self.assertTrue(calls)

    def test_streamed_hash_rejects_linked_artifact(self):
        link = Path(self.tmp.name) / "artifact-link.zip"
        try:
            link.symlink_to(self.artifact)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not supported")
        with self.assertRaises(ValueError):
            _digest_regular(link, LIMITS["artifact"])

    def test_streamed_hash_matches_reference_for_multimegabyte_file(self):
        self.artifact.write_bytes(os.urandom(4 * 1024 * 1024 + 123))
        self.assertEqual(_digest_regular(self.artifact, LIMITS["artifact"]), self.sha(self.artifact))
        self.sign()
        self.artifact_pin = self.sha(self.artifact)
        self.assertTrue(self.check()["audit_complete"])

    def test_post_verification_mutation_detected(self):
        import publisher_signature
        original = publisher_signature.subprocess.run
        def mutate_after(*args, **kwargs):
            outcome = original(*args, **kwargs)
            self.artifact.write_bytes(b"modified after external verification")
            return outcome
        with patch.object(publisher_signature.subprocess, "run", side_effect=mutate_after):
            result = self.check()
        self.assertFalse(result["audit_complete"])
        self.assertIn("changed during verification", str(result["errors"]))

    def test_post_verification_executable_mutation_detected(self):
        import publisher_signature
        original = publisher_signature._digest_regular
        executable = Path(OPENSSL).absolute()
        count = [0]
        def fake_second_tool_hash(path, maximum):
            if Path(path) == executable:
                count[0] += 1
                if count[0] == 2:
                    return "0" * 64
            return original(path, maximum)
        with patch.object(publisher_signature, "_digest_regular", side_effect=fake_second_tool_hash):
            result = self.check()
        self.assertFalse(result["audit_complete"])
        self.assertIn("executable changed", str(result["errors"]))

    def test_open_ssl_verification_does_not_modify_artifact(self):
        original = self.artifact.read_bytes()
        self.check()
        self.assertEqual(self.artifact.read_bytes(), original)

if __name__ == "__main__":
    unittest.main()
