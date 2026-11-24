"""Source-exact regression for primitive JSON values at array boundaries.

The production parser must stop a primitive at ']' as well as ',' and '}'.
This lab compiles the parser extracted from both board sketches and injects a
mutation that removes the array terminator again.
"""
import subprocess
import tempfile
from pathlib import Path

PARSER_FUNCTIONS = (
    "pollJsonSpace",
    "pollJsonHex",
    "pollJsonSkipString",
    "pollJsonSkipComposite",
    "pollJsonSkipPrimitive",
    "pollJsonSkipValue",
    "pollJsonTopLevelTrue",
)

ARRAY_MAIN = r"""
int main() {
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"items\":[1,2,3]}"), "ok")) return 61;
  if (!pollJsonTopLevelTrue(
          String("{\"items\":[1,2,3],\"ok\":true}"), "ok")) return 62;
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[false,null,-1.25e+2,{\"nested\":[true,0]}]}"),
          "ok")) return 63;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[1,2,3}"), "ok")) return 64;
  std::cout << "POLL_JSON_ARRAY_PRIMITIVE_PASS 3/3; UNMATCHED_ARRAY_REJECTED 1/1\n";
  return 0;
}
"""


def _compile_and_run(code, board, label):
    with tempfile.TemporaryDirectory(prefix="phx-json-array-") as folder:
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


def verify(boards, extract, stubs):
    for board, path in boards.items():
        source = path.read_text(encoding="utf-8")
        parser = "\n\n".join(
            extract(source, name) for name in PARSER_FUNCTIONS
        )
        baseline = _compile_and_run(stubs + parser + ARRAY_MAIN, board, "baseline")
        if baseline.returncode:
            raise AssertionError(
                f"{board}: valid primitive array was rejected "
                f"(exit={baseline.returncode}; stdout={baseline.stdout}; "
                f"stderr={baseline.stderr})"
            )

        primitive = extract(source, "pollJsonSkipPrimitive")
        delimiter = " && r[p]!=']'"
        if primitive.count(delimiter) != 1:
            raise AssertionError(
                f"{board}: expected exactly one explicit array-close delimiter"
            )
        mutated_primitive = primitive.replace(delimiter, "", 1)
        mutated_parser = parser.replace(primitive, mutated_primitive, 1)
        if mutated_parser == parser:
            raise AssertionError(f"{board}: array-terminator mutation was not applied")
        mutated = _compile_and_run(
            stubs + mutated_parser + ARRAY_MAIN, board, "missing_array_terminator"
        )
        if mutated.returncode != 61:
            raise AssertionError(
                f"{board}: missing-array-terminator mutation survived "
                f"(expected exit 61, got {mutated.returncode}; "
                f"stdout={mutated.stdout}; stderr={mutated.stderr})"
            )
        print(
            f"{board}: POLL_JSON_ARRAY_PRIMITIVE_PASS; "
            "MUTATION_REJECTED missing-array-terminator expected_exit=61"
        )
