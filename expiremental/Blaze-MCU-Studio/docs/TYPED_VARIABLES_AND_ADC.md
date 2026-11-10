# Typed project variables and Uno analog threshold controller — v0.4.3

## Compilable project representation

A project may store at most 64 typed global variables in `variables: [{name,type,initial}]`. Types currently supported are `long` (signed 32-bit literal), `float` (finite decimal literal), and `bool` (exact `true` or `false`). Identifier grammar is bounded, declarations are unique, and selected known C++ / Arduino reserved identifiers are rejected. Generated global symbols use the `blazeVar_` prefix. The model deliberately does not parse arbitrary C++ expressions or reverse-engineer manual source ownership.

- `setVariable`: writes an appropriately typed literal into a declared variable.
- `readAnalog`: for verified Arduino Uno R3 only, samples one of A0–A5 with `analogRead` into an existing `long` variable.
- `thresholdOutput`: for verified Uno only, compares a declared numeric value to an explicit numeric threshold using `<`, `<=`, `>`, `>=`, `==`, or `!=`, setting D0–D13 to one of two known digital values. D0/D1 are UART-sensitive, and explicit safety warnings remain.

When a variable is not declared, has the wrong type, or a node contains an invalid literal, visual firmware generation fails closed. Deleting a variable while a graph node references it is refused by the UI. Variables persist in the project JSON and regenerate in standard Arduino `.ino` source. Existing older projects without a `variables` field remain loadable and are interpreted as having no variables.

## Starter template

Create Project > **Uno Analog Threshold Controller** creates a fresh project with two connected blocks: sample A0 into `sensorValue:long` and set D8 HIGH when the reading is >=512, otherwise LOW. There is no hidden Blink loop delay in this template. Selecting a non-Uno board for this template fails with an explicit compatibility error. Blink and Empty Visual are also available.

## Analog simulation vs hardware evidence

The logic simulator has independent virtual `A0..A5` integer inputs in range 0..1023 and exposes variable snapshots. An unset ADC reading defaults to simulated zero *with an explicit trace annotation*, not an actual measured voltage. A HIGH/LOW threshold result is a deterministic logic-model result only. It does **not** model ADC calibration, electrical voltage limits, noise, switching transients, relays, or actual hardware safety.

A4 and A5 are also Uno hardware I2C pins; a generated Wire node cannot coexist with ADC sampling on the same pins. The existing peripheral planner detects analog/peripheral physical pin collisions when resources are explicitly assigned.

## Release requirements and limitations

A real target compiler must compile the generated sensor/threshold sketch before the feature is labeled compiler-tested. Uno pin mapping is bounded to verified simple Arduino APIs; Mega/Nano generated Blink compilation validates toolchain compatibility only, not their electrical pinout. No physical microcontroller tests, ESP32/ESP8266 compilation or 2 GB Windows memory acceptance is claimed.
