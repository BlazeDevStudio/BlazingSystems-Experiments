"""Source-exact host regression for pending-journal reclamation and quarantine failures.

This isolates clearPending() and quarantinePending() from GPIO/network behavior.
The lab extracts production helpers unchanged. readPendingFile(), appendQuarantineRecord()
and LittleFS remain explicit test adapters: they model record-read, append and
removal failures, not serialized bytes, LittleFS wear, power loss, or durability.
"""

from pending_clear_failure_lab_fixtures import (
    BOOT_ORPHAN_ATTEMPT_MAIN,
    CLEAR_PENDING_MAIN,
    CLEAR_PENDING_STUBS,
    QUARANTINE_PENDING_MAIN,
    QUARANTINE_PENDING_STUBS,
)


def run_pending_clear_failure_lab(
    board,
    clear_pending_source,
    same_pending_record_source,
    load_pending_source,
    pending_attempt_marker_matches_source,
    quarantine_pending_source,
    compile_and_run,
):
    """Compile exact production helpers and reject fail-open reclamation mutations."""
    sources = {
        "clearPending": clear_pending_source,
        "loadPending": load_pending_source,
        "samePendingRecord": same_pending_record_source,
        "pendingAttemptMarkerMatches": pending_attempt_marker_matches_source,
        "quarantinePending": quarantine_pending_source,
    }
    for name, source in sources.items():
        if not source:
            raise AssertionError(f"{board}: missing source-exact {name} helper")

    def compile_case(label, expected=0, clear_source=None, same_record_source=None,
                     load_source=None, main_source=None):
        selected_clear = clear_source if clear_source is not None else clear_pending_source
        selected_same = (
            same_record_source
            if same_record_source is not None
            else same_pending_record_source
        )
        selected_load = load_source if load_source is not None else load_pending_source
        selected_main = main_source if main_source is not None else CLEAR_PENDING_MAIN
        program = (
            CLEAR_PENDING_STUBS
            + selected_same
            + "\n"
            + pending_attempt_marker_matches_source
            + "\n"
            + selected_load
            + "\n"
            + selected_clear
            + "\n"
            + selected_main
        )
        return compile_and_run(program, board, expected, label)

    baseline = compile_case("pending-clear-precondition-and-removal-failures")
    for marker in (
        "PENDING_CLEAR_REMOVE_FAILURE_INJECTION_PASS 4/4 plus success control",
        "PENDING_CLEAR_PRECONDITION_FAILURE_INJECTION_PASS 7/7",
    ):
        if marker not in baseline:
            raise AssertionError(f"{board}: pending-clear baseline marker missing: {marker}")
    print(f"{board} {baseline}")

    boot_baseline = compile_case(
        "pending-clear-orphan-attempt-boot-deny",
        main_source=BOOT_ORPHAN_ATTEMPT_MAIN,
    )
    if "PENDING_CLEAR_ORPHAN_ATTEMPT_BOOT_DENY_PASS" not in boot_baseline:
        raise AssertionError(f"{board}: orphan attempt marker boot-deny marker missing")
    print(f"{board} {boot_baseline}")
    print(f"{board} PENDING_CLEAR_ORPHAN_ATTEMPT_BOOT_DENY_PASS")

    orphan_attempt_anchor = 'if(hasAttempt){\n      journalRecoveryRequired=true;'
    orphan_attempt_mutation = load_pending_source.replace(
        orphan_attempt_anchor,
        'if(false && hasAttempt){\n      journalRecoveryRequired=true;',
        1,
    )
    if orphan_attempt_mutation == load_pending_source:
        raise AssertionError(f"{board}: orphan attempt boot-deny mutation anchor missing")
    compile_case(
        "pending-clear-orphan-attempt-boot-deny-mutation",
        102,
        load_source=orphan_attempt_mutation,
        main_source=BOOT_ORPHAN_ATTEMPT_MAIN,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-orphan-attempt-boot-deny "
        "expected_exit=102"
    )

    attempt_remove_anchor = (
        'if(!LittleFS.remove("/pending.attempt") || LittleFS.exists("/pending.attempt")){'
    )
    attempt_remove_mutation = clear_pending_source.replace(
        attempt_remove_anchor,
        'LittleFS.remove("/pending.attempt"); if(false){',
        1,
    )
    if attempt_remove_mutation == clear_pending_source:
        raise AssertionError(f"{board}: attempt-marker removal mutation anchor missing")
    compile_case(
        "pending-clear-ignores-attempt-marker-removal-failure",
        91,
        clear_source=attempt_remove_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-attempt-marker-removal-failure "
        "expected_exit=91"
    )

    attempt_remove_readback_anchor = (
        'if(!LittleFS.remove("/pending.attempt") || LittleFS.exists("/pending.attempt")){'
    )
    attempt_remove_readback_mutation = clear_pending_source.replace(
        attempt_remove_readback_anchor,
        'if(!LittleFS.remove("/pending.attempt")){',
        1,
    )
    if attempt_remove_readback_mutation == clear_pending_source:
        raise AssertionError(f"{board}: attempt-marker remove-readback mutation anchor missing")
    compile_case(
        "pending-clear-ignores-attempt-marker-remove-readback-failure",
        103,
        clear_source=attempt_remove_readback_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-attempt-marker-remove-readback-failure "
        "expected_exit=103"
    )

    attempt_recheck_anchor = (
        'if(!readPendingFile("/pending.attempt",attempt) ||\n'
        '     attempt.pulses!=pendingPulses ||\n'
        '     strcmp(attempt.nonce,pendingNonce.c_str())!=0 ||\n'
        '     strcmp(attempt.target,pendingTarget.c_str())!=0){'
    )
    attempt_recheck_mutation = clear_pending_source.replace(
        attempt_recheck_anchor,
        'if(!readPendingFile("/pending.attempt",attempt)){',
        1,
    )
    if attempt_recheck_mutation == clear_pending_source:
        raise AssertionError(f"{board}: attempt-marker identity recheck mutation anchor missing")
    compile_case(
        "pending-clear-skips-second-attempt-identity-check",
        96,
        clear_source=attempt_recheck_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-skips-second-attempt-identity-check "
        "expected_exit=96"
    )

    same_record_anchor = (
        "return left.magic==right.magic && left.pulses==right.pulses &&\n"
        "         strcmp(left.nonce,right.nonce)==0 &&\n"
        "         strcmp(left.target,right.target)==0 &&\n"
        "         left.checksum==right.checksum;"
    )
    same_record_mutation = same_pending_record_source.replace(
        same_record_anchor,
        "return true;",
        1,
    )
    if same_record_mutation == same_pending_record_source:
        raise AssertionError(f"{board}: durable-record identity mutation anchor missing")
    compile_case(
        "pending-clear-ignores-durable-record-identity",
        97,
        same_record_source=same_record_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-durable-record-identity "
        "expected_exit=97"
    )

    candidate_count_anchor = "if(candidateCount!=1 || !candidatePath){"
    candidate_count_mutation = clear_pending_source.replace(
        candidate_count_anchor,
        "if(false){",
        1,
    )
    if candidate_count_mutation == clear_pending_source:
        raise AssertionError(f"{board}: candidate-count guard mutation anchor missing")
    compile_case(
        "pending-clear-ignores-ambiguous-journal-candidates",
        99,
        clear_source=candidate_count_mutation,
    )

    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-ambiguous-journal-candidates "
        "expected_exit=99"
    )

    def compile_quarantine_case(label, expected=0, quarantine_source=None, main_source=None):
        selected_quarantine = (
            quarantine_source
            if quarantine_source is not None
            else quarantine_pending_source
        )
        selected_main = main_source if main_source is not None else QUARANTINE_PENDING_MAIN
        program = (
            CLEAR_PENDING_STUBS
            + QUARANTINE_PENDING_STUBS
            + "\n"
            + same_pending_record_source
            + "\n"
            + pending_attempt_marker_matches_source
            + "\n"
            + clear_pending_source
            + "\n"
            + selected_quarantine
            + "\n"
            + selected_main
        )
        return compile_and_run(program, board, expected, label)

    quarantine_baseline = compile_quarantine_case(
        "quarantine-append-failure-preservation"
    )
    quarantine_markers = (
        "QUARANTINE_APPEND_FAILURE_PRESERVES_PENDING_AND_ATTEMPT_PASS",
        "QUARANTINE_APPEND_SUCCESS_CLEAR_CONTROL_PASS",
        "QUARANTINE_CLEAR_FAILURE_PRESERVES_ATTEMPT_AND_RAM_PASS",
        "QUARANTINE_MISSING_PENDING_DENIED_PASS",
        "QUARANTINE_MISMATCHED_ATTEMPT_DENIED_PASS",
        "QUARANTINE_DISPOSITION_FAILURE_INJECTION_PASS 1/1",
    )
    for marker in quarantine_markers:
        if marker not in quarantine_baseline:
            raise AssertionError(
                f"{board}: quarantine disposition baseline marker missing: {marker}"
            )
    print(f"{board} {quarantine_baseline}")

    append_guard_anchor = "if(!appendQuarantineRecord(reason)){"
    append_guard_mutation = quarantine_pending_source.replace(
        append_guard_anchor,
        "if(false){",
        1,
    )
    if append_guard_mutation == quarantine_pending_source:
        raise AssertionError(f"{board}: quarantine append-failure guard mutation anchor missing")
    compile_quarantine_case(
        "quarantine-append-failure-clears-pending",
        110,
        quarantine_source=append_guard_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED quarantine-append-failure-clears-pending "
        "expected_exit=110"
    )

    append_latch_anchor = (
        'journalRecoveryRequired=true;\n'
        '    Serial.println("CRITICAL: quarantine journal commit failed; pending coin retained and relay disabled.");'
    )
    append_latch_mutation = quarantine_pending_source.replace(
        append_latch_anchor,
        'journalRecoveryRequired=false;\n'
        '    Serial.println("CRITICAL: quarantine journal commit failed; pending coin retained and relay disabled.");',
        1,
    )
    if append_latch_mutation == quarantine_pending_source:
        raise AssertionError(f"{board}: quarantine append-failure latch mutation anchor missing")
    compile_quarantine_case(
        "quarantine-append-failure-without-recovery-latch",
        110,
        quarantine_source=append_latch_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED quarantine-append-failure-without-recovery-latch "
        "expected_exit=110"
    )

    attempt_gate_anchor = "if(!pendingAttemptMarkerMatches()){"
    attempt_gate_mutation = quarantine_pending_source.replace(
        attempt_gate_anchor,
        "if(false){",
        1,
    )
    if attempt_gate_mutation == quarantine_pending_source:
        raise AssertionError(f"{board}: quarantine attempt-marker guard mutation anchor missing")
    compile_quarantine_case(
        "quarantine-without-matching-attempt-marker",
        113,
        quarantine_source=attempt_gate_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED quarantine-without-matching-attempt-marker "
        "expected_exit=113"
    )

    clear_result_anchor = "  return clearPending();"
    clear_result_mutation = quarantine_pending_source.replace(
        clear_result_anchor,
        "  clearPending(); return true;",
        1,
    )
    if clear_result_mutation == quarantine_pending_source:
        raise AssertionError(f"{board}: quarantine clear-result propagation mutation anchor missing")
    compile_quarantine_case(
        "quarantine-ignores-clear-failure",
        114,
        quarantine_source=clear_result_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED quarantine-ignores-clear-failure "
        "expected_exit=114"
    )
