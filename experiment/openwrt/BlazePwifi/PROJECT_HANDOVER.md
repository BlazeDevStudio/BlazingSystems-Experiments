# BlazePwifi — ACTIVE BRANCH ROUTING (READ THIS FIRST)

**As of 2026-10-08, this default-branch handover is a historical snapshot, not the active v0.6.0 development state.** The active product is developed on `blazepwifi-v0.6.0-audit-foundation`, draft [PR #30](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/30).

**For every new ChatGPT conversation or developer handoff, read the ACTIVE branch files before touching any source:**
1. [Current development handover](https://github.com/BlazingSystems/BlazingSystems-Experiments/blob/blazepwifi-v0.6.0-audit-foundation/experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md) — current status at top.
2. [Current state and next exact action](https://github.com/BlazingSystems/BlazingSystems-Experiments/blob/blazepwifi-v0.6.0-audit-foundation/experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md).
3. [Mandatory continuous handover policy](https://github.com/BlazingSystems/BlazingSystems-Experiments/blob/blazepwifi-v0.6.0-audit-foundation/experiment/openwrt/BlazePwifi/docs/handover/HANDOVER_POLICY.md).
4. [Change/evidence ledger](https://github.com/BlazingSystems/BlazingSystems-Experiments/blob/blazepwifi-v0.6.0-audit-foundation/experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md).
5. [Cross-platform audit and open issues](https://github.com/BlazingSystems/BlazingSystems-Experiments/blob/blazepwifi-v0.6.0-audit-foundation/experiment/openwrt/BlazePwifi/AUDIT.md).

**Production is still frozen at full v0.5.2; Standalone Rental RC9 is separately frozen.** No v0.6.0 signed release or approved 0.6.0 firmware is implied. Do not merge untested branch code to `main`, overwrite the Windows `softtimer-v0.4.0` release, expose signing secrets, or assume that an earlier green CI run covers the new branch head.

**Canonical policy:** the above *active-branch* live records are synchronized at every meaningful source/test/blocker transition. This default-branch pointer is deliberately stable; it does not mirror every changing build result. Cross-check exact branch HEAD, draft PR and GitHub Actions at resume time.

---

# Archived main-branch handover — older operational snapshot

# BlazePwifi Project Handover

**Last updated:** 2026-10-07  
**Repository:** BlazingSystems/BlazingSystems-Experiments  
**Production baseline:** BlazePwifi **v0.5.2** is the frozen production release. BlazeRental production signing lineage `BlazeRental-production-lineage2` is established and must be preserved for all future production upgrades.  
**Active development:** **v0.5.3-dev.5 ZeroTier live activation**. Exact green application candidate `29a3815e81c9bd7db54c8f60eb6f579c818f34ad`; push workflow `37540065074` — PASS; PR #25 synthetic merge-tree workflow `37540072921` — PASS. This remains development-only; no v0.5.3 production tag/signing action has been taken.  
**Scope guard:** Full BlazePwifi is the active product. `profiles/standalone-rental` is reference-only and must not be modified by Full BlazePwifi work unless the owner explicitly changes that instruction.

## Current v0.5.3 development status

The post-v0.5.2 hardening work is implemented and artifact-validated. This is a **development line**, not a production v0.5.3 release.

- Development identity: `0.5.3-dev.5`.
- Android development versionCode: `50294`.
- Reserved development range: `50290–50298`.
- Frozen v0.5.2 rollback rescue versionCode: `50299`.
- Reserved final v0.5.3 production versionCode: `50300`.
- Full-console CSRF mutations now send both form-body and header tokens, use same-origin/no-store requests, refresh stale sessions and retry a CSRF mismatch once.
- Rental setup now has two explicit QR paths:
  - **Binding QR** for an already-installed BlazeRental APK;
  - **Device Owner Provisioning QR** for factory-reset Android Setup Wizard.
- Device Owner provisioning binds to the published signed APK checksum and pins the local BlazePwifi TLS certificate for secure enrollment against the default self-signed admin certificate.
- One-time enrollment is retry-safe across a lost response: the same persisted request nonce returns the same permanent identity, a different nonce is rejected, and the enrollment response is HMAC-authenticated before BlazeRental commits identity.
- BlazeRental and the PisoWiFi captive portal now have separate server-authoritative:
  - purchased/session countdown;
  - Insert Coin reservation countdown.
- Rental coin progress is server-accounted and signed: accepted pulse count and centavo value are displayed, duplicate Vendo events do not add credit twice, repeated open requests reuse the same active reservation, and Done/expiry releases the target.
- BlazeRental runtime UI now visibly renders `BLAZERENTAL`, `00:00:00`, `TIME FINISHED` and `INSERT COIN` in the unpaid Device Owner state.
- Exact green validation run `37486090360` passed:
  - static/security/config/integration/stress validation;
  - Android current + frozen-v0.5.2 rescue APK builds;
  - Android Device Owner emulator;
  - browser QR/CSRF/session-timer/coin-window runtime audit;
  - ESP8266 and ESP32 build/simulation;
  - Ruijie build/simulation;
  - x86_64 build + QEMU simulation;
  - required Orange Pi build/simulation targets;
  - transactional update bundle;
  - final candidate gate.
- Runtime Android audit artifact: `BlazePwifi-v0.5-android-simulation`.
- Current Android build artifact: `BlazePwifi-android-current`.
- Current update artifact: `BlazePwifi-current-update`.
- Current candidate-gate artifact: `BlazePwifi-current-candidate-gate`.
- **dev.2 Management Console operations are green:**
  - Advanced Terminal is disabled by default and requires admin re-authentication, CSRF, session/IP binding, short TTL/idle expiry, bounded runtime/output and single-command concurrency.
  - Advanced Terminal session tokens remain browser-memory-only; no localStorage/sessionStorage persistence.
  - High-risk appliance lifecycle/storage commands are blocked from the raw terminal path.
  - Safe Tools now include WAN/NTP/jitter/TCP-port/neighbors/controllers/services/logs diagnostics in addition to existing commands.
  - Worldwide Remote Access profiles support Disabled/WireGuard/ZeroTier staging with separate Monitoring/Management/Remote-Terminal permissions and no private-key field.
  - Remote live network/firewall activation remains intentionally safety-locked until a separate apply/rollback network-survival matrix is green.
  - Dynamic shell security test and Playwright user-flow audit both passed.
- Exact dev.2 branch workflow `37500821733` passed all required Android, browser, ESP8266/ESP32, Ruijie, Orange Pi, x86 QEMU, update-bundle and final candidate gates.
- PR #18 reconciles dev.2 with the four newer unrelated BlazePisonet SoftTimer commits on `main`. Synthetic merge tree `dee385974b7142afa4e8a56fc47d611f62a10ccf` passed workflow `37500829258`, including browser runtime, x86 QEMU, Android Device Owner emulator and final candidate gate.
- During PR validation a real UI race was found and fixed: an unconditional delayed startup `loadRemote()` could reset the selected remote mode while the operator was editing. The fixed console no longer preloads editable remote config in the background, suppresses stale async responses, and renders the authoritative save response immediately.
- Android Device Owner emulator explicitly passed `0.5.3-dev.2` using `candidate/android/BlazeRental-0.5.3-dev.2-ci.apk`.
- **dev.3 transactional WireGuard live activation is green on the Full BlazePwifi branch:**
  - WireGuard private key is generated/stored on-device with restrictive permissions; browser/API exposes only the public key.
  - Blaze-owned UCI network/firewall sections are used; existing LAN/WAN/EasyMode sections stay outside dev.3 ownership.
  - Unsafe routes are rejected before apply: default/full tunnel, overly broad routes, directly connected overlaps and current-admin-path capture.
  - Apply uses network/firewall/runtime snapshots, a detached watchdog and boot-time recovery.
  - Success requires interface start, firewall reload, a verified WireGuard handshake, and unchanged default/current management route signatures.
  - Failure restores the previous network/firewall/runtime state, including an older active Blaze WireGuard tunnel when updating it.
  - Remote admin uses a dedicated WireGuard-only HTTPS service with a restricted admin-only web root; the normal LAN admin/captive portal/Rental/Vendo surface is not exposed on the remote listener.
  - Remote Terminal permission is enforced server-side on the WireGuard admin path.
  - Console now exposes device public-key generation, staged profile save, Test & Apply, activation/handshake status and safe disable.
  - ZeroTier live activation remains staged-only in dev.3.
  - Exact branch workflow `37516557416` passed validation, browser runtime, Android build, Device Owner emulator, x86 QEMU, ESP8266/ESP32, Ruijie, required Orange Pi targets, update bundle and final candidate gate.
- **dev.4 Pisonet member metadata migration is green:**
  - export is verifier-free: no plaintext password, password hash/verifier, salt, KDF scheme or rounds are present;
  - strict portable `BLAZE_MEMBER_METADATA_V1` carries username, label/source metadata, enabled request, banked seconds and timestamps only;
  - import is preview-first and Apply requires Admin + CSRF + fresh password re-authentication;
  - preview tokens are TTL-limited, single-use, bound to admin session/IP and pinned to the central member revision;
  - collisions are explicit: abort, skip, or metadata-only update; no silent overwrite;
  - metadata-only collision updates preserve the existing central password verifier;
  - new members are created disabled with `reset_required` state and need a normal admin password reset before enable/authentication;
  - imports are transactional across member records, event history and global revision, with full rollback on injected mid-import failure;
  - duplicate usernames, malformed fields and oversized files/member sets are rejected;
  - the optional-empty-label member-store parsing bug was fixed across CRUD/auth/balance/transfer/public-list/snapshot/export paths;
  - exact application candidate `723c9c2191542e6f6867ee5fbbc31083590b49f2`, workflow `37527877646`, passed validation, migration regression, Playwright, Android build, Device Owner emulator, x86 QEMU, ESP8266/ESP32, Ruijie, required Orange Pi targets, update bundle and final candidate gate;
  - retained browser audit reports `member_metadata_export=true`, `member_import_preview=true`, `member_import_apply=true`, `dual_csrf_transport=true`, and `console_errors=false`.
- **dev.5 transactional ZeroTier live activation is green:**
  - stable ZeroTier identity is generated/stored on-device; browser/API exposes only node ID, never `global.secret`;
  - only Blaze-owned modern UCI section `zerotier.blazepwifi` is managed; legacy `.join` or foreign/custom network sections are refused safely;
  - the untouched stock `earth` sample is pruned only when still exactly default and unused;
  - Blaze network policy remains `allow_managed=1`, `allow_global=0`, `allow_default=0`, `allow_dns=0`;
  - apply requires ONLINE/TUNNELED node state, network OK, real interface, assigned IPv4, safe mesh routes, firewall/admin-listener success, and management/default-route survival;
  - ACCESS_DENIED, unsafe/overlapping/default routes, missing interface/address, listener/firewall failure, watchdog/reboot interruption and lost transaction ownership restore the previous state;
  - WireGuard and ZeroTier active transports are mutually exclusive;
  - disable is rejected from the ZeroTier path itself and preserves stable identity;
  - snapshots containing ZeroTier secret material are restrictive and deleted after success/rollback;
  - an existing valid `global.secret` is now a true no-op before snapshot creation, fixing a pre-transaction UCI mutation/line-reordering defect;
  - the transaction engine was rebuilt from the last clean sealed source after detecting a malformed duplicate tail; static validation again enforces one valid engine ending at the authoritative EOF marker;
  - retained browser audit reports `zerotier_identity_prepared=true`, `zerotier_live_apply=true`, `zerotier_safe_disable=true`, `wireguard_live_apply=true`, `member_import_apply=true`, and `console_errors=false`;
  - exact application candidate `29a3815e81c9bd7db54c8f60eb6f579c818f34ad`, push workflow `37540065074` and PR #25 merge-tree workflow `37540072921` both passed the full matrix.
- Full BlazePwifi dev.5 has zero changes under `profiles/standalone-rental`.
- No v0.5.3 production tag/release has been created.
- No production signing key was rotated or exposed.
- Frozen v0.5.2 release/tag and dedicated signing/recovery workflows remain unchanged.

## v0.5.3-dev.3 — BlazePisonet SoftTimer member authority

This is a **required architecture rule** for all future BlazePwifi + BlazePisonet SoftTimer work.

### Ownership rule

- **BlazePwifi Management Console is the central authority for SoftTimer member accounts whenever BlazePwifi integration is enabled.**
- Member creation, editing, enable/disable, password reset, banked-time adjustment, deletion/revocation and audit belong in **BlazePwifi Admin → Pisonet Members**.
- BlazePisonet SoftTimer must not maintain an independent authoritative member balance database while connected to BlazePwifi.
- SoftTimer may keep a signed/revisioned last-known-good **metadata** cache for display/discovery and resilience, but dev.3 does not distribute reusable password-verifier hashes to PCs. Central BlazePwifi member revision and banked-time ledger always win.
- Standalone SoftTimer deployments with no BlazePwifi server may continue using local-only member storage.

### Member data model

Central member records must at minimum carry:

- normalized member username / stable member ID;
- display name or optional label;
- enabled/revoked state;
- password verifier material only (never plaintext);
- banked seconds;
- monotonically increasing record revision;
- updated timestamp;
- last modifying actor/source;
- bounded idempotent member-event history for bank/restore/transfer operations.

Passwords must never be returned to the browser, SoftTimer, logs, exports or audit records. The console can reset a password, but cannot reveal the old one.

### SoftTimer synchronization contract

The BlazePwifi ↔ SoftTimer member integration must use the existing trusted controller relationship rather than anonymous captive-portal APIs.

Required behavior:

1. SoftTimer identifies itself with its configured BlazePwifi controller ID and signed controller request.
2. SoftTimer periodically requests a member snapshot/revision from BlazePwifi.
3. BlazePwifi returns only cache-safe member metadata: username/label/enabled state, password KDF salt/round count, banked balance, revision and timestamps. It does **not** return the stored password verifier/hash. SoftTimer derives a verifier transiently from the password entered by the member and sends only a nonce/controller-bound proof.
4. SoftTimer atomically replaces/updates its local member cache only after validating the signed response/revision.
5. When online/integrated, banked-time mutations are sent to BlazePwifi as idempotent events and BlazePwifi is the authority for the resulting balance.
6. Lost/retried requests must not duplicate banked time, restored time or transfers.
7. In dev.3, if BlazePwifi is unreachable, **central member authentication and all balance mutations fail closed**. Cached metadata may still be displayed, but it cannot authorize/spend banked time. A future explicit encrypted/offline-spend lease design may relax this only with collision-safe reservations.
8. When connectivity returns, the newest authoritative BlazePwifi revision replaces stale cached balance state.
9. BANK/RESTORE operations use a durable pending-event journal on SoftTimer. While an event is unresolved the local countdown is frozen, the station remains locked and new coin input is rejected.
10. BlazePwifi binds committed replay to the original controller ID + member + operation kind + event ID. SoftTimer can therefore recover an already-committed event after a crash without persisting the member password.
11. If BlazePwifi never received the original event, the pending event remains unresolved until the member re-enters the password; the retry must reuse the same event ID.

### Management Console requirements

Add a dedicated **Pisonet Members** page, separate from administrator accounts and hotspot device accounts.

Minimum console actions:

- list/search members;
- add member;
- edit label/name;
- enable/disable/revoke;
- reset password;
- view/set/add/subtract banked time;
- inspect revision / last update / source;
- view recent member events;
- transfer banked time between members;
- export/import member metadata without plaintext passwords — **implemented in dev.4 with reviewed preview, collision policy, fresh re-authentication and transactional rollback**.

Viewer role may read non-secret member status. Operator may create/edit ordinary member state and banked time within policy. Password reset, destructive delete/revoke and bulk import require Admin plus CSRF; high-risk bulk operations should require fresh re-authentication.

### Compatibility / migration

- Existing v0.3.0 SoftTimer local members must not be silently destroyed.
- Existing local SoftTimer members are still not silently auto-migrated.
- dev.4 provides an explicit metadata-only local→central migration/import workflow with reviewed username-collision classification and no silent overwrite.
- Password verifier/hash material is never imported through this workflow; new imported central members are disabled and require password reset before enable/authentication.
- SoftTimer remains able to operate in **Local Members** mode when BlazePwifi member authority is disabled.

### Scope guard

- Do **not** implement this by modifying `profiles/standalone-rental`. This belongs to Full BlazePwifi Management Console + BlazePisonet SoftTimer integration. Existing BlazeRental phone enrollment/member-independent rental accounting must continue to work unchanged.

### Validation gates for dev.3

- static shell validation for the member library/API;
- member CRUD/revision/idempotency tests;
- password-verifier non-disclosure test;
- browser Management Console member-flow test for current CRUD/balance/audit actions;
- SoftTimer build with warnings-as-errors;
- SoftTimer online sync / nonce-proof authentication / offline fail-closed authentication-and-balance test;
- duplicate bank/restore/transfer event test, including controller-bound crash replay without a stored plaintext password;
- full existing BlazePwifi regression matrix, including Android, ESP, Ruijie, Orange Pi and x86/QEMU gates;
- no production v0.5.3 tag/signing action from this development branch.

## Historical v0.5.1 maintenance target

The owner requested a maintenance release that eliminates full-system reflashing for ordinary feature/revision upgrades and adds safe rollback for BlazePwifi and BlazeRental.

Implemented on `blazepwifi-v0.5.1-implementation`:

- Transactional BlazePwifi overlay updater with exact SHA-256 verification.
- Configurable HTTPS update source, size bound, stability grace and rollback retention.
- Last-known-good snapshots before file replacement.
- Immediate health-check rollback and boot-health rollback guard.
- Manual rollback from Management Console → Updates & Recovery.
- Idempotent configuration migration; normal feature bundles do not overwrite persistent operator/session state.
- One-time v0.5.0 → v0.5.1 no-reflash bootstrap updater.
- Build-time `BlazePwifi-v0.5.1-update.tar.gz` generation.
- BlazeRental v0.5.1 version code `50100`.
- BlazeRental managed updater verifies SHA-256, package name and installed signing identity.
- Previous APK/version metadata retained; new build becomes stable only after a 30-second launcher health window.
- Known-good v0.5.0 rollback rescue is rebuilt from exact RC9 source `66e159b65b6d8fb5f74dd981dc73d46db7229adc` using recovery-only version code `50101`.
- Repeated failed boots while a Rental update remains pending can stage the configured rescue APK.
- Native Rental Admin update/check/rollback controls.
- Central Rental Update Manager in the BlazePwifi console.
- Locked v0.5.1 production signer workflow signs both current and rescue APKs with the exact existing certificate and refuses rotation.
- v0.5.1 release workflow supports validated prerelease publication if the locked signer remains unavailable.

Full firmware/sysupgrade remains reserved for base-system changes such as kernel, bootloader, partition/ABI or filesystem changes that cannot safely be delivered as an overlay.

## Current v0.5.1 release status

- GitHub Release: `v0.5.1` — **published prerelease**
- Release ID: `404404262`
- Release page: `https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.1`
- Exact validated candidate: `65f87d775793a1fdc09a9522cf752349f68c3b41`
- Validated build run: `37425063793` — **PASS**
- Validate/static/security/integration/stress: PASS.
- Transactional update/rollback regression: PASS.
- BlazeRental v0.5.1 update contract: PASS.
- Android APK build: PASS.
- Android Device Owner emulator: PASS.
- Browser, ESP8266, ESP32, Ruijie, x86 and required Orange Pi simulations: PASS.
- Final candidate gate: PASS.
- Release workflow run: `37426030884` — **PASS**
- Release target remains exact candidate SHA `65f87d775793a1fdc09a9522cf752349f68c3b41`.
- Update assets include:
  - `BlazePwifi-v0.5.1-update.tar.gz`
  - `BlazePwifi-v0.5.1-update-bootstrap.sh`
  - `BlazePwifi-v0.5.1-update-bootstrap.sh.sha256`
- Android validation/recovery assets include:
  - `BlazeRental-v0.5.1-TEST.apk`
  - `BlazeRental-v0.5.1-release-unsigned.apk`
  - `BlazeRental-v0.5.0-rescue-for-v0.5.1-TEST.apk`
  - `BlazeRental-v0.5.0-rescue-for-v0.5.1-release-unsigned.apk`
- Locked signing run `37425929657` failed safely at `Restore exact locked v0.4 production identity` because the exact keystore / `BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM` remains unavailable.
- The signing workflow refused certificate rotation. Therefore production `BlazeRental.apk` and signed rescue APK are intentionally absent.
- Locked production fingerprint remains:
  `C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`
- Canonical release log:
  `docs/handover/2026-10-06-v051-release-published.md`

## v0.5.1 main integration status

- BlazePwifi v0.5.1 is integrated into `main`.
- Published release candidate remains `65f87d775793a1fdc09a9522cf752349f68c3b41`.
- Published release build run: `37425063793` — PASS.
- Published release workflow: `37426030884` — PASS.
- Reconciled main integration SHA: `e081c6bdfc41d22ac07f918c4cbc62a745bca883`.
- Reconciled integration build run: `37426701445` — PASS, including Android Device Owner emulator, x86 QEMU and final candidate gate.
- Pull request `#14` — merged.
- Main merge commit: `1aa8926563e6dccb6a512a035e8f6f662b997d57`.
- Main merge tree: `f1c0194f8039577bad88a6e93b02d9b837e228c2`, exactly matching the green integration tree.
- Post-merge main build run: `37427339687` — PASS, including Android Device Owner emulator, x86 QEMU and final candidate gate.
- All 19 newer main-only standalone-rental/release files were preserved byte-for-byte.
- Superseded conflicting PR `#13` was closed without merging.
- GitHub Release `v0.5.1` remains pinned to exact candidate `65f87d775793a1fdc09a9522cf752349f68c3b41`; main integration did not retag or rewrite the release.
- Production Android signing remains blocked only by unavailable exact locked v0.4 signing material.

## Main branch integration status

- Full BlazePwifi v0.5.0 implementation is integrated into `main`.
- Conflict-resolved integration SHA: `09710a6d093f125a444c86bc686985edbfc89553`.
- Integration CI run: `37396023917` — PASS, including Android Device Owner emulator and final candidate gate.
- Pull request: `#12` — merged.
- Main merge commit: `06ddc5909b178d316f0f4d6fb8104f64da9a1be9`.
- The merge tree is exactly `d8fe2e6b6fca5ee3f619bc1d2e8ab35c4abcc850`, the same tree validated on the integration branch.
- All 16 main-only paths were preserved byte-for-byte, including the offline preview artifacts, handover logs, and unrelated Easymode encrypted-release files.
- Superseded conflicted PR `#11` was closed without merging.
- The `v0.5.0` tag/release remains pinned to validated RC9 candidate `66e159b65b6d8fb5f74dd981dc73d46db7229adc`; integrating code into main did not move or rewrite the release tag.
- Production Android signing remains intentionally blocked until the exact locked v0.4 signer is restored.

## Current v0.5.0 release status

- GitHub Release: `v0.5.0` — **published prerelease**
- Release ID: `403831689`
- Release page: `https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.0`
- Exact validated candidate: `66e159b65b6d8fb5f74dd981dc73d46db7229adc`
- Candidate branch: `blazepwifi-v0.5.0-rc9`
- Validated build run: `37326542666` — PASS
- Final candidate gate: PASS
- Release workflow run: `37327843195` — PASS
- Release-stage artifact: `11352224246`
- Tag `v0.5.0` points exactly to the validated RC9 commit.
- `RELEASE-MANIFEST.json`: `candidate_gate=passed`, `production_signed=false`, `signing_run_id=0`.
- Android release assets currently include:
  - `BlazeRental-v0.5.0-TEST.apk`
  - `BlazeRental-v0.5.0-release-unsigned.apk`
- A production `BlazeRental.apk` is intentionally absent until the locked v0.4 signer is restored.
- Locked signing run `37327439782` failed safely because `BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM` / exact keystore was unavailable; it refused certificate rotation. A second attempt on 2026-10-06 (`run_attempt=2`) reached the same protected restore step and failed for the same reason, again without altering the release or rotating the certificate.
- Locked production fingerprint remains:
  `C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`
- Canonical final release log:
  `docs/handover/2026-10-05-v050-release-published.md`

## Current v0.5.2 candidate status — 2026-10-06

- Exact candidate: `bf2992977fe8504d21b107df02826032c31d3a62`
- Exact build run: `37443570618` — **PASS**
- v0.5.2 LCM branding/alarm contracts: PASS.
- Android normal + v0.5.1 rescue APK build: PASS.
- Android Device Owner emulator: PASS.
- Transactional v0.5.2 update bundle: PASS.
- Browser, ESP, Ruijie, x86 and required Orange Pi simulations: PASS.
- Final v0.5.2 candidate gate: PASS.
- Release must be published from this exact candidate before production signing.
- Initial signing run ID must be `0`; Android assets remain TEST/unsigned until the later new-lineage signing step.

## Current v0.5.2 production release status — 2026-10-06

- GitHub Release: `v0.5.2` — **published production release**
- Release ID: `404545281`
- Exact release candidate: `bf2992977fe8504d21b107df02826032c31d3a62`
- Exact build run: `37443570618` — **PASS**
- Production signing run: `37448352082` — **PASS**
- Signing artifact: `11404278200`
- Production promotion/release run: `37448830953` — **PASS**
- Release title: `BlazePwifi v0.5.2 — LCM Branding & Rental Time Alarms`
- Release target remains exactly the green candidate; signing/recovery/docs commits did not retag the application.
- Release is no longer a prerelease.
- Production BlazeRental certificate lineage: `BlazeRental-production-lineage2`
- Permanent SHA-256 certificate fingerprint:
  `1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25`
- Production `BlazeRental.apk` SHA-256:
  `d0ad20bed00ea304db9bff45928542fed574070d416ed65b4fbf3d8ba23d7102`
- Production rollback-rescue SHA-256:
  `a1c8d759405842b85879c77e9525b1a6e9c4f6d62eb8bda9b0abc60fb899d513`
- Recovery A and Recovery B both successfully decrypted the sealed signer backup and restored a P12 matching the permanent fingerprint.
- Recovery A private key is retained in the owner's private ChatGPT Library under `/BlazePwifi Signing Recovery/`.
- Recovery B is the independent owner/offline recovery copy.
- GitHub stores only public recovery keys and AES-256-GCM encrypted signing material.
- `SIGNING_RECOVERY.md` is the permanent recovery entry point.
- The release includes signed main/rescue APKs, certificate/fingerprint, dual recovery assets, production Device Owner QR/provisioning assets, and correct release-level checksums.
- The original signing artifact checksum file referenced two temporary aligned APKs deleted before upload; all retained files verified correctly. The workflow bookkeeping was corrected in commit `1fd5720a101a3d88bbe05e70158736983fbbad6e` and the published release recomputed a clean release-level `SHA256SUMS`.
- The LCM production PNG is the clean 128×128 derivative of the user-supplied source and its Git blob is `19f1c2f843dca1f9f6e320ea0dbd94580f85e608`.
- Near End default: 10 minutes / 5-second ring.
- Urgent Add Credit default: 3 minutes / 10-second ring.
- Time's Up default: 00:00 / 15-second ring.
- Audible alarms use STREAM_ALARM, enforced non-zero minimum volume, optional DND override, and restore prior audio state after playback.
- Migration from the abandoned old v0.4 signer requires reprovision/factory reset. Once on v0.5.2 Lineage 2, all future production BlazeRental APKs must use this exact certificate.
- No older standalone release is to be newly production-signed.

## Current target

BlazePwifi is being developed as a complete PisoWiFi + Android rental-device platform with a full management console, customizable captive portal system, coin/Vendo controllers, vouchers, sales, networking/WAN/LAN/VLAN management, backups, multimedia, BlazeGames management, and BlazeRental Launcher3 integration.

## Current BlazeRental direction

Approved redesign direction:

- Rename the launcher/app from Rootless Pixel Launcher branding to **BlazeRental**.
- Use the approved LCM/BlazeRental icon family for APK/app branding and wider Blaze ecosystem branding where appropriate.
- Restore normal Launcher3 behavior instead of the current three-page rental replacement.
- Far-left page: BlazeRental / Insert Coin portal.
- Next page: Notifications.
- Then normal Launcher3 home pages.
- Swipe-up All Apps is allowed only while rental time is valid or `Use device as is` is enabled.
- Unpaid rental mode fails closed to the BlazeRental Insert Coin page.
- `Use device as is` must be available as a daily-driver mode and must not require BlazePwifi enrollment.
- Notifications page needs Clear All.
- On-device admin must be redesigned as a polished native Android management UI.
- QR scanner must preserve camera aspect ratio and use a stable scan frame.
- Rental Insert Coin appearance/sounds must be customizable from the on-device admin.

## Portal / management-console direction

- Core UI must not depend on Bootstrap, jQuery, CDN, or heavy framework runtimes.
- Factory Blaze portal is permanent/undeletable and acts as fallback.
- Portal Designer must support Add Portal Template and custom HTML/CSS/JS/media/sounds.
- LPB-style behavior should be supported through a compatibility layer without copying LPB visual design.
- Default portal must be child-friendly at first glance and expose richer safe network/device/system details when scrolled.
- Management Console should become a complete operating console, not a small admin page.
- Console richness includes Alerts, Scheduler/Automation, Announcements, Theme/Branding management, Audit Logs, Role-based Accounts, Import/Export, Template Sandbox/Safe Preview, API/Webhooks, Hardware Capability page, File/Asset Manager, Recovery/Fallback tools, Data Usage/Quota, Reports, Search/Quick Actions, Notes/Tags, and Multi-profile/Presets.
- Add a dedicated **Tools** module: ping, traceroute, DNS test, speed test, WAN reachability, port check, NTP test, Wi-Fi scan, interface diagnostics, controller tests, latency/jitter/packet-loss testing, safe local discovery, logs, service tools, storage cleanup, and diagnostics export.


## Management Console terminal / command tools

Approved design direction:

- Add a **Terminal / CMD** area to the Management Console.
- Do **not** expose an unrestricted web shell by default.
- Provide two levels:
  - **Safe Commands**: curated/allowlisted commands and guided tools for common admin tasks.
  - **Advanced Terminal**: optional owner-only shell with explicit enablement, re-authentication, timeout, audit logging, and strong rate/concurrency limits.
- Safe Commands should cover common operations such as:
  - ping, traceroute, nslookup/dig, route/ip status;
  - interface/WAN/LAN/VLAN status;
  - Wi-Fi scan/status;
  - storage/mount/USB status;
  - process/service status;
  - log viewing/tailing;
  - package/version checks;
  - network diagnostics;
  - controller diagnostics;
  - read-only hardware/runtime inspection.
- Dangerous/destructive actions should use dedicated Management Console controls or guarded command wrappers rather than raw arbitrary shell wherever practical.
- Advanced Terminal must be owner/admin-role restricted, disabled by default on Lite/public-facing deployments, and protected with:
  - fresh password re-authentication;
  - short-lived terminal session;
  - CSRF/session binding;
  - command audit history;
  - output/time limits;
  - idle timeout;
  - concurrent terminal/session limits;
  - brute-force/rate-limit protections;
  - no anonymous or portal-side access;
  - optional LAN-only/local-management restriction.
- Terminal access must never be exposed to captive-portal users.
- On constrained OpenWrt devices, prefer a small streamed command runner rather than a heavy full browser terminal emulator.


## Remote monitoring / remote management

Approved design direction:

- Add a dedicated **Remote Access / Fleet Management** section to the Management Console.
- The primary user goal is **true worldwide access**: the owner must be able to open and manage their BlazePwifi/PisoWiFi system from anywhere on the Internet (for example from mobile data, another city, or another country) without needing to be on the local LAN.
- The preferred UX is a normal browser-accessible remote console reached through the configured private overlay/VPN path, not direct public-WAN exposure of the admin page.
- Remote monitoring/management should work even when the BlazePwifi site is behind NAT/CGNAT, provided one of the supported outbound tunnel methods is configured.
- Do not hard-code a vendor, account, endpoint, address, key, subnet, route, or management scope. All remote-access parameters must be owner-configurable.
- Remote access is **disabled by default** until the owner explicitly configures it.
- When Remote Access is enabled, offer exactly two first-class modes:
  1. **WireGuard VPN — Recommended/default selection**
     - preferred for BlazePwifi because it is lightweight, OpenWrt-native/well-supported, owner-controlled, and suitable for site-to-site or outbound-to-hub management;
     - support a BlazePwifi node behind NAT/CGNAT by allowing it to initiate an outbound WireGuard tunnel to an owner-controlled hub/VPS/router;
     - configurable endpoint/FQDN, port, peer/public keys, optional preshared key, tunnel address, allowed IPs/routes, persistent keepalive, DNS, MTU, reconnect/health-check and management subnets;
     - private keys remain local and are never displayed after creation/export unless the owner explicitly rotates/reprovisions them.
  2. **ZeroTier — Easy-mesh alternative**
     - intended for simpler NAT/CGNAT traversal and multi-site mesh enrollment;
     - configurable Network ID, authorization state, managed IP/routes, local interface/firewall scope, low-bandwidth option where supported, and reconnect/health state;
     - no hard-coded ZeroTier account/network dependency.

- Monitoring and management permissions must be independently configurable:
  - Remote Monitoring only (read-only metrics/status);
  - Remote Management (configuration changes);
  - Remote Terminal (separate advanced permission, off by default).
- Remote-access scope should be configurable per service/module:
  - Dashboard/status;
  - alerts/events;
  - clients/sessions;
  - sales/reports;
  - backups;
  - portal/templates;
  - rental devices;
  - controllers;
  - network/WAN/LAN/VLAN;
  - system/firmware;
  - tools;
  - terminal.
- Add optional fleet-style status:
  - node name/site/location label;
  - online/offline;
  - last seen;
  - WAN health;
  - tunnel health/last handshake;
  - public/overlay/tunnel IPs where appropriate;
  - CPU/RAM/storage/temp;
  - active clients/sessions;
  - controller/rental-device health;
  - firmware/version;
  - alerts and backup status.
- Configurable heartbeat/refresh interval, offline-alert threshold, reconnect behavior, telemetry retention and alert severity.
- Remote management must bind to LAN/VPN/overlay interfaces only by default and must **not expose the Management Console directly to the public WAN**.
- Support configurable allowlists for remote management source addresses/subnets.
- Re-authentication should be required for high-risk actions such as firmware updates, factory reset, backup restore, credential/key changes and Advanced Terminal.
- Maintain complete audit logging of remote sessions and state-changing actions.
- Rate limits, session limits, timeouts and abuse controls apply equally to remote access.
- If the VPN/overlay fails, local LAN management and the captive portal must continue working normally.

## Networking / operations requirements captured

- Multiple WAN modes including Ethernet, WISP when Wi-Fi hardware is available, USB Ethernet, dual-WAN load balancing and failover.
- LAN/PisoWiFi AP modes including VLAN, second Ethernet, USB Ethernet, bridge/router modes.
- Voucher generator/designer/export.
- Rental settings and QR provisioning.
- Rental customization.
- Sales reporting.
- Device management.
- Manual/automatic backups with retention limits, download/import/restore.
- Sessions, rates, controllers, diagnostics, system/security and hardware-capability-aware controls.

## Wi-Fi portal multimedia / games direction

Approved portal additions:

- Wi-Fi portal may expose **Movies/Multimedia** and **Games** sections.
- These sections apply to the Wi-Fi portal, not the BlazeRental launcher unless explicitly added later.
- Multimedia page contents are entirely controlled by the administrator.
- Each media item can be configured as:
  - free to view, or
  - requires an active paid session with time actively running (paused time does not qualify).
- Add a **Multimedia Manager** to the Management Console:
  - detect removable USB storage when available;
  - allow supported internal/SSD/SD storage on larger builds;
  - choose multimedia storage target;
  - upload/import/delete/rename media;
  - folders/categories/collections;
  - poster/thumbnail/metadata management;
  - free-vs-paid-session access policy per item/category;
  - storage capacity/free-space/health view;
  - rescan/index storage;
  - safe eject/remount where supported;
  - media preview;
  - browser-native streaming with HTTP range support where practical;
  - no mandatory server-side transcoding on Lite targets.
- Add a **BlazeGames Manager** using the existing BlazeGames/offline arcade-emulator HTML project:
  - manage ROMs/content made available to users;
  - add/remove/enable/disable games;
  - categories/favorites/order/cover art/metadata;
  - storage target selection;
  - free-vs-active-session access policy;
  - emulator/core compatibility metadata;
  - per-game launch/test;
  - save-state/storage policy where supported;
  - keep Lite targets lightweight.
- Only administrator-supplied/licensed media and ROMs should be distributed; BlazePwifi should not ship copyrighted third-party content by default.

## Security / abuse-resistance requirements

The system must be designed to strongly resist brute-force and denial-of-service abuse, while avoiding claims of being literally “brute-force free” or “DDoS proof.”

Required controls include:

- escalating admin/login lockouts and rate limits;
- persistent lockout state where appropriate;
- strong password verification and secure secret storage;
- role/session controls, CSRF protection, nonces on state-changing APIs;
- request/body/upload size limits;
- connection/concurrency limits suitable for the hardware;
- per-client/IP/session token-bucket throttling for sensitive endpoints;
- login/API backoff and abuse detection;
- upload quotas and storage quotas;
- bounded logs and bounded backup/media retention;
- timeouts against slow/idle connections;
- fail-closed rental and policy behavior;
- static asset caching and lightweight portal rendering for constrained devices;
- audit/security event logging;
- safe recovery path for the owner.

## v0.5.0 implementation state

Implementation resumed by explicit owner instruction on 2026-10-05.

Current branch: `blazepwifi-v0.5.0-implementation`

Completed in the first v0.5 launcher milestone:

- Version bumped to 0.5.0 / Android versionCode 50000.
- User-visible Rootless Pixel/Launcher3 branding replaced with BlazeRental.
- Approved LCM icon added and wired as the APK launcher icon.
- Added one authoritative `canUseDevice()` gate: unrestricted OR valid paid lease.
- Added `BlazeLeftPanel` using Launcher3 custom-left content rather than deleting normal workspace pages.
- Unpaid rental state blocks leaving Blaze content for normal Home.
- Paid/unrestricted state restores normal Launcher3 chrome/interactions.
- Notifications gained Clear All support.
- First setup now offers `USE DEVICE AS IS · NORMAL LAUNCHER` without BlazePwifi enrollment.
- Legacy Google overlay is disabled so Blaze owns the custom-left gesture surface.

Next: complete v0.5 tests/emulator flow, QR scanner/native admin polish, rich Management Console/portal modules, then exact-SHA build and v0.5.0 release staging/publish.

## Last validated application candidate

BlazePwifi v0.5.0 RC9:

- Candidate SHA: `66e159b65b6d8fb5f74dd981dc73d46db7229adc`
- Build run: `37326542666` — PASS
- Candidate gate: PASS
- Android Device Owner emulator: PASS
- Browser/platform simulations: PASS
- Published as GitHub prerelease `v0.5.0`.

Previous v0.4 validated candidate remains `d2ee5e0c0493500ce6a0578b9cad5da0775be65e` with build run `37287301792`.

Do not replace or relabel the v0.5 TEST APK as production-signed. Production Android upgrade compatibility requires the existing locked v0.4 signing certificate.

## Latest preview artifact

An offline single-file Management Console + PisoWiFi Insert Coin + BlazeRental Insert Coin UX mockup was packaged as:

`preview/BlazePwifi_Offline_Management_Console_Preview.zip`

Mock login:

- username: `admin`
- password: `blaze1234`

This is a design mockup only and does not change production behavior.

## Resume rule

Before continuing implementation in a future chat:

1. Read this file.
2. Read the newest file in `docs/handover/`.
3. Inspect the current Git history and active implementation branch.
4. Reconcile repository state with these approved decisions.
5. Do not discard or redesign approved decisions unless the owner explicitly changes them.

## Logging rule

Update this handover at meaningful state changes: requirements, decisions, code/config changes, commits, tests, failures, fixes, workflow/build/release results, artifacts, blockers and exact next steps. Do not log every tool call.

### Mandatory success logging

Every successful milestone must also record:

- What changed and why.
- Exact files/areas touched.
- Commit SHA(s).
- Tests/audits performed.
- Successful workflow/build/release IDs when applicable.
- Any remaining known risks or limitations.
- Exact next recommended action.
- A ready-to-copy **Audit & Reconcile prompt** for a new chat.

Use this default prompt structure and specialize it to the latest milestone:

```text
@GitHub Reconcile and continue the BlazePwifi project from the repository state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read the newest file under experiment/openwrt/BlazePwifi/docs/handover/.
3. Inspect the recent Git history, current implementation branch, relevant workflow results, release/assets, and files changed by the latest milestone.
4. Audit the latest successful change instead of assuming it is correct. Check for regressions, incomplete wiring, security/UX conflicts, stale documentation, and mismatches with approved requirements.
5. Reconcile repository state with the approved project target and decisions in the handover logs.
6. Preserve completed/approved decisions unless the owner explicitly changed them.
7. If the latest success has a test/build/release artifact, verify the exact SHA/run/artifact before building on top of it.
8. Continue from the exact NEXT ACTION recorded in the newest handover log.
9. Update PROJECT_HANDOVER.md and add a new dated handover log after every meaningful success, failure, blocker, or design change.
10. For every successful milestone, include a new Audit & Reconcile prompt in the handover log for the next chat.
```

Failures should also be logged when meaningful, including reproduction/evidence, suspected cause, what was tried, and the safest next action.
