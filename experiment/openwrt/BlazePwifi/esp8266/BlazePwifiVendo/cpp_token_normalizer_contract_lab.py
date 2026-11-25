#!/usr/bin/env python3
"""Regression contracts for the PHX-HARDWARE C++ token normalizer.

These tests run against the existing bounded-response parity lab. They are
host-side lexical checks only; they do not compile or exercise a physical board.
"""
import unittest

from cpp_token_normalizer import tokenize_cpp


class CppTokenNormalizerContractTests(unittest.TestCase):
    def test_decimal_exponent_is_one_preprocessing_number(self):
        self.assertEqual(
            tokenize_cpp("return 1e-3;"),
            (("identifier", "return"), ("number", "1e-3"), ("punct", ";")),
        )

    def test_hexadecimal_exponent_is_one_preprocessing_number(self):
        self.assertEqual(
            tokenize_cpp("return 0x1.fp-2;"),
            (("identifier", "return"), ("number", "0x1.fp-2"), ("punct", ";")),
        )

    def test_whitespace_before_exponent_sign_changes_tokenization(self):
        compact = tokenize_cpp("return 1e-3;")
        separated = tokenize_cpp("return 1e - 3;")
        self.assertNotEqual(compact, separated)

    def test_raw_string_prefix_and_payload_are_preserved(self):
        self.assertEqual(
            tokenize_cpp('return u8R"cfg(alpha  beta)cfg";'),
            (
                ("identifier", "return"),
                ("literal", 'u8R"cfg(alpha  beta)cfg"'),
                ("punct", ";"),
            ),
        )

    def test_comments_do_not_join_adjacent_identifiers(self):
        self.assertNotEqual(tokenize_cpp("left/**/right"), tokenize_cpp("leftright"))

    def test_unterminated_block_comment_fails_closed(self):
        with self.assertRaises(ValueError):
            tokenize_cpp("int value; /* no close")

    def test_unterminated_quoted_literal_fails_closed(self):
        with self.assertRaises(ValueError):
            tokenize_cpp('return "unfinished')

    def test_overlong_raw_string_delimiter_fails_closed(self):
        delimiter = "abcdefghijklmnopq"
        with self.assertRaises(ValueError):
            tokenize_cpp(f'R"{delimiter}(body){delimiter}"')

    def test_longest_match_shift_assignment_is_one_punctuator(self):
        self.assertEqual(
            tokenize_cpp("value>>=2"),
            (("identifier", "value"), ("punct", ">>="), ("number", "2")),
        )

    def test_digit_separator_stays_inside_number_token(self):
        self.assertIn(("number", "1'000"), tokenize_cpp("return 1'000;"))

    def test_arithmetic_sign_is_not_absorbed_without_exponent_marker(self):
        self.assertEqual(
            tokenize_cpp("return 1+2;"),
            (
                ("identifier", "return"),
                ("number", "1"),
                ("punct", "+"),
                ("number", "2"),
                ("punct", ";"),
            ),
        )

    def test_user_defined_string_suffix_is_attached_to_literal(self):
        compact = tokenize_cpp('return u8"payload"_tag;')
        separated = tokenize_cpp('return u8"payload" _tag;')
        self.assertNotEqual(compact, separated)
        self.assertEqual(
            compact,
            (
                ("identifier", "return"),
                ("literal", 'u8"payload"_tag'),
                ("punct", ";"),
            ),
        )

    def test_user_defined_raw_string_suffix_is_attached_to_literal(self):
        compact = tokenize_cpp('return R"cfg(payload)cfg"_tag;')
        separated = tokenize_cpp('return R"cfg(payload)cfg" _tag;')
        self.assertNotEqual(compact, separated)
        self.assertEqual(
            compact,
            (
                ("identifier", "return"),
                ("literal", 'R"cfg(payload)cfg"_tag'),
                ("punct", ";"),
            ),
        )

    def test_user_defined_character_suffix_is_attached_to_literal(self):
        compact = tokenize_cpp("return 'x'_tag;")
        separated = tokenize_cpp("return 'x' _tag;")
        self.assertNotEqual(compact, separated)
        self.assertEqual(
            compact,
            (
                ("identifier", "return"),
                ("literal", "'x'_tag"),
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
    print("CPP_TOKEN_NORMALIZER_CONTRACT_PASS 14/14")
