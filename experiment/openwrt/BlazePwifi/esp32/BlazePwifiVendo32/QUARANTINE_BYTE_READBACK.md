# Quarantine byte readback — source-level lab

## Why
PR #283 added fail-closed LittleFS append guards, preventing deletion when
open/write/size verification fails. The first version only compared final
file **length**. If the filesystem returns an equal-length but corrupted
append, the check could still call `clearPending()`.

This branch compares each appended byte after close/reopen and refuses to
clear the pending coin on a mismatch. It intentionally does not change CORE
payment decisions, signing, controller authentication, GPIO or relay control.

## Reproducing tests
From the repo root:
```sh
python3 experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/quarantine_readback_lab.py
```
The lab compiles function bodies extracted verbatim from BOTH ESP32/ESP8266
source sketches under C++17 against a disposable fake LittleFS. Eleven
controlled scenarios per board include equal-size corruption and readback
bit-flips (which a size-only check misses). This is software-only, not a
durability guarantee. The tests must be independently re-run by PHX-QA.

## Limitations / release gate
Even exact post-close byte readback does **not** establish flash power-loss
atomicity. Source still needs an atomic journal/receipt protocol, antirollback,
safe config-auth producer/consumer binding, real ESP flash tests, and physical
power-cut / thirty-device soak acceptance. Do NOT flash or enable paid coins.
