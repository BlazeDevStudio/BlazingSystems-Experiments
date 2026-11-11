# LAN Messenger integration note — revoked ConnectIT session state

Compatibility target remains pinned LAN Messenger Flutter 0.3.2+15 at `7d8a08afb39bab8d001fce3d3ba33706e034fcb1`; temporary inert adapter on draft PR #230. This file changes no LAN Messenger code.

For future client: keep existing LAN X25519 key separate from ConnectIT Ed25519 proof-of-possession identity. Store protected ConnectIT device credentials in OS key storage, never the temporary test-client file. On HTTP 401/403 from Seed, show `ConnectIT session expired or revoked` and disable only the internet ConnectIT route. Retain independent local LAN chat/calls/files. If signed revocation cache becomes unavailable, show a service availability error rather than pretending the old credential is active. New Master enrollment and SecureBind approvals need their own audited screen, local PIN and signature flow before enabling.

Master 0.1.2 and Seed 0.1.2 interoperate for the tested signed revocation mechanism. Old Seed 0.1.1 cannot read signed revocation state and MUST be considered unsafe for public-node authorization. Native Flutter integration is NOT compiled/tested here; no new APK/EXE is claimed.
