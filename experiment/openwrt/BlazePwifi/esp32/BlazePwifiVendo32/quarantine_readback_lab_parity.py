"""Source-exact ESP32/ESP8266 safety-helper parity checks.

This module owns source extraction, board parity and deny-only mutation probes.
The companion runner owns C++ harness compilation and scenario execution.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ESP8266_LAB = ROOT / "esp8266/BlazePwifiVendo"
sys.path.insert(0, str(ESP8266_LAB))
from firmware_lab_source import extract_function

BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)


def extract(src: str, signature: str) -> str:
    # The caller stores a C++ signature prefix; delegate lexical parsing to the
    # shared helper so braces in comments and literals cannot truncate a body.
    name = signature.split("(", 1)[0].split()[-1]
    return extract_function(src, name)


def verify_lexical_extractor():
    fixture = (
        'String lexicalProbe(){\\n'
        '  const char *ordinary = "}";\\n'
        '  const char *raw = R"tag({ })tag";\\n'
        '  /* } */\\n'
        '  return ordinary;\\n'
        '}'
    )
    if extract(fixture, "String lexicalProbe(") != fixture:
        raise SystemExit(
            "PHX-HARDWARE: source extractor truncated a C++ literal/comment fixture"
        )


verify_lexical_extractor()


# These helpers define the pending-event/quarantine safety boundary. They are
# intentionally byte-identical across ESP32 and ESP8266 so board drift cannot
# silently weaken one controller while the other remains protected.
PARITY_SIGNATURES = (
    # Pending-event and quarantine persistence must remain byte-identical.
    "bool readPendingFile(",
    "bool markPendingPostAttempt(",
    "bool pendingAttemptMarkerMatches()",
    "bool clearPending(",
    "const char* quarantineLogFieldEscapeAt(",
    "String quarantineLogField(",
    "bool quarantineLogTokenValid(",
    "bool quarantineLogRecordValid(",
    "uint32_t quarantineLogCrc32Update(",
    "bool inspectQuarantineLog(",
    "bool appendQuarantineRecord(",
    "bool quarantinePending(",
    # The two board consumers must also share one poll/coin response boundary.
    "bool pollJsonSpace(",
    "bool pollJsonHex(",
    "bool pollJsonSkipString(",
    "bool pollJsonSkipComposite(",
    "bool pollJsonSkipPrimitive(",
    "bool pollJsonSkipValue(",
    "bool pollJsonTopLevelTrue(",
    "bool validSha256Hex(",
    "bool coinPostDispositionVerified(",
    "void handleCoinPostResponse(",
    "bool acceptPollResponse(",
)

POLARITY_SIGNATURE = "bool canAttemptCoinPost(){"


def board_safety_helpers():
    result = {}
    for board, ino in BOARDS:
        source = ino.read_text(encoding="utf-8")
        result[board] = {
            signature: extract(source, signature)
            for signature in PARITY_SIGNATURES
        }
        # This gate is intentionally board-specific until ESP32 has its own
        # reviewed local polarity profile. Compare its shared admission body
        # after validating the ESP8266-only interlock separately.
        result[board][POLARITY_SIGNATURE] = extract(source, POLARITY_SIGNATURE)
    return result


def board_parity_mismatches(helpers):
    return [
        signature for signature in PARITY_SIGNATURES
        if helpers["ESP32"][signature] != helpers["ESP8266"][signature]
    ]


def board_polarity_guard_problem(helpers):
    esp8266 = helpers["ESP8266"][POLARITY_SIGNATURE]
    esp32 = helpers["ESP32"][POLARITY_SIGNATURE]
    if "outputPolarityKnown && pinConfigSafe && fsReady" not in esp8266:
        return "ESP8266 local polarity/GPIO admission guard is missing"
    if "outputPolarityKnown && pinConfigSafe && fsReady" not in esp32:
        return "ESP32 local polarity/GPIO admission guard is missing"
    normalized_esp8266 = " ".join(esp8266.split())
    normalized_esp32 = " ".join(esp32.split())
    if normalized_esp8266 != normalized_esp32:
        return "coin POST gate differs between ESP32 and ESP8266 after local polarity guards"
    return None


def verify_board_safety_parity():
    helpers = board_safety_helpers()
    mismatches = board_parity_mismatches(helpers)
    if mismatches:
        raise SystemExit(
            "PHX-HARDWARE: ESP shared safety-helper drift: " + ", ".join(mismatches)
        )
    polarity_problem = board_polarity_guard_problem(helpers)
    if polarity_problem:
        raise SystemExit("PHX-HARDWARE: " + polarity_problem)

    # Failure injection: a fail-open append result on one board must be
    # detected before that board can diverge from the reviewed peer.
    mutated = {board: dict(functions) for board, functions in helpers.items()}
    signature = "bool appendQuarantineRecord("
    original = mutated["ESP8266"][signature]
    if "return verified;" not in original:
        raise SystemExit("PHX-HARDWARE: parity mutation anchor missing")
    mutated["ESP8266"][signature] = original.replace(
        "return verified;", "return true;", 1
    )
    if not board_parity_mismatches(mutated):
        raise SystemExit("PHX-HARDWARE: fail-open board-drift mutation was not detected")

    # A one-board fail-open coin disposition must be rejected before drift ships.
    disposition_signature = "bool coinPostDispositionVerified("
    disposition = mutated["ESP8266"][disposition_signature]
    if disposition.count("return false;") != 1:
        raise SystemExit("PHX-HARDWARE: coin-disposition fail-open mutation anchor is not unique")
    mutated_disposition = {board: dict(functions) for board, functions in helpers.items()}
    mutated_disposition["ESP8266"][disposition_signature] = disposition.replace(
        "return false;", "return true;", 1
    )
    if not board_parity_mismatches(mutated_disposition):
        raise SystemExit("PHX-HARDWARE: coin-disposition fail-open mutation was not detected")

    # A one-board permissive root-status parser must also be rejected.
    parser_signature = "bool pollJsonTopLevelTrue("
    parser = helpers["ESP8266"][parser_signature]
    parser_anchor = "return p==n && found==1 && accepted;"
    if parser.count(parser_anchor) != 1:
        raise SystemExit("PHX-HARDWARE: poll-parser permissive mutation anchor is not unique")
    mutated_parser = {board: dict(functions) for board, functions in helpers.items()}
    mutated_parser["ESP8266"][parser_signature] = parser.replace(
        parser_anchor, "return true;", 1
    )
    if not board_parity_mismatches(mutated_parser):
        raise SystemExit("PHX-HARDWARE: permissive poll-parser mutation was not detected")

    # A one-board quarantine escape mapping drift must be rejected before parity ships.
    field_escape_signature = "const char* quarantineLogFieldEscapeAt("
    field_escape = helpers["ESP8266"][field_escape_signature]
    escape_anchor = 'return "\\\\x20";'
    if field_escape.count(escape_anchor) != 1:
        raise SystemExit("PHX-HARDWARE: quarantine escape mapping mutation anchor is not unique")
    mutated_field_escape = {board: dict(functions) for board, functions in helpers.items()}
    mutated_field_escape["ESP8266"][field_escape_signature] = field_escape.replace(
        escape_anchor, 'return "\\\\x21";', 1
    )
    if not board_parity_mismatches(mutated_field_escape):
        raise SystemExit("PHX-HARDWARE: quarantine escape mapping drift was not detected")

    # acceptPollResponse is deliberately deny-only until CORE/QA approve a contract.
    admission_signature = "bool acceptPollResponse("
    admission = helpers["ESP8266"][admission_signature]
    if admission.count("return false;") != 1:
        raise SystemExit("PHX-HARDWARE: poll-admission mutation anchor is not unique")
    mutated_admission = {board: dict(functions) for board, functions in helpers.items()}
    mutated_admission["ESP8266"][admission_signature] = admission.replace(
        "return false;", "return true;", 1
    )
    if not board_parity_mismatches(mutated_admission):
        raise SystemExit("PHX-HARDWARE: positive poll-admission mutation was not detected")

    # Both boards must retain the local polarity admission gate.
    for board in ("ESP8266", "ESP32"):
        polarity_mutated = {name: dict(functions) for name, functions in helpers.items()}
        polarity_mutated[board][POLARITY_SIGNATURE] = (
            polarity_mutated[board][POLARITY_SIGNATURE].replace(
                "outputPolarityKnown && ", "", 1
            )
        )
        if board_polarity_guard_problem(polarity_mutated) is None:
            raise SystemExit("PHX-HARDWARE: " + board + " output-polarity gate removal mutation was not detected")

    print("BOARD_SHARED_SAFETY_PARITY_PASS 23/23 functions byte-identical")
    print("ESP32_AND_ESP8266_LOCAL_POLARITY_GATES_PASS")
    print("BOARD_PARITY_MUTATION_REJECTED fail-open append verification bypass")
    print("BOARD_PARITY_MUTATION_REJECTED fail-open coin disposition")
    print("BOARD_PARITY_MUTATION_REJECTED permissive poll status parser")
    print("BOARD_PARITY_MUTATION_REJECTED positive poll response admission")
    print("BOARD_PARITY_MUTATION_REJECTED quarantine escape-atom mapping drift")
    print("ESP32_AND_ESP8266_POLARITY_MUTATIONS_REJECTED removed local gate")


__all__ = ["BOARDS", "extract", "verify_board_safety_parity"]
