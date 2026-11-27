# WITNESS-0738: off-device durable witness candidate — NOT production admission

**Status:** development candidate only, 2026-10-13, P0 #43 / #31 / #32.
**Source:** `tools/v060_offdevice_witness_candidate.py`.
**Regression:** `tests/v060_offdevice_witness_candidate.sh`.
**Customer paid ACK / v0.6.0 release:** **FORBIDDEN**.

## What is real and what is not

This is a real local SQLite WAL/`synchronous=FULL` transaction store, not a
Python dictionary pretending to be persistent. It retains authenticated
per-device epoch, revision, digest, a single pending compare-and-advance
operation, and idempotent finalized receipts across individual process
restarts and injected crashes.

It is **not a verified independent monotonic witness**. Replacing/restoring
the candidate's *entire* SQLite database to an earlier snapshot also resets
its high-water mark. A separate host helps isolate some failures but does NOT
on its own establish physical nonrollbackability. The test intentionally
restores an older database and verifies that the tool still never issues a
payment admission. An authenticated `finalize` only means that a caller
*claimed* its local ledger was durable; the candidate has no direct proof
of router/device fsync.

There is no remote network daemon, TLS listener, enrollment, secret generator,
encrypted backup, P-256 signer, signed ACKP1 producer, v1→v2 importer,
customer state file, installed OpenWrt binary or release tag. The executable
**does not run on a router by default**. Do not connect it to paid CGI or
initialize it using existing customer balances.

## Candidate-only invocation contract

An operator on a **separate disposable, noncustomer host** must independently
provision a directory, owned by the invoking user with mode `0700`, and two
regular owner-only mode `0600` files:

* `.witness-candidate-only` with the **exact single-line marker**
  `BLAZE-WITNESS-CANDIDATE-NOT-HARDWARE-ATTESTED`.
* `secret.hex` with exactly 64 lowercase hex digits (operator's
  nonproduction random 32-byte HMAC key) followed by LF. Neither the key nor
  a real device ID should be committed or logged in GitHub.

Execute with Python 3, for example:

```text
python3 tools/v060_offdevice_witness_candidate.py ROOT init DEVICE EPOCH REV DIGEST HMAC
python3 tools/v060_offdevice_witness_candidate.py ROOT prepare DEVICE EPOCH OLDREV OLDDIGEST NEWREV NEWDIGEST NONCE HMAC
python3 tools/v060_offdevice_witness_candidate.py ROOT finalize DEVICE EPOCH NEWREV NEWDIGEST NONCE HMAC
python3 tools/v060_offdevice_witness_candidate.py ROOT status DEVICE CHALLENGE_NONCE HMAC
```

The `HMAC` is lowercase hex HMAC-SHA256 over the literal
`BLAZE-WITNESS-CANDIDATE/1` then tabs separating `COMMAND` and **all
positional args excluding the HMAC**, terminated by LF. It binds the entire
request. Each device/epoch/revision must be canonical. Digest = lowercase
64-hex SHA256 of the ledger snapshot (not a supplied plaintext balance);
nonce = lowercase 32–64 hex characters; caller must ensure freshness and
replay-safe custody. There is **no socket API** and no internal HMAC/key
generation. HMAC here authenticates a test command; it is not an attested
hardware signer or an independent signed controller ACK.

Operations are serialized by SQLite transactions:

1. `init` creates a single operator-approved genesis. It refuses resetting
   an existing device and therefore cannot perform migration rollback.
2. `prepare` compares exact committed old revision/digest, requires
   `newrev=oldrev+1`, then persists a single pending tuple. Other or
   conflicting pending work is denied. Even a successful PREPARE returns
   `paid_ack_authorized=false`.
3. Only matching `finalize` advances the committed candidate floor and
   durably stores a finalized tuple. Replayed finalize returns an idempotent
   **NO-ACK** status. The candidate cannot itself verify the target's
   atomic paid ledger or the physical durability of its fsync.
4. `status` is authenticated and exposes committed floor plus pending
   reconciliation status. A pending transaction does not auto-clear on
   timeout or after reboot. Recovery requires comparison against an
   independently verified real target state (currently unavailable).

### WITNESS-0739: challenge-authenticated candidate STATUS

The `status` request was already protected by a request HMAC, but its JSON reply
had no integrity protection. A requester checking an untrusted relay MUST
verify the newly returned `response_challenge` equals its unpredictable
fresh 32–64-character lowercase hex request nonce and independently verify
`response_mac`. Verify over a sorted-key, compact JSON serialization
of the complete reply **with `response_mac` removed**, encoded in UTF-8,
using HMAC-SHA256 with the existing operator-provisioned candidate secret:

```text
HMAC_SHA256(key, b"BLAZE-WITNESS-CANDIDATE-STATUS/1\\n" +
            canonical_reply_without_response_mac + b"\\n")
```

