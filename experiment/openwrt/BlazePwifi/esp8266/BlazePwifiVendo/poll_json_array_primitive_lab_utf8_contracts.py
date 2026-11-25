"""Raw UTF-8 validation contracts for source-extracted poll JSON strings."""

from poll_json_array_primitive_lab_fixtures import UTF8_MAIN


def verify_utf8_contracts(
    board, source, parser, stubs, extract, expect_mutation_rejected
):
    helper = extract(source, "pollJsonSkipUtf8Continuation")
    string_parser = extract(source, "pollJsonSkipString")
    callsite = (
        "if(c>=0x80 && !pollJsonSkipUtf8Continuation(r,p,c)) return false;"
    )
    minimum_guard = "if(second<minimumSecond) return false;"
    maximum_guard = "if(second>maximumSecond) return false;"

    if helper.count(minimum_guard) != 1 or helper.count(maximum_guard) != 1:
        raise AssertionError(
            f"{board}: UTF-8 overlong/surrogate/range guards changed"
        )
    if string_parser.count(callsite) != 1:
        raise AssertionError(
            f"{board}: raw UTF-8 bytes are not validated by the string parser"
        )

    bypass_callsite = string_parser.replace(callsite, "", 1)
    expect_mutation_rejected(
        stubs + parser.replace(string_parser, bypass_callsite, 1) + UTF8_MAIN,
        board,
        "bypass-invalid-utf8-deny",
        141,
    )

    widen_minimum = helper.replace("minimumSecond=0xA0;", "minimumSecond=0x80;", 1)
    expect_mutation_rejected(
        stubs + parser.replace(helper, widen_minimum, 1) + UTF8_MAIN,
        board,
        "accept-overlong-utf8-sequence",
        146,
    )

    widen_surrogate = helper.replace("maximumSecond=0x9F;", "maximumSecond=0xBF;", 1)
    expect_mutation_rejected(
        stubs + parser.replace(helper, widen_surrogate, 1) + UTF8_MAIN,
        board,
        "accept-utf8-surrogate-encoding",
        144,
    )

    widen_scalar = helper.replace("maximumSecond=0x8F;", "maximumSecond=0xBF;", 1)
    expect_mutation_rejected(
        stubs + parser.replace(helper, widen_scalar, 1) + UTF8_MAIN,
        board,
        "accept-utf8-above-unicode-range",
        145,
    )

    print(
        f"{board}: POLL_JSON_UTF8_VALIDATION_PASS "
        "valid=3/3 invalid=9/9; mutations=4/4 rejected"
    )
