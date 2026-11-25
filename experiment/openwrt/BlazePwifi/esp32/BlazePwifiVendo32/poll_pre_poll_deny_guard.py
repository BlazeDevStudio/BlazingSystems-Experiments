#!/usr/bin/env python3
"""Guard the fail-closed intake boundary around synchronous controller polling.

This is a source-structure regression guard for the two production sketches. It
does not simulate a physical coin acceptor, relay contact, or power interruption.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
BOARDS = {
    "ESP8266": ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}
POLL_IF = "if(WiFi.status()==WL_CONNECTED && millis()-lastPoll>1500)"
POLL_POST = '(void)post("poll");'


def braced_body(source: str, opening: int, label: str) -> str:
    if opening < 0 or source[opening] != "{":
        raise ValueError(f"{label}: opening brace not found")
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    i = opening
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
        elif ch == "/" and nxt == "/":
            line_comment = True
            i += 1
        elif ch == "/" and nxt == "*":
            block_comment = True
            i += 1
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:i]
        i += 1
    raise ValueError(f"{label}: unclosed brace")


def function_body(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise ValueError(f"missing function {signature}")
    opening = source.find("{", start + len(signature))
    return braced_body(source, opening, signature)


def contract_errors(source: str) -> list[str]:
    errors = []
    try:
        loop = function_body(source, "void loop()")
        poll_start = loop.find(POLL_IF)
        if poll_start < 0:
            return ["poll scheduling block missing"]
        poll_open = loop.find("{", poll_start + len(POLL_IF))
        poll = braced_body(loop, poll_open, "poll scheduling block")
        post_pos = poll.find(POLL_POST)
        if post_pos < 0:
            errors.append("synchronous poll POST missing")
        else:
            before = poll.rfind("denyRemoteControl();", 0, post_pos)
            after = poll.find("denyRemoteControl();", post_pos + len(POLL_POST))
            if before < 0:
                errors.append("pre-poll deny missing")
            if after < 0:
                errors.append("post-poll deny missing")
        deny = function_body(source, "void denyRemoteControl()")
        for token in (
            "controllerEnabled=false;",
            "coinEnabled=false;",
            "relayEnabled=false;",
            "ledEnabled=false;",
            "insertMode=false;",
            'activeTarget="";',
            "applyOutputs();",
        ):
            if token not in deny:
                errors.append(f"deny helper missing {token}")
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def replace_once(source: str, old: str, new: str) -> str:
    if old not in source:
        raise ValueError(f"mutation anchor missing: {old!r}")
    return source.replace(old, new, 1)


def main() -> int:
    sources = {}
    for board, path in BOARDS.items():
        if not path.is_file():
            print(f"POLL_PRE_POLL_DENY_RED board={board} reason=source_missing path={path}")
            return 1
        source = path.read_text(encoding="utf-8")
        sources[board] = source
        errors = contract_errors(source)
        if errors:
            print(f"POLL_PRE_POLL_DENY_RED board={board} reason={' ; '.join(errors)}")
            return 1
        print(f"POLL_PRE_POLL_DENY_BASELINE_PASS board={board}")

    mutations = (
        (
            "pre_poll_call_removed",
            '    denyRemoteControl();\n    // Current main poll replies',
            '    // Current main poll replies',
        ),
        (
            "relay_disable_removed",
            "  relayEnabled=false;\n",
            "",
        ),
        (
            "output_application_removed",
            "  applyOutputs();\n}\n\nvoid startSetupAp()",
            "}\n\nvoid startSetupAp()",
        ),
        (
            "insert_mode_disable_removed",
            "  insertMode=false;\n",
            "",
        ),
    )
    for board, source in sources.items():
        for name, old, new in mutations:
            try:
                mutated = replace_once(source, old, new)
            except ValueError as exc:
                print(f"POLL_PRE_POLL_DENY_MUTATION_FIXTURE_ERROR board={board} mutation={name} detail={exc}")
                return 2
            if not contract_errors(mutated):
                print(f"POLL_PRE_POLL_DENY_FAILOPEN_MUTATION_SURVIVED board={board} mutation={name}")
                return 1
            print(f"POLL_PRE_POLL_DENY_MUTATION_REJECTED board={board} mutation={name}")

    print("POLL_PRE_POLL_DENY_GUARD_PASS boards=2 mutations=8")
    print("SIMULATED_ONLY=1 PHYSICAL_COIN_ACCEPTANCE=0 PHYSICAL_RELAY_ACCEPTANCE=0 POWER_CUT_ACCEPTANCE=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
