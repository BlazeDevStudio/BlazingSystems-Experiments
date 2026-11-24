#!/usr/bin/env python3
"""Source-exact host lab for fail-closed ESP poll-response handling.

Compiles the production poll-status parser, acceptPollResponse(), and applyOutputs() functions from both board sketches. This is simulated control-flow evidence only.
"""
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from firmware_lab_source import extract_function as _extract_function, mask_active_cpp_code, mask_non_code

import poll_response_failclosed_lab_structure_guard  # noqa: F401
from poll_json_array_primitive_lab import verify as verify_json_array_primitive_delimiters
from poll_response_failclosed_lab_fixtures import (
    STUBS,
    MAIN,
    WINDOW_STUBS,
    WINDOW_MAIN,
)

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

def extract(source, name):
    try:
        return _extract_function(source, name)
    except RuntimeError as exc:
        raise AssertionError(str(exc)) from exc


def verify_lexical_extractor():
    fixture = r'''
void lexicalFixture() {
  const char *ordinary = "}";
  const char *raw = R"PHX({ raw brace })PHX";
  /* } in a block comment */
  if (ordinary[0] == '}') { return; }
}
'''
    extracted = extract(fixture, "lexicalFixture")
    if "if (ordinary[0] == '}') { return; }" not in extracted:
        raise AssertionError(
            "source extractor truncated a C++ literal/comment fixture"
        )
    if extracted.count("return;") != 1 or not extracted.rstrip().endswith("}"):
        raise AssertionError("source extractor returned an incomplete function")
    print("POLL_RESPONSE_LEXICAL_EXTRACTOR_PASS")


def verify_spliced_raw_string_prefix():
    fixtures = (
        ("R-quote", r'''
void splicedRawStringFixture() {
  const char *raw = R\
"PHX(
    "quoted } // not a comment"
    }
)PHX";
  if (true) { return; }
}
'''),
        ("u8-R", r'''
void splicedRawStringFixture() {
  const char *raw = u8\
R"PHX(
    "quoted } // not a comment"
    }
)PHX";
  if (true) { return; }
}
'''),
    )
    for label, fixture in fixtures:
        extracted = extract(fixture, "splicedRawStringFixture")
        if "if (true) { return; }" not in extracted:
            raise AssertionError(
                f"{label}: source extractor truncated a raw string whose prefix "
                "is joined by C++ phase-2 splicing"
            )
        if extracted.count("return;") != 1 or not extracted.rstrip().endswith("}"):
            raise AssertionError(f"{label}: source extractor returned an incomplete function")
        masked = mask_non_code(fixture)
        if "quoted }" in masked or "PHX(" in masked:
            raise AssertionError(f"{label}: raw-string body or delimiter remained visible")
        if label == "u8-R" and "u8" in masked:
            raise AssertionError("encoding prefix was not masked with the raw string")
    print("FIRMWARE_LAB_PHASE2_SPLICED_RAW_PREFIX_PASS 2/2")


def verify_debounce_clamp_callsite_count(source, board, minimum_calls):
    count = mask_active_cpp_code(source).count("boundedCoinDebounceMs(")
    if count < minimum_calls:
        raise RuntimeError(
            f"{board}: not all debounce configuration paths use the 20 ms clamp "
            f"({count} < {minimum_calls})"
        )
    return count


