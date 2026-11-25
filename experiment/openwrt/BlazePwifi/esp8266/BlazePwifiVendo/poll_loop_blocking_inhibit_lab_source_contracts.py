"""Cross-board poll-safety source contracts for the blocking-poll lab.

Keep ESP8266/ESP32 helper parity and fixture-shape mutation checks outside
the loop orchestration runner. Dependencies are explicit parameters so the
contract module can be reviewed and reused without hidden runner globals.
"""
from firmware_lab_source import mask_active_cpp_code, mask_non_code
from poll_loop_blocking_inhibit_lab_edge_fixtures import POLL_SAFETY_PARITY

def poll_safety_helpers(boards, extract_function):
    helpers = {}
    for board, path in boards.items():
        source = path.read_text(encoding="utf-8")
        helpers[board] = {}
        for name in POLL_SAFETY_PARITY:
            body = extract_function(source, name)
            if not body:
                raise AssertionError(f"{board}: missing shared poll-safety helper {name}")
            # Ignore formatting-only changes; comments and executable tokens remain
            # part of the comparison so safety intent cannot drift silently.
            helpers[board][name] = " ".join(body.split())
    return helpers


def poll_safety_parity_mismatches(helpers):
    reference = helpers["ESP8266"]
    candidate = helpers["ESP32"]
    return [
        name for name in POLL_SAFETY_PARITY
        if not reference.get(name) or reference.get(name) != candidate.get(name)
    ]


def verify_poll_safety_parity_preserves_literal_whitespace():
    class _SourceText:
        def __init__(self, value):
            self.value = value

        def read_text(self, encoding="utf-8"):
            return self.value

    original = 'void applyOutputs(){ Serial.println("FAULT  LATCHED"); }'
    mutated = original.replace("FAULT  LATCHED", "FAULT LATCHED", 1)

    def extract(source, name):
        return source if name == "applyOutputs" else "void helper(){}"

    helpers = poll_safety_helpers(
        {
            "ESP8266": _SourceText(original),
            "ESP32": _SourceText(mutated),
        },
        extract,
    )
    mismatches = poll_safety_parity_mismatches(helpers)
    if "applyOutputs" not in mismatches:
        raise SystemExit(
            "POLL_SAFETY_LITERAL_WHITESPACE_MUTATION_SURVIVED: "
            "string-literal whitespace was normalized away"
        )
    print("POLL_SAFETY_LITERAL_WHITESPACE_MUTATION_REJECTED")


def verify_poll_safety_board_parity(boards, extract_function):
    verify_poll_safety_parity_preserves_literal_whitespace()
    helpers = poll_safety_helpers(boards, extract_function)
    mismatches = poll_safety_parity_mismatches(helpers)
    if mismatches:
        raise SystemExit(
            "POLL_SAFETY_BOARD_PARITY_FAIL: " + ", ".join(mismatches)
        )
    print(
        f"POLL_SAFETY_BOARD_PARITY_PASS {len(POLL_SAFETY_PARITY)}/"
        f"{len(POLL_SAFETY_PARITY)} normalized helpers"
    )

    # Failure-inject a fail-open ESP32 drift in the persistent-fault output
    # gate and prove the parity guard detects it before either board is built.
    mutated = {
        board: dict(board_helpers)
        for board, board_helpers in helpers.items()
    }
    marker = "!journalRecoveryRequired"
    apply_outputs = mutated["ESP32"]["applyOutputs"]
    if marker not in apply_outputs:
        raise AssertionError("ESP32 applyOutputs parity mutation anchor missing")
    mutated["ESP32"]["applyOutputs"] = apply_outputs.replace(
        marker, "journalRecoveryRequired", 1
    )
    if not poll_safety_parity_mismatches(mutated):
        raise SystemExit(
            "POLL_SAFETY_BOARD_PARITY_MUTATION_SURVIVED: "
            "ESP32 applyOutputs lost journal-fault deny guard"
        )
    print(
        "POLL_SAFETY_BOARD_PARITY_MUTATION_REJECTED "
        "ESP32_applyOutputs_journal_fault_guard"
    )

    # Each one-board fail-open mutation must be caught by the shared-helper
    # parity contract before the board-specific labs proceed.
    authority_mutations = (
        ("acceptPollResponse", "insertMode=false;", "insertMode=true;"),
        ("coinPostDispositionVerified", "return false;", "return true;"),
        ("canAttemptCoinPost", "outputPolarityKnown && ", ""),
        ("markPendingPostAttempt", 'if(LittleFS.exists("/pending.attempt")){', "if(false){"),
        ("pendingAttemptMarkerMatches", "return attempt.pulses==pendingPulses &&", "return true;"),
        ("clearPending", "if(!pendingAttemptMarkerMatches()){", "if(false){"),
        ("quarantinePending", "if(!appendQuarantineRecord(reason)){", "if(false){"),
        ("coinIngressConfigurationAllows", "return controllerEnabled && coinEnabled && relayEnabled;", "return true;"),
    )
    for name, anchor, replacement in authority_mutations:
        mutated = {
            board: dict(board_helpers)
            for board, board_helpers in helpers.items()
        }
        body = mutated["ESP32"][name]
        if anchor not in body:
            raise AssertionError(f"ESP32 {name} parity mutation anchor missing")
        mutated["ESP32"][name] = body.replace(anchor, replacement, 1)
        mismatches = poll_safety_parity_mismatches(mutated)
        if name not in mismatches:
            raise SystemExit(
                f"POLL_COIN_AUTHORITY_PARITY_MUTATION_SURVIVED: ESP32 {name}"
            )
        print(f"POLL_COIN_AUTHORITY_PARITY_MUTATION_REJECTED ESP32_{name}")


