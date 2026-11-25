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
        148,
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


    unicode_helper = extract(source, "pollJsonSkipUnicodeEscape")
    high_surrogate_guard = "if(first>=0xD800 && first<=0xDBFF){"
    low_surrogate_guard = "return !(first>=0xDC00 && first<=0xDFFF);"
    if unicode_helper.count(high_surrogate_guard) != 1:
        raise AssertionError(f"{board}: expected one high-surrogate pair guard")
    if unicode_helper.count(low_surrogate_guard) != 1:
        raise AssertionError(f"{board}: expected one isolated-low-surrogate guard")

    bypass_high_pair = unicode_helper.replace(
        high_surrogate_guard, "if(false){", 1
    )
    expect_mutation_rejected(
        stubs + parser.replace(unicode_helper, bypass_high_pair, 1) + UTF8_MAIN,
        board,
        "accept-unpaired-high-surrogate",
        151,
    )

    bypass_low_rejection = unicode_helper.replace(
        low_surrogate_guard, "return true;", 1
    )
    expect_mutation_rejected(
        stubs + parser.replace(unicode_helper, bypass_low_rejection, 1) + UTF8_MAIN,
        board,
        "accept-isolated-low-surrogate",
        152,
    )

    print(
        f"{board}: POLL_JSON_UTF8_VALIDATION_PASS "
        "valid=5/5 invalid=13/13; mutations=6/6 rejected"
    )
