## PHX-MASTER UTC17 final post-checkpoint #353 readback — 2026-11-26T17:54Z

This supersedes the earlier 17:52Z IN_PROGRESS note. HARDWARE refreshed PR #353 to docs HEAD `f527b33c9e391a9a66490388d96f06d6c8761dfa`, source/test SHA `44de55a0e132cb15fdb60ecf85446e9490fa277e`, parent #352 `2fa3b7db1161ddb531ed94bcf60617947fa1a7bd`. The latest source/test commit changes only `coin_pulse_capture_lab_isr.py`: snapshot the prior `pollIntakeSuspended` state before temporary inhibit and restore that exact value only after successful post-attach quarantine. The PR body/handover is now current; previous cb1787ac/ed2f77d pointers are superseded.

- Exact-source Relay push [#45870624293](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624293) and PR [#45870635699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870635699): PASS.
- Exact-source Quarantine push [#45870624386](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624386) and PR [#45870635503](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870635503): PASS.
- Exact-source Full [#45870624355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624355): FAIL, inherited ESP8266 missing poll-signature check.
- Current docs-head Relay [#45871096516](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096516): PASS; Quarantine [#45871096480](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096480): PASS.
- Current docs-head Full [#45871096425](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096425): FAIL; raw validate log explicitly says `Missing poll signature check` in the ESP8266 sketch. All 14 target/platform jobs and Android PASS; production import, update bundle, simulations, candidate gate, signing handoff and publication are SKIPPED.
- No production `.ino`, controller/API, finance, signer, witness, migration or COE destination changed. These are source-extracted host simulations and CI only; HARDWARE ACCEPTED remains NO.

CORE owns authenticated poll/register producer contract; QA owns independent assertions; HARDWARE owns the lab. Do not add an ad-hoc signature or weaken default-deny.

---

## PHX-MASTER UTC17 post-checkpoint refresh — 2026-11-26T17:52Z

**This addendum supersedes the earlier #353 head, handover and current-run status recorded below.** During this same UTC17 activation, HARDWARE advanced #353 after the initial Master checkpoint.

- Current #353 PR/docs HEAD: `f527b33c9e391a9a66490388d96f06d6c8761dfa`; current source/test SHA: `44de55a0e132cb15fdb60ecf85446e9490fa277e`; parent #352 remains exact at `2fa3b7db1161ddb531ed94bcf60617947fa1a7bd`.
- The new source/test commit changes only Hardware-owned `coin_pulse_capture_lab_isr.py`. It now snapshots the pre-existing `pollIntakeSuspended` state before temporary inhibit and restores that exact prior state only after successful post-attach quarantine; the previous lab allowed a mutation that initialized the snapshot to `false`.
- HARDWARE refreshed its PR body/handover to current head `f527b33c`; the prior stale `cb1787ac/ed2f77d` pointers are superseded.
- Exact source/test SHA evidence: test-first RED [#45869946851](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45869946851); intermediate test-authoring issue [#45870280500](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870280500) was corrected; focused Relay [#45870624293](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624293) and PR [#45870635699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870635699) PASS; Quarantine [#45870624386](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624386) and PR [#45870635503](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870635503) PASS. Full [#45870624355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624355) still fails the inherited ESP8266 missing poll-signature check.
- New PR-docs-head runs on `f527b33c` are still IN_PROGRESS at readback: Quarantine [#45871096480](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096480), Relay [#45871096516](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096516), Full [#45871096425](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096425). These are not reported as PASS.
- Both production `.ino` sketches remain unchanged. Evidence is source-extracted host simulation and CI only; physical GPIO/relay, power-cut, soak and hardware acceptance remain NOT TESTED.

CORE still owns the authenticated poll/register producer contract; QA owns independent assertions; HARDWARE owns this lab. No ad-hoc signature or fail-open change is authorized.

---

# PHX-MASTER scheduled UTC17 — live owner CI, current Hardware test heads and COE #26 provenance

**Observed:** 2026-11-26T17:31Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Work item:** live control-plane, role-head, CI and cross-repository provenance reconciliation  
**Execution:** strict NO CODEX. Coordination-only source changes.

## 1. Required instruction and source readback

Read for this activation:
- Owner-uploaded `00_MASTER_PROJECT_PHOENIX(1).txt` (full 68-line master prompt).
- Latest Library `README_FIRST(20261114-191926).md` and `COMMUNICATION_PROTOCOL(20261114-191925).md`.
- Experiments `AGENTS.md` and current `README.md`.
- Current-owner `BlazeDevStudio/BlazingSystems/BLAZE_CLOUD_ARTIFACT_POLICY.md` and `BLAZE_CLOUD_STORAGE_HANDOVER.md`; AGENTS links use the historical `BlazingSystems` owner, while GitHub resolves the repository to `BlazeDevStudio`.
- Live control-plane issue #172, cleanup issue #266, PR #288, the current 11-route ownership manifest, role PRs/CI, COE main and PR #26.

The latest README_FIRST states that scheduled issue comments are only signals and do not wake dormant chats; BLAZE-COMMS/1 requires one active run per role and scheduled hour. No current-date PHX-MASTER UTC17 checkpoint existed before this run. The earlier UTC16 Master checkpoint is preserved.

## 2. Exact repository refs and Master PR

| Ref | Exact SHA |
|---|---|
| Experiments default `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Active v0.6 base `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy v0.5.3 development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master `phoenix/master-coordination` starting HEAD | `47678fdf9a38a75298f6d051ece3c7aced66a22d` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 is OPEN / DRAFT / UNMERGED, mergeable=true. Exact compare `main...phoenix/master-coordination`: 619 ahead / 1 behind, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, 238 changed paths, all under `coordination/phoenix/`. The PR base pin is still the historical merge base; no rebase or main synchronization was performed.

Cleanup issue #266 remains OPEN, 0/7 tracks checked. The live `OWNERSHIP_ROUTES.json` is blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER destination is null. No route grants recursive copy or migration authority.

## 3. Current role PR heads and exact-head CI

| Role / PR | Exact PR HEAD | Current exact-head result |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) scoped build PASS; no financial acceptance. CORE source untouched. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | [API21/23 #45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), [auth #45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), [APK #45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340) PASS; [shared build #45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Windows synthetic #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM NOT TESTED. |
| HARDWARE #340 | `f70f6af78c64ef86ba0f631faeb02b6cb6eb2725` | Six workflows PASS; [Full #45747758154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747758154) 26 successful jobs / 4 production skips. |
| HARDWARE #353 | `ac9e754e95b4dcc8486a39fb9f672f907fa5931e` | Relay [#45868482870](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45868482870) PASS; Quarantine [#45868483008](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45868483008) PASS; Full [#45868482753](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45868482753) FAIL at poll-signature validation. |
| HARDWARE #354 | `fc842342596786e072630179acfbbc4feeb2ba02` (source/test `145aac9607682071e2db05944a6f9db5aa06e524`) | Poll-deny [#45864684458](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684458) PASS; Mbed TLS 3.3.13/4.0.0 matrix [#45864684325](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684325) PASS; Full [#45864684497](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684497) and Native [#45864684295](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684295) FAIL at QA-owned assertions. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [Windows synthetic #43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM NOT TESTED. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head runs; mergeable=false. |
| RELEASE #242 | `d19fa750f55ed65dc06f77ab116ab33e046a34bf` | No exact-head runs/status; mergeable=false. Its recorded v0.6 base `6d4c9b48` is 22 commits behind active v0.6 HEAD `2fbd2475`. |
| RELEASE #291 | `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head runs/status; mergeable=false. Its recorded #242 base `734b89d9` is 16 commits behind current #242 HEAD `d19fa750`. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS. |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL. |
| COE RELEASE #35 | `e1ad4fad1c234976ba76a34758d1ca993a897776` | Shared [#45848921260](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45848921260): 255 PASS / 2 skipped, 10/10 appliance ULA profiles rejected; sandbox [#45848921270](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45848921270): 48/48 host tests PASS then Bubblewrap exit 125; case guard [#45848921527](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45848921527) PASS. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows queued, zero jobs; FROZEN. |

## 4. HARDWARE #353 — current source/test handover is stale

PR #353 is a child of #352 and its base SHA `2fa3b7db1161ddb531ed94bcf60617947fa1a7bd` exactly matches current #352 HEAD. Current #353 HEAD is `ac9e754e`; its latest commit changes only Hardware-owned `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/coin_pulse_capture_lab_isr.py`, tightening the post-quarantine restore assertion to the same attachment branch.

The PR body still pins docs HEAD `cb1787ac` and source/test SHA `ed2f77d`, so its handover is stale relative to current PR HEAD `ac9e754e`. Hardware must refresh its own PR body/handover.

Current exact-head CI:
- Relay Output Polarity workflow PASS. Its source-output-polarity job explicitly skips the absent child poll-window suite; this is not evidence for that suite.
- Quarantine Byte Readback workflow PASS.
- Full workflow FAILS at `tests/controllers.sh`: log explicitly reports **Missing poll signature check** in the ESP8266 sketch. ESP8266, ESP32, Android and all 14 target/platform jobs pass; production import, update bundle, simulations, candidate gate, signing handoff and publication are skipped.

CORE owns the authenticated poll/register producer contract; HARDWARE owns firmware/labs; QA owns independent assertions. Do not invent a signature or weaken the poll-signature gate.

## 5. HARDWARE #354 — deny-only candidate preserved

Current PR/docs HEAD `fc842342`, source/test SHA `145aac96`. The source/test commit changes only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab.py`; both production sketches are unchanged from the previous source pin.

- Focused poll-deny passes.
- Mbed TLS source-contract and clean reproducible builds on core 3.3.13 and 4.0.0 pass.
- Full validation fails at QA-owned `tests/controllers.sh:21`, which requires `config_revision` in both deny-only sketches; neither sketch consumes this unsigned field. The 14 target/platform builds and Android pass, but Full is not PASS.
- Native synthetic fails at QA-owned `tests/v060_vendo_sequence_contract.py:20`, which requires active `clearPending(true/false)` callsites. The candidate intentionally preserves pending evidence and has no active disposition callsite.

QA must replace incompatible legacy expectations with independent deny/no-callsite/pending-evidence-preservation assertions. CORE must publish the authenticated poll/register and receipt/disposition contract before any positive admission. Do not add unsigned config consumption or unsafe pending clearing to make tests green.

## 6. COE #26 — migration and provenance hold

COE main is `a6513ab4`; integration #26 is `b382d233`, unchanged from the previous complete recursive-tree read (286 entries, truncated=false). Five workflows remain queued with zero jobs.

Exact firmware files were re-read at current #354 source/test SHA and current #26 destination:
- ESP32 source `3edbe38da543ef118b287f3e04c1601692cfa99f` vs destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` — DIFFERENT.
- ESP8266 source `b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9` vs destination `c8be98f72596681e36a3ad1f8939bf8046c96887` — DIFFERENT.

The previous full test-tree comparison used older #354 source/test SHA `9bb46bb2` and #353 source SHA `5a5f319`. Current #354 `145aac96` and #353 `ac9e754e` each changed one source lab/test file. Source file counts remain documented at 150 (#354) and 47 (#353), but exact test-blob identity counts from the old source pins are stale and must be recomputed before staging. Do not carry forward old exact-match counts as current evidence.

Current #26 `Pisowifi/SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`:
- 61 runtime rows recount to 46 `byte_identical` + 15 `derived_cleanup_review_required_real_router_test`.
- Summary declares 47 identical + 14 derived: one-row mismatch.
- Source pin is historical `6d4c9b48`; destination pin is `feature/pisowifi-cleanup-stabilization`, not current #26 branch `integration/ecosystem-nonproprietary-candidate-20261111`.
- Flags remain `hardware_tested=false`, `full_ci_tested=false`, `source_admission_complete=false`.
Current `Pisowifi/MIGRATION_MAP.md` repeats the old source/destination branch pins.

Current `docs/audits/HARDWARE_FIRMWARE_AUDIT.md` is internally contradictory: line 16 says both Vendo sketches were **not copied** pending P0-1; its 2026-11-11 addendum says they were migrated under draft PR #27 and merged into candidate PR #26. Both sketches are present in #26 but have divergent blobs from the current #354 source. The COE integration owner must reconcile this record against exact file provenance.

Licensing readback:
- Product PisoWiFi LICENSE matches exactly: `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE have matching destination blobs.
- Source Experiments root `NOTICE.md` exists (blob `f6d92cd2`); COE root `NOTICE.md` is absent.
- Source Tabler LICENSE exists (blob `22ee8122`); COE candidate `Pisowifi/ui/vendor/tabler/LICENSE` is absent.
- Source BlazeRentalLauncher LICENSE exists (blob `c5b1efa7`); candidate `Rental/android/BlazeRentalLauncher/LICENSE` is absent. This is a separate RENTAL surface, not a Hardware route.
- COE root LICENSE is absent. The previously flagged jsqr 1.4.0 LICENSE still needs exact-path re-resolution; do not treat it as cleared.

The 11-route ownership manifest remains `DRAFT_REVIEW_ONLY`; PHX-MASTER target is null. No destination staging, copy, move, overwrite, cherry-pick or workflow dispatch occurred.

## 7. Registry and execution limits

The private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. The current tool inventory exposes no Google Drive connector. The full Library listing was paginated (8 pages); it surfaced registry v3-v7 and a Nov 9 private checkpoint referencing v11 as its prior canonical registry, but not v11 or a newer registry correction. The checkpoint is not a substitute. No private registry data or identifiers were published.

The Master branch has no workflow runs or combined statuses at starting HEAD `47678fdf`. Master Python tests and `verify_coordination.py` were not run because no usable local clone was available; prior local GitHub DNS resolution failure remains the known limitation. Inline source/coordination assertions were run separately and are not repository tests.

## 8. Owner actions and disposition

1. HARDWARE refreshes #353's handover to exact head `ac9e754e`; resolve the source/fixture/poll-parity boundary without fabricating an authenticated response.
2. QA updates #354 deny-only controller and native sequence assertions; preserve pending evidence and no unsigned config consumption.
3. CORE publishes the authenticated poll/register plus receipt/disposition contract; CORE source remains reserved and untouched by Master.
4. COE integration owner reconciles #26 intake counts, historical branch pins, contradictory firmware audit, exact test identities and missing license/NOTICE counterparts before any staging proposal.
5. RELEASE reconciles #242/#291 ancestry and obtains exact-head CI before review.
6. Registry custodian provides authorized v11/newer-correction access; repository administrators establish verifiable protected required-check gates.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device 24-hour soak and owner-authorized release gates remain mandatory. No merge, release, secret/signer provisioning, flashing, physical tests, real-payment operation or financial migration occurred.
