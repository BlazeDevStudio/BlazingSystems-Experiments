# Curated executable adapters — v0.4.2 checkpoint

**Wire (Arduino Uno / arduino:avr:uno)** is the first constrained library-backed, executable visual node. It is deliberately different from BALIE's untrusted signature inference. BALIE may list unknown libraries without compile permission; merely seeing a method declaration never enables arbitrary C++ insertion.

## Wire register-write node

Inputs: 7-bit I2C address 0x08–0x77, 8-bit register 0–255, and 8-bit data 0–255. Decimal or 0x-prefixed hex values are accepted and normalized before code generation; arbitrary expressions or code injection are rejected.

The generated sketch includes `<Wire.h>`, calls `Wire.begin()` once in setup, then `Wire.beginTransmission(addr)`, `Wire.write(register)`, `Wire.write(value)`, and stores `Wire.endTransmission()` into `uint8_t blazeLastWireStatus` in each loop. This is a **generic register-write transaction** and does not establish that any connected device supports this protocol. Physical connections, clock speed, device datasheet, power limits, acknowledge/status and actual execution must be verified separately.

Pin ownership: standard hardware Wire uses A4 (SDA) and A5 (SCL) on Arduino Uno R3. The node currently does not automatically allocate arbitrary I2C alternate pins. The existing resource planner is advisory and should be used to check bus sharing.

The adapter is compile-authorized only for `arduino:avr:uno` in this revision. Other boards receive a visible error instead of a guessed method or pin mapping. The precise AVR core/toolchain combination must be pinned by the Windows CI evidence; until its first successful run, compile acceptance remains **pending**.

## Serial Print and PWM Write

`serialPrint` exposes a bounded string and one of 9600/19200/38400/57600/115200 baud rates. Inconsistent baud rates across graph nodes are blocked. `pwmWrite` uses `analogWrite(pin, duty)` with 0–255 duty; Arduino Uno R3 PWM pin validation checks D3/D5/D6/D9/D10/D11. The simulator records a virtual PWM duty but makes no timing, frequency, servo, real voltage, or hardware claim.

Existing `.ino` manual source ownership and safe non-overwriting export are unchanged. A generated Wire project records `Wire` in exported library metadata. No third-party packages, unauthorized downloads, or hardware uploads are performed by these nodes.
