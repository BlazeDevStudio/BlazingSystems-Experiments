# ConnectIT v0.1.4 — Node Revocation / Manual Renewal (DEVELOPMENT ONLY)

New v0.1.4 hardening: exact Master-issued node certificate revocation, separate signed node-key revocation feed, fail-closed cached Seed enforcement on incoming/outgoing federation, safe same-key certificate hot reread, and new negative/live tests. See `docs/NODE_REVOCATION_v0.1.4.md`. Still NO-GO for production.

# ConnectIT v0.1.3 — Signed Satellite Federation / DEVELOPMENT NO-GO

**Current release candidate documentation.** Master-authorized short-lived Seed certificates, Ed25519 mutually signed mesh requests and responses, per-node allowlists, replay protection, and no remote shared-secret fallback are implemented and locally tested. Read `docs/FEDERATION_v0.1.3.md` first. The older v0.1.2/0.1.1/0.1.0 text preserved below is historical and its statements that federation "still uses a shared secret" do not describe the new signed mode. Device revocation and account authority remain separate. No production client, WAN/TLS acceptance, peer-certificate revocation or automatic certificate renewal.

# ConnectIT v0.1.2 REVOCATION INTEGRATION — DEVELOPMENT / NO-GO

revocation-url enforcement and cached signed revocation gate; source/testing details under docs/REVOCATION*.md. Existing v0.1.1 baseline remains below. Do not use as production service.

# ConnectIT Seed 0.1.0 — Standalone Satellite / Development Preview

Standalone, headless Go relay adapted from verified **Blaze Messenger Seed v0.2.0**. The relay now has its own CLI executable and directory without Master account-creation code or a Master private signing key. Existing packet signing, Ed25519 device certificates, append-only JSONL, store-and-forward, polling peer synchronization, request replay cache and encrypted-opaque-payload validation are preserved. User's LAN Messenger code was not modified.

## Local build and setup

Go 1.23+; no third-party dependencies. These cross-compiles are supported when the target runtime permits:

```sh
go test -v ./...
CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o connectit-seed .
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -o connectit-seed.exe .
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o connectit-seed-linux-arm64 .
GOOS=linux GOARCH=arm GOARM=7 CGO_ENABLED=0 go build -o connectit-seed-linux-armv7 .
GOOS=darwin GOARCH=arm64 CGO_ENABLED=0 go build -o connectit-seed-macos-arm64 .
```

```sh
./connectit-seed init --dir ./seed-a --node-id seed-a \
  --master-public-key ../master-data/public.key \
  --listen 127.0.0.1:8081 \
  --peers http://127.0.0.1:8082
./connectit-seed status --dir ./seed-a
# For LAN peers, supply an independent, strong 32+ char secret through the OS service manager;
# do not put a shared secret in source, release ZIP or a world-readable service file.
export CONNECTIT_MESH_SECRET='<independent-random-long-mesh-secret>'
./connectit-seed start --dir ./seed-a
```

`start` uses persisted config and never asks for an interactive password. Node Ed25519 `node.private.key` and `node.public.key` are generated at initialization, but currently **NOT used to authenticate peers**. Peer connections still authenticate using inherited mesh secret; per-node cryptographic federation enrollment and revocation are still pending. The Master public key must be pinned out-of-band.

`seed.json` controls listening IP/port, peer URLs, master key path, TLS PEM paths, `max_messages`, `max_payload_bytes`, `sync_seconds`, and `mesh_secret_env`. Config edits should occur while stopped. A peer address MUST use HTTPS unless it is loopback HTTP. A node behind ISP CGNAT, MikroTik, OpenWrt or cellular NAT cannot be discovered automatically; port forwarding/public rendezvous or an approved outbound tunnel will be necessary for incoming reachability. A router firewall and DNS do not substitute for TLS. Use a process manager/systemd/OpenWrt procd for restart automation. Physical router resource usage requires verification.

**Message hop cap:** the newly added metadata `hops` starts at zero when accepted from a client. Every ConnectIT Seed peer import increments it; peers no longer export an envelope with `hops >= 5`. This bounds federation *message forwarding* among new nodes; it is **not** privacy-preserving five-hop user discovery. Mixed with unmodified old relays, the hop limit is not guaranteed.

**Important limits:** decoded envelope payload 8192 bytes by default; only encrypted text and small encrypted `signal` allowed; **no file/call media can travel through the relay**. On-disk queue is bounded by retained **count**, not recipient ACK. A seed may acknowledge before peers replicate; a device offline past retention can lose messages. Signals expire after 180 seconds. Per-seed cursors, no exactly-once ordering guarantee, no realtime device revocation feed. Seed checks certificates by expiration and pinned Master public key while Master is offline; existing credentials expire after 7 days by default. No Flutter media/ICE implementation is included.

Verified: Go regression tests, standalone CLI initialization/status, Linux localhost master-authorized device->Seed A->Seed B relay with `hops=1`, and retrieving message from Seed B after Master shutdown. The seed's physical 1 GB target, high-load memory limits and multi-hop failure recovery remain not fully verified.

## Independent ConnectIT test dummy note (v0.1.1 packaging)
The separate `ConnectIT-LAN-Messenger-Draft` archive includes a real two-account local test in `test/lan_build_dummy_e2e.py`, with independently enrolled Ed25519 devices, X25519/AES-GCM dummy ciphertext, relay-to-relay delivery, bad-ciphertext rejection by the recipient, and file relay policy enforcement. This test uses this existing v0.1.0 Seed binary; it is NOT an Android/Windows LAN Messenger binary test. Node-specific federation enrollment, revocation and private discovery remain incomplete.
