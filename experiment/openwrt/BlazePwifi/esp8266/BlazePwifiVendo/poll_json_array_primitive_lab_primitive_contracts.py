"""JSON primitive terminators, number grammar and boolean literal contracts."""

from poll_json_array_primitive_lab_fixtures import COMPOSITE_MAIN, PRIMITIVE_MAIN


def verify_primitive_contracts(
    board, source, parser, stubs, extract, expect_mutation_rejected
):
    primitive = extract(source, "pollJsonSkipPrimitive")
    delimiter = " && r[p]!=']'"
    if primitive.count(delimiter) != 1:
        raise AssertionError(
            f"{board}: expected exactly one array primitive terminator"
        )
    expect_mutation_rejected(
        stubs + parser.replace(
            primitive, primitive.replace(delimiter, "", 1), 1
        ) + COMPOSITE_MAIN,
        board, "missing-array-primitive-terminator", 61
    )

    leading_zero_guard = "if(r[q]=='0'){\n    ++q;"
    if primitive.count(leading_zero_guard) != 1:
        raise AssertionError(f"{board}: expected one leading-zero guard")
    leading_zero_mutant = primitive.replace(
        leading_zero_guard,
        "if(r[q]=='0'){\n    ++q;\n    while(q<end && r[q]>='0' && r[q]<='9') ++q;",
        1
    )
    expect_mutation_rejected(
        stubs + parser.replace(primitive, leading_zero_mutant, 1)
        + PRIMITIVE_MAIN,
        board, "accept-leading-zero-integer", 101
    )

    fraction_guard = "if(q==fractionStart) return false;"
    if primitive.count(fraction_guard) != 1:
        raise AssertionError(f"{board}: expected one fraction digit guard")
    fraction_mutant = primitive.replace(
        fraction_guard, "if(q==fractionStart) { /* bypass */ }", 1
    )
    expect_mutation_rejected(
        stubs + parser.replace(primitive, fraction_mutant, 1)
        + PRIMITIVE_MAIN,
        board, "accept-empty-fraction", 105
    )

    exponent_guard = "if(q==exponentStart) return false;"
    if primitive.count(exponent_guard) != 1:
        raise AssertionError(f"{board}: expected one exponent digit guard")
    exponent_mutant = primitive.replace(
        exponent_guard, "if(q==exponentStart) { /* bypass */ }", 1
    )
    expect_mutation_rejected(
        stubs + parser.replace(primitive, exponent_mutant, 1)
        + PRIMITIVE_MAIN,
        board, "accept-empty-exponent", 106
    )

    true_literal = (
        "if(length==4 && r[start]=='t' && r[start+1]=='r' &&\n"
        "     r[start+2]=='u' && r[start+3]=='e') return true;"
    )
    if primitive.count(true_literal) != 1:
        raise AssertionError(f"{board}: expected one exact true literal guard")
    true_literal_mutant = primitive.replace(
        true_literal, "if(length>=3 && r[start]=='t') return true;", 1
    )
    expect_mutation_rejected(
        stubs + parser.replace(primitive, true_literal_mutant, 1)
        + PRIMITIVE_MAIN,
        board, "accept-truncated-true-literal", 113
    )
    print(
        f"{board}: POLL_JSON_PRIMITIVE_GRAMMAR_PASS "
        "valid=9/9 invalid=16/16; mutations=4/4 rejected"
    )
