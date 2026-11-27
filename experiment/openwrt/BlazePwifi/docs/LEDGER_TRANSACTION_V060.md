## TRUST-0695 — Synthetic provenance hardening and indexed TPM observations (lab-only)

The read-only `BLAZE_TRUST_CAPABILITY_V1` scanner now refuses mock invocation outside a canonical, private `/tmp/blaze-trust-*/root` fixture carrying the exact `BLAZE-TRUST-SYNTHETIC-ONLY` marker. A live `/`, `/dev`, missing or symlinked marker, symlinked fixture root, incorrect target and omitted explicit fixture flag all refuse with exit 64 and no JSON approval. Synthetic TPM nodes require regular fixture files and reject symlinked major-version paths. This does **not** make synthetic observations equivalent to physical hardware evidence; it reduces accidental false demonstrations.

TPM version information is read **only for a matching `tpmN` or `tpmrmN` device** (indices 0–7) using that exact `/sys/class/tpm/tpmN/tpm_version_major` public Linux ABI. A TPM 1.x device does not inherit TPM2 status merely because another index advertises version 2. This remains a read-only **candidate observation**, not proof of enabled/owned TPM, NV counters, boot-chain binding, witness separation or antirollback durability.

No hardware probe is remotely executed by CI. On a dedicated owner-authorized noncustomer Linux/OpenWrt device, the standalone command `sh tools/v060_trust_capability_inventory.sh TARGET` may produce a redacted JSON capability report and intentionally exits 2. No identity/serial, key, TPM command, `mmc-utils` mutation, production install, paid ACK, firmware flash or account migration occurs. *Never* interpret a successful synthetic regression test as a trustworthy, physical monotonic witness. Production blockers P0 #31/#32/#34/#43 remain open.

