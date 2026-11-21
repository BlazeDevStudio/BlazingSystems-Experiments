"""Source-exact ESP32/ESP8266 poll, coin and quarantine parity guards.

This module owns C++ token-aware normalization and shared-helper parity.
The companion runner owns the extracted loop scenarios and compilation.
"""
from firmware_lab_source import extract_function

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


def normalize_cpp_function_body(body):
    """Collapse code whitespace without changing C++ literal or comment bytes."""
    output = []
    pending_space = False
    i = 0

    def flush_space():
        nonlocal pending_space
        if pending_space and output and output[-1] != " ":
            output.append(" ")
        pending_space = False

    raw_prefixes = ("u8R\"", "uR\"", "UR\"", "LR\"", "R\"")
    while i < len(body):
        ch = body[i]

        if ch.isspace():
            pending_space = True
            i += 1
            continue

        raw_prefix = next((prefix for prefix in raw_prefixes if body.startswith(prefix, i)), None)
        if raw_prefix is not None:
            flush_space()
            quote_index = i + len(raw_prefix) - 1
            open_paren = body.find("(", quote_index + 1)
            if open_paren < 0:
                raise ValueError("unterminated C++ raw-string delimiter")
            delimiter = body[quote_index + 1:open_paren]
            if len(delimiter) > 16 or any(c.isspace() or c in "()\\" for c in delimiter):
                raise ValueError("invalid C++ raw-string delimiter")
            terminator = ")" + delimiter + '"'
            close = body.find(terminator, open_paren + 1)
            if close < 0:
                raise ValueError("unterminated C++ raw string")
            end = close + len(terminator)
            output.append(body[i:end])
            i = end
            pending_space = False
            continue

        if body.startswith("//", i):
            start = i
            cursor = i + 2
            while cursor < len(body):
                if body[cursor] not in "\r\n":
                    cursor += 1
                    continue
                newline_end = cursor + 1
                if body[cursor] == "\r" and newline_end < len(body) and body[newline_end] == "\n":
                    newline_end += 1
                # C++ phase 2 splices backslash-newline before // comment parsing.
                # Keep every continued physical line inside the comment token.
                if cursor > start and body[cursor - 1] == "\\":
                    cursor = newline_end
                    continue
                break
            end = cursor
            comment = body[start:end].replace("\r\n", "\n").replace("\r", "\n")
            if output and output[-1] != " ":
                output.append(" ")
            output.append(comment)
            i = end
            pending_space = True
            continue

        if body.startswith("/*", i):
            end = body.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated C++ block comment")
            end += 2
            comment = body[i:end].replace("\r\n", "\n").replace("\r", "\n")
            if output and output[-1] != " ":
                output.append(" ")
            output.append(comment)
            i = end
            pending_space = True
            continue

        if ch in ("\"", "'"):
            flush_space()
            quote = ch
            literal_start = i
            i += 1
            while i < len(body):
                if body[i] == "\\":
                    if i + 1 >= len(body):
                        raise ValueError("unterminated C++ escape sequence")
                    i += 2
                elif body[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("unterminated C++ quoted literal")
            output.append(body[literal_start:i])
            pending_space = False
            continue

        flush_space()
        output.append(ch)
        i += 1
        pending_space = False

    return "".join(output)


def verify_cpp_parity_normalizer():
    cases = (
        ("formatting-only", 'void f() { return "pending event"; }', 'void f()  {\n  return   "pending event";  }', True),
        ("string-literal-whitespace", 'void f(){ return "pending event"; }', 'void f(){ return "pending  event"; }', False),
        ("character-literal-whitespace", "void f(){ char c=' '; }", r"void f(){ char c='\t'; }", False),
        ("comment-content", "void f(){ /* durable record */ return true; }", "void f(){ /*durable record*/ return true; }", False),
        ("raw-string-literal-whitespace", 'void f(){ auto s=R"tag(pending event)tag"; }', 'void f(){ auto s=R"tag(pending  event)tag"; }', False),
        ("escaped-quote", r'void f(){ const char *s="quote: \" pending"; }', r'void f(){ const char *s="quote: pending"; }', False),
        ("line-comment-content", "void f(){ // pending event\n return true; }", "void f(){ // pending  event\n return true; }", False),
        ("line-comment-backslash-newline-content", "void f(){ // pending \\\n event  text\n return true; }", "void f(){ // pending \\\n event text\n return true; }", False),
        ("line-comment-splice-boundary", "void f(){ // pending \\\n return false;\n}", "void f(){ // pending\n return false;\n}", False),
        ("line-comment-crlf-normalization", "void f(){ // pending \\\r\n event text\r\n return true; }", "void f(){ // pending \\\n event text\n return true; }", True),
    )
    for label, left, right, expected_equal in cases:
        actual_equal = normalize_cpp_function_body(left) == normalize_cpp_function_body(right)
        if actual_equal != expected_equal:
            raise SystemExit(f"POLL_SAFETY_CPP_PARITY_NORMALIZER_FAIL: {label}")
    print(f"POLL_SAFETY_CPP_PARITY_NORMALIZER_PASS {len(cases)}/{len(cases)}")


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


verify_poll_safety_board_parity()
verify_drain_abort_polarity_fixture_is_shared()
