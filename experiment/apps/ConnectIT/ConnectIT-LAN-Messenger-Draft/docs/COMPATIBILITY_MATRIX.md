## v0.1.2 addendum — signed revocation gate

| Master | Seed | Client | Evidence |
|---|---|---|---|
| ConnectIT Master 0.1.2 | ConnectIT Seed 0.1.2 | Python Ed25519 device fixture | Live localhost: enrolled client 200, revoked device 401 after refreshed signed snapshot, still 401 after Master shutdown. PASSED. |
| ConnectIT Master 0.1.2 | ConnectIT Seed 0.1.1 | Any | Signed revocation extension UNSUPPORTED by old Seed; upgrade needed for remote exposure. |
| ConnectIT Master 0.1.2 | ConnectIT Seed 0.1.2 | LAN Messenger 0.3.2 dummy PR #230 | Native Flutter application integration remains **unimplemented**, no client binary claim. |
| Any | Any | 5-hop discovery, real WebRTC over internet | NOT IMPLEMENTED. |

# ConnectIT Compatibility Matrix v0.1.0

| Master | Seed | Client | Evidence / status |
|---|---|---|---|
| ConnectIT Master Seed 0.1.0 | ConnectIT Seed 0.1.0 | Python Ed25519 test utility | PASS local Linux: 10-digit ID, signed enrollment, two-seed sync, Master offline retrieval |
| ConnectIT Master Seed 0.1.0 | Original Blaze Seed v0.2.0 | Original CLI test client | Expected wire compatibility (issuer/audience and envelope), not run as a pair |
| ConnectIT Master Seed 0.1.0 | ConnectIT Seed 0.1.0 | ConnectIT Flutter draft 0.1.0 | Interfaces only, NOT usable app integration |
| Master unavailable | ConnectIT Seed 0.1.0 | Already authorized test device | Valid unexpired cert tested; new devices cannot enroll |
| Any | Any | Five-hop private discovery + WebRTC file/media | NOT IMPLEMENTED |

Do not infer full v1 compatibility from a reused `/v1/` route label. See full protocol document.

## v0.1.1 separate dummy addendum (2026-10-28)

| LAN Messenger reference | ConnectIT Master | ConnectIT Seed | Verification |
|---|---|---|---|
| Latest **CI-built** LAN Messenger Flutter `0.3.2+15` at `7d8a08a` | v0.1.0 | v0.1.0 | Existing LAN binary build artifact verified; **not integrated** with ConnectIT |
| Temporary Python protocol client matching X25519 design and Ed25519 Seed auth, not native Flutter | v0.1.0 | v0.1.0 x2 | **PASS** two-account local encrypted text, 1-hop, trusted-sender signature, tamper rejection, forbidden file payload, Master-offline retrieval |
| Inert Dart bridge on isolated draft PR #230, exact base `7d8a08a` | v0.1.0 | v0.1.0 | Compile/test proposed; **NOT verified** at PR head |
| Later LAN Messenger `0.3.3+16` draft #229 at `a9f8745` | v0.1.0 | v0.1.0 | Source identified, **no verified binary in this handout** |
