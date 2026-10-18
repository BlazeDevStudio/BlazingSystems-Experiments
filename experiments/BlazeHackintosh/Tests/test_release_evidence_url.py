"""Regression tests for public HTTPS evidence URL syntax (not authenticity)."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_gates", ROOT / "release_gates.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvidenceURLTests(unittest.TestCase):
    def test_current_manifest_stays_blocked(self):
        result = module.readiness()
        self.assertEqual(result["gates_total"], 26)
        self.assertEqual(result["gates_verified"], 3)
        self.assertEqual(result["remaining"], 23)
        self.assertFalse(result["production_ready"])

    def test_valid_public_https_urls(self):
        for value in (
            "https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39143682283",
            "https://example.org/docs/license",
            "https://example.org:443/evidence?hash=abc",
        ):
            with self.subTest(url=value):
                self.assertTrue(module._valid_evidence_url(value))

    def test_invalid_evidence_urls(self):
        invalid = (
            "https://", "http://example.org/evidence",
            "https://localhost/evidence", "https://127.0.0.1/evidence",
            "https://[::1]/evidence", "https://internal.local/evidence",
            "https://internal.test/evidence", "https://192.168.0.1/evidence",
            "https://user:password@example.org/evidence",
            "https://user@example.org/evidence",
            "https://example.org:badport/evidence",
            "https://example.org:8443/evidence",
            "https://example.org:999999/evidence",
            "https://example.org/evidence#fragment",
            "https://example.org", "https://singlelabel/evidence",
            "https://bad_host.example.org/evidence",
            "https://-bad.example.org/evidence",
            "https://example.org./evidence",
            "https://example.org/evidence ",
            "https://example.org/\u00fc",
            "https://example.org/evidence\x00",
            "https://example.org/evidence\r\nHeader: value",
            "https://example.org/" + "a" * 2050,
        )
        for value in invalid:
            with self.subTest(url=value):
                self.assertFalse(module._valid_evidence_url(value), value)

    def test_invalid_url_rejected_by_readiness(self):
        document = json.loads(module.DEFAULT.read_text(encoding="utf-8"))
        gate = next(item for item in document["gates"] if item["status"] == "verified")
        gate["evidence"] = ["https://127.0.0.1/fake"]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "gates.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Evidence URLs"):
                module.readiness(path)

    def test_missing_gate_still_rejected(self):
        document = json.loads(module.DEFAULT.read_text(encoding="utf-8"))
        document["gates"].pop()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "gates.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing or unrecognized"):
                module.readiness(path)


if __name__ == "__main__":
    unittest.main()
