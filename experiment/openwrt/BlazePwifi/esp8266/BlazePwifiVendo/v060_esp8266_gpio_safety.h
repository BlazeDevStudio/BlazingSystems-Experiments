#ifndef BLAZEPWIFI_V060_ESP8266_GPIO_SAFETY_H
#define BLAZEPWIFI_V060_ESP8266_GPIO_SAFETY_H

/*
 * ESP8266 NodeMCU Vendo hardware pin allowlist (not an ESP32 policy).
 *
 * GPIO 6-11 are used for SPI flash, GPIO 0/2/15 affect bootstrap,
 * GPIO 1/3 are UART, and GPIO 16 has special pull-up semantics.
 * GPIO 4/5/12/13/14 are the supported coin input, relay and LED lines.
 * Reject all shared roles: a relay/LED collision can energize the acceptor
 * and input/output collision can lose or miscount physical coin pulses.
 *
 * No implicit pin remapping of installed equipment is authorized. An unsafe
 * persisted configuration disables physical acceptance until corrected.
 * Host C++ regression compiles this exact dependency shipped with .ino.
 */
static inline bool bp_esp8266_vendo_pin_supported(int pin) {
  return pin == 4 || pin == 5 || pin == 12 || pin == 13 || pin == 14;
}

static inline bool bp_esp8266_vendo_pins_safe(int coinPin,
                                               int relayPin,
                                               int ledPin) {
  return bp_esp8266_vendo_pin_supported(coinPin) &&
         bp_esp8266_vendo_pin_supported(relayPin) &&
         bp_esp8266_vendo_pin_supported(ledPin) &&
         coinPin != relayPin && coinPin != ledPin && relayPin != ledPin;
}

#endif
