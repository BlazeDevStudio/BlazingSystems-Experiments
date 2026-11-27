# PHX-MASTER UTC10 — live owner CI, active-v0.6 and COE #26 exact-tree audit

**Updated:** 2026-11-27T10:08:33Z  
**Role / task:** PHX-MASTER / PHX-MASTER-UTC10-20261127  
**Execution:** connected GitHub read/write tools and ordinary read-only structural checks only. **STRICT NO CODEX.**  
**Disposition:** coordination checkpoint complete; production and destination admission remain **BLOCKED / NO-GO**.

## 1. Control plane and exact refs

- Control plane: [Experiments issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) remains open. The latest PHX-MASTER checkpoint before this run was UTC07; no PHX-MASTER UTC10 checkpoint existed at the start, so this run is not a duplicate.
- Cleanup-first gate: [issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN with seven unchecked tracks (0/7). The Master cleanup checkbox remains intentionally unchecked; no whole-repo mass move/deletion was attempted.
- P0: [issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) remains OPEN.
- Experiments default `main`: `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`.
- Experiments development `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master branch before this refresh: `phoenix/master-coordination@066b052fd78bd87757584f36ca8e7b433c836859`.
- Master [PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) is OPEN / DRAFT / UNMERGED. Its base remains `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; compare against current main is 656 commits ahead / 1 behind. Its 250 changed paths remain under `coordination/phoenix/`; no subsystem source path is included. No rebase or merge was performed.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`. [COE integration PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) is OPEN / DRAFT on `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`, based on current COE main.

## 2. Live role PR and CI reconciliation

All run references below are exact-head GitHub Actions records. PASS means only the named hosted workflow passed; it does not imply hardware or production acceptance.

| Role / PR | Exact head | Evidence and owner boundary |
|---|---|---|
| PHX-CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped build only. CORE remains owner-reserved to its separate continuation; no duplicate CORE work or source edits were started. |
| PHX-RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | API21/23 #45622918364, native auth/installer #45622918551 and APK identity #45622918340 SUCCESS. [Shared build #45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAILURE at mandatory handover freshness and ESP32 compile. Predecessor #289 `68928774`: build #43653329229 and isolated auth #43653329235 SUCCESS. RENTAL owns the correction. |
| PHX-PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Windows synthetic #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS. Native COM/device acceptance remains NOT TESTED. |
| PHX-HARDWARE #358 | docs/PR `d8c3261e9b8aac2637c4395e5c92285bf7d8df53`; source/test `af3ed03db1c07a950ad27adc3e18f27a1afc1ec6`; base #353 `f527b33c9e391a9a66490388d96f06d6c8761dfa` | [Relay #45976531381](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45976531381) PASS; [Quarantine #45976531391](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45976531391) PASS; [Full #45976531386](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45976531386) FAIL at QA-owned Controller protocol parity / missing poll signature. All 14 firmware target/platform jobs and Android pass; downstream production import/signing/publication and simulation/candidate stages are skipped. HARDWARE owns firmware/fixture; QA/CORE own the semantic contract. Physical GPIO/relay/coin acceptance NOT TESTED. |
| PHX-HARDWARE #356 | `0ea32d31ed5c902b2187d98c181aab14bc9fdeae` | Preflight #45940999149, Mbed #45940999085, Native #45940999113 and Full #45940999134 all SUCCESS. CI VERIFIED / SIMULATED only; physical storage, flash and power-cut acceptance NOT TESTED. |
| PHX-HARDWARE #355 / #354 | #355 `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`; #354 `fc842342596786e072630179acfbbc4feeb2ba02` | #355 Poll #45948626013 and Mbed #45948625942 PASS; Full #45948625969 and Native #45948626003 FAIL. #354 Poll #45864684458 and Mbed #45864684325 PASS; Full #45864684497 and Native #45864684295 FAIL. Preserve deny-only behavior; QA/CORE reconcile the inherited assertions and receipt/disposition semantics. |
| PHX-QA #290 / #292 | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | [#290 Windows synthetic #43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS. #292 has no PR-triggered run and is based on stale Master `b1ca02e2087f3b1a7169ceab9c34e52646e700df`, not current `066b052f`. QA owns restacking and independent semantic review. |
| PHX-RELEASE #242 / #291 | #242 `36c0d0bb3e58786359555b307bb784f720f023ce`; #291 `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head PR workflow runs returned for either head. RELEASE owns signing/publisher and exact-head CI evidence. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five candidate workflows are terminal CANCELLED: #43096752563, #43096752800, #43096752557, #43096752609 and #43096752632. Check-runs total_count is zero. FROZEN. |

The Master head `066b052f` has no workflow runs and no combined statuses. No CI pass is claimed for the Master documentation suite.

## 3. Active-v0.6 P0 source readback

The active branch is `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`. The older source pin in issue #177 is stale, but the current active branch still contains the same exact sketch blobs:

- ESP8266 blob `12c4bb82b6fddafe813674a0b5f692c1d3634073`: 3,500 ms timeout at line 263; synchronous `post("poll")` at line 354; first `digitalRead(runCoinPin)` at line 357.
- ESP32 blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d`: 3,500 ms timeout at line 230; synchronous `post("poll")` at line 314; first `digitalRead(runCoinPin)` at line 318.

The poll still precedes the first coin sample on both boards. The #358 strap-pin guard does not resolve this P0. Keep coin/relay admission deny-only until HARDWARE's local inhibit/nonblocking capture, CORE's authenticated response/receipt contract and QA's same-SHA semantic checks are independently accepted. Host reproduction is simulated; no actual coin, relay, device power loss or money state was operated.

## 4. COE #26 exact-tree and migration-staging review

Both recursive trees were complete and non-truncated: source #358 tree `d8c3261e...` has 2,573 entries; destination #26 tree `b382d233...` has 286.

| Mapped area | Source files | Destination files | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 board tree | 16 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 board tree | 67 | 1 | 0 | 1 | 66 | 0 |
| PisoWiFi tests | 47 | 19 | 1 | 3 | 43 | 15 |
| OpenWrt `blazepwifi` library overlay | 15 | 20 | 6 | 9 | 0 | 5 |
| Vendo CGI entry | 1 | 1 | 0 | 1 | 0 | 0 |

Neither destination board sketch is byte-identical to the current #358 source candidate. The test path has only one exact blob; three mapped originals diverge, 43 source tests are absent and 15 destination-only tests exist. The overlay contains six exact blobs, nine changed files and five destination-only files.

### License/notice identity

The mapped source has eight relevant LICENSE/NOTICE path entries; the destination has four. Four destination counterparts are exact: product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. The UI QRCode LICENSE is a duplicate source path with the same blob as the mapped OpenWrt QRCode license. Three unique source notice/license blobs have no destination counterpart: repository-root `NOTICE.md` (blob `f6d92cd2`), Android `BlazeRentalLauncher/LICENSE` (blob `c5b1efa7`), and `ui/vendor/tabler/LICENSE` (blob `22ee8122`). This is path/blob evidence only, not legal approval.

### Intake and test-map inconsistency

- COE #26 `Pisowifi/SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f` has 61 runtime rows. Its summary declares 47 byte-identical / 14 derived, while the actual rows contain 46 byte-identical / 15 derived.
- The intake lists four original tests and 15 derived tests; derived CI state is 11 NOT_RUN and four PENDING_CI_RUN. `release_authorized`, `hardware_tested`, `full_ci_tested` and `source_admission_complete` are all false.
- `Pisowifi/MIGRATION_MAP.md` blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` contains four original-test rows and 14 derived-test rows. It omits `voucher_txn_journal.sh`; `run_focus.sh` and `member_txn_journal.sh` hashes disagree with SOURCE_INTAKE (`fa1f4f2c` vs `2b7b861e`; `01dc9c65` vs `d04df3c6`).
- The intake still names destination branch `feature/pisowifi-cleanup-stabilization` and source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00`; live PR #26 instead uses `integration/ecosystem-nonproprietary-candidate-20261111@b382d233`.

**Disposition:** keep #26 FROZEN. The COE integration owner must reconcile branch/source pins, 46/15 vs 47/14 counts, test-map rows/hashes, missing firmware/tests and license notices, then run CI at the exact proposed SHA before any staging review. No destination staging, copy, move, overwrite, cherry-pick, rebase or write was performed.

## 5. Registry, tests and limitations

- The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were NOT RECOVERED. Library search exposed older v7/v6/v5/v4/v3 registry snapshots only; no Google Drive connector action is exposed in this runtime. No older snapshot was substituted and no private contents or Drive IDs were published.
- A 45/45 read-only structural assertion script passed over exact trees, route invariants, intake, migration map, PR refs and cleanup checklist. This is a tool-runtime audit, **not** the repository test suite.
- `coordination/phoenix/test_*.py` and `verify_coordination.py` were NOT RUN. Local `git ls-remote` failed because `github.com` DNS could not resolve; no authenticated local checkout or Master CI execution path was available. The Master exact head also has no workflow runs/combined statuses.
- No physical GPIO, relay, coin, storage, power-cut, 150-power-cut, 30-device/24-hour soak or native acceptance test was run in this audit.

## 6. Next owner actions and safety decision

1. COE integration owner reconciles #26's live branch/source pins, runtime 46/15 vs 47/14 count, missing/divergent tests, stale test hashes and license/notice counterparts; run all five destination workflows at an exact SHA before staging review.
2. PHX-QA refreshes #292 against current Master and owns independent semantic tests. PHX-CORE publishes the authenticated register/poll and receipt/disposition contract. Do not add unsigned response trust or unsafe `clearPending` callsites.
3. PHX-HARDWARE owns #358 and P0 #177 implementation; keep coin/relay admission deny-only until local pulse capture/inhibit and authenticated disposition are independently verified. Physical GPIO, relay, coin, power-cut and soak evidence remains NOT TESTED.
4. PHX-RENTAL resolves #328 handover freshness and ESP32 compile failure. PHX-RELEASE supplies exact-head workflow evidence for #242/#291.
5. Registry custodian supplies v11 and newer corrections through authorized private Drive access. MASTER reruns the repository suite when an authenticated checkout or Master CI path is available.

**No ownership reassignment, merge, release, hardware flash, financial migration, signer provisioning, secret operation or production approval. PRODUCTION NO-GO remains in force.**
