"""Nested array/object separators, depth and JSON string escape contracts."""

from poll_json_array_primitive_lab_fixtures import COMPOSITE_MAIN, DEPTH_MAIN


def verify_composite_contracts(
    board, source, parser, stubs, extract, expect_mutation_rejected
):
    composite = extract(source, "pollJsonSkipCompositeDepth")
    depth_guard = " || depth>16"
    if composite.count(depth_guard) != 1:
        raise AssertionError(
            f"{board}: expected exactly one composite nesting-depth guard"
        )
    depth_mutant = composite.replace(depth_guard, "", 1)
    expect_mutation_rejected(
        stubs + parser.replace(composite, depth_mutant, 1) + DEPTH_MAIN,
        board, "remove-composite-depth-cap", 122
    )

    off_by_one_mutant = composite.replace("depth>16", "depth>17", 1)
    if off_by_one_mutant == composite:
        raise AssertionError(f"{board}: depth-bound mutation anchor missing")
    expect_mutation_rejected(
        stubs + parser.replace(composite, off_by_one_mutant, 1) + DEPTH_MAIN,
        board, "allow-depth-17", 122
    )

    separator = "if(p>=n || r[p++]!=',') return false;"
    if composite.count(separator) != 2:
        raise AssertionError(
            f"{board}: expected one array and one object member separator"
        )
    array_mutant = composite.replace(separator, "", 1)
    expect_mutation_rejected(
        stubs + parser.replace(composite, array_mutant, 1) + COMPOSITE_MAIN,
        board, "missing-array-separator", 61
    )

    object_prefix, object_suffix = composite.rsplit(separator, 1)
    object_mutant = object_prefix + object_suffix
    expect_mutation_rejected(
        stubs + parser.replace(composite, object_mutant, 1) + COMPOSITE_MAIN,
        board, "missing-object-separator", 71
    )

    string_parser = extract(source, "pollJsonSkipString")
    control_guard = "if(c<0x20) return false;"
    if string_parser.count(control_guard) != 1:
        raise AssertionError(f"{board}: expected one raw-control guard")
    expect_mutation_rejected(
        stubs + parser.replace(
            string_parser, string_parser.replace(control_guard, "", 1), 1
        ) + COMPOSITE_MAIN,
        board, "accept-raw-control-in-string", 76
    )

    escape_start = string_parser.find("} else if(e!='")
    if escape_start < 0 or string_parser.count("} else if(e!='") != 1:
        raise AssertionError(f"{board}: expected one unsupported-escape branch")
    escape_end = string_parser.find("{", escape_start) + 1
    if escape_end <= escape_start:
        raise AssertionError(f"{board}: unsupported-escape branch is incomplete")
    mutated_string_parser = (
        string_parser[:escape_start] + "} else if(false){"
        + string_parser[escape_end:]
    )
    expect_mutation_rejected(
        stubs + parser.replace(string_parser, mutated_string_parser, 1)
        + COMPOSITE_MAIN,
        board, "accept-unsupported-string-escape", 73
    )

    unicode_guard = "!pollJsonHex(r[p])"
    if string_parser.count(unicode_guard) != 1:
        raise AssertionError(f"{board}: expected one Unicode hex guard")
    expect_mutation_rejected(
        stubs + parser.replace(
            string_parser,
            string_parser.replace(unicode_guard, "false", 1),
            1
        ) + COMPOSITE_MAIN,
        board, "accept-nonhex-unicode-escape", 75
    )
