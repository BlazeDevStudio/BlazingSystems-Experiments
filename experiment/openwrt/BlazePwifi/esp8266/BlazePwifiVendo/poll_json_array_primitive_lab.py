"""Source-exact strict JSON composite grammar regression for both coin controllers.

The firmware parser must validate nested array/object separators, primitive
terminators, and closing delimiters before a root-level status can be read.
The host lab is simulated control-flow evidence, not controller authentication.
"""
import subprocess
import tempfile
from pathlib import Path

from poll_json_array_primitive_lab_fixtures import (
    COMPOSITE_MAIN,
    DEPTH_MAIN,
    DUPLICATE_ROOT_MAIN,
    PARSER_FUNCTIONS,
    PRIMITIVE_MAIN,
    PROTOTYPES,
    TRAILING_DATA_MAIN,
)



def _compile_and_run(code, board, label):
    with tempfile.TemporaryDirectory(prefix="phx-json-composite-") as folder:
        cpp = Path(folder) / f"{label}.cpp"
        binary = Path(folder) / label
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            raise RuntimeError(
                f"{board}: {label} compile failed:\n{built.stderr[-3000:]}"
            )
        return subprocess.run(
            [str(binary)], capture_output=True, text=True, timeout=10
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


def verify(boards, extract, stubs):
    for board, path in boards.items():
        source = path.read_text(encoding="utf-8")
        parser = PROTOTYPES + "\n\n".join(
            extract(source, name) for name in PARSER_FUNCTIONS
        )
        baseline = _compile_and_run(stubs + parser + COMPOSITE_MAIN, board, "baseline")
        if baseline.returncode:
            raise AssertionError(
                f"{board}: strict JSON composite cases failed "
                f"(exit={baseline.returncode}; stdout={baseline.stdout}; "
                f"stderr={baseline.stderr})"
            )


        primitive_baseline = _compile_and_run(
            stubs + parser + PRIMITIVE_MAIN, board, "primitive-baseline"
        )
        if primitive_baseline.returncode:
            raise AssertionError(
                f"{board}: strict JSON primitive cases failed "
                f"(exit={primitive_baseline.returncode}; "
                f"stdout={primitive_baseline.stdout}; "
                f"stderr={primitive_baseline.stderr})"
            )

        depth_baseline = _compile_and_run(
            stubs + parser + DEPTH_MAIN, board, "depth-baseline"
        )
        if depth_baseline.returncode:
            raise AssertionError(
                f"{board}: composite nesting-depth boundary failed "
                f"(exit={depth_baseline.returncode}; "
                f"stdout={depth_baseline.stdout}; "
                f"stderr={depth_baseline.stderr})"
            )
        print(
            f"{board}: POLL_JSON_COMPOSITE_DEPTH_PASS "
            "max=16 rejected=17 arrays=1 objects=1"
        )
        duplicate_result = _compile_and_run(
            stubs + parser + DUPLICATE_ROOT_MAIN, board, "duplicate-root-baseline"
        )
        if duplicate_result.returncode:
            raise AssertionError(
                f"{board}: duplicate root status keys were not denied "
                f"(exit={duplicate_result.returncode}; "
                f"stdout={duplicate_result.stdout}; stderr={duplicate_result.stderr})"
            )
        print(duplicate_result.stdout.strip())

        trailing_result = _compile_and_run(
            stubs + parser + TRAILING_DATA_MAIN, board, "trailing-data-baseline"
        )
        if trailing_result.returncode:
            raise AssertionError(
                f"{board}: trailing JSON data was not denied or whitespace failed "
                f"(exit={trailing_result.returncode}; "
                f"stdout={trailing_result.stdout}; stderr={trailing_result.stderr})"
            )
        print(trailing_result.stdout.strip())

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
        _expect_mutation_rejected(
            stubs + parser.replace(top_level, duplicate_mutant, 1)
            + DUPLICATE_ROOT_MAIN,
            board, "allow-duplicate-root-status", 91
        )

        trailing_mutant = top_level.replace(
            final_guard, "return found==1 && accepted;", 1
        )
        _expect_mutation_rejected(
            stubs + parser.replace(top_level, trailing_mutant, 1)
            + TRAILING_DATA_MAIN,
            board, "accept-trailing-json-data", 93
        )
        print(
            f"{board}: POLL_JSON_ROOT_ENVELOPE_PASS "
            "duplicate=2/2 trailing=3/3; mutations=2/2 rejected"
        )

        primitive = extract(source, "pollJsonSkipPrimitive")
        delimiter = " && r[p]!=']'"
        if primitive.count(delimiter) != 1:
            raise AssertionError(
                f"{board}: expected exactly one array primitive terminator"
            )
        _expect_mutation_rejected(
            stubs + parser.replace(
                primitive, primitive.replace(delimiter, "", 1), 1
            ) + COMPOSITE_MAIN,
            board, "missing-array-primitive-terminator", 61
        )

        composite = extract(source, "pollJsonSkipCompositeDepth")
        depth_guard = " || depth>16"
        if composite.count(depth_guard) != 1:
            raise AssertionError(
                f"{board}: expected exactly one composite nesting-depth guard"
            )
        depth_mutant = composite.replace(depth_guard, "", 1)
        _expect_mutation_rejected(
            stubs + parser.replace(composite, depth_mutant, 1) + DEPTH_MAIN,
            board, "remove-composite-depth-cap", 122
        )
        off_by_one_mutant = composite.replace("depth>16", "depth>17", 1)
        if off_by_one_mutant == composite:
            raise AssertionError(f"{board}: depth-bound mutation anchor missing")
        _expect_mutation_rejected(
            stubs + parser.replace(composite, off_by_one_mutant, 1) + DEPTH_MAIN,
            board, "allow-depth-17", 122
        )

        separator = "if(p>=n || r[p++]!=',') return false;"
        if composite.count(separator) != 2:
            raise AssertionError(
                f"{board}: expected one array and one object member separator"
            )
        array_mutant = composite.replace(separator, "", 1)
        _expect_mutation_rejected(
            stubs + parser.replace(composite, array_mutant, 1) + COMPOSITE_MAIN,
            board, "missing-array-separator", 61
        )

        object_prefix, object_suffix = composite.rsplit(separator, 1)
        object_mutant = object_prefix + object_suffix
        _expect_mutation_rejected(
            stubs + parser.replace(composite, object_mutant, 1) + COMPOSITE_MAIN,
            board, "missing-object-separator", 71
        )

        string_parser = extract(source, "pollJsonSkipString")
        control_guard = "if(c<0x20) return false;"
        if string_parser.count(control_guard) != 1:
            raise AssertionError(f"{board}: expected one raw-control guard")
        _expect_mutation_rejected(
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
        _expect_mutation_rejected(
            stubs + parser.replace(string_parser, mutated_string_parser, 1)
            + COMPOSITE_MAIN,
            board, "accept-unsupported-string-escape", 73
        )

        unicode_guard = "!pollJsonHex(r[p])"
        if string_parser.count(unicode_guard) != 1:
            raise AssertionError(f"{board}: expected one Unicode hex guard")
        _expect_mutation_rejected(
            stubs + parser.replace(
                string_parser,
                string_parser.replace(unicode_guard, "false", 1),
                1
            ) + COMPOSITE_MAIN,
            board, "accept-nonhex-unicode-escape", 75
        )


        leading_zero_guard = "if(r[q]=='0'){\n    ++q;"
        if primitive.count(leading_zero_guard) != 1:
            raise AssertionError(f"{board}: expected one leading-zero guard")
        leading_zero_mutant = primitive.replace(
            leading_zero_guard,
            "if(r[q]=='0'){\n    ++q;\n    while(q<end && r[q]>='0' && r[q]<='9') ++q;",
            1
        )
        _expect_mutation_rejected(
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
        _expect_mutation_rejected(
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
        _expect_mutation_rejected(
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
        _expect_mutation_rejected(
            stubs + parser.replace(primitive, true_literal_mutant, 1)
            + PRIMITIVE_MAIN,
            board, "accept-truncated-true-literal", 113
        )
        print(
            f"{board}: POLL_JSON_PRIMITIVE_GRAMMAR_PASS "
            "valid=9/9 invalid=16/16; mutations=4/4 rejected"
        )

        print(f"{board}: POLL_JSON_COMPOSITE_GRAMMAR_PASS valid=6/6 invalid=12/12")
