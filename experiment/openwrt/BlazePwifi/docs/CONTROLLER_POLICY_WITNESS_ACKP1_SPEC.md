# PHX-L-CORE — controller-policy witness and coin ACKP1 contract (REVIEW DRAFT)

**Status:** DESIGN / TEST-FIRST SPECIFICATION ONLY. NOT IMPLEMENTED, NOT DEPLOYED, NOT PRODUCTION AUTHORIZED.
**Owners:** CORE backend; MASTER architecture/integration; VERIFY firmware/hardware; APPS consumer compatibility.
**Tracked:** P0 #31 (money), #32 (rental), #43 (independent rollback witness), #34 (hardware).
**Source RED:** PR #198, Full Actions #40144507985 and #40144831839; actual signed Vendo CGI accepted member_bank + coin after simulated volatile BP_RUN loss and older valid enabled controller-registry rollback. These are isolated /tmp tests, not physical reboot or flash tests.
**Review decision:** MASTER #172 comment 6392163568 authorizes the *trust-boundary direction for test-first specification only*. It does NOT approve a production witness, signer, merge or financial cutover.

## Security invariants

W1. A fresh paid operation is admitted only if a freshly authenticated, independent, nonrollbackable controller-policy witness authorizes the exact controller ID, epoch, revision, canonical policy digest, enabled/coin flags, bound target and signer identity. Any absent, stale, forked, untrusted or unreachable witness yields DENY/QUARANTINE, never a fallback to local controllers.tsv or BP_RUN.

W2. The witness is **outside** the router's registry, firmware image, runtime directory, filesystem snapshot and update rollback domain. An on-router mirrored file, CRC, ordinary HMAC with a locally extractable key, or a locally incremented counter is **not** a witness. The witness must authenticate reads and monotonic compare-and-advance, persist the result before ACK, and reject revision rewind/fork. Real service, protected key and availability policy are unselected P0 #43 dependencies.

W3. Witness response fields: protocol version, controller_id, controller_epoch, revision (uint64, no wrap), state (PENDING|COMMITTED|QUARANTINED), canonical_policy_sha256, enabled, coin_enabled, target_binding_digest, signer_key_id, operation_id, request_challenge, and authenticated statement/signature. A challenge alone does not establish monotonicity; client verifies witness identity and authenticated latest highwater through the independent trust anchor. Reject unknown versions/fields where critical, malformed lengths, stale challenges and invalid signatures.

W4. One **shared accounting/controller lock** must serialize policy transitions and fresh paid admissions. Under lock, compare the *durably verified* local row and all identity/permission fields against the latest witness COMMITTED statement. Read-only inspection never silently re-enrolls, repairs or enables a controller. Keep replay of an already durably committed immutable receipt idempotent without second money mutation; if ledger highwater/receipt cannot be independently verified, return UNKNOWN and do not clear device journal.

W5. No admin update may expose an enabled row for fresh money before an independent deny-first fence exists. Use an idempotent two-phase witness operation with the same operation_id:
  1. Under lock, read and authenticate current witness revision and controller binding; any mismatch quarantines.
  2. `PREPARE(expected_revision, new_revision, operation_id, proposed_digest)` is durably recorded by witness as **PENDING/DENY**; an uncertain prepare ACK is treated as PENDING/DENY, not success.
  3. Atomically stage/replace local policy, fsync file and parent directory; any write/sync uncertainty remains DENY.
  4. `COMMIT(operation_id, exact_digest)` durably transitions witness to COMMITTED only if prepared operation and digest match. An uncertain COMMIT ACK remains DENY until a fresh authenticated witness read proves COMMITTED and the local row matches.
  5. Release lock only after state is resolved or quarantined. A post-crash cold start repeats independent verification; it never trusts volatile state or locally visible enabled rows.
  6. Concurrent updates use monotonic CAS; conflicting operation_id/revision/digest cannot overwrite an existing decision.

W6. Operator recovery is explicitly authenticated and audited. On mismatch/fork/unknown witness history, keep controller disabled, freeze new coin admission, preserve firmware pending coin events, inspect immutable receipts and ledger highwater, then reconcile with witness authority. A new epoch/signer binding or higher witnessed revision may be authorized only after independent operator approval. Never auto-clear a PENDING fence or re-enable from a restored snapshot. If witness history is irrecoverable, **do not accept money**.

