#!/usr/bin/env python3
"""Independent PHX-QA recipient-contract regression against real Master source.

Execute from the repository root:
    python3 -m unittest discover -s tests/phoenix_coordination -p 'test_*.py' -v

This intentionally imports coordination/phoenix/verify_coordination.py rather
than copying its implementation. Current verifier is expected to be RED for
unrecognized 'to' roles until PHX-MASTER fixes the contract.
No network, firmware, money, or real devices are involved.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COORDINATION = ROOT / "coordination" / "phoenix"
VERIFIER = COORDINATION / "verify_coordination.py"
EXAMPLE = COORDINATION / "COMMUNICATION_EXAMPLE.json"


def load_real_validator():
    """Fail INCONCLUSIVE on missing source, never replace it with a mock."""
    if not VERIFIER.is_file() or not EXAMPLE.is_file():
        raise RuntimeError("Actual PHX-MASTER source and fixture are required")
    spec = importlib.util.spec_from_file_location("phoenix_master_verifier", VERIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load actual PHX-MASTER verification module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecipientContractRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_real_validator()
        cls.example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        cls.assertion_context = (
            "The BLAZE-COMMS/1 'to' field must not accept an unknown role; "
            "PHX-MASTER owns the source fix."
        )

    def validate_with_recipient(self, recipient: str) -> list[str]:
        message = copy.deepcopy(self.example)
        message["to"] = recipient
        return self.module.validate_envelope(message)

    def test_existing_all_recipient_remains_valid(self):
        self.assertEqual(self.validate_with_recipient("ALL"), [])

    def test_known_role_recipient_remains_valid(self):
        self.assertEqual(self.validate_with_recipient("PHX-QA"), [])

    def test_unknown_single_recipient_is_denied(self):
        self.assertTrue(
            self.validate_with_recipient("PHX-UNKNOWN"),
            self.assertion_context,
        )

    def test_unknown_recipient_in_multi_target_is_denied(self):
        # Some historical comments used semicolon-separated recipients.
        # Regardless of the Master's final list policy, a nonexistent role
        # mixed with a real one must never silently validate.
        self.assertTrue(
            self.validate_with_recipient("PHX-QA;PHX-UNKNOWN"),
            self.assertion_context,
        )


if __name__ == "__main__":
    unittest.main()
