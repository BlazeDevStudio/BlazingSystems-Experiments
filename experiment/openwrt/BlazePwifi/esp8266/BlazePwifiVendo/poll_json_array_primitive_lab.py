"""Source-exact strict JSON composite grammar regression for both coin controllers.

The firmware parser must validate nested array/object separators, primitive
terminators, and closing delimiters before a root-level status can be read.
The host lab is simulated control-flow evidence, not controller authentication.
"""
from pathlib import Path

from cpp_fixture_runner import run_cpp_fixture

from poll_json_array_primitive_lab_fixtures import (
    COMPOSITE_MAIN,
    DEPTH_MAIN,
    DUPLICATE_ROOT_MAIN,
    PARSER_FUNCTIONS,
    PRIMITIVE_MAIN,
    PROTOTYPES,
    TRAILING_DATA_MAIN,
    UTF8_MAIN,
)
from poll_json_array_primitive_lab_root_contracts import (
    verify_root_envelope_contracts,
)
from poll_json_array_primitive_lab_composite_contracts import (
    verify_composite_contracts,
)
from poll_json_array_primitive_lab_primitive_contracts import (
    verify_primitive_contracts,
)


def _compile_and_run(code, board, label):
    """Use the shared bounded compiler/runner for every source-extracted case."""
    return run_cpp_fixture(
        code,
        prefix="phx-json-composite-",
        stem=label,
        extra_flags=("-Wno-unused-parameter",),
        compile_timeout=30,
        run_timeout=10,
        context=f"{board}: {label}",
    )


def _expect_mutation_rejected(code, board, label, expected_exit):
    result = _compile_and_run(code, board, label)
    if result.returncode != expected_exit:
        raise AssertionError(
            f"{board}: {label} mutation survived or failed unexpectedly "
            f"(expected exit {expected_exit}, got {result.returncode}; "
            f"stdout={result.stdout}; stderr={result.stderr})"
        )
    print(f"{board}: MUTATION_REJECTED {label} expected_exit={expected_exit}")


def _require_baseline(board, label, description, result):
    if result.returncode:
        raise AssertionError(
            f"{board}: {description} "
            f"(exit={result.returncode}; stdout={result.stdout}; "
            f"stderr={result.stderr})"
        )


def verify(boards, extract, stubs):
    for board, path in boards.items():
        source = path.read_text(encoding="utf-8")
        parser = PROTOTYPES + "\n\n".join(
            extract(source, name) for name in PARSER_FUNCTIONS
        )

        baselines = (
            (
                "baseline",
                "strict JSON composite cases failed",
                COMPOSITE_MAIN,
            ),
            (
                "primitive-baseline",
                "strict JSON primitive cases failed",
                PRIMITIVE_MAIN,
            ),
            (
                "utf8-baseline",
                "strict JSON UTF-8 cases failed",
                UTF8_MAIN,
            ),
            (
                "depth-baseline",
                "composite nesting-depth boundary failed",
                DEPTH_MAIN,
            ),
            (
                "duplicate-root-baseline",
                "duplicate root status keys were not denied",
                DUPLICATE_ROOT_MAIN,
            ),
            (
                "trailing-data-baseline",
                "trailing JSON data was not denied or whitespace failed",
                TRAILING_DATA_MAIN,
            ),
        )
        for label, description, fixture in baselines:
            result = _compile_and_run(stubs + parser + fixture, board, label)
            _require_baseline(board, label, description, result)
            if label == "depth-baseline":
                print(
                    f"{board}: POLL_JSON_COMPOSITE_DEPTH_PASS "
                    "max=16 rejected=17 arrays=1 objects=1"
                )
            elif label in ("duplicate-root-baseline", "trailing-data-baseline", "utf8-baseline"):
                print(result.stdout.strip())

        verify_root_envelope_contracts(
            board, source, parser, stubs, extract, _expect_mutation_rejected
        )
        verify_composite_contracts(
            board, source, parser, stubs, extract, _expect_mutation_rejected
        )
        verify_primitive_contracts(
            board, source, parser, stubs, extract, _expect_mutation_rejected
        )
        print(
            f"{board}: POLL_JSON_COMPOSITE_GRAMMAR_PASS "
            "valid=6/6 invalid=12/12"
        )
