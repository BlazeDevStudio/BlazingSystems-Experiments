#!/usr/bin/env python3
"""Execute the actual ESP loop() around the synchronous poll with bounded host I/O stubs.

The production loop, poll-window helpers, output gate, coin POST disposition
helper and default-deny acceptPollResponse() are extracted unchanged from both sketches. Secondary
NVS/EEPROM helpers are stubbed here; poll_fault_dual_store_lab.py tests them
separately. This is SIMULATED control-flow evidence, not physical coin proof.
"""
from pathlib import Path
from cpp_fixture_runner import run_cpp_fixture
from cpp_fixture_runner_contract_lab import verify as verify_cpp_fixture_runner_contract

from firmware_lab_source import extract_function
from firmware_lab_source_lab import run_source_extractor_regressions
from remote_config_pin_recovery_lab import run_remote_config_pin_recovery_lab
from pending_clear_failure_lab import run_pending_clear_failure_lab

verify_cpp_fixture_runner_contract()
run_source_extractor_regressions()

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

from poll_loop_blocking_inhibit_lab_fixtures import (
    STUBS,
    SUPPORT,
    MAIN,
    COIN_POST_ISR_MAIN,
    POLL_HTTP_ISR_MAIN,
    RACE_MAIN,
    post_drain_rollover_main,
    missed_sample_main,
    TIMING_MAIN,
    RELEASE_EDGE_MAIN,
    with_active_low_relay,
    CLEAR_WINDOW_ISR_MAIN,
)
from poll_loop_blocking_inhibit_lab_edge_fixtures import (
    ACTIVE_HIGH_MISSED_SAMPLE_MAIN,
    ACTIVE_LOW_MISSED_SAMPLE_MAIN,
    STICKY_FAULT_LATER_ISR_MAIN,
    pre_poll_active_line_main,
    late_poll_baseline_main,
)
from poll_loop_blocking_inhibit_lab_response_contracts import run_poll_response_denial_matrix
from poll_loop_blocking_inhibit_lab_source_contracts import (
    verify_poll_safety_board_parity,
    verify_drain_abort_polarity_fixture_is_shared,
)
from poll_loop_blocking_inhibit_lab_pending_identity_contracts import run_pending_identity_matrix
from poll_loop_blocking_inhibit_lab_edge_race_contracts import run_poll_edge_race_contracts
from poll_loop_blocking_inhibit_lab_failclosed_mutation_contracts import run_poll_failclosed_mutation_contracts

def compile_and_run(code, board, expected=0, label="normal"):
    ran = run_cpp_fixture(
        code,
        prefix="phx-poll-loop-",
        stem="poll_loop",
        extra_flags=("-Wno-unused-parameter",),
        compile_timeout=30,
        run_timeout=10,
        context=f"{board} {label}",
    )
    if ran.returncode != expected:
        raise RuntimeError(
            f"{board} {label}: expected exit {expected}, got {ran.returncode}\n"
            f"stdout={ran.stdout}\nstderr={ran.stderr}"
        )
    return ran.stdout.strip()

verify_poll_safety_board_parity(BOARDS, extract_function)
verify_drain_abort_polarity_fixture_is_shared(MAIN)


