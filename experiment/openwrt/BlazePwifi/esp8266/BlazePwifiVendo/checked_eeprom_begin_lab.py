"""Run source-linked CheckedEEPROMClass bounds and flash-read failure tests."""
from pathlib import Path

from checked_eeprom_begin_lab_contract import assert_checked_eeprom_begin
from checked_eeprom_begin_lab_harness import checked_eeprom_begin_harness
from config_persistence_write_result_lab_harness import compile_and_run, compile_and_run_result


BLAZEPWIFI = Path(__file__).resolve().parents[2]
ESP8266 = BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"


def expect_contract_rejected(label: str, source: str, expected: str) -> None:
    try:
        assert_checked_eeprom_begin(source)
    except AssertionError as exc:
        if expected not in str(exc):
            raise AssertionError(f"{label} failed for the wrong reason: {exc}") from exc
        print(f"CHECKED_EEPROM_SOURCE_MUTATION_REJECTED {label}")
    else:
        raise AssertionError(f"unsafe CheckedEEPROMClass mutation was accepted: {label}")


def expect_runtime_rejected(
    label: str, source: str, expected_return_code: int
) -> None:
    result = compile_and_run_result(
        checked_eeprom_begin_harness(source), f"checked_eeprom_{label}"
    )
    if result.returncode == 0:
        raise AssertionError(f"unsafe CheckedEEPROMClass runtime mutation survived: {label}")
    if result.returncode != expected_return_code:
        raise AssertionError(
            f"{label}: expected invariant exit {expected_return_code}, "
            f"got {result.returncode}; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )
    print(
        f"CHECKED_EEPROM_RUNTIME_MUTATION_REJECTED {label} "
        f"exit={expected_return_code}"
    )


def main() -> None:
    source = ESP8266.read_text(encoding="utf-8")
    assert_checked_eeprom_begin(source)
    print(compile_and_run(checked_eeprom_begin_harness(source), "checked_eeprom_begin"))

    expect_contract_rejected(
        "aligned-sector-cap-removed",
        source.replace(
            "if(aligned==0 || aligned>kFlashSectorBytes) return false;",
            "if(aligned==0) return false;",
            1,
        ),
        "aligned request must fit one flash sector",
    )
    expect_contract_rejected(
        "allocation-null-guard-removed",
        source.replace("if(!_data){", "if(false){", 1),
        "allocation failure must return false and clear state",
    )
    expect_contract_rejected(
        "flash-read-result-ignored",
        source.replace(
            "if(!ESP.flashRead(address,_data,_size)){",
            "ESP.flashRead(address,_data,_size); if(false){",
            1,
        ),
        "flash read failure must be checked and rolled back",
    )
    expect_contract_rejected(
        "flash-sector-derived-address-removed",
        source.replace(
            "const uint32_t address=static_cast<uint32_t>(_sector*kFlashSectorBytes);",
            "const uint32_t address=0;",
            1,
        ),
        "flash address must use the inherited EEPROM sector",
    )
    expect_contract_rejected(
        "read-failure-buffer-null-reset-removed",
        source.replace(
            "if(!ESP.flashRead(address,_data,_size)){\n      delete[] _data;\n      _data=nullptr;",
            "if(!ESP.flashRead(address,_data,_size)){\n      delete[] _data;",
            1,
        ),
        "read failure must release and null the buffer",
    )

    oversized = source.replace(
        "if(requested==0 || requested>kFlashSectorBytes) return false;",
        "if(requested==0) return false;",
        1,
    ).replace(
        "if(aligned==0 || aligned>kFlashSectorBytes) return false;",
        "if(aligned==0) return false;",
        1,
    )
    expect_runtime_rejected(
        "oversized-sector", oversized, 3
    )
    expect_runtime_rejected(
        "allocation-failure-guard-removed",
        source.replace("if(!_data){", "if(false){", 1),
        13,
    )
    expect_runtime_rejected(
        "flash-read-failure-ignored",
        source.replace(
            "if(!ESP.flashRead(address,_data,_size)){",
            "ESP.flashRead(address,_data,_size); if(false){",
            1,
        ),
        5,
    )
    expect_runtime_rejected(
        "wrong-flash-sector",
        source.replace(
            "const uint32_t address=static_cast<uint32_t>(_sector*kFlashSectorBytes);",
            "const uint32_t address=0;",
            1,
        ),
        8,
    )
    expect_runtime_rejected(
        "failed-read-buffer-not-cleared",
        source.replace(
            "if(!ESP.flashRead(address,_data,_size)){\n      delete[] _data;\n      _data=nullptr;",
            "if(!ESP.flashRead(address,_data,_size)){\n      delete[] _data;",
            1,
        ),
        6,
    )
    print("CHECKED_EEPROM_BEGIN_RUNTIME_AND_MUTATION_MATRIX_PASS")


if __name__ == "__main__":
    main()
