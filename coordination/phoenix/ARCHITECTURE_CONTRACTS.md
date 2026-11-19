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

### 2.1.1 Relay/LED OFF preload before output enable — provisional software invariant (2026-11-18 UTC03)

For runtime pin reassignment on both ESP32 and ESP8266, the relay and LED must be placed at their polarity-correct logical OFF level before the new output driver is enabled:

1. Drive the old relay and LED pins logically OFF using the old polarity before changing pin assignments.
2. Assign the new coin, relay and LED pin numbers.
3. Preload the new relay and LED logical OFF levels while those pins are not yet configured as OUTPUT.
4. Only then call `pinMode(..., OUTPUT)`.
5. Attach the coin interrupt after the output pins are configured.
6. Reassert logical OFF after output enable.

This is especially important for active-low relay wiring, where a default LOW output latch can energize the relay during an OUTPUT-mode transition. HARDWARE owns the firmware implementation; QA owns independent source-linked verification. This invariant does not authorize relay actuation, coin admission or financial disposition.

Source: HARDWARE PR #322, source/test SHA `7ba56c1ba92dcffa2555e4cce10d3010c3afaf5b`; current docs-only PR head `50d93e0de3d682550b6f02fb43484e76ad9c7e08`. Exact-head focused output-order run [44232877611](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877611) passed on both boards; logs report `OUTPUT_SEQUENCE_PASS` for ESP8266 and ESP32 and the workflow explicitly classifies evidence as SIMULATED ONLY. The companion quarantine/readback run [44232877649](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877649) also passed.

The current-head Full build [44232877624](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877624) is not a Full pass: its validation job failed at the inherited QA-owned `Missing poll signature check`; 14/14 target/platform jobs completed SUCCESS; 12 downstream simulation/update/publish/signing jobs SKIPPED after the validation failure. Physical GPIO voltage, relay transient, contacts, electrical pulse behavior and hardware acceptance remain NOT TESTED.

### 2.2 Client-side response trust boundary — current deny-only state (2026-11-18 UTC08)

- `bp_check_vendo_sig()` checks the incoming request tuple against a keyed SHA-256 concatenation. This is not standard HMAC, is request-side only, and does not authenticate the JSON body returned to the controller.
- On the current Experiments development producer, `bp_json()` only emits HTTP headers plus the supplied JSON body. The `register|ping`, `poll`, and `coin` response bodies do not include `response_sig`.
- The current HARDWARE #323 candidate is deliberately fail-closed: both board implementations return `false` from `acceptPollResponse()` and `coinPostDispositionVerified()`. The register-tuple check also remains false when the response has no `response_sig`; remote configuration remains disabled.
- Do not describe response verification as implemented, and do not require a positive `|poll|` signature expression, until PHX-CORE defines a versioned response envelope and canonical serialization, PHX-HARDWARE implements the approved consumer, and PHX-QA independently verifies positive/negative golden vectors at the same pinned source SHA.
- Until that gate is met, poll admission and coin POST disposition remain hard-deny. A missing signature is not a reason to weaken firmware or clear pending evidence.

See §6.23 for exact source, candidate, fixture and CI evidence.

### 2.3 Swallowed Coin Quarantine (LittleFS)
- If the router returns an error (e.g. `"coin window expired"`, `"controller disabled"`), coins MUST NOT be deleted uncredited.
- The firmware MUST append uncredited coin events to `/quarantine.log` in LittleFS with timestamp, nonce, target, pulse count, and error reason for physical operator auditing.

### 2.3.1 Durable one-shot coin POST attempt marker (provisional; CORE/QA review required)

A firmware coin POST is an ambiguous financial side effect: a timeout or lost reply does not prove that the server did not commit the event. The client MUST NOT automatically replay an event after an uncertain attempt.

1. Before the first network dispatch, persist a LittleFS attempt marker bound to the exact pending record (pulse count, nonce, and target). Flush/close it, read it back through the same bounded record/checksum validator, and compare every bound field. If write, close, readback, or comparison fails, deny dispatch and keep outputs fail-closed.
2. The marker is one-shot. A matching, malformed, mismatched, truncated, or orphan marker discovered at boot MUST block automatic replay and preserve all evidence for operator reconciliation. Do not infer “not sent” from a missing HTTP reply.
3. Remove the pending record first and the attempt marker last, only after an authoritative receipt or a separately durable quarantine disposition has been verified. If either removal fails, retain the remaining evidence and keep admission blocked.
4. A power loss after marker commit but before request transmission is deliberately treated as ambiguous; recovery is operator/CORE reconciliation, not an automatic retry. This conservative client fence does NOT replace server-side idempotency, stable event identity, or durable receipt replay protection.
5. The source-extracted fake-LittleFS lab is simulation evidence only. PHX-CORE must review server receipt/replay semantics; PHX-QA must independently verify the exact same source SHA; native flash/power-cut evidence remains mandatory.

This subsection records the owner-implemented #315 behavior as a **provisional cross-subsystem invariant**, not a claim of financial acceptance or production approval.

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


## 6. Open P0 poll-response trust and rejected-event durability contract (2026-11-16 UTC22)

**Status: MASTER DECISION (2026-11-17 UTC02): keyless/bootstrap is never coin authority.** This admission invariant is final; implementation acceptance remains pending PHX-CORE / PHX-HARDWARE owner review and independent PHX-QA exact-head verification. See [HARDWARE_POLL_CONTRACT_AND_STACK_HOLD_20261116_UTC22.md](HARDWARE_POLL_CONTRACT_AND_STACK_HOLD_20261116_UTC22.md) for exact PR heads, CI observations and source-diff evidence.

### 6.1 Keyless poll responses cannot authorize coin intake

- An empty or unprovisioned controller key is **not** an authentication success.
- No keyless `ok=true` poll response may set coin admission, active target or relay authorization.
- Coin intake can be enabled only after a fresh response verifies under the approved provisioned key/signature and target/freshness checks.
- Missing, malformed, expired or mismatched authentication must leave intake denied and must not reuse a previous positive poll.
- A separate setup/bootstrap path may remain available, but it cannot authorize coin admission.

### 6.2 Failed quarantine persistence must survive reboot safely

- If the controller rejects an event and local quarantine persistence fails, the event must remain durably pending or durably marked for reconciliation before any process can retry or credit it after reboot.
- A RAM-only `journalRecoveryRequired` latch can inhibit same-boot retries but is not proof of cross-reboot non-replayability.
- While the event's durable disposition is ambiguous, deny retry, duplicate POST, credit and relay admission.

These are **shared interface/accounting invariants**, not permission for PHX-MASTER to edit firmware or financial source. PHX-CORE owns financial/replay semantics; PHX-HARDWARE owns firmware/journal implementation; PHX-QA independently verifies positive, negative and reboot/failure cases. Do not mark either invariant implemented or accepted until the owners agree on the exact contract and QA verifies the combined exact SHA.


### 6.3 Historical poll producer/consumer comparison — 2026-11-16 snapshot; current #323 state in §6.23

This section preserves the earlier #315 comparison as historical evidence. It does not describe the current #323 deny-only candidate. Use §6.23 for the current producer/consumer refs and QA fixture status.

The keyless-deny invariant does not by itself establish that the current server can authorize a provisioned controller. Exact poll-action inspection at this snapshot found:

| Ref | cgi-bin/vendo blob | Poll response signature |
|---|---|---|
| Experiments main f4e8a891... | 2e3a1430d08cc6606429a042df3b5848f53c7267 | Absent |
| Experiments v0.5.3 development aad3aade... | a1c19180385e618c412b4af21c0e91c1f47da1dd | Absent |
| Experiments v0.6 audit-foundation 2fbd2475... | db58041c0575ad0a1101d99cb85403e03c8dcb22 | Absent |
| COE integration PR #26 b382d233... | 0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e | Present; derived candidate |

The source branches emit poll JSON without response_sig. The COE candidate defines vendo_poll_sig and includes response_sig in its poll response. This is a real source/destination behavior difference, not byte parity or proof of semantic equivalence.

The current HARDWARE #315 consumer expects a provisioned cfg.key and verifies response_sig against the ordered fields key, poll, controller id, request nonce, insert bit, target nonce, expiry, key. The COE candidate's producer expression has the same apparent field order using secret, id, nonce, insert, target and expires. This is only a structural comparison: no shared golden vector has been independently executed, and the key/id/nonce binding, canonical serialization and digest implementation still require PHX-CORE and PHX-QA verification.

The observed candidate expression is a keyed SHA-256 construction with key material at both ends; do not describe it as standard HMAC. PHX-CORE and PHX-QA must review the cryptographic construction and publish exact positive/negative test vectors before treating it as an approved shared protocol. Do not silently change the algorithm in one client or copy the derived candidate over canonical source.

Until a canonical producer emits the exact approved authenticated poll response and independent QA verifies both sides at pinned SHAs, configured-key coin admission remains fail-closed. No keyless/bootstrap fallback is permitted. This section does not authorize source migration or firmware edits by PHX-MASTER.


### 6.4 Remote configuration has a separate authorization domain

**Status: MASTER HOLD — implementation and exact cryptographic schema pending PHX-CORE / PHX-HARDWARE / PHX-QA review.**

The poll-admission signature authenticates only the poll admission tuple. The register/ping response signature currently authenticates only its register tuple (action, controller ID, request nonce and server time). Neither signature authenticates the returned controller configuration object.

At the historical HARDWARE PR #315 head `58ade5df83df0c6894dd8d1e2a70617b90dae374`, both ESP `connectSta()` implementations still initialize `sigOk=true`, conditionally verify a register `response_sig` only when a key is configured, then call `applyRemoteConfig(r)` on `ok:true`. Consequently:
- an empty key leaves the register response accepted for configuration application without signature verification;
- a configured-key register signature does not bind the `controller` configuration fields in the COE #26 candidate producer;
- the poll-path config-isolation fix does not close this separate register path.

See [POLL_CONFIG_REGISTER_TRUST_BOUNDARY_AUDIT_20261117_UTC03.md](POLL_CONFIG_REGISTER_TRUST_BOUNDARY_AUDIT_20261117_UTC03.md) for exact file links, heads and CI evidence.

**Binding rules:**
1. Until a separate configuration-authentication envelope is approved and independently tested, `applyRemoteConfig` MUST NOT be invoked from poll or register/ping responses. Keep remote configuration disabled; do not reuse admission or register signatures as a configuration signature.
2. An empty/unprovisioned key never authorizes remote configuration.
3. A future configuration signature must use a domain separate from poll admission and bind a deterministic canonical representation of schema/version, controller identity, request nonce, monotonic configuration revision, freshness/expiry data, key identity/version when applicable, and every behavior-changing configuration field (enable flags, GPIOs, polarity, debounce/timing, pulse grouping, retry settings and future additions).
4. PHX-CORE owns the exact schema and cryptographic construction; PHX-QA independently approves canonical positive/negative golden vectors. Do not describe ad-hoc keyed SHA-256 concatenation as HMAC.
5. Verify identity, signature, freshness, revision and all field bounds before mutation. Persist the complete configuration atomically before runtime activation. Any failure preserves the prior configuration, applies no partial fields and leaves coin admission denied.

This is a shared interface contract and coordination hold, not authorization for PHX-MASTER to edit firmware or CORE source. The exact schema/algorithm remains pending owner review.


### 6.4.1 Live source/staging correction — 2026-11-17 UTC04

The register-path finding above was confirmed at the earlier #315 snapshot 58ade5df83df0c6894dd8d1e2a70617b90dae374. It is now corrected on the current PHX-HARDWARE owner branch #315 head 75dc5f0b888f16e2c85e4321f62df4685639ad33: both sketches retain one dormant applyRemoteConfig definition and have no response call sites. Both connectSta() implementations keep register-tuple authentication fail-closed and do not apply returned configuration.

The exact-head focused source-extracted CI run 44013351048 passed the register-config denial lab 7/7 per board. This is simulated/host CI evidence only. The full run 44013351035 still fails in the QA-owned poll extractor because acceptPollResponse() is not extracted; the full workflow is not green and no physical acceptance is established.

**The COE integration candidate remains blocked.** At PR #26 head b382d233ff06c8791b1028bed3c617cc7b670d12, both destination sketches still have two applyRemoteConfig(r) call sites and two sigOk=true defaults. Positive keyless register or poll replies can reach the configuration mutator. The source-side correction has not been propagated to the destination candidate. Do not treat the #315 focused pass as evidence for COE #26.

The separate configuration authorization domain remains the governing invariant: remote configuration stays disabled until PHX-CORE defines the canonical envelope and PHX-QA independently verifies it. For the current destination candidate, the immediate safe requirement is to remove response-driven configuration application rather than reuse the register or poll admission signature.

See REMOTE_CONFIG_MIGRATION_STAGING_AUDIT_20261117_UTC04.md for exact blob IDs, license and manifest scope, current role CI, and reproduction steps. This correction changes no source ownership and authorizes no copy or merge.


### 6.4.2 Current COE staging still contains the pre-correction paths — 2026-11-17 UTC05

The current HARDWARE owner branch #315 at 75dc5f0b888f16e2c85e4321f62df4685639ad33 has the remote-configuration correction on both boards: applyRemoteConfig() is definition-only, connectSta() does not apply returned configuration, and acceptPollResponse() defaults signatureOk=false. Exact source blobs: ESP32 38a2d239eed6af876d421f9f908bbb62b3ae27e1; ESP8266 f59e624ae2da04bddc70ddc2809bf6d8ff486aac.

COE integration #26 at b382d233ff06c8791b1028bed3c617cc7b670d12 still contains three applyRemoteConfig() occurrences and two bool sigOk=true defaults per board, including register and poll response call sites. Exact destination blobs: ESP32 3cc7ec54b476943dc04a8d1af5e2df5fe054e422; ESP8266 c8be98f72596681e36a3ad1f8939bf8046c96887. This candidate also retains a POST /quarantine/clear handler that deletes /quarantine.log and returns HTTP 200 on both boards; the current #315 source returns HTTP 403 and contains no quarantine-log deletion call.

Keep COE #26 blocked for Hardware migration. See HARDWARE_STAGING_PARITY_AUDIT_20261117_UTC05.md for exact lines, test identities, modes, CI and owner actions. No source/destination copy or firmware edit is authorized by this finding.
 
### 6.5 Quarantine evidence is non-deletable until authenticated reconciliation — 2026-11-17 UTC05

The quarantine log records unpaid coin events and is reconciliation evidence. A network POST must not erase it or claim success without an approved authenticated operator recovery contract, a durable receipt/reconciliation record, and independent negative/positive tests. Current owner source #315 responds HTTP 403 to POST /quarantine/clear and does not call LittleFS.remove("/quarantine.log"). The COE #26 candidate still deletes the log and returns HTTP 200 on both boards, with no explicit setup-AP-origin guard in those handlers.

A future clear/reconciliation flow requires owner-approved identity and authorization, immutable export/readback, durable receipt linkage, replay/idempotency rules, failure atomicity, and independent QA. Until then, preserve the evidence and deny deletion. This contract does not authorize PHX-MASTER to edit firmware or approve a physical/financial operation.

## 6.6 Coin POST disposition requires an event-bound authenticated receipt — 2026-11-17 UTC07

The current HARDWARE #315 source deliberately returns DENY from `coinPostDispositionVerified()` for every response. The present endpoint uses plain HTTP and no approved event-bound signed receipt/disposition contract exists. This is a safe hold, not a completed receipt protocol.

**Authority invariant:** raw HTTP status, root `ok:true`, root `ok:false`, nested `receipt.ok:true`, error text, timeout, empty body or transport success is never financial authority. After the durable `/pending.attempt` marker is written, flushed, closed and read back, any missing/invalid/ambiguous disposition must retain the pending journal and marker, set the recovery hold, keep outputs fail-closed, and deny automatic replay. It must not clear the pending event or delete reconciliation evidence.

Before firmware may accept a coin POST result, PHX-CORE must define a domain-separated authenticated receipt that binds at minimum: protocol/domain version, controller identity, key version, unique event/receipt ID, event nonce, target nonce, pulse count, server ledger epoch/sequence, freshness/expiry, disposition enum and reason. The owner-approved cryptographic construction and canonical serialization must have positive and negative golden vectors. Do not substitute an ad-hoc SHA-256 concatenation or reuse the poll/register admission signature.

Server handling must be idempotent for a repeated event ID and return the same authoritative receipt without duplicate credit. The controller must verify signature, identity, key version, event/target/pulse binding, freshness, sequence and disposition. An accepted receipt can clear pending state only after the receipt and resulting state are durably committed. A rejected receipt can transition to quarantine only after its authenticated negative disposition is durably recorded with reconciliation evidence. Every unknown outcome stays in a recovery hold until operator reconciliation; never automatically replay.

This contract does not authorize remote configuration, which remains a separate authorization domain. PHX-CORE owns the protocol proposal; PHX-QA owns independent vectors and failure tests; PHX-HARDWARE implements only after those owners complete review. This is a Master-level fail-closed requirement, not an implementation claim or release approval.

