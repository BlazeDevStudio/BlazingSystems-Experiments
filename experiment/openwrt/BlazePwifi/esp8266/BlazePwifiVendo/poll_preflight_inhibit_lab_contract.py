"""Source-level contracts for fail-closed startup, register and poll handling in both Vendo sketches."""
import re

__all__ = ["coin_post_matches", "gpio_write_authority_locations", "poll_call_matches", "poll_guard_locations", "register_call_matches", "register_guard_locations"]

from firmware_source_extract import extract_braced, extract_function, mask_non_code


def poll_call_matches(source: str):
    """Find executable post("poll") calls, excluding comments and literals."""
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


def _assert_unconditional_call(
    masked_block: str,
    call_at: int,
    label: str,
    call_text: str,
    expected_depth: int = 1,
) -> int:
    """Require a direct, unconditional standalone call at its expected block depth."""
    depth = masked_block[:call_at].count("{") - masked_block[:call_at].count("}")
    if depth != expected_depth:
        raise AssertionError(
            f"{label}: deny guard must be an unconditional standalone statement"
        )

    boundary = max(
        masked_block.rfind(";", 0, call_at),
        masked_block.rfind("{", 0, call_at),
        masked_block.rfind("}", 0, call_at),
    )
    if masked_block[boundary + 1:call_at].strip():
        raise AssertionError(
            f"{label}: deny guard must be an unconditional standalone statement"
        )

    call_end = call_at + len(call_text)
    semicolon = masked_block.find(";", call_end)
    if semicolon < 0 or masked_block[call_end:semicolon].strip():
        raise AssertionError(
            f"{label}: deny guard must be an unconditional standalone statement"
        )
    return semicolon + 1


def _assert_unconditional_guard(
    masked_block: str, guard_at: int, label: str, expected_depth: int = 1
) -> int:
    return _assert_unconditional_call(
        masked_block, guard_at, label, "denyRemoteControl()", expected_depth
    )


def _assert_no_control_transfer(
    masked_block: str, start: int, end: int, label: str
):
    if re.search(r"\b(?:return|goto|break|continue|throw)\b", masked_block[start:end]):
        raise AssertionError(f"{label}: control transfer can bypass deny guard")


def poll_guard_locations(source: str):
    """Require one deny-only wrapper to own every blocking poll request."""
    loop = extract_function(source, "void loop()")
    masked_loop = mask_non_code(loop)
    if coin_post_matches(loop):
        raise AssertionError("automatic coin POST remains in loop before authenticated receipt contract approval")
    if re.search(r"\bclearPending\s*\(", masked_loop):
        raise AssertionError("pending coin disposition remains active in loop before authenticated receipt contract approval")

    readiness_guard = (
        r"configStoreReady\s*&&\s*"
        if "configStoreReady" in masked_loop
        else r"(?:configStoreReady\s*&&\s*)?"
    )
    condition = re.search(
        r"if\s*\(\s*WiFi\.status\(\)\s*==\s*WL_CONNECTED\s*&&\s*"
        + readiness_guard
        + r"millis\(\)\s*-\s*lastPoll\s*>\s*1500\s*\)",
        masked_loop,
    )
    if not condition:
        raise AssertionError("missing bounded synchronous poll condition")
    brace = masked_loop.find("{", condition.end())
    if brace < 0:
        raise AssertionError("bounded synchronous poll condition has no body")
    poll_block = extract_braced(loop, brace)
    masked_poll_block = mask_non_code(poll_block)

    helper_pattern = re.compile(r"\bpollDenyOnly\s*\(\s*\)\s*;")
    loop_helper_calls = list(helper_pattern.finditer(masked_loop))
    poll_block_helper_calls = list(helper_pattern.finditer(masked_poll_block))
    all_helper_calls = list(helper_pattern.finditer(mask_non_code(source)))
    if (
        len(loop_helper_calls) != 1
        or len(poll_block_helper_calls) != 1
        or len(all_helper_calls) != 1
    ):
        raise AssertionError("pollDenyOnly must be the single poll callsite inside the bounded loop block")

    helper_call = poll_block_helper_calls[0]
    _assert_unconditional_call(
        masked_poll_block, helper_call.start(), "poll wrapper call",
        "pollDenyOnly()", expected_depth=1,
    )

    if poll_call_matches(loop):
        raise AssertionError("synchronous poll request must not be issued directly from loop")
    poll_helper = extract_function(source, "void pollDenyOnly()")
    masked_helper = mask_non_code(poll_helper)
    helper_definitions = re.findall(
        r"\bvoid\s+pollDenyOnly\s*\(\s*\)\s*\{",
        mask_non_code(source),
    )
    if len(helper_definitions) != 1:
        raise AssertionError("pollDenyOnly definition must exist exactly once")

    all_poll_calls = poll_call_matches(source)
    helper_poll_calls = poll_call_matches(poll_helper)
    if len(all_poll_calls) != 1 or len(helper_poll_calls) != 1:
        raise AssertionError("all synchronous poll requests must be owned by pollDenyOnly")

    match = helper_poll_calls[0]
    prefix = masked_helper[max(0, match.start() - 32):match.start()]
    suffix = masked_helper[match.end():]
    if not re.search(r"\(\s*void\s*\)\s*$", prefix):
        raise AssertionError("poll response must be explicitly discarded until authenticated contract approval")
    if not re.match(r"\s*;", suffix):
        raise AssertionError("poll response must not be consumed before post-poll deny")

    if re.search(r"\bapplyRemoteConfig\s*\(", masked_loop + masked_helper):
        raise AssertionError("remote configuration must remain unapplied until authenticated contract approval")

    pre_guard = masked_helper.find("denyRemoteControl();")
    if pre_guard < 0:
        raise AssertionError("coin intake is not denied before blocking poll request 1")
    pre_guard_end = _assert_unconditional_guard(masked_helper, pre_guard, "pre-poll")
    if pre_guard_end > match.start():
        raise AssertionError("pre-poll deny guard overlaps the blocking poll call")
    _assert_no_control_transfer(masked_helper, pre_guard_end, match.start(), "pre-poll")

    post_guard = masked_helper.find("denyRemoteControl();", match.end())
    if post_guard < 0:
        raise AssertionError("post-poll deny guard is missing for request 1")
    post_guard_end = _assert_unconditional_guard(masked_helper, post_guard, "post-poll")
    _assert_no_control_transfer(masked_helper, match.end(), post_guard, "post-poll")

    if not re.search(r"\bwifiFailures\s*=\s*0\s*;", masked_helper[:pre_guard]):
        raise AssertionError("poll wrapper must reset the Wi-Fi failure counter before the request")
    if not re.search(r"\blastPoll\s*=\s*millis\(\)\s*;", masked_helper[post_guard_end:]):
        raise AssertionError("poll wrapper must timestamp completion after the post-poll deny")

    helper_body = extract_braced(poll_helper, masked_helper.find("{"))
    sample = masked_loop.find("digitalRead(runCoinPin)")
    if sample < 0 or sample <= loop_helper_calls[0].start():
        raise AssertionError("coin input sampling moved before/inside the blocking poll sequence")
    return loop, helper_body, pre_guard, match.start(), post_guard


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