def verify_debounce_clamp_callsite_decoys(source, board, minimum_calls):
    marker = "runDebounceMs=boundedCoinDebounceMs("
    if source.count(marker) != 1:
        raise RuntimeError(f"{board}: expected one shared run-debounce callsite anchor")
    without_call = source.replace(marker, "runDebounceMs=(uint16_t)", 1)
    comment_mutant = without_call.replace(
        "runDebounceMs=(uint16_t)",
        "// boundedCoinDebounceMs(...) decoy\\n  runDebounceMs=(uint16_t)",
        1,
    )
    string_mutant = without_call.replace(
        "runDebounceMs=(uint16_t)",
        'static const char *phxDebounceDecoy = "boundedCoinDebounceMs(";\\n  runDebounceMs=(uint16_t)',
        1,
    )
    survivors = []
    for label, mutant in (("comment", comment_mutant), ("string", string_mutant)):
        try:
            verify_debounce_clamp_callsite_count(mutant, board, minimum_calls)
        except RuntimeError:
            continue
        survivors.append(label)
    if survivors:
        raise SystemExit(
            "POLL_RESPONSE_DEBOUNCE_CALLSITE_DECOY_SURVIVED: "
            + board + ":" + ",".join(survivors)
        )
    inactive_decoys = (
        "#if 0\n"
        + "\n".join(
            "runDebounceMs=boundedCoinDebounceMs(40);"
            for _ in range(minimum_calls)
        )
        + "\n#endif\n"
    )
    legacy_inactive_count = mask_non_code(inactive_decoys).count("boundedCoinDebounceMs(")
    if legacy_inactive_count != minimum_calls:
        raise AssertionError(
            f"{board}: legacy mask did not expose all inactive debounce decoys "
            f"({legacy_inactive_count} != {minimum_calls})"
        )
    try:
        verify_debounce_clamp_callsite_count(inactive_decoys, board, minimum_calls)
    except RuntimeError:
        pass
    else:
        raise SystemExit(
            f"{board}: POLL_RESPONSE_DEBOUNCE_INACTIVE_BRANCH_DECOY_SURVIVED"
        )
    print(
        f"{board}: POLL_RESPONSE_DEBOUNCE_INACTIVE_BRANCH_DECOY_REJECTED "
        f"{minimum_calls}/{minimum_calls}"
    )
    branch_chain_decoys = (
        "#if PHX_UNKNOWN\n"
        "runDebounceMs=boundedCoinDebounceMs(30);\n"
        "#elif 1\n"
        "runDebounceMs=boundedCoinDebounceMs(40);\n"
        "#else\n"
        "runDebounceMs=boundedCoinDebounceMs(50);\n"
        "#endif\n"
    )
    branch_chain_mask = mask_active_cpp_code(branch_chain_decoys)
    if branch_chain_mask.count("boundedCoinDebounceMs(") != 2:
        raise SystemExit(
            f"{board}: POLL_RESPONSE_DEBOUNCE_INACTIVE_ELSE_BRANCH_DECOY_SURVIVED"
        )
    print(f"{board}: POLL_RESPONSE_DEBOUNCE_ELIF_CHAIN_REJECTED 1/1")
    print(f"{board}: POLL_RESPONSE_DEBOUNCE_CALLSITE_DECOY_REJECTED 2/2")


verify_lexical_extractor()
verify_spliced_raw_string_prefix()


