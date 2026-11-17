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


### 6.3 Poll producer/consumer compatibility is not established

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