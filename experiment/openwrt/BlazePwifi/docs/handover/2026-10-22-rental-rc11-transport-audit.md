# Handover — 2026-10-22 — BlazeRental RC11 transport boundary audit

## Verified baseline

- Latest exact provisioning release: `v0.5.2-rental.2-rc.10`, prerelease, target `047b4ac798e75b69d324eb802013fdaf7695bb91`.
- Dedicated RC10 release CI `39742380175`: success. General build run `39742380196`: cancelled; do not describe it as a pass.
- Physical Setup Wizard results and production signing continuity are **not** established. Keep stable-promotion gate closed.
- The older active `blazepwifi-rental-v0.5.2-hotfix2` branch is at RC9 (`5d9005f47a43a54dd64f419e5885ff88e6502244`) and is not the newest RC10 baseline.

## Finding and isolated implementation

`LeaseClient.post()` is shared by BlazeRental enrollment, authenticated status/policy updates, and coin-start. RC10 still inherited the platform default redirect-following behavior and buffered response JSON with no maximum size. This is a credential-routing/resource-consumption concern on an untrusted shared LAN.

Branch: `blazepwifi-rental-v0.5.2-rc11-network-audit`
Starting commit: `047b4ac798e75b69d324eb802013fdaf7695bb91`
Security implementation commit: `4f3f5cf75ff33ab8ada1a110858ea3f58bdc853f`

Affected files:
- `android/BlazeRentalLauncher/src/com/blazesystems/blazerental/LeaseClient.java`
- `android/BlazeRentalLauncher/src/com/blazesystems/blazerental/RentalHttpResponseGuard.java` (new)
- `android/BlazeRentalLauncher/tests/unit/com/blazesystems/blazerental/RentalHttpResponseGuardTest.java` (new)
- `profiles/standalone-rental/tests/static.sh`
- `profiles/standalone-rental/PROVISIONING-AUDIT.md`

Behavior: disable redirects for every Rental API POST, reject HTTP 3xx, enforce a 256 KiB JSON limit on successful and error responses, and always release streams/connections. Keep structured non-200 error JSON behavior intact.

JUnit tests cover 301/302/303/307/308 rejection, normal success, exactly-at-limit input, oversized refusal, and input-stream closure. Existing Android CI includes `testAospDebugUnitTest`. Do **not** record a pass until the CI run completes successfully.

## Non-goals and remaining blockers

RC10 and its assets remain immutable. RC11 is a source development checkpoint, not a published release. No R281 network/wireless/firewall changes, no update to coin controller code, and no change to one-time enrollment crypto. A signed TEST APK does not establish production signing identity; repeat Android Setup Wizard tests on authorized factory-reset devices. No universal GMS DPC compatibility claim.

## NEXT ACTION

1. Check the latest BlazePwifi build for this branch; investigate JUnit/Android or static regressions and correct them.
2. Confirm pure Java HTTP-bound tests ran (not only static grep).
3. Reconcile the final result with the lease/policy authenticated-update order from RC10.
4. If the code is green, record exact tested SHA/run in this handover; then prepare RC11 only with an immutable tag, distinct APK version code, exact release-bound checksum, and failing production-promotion gate until actual physical evidence is supplied.
5. Keep the user informed that no device was remotely flashed or physical Setup Wizard tested.

## Audit & Reconcile prompt

```text
@GitHub Reconcile and continue the BlazeRental / BlazePwifi Standalone Rental provisioning audit.
Read PROJECT_HANDOVER.md and docs/handover/2026-10-22-rental-rc11-transport-audit.md.
Verify RC10 exact published tag/asset target 047b4ac798e75b69d324eb802013fdaf7695bb91.
Review branch blazepwifi-rental-v0.5.2-rc11-network-audit and the latest BlazePwifi CI run.
Audit the new RentalHttpResponseGuard, LeaseClient no-redirect/size/cleanup integration, and JUnit test execution.
Reconcile enrollment v2 replay safety, verified policy-before-credit, server certificate pinning, stable promotion gate, Android DPC signing identity, and physical Setup Wizard blocker.
Fix only evidence-backed deficiencies. Do not alter RC10 tag, full BlazePwifi networking, or unrelated subsystems.
After every milestone update canonical handover and add a dated log with exact commit/run IDs and next action.
```
