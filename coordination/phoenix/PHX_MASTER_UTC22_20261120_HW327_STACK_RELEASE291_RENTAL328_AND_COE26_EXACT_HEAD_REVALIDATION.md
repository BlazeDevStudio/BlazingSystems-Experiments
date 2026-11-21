# PHX-MASTER UTC22 — Live Hardware Stack, Role CI and COE Provenance Revalidation

**Audit timestamp:** 2026-11-20T22:34:16Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Audit-start branch:** `phoenix/master-coordination@6c1edfe001695bad55e701295799422f17f0fea1`  
**PR #288:** OPEN / DRAFT / UNMERGED; base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; 138 changed paths, all under `coordination/phoenix/`.  
**Scope:** coordination, architecture/interface contracts, cross-repository provenance and integration matrices only. No subsystem source branch was changed.

## 1. Authority and exact refs

The uploaded full-team Master directive, newest Library README_FIRST and BLAZE-COMMS/1 protocol were re-read. Experiments root `AGENTS.md` blob: `d8777e3b58efc41caa5aa3c969c932aee9103d5f`. Its linked Cloud Artifact Policy and Storage Recovery Handover were read from `BlazeDevStudio/BlazingSystems` main at blobs `5e503925750c4e511314e4b7624579d82f60aae2` and `a15f14cb3baf46424b820e1a921462794422f06b`. The policy requires private registry/sync-ledger review before Drive artifact creation and says to report BLOCKED if Drive access is unavailable.

| Ref | Exact HEAD |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Active `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master `phoenix/master-coordination` | `6c1edfe001695bad55e701295799422f17f0fea1` at audit start |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

Cleanup issue #266 remains OPEN with 0/7 role checkboxes complete. The Master cleanup item remains unchecked; the broader duplicate/dead-code inventory is not complete.

## 2. HARDWARE stack — exact ancestry and current CI

Current stacked ancestry is:

`#320@b2b41a3d` → `#322@50d93e0d` → `#323@988904e8` → `#326@58c558fb` → `#327@427bca9f`.

- #322 is based on #320's exact head; #323 on #322; #326 on #323; #327 on #326.
- #321 at `4c54d629...` is a sibling based on `fce915c1...`, not a parent of this chain.
- #327 source/test anchor is `af8e0e1e70e17ce70be77ec46b2ffbe738a16df2`; comparison to current docs/PR head `427bca9f32e5527181ca8d27fccb03887f272dfa` is exactly one documentation-only commit adding `experiment/openwrt/BlazePwifi/docs/handover/2026-11-21-hw-active-low-post-drain-multi-edge-rollover.md`.

