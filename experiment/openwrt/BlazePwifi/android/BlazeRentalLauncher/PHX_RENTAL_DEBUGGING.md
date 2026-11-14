# PHX-RENTAL — Android source map and debugging guide

> **Scope:** Launcher3-derived BlazeRental Android client. Draft-only, not a release
> or an authorization to handle real devices, signing keys, coins, or customer data.

## Verified source placement (2026-11-15)

- Active, full native launcher source: `BlazeDevStudio/BlazingSystems-Experiments`,
  `experiment/openwrt/BlazePwifi/android/BlazeRentalLauncher/`.
  Its authentication-first changes are tracked in **draft PR #240**
  (`phoenix/rental-auth-before-persistence-20261029`).
- The same Experiments repository also has
  `experiment/openwrt/BlazePwifi/android/BlazeRental/` (a different Android
  client tree) and `android/token-launcher/` (a separate token launcher).
  **Do not replace the Launcher3-derived client with either by filename.**
- `BlazeDevStudio/CoinOperatedEcosystem/main` remains an intake scaffold.
  Draft integration PR **#26** already stages a separate
  `Rental/android/` Android status scaffold and standalone OpenWrt server.
  The staged scaffold is **not a byte-for-byte migration of the complete
  Launcher3-derived application**.
- Standalone `Rental/openwrt/` development also exists as draft
  CoinOperatedEcosystem PRs **#19** and **#22**. Their ledger/HMAC routines
  are not equivalent to full BlazePwifi's financial authority.
- The owner-only Google Drive project registry v11 (2026-10-27) marks the
  integrated Phoenix ecosystem source recovery as partial and production as
  NO-GO. The registry is historical inventory, not an overriding Git ref.

**Migration action:** do not copy, delete, or reparent these trees until
PHX-MASTER resolves module ownership, source ancestry, licensing, build entry
points, and a file-by-file equivalence map. Preserve original paths/commit
history and avoid case-colliding `Rental/` versus `rental/` copies.

## Authentication and state flow: `LeaseClient.sync(Context)`

1. Read pinned server/enrollment/device identity from `RentalLeaseStore`.
2. Build nonce-bound `enroll` or `status` request. Post over configured
   network transport.
3. Validate identity and enrollment proof (enroll) or **coin-window HMAC and
   policy v1/v2/v3 HMAC** (status), using the installed device secret, not any
   response-supplied key.
4. Check policy revision against `AndroidRentalPolicyRepository.revision`.
   Stale revisions fail before lease, alarms, UI, and policy writes.
5. Build and validate immutable `RentalPolicy`. For the **same** revision,
   `RentalPolicyRevisionGuard` checks that a lease-only refresh cannot rewrite
   policy. A server-signed `*` can tolerate an inventory change only when
   the previously accepted v2/v3 payload was also signed with `*`.
6. Only then call `RentalLeaseStore.recordLease`, update the coin-window
   display, and (on strictly newer revisions) persist policy/UI/admin/update
   metadata. Finally reconcile `ManagedPolicyController`.

**Important:** `RentalPolicyRevisionGuard` is a pure *compatibility*
predicate; it neither authenticates signatures nor authorizes leases. Do not
call it before signature verification or substitute it for revision checks.

## Quick developer verification

- Host-JVM regression fixture:
  `tests/unit/com/blazesystems/blazerental/RentalPolicyRevisionGuardTest.java`.
  Covers same-revision positive and wildcard-inventory positive, explicit
  restriction, mismatched device/revision, hidden list, and mode drift.
- Existing Android instrumentation fixture:
  `tests/src/com/blazesystems/blazerental/LeaseSyncAuthBeforeCommitTest.java`.
  It checks **real sync state** for invalid coin proof, attacker-provided
  secret, stale revision, same-revision refresh, wildcard, and alarms.
- This is a legacy **Android SDK 27 / build-tools 27.0.3 / Java 8 /
  Gradle 4.4.1 / Android Gradle Plugin 3.1.3** build. Preserve those
  version constraints unless a separate tested migration is approved.
  Use the PR #240 native Android CI entrypoint
  `.github/scripts/run-blazerental-native-auth.sh` for emulator verification;
  do not interpret Java host-unit PASS as Android or Device Owner acceptance.
- For diagnosis, capture exact commit SHA, failing test method and first
  exception, revision before/after, nonce *presence* (never its value),
  and which phase rejected the status. Do not log HMAC secrets, enrollment
  tokens, private keys, signed customer QR data, or customer identifiers.

## Safety and integration status

Financial receipt and controller admission remain owned by PHX-CORE;
cross-subsystem signing/receipt schema changes need MASTER + CORE review.
Production stays **NO-GO** pending independent anti-rollback witness,
safe financial migration, real-device signing/provisioning and authenticated
physical power-cut / soak evidence. A passing local unit or emulator test
does not satisfy those gates.
