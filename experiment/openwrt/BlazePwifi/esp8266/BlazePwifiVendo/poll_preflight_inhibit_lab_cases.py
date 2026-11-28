"""Board-level source assertions and failure-injection scenarios for poll denial."""
from pathlib import Path
import re

from firmware_source_extract import (
    extract_function,
    has_empty_string_assignment,
    mask_non_code,
)
from poll_preflight_inhibit_lab_contract import (
    coin_post_matches,
    gpio_write_authority_locations,
    poll_guard_locations,
    register_guard_locations,
    startup_storage_guard_locations,
)
from poll_preflight_inhibit_lab_harness import (
    compile_and_run,
    compile_blocking_poll_and_run,
    compile_poll_transport_outcome_matrix,
    expect_poll_guard_mutation_rejected,
    remove_first_code_token,
)

__all__ = ["main", "verify_board", "verify_gpio_write_authority_mutations", "verify_register_preflight", "verify_startup_storage_order", "verify_source_extractor_decoy_regressions"]



BLAZEPWIFI = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": BLAZEPWIFI / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}



def verify_startup_storage_order(name: str, source: str):
    """Require the board's configured outputs to be denied before LittleFS work."""
    setup = startup_storage_guard_locations(source)
    masked_setup = mask_non_code(setup)
    config_load = re.search(
        r"\b(?:loadCfg|loadConfig)\s*\(\s*\)\s*;",
        masked_setup,
    )
    if not config_load:
        raise AssertionError(f"{name}: persisted pin configuration load missing")

    storage_match = re.search(
        r"\binitPendingStore\s*\(\s*\)\s*;"
        r"|\bfsReady\s*=\s*LittleFS\s*\.\s*begin\s*\([^;]*\)\s*;",
        masked_setup,
    )
    if not storage_match:
        raise AssertionError(f"{name}: LittleFS startup entrypoint missing")

    storage_statement = setup[storage_match.start():storage_match.end()]
    without_storage = (
        setup[:storage_match.start()] + setup[storage_match.end():]
    )
    without_mask = mask_non_code(without_storage)
    config_after_removal = re.search(
        r"\b(?:loadCfg|loadConfig)\s*\(\s*\)\s*;",
        without_mask,
    )
    if not config_after_removal:
        raise AssertionError(f"{name}: config load anchor lost during mutation")
    mutated_setup = (
        without_storage[:config_after_removal.end()]
        + "\n  " + storage_statement
        + without_storage[config_after_removal.end():]
    )
    mutated_source = source.replace(setup, mutated_setup, 1)

    try:
        startup_storage_guard_locations(mutated_source)
    except AssertionError as exc:
        expected = "filesystem initialization must follow configured output pins"
        if expected not in str(exc):
            raise AssertionError(
                f"{name}: early-LittleFS mutation failed for the wrong reason: {exc}"
            ) from exc
    else:
        raise AssertionError(
            f"{name}: moving LittleFS startup before the output deny latch was not rejected"
        )

    print(f"STARTUP_OUTPUT_BEFORE_LITTLEFS_PASS {name}")
    print(f"EARLY_LITTLEFS_BEFORE_OUTPUT_DENY_MUTATION_REJECTED {name}")

