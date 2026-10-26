# Pin/Peripheral planner — v0.4.0

- Existing conservative Uno R3 digital pin validation remains in codegen.
- Optional named I2C, SPI and GPIO peripheral resource reservations are validated separately and surfaced in Resources.
- I2C SDA/SCL share a named bus when identical roles and pins match; devices with duplicate known 7-bit I2C addresses on the same bus fail.
- SPI SCK/MISO/MOSI share a named bus when identical roles/pins match; chip-select and cross-role signals remain exclusive.
- Current active visual node/flowchart GPIO claims are checked against external peripheral assignments. An inactive editor does not reserve its pins, except `callNodes` reserves its invoked graph pins.
- Uno hardware SPI roles D13 SCK, D12 MISO, D11 MOSI, I2C A4 SDA/A5 SCL are used as provisional planning references. Alternate wiring is warned. Pin mappings on unverified boards remain **Unknown / Verification Required**.
- This is **not** a formal electrical validation: voltage limits, power distribution, current draw, bus capacitance, bootstrapping and actual peripheral driver compatibility require documentation and physical testing.
