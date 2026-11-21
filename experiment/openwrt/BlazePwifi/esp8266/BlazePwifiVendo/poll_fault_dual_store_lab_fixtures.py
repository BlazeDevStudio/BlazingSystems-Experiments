"""Compose source-extracted firmware helpers with shared and board-specific C++ fixtures."""
from firmware_lab_source import extract_block, extract_function
from poll_fault_dual_store_lab_fixtures_common import (
    MAIN,
    PRELUDE,
    RAW_FLASH_READ_ERROR,
    constants,
)
from poll_fault_dual_store_lab_fixtures_esp32 import backend as esp32_backend
from poll_fault_dual_store_lab_fixtures_esp8266 import backend as esp8266_backend

__all__ = ["constants", "harness"]


_TEMPLATE_MARKER_COUNTS = {
    "NVS_WRITE_BEFORE_COMMIT_ASSERT": 1,
    "COMMIT_FAIL_BEFORE_PERSISTENCE_SETUP": 1,
    "COMMIT_FAIL_BEFORE_PERSISTENCE_CLEAR": 1,
    "NVS_READ_ERROR_SCENARIO": 1,
    "RAW_FLASH_READ_ERROR_SCENARIO": 1,
    "READ_FAIL_SETUP": 1,
    "READ_FAIL_CLEAR": 1,
    "WRITE_FAIL_SETUP": 3,
    "WRITE_FAIL_CLEAR": 2,
    "AMBIGUOUS_COMMIT_SETUP": 2,
    "AMBIGUOUS_COMMIT_CLEAR": 2,
    "NO_MARKER_RESET": 1,
}
_BOARD_NAME_COUNT = 9


def _render_main(board: str, spec: dict) -> str:
    required_keys = {
        "nvs_write_before_commit_assert",
        "commit_fail_before_persistence_setup",
        "commit_fail_before_persistence_clear",
        "nvs_read_error",
        "fail_read",
        "clear_fail",
        "fail_write",
        "ambiguous_commit_setup",
        "no_marker",
    }
    missing_keys = sorted(required_keys.difference(spec))
    if missing_keys:
        raise ValueError(f"{board} fixture backend is missing required values: {', '.join(missing_keys)}")

    replacements = {
        "NVS_WRITE_BEFORE_COMMIT_ASSERT": spec["nvs_write_before_commit_assert"],
        "COMMIT_FAIL_BEFORE_PERSISTENCE_SETUP": spec["commit_fail_before_persistence_setup"],
        "COMMIT_FAIL_BEFORE_PERSISTENCE_CLEAR": spec["commit_fail_before_persistence_clear"],
        "NVS_READ_ERROR_SCENARIO": spec["nvs_read_error"],
        "RAW_FLASH_READ_ERROR_SCENARIO": RAW_FLASH_READ_ERROR if board == "ESP8266" else "",
        "READ_FAIL_SETUP": spec["fail_read"],
        "READ_FAIL_CLEAR": spec["clear_fail"],
        "WRITE_FAIL_SETUP": spec["fail_write"],
        "WRITE_FAIL_CLEAR": spec["clear_fail"],
        "AMBIGUOUS_COMMIT_SETUP": spec["ambiguous_commit_setup"],
        "AMBIGUOUS_COMMIT_CLEAR": spec["clear_fail"],
        "NO_MARKER_RESET": spec["no_marker"],
    }

    main = _render_main(board, spec)
    return "\n".join([PRELUDE, record, consts, spec["backend"], helpers, main])
