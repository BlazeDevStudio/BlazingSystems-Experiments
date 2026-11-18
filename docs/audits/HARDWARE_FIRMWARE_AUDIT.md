# Project Phoenix: Hardware & Firmware Integration Audit (PHX-HARDWARE)

**Document Reference:** `docs/audits/HARDWARE_FIRMWARE_AUDIT.md`  
**Role:** PHX-HARDWARE (Hardware / Firmware Integration Engineer)  
**Classification:** LAB & CODE HARDENING ONLY — STRICT PRODUCTION NO-GO  
**Target Baseline:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; parallel firmware candidate `PR #283@830c355376380f9b5533d5cda2558beed41a593a`  
**Active Review Branch:** `phoenix/hardware-clear-pending-remove-verify-20261118` (DRAFT PR #325, child of PR #283)

---

## 1. Executive Summary & Production Gate Status

This audit establishes the hardware, electrical, and firmware baseline for Blaze Systems / Project Phoenix coin-ingress controllers (ESP8266, ESP32, and Linux GPIO), as well as router deployment targets (Ruijie RG-EW1200G Pro v1.1, Orange Pi Zero 3, x86_64, and R281).

### Standing Safety Boundary (NO-GO)
In accordance with `AGENTS.md` and the Master Coordination Directive:
- **HARDWARE RELEASE & FLASHING GATE:** **NO-GO**. No flashing of production or customer devices.
- **FINANCIAL ADMISSION GATE:** **NO-GO**. No production money cutover or ledger migration without verified independent durable witness and physical noncustomer acceptance.
- **EVIDENCE REQUIREMENT:** CI passage, green simulation suites, or static checksum verification do **not** constitute physical hardware or electrical acceptance.

---

## 2. Firmware Boards & Controller Inventory

| Target Board | MCU / SoC | Clock & RAM | Storage / Partitioning | Ingress Interface | Primary Firmware Sketch |
|---|---|---|---|---|---|
| **NodeMCU v2 / ESP-12E/F** | ESP8266 (Xtensa LX106) | 80/160 MHz, 80 KB RAM | 4 MB SPI NOR Flash; LittleFS journal partition (1 MB) | GPIO4 (Coin In), GPIO14 (LED), GPIO5 (Relay) | `esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` |
| **ESP32-DevKitC / WROOM-32** | ESP32 (Xtensa Dual LX6) | 240 MHz, 520 KB SRAM | 4 MB SPI Flash; NVS (Preferences) + LittleFS journal | Configurable (Default GPIO27 In, GPIO2 LED, GPIO26 Relay) | `esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` |
| **Orange Pi Zero 3** | Allwinner H618 (Quad Cortex-A53) | 1.5 GHz, 1 GB / 2 GB | SPI Flash + MicroSD / eMMC; Linux character device | Linux GPIO character device (`/dev/gpiochip*` via `libgpiod`) | `linux-agent/blazepwifi-gpio-agent.sh` |
| **Windows SoftTimer Client** | x86 / x64 PC | Host Native | Host NTFS / Registry; `GuidDevinterfaceComport` | USB-to-Serial COM port (DSR / CTS modem control pin) | `BlazePisonet-SoftTimer` C# Serial Hardware |

---

## 3. Electrical Pulse Conditioning & Wiring Specifications

### 3.1 Coin Acceptor Models & Pulse Timing
Supported Philippine PisoWiFi coin acceptors:
- **Allan 123A (Single Coin / 1 Peso):** Generates 1 pulse per 1 PHP coin inserted.
- **Allan 926 / 633 / Multi-Coin Programmable:** Generates discrete pulse trains per coin denomination (e.g., 1 pulse for 1 PHP, 5 pulses for 5 PHP, 10 pulses for 10 PHP, 20 pulses for 20 PHP).
- **JY-923 / Multi-Currency Selectors:** Programmable pulse width and pulse frequency.

**Timing Invariants:**
- **Pulse Width:** 30 ms to 100 ms (nominal 40 ms – 60 ms).
- **Inter-Pulse Interval:** 20 ms to 60 ms.
- **Debounce Window (`coinDebounceMs`):** Default **40 ms** (configurable 10 ms – 100 ms). Edges arriving faster than debounce window are filtered out as mechanical or electrical noise.
- **Pulse Group Window (`pulseGroupMs`):** Default **400 ms** (configurable 150 ms – 1000 ms). An active pulse group remains accumulating until the line stays idle for `> pulseGroupMs`, at which point `pendingReady = true` is asserted.

### 3.2 Electrical Isolation Circuit (Mandatory)
Coin acceptors operate on **12V DC**, while ESP8266 and ESP32 GPIO inputs operate at **3.3V logic** (5V tolerant pins do not exist on ESP32, and 12V will permanently destroy the MCU).

```
  +12V Supply -----------------------------+--> Coin Acceptor VCC (+12V)
                                           |
  Coin Acceptor COIN Line (Open Collector) -+--> [ 1.5k Resistor ] --> Optocoupler Anode (Pin 1, PC817)
                                                                       Optocoupler Cathode (Pin 2) --> GND (12V)

  3.3V VDD (MCU) ----+--> [ 4.7k Pull-Up ]
                     |
  MCU GPIO (Coin) ---+--------------------> Optocoupler Collector (Pin 4, PC817)
                                            Optocoupler Emitter (Pin 3) --> GND (MCU 3.3V)
```
- **Active-Low Ingress:** With the optocoupler active, an incoming pulse grounds the MCU GPIO.
- **Reverse Polarity Support:** The firmware supports `coinActiveLow = false` for inverting optoisolator stages.

### 3.3 Coin Inhibit Circuit & Fail-Closed Output
To prevent users from dropping coins when the system is offline, unassigned, or booting:
- **Coin Relay Control:** The coin acceptor inhibit / power line is controlled via a relay driven by a transistor (2N2222 / 2N7002 / opto-triac).
- **Fail-Closed Condition:** `applyOutputs()` enforces:
  ```cpp
  bool accepting = controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady;
  ```
  If `WiFi` is down, `insertMode` is false (no active user session), `fsReady` is false (LittleFS write failure), or `pendingReady` is true (awaiting backend ACK for an earlier coin), the relay de-energizes immediately.

---

## 4. Current firmware state machine and event traceability

**Review lineage**
- Experiments main baseline: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`
- Parallel deny-only firmware candidate: PR #283, branch `cleanup/esp-firmware-hardening-and-quarantine-20261111`, exact parent head `830c355376380f9b5533d5cda2558beed41a593a`
- This scoped hardware child: PR #325, branch `phoenix/hardware-clear-pending-remove-verify-20261118`; it is a draft child of #283, not part of the separate #322 → #323 review-candidate stack.

**Current deny-only runtime**
1. Boot mounts LittleFS without format-on-failure. A mount failure leaves the pending store unavailable and keeps remote actuation denied; it does not format away uncredited evidence.
2. Pending recovery accepts exactly one valid candidate. Multiple, corrupt, truncated or ambiguous candidates are preserved and keep intake denied.
3. Register and poll are discovery/heartbeat requests only. Their response fields are ignored; `denyRemoteControl()` reasserts all actuation flags OFF. The current source does not call `applyRemoteConfig()` from these responses.
4. Automatic coin POST, retry and positive-response clearing are removed. There is no approved authenticated response/receipt-disposition contract, and coin admission remains disabled.
5. `appendQuarantineRecord()` validates the existing prefix fingerprint and exact appended suffix bytes in the host fixture. `quarantinePending()` is defined but has no active runtime callsite in this candidate.
6. In this child, `clearPending()` returns a status. It holds `pendingReady` true while checking filesystem readiness, every existing `/pending.dat`, `/pending.new`, and `/pending.bak` removal result, and post-removal absence. Any unverified removal applies the denied output state and returns false without clearing the in-memory event. `quarantinePending()` now returns false if this cleanup is not verified.

The resulting software flow is:

```text
coin edge / pending journal
        |
        v
pending event retained; remote admission remains DENY
        |
        +--> no automatic coin POST or retry
        |
        +--> operator / CORE reconciliation only
                 |
                 +--> future authenticated disposition contract required
```

This does not establish flash atomicity, cross-reboot no-replay, a protected freshness witness, or a positive financial receipt. LittleFS `exists()` cannot distinguish a genuinely absent path from every possible lower-level metadata I/O error; physical power-cut behavior remains unproven.

---

## 5. Threat and failure model — current evidence

| Failure / threat | Current firmware behavior | Evidence class and limitation |
|---|---|---|
| LittleFS mount failure | No auto-format fallback; pending store unavailable; actuation denied | Source-extracted host test; SIMULATED, not physical flash proof |
| Multiple / corrupt pending candidates | Preserve candidates and deny rather than selecting or deleting an ambiguous record | Pending-journal boot lab; SIMULATED |
| Quarantine append open/write/readback failure | Append returns false; pending event is not cleared | Quarantine append lab; SIMULATED |
| Pending candidate removal failure | Child #325 keeps RAM hold, applies outputs OFF and returns false when remove reports failure or a candidate remains | Exact-head focused CI is VERIFIED at checkout 18de1edae0a8b344ae600ff517f65b418d8ae3af: workflow run #44307404773, job 134812426061, SUCCESS. Append 13/13, boot recovery 14/14 and pending-clear 11/11 pass on both board fixtures; all are SIMULATED host tests. |
| Register/poll response injection | No response fields are accepted for remote control; no positive response authentication is implemented | Fail-closed source behavior only; positive authentication is NOT TESTED |
| Coin POST timeout / replay | Automatic coin POST/retry is disabled; no positive disposition is accepted | Source behavior only; durable financial replay remains BLOCKED |
| Coin pulse during synchronous poll | No positive coin admission is enabled in this candidate | Physical pulse capture and electrical recovery are NOT TESTED |
| Relay / LED state | Software output helper is deny-only in this branch | Host simulation is not GPIO voltage, contact-release or electrical acceptance |
| Brown-out / power cut | No physical durability conclusion | NOT TESTED |

The legacy QA-owned `tests/controllers.sh` and `v05_firmware_hardening_test.sh` contain static `response_sig`, `|register|` and `|poll|` token checks. Those strings do not prove a working authenticated response contract. PHX-HARDWARE does not edit those QA-owned files; PHX-QA must replace or qualify the stale assertions independently.

---

## 6. Target matrix — candidate status, not hardware support

| Target | Current classification | Remaining proof |
|---|---|---|
| ESP8266 NodeMCU / ESP-12 | Firmware source candidate; CI compilation is SHA-specific | Physical pulse, relay polarity, storage and power-cut acceptance |
| ESP32 DevKitC / WROOM-32 | Firmware source candidate; CI compilation is SHA-specific | Physical pulse, relay polarity, storage and power-cut acceptance |
| Ruijie RG-EW1200G Pro v1.1 | OpenWrt deployment candidate | Exact board/partition/bootloader recovery proof and noncustomer acceptance |
| EW1300G Pro / EW300 Pro | Candidate only | Board-specific DTS, partition and recovery proof |
| Boosteven ZLT-R281 | Experimental reference only | NAND layout, bad-block handling and recovery proof |
| Orange Pi Zero 3 | Linux GPIO software target | Physical GPIO/electrical acceptance and recovery |
| x86_64 appliance | Software/build target | Exact appliance boot/recovery and physical acceptance |
| Windows SoftTimer | Separate PHX-PISONET ownership | Not a PHX-HARDWARE firmware acceptance target |

A target build or host test is not proof that a device is supported, safely flashable, or field-qualified.

---

## 7. Required noncustomer hardware acceptance

All items below remain **NOT TESTED** unless a separate, exact-device evidence record is independently attached:

1. **150 controlled power cuts** across the approved noncustomer architectures and documented fault checkpoints.
2. **30-device, 24-hour soak** with continuous storage, pulse and recovery observation.
3. Electrical pulse conditioning, isolation, active-low/active-high relay behavior, contact release, brown-out and recovery measurements.
4. Repeated coin insertion and recovery with no customer coins or customer persistent media.
5. Reproducible per-target firmware artifacts, SHA256 provenance, reversible upgrade and recovery instructions.

Protected anti-rollback signer/witness, durable accounting/replay, reversible v1→v2 financial migration, target-supported release builds, independent QA and Master/release signoff are separate production gates. This audit does not satisfy them.

---

## 8. Defect identifiers and current disposition

| Defect | Current disposition | Evidence / owner |
|---|---|---|
| HW-P0-1 — response trust boundary | **DENY ONLY**. Register/poll response fields are ignored; no positive response signature contract is implemented. | PHX-CORE owns the canonical response envelope; PHX-QA owns independent golden vectors |
| HW-P0-2 — uncredited pending/quarantine evidence | Automatic coin POST/retry/clear remains disabled. Append is source-checked; pending removal now has a fail-closed result contract in child #325. No active quarantine callsite or cross-reboot no-replay proof is claimed. | PHX-HARDWARE #283 / #325; PHX-QA independent review pending |
| HW-P0-3 — legacy controller test assertions | Static token checks are not authentication evidence and are stale against the current deny-only producer/consumer. | PHX-QA owns `tests/controllers.sh` and `v05_firmware_hardening_test.sh` |
| HW-P1-1 — nonce generation | Board RNG source is present; no entropy measurement or hardware RNG health acceptance is claimed. | PHX-HARDWARE source only |
| HW-P2-1 — setup portal escaping | Escaping helper is present; no independent browser/XSS acceptance is claimed. | PHX-HARDWARE source only |

---

## 9. Pending-journal removal correction — PR #325

**Scope:** ESP32 and ESP8266 `clearPending()` plus its `quarantinePending()` caller, one hardware-owned source-extracted lab, the dedicated hardware-only workflow and this audit.

**Invariant implemented:** do not clear pulse count, nonce, target, pending-ready state or retry state until every existing pending candidate has a successful remove result and all three candidate paths are absent on the subsequent check. Filesystem-unavailable, failed remove, ambiguous false return, or a candidate that remains causes a false return, keeps the in-memory hold and reapplies logical outputs OFF. The quarantine caller now reports failure when cleanup is not verified.

**Test-first evidence**
- Expected RED against the original #283 source: [Actions run #44305881613](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44305881613), job `134807202118`, exact test-only head `1c528abfc8f03a5c0859eb245c6649eb9cd3b387`. The new harness failed because the production function was still `void clearPending()`; this reproduced the missing checked-removal contract. The existing append/readback lab completed 13/13 scenarios per board in that run.
- Intermediate harness failures after the source change exposed a missing applyOutputs stub and then an escaped-newline error in the generated C++ fixture. These were test-harness defects, not firmware regressions; the fixes are in cc6b0e49ce1b74c3c4882d325f83afdacce83fe7 and 26788b6f6178a70ab9e07d04fcb6eddb6e326d32.
- Exact-head focused CI is SUCCESS: run #44307404773, job 134812426061, checkout 18de1edae0a8b344ae600ff517f65b418d8ae3af. The append/readback lab passed 13/13 per board, pending-boot lab 14/14 per board, and the new pending-clear lab 11/11 per board. All are SIMULATED host fixtures. The full BlazePwifi build run #44307404941 is still in progress at this revision; no full matrix conclusion is claimed.

**Limitations:** source-extracted host tests are SIMULATED. They do not prove LittleFS metadata durability, flash erase/program atomicity, behavior during a physical power cut, or recovery after simultaneous storage faults. No coin, relay, GPIO, live money, signer, migration, flash or production action occurred.

---

## 10. Next exact actions

1. PHX-QA independently reviews the new pending-removal vectors and replaces the stale positive poll-signature assertion without weakening deny-only firmware.
2. PHX-MASTER confirms the #322 → #323 candidate stack separately; PR #325 remains a child of the parallel #283 branch and must not be merged or silently composed.
3. PHX-CORE defines the canonical authenticated response and event-bound receipt/disposition contract before any positive firmware admission is considered.
4. PHX-HARDWARE refreshes all heads and obtains exact-head focused CI plus independent review before proposing any integration.

**Standing disposition: OPEN / DRAFT / UNMERGED / SIMULATED ONLY / HARDWARE ACCEPTANCE NOT TESTED / PRODUCTION NO-GO.**
