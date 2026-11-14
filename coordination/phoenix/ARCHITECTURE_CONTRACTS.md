# Project Phoenix — Architecture Contracts & System Invariants

**Protocol Specification:** BLAZE-COMMS/1  
**Authority:** Master Auditor / Integration Coordinator (`PHX-MASTER`)  
**Scope:** Cross-subsystem integration rules for BlazePwifi (OpenWrt), BlazeRental (Android), BlazePisonet SoftTimer (Windows), ESP32/ESP8266 Firmware, QA Regression, and Release Engineering.

---

## 1. Financial Receipt Schema & Accounting Invariants

### 1.1 Single-Authority Durable Ledger
All money, coin pulses, prepaid member balances, and time grants must be authorized by a single durable authority per installation. In-memory mutations must NEVER precede persistent journal entry.

### 1.2 Canonical Receipt Schema
Every coin insertion, member time transfer, or rental payment event must emit a canonical receipt record structured as follows:

```json
{
  "$schema": "https://json-schema.blazing.systems/phx/v1/receipt.json",
  "event_id": "88888888888888888888888888888881",
  "protocol_version": "v2",
  "controller_id": "esp32-vendo-01",
  "target": "192.168.10.45",
  "amount_centavos": 500,
  "pulse_count": 5,
  "seconds_granted": 900,
  "timestamp_utc": "2026-11-13T19:00:00Z",
  "nonce": "a1b2c3d4e5f60718",
  "signature": "3045022100...P256-OR-HMAC-SIGNATURE",
  "replayed": false
}
```

### 1.3 Accounting Invariants
1. **Idempotent Replay Guarantee:**
   Resubmission of an already-committed `event_id` MUST return `{"ok": true, "replayed": true, ...}`. It MUST NOT credit additional balance, lengthen existing leases, or append a duplicate transaction record.
2. **Revocation / Admission Serialization:**
   Controller validation (`bp_controller_paid_allowed`) must occur under the serialization lock (`fd4` controller admission) before debit/credit execution. If an administrative change (`bp_controller_set`) disables a controller between initial client proof and writer lock acquisition, the transfer MUST fail closed with `{"ok": false, "error": "controller_disabled"}` without balance mutation.
3. **No Phantom Grants on Persistence Failure:**
   If storage sync (`fsync` or journal write) fails (e.g. disk full, EIO, power cut), the transaction MUST fail closed and revert all in-memory balance modifications.

---

## 2. Coin Pulse-to-Credit Pipeline

### 2.1 Hardware Timing & Electrical Rules
- **Pulse Width:** 30ms to 100ms per coin pulse.
- **Debounce Threshold:** Minimum 20ms stable signal before edge transition is recognized.
- **Inter-Coin Timeout:** 250ms quiet period marks completion of a pulse train before credit calculation.

### 2.2 Client-Side Response Verification (Firmware)
- ESP32 (`BlazePwifiVendo32.ino`) and ESP8266 (`BlazePwifiVendo.ino`) sketches MUST store `lastSentNonce` and verify `response_sig` returned by `/cgi-bin/vendo` for `register` and `poll` actions.
- Unauthenticated or signature-mismatched HTTP/CGI responses MUST be logged and ignored to prevent LAN spoofing.

### 2.3 Swallowed Coin Quarantine (LittleFS)
- If the router returns an error (e.g. `"coin window expired"`, `"controller disabled"`), coins MUST NOT be deleted uncredited.
- The firmware MUST append uncredited coin events to `/quarantine.log` in LittleFS with timestamp, nonce, target, pulse count, and error reason for physical operator auditing.

### 2.4 Win32 Native Serial Coin Input (Windows SoftTimer)
- SoftTimer MUST bind to hardware via `GUID_DEVINTERFACE_COMPORT` using a single verified, pinned `HANDLE`.
- The serial session MUST handle CTS state changes atomically to prevent CTS reconnection races (V4/V5 race conditions where reconnecting drops or attributes pulses to the wrong session).

---

## 3. Rental & Pisonet Client Time Grant Contracts

### 3.1 BlazeRental Android Client
1. **Dual Server-Authoritative Countdowns:**
   - Active Purchased Session Countdown: counts down remaining rental usage.
   - Insert Coin Reservation Countdown: temporary reservation window for inserting physical coins.
2. **Authenticated Status Before Persistence:**
   - BlazeRental MUST authenticate server status before persisting local lease state.
   - Stale-revision denial: Responses with outdated revision numbers must be rejected.
   - Zero write on authentication failure.
3. **Device Owner Provisioning:**
   - QR provisioning binds to published signed APK checksum and pins local TLS certificate.
   - Offline QR generator tools must preserve raw APK URLs and never substitute placeholder strings within valid HTTPS URLs.

### 3.2 BlazePisonet Windows SoftTimer
1. **Overflow-Denying Time Math:**
   - All time additions (`AddSeconds`, `BankCurrentTime`, `RestoreMemberTime`, `TransferMemberTime`) MUST pass through `TimeCreditMath.TryAdd` (non-negative, overflow-denying math).
2. **Persistence Integrity:**
   - `Storage.SaveState` must execute transactional writes before updating runtime state to prevent divergence between in-memory and on-disk balances.

---

## 4. Identity, Authentication & Rollback Defense

### 4.1 Cryptographic Identifiers
- **Controller Nonces:** Minimum 64-bit entropy derived from hardware RNG (`ESP.random()` on ESP8266/ESP32, `/dev/urandom` on Linux).
- **Controller Authentication:** HMAC-SHA256 with provisioned keys or P-256 ECDSA signatures.
- **Signer Provenance:** Production APK signing must follow immutable lineage (`BlazeRental-production-lineage2`). SoftTimer Windows executables must follow Authenticode signing pipeline gates.

### 4.2 Standalone Installer Rollback Defense
- Standalone installer backup directories MUST use unique collision-safe naming (timestamp + high-resolution entropy).
- File copy operations during backup MUST verify write success and file size/hash before proceeding with upgrades.

---

## 5. Build, Packaging & Release Promotion Hierarchy

All subsystems must be classified under one of the following five operational states:

| State | Definition | Gate Criteria |
|---|---|---|
| **NOT TESTED** | Source written or drafted without test execution | Default state for new PRs |
| **SIMULATED** | Host C++, mocked shell, or synthetic emulation passing | Passes local unit test suite |
| **CI VERIFIED** | Source-exact SHA green on official GitHub Actions workflow | Passes all lint, security, and integration workflows |
| **HARDWARE ACCEPTED** | Physical hardware testing verified on non-customer test bench | 150 real power cuts, 30-device 24h soak, physical coin test |
| **PRODUCTION READY** | Authorized release signed and approved by Master Auditor | All security, migration, and witness gates cleared |

> [!CAUTION]
> **Production Status: NO-GO**  
> Under no circumstances may code be promoted to commercial production, deployed to live routers, or flashed to customer hardware without independent durable accounting, anti-rollback witness, QA review, and physical hardware acceptance.