for board,path in BOARDS.items():
    source=path.read_text(encoding="utf-8")
    edge_decl=source.find("volatile uint32_t coinEdgeSequence")
    edge_isr=min(
        (pos for pos in (
            source.find("void ICACHE_RAM_ATTR coinEdgeISR"),
            source.find("void IRAM_ATTR coinEdgeISR"),
        ) if pos >= 0),
        default=-1,
    )
    if edge_decl < 0 or edge_isr < 0 or edge_decl > edge_isr:
        raise AssertionError(f"{board}: coinEdgeSequence must be declared before coinEdgeISR")
    loop=extract_function(source, "loop")
    write=extract_function(source, "writeLogical")
    output=extract_function(source, "applyOutputs")
    coin_ingress_config=extract_function(source, "coinIngressConfigurationAllows")
    if not coin_ingress_config:
        raise AssertionError(f"{board}: missing configured coin-ingress predicate")
    idle=extract_function(source, "coinLineIdle")
    can_start=extract_function(source, "canStartPoll")
    quiet=extract_function(source, "coinLineQuietAfterInhibit")
    begin=extract_function(source, "beginPollWindow")
    accept=extract_function(source, "acceptPollResponse")
    isr=extract_function(source, "coinEdgeISR")
    snapshot=extract_function(source, "snapshotCoinEdgeSequence")
    configure=extract_function(source, "configureRuntimePins")
    write_fault=extract_function(source, "writePollPulseFaultMarker")
    load_fault=extract_function(source, "loadPollPulseFaultLatch")
    latch_fault=extract_function(source, "latchPollPulseFault")
    quarantine=extract_function(source, "quarantineCoinIngressTransition")
    init_store=extract_function(source, "initPendingStore")
    sample=extract_function(source, "sampleCoinPulseEdge")
    drain_abort=extract_function(source, "handlePollDrainAbortAfterSample")
    reconcile=extract_function(source, "reconcileUnobservedCoinEdges")
    handle=extract_function(source, "handleCoinPostResponse")
    clear_pending=extract_function(source, "clearPending")
    load_pending=extract_function(source, "loadPending")
    same_pending_record=extract_function(source, "samePendingRecord")
    pending_attempt_marker_matches=extract_function(source, "pendingAttemptMarkerMatches")
    quarantine_pending=extract_function(source, "quarantinePending")
    if not clear_pending or not load_pending or not same_pending_record or not pending_attempt_marker_matches or not quarantine_pending:
        raise AssertionError(f"{board}: missing source-exact pending-clear/recovery helper set")

    def assemble(loop_source=loop,output_source=output,quiet_source=quiet,accept_source=accept,
                 configure_source=configure,isr_source=isr,write_fault_source=write_fault,
                 load_fault_source=load_fault,latch_fault_source=latch_fault,init_store_source=init_store,
                 begin_source=begin,sample_source=sample,main_source=MAIN,reconcile_source=reconcile,
                 handle_source=handle,drain_abort_source=drain_abort,quarantine_source=quarantine,
                 idle_source=idle,coin_ingress_config_source=coin_ingress_config,support_source=SUPPORT):
        board_define = "#define TARGET_ESP32\n" if board=="ESP32" else "#define ESP8266\n"
        return (board_define+STUBS+isr_source+snapshot+write+coin_ingress_config_source+output_source+idle_source+can_start+
                quiet_source+begin_source+write_fault_source+
                load_fault_source+latch_fault_source+quarantine_source+configure_source+accept_source+reconcile_source+init_store_source+support_source+handle_source+sample_source+drain_abort_source+loop_source+main_source)

    print(board,compile_and_run(assemble(),board,0,"exact-source"))
    coin_post_output=compile_and_run(
        assemble(main_source=COIN_POST_ISR_MAIN),
        board,0,"coin-post-isr-multi-edge-rollover"
    )
    if "COIN_POST_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS" not in coin_post_output:
        raise AssertionError(f"{board}: coin-POST ISR rollover marker missing")
    print(f"{board} COIN_POST_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS")

    poll_http_output=compile_and_run(
        assemble(main_source=POLL_HTTP_ISR_MAIN),
        board,0,"poll-http-isr-multi-edge-rollover"
    )
    if "POLL_HTTP_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS" not in poll_http_output:
        raise AssertionError(f"{board}: blocked-poll ISR rollover marker missing")
    print(f"{board} POLL_HTTP_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS")

    # Re-run the blocked-poll ISR case with the empty String returned when
    # HTTPClient reports a transport timeout or another non-positive status.
    timeout_response_anchor = r'    return String("{\"ok\":true,\"insert\":true,\"target\":\"spoof-target\"}");'
    if SUPPORT.count(timeout_response_anchor) != 1:
        raise AssertionError(f"{board}: blocked-poll hostile response stub is not unique")
    timeout_support = SUPPORT.replace(timeout_response_anchor, "    return String();", 1)
    poll_http_timeout_main = POLL_HTTP_ISR_MAIN.replace(
        "POLL_HTTP_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS",
        "POLL_HTTP_TIMEOUT_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS",
        1,
    )
    timeout_output = compile_and_run(
        assemble(support_source=timeout_support,main_source=poll_http_timeout_main),
        board,0,"poll-http-timeout-isr-multi-edge-rollover"
    )
    if "POLL_HTTP_TIMEOUT_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS" not in timeout_output:
        raise AssertionError(f"{board}: timeout-path ISR fault marker missing")
    print(f"{board} POLL_HTTP_TIMEOUT_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS")

    run_poll_response_denial_matrix(
        board=board,
        accept=accept,
        support=SUPPORT,
        timeout_response_anchor=timeout_response_anchor,
        timeout_support=timeout_support,
        compile_and_run=compile_and_run,
        assemble=assemble,
        with_active_low_relay=with_active_low_relay,
        loop=loop,
        output=output,
    )
    # The post-HTTP ISR delta must be durably latched before the ordinary input sample.
    poll_reconcile_anchor="if(pollEdgeEnd!=pollEdgeStart){"
    poll_reconcile_mutation=loop.replace(poll_reconcile_anchor,"if(false){",1)
    if poll_reconcile_mutation==loop:
        raise AssertionError(f"{board}: post-HTTP poll-edge reconciliation mutation anchor missing")
    compile_and_run(
        assemble(loop_source=poll_reconcile_mutation,main_source=POLL_HTTP_ISR_MAIN),
        board,88,"poll-http-missing-post-response-edge-reconciliation"
    )
    print(f"{board} MUTATION_REJECTED poll-http-missing-post-response-edge-reconciliation expected_exit=88")

    # The timeout path must also fail if the post-response ISR reconciliation is removed.
    compile_and_run(
        assemble(loop_source=poll_reconcile_mutation,main_source=poll_http_timeout_main),
        board,88,"poll-http-timeout-missing-post-response-edge-reconciliation"
    )
    print(f"{board} MUTATION_REJECTED poll-http-timeout-missing-post-response-edge-reconciliation expected_exit=88")

    # The real relay/LED gate must remain inhibited for the entire blocking HTTP call.
    poll_output_mutation=output.replace("!pollIntakeSuspended &&","true &&",1)
    if poll_output_mutation==output:
        raise AssertionError(f"{board}: poll-intake output gate mutation anchor missing")
    compile_and_run(
        assemble(output_source=poll_output_mutation,main_source=POLL_HTTP_ISR_MAIN),
        board,88,"poll-http-output-gate-ignores-intake-inhibit"
    )
    print(f"{board} MUTATION_REJECTED poll-http-output-gate-ignores-intake-inhibit expected_exit=88")

    coin_post_attach_anchor=(
        "attachInterrupt(digitalPinToInterrupt(runCoinPin),coinEdgeISR,"
        "runCoinActiveLow?FALLING:RISING);"
    )
    coin_post_missing_isr=configure.replace(coin_post_attach_anchor,"")
    if coin_post_missing_isr==configure:
        raise AssertionError(f"{board}: coin-POST ISR attachment mutation anchor missing")
    compile_and_run(
        assemble(configure_source=coin_post_missing_isr,
                 main_source=COIN_POST_ISR_MAIN),
        board,45,"coin-post-missing-isr-attachment"
    )
    print(f"{board} MUTATION_REJECTED coin-post-missing-isr-attachment expected_exit=45")

    print(board,compile_and_run(assemble(main_source=CLEAR_WINDOW_ISR_MAIN),
                                board,0,"coin-post-clear-window-isr-edge"))
    clear_recheck_anchor = (
        "if(reconcileUnobservedCoinEdges()) clearPending();\n"
        "    if(!reconcileUnobservedCoinEdges()) applyOutputs();"
    )
    clear_recheck_mutation = handle.replace(
        clear_recheck_anchor,
        "if(reconcileUnobservedCoinEdges()) clearPending();",
        1,
    )
    if clear_recheck_mutation == handle:
        raise AssertionError(f"{board}: clear-window reconciliation mutation anchor missing")
    compile_and_run(
        assemble(handle_source=clear_recheck_mutation,
                 main_source=CLEAR_WINDOW_ISR_MAIN),
        board,54,"coin-post-clear-window-isr-recheck"
    )
    print(f"{board} MUTATION_REJECTED coin-post-clear-window-isr-recheck expected_exit=54")
    run_pending_clear_failure_lab(board,clear_pending,same_pending_record,load_pending,
                                   pending_attempt_marker_matches,quarantine_pending,compile_and_run)
    run_pending_identity_matrix(
        board=board,
        assemble=assemble,
        compile_and_run=compile_and_run,
        sample=sample,
        latch_fault=latch_fault,
        output=output,
        coin_ingress_config=coin_ingress_config,
    )
    run_poll_edge_race_contracts(
        board=board,
        assemble=assemble,
        compile_and_run=compile_and_run,
        loop=loop,
        output=output,
        poll_output_mutation=poll_output_mutation,
        quiet=quiet,
        accept=accept,
        configure=configure,
        isr=isr,
        begin=begin,
        quarantine=quarantine,
        drain_abort=drain_abort,
        idle=idle,
    )
    run_poll_failclosed_mutation_contracts(
        board=board,
        assemble=assemble,
        compile_and_run=compile_and_run,
        loop=loop,
        output=output,
        quiet=quiet,
        accept=accept,
        configure=configure,
        isr=isr,
        write_fault=write_fault,
        load_fault=load_fault,
        latch_fault=latch_fault,
        init_store=init_store,
        sample=sample,
        reconcile=reconcile,
    )

run_remote_config_pin_recovery_lab()

print("PHX-HARDWARE: poll-fault and coin-POST ISR reconciliation passed on ESP8266 and ESP32; no hardware evidence")
