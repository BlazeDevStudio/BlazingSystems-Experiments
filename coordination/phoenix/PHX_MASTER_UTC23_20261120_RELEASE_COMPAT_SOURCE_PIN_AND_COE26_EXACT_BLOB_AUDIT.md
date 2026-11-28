# PHX-MASTER UTC23 — Release compatibility source pin and COE #26 exact-blob audit

**Timestamp:** 2026-11-20T23:38:20Z  
**Role:** PHX-MASTER — coordination / architecture / integration provenance only  
**Disposition:** DRAFT REVIEW ONLY · COE #26 FROZEN · PRODUCTION NO-GO  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.

## 1. Live refs and ownership

| Ref | Exact value |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` (comparison-only) |
| Master branch at audit start | `phoenix/master-coordination@230a1a16cb323c6743f8b932e4c6d2e531dbc3b0` |
| Master PR #288 base | `main@f4e8a891...` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 was OPEN / DRAFT / UNMERGED at audit start, with 139 changed paths, all under `coordination/phoenix/`; it had no PR-triggered workflow run and no submitted review. The live role/ownership routing manifest is unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`.

CORE implementation remains with the separate **Blaze Production Continuation** automation. No CORE, RENTAL, PISONET, HARDWARE, QA, RELEASE or COE destination source paths were edited.

## 2. New verified result — RELEASE #291 compatibility workflow now qualifies the exact current HARDWARE source

Current owner refs:

- RELEASE #291 docs/PR head: `88d8e326e0b19bed8a157fb88aa0a3a9524d90a9`
- RELEASE #291 source/test head: `87fb52cb06d10765aa4f60eb66a47ece88c7ce43`
- HARDWARE #327 docs/PR head: `1dbbdff7f6d40e011ae5ff9043c9e8669d02d9cd`
- HARDWARE #327 source/test anchor: `83c20c9d59bcdf6c24e2112f3396b90847b5bde0`
- Expected current ESP32 sketch blob: `ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7`

The Release compatibility workflow and test guard both pin HARDWARE source `83c20c9...` and the exact ESP32 sketch blob `ae0da8e...`. The workflow checks out that source into a separate `hardware-source` directory, verifies both Git identities, then compiles the pinned sketch.

