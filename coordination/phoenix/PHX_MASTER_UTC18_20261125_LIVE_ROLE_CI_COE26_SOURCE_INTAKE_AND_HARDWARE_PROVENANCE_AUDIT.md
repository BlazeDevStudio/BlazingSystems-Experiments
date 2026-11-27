# PHX-MASTER UTC18 — live owner CI, COE #26 source intake and Hardware provenance audit

**Observed:** 2026-11-25T18:37Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** exact-head coordination and migration-provenance audit; no new task ID was assigned.  
**Starting branch:** `phoenix/master-coordination@555f50d8dd3ecd8ee2e7adbf8ecafd092470288f`  
**Mode:** strict NO CODEX.

## 1. Exact repository references

- Experiments default branch: `main@6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`.
- Active v0.6 development: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Legacy v0.5.3 development: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master starting HEAD: `phoenix/master-coordination@555f50d8dd3ecd8ee2e7adbf8ecafd092470288f`.
- COE default branch: `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` (three tree entries; scaffold only).
- COE integration candidate PR #26: `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Current HARDWARE #352: PR/docs head `8daccf67e939dbd331c9111c91cb7bfb96d1cc94`; exact source/test head `8eab82606ab8bf7ae5c598edde739d7b47e7c7a2`.
- Current COE RELEASE #35: PR/docs head `28da39c6db9953630400a12701621c5c824b90b0`; source/test head `10f19a28fbdd7eccb7b78ab11b3cbd4a49f37d74`.
- Current Experiments RELEASE #291: `9b928c9eaa72cb26fdcf3f0e50a0ec024f4e3c30`.

## 2. Master draft and control plane

