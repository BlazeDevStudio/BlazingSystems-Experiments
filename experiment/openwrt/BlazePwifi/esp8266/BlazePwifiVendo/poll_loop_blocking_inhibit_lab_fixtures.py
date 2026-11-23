"""Stable fixture exports for the blocking-poll regression lab.

The runner imports from this module. Implementations are split into runtime
stubs and scenario definitions for smaller, human-reviewable source units.
"""

from poll_loop_blocking_inhibit_lab_runtime_fixtures import STUBS, SUPPORT
from poll_pending_recovery_lab_fixtures import (
    PENDING_PRESERVATION_MAIN,
    CLEAR_WINDOW_ISR_MAIN,
)

from poll_loop_blocking_inhibit_lab_scenario_fixtures import (
    MAIN,
    COIN_POST_ISR_MAIN,
    RACE_MAIN,
    post_drain_rollover_main,
    missed_sample_main,
    TIMING_MAIN,
    RELEASE_EDGE_MAIN,
)

__all__ = [
    "STUBS",
    "SUPPORT",
    "MAIN",
    "COIN_POST_ISR_MAIN",
    "PENDING_PRESERVATION_MAIN",
    "RACE_MAIN",
    "post_drain_rollover_main",
    "missed_sample_main",
    "TIMING_MAIN",
    "RELEASE_EDGE_MAIN",
    "CLEAR_WINDOW_ISR_MAIN",
]
