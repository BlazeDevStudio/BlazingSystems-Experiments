# Project Phoenix: Hardware & Firmware Integration Audit (PHX-HARDWARE)

**Document Reference:** `docs/audits/HARDWARE_FIRMWARE_AUDIT.md`  
**Role:** PHX-HARDWARE (Hardware / Firmware Integration Engineer)  
**Classification:** LAB & CODE HARDENING ONLY — STRICT PRODUCTION NO-GO  
**Target Baseline:** `main` (`f4e8a89`) / `blazepwifi-v0.6.0-audit-foundation` (`2fbd2475`)  
**Active Working Branch:** `cleanup/esp-firmware-hardening-and-quarantine-20261111` (PR #283)

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

## 4. End-to-End State Machine & Event Traceability

```
[ Physical Coin Inserted ]
       │
       ▼
[ Electrical Optocoupler Pulse ]
       │ (Debounce Filter: millis() - lastEdge > runDebounceMs)
       ▼
[ In-Memory Pulse Accumulation ]
       │ (pendingPulses++, max 20)
       ▼
[ Atomic LittleFS Journal Write ]
       │ - Write struct to /pending.new
       │ - Flush & verify byte count == sizeof(PendingRecord)
       │ - Atomic rename /pending.dat -> /pending.bak
       │ - Atomic rename /pending.new -> /pending.dat
       │ - Remove /pending.bak
       ▼
[ Pulse Group Settlement ]
       │ (millis() - lastEdge > runPulseGroupMs)
       ▼
[ pendingReady = true ]
       │ (Relay drops to inhibit further coins during network transit)
       ▼
[ HTTP POST /cgi-bin/vendo (action=coin) ]
       │ - Sent with signedBody (key|action|id|nonce|pulses|target|key)
       ▼
[ Router Backend Admission & Credit ]
       │ - Atomic ledger write with idempotent event marker
       ▼
[ Router Response Received & Verified ]
       ├─► HTTP 200 "ok":true ──────────────────► clearPending() (delete /pending.dat)
       └─► Error ("coin window expired", etc.) ─► quarantinePending(reason) (write /quarantine.log)
```

---

## 5. Threat & Failure Model

| Failure Scenario | Physical / Electrical Effect | Firmware Defense Mechanism | Status |
|---|---|---|---|
| **Sudden Power Loss During Coin Fall** | MCU loses 3.3V rail while coin is physically traversing slot | If pulse group not completed, pulse lost before journal. If LittleFS write completed (`/pending.dat`), coin is recovered on next boot by `loadPending()`. | **VERIFIED** in LittleFS atomic rename logic |
| **Flash Write Failure / Brown-Out** | Power supply voltage sags below 2.7V during SPI flash write | `savePending()` detects incomplete write (`n != sizeof(r)`); sets `fsReady = false`; `applyOutputs()` de-energizes relay; halts intake. | **VERIFIED** in sketch error handling |
| **Network Loss / Lost Router ACK** | Coin accepted and journaled, but HTTP response lost | Event stays in `/pending.dat`. Retry loop fires every 900 ms with identical `pendingNonce`. Backend recognizes duplicate and ACKs without re-crediting. | **VERIFIED** in protocol specification |
| **Response Injection / Man-in-the-Middle** | Spoofed LAN packet attempts to inject remote configuration | Client-side response signature verification (HW-P0-1) checks `response_sig` against keyed HMAC over request nonce. Discards untrusted replies. | **VERIFIED** in `v05_firmware_hardening_test.sh` |
| **Uncredited Swallowed Coin** | Coin window expires before user drops coin; backend returns error | Pre-v0.5 firmware called `clearPending()` (silent drop). Hardened firmware (HW-P0-2) calls `quarantinePending(reason)`, appending record to `/quarantine.log`. | **VERIFIED** in `v05_firmware_hardening_test.sh` |
| **Weak Nonce / Predictable PRNG** | Nonce predictable if based on `micros()` | HW-P1-1 replaces predictable microsecond low-word with dual 32-bit hardware RNG reads (`ESP.random()`). | **VERIFIED** in `v05_firmware_hardening_test.sh` |
| **Setup Portal XSS** | Malicious SSID or server string injected via captive portal | HW-P2-1 applies `htmlEsc()` escaping `&`, `'`, `"`, `<`, `>` to all form fields. | **VERIFIED** in `v05_firmware_hardening_test.sh` |

---

## 6. Viable Image & Firmware Target Matrix

| Device / Architecture | Flash / RAM | OpenWrt Target | Viability / Packaging Status | Field Qualification Notes |
|---|---|---|---|---|
| **Ruijie RG-EW1200G Pro v1.1** | 16 MB NOR / 128 MB DDR3 | `ramips/mt7621` (OpenWrt 25.12.5) | **Primary Target**; Sysupgrade & recovery initramfs generated in CI. | Tight flash budget (16 MB). Requires lean BusyBox/UCI image without heavy runtime components. |
| **Ruijie EW1300G Pro / EW300 Pro** | 16 MB / 128 MB | `ramips/mt7621` | **Candidate**; Requires board-specific DTS and partition verification before image build. | Do not flash stock vendor firmware without serial/TFTP unbrick proof. |
| **Boosteven ZLT-R281** | 128 MB NAND / 128 MB RAM | `ramips/mt7621` | **Experimental Reference**; Custom OpenWrt port exists in archive. | NAND flash bad block management required. Bootloader recovery must be kept on file. |
| **Orange Pi Zero 3** | MicroSD/eMMC, 1GB–2GB RAM | `allwinner/h618` (AArch64) | **Supported SBC**; Linux GPIO agent verified via `libgpiod`. | High performance, capable of acting as both router/gateway and coin controller. |
| **x86_64 PC / Appliance** | Dual SATA/NVMe, >= 2GB RAM | `x86/64` (BIOS + UEFI) | **Supported Edge Server**; Combined image builds in CI. | Used for high-volume multi-slot internet café (Pisonet) installations. |

---

## 7. Physical Durability & Non-Customer Acceptance Gates

In accordance with `V060_PHYSICAL_DURABILITY_ACCEPTANCE.md`:
1. **150 Controlled Power-Cut Trials:**
   - 3 architectures (Ruijie MIPS, Orange Pi AArch64, x86_64).
   - 5 physical fault checkpoints (pre-journal, during-journal, post-journal/pre-HTTP, post-HTTP/pre-ACK, during-ACK).
   - 10 repeated trials per checkpoint per architecture.
2. **30-Device 24-Hour Soak:**
   - Continuous operation under load without kernel panic, memory leak, or filesystem corruption.
3. **Traceability Contract:**
   - Verification using `tools/v060_physical_evidence_contract.py` requiring genuine commit SHA-1 and SHA-256 package digests.

---

## 8. Defect Identifiers & Hardening Status

| Defect ID | Description | Resolution in Branch | Test Verification |
|---|---|---|---|
| **HW-P0-1** | Client-Side Response Signature Verification | Captured `lastSentNonce` and verified `response_sig` on `register` and `poll`. | `v05_firmware_hardening_test.sh` |
| **HW-P0-2** | Uncredited Coin Quarantine | Swallowed coins saved to `/quarantine.log` with timestamp, nonce, target, and pulses. | `v05_firmware_hardening_test.sh` |
| **HW-P1-1** | Full Hardware RNG Nonce on ESP8266 | Removed `micros()`; uses two 32-bit `ESP.random()` words. | `v05_firmware_hardening_test.sh` |
| **HW-P2-1** | Setup Portal HTML Escaping | Added `htmlEsc()` for SSID, server, and ID. | `v05_firmware_hardening_test.sh` |
| **HW-P0-3** | Controller Test Suite Wiring | Hooked `v05_firmware_hardening_test.sh` into `controllers.sh`. | `controllers.sh` execution pass |