Exact source/staging evidence and current CI are in [COIN_POST_DISPOSITION_AUTHORITY_AUDIT_20261117_UTC07.md](COIN_POST_DISPOSITION_AUTHORITY_AUDIT_20261117_UTC07.md). COE #26 remains blocked; no firmware copy or destination edit is authorized. **PRODUCTION NO-GO.**



## 6.7 Legacy poll-signature fixture must not override default-deny — 2026-11-17 UTC09

The current PHX-HARDWARE #315 source at `84fe6b790139d147f330f13a40b3ae3e89a7042d` deliberately makes `acceptPollResponse()` return DENY on both ESP8266 and ESP32, clearing the candidate insert/target state. `coinPostDispositionVerified()` also remains default-deny. The derived `response_sig` poll construction is not an approved authorization contract; do not reintroduce it to satisfy an inherited test.

The inherited `tests/v05_firmware_hardening_test.sh` still requires `|poll|` and simulates a positive poll signature. It is invoked by `tests/controllers.sh` and is unchanged in PR #315. Current Full validation fails at this stale assertion before reaching the separate v0.6 extractor omission. This is a real CI failure and a test-contract mismatch, not proof that default-deny firmware should be weakened.

**QA contract:** replace the positive legacy assertion with source-linked negative cases for empty/unprovisioned key, provisioned key with unapproved/forged/missing/malformed/stale response, root/nested `ok:true`, mismatched target/nonce and ambiguous responses. Assert intake remains disabled, candidate target is cleared, no credit/relay/LED output is authorized, and pending/attempt evidence is preserved. Keep positive acceptance vectors blocked until PHX-CORE publishes the canonical producer/consumer contract and PHX-QA independently approves both-board golden vectors. PHX-QA owns test files; PHX-HARDWARE owns firmware. **PRODUCTION NO-GO.**

## 6.8 Appliance ULA prefix must be valid and deployment-scoped — 2026-11-17 UTC11

COE #26 and its current release child #31 both emit the hard-coded option ula_prefix 'fd00:db8:blaze::/48'. The blaze hextet is not hexadecimal. The current profile has no networking.ula_prefix field, and the current #31 packager tests have no ULA/IPv6 assertions. The #31 interface/VLAN validation change does not address this independent defect.

**Contract:** generated ula_prefix must be a strictly parsed RFC 4193 ULA in fd00::/8 with /48 prefix length. Reject malformed, non-ULA, host-bit-set, wrong-length and missing values before any staged UCI write. Do not substitute one globally hard-coded prefix: define a reviewed profile input or deployment-time generation/persistence policy that gives each independent LAN/site a unique prefix while devices on the same LAN share it. PHX-RELEASE owns packager/profile/tests; PHX-CORE and COE owner define provisioning; PHX-QA independently verifies exact-head output; PHX-HARDWARE validates only after correction. Master owns this contract and routing, not implementation.

See [APPLIANCE_IPV6_ULA_PREFIX_CONTRACT_AUDIT_20261117_UTC11.md](APPLIANCE_IPV6_ULA_PREFIX_CONTRACT_AUDIT_20261117_UTC11.md). Keep #26/#31 draft. **PRODUCTION NO-GO.**


## 6.9 ULA prefix is installation identity, not hardware profile — 2026-11-17 UTC13

The shared router profile describes hardware capabilities and is reused across independent installations. A site ULA prefix is deployment identity, not a model property. Do **not** add one static `networking.ula_prefix` to the shared hardware-profile schema as the default fix.

A generic appliance image must not embed a globally shared ULA placeholder. The installation/first-boot authority must create a locally assigned RFC 4193 ULA /48 for that installation, persist it durably before network services consume it, and reuse it across reboot, upgrade and restore. Devices on the same LAN/site share that prefix; independent sites receive independently generated prefixes. Require canonical strict parsing, locally assigned `fd00::/8`, exact `/48` length and network alignment.

The implementation owner must choose and verify one target-supported mechanism: (1) first-boot generation plus atomic persistence, or (2) a validated deployment-specific prefix input when an artifact is intentionally unique to one site. Do not silently fall back to a fixed example, regenerate on each build/boot, or assume netifd supplies a valid prefix without target evidence. If neither mechanism is present, keep integration blocked.

**Owner routing:** PHX-RELEASE owns packager/first-boot implementation and tests; the COE integration owner owns destination staging; PHX-QA independently verifies valid/invalid inputs and generated UCI; PHX-HARDWARE validates target behavior only after correction and authorization. PHX-MASTER owns this cross-repo contract and gate only. Exact evidence is in [COE_ULA_PREFIX_CONTRACT_REVALIDATION_20261117_UTC13.md](COE_ULA_PREFIX_CONTRACT_REVALIDATION_20261117_UTC13.md). **PRODUCTION NO-GO.**


### 6.9.1 Appliance-local randomness is not a site authority — 2026-11-19 UTC11

For this contract, **installation means the LAN/site identity boundary, not each physical router independently**. A first-boot script that independently samples a fresh 40-bit Global ID on every appliance can create different /48 prefixes for two routers on the same site. That does not satisfy the same-site sharing invariant, even if each local UCI write is syntactically valid and durable.

Before acceptance, the selected authority must allocate one site prefix and make the same canonical value available to every appliance on that LAN/site. It must survive reboot, upgrade, backup and restore. Concurrent first boots must not create competing site identities. Failed allocation, write, commit or readback must leave network services blocked and preserve unrelated UCI state. No appliance may silently replace a valid site prefix with a new random value.

Independent QA must prove:
1. Two appliance instances attached to one site receive the same prefix.
2. Two independent sites receive distinct prefixes.
3. Concurrent first-boot attempts converge on one durable value or fail closed.
4. Reboot, upgrade, backup and restore preserve the exact prefix.
5. Failed UCI stage, commit or readback leaves no partial/conflicting identity and preserves unrelated network settings.

A per-appliance first-boot random generator is therefore a local allocation primitive only; it is not evidence of site-level allocation or distribution. This contract does not select the authority design. PHX-CORE and the COE integration owner choose durable authority/distribution; PHX-RELEASE implements it; PHX-QA independently verifies it; PHX-HARDWARE performs target validation only after approval. Until the owner decision and exact-head tests exist, keep COE ULA integration blocked.


## 6.10 ImageBuilder build execution must actually be sandboxed — 2026-11-17 UTC13

ImageBuilder Makefiles and their recipes are executable inputs that can create symlinks and write files. Installing bubblewrap or proving that a trivial 'bwrap ... true' namespace probe succeeds is not containment. The actual Make/ImageBuilder subprocess that processes the candidate workspace must run inside the approved filesystem boundary.

Minimum contract: only a disposable build workspace may be writable inside the namespace; source inputs and toolchain paths are read-only; operator-owned files and sentinels remain outside the writable bind set or are read-only; caller UID/GID and ownership semantics are preserved; the build fails closed when the namespace cannot be established. Network isolation is a separate property and must not be claimed unless separately configured and verified. Do not expose secrets or write credentials into the build workspace.

The regression must execute a synthetic malicious Makefile inside the same sandbox boundary and prove that a symlinked firmware output cannot change an external sentinel. The test harness must invoke the sandbox wrapper, not merely check that bwrap exists. A standalone capability probe followed by a direct Python/test invocation is not sufficient.

Current COE RELEASE #31 exact head 19fc87988e55f47e8c6a512e51b470a91abbf816 has sandbox run 44098939249 failing at the UID/GID probe; packaging tests are skipped. The workflow's subsequent Python test step is direct, and the test launches the generated shell wrapper directly. An earlier exact head edf4a37 run 44098400955 observed the synthetic external sentinel overwritten. Exact source, job and log evidence: COE_IMAGEBUILDER_SANDBOX_EXECUTION_BOUNDARY_AUDIT_20261117_UTC13.md.

PHX-RELEASE owns the wrapper/workflow/test correction; PHX-QA independently verifies the exact final head. PHX-MASTER owns this cross-repo invariant and release gate only. Keep COE #31/#26 draft and **PRODUCTION NO-GO**.

## 6.11 CI test-harness containment is not generated-build enforcement — 2026-11-17 UTC14

At COE RELEASE #31 final head d45b84c67dc587fca6226662cb1d8bc59bdb11ae, the test helper invokes run_imagebuilder_sandbox.py when PHX_REQUIRE_BWRAP=1, and the dedicated workflow sets that variable. This proves only that the synthetic test harness attempts to execute its generated wrapper under the runner.

The production packager blob fd558928b2869ce1f4b2cb2776b405b4b723b310 contains no bubblewrap or runner invocation in generate_build_script(). The generated build script therefore does not enforce the same boundary when an operator runs it directly. Runtime build execution remains NOT SANDBOX-ENFORCED / UNKNOWN until RELEASE either integrates the runner into the generated entrypoint or documents and independently verifies a mandatory external isolated build-host boundary.

The current runner explicitly passes --share-net; network isolation is not present or claimed. Its read-only host-root bind is a write boundary, not a confidentiality boundary. Do not describe this as a full sandbox or run untrusted build inputs on a secret-bearing host. PHX-RELEASE owns implementation; PHX-QA independently verifies the actual supported build invocation; PHX-MASTER owns this contract and release gate only.


## 6.12 Generated shell templates require runtime-path verification — 2026-11-17 UTC15

A successful `sh -n` check proves only that the shell parser accepts the generated file; it does not prove that each generated command path executes correctly. When Python emits a shell script from a triple-quoted template, a literal `\\n` is not a line break: it becomes backslash-plus-`n` in the emitted script. Do not use escaped line-break text inside a multiline template unless the resulting shell bytes are explicitly intended and tested.

For generated ImageBuilder wrappers, require both shell syntax validation and actual execution of each security-relevant branch using a disposable Makefile. In particular, the empty-image denial must return its expected nonzero status and diagnostic, create no release manifest, and preserve external sentinels. A syntax-only test is not a substitute for the runtime regression.

At COE RELEASE #31 exact head `d45b84c67dc587fca6226662cb1d8bc59bdb11ae`, packager blob `fd558928b2869ce1f4b2cb2776b405b4b723b310`, source line 495 contains literal `\\n` sequences between the empty-image guard and checksum command. A minimal local reproduction returned `sh -n=0` but execution exit 2 (`Syntax error: Bad fd number`). The exact-head sandbox workflow [#44104956173](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104956173), job `134126241456`, was IN_PROGRESS at last read; no final CI result is claimed.

PHX-RELEASE owns the correction on COE #31; PHX-QA independently verifies the exact corrected head. PHX-MASTER owns this contract and integration gate only. Keep #31/#26 draft; no migration or release. **PRODUCTION NO-GO.**


### §6.12 exact-head CI follow-up — 2026-11-17 UTC15:14Z

COE #31 sandbox run [#44104956173](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104956173), job `134126241456`, completed `CANCELLED` at exact head `d45b84c67dc587fca6226662cb1d8bc59bdb11ae`. The log shows 15 packaging tests returned `ok`, including the syntax-only generated-wrapper check, then the operation was canceled at 15:14:22Z. The runtime empty-firmware test was not reached. Do not report this as a source-test failure or pass; it is incomplete evidence. Require a non-cancelled exact-head runtime execution after RELEASE corrects the literal `\\n` template sequence, then independent QA review.

## 6.13 Generated-wrapper newline correction is source-only until exact-head sandbox CI completes — 2026-11-17 UTC15

The earlier literal-backslash-n defect in COE RELEASE #31's generated shell template is corrected in the current source candidate. The release-owned test-first commit is [293a006d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/293a006d6809493ba164f10d1e2917e8979e1633), the source correction is [b14841e7](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b14841e75d57144f8c72867ef54fdff796b9483d), and the current handover head is [06d8b7c5](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/06d8b7c593f8e139891a6a659bf79e694ee229d5). At that exact head, packager blob `66fc283eb52add75caee6131b78dcadbb5d8a7fc` contains actual multiline shell template text, and test blob `3e917c30654ce629391c3fbd864d5b671b0a2e46` contains `test_generated_wrapper_emits_empty_image_guard_as_real_shell_lines`.

**Current exact-head evidence:** sandbox run [44113058229](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058229), job `134155724688`, is still IN_PROGRESS; do not report a PASS or failure until it concludes. Shared/hardware run [44113058271](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058271) and case-collision run [44113058276](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058276) are SUCCESS, scoped only.

A separate execution-boundary blocker remains: `generate_build_script()` still emits a wrapper that changes to `$BUILD_DIR` and invokes the interpolated ImageBuilder command directly. It does **not** invoke `run_imagebuilder_sandbox.py` or bubblewrap. The dedicated workflow sets `PHX_REQUIRE_BWRAP=1`, and the test harness invokes the helper, but that proves only test-harness containment—not that an operator's generated build entrypoint is sandbox-enforced. PHX-RELEASE must enforce the supported operator path or document and independently verify a mandatory isolated build-host boundary; PHX-QA must test that exact invocation. The helper uses `--share-net`; network isolation is not present or claimed, and its read-only host-root bind is a write boundary, not a confidentiality boundary.

The independent ULA blocker is unchanged: the packager still emits `fd00:db8:blaze::/48`, and the exact packaging test file contains no ULA parser assertions. Preserve §6.9: site-scoped RFC 4193 /48 generation/persistence belongs to installation identity, not a shared hardware profile. PHX-RELEASE owns implementation, PHX-CORE/COE define provisioning, PHX-QA independently verifies, PHX-HARDWARE validates only after correction and authorization. PHX-MASTER owns the contract and integration gate only.

Bounded live-source/manifest assertions executed by PHX-MASTER: **13/13 PASS**. These are static source assertions, not Python packaging tests, full Master tests, CI, OpenWrt UCI/netifd execution or hardware acceptance. COE #26 remains draft with five queued workflows and zero jobs returned. Keep #26/#31 draft and **PRODUCTION NO-GO**.


## 6.14 COE #31 operator sandbox correction and runtime timeout — 2026-11-17 UTC16

The earlier UTC14/UTC15 finding that the generated operator wrapper bypassed the sandbox is superseded at current COE RELEASE #31 head `9c2bebf50030c03bc4dd1e827e050863ba482eab`. Packager blob `f819ef1cd5265ff026e8a98ad9541c36ed087617` now validates the runner and routes an uncontained operator invocation through `sudo -- python3 run_imagebuilder_sandbox.py`; runner blob `ce098e44e847c265604e3dbb5d8df505025dd0ad` uses a read-only host-root bind and a writable bind only for the ImageBuilder workspace. The runner uses `--share-net`; network isolation is not provided or claimed. This is a filesystem write-boundary claim, not a confidentiality guarantee.

Runtime acceptance remains **BLOCKED**. Exact-head sandbox run [44125258197](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44125258197), job `134197585782`, was CANCELLED at the workflow's 20-minute timeout after 15 packaging tests reported `ok`. The first unreported test by unittest sort order is `test_generated_wrapper_contains_make_created_symlink_write_to_host`; this does not prove that test is the cause. The test helper's `subprocess.run` and runner's `process.communicate` have no per-invocation timeout. RELEASE must bound each invocation, terminate the complete child process group, preserve diagnostics, and rerun the complete exact-head suite; QA independently verifies the same SHA.

The independent ULA P0 remains open: packager blob `f819ef1c...` still emits invalid `fd00:db8:blaze::/48`, and test blob `a5310f90...` has no IPv6/ULA parser coverage. Preserve §6.9: the RFC 4193 /48 is durable installation/site identity, not a global hardware-profile constant. RELEASE owns implementation; CORE/COE define provisioning; QA independently verifies; HARDWARE validates only after correction and authorization.

This source correction does not establish a real OpenWrt ImageBuilder build, UCI/netifd acceptance, network isolation, signing, hardware acceptance, or production readiness. Keep #26/#31 draft and **PRODUCTION NO-GO**.

## 6.15 ImageBuilder user-namespace ownership must remain unprivileged — 2026-11-17 UTC17

**MASTER DECISION — APPROVED FOR IMPLEMENTATION TRIAL AND INDEPENDENT QA REVIEW ONLY.** The preferred model is an unprivileged runner process whose user namespace maps namespace UID 0 and GID 0 to the invoking host user's UID and GID, exactly one ID each. Do not elevate the runner with `sudo`, require `SUDO_UID`/`SUDO_GID`, invoke `newuidmap`/`newgidmap`, provision subordinate UID/GID ranges, or grant a broader host identity. Preserve the owner probe, path checks, disposable writable ImageBuilder bind, and fail-closed behavior. If the host cannot create the namespace without elevation or extra IDs, stop; the only alternative for review is a disposable isolated no-secret runner with an explicitly provisioned least-privilege namespace policy.

This decision is a design direction, not proof that the Ubuntu hosted runner supports the mapping and not sandbox acceptance. PHX-RELEASE must implement the trial on the existing COE #31 branch; PHX-QA must independently verify the exact resulting SHA, one-ID UID/GID mapping, host ownership, symlink/sentinel confinement, timeout process-group termination, and fail-closed behavior when user namespaces are unavailable.

