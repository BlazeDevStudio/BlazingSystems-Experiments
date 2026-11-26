"""Source-level contracts for fail-closed poll handling in both Vendo sketches."""
import re

__all__ = ["coin_post_matches", "poll_call_matches", "poll_guard_locations", "register_call_matches", "register_guard_locations"]

from firmware_source_extract import extract_braced, extract_function, mask_non_code

def poll_call_matches(source: str):
    # Match the literal argument in source, but accept it only when the call
    # identifier itself is code rather than a comment/string decoy.
    pattern = re.compile(r'\bpost\s*\(\s*"poll"\s*\)')
    masked = mask_non_code(source)
    return [
        match for match in pattern.finditer(source)
        if masked[match.start():match.start() + 4] == "post"
    ]

def coin_post_matches(source: str):
    pattern = re.compile(r'\bpost\s*\(\s*"coin"')
    masked = mask_non_code(source)
    return [
        match for match in pattern.finditer(source)
        if masked[match.start():match.start() + 4] == "post"
    ]

def _assert_unconditional_guard(
    masked_block: str, guard_at: int, label: str, expected_depth: int = 1
) -> int:
    """Require a direct, unconditional deny statement at its expected block depth."""
    depth = masked_block[:guard_at].count("{") - masked_block[:guard_at].count("}")
    if depth != expected_depth:
        raise AssertionError(
            f"{label}: deny guard must be an unconditional standalone statement"
        )

    boundary = max(
        masked_block.rfind(";", 0, guard_at),
        masked_block.rfind("{", 0, guard_at),
        masked_block.rfind("}", 0, guard_at),
    )
    if masked_block[boundary + 1:guard_at].strip():
        raise AssertionError(
            f"{label}: deny guard must be an unconditional standalone statement"
        )

    call_end = guard_at + len("denyRemoteControl()")
    semicolon = masked_block.find(";", call_end)
    if semicolon < 0 or masked_block[call_end:semicolon].strip():
        raise AssertionError(
            f"{label}: deny guard must be an unconditional standalone statement"
        )
    return semicolon + 1

def _assert_no_control_transfer(
    masked_block: str, start: int, end: int, label: str
):
    if re.search(r"\b(?:return|goto|break|continue|throw)\b", masked_block[start:end]):
        raise AssertionError(f"{label}: control transfer can bypass deny guard")