## Independent financial ledger/receipt highwater — separate from controller policy witness

**MASTER request:** #172 UTC02 comment #6392625254. Controller-policy authorization revision (W1–W6) does NOT attest that paid member balances, rental leases, immutable receipts, or event-deduplication history are current. A controller may be legitimately enabled while the money ledger is rolled back. Therefore **policy witness COMMITTED is necessary but not sufficient** for a terminal paid ACK.

L1. Maintain a **separate, protected monotonic financial authority namespace** (e.g. `finance/<authority_id>/<epoch>`), independent of the local OpenWrt filesystem/update/snapshot rollback domain. Bind ledger epoch, monotonic ledger revision, canonical aggregate state digest, immutable receipt-set commitment, last committed event identity, and signer/authority identity. A policy revision must never substitute for a ledger revision. The same physical protected witness service may implement both namespaces only with distinct authenticated records, monotonicity and failure isolation; no on-router counter or local HMAC qualifies.

L2. Use **one durable authoritative transaction** for each paid event's balance/lease effect, event uniqueness, and immutable receipt (single WAL/aggregate commit or equivalently crash-recoverable journal). Bounded UI/audit history is NOT the authoritative deduplication index. An event ID is scoped to authenticated controller+epoch+event identity and target binding, with a canonical request digest; replay with changed pulses, amount, target or binding is a conflict, not a new credit. Avoid independent member/rental commit paths that can acknowledge one side before the other.

L3. Under the same financial writer lock used for admission, verify the current policy witness **and** financial witness before any fresh paid mutation. For a new event: durable PREPARE of the financial event (no terminal ACK); atomically persist the aggregate state+receipt and fsync data and directory; then durably advance the independent financial witness with CAS on prior ledger revision and exact receipt/state commitments. Return authenticated COMMITTED only after fresh verified financial witness COMMITTED matches local durable ledger and immutable receipt. If a witness commit or its ACK is uncertain, return UNKNOWN/retain device journal and reconcile via a fresh authenticated read; **never** replay the mutation blindly. A local commit ahead of the witness is pending reconciliation, not an ACK. This ordering is a proposed protocol, not a proven distributed transaction.

L4. On cold start, ledger rollback, torn lease/receipt, missing deduplication tombstone, witness revision fork, unknown transaction status, or locally valid older snapshot, quarantine fresh financial admission. An independently protected highwater can **detect** lost local paid state but does not by itself reconstruct it. Recover only from a separately verified authoritative WAL/backup plus receipt/event proof or authenticated operator reconciliation; never silently reset the highwater, overwrite the witness with a restored snapshot, or synthesize missing credits.

L5. Receipt replay is not a new paid admission. Return ALREADY_COMMITTED for the original event only after checking immutable receipt and event/request binding against the independent financial highwater. If original receipt/highwater cannot be proven, return UNKNOWN with **zero new mutation** and retain the firmware journal, even if the local controller registry says enabled. An operator-disabled controller cannot re-credit a previously committed event; safe historical receipt lookup must not bypass the financial witness.

L6. Rental-specific torn boundary: lease replacement before receipt append, receipt before lease replacement, process exit between them, and fsync failure must never produce terminal COMMITTED unless the same durable aggregate transaction and protected financial highwater prove both lease and receipt. A delayed duplicate after a crash must reconcile to one effect or UNKNOWN; no second paid-time grant. All tests are synthetic until physical #34 acceptance.

## ACKP1 wire contract — proposed, requires MASTER/VERIFY signoff

A firmware coin event must have a stable controller-scoped event ID across retransmissions and reboot. The backend may emit a **terminal authenticated COMMITTED / ALREADY_COMMITTED** ACK only after durable authoritative receipt commit. Canonical authenticated payload binds: protocol version, controller ID+epoch, event ID+nonce, target ID+binding epoch, pulse count, credited amount/currency, immutable receipt ID+digest, ledger revision, independently witnessed highwater, result, server signing key ID, and event-request digest. Enforce strict parsing, bounded lengths, signature validation, controller/target matching, no stale signer and no replay-as-new-credit. A successful HTTP status or plaintext substring `"ok":true` is not proof.

