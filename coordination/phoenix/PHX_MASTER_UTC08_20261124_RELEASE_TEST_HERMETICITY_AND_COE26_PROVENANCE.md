# PHX-MASTER UTC08 — release-test hermeticity, owner CI and COE #26 provenance

**Observed UTC:** 2026-11-24T08:05:17Z  
**Role:** PHX-MASTER — coordination, architecture contracts and migration provenance only  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Starting branch/HEAD:** `phoenix/master-coordination@3282a7c3060b404000972084825767d40145e3d5`  
**PR #288:** OPEN / DRAFT / UNMERGED; base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; 192 existing paths, all under `coordination/phoenix/`.  
**Execution:** NO CODEX. No subsystem source files or COE destination files changed.

## 1. Current refs and governance

| Ref | Exact SHA / state |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Issue-designated development `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| PHX-MASTER branch before this update | `3282a7c3060b404000972084825767d40145e3d5` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| PR #288 | OPEN / DRAFT / UNMERGED; 192 existing changed paths |
| Issue #172 | OPEN; latest Master checkpoint before this run is UTC07 |
| Cleanup issue #266 | OPEN; 0/7 checklist items complete |

The machine-readable `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER source `coordination/phoenix/`, target `null`. No route or ownership changed.

Branch objects report `protected=false` for Experiments main, development, and COE main. The rulesets list is empty. The Master branch protection detail could not be read through the current connector path; do not infer its state.

## 2. Exact owner PR and CI reconciliation

