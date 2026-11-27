# PHX-MASTER UTC17 — live exact-head, controller contract, COE route matrix and storage-policy revalidation

**Task:** `PHX-MASTER-20261127T17Z`  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Branch:** `phoenix/master-coordination`  
**Parent HEAD at audit start:** `0662a64e1fe450cf1517a910e058491bb7de7a58`  
**Scope:** `coordination/phoenix/` only. No subsystem source, owner branch, COE destination, financial state, secrets, hardware or release artifact changed.

## 1. Control plane and branch authority

- Experiments main: `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`.
- Active v0.6 development: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Legacy v0.5.3 development: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master branch / PR #288 start: `0662a64e1fe450cf1517a910e058491bb7de7a58`; PR #288 is OPEN / DRAFT / UNMERGED, base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Compare from current main `6be5d19b` to Master start `0662a64e1fe450cf1517a910e058491bb7de7a58`: **667 ahead / 1 behind**, merge base `f4e8a891`. The base-side commit remains unreviewed here; no rebase, retarget or merge was performed.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration PR #26: `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Issue #172 remains OPEN; latest Master checkpoint before this run was UTC16 comment #7223743369. The latest comment at audit start was HARDWARE UTC17 #7224312557; no duplicate Master UTC17 checkpoint existed.
- Cleanup issue #266 remains OPEN / **0-of-7** tracks checked. P0 issue #177 remains OPEN.

## 2. Role PR and exact-head CI reconciliation

All listed role PRs remain owner-owned; no source ownership or task assignment changed.

| Role | PR / exact head | Exact-head evidence |
|---|---|---|
| MASTER | #288 / `0662a64e1fe450cf1517a910e058491bb7de7a58` | No exact-head Master workflow run or combined status. |
| CORE | #252 / `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Build #42698139210 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210), scoped build only. |
| RENTAL | #328 / `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | [API #45622918364 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), [auth/installer #45622918551 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), [APK identity #45622918340 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340); [shared build #45622918468 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468). |
| PISONET | #255 / `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Windows synthetic #42462978704 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704); native COM/device acceptance NOT TESTED. |
| HARDWARE | #364 / `ea765fb822e1c517db4e61c103b86d8eb2c66c92` | [Focused PR #46041398065 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46041398065); [Mbed TLS #46041397937 PASS 3/3](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46041397937); [Full #46041397974 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46041397974). |
| HARDWARE parent | #362 / `eeddfc37d24d20ebc14641dfe3ffa247bbbc1ebd` | Focused/Mbed PASS; [Full #46029353015 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46029353015) at `config_revision`; [Native #46029353001 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46029353001) at QA-owned PAY-0745 assertion. |
| QA | #290 / `5c29d15994cee1279058f1eca12f2a3180704292` | [Windows synthetic #43633486963 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963); native COM lab not invoked. |
| QA | #292 / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head PR workflow run. |
| RELEASE | #291 / `bf339a76964a1abe2412fac45392fe06a8e66418`; #242 / `36c0d0bb3e58786359555b307bb784f720f023ce` | No exact-head PR-triggered workflow runs. |

HARDWARE #364 is a child of #362. Its source/test commit is `f77869c4efdf34416526be67728c81197b00c25e`; current docs/PR head is `ea765fb8`. The cleanup-only split moves source-contract assertions and unsafe-mutation helpers into `pending_recovery_promotion_lab_contract.py`; it does not change either firmware sketch or runtime behavior. Focused CI retains 15 recovery scenarios per board, six ambiguous-preservation cases and 18/18 unsafe mutations rejected. The Full run passes Android and all 13 firmware target jobs, but fails validation at `tests/controllers.sh:21` on `config_revision`; update bundle, simulations, signing and publication stages skip. This is a source/base parity failure, not proof the assertion is false.

## 3. Current interface mismatch and P0 poll ordering

Issue #177's embedded source pin `9df0a7e7...` is stale. The live active v0.6 branch is `2fbd2475...`; the exact board sketch blobs fetched from that branch are:

- ESP8266: `12c4bb82b6fddafe813674a0b5f692c1d3634073`; `h.setTimeout(3500)` line 263, synchronous `post("poll")` line 354, first `digitalRead(runCoinPin)` line 357.
- ESP32: `29f1125d52ff474a0d028ad41f7af201be1f0f9d`; `h.setTimeout(3500)` line 230, synchronous `post("poll")` lines 314–315, first `digitalRead(runCoinPin)` line 318.

Both live v0.6 loops still block on poll before sampling the coin input. The source confirms the P0 ordering concern; no physical pulse-loss reproduction was run in this activation.

A separate exact-head parity mismatch explains the #364 Full failure: current Experiments main `6be5d19b` contains `config_revision` in ESP8266 line 209 (blob `bfb94920eb0a189ca01d52e5443954fa133f5423`) and ESP32 line 168 (blob `117c6e937e8f12f3890ace2ae23b3a23ff1c3df0`), while the active v0.6 sketches at `2fbd2475` do not contain that field. The child stack descends from the older v0.6 base; QA's current-main parity assertion exposes real branch drift. HARDWARE/CORE must resolve source-base authority; QA owns assertion semantics. Do not add a decoy token or weaken the guard.

The current main CGI producer blob `2e3a1430d08cc6606429a042df3b5848f53c7267` has `register|ping` at line 63 and `poll` at line 68; those controller response blocks do not emit `response_sig`. Later `response_sig` fields at lines 94 onward belong to member endpoints and are not controller poll authentication. CORE owns the authenticated response/event contract; QA owns golden vectors and independent semantic validation; HARDWARE owns firmware changes. Keep consumer behavior deny-only until the canonical contract is approved.