def verify_register_preflight(name: str, source: str):
    """Protect the deny-only startup register exchange on both controller boards."""
    setup, connect = register_guard_locations(source)

    def expect_rejected(label: str, mutated_source: str, expected: str):
        try:
            register_guard_locations(mutated_source)
        except AssertionError as exc:
            if expected not in str(exc):
                raise AssertionError(
                    f"{name}: {label} failed for the wrong reason: {exc}"
                ) from exc
        else:
            raise AssertionError(f"{name}: {label} mutation was not rejected")

    # The setup-level deny must stay unconditional and precede connectSta().
    mutated_setup = setup.replace("denyRemoteControl();", "", 1)
    if mutated_setup == setup:
        raise AssertionError(f"{name}: startup deny mutation anchor missing")
    expect_rejected(
        "missing startup pre-register deny",
        source.replace(setup, mutated_setup, 1),
        "startup pre-register deny guard is missing",
    )

    mutated_setup = setup.replace(
        "denyRemoteControl();", "if (false) { denyRemoteControl(); }", 1
    )
    expect_rejected(
        "conditional startup pre-register deny",
        source.replace(setup, mutated_setup, 1),
        "startup pre-register: deny guard must be an unconditional standalone statement",
    )

    # A register request must not move outside the actual Wi-Fi-connected branch.
    mutated_connect = connect.replace(
        "WiFi.status()==WL_CONNECTED", "true", 1
    )
    if mutated_connect == connect:
        raise AssertionError(f"{name}: connected-branch mutation anchor missing")
    expect_rejected(
        "register outside Wi-Fi-connected branch",
        source.replace(connect, mutated_connect, 1),
        "register POST must remain inside the Wi-Fi-connected startup branch",
    )

    # Registration must be followed by a direct deny in the connected branch.
    mutated_connect = connect.replace("denyRemoteControl();", "", 1)
    if mutated_connect == connect:
        raise AssertionError(f"{name}: post-register deny mutation anchor missing")
    expect_rejected(
        "missing post-register deny",
        source.replace(connect, mutated_connect, 1),
        "post-register deny guard is missing",
    )

    mutated_connect = connect.replace(
        "denyRemoteControl();", "if (false) { denyRemoteControl(); }", 1
    )
    expect_rejected(
        "conditional post-register deny",
        source.replace(connect, mutated_connect, 1),
        "post-register: deny guard must be an unconditional standalone statement",
    )

    # No startup register response may become a remote actuation/configuration input.
    mutated_connect = connect.replace(
        '(void)post("register");',
        'String response = post("register"); applyRemoteConfig(response);',
        1,
    )
    if mutated_connect == connect:
        raise AssertionError(f"{name}: register response mutation anchor missing")
    expect_rejected(
        "consumed register response",
        source.replace(connect, mutated_connect, 1),
        "register response must be explicitly discarded",
    )

    mutated_connect = connect.replace(
        '(void)post("register");',
        '(void)post("register"); applyRemoteConfig(staleResponse);',
        1,
    )
    expect_rejected(
        "applied register response",
        source.replace(connect, mutated_connect, 1),
        "startup register response must not apply remote configuration",
    )

    # A second executable register POST outside connectSta() must not be hidden.
    loop_at = source.find("void loop()")
    loop_brace = source.find("{", loop_at)
    if loop_at < 0 or loop_brace < 0:
        raise AssertionError(f"{name}: loop() anchor missing for duplicate-register mutation")
    mutated_source = (
        source[:loop_brace + 1]
        + '\n    (void)post("register");'
        + source[loop_brace + 1:]
    )
    expect_rejected(
        "duplicate register POST outside connectSta",
        mutated_source,
        "register POST must exist exactly once",
    )

    # Comment and string decoys must not be counted as executable register POSTs.
    decoy_source = (
        source
        + '\n// post("register");'
        + '\nconst char *registerNote = "post(\\"register\\");";'
    )
    register_guard_locations(decoy_source)

    print(f"REGISTER_STARTUP_DENY_PASS {name}")
    print(f"REGISTER_STARTUP_DENY_MUTATIONS_REJECTED {name} 8/8")
    print(f"REGISTER_POST_RESPONSE_USE_MUTATIONS_REJECTED {name} 2/2")
    print(f"REGISTER_POST_DECOY_MUTATIONS_IGNORED {name}")


