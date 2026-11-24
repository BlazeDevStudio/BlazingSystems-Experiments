#!/usr/bin/env python3
"""Exact-source dual-store poll-fault persistence regression for ESP32 and ESP8266.

This host lab models the NVS and EEPROM APIs. It does not emulate flash physics,
power-loss timing, wear, or an independent physical witness.
"""
from pathlib import Path
import subprocess
import tempfile
import sys

from firmware_lab_source import extract_block, extract_function, extract_functions, find_repo_root, mask_non_code
from poll_fault_dual_store_lab_fixtures import constants, harness

ROOT = find_repo_root(Path(__file__))
ESP32 = ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
ESP8266 = ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"

if "--root-probe" in sys.argv:
    if ESP32.is_file() and ESP8266.is_file():
        print("LAB_ROOT_EXTERNAL_CWD_PASS")
        raise SystemExit(0)
    print(f"LAB_ROOT_EXTERNAL_CWD_FAIL root={ROOT}", file=sys.stderr)
    raise SystemExit(1)


def test_external_cwd_invocation():
    script = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix="phx-lab-root-cwd-") as outside_repo:
        result = subprocess.run(
            [sys.executable, str(script), "--root-probe"],
            cwd=outside_repo,
            text=True,
            capture_output=True,
        )
    if result.returncode != 0 or "LAB_ROOT_EXTERNAL_CWD_PASS" not in result.stdout:
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        raise AssertionError("dual-store lab must locate both board sketches independently of the caller's working directory")
    print("POLL_FAULT_LAB_EXTERNAL_CWD_PASS")


def test_repo_root_requires_both_board_sentinels():
    esp32_rel = Path("experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino")
    esp8266_rel = Path("experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino")
    probe_rel = Path("tests/root_probe.py")

    with tempfile.TemporaryDirectory(prefix="phx-root-sentinel-") as temp:
        root = Path(temp)
        probe = root / probe_rel
        probe.parent.mkdir(parents=True, exist_ok=True)
        (root / esp32_rel).parent.mkdir(parents=True, exist_ok=True)
        (root / esp32_rel).write_text("ESP32 sentinel", encoding="utf-8")

        try:
            find_repo_root(probe)
        except RuntimeError:
            pass
        else:
            raise AssertionError("a checkout missing the ESP8266 sketch must not be accepted as the repository root")

        (root / esp8266_rel).parent.mkdir(parents=True, exist_ok=True)
        (root / esp8266_rel).write_text("ESP8266 sentinel", encoding="utf-8")
        if find_repo_root(probe) != root.resolve():
            raise AssertionError("repository root discovery must walk upward from a nested file path")

    helper_path = Path(__file__).with_name("firmware_lab_source.py")
    helper_source = helper_path.read_text(encoding="utf-8")
    guard = "if all((candidate / relative).is_file() for relative in required_sketches):"
    if helper_source.count(guard) != 1:
        raise AssertionError("both-board root-sentinel guard mutation anchor must occur exactly once")
    single_board_mutant = helper_source.replace(
        guard,
        "if (candidate / required_sketches[0]).is_file():",
        1,
    )

    with tempfile.TemporaryDirectory(prefix="phx-root-sentinel-mutation-") as temp:
        mutant_dir = Path(temp)
        (mutant_dir / "firmware_lab_source.py").write_text(single_board_mutant, encoding="utf-8")
        probe_script = mutant_dir / "probe.py"
        probe_script.write_text(
            """from pathlib import Path
import sys
from firmware_lab_source import find_repo_root
try:
    find_repo_root(Path(sys.argv[1]))
except RuntimeError:
    print("ROOT_REJECTED")
    raise SystemExit(0)
print("ROOT_ACCEPTED")
raise SystemExit(1)
""",
            encoding="utf-8",
        )
        partial_root = mutant_dir / "partial-checkout"
        (partial_root / esp32_rel).parent.mkdir(parents=True, exist_ok=True)
        (partial_root / esp32_rel).write_text("ESP32 sentinel", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(probe_script), str(partial_root / probe_rel)],
            cwd=mutant_dir,
            text=True,
            capture_output=True,
        )
        if result.returncode != 1 or result.stdout.strip() != "ROOT_ACCEPTED":
            print(result.stdout, end="")
            print(result.stderr, file=sys.stderr, end="")
            raise AssertionError("single-board-only root discovery mutation was not exercised")
    print("MUTATION_REJECTED ROOT_DISCOVERY_SINGLE_BOARD_SENTINEL")