The current COE #31 runner still requires root, `SUDO_UID`/`SUDO_GID`, and `newuidmap`/`newgidmap`. Exact-head sandbox run [44137935105](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137935105), job `134232499311`, fails with `newuidmap: uid range [0-1) -> [1001-1002) not allowed`; the 1-second real-bwrap timeout path was not reached. The current runner uses `--ro-bind / /` and a writable ImageBuilder bind, but `--share-net` retains the host network and the host root remains readable. This is write-confinement only, not confidentiality or network isolation. Do not run untrusted build inputs on a secret-bearing host.

The separate ULA blocker remains open under §6.9. Keep #31/#26 draft and **PRODUCTION NO-GO**.


## 6.16 Hosted ImageBuilder user-namespace capability is a release prerequisite — 2026-11-17 UTC18

**Status: BLOCKED at the runner substrate; the approved single-ID source trial is present but not runtime accepted.** This section supersedes the older §6.15 description of the root/SUDO/newuidmap implementation for the current COE #31 head; preserve §6.15 as historical decision provenance.

COE #31 now starts the runner as the invoking non-root identity and uses bubblewrap `--unshare-user --uid 0 --gid 0` without sudo, SUDO identity variables, newuidmap/newgidmap, or subordinate-ID helpers. The dedicated workflow requires `PHX_REQUIRE_BWRAP=1` on `ubuntu-24.04`. At exact #31 head `d0491517388479aa44c6c0ede8fc876f0be5950c`, sandbox run [44147379837](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379837), job `134266101493`, fails during bubblewrap UID-map setup with `bwrap: setting up uid map: Permission denied`. The suite ran 53 tests and reported 20 failures because the owner probe was never created; the real symlink and delayed-write timeout integration paths were not reached. Shared/hardware [44147379880](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379880) and case-collision [44147379865](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379865) passed only their scoped jobs.

Do not keep changing runner code to compensate for a host that denies the required namespace. The next prerequisite is an infrastructure-owner-approved disposable, ephemeral, no-secret runner with the unprivileged user namespace explicitly available. Do not reintroduce sudo, mapping helpers, broad subuid/subgid grants, or direct unsandboxed Make fallback. Add a clear early capability diagnostic, but never treat an unsupported host as sandbox acceptance or skip the mandatory exact-head integration test.

The runner uses a read-only host-root bind and `--share-net`; host files remain readable and the host network remains shared. This is write confinement only, not confidentiality or network isolation. No secrets/customer data may be exposed to untrusted build inputs; external egress policy must be reviewed outside bubblewrap.

Independent PHX-QA review remains required on the same exact candidate SHA: one-ID UID/GID mapping, host ownership probe, nested-symlink sentinel confinement, actual timeout/process-group cleanup, and fail-closed behavior when namespaces are unavailable. The invalid ULA `fd00:db8:blaze::/48` remains a separate P0. **PRODUCTION NO-GO.**
## 6.17 Exact-head default-deny, sandbox and migration acceptance hold — 2026-11-17 UTC19

**Poll authority remains default-deny.** Current HARDWARE #317 source has no positive `sigOk=true` default and no active `applyRemoteConfig` call. Its source-extracted poll-response lab keeps empty, unsigned, malformed, replay-like and positive-looking unverified replies from restoring intake or outputs. The current Full workflow still fails at the inherited QA assertion `Missing poll signature check`; this is a stale positive expectation, not authority to re-enable poll admission. PHX-QA must replace it with exact-source negative assertions for default-deny, no remote-config mutation and safe output state. Do not add a permissive signature path until CORE publishes the canonical authenticated producer/consumer contract and QA independently verifies the same SHA.

**ImageBuilder namespace support is an infrastructure prerequisite.** COE #31 uses the unprivileged single-ID bubblewrap runner and now contains bounded build timeout/process-group cleanup, but exact sandbox run 44158649032 fails because the hosted runner denies UID-map setup. Do not change the runner to elevate or silently bypass isolation. Require an infrastructure-owner-approved disposable, ephemeral, no-secret runner with unprivileged user namespaces enabled, then independently verify owner mapping, symlink/sentinel confinement, timeout cleanup and fail-closed behavior.

The runner still uses `--share-net` and read-only binds the host root: host network is shared and host files remain readable. This is write confinement only, not network isolation or confidentiality. Never expose secrets/customer data to untrusted build inputs.

**Site-scoped ULA remains mandatory under §6.9.** The current packager's `fd00:db8:blaze::/48` is invalid; no ULA profile property or parser regression exists. Do not guess a replacement or use one global prefix. CORE/RELEASE must define durable installation identity, persistence across reboot/upgrade/restore, and shared same-LAN provisioning; QA must verify generated UCI and negative cases.

**Migration is evidence-gated.** Current #317 firmware/test blobs differ from COE #26 destination, whose sketches/tests/docs retain positive poll/config and quarantine-clear behavior. No file move or destination overwrite is allowed until exact blobs, license/NOTICE applicability, imported test identities, full CI and owner/QA sign-off reconcile. #318 remains a divergent child and cannot be silently composed.

## 6.18 BLAZE-COMMS/1 exact recipient contract — 2026-11-17 UTC20

The envelope `to` field accepts exactly one registered role ID or the literal `ALL`, as defined by `COMMUNICATION_PROTOCOL.md`. It is not a semicolon-delimited recipient list. Unknown roles, list/object/number values, empty values, case variants and leading/trailing whitespace must fail closed. Current Master validator blob `3a6d0ca34cad54cd113abbda17d90898603547b3` enforces this exact rule. QA #292's original RED belongs to older verifier blob `a8a98996...`; its recorded post-fix 4/4 retest used blob `903df403...` at Master commit `0bc5e3fa...`. Current exact-head independent QA rerun is still required; no approval is inferred from the older retest.

The Master regression suite now additionally covers non-string and empty recipient values. Bounded exact-function execution passed 14/14 recipient cases; this is not the full Master suite or CI. **PRODUCTION NO-GO.**

## 6.9 Clear-helper tests are not disposition authority — 2026-11-18 UTC00

A direct test of clearPending() proves only its deletion preconditions. It does not prove that a coin POST received an authoritative disposition. The normal call path must still pass the event-bound receipt/disposition verifier in §6.6. At current HARDWARE #317 source/test head ddc7ed1f, coinPostDispositionVerified returns false for every response; the loop therefore preserves the pending journal/attempt marker and denies automatic replay. No positive coin-clear or quarantine transition is currently authorized.

The source-extracted pending-journal lab compiles the real readPendingFile, checksum, loadPending, attempt-marker match, clearPending and output-gate helpers against fake LittleFS. Its 16 boot and 17 pending-clear scenarios per board are useful software evidence, but not flash durability, crash atomicity, receipt authority or physical power-cut evidence.

Static presence checks for response_sig, |register| or |poll| are not signature verification. In current #283 source, the |poll| and response_sig tokens appear in comments describing the rejected candidate, while register/poll paths call denyRemoteControl(). QA must assert the actual source behavior: poll admission remains denied, target is cleared, outputs remain off, and ambiguous coin disposition preserves pending evidence. CORE owns the producer/receipt contract; QA owns independent vectors/tests; HARDWARE owns firmware. This clarification does not change the existing default-deny contract or authorize a positive path.


## 6.10 Poll-edge fault marker failure is not a reboot guarantee — 2026-11-18 UTC03

At HARDWARE #320 exact head b2b41a3d6ce7887b9624137c966f58462895d3fa, both ESP32 and ESP8266 sketches latch journalRecoveryRequired, disable insert mode, clear the active target, attempt a /pollpulse.fault write, flush/close it, and verify exact size plus byte-for-byte readback. If persistence fails, the source explicitly describes the device as fail-closed this boot. The RAM latch is not proof that a pulse edge survives reboot when no other durable pending record remains.

The boot path treats an existing marker as a deny latch and does not auto-clear it. The writer's failure path has no independent durable fallback. Therefore:
- Do not claim reboot/power-cut durability from the RAM-only failure latch.
- Do not enable poll/coin intake or clear evidence after an ambiguous marker write/readback.
- Require exact-head QA failure injection for marker open/short-write/readback failure, mount failure, reboot with a valid/partial marker, and reboot when marker persistence failed and no pending record exists.
- CORE/MASTER must define durable recovery semantics; HARDWARE owns implementation; QA owns independent vectors.
- coinPostDispositionVerified() and acceptPollResponse() remain hard false on both boards. No positive poll or financial disposition path is authorized.

This clarifies the durability boundary only; it does not alter firmware or grant production authority.

## 6.11 Poll-fault marker-open failure has no reboot proof — 2026-11-18 UTC03

At HARDWARE PR #320 exact head `b2b41a3d6ce7887b9624137c966f58462895d3fa`, both sketches implement a readback-verified `/pollpulse.fault` marker. The writer checks open, full write length, flush/close, exact file size and byte-for-byte readback. `latchPollPulseFault()` sets `journalRecoveryRequired`, disables insertion, clears the active target and applies outputs before attempting persistence. If marker creation/readback fails, the source explicitly reports only that the device remains fail-closed **this boot**.

The boot loader restores this fault latch only when `/pollpulse.fault` exists. If marker creation itself fails and no other durable pending record survives, the RAM-only latch can disappear on reboot. The current `poll_loop_blocking_inhibit_lab.py` injects `fakeOpenFail` and checks same-boot relay/LED denial, but the open-failure case does not reboot or call `initPendingStore()` afterward. It therefore does not prove reboot-safe recovery for the no-marker case.

Required before any durability claim:
- PHX-QA adds an exact-source reboot/reset vector after marker-open failure and after short-write/readback failure, including the case with no surviving pending record.
- PHX-HARDWARE implements an owner-reviewed durable fallback/witness or preserves another durable record that causes boot to remain denied.
- PHX-CORE reviews event identity, receipt/replay and reconciliation semantics; PHX-QA independently verifies the same exact source SHA.
- Keep poll admission, coin POST disposition, automatic replay and relay output fail-closed until the combined exact-head behavior is verified.

Bounded Master source assertions on the exact #320/#322 files passed 15/15; these were static source checks, not firmware runtime tests. The #320 focused poll-edge workflow [44225475672](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225475672) is attached to predecessor source/test SHA `b6e9cfa75105e6cd29c29b93266255d3110c8296`, not the final #320 head. The current #320 focused quarantine/relay runs passed, but no current-head poll-edge run was returned. This section records a test/contract gap; it does not approve a durable implementation.


## 6.19 COE INTERCON journal formats remain unadopted — 2026-11-18 UTC04

COE draft PRs #39, #40 and #42 independently implement the same Stage-3 staging path from #38 but define different on-flash formats: 64-byte (#39), 76-byte (#40) and 92-byte (#42). Their sketch, workflow and journal/test blobs differ; #41 is a Stage-4 child of #39 only. These are review candidates, **not the canonical Phoenix financial receipt/journal contract**. Do not connect any of them to BlazePwifi Vendo, the live Pisonet timer, customer balances or COE #26 until one format is selected by its owner, independently reviewed by QA, and validated on actual hardware. CRC32 detects corruption; it does not authenticate a peer or authorize money. The host fault-injection runs do not prove real LittleFS/power-cut atomicity. See [COE_INTERCON_STAGE3_PARALLEL_JOURNAL_LINEAGE_AUDIT_20261118_UTC04.md](COE_INTERCON_STAGE3_PARALLEL_JOURNAL_LINEAGE_AUDIT_20261118_UTC04.md). **PRODUCTION NO-GO.**

## 6.20 Poll-fault secondary stores are same-chip fail-closed fallback only — 2026-11-18 UTC05

At PHX-HARDWARE PR #323 current head `f98bc39c29eeb82b292aa83fa680d05d2e36efd5` (source/test change commit `6738171209a748c3c210ac13ebe69450eb6405f5`), both ESP32 and ESP8266 `latchPollPulseFault()` implementations now set the RAM deny state, disable insertion, clear the active target, and invoke `applyOutputs()` before any potentially blocking NVS/EEPROM or LittleFS persistence. This output-inhibit ordering is a required fail-closed invariant; it does not prove the electrical relay has physically deasserted.

The candidate adds:
- ESP32: a fixed 20-byte versioned NVS record at namespace `phx_fault`, key `poll_fault`, with write-length and exact readback checks.
- ESP8266: a 20-byte sticky record at EEPROM-emulation offset 512 in a 544-byte buffer; static assertions keep the existing Config before offset 512, then commit/end/reopen/readback.
- Any existing or malformed record is a deny hold; no auto-clear is added. FNV-1a is corruption detection, not authentication or anti-rollback.

These are separate regions on the same physical flash chip, **not an independent physical witness**. If either marker persists, boot remains denied. If both stores fail, the source explicitly guarantees only current-boot fail-closed behavior; reboot durability is not established. Do not claim crash-atomic financial state, independent anti-rollback, or production durability from this fallback.

Exact-head source-extracted dual-store lab [44242190343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190343) reports PASS for both boards and `EXPECTED_CURRENT_BOOT_ONLY` for both-store failure. Relay/output lab [44242190332](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190332) passes logical host scenarios. Full build [44242190324](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190324) fails the QA-owned legacy `Missing poll signature check` assertion; 14 target/platform builds pass, downstream simulations/signing/publishing are skipped. These are CI/source-extracted results, not real flash or physical acceptance.

Require independent QA reboot vectors for primary/secondary read/write failure, corrupt/partial records and both-store failure. Preserve poll/coin default-deny. Keep #323 draft-only; no COE #26 migration or production authority is granted. See [HARDWARE_POLL_FAULT_DUAL_STORE_AND_COE_STAGING_RECONCILIATION_20261118_UTC05.md](HARDWARE_POLL_FAULT_DUAL_STORE_AND_COE_STAGING_RECONCILIATION_20261118_UTC05.md). **PRODUCTION NO-GO.**

---

## 6.21 COE INTERCON Stage-3/Stage-4 candidates — provisional integration boundary (2026-11-18 UTC06)

COE INTERCON is not an adopted Phoenix financial authority. Three incompatible Stage-3 candidates remain open: #39 uses a 64-byte record, #40 a 76-byte record, and #42 a 92-byte record. Stage-4 #41 is a journal-only shadow-credit child of #39; Stage-4 #43 is a live timer/relay child of #42. Do not combine these formats or call either Stage-4 branch canonical without an explicit COE owner decision, independent QA and a reversible format migration plan.

The #43 source commits Master pending state before CRED and commits Slave paid time + receipt/sequence before live timer/output changes. That is useful candidate ordering, but it is a two-device prototype, not integration with the Phoenix CORE ledger: the PR explicitly leaves the BlazePwifi router adapter and multi-target accounting separate. Any future integration must map to the canonical receipt/event identity, idempotency, disposition and reconciliation contracts in §§1–2. A local 64-bit sequence and paid-event count are not by themselves proof of cross-system receipt parity.

The current #43 unresolved pulse count is RAM-only and absent from its journal record. A failed/unavailable Master journal can therefore leave an unresolved physical coin alarm without demonstrated reboot persistence. Such a state must remain deny/CS-off and must be durably reconciled before another paid event is admitted.

The inspected peer-auth source stores a raw 32-byte shared key in a LittleFS config record. No protected key store or independent signer is shown in the inspected files. HMAC transport and a checksum do not satisfy the independent protected P-256 signer / anti-rollback witness gate.

The #43 host end-to-end test models two journal slots in RAM and copies encoded bytes to simulate a rename boundary. It does not certify actual LittleFS metadata atomicity, flash brownouts, watchdog behavior or power-cut recovery. Its 650 ms burst grouping and 60-second timer checkpoint are prototype assumptions; the latter can restore up to approximately 60 seconds of consumed time after a sudden outage. Physical coin acceptance, CS inhibit/hold-up, relay behavior and real flash recovery remain NOT TESTED.

#41 remains shadow-only and must not be represented as live paid-time acceptance. #43 changes live timer/relay behavior but remains DRAFT / NO-GO. No COE INTERCON source route exists in OWNERSHIP_ROUTES.json; no PHX-PISONET or PHX-HARDWARE ownership is inferred for this subtree.

---

## 6.22 Current poll admission is intentionally hard-deny; legacy positive-signature fixture is incompatible — 2026-11-18 UTC07

At current PHX-HARDWARE PR #323 source/test SHA `a3aa967087680887e925791f83a8fbc48a1e62b9` (current PR/docs head `0d6f0c7f4f9d2d07bc43d24e5db63d8bddb11f43`), both ESP sketches keep `acceptPollResponse()` deny-only: ignore the response, force `insertMode=false`, clear `activeTarget`, and return false. Both `coinPostDispositionVerified()` functions also return false. This is the current safe contract, not an incomplete positive verifier.

The current Experiments `cgi-bin/vendo` poll branch (blob `2e3a1430d08cc6606429a042df3b5848f53c7267`) emits no `response_sig`. The inherited `tests/v05_firmware_hardening_test.sh` (blob `41211b2c110ab409f6d9d1812ef12fda73b13211`) still requires `response_sig` and literal `|poll|` in both sketches, so the Full workflow fails at `Missing poll signature check`. That fixture does not match the current deny-only contract or current producer. It must be replaced by negative tests proving unsigned/unknown responses cannot enable insertion, retain a target, clear a pending coin or authorize disposition. Do not add a synthetic signature string or enable unauthenticated poll admission to satisfy the old assertion.

