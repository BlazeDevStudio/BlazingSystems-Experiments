# ConnectIT Protocol v1 — Foundation Contract

**Status:** Draft 2026-10-28. This document distinguishes **implemented compatibility subset** from planned v1 capabilities. No claim of a complete, interoperable v1 product.

## Architecture / versioning

- `connectit-v1-foundation` denotes the new Master authority HTTP API and database schema v1.
- `blaze-seed-v1` is the **preserved, implemented** prototype wire format for Master-issued Ed25519 JWT device certificates and relay envelopes. This name cannot be changed on the wire without invalidating existing certificates.
- `connectit-v1-discovery` is a proposed, **not implemented**, privacy-preserving directory/discovery extension.
- HTTP and JSON are versioned under `/v1/`; unsigned modifications to the signed envelope are not E2E-protected. New protocol major versions must negotiate explicitly and reject unsupported features.
- Master and satellite MUST use an out-of-band pinned Master Ed25519 public key. Downloading `/v1/public-key` without an authenticated trust comparison is insufficient.

## Master: implemented HTTP subset

All below are Master-side operations; localhost HTTP for testing; HTTPS required on non-loopback listeners. By default Master binds to `127.0.0.1:7070`.

- `GET /healthz`, `GET /v1/public-key`.
- `POST /v1/enroll` — `{ "username":"0000000001", "password":"...", "device_public_key_b64":"base64-Ed25519-public", "installation_id":"pseudonymous-install-token", "nonce":"base64url-16-plus-random-bytes", "proof_signature_b64":"base64url-Ed25519" }`. Signature over UTF8 `ConnectIT-enroll-v1\n<username>\n<nonce>`; returns `device_certificate` signed JWT, `expires_in` (7 days); only first device or previously bound *same* active key and token may enroll.
- `POST /v1/bind/start` — same fields as enrollment plus `confirmed:true`; proof string `ConnectIT-bind-start-v1\n<username>\n<nonce>`. Returns binding ID, challenge, server start and deadline; **never authorizes a device**.
- `GET /v1/bind/pending` — requires Master-signed original-device certificate and signed HTTP request proof; returns account's pending requests. UI polling only, not scheduled 20-minute notifications.
- `POST /v1/bind/decision` — trusted-device certified request + per-decision Ed25519 signature; action `approve|revoke|not_me`, `binding_id`, `approval_id`, `issued`, `interval_index`, `signature_b64`.
- `POST /v1/bind/finalize` — account credentials, target-device signed proof, countdown and approval requirement. Signature string `ConnectIT-bind-finalize-v1\n<binding_id>\n<nonce>`. Only then issues target credential.

### Signed request proof (existing Blaze Seed v0.2.0 contract)

For an already registered device, sign:

```
METHOD + "\n" + REQUEST_HOST_WITH_PORT + "\n" + REQUEST_URI + "\n" + UNIX_SECONDS + "\n" + RANDOM_BASE64URL_NONCE + "\n" + LOWERCASE_HEX_SHA256(RAW_BODY)
```

Headers:

```
Authorization: Bearer <Ed25519-master-signed-device-certificate>
X-Device-Time: <unix seconds>
X-Device-Nonce: <base64url no padding of >=16 random bytes>
X-Device-Signature: <Ed25519 signature base64url no padding>
```

Master verifies signature and active device record; its nonce replay cache is memory-local in this preview and will not survive Master restart. SQLite per-approval identifiers/interval uniqueness **do** survive restart.

### SecureBind signed decision (implemented)

UTF8 bytes, newline-delimited in this exact order:

```
ConnectIT-SecureBind-v1
<binding_id>
<approval_id>
<trusted_device_id>
<target_ed25519_public_key_base64>
<master_server_challenge>
<zero_based_20_minute_interval_number>
<issued_unix_seconds>
<action: approve|revoke|not_me>
```

- Every request starts at `started_at`, expires after 24h in this preview.
- Four-hour countdown starts at `started_at`; each unique, authenticated approval in a unique 20-minute interval deducts 30 minutes. Effective `not_before = started_at + max(0, 14400 - 1800*approvals)`.
- `approval_id` UNIQUE, `(binding_id, interval_index)` UNIQUE, and decision is verified and updated within one SQLite transaction. Revocation wins if it commits first; subsequent approval is rejected. Countdown alone NEVER completes binding.
- The trusted-device UI MUST require a locally verified PIN or biometric before signing (UI implementation pending). Master cannot verify a PIN that stays local.
- This preview's `not_me` revokes pending request and flags session records, but does not yet distribute realtime certificate revocation to satellite nodes; do not treat it as complete security-response implementation.