def test_unknown_board_identifier_fails_closed():
    source = ESP8266.read_text(encoding="utf-8")
    try:
        harness("ESP8266-typo", source)
    except ValueError as exc:
        if "ESP8266-typo" not in str(exc):
            raise AssertionError("unknown-board error should identify the rejected label") from exc
    else:
        raise AssertionError(
            "unknown board label silently selected the ESP8266 persistence backend"
        )
    print("POLL_FAULT_UNKNOWN_BOARD_REJECTED")


def test_extractors():
    sample = r'''
/*
bool selected(int value) { return false; }
struct Record { int fake; };
*/
const char *rawMarker = R"fake(
bool selected(int value) { return false; }
struct Record { int fake; };
)fake";
// bool selected(int value) { this is only a line comment }
bool selected(int value);
void caller() { selected(1); }
struct Record {
  const char *text = "}";
  char brace = '{';
  // } { inside a line comment
  /* { } inside a block comment */
  const char *raw = R"tag({ raw } )tag";
  int nested[2] = {1, 2};
};
bool selected(int value) {
  const char *text = "}";
  if (value) { return true; }
  return false;
}
'''
    masked = mask_non_code(sample)
    if len(masked) != len(sample) or masked.count("\n") != sample.count("\n"):
        raise AssertionError("source mask must preserve offsets and line positions")
    if "bool selected(int value) { return false; }" in masked:
        raise AssertionError("comment/raw-string decoy was not masked")

    record = extract_block(sample, "struct Record")
    function = extract_function(sample, "selected")
    functions = extract_functions(sample, "selected")
    if "int nested[2] = {1, 2};" not in record:
        raise AssertionError("struct extractor stopped inside a literal/comment")
    if not function.startswith("bool selected") or "if (value) { return true; }" not in function:
        raise AssertionError("function extractor did not select the definition")
    if len(functions) != 1 or functions[0][1] != function:
        raise AssertionError("function list must contain the single real definition")

    # C++ translation phase 2 removes backslash-newline before // comment
    # recognition. A continued comment must not expose a fake function body.
    continued_comment = (
        "// continued comment " + "\\" + "\n"
        + "bool selected(int value) { return false; }\n"
    )
    continued_masked = mask_non_code(continued_comment)
    if len(continued_masked) != len(continued_comment):
        raise AssertionError("continued-comment mask must preserve source offsets")
    if extract_functions(continued_comment, "selected"):
        raise AssertionError("backslash-newline // comment exposed a fake function")

    continued_crlf = (
        "// continued CRLF comment " + "\\" + "\r\n"
        + "bool selected(int value) { return false; }\r\n"
    )
    continued_crlf_masked = mask_non_code(continued_crlf)
    if continued_crlf_masked.count("\r\n") != continued_crlf.count("\r\n"):
        raise AssertionError("continued CRLF comment must preserve newline positions")
    if extract_functions(continued_crlf, "selected"):
        raise AssertionError("backslash-CRLF // comment exposed a fake function")

    # C++ translation phase 2 runs before comment-token recognition. A splice
    # can form the delimiter itself, not only continue an already-open comment.
    spliced_line_comment = (
        "/" + "\\" + "\n" + "/" + "\\" + "\r\n"
        + "bool selected(int value) { return false; }\r\n"
    )
    line_masked = mask_non_code(spliced_line_comment)
    if len(line_masked) != len(spliced_line_comment):
        raise AssertionError("spliced // opener must preserve source offsets")
    if line_masked.count("\r\n") != spliced_line_comment.count("\r\n"):
        raise AssertionError("spliced // opener must preserve CRLF positions")
    if extract_functions(spliced_line_comment, "selected"):
        raise AssertionError("line-spliced // opener exposed a fake function")

    spliced_block_comment = (
        "/" + "\\" + "\n" + "*\n"
        + "bool selected(int value) { return false; }\n*/\n"
    )
    block_masked = mask_non_code(spliced_block_comment)
    if len(block_masked) != len(spliced_block_comment):
        raise AssertionError("spliced /* opener must preserve source offsets")
    if extract_functions(spliced_block_comment, "selected"):
        raise AssertionError("line-spliced /* opener exposed a fake function")

    spliced_block_terminator = (
        "/* hidden " + "*" + "\\" + "\r\n" + "/\r\n"
        + "bool selected(int value) { return true; }\r\n"
    )
    terminator_masked = mask_non_code(spliced_block_terminator)
    if len(terminator_masked) != len(spliced_block_terminator):
        raise AssertionError("spliced */ terminator must preserve source offsets")
    if terminator_masked.count("\r\n") != spliced_block_terminator.count("\r\n"):
        raise AssertionError("spliced */ terminator must preserve CRLF positions")
    terminated_functions = extract_functions(spliced_block_terminator, "selected")
    if len(terminated_functions) != 1 or "return true;" not in terminated_functions[0][1]:
        raise AssertionError("line-spliced */ terminator did not expose following code")

    if not function.endswith("}"):
        raise AssertionError("function extractor returned an incomplete body")

    attributed = "void ICACHE_RAM_ATTR edgeHandler() { if (true) { ++count; } }"
    if "edgeHandler" not in extract_function(attributed, "edgeHandler"):
        raise AssertionError("attribute-qualified function definition was not found")

    if extract_function("bool declared(int value);", "declared", required=False):
        raise AssertionError("declaration must not be returned as a definition")

    try:
        extract_block('struct Broken { const char *value = "}" ;', "struct Broken")
    except RuntimeError:
        pass
    else:
        raise AssertionError("unterminated block must fail closed")

    print("POLL_FAULT_EXTRACTOR_SELFTEST=PASS")



