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


def harness(board: str, source: str) -> str:
    if board not in ("ESP32", "ESP8266"):
        raise ValueError(f"unsupported board fixture: {board!r}; expected ESP32 or ESP8266")
    record = extract_block(source, "struct PollFaultRecord") + ";"
    helper_names = [
        "pollFaultRecordChecksum",
        "makePollFaultRecord",
        "validPollFaultRecord",
        "pollFaultBackupPresentOrCorrupt",
        "writePollFaultBackup",
        "loadPollPulseFaultLatch",
        "latchPollPulseFault",
    ]
    if board == "ESP32":
        helper_names.append("initPollFaultBackupStore")
        spec = esp32_backend()
    else:
        helper_names[3:3] = [
            "readFullEepromImage",
            "restoreEepromRamImage",
            "refreshVerifiedEepromImage",
            "readPollFaultBackupFlash",
        ]
        spec = esp8266_backend()
    helpers = "\n".join(extract_function(source, name) for name in helper_names)
    consts = constants(source, (
        "POLL_FAULT_RECORD_MAGIC",
        "POLL_FAULT_RECORD_VERSION",
        "POLL_FAULT_EEPROM_OFFSET",
        "POLL_FAULT_EEPROM_BYTES",
    ))
    main = MAIN
    main = main.replace("NVS_WRITE_BEFORE_COMMIT_ASSERT", spec["nvs_write_before_commit_assert"])
    main = main.replace("COMMIT_FAIL_BEFORE_PERSISTENCE_SETUP", spec["commit_fail_before_persistence_setup"])
    main = main.replace("COMMIT_FAIL_BEFORE_PERSISTENCE_CLEAR", spec["commit_fail_before_persistence_clear"])
    main = main.replace("NVS_READ_ERROR_SCENARIO", spec["nvs_read_error"])
    main = main.replace("RAW_FLASH_READ_ERROR_SCENARIO", RAW_FLASH_READ_ERROR if board == "ESP8266" else "")
    main = main.replace("READ_FAIL_SETUP", spec["fail_read"]).replace("READ_FAIL_CLEAR", spec["clear_fail"])
    main = main.replace("WRITE_FAIL_SETUP", spec["fail_write"]).replace("WRITE_FAIL_CLEAR", spec["clear_fail"])
    main = main.replace("AMBIGUOUS_COMMIT_SETUP", spec["ambiguous_commit_setup"]).replace("AMBIGUOUS_COMMIT_CLEAR", spec["clear_fail"])
    main = main.replace("NO_MARKER_RESET", spec["no_marker"])
    main = main.replace("BOARD_NAME", board)
    return "\n".join([PRELUDE, record, consts, spec["backend"], helpers, main])