A positive poll path remains blocked until PHX-CORE publishes a canonical producer/consumer schema and golden vectors, PHX-QA verifies both sides at pinned SHAs, and the independent signer/anti-rollback gates are satisfied. See [HARDWARE323_POLL_DENY_CONTRACT_AND_EXACT_HEAD_RECONCILIATION_20261118_UTC07.md](HARDWARE323_POLL_DENY_CONTRACT_AND_EXACT_HEAD_RECONCILIATION_20261118_UTC07.md). **PRODUCTION NO-GO.**


## 6.23 Exact poll response producer/consumer reconciliation — 2026-11-18 UTC08

**Decision:** the current Experiments source producer and the current #323 firmware consumer do not implement an authenticated positive poll response. Keep coin admission and coin POST disposition fail-closed. The COE #26 response-signature expression is a separate, unapproved candidate and is not permission to copy or enable it.

### Exact refs and source evidence

| Component | Exact ref / blob | Observed behavior |
|---|---|---|
| Experiments development `blazepwifi-v0.5.3-development` | branch HEAD `aad3aade72c1156eecba1fed30907c6d0283b2c5`; `vendo` blob `a1c19180385e618c412b4af21c0e91c1f47da1dd` | `register|ping`, `poll`, and `coin` response bodies contain no `response_sig` |
| Experiments development `common.sh` | blob `ca4920d3d9572382fb381a325183a18311be5954` | `bp_vendo_sig_expected()` / `bp_check_vendo_sig()` check a keyed SHA-256 concatenation (not standard HMAC); `bp_json()` only prints headers and the supplied JSON, with no response-signing wrapper |
| Experiments development `controller.sh` | blob `54bdc59949884bd3e734f8c07ddeb1d7c2cf9848` | `bp_controller_json()` emits configuration fields, not an authenticated configuration envelope |
| Current HARDWARE #323 ESP8266 | source/test SHA `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`; sketch blob `8e79b9eb8856e67d966f4c6385f89fccdc8be7fc` | `acceptPollResponse()` and `coinPostDispositionVerified()` return false; missing register `response_sig` leaves remote configuration disabled |
| Current HARDWARE #323 ESP32 | same source/test SHA; sketch blob `bd74b11c1496b0943404ff387ee72bb45d4743e5` | Same deny-only poll and coin disposition behavior |
| COE integration #26 | head `b382d233ff06c8791b1028bed3c617cc7b670d12`; `vendo` blob `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e` | Contains `vendo_poll_sig()` and emits a candidate `response_sig`; its construction is keyed SHA-256 concatenation, not standard HMAC |

The COE candidate's poll expression is ordered as secret, action, controller ID, request nonce, insert flag, target nonce, expiry, secret, then SHA-256. Structural field-order similarity is not cryptographic approval: there is no accepted canonical schema, key/version lifecycle, independently executed shared golden vector, or exact combined-tree QA evidence. Do not transplant this candidate into Experiments or infer that #323 consumes it.

### Exact #323 CI and stale QA fixture

- Current PR/docs head: `4850b16a31a1ccb67f265e5224a2799b25cf2e01`; source/test SHA: `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`; parent #322: `50d93e0de3d682550b6f02fb43484e76ad9c7e08`.
- Focused quarantine/readback run [44262258247](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258247): SUCCESS.
- Focused relay/output run [44262258937](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258937): SUCCESS.
- Full build [44262258842](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258842): FAILURE at validation job `134658178171`, which reports `Missing poll signature check` in ESP8266. All 14 firmware target jobs and Android completed SUCCESS; downstream import, update, simulations, candidate gate, signing and publishing jobs were SKIPPED.
- The exact merge-tree QA fixture `v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` requires literal `response_sig` and `|poll|` presence. It does not test the current intentional deny-only behavior. The `controllers.sh` entrypoint blob `f7896647713d6bf8034ff48ed19b6383e4dedea0` invokes this fixture.
- The focused CI runs are source-extracted simulations, not physical flash, GPIO, coin-acceptor or power-cut acceptance.

### Owner actions — no source takeover

1. **PHX-QA:** replace the positive `|poll|` string-presence assertion with source-linked negative behavior tests for both boards: arbitrary/missing/forged poll bodies must leave `insertMode=false`, clear `activeTarget`, and never enable intake; coin POST disposition must remain false. Keep the test bound to the exact #323 source/test SHA.
2. **PHX-CORE:** define the canonical versioned response schema, cryptographic construction (do not label concatenated SHA-256 as HMAC), key identity/version, nonce and target binding, freshness/expiry, canonical field order, and positive/negative golden vectors.
3. **PHX-HARDWARE:** retain deny-only behavior until the approved producer and consumer exist; keep source/test and handover refs synchronized.
4. **PHX-RELEASE:** keep downstream signing, candidate-gate and publishing jobs closed while validation fails.
5. **PHX-MASTER:** maintain this contract and migration matrix only; do not edit worker-owned firmware, CGI or QA fixture files.

### Integration and release boundary

COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, with five workflows QUEUED and zero jobs. Its staged poll producer differs from Experiments development; exact per-file source/destination blob, license/NOTICE, import-completeness, test-identity and exact-head CI review is still required. No file was copied, moved, overwritten or deleted. The ownership manifest remains `DRAFT_REVIEW_ONLY`, with PHX-MASTER destination null.

The private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed Library/Drive surface. The AGENTS-linked cloud artifact policy/storage handover could not be retrieved through the GitHub connector or web endpoint; COE root `AGENTS.md` returned 404. No older registry snapshot was substituted and no private registry contents were published.

**Status:** DEVELOPMENT / LAB ONLY; integrated acceptance UNKNOWN; physical acceptance NOT TESTED; **PRODUCTION NO-GO**. Independent protected signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

## 6.24 Current HARDWARE #323 to COE #26 provenance and test-identity hold — 2026-11-18 UTC09

**Decision:** keep #323 and COE #26 separate DRAFTs. The current source candidate is not byte-identical to the staged destination and its source dual-store lab is not imported or invoked there. No copy/move/overwrite or positive poll admission is authorized.

- Current Hardware branch/docs head: 1761bf38d01c44f3bfd87acc6c7f03d97d7e1d17; exact source/test SHA: d37d5da9bdd8e3be08f6344f4a2520c29c2d0abb; parent #322: 50d93e0de3d682550b6f02fb43484e76ad9c7e08.
- COE #26 head: b382d233ff06c8791b1028bed3c617cc7b670d12. ESP32 source/destination blobs bd74b11c1496b0943404ff387ee72bb45d4743e5 / 3cc7ec54b476943dc04a8d1af5e2df5fe054e422; ESP8266 source/destination blobs 8e79b9eb8856e67d966f4c6385f89fccdc8be7fc / c8be98f72596681e36a3ad1f8939bf8046c96887. Both pairs differ.
- Source dual-store lab blob 25f5e8bd1a344d69acc0505324156f66a1abffa4 has no COE #26 mapped counterpart. The source Hardware workflow blob 2358e4ab940b9879e961046180f01fc3d5356709 is not the COE Hardware workflow blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793; COE's workflow invokes a different generic test script.
- COE #26 test blob f921c56cecc19cab1989507b9b4ade1f45dac54e still greps for response_sig and |poll|; current source remains deny-only. COE Hardware README's keyed SHA-256 concatenation label is not standard HMAC.
- Source MIT license blob 1ee55b94183417be977ca287cd7391f9a6f7e721 equals sibling Pisowifi/LICENSE, but Hardware/root LICENSE/NOTICE applicability is unresolved; source root NOTICE is absent in the destination tree.
- #323 current-head focused CI [44278980129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980129) and [44278980263](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980263) PASS; Full [44278980291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980291) fails at Missing poll signature check. COE #26 has five queued workflows and zero jobs.

The source MIT license and sibling Pisowifi license match does not establish Hardware subtree licensing. The current QA fixture mismatch is not permission to add synthetic signatures or enable positive admission. See [HARDWARE323_CURRENT_HEAD_AND_COE26_MIGRATION_PROVENANCE_20261118_UTC09.md](HARDWARE323_CURRENT_HEAD_AND_COE26_MIGRATION_PROVENANCE_20261118_UTC09.md). **PRODUCTION NO-GO.**

## 6.25 UTC12 — poll-fault output-inhibit ordering (provisional, source-verified)

PHX-HARDWARE selected the #322 → #323 review-candidate stack in control-plane comment 6978026438. This is an owner-reported candidate selection, not a Master merge decision or hardware acceptance.

At #323 PR/docs head 0975fe4416daa72c097d3fee2b631950eb64908c, both board sketches contain the same latch ordering: set journalRecoveryRequired, disable insertMode, clear activeTarget, call applyOutputs(), then attempt the secondary NVS/EEPROM backup and LittleFS marker. If both stores fail, the source explicitly says the current boot remains fail-closed but reboot durability is NOT established. The two stores are not an independent protected witness.

Exact source/test commit 176ad50da2180ee085e2fb63ddb23d17b53dd63d corrected the source-extracted mutation so the deferred-output-inhibit mutation actually matches the source newline. Exact-head focused runs 44301775875 and 44301775918 pass; their logs show POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS and reject defer-fault-output-inhibit on ESP8266 and ESP32. This is host/source-extracted CI only.

Full build 44301775872 fails at the QA-owned Controller protocol parity assertion Missing poll signature check in the ESP8266 sketch. All 13 firmware-target jobs and Android completed successfully; downstream simulations, candidate gate, signing and publishing were skipped. Both acceptPollResponse() and coinPostDispositionVerified() remain deny-only. Do not add a synthetic signature or relax firmware to satisfy the stale positive fixture.

PHX-QA owns replacing the positive string-presence fixture with exact-source negative behavior tests. PHX-HARDWARE owns refreshing the stale #323 PR description (it still cites older docs/source SHAs) and reconciling sibling #324. PHX-CORE owns the canonical response envelope and replay contract. Physical relay, coin, flash, power-cut and soak acceptance remain NOT TESTED.

---

<!-- PHX-MASTER-20261118-UTC13-ESP8266-BOOT-POLARITY-AUDIT -->


## 2.1.2 Boot-time relay/LED polarity must be established before first OUTPUT transition (2026-11-18 UTC13)

The OFF-preload ordering above is safe only when the polarity variables already match the physical relay/LED wiring before the first call to `configureRuntimePins()`. The source-exact audit in [HARDWARE_ESP8266_BOOT_POLARITY_SOURCE_AUDIT_20261118_UTC13.md](HARDWARE_ESP8266_BOOT_POLARITY_SOURCE_AUDIT_20261118_UTC13.md) found a board-specific gap:

- At HARDWARE #323 source/test SHA `176ad50da2180ee085e2fb63ddb23d17b53dd63d` (docs-only PR head `0975fe4416daa72c097d3fee2b631950eb64908c`), ESP8266 initializes `runRelayActiveHigh=true` and `runLedActiveHigh=true` at line 46. The only later assignments to those runtime polarity values are inside `applyRemoteConfig()` (lines 587–605), which is explicitly marked intentionally dormant because the returned configuration is not authenticated. The ESP8266 `setup()` reaches `configureRuntimePins()` without a persisted/local polarity load.
- Therefore the source currently demonstrates the OFF-preload sequence only under the active-high default for ESP8266. It does **not** establish a safe active-low ESP8266 boot profile. If a deployed relay is active-low, the active-high default may drive the wrong physical level; the actual wiring is not inferred here.
- ESP32 is a separate path: `loadConfig()` reads relay/LED polarity from Preferences and `setup()` loads it before the first `configureRuntimePins()`. This source distinction is not physical acceptance and does not prove behavior for corrupted/missing NVS or every board.
- The #323 poll-fault host lab observes the relay/LED state at both the secondary backup-write and LittleFS marker-open boundaries. That proves the fault latch deasserts outputs before those persistence calls in the extracted control-flow harness; it does not prove the boot-time polarity source or electrical behavior.

**Required gate:** PHX-HARDWARE must either (a) define and document a verified active-high-only ESP8266 target profile with board/wiring evidence, or (b) implement a persistent, validated local polarity source loaded before the first output configuration. PHX-QA must independently test cold boot with default, missing, corrupt and each supported polarity value, including the first GPIO level before OUTPUT mode. Do not activate remote polarity configuration until the authenticated response-envelope contract and exact-SHA QA vectors are approved. Physical relay voltage and reset-state acceptance remain NOT TESTED; no firmware flash or production admission is authorized.



## 6.25 Current ESP8266 local boot-polarity implementation and test-wiring hold (2026-11-18 UTC14)

**Disposition: BLOCKED at the exact current HARDWARE #323 head; no boot-polarity implementation or CI verification is established.**

The Hardware owner acknowledged an implementation plan in control-plane comment [6980748685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-6980748685), but the current PR head is now 9cd889ec184c81d96569d3994602da3076efb537. At that exact head:

- ESP8266 sketch blob: 8e79b9eb8856e67d966f4c6385f89fccdc8be7fc. The file contains ConfigV1 and the current Config record with MAGIC 0x42505732; it has no ConfigV2/ConfigV3 structure, no outputPolarityConfigured/outputPolarityKnown state, no configChecksum, and no local relay_active_high / led_active_high setup fields. loadCfg() at line 498 accepts the current record or migrates V1; setup() at line 1379 loads that config and calls configureRuntimePins() without a validated local polarity source. applyRemoteConfig() contains remote polarity assignments, but that function is explicitly dormant and is not an authorized boot-time source.
- New boot-polarity lab blob: f08e1aadc40acf09e08ad055c92a38073c33f6c2. Its first prerequisite checks require the missing ConfigV2, outputPolarityConfigured, outputPolarityKnown, configChecksum and local setup fields. The lab is not source-compatible with the exact sketch blob and would fail if actually invoked at this head.
- Workflow blob: dd2692df58c5311ad5d365a5539279da2018d8f7. The new command is written as a folded YAML plain scalar: the second Python line is part of the first command, not a second command or step. The exact Actions log for run 44320124000 confirms the shell received one command containing both script names. Only the relay-output lab ran; the boot-polarity lab did not execute.

Therefore the focused relay/output result [44320124000](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320124000) is PASS only for the existing relay-output lab. It is NOT boot-polarity regression evidence. Quarantine/readback [44320123810](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320123810) passed independently. Full build [44320123851](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320123851) completed FAILURE. Validation job 134856529480 failed at Controller protocol parity with the exact message Missing poll signature check. All 13/13 firmware target jobs and Android job 134856530339 completed SUCCESS; downstream simulations, update bundle, candidate gate, signing and publishing jobs were SKIPPED. This is not Full CI acceptance.

**Required owner actions:** PHX-HARDWARE must first commit the actual versioned local polarity record, fail-closed V1/V2 migration, boot-time read/validation before any output configuration, and strict local setup AP 0/1 selection. Correct the workflow using a block scalar (run: |) with separate commands or a separate step, then verify the log shows the boot lab itself executing and its negative mutations being rejected. PHX-QA must independently test cold boot with default, missing, corrupt, active-high and active-low values, including the first GPIO level before OUTPUT mode, at the same exact source SHA. Do not read polarity from unauthenticated remote configuration. Physical relay voltage/reset-state acceptance remains NOT TESTED.

This section supersedes the earlier UTC13 statement that the local-polarity implementation was in progress as if the current source already contained it. The owner plan is real; the current source implementation is not yet present. Keep the candidate DRAFT, keep financial/coin admission NO-GO, and do not migrate this firmware into COE.

## 6.26 — ESP8266 ConfigV3 local polarity authority (provisional; 2026-11-18 UTC14)

The current Hardware review candidate #323 at 4dc5fd566da6ed3e523e3e15174837f5cfb8b183 introduces an ESP8266-only local ConfigV3 polarity profile. V1/V2 migration leaves polarity unconfigured; boot validates the record before runtime pin configuration; unknown polarity leaves relay/LED pins as INPUT and blocks poll/coin paths; only the WPA2 setup AP accepts explicit 0/1 local polarity values. EEPROM commit is followed by reopen/readback and full record comparison.

Focused exact-head CI 44329837932 and 44329837962 passed, including the boot-polarity lab and interrupt-attachment mutation rejection. Full build 44329837987 was pending at the snapshot. This is host-simulation evidence only. Physical relay, coin pulse and power-cut acceptance remain NOT TESTED. Do not generalize the ESP8266 profile to ESP32; the ESP32 configuration path requires separate review. Poll-response admission and coin-post disposition remain deny-only.



## 6.27 — Current ConfigV3 failure-latch result and ESP32 polarity parity (2026-11-18 UTC15)

