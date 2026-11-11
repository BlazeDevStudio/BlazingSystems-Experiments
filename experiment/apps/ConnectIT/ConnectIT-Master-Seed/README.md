# ConnectIT v0.1.2 REVOCATION INTEGRATION — DEVELOPMENT / NO-GO

CLI device-revoke and signed /v1/revocations endpoint; source/testing details under docs/REVOCATION*.md. Existing v0.1.1 baseline remains below. Do not use as production service.

# ConnectIT Master Seed 0.1.0 — Functional Foundation / NOT production-ready

This standalone Go CLI + SQLite authority **was built from source and tested** on Linux x86-64. It modernizes the original Blaze Messenger Seed v0.2.0 Master boundary; signed device JWTs remain intentionally wire-compatible with that prototype's relays (`iss=blaze-seed-v1`, `aud=blaze-relays`). The existing LAN Messenger source was not modified.

**Implemented and tested:** local SQLite schema, ten-digit randomly generated IDs (strings preserve zeros), password hashing with PBKDF2-HMAC-SHA256 (310,000 iterations), Ed25519 Master signing keys and 7-day device certificates, initial admin password rotation gate, signed first-device enrollment, per-installation pseudonymous HMAC token uniqueness, new-device pending requests, trusted-device signed SecureBind approvals with single-interval deductions, replay resistance using SQLite unique keys, approval prerequisite, countdown and revocation decision, local state inspection, database integrity and SQLite online snapshot backups. Test suite includes a simulated countdown time shift; actual 4-hour wall-clock endurance has not been field-tested.

**Security warning:** installation tokens are resettable app-scoped device recognition, not spoof-proof hardware identity. A one-account-per-device anti-smurf guarantee is impossible without a trusted hardware attestation and recovery framework. SecureBind decision UI with local PIN and alerts is NOT yet integrated, and not-me currently does NOT invalidate credentials already cached on disconnected satellites. Realtime revocation, recovery codes, a WebRTC client and end-to-end ciphertext construction are NOT implemented.

## Build

Go 1.23+, C compiler + SQLite development headers/library (`libsqlite3-dev` on Linux), `CGO_ENABLED=1`. No downloaded Go third-party modules are required. Database is standard SQLite using the OS-provided `libsqlite3`, which makes cross-compiling from Linux nontrivial.

```sh
CGO_ENABLED=1 go test -v ./...
CGO_ENABLED=1 go build -trimpath -ldflags='-s -w' -o connectit-master .
```

Binary included in `bin/` is tested only on Linux x86-64; Windows/macOS/Linux ARM require the target OS C toolchain and SQLite shared library. Avoid copying the Linux binary to other platforms.

## First installation (no hardcoded production password)

The administrator username is **blaze**. Set the owner-selected temporary bootstrap password through a shell environment variable at installation. The owner-requested sample password should **not** be embedded in distributed source, configuration or binary. It cannot be used to expose remote administration; the server refuses to start until changed.

```sh
# Supply your chosen temporary bootstrap value securely in the environment.
export CONNECTIT_BOOTSTRAP_PASSWORD='<your-temporary-initial-password>'
./bin/connectit-master init --dir ./master-data
# Securely provide old and different new values.
export CONNECTIT_OLD_ADMIN_PASSWORD="$CONNECTIT_BOOTSTRAP_PASSWORD"
export CONNECTIT_NEW_ADMIN_PASSWORD='<your-new-long-admin-password>'
./bin/connectit-master admin-rotate --dir ./master-data
unset CONNECTIT_BOOTSTRAP_PASSWORD CONNECTIT_OLD_ADMIN_PASSWORD CONNECTIT_NEW_ADMIN_PASSWORD

export CONNECTIT_PASSWORD='<new-user-password-minimum-12-characters>'
./bin/connectit-master account-create --dir ./master-data --nickname "Alice"
unset CONNECTIT_PASSWORD

./bin/connectit-master check --dir ./master-data
./bin/connectit-master status --dir ./master-data
./bin/connectit-master backup --dir ./master-data --backup-to ./backups/master-snapshot.sqlite3
./bin/connectit-master start --dir ./master-data --listen 127.0.0.1:7070
```

Public listener: use `--listen 0.0.0.0:7070 --tls-cert /path/cert.pem --tls-key /path/key.pem` **only after** firewall, public IP/DNS, rate limits and TLS are validated. Prefer localhost listener behind a controlled HTTPS reverse proxy. Private key `master-data/private.key`, installation HMAC key and WAL/SQLite files must be readable only by the service account. Serve no administrative HTTP API; local CLI assumes the OS account is trusted. `start` runs in foreground; use Ctrl+C/SIGTERM or service-manager stop. `status` reports database counts, not a background process health probe.

## Main local commands

- `init`: create signing key pair, keyed device-token HMAC, SQLite schema and temporary admin record.
- `admin-rotate`: verify old password and replace it before listeners become available.
- `account-create`: allocate a random, unique 10-digit ID, set nickname and password.
- `account-disable --id 0123456789`: disable account and mark registered devices revoked in Master database. **Offline Seeds do not receive revocations yet.**
- `start`: run documented Master HTTP endpoints. `status` and `check` inspect database, `backup` uses `VACUUM INTO` and checks integrity.

See `schema.sql` and the copied protocol document for request/response details. GUI readers: DB Browser for SQLite, SQLiteStudio, DBeaver (read-only mode suggested). The server is the write authority. Back up with `backup`, not a raw copy of a live WAL file. Restore is currently **operator-supervised only with all services stopped**; no automatic restore CLI (prevent accidental overwrites). PostgreSQL migration schema is planned, not implemented.

## Verified test evidence

`go test ./...`: identity/first-device, forbidden second-device enroll, signed SecureBind approval, per-interval replay denial, countdown gating, target-key proof, double-finalization rejection, malformed signature and ID validation. CLI smoke: forced rotation, account creation, SQLite integrity and `VACUUM INTO` backup. Linux localhost integration smoke: Master-signed enrollment, signed ciphertext test envelope, two relays, 1-hop sync, Master offline message retrieval. **The smoke uses opaque test bytes, not true E2E client encryption.**

## Open release blockers

- Seed revocation feeds, identity attestation, recovery codes/device release, audited password KDF upgrade (Argon2id where supported), authenticated remote administration (if introduced), signed account privacy directory, authenticated Seed enrollment, complete SecureBind notification delivery and local PIN confirmation.
- SQLite schema migration/rollback engine and supervised offline restore, platform secure key storage, multi-OS build/CI and hardware endurance tests.
- A real Flutter/Windows integrated E2E client, full five-hop discovery, direct-only file/call ICE and load/reliability acceptance.

**This is a tested development foundation, not a complete SecureBind production service.**

## Independent ConnectIT test dummy note (v0.1.1 packaging)
A newly verified protocol-level two-account, E2E-encrypted relay regression is in the separate `ConnectIT-LAN-Messenger-Draft` archive at `test/lan_build_dummy_e2e.py`. It uses this existing v0.1.0 Master binary and requires the independent Seed package. The Master executable was NOT replaced or upgraded for this integration test. No Flutter native client login or SecureBind UI is asserted.
