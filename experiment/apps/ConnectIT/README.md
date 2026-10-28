# ConnectIT — independent development products (v0.1.3)

**Development only; NO-GO for production.**

Separate, individually distributable source trees: `ConnectIT-Master-Seed/` (SQLite and account authority), `ConnectIT-Seed/` (Go satellite relay), `ConnectIT-LAN-Messenger-Draft/` (disabled-by-default Flutter interface draft). The current source builds server binaries only, not a ConnectIT native Flutter app. The original LAN Messenger code is untouched.

v0.1.2 introduced Master-signed device revocation cache; v0.1.3 adds Master-authorized short-lived Seed certificates, signed peer GET/response exchange with explicit peer ID allowlists, replay controls, no remote shared-password fallback. See `ConnectIT-Seed/docs/FEDERATION_v0.1.3.md` for commands and threat limitations.

To run CI locally: build Master and Seed in their own `go.mod` directories; run `go test ./...` and `go vet ./...`. See `ConnectIT-Master-Seed/tests/signed_mesh_e2e.py` for 201-message Master→Seed-A→Seed-B smoke. A real internet TLS deployment, peer certificate revocation, key protection, automatic renewal, E2EE native client, SecureBind UI, NAT traversal, five-hop discovery and real Android/Windows integration remain blocked.

Historical audit trail: v0.1.2 draft PR #231; v0.1.3 draft PR is stacked and should not be merged until dependency accepted. Binary/source ZIPs are stored in user's private Drive under `ConnectIT Development`; no release artifact or signing key should be committed here.