def poll_guard_locations(source: str):
    loop = extract_function(source, "void loop()")
    masked_loop = mask_non_code(loop)
    if coin_post_matches(loop):
        raise AssertionError("automatic coin POST remains in loop before authenticated receipt contract approval")
    if re.search(r"\bclearPending\s*\(", masked_loop):
        raise AssertionError("pending coin disposition remains active in loop before authenticated receipt contract approval")
    condition = re.search(
        r"if\s*\(\s*WiFi\.status\(\)\s*==\s*WL_CONNECTED\s*&&\s*"
        r"millis\(\)\s*-\s*lastPoll\s*>\s*1500\s*\)",
        masked_loop,
    )
    if not condition:
        raise AssertionError("missing bounded synchronous poll condition")
    brace = masked_loop.find("{", condition.end())
    poll_block = extract_braced(loop, brace)
    masked_poll_block = mask_non_code(poll_block)
    loop_poll_matches = poll_call_matches(loop)
    poll_matches = poll_call_matches(poll_block)
    if len(loop_poll_matches) != len(poll_matches):
        raise AssertionError("synchronous poll request exists outside the bounded guarded block")
    if not poll_matches:
        raise AssertionError("missing synchronous poll request")

    # Until CORE publishes an authenticated poll/configuration contract, the
    # response must be explicitly discarded and no remote config may be applied
    # anywhere in this loop. This closes a transient relay-enable window between
    # the pre-poll and post-poll deny calls.
    for match in poll_matches:
        prefix = masked_poll_block[max(0, match.start() - 32):match.start()]
        suffix = masked_poll_block[match.end():]
        if not re.search(r"\(\s*void\s*\)\s*$", prefix):
            raise AssertionError("poll response must be explicitly discarded until authenticated contract approval")
        if not re.match(r"\s*;", suffix):
            raise AssertionError("poll response must not be consumed before post-poll deny")
    if re.search(r"\bapplyRemoteConfig\s*\(", masked_loop):
        raise AssertionError("remote configuration must remain unapplied until authenticated contract approval")

    first_pre_guard = -1
    last_post_guard = -1
    for index, match in enumerate(poll_matches):
        previous_end = 0 if index == 0 else poll_matches[index - 1].end()
        next_start = (
            poll_matches[index + 1].start()
            if index + 1 < len(poll_matches)
            else len(poll_block)
        )
        pre_guard = masked_poll_block.rfind(
            "denyRemoteControl();", previous_end, match.start()
        )
        if pre_guard < 0:
            raise AssertionError(
                f"coin intake is not denied before blocking poll request {index + 1}"
            )
        pre_guard_end = _assert_unconditional_guard(
            masked_poll_block, pre_guard, "pre-poll"
        )
        if pre_guard_end > match.start():
            raise AssertionError("pre-poll deny guard overlaps the blocking poll call")
        _assert_no_control_transfer(
            masked_poll_block, pre_guard_end, match.start(), "pre-poll"
        )

        post_guard = masked_poll_block.find(
            "denyRemoteControl();", match.end(), next_start
        )
        if post_guard < 0:
            raise AssertionError(
                f"post-poll deny guard is missing for request {index + 1}"
            )
        _assert_unconditional_guard(masked_poll_block, post_guard, "post-poll")
        _assert_no_control_transfer(
            masked_poll_block, match.end(), post_guard, "post-poll"
        )
        if index == 0:
            first_pre_guard = pre_guard
        last_post_guard = post_guard

    global_last_poll = brace + poll_matches[-1].start()
    sample = masked_loop.find("digitalRead(runCoinPin)")
    if sample < 0 or sample <= global_last_poll:
        raise AssertionError(
            "coin input sampling moved before/inside the blocking poll sequence"
        )
    return loop, poll_block, first_pre_guard, poll_matches[0].start(), last_post_guard


def register_call_matches(source: str):
    """Find executable register POST calls, excluding comments and literals."""
    pattern = re.compile(r'\bpost\s*\(\s*"register"\s*\)')
    masked = mask_non_code(source)
    return [
        match for match in pattern.finditer(source)
        if masked[match.start():match.start() + 4] == "post"
    ]


