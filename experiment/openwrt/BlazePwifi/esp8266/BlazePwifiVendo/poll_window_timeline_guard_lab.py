#!/usr/bin/env python3
"""Static guard against impossible time travel in the poll-window host fixture.

This is a regression check for the test harness, not hardware evidence.
"""
from pathlib import Path

lab = Path(__file__).with_name("poll_response_failclosed_lab.py").read_text(encoding="utf-8")
marker = "# Model the complete synchronous HTTP timeout after the real loop has"
assert marker in lab, "missing synchronous-poll scenario"
scenario = lab.split(marker, 1)[1].split('std::cout<<\"DEBOUNCE_FLOOR_PASS', 1)[0]
assert "const uint32_t pollReadyAt=fakeNow;" in scenario, "poll-ready timestamp not captured"
assert "pulseStart=300; pulseEnd=380;" in scenario, "HTTP-time pulse must begin after 250 ms quiet window"
assert "advanceFakeTime(320)" in scenario, "HTTP-time pulse must be sampled on a monotonic clock"
assert "advanceFakeTime(3600)" in scenario, "HTTP timeout must advance monotonically"
assert "fakeNow=120" not in scenario, "fixture rewinds time before simulating the HTTP-time pulse"
print("POLL_WINDOW_TIMELINE_GUARD_PASS")
