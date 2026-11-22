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

    spliced_cases = 0
    for newline in ("\n", "\r\n", "\r"):
        splice = "\\" + newline
        for prefix in _RAW_PREFIXES:
            # Phase 2 removes a backslash-newline between any two raw-prefix
            # characters, including the final R/quote boundary, before tokenization.
            for split in range(1, len(prefix) + 1):
                label = f"{prefix} split={split} newline={newline!r}"
                physical_prefix = prefix[:split] + splice + prefix[split:] + '"'
                source = (
                    "void selected() {\n"
                    f'  const auto *payload = {physical_prefix}tag({{ " }} /* not a comment */ {{ )tag";\n'
                    "  return;\n"
                    "}\n"
                )
                masked = mask_non_code(source)
                if len(masked) != len(source):
                    raise AssertionError(f"{label}: lexer changed source offsets")
                if masked.count("\n") != source.count("\n"):
                    raise AssertionError(f"{label}: lexer changed newline positions")

                literal_start = source.index("payload = ") + len("payload = ")
                literal_end = source.index(')tag"', literal_start) + len(')tag"')
                if any(masked[index] not in " \r\n" for index in range(literal_start, literal_end)):
                    raise AssertionError(
                        f"{label}: phase-2-spliced raw literal was not fully masked"
                    )

                extracted = extract_function(source, "selected")
                if "return;" not in extracted or not extracted.rstrip().endswith("}"):
                    raise AssertionError(
                        f"{label}: spliced raw literal truncated the containing function"
                    )
                spliced_cases += 1

    print("FIRMWARE_SOURCE_EXTRACTOR_RAW_PREFIX_PASS 5/5")
    print(f"FIRMWARE_SOURCE_EXTRACTOR_SPLICED_RAW_PREFIX_PASS {spliced_cases}/{spliced_cases}")


if __name__ == "__main__":
    run_source_extractor_regressions()