def test_constants_extract_only_active_declarations():
    sample = r"""
/*
static const uint32_t POLL_FAULT_RECORD_MAGIC = 0xBAD;
static const uint32_t POLL_FAULT_EEPROM_OFFSET = 1;
*/
const char *raw = R"phx(
static const uint32_t POLL_FAULT_RECORD_VERSION = 0xBAD;
static const uint32_t POLL_FAULT_EEPROM_BYTES = 2;
)phx";
#if 0
static const uint32_t POLL_FAULT_RECORD_MAGIC = 0xBAD;
#if 1
static const uint32_t POLL_FAULT_RECORD_VERSION = 0xBAD;
#endif
#elif 0
static const uint32_t POLL_FAULT_EEPROM_OFFSET = 1;
#else
static const uint32_t UNUSED_ACTIVE_BRANCH = 9;
#endif
#if 1
static const uint32_t UNUSED_TRUE_BRANCH = 10;
#else
static const uint32_t POLL_FAULT_EEPROM_BYTES = 2;
#endif
static const uint32_t POLL_FAULT_RECORD_MAGIC = 0x1234;
static const uint32_t POLL_FAULT_RECORD_VERSION = 1;
static const uint32_t NOT_POLL_FAULT_EEPROM_OFFSET_ALIAS = 9;
static const uint32_t POLL_FAULT_EEPROM_OFFSET = 64;
static const uint32_t POLL_FAULT_EEPROM_BYTES = 32;
"""
    selected = constants(sample, (
        "POLL_FAULT_RECORD_MAGIC",
        "POLL_FAULT_RECORD_VERSION",
        "POLL_FAULT_EEPROM_OFFSET",
        "POLL_FAULT_EEPROM_BYTES",
    ))
    expected = [
        "static const uint32_t POLL_FAULT_RECORD_MAGIC = 0x1234;",
        "static const uint32_t POLL_FAULT_RECORD_VERSION = 1;",
        "static const uint32_t POLL_FAULT_EEPROM_OFFSET = 64;",
        "static const uint32_t POLL_FAULT_EEPROM_BYTES = 32;",
    ]
    if selected.splitlines() != expected:
        raise AssertionError(
            "constant extraction must ignore comment/raw-string decoys and "
            f"identifier substrings; got={selected.splitlines()!r}"
        )
    print("POLL_FAULT_CONSTANT_EXTRACTION_NON_CODE_DECOYS_REJECTED 4/4")
    print("POLL_FAULT_CONSTANT_EXTRACTION_PREPROCESSOR_INACTIVE_REJECTED 4/4")

    # C++ translation phase 2 splices backslash-newline before directive parsing.
    # A literal-zero #if whose expression continues on the next physical line
    # must not expose its inactive constant to the host harness.
    spliced_if_zero = (
        "#if " + "\\" + "\n"
        + "0\n"
        + "static const uint32_t POLL_FAULT_RECORD_MAGIC = 0xBAD;\n"
        + "#else\n"
        + "static const uint32_t POLL_FAULT_RECORD_MAGIC = 0x1234;\n"
        + "#endif\n"
    )
    selected_spliced_if = constants(spliced_if_zero, ("POLL_FAULT_RECORD_MAGIC",))
    expected_spliced_if = ["static const uint32_t POLL_FAULT_RECORD_MAGIC = 0x1234;"]
    if selected_spliced_if.splitlines() != expected_spliced_if:
        raise AssertionError(
            "backslash-newline #if expression must keep the literal-zero branch inactive; "
            f"got={selected_spliced_if.splitlines()!r}"
        )
    print("POLL_FAULT_CONSTANT_EXTRACTION_PHASE2_IF_SPLICE_REJECTED 1/1")

    # The directive keyword itself may be formed across a splice. Exercise
    # CRLF as well as an #elif-zero branch after an already-taken #if branch.
    spliced_elif_zero = (
        "#if 1\r\n"
        "static const uint32_t POLL_FAULT_RECORD_VERSION = 1;\r\n"
        "#el" + "\\" + "\r\n" + "if 0\r\n"
        "static const uint32_t POLL_FAULT_RECORD_VERSION = 0xBAD;\r\n"
        "#else\r\n"
        "static const uint32_t POLL_FAULT_RECORD_VERSION = 2;\r\n"
        "#endif\r\n"
    )
    selected_spliced_elif = constants(spliced_elif_zero, ("POLL_FAULT_RECORD_VERSION",))
    expected_spliced_elif = ["static const uint32_t POLL_FAULT_RECORD_VERSION = 1;"]
    if selected_spliced_elif.splitlines() != expected_spliced_elif:
        raise AssertionError(
            "spliced #elif 0 must remain inactive after a taken #if 1; "
            f"got={selected_spliced_elif.splitlines()!r}"
        )
    print("POLL_FAULT_CONSTANT_EXTRACTION_PHASE2_ELIF_SPLICE_REJECTED 1/1")

