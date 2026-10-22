# BlazePwifi Standalone Rental Server v0.5.2-rental.2-rc.11

**Security audit candidate — NOT a production Device Owner release.**

RC10 contains a targeted correction to authenticated Rental lease/policy state handling. Previous source applied local `recordLease()` before validating the signature of a status response. RC10 no longer changes local paid time for an unverified or stale signed status response.

### Changes

- Require the response device ID to match the persisted Rental identity.
- Verify signed policy and reject decreasing policy revisions before recording lease time.
- Permit same-revision signed status updates to refresh a lease without rewriting operator policy.
- Reject unversioned/legacy policy response after a modern revision has been accepted.
- Persist newly verified policy synchronously; fail instead of continuing when storage fails.
- Android provisioning-compliance activity requires a successful follow-up authenticated status sync and persisted policy before returning `RESULT_OK`.
- Device Owner completion rejects previously saved Standard Enrollment state and changed/invalid provisioning callbacks; the legacy provisioning-complete receiver enforces the same source identity and second authenticated policy sync.
- New pure-Java JUnit revision tests and static source-order checks are executed in the Android/release validation matrix.
- Android TEST APK versionCode **50212** and versionName **0.5.2-rental.2-rc.10**, unique versus RC9.
- Existing Standard Enrollment and Device Provisioning QRs remain distinct. R281/EasyMode and BusyBox installer boundaries are preserved.

### Release constraints

This is a **prerelease with TEST signing**. No claim is made that the Device Owner Setup Wizard flow has succeeded on a physical phone, that the DPC is GMS-approved, or that production signing continuity has been established.

A stable promotion still requires the exact production APK signer and physical evidence specified in `PROVISIONING-AUDIT.md`. Do not install this TEST-signed APK over existing production-signed managed devices: Android signing identity continuity will reject or disrupt that upgrade path.

To avoid a Setup Wizard callback race, `DeviceAdminReceiver` no longer attempts the initial server enrollment on Android 8+; the dedicated provisioning activity owns that path. The receiver retains the legacy Android 5–7 fallback only.

A nonnegative local revision by itself is not sufficient: RC10 additionally requires evidence of a persisted signed policy before allowing a same-revision lease refresh or returning Device Owner provisioning success.

RC9 tags/assets remain immutable.

### Primary Windows installer

`BlazePwifi-Rental-Standalone-Windows-OneClick-v0.5.2-rental.2-rc.11.zip`

The Windows package continues to include the separately named admin reset BAT and retains router/network configuration isolation.

### Immutable-tag correction

RC10 was published from commit `047b4ac798e75b69d324eb802013fdaf7695bb91` before later audit fixes were complete. Its release guard correctly prevented an overwrite. RC11 contains those later verified-policy, Device Owner callback-source and modern Android single-owner completion corrections as separately versioned assets. RC10 remains unchanged. RC11 is TEST-only pending production signer and physical Setup Wizard validation.
