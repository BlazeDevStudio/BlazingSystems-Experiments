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

Therefore the focused relay/output result [44320124000](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320124000) is PASS only for the existing relay-output lab. It is NOT boot-polarity regression evidence. Quarantine/readback [44320123810](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320123810) passed independently. Full build [44320123851](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320123851) was still in progress at the last read; its validation job had already failed at the QA-owned Controller protocol parity assertion. ESP8266 target compilation passed; remaining target jobs were not all terminal at that read.

**Required owner actions:** PHX-HARDWARE must first commit the actual versioned local polarity record, fail-closed V1/V2 migration, boot-time read/validation before any output configuration, and strict local setup AP 0/1 selection. Correct the workflow using a block scalar (run: |) with separate commands or a separate step, then verify the log shows the boot lab itself executing and its negative mutations being rejected. PHX-QA must independently test cold boot with default, missing, corrupt, active-high and active-low values, including the first GPIO level before OUTPUT mode, at the same exact source SHA. Do not read polarity from unauthenticated remote configuration. Physical relay voltage/reset-state acceptance remains NOT TESTED.

This section supersedes the earlier UTC13 statement that the local-polarity implementation was in progress as if the current source already contained it. The owner plan is real; the current source implementation is not yet present. Keep the candidate DRAFT, keep financial/coin admission NO-GO, and do not migrate this firmware into COE.
