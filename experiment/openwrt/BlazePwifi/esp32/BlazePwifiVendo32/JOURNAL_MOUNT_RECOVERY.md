# Hardware journal mount failure — non-destructive recovery (LAB ONLY)

## Problem
The ESP8266 draft controller automatically called `LittleFS.format()` after a
failed mount; ESP32 used `LittleFS.begin(true)`, which enables automatic
format-on-mount-failure. Both operations can destroy unacknowledged coin
journals and quarantine evidence during corruption, first boot or power loss.

## Behavior after patch
- ESP8266 calls `LittleFS.begin()`; ESP32 calls
  `LittleFS.begin(false)`. Neither controller formats media at boot.
- If mounting fails, `fsReady=false`, saved pending records are not loaded,
  and `applyOutputs()` keeps coin relay/output disabled via the existing
  fail-closed `fsReady` gate.
- Serial output reports mount failure and recovery needed. No setup portal,
  remote request, or timeout can authorize formatting automatically.
- A truly blank unformatted device will also fail closed until a separately
  approved, explicit, noncustomer commissioning/recovery process exists.
  Never format a device that could contain money evidence without a
  safeguarded backup/reconciliation procedure.

## Source-extracted LAB
```sh
python3 experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/journal_mount_failclosed_lab.py
```
The test extracts and compiles the genuine `initPendingStore` and
`applyOutputs` functions from both firmware sketches, injects failed and
successful mounts plus pending/controller/coin/insert gate variations,
and checks that the relay cannot enable after mount failure. It DOES NOT
simulate real flash translation, wear, voltage sag or powered GPIO.

## Open release gates
In addition to actual on-device noncustomer recovery validation:
protected monotonic witness, signed backend response contract, financial
receipt/ACK durability, reversible migration, 150 real power cuts,
30-device 24-hour soak and independent QA/RELEASE approval all remain NO-GO.
