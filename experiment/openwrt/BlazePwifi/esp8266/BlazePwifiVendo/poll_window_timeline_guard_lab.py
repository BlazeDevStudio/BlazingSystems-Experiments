#!/usr/bin/env python3
"""Static guard against impossible time travel in the poll-window host fixture.

This is a regression check for the test harness, not hardware evidence.
"""
from pathlib import Path

lab = Path(__file__).with_name("poll_response_failclosed_lab.py").read_text(encoding="utf-8")
marker = "// Model the complete synchronous HTTP timeout after the real loop has"
assert marker in lab, "missing synchronous-poll scenario"
scenario = lab.split(marker, 1)[1].split('std::cout<<"DEBOUNCE_FLOOR_PASS', 1)[0]
assert "pulseStart=250; pulseEnd=330;" in lab, "missing pulse at exact 250 ms quiet boundary"
assert "POLL_WINDOW_GUARD_PASS 13/13" in lab, "poll-window scenario count must include exact-boundary case"
assert "mutated_quiet = quiet.replace(\"return coinLineIdle();\", \"return true;\", 1)" in lab, "missing final-idle-sample mutation injection"
assert "MUTATION_REJECTED remove-final-quiet-sample" in lab, "missing exact-boundary mutation rejection evidence"
assert "const uint32_t pollStartedAt=fakeNow;" in scenario, "fixture must capture the post-quiet poll start"
assert "if(pollStartedAt!=250) return 26;" in scenario, "fixture must prove the quiet window ended at 250 ms"
assert "pulseStart=300; pulseEnd=380;" in scenario, "HTTP-time pulse must begin after 250 ms quiet window"
assert "setFakeNow(pollStartedAt+70);" in scenario, "HTTP-time pulse must be sampled 70 ms into the poll"
assert "setFakeNow(pollStartedAt+3500);" in scenario, "HTTP timeout must model the complete 3500 ms block"
assert "if(fakeNow-pollStartedAt!=3500) return 27;" in scenario, "fixture must verify the exact timeout duration"
assert "bool timeWentBackwards=false;" in lab, "fixture must track clock rewinds"
assert "void setFakeNow(uint32_t value)" in lab, "fixture must update time through a monotonicity-checking helper"
assert "setFakeNow(pollStartedAt+70);" in scenario, "post-quiet pulse sample must use the checked clock helper"
assert "setFakeNow(pollStartedAt+3500);" in scenario, "timeout completion must use the checked clock helper"
assert "POLL_WINDOW_MUTATION_REJECTED clock-rewind" in lab, "missing deliberate clock-rewind mutation rejection"
ordered = [
    scenario.index("const uint32_t pollStartedAt=fakeNow;"),
    scenario.index("pulseStart=300; pulseEnd=380;"),
    scenario.index("setFakeNow(pollStartedAt+70);"),
    scenario.index("setFakeNow(pollStartedAt+3500);"),
]
assert ordered == sorted(ordered), "poll-window fixture events are not monotonic"
assert "fakeNow=120" not in scenario, "fixture rewinds time before simulating the HTTP-time pulse"
print("POLL_WINDOW_TIMELINE_GUARD_PASS")
