# BlazePwifi Linux GPIO agent

This is the Standard/Full-target controller for Orange Pi and similar Linux/OpenWrt SBCs.

It uses libgpiod's GPIO character-device tools:
- `gpiomon` for edge events, debounce, and pulse grouping
- `gpioset` as a long-lived line owner for relay/LED output

It intentionally does not use deprecated sysfs GPIO.

## Safety

Board header pin numbers are **not** the same thing as gpiochip line offsets. Profiles identify the board and OpenWrt image profile, but coin/relay/LED line offsets remain unset until the exact board/revision is inspected with `gpioinfo`.

A 12 V coin acceptor must never be wired directly to a 3.3 V SBC GPIO. Use proper opto-isolation/level conditioning and common-ground design appropriate to the interface.

The agent journals one unacknowledged coin event under persistent BlazePwifi state before sending it, then retries that same nonce/target/pulse count until acknowledged.