def run(board: str, path: Path):
    source = path.read_text(encoding="utf-8")
    program = harness(board, source)
    with tempfile.TemporaryDirectory(prefix="phx-poll-fault-") as tmp:
        cpp = Path(tmp) / "lab.cpp"
        exe = Path(tmp) / "lab"
        cpp.write_text(program, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
        )
        try:
            result = subprocess.run([str(exe)], check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout or "", end="")
            print(exc.stderr or "", file=sys.stderr, end="")
            raise
        print(result.stdout, end="")
        required_markers = (
            f"POLL_FAULT_FIRST_LATCH_SNAPSHOT_STABLE_PASS board={board}",
        )
        if board == "ESP8266":
            required_markers += (
                "ESP8266_EEPROM_END_FAILURE_REBOOT_DENY_PASS",
                "ESP8266_EEPROM_REOPEN_FAILURE_REBOOT_DENY_PASS",
            )
        missing_markers = [marker for marker in required_markers if marker not in result.stdout]
            if missing_markers:
                raise AssertionError(
                    "POLL_FAULT_EEPROM_LIFECYCLE_FAILURE_INJECTION_MISSING "
                    f"board={board} markers={','.join(missing_markers)}"
                )

def run_esp32_missing_commit_mutation(path: Path):
    source = path.read_text(encoding="utf-8")
    needle = (
        "  if(nvs_commit(pollFaultNvsHandle)!=ESP_OK){\n"
        "    pollFaultBackupWriteFailed=true;\n"
        "    return false;\n"
        "  }\n"
    )
    if source.count(needle) != 1:
        raise AssertionError("ESP32 NVS commit call mutation anchor must occur exactly once")
    mutated_source = source.replace(
        needle,
        "  // MUTATION: deliberately omit nvs_commit; readback must not count as durable.\n",
        1,
    )
    program = harness("ESP32", mutated_source)
    with tempfile.TemporaryDirectory(prefix="phx-nvs-commit-omission-") as tmp:
        cpp = Path(tmp) / "lab.cpp"
        exe = Path(tmp) / "lab"
        cpp.write_text(program, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
        )
        result = subprocess.run([str(exe)], text=True, capture_output=True)
    expected = "POLL_FAULT_BACKUP_COMMIT_CALL_COUNT_FAIL board=ESP32 actual=0"
    if result.returncode != 61 or expected not in result.stderr:
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        raise AssertionError("omitted ESP32 nvs_commit was not rejected by the commit-count guard")
    print("MUTATION_REJECTED ESP32_NVS_COMMIT_OMITTED exit=61")