Firmware clears its persistent pending journal entry **only after** verifying the exact event-bound authenticated terminal COMMITTED / ALREADY_COMMITTED response. On timeout, unsigned/malformed/mismatched response, uncertain durable commit, unknown revision, DENY or unavailable witness: retain pending event, inhibit further paid intake as needed, and request authenticated operator reconciliation. An authenticated DENY does not silently discard an already-inserted coin. Source/firmware protocol compatibility and eventual disposition of denied physical coins require VERIFY/Master approval; no firmware changes in this CORE specification.

## Test-first acceptance matrix (no production GREEN claim)

T1–T4: existing actual signed CGI RED cases: bank+coin after BP_RUN loss following ambiguous policy write; bank+coin after valid enabled-registry rollback after disable. With real protected witness integration these must DENY with no money/receipt mutation.

T5: cold start with witness unreachable, untrusted signature, stale challenge or unknown key -> DENY.
T6: old valid enabled local registry paired with newer witnessed disable revision -> DENY.
T7: witness PREPARE succeeded, local write failed/parent fsync failed/process exited -> persistent PENDING/DENY across restart.
T8: local write succeeded, witness COMMIT failed/ACK lost -> DENY until independent authenticated reconciliation.
T9: witness COMMIT succeeded but local registry rolled back -> digest/revision mismatch, DENY.
T10: witness revision fork, concurrent update CAS conflict, epoch/controller/target mismatch -> DENY.
T11: valid new operator-authorized enable with witnessed COMMITTED revision -> exactly one new paid event admitted, one durable receipt.
T12: replay original committed event with a new signed transport nonce after disable -> original immutable receipt only, no second credit; unknown receipt/highwater -> UNKNOWN/no mutation.
T13: forged, substring-only, truncated, wrong-event/target/pulse/amount, stale-signer or nonterminal HTTP response -> firmware pending journal NOT cleared.
T14: valid signed COMMITTED/ALREADY_COMMITTED response for the exact durable event -> pending journal may clear once; duplicate retransmission cannot re-credit.
T15: 150 real power cuts and 30-device 24h soak on owner-authorized hardware remain separate #34 gates, never inferred from mocks.
T16: controller policy witness COMMITTED but financial witness unavailable/stale/forked -> new bank/coin/rental event DENY or UNKNOWN, no mutation and no terminal ACK.
T17: local member/lease/receipt snapshot rolled back after protected ledger revision advanced -> mismatch quarantines; never credit a retransmission or acknowledge the stale snapshot.
T18: financial PREPARE durable, process dies before aggregate state+receipt commit -> no terminal ACK; recovery cannot invent credit or lose event identity.
T19: aggregate state+receipt durable, witness advance fails/ACK lost -> UNKNOWN and journal retained; authenticated witness reread either confirms one committed event or requires reconciliation, never second credit.
T20: witness COMMITTED but local paid aggregate or receipt missing/torn after restart -> DENY/UNKNOWN; independent highwater detects mismatch, does not claim to restore missing funds.
T21: same signed event replay after history truncation, controller disable, reboot, and changed transport nonce -> original verified immutable receipt only; changed target/pulses/amount/epoch -> conflict, no mutation.
T22: rental lease rename succeeds but receipt append/fsync fails (and inverse ordering) -> no terminal ACK; retry after process death produces exactly one provable lease+receipt or UNKNOWN.
T23: interleaved member transfer and rental credit with ledger CAS conflict, partial WAL, concurrent same event, and independent policy disable -> no double credit, no partial transfer/lease ACK, quarantine on ambiguity.
T24: ACKP1 terminal COMMITTED/ALREADY_COMMITTED must bind **both** current controller-policy witness and distinct financial ledger highwater+receipt; policy-only signed success, forged financial revision or stale receipt digest retains firmware pending journal.

**Review status:** L1–L6 and T16–T24 are **proposed test-first contract additions**, not implemented or passed tests. A protected financial witness and crash-atomic v2 ledger are unselected P0 #31/#32/#43 dependencies; production remains NO-GO.\n\n**Implementation order after independent review:** (a) test-only deterministic witness-fault injection and signed CGI source RED; (b) minimal backend witness adapter/deny-first fence; (c) exact-source Full CI and source/test blob verification; (d) VERIFY-owned firmware ACK tests and independently reviewed wire compatibility; (e) hardware, migration, signer and integration authorization. Until then keep PR #198 DRAFT/UNMERGED and financial admission NO-GO.