def verify_board(name: str, path: Path):
    source = path.read_text(encoding="utf-8")
    masked_source = mask_non_code(source)
    gpio_write_authority_locations(source)
    if len(re.findall(r"clearPending\s*\(", masked_source)) != 1:
        raise AssertionError(f"{name}: clearPending must remain definition-only until authenticated receipt approval")
    if coin_post_matches(source):
        raise AssertionError(f"{name}: automatic coin POST must remain absent from firmware")
    verify_register_preflight(name, source)
    loop, poll_block, pre_guard, poll_at, post_guard = poll_guard_locations(source)
    poll_helper = extract_function(source, "void pollDenyOnly()")
    if not (pre_guard < poll_at < post_guard):
        raise AssertionError(f"{name}: invalid poll guard order")

    apply_fn = extract_function(source, "void applyOutputs()")
    deny_fn = extract_function(source, "void denyRemoteControl()")
    deny_code = mask_non_code(deny_fn)
    apply_code = mask_non_code(apply_fn)
    required = (
        "controllerEnabled=false;",
        "coinEnabled=false;",
        "relayEnabled=false;",
        "insertMode=false;",
        "applyOutputs();",
    )
    for token in required:
        if token not in deny_code:
            raise AssertionError(f"{name}: denyRemoteControl missing {token!r}")
    if not has_empty_string_assignment(deny_fn, "activeTarget"):
        raise AssertionError(f"{name}: denyRemoteControl does not clear active target")
    readiness_guard = "configStoreReady && " if "configStoreReady" in apply_code else ""
    expected_accepting = (
        "bool accepting=" + readiness_guard
        + "controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady;"
    )
    if expected_accepting not in apply_code:
        raise AssertionError(f"{name}: relay acceptance predicate changed unexpectedly")
    if "if(relayEnabled)" not in apply_code or "writeLogical(runRelayPin,false,runRelayActiveHigh)" not in apply_code:
        raise AssertionError(f"{name}: relay-off GPIO branch is not explicit")

    compile_and_run(apply_fn, deny_fn, True, f"{name} safe pre-poll state")
    compile_blocking_poll_and_run(
        apply_fn, deny_fn, poll_block, True, f"{name} actual blocking poll wait"
    )

    compile_poll_transport_outcome_matrix(
        apply_fn, deny_fn, poll_block, True,
        f"{name} poll transport outcome matrix",
    )

    # Failure injection: consume an untrusted positive poll body, briefly
    # re-enable relay/LED outputs, then rely on the final deny. The harness
    # must catch the transient active write even though the final state is OFF.
    response_mutation = poll_block.replace(
        '(void)post("poll");',
        'String response = post("poll");\n'
        '        if (response.find("\\\"insert\\\":true") != std::string::npos) {\n'
        '            controllerEnabled = true;\n'
        '            coinEnabled = true;\n'
        '            relayEnabled = true;\n'
        '            ledEnabled = true;\n'
        '            insertMode = true;\n'
        '            applyOutputs();\n'
        '        }',
        1,
    )
    if response_mutation == poll_block:
        raise AssertionError(f"{name}: untrusted-response actuation mutation anchor missing")
    compile_poll_transport_outcome_matrix(
        apply_fn, deny_fn, response_mutation, False,
        f"{name} transient untrusted-response actuation mutation",
    )

    # Failure injection: a direct relay GPIO write after the final deny must also fail.
    # This bypasses applyOutputs(), so the write-history latch must catch it.
    post_deny_gpio_mutation = poll_block.replace(
        "lastPoll=millis();",
        "writeLogical(runRelayPin,true,runRelayActiveHigh);\n        lastPoll=millis();",
        1,
    )
    if post_deny_gpio_mutation == poll_block:
        raise AssertionError(f"{name}: post-deny direct GPIO mutation anchor missing")
    compile_poll_transport_outcome_matrix(
        apply_fn, deny_fn, post_deny_gpio_mutation, False,
        f"{name} direct relay GPIO re-enable after final post-poll deny",
    )
    print(f"POST_POLL_DENY_DIRECT_GPIO_REENABLE_MUTATION_REJECTED {name}")

    # Failure injection: removing the pre-poll deny must leave an energized
    # relay visible to the 3500 ms wait model and be rejected.
    mutated_poll_block = poll_block.replace("denyRemoteControl();", "", 1)
    if mutated_poll_block == poll_block:
        raise AssertionError(f"{name}: pre-poll deny mutation anchor missing")
    compile_blocking_poll_and_run(
        apply_fn, deny_fn, mutated_poll_block, False,
        f"{name} missing pre-poll deny during blocking wait",
    )

    # Failure injection: logical deny flags alone are insufficient. The
    # physical GPIO OFF write must happen before the blocking HTTP wait.
    mutated_deny_without_gpio_write = deny_fn.replace("applyOutputs();", "", 1)
    if mutated_deny_without_gpio_write == deny_fn:
        raise AssertionError(f"{name}: immediate GPIO write mutation anchor missing")
    compile_blocking_poll_and_run(
        apply_fn, mutated_deny_without_gpio_write, poll_block, False,
        f"{name} deny latch without immediate GPIO OFF write",
    )
    print(f"PREPOLL_GPIO_OFF_WRITE_MUTATION_REJECTED {name}")

    # Failure injection: the relay OFF branch must use relay polarity even
    # when the LED has the opposite active level.
    mutated_apply = apply_fn.replace(
        "writeLogical(runRelayPin,false,runRelayActiveHigh)",
        "writeLogical(runRelayPin,false,runLedActiveHigh)",
        1,
    )
    if mutated_apply == apply_fn:
        raise AssertionError(f"{name}: relay OFF polarity mutation anchor missing")
    compile_blocking_poll_and_run(
        mutated_apply, deny_fn, poll_block, False,
        f"{name} relay OFF borrows LED polarity during blocking wait",
    )

    # Failure injection: the relay OFF path must use relay polarity, not LED
    # polarity. The standalone GPIO harness crosses all four independent
    # relay/LED combinations, including both mismatched-polarity cases.
    mutated_relay_polarity = apply_fn.replace(
        "writeLogical(runRelayPin,false,runRelayActiveHigh)",
        "writeLogical(runRelayPin,false,runLedActiveHigh)",
        1,
    )
    if mutated_relay_polarity == apply_fn:
        raise AssertionError(f"{name}: relay OFF polarity mutation anchor missing")
    compile_and_run(
        mutated_relay_polarity, deny_fn, False,
        f"{name} relay OFF incorrectly borrows LED polarity",
    )

    # The status LED is independent too; its OFF write must not borrow relay polarity.
    mutated_led_polarity = apply_fn.replace(
        "writeLogical(runLedPin,false,runLedActiveHigh)",
        "writeLogical(runLedPin,false,runRelayActiveHigh)",
        1,
    )
    if mutated_led_polarity == apply_fn:
        raise AssertionError(f"{name}: LED OFF polarity mutation anchor missing")
    compile_and_run(
        mutated_led_polarity, deny_fn, False,
        f"{name} LED OFF incorrectly borrows relay polarity",
    )

    # Failure injection: remove all four actuation-deny assignments. The
    # source-extracted GPIO model must detect that the relay stays energized.
    mutated_deny = deny_fn
    for token in ("controllerEnabled=false;", "coinEnabled=false;",
                  "relayEnabled=false;", "insertMode=false;"):
        mutated_deny = remove_first_code_token(mutated_deny, token)
    compile_and_run(apply_fn, mutated_deny, False, f"{name} deny-state mutation")

    # Failure injection: remove the pre-poll guard while retaining the
    # post-poll guard. The source-order assertion must reject this regression.
    mutated_helper = poll_helper.replace("denyRemoteControl();", "", 1)
    if mutated_helper == poll_helper:
        raise AssertionError(f"{name}: pre-poll guard not found for mutation")
    mutated_source = source.replace(poll_helper, mutated_helper, 1)
    try:
        poll_guard_locations(mutated_source)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: missing pre-poll guard mutation was not rejected")


    # Failure injection: a deny call nested under a false condition must not
    # satisfy the pre-poll guard requirement.
    expect_poll_guard_mutation_rejected(
        name, source,
        r"denyRemoteControl\(\);\s*\(void\)post\(\"poll\"\);",
        'if (false) { denyRemoteControl(); }\n    (void)post("poll");',
        "braced conditional pre-poll guard",
        "pre-poll: deny guard must be an unconditional standalone statement",
    )
    expect_poll_guard_mutation_rejected(
        name, source,
        r"denyRemoteControl\(\);\s*\(void\)post\(\"poll\"\);",
        'if (false) denyRemoteControl();\n    (void)post("poll");',
        "unbraced conditional pre-poll guard",
        "pre-poll: deny guard must be an unconditional standalone statement",
    )
    # Failure injection: a conditional post-poll deny or an early return must
    # not allow the blocking poll to bypass the final fail-closed state.
    expect_poll_guard_mutation_rejected(
        name, source,
        r"\(void\)post\(\"poll\"\);\s*denyRemoteControl\(\);",
        '(void)post("poll");\n    if (false) { denyRemoteControl(); }',
        "braced conditional post-poll guard",
        "post-poll: deny guard must be an unconditional standalone statement",
    )
    expect_poll_guard_mutation_rejected(
        name, source,
        r"\(void\)post\(\"poll\"\);\s*denyRemoteControl\(\);",
        '(void)post("poll");\n    if (false) denyRemoteControl();',
        "unbraced conditional post-poll guard",
        "post-poll: deny guard must be an unconditional standalone statement",
    )
    expect_poll_guard_mutation_rejected(
        name, source,
        r"\(void\)post\(\"poll\"\);\s*denyRemoteControl\(\);",
        '(void)post("poll");\n    return;\n    denyRemoteControl();',
        "early return before post-poll guard",
        "post-poll: control transfer can bypass deny guard",
    )

    # Failure injection: a poll request outside the bounded guarded block
    # must be rejected, not hidden by the first guarded site.
    sample_at = mask_non_code(loop).find("digitalRead(runCoinPin)")
    if sample_at < 0:
        raise AssertionError(f"{name}: cannot place unguarded second-poll mutation")
    mutated_loop = loop[:sample_at] + '    post("poll");\n    ' + loop[sample_at:]
    mutated_source = source.replace(loop, mutated_loop, 1)
    try:
        poll_guard_locations(mutated_source)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: unguarded second-poll mutation was not rejected")

    # Failure injection: reintroducing an automatic coin POST must be rejected.
    mutated_loop = loop.replace("delay(2);", 'post("coin");\n    delay(2);', 1)
    mutated_source = source.replace(loop, mutated_loop, 1)
    try:
        poll_guard_locations(mutated_source)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: automatic coin POST mutation was not rejected")

    # Failure injection: clearing a pending event without an authenticated
    # receipt/disposition contract must be rejected.
    mutated_loop = loop.replace("delay(2);", "clearPending();\n    delay(2);", 1)
    mutated_source = source.replace(loop, mutated_loop, 1)
    try:
        poll_guard_locations(mutated_source)
    except AssertionError:
        pass
    else:
        raise AssertionError(f"{name}: pending clear mutation was not rejected")

    print(f"POLL_INTAKE_GUARD_PASS {name}")
    print(f"PENDING_COIN_POST_MUTATION_REJECTED {name}")
    print(f"PENDING_CLEAR_MUTATION_REJECTED {name}")
    print(f"POLL_INTAKE_DENY_MUTATION_REJECTED {name}")
    print(f"POLL_PREPOLL_ORDER_MUTATION_REJECTED {name}")

