#!/usr/bin/env python3
"""PHX-HW proposal-only controller response fixtures. Never grants GPIO or coins.

Run: python3 -m unittest -v tests/test_v060_controller_envelope_proposal.py
This checks proposed envelope shape and binding only; it does NOT authenticate.
No signer, key, accepted wire format or protected monotonic witness is supplied.
"""
import copy
import json
import unittest

EXPECTED = {
    "profile": "PROPOSAL_ONLY_NOT_CORE_WIRE",
    "device_id": "lab-esp8266-a",
    "request_nonce": "0123456789abcdef",
    "config_revision": 7,
    "configuration": {
        "enabled": 1, "coin_enabled": 1, "relay_enabled": 1,
        "led_enabled": 0, "coin_pin": 4, "relay_pin": 5,
        "led_pin": 14, "coin_active_low": 1,
        "relay_active_high": 0, "led_active_high": 1,
        "coin_debounce_ms": 40, "pulse_group_ms": 400,
        "max_wifi_retries": 6
    },
    "signature": "UNAVAILABLE",
    "protected_witness": "UNAVAILABLE"
}
FIELDS = set(EXPECTED["configuration"])


def strict_json(raw):
    def pairs(seq):
        obj = {}
        for key, value in seq:
            if key in obj:
                raise ValueError("duplicate key")
            obj[key] = value
        return obj
    return json.loads(raw, object_pairs_hook=pairs)


def proposal_shape(envelope, device_id, request_nonce, minimum_revision):
    """Schema-check only. True is NEVER authorization to energize or accept coins."""
    if not isinstance(envelope, dict) or set(envelope) != set(EXPECTED):
        return False
    if envelope["profile"] != EXPECTED["profile"]:
        return False
    if envelope["device_id"] != device_id or envelope["request_nonce"] != request_nonce:
        return False
    revision = envelope["config_revision"]
    if type(revision) is not int or revision <= minimum_revision:
        return False
    config = envelope["configuration"]
    if not isinstance(config, dict) or set(config) != FIELDS:
        return False
    for key in ("enabled", "coin_enabled", "relay_enabled", "led_enabled",
                "coin_active_low", "relay_active_high", "led_active_high"):
        if type(config[key]) is not int or config[key] not in (0, 1):
            return False
    for key in ("coin_pin", "relay_pin", "led_pin"):
        if type(config[key]) is not int or not (-1 <= config[key] <= 63):
            return False
    for key, low, high in (("coin_debounce_ms", 1, 2000),
                           ("pulse_group_ms", 10, 10000),
                           ("max_wifi_retries", 1, 60)):
        if type(config[key]) is not int or not low <= config[key] <= high:
            return False
    return True


def may_admit_coin(_envelope):
    """Fail-closed until CORE contract, real verifier and protected witness exist."""
    return False


class ContractProposalFixtures(unittest.TestCase):
    def test_positive_schema_only_not_authorized(self):
        self.assertTrue(proposal_shape(EXPECTED, "lab-esp8266-a", "0123456789abcdef", 6))
        self.assertFalse(may_admit_coin(EXPECTED))

    def test_wrong_device(self):
        self.assertFalse(proposal_shape(EXPECTED, "lab-esp32-b", "0123456789abcdef", 6))

    def test_wrong_request_nonce(self):
        self.assertFalse(proposal_shape(EXPECTED, "lab-esp8266-a", "fedcba9876543210", 6))

    def test_replay_or_rollback(self):
        for min_revision in (7, 8):
            self.assertFalse(proposal_shape(EXPECTED, "lab-esp8266-a", "0123456789abcdef", min_revision))

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError):
            strict_json('{"config_revision":7,"config_revision":8}')

    def test_malformed_types_and_unknown_fields(self):
        for field, value in (("enabled", True), ("coin_pin", 99), ("coin_debounce_ms", 0)):
            fixture = copy.deepcopy(EXPECTED)
            fixture["configuration"][field] = value
            self.assertFalse(proposal_shape(fixture, "lab-esp8266-a", "0123456789abcdef", 6))
        fixture = copy.deepcopy(EXPECTED)
        fixture["configuration"]["unknown"] = 1
        self.assertFalse(proposal_shape(fixture, "lab-esp8266-a", "0123456789abcdef", 6))

    def test_missing_signature_or_witness_never_authorizes(self):
        for key in ("signature", "protected_witness"):
            fixture = copy.deepcopy(EXPECTED)
            del fixture[key]
            self.assertFalse(proposal_shape(fixture, "lab-esp8266-a", "0123456789abcdef", 6))
            self.assertFalse(may_admit_coin(fixture))


if __name__ == "__main__":
    unittest.main()
