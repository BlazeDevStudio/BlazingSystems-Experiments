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


## Installer failure and pending-state debugging (draft)

- `BlazeRentalUpdateManager.markInstallPending` writes a pending version before
  handing an APK to Android `PackageInstaller`. A successful **request to
  install** is not proof that installation succeeded.
- `BlazeRentalUpdateReceiver` receives asynchronous installer callbacks.
  A genuine `STATUS_PENDING_USER_ACTION` with a confirmation Intent keeps
  `pending_code` intact; user action is still outstanding.
- A terminal failure (including a missing required confirmation Intent) calls
  `recordTerminalInstallFailure`, which removes only `pending_version`,
  `pending_code`, `pending_rescue`, `pending_boots` and
  `pending_started_wall`. It preserves `last_error` and `previous_apk`
  for diagnosis; do not delete any real installer backup here.
- Four isolated API27 regression cases are in
  `tests/src/com/blazesystems/blazerental/BlazeRentalUpdateFailureTest.java`.
  They use separate test preferences and intercept the user confirmation
  Intent; no APK download/install or real Device Owner interaction occurs.
  Run explicitly in an Android27 emulator with the instrumented class:
  `connectedAospDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=com.blazesystems.blazerental.BlazeRentalUpdateFailureTest`.
- The existing focused auth suite only executes
  `LeaseSyncAuthBeforeCommitTest` (7 cases), **not** this new class.
  New tests are not accepted until exact-SHA XML evidence confirms all four.
  The broader build compiles the Android test APK but does not necessarily
  execute every instrumentation class.
- Synchronous failures before or during `commitInstall` are a separate
  recovery review. Do not claim full installer transaction atomicity.


### Attempt correlation and stale callback protection

Each pending installation now receives an opaque random token from
`markInstallPending`, carried in the explicit `PackageInstaller` result
`PendingIntent`. Its unique action includes the token so an earlier
installation cannot reuse the newer result sender. The receiver checks that
the callback token matches the currently pending attempt before touching
the UI or clearing state. Terminal failure clearing repeats the token check
inside a synchronized transition, so a stale callback cannot clear a newer
attempt even if the state changes between receipt and write.

The fourth isolated test exercises an old failed result arriving after a
new attempt begins. The four-case test suite is **not** executed by the
existing seven-case lease-authentication workflow and must be run
explicitly on API27 for a source-exact proof. Synchronous exceptions before
or during `commitInstall` remain a distinct recovery follow-up.


## Synchronous PackageInstaller submission exceptions (2026-11-15)

- `BlazeRentalPackageUpdater.downloadAndInstall` retains the pending
  attempt token once `markInstallPending` succeeds. Before
  `PackageInstaller.Session.commit` is invoked, a staging/streaming
  exception abandons the session (including the created session ID if
  the handle could not be opened), closes owned resources, and clears
  **only that token's** pending metadata while retaining the diagnostic.
- Once `commit()` is attempted, an exception can mean the submission
  result is *ambiguous*, not that Android rejected the installation.
  It therefore keeps the pending attempt for a matching asynchronous
  callback; `recordPendingInstallError` scopes the diagnosis to that
  token. An older failure cannot clobber a newer attempt.
- `Session.close()` is handled in `finally` without reclassifying
  an accepted commit as a terminal installation failure.
- `BlazeRentalUpdateFailureTest` now includes **six** isolated API27
  cases (two new: precommit exception/current token and commit-attempt
  uncertainty/callback). The source-linked runner checks these six plus
  seven lease-authentication cases: **13 total**. Do not treat test
  authoring or app APK compilation as 13/13 execution evidence.
- Real installer session failure injection, actual signed installation,
  legacy pre-token pending recovery, device-owner compatibility, power
  interruption and rollback acceptance still require separate tests.
  Neither this change nor CI autorizes production rollout.


## PHX-ANDROID staged continuation checkpoint — 2026-11-25

**Original role specification:** `02_BLAZERENTAL_ANDROID.txt` recovered; retained responsibilities include Launcher3 Android client, management modes, local allowed/hidden applications, alarms, offline lease UX, QR/auth, admin access, APK signing continuity, and assigned standalone rental-facing server integration. The latter is an interface responsibility, **not** ownership of PHX-CORE's money, receipt or ledger authority. Supplemental `Pasted text(2).txt` outlines multi-agent coordination. The 2026-11-25 master staged directive supersedes blanket development-stop language but **not** real acceptance gates.

**Source/coordination:** Keep `phoenix/rental-apk-contract-audit-20261121` draft PR #328 stacked on PHX-RENTAL #289 → #240. Master owns issue #172, PR #288 and `coordination/phoenix/`; owner mapping remains `DRAFT_REVIEW_ONLY`. Do not relocate, merge, delete, sign, flash or run on customer devices without the relevant independent conditions being met.