At current Hardware #323 head `bc0447f013698a2e45c154b0ae69a098b0e75fe5`, ESP8266 ConfigV3 is present (firmware blob `283dbe329a5445931cc9fe7096561a68b9c8bf62`). Its default/missing-config and V1/V2 migration failure paths call `latchConfigPersistenceFailure()`, which clears output-polarity authority, keeps GPIO configuration unsafe, disables insertion and sets `journalRecoveryRequired=true`. The boot lab (blob `25fe2f6040f59c4fa74c9d88c821aed9804d3fe2`) now actually executes: workflow blob `1140daf71d5218c9c58cdf74ae4cc3ab3822c51a` uses separate block-scalar commands, and run [44330729195](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44330729195) shows the relay lab passing before the boot lab fails at the `journalRecoveryRequired` assertion after injected EEPROM commit failure. The visible firmware path and observed source-extracted result contradict one another; root cause is unresolved. Do not label the firmware or test harness correct until Hardware instruments the fake commit, extraction and latch path and reproduces the branch decision.

**Cross-board P0:** ESP32 blob `bd74b11c1496b0943404ff387ee72bb45d4743e5` is not at ConfigV3 parity. Its `Config` defaults relay/LED polarity to active-high; `loadConfig()` reads Preferences with `getBool(..., true)`; setup calls `configureRuntimePins()` before `setupPortal()`; and that routine writes logical OFF using the default polarity before enabling OUTPUT. It has no explicit unknown-polarity validity flag or INPUT hold. The local setup form appears later and cannot protect the initial output transition. For active-low relay wiring, the default LOW write is potentially active. No physical assertion is made, but the source ordering is insufficient for a safe active-low boot claim.

**Required contract:** both boards must boot with relay/LED pins as INPUT until a locally configured, validated, durably read-back polarity profile is known. Unknown, missing, corrupt, future-version or failed-commit state must remain fail-closed; no remote response may establish polarity. QA must independently verify both board paths at the same exact source SHA. Focused host tests are not physical acceptance; poll/coin admission remains deny-only. **PRODUCTION NO-GO.**


## 6.28 — UTC16 ConfigV3 two-board boot gate and COE poll-contract provenance (2026-11-18)

At current HARDWARE #323 head 988904e8bcd058b62a9fac4aa6319a9b7c5b2470 (latest source/test tree 359bd8f685a2a464f4a77b84501fcf4055944d5c; later commits are documentation-only), both ESP8266 and ESP32 now have source-extracted local polarity boot gates. ESP8266 ConfigV3 uses validated local persistence/readback; V1/V2 and unknown/future schemas remain unconfigured, and missing/corrupt/failed-commit state stays fail-closed. ESP32 holds unknown/legacy polarity as INPUT until the local marker/profile is validated and read back. Focused logs record ESP8266_COMMIT_FAILURE_TRACE=PASS, UNKNOWN_EEPROM_SCHEMA_PRESERVED=PASS, ESP8266_BOOT_POLARITY_CONFIG_V3=PASS and ESP32 boot-polarity gate PASS. Runs: [44347847077](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347847077) and [44347847191](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347847191).

This supersedes §6.27's prior unresolved failed-commit / ESP32 parity statement. It is Hardware-owner source/test + focused CI evidence only; both labs report SIMULATED_ONLY, physical relay/polarity and power-cut acceptance remain NOT TESTED. QA has not independently accepted the same exact source/test tree.

Full #323 [44347846832](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347846832) still fails at QA-owned Missing poll signature check; 13/13 firmware targets and Android completed, but downstream simulations/signing/publishing did not pass. The source fixture requires positive response_sig and |poll| strings. Current firmware poll-response admission and coin-POST disposition remain deny-only. Do not add synthetic signatures or relax firmware. QA must replace the stale positive-presence test with negative default-deny behavior tests; CORE owns the canonical producer/consumer contract.

COE #26 is not a safe migration destination at current head b382d233ff06c8791b1028bed3c617cc7b670d12: both board firmware blobs differ from current #323, all three new boot/dual-store labs are absent, the generic Hardware test still expects positive poll signatures, and its workflow does not invoke the new labs. Source main/development poll producers do not emit a signed poll response, while the COE destination producer adds vendo_poll_sig. Source MIT license matches Pisowifi/LICENSE, but Hardware-scoped LICENSE/NOTICE and COE root LICENSE/NOTICE are absent. No move/copy is proposed; manifest remains DRAFT_REVIEW_ONLY / target null. **PRODUCTION NO-GO.**


## Live exact-head contract reconciliation — 2026-11-18T17:39:33Z

HARDWARE #326 is now at PR/docs head `58c558fb6a237935214621adc3dee65a10fe1a51`, with source/test commit `28e13fc82a250821e815fd84b5fd61f1769e7106`. The current source-extracted lab compiles production `latchPollPulseFault()` and `sampleCoinPulseEdge()` for ESP32 and ESP8266; only persistence backends are fault-injected. The latch deasserts outputs before attempting both NVS/EEPROM and LittleFS markers. If both fail, the source explicitly says current-boot denial only and reboot durability is NOT established. This same-chip fallback is not an independent witness, durable ledger, receipt, or proof of coin recovery.

Focused PR runs [44358712365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712365) and [44358712238](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712238) pass on PR head `58c558fb...`; Full [44358712823](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712823) fails the inherited QA positive `Missing poll signature check`. Firmware poll/coin admission remains deny-only. QA must change the fixture to negative deny behavior; do not add synthetic signatures or relax firmware. These are host simulations/build CI only, not electrical acceptance.



## 6.29 — UTC18 Hardware #327 pre-poll edge and ambiguous backup-commit fence (provisional; 2026-11-18T18:52Z)

Current Hardware stack: PR #323 `988904e8bcd058b62a9fac4aa6319a9b7c5b2470` → child #326 `58c558fb6a237935214621adc3dee65a10fe1a51` → child #327 current docs HEAD `0a26468022d25746fdc38525c0c0979da098f6d4`; exact source/test SHA `e774420c3404141ffe4ec7b9c002c14d3c2286b8`. PR #327 is OPEN / DRAFT / UNMERGED. Firmware blobs at the current #327 tree are ESP8266 `dde063b1f578fa66a52221b74643d8862a38957c` and ESP32 `ada9723c5f07879775284eb128a986ac865394f7`.

### 6.29.1 Pre-poll ISR edge fence

Both sketches snapshot the ISR edge sequence before `beginPollWindow()`. After the quiet-drain helper returns successfully, but **before** synchronous `post("poll")`, the loop snapshots again. If the sequence advanced during the drain window, it calls the existing `latchPollPulseFault(delta)` while poll intake remains inhibited, does not dispatch the HTTP poll, reapplies outputs under the sticky recovery deny, updates the poll timestamp, and defers the next poll. This closes the source-level interval in which an ISR edge could otherwise remain volatile during the blocking HTTP wait.

The source-extracted `poll_loop_blocking_inhibit_lab.py` injects an edge after the final quiet sample and asserts that no poll dispatch occurs before the fault marker. Exact-source focused CI on #327 source/test SHA `e774420c...`: quarantine/readback [44373043845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043845) PASS; relay/output [44373043958](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043958) PASS. The later docs-only PR head `0a264680...` also has focused quarantine [44373742439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742439) PASS and relay/output [44373742382](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742382) PASS. These are source-extracted host/fake-I/O simulations, not physical ISR, acceptor or relay acceptance.

### 6.29.2 Ambiguous backup-commit retry fence

Both sketches now set current-boot `pollFaultBackupWriteFailed` when the secondary NVS/EEPROM set, commit, reopen or readback path is ambiguous. Further same-boot backup writes return false instead of treating dirty EEPROM/NVS cache state as proof of durable storage. A cold boot resets the RAM-only flag and checks the flash-backed marker again. The source-extracted dual-store lab exercises ordinary commit failure, ambiguous commit-after-write, no same-boot retry, and reboot marker detection; both board markers report `FAILED_COMMIT_RETRY_HELD_UNTIL_REBOOT_PASS` and `AMBIGUOUS_COMMIT_RETRY_DENY_REBOOT_MARKER_PASS`.

**Limit:** the flag itself is RAM-only. If both LittleFS and NVS/EEPROM fail and no marker reaches durable media, the source proves current-boot denial only; reboot durability remains NOT ESTABLISHED. Same-chip stores are not an independent anti-rollback/freshness witness, durable ledger or receipt authority. The lab explicitly reports `DUAL_STORE_FAILURE_LIMITATION=EXPECTED_CURRENT_BOOT_ONLY`. This is not a production durability pass.

### 6.29.3 Test-harness correction and Full validation

An intermediate #327 source/test commit `fcb5c1ab...` had a test-only symbol typo `pollFaultBackupBackupPresentOrCorrupt`; quarantine CI failed at C++ compilation before the dual-store and pre-poll labs. Hardware corrected the assertion in test-only commit `e774420c...` to `pollFaultBackupPresentOrCorrupt`. The exact-source focused runs above then passed. Do not carry the intermediate harness failure forward as a current source defect, and do not carry an earlier focused PASS to a different SHA without exact-head evidence.

Full build on the latest docs head [44373742348](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742348) **FAILED**: validation job `135047376378` still rejects the inherited QA-owned positive `response_sig` / `|poll|` assertion as `Missing poll signature check`; Android job `135047377045` separately failed resolving legacy Gradle dependencies (including protobuf-gradle-plugin 0.8.3 and Kotlin 1.2.0 artifacts). Other firmware/platform target jobs completed successfully, but downstream simulation, signing, candidate and publishing gates were skipped. The current firmware remains deliberately deny-only; do not add synthetic positive signatures or weaken it. QA must replace the stale positive fixture with negative default-deny tests and rerun the exact combined candidate.

**Owner routing:** HARDWARE owns #327 source and labs; QA owns the stale poll-signature fixture and independent same-SHA review; CORE owns unresolved-ingress/ledger reconciliation semantics; RELEASE/INFRA own Android dependency and runner/build-environment triage. MASTER records the contract and integration gate only. No source ownership or release authority transfers here. **PRODUCTION NO-GO.**


## 6.30 First-boot ULA generation must preserve site scope across appliances — 2026-11-19 UTC00 refresh

Section 6.9 remains normative: an RFC 4193 `fd00::/8` /48 is durable site identity, unique between independent sites and shared by devices on the same LAN/site. It must survive reboot, upgrade and restore; it is not a static hardware-profile property.

COE Release PR #44 is OPEN / DRAFT at `582fd5d5e83e36b36546ac28534740298ba94af4`, based on #35 at `1a5be48d2845781b0b07bad39a37f8440cea4d4f`. Its first-boot script creates a random 40-bit ULA global ID, validates the resulting /48, persists `network.globals.ula_prefix`, checks the named UCI section type, and scopes rollback to the ULA option/newly-created globals section.

