# ConnectIT — v0.1.2 development-only source dump

Three independent products reside in their respective folders. The original LAN Messenger source and release are **not modified**. This branch preserves the prior Blaze Messenger Seed v0.2.0 relay compatibility while developing Master-owned device authority and a signed revocation view. Current LAN Messenger test adapter remains separately parked in draft PR #230.

## Evidence

Go 1.23 Linux x86-64: both projects' unit tests, `go vet`, build; Windows x86-64 Seed cross-build. Local Python integration: two-seed relay, signed enrollment, Master-offline retrieval, revocation refresh and revoked credential rejection. Draft Flutter source is not a compiled client. Physical device acceptance, peer node-identity signatures, production TLS deployment, five-hop private user discovery, SecureBind notification delivery, P2P file/audio/video, Android key storage and production signing remain **NO-GO**.

## Security-specific scope

Master `GET /v1/revocations` returns signed, hour-limited revocation fingerprints with monotonic SQLite generation. Satellite HTTPS fetches and verifies pinned Master signature; stored cache allows a bounded Master outage. Remote-listening satellites require configured revocation URL. Accepted credentials without a current signed view are rejected when cache expires. Local-only legacy mode is not production-safe. No claim of immediate revocation propagation or rollback-resistant hardware witnessed trust.

## Go workflow

```bash
cd ConnectIT-Master-Seed && go test ./... && go build -o bin/connectit-master .
cd ../ConnectIT-Seed && go test ./... && go build -o bin/connectit-seed .
cd ..
python3 ConnectIT-Master-Seed/tests/revocation_smoke.py
```

## Artifacts

Independent dev ZIP archives with built binaries and SHA256 manifests are kept in the private Google Drive `ConnectIT Development` folder. Never commit or publish private signing keys, generated installation tokens, live SQLite databases, or device credentials. No production release or merge authorized.