failed=[]
for board,path in BOARDS.items():
    source=path.read_text(encoding="utf-8")
    loop=extract(source,"loop")
    poll_start=loop.index("const uint32_t pollEdgeStart=snapshotCoinEdgeSequence()")
    begin_poll=loop.index("const bool pollWindowReady=beginPollWindow()",poll_start)
    drain_snapshot=loop.index("const uint32_t pollEdgeAfterDrain=snapshotCoinEdgeSequence()",begin_poll)
    pre_poll_guard=loop.index("if(pollEdgeAfterDrain!=pollEdgeStart)",drain_snapshot)
    assert poll_start < begin_poll < drain_snapshot < pre_poll_guard, board+": drain ISR reconciliation must follow both helper outcomes"
    pre_poll_latch=loop.index("latchPollPulseFault(pollEdgeAfterDrain-pollEdgeStart)",pre_poll_guard)
    pre_poll_release=loop.index("pollIntakeSuspended=false",pre_poll_latch)
    poll_call=loop.index('String r=post("poll")')
    accept=loop.index("acceptPollResponse(r)",poll_call)
    post_release=loop.index("pollIntakeSuspended=false",accept)
    outputs=loop.index("applyOutputs();",post_release)
    last_poll=loop.index("lastPoll=millis()",outputs)
    assert pre_poll_guard < pre_poll_latch < pre_poll_release < poll_call < accept < post_release < outputs < last_poll, board+": poll release ordering changed"
    parser="\n".join(extract(source,name) for name in ("pollJsonSpace","pollJsonHex","pollJsonSkipString","pollJsonSkipComposite","pollJsonSkipPrimitive","pollJsonSkipValue","pollJsonTopLevelTrue","coinPostDispositionVerified"))
    code=("#define TARGET_ESP32\n" if board=="ESP32" else "")+STUBS+parser+extract(source,"acceptPollResponse")+extract(source,"coinIngressConfigurationAllows")+extract(source,"applyOutputs")+MAIN
    with tempfile.TemporaryDirectory(prefix="phx-poll-response-") as folder:
        cpp=Path(folder)/"test.cpp"; binary=Path(folder)/"test"
        cpp.write_text(code,encoding="utf-8")
        built=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-Wno-unused-parameter",str(cpp),"-o",str(binary)],capture_output=True,text=True,timeout=30)
        if built.returncode:
            print(board,"COMPILE FAIL",built.stderr[-2000:]); failed.append(board); continue
        ran=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        print(board,"PASS" if ran.returncode==0 else "FAIL",ran.stdout.strip(),ran.stderr.strip())
        if ran.returncode: failed.append(board)
        coin_post = loop.find('String r=post("coin"')
        if coin_post < 0:
            print(board, "COIN_POST_ACK_GUARD RED: missing production coin POST")
            failed.append(board)
        else:
            coin_branch = loop[coin_post:]
            handler_call = coin_branch.find("handleCoinPostResponse(r);")
            if handler_call < 0:
                print(board, "COIN_POST_DISPOSITION RED: loop does not delegate to source-extracted disposition helper")
                failed.append(board)
            elif "clearPending();" in coin_branch or "quarantinePending(" in coin_branch:
                print(board, "COIN_POST_DISPOSITION RED: loop retains inline journal disposition bypass")
                failed.append(board)
            else:
                handler = extract(source, "handleCoinPostResponse")
                auth_guard = handler.find("if(!coinPostDispositionVerified(response,pendingNonce,pendingTarget,pendingPulses))")
                coin_success = handler.find('if(pollJsonTopLevelTrue(response,"ok"))')
                clear_pending = handler.find("clearPending();")
                quarantine = handler.find("quarantinePending(response);")
                if auth_guard < 0 or (clear_pending >= 0 and clear_pending < auth_guard) or (quarantine >= 0 and quarantine < auth_guard):
                    print(board, "COIN_POST_DISPOSITION RED: no authenticated-disposition deny guard before journal disposition")
                    failed.append(board)
                elif coin_success < auth_guard or clear_pending < coin_success:
                    print(board, "COIN_POST_DISPOSITION RED: positive ACK path is not ordered after the deny guard")
                    failed.append(board)
                elif handler.find("response.indexOf(", 0, clear_pending) >= 0:
                    print(board, "COIN_POST_DISPOSITION RED: substring-based success check remains before clearPending")
                    failed.append(board)
                else:
                    print(board, "COIN_POST_DISPOSITION PASS: source-extracted helper gates clear/quarantine")
if failed: sys.exit("poll-response fail-closed lab failed: "+",".join(failed))
print("PHYSICAL_COIN_ACCEPTOR_VERIFIED=0")
print("PRODUCTION_FINANCIAL_AUTHORIZED=0")


