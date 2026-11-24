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
    PENDING_PRESERVATION_MAIN,
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
    ATTEMPTED_EVIDENCE_MAIN,
    STICKY_FAULT_LATER_ISR_MAIN,
    disabled_ingress_gate_main,
    pre_poll_active_line_main,
    late_poll_baseline_main,
)
from poll_loop_blocking_inhibit_lab_response_fixtures import (
    POLL_HTTP_RESPONSE_DENY_NO_EDGE_MAIN,
    POLL_HTTP_KEYLESS_RESPONSE_DENY_MAIN,
)
from poll_loop_blocking_inhibit_lab_source_contracts import (
    verify_poll_safety_board_parity,
    verify_drain_abort_polarity_fixture_is_shared,
)

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

    # Isolate response denial from the ISR fault latch: no edge occurs during
    # the 3.5-second HTTP call, so only acceptPollResponse() may keep intake OFF.
    permissive_accept = accept
    for anchor, replacement in (
        ("insertMode=false;", "insertMode=true;"),
        ('activeTarget="";', 'activeTarget="spoof-target";'),
        ("return false;", "return true;"),
    ):
        if permissive_accept.count(anchor) != 1:
            raise AssertionError(f"{board}: poll-response fail-open mutation anchor is not unique: {anchor}")
        permissive_accept = permissive_accept.replace(anchor, replacement, 1)

    response_cases = (
        ("hostile-positive", SUPPORT),
        ("empty-timeout", timeout_support),
    )
    relay_cases = (
        ("active-high", POLL_HTTP_RESPONSE_DENY_NO_EDGE_MAIN),
        ("active-low", with_active_low_relay(POLL_HTTP_RESPONSE_DENY_NO_EDGE_MAIN)),
    )
    for relay_name, response_main in relay_cases:
        for response_name, response_support in response_cases:
            scenario = f"poll-http-no-edge-{relay_name}-{response_name}"
            response_output = compile_and_run(
                assemble(main_source=response_main, support_source=response_support),
                board, 0, scenario,
            )
            if "POLL_HTTP_RESPONSE_DENY_NO_EDGE_PASS" not in response_output:
                raise AssertionError(f"{board}: no-edge response-deny marker missing for {scenario}")
            print(f"{board} {scenario.upper().replace('-', '_')}_PASS")

            compile_and_run(
                assemble(
                    accept_source=permissive_accept,
                    main_source=response_main,
                    support_source=response_support,
                ),
                board, 90, scenario + "-fail-open-mutation",
            )
            print(
                f"{board} MUTATION_REJECTED {scenario}-fail-open-mutation "
                "expected_exit=90"
            )

    # Keyless poll responses remain deny-only even when they carry an untrusted
    # response_sig-looking field. The placeholder below is deliberately not a
    # protocol vector and must never be treated as a valid signature.
    keyless_response_support = SUPPORT.replace(
        timeout_response_anchor,
        r'    return String("{\"ok\":true,\"insert\":true,\"target\":\"spoof-target\",\"response_sig\":\"unapproved-test-only\"}");',
        1,
    )
    if keyless_response_support == SUPPORT:
        raise AssertionError(f"{board}: keyless response-signature fixture anchor missing")

    keyless_fail_open = accept.replace(
        '  (void)response;\n  insertMode=false;\n  activeTarget="";\n  return false;',
        '  (void)response;\n  if(controllerKeyEmpty()){ insertMode=true; activeTarget="spoof-target"; return true; }\n  insertMode=false;\n  activeTarget="";\n  return false;',
        1,
    )
    if keyless_fail_open == accept:
        raise AssertionError(f"{board}: keyless fail-open mutation anchor missing")

    for relay_name, _response_main in relay_cases:
        keyless_main = (
            POLL_HTTP_KEYLESS_RESPONSE_DENY_MAIN
            if relay_name == "active-high"
            else with_active_low_relay(POLL_HTTP_KEYLESS_RESPONSE_DENY_MAIN)
        )
        scenario = f"poll-http-keyless-response-{relay_name}"
        keyless_output = compile_and_run(
            assemble(main_source=keyless_main, support_source=keyless_response_support),
            board, 0, scenario,
        )
        if "POLL_HTTP_KEYLESS_RESPONSE_DENY_PASS" not in keyless_output:
            raise AssertionError(f"{board}: keyless response-deny marker missing for {scenario}")
        print(f"{board} {scenario.upper().replace('-', '_')}_PASS")
        compile_and_run(
            assemble(
                accept_source=keyless_fail_open,
                main_source=keyless_main,
                support_source=keyless_response_support,
            ),
            board, 90, scenario + "-fail-open-mutation",
        )
        print(f"{board} MUTATION_REJECTED {scenario}-fail-open-mutation expected_exit=90")

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
    # Execute the focused pending-identity matrix on the unmutated exact source;
    # mutation-only execution is not a substitute for a green baseline run.
    print(board,compile_and_run(assemble(main_source=PENDING_PRESERVATION_MAIN),
                                board,0,"disabled-intake-pending-identity"))
    print(board,compile_and_run(assemble(main_source=ATTEMPTED_EVIDENCE_MAIN),
                                board,0,"disabled-intake-attempted-pending-evidence"))
    pending_ready_mutation = sample.replace(
        "if(pendingPulses>0U) pendingReady=true;",
        "if(false) pendingReady=true;",
        1,
    )
    if pending_ready_mutation == sample:
        raise AssertionError(f"{board}: disabled-intake pendingReady mutation anchor missing")
    compile_and_run(
        assemble(sample_source=pending_ready_mutation,main_source=PENDING_PRESERVATION_MAIN),
        board,66,"disabled-intake-pending-ready-preservation"
    )
    print(f"{board} MUTATION_REJECTED disabled-intake-pending-ready-preservation expected_exit=66")
    pending_identity_mutation = latch_fault.replace(
        'activeTarget="";',
        'activeTarget=""; pendingTarget=""; pendingNonce="";',
        1,
    )
    if pending_identity_mutation == latch_fault:
        raise AssertionError(f"{board}: pending-identity mutation anchor missing")
    compile_and_run(
        assemble(latch_fault_source=pending_identity_mutation,main_source=PENDING_PRESERVATION_MAIN),
        board,66,"disabled-intake-pending-identity"
    )
    print(f"{board} MUTATION_REJECTED disabled-intake-pending-identity expected_exit=66")

    pending_evidence_paths = (
        "/pending.dat",
        "/pending.new",
        "/pending.bak",
        "/pending.attempt",
    )
    for evidence_path in pending_evidence_paths:
        pending_evidence_mutation = latch_fault.replace(
            'activeTarget="";',
            f'activeTarget=""; LittleFS.files.erase("{evidence_path}");',
            1,
        )
        if pending_evidence_mutation == latch_fault:
            raise AssertionError(
                f"{board}: pending evidence deletion mutation anchor missing for {evidence_path}"
            )
        compile_and_run(
            assemble(latch_fault_source=pending_evidence_mutation,
                     main_source=ATTEMPTED_EVIDENCE_MAIN),
            board,82,f"disabled-intake-pending-evidence-preservation-{evidence_path}"
        )
        print(
            f"{board} MUTATION_REJECTED disabled-intake-pending-evidence-preservation "
            f"path={evidence_path} expected_exit=82"
        )

    pending_attempt_state_mutation = latch_fault.replace(
        'activeTarget="";',
        'activeTarget=""; pendingPostAttempted=false;',
        1,
    )
    if pending_attempt_state_mutation == latch_fault:
        raise AssertionError(f"{board}: pending attempt-state mutation anchor missing")
    compile_and_run(
        assemble(latch_fault_source=pending_attempt_state_mutation,
                 main_source=ATTEMPTED_EVIDENCE_MAIN),
        board,82,"disabled-intake-pending-attempt-state-preservation"
    )
    print(
        f"{board} MUTATION_REJECTED disabled-intake-pending-attempt-state-preservation "
        "expected_exit=82"
    )

    pending_edge_delta_mutation = sample.replace(
        "latchPollPulseFault((uint32_t)pendingPulses+unseenEdges);",
        "latchPollPulseFault((uint32_t)pendingPulses+1U);",
        1,
    )
    if pending_edge_delta_mutation == sample:
        raise AssertionError(f"{board}: pending multi-edge delta mutation anchor missing")
    compile_and_run(
        assemble(sample_source=pending_edge_delta_mutation,main_source=PENDING_PRESERVATION_MAIN),
        board,72,"disabled-intake-pending-edge-delta"
    )
    print(f"{board} MUTATION_REJECTED disabled-intake-pending-edge-delta expected_exit=72")

    relay_gate_mutation = output.replace(
        "bool accepting=pinConfigSafe && coinIngressConfigurationAllows() && insertMode",
        "bool accepting=pinConfigSafe && true && insertMode",
        1,
    )
    if relay_gate_mutation == output:
        raise AssertionError(f"{board}: configured relay output gate mutation anchor missing")
    compile_and_run(
        assemble(output_source=relay_gate_mutation,main_source=PENDING_PRESERVATION_MAIN),
        board,80,"disabled-intake-relay-output-gate"
    )
    print(f"{board} MUTATION_REJECTED disabled-intake-relay-output-gate expected_exit=80")
    # The output-gate mutation above protects applyOutputs(), but that alone
    # cannot prove that sampleCoinPulseEdge() refuses to create a pending credit.
    # Independently remove each configured admission term and require the
    # existing no-pending disabled-ingress scenarios to fail on that mutation.
    coin_ingress_gate_mutations = (
        ("controller", "true && coinEnabled && relayEnabled", 64),
        ("coin", "controllerEnabled && true && relayEnabled", 62),
        ("relay", "controllerEnabled && coinEnabled && true", 60),
    )
    original_coin_ingress_gate = "return controllerEnabled && coinEnabled && relayEnabled;"
    # Isolate sample-path admission while retaining the real output function's
    # side effects: force only its configured-admission call false.
    output_gate_for_sample_mutation = output.replace(
        "coinIngressConfigurationAllows()", "false", 1
    )
    if output_gate_for_sample_mutation == output:
        raise AssertionError(f"{board}: sample isolation output-gate anchor missing")
    disabled_flags = {
        "controller": "controllerEnabled",
        "coin": "coinEnabled",
        "relay": "relayEnabled",
    }
    for gate_name, mutated_gate, expected_exit in coin_ingress_gate_mutations:
        coin_ingress_gate_mutation = coin_ingress_config.replace(
            original_coin_ingress_gate,
            f"return {mutated_gate};",
            1,
        )
        if coin_ingress_gate_mutation == coin_ingress_config:
            raise AssertionError(
                f"{board}: configured {gate_name} coin-ingress gate mutation anchor missing"
            )
        gate_main = disabled_ingress_gate_main(disabled_flags[gate_name], expected_exit)
        compile_and_run(
            assemble(output_source=output_gate_for_sample_mutation, main_source=gate_main),
            board,
            0,
            f"disabled-intake-{gate_name}-coin-ingress-baseline",
        )
        print(f"{board} BASELINE_PASS disabled-intake-{gate_name}-coin-ingress")
        compile_and_run(
            assemble(output_source=output_gate_for_sample_mutation,
                     coin_ingress_config_source=coin_ingress_gate_mutation,
                     main_source=gate_main),
            board,
            expected_exit,
            f"disabled-intake-{gate_name}-coin-ingress-gate",
        )
        print(
            f"{board} MUTATION_REJECTED disabled-intake-{gate_name}-coin-ingress-gate "
            f"expected_exit={expected_exit}"
        )
    print(board,compile_and_run(assemble(main_source=RELEASE_EDGE_MAIN),board,0,
                                "poll-release-output-interlock"))
    timing_output=compile_and_run(assemble(main_source=TIMING_MAIN),board,0,
                                 "issue-177-original-1501-1600-1680-timing")
    if "PHX_177_ORIGINAL_1501_1600_1680_PULSE_ABORTED_BEFORE_HTTP_PASS" not in timing_output:
        raise AssertionError(f"{board}: exact #177 timing marker missing")
    print(f"{board} PHX_177_ORIGINAL_1501_1600_1680_TIMING_PASS")
    unsafe_timing_loop=loop.replace(
        "const bool pollWindowReady=beginPollWindow();",
        "const bool pollWindowReady=true;",
        1,
    )
    if unsafe_timing_loop==loop:
        raise AssertionError(f"{board}: #177 pre-poll inhibit mutation anchor missing")
    compile_and_run(assemble(loop_source=unsafe_timing_loop,main_source=TIMING_MAIN),
                    board,47,"issue-177-missing-prepoll-inhibit")
    print(f"{board} MUTATION_REJECTED issue-177-missing-prepoll-inhibit expected_exit=47")

    # Cross-check the complete blocking-poll path with an active-low acceptor relay.
    # The separate polarity lab covers applyOutputs() in isolation; this scenario
    # composes the configured polarity with the 1501/1600/1680 timing and HTTP path.
    active_low_timing_main = with_active_low_relay(TIMING_MAIN)
    active_low_timing_output = compile_and_run(
        assemble(main_source=active_low_timing_main),
        board, 0, "issue-177-active-low-relay-original-timing",
    )
    if "PHX_177_ORIGINAL_1501_1600_1680_PULSE_ABORTED_BEFORE_HTTP_PASS" not in active_low_timing_output:
        raise AssertionError(f"{board}: active-low #177 timing marker missing")
    print(f"{board} PHX_177_ACTIVE_LOW_RELAY_1501_1600_1680_TIMING_PASS")
    compile_and_run(
        assemble(loop_source=unsafe_timing_loop, main_source=active_low_timing_main),
        board, 47, "issue-177-active-low-relay-missing-prepoll-inhibit",
    )
    print(f"{board} MUTATION_REJECTED issue-177-active-low-relay-missing-prepoll-inhibit expected_exit=47")

    active_low_http_main = with_active_low_relay(POLL_HTTP_ISR_MAIN)
    active_low_http_output = compile_and_run(
        assemble(main_source=active_low_http_main),
        board, 0, "poll-http-active-low-relay",
    )
    if "POLL_HTTP_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS" not in active_low_http_output:
        raise AssertionError(f"{board}: active-low blocked-poll marker missing")
    print(f"{board} POLL_HTTP_ACTIVE_LOW_RELAY_INHIBIT_PASS")
    compile_and_run(
        assemble(output_source=poll_output_mutation, main_source=active_low_http_main),
        board, 88, "poll-http-active-low-relay-output-gate-mutation",
    )
    print(f"{board} MUTATION_REJECTED poll-http-active-low-relay-output-gate expected_exit=88")
    non_wrap_safe_loop=loop.replace(
        "latchPollPulseFault(pollEdgeEnd-pollEdgeStart);",
        "latchPollPulseFault(pollEdgeEnd>pollEdgeStart ? pollEdgeEnd-pollEdgeStart : 0U);",
        1,
    )
    if non_wrap_safe_loop==loop:
        raise AssertionError(f"{board}: poll-edge wrap mutation anchor missing")
    compile_and_run(assemble(loop_source=non_wrap_safe_loop),board,50,
                    "non-wrap-safe-poll-edge-delta")
    print(f"{board} MUTATION_REJECTED non-wrap-safe-poll-edge-delta expected_exit=50")
    single_edge_loop=loop.replace(
        "latchPollPulseFault(pollEdgeEnd-pollEdgeStart);",
        "latchPollPulseFault(1U);",
        1,
    )
    if single_edge_loop==loop:
        raise AssertionError(f"{board}: exact poll-edge count mutation anchor missing")
    compile_and_run(assemble(loop_source=single_edge_loop),board,51,
                    "single-edge-poll-delta")
    print(f"{board} MUTATION_REJECTED single-edge-poll-delta expected_exit=51")
    idle_fault_shortcut = quarantine.replace(
        "  if(journalRecoveryRequired){",
        "  if(lineIdle && unhandledEdges==0U) return true;\n  if(journalRecoveryRequired){",
        1,
    )
    if idle_fault_shortcut == quarantine:
        raise AssertionError(f"{board}: journal-fault idle-line mutation anchor missing")
    compile_and_run(assemble(quarantine_source=idle_fault_shortcut),board,48,
                    "journal-fault-idle-line-shortcut")
    print(f"{board} MUTATION_REJECTED journal-fault-idle-line-shortcut")
    edge_hook = begin.replace(
        "return coinLineQuietAfterInhibit();",
        "if(coinLineQuietAfterInhibit()){ if(injectAfterDrainEdge){ for(unsigned edge=0; edge<injectAfterDrainEdgeCount; ++edge){ if(interruptAttached && attachedIsr && attachedPin==runCoinPin && attachedMode==(runCoinActiveLow?FALLING:RISING)) attachedIsr(); } injectAfterDrainEdge=false; } return true; } return false;",
        1,
    )
    if edge_hook == begin:
        raise AssertionError(f"{board}: missing post-drain edge injection point")
    compile_and_run(assemble(begin_source=edge_hook,main_source=RACE_MAIN),board,0,
                    "edge-after-drain-before-snapshot")
    print(f"{board} POLL_EDGE_SNAPSHOT_RACE_PASS")
    single_post_drain_edge_loop = loop.replace(
        "latchPollPulseFault(pollEdgeAfterDrain-pollEdgeStart);",
        "latchPollPulseFault(1U);",
        1,
    )
    if single_post_drain_edge_loop == loop:
        raise AssertionError(f"{board}: post-drain exact-edge-count mutation anchor missing")
    compile_and_run(
        assemble(loop_source=single_post_drain_edge_loop,begin_source=edge_hook,main_source=RACE_MAIN),
        board,55,"single-edge-post-drain-count"
    )
    print(f"{board} MUTATION_REJECTED single-edge-post-drain-count expected_exit=55")

    # The dedicated active-high scenario uses the real RISING ISR on both boards.
    compile_and_run(assemble(begin_source=edge_hook,main_source=post_drain_rollover_main(active_low=False)),
                    board,0,"active-high-post-drain-multi-edge-rollover")
    print(f"{board} POLL_POST_DRAIN_ACTIVE_HIGH_MULTI_EDGE_ROLLOVER_PASS")
    active_high_wrong_edge = configure.replace(
        "runCoinActiveLow?FALLING:RISING",
        "runCoinActiveLow?FALLING:FALLING",
    )
    if active_high_wrong_edge == configure:
        raise AssertionError(f"{board}: active-high ISR polarity mutation anchor missing")
    compile_and_run(
        assemble(configure_source=active_high_wrong_edge,begin_source=edge_hook,main_source=post_drain_rollover_main(active_low=False)),
        board,56,"active-high-post-drain-edge-polarity"
    )
    print(f"{board} MUTATION_REJECTED active-high-post-drain-edge-polarity expected_exit=56")

    # The active-low counterpart uses the real FALLING ISR across the same wrap race.
    compile_and_run(assemble(begin_source=edge_hook,main_source=post_drain_rollover_main(active_low=True)),
                    board,0,"active-low-post-drain-multi-edge-rollover")
    print(f"{board} POLL_POST_DRAIN_ACTIVE_LOW_MULTI_EDGE_ROLLOVER_PASS")
    active_low_wrong_edge = configure.replace(
        "runCoinActiveLow?FALLING:RISING",
        "runCoinActiveLow?RISING:RISING",
    )
    if active_low_wrong_edge == configure:
        raise AssertionError(f"{board}: active-low ISR polarity mutation anchor missing")
    compile_and_run(
        assemble(configure_source=active_low_wrong_edge,begin_source=edge_hook,main_source=post_drain_rollover_main(active_low=True)),
        board,59,"active-low-post-drain-edge-polarity"
    )
    print(f"{board} MUTATION_REJECTED active-low-post-drain-edge-polarity expected_exit=59")

    # A high-polarity pulse can disappear after the drain read but before the
    # ordinary loop sample. Preserve the unresolved event instead of polling.
    missed_sample_output = compile_and_run(
        assemble(main_source=ACTIVE_HIGH_MISSED_SAMPLE_MAIN),
        board, 0, "active-high-pulse-ended-before-sample"
    )
    if "POLL_ABORT_ACTIVE_HIGH_PULSE_ENDED_BEFORE_SAMPLE_FAIL_CLOSED_PASS" not in missed_sample_output:
        raise AssertionError(f"{board}: active-high missed-sample marker missing")
    print(f"{board} POLL_ABORT_ACTIVE_HIGH_PULSE_ENDED_BEFORE_SAMPLE_PASS")

    active_high_idle_fail_open = idle.replace(
        "return runCoinActiveLow?raw:!raw;",
        "return runCoinActiveLow?raw:true;",
        1,
    )
    if active_high_idle_fail_open == idle:
        raise AssertionError(f"{board}: active-high coin-line idle mutation anchor missing")
    compile_and_run(
        assemble(idle_source=active_high_idle_fail_open,
                 main_source=ACTIVE_HIGH_MISSED_SAMPLE_MAIN),
        board, 57, "active-high-pulse-misread-as-idle"
    )
    print(f"{board} MUTATION_REJECTED active-high-pulse-misread-as-idle expected_exit=57")
    # The active-low counterpart isolates the same missed-sample failure path.
    missed_sample_low_output = compile_and_run(
        assemble(main_source=ACTIVE_LOW_MISSED_SAMPLE_MAIN),
        board, 0, "active-low-pulse-ended-before-sample"
    )
    if "POLL_ABORT_ACTIVE_LOW_PULSE_ENDED_BEFORE_SAMPLE_FAIL_CLOSED_PASS" not in missed_sample_low_output:
        raise AssertionError(f"{board}: active-low missed-sample marker missing")
    print(f"{board} POLL_ABORT_ACTIVE_LOW_PULSE_ENDED_BEFORE_SAMPLE_PASS")

    active_low_idle_fail_open = idle.replace(
        "return runCoinActiveLow?raw:!raw;",
        "return runCoinActiveLow?true:!raw;",
        1,
    )
    if active_low_idle_fail_open == idle:
        raise AssertionError(f"{board}: active-low coin-line idle mutation anchor missing")
    compile_and_run(
        assemble(idle_source=active_low_idle_fail_open,
                 main_source=ACTIVE_LOW_MISSED_SAMPLE_MAIN),
        board, 58, "active-low-pulse-misread-as-idle"
    )
    print(f"{board} MUTATION_REJECTED active-low-pulse-misread-as-idle expected_exit=58")
    release_on_abort = drain_abort.replace(
        "if(!coinLineIdle()) return;",
        "pollDrainAbortedOnActiveLine=false; pollIntakeSuspended=false; applyOutputs(); return;",
        1,
    )
    if release_on_abort == drain_abort:
        raise AssertionError(f"{board}: drain-abort release mutation anchor missing")
    compile_and_run(assemble(drain_abort_source=release_on_abort),board,34,"release-while-active-drain-line")
    print(f"{board} MUTATION_REJECTED release-while-active-drain-line")
    poll_start_snapshot = loop.find("const uint32_t pollEdgeStart=snapshotCoinEdgeSequence();")
    begin_poll = loop.find("const bool pollWindowReady=beginPollWindow();")
    if poll_start_snapshot < 0 or begin_poll < 0 or poll_start_snapshot > begin_poll:
        raise AssertionError(f"{board}: ISR baseline must be captured before intake inhibit/drain")
    pre_poll_guard = loop.find("if(pollEdgeAfterDrain!=pollEdgeStart)")
    poll_call = loop.find('String r=post("poll")')
    if pre_poll_guard < 0 or poll_call < 0 or pre_poll_guard > poll_call:
        raise AssertionError(f"{board}: pre-poll edge guard must precede HTTP poll")

    begin_poll = loop.find("const bool pollWindowReady=beginPollWindow();")
    drain_snapshot = loop.find("const uint32_t pollEdgeAfterDrain=snapshotCoinEdgeSequence();", begin_poll)
    if begin_poll < 0 or drain_snapshot < begin_poll or pre_poll_guard < drain_snapshot:
        raise AssertionError(f"{board}: ISR snapshot must follow either drain outcome before branching")
    poll_guard_removed = loop.replace(
        "const uint32_t pollEdgeAfterDrain=snapshotCoinEdgeSequence();",
        "const uint32_t pollEdgeAfterDrain=pollEdgeStart;",
        1,
    )
    if poll_guard_removed == loop:
        raise AssertionError(f"{board}: missing pre-poll edge-abort guard")
    compile_and_run(assemble(loop_source=poll_guard_removed,begin_source=edge_hook,main_source=RACE_MAIN),
                    board,25,"missing-drain-abort-edge-reconciliation")
    print(f"{board} MUTATION_REJECTED missing-pre-poll-edge-abort")
    # Failure injection: moving the ISR baseline until after the 250 ms drain
    # absorbs an edge that arrived during the drain into the baseline. The
    # post-drain comparison then misses it and incorrectly permits HTTP polling.
    late_poll_start_loop = loop.replace(
        "const uint32_t pollEdgeStart=snapshotCoinEdgeSequence();",
        "uint32_t pollEdgeStart=lastHandledCoinEdgeSequence;",
        1,
    )
    if late_poll_start_loop == loop:
        raise AssertionError(f"{board}: initial poll-edge baseline mutation anchor missing")
    late_poll_start_loop = late_poll_start_loop.replace(
        "const bool pollWindowReady=beginPollWindow();",
        "const bool pollWindowReady=beginPollWindow();\n      pollEdgeStart=snapshotCoinEdgeSequence();",
        1,
    )
    if late_poll_start_loop == loop or "pollEdgeStart=snapshotCoinEdgeSequence();" not in late_poll_start_loop:
        raise AssertionError(f"{board}: late poll-edge baseline mutation did not apply")
    late_baseline_main = late_poll_baseline_main()
    compile_and_run(
        assemble(begin_source=edge_hook,main_source=late_baseline_main),
        board,0,"late-poll-edge-baseline-control"
    )
    print(f"{board} POLL_PRE_DRAIN_BASELINE_EDGE_CONTROL_PASS")
    compile_and_run(
        assemble(loop_source=late_poll_start_loop,begin_source=edge_hook,main_source=late_baseline_main),
        board,22,"late-poll-edge-baseline-after-drain"
    )
    print(f"{board} MUTATION_REJECTED late-poll-edge-baseline-after-drain expected_exit=22")

    mutations=(
      ("remove-beginPollWindow",loop.replace("const bool pollWindowReady=beginPollWindow();","const bool pollWindowReady=true;",1),output,quiet,accept),
      ("ignore-pollIntakeSuspended",loop,output.replace(" && !pollIntakeSuspended","",1),quiet,accept),
      ("shorten-quiet-window-to-249ms",loop,output,quiet.replace("pulseTrainQuietMs=250UL;","pulseTrainQuietMs=249UL;",1),accept),
      ("keep-insert-enabled-after-poll",loop,output,quiet,accept.replace("insertMode=false;","insertMode=true;",1)),
      ("retain-stale-target-after-poll",loop,output,quiet,accept.replace('activeTarget="";','activeTarget="stale-target";',1)),
    )
    journal_fault_guard_removed = output.replace("!journalRecoveryRequired && ", "", 1)
    if journal_fault_guard_removed == output:
        raise AssertionError(f"{board}: journal-recovery output guard mutation did not apply")
    compile_and_run(assemble(output_source=journal_fault_guard_removed),board,48,
                    "ignore-journal-recovery-output-deny")
    print(f"{board} MUTATION_REJECTED ignore-journal-recovery-output-deny expected_exit=48")

    for name,mut_loop,mut_output,mut_quiet,mut_accept in mutations:
        if name=="remove-beginPollWindow" and mut_loop==loop:
            raise AssertionError(f"{board}: poll-window call mutation did not apply")
        if name=="ignore-pollIntakeSuspended" and mut_output==output:
            raise AssertionError(f"{board}: output-gate mutation did not apply")
        if name=="shorten-quiet-window-to-249ms" and mut_quiet==quiet:
            raise AssertionError(f"{board}: quiet-window mutation did not apply")
        if name=="keep-insert-enabled-after-poll" and mut_accept==accept:
            raise AssertionError(f"{board}: insert-state mutation did not apply")
        if name=="retain-stale-target-after-poll" and mut_accept==accept:
            raise AssertionError(f"{board}: stale-target mutation did not apply")
        compile_and_run(assemble(mut_loop,mut_output,mut_quiet,mut_accept),board,10,name)
        print(f"{board} MUTATION_REJECTED {name} expected_exit=10")

    extra_mutations=(
      ("remove-edge-interrupt-attachment",loop,output,quiet,accept,
       configure.replace("attachInterrupt(digitalPinToInterrupt(runCoinPin),coinEdgeISR,runCoinActiveLow?FALLING:RISING);",""),isr,write_fault,load_fault,latch_fault,init_store,12),
      ("ignore-poll-edge-delta",loop.replace("if(pollEdgeEnd!=pollEdgeStart){","if(false){",1),output,quiet,accept,
       configure,isr,write_fault,load_fault,latch_fault,init_store,12),
      ("no-op-coin-isr",loop,output,quiet,accept,configure,
       isr.replace("coinEdgeSequence++;","coinEdgeSequence+=0;",1),write_fault,load_fault,latch_fault,init_store,12),
      ("remove-fault-marker-write",loop,output,quiet,accept,configure,isr,
       write_fault,load_fault,latch_fault.replace("const bool littleFsPersisted=writePollPulseFaultMarker(pulseEdges);","const bool littleFsPersisted=false;",1),init_store,12),
      ("defer-fault-output-inhibit",loop,output,quiet,accept,configure,isr,write_fault,load_fault,
       latch_fault.replace("  // Deassert the physical outputs before any flash persistence can block.\n  applyOutputs();\n  const bool backupPersisted=writePollFaultBackup(pulseEdges);",
                           "  const bool backupPersisted=writePollFaultBackup(pulseEdges);",1),
       init_store,23),
      ("remove-boot-fault-latch",loop,output,quiet,accept,configure,isr,write_fault,
       load_fault.replace("if(backupHold || littleFsHold){","if(backupHold && littleFsHold){",1),
       latch_fault,init_store,15),
    )
    for name,ml,mo,mq,ma,mc,mi,mw,mload,mlatch,ms,expected in extra_mutations:
        if name=="remove-edge-interrupt-attachment" and mc==configure:
            raise AssertionError(f"{board}: interrupt-attachment mutation did not apply")
        if name=="ignore-poll-edge-delta" and ml==loop:
            raise AssertionError(f"{board}: poll-edge-delta mutation did not apply")
        if name=="no-op-coin-isr" and mi==isr:
            raise AssertionError(f"{board}: ISR mutation did not apply")
        if name=="remove-fault-marker-write" and mlatch==latch_fault:
            raise AssertionError(f"{board}: fault-marker mutation did not apply")
        if name=="defer-fault-output-inhibit" and mlatch==latch_fault:
            raise AssertionError(f"{board}: pre-persistence output-inhibit mutation did not apply")
        if name=="remove-boot-fault-latch" and mload==load_fault:
            raise AssertionError(f"{board}: boot-latch mutation did not apply")
        compile_and_run(assemble(ml,mo,mq,ma,mc,mi,mw,mload,mlatch,ms),board,expected,name)
        print(f"{board} MUTATION_REJECTED {name} expected_exit={expected}")

    # Prove the release-window ISR edge is caught by the ordinary sample path
    # when it arrives after the post-poll snapshot but before the loop's final sample.
    missing_release_sample = loop.replace(
        "sampleCoinPulseEdge(active);",
        "(void)active; // mutation: final post-poll sample omitted",
        1,
    )
    if missing_release_sample == loop:
        raise AssertionError(f"{board}: final post-poll sample mutation did not apply")
    compile_and_run(assemble(loop_source=missing_release_sample),board,29,
                    "skip-poll-release-edge-sample")
    print(f"{board} MUTATION_REJECTED skip-poll-release-edge-sample")


    # A pulse already active before poll admission, with no ISR transition,
    # must be sampled once and remain pending after the line returns idle.
    for active_low, label, failure_code in (
        (True, "active-low", 88),
        (False, "active-high", 89),
    ):
        active_line_main = pre_poll_active_line_main(
            active_low=active_low,
            failure_code=failure_code,
        )
        active_line_output = compile_and_run(
            assemble(main_source=active_line_main),
            board,
            0,
            f"pre-poll-active-line-{label}",
        )
        marker = f"POLL_PRESTART_{label.upper().replace('-', '_')}_NO_ISR_CAPTURED_ONCE_PASS"
        if marker not in active_line_output:
            raise AssertionError(f"{board}: missing {label} pre-poll active-line marker")
        print(f"{board} {marker}")

        missing_active_sample = sample.replace(
            "if(fsReady && !journalRecoveryRequired && active && !lastCoin &&",
            "if(false && !journalRecoveryRequired && active && !lastCoin &&",
            1,
        )
        if missing_active_sample == sample:
            raise AssertionError(f"{board}: pre-poll active-line sample mutation anchor missing")
        compile_and_run(
            assemble(sample_source=missing_active_sample, main_source=active_line_main),
            board,
            failure_code,
            f"pre-poll-active-line-missing-sample-{label}",
        )
        print(
            f"{board} MUTATION_REJECTED pre-poll-active-line-missing-sample-{label} "
            f"expected_exit={failure_code}"
        )

    pre_poll_edge_guard_removed = loop.replace(
        "if(pollEdgeStart!=lastHandledCoinEdgeSequence){",
        "if(false){",
        1,
    )
    if pre_poll_edge_guard_removed == loop:
        raise AssertionError(f"{board}: pre-poll unobserved-edge guard mutation did not apply")
    compile_and_run(assemble(loop_source=pre_poll_edge_guard_removed),board,44,
                    "ignore-unobserved-edge-before-poll")
    print(f"{board} MUTATION_REJECTED ignore-unobserved-edge-before-poll")
    missing_coin_post_latch = reconcile.replace(
        "latchPollPulseFault((uint32_t)pendingPulses+unhandledEdges);",
        "// mutation: unresolved edge persistence omitted",
        1,
    )
    if missing_coin_post_latch == reconcile:
        raise AssertionError(f"{board}: coin-post persistence mutation did not apply")
    compile_and_run(assemble(reconcile_source=missing_coin_post_latch),board,45,
                    "missing-coin-post-edge-persistence")
    print(f"{board} MUTATION_REJECTED missing-coin-post-edge-persistence")

    sticky_output = compile_and_run(
        assemble(main_source=STICKY_FAULT_LATER_ISR_MAIN),
        board, 0, "first-fault-snapshot-after-later-isr"
    )
    if "POLL_FAULT_FIRST_LATCH_SNAPSHOT_STABLE_AFTER_LATER_ISR_PASS" not in sticky_output:
        raise AssertionError(f"{board}: first-fault snapshot marker missing")
    print(f"{board} POLL_FAULT_FIRST_LATCH_SNAPSHOT_STABLE_AFTER_LATER_ISR_PASS")

    # Failure injection: re-entering latchPollPulseFault after the sticky flag
    # is set must be rejected by the write-attempt count and immutable marker.
    sticky_latch_guard_removed = sample.replace(
        "if(!journalRecoveryRequired){", "if(true){", 1
    )
    if sticky_latch_guard_removed == sample:
        raise AssertionError(f"{board}: sticky-latch guard mutation anchor missing")
    compile_and_run(
        assemble(sample_source=sticky_latch_guard_removed,
                 main_source=STICKY_FAULT_LATER_ISR_MAIN),
        board, 90, "later-isr-reenters-sticky-fault-latch"
    )
    print(f"{board} MUTATION_REJECTED later-isr-reenters-sticky-fault-latch expected_exit=90")

run_remote_config_pin_recovery_lab()

print("PHX-HARDWARE: poll-fault and coin-POST ISR reconciliation passed on ESP8266 and ESP32; no hardware evidence")
