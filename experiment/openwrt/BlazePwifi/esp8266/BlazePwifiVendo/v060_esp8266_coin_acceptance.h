#ifndef BLAZEPWIFI_V060_ESP8266_COIN_ACCEPTANCE_H
#define BLAZEPWIFI_V060_ESP8266_COIN_ACCEPTANCE_H

/*
 * NodeMCU ESP8266 coin-acceptor relay eligibility (NOT ESP32 or a server
 * payment authority). A powered relay must never accept a physical coin
 * that the local LittleFS pending sequence cannot represent.
 *
 * The caller must set targetPresent only for the active server coin window.
 * An existing pulse group is bound to its ORIGINAL target. Do not silently
 * rebind bought pulses after a polling/window change. Journal capacity is
 * exactly 20 pulses; do not accept a 21st unrecordable physical pulse.
 *
 * Portable contract allows the real firmware and host safety tests to share
 * the same predicate; it is not a real relay timing or power-cut proof.
 */
static inline bool bp_esp8266_coin_can_accept(bool controllerEnabled,
                                               bool coinEnabled,
                                               bool relayEnabled,
                                               bool insertMode,
                                               bool fsReady,
                                               bool pendingReady,
                                               bool targetPresent,
                                               bool pendingTargetMatches,
                                               unsigned int pendingPulses) {
  return controllerEnabled && coinEnabled && relayEnabled &&
         insertMode && fsReady && !pendingReady && targetPresent &&
         pendingPulses < 20U &&
         (pendingPulses == 0U || pendingTargetMatches);
}

#endif