## Relay: implemented, carried forward from Blaze Messenger Seed v0.2.0

- `GET /healthz`, `GET /v1/info`.
- `POST /v1/messages` accepts `{ "id":"stable-random-id", "to":"recipient-10-digit-string", "kind":"message|signal", "ciphertext_b64":"already-e2e-encrypted-opaque-data", "created":<unix-seconds>, "device_signature_b64":"base64url-signature" }` under Master-issued device certificate and signed request proof. Master v1 certificates intentionally keep legacy JWT `iss=blaze-seed-v1`, `aud=blaze-relays`, with `sub` equal to ten-digit ID.
- Envelope signature covers JSON fields in exactly this order: `id`, `from`, `to`, `kind`, `ciphertext_b64`, `created`. Relay prefixes `from + ':'` to submitted message ID before validation; the signed JSON must use the fully prefixed ID.
- `GET /v1/messages?since=0&wait=0..25` returns visible envelopes; cursors are **per seed** and cannot be reused across seeds.
- `GET /internal/export?since=0` is peer-only shared-secret secured, **not externally safe** without a tightly controlled network. Ciphertext envelopes have independent client signatures. The new `hops` unsigned relay metadata is incremented at each import and cannot be forwarded after hop five among new nodes.
- Relay `message` payload defaults to 8192 decoded bytes; `signal` is a small control envelope with 3-minute delivery expiry. Sender must E2E-encrypt the payload itself; relay does not perform E2E encryption for the client.
- The implementation uses append-only JSONL and disk-backed cursor state; retention is bounded by message count. No recipient-ack guarantee, signed revocation feed or delivery quorum.

## v1 extensions: NOT YET IMPLEMENTED

- Privacy-preserving five-hop **user discovery** with explicit user consent and authorized directory rendezvous. Existing `hops` limits envelope propagation only.
- Authenticated **per-node identity federation** replacing shared mesh secret with mTLS or per-peer Ed25519 verified node credentials, node revocation, and peer authorization.
- Master-issued, signed epoch-based revocation snapshot and short-lived freshness attestations, distributed fail-closed to Seeds.
- Connection request privacy, contact opt-in, enumeration mitigation and scoped lookup rate limiting.
- A real E2E chat implementation with verified device-key directory, key continuity and forward secrecy (e.g. audited Signal-style ratchet/MLS where appropriate).
- Reliable encrypted delivery receipts, ACK quorum, peer crash-safe replay, routing priority and long offline retention.
- Real WebRTC STUN/ICE signaling adapters and authenticated direct datachannels for resumeable file transfer and audio/video calling. TURN intentionally excluded by policy.
- Android/Windows OS-specific secure key storage, protected local PIN approval and background notifications.

## Compatibility matrix

| Master | Satellite | Flutter adapter | Result |
|---|---|---|---|
| ConnectIT Master Seed 0.1.0 | ConnectIT Seed 0.1.0 | Test client using `blaze-seed-v1` | **Tested**: enrollment, signed relay, one-hop sync, Master-offline retrieval on Linux localhost |
| ConnectIT Master Seed 0.1.0 | Blaze Messenger Seed 0.2.0 | Original prototype test client | **Source-level expected**, not integration-tested: Ed25519 JWT issuer/audience and message envelope compatible for ten-digit IDs; new binding endpoints unknown to old client |
| ConnectIT Master Seed 0.1.0 | ConnectIT Seed 0.1.0 | ConnectIT Flutter Draft 0.1.0 | **Interface design only**; no executable Flutter network integration |
| No Master online | ConnectIT Seed 0.1.0 | Already enrolled compatible test client | **Tested**: valid, unexpired cert continues on reachable seed; new enrollment/binding unavailable |
| Master 0.1.0 | Seed 0.1.0 | Full five-hop discovery / WebRTC direct transfer | **Unsupported**, planned extension, NOT green |

## Security scope warning

The v0.2.0 seed protocol itself has not had an independent cryptographic audit. There is no guarantee of universal NAT traversal, instant offline revocation or message durability. Do not deploy with real personal messaging before authentication, real E2E implementation, revocation and operational review pass.