| Owner / candidate | Current PR head | Exact-head evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS, scoped. CORE remains with its separate continuation owner. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [APK identity #44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and [API smoke #44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; [build #44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Windows #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; hosted/synthetic only. |
| HARDWARE parent #347 | `960184670379f01e20f0e7e8bc23b3e5eedacd3f` | [Quarantine #45299741995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299741995), [Relay #45299742437](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299742437), and [Full #45299741993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299741993) FAIL. Parent results remain distinct from child results. |
| HARDWARE #349 | docs/head `dff053bb8fe276d3f0ba9764e845d61ebe640539`; source/test checkpoint `da046d5ea80a8daac7258d302ecc310cd5634b24` | [Quarantine #45343153318](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45343153318) and [Relay #45343153313](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45343153313) PASS; [Full #45343153346](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45343153346) FAIL at QA-owned Controller protocol parity / `Missing poll signature check`. |
| HARDWARE #348 | `eb7afcb2ba0d1e84054c052c8b129cb51a91d062` | [Focused header #45352513178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513178) PASS; [build #45352513177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513177) FAIL. Its validate job passed, but ESP32 compilation fails at `BlazePwifiVendo32.ino:6:10`: `mbedtls/sha256.h: No such file or directory`. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [Windows #43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered workflow runs. |
| RELEASE #291 | `dabfd75cdccea6ab2f5adfe5251fbc3b506e38aa` | [Windows #45352021031](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352021031) FAIL at `negative-selftest.ps1:326`; [BlazePwifi build #45352021135](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352021135) PASS; [ESP32 compatibility #45352021234](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352021234) PASS. Publisher step skipped after the Windows failure. |

COE owner candidates: #35 `e7801818b00854f34a5a88955d979c601ec96404` — validation and sandbox fail, case-collision passes; #45 `9d76a134c1f6512aa40c20ec4d247306a71a8cce` — overlay and case checks pass; #49 `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` — Stage 5.1 and case checks pass, Shared ESP32 compile fails. These are scoped CI results, not production acceptance.

## 3. New actionable finding — RELEASE #291 synthetic lookup is not hermetic

Exact current source blobs at #291 head:

- `.github/workflows/blazepisonet-softtimer-release.yml`: `61031c13aad934fb52aef3038598f8b4d6a89334`
- `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1`: `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`

The current Windows run fails at `negative-selftest.ps1:326` with:

`RELEASE-PUBLISHER executable lookup regression: missing tag accepted=False`

Source inspection shows the extracted publisher decision block contains two distinct live read-only CLI calls:

1. `gh api -i repos/$GITHUB_REPOSITORY/releases/tags/$releaseTag`
2. `gh api -i repos/$GITHUB_REPOSITORY/git/ref/tags/$releaseTag`

The self-test only substitutes the assignment `$lookupExit = $LASTEXITCODE` with `$fixtureExit`. It does not replace the first `gh api` command/output, the second `gh api` command/output, or `$tagLookupExit = $LASTEXITCODE`. The extracted block is executed as a scriptblock, so the purported synthetic negative test can still reach the real GitHub API. The missing-tag vector expects `Allowed=$true`, but the exact-head test observes `$accepted=$false`. The actual HTTP response was not printed, so its cause is not inferred.

**Required owner action:** PHX-PISONET and PHX-RELEASE must isolate both lookup endpoints at the process/adapter boundary, inject each response body and exit status, and prove the negative self-test makes zero real `gh api` calls. Keep the production publisher fail-closed. PHX-QA must independently review the corrected exact head. Master did not edit either owner-owned file.

## 4. Exact #349 → COE #26 tree and import comparison

Complete recursive trees, both non-truncated:

- Experiments #349: 2,499 entries.
- COE #26: 286 entries.
- COE main: 3 entries (structure-only scaffold).

Board directories:

- Source: 56 entries (two directories plus 54 files), including 42 Python labs/helpers.
- Destination: 4 entries (two directories plus two firmware sketches), zero Python labs/helpers.

| Artifact | Source #349 | Destination #26 | Result |
|---|---|---|---|
| ESP8266 sketch | `2f87a9de84ac53dbb0d2718b5c79a4662b63de8f` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different blobs |
| ESP32 sketch | `a9a1c2fecb001d71f8f22b43952edbd160aacaf8` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different blobs |
| ESP8266 JSON primitive parser lab | `15c0d31ef9c07c549a0ddd5cf4d26c687cac8fd3` | Missing | Not imported |
| Parser fixture module | `b55ec6ef0ec4184c7b18b4e55bd65aeb96951812` | Missing | Not imported |

Mapped test directory comparison (`experiment/openwrt/BlazePwifi/tests/` → `Pisowifi/tests/`): 47 source files, 19 destination files, 1 exact blob+mode match, 3 same-path divergent blobs, 43 source files with no counterpart, and 15 destination-only files. The three divergent same-path files are `config.sh`, `integration.sh`, and `security.sh`. This is a focused mapping comparison, not a claim that every historical 61-row intake record was rerun.

Licensing evidence:

- Product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE match exact source blobs at their mapped destination paths.
- Source root `NOTICE.md` is absent at COE #26 root.
- Tabler LICENSE and BlazeRentalLauncher LICENSE are absent at the destination.
- The #348 source candidate `ControllerAuthV1Lab.h` (blob `27950692147b2ec89b92505062d085deb8afb699`) and its native test `v060_controller_auth_header_native.cpp` (blob `404ce87229ba754b08d9842315c13c99b9e1b1c7`) have no counterpart in the complete COE #26 tree.

COE #26 remains OPEN / DRAFT / FROZEN with 205 changed paths. Its five workflows are queued; there are zero completed jobs and zero commit statuses. No staging, copy, move, overwrite, rebase, cherry-pick, or destination write occurred.

## 5. Access, tests and production disposition

- Root Experiments `AGENTS.md` was read at main; blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`. Its linked Cloud Artifact Policy and Storage Handover could not be resolved through the current GitHub connector path.
- `README_FIRST`, the exact uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`, and current `COMMUNICATION_PROTOCOL` were read. NO CODEX used.
- Private canonical registry v11 and newer corrections were not found in the connected Library. The Library contains older v3–v7 snapshots and a later checkpoint that references v11, but not the canonical v11 bytes. No older substitute, private IDs, or registry contents were published. No Google Drive connector is exposed.
- Master Python unittest suite and `verify_coordination.py` were NOT RUN: no authenticated local checkout is available. Master PR #288 has zero PR-triggered Actions runs/statuses at its current head. Remote tree/blob inspections and ordinary JavaScript consistency checks were used instead.
- No hardware was flashed or physically tested; no payment system, signer, secret, production release, or customer migration was touched.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates have independently verified evidence.

## 6. Next exact owner actions

1. PHX-PISONET + PHX-RELEASE: fixture both release-object and Git-tag lookups; make the test zero-network and rerun Windows at a new exact head.
2. PHX-HARDWARE: resolve the ESP32 Mbed TLS include at #348 and preserve the separate #349 Full poll-signature blocker.
3. PHX-CORE + PHX-HARDWARE + PHX-QA: define and independently verify the authenticated poll-response producer/consumer contract before any positive poll admission.
4. COE integration owner: provide a per-file source/test/license/provenance map and runnable destination CI before any staging proposal.
5. Registry custodian: restore authorized v11/newer-correction access; repository administrator: establish effective branch protection.
6. Authorized human runner: provide a local authenticated checkout and run the Master Python suite plus `verify_coordination.py`.


## UTC08 follow-up — exact live refs, release handover freshness and destination recheck (2026-11-24T08:37:40Z)

### Starting refs and ownership

- Master branch/PR #288 starting head: `07bc60a1cefe1373581460107d9dff5ef13caf5f`; parent `3282a7c3060b404000972084825767d40145e3d5`; base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `aad3aade72c1156eecba1fed30907c6d0283b2c5`; COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. Issue #172 OPEN; cleanup #266 OPEN / 0-of-7.

### New actionable finding — RELEASE #291 handover freshness is now the build blocker

Current RELEASE #291 head is `bffc4ffd86794a2df3408a099369e3d48f8b3f0b`. Its latest commit changes only `.github/scripts/test_phx_release_esp32_core_compatibility.py`; the test now expects HARDWARE #349 source/test `6ce423783b306411bdb7e7217081c050cb4cbec4` and docs/PR head `a994f7048673677651449eeb0a04d2bf9e91737c`.

The RELEASE handover `.github/PHX_RELEASE_HANDOVER.md` remains blob `500cc0be69efdb7320320595f07d5d1f37c5df63` and its UTC07 entry still records docs head `dff053bb8fe276d3f0ba9764e845d61ebe640539` and PR head `6ce423783b306411bdb7e7217081c050cb4cbec4`. This is a concrete stale anchor.

- Windows [#45357167284](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45357167284): FAIL at PISONET-owned `negative-selftest.ps1:326`, `missing tag accepted=False`; publisher skipped.
- BlazePwifi build [#45357167281](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45357167281): FAIL at CI-0701 `PHX-RELEASE-HANDOVER-ANCHOR-RED` before firmware compilation; dependent build/release jobs skipped.
- ESP32 compatibility [#45357167298](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45357167298): PASS 3/3, both core 3.3.13 and 4.0.0 legs.

Owner actions: PHX-RELEASE refreshes its own handover and reruns exact-head build/Windows; PHX-PISONET owns the negative-selftest and PublisherMockCli paths; PHX-QA independently reviews. Master made no RELEASE or PISONET source edits.

### HARDWARE exact-head results

- #349 source/test `6ce423783b306411bdb7e7217081c050cb4cbec4`; docs/PR head `a994f7048673677651449eeb0a04d2bf9e91737c`; ESP32 sketch blob `a9a1c2fecb001d71f8f22b43952edbd160aacaf8`.
- Quarantine [#45355139574](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45355139574) PASS; Relay [#45355139569](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45355139569) PASS; build [#45355139770](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45355139770) fails validation at QA-owned `Missing poll signature check`. All 14 firmware target jobs and Android pass; dependent release stages are skipped.
- #348 `eb7afcb2ba0d1e84054c052c8b129cb51a91d062`: focused [#45352513178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513178) PASS; build [#45352513177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513177) fails ESP32 compilation at `mbedtls/sha256.h` under core 4.0.0.
- Parent #347 `960184670379f01e20f0e7e8bc23b3e5eedacd3f` remains a distinct failing candidate; no child result is transferred to it.

### Current cross-owner handover identities

| Shared path | CORE #252 | PISONET #255 | QA #290 | RELEASE #291 |
|---|---|---|---|---|
| `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` | `72e8e487d333a9488f77c2c3e68652d1a650ff85` | `d3e66608280644af8c42635168a7e27c8fba8f31` | `83db03cf387f280ba2d595ff6e9d58ffa23417c5` | `afe7bd131afb7d8dd0e61ffda3162cfc9b6cf9bb` |
| `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md` | `df50981c1596838b1abf544e94f68e89ad556b7d` | `02963d32018ea09ad2a6a5a95b487de1f65ff4f2` | `3180e1a93c852e5c983f947e8ca45a897df0479f` | `17afd0738cc1b78d348f4cc9a9d2f418cc86b6b6` |
| `experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md` | `72c38aeb93377f3aedb758c91d670ff1150e87bd` | `47e07b7c0e06766d0d4ebb18bc13bfb274adfe22` | `73b9d1d6acbd8b58c13f2d1b9d17512c392f444a` | `85dd3c1e9254d947c4e75daaeaf3351ef3e105e3` |

All four role heads have different blobs on each shared handover path. RELEASE #291 also changes PISONET-owned `negative-selftest.ps1` and `PublisherMockCli.ps1`. Do not overwrite, cherry-pick, rebase, or merge to resolve these conflicts; require owner reconciliation.

### COE #26 exact-tree recheck

Complete recursive trees, both non-truncated: Experiments #349 `a994f704` = 2,501 entries; COE #26 `b382d233` = 286 entries. Board subtree: 57 source entries including 43 Python labs/helpers versus four destination entries and zero Python files.

- Firmware: ESP8266 `2f87a9de84ac53dbb0d2718b5c79a4662b63de8f` vs `c8be98f72596681e36a3ad1f8939bf8046c96887`; ESP32 `a9a1c2fecb001d71f8f22b43952edbd160aacaf8` vs `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` — both differ.
- JSON primitive parser lab `15c0d31ef9c07c549a0ddd5cf4d26c687cac8fd3` and fixture module `b55ec6ef0ec4184c7b18b4e55bd65aeb96951812` have no destination counterparts.
- Tests: 47 source / 19 destination; 1 exact blob+mode match, 3 divergent, 43 source-only, 15 destination-only. Divergent same-path files: `config.sh`, `integration.sh`, `security.sh`.
- #348 ControllerAuth header `27950692147b2ec89b92505062d085deb8afb699` and native test `404ce87229ba754b08d9842315c13c99b9e1b1c7` are absent from COE #26.
- Product LICENSE, QRCode LICENSE, TailAdmin LICENSE and NOTICE match. Root NOTICE, Tabler LICENSE and BlazeRentalLauncher LICENSE remain missing.
- COE #26 five workflows remain QUEUED / zero jobs and zero statuses. No migration staging or destination edits.

### Other COE exact-head CI

- #35 `e7801818b00854f34a5a88955d979c601ec96404`: case collision [#45303825417](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45303825417) PASS; all 10 appliance profiles fail closed without approved site ULA /48 [#45303825436](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45303825436); Bubblewrap unavailable, sandbox exit 125 [#45303825459](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45303825459).
- #45 `9d76a134c1f6512aa40c20ec4d247306a71a8cce`: overlay [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case collision [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS.
- #49 `aeb8ff11b2f5db9a5f86280ab62ab988245f3919`: Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case collision [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; ESP32 compile [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) fails at `mbedtls/sha256.h`.

### Governance, access and test limits

- `OWNERSHIP_ROUTES.json`: 11 routes / `DRAFT_REVIEW_ONLY` / PHX-MASTER target null. Cleanup #266 remains OPEN / 0-of-7.
- Experiments main/development and COE main report `protected=false`; Master branch protection is not independently verified.
- Private Drive registry v11 and newer corrections were not available through the authorized Library; no Google Drive connector is exposed. Older v3-v7 snapshots were not substituted; no private registry content or IDs were disclosed.
- Root `AGENTS.md` blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`, README blob `feb909e3f74ffb7b5b22df50399ccd127ada3b95`, README_FIRST and COMMUNICATION_PROTOCOL were read. Linked Cloud Artifact Policy and Storage Handover could not be resolved through the GitHub connector.
- Master PR #288 has zero Actions runs/statuses. Master Python suite and `verify_coordination.py` NOT RUN because no authenticated local checkout is available. Remote tree/blob comparisons and ordinary JavaScript assertions were executed; not a Python suite pass.

PRODUCTION NO-GO. No merge, release, signing, secret provisioning, hardware flash, physical test, payment operation, customer cutover, COE migration, or financial migration occurred.