Current #327 exact-head runs:
- [Quarantine byte readback #44828750699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44828750699): PASS.
- [Relay/output polarity #44828750648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44828750648): PASS.
- [Full BlazePwifi #44828750581](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44828750581): FAIL at `validate / Controller protocol parity`, job `136608090662`. Exact log: `Missing poll signature check` in the ESP8266 controller source parity check. Fourteen ESP/Android/firmware target jobs passed; downstream simulations, candidate, signing and publication jobs were skipped.

The latest Hardware owner checkpoint reports a source-extracted active-low multi-edge rollover regression at the source/test anchor: sequence wrap from `0xFFFFFFFE`, two post-drain edges, durable `COIN_INGRESS_UNRESOLVED` count 2, no HTTP poll, no pending credit and relay/LED OFF; the wrong-edge mutation is rejected on both boards. This is simulated/focused evidence, not physical acceptance. The Full failure is the inherited QA-owned positive poll-signature assertion in `tests/controllers.sh`; do not add a positive firmware poll path to satisfy it. PHX-CORE must define an approved versioned authenticated response/receipt contract before any positive consumer.

Parallel Hardware drafts remain separate:
- #254 head `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`: focused header run [#44683629378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629378) PASS; Full [#44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) FAIL because `mbedtls/sha256.h` is absent under ESP32 core 4.0.0.
- #283 head `830c355376380f9b5533d5cda2558beed41a593a`: quarantine append and Full runs [#44219099309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099309) and [#44219099256](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099256) PASS; it remains a separate candidate, not a child of #327.
- #239 head `d83b715b116185107737fef721c2eece8feebf39` remains an older separate candidate.
- #320 Full was cancelled; #321, #322, #323 and #326 Full runs failed while focused relay/quarantine runs passed. No Full stack acceptance is established.

## 3. Other current role PRs and exact CI

| Role / PR | Exact head and base | Exact current evidence |
|---|---|---|
| PHX-CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) scoped PASS. Separate Blaze Production Continuation retains CORE ownership. |
| PHX-RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070`, base #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 emulator [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS. Shared build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAILS at CORE-owned handover freshness (checkpoint `468adc8129ea311e13f4c5c63eb6bb01ca67ecb0`) and ESP32 compilation (`mbedtls/sha256.h` missing). Rental owns six Android/APK paths only. |
| PHX-PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) scoped PASS. PISONET retains SoftTimer/self-test ownership. |
| PHX-QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`; #292 base historical `b1ca02e...` | #290 [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) scoped PASS; #292 has no PR-triggered workflow run. QA owns the stale positive poll-signature fixture. |
| PHX-RELEASE #291 | docs/PR head `3344297fca7a4cefed71cccdec96bbbb7ff1bca4`; source/test `4c0dcc732c9123f61cbb17c6899006757d5d8a09`; base #242 `734b89d9...` | Docs head is one commit ahead of source/test and changes only `.github/PHX_RELEASE_HANDOVER.md`. Compatibility [#44829497810](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44829497810) PASS 3/3. Full [#44829497792](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44829497792) FAILS at CORE-owned mandatory handover freshness (last checkpoint `adcae8141e673dc2147fcad50521ef3a23084d71`); Windows [#44829497735](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44829497735) fails at the same gate and skips build/publisher. The earlier PISONET `$buildWorkflow` failure is not the current exact-head failing step and remains unverified behind this gate. The 26-path diff includes 21 RELEASE / 3 CORE / 2 PISONET paths; owner reviews remain required. |
| COE RELEASE #35 | `580855b6a45a6d3cf506a6aa9320bc4782efc246`, base #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b` | [Shared/Hardware #44820473859](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44820473859) FAILS after 120 packaging/tool tests PASS / 2 skip: all 10 profiles lack approved site-scoped RFC 4193 ULA /48; ESP compile jobs skipped. [Sandbox #44820473769](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44820473769) runs 14 host preflight tests then fails closed because Bubblewrap is absent (exit 125). [Case collision #44820473809](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44820473809) PASS. No real ImageBuilder build or firmware artifact. #35 is separate from #26. |

## 4. COE #26 exact source/destination staging review

Recursive Git trees were read completely at Experiments #327 head `427bca9f...` (2,448 entries) and COE #26 `b382d233...` (286 entries). These are review-only candidate trees, not an authorized migration pair.

The route manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, source ref Experiments main `f4e8a891...`, destination PR #26 `b382d233...`, PHX-MASTER target `null`. The active #327 Hardware candidate is not the manifest's pinned source ref.

| Route | Source files | Destination files | Exact result |
|---|---:|---:|---|
| ESP32 `experiment/openwrt/BlazePwifi/esp32/` → `Hardware/esp32/` | 16 | 1 | 0 identical; 1 divergent sketch; 15 source-only |
| ESP8266 `experiment/openwrt/BlazePwifi/esp8266/` → `Hardware/esp8266/` | 20 | 1 | 0 identical; 1 divergent sketch; 19 source-only |
| QA tests `experiment/openwrt/BlazePwifi/tests/` → `Pisowifi/tests/` | 47 | 19 | 1 identical; 3 divergent; 43 source-only; 15 destination-only |
| Hardware workflows | 3 scoped source workflows | 1 generic destination workflow | Invocation/coverage parity not established |

Exact firmware blobs (mode `100644`):
- ESP32 source `ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7` vs COE `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 source `a1f12edc3d0a2ce93641c3ae2ef1e0e258dbbdaa` vs COE `c8be98f72596681e36a3ad1f8939bf8046c96887`.

License/NOTICE:
- Source BlazePwifi LICENSE `1ee55b94183417be977ca287cd7391f9a6f7e721` equals COE `Pisowifi/LICENSE` exactly.
- Source root NOTICE `f6d92cd21465312be5993631fe26977219be0fb9` has no destination root counterpart.
- No root or Hardware-local LICENSE/NOTICE was found in the COE candidate. Pisowifi-only license match does not resolve Hardware notice scope; owner/custodian review remains required.

COE #26 remains OPEN / DRAFT / FROZEN with five workflows QUEUED / zero jobs and no submitted reviews. Imports/dependencies, test identities, license/NOTICE scope and exact-head destination CI remain incomplete. No copy, move, overwrite, cherry-pick, rebase, merge or route promotion occurred.

## 5. Master execution and limitations

- GitHub API/tree review is source/tree inspection, not a code-test result.
- Full Master Python suite: **NOT RUN**. Direct `git ls-remote` failed because this runtime could not resolve `github.com`; no authenticated local checkout was available.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections: **BLOCKED / NOT ACCESSIBLE**. No Google Drive connector is exposed and exact-title Library search did not return v11. Older v3–v7 snapshots were not substituted. No Drive artifacts or folders were created.
- Effective branch protection remains unverified; available API evidence did not establish organization-level rules.
- No hardware, physical power-cut, 30-device soak, financial, signer, flash, release or payment tests were run.

## 6. Required next actions and release gate

1. PHX-QA replaces the stale positive poll-signature assertion with source-exact negative/default-deny cases and reruns #327 Full at the current Hardware head; do not change firmware to satisfy the obsolete assertion.
2. PHX-CORE refreshes its authoritative handover after checkpoint `adcae814...` and resolves #328's CORE-owned freshness gate; CORE remains with the separate Blaze Production Continuation.
3. PHX-HARDWARE / PHX-RELEASE reconcile the accepted ESP32 firmware and toolchain baseline; Rental must not carry the stale inherited sketch.
4. PHX-RELEASE resolves approved site ULA authority and obtains a Bubblewrap-capable runner for COE #35; do not fabricate a prefix or install privileged tools in CI.
5. COE integration keeps #26 frozen until exact per-file source/destination blobs and modes, license/NOTICE applicability, dependency/import completeness, test identities and exact-head destination CI are independently accepted.
6. Registry custodian restores authorized v11/newer-correction access; repository administrator verifies effective branch protection.
7. PHX-MASTER runs the full coordination suite after authenticated checkout becomes available.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, flash, real-payment operation, migration or physical test was authorized.