def _call_arguments(masked_source, match):
    """Split a simple C++ call argument list while respecting nested parentheses."""
    opening = masked_source.find("(", match.start())
    if opening < 0:
        raise AssertionError("callsite has no opening parenthesis")
    depth = 0
    start = opening + 1
    arguments = []
    for position in range(opening, len(masked_source)):
        character = masked_source[position]
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                arguments.append(masked_source[start:position].strip())
                return tuple(arguments)
        elif character == "," and depth == 1:
            arguments.append(masked_source[start:position].strip())
            start = position + 1
    raise AssertionError("unclosed writeLogical argument list")


def gpio_write_authority_locations(source: str):
    """Keep physical GPIO writes centralized behind the existing deny predicate."""
    masked = mask_non_code(source)
    definitions = list(re.finditer(r"\bvoid\s+writeLogical\s*\(", masked))
    if len(definitions) != 1:
        raise AssertionError("writeLogical must have exactly one implementation")
    definition_name = masked.find("writeLogical", definitions[0].start())

    write_function = extract_function(source, "void writeLogical")
    write_mask = mask_non_code(write_function)
    digital_calls = list(re.finditer(r"\bdigitalWrite\s*\(", masked))
    writer_digital_calls = list(re.finditer(r"\bdigitalWrite\s*\(", write_mask))
    if len(digital_calls) != 1 or len(writer_digital_calls) != 1:
        raise AssertionError("digitalWrite must be centralized in writeLogical")

    configure = extract_function(source, "void configureRuntimePins")
    apply = extract_function(source, "void applyOutputs()")
    configure_mask = mask_non_code(configure)
    apply_mask = mask_non_code(apply)
    configure_calls = list(re.finditer(r"\bwriteLogical\s*\(", configure_mask))
    apply_calls = list(re.finditer(r"\bwriteLogical\s*\(", apply_mask))
    all_calls = [
        match for match in re.finditer(r"\bwriteLogical\s*\(", masked)
        if match.start() != definition_name
    ]

    if len(configure_calls) != 6 or len(apply_calls) != 4:
        raise AssertionError(
            "writeLogical callsites must remain limited to six startup OFF writes "
            "and four applyOutputs gate writes"
        )
    if len(all_calls) != len(configure_calls) + len(apply_calls):
        raise AssertionError(
            "writeLogical calls must be limited to configureRuntimePins and applyOutputs"
        )

    for call in configure_calls:
        arguments = _call_arguments(configure_mask, call)
        if len(arguments) != 3 or arguments[1] != "false":
            raise AssertionError("configureRuntimePins may only write logical OFF")

    actual_apply = sorted(_call_arguments(apply_mask, call) for call in apply_calls)
    expected_apply = sorted((
        ("runLedPin", "accepting", "runLedActiveHigh"),
        ("runLedPin", "false", "runLedActiveHigh"),
        ("runRelayPin", "accepting", "runRelayActiveHigh"),
        ("runRelayPin", "false", "runRelayActiveHigh"),
    ))
    if actual_apply != expected_apply:
        raise AssertionError(
            "applyOutputs must retain the exact accepting-gated GPIO call set"
        )

    return {
        "digital_write_calls": len(digital_calls),
        "startup_off_calls": len(configure_calls),
        "gated_output_calls": len(apply_calls),
    }
