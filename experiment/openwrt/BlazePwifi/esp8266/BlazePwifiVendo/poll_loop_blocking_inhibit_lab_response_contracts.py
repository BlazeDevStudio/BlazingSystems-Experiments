"""Response-denial scenarios for the blocking-poll host regression lab.

These cases deliberately contain no ISR edge during HTTP. They isolate the
consumer response decision from pulse-fault handling and keep active-high and
active-low relay variants in one reviewable matrix. The signature-looking
value is a non-protocol placeholder and is never an authorization vector.
"""

from poll_loop_blocking_inhibit_lab_response_fixtures import (
    POLL_HTTP_KEYLESS_RESPONSE_DENY_MAIN,
    POLL_HTTP_RESPONSE_DENY_NO_EDGE_MAIN,
)


def run_poll_response_denial_matrix(
    *,
    board,
    accept,
    support,
    timeout_response_anchor,
    timeout_support,
    compile_and_run,
    assemble,
    with_active_low_relay,
    loop,
    output,
):
    """Run no-edge response denial and fail-open mutations for one board."""
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
        ("hostile-positive", support),
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
    keyless_response_support = support.replace(
        timeout_response_anchor,
        r'    return String("{\"ok\":true,\"insert\":true,\"target\":\"spoof-target\",\"response_sig\":\"unapproved-test-only\"}");',
        1,
    )
    if keyless_response_support == support:
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

