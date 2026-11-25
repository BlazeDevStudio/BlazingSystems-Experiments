#!/usr/bin/env python3
"""Regression contracts for the PHX-HARDWARE C++ token normalizer.

These tests run against the existing bounded-response parity lab. They are
host-side lexical checks only; they do not compile or exercise a physical board.
"""
import unittest

from bounded_http_response_lab import _cpp_token_sequence


class CppTokenNormalizerContractTests(unittest.TestCase):
    def test_decimal_exponent_is_one_preprocessing_number(self):
        self.assertEqual(
            _cpp_token_sequence("return 1e-3;"),
            (("identifier", "return"), ("number", "1e-3"), ("punct", ";")),
        )

    def test_hexadecimal_exponent_is_one_preprocessing_number(self):
        self.assertEqual(
            _cpp_token_sequence("return 0x1.fp-2;"),
            (("identifier", "return"), ("number", "0x1.fp-2"), ("punct", ";")),
        )

    def test_whitespace_before_exponent_sign_changes_tokenization(self):
        compact = _cpp_token_sequence("return 1e-3;")
        separated = _cpp_token_sequence("return 1e - 3;")
        self.assertNotEqual(compact, separated)

    def test_digit_separator_stays_inside_number_token(self):
        self.assertIn(("number", "1'000"), _cpp_token_sequence("return 1'000;"))

    def test_arithmetic_sign_is_not_absorbed_without_exponent_marker(self):
        self.assertEqual(
            _cpp_token_sequence("return 1+2;"),
            (
                ("identifier", "return"),
                ("number", "1"),
                ("punct", "+"),
                ("number", "2"),
                ("punct", ";"),
            ),
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        CppTokenNormalizerContractTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("CPP_TOKEN_NORMALIZER_CONTRACT_PASS 5/5")