def register_guard_locations(source: str):
    """Require startup and post-register deny guards before any response consumer."""
    setup = extract_function(source, "void setup()")
    connect = extract_function(source, "void connectSta()")
    masked_setup = mask_non_code(setup)
    masked_connect = mask_non_code(connect)

    all_register = register_call_matches(source)
    connect_register = register_call_matches(connect)
    if len(all_register) != 1 or len(connect_register) != 1:
        raise AssertionError(
            "register POST must exist exactly once, inside connectSta()"
        )

    register = connect_register[0]
    prefix = masked_connect[max(0, register.start() - 32):register.start()]
    suffix = masked_connect[register.end():]
    if not re.search(r"\(\s*void\s*\)\s*$", prefix):
        raise AssertionError(
            "register response must be explicitly discarded until authenticated contract approval"
        )
    if not re.match(r"\s*;", suffix):
        raise AssertionError("register response must not be consumed")

    if re.search(r"\bapplyRemoteConfig\s*\(", masked_connect):
        raise AssertionError(
            "startup register response must not apply remote configuration before authenticated contract approval"
        )

    connected_if = re.search(
        r"if\s*\(\s*WiFi\.status\(\)\s*==\s*WL_CONNECTED\s*\)",
        masked_connect,
    )
    if not connected_if:
        raise AssertionError(
            "register POST must remain inside the Wi-Fi-connected startup branch"
        )
    connected_open = masked_connect.find("{", connected_if.end())
    if connected_open < 0:
        raise AssertionError("Wi-Fi-connected startup branch has no body")
    connected_branch = extract_braced(connect, connected_open)
    connected_end = connected_open + len(connected_branch)
    if not (connected_open < register.start() < connected_end):
        raise AssertionError(
            "register POST must remain inside the Wi-Fi-connected startup branch"
        )

    register_depth = (
        masked_connect[:register.start()].count("{")
        - masked_connect[:register.start()].count("}")
    )
    if register_depth != 2:
        raise AssertionError(
            "register POST must remain inside the connected startup branch"
        )

    post_guard = masked_connect.find("denyRemoteControl();", register.end())
    if post_guard < 0:
        raise AssertionError("post-register deny guard is missing")
    post_end = _assert_unconditional_guard(
        masked_connect, post_guard, "post-register", expected_depth=register_depth
    )
    if post_end <= register.end():
        raise AssertionError("post-register deny guard does not follow register POST")
    _assert_no_control_transfer(
        masked_connect, register.end(), post_guard, "post-register"
    )

    connect_calls = list(re.finditer(r"\bconnectSta\s*\(\s*\)", masked_setup))
    if len(connect_calls) != 1:
        raise AssertionError("setup() must invoke connectSta() exactly once")
    connect_call = connect_calls[0]
    pre_guard = masked_setup.rfind("denyRemoteControl();", 0, connect_call.start())
    if pre_guard < 0:
        raise AssertionError(
            "startup pre-register deny guard is missing before connectSta()"
        )
    pre_end = _assert_unconditional_guard(
        masked_setup, pre_guard, "startup pre-register", expected_depth=1
    )
    if pre_end > connect_call.start():
        raise AssertionError("startup deny guard overlaps connectSta()")
    _assert_no_control_transfer(
        masked_setup, pre_end, connect_call.start(), "startup pre-register"
    )

    if re.search(r"\bapplyRemoteConfig\s*\(", masked_setup):
        raise AssertionError(
            "setup() must not apply unauthenticated register configuration"
        )
    return setup, connect

def startup_storage_guard_locations(source: str):
    """Require configured outputs and the deny latch before LittleFS startup work."""
    setup = extract_function(source, "void setup()")
    masked_setup = mask_non_code(setup)

    config_loads = list(re.finditer(
        r"\b(?:loadCfg|loadConfig)\s*\(\s*\)\s*;",
        masked_setup,
    ))
    pin_initializers = list(re.finditer(
        r"\bconfigureRuntimePins\s*\(",
        masked_setup,
    ))
    deny_guards = list(re.finditer(
        r"\bdenyRemoteControl\s*\(\s*\)\s*;",
        masked_setup,
    ))
    storage_calls = []
    for pattern in (
        r"\binitPendingStore\s*\(\s*\)\s*;",
        r"\bLittleFS\s*\.\s*begin\s*\(",
    ):
        storage_calls.extend(re.finditer(pattern, masked_setup))

    if len(config_loads) != 1:
        raise AssertionError("setup must load persisted pin configuration exactly once")
    if len(pin_initializers) != 1:
        raise AssertionError("setup must configure runtime output pins exactly once")
    if len(deny_guards) != 1:
        raise AssertionError("setup must apply one startup output-deny latch")
    if len(storage_calls) != 1:
        raise AssertionError("setup must have one explicit LittleFS startup entrypoint")

    config_load = config_loads[0]
    pin_init = pin_initializers[0]
    deny = deny_guards[0]
    storage = storage_calls[0]

    pin_depth = (
        masked_setup[:pin_init.start()].count("{")
        - masked_setup[:pin_init.start()].count("}")
    )
    if pin_depth != 1:
        raise AssertionError("runtime output pin initialization must be unconditional")
    deny_end = _assert_unconditional_guard(
        masked_setup, deny.start(), "startup output deny", expected_depth=1
    )
    storage_depth = (
        masked_setup[:storage.start()].count("{")
        - masked_setup[:storage.start()].count("}")
    )
    if storage_depth != 1:
        raise AssertionError("LittleFS startup must remain an unconditional setup step")
    if not (
        config_load.end() <= pin_init.start()
        < deny.start() < deny_end <= storage.start()
    ):
        raise AssertionError(
            "filesystem initialization must follow configured output pins and the startup deny latch"
        )

    return setup