def run_esp32_precommit_persistence_mutation(path: Path):
    source = path.read_text(encoding="utf-8")
    program = harness("ESP32", source)
    needle = "NvsFlash::pending.assign(bytes,bytes+length);\n  return ESP_OK;"
    replacement = (
        "NvsFlash::pending.assign(bytes,bytes+length);\n"
        "  NvsFlash::durable.assign(bytes,bytes+length);\n"
        "  return ESP_OK;"
    )
    if program.count(needle) != 1:
        raise AssertionError("ESP32 NVS pre-commit mutation anchor must occur exactly once")
    mutated = program.replace(needle, replacement, 1)
    with tempfile.TemporaryDirectory(prefix="phx-nvs-precommit-mutation-") as tmp:
        cpp = Path(tmp) / "lab.cpp"
        exe = Path(tmp) / "lab"
        cpp.write_text(mutated, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
        )
        result = subprocess.run([str(exe)], text=True, capture_output=True)
    if result.returncode != 60 or "ESP32_NVS_SET_BLOB_DURABLE_BEFORE_COMMIT" not in result.stderr:
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        raise AssertionError("premature ESP32 NVS durability mutation was not rejected")
    print("MUTATION_REJECTED ESP32_NVS_SET_BLOB_PREMATURE_DURABILITY exit=60")




def run_first_fault_snapshot_overwrite_mutation(board: str, path: Path):
    """Prove the new first-latch regression rejects a writer that overwrites V1."""
    source = path.read_text(encoding="utf-8")
    if board == "ESP32":
        existing_guard = (
            "if(existing==ESP_OK) return true; // Any existing value, including malformed data, keeps the deny latch."
        )
        not_found_guard = "if(existing!=ESP_ERR_NVS_NOT_FOUND){"
        if source.count(existing_guard) != 1 or source.count(not_found_guard) != 1:
            raise AssertionError("ESP32 first-latch overwrite mutation anchors must be unique")
        mutated_source = source.replace(
            existing_guard,
            "if(existing==ESP_OK){ /* mutation: permit overwriting first-fault snapshot */ }",
            1,
        ).replace(
            not_found_guard,
            "if(existing!=ESP_ERR_NVS_NOT_FOUND && existing!=ESP_OK){",
            1,
        )
    else:
        existing_guard = (
            "for(size_t i=0;i<sizeof(existing);++i) if(existingBytes[i]!=0xFF) return true;"
        )
        if source.count(existing_guard) != 1:
            raise AssertionError("ESP8266 first-latch overwrite mutation anchor must be unique")
        mutated_source = source.replace(
            existing_guard,
            "for(size_t i=0;i<sizeof(existing);++i) (void)existingBytes[i];",
            1,
        )
    program = harness(board, mutated_source)
    with tempfile.TemporaryDirectory(prefix="phx-first-latch-overwrite-mutation-") as tmp:
        cpp = Path(tmp) / "lab.cpp"
        exe = Path(tmp) / "lab"
        cpp.write_text(program, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
        )
        result = subprocess.run([str(exe)], text=True, capture_output=True)
    expected = f"POLL_FAULT_FIRST_LATCH_SNAPSHOT_CHANGED board={board}"
    if result.returncode != 74 or expected not in result.stderr:
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        raise AssertionError(f"{board}: first-latch overwrite mutation was not rejected")
    print(f"MUTATION_REJECTED {board}_FIRST_LATCH_SNAPSHOT_OVERWRITE exit=74")


if __name__ == "__main__":
    test_external_cwd_invocation()
    test_repo_root_requires_both_board_sentinels()
    test_extractors()
    test_constants_extract_only_active_declarations()
    test_unknown_board_identifier_fails_closed()
    print("POLL_FAULT_EXTRACTOR_SELFTEST=PASS", flush=True)
    run("ESP32", ESP32)
    run_first_fault_snapshot_overwrite_mutation("ESP32", ESP32)
    run_esp32_precommit_persistence_mutation(ESP32)
    run_esp32_missing_commit_mutation(ESP32)
    run("ESP8266", ESP8266)
    run_first_fault_snapshot_overwrite_mutation("ESP8266", ESP8266)