## 4. COE #26 exact route-mapped tree review

Both recursive trees were non-truncated:

- Source candidate: Experiments PR #364 head `ea765fb822e1c517db4e61c103b86d8eb2c66c92`, **2,430 entries**.
- Destination candidate: COE PR #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`, **286 entries**.

The table applies the 11-route manifest's path-prefix substitution to exact file blobs/modes. It is an audit comparison only, not a copy plan or migration authorization.

| Route | Source blobs | Destination blobs | Exact | Divergent | Missing | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE OpenWrt library | 20 | 20 | 14 | 6 | 0 | 0 |
| CORE Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL standalone server | 12 | 4 | 0 | 1 | 11 | 3 |
| PISONET SoftTimer | 44 | 47 | 16 | 9 | 19 | 22 |
| HARDWARE ESP32 | 4 | 1 | 0 | 1 | 3 | 0 |
| HARDWARE ESP8266 | 16 | 1 | 0 | 1 | 15 | 0 |
| QA PisoWiFi tests | 151 | 19 | 2 | 2 | 147 | 15 |
| RELEASE workflow reimplementation | 1 | 1 | 0 | 1 | 0 | 0 |

The QA route counts are file/path entries under `tests/`, including README, fixtures and vendor content; they are not 151 executable tests. The new Hardware module `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/pending_recovery_promotion_lab_contract.py` is source blob `883665eadccb0257c03cc5901183349cb8f199c3`; its route-derived destination `Hardware/esp8266/BlazePwifiVendo/pending_recovery_promotion_lab_contract.py` is absent from #26.

License/notice review remains incomplete: four reviewed counterparts are exact (PisoWiFi product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE); four source notices remain without mapped counterparts (repository NOTICE.md, Android Launcher LICENSE, jsQR LICENSE and Tabler LICENSE). The Android `assets/license.html` also has no destination counterpart and needs owner review. This is path/blob evidence, not legal approval.

The routing manifest remains schema `phoenix/ownership-routes/v1`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. Its `source_ref` remains historical `f4e8a891...`, not current main `6be5d19b...`. SOURCE_INTAKE/MIGRATION_MAP still name destination branch `feature/pisowifi-cleanup-stabilization` and historical source `6d4c9b48...`; live PR #26 is `integration/ecosystem-nonproprietary-candidate-20261111@b382d233`. All five candidate workflows are CANCELLED with zero jobs. COE #26 remains FROZEN. No staging, copy, move, overwrite, rebase, cherry-pick or retarget was performed.

## 5. Storage policy and private registry access

The current Experiments root `AGENTS.md` blob is `d8777e3b58efc41caa5aa3c969c932aee9103d5f`. Its historical owner URL resolves to the renamed repository `BlazeDevStudio/BlazingSystems`. The linked [BLAZE_CLOUD_ARTIFACT_POLICY.md](https://github.com/BlazeDevStudio/BlazingSystems/blob/main/BLAZE_CLOUD_ARTIFACT_POLICY.md) was read at blob `5e503925750c4e511314e4b7624579d82f60aae2`; [BLAZE_CLOUD_STORAGE_HANDOVER.md](https://github.com/BlazeDevStudio/BlazingSystems/blob/main/BLAZE_CLOUD_STORAGE_HANDOVER.md) was read at blob `a15f14cb3baf46424b820e1a921462794422f06b`. This supersedes older Master notes that said these public documents could not be fetched.

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. Library search surfaced only v3–v7 registry snapshots and duplicate/older manifest and sync-ledger records; the public-policy path `Experimental Projects/Blaze-Systems-Project-Mirror/00-MASTER-CONTROL` was not present in Library. No Google Drive connector is exposed. Older records were not substituted, no private IDs/content were published, and no Drive writes or sharing changes occurred. Registry custodian must restore authorized v11 and current corrections before any mirror/staging action.

## 6. Automation deconfliction

The automation inventory surfaced 17 tasks. It includes active `Blaze Hourly Production Development`, whose saved prompt explicitly assigns PHX-HARDWARE. No exact-title `Blaze Production Continuation` task appeared in that inventory. CORE source PR #252 was left untouched; no competing CORE worker, branch or automation was created or redirected. The existing PHX-HARDWARE worker remains owner of its branch/PR stack.

## 7. Execution classification and next actions

- **Executed:** GitHub issue/PR/branch/tree/blob reads; exact recursive source/destination tree comparison; route mapping and blob/mode comparison; current-main/v0.6 firmware and CGI source inspection; role CI run inspection; current AGENTS-linked policy/handover reads.
- **Not executed:** Master Python suite, `verify_coordination.py`, local firmware host tests, new Master Actions, native COM/device acceptance, physical pulse/relay tests, power cuts or soak. GitHub connector reads do not equal local test execution; no Master exact-head workflow/status exists.
- **Next:** (1) Registry custodian restores canonical v11/corrections; (2) CORE/HARDWARE agree authenticated poll/receipt/disposition and source-base authority; (3) QA resolves `config_revision` and PAY-0745 semantics without weakening fail-closed guards; (4) COE owner reconciles exact source pin, all route blobs, test identities, licenses and candidate CI; (5) repository admin provides an ordinary non-Codex checkout or dedicated Master CI path.

**Disposition:** Master coordination only. Cleanup #266 remains OPEN / 0-of-7. COE #26 remains FROZEN. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. **PRODUCTION NO-GO.** No merge, release, flash, secret provisioning, payment operation, financial migration or physical test occurred.