References (behavior/documentation only):
- [Linux stable TPM sysfs ABI](https://kernel.googlesource.com/pub/scm/linux/kernel/git/netdev/net-next.git/+/refs/tags/v7.1-rc4/Documentation/ABI/stable/sysfs-class-tpm): `tpm_version_major` denotes the implemented major specification version, not functional witness readiness.
- [Linux MMC device attributes](https://cdn.kernel.org/doc/html/latest/driver-api/mmc/mmc-dev-attrs.html): `raw_rpmb_size_mult` describes RPMB capacity; available capacity alone is not an authenticated update service.
- [Dell Wyse 5070 technical datasheet](https://www.delltechnologies.com/asset/en-us/products/thin-clients/technical-support/Wyse_5070_executive_summary_and_data_sheet.pdf): TPM 2.0 is listed as an optional security configuration. Verify each unit rather than relying on model designation.

---

## TRUST-0694 — Read-only capability discovery, not antirollback custody (lab-only)

The optional POSIX-shell diagnostic `sh tools/v060_trust_capability_inventory.sh TARGET` accepts an explicit target class (`x86_64`, `orangepi`, `ruijie`, `r281`, `generic`). It reads only whether TPM character-device nodes and the public TPM major-version sysfs entry are present, and whether an eMMC RPMB sysfs class candidate exists. It does not read serials, secrets, keys or personal data, mutate hardware, connect to networks, write paid state or alter system configuration.

Its JSON `BLAZE_TRUST_CAPABILITY_V1` reports **possible capabilities**, not a verified trust root. Even `tpm2_candidate=true` or `rpmb_candidate=true` always produces `decision=BLOCKED_UNVERIFIED_TRUST_ROOT`, `independent_witness_verified=false`, `paid_ack_authorized=false`, `financial_migration_authorized=false`, `customer_install_authorized=false` and `physical_powercut_verified=false`, exiting with status **2**. TPM 2.0 *presence* cannot prove enabled, provisioned, persistent monotonic custody or independent rollback domain. RPMB device presence similarly cannot prove authenticated counter availability or safe service operation. Device category strings are operator labels, not verified hardware identity.

Unit tests use `--fixture-root PATH` only when `BLAZE_TRUST_TEST_FIXTURE=1`, with mock files and distinct `evidence_mode=synthetic`. These tests must NEVER be used as physical acceptance evidence. The script is **not installed into an OpenWrt firmware profile** or enabled in any payment/installer flow by this change. Deploying it manually as a read-only tool requires an operator to select the actual target label; the output cannot authorize commercial use.

**Required before any finance mutation:** per-unit confirmed trust-root capabilities, independently durable witness device identity/epoch/revision, authentication, atomic staged-update and recovery semantics, disconnected-operation policy, verified rollback-domain separation, owner-approved power-cut fixtures, and multi-client soak/rollback/migration acceptance. See issue #43 and P0 issues #31, #32 and #34. The existing v2 native stale-ledger replay remains **UNFIXED**.

---

# BlazePwifi v0.6.0 — prepaid ledger transaction safety contract
Status: **DESIGN / NOT IMPLEMENTED** · 2026-10-09 (Asia/Manila) · P0 issue #31

## Why this contract exists
The current v0.5.x-style `member.sh` mutates money/time rows and then appends a
bounded event history. This cannot promise that a paid transaction is recorded
exactly once. GitHub CI [#37810302638](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/37810302638)
reproduced **duplicate prepaid credit** after an event ID aged out and a
**partial sender debit** when the process died between two transfers.

An isolated development fix at `5782937deeb1651d45204d446a9851179be9d6c3`
replaces both sides of a transfer in one rename; staged test
[#37810785263](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/37810785263)
shows that particular interruption boundary passing. It is NOT sufficient
for reboot-safe event receipt or durability: `member-events.tsv` remains
a separate, fallible write. Staged CI
[#37811179871](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/37811179871)
also reproduced a failed receipt write followed by a successful credit response.

## Mandatory invariants (apply to all financial operations)
1. A validated, authenticated operation either makes **both** the balance
   effect and a durable receipt visible on recovery, or makes neither visible.
   No acknowledgment before a durable commit.
2. A retry of an accepted transaction must never reapply its financial delta.
   Reusing the ID/sequence with changed amount, member, destination, or
   controller is rejected. A previously committed operation may return its
   original result and signature.
3. Transfer preserves the total across both accounts, including crash and
   disk-full boundaries. Debit and credit are one logical operation.
4. Concurrent events are serialized through a tested lock. Readers never see
   a partially applied financial transition. Stale state revisions are
   rejected, not silently overwritten by a backup or second process.
5. Every accepted paid event is either durably committed or explicitly
   rejected; no over-credit or lost seconds under an uncertain ACK.
6. Corrupt or insufficient storage goes **read-only/fail-closed for paid
   mutations**, with operator recovery instructions; never default a corrupt
   money balance to zero or silently truncate authoritative journal records.
7. A bounded device must not silently forget IDs that it can subsequently
   accept as new. Arbitrarily old random IDs and finite replay storage
   cannot simultaneously guarantee indefinitely remembered receipts.

## Proposed v2 transaction structure — not a production API
- **Server authoritative:** a versioned write-ahead transaction journal is
  the source of truth. Each record carries a protocol version, strict
  controller identity, authenticated monotonic sequence, immutable event ID,
  source/destination members, signed delta, previous revision, after-state or
  deterministic update, result/ACK digest and integrity framing.
- **Atomic commit:** write one complete financial operation **and its receipt**
  as a single journal transaction with integrity framing; durably flush the
  record and metadata before returning ACK. Materialize `members.tsv` as a
  verified read model *after* commit, reconstructable on boot. Do not
  treat independently updated `member-events.tsv` as authoritative.
- **Crash scanning:** accept only complete valid committed records in order;
  truncate/quarantine a verifiably incomplete unacknowledged tail using a
  tested procedure; never discard an already acknowledged record. Verify
  snapshot epoch, checksum, previous journal hash/revision and write ordering.
- **Bounded storage:** use bounded retained journal segments + checkpoints;
  persist a **per-controller high-water mark and bounded replay window**.
  IDs/sequences older than the admissible window must be rejected as stale,
  *never* accepted as new. A still-outstanding ambiguous operation must keep
  the controller paused/frozen until reconciled rather than issuing a new ID.
  Before reclaiming segments, prove that checkpoints retain all balances,
  controller floors, sequence-window receipt data and recovery metadata.
  On quota exhaustion reject new paid events safely; **never** evict an
  admissible receipt to create space.
- **Protocol compatibility:** current SoftTimer v0.4.x uses random persisted
  event IDs, so simply adding a sequence check on the server would break
  legitimate clients. Introduce negotiated v2 protocol and durable
  controller sequence/ACK journal, with an explicit v1 quiescence/migration
  plan. Binding and source/controller mismatch checks remain mandatory.
- **Other callers:** admin set/add/transfer/restore must have stable idempotency
  keys and the same ledger transaction mechanism. Rental lease/coin changes
  in `rental.sh` and `common.sh` need an equivalent P0 assessment; fixing
  members alone does not certify the other money stores.

## Implementation acceptance, in strict order
1. Prove failing old-code fixtures: trimmed ID replay, interrupted transfer,
   receipt EIO, event-ID collision across users/controllers, concurrent writes,
   out-of-order ACK, old/stale sequence, storage full, corrupt/incomplete tail.
2. Prototype journal off-device with fictional balances and deterministic
   crash injection **before/after** intent, commit flush, materialized view,
   ACK, compaction and restart; assert exact once, total conservation, no
   lost-ACK re-credit. A green mock test is only engineering evidence.
3. Determine target-specific durable write mechanism. Today
   `bp_durable_sync` can be **disabled** via `durable_sync` config;
   this is inadequate for a guaranteed prepaid ACK. Verify write/fsync and
   parent-directory durability on target OpenWrt/ImmortalWrt filesystems.
   Do not assume `mv` alone guarantees power-loss persistence.
4. Version, migrate and verify old member/event/controller/rental state
   under an offline, transaction-quiesced signed migration. Previously
   evicted v0.5 receipts **cannot be reconstructed** from a truncated
   history: do not silently certify historic exactly-once semantics.
5. Expand required CI on the exact source SHA, including SoftTimer reconnect,
   Windows installer, firmware/ESP, Android, x86/Ruijie/Orange Pi, admin API,
   portable profile safety, and 30-device accounting soak. Add real power-cut
   testing on supported flash/storage before unblocking shipping.
6. Encrypted private backup must cover journal, controller sequence floors,
   retained receipts, balances, signer identity and migration epoch. Restore
   must fail closed if newer paid transactions occurred after snapshot.
   Exercise signed release/rescue/rollback using the unchanged Lineage-2 signer.

## Explicit prohibition
Do not advertise this document, the staging test, or the one-rename transfer
patch as complete journal support or production-quality money safety.
No live database migration, firmware flash, real customer files, production
release, signer/key rotation, or default-account changes are authorized.
Existing v0.6-family update preflight must remain blocked.

## Next concrete source step
Build a new isolated, source-controlled v2 journal **fixture prototype**
and fault-injection test harness, with exact acceptance vectors above.
Only integrate it behind a disabled-by-default migration guard after the
prototype passes and actual v1 controller compatibility has been analyzed.
Do not patch only the rolling `member-events.tsv` cache and assume the
P0 problem is solved.

## ROLLBACK-0691 — valid older snapshot loses ACKed member + rental credits (EXPECTED UNSAFE / OPEN)

Source-controlled, off-device, LAB-ONLY reproduction: `tests/v060_v2_snapshot_rollback_repro.sh` compiles the `-DBLAZE_FIXTURE_ONLY` authenticated v2 journal. It acknowledges a fictional member credit, snapshots `ledger.tsv`, then acknowledges another member credit plus a rental lease from another private fixture controller. A manual restore of the first **checksum-valid** snapshot erases the two later paid operations **and their receipt/controller sequence high-water state**. Retrying the identical signed operations now produces **new `COMMIT`** responses rather than `REPLAY`. The earlier known source paths have no independent freshness attestation; the snapshot's SHA-256 proves integrity of its bytes, not that it is the latest paid state. Full GitHub Actions [#37990879058](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/37990879058) at source head `b4ca34ad8dd30fafcd0e888b629152ed02cee1f6` completed **26 success, 4 production skips, 0 failures**. Its specifically named `ROLLBACK-0691 EXPECTED UNSAFE` step **passed because the flaw was reproduced**, not because it was fixed.

Before a v2 state restore or migration can ever take payment, require all of these independently verified conditions:

1. Capture a **trusted anti-rollback epoch / per-controller committed sequence floor** that cannot be silently replaced along with `ledger.tsv`. Define its custody and durability boundary; a second unprotected file in the same snapshot or directory is not independent authority. Authenticate any off-device witness, including scope to exact appliance and controller generation. Offline/absent witness must block reactivation rather than silently trust an old checksum-valid snapshot.
2. Freeze and drain **all** coin, member, rental, Windows and admin paid-state writers before snapshot/migration. Record unresolved ACK outcomes and treat them as UNKNOWN, not new receipts. Independently validate every last-ACKed high-water floor against the restored snapshot.
3. **Fail closed** when presented with a stale but internally valid snapshot: never mint missing paid time, rewrite the trusted sequence floor downward, auto-replay unacknowledged transactions as if new, or overwrite newer prepaid state. Require private owner-authorized reconciliation with controller receipts and device leases.
4. Extend synthetic fault-injection for: restore-to-older epoch; missing/corrupt witness; conflicting controller floors; interrupted two-phase witness update; acknowledged payment between backup and attempted restore; lost ACK before witness persistence; backup from another device; source-version mismatch; retention/compaction; concurrent write during snapshot. A new independent witness scheme must prove no false ACK and no accepted rollback under these cases **before** its guard could be enabled on any real device.
5. Prove on isolated disposable physical storage with real independent power-control telemetry, signed current+rescue Android enrollment, original signer continuity, and 30+ real client/24-hour acceptance before any 0.6 release. An unverified synthetic result is never physical acceptance.

**Status: OPEN P0, NO PRODUCTION v0.6.0; migration/update preflight denial remains intact.** This reproduction involves deliberate manual file replacement inside a 0700 fake `/tmp` lab and does not establish a remote compromise or actual customer event. Linked trackers: member [#31](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/31), rental [#32](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/32), hardware [#34](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/34).

## WITNESS-0692 — hypothetical independent freshness witness (IN-MEMORY MODEL, NOT DEPLOYED)

The self-contained `tests/v060_trusted_witness_model.py` is an **off-device security-model fixture** for designing a future mitigation to ROLLBACK-0691. It does **not** modify BlazePwifi's current installed `member.sh`/`rental.sh` paths, the native `-DBLAZE_FIXTURE_ONLY` C ledger, APK, ESP firmware, OpenWrt startup or any release channel. It uses fictional member and rental balances, mock HMAC envelopes, and Python memory only (no filesystem/network). A green test confirms an abstract policy's behavior under its *assumed* trusted witness; it is **not** evidence that such a witness exists or is operationally durable on any device.

The model states the trusted side stores an authenticated manifest of **device identity + migration epoch + monotonically increasing revision + canonical ledger snapshot digest + all controller sequence floors** outside the rollback domain of the ledger backup. Before *any paid mutation or replay*, the authority must fetch and authenticate the witness and require an exact snapshot match. Offline, absent, corrupt, foreign-epoch, stale or partially committed state must **reject** all paid operations. The protocol never silently chooses the highest checksum or resets the witness to match an old file.

**Modeled transition / crash outcomes:**

| Cut / input | Required modeled result | Owner recovery |
| --- | --- | --- |
| Before ledger snapshot replacement | No ACK, no paid change; same signed operation can commit when witness still matches | Normal exact retry |
| Ledger newer than witness after an interrupted update | No ACK; all subsequent member and rental writes blocked | Quarantine / reconcile under independent trust |
| Witness newer than ledger | Reject paid writes and replay; never rewind witness | Quarantine / reconcile |
| Ledger and witness updated, ACK lost | Same signed transaction returns `REPLAY` with original result, without a new credit | Exact retry |
| Older internally valid ledger restored after acknowledged credit | Refuse new payment and even a previously accepted replay; old receipts/floors cannot be trusted | Owner-controlled reconciliation |
| Missing, offline, corrupted or mismatched trust record | Deny all paid writes rather than fall back to unverified local state | Restore authenticated independent authority |
| Altered controller payload or stale/out-of-order sequence | Reject without ledger mutation | Validate original signed event |
| Multiple controllers and member/rental writes | Require one shared ledger state and independent sequence floors; conserve transfers | Validate all last-ACKed devices |

**Important limitation:** Two logically separate state stores do not automatically have an atomic cross-device commit or a valid recovery algorithm. A witness first/ledger second or ledger first/witness second write can produce divergence during power loss, requiring paid-state quarantine. The model's HMAC and Python in-memory witness are illustrative, not a hardware secure element, attested remote authority, durable monotonic counter, or original production Android signer. Do not implement this by copying the witness into `/etc`, another file on the same router, the same firmware backup, or any rollback-controlled partition. A genuinely independent witness needs authenticated device binding, administrative custody, durable monotonicity, availability policy, disaster-recovery and offline fail-closed behavior. If both ledger **and** witness can be restored together, this model provides **no rollback resistance**.

**Outstanding P0 acceptance:** specify and implement an independently operated trusted authority; prove crash-consistent commit/ACK ordering and safe reconciliation across it; benchmark real BusyBox/OpenWrt fsync and flash/SSD behavior, controller disconnected/partition scenarios, malicious or accidentally stale backup replays, backup/restore epochs, time-based rental expiry, multi-device financial reconciliation, 30-device endurance, signed rescue rollback and migration owner approval. None of these are implemented or certified by WITNESS-0692. Keep P0 #31/#32/#34 OPEN and the v0.6.0 preflight blocked.

## WITNESS-0693 — two-stage independently witnessed commit and manual reconciliation (LAB ONLY)

This is a **design simulation**, not a deployed solution. `tests/v060_witness_two_stage_recovery.py` reuses the fictional signed-transaction oracle from `tests/v060_trusted_witness_model.py`. It assumes a trustworthy **out-of-rollback-domain** witness with authenticated state and **quiesced, single-writer** access; neither requirement is implemented or confirmed on the supported OpenWrt hardware. It contains no filesystem/network calls, no durable synced writes, no real signer and no installed payment code. The independent witness assumed here is an idealized Python object.

The proposed sequence is **verify current witness+ledger → witness PREPARE(old+new digests and signed envelope fingerprint) → replace ledger with proposed balance+receipt/floor snapshot → witness FINALIZE → return COMMIT ACK**. A duplicate signed event after both sides agree returns only its original `REPLAY` result; a receipt collision, missing/invalid signature, unknown state or mismatched epoch is refused. NO ACK is emitted at any interruption boundary before finalization. After interruption, an owner-controlled, writer-quiesced recovery may **abort** a pending preparation only if the ledger *exactly* matches the trusted old digest, or **finalize** it only if the ledger *exactly* matches the prepared new digest; any third digest, absent/offline/altered witness or unquiesced recovery must **quarantine**. A finalized witness paired with an older checksum-valid ledger must never be automatically downgraded.

**Exact model fault vectors:** before prepare; witness prepared but ledger old; ledger advanced with witness pending; witness finalized but response lost; member+rental writes from separate controllers while pending; stale valid restore after ACK; unknown/corrupted proposed state; offline/missing/altered witness; wrong epoch; old receipt replay, changed payload collision and prepaid transfer conservation. The fixture also intentionally confirms the **expected UNSAFE** case: if the witness is stored in the same backup/rollback domain as the ledger, rolling back both restores old floors and an already ACKed event is accepted as NEW COMMIT. A model that includes this unsafe test has **not** built a real anti-rollback defense.

**Prohibitions before any production use:** Do not equate Python objects, HMAC mocks or logical checkpoints with real monotonic/tamper-proof storage, physical fsync, remote witness availability, trust enrollment, durable two-system consensus or a verifiable power-cut test. Two stores do not magically commit atomically. Any attempt at real implementation must document the independent witness owner/custodian, device identity, controller generation, durable monotonic counter or attested append-only authority, API authentication/replay defenses, power-failure recovery, offline/partition behavior, disaster recovery and exact ACK boundary. OpenWrt/ESP hardware without truly trustworthy monotonic custody must remain **fail-closed** on restore, not silently issue credits. Real frozen-writer migration, source-to-target receipt reconciliation, signed Android rescue continuity, 30-device endurance and independent physical cutoff remain P0. Issues #31/#32/#34 and the live v0.6 release block remain OPEN.
