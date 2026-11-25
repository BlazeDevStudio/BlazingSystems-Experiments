"""Ordered assembly of the coin-pulse C++ host fixture sections.

Keep the section order explicit: the runner inserts extracted production helpers
at the single placeholder in CPP_RUNTIME before compiling the complete fixture.
"""
from coin_pulse_capture_lab_fixture_runtime import CPP_RUNTIME
from coin_pulse_capture_lab_fixture_poll import CPP_POLL
from coin_pulse_capture_lab_fixture_gates import CPP_GATES
from coin_pulse_capture_lab_fixture_faults import CPP_FAULTS
from coin_pulse_capture_lab_fixture_edges import CPP_EDGES
from coin_pulse_capture_lab_fixture_entry import CPP_ENTRY

CPP = "".join((
    CPP_RUNTIME,
    CPP_POLL,
    CPP_GATES,
    CPP_FAULTS,
    CPP_EDGES,
    CPP_ENTRY,
))