**Provisional deterministic workstream acceptance ledger:** `PHX_RENTAL_WORKSTREAM_ACCEPTANCE.json` revision `PXA-WORKSTREAM-R1-2026-11-25`, 31 mandatory criteria, 100 fixed risk-weighted points with actual deployment separated (2 points). After the latest Android 27 evidence, six criteria worth **21 readiness points out of 98** are verified: 21.43% **PROVISIONAL PHX-ANDROID only**. Previous checkpoint before API27 test was 10/98=10.20%, net +11/98=+11.22 percentage points. Unverified readiness weight = 77. Unknown readiness weight = 11. The theoretical upper bound is 100%, range 78.57 percentage points; this is not statistical uncertainty or proof of likely completion. Exact reproducible calculation:
`python3 tools/compute_acceptance_progress.py PHX_RENTAL_WORKSTREAM_ACCEPTANCE.json` (execute from this launcher directory).
Global deployment readiness is **NOT YET MEASURABLE**, pending MASTER's deduplicated cross-role ledger.

**Evidence pins**
- Android API21/API23 install/startup + debug signing: [CI run 44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) SUCCESS, source `0e0da62acd47c6a1ce287f8a30fc700d603fa070`.
- Android API27 7 lease-auth + 6 installer cases: [CI run 45621832195](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45621832195) SUCCESS, source `0907da70c55b61d013aa75b5002ab37a51ccdf0a`, JUnit [artifact #15026510211](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45621832195/artifacts/15026510211).
- Workstream staged ledger + APK contract verifier: [CI run 45621832194](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45621832194), 22/22 host cases PASS on `0907da70c55b61d013aa75b5002ab37a51ccdf0a`.
- These are bounded source-exact results. They do not validate a physical OEM device, live credit transaction, Device Owner or Work Profile recovery, release signing or actual deployment.

**Stage 00–09 status (PHX-ANDROID only; gates do not advance on source edits alone)**
| Stage | Gate status and next evidence |
| --- | --- |
| 00 Mission recovery | IN PROGRESS — original mission and later directives recovered; MASTER scope/ownership signoff pending |
| 01 Architecture/planning | IN PROGRESS — R1 weighted workstream ledger defined and tested; MASTER deduplication/acceptance pending |
| 02 Stabilization | IN PROGRESS — API21/23 install and API27 focused suites pass; broader CI and regression coverage not fully green |
| 03 Functional development | IN PROGRESS — complete explicit lifecycle, admin, offline/reboot and DPC behavior plus real integration tests |
| 04 Compatibility | IN PROGRESS — only API21/API23 x86 installation has current evidence; API26+ and ARM/OEM pending |
| 05 Cross-system integration | BLOCKED — CORE durable credit receipt contract and isolated backend transactions need coordination |
| 06 QA/security | NOT STARTED for final gate — independent managed policy/reversal, fault injection and physical QA outstanding |
| 07 Release engineering | BLOCKED — production signing/versionCode, rescue, reproducibility and review gates outstanding |
| 08 Deployment validation | NOT STARTED — fresh authorized provisioning, signed upgrade, rollback and recovery |
| 09 Production acceptance | NOT STARTED — owner approval and operational acceptance not performed |

**Actionable blocker register**
- **PXA-BLK-001 / migration ownership:** PHX-MASTER's `OWNERSHIP_ROUTES.json` is `DRAFT_REVIEW_ONLY`; prepare SHA-256 file-by-file source/target/licensing map, reconcile private storage registry, request owner approval before transfer. Parallel: launcher code tests and source audit.
- **PXA-BLK-002 / shared build:** Whole BlazePwifi CI fails at a CORE-owned handover freshness gate and ESP32 Mbed TLS/toolchain problem in inherited streams. CORE/HARDWARE/QA own respective fixes; continue scoped Android tests without bypassing mandatory gates.
- **PXA-BLK-003 / Device Owner and Work Profile:** No source-exact fresh disposable enrollment/lock/reversal evidence; implement reversible instrumented policy tests without customer devices. PHX-ANDROID with PHX-QA review.
- **PXA-BLK-004 / credit authority:** Client cannot claim durable financial ACK or replay acceptance until PHX-CORE supplies a versioned, tested receipt/lease contract. PHX-ANDROID prepares negative integration tests only.
- **PXA-BLK-005 / production signing:** Only Lineage-2 certificate metadata is documented; actual owner-signed upgrade and physical rollback are unverified. PHX-RELEASE/owner key custody required; no debug APK passes as an upgrade.
- **PXA-BLK-006 / autonomous wake-up:** Separate hourly PHX-ANDROID automation could not be created because account already has five active scheduled tasks (plan limit); current session is real, but future wake-up remains **NEEDS_EXTERNAL_WAKEUP** unless an existing authorized scheduler is arranged. Do not silently replace another role's task.

**Next owned sequence:** (1) Confirm current PR #328 head/CI and remote-readback ledger, (2) add safe Device Owner policy apply-and-reverse regression on a fresh API27 emulator, (3) inspect actual protocol fixtures with CORE for replay/ACK safety, (4) expand API26/29/30/33/35 compatibility, (5) request PHX-QA and MASTER review and submit a deduplicated BLAZE-COMMS/1 progress envelope. No production cutover merely because development may proceed.