def verify_source_extractor_decoy_regressions():
    # A source guard must select real definitions, not comments or literals.
    cases = {
        "block-comment decoy": (
            "/* void loop() { fake_poll(); } */\\n"
            "void loop() { actual_poll(); }\\n"
        ),
        "string-literal decoy": (
            'const char *note = "void loop() { quoted_decoy(); }";\\n'
            "void loop() { actual_poll(); }\\n"
        ),
        "raw-string brace": (
            'void loop() { const char *payload = R"tag( } " // /* { )tag"; '
            "actual_poll(); }\\n"
        ),
    }
    for label, source in cases.items():
        try:
            extracted = extract_function(source, "void loop()")
        except AssertionError as exc:
            raise AssertionError(f"{label}: source extractor failed: {exc}") from exc
        if "actual_poll();" not in extracted:
            raise AssertionError(
                f"{label}: source extractor selected a non-code decoy or truncated the function"
            )


    poll_source = r'''
void pollDenyOnly() {
    wifiFailures = 0;
    denyRemoteControl();
    (void)post("poll");
    denyRemoteControl();
    lastPoll = millis();
}
void loop() {
    // post("poll"); denyRemoteControl(); post("coin"); clearPending(true);
    const char *note = "post(\\"poll\\"); post(\\"coin\\"); clearPending(true);";
    if (WiFi.status() == WL_CONNECTED && millis() - lastPoll > 1500) {
        pollDenyOnly();
    }
    digitalRead(runCoinPin);
}
'''
    poll_guard_locations(poll_source)
    # Failure injection: both response consumption and independent remote-config
    # application must be rejected until the authenticated contract is approved.
    unsafe_poll_source = poll_source.replace(
        '    (void)post("poll");',
        '    String response = post("poll");\n    applyRemoteConfig(response);',
    )
    try:
        poll_guard_locations(unsafe_poll_source)
    except AssertionError:
        pass
    else:
        raise AssertionError("poll-response consumption mutation was not rejected")
    unsafe_config_source = poll_source.replace(
        '    (void)post("poll");',
        '    (void)post("poll");\n    applyRemoteConfig(staleResponse);',
    )
    try:
        poll_guard_locations(unsafe_config_source)
    except AssertionError:
        pass
    else:
        raise AssertionError("remote-config application mutation was not rejected")
    print("POLL_RESPONSE_USE_MUTATION_REJECTED")
    print("POLL_REMOTE_CONFIG_MUTATION_REJECTED")
    if not has_empty_string_assignment('void f() { activeTarget = ""; }', "activeTarget"):
        raise AssertionError("empty-target assignment was not recognized")
    if has_empty_string_assignment('void f() { /* activeTarget = ""; */ }', "activeTarget"):
        raise AssertionError("comment-only empty-target decoy was accepted")