[Run #44835998901](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44835998901) is terminal SUCCESS on PR/docs head `88d8e326...`, with 3/3 jobs successful:

| Job | Result | Evidence |
|---|---|---|
| ESP32 core 3.3.13 / source 83c20c9d59bc | PASS | Exact source SHA and sketch blob verified; reproducible image 1,044,432 bytes, SHA-256 `8b53a0c9c1374c11029a78d1a3dcd5bc4e817b7515d44d399a0ae0848696135d` |
| ESP32 core 4.0.0 / source 83c20c9d59bc | PASS | Exact source SHA and sketch blob verified; reproducible image 1,098,528 bytes, SHA-256 `dfc6dc1d2138c2bfffef7f642a8473af5fd7fcaf7ba094d75d752a6f775cc17a` |
| Release artifact provenance regression suite | PASS | 32 tests; immutable action-pin checks passed |

**Important source identity distinction:** the Release #291 branch's own inherited ESP32 sketch blob at its docs head is `29f1125d52ff474a0d028ad41f7af201be1f0f9d`, not `ae0da8e...`. The compatibility workflow does not compile that local inherited blob; it deliberately checks out and compiles the separate current HARDWARE #327 source. Therefore the compatibility PASS qualifies only HARDWARE source `83c20c9...` / blob `ae0da8e...` under the two tested cores. It must not be described as proof that the Release branch's different inherited sketch was compiled.

## 3. Terminal Release and Hardware gates remain blocked

### RELEASE #291

- [Full run #44835998849](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44835998849): **FAILURE** at the canonical handover freshness gate. The log says `PROJECT_HANDOVER.md` is stale after `.github/workflows/blazepisonet-softtimer-release.yml`; last checkpoint commit `adcae8141e673dc2147fcad50521ef3a23084d71`. The 14 target/platform jobs completed successfully, but validation failure skipped downstream simulations, signing and publishing.
- [Windows run #44835998862](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44835998862): **FAILURE** at the same handover gate. Windows build and publisher jobs were skipped.
- No merge, signing, tag, package publication or release promotion is authorized. The compatibility result is not a terminal Release pass.

The handover owner must refresh the canonical record after the exact workflow change and include the exact evidence. RELEASE must not bypass the gate or edit another role's handover.

### HARDWARE #327

- [Quarantine #44831843790](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44831843790): PASS.
- [Relay/output #44831844009](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44831844009): PASS.
- [Full #44831844300](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44831844300): **FAILURE** at QA-owned `Missing poll signature check`. Fourteen target/platform jobs passed; downstream simulations/signing/publishing were skipped.

Current producer/consumer contract remains deny-only. QA must replace the obsolete positive poll-signature fixture with source-linked negative/default-deny cases. Do not add a fabricated `response_sig`, positive poll admission or a firmware bypass to make the inherited test green. Focused CI is simulated/host evidence, not physical acceptance.

### RENTAL #328

Head `0e0da62acd47c6a1ce287f8a30fc700d603fa070`:

- [APK identity #44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384): PASS.
- [API21/API23 smoke #44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393): PASS.
- [Shared build #44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390): FAILURE. Handover freshness gate reports `PROJECT_HANDOVER.md` stale after the PISONET release workflow change (last checkpoint `468adc8129ea311e13f4c5c63eb6bb01ca67ecb0`); ESP32 core 4.0.0 also fails because inherited sketch includes missing `mbedtls/sha256.h`.

The six-file Rental PR is Android/APK-only. Rental must not edit inherited firmware; CORE/hand-over owner and HARDWARE/RELEASE must coordinate the current source/toolchain baseline.

### QA and other role ownership

- QA #292 remains at head `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`, based on historical Master `b1ca02e...`, with no PR-triggered CI. Its prior bounded 4/4 source-extracted recipient check is not a full verifier-module run or hosted Master-suite evidence. QA should rebase/replay the unchanged regression against current Master and run exact-head CI.
- CORE #252 remains `c82705f2de865c89ab733b10efa84f26f56a5cc4`; separate CORE automation retains implementation.
- PISONET #255 remains `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09`; QA #290 remains `5c29d15994cee1279058f1eca12f2a3180704292`, with scoped CI #43633486963 PASS. Physical COM acceptance remains unverified.

## 4. COE #26 exact source/destination file review — keep frozen

COE #26 remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`, with 205 changed paths and five workflows QUEUED / zero jobs.

| Artifact | Experiments #327 source | COE #26 destination | Result |
|---|---|---|---|
| ESP32 sketch | `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` — `ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7` | `Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` — `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different blobs / different code baseline |
| ESP8266 sketch | `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` — `a1f12edc3d0a2ce93641c3ae2ef1e0e258dbbdaa` | `Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` — `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different blobs / different code baseline |
| Firmware hardening test | `experiment/openwrt/BlazePwifi/tests/v05_firmware_hardening_test.sh` — `41211b2c110ab409f6d9d1812ef12fda73b13211` | `Hardware/tests/test_firmware_hardening.sh` — `f921c56cecc19cab1989507b9b4ade1f45dac54e` | Different test identities; both still assert positive `response_sig`, `|register|` and `|poll|` markers, conflicting with current deny-only contract |
| Pisowifi MIT LICENSE | `experiment/openwrt/BlazePwifi/LICENSE` — `1ee55b94183417be977ca287cd7391f9a6f7e721` | `Pisowifi/LICENSE` — same blob | Exact match |
| Root NOTICE.md | `NOTICE.md` — `f6d92cd21465312be5993631fe26977219be0fb9` | Root `NOTICE.md` absent at #26 | Required notice scope is incomplete; no legal conclusion inferred |

The current routing manifest is still blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with source ref Experiments main, destination candidate #26, and PHX-MASTER destination `null`. It is not a copy/move instruction. No destination file was staged, copied, moved, overwritten, rebased, cherry-picked or promoted.

## 5. Governance, storage and test limitations

- Control plane #172 is OPEN. No PHX-MASTER UTC23 role-lock/checkpoint existed at audit start; PHX-RELEASE's UTC23 checkpoint was preserved.
- Cleanup issue #266 remains OPEN with 0/7 checkboxes checked; the Master cleanup inventory remains incomplete.
- The current repository `AGENTS.md`, Cloud Artifact Policy and Storage Recovery Handover were read. The policy requires the private registry and sync ledger before Drive mirror creation and requires remote readback/SHA256 for verified transfers.
- Exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not returned by exact-title Library search; only older v5–v7 snapshots and a separate checkpoint surfaced. No older snapshot was substituted. No Google Drive connector is exposed in this runtime; no Drive artifact, folder or sharing change was made.
- GitHub branch objects report `protected=false` for the inspected refs; effective organization/repository ruleset enforcement was not independently established.
- Full Master Python coordination suite was **NOT RUN**. This audit used connected GitHub source/blob reads, issue/PR metadata and hosted Actions logs. No local authenticated checkout was performed.
- No physical hardware test, power-cut test, device soak, production financial test, signing, firmware flash, secret provisioning, payment operation, merge or release occurred.

## 6. Exact next actions

1. **QA:** replace the inherited positive poll-signature test with negative/default-deny source-linked cases; rerun HARDWARE #327 Full on the exact current source/docs heads. Do not change firmware to satisfy the stale assertion.
2. **Canonical handover owner(s):** update `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` with the exact latest PISONET workflow/source evidence; rerun RELEASE #291 Full and Windows and RENTAL #328 shared validation.
3. **RELEASE + HARDWARE:** retain the exact source/blob/toolchain pins; do not imply the Release branch's inherited sketch was compiled by the external-source compatibility matrix.
4. **QA:** rebase/replay #292 and provide PR-triggered CI at current Master.
5. **COE integration owner / QA / Hardware / Release:** keep #26 frozen until exact blob/test import, license/NOTICE scope, destination CI and owner acceptance are complete.
6. **Registry custodian / repository administrator:** restore authorized private v11/newer-correction access and independently verify effective branch protection.
7. **Independent QA / hardware owners:** produce native acceptance, 150 real power cuts and 30-device/24-hour soak evidence before any release-gate reconsideration.

**Final disposition: PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates remain mandatory.
