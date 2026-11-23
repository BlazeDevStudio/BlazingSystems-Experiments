#!/usr/bin/env python3
"""Execute the actual ESP loop() around the synchronous poll with bounded host I/O stubs.

The production loop, poll-window helpers, output gate, coin POST disposition
helper and default-deny acceptPollResponse() are extracted unchanged from both sketches. Secondary
NVS/EEPROM helpers are stubbed here; poll_fault_dual_store_lab.py tests them
separately. This is SIMULATED control-flow evidence, not physical coin proof.
"""
from pathlib import Path
import subprocess
import tempfile

from firmware_lab_source import extract_function, mask_active_cpp_code, mask_non_code
from firmware_lab_source_lab import run_source_extractor_regressions
from remote_config_pin_recovery_lab import run_remote_config_pin_recovery_lab

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
    PENDING_PRESERVATION_MAIN,
    RACE_MAIN,
    post_drain_rollover_main,
    missed_sample_main,
    TIMING_MAIN,
    RELEASE_EDGE_MAIN,
)

ACTIVE_HIGH_MISSED_SAMPLE_MAIN = missed_sample_main(active_low=False, failure_code=57)
ACTIVE_LOW_MISSED_SAMPLE_MAIN = missed_sample_main(active_low=True, failure_code=58)


def compile_and_run(code, board, expected=0, label="normal"):
    with tempfile.TemporaryDirectory(prefix="phx-poll-loop-") as folder:
        cpp=Path(folder)/"poll_loop.cpp"
        binary=Path(folder)/"poll_loop"
        cpp.write_text(code,encoding="utf-8")
        built=subprocess.run(
            ["g++","-std=c++17","-Wall","-Wextra","-Werror",
             "-Wno-unused-parameter",str(cpp),"-o",str(binary)],
            capture_output=True,text=True,timeout=30
        )
        if built.returncode:
            raise RuntimeError(f"{board} {label}: compile failed:\n{built.stderr[-3000:]}")
        ran=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        if ran.returncode!=expected:
            raise RuntimeError(
                f"{board} {label}: expected exit {expected}, got {ran.returncode}\n"
                f"stdout={ran.stdout}\nstderr={ran.stderr}"
            )
        return ran.stdout.strip()

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


def poll_safety_helpers():
    helpers = {}
    for board, path in BOARDS.items():
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


def verify_poll_safety_board_parity():
    helpers = poll_safety_helpers()
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


def verify_drain_abort_polarity_fixture_is_shared():
    helper = "int runDrainAbortWithoutIsr(bool activeLow, int holdFailureCode, int releaseFailureCode,"
    if normalized_cpp_fixture(MAIN).count(helper) != 1:
        raise SystemExit(
            "POLL_DRAIN_ABORT_POLARITY_BUILDER_MISSING: expected one shared C++ helper"
        )
    normalized_main = normalized_cpp_fixture(MAIN)
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
        mutated = MAIN.replace(original, decoy, 1)
        if mutated == MAIN:
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


verify_poll_safety_board_parity()
verify_drain_abort_polarity_fixture_is_shared()


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

    def assemble(loop_source=loop,output_source=output,quiet_source=quiet,accept_source=accept,
                 configure_source=configure,isr_source=isr,write_fault_source=write_fault,
                 load_fault_source=load_fault,latch_fault_source=latch_fault,init_store_source=init_store,
                 begin_source=begin,sample_source=sample,main_source=MAIN,reconcile_source=reconcile,
                 handle_source=handle,drain_abort_source=drain_abort,quarantine_source=quarantine,
                 idle_source=idle):
        board_define = "#define TARGET_ESP32\n" if board=="ESP32" else "#define ESP8266\n"
        return (board_define+STUBS+isr_source+snapshot+write+output_source+idle_source+can_start+
                quiet_source+begin_source+write_fault_source+
                load_fault_source+latch_fault_source+quarantine_source+configure_source+accept_source+reconcile_source+init_store_source+SUPPORT+handle_source+sample_source+drain_abort_source+loop_source+main_source)

    print(board,compile_and_run(assemble(),board,0,"exact-source"))
    # Execute the focused pending-identity matrix on the unmutated exact source;
    # mutation-only execution is not a substitute for a green baseline run.
    print(board,compile_and_run(assemble(main_source=PENDING_PRESERVATION_MAIN),
                                board,0,"disabled-intake-pending-identity"))
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
                     main_source=PENDING_PRESERVATION_MAIN),
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
                 main_source=PENDING_PRESERVATION_MAIN),
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
        "bool accepting=pinConfigSafe && controllerEnabled && coinEnabled && relayEnabled && insertMode",
        "bool accepting=pinConfigSafe && controllerEnabled && coinEnabled && insertMode",
        1,
    )
    if relay_gate_mutation == output:
        raise AssertionError(f"{board}: configured relay output gate mutation anchor missing")
    compile_and_run(
        assemble(output_source=relay_gate_mutation,main_source=PENDING_PRESERVATION_MAIN),
        board,80,"disabled-intake-relay-output-gate"
    )
    print(f"{board} MUTATION_REJECTED disabled-intake-relay-output-gate expected_exit=80")
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

run_remote_config_pin_recovery_lab()

print("PHX-HARDWARE: poll-fault and coin-POST ISR reconciliation passed on ESP8266 and ESP32; no hardware evidence")