**Exact-head evidence:**
- Shared Hardware/Contracts [run #44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309), job 135105225016: 109 packager tests ran, 2 sandbox-only skips; 10/10 appliance profiles passed. The ULA first-boot, commit-failure rollback and wrong-`network.globals`-type tests executed and passed.
- Case-collision [run #44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296): PASS.
- Mandatory ImageBuilder sandbox [run #44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327): FAILED CLOSED because `bwrap` is absent; 14/14 host-preflight tests passed before the availability gate. No unsandboxed fallback or packaging pass is claimed from this run.

**Remaining contract gap:** random generation per installation does not prove that two independently installed appliances at the same site receive the same /48. The current implementation contains no site-level assignment authority or shared site identity input. Two first boots can therefore produce different prefixes on one site.

**Acceptance before contract completion:** PHX-CORE/COE owners must define a site-scoped assignment authority or explicitly propose a one-installation-per-site constraint for owner review. QA must verify two appliances on one site share the same prefix, independent sites receive distinct prefixes, and reboot/upgrade/restore preserve identity. Missing, malformed, unavailable or conflicting authority must fail closed before network services consume the prefix. No static/global fallback is permitted.

PHX-RELEASE owns first-boot implementation; COE integration owns destination staging; PHX-CORE/COE define provisioning authority; PHX-QA independently verifies exact-source behavior; PHX-HARDWARE validates target behavior only after authorization. PHX-MASTER owns the contract and gate, not implementation. Keep #44/#26 draft. **PRODUCTION NO-GO.**

## 6.31 ESP8266 EEPROM full-image read failure is not an erased Config state — source correction verified, physical durability open — 2026-11-19 UTC00

**Prior source hazard: corrected in the current Hardware candidate; independent QA and physical acceptance remain open.**

Hardware PR #327 is OPEN / DRAFT at docs head `3046c74d19ee1040996860a66cbdcb850acdbe14`; exact source/test head is `6b52d63f889a9567303f9f2de464c743c1991f0c`. Source correction commit is `40cfc0799a6e65e4a724e8ccbe6baa0f5f51de54`.

The ESP8266 sketch now performs a status-bearing raw `ESP.flashRead` of the full 544-byte EEPROM image using the core 3.1.2 EEPROM sector mapping. It reconciles the EEPROM emulation RAM buffer from that verified image before `EEPROM.get()` can supply Config. `configImageReadVerified` gates subsequent configuration and poll-fault writes. If the full-image read or RAM restoration fails, `loadCfg()` latches the persistence failure and returns before defaults, schema migration or commit; output polarity remains unknown and coin admission stays denied.

The source-extracted `config_load_read_failure_lab.py` at blob `9da02102020e97360320cfa7bc1f39a184b20011` executes the production `loadCfg/saveCfg` functions against a fault-injected EEPROM model that reproduces ESP8266 core 3.1.2 `EEPROM.begin()` ignoring the `flashRead` return value. It verifies:
- transient initial `EEPROM.begin()` read failure followed by a successful full-image read preserves the pre-existing poll-fault marker;
- recovered image survives the modeled cold-boot deny check;
- a subsequent full-read failure with marker-only recovery does not commit an unverified Config image;
- persistent full-image read failure prevents save/marker writes and preserves the existing marker.

**Exact-head CI at PR/docs head `3046c74d...`:**
- Quarantine/readback [run #44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021), job 135225761344: PASS; logs include all four EEPROM recovery markers above, plus dual-store and pending-journal source-extracted cases.
- Relay/output [run #44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181): PASS; includes the same EEPROM recovery markers.
- Full [run #44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063): FAILED only at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. All 13 firmware/platform target jobs plus Android succeeded; downstream simulations, update bundle, candidate gate, signing and publishing were skipped.

This corrects the previous full-image-read hazard in source-extracted host tests; it is **not** physical flash or power-cut evidence. LittleFS and EEPROM remain on the same flash device and do not constitute an independent witness. Physical reboot/power-cut behavior, 150 real power cuts, 30-device/24-hour soak, independent anti-rollback witness and production durable-accounting proof remain open. HARDWARE owns #327 source; QA owns the positive-signature fixture correction and independent same-SHA review; RELEASE owns toolchain pinning. MASTER does not modify firmware. **PRODUCTION NO-GO.**

## 6.32 ISR edge reconciliation must cover both poll-window outcomes — 2026-11-18 UTC21

**Status:** P0 source-level race reproduced by the current Hardware-owned source-extracted regression. PHX-HARDWARE owns the firmware correction; PHX-QA owns independent exact-SHA review. This is simulated control-flow evidence, not a reported physical coin/customer event.

At current Hardware PR #327 head `b346eba3ebee228abcff03456deb7889f2d39144`, the ESP8266 sketch blob is `4d73c5dc451c29f2ffd64a5cb2d230cc84a78ed5`. `loop()` snapshots `coinEdgeSequence` before `beginPollWindow()`, but compares it again only inside `if(beginPollWindow())`. The helper returns false when `coinLineQuietAfterInhibit()` detects activity; on that path it currently clears `pollIntakeSuspended`, reapplies outputs, and returns before the caller reconciles the ISR sequence.

The new `injectDuringDrainAbort` source-extracted case injects an ISR edge during the drain read and returns an active level, forcing the false-return path. The next main-loop sample sees the line idle after the injected pulse has ended. The caller does not observe the sequence delta, and the expected sticky `/pollpulse.fault` marker is absent. Exact-head focused CI fails this case with exit 25 on ESP8266. The current run stops on ESP8266, so no ESP32 result for this new false-return case is claimed.

**Required invariant:** after the quiet-drain helper returns, reconcile the ISR sequence regardless of whether the poll window is ready or aborted. Keep poll intake/output inhibition asserted until that reconciliation is complete. If the sequence advanced, latch unresolved ingress and persist the deny marker before any release or HTTP poll; do not convert the edge into pending credit or silently drop it. Only dispatch `post("poll")` when the helper reports ready and the before/after sequence is unchanged. A non-edge abort may follow its separately defined safe release path.

**Acceptance on both ESP8266 and ESP32:** inject an ISR edge during the final drain/abort sample, let the pulse end before the next ordinary loop sample, and assert: no HTTP poll; sticky recovery deny; marker persistence attempted before inhibition release; relay/LED logically OFF; active target cleared; no pending credit; poll timestamp deferred; no hot retry. Include a mutation that removes false-return reconciliation and must fail. Do not weaken default-deny or add synthetic poll signatures.

Exact evidence: [current sketch](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/b346eba3ebee228abcff03456deb7889f2d39144/experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino), [source-extracted poll-loop lab](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/b346eba3ebee228abcff03456deb7889f2d39144/experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py), [quarantine run 44404536230](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44404536230), [relay/output run 44404536459](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44404536459). These are host/source-extracted tests only; physical ISR, coin acceptor, relay and power-cut acceptance remain NOT TESTED.

**Separate P0 retained:** §6.31's full-image `EEPROM.begin()` read-failure/default-`saveCfg()` hazard remains open. The marker-only raw flash read does not prove the whole 544-byte EEPROM image was read successfully. The current #327 false-return regression does not address that separate path.

### §6.32 — UTC22 exact-head evidence refresh (2026-11-18T22:51:38.802Z)

Live Hardware #327 API head is f9d1fa165ccc94b18aeac7e85ffd83c29899463f; source/test SHA is ed667e88f6844284834ebd3a337dfce07a817e8c; firmware correction commit is ddb386847e152e8ca4992e9f6b3370bfa3f20462. The PR description still cites c51271938c15e13998d1c99f1d311ca777bb1cc2 and is stale. #327 remains OPEN/DRAFT under #326 at 58c558fb6a237935214621adc3dee65a10fe1a51.

- ESP8266 sketch blob cd1acb1da298d4f9598e943dae05918b088e5363; ESP32 sketch blob ef498761e46d37134730dd41de1cc322d5d443e8; poll-loop lab blob 02dc80e547424817d00bfa23c70540a51a262273; full-image EEPROM read lab blob 07e44b5076db69c1d55e913790c44a5feac29ca3.
- Exact-head quarantine/readback 44414150601 and relay/output 44414150956 both pass the poll-drain abort scenario on ESP8266 and ESP32, including POLL_ABORT_DRAIN_INHIBIT_CONTINUITY_PASS, both abort-edge persistence modes, and POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS.
- Both focused jobs then fail in ESP8266 config_load_read_failure_lab.py: expected exit 0, got 31 in the first recovery scenario. The combined predicate is not split into individual failure messages. Source inspection shows loadCfg() still calls EEPROM.begin(544) then EEPROM.get(0,current); the status-bearing raw ESP.flashRead helper reads only the poll-fault marker, not the complete Config image. Full-image read-failure/recovery remains OPEN.
- Full run 44414150578 has validation job 135190015439 failing at the inherited QA-owned “Missing poll signature check”. All 13 firmware/platform targets and Android completed SUCCESS; simulations, bundle, candidate, signing and publishing were skipped.

Disposition: poll-drain abort is focused CI subtest PASS on both source models; overall focused jobs remain FAIL at the separate full-image EEPROM read lab; Full validation FAIL; independent QA and physical hardware acceptance pending. Same-flash stores are not an independent anti-rollback witness.

## 6.33 COE #45 receipt v1 — contract candidate, not Master adoption (2026-11-18 UTC23)

**Disposition:** CONTRACT CANDIDATE / SYNTHETIC CI VERIFIED / RUNTIME DENY / NOT IN COE #26.

Exact candidate: COE PR #45, OPEN/DRAFT, head 9d76a134c1f6512aa40c20ec4d247306a71a8cce, base d0830332 (a separate candidate base, not COE #26). The contract, golden vectors, verifier and focus runner are under Pisowifi/docs/contracts and Pisowifi/tests. Exact-head run [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) passed and logs include COIN_RECEIPT_V1_GOLDEN_PASS; case-collision run [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) passed. These are synthetic/host contract checks, not a deployed producer, firmware parser, financial ledger, key provisioner or hardware acceptance.

### Contract shape and incompatibility

COE v1 uses canonical ASCII name/value lines with LF, fixed field order and HMAC-SHA256. It binds receipt_id to the event hash and includes event_nonce, target_nonce, account_id_hash, ledger_epoch, ledger_sequence, issued_at, expires_at, disposition/reason, pulse_count, credit_delta_centavos, credit_total_centavos and key_version. It specifies stable retry bytes for an already committed event.

Master §1.2 currently documents a different v2-style receipt example: event_id, protocol_version, target, amount_centavos, seconds_granted, timestamp_utc, nonce, signature and replayed. There is no approved v1-to-v2 mapping, version negotiation, field-equivalence table or consumer migration. In particular, target vs target_nonce, seconds_granted vs credit_delta_centavos, event_id vs receipt_id, and signature vs HMAC are not one-to-one substitutions. The new ledger_epoch/ledger_sequence and account_id_hash fields have no approved Master-v2 mapping. **Do not adopt COE v1 as the Master canonical receipt or copy it into #26 until CORE and QA approve an explicit versioned bridge.**

### Test coverage and remaining proof

The exact verifier checks the known golden vectors, fixed field ordering, event-derived receipt ID, HMAC sensitivity to each field and byte-identical committed retry. Source inspection shows the verifier does not yet enforce uint32/uint64 upper bounds for key_version, ledger_sequence, timestamps and centavo values; it checks account_id_hash syntax but does not derive it from an approved canonical account identity; it has no approved clock-skew policy; and it does not implement or test a production parser/consumer. The three committed vectors do not exercise every allowed disposition/reason or malformed, duplicate, missing, unknown and reordered input. These are QA/CORE follow-ups, not a reason to weaken runtime default-deny.

**Adoption gate:** CORE must publish the versioned field mapping, numeric bounds, account-hash derivation, key-version authority, ledger-epoch authority and replay semantics. QA must add parser-level malformed/boundary/replay vectors. Hardware and Release must remain deny-only until the shared contract and durable authority are independently approved.

## 6.34 Hardware #327 — full-image EEPROM read recovery corrected in source tests (2026-11-18 UTC23)

**Current live PR head:** 3046c74d19ee1040996860a66cbdcb850acdbe14 (docs-only handover sync), child of #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. **Exact source/test head:** 6b52d63f889a9567303f9f2de464c743c1991f0c. **Firmware correction commit:** 40cfc0799a6e65e4a724e8ccbe6baa0f5f51de54.

The source correction adds a status-bearing read of the complete 544-byte ESP8266 EEPROM image, restores that verified image into the EEPROM RAM buffer, and tracks configImageReadVerified. loadCfg refuses to interpret an unreadable image as erased defaults; saveCfg and writePollFaultBackup require a verified image and revalidate after reopening. The reserved poll-fault bytes at offset 512 are preserved by the source-extracted recovery lab.

Exact source/test-head focused evidence:
- [Quarantine/readback #44423903845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903845) PASS. Logs show full-image first-read recovery with marker preservation, recovered-image cold-boot deny, marker-only recovery without commit, persistent full-read failure without commit, poll-drain abort continuity and pulse capture pass on both board-shaped harnesses.
- [Relay/output #44423903842](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903842) PASS. Both boards report 48/48 relay-polarity cases; output-off preload, poll-drain and pulse-capture checks pass.
- Source/test-head Full runs [PR #44423903891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903891) and [push #44423897080](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423897080) completed FAILURE at the inherited QA-owned Missing poll signature check. All 13 firmware/platform targets plus Android completed successfully; simulation, update bundle, candidate, signing and publishing jobs were skipped.

The live PR head advanced after those source/test runs: docs-head quarantine [#44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021) and relay [#44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181) were IN_PROGRESS at this audit; Full [#44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063) was QUEUED. Therefore the current PR head 3046c is not yet exact-head CI VERIFIED. PR description and the top handover pin still cite older c51271938; the live PR API and the appended UTC23 handover section are newer. HARDWARE must refresh its own PR description and top handover pin.

These are source-extracted host/fake-I/O simulations only. The same flash chip backs LittleFS and EEPROM/NVS; simultaneous store failure still yields current-boot denial only and is not an independent protected witness. No physical flash, GPIO/relay/acceptor test, power cut, native acceptance or 30-device soak is established.

## 6.35 Hardware #327 docs-head final CI readback — 2026-11-18 UTC23

The live #327 PR head remains 3046c74d19ee1040996860a66cbdcb850acdbe14; exact firmware/source-test head remains 6b52d63f889a9567303f9f2de464c743c1991f0c. The docs-head Actions runs have now completed:
- [Quarantine/readback #44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021): PASS.
- [Relay/output #44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181): PASS.
- [Full build #44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063): FAILURE at QA-owned Controller protocol parity / Missing poll signature check. All 13 firmware/platform targets plus Android passed; simulation, update bundle, candidate, signing and publishing jobs were skipped.

This supersedes the in-progress/queued snapshot in §6.34 for the same docs-head. The EEPROM read-recovery correction remains source/test verified; the only Full validation failure is the inherited positive poll-signature fixture. The PR body/top handover still cite c51271938 and must be refreshed by HARDWARE. No physical hardware or power-cut acceptance is established.



## 6.36 Release ImageBuilder overlay-size accounting — descriptor-pinned no-follow contract (2026-11-19 UTC01)

**Disposition:** SOURCE/TEST FIX VERIFIED IN HOST CI / MANDATORY IMAGEBUILDER SANDBOX BLOCKED / INDEPENDENT QA REVIEW REQUIRED / NOT A RELEASE APPROVAL.

COE Release PR #35 current docs head is 3455e0ce56bed780a727a6297db14a8e1d345f99; exact packaging source/test head is 5e25e4ceab7c0615bcdad8309d50739e6b255f46. The source replaces path-based overlay walking with Linux/POSIX descriptor-pinned traversal: open entries with O_PATH|O_NOFOLLOW, fstat the opened object, compare its device/inode to a no-follow stat relative to the pinned parent directory, open child directories with O_DIRECTORY|O_NOFOLLOW, and fail closed on identity changes or missing platform primitives. Symlinks are excluded from the byte budget; regular staged files are counted from the opened object rather than a re-resolved path.

Test-first evidence:
- RED #44435063672 reproduced regular-file-to-symlink replacement at the open boundary.
- RED #44436345907 reproduced symlink-to-regular replacement and the old undercount.
- Exact source/test shared run #44436769990 passed; docs-head shared run #44438686744 passed 107 packaging tests with two intentional sandbox-only skips, all ten appliance profiles, shared-contract checks, and ESP32/ESP8266 compile/upload.
- Docs-head case-collision #44438686678 passed.
- Mandatory sandbox #44438687009 failed closed after 13/13 host-preflight tests because bubblewrap is absent (exit 125). No unsandboxed fallback or actual sandbox packaging acceptance is claimed.

**QA follow-up discovered by Master source/test inspection:** both race fixtures replace the directory entry inside the patched os.open wrapper before delegating to the real open. They cover both entry types at the open boundary, but do not exercise replacement after the O_PATH descriptor has been acquired and before the subsequent dir_fd no-follow stat. The implementation compares inode identity and raises ValueError on that later mismatch, but this branch lacks a deterministic regression. PHX-QA should add both post-open replacement directions and assert fail-closed behavior with unchanged external sentinel bytes. This is a test-coverage gap, not a confirmed source defect.

The CI artifacts are nonproduction build archives. PR and push artifact ZIP digests differ; no byte-reproducible firmware claim, signed release, real ImageBuilder sandbox run, target flash, or hardware acceptance follows from these checks.

## 6.37 COE Release #44 site ULA and #35 stack ancestry — no adoption (2026-11-19 UTC01)

COE #44 remains OPEN/DRAFT at 582fd5d5e83e36b36546ac28534740298ba94af4, based on the earlier #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4. Current #35 is at 3455e0ce56bed780a727a6297db14a8e1d345f99. GitHub compare reports #44 is 15 commits ahead and 13 commits behind current #35. These are divergent sibling stacks; #44 does not contain the current #35 overlay-accounting source/test and terminal handover commits. PHX-MASTER did not merge, rebase, cherry-pick, or alter either release branch. PHX-RELEASE must reconcile the stack without force-push before treating the candidates as one release lineage.

The #44 first-boot script generates a random 40-bit RFC 4193 ULA global ID per installation, commits the prefix to UCI, validates persisted readback, and scopes rollback to its own option/section. Its shared CI #44390136309 and case-collision #44390136296 pass; mandatory sandbox #44390136327 remains blocked by missing bubblewrap. A random prefix per installation does not establish the Master §6.9 same-site rule that multiple appliances at one site share a site identity. Site-level assignment authority and same-site/different-site, reboot, upgrade, and restore tests remain open. No ULA contract adoption or migration is approved.


## 6.38 Board toolchain versions are part of firmware and migration identity — 2026-11-19 UTC02

**Disposition:** exact-head CI exposes unpinned ESP32 core drift; COE destination compile is blocked; PHX-MASTER changed no firmware or workflow source.

Experiments #327 source sketch blob ef498761e46d37134730dd41de1cc322d5d443e8 (59,117 bytes) differs from COE #35 destination blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 (18,505 bytes). Both contain mbedtls/sha256.h; source also includes nvs.h and string.h, absent from destination.

Experiments #327 run #44439616677 installed esp32:esp32 3.3.13 and compiled. COE #35 run #44443780617 installed 4.0.0 and failed because mbedtls/sha256.h was not found; ESP32 artifact upload was skipped. Both workflows use unpinned arduino-cli core install esp32:esp32 commands. A green unpinned source run is not a reproducible destination-compatibility claim.

**Required contract:** pin Arduino CLI, exact ESP32/ESP8266 core versions, FQBN and build options. Source and destination must use the same pinned toolchain, or an independently verified upgrade matrix. Record resolved versions with job evidence; never use an unpinned latest package index as migration equivalence. RELEASE owns workflow pinning; HARDWARE owns firmware compatibility; QA owns independent same-SHA verification. Master edits neither subsystem firmware nor release workflows.

COE #35 mandatory sandbox remains blocked by missing bubblewrap after 14/14 host-preflight tests (exit 125). Site-scoped ULA, independent durability witness and production acceptance remain open. **PRODUCTION NO-GO.**

## 6.38.1 UTC03 correction — COE #35 toolchain pinning verified; #26 remains floating

**Disposition:** the earlier UTC02 ESP32 toolchain-drift finding is corrected for COE #35 only. It is not corrected for the integration candidate #26.

At COE #35 current PR head a270b547fb5ff570bd2bc49c2e96219043d7c9bd, source/test head 3b83a408583091f2b2e8a7cf4ef73833f2eb9e39, the release-owned hardware workflow pins Arduino CLI 1.6.0, ESP8266 core 3.1.2, and ESP32 core 3.3.13, with runtime version checks. The setup action is pinned to immutable commit b3cda96fddef6af6c56b4c5efb5c47e2357935db. The pin guard is tools/test_release_toolchain_pins.py. Current workflow blob: e16e6e0f97092bd63a5dec8b871f98be2149847f; guard blob: 983f12ead5e76e59f5d1dec0b42b3facda66fd32.

Exact-head evidence: shared/firmware run 44451317780 PASS, including both board compile/artifact-upload jobs; case-collision 44451317996 PASS; mandatory sandbox 44451317807 FAIL CLOSED because bwrap is absent (exit 125). No unsandboxed fallback was used. The current PR description still contains older head/status text; the current handover at a270 records the pinned toolchain evidence. PHX-RELEASE owns refreshing its PR description.

COE #26 remains different: its hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 uses arduino/setup-arduino-cli@v2 and unversioned core-install commands for both ESP targets. Its Hardware/README.md blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb documents ESP32 core 3.3.12 and ESP8266 core 3.1.2. The #35 pin fix is not present in #26, and #26's README/workflow do not agree on an exact ESP32 core. Do not infer toolchain parity across branches.

## 6.39 Hardware migration identity requires exact source, test, license, and toolchain parity

**Disposition:** COE #26 is not an import-complete or behavior-equivalent destination for current Experiments Hardware #327. No staging, copy, move, overwrite, or migration is approved.

Current Experiments #327 branch head is 11fae729df415cc26b9e1675b1758cd8e4d22648, child of #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. The PR description still says a3597125fef3964ab08f05b3300c8de3e47516ae; that description is stale. Commit 11fae729 adds an explicit Mbed TLS major guard: major 4 uses PSA Crypto, major 3 uses the legacy SHA-256 API, and every other major fails compilation. Exact current ESP32 source blob f54805b17cac45388dfacc5e65eff9b731234316 is 60,326 bytes. ESP8266 source blob 1b32cb90be11da79ba7ea1155f128aee9e495dd2 is 67,300 bytes.

The latest #327 exact-head CI is focused quarantine/readback 44453235563 PASS, relay/output 44453235544 PASS, and Full build 44453235564 FAILURE at the QA-owned Controller protocol parity / Missing poll signature check. The ESP32 job 135322011864 compiled successfully with esp32:esp32@4.0.0 and uploaded artifact 14496054232; all target and Android jobs completed successfully. Downstream update bundle, simulation, signing, candidate and publishing jobs were skipped. The 4.0.0 compile verifies the Mbed TLS 4 branch, not the Mbed TLS 3 branch or unsupported-major rejection at runtime. The latest source-extracted lab head remains 071a711d6598c67124e84ffd995fd48aa7d9f054; no dedicated unsupported-major test was added. PHX-HARDWARE owns the source; PHX-QA owns independent negative/default-deny and version-matrix review. Master did not edit the Hardware branch.

Exact current source/destination sketch comparison at #327 head 11fae729 and COE #26 head b382d233:

| Platform | Experiments #327 source blob / bytes | COE #26 destination blob / bytes |
|---|---|---|
| ESP8266 | 1b32cb90be11da79ba7ea1155f128aee9e495dd2 / 67,300 | c8be98f72596681e36a3ad1f8939bf8046c96887 / 18,394 |
| ESP32 | f54805b17cac45388dfacc5e65eff9b731234316 / 60,326 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 / 18,505 |

Neither platform is byte-identical. The current source acceptPollResponse() returns false on both boards and contains no positive |poll| token. COE #26's Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e (4,118 bytes) is one generic shell test that greps for response_sig, |register|, |poll| and quarantine routes, then performs brace balancing. It is not equivalent to the eight source-side Python lab files in #327 (coin pulse capture, config read failure, boot polarity, dual-store fault, poll-loop inhibit, fail-closed response, poll-window drain, request-digest failure). Importing the current source without replacing this positive-presence fixture would produce a test-identity conflict. The destination README also describes positive response-signature verification, while the current Master/HW contract intentionally remains default-deny pending the approved producer and QA vectors.

License evidence: source BlazePwifi/LICENSE and COE Pisowifi/LICENSE are byte-identical at blob 1ee55b94183417be977ca287cd7391f9a6f7e721. COE Hardware/LICENSE and Hardware/NOTICE.md are absent; source BlazePwifi/NOTICE.md and COE Pisowifi/NOTICE.md are also absent. The #26 PR description was updated at 2026-11-19T03:44:46Z to claim the licensing/privacy gate is resolved, but the Hardware subtree's explicit license/notice scope is not established by the exact files inspected. That claim is not independently accepted as migration evidence.

COE #26 remains OPEN/DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12. Its five current workflows (case-collision, Windows SoftTimer, Hardware/shared contracts, Rental, Pisowifi) are QUEUED with zero jobs. The PR description also claims 18/18 tests and 95% software readiness; those claims are not destination-CI evidence while all five workflows have no jobs.

**Required admission evidence:** per-file source/destination path, mode and blob SHA; complete import inventory; license and NOTICE scope; exact test identity and negative-path coverage; pinned CLI/core/FQBN/options; exact-head destination CI; reversible rollback evidence; owner approvals. Until all are independently reviewed, keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null.


## 6.40 Local EEPROM configuration migration is not financial-ledger migration evidence

**Classification rule:** ESP8266 local device-configuration migration from ConfigV1/ConfigV2 to ConfigV3 is a separate persistence domain from the financial ledger v1-to-v2 migration. Passing the former must never be reported as testing, proving, or authorizing the latter.

At current Hardware PR #327 branch head e799b0f042889b97ba7bae2ae2e06c1ec76392d6 (docs-only successor), the relevant firmware source commit is 11fae729df415cc26b9e1675b1758cd8e4d22648 and the exact source/test lab head recorded by Hardware is 071a711d6598c67124e84ffd995fd48aa7d9f054. The ESP8266 source blob 1b32cb90be11da79ba7ea1155f128aee9e495dd2 is 67,300 bytes; the COE #26 destination blob c8be98f72596681e36a3ad1f8939bf8046c96887 is 18,394 bytes. The ESP32 source blob f54805b17cac45388dfacc5e65eff9b731234316 is 60,326 bytes; the COE #26 destination blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 is 18,505 bytes. Neither platform is byte-identical.

The local configuration failure lab is present at source blob 40dfa46e48d8288bf94ad8c5579bf0d7436d4df6. It is invoked indirectly by coin_pulse_capture_lab.py blob cdc6d85aed5e5a0c85b154afa67c302023ec20b9 (lines 337-339); the PHX-HARDWARE quarantine workflow blob fe98e5e41dbf73e22fbd34479dbc971f008d18c9 invokes coin_pulse_capture_lab.py. This invocation chain is confirmed by exact-head quarantine/readback run 44453718564, job 135323579699. The job log reports full-image read failure/recovery cases, malformed v1/v2 and unknown-schema setup-save denial, valid local v1/v2 migration marker preservation, and failed local migration commit same-boot denial/cold-boot retry.

The lab explicitly emits LOCAL_CONFIG_MIGRATION_LAB_ONLY=1, FINANCIAL_MIGRATION_TESTED=0, PRODUCTION_MIGRATION_AUTHORIZED=0, SIMULATED_ONLY=1 and PHYSICAL_POWER_CUT_VERIFIED=0. This is source-extracted fake-I/O evidence only. It does not establish physical EEPROM durability, a financial ledger schema transition, receipt/replay consistency, an independent durability witness, or reversible financial migration.

Exact-head #327 focused quarantine run 44453718564 and relay/output run 44453718633 pass. Full run 44453718661 fails at the QA-owned Missing poll signature check (validation job 135323581119); all 13 firmware/platform target jobs and Android complete successfully, while downstream simulation, signing, candidate and publishing jobs are skipped. The Mbed TLS 4 / ESP32 core 4.0.0 path has compile evidence; an exact-head Mbed TLS 3 / ESP32 core 3.3.13 rebuild and an executable unsupported-major compile-rejection test remain NOT RUN.

**Contract:** PHX-HARDWARE owns local device configuration and firmware; PHX-CORE owns financial ledger and receipt semantics; PHX-QA independently verifies both domains at exact SHAs. Do not let a local EEPROM configuration test satisfy the financial migration gate. No financial interface or source code was changed by Master.


## 6.41 Hardware #327 Mbed TLS selector and COE #26 migration gate — exact current heads (2026-11-19 UTC06)

**Disposition: COE #26 Hardware migration remains BLOCKED. Keep the current firmware poll and coin-disposition consumers deny-only. No source or destination staging is authorized.**

Experiments Hardware PR #327 is OPEN / DRAFT at branch head ba4c0cb0c5eae4be5e014c0df6f5abe20a67b0bf, based on #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. Its source/test commit is 0e5514adb0088649eca8bec9df6215faa50b556c. Current ESP32 sketch blob c29483f0761ca6e2db0573bd12d6bfa502f12434 is 61,807 bytes; ESP8266 sketch blob 1b32cb90be11da79ba7ea1155f128aee9e495dd2 is 67,300 bytes.

The ESP32 sketch selects PSA Crypto for Mbed TLS major 4, the legacy SHA-256 API for major 3, and emits a compile-time error for every other major. Both current board sketches keep acceptPollResponse() and coinPostDispositionVerified() fail-closed: each returns false. The response_sig reference in source comments describes an unapproved derived candidate; it is not a positive poll authorization implementation.

Exact current-head Hardware CI:
- Focused quarantine/readback [#44468941707](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941707), job 135373435174: SUCCESS. Logs report Mbed TLS 3/4 selector and digest checks, rejection of unsupported majors 2/5, coin POST gate scenarios, poll-window/edge labs and local EEPROM configuration failure cases.
- Relay/output [#44468941718](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941718): SUCCESS.
- Full [#44468941728](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941728), validation job 135373435914: FAILURE at the inherited QA-owned v05_firmware_hardening_test.sh assertion “Missing poll signature check”. The 13 firmware/platform targets and Android completed successfully; downstream simulation, candidate, signing and publishing jobs were skipped.

The focused Mbed TLS lab emits MBEDTLS_MAJOR_3_SELECTOR_AND_DIGEST_PASS, MBEDTLS_MAJOR_4_SELECTOR_AND_DIGEST_PASS, MBEDTLS_UNSUPPORTED_MAJOR_2_REJECTED and MBEDTLS_UNSUPPORTED_MAJOR_5_REJECTED, but explicitly sets STUB_API_ONLY=1 and EXACT_ESP32_CORE_3_3_13_BUILD_REQUIRED=1. This is host stub/API evidence, not an actual ESP32 core 3.3.13 build. The Full run compiled ESP32 using resolved core 4.0.0 and ESP8266 using 3.1.2. The Experiments build workflow blob 2cd6ce83b01c65fd78df091e502b68bf4fd277dc still installs unversioned board cores.

The source-side v05_firmware_hardening_test.sh blob 41211b2c110ab409f6d9d1812ef12fda73b13211 still requires response_sig, |register| and |poll| strings. Its current failure is the positive |poll| assertion. Do not weaken the firmware or add a fake signature token to satisfy this legacy fixture. PHX-QA owns replacing the obsolete positive-presence assertion with source-exact negative/default-deny tests at the current source SHA.

COE integration PR #26 remains OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12; COE main is a6513ab4412b4c014eee2863e45cbe32d06cb243. Its ESP32 destination sketch blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 is 18,505 bytes, has no Mbed TLS major selector, retains the legacy mbedtls/sha256.h include and contains a positive response_sig/|poll| consumer. It is not the current deny-only source. The source/destination ESP32 Git blobs differ.

PR #327's changed-path inventory contains nine Python lab files (eight ESP8266-oriented labs and one ESP32 Mbed TLS compatibility guard). COE #26 has one generic Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e. That destination test positively requires response_sig, |register| and |poll|; it is not equivalent to the current source labs or contract. The five #26 workflows remain QUEUED with zero jobs, so no destination build or test has executed.

COE #26 hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 installs unversioned ESP32/ESP8266 cores. Hardware/README.md blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb documents ESP32 3.3.12 and ESP8266 3.1.2, which is not enforced by that workflow. COE Release #35 has a separate pinned toolchain at head 5047af8b5a8296e06294bbda6bf42a6baea2294d: Arduino CLI 1.6.0, ESP8266 3.1.2 and ESP32 3.3.13. Its shared/firmware run #44465377784 and case-collision run #44465377781 pass; mandatory sandbox run #44465377807 fails closed because bubblewrap is absent after 14/14 host-preflight tests. The #35 pin fix is not present in #26.

Release #35 is 108 commits ahead / 0 behind parent #31 at 59ed44d0b911e176f1a95b9cf5585ef811ffd31b. Release #44 is at 582fd5d5e83e36b36546ac28534740298ba94af4, based on older #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4; compare #35 → #44 is DIVERGED, 15 ahead / 25 behind, and PR #44 reports mergeable=false. PHX-RELEASE owns history-preserving reconciliation; Master did not modify either branch.

COE INTERCON candidates remain separate. Stage-3 #39 uses a 64-byte journal, #40 a 76-byte journal, and #42 a 92-byte journal; each has exact-head host/simulation and board compile CI success. Stage-4 #41 is shadow-credit only on #39; #43 is live timer/relay behavior on #42. Both have passing scoped CI, but they are not equivalent and do not establish physical flash durability, real power-cut recovery, protected key custody or a canonical router financial adapter. No candidate is selected.

License evidence remains incomplete: source BlazePwifi/LICENSE and COE Pisowifi/LICENSE are the same MIT blob 1ee55b94183417be977ca287cd7391f9a6f7e721, but COE Hardware/LICENSE and Hardware/NOTICE.md are absent at #26. The source BlazePwifi/NOTICE.md is also absent at the inspected source root. The Pisowifi license does not by itself establish Hardware subtree license/NOTICE scope.

**Migration admission remains closed** until exact per-file path/mode/blob provenance, all required source labs or reviewed equivalents, negative/default-deny tests, pinned CLI/core/FQBN/options, runnable exact-head destination CI, explicit Hardware license/NOTICE scope, reversible rollback evidence and owner acceptance are independently verified. Keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, with PHX-MASTER destination null. PRODUCTION NO-GO remains binding.

### UTC07 exact-head supersession — 2026-11-19

At current Hardware PR #327 head, branch phoenix/hardware-prepoll-edge-abort-20261119 is 31f5d727f0f61128694b9b0c4b92af8e4b6afa52, based on #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. Hardware identifies c37338439eec23c54a2e4a5f9c9c538d08f182cf as the source/test commit. Current sketch blobs are ESP8266 1b32cb90be11da79ba7ea1155f128aee9e495dd2 (67,300 bytes) and ESP32 c29483f0761ca6e2db0573bd12d6bfa502f12434 (61,807 bytes).

Exact-head CI:
- Focused quarantine/readback [#44478447580](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447580), job 135404563994: SUCCESS. The source-extracted poll-response lab reports 11/11 fail-closed cases per board, 13/13 strict-root-JSON cases per board, coin POST root-status 4/4 per board, and coin-disposition default-deny 4/4 per board. The same run reports simulated EEPROM/NVS, poll-window, pending-journal and request-digest labs; physical flags remain zero.
- Relay/output [#44478447647](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447647), jobs 135404564309 and 135404565326: SUCCESS. ESP32 boot-polarity logs show unknown/legacy profile stays INPUT, local polarity readback passes, active-high/active-low OFF preload passes, and remote polarity authority is denied.
- Full PR [#44478447410](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447410), validation job 135404563869: FAILURE. All 13 firmware/platform targets and Android completed successfully; downstream simulation, update-bundle, signing, candidate and publishing jobs were skipped.

The Full failure is the legacy QA fixture, not a reason to relax firmware. The exact test chain is:
- controllers.sh blob f7896647713d6bf8034ff48ed19b6383e4dedea0 invokes tests/v05_firmware_hardening_test.sh.
- That fixture blob 41211b2c110ab409f6d9d1812ef12fda73b13211 still requires positive response_sig, |register| and |poll| source strings; its |poll| assertion is the reported failure.
- Both current board sketches keep acceptPollResponse() and coinPostDispositionVerified() fail-closed (return false). The focused source-extracted poll_response_failclosed_lab.py blob 69dbddee4133588940f4c5b53817401db531a8a4 already exercises negative/positive-looking response denial.

**Master direction:** PHX-QA must replace only the obsolete positive-presence assertion with source-exact negative/default-deny tests and ensure the source-extracted lab remains in the Full validation path. Do not add a fake |poll| token, enable positive unauthenticated admission, or weaken the firmware to satisfy a string grep. PHX-HARDWARE retains sketch ownership. This remains SIMULATED/CI evidence only; physical relay, coin acceptor, flash and power-cut acceptance are NOT TESTED.


## 6.42 Release handover freshness is a build-provenance admission gate — 2026-11-19 UTC07

Release PR #291 is OPEN/DRAFT on branch phoenix/release-publisher-isolation-20261115. The live PR and branch ref both remain 3ef73265abd52bf44273584afc406382c2805b1d (base 734b89d9e7792247e8376335c3f3685500ab3f89). The PHX-RELEASE UTC07 progress comment reports b8f4e3619a8c84b4e81d8bb24ba3da02825fa9e6, but the branch did not move. That commit object changes only .github/PHX_RELEASE_HANDOVER.md; it is not the current PR head and does not prove the reported workflow/script scope is on the branch.

Exact current-head CI:
- Windows release [#44479756135](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756135), handover job 135408844761: FAILURE; build and publisher skipped.
- BlazePwifi build [#44479756093](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756093), validation job 135408938465: FAILURE at tests/handover_gate.sh. The log says source/workflow changes are newer than experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md, identifies .github/workflows/blazepwifi-build.yml, and reports last checkpoint c0b5f3731e1db81faf275bf8f32a757f7d52f3d2. Downstream release/simulation/signing/publishing jobs are skipped.
- ESP32 core compatibility [#44479756113](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756113): SUCCESS.

**Contract:** any release-owned build/workflow/toolchain/provenance change must be followed on the same candidate branch by an updated authoritative product handover, live state and change ledger that identify the exact source/workflow SHAs, pinned CLI/core/FQBN/options, artifact hashes, CI run/job IDs, and explicit unsigned/unreleased state. The handover freshness gate must pass before artifacts are admitted to downstream simulation, signing, publishing or promotion. Green compile jobs do not override a failed handover gate. Do not bypass or disable the gate. PHX-RELEASE owns its branch/workflow and must coordinate with the designated handover owner; PHX-MASTER owns this contract only and does not edit subsystem or release files.


## 6.43 Exact-head release provenance and current poll-deny validation — 2026-11-19 UTC08

**Disposition: release handover and COE migration remain blocked; current poll and coin-disposition consumers remain deny-only.** A BLAZE-COMMS checkpoint is a status statement, not a substitute for the live PR head. Reviewers must compare the named checkpoint SHA with the current PR head and record ancestry before treating its tests as exact-head evidence.

At live Experiments PR #291, the current head is d498afbf2aa0e60fc1b1d0471328f5e6eb8e597c. The UTC08 RELEASE checkpoint #7003579497 names b8f4e3619a8c84b4e81d8bb24ba3da02825fa9e6 as current head, but GitHub compare shows the current PR head is 12 commits ahead / 0 behind that SHA. The current d498af exact-head Windows and BlazePwifi workflows fail the mandatory handover freshness gate; board compilation and the separate ESP32 compatibility workflow passing do not override it. RELEASE must refresh canonical product handovers and re-run the exact live PR head. No bypass is permitted.

At Hardware PR #327 head c62af73ec5b45cd87f4c8f3295ede18f307fb359, quarantine/readback and relay/output focused workflows pass, while Full validation fails at the inherited positive “Missing poll signature check” assertion. The source-extracted poll-response lab deliberately denies current positive-looking responses. QA must replace the obsolete positive-presence fixture with negative/default-deny source-exact tests; Hardware retains firmware ownership. Do not add a fake signature token or enable unauthenticated admission.

COE #26 remains a separate draft staging candidate. Its ESP32/ESP8266 blobs differ from current #327 source, its Hardware test still requires positive signature/poll strings, its Hardware license/NOTICE scope is absent, and all five destination workflows remain queued with zero jobs. The source and destination LICENSE blobs match only for the Pisowifi/BlazePwifi scope; this does not establish Hardware subtree license scope. No migration is authorized.

Master CI was not run because the execution runtime could not resolve github.com; no Master test pass is claimed. This section records source/tree and exact-head Actions inspection only. PRODUCTION NO-GO remains binding.


## 6.44 Exact-head poll consumer remains deny-only — 2026-11-19 UTC10

**Disposition: retain firmware default-deny; repair the legacy positive fixture in QA-owned validation, not in firmware.**

At Experiments HARDWARE PR #327 head `47eceaf2ccd3cfdc3403df6b1964610bd32ed24f`, ESP8266 sketch blob `75f62c359bbb69f4f580b7ee0c3875396b12cc7f` has `acceptPollResponse()` explicitly clear `insertMode` and `activeTarget`, then return `false`; `coinPostDispositionVerified()` also returns `false`. The source says the current `response_sig` expression is only a derived candidate pending CORE's canonical producer and QA-approved vectors. The source-extracted poll lab is blob `69dbddee4133588940f4c5b53817401db531a8a4`.

Exact-head Full run [#44501072563](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072563) fails in validation job `135480829727` at legacy `Missing poll signature check`. All 13 firmware/platform targets and Android completed; downstream simulations, update bundle, candidate, signing and publishing were skipped. Focused quarantine [#44501072485](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072485) and relay/output [#44501072498](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072498) passed. Quarantine logs include both-board poll-fault and EEPROM/config labs, but explicitly report `SIMULATED_ONLY=1`, `FINANCIAL_MIGRATION_TESTED=0`, and `PHYSICAL_POWER_CUT_VERIFIED=0`.

Do not add fake `response_sig` or `|poll|` markers and do not enable poll admission to make the old assertion green. PHX-QA owns source-exact negative/default-deny cases at the same source/test SHA. PHX-CORE owns the future canonical response envelope and golden vectors; PHX-HARDWARE retains firmware ownership. This is not financial disposition or hardware acceptance.


## 6.45 Site-scoped RFC 4193 ULA provisioning contract — decision required (2026-11-19 UTC10)

COE Release #35 at `5047af8b5a8296e06294bbda6bf42a6baea2294d` emits `option ula_prefix 'fd00:db8:blaze::/48'` from packager blob `f1d9c8ef1da7e1d3df11f45dfe36f14f5f11a650`. Independent Python `ipaddress.IPv6Network(..., strict=False)` rejects it: `AddressValueError: Only hex digits permitted in 'blaze'`. The accompanying test blob `e3f625673bd90bb28e107a88aff9ed4d824a2bb7` checks bridge/VLAN output and formatting but contains no ULA/IPv6-prefix validity assertion.

**Normative interface constraints:**
1. A site ULA must be a valid RFC 4193 prefix in `fd00::/8`, with a 40-bit Global ID and `/48` length. Reject malformed/non-hex, non-`/48`, documentation placeholders, multicast, link-local, global-unicast and unspecified values.
2. It is site-scoped: all appliances at one site share the same prefix; distinct sites use independently provisioned/generated Global IDs with collision-aware handling. A random prefix per appliance is not a site identity.
3. Persist the prefix across reboot, upgrade, migration, backup and restore. Do not regenerate it during ordinary boot/restore or derive it from a device MAC/product name.
4. The provisioning authority is undecided. PHX-CORE and the COE integration owner must choose owner-provisioned site prefix or a first-boot site authority that creates/distributes one durable identity. PHX-MASTER does not invent a prefix, secret or site credential.
5. Until that decision exists, packagers fail closed when no approved site prefix is supplied. Never emit `fd00:db8:blaze::/48`, another hard-coded vendor literal, or a per-appliance fallback.
6. QA independently tests syntax, /48, same-site sharing, distinct-site separation, persistence/restore and authority-unavailable denial.

PHX-CORE/COE own the provisioning decision; PHX-RELEASE implements after approval; PHX-QA owns independent vectors. This contract does not change networking code or authorize hardware acceptance.



### UTC14 exact-head supersession — 2026-11-19T14:39:41Z — site ULA implementation evidence

The §6.45 decision remains **site-scoped**, not per-appliance: appliances at one site must share one durable RFC 4193 /48; independent sites must not share the same Global ID; the selected identity must survive reboot, upgrade, backup and restore. The current COE RELEASE #35 source/test head is `90ce4200b66ce0b55f40feaab42cc7b53fad1f2d`, with final documentation head `0e3662b9aef4b2a2248e3a064b07d07e9097be1b`. Its packager now sets `APPROVED_SITE_ULA_PREFIX = None` and strictly validates an explicitly supplied RFC 4193 /48 before writing UCI. The tests patch `fd12:3456:789a::/48` only as a **synthetic test fixture**; it is not a production allocation or approved site prefix.

Exact final-head PR run [44543625272](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625272) ran 116 packager/tool tests successfully (two intentional skips), then correctly failed `validate_all_profiles`: all 10 profiles reject the absent approved site prefix. Firmware compile jobs were skipped. This is a **fail-closed gate**, not a successful profile build or release. The mandatory sandbox [44543625389](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625389) passed 14/14 host preflight tests but failed because Bubblewrap is not installed (exit 125); sandbox packaging tests were skipped.

COE RELEASE #44 at `582fd5d5e83e36b36546ac28534740298ba94af4` generates a random 40-bit Global ID per appliance installation and persists it locally. That does not prove same-site appliances share one /48 and therefore does not satisfy §6.45. Exact compare from #35 head to #44 is 15 commits ahead / 29 behind; GitHub reports the candidate non-mergeable. Do not select, merge or reconcile #44 as the site authority. PHX-CORE and the COE integration owner must define the site-prefix authority and supply contract; PHX-RELEASE may consume only that approved input; PHX-QA must independently test same-site sharing, different-site separation and persistence/restore.


## 6.46 NVS/EEPROM commit-call evidence is not a durability witness — 2026-11-19 UTC15

Current Experiments HARDWARE PR #327 API head is c4954de95e319f7a2acf4bf4ee0bcae44b4b99b5; its current source/test head is 05ddd64f0d982c32d0297010596bfa9bd46bb472. The host lab blob 2562cdb84135b3e9dab6e531567c6b1619eeeed3 adds a one-commit call-count assertion for the ESP32 NVS backup and ESP8266 EEPROM backup. Its source mutation removes the ESP32 nvs_commit() call and must be rejected (exit 61); the premature-durability mutation remains rejected (exit 60). Focused quarantine run [44555100182](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555100182) and relay/output run [44555100184](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555100184) passed for that source/test checkpoint.

This is a control-flow/call-site regression, not proof that bytes survive power loss. The fake same-handle readback can observe pending data; a successful commit call does not independently establish media durability, atomicity across NVS/EEPROM and LittleFS, or a second anti-rollback witness. Those stores share the same physical flash. Local configuration migration V1/V2-to-V3 is not the financial-ledger v1-to-v2 migration.

Current #327 focused quarantine [44557974485](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974485) and relay/output [44557974378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974378) passed. Current Full run [44557974541](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974541) completed FAILURE at the inherited QA-owned “Missing poll signature check”; all 13 firmware/platform jobs and Android completed PASS, while downstream simulations, update bundle, signing and publishing were skipped. Both current source sketches keep acceptPollResponse() and coinPostDispositionVerified() returning false. Do not add fake signature/poll markers or enable admission to satisfy the old fixture. PHX-QA owns the fixture; PHX-HARDWARE owns firmware.

**Acceptance boundary:** a future durability claim requires an independently designed power-fail test that cuts power at each write/commit phase, cold-reboots, verifies canonical and sidecar state, journal/attempt-marker consistency and replay/rollback behavior, plus independent protected anti-rollback witness evidence. Until the required 150 real power cuts, 30-device/24-hour soak and owner-authorized independent QA are complete, keep physical and financial acceptance NOT TESTED and PRODUCTION NO-GO.

## 6.47 Build-artifact payload single-link admission — 2026-11-19 UTC16

Release provenance inventory must not admit a payload file that aliases an inode also named outside the artifact tree.

1. A payload must be a regular, non-symlink file reached through descriptor-relative parent traversal with no-follow semantics. If the platform cannot provide the required no-follow descriptor operations, admission fails closed.
2. Require st_nlink == 1 on the directory entry before open, the opened descriptor after open, and both descriptor/path identities after read or hash. Stable identity comparisons include device, inode, size, modification time, change time, and link count.
3. Reject a hard-linked payload before rewriting SHA256SUMS or creating BUILD-PROVENANCE.json. Do not mutate the external alias.
4. QA independently reviews the hard-link and path-race rejection on the exact source/test SHA; this host-side artifact rule does not establish signing, archive transfer, financial durability, or hardware acceptance.

Exact RELEASE evidence: source/test commit 90165b173179e9b36c73f98e06cfd5e0a06a3fe3; writer blob 7a85da2c6a46abed1c7585e78b72e854637fb93f; test blob 081c05b94377d4251f02e4fadeeb4d44e1fdb3d8. The test creates an external hard link and requires ProvenanceError while preserving SHA256SUMS, omitting BUILD-PROVENANCE.json, and leaving external bytes unchanged. Expected RED was recorded in run 44564359785. Exact PR docs-head run 44565010341, job 135704442410, reports 22/22 provenance tests PASS including the new hard-link test. This is CI-verified host behavior only; no release or production gate is waived.


## 6.48 Poll response remains deny-only until producer/consumer contract approval (2026-11-19 UTC17)

**Authority boundary:** The current ESP32 and ESP8266 source/test candidate #327 at `ad421e48b2908fab48dc85b40c169450d9c0239c` does not authorize coin intake from the current plain-HTTP poll response. Both sketches implement `acceptPollResponse(const String &response)` as fail-closed: ignore the unapproved response, set `insertMode=false`, clear `activeTarget`, and return `false`. Both implement `coinPostDispositionVerified(...)` as `false` until PHX-CORE publishes an approved event-bound receipt/disposition contract and PHX-QA approves its vectors. Pending journal and one-shot attempt evidence must remain; body text, root `ok:true`, or a derived `response_sig` expression is not authority to clear/credit.

**Test requirement:** QA must not require a positive literal `|poll|` marker or inject a fake signature string to make the legacy test green. Replace marker-presence assertions with source-linked negative tests that prove malformed/unsigned poll responses cannot enable insertion, assign a target, clear pending evidence, authorize coin-post disposition, credit time or energize relay output. The current inherited `v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` requires `|poll|` and causes the exact current shared build validation failure. QA owns `experiment/openwrt/BlazePwifi/tests/`; HARDWARE owns the board sketches. Any later signed poll contract must be coordinated across CORE producer, HARDWARE consumer, QA vectors and RELEASE only after exact pinned interoperability tests.

**Evidence class:** source inspection plus hosted host-lab CI only. Current #327 Quarantine run 44580223038 passed; Relay run 44580223257 was still in progress at the read; shared build run 44580223115 failed validation at the QA-owned positive poll marker assertion. This section does not claim physical hardware acceptance, a protected signer, financial durability or production authorization.


## 6.49 Destination intake evidence is scoped to its declared source root and commit — 2026-11-19 UTC18

A destination intake manifest proves only the exact source commit, tree, path root, and file classes that it declares. It must not be extrapolated to neighboring product trees.

1. COE integration PR #26 contains Pisowifi/SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f, schema version 8. It pins Experiments source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00, project root experiment/openwrt/BlazePwifi, and destination root Pisowifi/. Its recorded rootfs summary is 61/61 files recovered, 47 byte-identical, 14 locally derived, zero unrecovered rootfs files, and only two unchanged original tests. It does not declare Hardware/ as an intake root and does not establish firmware-tree or firmware-test import completeness.
2. At current Experiments main f4e8a891aed8af86d5fd315d28750a0ac3a7372b, the ESP32 sketch blob is 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0 (15,049 bytes) and ESP8266 is bfb94920eb0a189ca01d52e5443954fa133f5423 (14,583 bytes). COE #26 destination blobs are ESP32 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 (18,505 bytes) and ESP8266 c8be98f72596681e36a3ad1f8939bf8046c96887 (18,394 bytes). Neither current-main pair is byte-identical. At the manifest's historical source commit, the sketch blobs are also different from the COE destination: ESP32 29f1125d52ff474a0d028ad41f7af201be1f0f9d; ESP8266 12c4bb82b6fddafe813674a0b5f692c1d3634073. Treat Hardware files as derived candidates requiring owner/QA provenance, not exact copies.
3. The current-main experiment/openwrt/BlazePwifi/tests/ tree has 38 entries; COE #26 Pisowifi/tests/ has 19. Four basenames overlap (config.sh, integration.sh, portal.sh, security.sh); only portal.sh has the same Git blob 71b3c9622f51a80dc09a446389ba6faa001b7897. COE Hardware/tests/ contains one generic test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e. File counts or matching names are not test identity; maintain a source-SHA-to-destination-test mapping and execute it on the exact destination candidate.
4. experiment/openwrt/BlazePwifi/LICENSE and COE Pisowifi/LICENSE match at blob 1ee55b94183417be977ca287cd7391f9a6f7e721. Experiments root NOTICE.md exists at f6d92cd21465312be5993631fe26977219be0fb9; COE root NOTICE.md, Hardware/LICENSE, and Hardware/NOTICE.md are absent at the inspected #26 candidate. The Pisowifi license match does not establish Hardware licensing/notice scope; obtain owner and licensing review before any Hardware migration.
5. COE #26 exact head b382d233ff06c8791b1028bed3c617cc7b670d12 has five queued workflows and zero jobs. Until destination workflows execute on a reviewed exact candidate SHA, no destination CI or integrated acceptance is established.

No copy, move, overwrite, rebase, cherry-pick, merge, or migration staging is authorized by this contract. PHX-MASTER owns this evidence boundary; source implementations and destination files remain with their respective owners.


## 6.50 Poll-fault pulseEdges is a first-latch lower bound — 2026-11-19 UTC19

**Source-grounded interpretation; no persistence schema change.** Current Hardware #327 sketches at ESP8266 blob `284f4337bc9e2aa4d78c61f0d7e4c4163ffb0a82` and ESP32 blob `f89bc561b2093328286d7633da794667b2ab06de` define a V1 `PollFaultRecord` with `magic`, `version`, `size`, `pulseEdges`, `bootMillis`, and `checksum` (20 bytes). The first call to `latchPollPulseFault()` sets the sticky `journalRecoveryRequired` flag, inhibits outputs, and persists the supplied edge count to the secondary store and LittleFS.

In `sampleCoinPulseEdge()`, the count supplied on the first latch is `pendingPulses + unseenEdges`. Once `journalRecoveryRequired` is true, later ISR deltas are consumed by advancing `lastHandledCoinEdgeSequence` but do not call the latch again and are not added to the already-persisted V1 record. Therefore:

1. **V1 meaning:** `pulseEdges` is the first-fault snapshot, not a live cumulative counter.
2. **Reconciliation meaning:** it is a lower bound on observed edge activity over the full quarantine/recovery window; later edges may be absent. It is not an exact total.
3. **Financial boundary:** never use this field to credit time, settle/refund a coin, infer a precise denomination/count, or clear pending evidence. The sticky fault remains deny-only until separately authorized reconciliation.
4. **Completeness:** V1 has no explicit completeness flag. Consumers must treat every V1 count as potentially incomplete; absence of a flag is not evidence that no later edge occurred.
5. **Schema boundary:** do not add a field or change record layout in this task. Any future completeness flag requires a new version, dual-store migration/recovery tests, exact-head QA, and explicit HARDWARE/CORE/QA review.

**Regression gap / owner action:** the current dual-store lab `poll_fault_dual_store_lab.py` blob `7d211b5e8e47232d08d2a2c625d3212676aee7a9` does not extract/call `sampleCoinPulseEdge()`. The poll-loop lab blob `440efc0fc76e90d22283f62c6605628a6c79342e` covers a release-window edge and unobserved-edge persistence, but no explicit second-ISR-after-sticky-latch count assertion was found. PHX-HARDWARE should add a two-board host regression proving the persisted first-fault snapshot stays unchanged after later edges and admission/output remain denied; PHX-QA independently reviews it; PHX-CORE confirms the count is never treated as a financial quantity. This section resolves the interpretation for existing V1 records, not owner approval of a future schema.

Evidence is source inspection and hosted simulated labs only. No physical device, flash, financial state, record migration, or production action is authorized. **PRODUCTION NO-GO.**
