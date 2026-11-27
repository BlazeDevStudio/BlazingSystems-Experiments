# Standalone Rental Releases

> The provisioning candidates below are immutable release/tag builds. The current `main` runtime source is not automatically equivalent to the newest provisioning RC. Use the corresponding tag/release when validating a candidate.

## Latest provisioning candidate

### v0.5.2-rental.2-rc.9

RC9 supersedes RC8 for Device Provisioning validation while leaving RC8 immutable.

Security delta:

- pins the first accepted pending Device Provisioning identity to the exact server origin, one-time enrollment token and certificate SHA-256 pin;
- accepts exact Android Setup Wizard callback replay idempotently;
- rejects a changed token, server origin or certificate pin instead of silently replacing pending provisioning state;
- rejects Device Provisioning callbacks over pending Standard Enrollment state or partial/permanent device identity;
- adds executable JUnit coverage for the provisioning-state acceptance/rejection matrix;
- Android package identity `0.5.2-rental.2-rc.9`, versionCode `50210`.

RC9 remains TEST-signed and `physical_setup_wizard_validation_pending=true`. It is not a stable production-signing release.

Release: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.2-rental.2-rc.9

### v0.5.2-rental.2-rc.8

RC8 added stable-promotion signer verification and explicit provisioning target scope:

- verifies the actual APK signer certificate instead of trusting signer metadata alone;
- restricts non-GMS-approved custom DPC releases to `aosp_non_gms_or_explicit_oem_only`;
- binds physical validation evidence to exact target scope and signer identity;
- Android package identity `0.5.2-rental.2-rc.8`, versionCode `50209`.

### v0.5.2-rental.2-rc.7

RC7 added strict server-origin parity: host/port validation, bracketed IPv6 handling, and rejection of userinfo/path/query/fragment/backslash/whitespace/control-character ambiguity.

### v0.5.2-rental.2-rc.6

RC6 added idempotent repeated provisioning callbacks, safe Standard Enrollment rebind behavior, bounded stale enrollment state, and explicit Transfer-before-rebind semantics.

### v0.5.2-rental.2-rc.5

RC5 introduced secure enrollment protocol v2:

- Standard schema `blazerental.enrollment.v2`;
- provisioning schema `blazerental.provisioning.v2`;
- derived long-lived device secret rather than transmitting it;
- HMAC-authenticated enrollment response;
- retry-safe one-time enrollment and protocol-downgrade rejection.

### v0.5.2-rental.2-rc.4

Administrator-only Device Provisioning generation and canonical padded Base64URL APK checksum handling.

### v0.5.2-rental.2-rc.3

Exact APK/signer evidence, shared provisioning metadata generation and explicit custom-DPC/GMS compatibility gating.

### v0.5.2-rental.2-rc.2

Atomic one-time enrollment claims, exact TEST APK identity and executable provisioning/race CI.

### v0.5.2-rental.2-rc.1

First published split Standard Enrollment / Device Provisioning candidate.

## Latest stable server

### v0.5.2-rental.1

Stable server/UI hotfix line predating the full provisioning-candidate architecture.

## Older stable/RC lines

- v0.5.2-rental
- v0.5.2-rental-rc.2
- v0.5.2-rental-rc.1
