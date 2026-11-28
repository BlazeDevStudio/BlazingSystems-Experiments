"""Source contract for the ESP8266 CheckedEEPROMClass initialization path."""
import re

from firmware_source_extract import extract_braced, extract_function, mask_non_code


def extract_checked_eeprom_class(source: str) -> str:
    masked = mask_non_code(source)
    match = re.search(
        r"\bclass\s+CheckedEEPROMClass\s*:\s*public\s+EEPROMClass\s*\{",
        masked,
    )
    if not match:
        raise AssertionError("missing CheckedEEPROMClass definition")
    opening = masked.find("{", match.start())
    block = extract_braced(source, opening)
    return source[match.start():opening] + block + ";"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_checked_eeprom_begin(source: str) -> None:
    checked_class = extract_checked_eeprom_class(source)
    masked_class = mask_non_code(checked_class)
    _require(
        "static const uint32_t kFlashSectorBytes=4096U;" in masked_class,
        "checked EEPROM sector size must remain explicit",
    )

    begin = mask_non_code(
        extract_function(checked_class, "bool beginChecked(size_t requested)")
    )
    _require(
        re.search(
            r"if\s*\(\s*requested\s*==\s*0\s*\|\|\s*requested\s*>\s*kFlashSectorBytes\s*\)\s*return\s+false\s*;",
            begin,
        ) is not None,
        "requested EEPROM size must be bounded before allocation",
    )
    _require(
        re.search(
            r"const\s+size_t\s+aligned\s*=\s*\(\s*requested\s*\+\s*3U\s*\)\s*&\s*~static_cast\s*<\s*size_t\s*>\s*\(\s*3U\s*\)\s*;",
            begin,
        ) is not None,
        "EEPROM buffer size must be rounded to four-byte alignment",
    )
    _require(
        re.search(
            r"if\s*\(\s*aligned\s*==\s*0\s*\|\|\s*aligned\s*>\s*kFlashSectorBytes\s*\)\s*return\s+false\s*;",
            begin,
        ) is not None,
        "aligned request must fit one flash sector",
    )
    _require(
        re.search(
            r"if\s*\(\s*_data\s*&&\s*_size\s*!=\s*aligned\s*\)\s*\{\s*delete\s*\[\s*\]\s*_data\s*;\s*_data\s*=\s*nullptr\s*;\s*_size\s*=\s*0\s*;\s*\}",
            begin,
        ) is not None,
        "resizing must release and reset the previous buffer",
    )
    _require(
        re.search(
            r"if\s*\(\s*!_data\s*\)\s*_data\s*=\s*new\s*\(\s*std::nothrow\s*\)\s*uint8_t\s*\[\s*aligned\s*\]\s*;",
            begin,
        ) is not None,
        "EEPROM allocation must remain nothrow",
    )
    _require(
        re.search(
            r"if\s*\(\s*!_data\s*\)\s*\{\s*_size\s*=\s*0\s*;\s*_dirty\s*=\s*false\s*;\s*return\s+false\s*;\s*\}",
            begin,
        ) is not None,
        "allocation failure must return false and clear state",
    )
    _require(
        re.search(
            r"const\s+uint32_t\s+address\s*=\s*static_cast\s*<\s*uint32_t\s*>\s*\(\s*_sector\s*\*\s*kFlashSectorBytes\s*\)\s*;",
            begin,
        ) is not None,
        "flash address must use the inherited EEPROM sector",
    )

    read_guard = re.search(
        r"if\s*\(\s*!ESP\.flashRead\s*\(\s*address\s*,\s*_data\s*,\s*_size\s*\)\s*\)\s*\{",
        begin,
    )
    _require(
        read_guard is not None,
        "flash read failure must be checked and rolled back",
    )
    read_block = extract_braced(begin, begin.find("{", read_guard.start()))
    masked_read_block = mask_non_code(read_block)
    for token in ("delete[] _data;", "_data=nullptr;", "_size=0;", "_dirty=false;", "return false;"):
        _require(token in masked_read_block, "read failure must release and null the buffer")

    _require(
        re.search(r"_dirty\s*=\s*false\s*;\s*return\s+true\s*;", begin) is not None,
        "EEPROM readiness may be reported only after a successful flash read",
    )
