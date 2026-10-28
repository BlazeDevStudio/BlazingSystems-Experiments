# ConnectIT v0.1.3: Master-authorized Seed federation (development only)

A Seed now uses its existing local Ed25519 node private key to authenticate `/internal/export` requests. The Master **offline privileged CLI** issues a 1–168-hour signed authorization certificate scoped to a distinct `node_id`. The Master private signing key never leaves the Master server; no shared mesh password is needed in signed mode.

## Installation / two Seed example

1. Initialize and **rotate** the Master administrator password as in the Master README.
2. Initialize each Seed (same trust anchor; different node keys), and supply the explicit expected peer IDs in the same order as `--peers`:

```sh
connectit-seed init --dir /srv/connectit/a --node-id seed-a \
  --master-public-key /secure/master/public.key \
  --listen 127.0.0.1:8081 --peers http://127.0.0.1:8082 --peer-ids seed-b \
  --revocations-url http://127.0.0.1:7070/v1/revocations
connectit-seed init --dir /srv/connectit/b --node-id seed-b \
  --master-public-key /secure/master/public.key \
  --listen 127.0.0.1:8082 --peers http://127.0.0.1:8081 --peer-ids seed-a \
  --revocations-url http://127.0.0.1:7070/v1/revocations
```

3. Issue certificates on the **Master host** after the admin rotation, having transferred the Seed public key through an authenticated channel and checked that it actually belongs to the intended Seed:

```sh
connectit-master node-authorize --dir /srv/connectit/master --node-id seed-a \
  --node-public-key /staging/seed-a-node.public.key \
  --node-cert-out /staging/seed-a-node.cert.json --node-ttl-hours 24
connectit-master node-authorize --dir /srv/connectit/master --node-id seed-b \
  --node-public-key /staging/seed-b-node.public.key \
  --node-cert-out /staging/seed-b-node.cert.json --node-ttl-hours 24
```

4. Deliver each `node.cert.json` to its owning Seed's configured `node_cert` path, mode 0600. Protect `node.private.key` (0600); never put private keys in GitHub or public bundles. Run Master first to refresh signed device revocations; start Seeds. Signed mode auto-activates when the cert file is present. Ensure `peer_ids` is configured, and use verified HTTPS certificates with DNS hostnames on non-loopback links. Certificate renewal requires deliberate operator action **before** expiry; stop the Seed to replace the cert, then restart.

## Authentication protocol

Each GET request carries its Master-signed node certificate and Ed25519 signature bound to method, `RequestURI`, timestamp (±90s), random 24-byte nonce, and **expected destination node ID**. Receivers verify the Master cert, local allowlist of node IDs, exact audience, timestamp and nonce replay cache (up to 4096 entries). Requests cannot use a shared secret in signed mode.

Each success or retention-410 response includes its own Master-signed node certificate and node-signed response binding the request nonce, status code and SHA-256 body digest. Clients verify the expected node ID before parsing imported messages, reject redirects, and cap response bodies at 24 MiB. Opaque message envelopes retain existing device signatures, per-account destination, hop limit, TTL, dedupe and signed-revocation checks.

Remote federation **fails closed without signed identity**; legacy `X-Mesh-Secret` is available only when the listener and all configured peer URLs are loopback and no signed identity is configured. Do not expose this test compatibility mode.

## Tests and remaining limitations

Local Go `go test ./...`, race-protected Seed tests, Go vet, Linux/Windows builds and live Master/2-Seed E2E signed delivery pass. A 201-message local run measured roughly 11.4 MiB and 9.9 MiB RSS (not load certification). Actual WAN/TLS, offline renewal, peer key theft, power-cut rollback, and physical 1 GiB memory/hardware acceptance are untested.

**Important NO-GO:** certificates currently have an expiry but no explicit Seed certificate revocation list, issuer audit trail or seamless key rollover. A compromised issued node remains authorized until its certificate expires, subject to the local peer allowlist. To contain it now, remove that node ID from all Seed peer allowlists and redeploy peer configs; short-lived certificates reduce exposure but are not immediate global revocation. No trust-on-first-use, discovery, TURN or automatic certificate issuance. Device revocations are a separate Master feed. Do not deploy as a production internet service yet.
