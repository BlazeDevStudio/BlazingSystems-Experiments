"""Native fake-flash harness for the extracted CheckedEEPROMClass."""
from checked_eeprom_begin_lab_contract import extract_checked_eeprom_class


def checked_eeprom_begin_harness(source: str) -> str:
    checked_class = extract_checked_eeprom_class(source)
    return r"""
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <cstdlib>
#include <cstddef>
#include <new>

static bool fail_next_array_allocation = false;
void* operator new[](std::size_t size) {
    if (fail_next_array_allocation) {
        fail_next_array_allocation = false;
        throw std::bad_alloc();
    }
    void *memory = std::malloc(size);
    if (!memory) throw std::bad_alloc();
    return memory;
}
void operator delete[](void *memory) noexcept { std::free(memory); }
void operator delete[](void *memory, std::size_t) noexcept { std::free(memory); }
void* operator new[](std::size_t size, const std::nothrow_t&) noexcept {
    try { return ::operator new[](size); } catch (...) { return nullptr; }
}
void operator delete[](void *memory, const std::nothrow_t&) noexcept { ::operator delete[](memory); }

class EEPROMClass {
protected:
    uint32_t _sector;
    uint8_t *_data = nullptr;
    size_t _size = 0;
    bool _dirty = false;
public:
    EEPROMClass() : _sector(17U) {}
    ~EEPROMClass() { delete[] _data; }
};

struct FakeEsp {
    bool read_result = true;
    int read_calls = 0;
    uint32_t address = 0;
    size_t read_size = 0;
    bool flashRead(uint32_t read_address, uint8_t *data, size_t size) {
        ++read_calls;
        address = read_address;
        read_size = size;
        if (!data || size == 0) return false;
        memset(data, 0x5A, size);
        return read_result;
    }
};
FakeEsp ESP;
""" + checked_class + r"""

class InspectableCheckedEEPROM : public CheckedEEPROMClass {
public:
    uint8_t *data() const { return _data; }
    size_t size() const { return _size; }
    bool dirty() const { return _dirty; }
    uint32_t sector() const { return _sector; }
    void markDirty() { _dirty = true; }
};

int main() {
    InspectableCheckedEEPROM store;
    if (store.beginChecked(0)) return 1;
    if (ESP.read_calls != 0 || store.data() != nullptr || store.size() != 0) return 2;
    if (store.beginChecked(4097)) return 3;
    if (ESP.read_calls != 0 || store.data() != nullptr || store.size() != 0) return 4;
    puts("CHECKED_EEPROM_INVALID_SIZE_DENY_PASS");

    InspectableCheckedEEPROM allocation_failure_store;
    fail_next_array_allocation = true;
    if (allocation_failure_store.beginChecked(128)) return 12;
    if (allocation_failure_store.data() != nullptr || allocation_failure_store.size() != 0 ||
        allocation_failure_store.dirty() || ESP.read_calls != 0) return 13;
    puts("CHECKED_EEPROM_ALLOCATION_FAILURE_FAIL_CLOSED_PASS");

    store.markDirty();
    ESP.read_result = false;
    if (store.beginChecked(64)) return 5;
    if (store.data() != nullptr || store.size() != 0 || store.dirty()) {
        fflush(stdout);
        std::_Exit(6);
    }
    puts("CHECKED_EEPROM_FLASH_READ_FAILURE_CLEANUP_PASS");

    ESP.read_result = true;
    if (!store.beginChecked(4093)) return 7;
    if (!store.data() || store.size() != 4096 || ESP.address != 17U * 4096U ||
        ESP.read_size != 4096 || store.sector() != 17U || store.dirty()) return 8;
    uint8_t *first = store.data();
    if (!store.beginChecked(4093) || store.data() != first || ESP.read_calls != 3) return 9;
    puts("CHECKED_EEPROM_ALIGNED_SECTOR_READ_AND_REUSE_PASS");

    if (!store.beginChecked(100) || store.size() != 100 ||
        ESP.address != 17U * 4096U || ESP.read_size != 100) return 10;
    puts("CHECKED_EEPROM_RESIZE_REINITIALIZE_PASS");

    uint8_t *before_invalid = store.data();
    if (store.beginChecked(0) || store.data() != before_invalid ||
        store.size() != 100 || ESP.read_calls != 4) return 11;
    puts("CHECKED_EEPROM_INVALID_RETRY_PRESERVES_READY_BUFFER_PASS");
    return 0;
}
"""


