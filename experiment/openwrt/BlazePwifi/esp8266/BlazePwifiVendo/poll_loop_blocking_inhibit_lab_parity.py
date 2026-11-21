"""Source-exact ESP32/ESP8266 poll, coin and quarantine parity guards.

This module owns board-helper parity and fail-open mutation guards.
C++ token-aware normalization lives in the adjacent normalizer module.
The companion runner owns the extracted loop scenarios and compilation.
"""
from firmware_lab_source import extract_function
from poll_loop_blocking_inhibit_lab_normalizer import normalize_cpp_function_body

POLL_SAFETY_PARITY = (
    "coinEdgeISR",
    "snapshotCoinEdgeSequence",
    "boundedCoinDebounceMs",
    "canStartPoll",
    "applyOutputs",
    "beginPollWindow",
    "sampleCoinPulseEdge",
    "latchPollPulseFault",
    "quarantineCoinIngressTransition",
    "handlePollDrainAbortAfterSample",
    "reconcileUnobservedCoinEdges",
    # Shared trust, receipt and pending-evidence authority must not drift by board.
    "acceptPollResponse",
    "coinPostDispositionVerified",
    "canAttemptCoinPost",
    "markPendingPostAttempt",
    "pendingAttemptMarkerMatches",
    "clearPending",
    # Quarantine persistence/cleanup is shared safety policy, not board-specific.
    "quarantineLogTokenValid",
    "quarantineLogField",
    "quarantineLogRecordValid",
    "inspectQuarantineLog",
    "appendQuarantineRecord",
    "quarantinePending",
)


REQUIRED_COIN_AUTHORITY_PARITY = (
    "acceptPollResponse",
    "coinPostDispositionVerified",
    "canAttemptCoinPost",
    "markPendingPostAttempt",
    "pendingAttemptMarkerMatches",
    "clearPending",
)
missing_coin_authority_helpers = [
    name for name in REQUIRED_COIN_AUTHORITY_PARITY
    if name not in POLL_SAFETY_PARITY
]
if missing_coin_authority_helpers:
    raise SystemExit(
        "POLL_COIN_AUTHORITY_PARITY_REQUIRED_HELPERS_MISSING: "
        + ", ".join(missing_coin_authority_helpers)
    )


REQUIRED_QUARANTINE_PARITY = (
    "quarantineLogTokenValid",
    "quarantineLogField",
    "quarantineLogRecordValid",
    "inspectQuarantineLog",
    "appendQuarantineRecord",
    "quarantinePending",
)
missing_quarantine_helpers = [
    name for name in REQUIRED_QUARANTINE_PARITY
    if name not in POLL_SAFETY_PARITY
]
if missing_quarantine_helpers:
    raise SystemExit(
        "POLL_QUARANTINE_PARITY_REQUIRED_HELPERS_MISSING: "
        + ", ".join(missing_quarantine_helpers)
    )


def poll_safety_helpers(boards):
    helpers = {}
    for board, path in boards.items():
        source = path.read_text(encoding="utf-8")
        helpers[board] = {}
        for name in POLL_SAFETY_PARITY:
            body = extract_function(source, name)
            if not body:
                raise AssertionError(f"{board}: missing shared poll-safety helper {name}")
            # Normalize code whitespace only; preserve literal and comment bytes.
            helpers[board][name] = normalize_cpp_function_body(body)
    return helpers


def poll_safety_parity_mismatches(helpers):
    reference = helpers["ESP8266"]
    candidate = helpers["ESP32"]
    return [
        name for name in POLL_SAFETY_PARITY
        if not reference.get(name) or reference.get(name) != candidate.get(name)
    ]


def verify_poll_safety_board_parity(boards):
    helpers = poll_safety_helpers(boards)
    mismatches = poll_safety_parity_mismatches(helpers)
    if mismatches:
        raise SystemExit(
            "POLL_SAFETY_BOARD_PARITY_FAIL: " + ", ".join(mismatches)
        )
    print(
        f"POLL_SAFETY_BOARD_PARITY_PASS {len(POLL_SAFETY_PARITY)}/"
        f"{len(POLL_SAFETY_PARITY)} normalized helpers"
    )
    print(
        f"POLL_QUARANTINE_HELPER_BOARD_PARITY_PASS "
        f"{len(REQUIRED_QUARANTINE_PARITY)}/{len(REQUIRED_QUARANTINE_PARITY)}"
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

    # Quarantine write/readback and pending cleanup must remain fail-closed on
    # both boards. These mutations model bypassing the durable append guards.
    quarantine_mutations = (
        ("appendQuarantineRecord", "if(written!=(size_t)len){", "if(false){"),
        ("quarantinePending", "if(!appendQuarantineRecord(reason)){", "if(false){"),
    )
    for name, anchor, replacement in quarantine_mutations:
        mutated = {
            board: dict(board_helpers)
            for board, board_helpers in helpers.items()
        }
        body = mutated["ESP32"][name]
        if anchor not in body:
            raise AssertionError(f"ESP32 {name} quarantine mutation anchor missing")
        mutated["ESP32"][name] = body.replace(anchor, replacement, 1)
        mismatches = poll_safety_parity_mismatches(mutated)
        if name not in mismatches:
            raise SystemExit(
                f"POLL_QUARANTINE_PARITY_MUTATION_SURVIVED: ESP32 {name}"
            )
        print(f"POLL_QUARANTINE_PARITY_MUTATION_REJECTED ESP32_{name}")


def verify_drain_abort_polarity_fixture_is_shared(main):
    helper = "int runDrainAbortWithoutIsr(bool activeLow, int holdFailureCode, int releaseFailureCode,"
    if main.count(helper) != 1:
        raise SystemExit(
            "POLL_DRAIN_ABORT_POLARITY_BUILDER_MISSING: expected one shared C++ helper"
        )
    normalized_main = " ".join(main.split())
    calls = (
        "runDrainAbortWithoutIsr( true, 34, 35,",
        "runDrainAbortWithoutIsr( false, 36, 37,",
    )
    for call in calls:
        if normalized_main.count(call) != 1:
            raise SystemExit(
                "POLL_DRAIN_ABORT_POLARITY_BUILDER_CALL_MISSING: " + call
            )
    print("POLL_DRAIN_ABORT_POLARITY_BUILDER_PASS 2/2")

