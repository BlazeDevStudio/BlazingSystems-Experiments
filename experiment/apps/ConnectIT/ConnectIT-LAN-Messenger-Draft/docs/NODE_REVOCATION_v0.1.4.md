# ConnectIT v0.1.4 — Node-key revocation and same-key certificate renewal

**Development only. NOT public-network / production-ready.** This update stacks on v0.1.3 signed federation, which stacks on v0.1.2 signed device revocations.

## Authority and state

- Master local administrator may call `node-revoke --node-cert /path/exact-node.cert.json`. The certificate must be validly signed by this exact Master, but may already have expired. A revoked Ed25519 **public signing key** can never be re-authorized. The command is idempotent for the same key, records an audit entry, and atomically increments `node_revocation_generation` in SQLite.
- Master `GET /v1/node-revocations` signs `connectit-node-revocations-v1` JSON: sorted SHA-256 node-signing-key fingerprints, generation and maximum 1-hour validity. This is separate from device revocations, whose wire format remains unchanged.
- Existing v0.1.3 node certificates are revocable by supplying their original signed JSON file, even if Master has no historical issuance record. New issuances are recorded in `node_cert_issues`; v0.1.4 creates the new tables on demand for existing v0.1.3 databases. Back up the live database using the CLI `backup` command first.
- A signing key cannot be reused for a different node ID, and an already-revoked key cannot get a new certificate. A legitimate existing-key renewal keeps the same node ID and private key.

## Satellite enforcement

- A signed-mode Seed must obtain a valid, Master-signed node-revocation view at startup (or an unexpired signed cached view if Master is offline). Signed incoming requests, outgoing requests, and signed peer responses check the node public signing key against this view. Missing/expired view fails closed.
- The Seed polls the Master every 30 seconds. Revocations are **not instantly propagated**; network outages can prevent refresh until the signed snapshot expires (up to one hour).
- Each signed operation rereads the local certificate from `node.cert.json`; an owner can renew by placing a **valid same-key certificate** into the path using an atomic same-directory rename. There is no restart required for this exact same-key renewal, but there is NO automated renewal agent. Preserve file permissions 0600. Do not edit JSON in place.
- A compromised key requires a **new keypair** and an owner-supervised Seed re-provisioning/migration process. Hot-swapping the private key is deliberately unsupported and must not reuse the compromised key. Never copy a revoked key onto a replacement node.

## Local commands

```sh
# Issuance after the Master admin has rotated the bootstrap password:
connectit-master node-authorize --dir ./master-data \
  --node-id seed-a --node-public-key ./seed-a/node.public.key \
  --node-cert-out ./seed-a/node.next.cert.json --node-ttl-hours 24

# Install the verified same-key renewal atomically (same directory/file system):
chmod 600 ./seed-a/node.next.cert.json
mv -f ./seed-a/node.next.cert.json ./seed-a/node.cert.json

# Emergency kill switch, using any authentic old/current certificate:
connectit-master node-revoke --dir ./master-data --node-cert ./compromised.cert.json
```

**Do NOT overwrite an existing certificate with the issue command.** Write a new path and deliberately install it. `node-revoke` is local administrator authority only; there is no public remote-admin API.

## Verification

- Both Go suites and `go vet` pass, with dedicated negative tests for invalid issuer, tampered view, stale/rollback, cache reload, revoked sender, local revoked signing, wrong identity and hot-swap tamper.
- Live localhost smoke: Master+two Seeds, signed HTTP 200 before revocation, 403 after the receiver obtains a new signed revocation snapshot, still 403 after Master shutdown; retained cached snapshot file.
- v0.1.3 independent 201-message federated replication and Master-offline retrieval regression must continue to pass.
- No public TLS/load/OEM validation, no trusted hardware key sealing, no automated node credential recovery, and no full Flutter ConnectIT account/UI test. **Production remains NO-GO**.

## Known security and operational limitations

- Cache and rollback resistance across *running-process refresh* is implemented; tamper-proof monotonic rollback detection against an attacker able to restore the entire local disk to an older valid snapshot is NOT achieved. Requires protected monotonic counter/remote witness.
- 30-second polling is not push revocation. Stronger immediate cutoff needs an authenticated push or short-lived noncacheable revocation status. Snapshot maximum 1 hour.
- A satellite already connected may briefly accept requests before receiving a newly signed snapshot. Do not claim immediate globally consistent revocation.
- Node identity rotation while preserving stored envelopes is a supervised deployment task; automatic replacement is not implemented.
