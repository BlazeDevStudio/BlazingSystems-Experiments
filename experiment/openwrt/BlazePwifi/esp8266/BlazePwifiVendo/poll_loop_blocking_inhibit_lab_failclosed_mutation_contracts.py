"""Fail-closed mutation matrix for the blocking-poll firmware lab.

Keep authority/output, ISR persistence, final-sample, and sticky-fault
mutations separate from the runner's board orchestration.
"""

from poll_loop_blocking_inhibit_lab_edge_fixtures import (
    STICKY_FAULT_LATER_ISR_MAIN,
    pre_poll_active_line_main,
)


def run_poll_failclosed_mutation_contracts(
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
    write_fault,
    load_fault,
    latch_fault,
    init_store,
    sample,
    reconcile,
):
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
