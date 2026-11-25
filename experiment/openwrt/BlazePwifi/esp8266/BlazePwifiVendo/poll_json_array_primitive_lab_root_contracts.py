"""Root-level status uniqueness and complete-document JSON contracts."""

from poll_json_array_primitive_lab_fixtures import (
    DUPLICATE_ROOT_MAIN,
    TRAILING_DATA_MAIN,
)


def verify_root_envelope_contracts(
    board, source, parser, stubs, extract, expect_mutation_rejected
):
    top_level = extract(source, "pollJsonTopLevelTrue")
    duplicate_guard = "if(++found!=1) return false;"
    final_guard = "return p==n && found==1 && accepted;"
    if top_level.count(duplicate_guard) != 1 or top_level.count(final_guard) != 1:
        raise AssertionError(
            f"{board}: duplicate-root or trailing-data guard anchor changed"
        )

    duplicate_mutant = top_level.replace(duplicate_guard, "++found;", 1)
    duplicate_mutant = duplicate_mutant.replace(
        final_guard, "return p==n && found>=1 && accepted;", 1
    )
    expect_mutation_rejected(
        stubs + parser.replace(top_level, duplicate_mutant, 1)
        + DUPLICATE_ROOT_MAIN,
        board, "allow-duplicate-root-status", 91
    )

    trailing_mutant = top_level.replace(
        final_guard, "return found==1 && accepted;", 1
    )
    expect_mutation_rejected(
        stubs + parser.replace(top_level, trailing_mutant, 1)
        + TRAILING_DATA_MAIN,
        board, "accept-trailing-json-data", 93
    )
    print(
        f"{board}: POLL_JSON_ROOT_ENVELOPE_PASS "
        "duplicate=2/2 trailing=3/3; mutations=2/2 rejected"
    )