def _expect_gpio_writer_mutation_rejected(
    name: str, label: str, mutated_source: str, expected: str
):
    try:
        gpio_write_authority_locations(mutated_source)
    except AssertionError as exc:
        if expected not in str(exc):
            raise AssertionError(
                f"{name}: {label} failed for an unexpected reason: {exc}"
            ) from exc
    else:
        raise AssertionError(f"{name}: {label} mutation was not rejected")


def verify_gpio_write_authority_mutations():
    """Reject direct and alternate GPIO output paths on both board source fixtures."""
    alternative_calls = (
        ("analogWrite", "analogWrite(runRelayPin,255);"),
        ("digitalWriteFast", "digitalWriteFast(runRelayPin,HIGH);"),
        ("ledcWrite", "ledcWrite(0,255);"),
        ("ledcWriteChannel", "ledcWriteChannel(0,255);"),
        ("dacWrite", "dacWrite(runRelayPin,255);"),
        ("gpio_set_level", "gpio_set_level((gpio_num_t)runRelayPin,1);"),
        ("gpio_ll_set_level", "gpio_ll_set_level(&GPIO,runRelayPin,1);"),
        ("gpio_hal_set_level", "gpio_hal_set_level(&GPIO,runRelayPin,1);"),
        ("tone", "tone(runRelayPin,1000);"),
        ("noTone", "noTone(runRelayPin);"),
        ("shiftOut", "shiftOut(runRelayPin,runLedPin,MSBFIRST,0xFF);"),
    )
    register_writes = (
        ("esp8266-gpos", "GPOS = (1U << runRelayPin);"),
        ("esp8266-gpoc", "GPOC = (1U << runRelayPin);"),
        ("esp32-out-w1ts", "GPIO.out_w1ts = (1U << runRelayPin);"),
        ("esp32-out-w1tc", "GPIO.out_w1tc = (1U << runRelayPin);"),
        ("esp8266-gpos-or-assign", "GPOS |= (1U << runRelayPin);"),
        ("esp8266-gpoc-or-assign", "GPOC |= (1U << runRelayPin);"),
        ("esp32-out-w1ts-val", "GPIO.out_w1ts.val = (1U << runRelayPin);"),
        ("esp32-out-w1tc-val", "GPIO.out_w1tc.val = (1U << runRelayPin);"),
        ("esp32-out1-w1ts-val", "GPIO.out1_w1ts.val = (1U << runRelayPin);"),
        ("esp32-out1-w1tc-val", "GPIO.out1_w1tc.val = (1U << runRelayPin);"),
        ("esp32-out-w1ts-or-assign", "GPIO.out_w1ts |= (1U << runRelayPin);"),
        ("esp32-out1-w1tc-or-assign", "GPIO.out1_w1tc |= (1U << runRelayPin);"),
    )
    rejected = 0

    for name, path in SKETCHES.items():
        source = path.read_text(encoding="utf-8")
        gpio_write_authority_locations(source)

        existing_mutations = (
            (
                "direct-logical-writer",
                source.replace(
                    "void denyRemoteControl(){",
                    "void denyRemoteControl(){\n  writeLogical(runRelayPin,true,runRelayActiveHigh);",
                    1,
                ),
                "writeLogical calls must be limited to configureRuntimePins and applyOutputs",
            ),
            (
                "raw-digital-write",
                source.replace(
                    "void denyRemoteControl(){",
                    "void denyRemoteControl(){\n  digitalWrite(runRelayPin,HIGH);",
                    1,
                ),
                "digitalWrite must be centralized in writeLogical",
            ),
            (
                "startup-on-write",
                source.replace(
                    "writeLogical(runRelayPin,false,runRelayActiveHigh);",
                    "writeLogical(runRelayPin,true,runRelayActiveHigh);",
                    1,
                ),
                "configureRuntimePins may only write logical OFF",
            ),
            (
                "ungated-output",
                source.replace(
                    "writeLogical(runRelayPin,accepting,runRelayActiveHigh)",
                    "writeLogical(runRelayPin,true,runRelayActiveHigh)",
                    1,
                ),
                "applyOutputs must retain the exact accepting-gated GPIO call set",
            ),
        )
        for label, mutated, expected in existing_mutations:
            if mutated == source:
                raise AssertionError(f"{name}: {label} mutation anchor missing")
            _expect_gpio_writer_mutation_rejected(name, label, mutated, expected)
            rejected += 1
            print(f"GPIO_WRITE_AUTHORITY_MUTATION_REJECTED {name} {label}")

        for label, statement in alternative_calls:
            mutated = source.replace(
                "void denyRemoteControl(){",
                "void denyRemoteControl(){\n  " + statement,
                1,
            )
            if mutated == source:
                raise AssertionError(f"{name}: {label} mutation anchor missing")
            _expect_gpio_writer_mutation_rejected(
                name,
                label,
                mutated,
                f"alternative GPIO writer API '{label}' must remain absent",
            )
            rejected += 1
            print(f"GPIO_WRITE_BYPASS_MUTATION_REJECTED {name} {label}")

        for label, statement in register_writes:
            mutated = source.replace(
                "void denyRemoteControl(){",
                "void denyRemoteControl(){\n  " + statement,
                1,
            )
            if mutated == source:
                raise AssertionError(f"{name}: {label} mutation anchor missing")
            _expect_gpio_writer_mutation_rejected(
                name,
                label,
                mutated,
                "direct GPIO output register writes must remain absent",
            )
            rejected += 1
            print(f"GPIO_WRITE_REGISTER_MUTATION_REJECTED {name} {label}")

        # Comments and string literals must not create false-positive bypasses.
        decoy_source = (
            source
            + "\n// analogWrite(runRelayPin,255); GPOS = (1U << runRelayPin);"
            + '\nconst char *gpioWriterDecoy = "ledcWrite(0,255); GPIO.out_w1ts = BIT(runRelayPin);";'
        )
        gpio_write_authority_locations(decoy_source)
        print(f"GPIO_WRITE_BYPASS_COMMENT_STRING_DECOYS_IGNORED {name}")

    print(f"GPIO_WRITE_AUTHORITY_MUTATIONS_REJECTED={rejected}")
    if rejected != 54:
        raise AssertionError(f"expected 54 GPIO writer mutations, got {rejected}")

def main():
    startup_failures = []
    for name, path in SKETCHES.items():
        if not path.is_file():
            raise SystemExit(f"missing sketch: {path}")
        try:
            verify_startup_storage_order(name, path.read_text(encoding="utf-8"))
        except AssertionError as exc:
            startup_failures.append(f"{name}: {exc}")
    if startup_failures:
        raise AssertionError("STARTUP_OUTPUT_ORDER_RED: " + " | ".join(startup_failures))

    verify_source_extractor_decoy_regressions()
    verify_gpio_write_authority_mutations()
    for name, path in SKETCHES.items():
        verify_board(name, path)
    print("POLL_INTAKE_GUARD_SIMULATED_ONLY=1")
    print("PHYSICAL_COIN_RELAY_ACCEPTANCE=0")
    print("PHYSICAL_POWER_CUT_ACCEPTANCE=0")


if __name__ == "__main__":
    main()
