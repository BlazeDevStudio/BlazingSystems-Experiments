#!/usr/bin/env python3
"""Static guard against impossible time travel in the poll-window host fixture.

The C++ timeline payload lives in poll_response_failclosed_lab_fixtures.py;
the Python runner only imports and executes it. This guard follows that
boundary and separately checks the runner's failure-injection wiring.
This is a regression check for the test harness, not hardware evidence.
"""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "poll_response_failclosed_lab.py"
FIXTURE_PATH = HERE / "poll_response_failclosed_lab_fixtures.py"

runner = RUNNER_PATH.read_text(encoding="utf-8")
if not FIXTURE_PATH.is_file():
    raise AssertionError("missing poll-response fixture module")

spec = importlib.util.spec_from_file_location(
    "_phx_poll_response_fixtures", FIXTURE_PATH
)
if spec is None or spec.loader is None:
    raise AssertionError("cannot load poll-response fixture module")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)

window_main = getattr(fixtures, "WINDOW_MAIN", None)
if not isinstance(window_main, str):
    raise AssertionError("missing WINDOW_MAIN fixture payload")


def validate_timeline(payload: str) -> None:
    marker = "// Model the complete synchronous HTTP timeout after the real loop has"
    assert marker in payload, "missing synchronous-poll scenario in WINDOW_MAIN"
    scenario = payload.split(marker, 1)[1].split(
        'std::cout<<"DEBOUNCE_FLOOR_PASS', 1
    )[0]
    assert "pulseStart=250; pulseEnd=330;" in payload, (
        "missing pulse at exact 250 ms quiet boundary"
    )
    assert "POLL_WINDOW_GUARD_PASS 13/13" in payload, (
        "poll-window scenario count must include exact-boundary case"
    )
    assert "const uint32_t pollStartedAt=fakeNow;" in scenario, (
        "fixture must capture the post-quiet poll start"
    )
    assert "if(pollStartedAt!=250) return 26;" in scenario, (
        "fixture must prove the quiet window ended at 250 ms"
    )
    assert "pulseStart=300; pulseEnd=380;" in scenario, (
        "HTTP-time pulse must begin after the 250 ms quiet window"
    )
    assert "fakeNow=pollStartedAt+70;" in scenario, (
        "HTTP-time pulse must be sampled 70 ms into the poll"
    )
    assert "fakeNow=pollStartedAt+3500;" in scenario, (
        "fixture must model the complete 3500 ms blocking timeout"
    )
    assert "if(fakeNow-pollStartedAt!=3500) return 27;" in scenario, (
        "fixture must verify the exact timeout duration"
    )
    ordered = [
        scenario.index("const uint32_t pollStartedAt=fakeNow;"),
        scenario.index("pulseStart=300; pulseEnd=380;"),
        scenario.index("fakeNow=pollStartedAt+70;"),
        scenario.index("fakeNow=pollStartedAt+3500;"),
    ]
    assert ordered == sorted(ordered), "poll-window fixture events are not monotonic"
    assert "fakeNow=120" not in scenario, (
        "fixture rewinds time before simulating the HTTP-time pulse"
    )


# The moved payload is the source of truth; the runner must still own the
# final-idle-sample failure injection and report its rejection.
assert "from poll_response_failclosed_lab_fixtures import (" in runner, (
    "runner no longer imports the extracted fixture module"
)
assert "WINDOW_MAIN" in runner and "WINDOW_STUBS" in runner, (
    "runner does not import both poll-window fixture exports"
)
assert (
    'mutated_quiet = quiet.replace("const bool idle=coinLineIdle();", "const bool idle=true;", 1)'
    in runner
), "missing final-idle-sample mutation injection"
assert "MUTATION_REJECTED remove-final-quiet-sample" in runner, (
    "missing exact-boundary mutation rejection evidence"
)

validate_timeline(window_main)

# Guard self-test: shortening the modeled synchronous timeout must be rejected.
mutated_window = window_main.replace(
    "fakeNow=pollStartedAt+3500;",
    "fakeNow=pollStartedAt+3499;",
    1,
)
if mutated_window == window_main:
    raise AssertionError("could not construct blocking-timeout mutation")
try:
    validate_timeline(mutated_window)
except AssertionError as exc:
    print(f"MUTATION_REJECTED shorten-blocking-poll-timeout: {exc}")
else:
    raise AssertionError("shortened blocking-poll timeout mutation was accepted")

print("POLL_WINDOW_TIMELINE_GUARD_PASS; MUTATION_REJECTED=1/1")
