"""Release-readiness contract: never silently omit unfinished production gates."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_gates", ROOT / "release_gates.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ReleaseGatesTests(unittest.TestCase):
    def test_full_production_manifest_is_not_prematurely_green(self):
        result = module.readiness()
        self.assertGreaterEqual(result["gates_total"], 20)
        self.assertGreater(result["remaining"], 0)
        self.assertFalse(result["production_ready"])
        names = {b["id"] for b in result["blockers"]}
        self.assertIn("hardware-acceptance", names)
        self.assertIn("windows-gui", names)
        self.assertIn("production-release", names)

    def test_verified_gate_must_have_reviewable_evidence(self):
        manifest = json.loads(module.DEFAULT.read_text())
        item = next(x for x in manifest["gates"] if x["status"] == "verified")
        item["evidence"] = []
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gates.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "requires evidence"):
                module.readiness(path)

    def test_duplicate_required_gate_rejected(self):
        manifest = json.loads(module.DEFAULT.read_text())
        manifest["gates"].append(copy.deepcopy(manifest["gates"][0]))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gates.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                module.readiness(path)

    def test_cannot_drop_a_required_gate_to_fake_completion(self):
        manifest = json.loads(module.DEFAULT.read_text())
        manifest["gates"] = [g for g in manifest["gates"] if g["id"] != "windows-gui"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gates.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "Missing or unrecognized"):
                module.readiness(path)

if __name__ == "__main__":
    unittest.main()
