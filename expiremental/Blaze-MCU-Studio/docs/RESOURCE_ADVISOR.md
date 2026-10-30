# Resource Advisor and Storage Forecast — v0.4.0

**Measured:** After a successful Arduino CLI compile, parse reported executable program flash and static/global SRAM from compiler text. The selected project's new edits invalidate prior measurements.

**Known board metadata:** Arduino Uno R3 ATmega328P has 32 KB flash (about 0.5 KB bootloader reserved) and 2 KB SRAM per official board specification. Unknown boards show **Unknown / Verification Required**. No guessed limits for ESP families.

**Not measured:** peak runtime stack, heap, PSRAM, CPU time, filesystem free bytes, SD endurance, sensor sampling overhead, large dynamic allocations. The UTF-8 `.ino` source file size is deliberately labeled **not firmware binary size**.

**Storage Forecast:** user specifies interval (seconds), bytes/record, available capacity, desired retention. Calculations include a transparent 5% default overhead and optional compression ratio. The display reports records/hour/day, 7/30-day requirements and estimated days to fill. This is not a promise of filesystem longevity or power-loss durability.

**SD guidance:** advisory only. Clicking Plan SPI SD card on the Uno requires conflict-free SPI D11 (MOSI), D12 (MISO), D13 (SCK), D10 (CS); no automatic SD library installation, mount code, write synchronization or journaling is added. Refuse known conflicts with the current project's active visual logic. SD **cannot** cure insufficient program flash or SRAM.
