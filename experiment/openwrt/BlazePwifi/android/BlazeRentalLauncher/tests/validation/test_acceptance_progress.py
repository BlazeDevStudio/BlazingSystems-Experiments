"""Host-only negative tests for the provisional PHX-ANDROID acceptance ledger."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

LAUNCHER = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "compute_acceptance_progress",
    LAUNCHER / "tools" / "compute_acceptance_progress.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class AcceptanceLedgerTest(unittest.TestCase):
    def setUp(self):
        self.ledger = json.loads(
            (LAUNCHER / "PHX_RENTAL_WORKSTREAM_ACCEPTANCE.json").read_text())

    def test_actual_31_criterion_scope_is_stably_weighted(self):
        result = checker.calculate(self.ledger)
        self.assertEqual(len(self.ledger["criteria"]), 31)
        self.assertEqual(result["readiness_total_weight"], 98)
        expected = sum(c["weight"] for c in self.ledger["criteria"]
                       if c["status"] == "VERIFIED" and c["dimension"] != "actual_deployment")
        self.assertEqual(result["readiness_verified_weight"], expected)
        self.assertEqual(result["readiness_bar20"],
                         "#" * (expected * 20 // 98) + "." * (20 - expected * 20 // 98))
        self.assertEqual(result["actual_deployment_verified_percent"], 0)

    def test_scoped_document_cannot_call_itself_global(self):
        self.ledger["scope_status"] = "GLOBAL_CONFIRMED"
        with self.assertRaisesRegex(checker.LedgerInvalid, "global roadmap"):
            checker.calculate(self.ledger)

    def test_duplicate_ids_fail(self):
        self.ledger["criteria"][1]["id"] = self.ledger["criteria"][0]["id"]
        with self.assertRaisesRegex(checker.LedgerInvalid, "duplicated"):
            checker.calculate(self.ledger)

    def test_wrong_status_fails(self):
        self.ledger["criteria"][0]["status"] = "MOSTLY DONE"
        with self.assertRaisesRegex(checker.LedgerInvalid, "invalid status"):
            checker.calculate(self.ledger)

    def test_missing_verified_evidence_fails(self):
        item = next(c for c in self.ledger["criteria"] if c["status"] == "VERIFIED")
        item["evidence"] = []
        with self.assertRaisesRegex(checker.LedgerInvalid, "without exact"):
            checker.calculate(self.ledger)

    def test_denominator_cannot_drift_silently(self):
        self.ledger["criteria"][0]["weight"] += 1
        with self.assertRaisesRegex(checker.LedgerInvalid, "denominator drifted"):
            checker.calculate(self.ledger)

    def test_not_applicable_needs_documented_scope_decision(self):
        self.ledger["criteria"][0]["status"] = "NOT APPLICABLE"
        with self.assertRaisesRegex(checker.LedgerInvalid, "approved scope decision"):
            checker.calculate(self.ledger)

    def test_unknown_items_receive_no_partial_credit(self):
        self.ledger["criteria"][0]["status"] = "UNKNOWN"
        output = checker.calculate(self.ledger)
        self.assertEqual(output["readiness_verified_weight"], sum(c["weight"] for c in self.ledger["criteria"] if c["status"] == "VERIFIED" and c["dimension"] != "actual_deployment"))
        self.assertGreater(output["readiness_unknown_weight"], 0)

    def test_non_integer_weight_fails(self):
        self.ledger["criteria"][0]["weight"] = 0.5
        with self.assertRaisesRegex(checker.LedgerInvalid, "positive fixed integer"):
            checker.calculate(self.ledger)

    def test_verified_date_is_required(self):
        item = next(c for c in self.ledger["criteria"] if c["status"] == "VERIFIED")
        item["verified_at_utc"] = None
        with self.assertRaisesRegex(checker.LedgerInvalid, "without exact"):
            checker.calculate(self.ledger)


if __name__ == "__main__":
    unittest.main()