The MAC binds revision, epoch, digest, pending status, nonce and **all
authorization-false flags**. The test rejects changed floor, pending or paid
authorization, altered digest, and replay of a captured reply under a different
challenge. A response using an old/reused nonce is not fresh; callers
must generate and independently track unique challenges.

**This is NOT a hardware-backed signature or antirollback counter.** An
attacker with the shared key, a restored SQLite/key snapshot, or a compromised
candidate host may still forge plausible past state. There remains no
network transport or secure production key custody. Client admission continues
to require independent physical monotonicity and hardware acceptance.
All candidate replies remain non-authoritative for payments. The original
`STATUS/1` response MAC contract remains compatible after WITNESS-0740;
the complete new response fields are covered by that existing MAC.

### WITNESS-0740: challenge-bound signed transaction replies and pending tuple

The original authenticated `status` response (`response_challenge` and
`response_mac` using `BLAZE-WITNESS-CANDIDATE-STATUS/1`) is **preserved**.
Every successful `init`, `prepare`, `finalize` and idempotent-replay
result now also has a `response_mac` over the entire reply using the
separate `BLAZE-WITNESS-CANDIDATE-TRANSACTION-REPLY/1` domain:

```text
request_sha256 = lowercase_hex_SHA256(exact_original_canonical_request)
payload = sorted_key_compact_json(reply_with_response_mac_removed)
response_mac = HMAC_SHA256(operator_secret,
    ASCII("BLAZE-WITNESS-CANDIDATE-TRANSACTION-REPLY/1") + TAB +
    ASCII(request_sha256) + TAB + UTF8(payload) + LF)
```

All replies include `request_sha256` and `reply_schema`, which is
`BLAZE-WITNESS-CANDIDATE-STATUS/1` for status or the transaction reply
domain for other commands. A consumer MUST recompute `request_sha256`
from the exact command/device/epoch/digest/nonce it actually sent; validate
the domain and constant-time compare `response_mac` over all remaining
fields. A fresh caller-generated `status` challenge is essential.
Replies also include authenticated `pending_revision`, `pending_digest`
and `pending_nonce` (JSON null if no pending transaction), allowing
operator-side reconciliation of the exact disputed staging tuple.

`tests/v060_offdevice_witness_reply_auth.py` independently recomputes both
versioned reply formats and rejects tampered floors, changed pending
digests, replayed old status under a fresh challenge, cross-device/command
substitutions, wrong keys and any forged `paid_ack_authorized=true`.
Existing WITNESS-0739 status tests must continue passing unchanged.

These are **HMAC-protected candidate responses**, not a hardware-backed
antirollback witness, trusted network transport, verified target fsync,
protected P-256 signature, or customer ACKP1. Restoring SQLite + the
operator key together still rewinds the candidate; no true paid admission
or customer migration is allowed.

Every successful response explicitly includes
`independent_monotonic_witness_verified=false`,
`financial_migration_authorized=false`, `paid_ack_authorized=false`,
and `customer_install_authorized=false`. Failed commands return nonzero
and never print a positive response.

Only marker-validated `/tmp/blaze-witness0738-*/` fixture roots can trigger
intentional `BLAZE_WITNESS0738_TEST_FAULT` process exits. Real operator
paths never enable that switch. The tests use ephemeral generated fixture
inputs and never access router partitions, TPM, RPMB, USB coin hardware or
production secrets.

## Missing independent hardware admission (strict P0)

Before any real paid ACK or migration:

1. Establish **operator-approved physically isolated hardware** with a
   monotonic state primitive whose counter cannot be restored with ordinary
   SQLite/media snapshots, and prove the actual device's measured support.
   If none exists on a target, paid operations must remain unavailable.
2. Provision pinned device and witness identities with audited key custody,
   mutual authenticated transport, authenticated counter challenge/freshness,
   controller sequence floors and protection against server/storage rollback.
3. Bind `PREPARE` and `FINALIZE` to the *actual* target journal fsync
   contract and proven target-durable signature. Demonstrate recoveries when
   witness is ahead, ledger is ahead, ACK is lost, or communications fail.
   Default = refuse all paid mutation and paid replay ACK until reconciled.
4. Prove 150 isolated physical abrupt power cut cases across supported
   targets/transaction stages, 30+ real client 24-hour soak, signed Android
   current/rescue and Device Owner provisioning, and reversible owner-approved
   encrypted v1→v2 migration without old-writer fallback.

The existing native journal is still fixture-gated; this candidate does not
give it a public runtime route. **Do not treat a green CI result, WAL fsync,
or a signed demonstration statement as physical acceptance.**

**Release locks:** `VERSION=0.5.3`,
`CUSTOMER_INSTALL_AUTHORIZED=0`,
`PRODUCTION_v0.6.0_RELEASED=0`. P0 #31/#32/#34/#43 remain OPEN.
