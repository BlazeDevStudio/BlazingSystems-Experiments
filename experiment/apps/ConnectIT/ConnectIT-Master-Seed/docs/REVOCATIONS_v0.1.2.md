# ConnectIT Master Revocations v0.1.2 — development-only

Implemented: `GET /v1/revocations` signs the canonical JSON payload using the Master Ed25519 private key, with domain separation `ConnectIT-revocations-v1\n`. The response contains only SHA256 fingerprints of revoked device Ed25519 public keys; it does not include account IDs or raw public keys. Snapshot generation is a monotonically increasing SQLite meta value on `device-revoke` and `account-disable`. Validity is 1 hour. All returned hashes are sorted, with hard cap 50,000.

Local, privileged CLI: `connectit-master device-revoke --dir ./master-data --device-id THE_DATABASE_DEVICE_ID`. Do NOT revoke via unauthenticated HTTP. This CLI calls an SQLite transaction, marks device revoked, writes audit revocation row, and bumps generation. Account disable also bumps generation and changes all account device states.

Snapshots are public signed data. Operators must provision the correct pinned Master public key to every Seed, and HTTPS certificates when accessible remotely. First-match token issuance and HWID policy do not become production-certified by this mechanism.

**Security caveat**: A Seed that still holds an older unexpired snapshot may accept a newly revoked device until its next successful refresh (every 60 seconds by default). If it cannot refresh, a valid cached snapshot is accepted until `valid_until`, at most one hour after generation; afterwards it fails closed. There is no push revocation or global immediate propagation. The current database and snapshot are not backed by a tamper-resistant monotonic hardware clock or ledger. Deleted/misconfigured revocation files must never cause silent fallback to long-lived trust on production nodes.

**Tests**: `go test ./...`, `go vet ./...`, live `python tests/revocation_smoke.py`, legacy `python tests/integration_smoke.py`. The live smoke intentionally forces a Seed restart to fetch the updated signed view immediately. Actual background polling on physical hosts is not yet field-tested.
