# PHX-MASTER UTC15 — active development, HARDWARE exact-head failures, and COE #26 provenance re-audit

**Observed:** 2026-11-26T15:10Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Starting Master branch HEAD:** `8287045b861f019e011745fc054478747630bc5f` on `phoenix/master-coordination`  
**PR #288:** OPEN / DRAFT / UNMERGED. No subsystem source or COE destination files were changed.

## 1. Exact live repository references

| Repository / ref | Exact commit |
|---|---|
| Experiments default `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Active v0.6 development base `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy v0.5.3 development line `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master `phoenix/master-coordination` (starting HEAD) | `8287045b861f019e011745fc054478747630bc5f` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE #26 branch `integration/ecosystem-nonproprietary-candidate-20261111` | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

The active v0.6 development base is distinguished from the legacy v0.5.3 development line; PR #354 is explicitly based on the v0.6 branch. Experiments main is the repository default branch.

## 2. Current owner PR heads and exact-head CI

| Owner / PR | Exact PR HEAD | Current exact-head evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Scoped BlazePwifi build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | API21/API23, native auth/installer recovery and APK identity [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340) PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM not tested |
| HARDWARE #353 | `df1a633474cdfac139df9254a5c885961df94985` | Three exact-head workflows fail; see §3 |
| HARDWARE #354 | `bbb209f55ddcd48f248eb8d700629db8754dc13a` | Focused deny/polarity [#45836227697](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227697) PASS; ESP32 Mbed TLS matrix [#45836227855](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227855) PASS; Full [#45836227694](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227694) FAIL; Native [#45836227876](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227876) FAIL |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows synthetic [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM not tested |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow runs returned |
| RELEASE #291 | `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head workflow runs returned; PR API reports mergeable=false |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared CI [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL |
| COE RELEASE #35 | `1cb3a4346c64d257ebc18e55c9724998b689f6b6` | Case guard [#45837377963](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45837377963) PASS; shared [#45837377899](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45837377899) and sandbox [#45837377925](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45837377925) FAIL |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows remain QUEUED with zero jobs |

CORE, RENTAL, PISONET, HARDWARE, QA and RELEASE source branches remain owner-controlled. PHX-MASTER did not edit them.

## 3. HARDWARE #353 — current exact-head failures and stale handover

PR #353 is OPEN / DRAFT / UNMERGED at `df1a633474cdfac139df9254a5c885961df94985`, based on parent #352 at `2fa3b7db1161ddb531ed94bcf60617947fa1a7bd`. The current PR body still identifies documentation HEAD `cb1787ac8f89562f20b6ecdee0c7969fbd12bd01` and source/test SHA `ed2f77d5924172881f27222cc26649f8f85abe6c`; those pins are stale relative to the actual PR HEAD. Master does not infer a replacement source/test SHA from a commit message. HARDWARE must refresh its PR body and exact-source handover.

- Relay polarity lab [#45843872877](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45843872877), failed job `139992333961`: the boot-polarity job passed, but source-output-polarity failed with `ESP8266: runtime pin attachment must quarantine coin ingress`. The 48/48 polarity scenarios and lexical extraction passed before this separate runtime-attachment assertion failed.
- Quarantine byte-readback [#45843872813](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45843872813), failed job `139992332657`: exact-source compilation failed because `runtimePinsSafe` was not declared in the extracted poll-loop fixture (`poll_loop.cpp:394`). Several JSON, UTF-8 and quarantine mutation checks passed; this compile failure stopped later checks.
- Full build [#45843872829](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45843872829), failed validation job `139992488154`: Controller protocol parity reported `Missing poll signature check` in the ESP8266 sketch. Firmware/platform jobs and Android passed; downstream simulations, update bundle, candidate gate, signing and publication were skipped.

These are HARDWARE-owned source/fixture defects. QA retains test ownership and CORE retains the authenticated poll/register contract. Master made no firmware edits.

## 4. HARDWARE #354 — deny-only contract remains blocked

At PR HEAD `bbb209f55ddcd48f248eb8d700629db8754dc13a`, source/test SHA remains `9bb46bb27e4be80f6506dbebf2846700efd4cb81`.

- Full [#45836227694](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227694) passes all 14 firmware/platform builds and Android, but validation fails at the QA-owned Controller protocol parity check (`Missing poll signature check`).
- Native [#45836227876](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227876) fails `tests/v060_vendo_sequence_contract.py:20`, which requires active `clearPending(true)` and `clearPending(false)` callsites. The candidate is intentionally deny-only and preserves pending evidence; do not add unsafe clear callsites merely to satisfy the assertion.
- Focused deny/polarity and ESP32 Mbed TLS matrix pass at this exact head. Production simulations, update bundle, candidate gate, signing and publication remain skipped.

QA must reconcile the assertion with the fail-closed contract; CORE must publish the authenticated disposition contract; HARDWARE owns firmware.

## 5. COE #35 current release gate

At `1cb3a4346c64d257ebc18e55c9724998b689f6b6`, source/test HEAD is `bf95c32be54f6427d81746d43141195830ef6bd9`.

- Shared CI [#45837377899](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45837377899): 254 tests passed, 2 skipped; then all 10 appliance profiles failed because an approved site-scoped RFC 4193 ULA /48 authority is missing.
- Sandbox [#45837377925](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45837377925): 48/48 host tests passed; Bubblewrap is absent on the runner, so the required sandbox gate exits 125. No privileged installation or unsandboxed fallback was used.
- Case-collision guard [#45837377963](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45837377963) PASS.

Release remains blocked pending approved site-prefix authority and a runner with the required sandbox capability.

## 6. COE #26 exact recursive-tree and blob comparison

The complete recursive trees were retrieved at exact commits; all report `truncated=false`:

- HARDWARE #353 `df1a633474cdfac139df9254a5c885961df94985`: 2,572 entries.
- HARDWARE #354 `bbb209f55ddcd48f248eb8d700629db8754dc13a`: 2,406 entries.
- COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`: 286 entries / 207 blobs.

| Route | Source PR | Source files | Destination files | Common | Exact blob+mode | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ESP32 | #353 | 16 | 1 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 | #353 | 67 | 1 | 1 | 0 | 1 | 66 | 0 |
| Vendo tests | #353 | 47 | 19 | 4 | 1 | 3 | 43 | 15 |
| ESP32 | #354 | 4 | 1 | 1 | 0 | 1 | 3 | 0 |
| ESP8266 | #354 | 8 | 1 | 1 | 0 | 1 | 7 | 0 |
| Vendo tests | #354 | 150 | 19 | 4 | 2 | 2 | 146 | 15 |

The two destination firmware blobs are identical across these comparisons but diverge from both current source candidates:

| Sketch | #353 source | #354 source | COE #26 destination |
|---|---|---|---|
| ESP32 | `8154297e30e72d82692987ed5690983df4955aea` | `3edbe38da543ef118b287f3e04c1601692cfa99f` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` |
| ESP8266 | `2613bfc36b0ddac9dd720592d4ff37e32a891744` | `b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9` | `c8be98f72596681e36a3ad1f8939bf8046c96887` |

## 7. COE #26 intake, audit and licensing inconsistencies

The current destination files were fetched at the #26 branch head:

- `Pisowifi/SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f` pins historical Experiments source `6d4c9b487af4d768c4d7627654d119417fcc6e00`, destination branch `feature/pisowifi-cleanup-stabilization`, and summary counts 47 byte-identical / 14 derived. Recounting its 61 runtime rows gives 46 byte-identical / 15 non-identical or derived rows.
- `Pisowifi/MIGRATION_MAP.md` blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` repeats the historical source and destination branch, not current #26 branch `integration/ecosystem-nonproprietary-candidate-20261111`.
- `docs/audits/HARDWARE_FIRMWARE_AUDIT.md` blob `86c06e7574761465b80482430296eb712d985367` says both Vendo sketches have not been copied pending P0-1, but the current destination tree contains both sketches with the divergent blobs in §6.

These are record-to-tree inconsistencies, not authorization to move or replace files. The integration owner must reconcile the records and decide whether destination sketches are historical candidates, unauthorized staging, or an approved-but-still-draft exception before any move is proposed.

Licensing/provenance gaps remain: product MIT LICENSE blob `1ee55b94183417be977ca287cd7391f9a6f7e721` matches exactly; the #354 source jsqr 1.4.0 LICENSE blob `8f71f43fee3f78649d238238cbde51e6d7055c82` has no destination counterpart; source root NOTICE, Tabler LICENSE, BlazeRentalLauncher LICENSE and COE root LICENSE are absent from the destination candidate.

The 11-route `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`; source_ref is `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; PHX-MASTER destination remains `null`. Five COE #26 workflows are queued with zero jobs. **No destination staging, copying, moving, cherry-picking, overwrite or mutation occurred.**

## 8. Governance, registry and Master-side execution

- Cleanup issue #266 remains OPEN, 0/7.
- Repository rulesets are empty in both repositories. Branch API reports `protected=false` for Experiments main, the active v0.6 development branch and COE main; effective required-check enforcement is not established.
- The private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. No Google Drive connector was exposed in this run, and the Library inventory did not surface v11. No older registry was substituted and no private registry contents were copied into this public report.
- Master exact-head GitHub Actions: zero workflow runs and zero combined statuses for `8287045b861f019e011745fc054478747630bc5f`.
- A normal shallow Git clone was attempted but failed because the execution container could not resolve `github.com`. The repository Master Python suite and `verify_coordination.py` were therefore NOT RUN.
- Fourteen Master-side static/source-tree assertions passed. These are coordination assertions, not source tests, not CI, and not hardware evidence.

## 9. Required next owner actions

1. HARDWARE refreshes #353 PR body and handover to actual head `df1a633`, identifies the exact current source/test SHA, and fixes its own runtime pin quarantine, `runtimePinsSafe` compile, and poll-signature failures.
2. QA corrects #354 assertions without weakening default-deny or pending-evidence preservation; CORE supplies the authenticated poll/register and receipt/disposition contract.
3. COE integration owner reconciles #26's historical source pin, branch label, runtime-row counts, Vendo sketch presence, test gaps and license/notice gaps before any destination move is proposed.
4. RELEASE/INFRA supplies approved site-scoped ULA authority and a runner with Bubblewrap available.
5. Registry custodian restores authorized v11/newer-correction access; repository administrators establish verifiable required-check protection.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, firmware flashing, physical test, real-payment operation or financial migration occurred.