def normalized_cpp_fixture(source: str) -> str:
    """Normalize only C++ code; comments and literal contents are not callsites."""
    return " ".join(mask_active_cpp_code(source).split())


def verify_drain_abort_polarity_fixture_is_shared(main_fixture):
    helper = "int runDrainAbortWithoutIsr(bool activeLow, int holdFailureCode, int releaseFailureCode,"
    if normalized_cpp_fixture(main_fixture).count(helper) != 1:
        raise SystemExit(
            "POLL_DRAIN_ABORT_POLARITY_BUILDER_MISSING: expected one shared C++ helper"
        )
    normalized_main = normalized_cpp_fixture(main_fixture)
    calls = (
        "runDrainAbortWithoutIsr( true, 34, 35,",
        "runDrainAbortWithoutIsr( false, 36, 37,",
    )
    for call in calls:
        if normalized_main.count(call) != 1:
            raise SystemExit(
                "POLL_DRAIN_ABORT_POLARITY_BUILDER_CALL_MISSING: " + call
            )

    # Failure injection: a call-shaped comment/string must not stand in for
    # the active-low/active-high C++ callsites.
    decoy_cases = (
        (
            'const int activeLowDrainResult=runDrainAbortWithoutIsr(\n      true, 34, 35,',
            'const int activeLowDrainResult=0;\n  // runDrainAbortWithoutIsr( true, 34, 35,',
            calls[0],
            "comment",
        ),
        (
            'const int activeHighDrainResult=runDrainAbortWithoutIsr(\n      false, 36, 37,',
            'const int activeHighDrainResult=0;\n  std::cout << "runDrainAbortWithoutIsr( false, 36, 37,";',
            calls[1],
            "string",
        ),
    )
    for original, decoy, marker, label in decoy_cases:
        mutated = main_fixture.replace(original, decoy, 1)
        if mutated == main_fixture:
            raise AssertionError(f"could not construct {label} decoy mutation")
        if normalized_cpp_fixture(mutated).count(marker) != 0:
            raise SystemExit(
                f"POLL_DRAIN_ABORT_POLARITY_{label.upper()}_DECOY_SURVIVED"
            )
    # A call-shaped expression in a literal #if 0 branch must not satisfy the
    # active-low/active-high builder contract. This is a static matcher mutation;
    # it does not compile or execute the fixture fragment.
    inactive_branch_cases = (
        (
            "#if 0\nrunDrainAbortWithoutIsr(\n"
            "    true, 34, 35, \"inactive-low-capture\", \"inactive-low-release\");\n"
            "#endif\n",
            calls[0],
            "active-low",
        ),
        (
            "#if 0\nrunDrainAbortWithoutIsr(\n"
            "    false, 36, 37, \"inactive-high-capture\", \"inactive-high-release\");\n"
            "#endif\n",
            calls[1],
            "active-high",
        ),
    )
    for inactive_source, marker, label in inactive_branch_cases:
        legacy_count = " ".join(mask_non_code(inactive_source).split()).count(marker)
        if legacy_count != 1:
            raise AssertionError(
                f"legacy comment/literal-only mask did not expose {label} decoy: {legacy_count}"
            )
        if normalized_cpp_fixture(inactive_source).count(marker) != 0:
            raise SystemExit(
                f"POLL_DRAIN_ABORT_POLARITY_INACTIVE_BRANCH_DECOY_SURVIVED: {label}"
            )
    print("POLL_DRAIN_ABORT_POLARITY_INACTIVE_BRANCH_DECOY_REJECTED 2/2")

    print("POLL_DRAIN_ABORT_POLARITY_DECOY_REJECTED 2/2")
    print("POLL_DRAIN_ABORT_POLARITY_BUILDER_PASS 2/2")


