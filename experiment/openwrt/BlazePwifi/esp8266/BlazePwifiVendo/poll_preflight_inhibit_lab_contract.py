"""Source-level contracts for fail-closed poll handling in both Vendo sketches."""
import re

__all__ = ["coin_post_matches", "poll_guard_locations"]

from firmware_source_extract import extract_braced, extract_function, mask_non_code

def _poll_call_matches(source: str):
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

def _assert_unconditional_guard(masked_block: str, guard_at: int, label: str) -> int:
    """Require a direct, unconditional deny statement at the poll block's top level."""
    depth = masked_block[:guard_at].count("{") - masked_block[:guard_at].count("}")
    if depth != 1:
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
    loop_poll_matches = _poll_call_matches(loop)
    poll_matches = _poll_call_matches(poll_block)
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
