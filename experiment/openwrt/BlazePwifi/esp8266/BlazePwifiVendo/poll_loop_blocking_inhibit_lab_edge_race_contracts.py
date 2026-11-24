"""Blocking-poll edge, relay-polarity, and drain-order contracts.

These source-extracted scenarios cover the P0 pulse-loss boundary without
claiming physical coin-acceptor or relay evidence. The runner supplies exact
board source and host compile callbacks; fixture programs stay in their
existing fixture modules.
"""

from poll_loop_blocking_inhibit_lab_edge_fixtures import (
    ACTIVE_HIGH_MISSED_SAMPLE_MAIN,
    ACTIVE_LOW_MISSED_SAMPLE_MAIN,
    late_poll_baseline_main,
    pre_poll_active_line_main,
)
from poll_loop_blocking_inhibit_lab_fixtures import (
    POLL_HTTP_ISR_MAIN,
    RACE_MAIN,
    RELEASE_EDGE_MAIN,
    TIMING_MAIN,
    post_drain_rollover_main,
    with_active_low_relay,
)


def run_poll_edge_race_contracts(
    *,
    board,
    assemble,
    compile_and_run,
    loop,
    output,
    quiet,
    accept,
    configure,
    isr,
    begin,
    quarantine,
    drain_abort,
    idle,
):
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
    
