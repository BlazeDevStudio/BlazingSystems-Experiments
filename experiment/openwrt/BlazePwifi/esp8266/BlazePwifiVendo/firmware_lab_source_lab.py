#!/usr/bin/env python3
"""Regression checks for the shared ESP firmware C/C++ source lexer."""

from firmware_lab_source import extract_function, mask_non_code

_RAW_PREFIXES = ("u8R", "uR", "UR", "LR", "R")


def run_source_extractor_regressions():
    for prefix in _RAW_PREFIXES:
        source = (
            "void selected() {\n"
            f'  const char *payload = {prefix}"tag(" }} " /* not a comment */ {{ " )tag";\n'
            "  return;\n"
            "}\n"
        )
        masked = mask_non_code(source)
        if len(masked) != len(source):
            raise AssertionError(f"{prefix}: lexer changed source offsets")
        if masked.count("\n") != source.count("\n"):
            raise AssertionError(f"{prefix}: lexer changed newline positions")

        raw_start = source.index(f'{prefix}"')
        raw_end = source.index(')tag"', raw_start) + len(')tag"')
        if any(masked[index] not in " \r\n" for index in range(raw_start, raw_end)):
            raise AssertionError(f"{prefix}: raw literal or encoding prefix was not masked")

        extracted = extract_function(source, "selected")
        if "return;" not in extracted or not extracted.rstrip().endswith("}"):
            raise AssertionError(f"{prefix}: raw literal truncated the containing function")

    print("FIRMWARE_SOURCE_EXTRACTOR_RAW_PREFIX_PASS 5/5")


if __name__ == "__main__":
    run_source_extractor_regressions()
