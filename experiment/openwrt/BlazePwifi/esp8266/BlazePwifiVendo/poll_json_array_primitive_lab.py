"""Source-exact strict JSON composite grammar regression for both coin controllers.

The firmware parser must validate nested array/object separators, primitive
terminators, and closing delimiters before a root-level status can be read.
The host lab is simulated control-flow evidence, not controller authentication.
"""
import subprocess
import tempfile
from pathlib import Path

PARSER_FUNCTIONS = (
    "pollJsonSpace",
    "pollJsonHex",
    "pollJsonSkipString",
    "pollJsonSkipPrimitive",
    "pollJsonSkipValueDepth",
    "pollJsonSkipCompositeDepth",
    "pollJsonSkipComposite",
    "pollJsonSkipValue",
    "pollJsonTopLevelTrue",
)

PROTOTYPES = (
    "bool pollJsonSkipValueDepth(const String &r,int &p,uint8_t depth);\n"
    "bool pollJsonSkipCompositeDepth(const String &r,int &p,uint8_t depth);\n"
)

COMPOSITE_MAIN = r"""
int main() {
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"items\":[1,2,3]}"), "ok")) return 61;
  if (!pollJsonTopLevelTrue(
          String("{\"items\":[1,2,3],\"ok\":true}"), "ok")) return 62;
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[false,null,-1.25e+2,{\"nested\":[true,0]}]}"),
          "ok")) return 63;
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[]}"), "ok")) return 64;
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":{}}"), "ok")) return 65;

  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"quote\\\" slash\\\\ backspace\\b formfeed\\f newline\\n carriage\\r tab\\t unicode\\u0041\"}"),
          "ok")) return 72;

  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[1,]}"), "ok")) return 66;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[1 2]}"), "ok")) return 67;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":{\"a\":1,}}"), "ok")) return 68;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":{\"a\" 1}}"), "ok")) return 69;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[1,2,3}"), "ok")) return 70;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":{\"a\":1 \"b\":2}}"), "ok")) return 71;

  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"bad\\x41\"}"), "ok")) return 73;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"bad\\u12\"}"), "ok")) return 74;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"bad\\u12G4\"}"), "ok")) return 75;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"bad\nline\"}"), "ok")) return 76;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"unterminated}"), "ok")) return 77;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"dangling\\"), "ok")) return 78;

  std::cout << "POLL_JSON_COMPOSITE_GRAMMAR_PASS valid=6/6 invalid=12/12\n";
  return 0;
}
"""


PRIMITIVE_MAIN = r"""
int main() {
  if (!pollJsonTopLevelTrue(String("{\"meta\":0,\"ok\":true}"), "ok")) return 81;
  if (!pollJsonTopLevelTrue(String("{\"meta\":-0,\"ok\":true}"), "ok")) return 82;
  if (!pollJsonTopLevelTrue(String("{\"meta\":1,\"ok\":true}"), "ok")) return 83;
  if (!pollJsonTopLevelTrue(String("{\"meta\":-12,\"ok\":true}"), "ok")) return 84;
  if (!pollJsonTopLevelTrue(String("{\"meta\":0.25,\"ok\":true}"), "ok")) return 85;
  if (!pollJsonTopLevelTrue(String("{\"meta\":-0.25,\"ok\":true}"), "ok")) return 86;
  if (!pollJsonTopLevelTrue(String("{\"meta\":1e3,\"ok\":true}"), "ok")) return 87;
  if (!pollJsonTopLevelTrue(String("{\"meta\":1E+3,\"ok\":true}"), "ok")) return 88;
  if (!pollJsonTopLevelTrue(String("{\"meta\":1e-3,\"ok\":true}"), "ok")) return 89;

  if (pollJsonTopLevelTrue(String("{\"meta\":01,\"ok\":true}"), "ok")) return 101;
  if (pollJsonTopLevelTrue(String("{\"meta\":-01,\"ok\":true}"), "ok")) return 102;
  if (pollJsonTopLevelTrue(String("{\"meta\":+1,\"ok\":true}"), "ok")) return 103;
  if (pollJsonTopLevelTrue(String("{\"meta\":.1,\"ok\":true}"), "ok")) return 104;
  if (pollJsonTopLevelTrue(String("{\"meta\":1.,\"ok\":true}"), "ok")) return 105;
  if (pollJsonTopLevelTrue(String("{\"meta\":1e,\"ok\":true}"), "ok")) return 106;
  if (pollJsonTopLevelTrue(String("{\"meta\":1e+,\"ok\":true}"), "ok")) return 107;
  if (pollJsonTopLevelTrue(String("{\"meta\":1e-,\"ok\":true}"), "ok")) return 108;
  if (pollJsonTopLevelTrue(String("{\"meta\":--1,\"ok\":true}"), "ok")) return 109;
  if (pollJsonTopLevelTrue(String("{\"meta\":NaN,\"ok\":true}"), "ok")) return 110;
  if (pollJsonTopLevelTrue(String("{\"meta\":Infinity,\"ok\":true}"), "ok")) return 111;
  if (pollJsonTopLevelTrue(String("{\"meta\":TRUE,\"ok\":true}"), "ok")) return 112;
  if (pollJsonTopLevelTrue(String("{\"meta\":tru,\"ok\":true}"), "ok")) return 113;
  if (pollJsonTopLevelTrue(String("{\"meta\":nullx,\"ok\":true}"), "ok")) return 114;
  if (pollJsonTopLevelTrue(String("{\"meta\":1e++2,\"ok\":true}"), "ok")) return 115;
  if (pollJsonTopLevelTrue(String("{\"meta\":0x10,\"ok\":true}"), "ok")) return 116;

  std::cout << "POLL_JSON_PRIMITIVE_GRAMMAR_PASS valid=9/9 invalid=16/16\\n";
  return 0;
}
"""


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
            fraction_guard, "if(false) return false;", 1
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
            exponent_guard, "if(false) return false;", 1
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
