<!-- PHX-HARDWARE-20261115-COIN-JOURNAL-RECOVERY-POST-GATE:START -->
> **PHX-HARDWARE 2026-11-15 (Asia/Manila), LAB ONLY.** Own branch [DRAFT #293](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/293) based on unmerged DRAFT #283. At source commit [`c7823f7f409c`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c7823f7f409c1ad2fd483a5d303555f6a837d6b2), both ESP variants refuse boot admission if any pending journal candidate is corrupt/unreadable or more than one `/pending.dat`, `/pending.new`, `/pending.bak` coexist. On ambiguous state they preserve the bytes untouched; `journalRecoveryRequired` blocks raw GPIO coin pulses, relay/LED, pending saves and clears. Valid one-file journals retain evidence without boot-time rename. Nonce/target are validated using bounded `memchr` NUL searches, not unbounded `strlen`. The owned `PENDING_JOURNAL_AMBIGUITY.md` and source-extracted C++ host lab cover 16 cases per board. Follow-up source adds `canAttemptCoinPost()` to both sketches so failed flash saves cannot nevertheless POST RAM-only coins. Owned `COIN_POST_DURABILITY_GATE.md` and a source-extracted C++ test cover that new guard. This header is append-only provenance; all previous handovers below preserved.
> **Actual verified prior tests:** [#43653481980](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653481980) **COMPLETED SUCCESS** (22 original quarantine + 14 mount + 32 ambiguous boot = 68/68 software host tests), latest completed source sha `466a23837bcf85061a234b83599b9d0f02db1a82`; prior full build [#43653482006](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653482006) was still queued/in progress at checkpoint time. New dispatch helper and docs need **new exact-head CI**; do not inherit previous green tests. No physical flash, 150 power-cuts, 30-device soak, signed receipts/ACK, protected witness, safe money migration, release authority or deployment validated. **NO-GO for production**.
> **Next:** QA independently review source and physical noncustomer cases, CORE author crypto event-bound paid receipt ACK/replay contract, MASTER reconcile branch migration to COE under roles, RELEASE validate new full board workflow and artifact hashes. Do not merge, flash customer hardware or promote a release.
<!-- PHX-HARDWARE-20261115-COIN-JOURNAL-RECOVERY-POST-GATE:END -->

<!-- PHX-HARDWARE-20261115-NONDESTRUCTIVE-MOUNT:START -->
> **PHX-HARDWARE / software LAB / 2026-11-15 Manila / no production authorization.**
> DRAFT [PR #293](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/293), stacked on open #283, source [`354a303373b1e108f0f62219a3bbcba8b335e6da`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/354a303373b1e108f0f62219a3bbcba8b335e6da): both ESP8266 and ESP32 coin controllers now use non-destructive LittleFS mount; ESP8266 `begin()` no longer invokes `LittleFS.format()` after mount failure, and ESP32 replaces automatic `begin(true)` with `begin(false)`. Shared `initPendingStore()` logs a critical recovery warning, leaves `fsReady=false`, refuses `loadPending()`, and the existing relay/coin output gate remains OFF. Never format potential unpaid coin evidence as routine boot recovery. A new LAB `journal_mount_failclosed_lab.py` extracts the actual board firmware mount and output functions, compiles each with C++17 fake LittleFS and tests failure, successful mount and disabled output cases. A separate operator note `JOURNAL_MOUNT_RECOVERY.md` explains safe handling. NO hardware or user/customer devices operated.
> **Confirmed focused CI:** [run #43643397940](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43643397940) **COMPLETED SUCCESS**, job `132595675413`, real source-extracted C++: preexisting 22/22 quarantine cases plus new 12/12 mount/output cases; 34/34 total. The full build [#43643397850](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43643397850) was **RUNNING/QUEUED** when this checkpoint was written; inspect its final exact-head outcome before claiming ESP board compilation success. Focused host fake filesystem tests do not constitute flash wear, power-loss or relay electrical acceptance.
> **NEXT:** Review exact SHA source; classify full Arduino ESP8266+ESP32 build. PHX-QA independently reproduce the no-format/failure-output source checks and inspect quarantine/pending journal power-cut transitions; PHX-RELEASE reviews focused workflow and image handling; PHX-CORE resolves register/poll authentication response signature. Production admission, migration, keys, signer/witness, #31/#32/#34/#43, 150 *real* noncustomer power-cuts and 30-device 24-hour soak remain **NO-GO**.
<!-- PHX-HARDWARE-20261115-NONDESTRUCTIVE-MOUNT:END -->

<!-- PHX-HARDWARE-20261115-QUARANTINE-READBACK:START -->
> PHX-HARDWARE DRAFT / LAB ONLY, 2026-11-15. Based on evolving draft PR #283 source `a87567291e80006f3f30cea81fc20e8b299b95e8`, NOT a merge into shared Phoenix development. The upstream PR #283 already handles open/write/size failures without clearing pending coins; the older isolated experiment `phoenix/hardware-quarantine-failclosed-20261115@e2aa3dec` was superseded and must not be cherry-picked. This branch `phoenix/hardware-quarantine-byte-readback-20261115` adds exact appended-byte readback to both firmware sketches (code commit `18d577ebacc81912ad025b76ee89eb31952f836c`) to catch equal-length corrupt writes that size-only checks miss. A source-extracted C++17 fault-injection harness (11 scenarios/board) and a focused draft-PR GitHub workflow (`bdbb02e505b50a2efd00a1625a96fb507b7361d5`) are staged; NOT TESTED until actual CI execution. Check `experiment/openwrt/BlazePwifi/docs/handover/2026-11-15-hw-quarantine-byte-readback.md` for evidence and next action. No coin/relay GPIO, CORE financial logic, production keys, flashing or releases changed.
> RELEASE NO-GO: signed controller response format and antirollback witness still unresolved; power-cut and soak tests #34, financial #31/#32, protected witness #43, v1→v2 migration and hardware acceptance are absent. This main-based draft differs from the later full Phoenix development branch; the advanced `docs/handover/CURRENT_STATE.md` and `CHANGE_LEDGER.md` are not present on this branch. Do not import those massive unrelated histories without MASTER integration approval.
<!-- PHX-HARDWARE-20261115-QUARANTINE-READBACK:END -->

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

**2026-11-15 exact-head Full CI feedback — NO production success claim:** Original draft HEAD `40658e2b9ff88bf61c04e77930e84d47f40b78bf` focused source-extracted host run [#43635316939](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43635316939), job 132570723766 **COMPLETED SUCCESS: 22/22 synthetic cases**, but broader [Full run #43635316868](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43635316868) reached pre-existing `v05_firmware_hardening_test.sh` parity guard and reported missing literal `after==before+(size_t)len`. The new byte-verified code preserved the size equality semantically but expressed it as `verify.size()==...`; this is a source/QA contract mismatch, not a license to remove the safety test. Current follow-up restores explicit `size_t after=verify.size(); bool verified=after==before+(size_t)len && verify.seek(...)` before the byte comparison on BOTH sketches; neither existing strict assertion nor byte integrity check is bypassed. **New exact-head full and focused verification required**; do not inherit previous greens. Hardware/power-cut/money remains NO-GO.

## 2026-11-17 UTC06 — one-shot attempt-marker harness compatibility

At #315 exact source head `0ad3c0146ce473a9fb77523cbacd626ba1c78cd7`, the new one-shot `/pending.attempt` marker added `pendingPostAttempted` to the production `canAttemptCoinPost()` gate. The focused hardware-owned quarantine orchestrator still used its prior C++ stub and failed to declare/reset that state. Exact focused run [44027835302](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44027835302), job `133852350930`, failed at compile with `pendingPostAttempted was not declared`; no runtime test executed. The same head's target build workflow [44027835329](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44027835329) passed ESP8266, ESP32, Orange Pi Zero 3, Ruijie, x86_64 and returned optional targets, but its Full validation failed in the QA-owned `tests/v060_esp_poll_intake_guard.py` extractor: the extracted production loop references `pendingPostAttempted`, `markPendingPostAttempt()`, and `acceptPollResponse()` without extracting/declaring them. PHX-HARDWARE did not edit QA-owned tests.

This activation updates only the hardware-owned `quarantine_readback_lab.py` stub to declare/reset `pendingPostAttempted` and to clear it only in the stub's successful disposition path, matching the production gate state. The separate `pending_attempt_marker_lab.py` continues to compile and fault-inject the actual production marker/read/load/clear/gate functions. New exact-head focused CI is pending; no pass is claimed yet. PHX-QA must independently repair its canonical extractor and rerun Full validation.

No firmware behavior, shared API, financial source, QA-owned test, release workflow, or production state changed. No flash, reset, live coin, money, migration, merge, release, or deployment occurred.

## 2026-11-17 UTC06 — one-shot marker harness dependency alignment

At #315 head `11454643a7444df8e54f301ce0ccf2ec0d14ab1d`, the focused workflow [44028688657](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44028688657), job `133855092803`, failed in the hardware-owned `pending_journal_recovery_lab.py`: the new production `loadPending()` references `samePendingRecord()` and the new `clearPending()/savePending()/canAttemptCoinPost()` state references `pendingPostAttempted`, which the old harness did not extract/declare. The Full build [44028686420](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44028686420), validation job `133855087098`, separately failed in QA-owned `v060_esp_poll_intake_guard.py` for missing `pendingPostAttempted`, `acceptPollResponse()`, and `markPendingPostAttempt()` in its extracted-loop harness.

Follow-up hardware-owned test-only commits updated `pending_journal_recovery_lab.py` to declare the one-shot state and extract `samePendingRecord()`, updated `pending_write_readback_lab.py` for the new save gate, and added an explicit attempted-marker denial case to `coin_post_gate_lab.py`. Exact focused run [44028990570](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44028990570), job `133856072612`, **PASS**. Its logs show quarantine 17/17 per board, poll response 11/11 per board, root JSON 13/13 per board, register-config 7/7 per board, pending attempt-marker 19 cases per board, mount 7/7 per board, and the combined hardware orchestrator completed successfully. The marker lab printed an incorrect denominator `19/16` and stale aggregate `32/32`; this documentation/test-output-only update corrects them to `19/19` per board and `38/38` total. A fresh focused run at the new exact head is pending.

Full run [44028990577](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44028990577) remains **NOT GREEN**: QA-owned validation job `133856107226` failed in Controller protocol parity because its loop extractor still omits `pendingPostAttempted`, `acceptPollResponse()`, and `markPendingPostAttempt()`. ESP8266 compile and one optional target completed PASS; remaining platform jobs were still running at the last observation. PHX-HARDWARE did not modify QA-owned tests.

No runtime firmware, shared API, finance, release workflow, or production state changed in this follow-up. Physical flash durability, coin electrical acceptance, power cuts, soak, signer/witness, migration and independent release acceptance remain NOT TESTED/BLOCKED.

## 2026-11-17 UTC06 — exact-head marker summary guard

The focused orchestrator now captures the one-shot marker lab output and asserts exactly two `PENDING_ATTEMPT_MARKER_PASS 19/19` board summaries plus the aggregate `38/38 total` line. This prevents a future harness from silently reporting stale denominators. The exact PR #315 head at this test is `ca2275bd4998197c6450d8a00cae367b255335d0`.

- Focused [run 44029841923](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44029841923), job `133858849902`: **COMPLETED SUCCESS at exact HEAD ca2275bd4998197c6450d8a00cae367b255335d0**. The source-extracted matrix passed: quarantine 17/17 per board; poll response 11/11 and strict JSON 13/13 per board; debounce/poll-window 8/8 per board; register-config 7/7 per board; attempt marker 19/19 per board (38/38 total); mount 7/7 per board; pending recovery 16/16 per board; pending clear 11/11 per board; pending write/readback 22/22 per board; coin POST gate 10/10 per board. All fake-filesystem/host simulations only.
- Full [run 44029841759](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44029841759), validation job `133858850165`: **FAILED** at QA-owned Controller protocol parity. Its extracted-loop harness still lacks `pendingPostAttempted`, `acceptPollResponse()`, and `markPendingPostAttempt()` for both boards. Other target jobs were still in progress at the last observation; no Full success is claimed.

PHX-QA must repair its owned `tests/v060_esp_poll_intake_guard.py` and independently rerun Full validation at the current #315 head. No QA-owned source was changed. No runtime firmware change, physical flash, real coin, relay, power cut, electrical pulse, soak, production migration, signing, merge, release or deployment occurred.

## 2026-11-17 UTC06 — coin POST gate aggregate count correction

The coin POST gate lab has 10/10 cases per board after the explicit one-shot-marker denial case was added; its previous aggregate banner still said 18/18. Corrected the banner to `20/20` total. The focused orchestrator workflow reran the actual ESP8266/ESP32 source-extracted suite at exact #315 head `b06034215439ff3264d273d20e0f851fdafc2366`.

- Focused [run 44030370904](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44030370904), job `133860589530`: **COMPLETED SUCCESS at exact HEAD b06034215439ff3264d273d20e0f851fdafc2366**. Logs confirm quarantine 17/17 per board; poll 11/11 and strict JSON 13/13 per board; debounce/poll-window 8/8 per board; register-config 7/7 per board; pending marker 19/19 per board (38/38 total); mount 7/7 per board; pending recovery 16/16 and pending clear 11/11 per board; write/readback 22/22 per board; coin POST gate 10/10 per board (20/20 total). Fake LittleFS/source-extracted host checks only.
- Full [run 44029841759](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44029841759) **COMPLETED CANCELLED** after validation job `133858850165` FAILED in QA-owned Controller protocol parity. The extractor still omits `pendingPostAttempted`, `acceptPollResponse()`, and `markPendingPostAttempt()`; ESP8266 compiled successfully, several Orange Pi targets passed, and ESP32/Ruijie/x86/Android plus simulations/release jobs were cancelled. No Full success.

No runtime firmware changed in this activation. PHX-QA still owns the failing extractor. No physical coin/relay/power-cut/electrical/soak test, production migration, signer, merge, release or deployment occurred.


## 2026-11-17 UTC07 — coin POST disposition default-deny (P0 financial integrity)

At the pre-fix #315 source head \`c86fd327d96455214d2ec0027d1f2fe2b394ce87\`, the ESP8266 and ESP32 loops accepted any response byte string containing \`"ok":true\` and called \`clearPending()\`. The same response could contain a top-level denial plus a nested or quoted positive decoy (for example \`{"ok":false,"detail":{"ok":true}}\`). The hardware-owned source-extracted poll lab reproduced this wiring defect: focused run [44037582162](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44037582162), job \`133884082616\`, failed on both boards with \`COIN_POST_ACK_GUARD RED\`. The parser-only root-status cases passed 13/13; the production coin POST path was still using substring search.

A second test-first commit \`c574511d50f2acf0b54271888ad89f1a9ac46186\` required an authenticated event-disposition guard before either pending clear or quarantine. Focused run [44038005945](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44038005945), job \`133885469359\`, failed because the production verifier did not yet exist. This was the expected RED.

**Source correction at \`79ea039a1f7fe15d471a1e80e33171ff1db615da\`:**
- Both sketches now call \`coinPostDispositionVerified(response, pendingNonce, pendingTarget, pendingPulses)\` before any response-driven \`clearPending()\` or \`quarantinePending()\`.
- The helper intentionally returns \`false\` for every response. The current firmware \`post()\` uses plain \`http://\` with \`WiFiClient\`; there is no approved event-bound authenticated receipt/negative-disposition contract in the producer/consumer pair. Neither root \`ok:true\` nor an error string is financial authority.
- An unauthenticated or ambiguous response now sets \`journalRecoveryRequired\`, leaves the pending record and \`/pending.attempt\` marker intact, denies automatic replay, and leaves logical outputs disabled.
- The existing strict root-level \`ok:true\` parser remains a structural check only, behind the future verifier. It is not a receipt signature or TLS substitute.
- No controller API, finance/ledger source, shared schema, QA-owned test or RELEASE-owned workflow was changed.

**Focused exact-head CI:** [run 44038183753](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44038183753), job \`133886056475\`, **COMPLETED SUCCESS at exact source SHA \`79ea039a1f7fe15d471a1e80e33171ff1db615da\`**. Both ESP source-extracted host suites passed:
- coin disposition default-deny: 4/4 per board;
- poll-response cases: 11/11 per board;
- strict root JSON: 13/13 per board;
- poll-window guard: 9/9 per board;
- blocking-poll relay-inhibit: 1/1 per board;
- register-config denial: 7/7 per board;
- quarantine: 17/17 per board;
- attempt marker: 19/19 per board;
- mount/output: 7/7 per board;
- pending recovery: 16/16 per board;
- pending clear: 11/11 per board;
- pending write/readback: 22/22 per board;
- coin POST gate: 10/10 per board.

All of these are source-extracted C++ host/fake-LittleFS simulations, not physical flash or financial acceptance.

**Full validation remains FAILED:** PR run [44038183730](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44038183730), validation job \`133886169030\`, and push run [44038177403](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44038177403), validation job \`133886148625\`, both fail in the QA-owned controller poll-loop extractor. It extracts \`loop()\` without the complete dependency set: \`pendingPostAttempted\`, \`acceptPollResponse()\`, \`markPendingPostAttempt()\`, \`coinPostDispositionVerified()\`, and \`pollJsonTopLevelTrue()\`. PHX-HARDWARE did not edit QA-owned \`tests/v060_esp_poll_intake_guard.py\`. At the latest observation the push ESP8266 job passed and several target jobs passed, while ESP32/x86/Android and remaining PR target jobs were still running; no Full success is claimed. Production import/sign/publish jobs were skipped.

**Required cross-role contract:** PHX-CORE must define an event-bound authenticated coin receipt and negative disposition binding controller identity, request nonce, event nonce, target, pulse count, disposition, unique receipt ID, freshness/expiry and key version, including idempotency/replay semantics and canonical serialization. PHX-QA must publish independent positive/negative golden vectors and power-loss/replay cases. PHX-MASTER must approve the contract. Only then may PHX-HARDWARE replace the default-deny helper with a real verifier. Until that happens, coin POST disposition remains intentionally disabled and this branch is not operationally accepted.

No flash, reset, live coin, relay bench, 150 power cuts, 30-device soak, electrical pulse test, production migration, signer provisioning, merge, release or deployment occurred. **PRODUCTION NO-GO.**


<!-- PHX-HARDWARE-20261117-QUARANTINE-TIMESTAMP-VALIDATION:START -->
## PHX-HARDWARE — quarantine-log timestamp validation (2026-11-17 UTC07)

**Defect reproduced:** the prior inspectQuarantineLog parser accepted any token after TIME=. A complete-looking line with a matching PULSES/NONCE/TARGET/REASON identity but a nonnumeric timestamp could be counted as an existing quarantine record; quarantinePending would then clear the pending coin record without a valid firmware-generated record.

**Test-first RED:** [run #44041100586](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44041100586), job 133895620908, test-only SHA af0ee82becb2a005c9a2ffc16d8d79e7c6a91b5b. The source-extracted C++17 fake-LittleFS lab failed at scenario 17 on the malformed timestamp case.

**Source correction:** commit efe8ee83d521139a3e3f0c8eaf60b29a9f9e4d75 updates both ESP sketches. inspectQuarantineLog now accepts only canonical decimal uint32 millisecond timestamps (1–10 digits, no leading zero except zero, overflow checked). Invalid/overflowed timestamps fail log inspection, latch journalRecoveryRequired through the existing append path, retain pending evidence and deny automatic POST retry. No receipt/API/finance/crypto contract changed.

**Exact-head focused CI:** [run #44041398477](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44041398477), job 133896584393, exact SHA efe8ee83d521139a3e3f0c8eaf60b29a9f9e4d75 — **SUCCESS**. Quarantine readback: 19/19 scenarios per board, 38/38 total. Existing poll/register, pending-marker, mount/output, journal-recovery, pending-clear, write/readback and coin-POST-gate labs also passed. Logs explicitly retain SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_VERIFIED=0 and FINANCIAL_PRODUCTION_AUTHORIZED=0.

**Full workflow:** [run #44041398463](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44041398463), validation job 133896701236 — **FAILED**. The QA-owned extracted-loop harness omits pendingPostAttempted, acceptPollResponse(), markPendingPostAttempt(), coinPostDispositionVerified() and pollJsonTopLevelTrue(). PHX-HARDWARE did not modify QA-owned tests or workflows. Several target jobs were still running at checkpoint time; no Full success is claimed.

Only the narrow hardware handover and this project ledger were updated. CURRENT_STATE.md and CHANGE_LEDGER.md are not present on this branch; no historical branch was imported to create them. No physical flash, relay/coin test, power-cut trial, soak, live payment, migration, signer provisioning, merge, release or deployment occurred. **PRODUCTION NO-GO.**
<!-- PHX-HARDWARE-20261117-QUARANTINE-TIMESTAMP-VALIDATION:END -->

<!-- PHX-HARDWARE-20261117-POLL-AUTHORITY-DENY:START -->
## PHX-HARDWARE — poll admission remains denied pending approved contract (2026-11-17 UTC08)

**Master contract:** the live Architecture Contracts §6.3 at Master PR #288 head 47f2f6e9107f58902396d5731cfcd77b80598eb5 states that the current poll producer/consumer signature is only a derived candidate: no shared golden vector has been independently executed, and configured-key admission remains fail-closed until CORE publishes the canonical producer and QA verifies both sides at pinned SHAs.

**Test-first RED:** test-only commit 91b0e67c87ead7df0b9a6c783f10bdf2de0a7a00 introduced a positive-looking provisioned-key candidate response that must not enable intake, but its first C++ JSON literal was over-escaped; run 44050812024 is a harness compile failure, not valid RED evidence. Test-only correction 491cd094e77c264b2c8053aff0c59913f0faa229 uses a raw JSON literal. Focused RED run [44051036806](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051036806), job 133928606170, then failed at the new default-deny assertion on both boards as expected; existing quarantine tests passed 19/19 per board.

**Source correction:** both ESP sketches now make acceptPollResponse() explicitly clear insertMode and activeTarget and return DENY. The unapproved derived SHA construction is no longer used to authorize relay/coin intake. No shared API, CORE financial source, remote configuration, receipt/disposition, or QA-owned file was changed.

**Scope:** this is a safety hold, not a replacement protocol. CORE must publish the canonical producer/consumer contract, including freshness and canonical serialization; QA must approve positive/negative golden vectors at pinned source SHAs; MASTER must approve before HARDWARE can implement a verifier. Until then, poll-based coin admission remains disabled.

No flash, reset, live coin, relay bench, physical power cut, 30-device soak, electrical pulse test, migration, signer provisioning, merge, release or deployment occurred. **PRODUCTION NO-GO.**
<!-- PHX-HARDWARE-20261117-POLL-AUTHORITY-DENY:END -->

**Exact-head focused GREEN:** [run 44051446853](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051446853), job 133930014829, exact PR head 3c2ccc09dcc0d2eab01c1bdaae5aa7548f245798 — SUCCESS. Both ESP8266 and ESP32: poll-response fail-closed 11/11, strict root JSON 13/13, coin POST ACK root status 4/4, coin disposition default-deny 4/4, register-config denial 7/7. Quarantine 19/19 per board, attempt marker 19/19 per board, mount/output 14/14 total, boot recovery 32/32 total, pending-clear 22/22 total, pending write/readback 22/22 per board, coin POST gate 20/20 total. All are source-extracted host/fake-LittleFS simulations.

**Full validation:** [run 44051446855](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051446855), validation job 133930149201 — FAILED in QA-owned experiment/openwrt/BlazePwifi/tests/controllers.sh, which still requires an active poll signature check in the firmware. That expectation conflicts with Master Architecture Contracts §6.3: the current response_sig construction is unapproved and coin admission must remain fail-closed. PHX-HARDWARE did not edit QA-owned tests. The previously observed v060_esp_poll_intake_guard.py extractor omissions remain an independent QA blocker; this run stopped earlier in controllers.sh, so the extractor was not reached. ESP8266 target compilation passed; ESP32 and several platform jobs were still in progress at the latest observation. No Full success is claimed.


## Final exact-head reconciliation — 2026-11-17 UTC09

Final PR head before this documentation-only checkpoint: 9c30d8c97763b610c4ab2d0df0168b4ace9cf8a3. Focused [run 44051895971](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051895971), job 133931499416, completed SUCCESS at that exact head. Both ESP boards passed poll-response fail-closed 11/11, strict root JSON 13/13, coin POST ACK root 4/4, disposition default-deny 4/4, register-config denial 7/7, quarantine 19/19 and pending-attempt marker 19/19. All tests are source-extracted host/fake-LittleFS simulations.

Full [run 44051896075](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051896075) at the same exact head is now COMPLETED FAILURE. Validation job 133931629492 failed in QA-owned tests/controllers.sh because it requires an active poll signature check. This is incompatible with Master §6.3 default-deny; do not restore the unapproved candidate to satisfy the test. The separate v060_esp_poll_intake_guard.py extractor issue remains unresolved and was not reached. ESP8266, ESP32, Android, Ruijie, x86_64 and all returned Orange Pi target jobs completed PASS. Production import/sign, update bundle, v0.4 simulations/candidate gate and release publication were skipped.

Final status remains SIMULATED / CI VERIFIED only. Physical relay/coin acceptance, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain unproven. PRODUCTION NO-GO.


## PHX-HARDWARE — quarantine requires a matching durable attempt marker (2026-11-17 UTC09)

Both ESP sketches now require a valid /pending.attempt record bound to the current pending pulse count, nonce and target before quarantinePending() can append a rejected-event record or clear pending evidence. Missing, corrupt, mismatched, unattempted, unready or out-of-range state latches recovery and denies the disposition before filesystem mutation. The existing marker is written and read back before the only coin POST; failed quarantine append leaves it intact, and the existing boot loader treats a matching marker as ambiguous/reconciliation-required.

Test-first RED: exact-head focused run [#44053916296](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44053916296), job 133938244153, failed on both boards at SOURCE_QUARANTINE_FAIL scenario=19 when the attempted-state flag was absent. Final exact-head focused GREEN: [#44054509206](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054509206), job 133940278029, exact PR HEAD 4602386add8150b37fdcf8252b68bf27d95bb3d9: quarantine 23/23 per board; poll/default-deny, register-config denial, attempt-marker 19/19 per board, mount/output 14/14, boot-recovery 32/32, pending-clear 22/22, write/readback 22/22 per board, and coin-POST gate 20/20 passed. Host C++/fake-LittleFS only.

The current coinPostDispositionVerified() remains default-deny, so this guard does not authorize coin disposition or re-enable paid intake. Full build run [#44054501269](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054501269), validation job 133940390771, FAILED in the QA-owned tests/controllers.sh because it still requires an active poll signature check, contrary to Master Architecture Contracts §6.3. PHX-HARDWARE did not edit QA-owned tests/workflows.

This is source-level fail-closed evidence only. Actual flash durability, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain NOT TESTED/BLOCKED. No flash, reset, live payment, merge, migration, signing, release or deployment.


## PHX-HARDWARE — clearPending requires exact durable event evidence (2026-11-17 UTC09)

**Defect reproduced at parent PR #315 HEAD `84fe6b790139d147f330f13a40b3ae3e89a7042d`:** `clearPending()` allowed `candidateCount == 0`. With a valid `/pending.attempt` marker but no `/pending.dat`, `/pending.new`, or `/pending.bak`, it returned success, removed the only remaining attempt evidence, and reset the RAM event. This is unsafe: a marker-only state is ambiguous evidence and must require operator reconciliation.

**Correction:** both ESP sketches now require (1) a valid attempt marker matching the current RAM pulse count/nonce/target, (2) exactly one durable pending-journal candidate, and (3) a valid candidate whose complete record matches the marker, including checksum, before deleting anything. Missing, duplicate, corrupt, or mismatched candidates latch `journalRecoveryRequired` and preserve all files/RAM. Pending journal removal is verified before the attempt marker is removed last.

**Test-first evidence (local C++ host harness; not CI):**
- RED against the exact parent `clearPending()`: `cleared=1 marker_exists=0 pending_pulses=0 recovery=0` for an orphan-marker-only state.
- GREEN against the patched guard: 7/7 scenarios passed — orphan marker retained; valid single matching journal clears; duplicate journals retained; mismatched journal retained; mismatched marker retained; failed pending removal retains marker/RAM; failed marker removal latches recovery.
- The initial harness fixture was corrected to a firmware-valid 16-character nonce before GREEN; no production source was relaxed.

**Cross-role request:** PHX-QA owns `experiment/openwrt/BlazePwifi/tests/`. Please add the orphan-marker-only, missing-candidate, duplicate-candidate, mismatched-record, and both removal-failure cases to the canonical pending-clear exact-source lab and independently run it at this PR's exact head. PHX-HARDWARE did not edit QA-owned tests or workflows.

**Evidence classification:** local failure injection is SIMULATED. New PR exact-head CI is pending. This does not enable coin disposition; `coinPostDispositionVerified()` and `acceptPollResponse()` remain default-deny. Physical flash durability, 150 power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain NOT TESTED/BLOCKED. **PRODUCTION NO-GO.**


## PHX-HARDWARE — exact-one pending journal before coin POST (2026-11-17 UTC10)

A source audit found **markPendingPostAttempt()** could write the one-shot marker when one pending candidate matched RAM while a second conflicting, duplicate, or corrupt **/pending.dat**, **/pending.new**, or **/pending.bak** also existed. The marker boundary now independently requires exactly one durable candidate, validated and matched to the current pending record before marker write or network dispatch.

Test-first evidence: [RED #44064000610](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064000610), job **133972839735**, failed as intended at the conflicting-extra-candidate case. Firmware fix [6100a74](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6100a74f8a94f314d99420917d51c28c75b5847d) updates ESP32 and ESP8266. Positive single-**pending.new** and single-**pending.bak** recovery cases are included in [f2bf146](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f2bf1465ddb95cc17a9d814cf68ba556000b9a8d).

Focused exact-head [run #44064230539](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064230539), job **133973625675**, **SUCCESS** at **f2bf1465ddb95cc17a9d814cf68ba556000b9a8d**: pending-attempt marker 28/28 per board (56/56 total); inherited hardware source-extracted labs passed. Full validation remains separate and is not claimed green.

Classification: **SIMULATED / CI VERIFIED**. Physical flash, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. Coin receipt verification remains default-deny; no merge, migration, flash, production signing, release or deployment.