# PHX-HARDWARE pulse-window and debounce-floor regression.
# This compiles the actual clamp, line-state, poll-window and output-gate functions
# from both sketches. It is host simulation, not electrical or coin-acceptor proof.
for board, path in BOARDS.items():
    source = path.read_text(encoding="utf-8")
    minimum_calls = 2 if board == "ESP8266" else 4
    verify_debounce_clamp_callsite_count(source, board, minimum_calls)
    verify_debounce_clamp_callsite_decoys(source, board, minimum_calls)
    loop = extract(source, "loop")
    begin = loop.find("beginPollWindow()")
    pre_poll_guard = loop.find("if(pollEdgeAfterDrain!=pollEdgeStart)")
    pre_poll_latch = loop.find("latchPollPulseFault(pollEdgeAfterDrain-pollEdgeStart)", pre_poll_guard)
    pre_poll_release = loop.find("pollIntakeSuspended=false", pre_poll_latch)
    poll_call = loop.find('String r=post("poll")')
    response_accept = loop.find("acceptPollResponse(r)", poll_call)
    response_release = loop.find("pollIntakeSuspended=false", response_accept)
    order = [begin, pre_poll_guard, pre_poll_latch, pre_poll_release, poll_call, response_accept, response_release]
    if any(pos < 0 for pos in order) or order != sorted(order):
        raise RuntimeError(f"{board}: pre-poll abort / response / release ordering changed: {order}")
    functions = "\n".join([
        extract(source, "boundedCoinDebounceMs"),
        extract(source, "coinIngressConfigurationAllows"),
        extract(source, "applyOutputs"),
        extract(source, "coinLineIdle"),
        extract(source, "canStartPoll"),
        extract(source, "coinLineQuietAfterInhibit"),
        extract(source, "beginPollWindow"),
    ])
    code = WINDOW_STUBS + functions + WINDOW_MAIN
    with tempfile.TemporaryDirectory(prefix="phx-poll-window-") as folder:
        cpp = Path(folder) / "poll_window.cpp"
        binary = Path(folder) / "poll_window"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            raise RuntimeError(f"{board}: poll-window compile failed:\n{built.stderr[-3000:]}")
        ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
        if ran.returncode:
            raise RuntimeError(f"{board}: poll-window scenarios failed ({ran.returncode}): {ran.stderr}")
        print(f"{board}: {ran.stdout.strip()}; source ordering PASS")

    # Failure injection: removing the final idle sample must be caught by the
    # pulse that begins exactly at the 250 ms quiet boundary.
    quiet = extract(source, "coinLineQuietAfterInhibit")
    if quiet.count("const bool idle=coinLineIdle();") != 1:
        raise RuntimeError(f"{board}: expected one final idle sample to mutate")
    mutated_quiet = quiet.replace("const bool idle=coinLineIdle();", "const bool idle=true;", 1)
    mutated_functions = "\n".join([
        extract(source, "boundedCoinDebounceMs"),
        extract(source, "coinIngressConfigurationAllows"),
        extract(source, "applyOutputs"),
        extract(source, "coinLineIdle"),
        extract(source, "canStartPoll"),
        mutated_quiet,
        extract(source, "beginPollWindow"),
    ])
    mutated_code = WINDOW_STUBS + mutated_functions + WINDOW_MAIN
    with tempfile.TemporaryDirectory(prefix="phx-poll-window-mutation-") as folder:
        cpp = Path(folder) / "poll_window_mutated.cpp"
        binary = Path(folder) / "poll_window_mutated"
        cpp.write_text(mutated_code, encoding="utf-8")
        built = subprocess.run(
            [ "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
              "-Wno-unused-parameter", str(cpp), "-o", str(binary) ],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            raise RuntimeError(f"{board}: mutated poll-window compile failed:\n{built.stderr[-3000:]}")
        mutated = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
        if mutated.returncode != 25:
            raise RuntimeError(
                f"{board}: remove-final-quiet-sample mutation was not rejected at exact-boundary case 25; "
                f"exit={mutated.returncode}; stdout={mutated.stdout}; stderr={mutated.stderr}"
            )
        print(f"{board}: MUTATION_REJECTED remove-final-quiet-sample (exit=25)")

verify_json_array_primitive_delimiters(BOARDS, extract, STUBS)
