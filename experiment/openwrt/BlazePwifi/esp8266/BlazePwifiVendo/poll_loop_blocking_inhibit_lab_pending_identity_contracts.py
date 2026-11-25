"""Pending identity and configured-ingress denial matrix for the blocking-poll lab.

Keep these scenarios separate from loop orchestration. The runner supplies the
board-specific source extractors and compile callback explicitly; fixture inputs
remain the same source-extracted C++ used before this cleanup.
"""
from poll_loop_blocking_inhibit_lab_edge_fixtures import (
    ATTEMPTED_EVIDENCE_MAIN,
    disabled_ingress_gate_main,
)
from poll_loop_blocking_inhibit_lab_fixtures import PENDING_PRESERVATION_MAIN


def run_pending_identity_matrix(
    board,
    assemble,
    compile_and_run,
    sample,
    latch_fault,
    output,
    coin_ingress_config,
):
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