- PR #288 remains OPEN / DRAFT / UNMERGED. At the starting HEAD it had 218 changed paths, all under `coordination/phoenix/`; no subsystem source path was changed.
- `main...phoenix/master-coordination` was 573 ahead / 1 behind, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. No rebase, retarget or merge was attempted.
- Master exact-head Actions and combined statuses returned zero runs/statuses.
- `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains 11 routes / `DRAFT_REVIEW_ONLY`; its source ref is `f4e8a891...`, candidate #26 is `b382d233...`, and the PHX-MASTER destination is null.
- Issue #266 remains OPEN / 0-of-7. No cleanup checkbox was claimed complete.

## 3. Current role-owned PR and exact-head CI

| Owner / PR | Exact head | Current evidence and disposition |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; scoped/older evidence only, not financial acceptance. CORE owns poll/register producer, durable finance and canonical handover. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | APK [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340), API [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth/recovery [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551) PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL. RENTAL owns correction. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM not invoked. |
| HARDWARE #352 | docs `8daccf67`; source/test `8eab8260` | Source Quarantine [#45672193685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672193685), Relay [#45672194428](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672194428), ESP8266 [#45672193510](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672193510), ESP32 [#45672193620](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672193620) PASS. Docs-head Quarantine [#45673358225](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45673358225), Relay [#45673358477](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45673358477), ESP8266 [#45673358221](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45673358221), ESP32 [#45673358181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45673358181) PASS; docs-head Full [#45673358387](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45673358387) FAIL at `Missing poll signature check` in the ESP8266 sketch. CORE owns the authenticated response contract; QA owns independent assertion review. |
| HARDWARE parent #349 | `2a5c997add4f49fcd74f753101d3a9daac0040bf` | Quarantine [#45603969253](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969253) and Relay [#45603968961](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603968961) PASS; Full [#45603969181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969181) FAIL. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM not invoked. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered runs. |
| RELEASE #291 | `9b928c9eaa72cb26fdcf3f0e50a0ec024f4e3c30` | Windows [#45669599214](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599214) and Full [#45669599438](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599438) FAIL at CORE CURRENT_STATE freshness; ESP32 compatibility [#45669599322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599322) PASS. Logs name checkpoint `d85eb6a2766781b6cac1807cef461993d8216b84` and four workflow files newer than `CURRENT_STATE.md`; downstream release stages skipped. PR description remains stale at UTC17; RELEASE owns refresh. |
| COE RELEASE #35 | docs `28da39c6`; source/test `10f19a28` | Exact source [#45673470909](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45673470909) and PR [#45673479995](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45673479995): 231 tests PASS / 2 skips, then 10/10 site-ULA profiles fail closed. Docs-head shared [#45673818111](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45673818111): 231 PASS / 2 skips, 10/10 ULA profiles fail closed. Sandbox [#45673815489](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45673815489): 40/40 host tests PASS, then Bubblewrap absent / exit 125. Case guard [#45673815464](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45673815464) PASS. RELEASE PR body current at UTC18; site authority and sandbox runner remain blockers. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; focused only. |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared Hardware/contracts [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED; all five job listings returned zero jobs. Candidate remains FROZEN; queued/no-job is not a pass. |

## 4. COE #26 source/destination provenance — no staging

### Rootfs intake

- Canonical whole-product source is active v0.6 development `2fbd2475e9f54878c316fa7cea2f228386b0e859`; complete tree 2,392 entries / 1,846 blobs; `openwrt/rootfs` 61 blobs.
- COE #26 is 286 entries / 207 blobs; `Pisowifi/openwrt/rootfs` is 62 blobs. Extra destination file: `Pisowifi/openwrt/rootfs/usr/sbin/blaze-appliance-diag` (blob `6690c739e931929d7beb3c256dd50b4531be3ba3`), absent from the 61-row intake; owner provenance required.
- `Pisowifi/SOURCE_INTAKE.json` (blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`, schema 8) pins source `6d4c9b487af4d768c4d7627654d119417fcc6e00` and destination branch `feature/pisowifi-cleanup-stabilization`, not current PR #26 branch `integration/ecosystem-nonproprietary-candidate-20261111`.
- All 61 manifest source/destination paths exist at active v0.6 and #26. Exact current source-vs-destination comparison is 46 equal / 15 different blobs. Runtime rows classify 46 byte-identical / 15 derived, but JSON summary says 47 / 14.
- `openwrt/rootfs/usr/lib/blazepwifi/common.sh` advanced on active v0.6 to `50fa2d02d40af7fd8b06e83974345f1016a317f9`; candidate remains at `ae00667da26c68c9e44a54a941887191029afc11`; intake still records old source `4ccb10777b08f541d092f7c2c2d2aad4d2f6562e`. Owner review required.
- `Pisowifi/MIGRATION_MAP.md` blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` repeats old source commit and destination branch. Reconcile only under COE integration ownership.

### Test identity and Hardware route

- Active v0.6 test-directory blobs: 150 source / 19 destination; 2 exact, 2 divergent (`config.sh`, `integration.sh`), 131 source-only, 15 destination-only.
- Active v0.6 source tests include `tests/vendor/jsqr-1.4.0/{LICENSE,PROVENANCE.json,jsQR.js}`; absent from COE #26 and requires third-party provenance review.
- HARDWARE #352 source/test `8eab8260`: 76 ESP32/ESP8266 subtree blobs (16/60), 64 board-local Python helpers; COE #26 has 2 board blobs (1/1) and zero helpers.
- #352 test snapshot: 47 source / 19 destination; 1 exact, 3 divergent, 43 source-only, 15 destination-only. ESP32 source sketch `1412cf57b70c6ee3061da9831b8d9abf6d58d94e` differs from `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`; ESP8266 source `b99f1f21d8ad1e6df0e403b2b34507f97bd90c16` differs from `c8be98f72596681e36a3ad1f8939bf8046c96887`.

### Licensing

- Product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE have exact destination counterparts.
- Experiments root `NOTICE.md` and `ui/vendor/tabler/LICENSE` are absent from COE #26.
- `BlazeRentalLauncher/LICENSE` is under the separate PHX-RENTAL route and is not a PisoWiFi #26 destination path.
- COE main has three tree entries. Five #26 workflows are QUEUED / zero jobs. Ownership manifest remains 11 routes / `DRAFT_REVIEW_ONLY` / Master target null.
- No staging, copy, move, overwrite, rebase, cherry-pick, retarget or promotion. Candidate remains FROZEN.

## 5. Registry and execution limits

- Experiments `AGENTS.md` blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f` requires restricted Drive registry/manifests before Drive artifact creation and exact readback before an artifact is VERIFIED.
- No Google Drive connector was available; Library search did not recover `BLAZE_PROJECT_REGISTRY_v11_20261027.json` or newer corrections. Registry remains NOT_RECOVERED; no older snapshot substituted and no private data published.
- Issue #172 had no `PHX-MASTER-20261125T18` checkpoint when checked. Cleanup #266 remains 0/7.
- GitHub branch/PR/tree/blob, manifest, test-identity, license-path and CI inspections executed. Master Python tests and `verify_coordination.py` NOT RUN because no authenticated local checkout/test runner was available. Master Actions at starting HEAD returned zero runs. Remote owner CI is not a Master test pass.

## 6. Next owner actions

1. PHX-CORE publishes canonical CURRENT_STATE / PROJECT_HANDOVER and authenticated poll/register producer contract; CORE retains its source branch and financial authority.
2. PHX-QA independently reconciles the HARDWARE Full poll-signature assertion and reviews COE RELEASE #35.
3. PHX-RELEASE refreshes its own #291 description to `9b928c9e`, then reruns Windows and Full after CORE publishes the exact canonical handover SHA.
4. COE integration owner reconciles SOURCE_INTAKE/MIGRATION_MAP, common.sh drift, extra diagnostic file, test identity, jsQR provenance and license gaps; keep #26 frozen until exact-head CI has jobs and terminal evidence.
5. RELEASE/INFRA obtains approved site-scoped RFC 4193 ULA /48 authority and Bubblewrap-capable runner; no invented prefix or unsandboxed fallback.
6. Registry custodian restores authorized access to current private v11 registry and newer corrections.

## 7. Safety disposition

PRODUCTION NO-GO. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No subsystem source, COE destination, secrets, signer, firmware, hardware, real payment state or release artifact was changed.