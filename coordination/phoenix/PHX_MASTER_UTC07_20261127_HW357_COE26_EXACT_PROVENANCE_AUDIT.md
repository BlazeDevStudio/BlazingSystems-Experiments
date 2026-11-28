# PHX-MASTER UTC07 — exact-head Hardware and COE provenance reconciliation

**Observed:** 2026-11-27T07:41:11Z  
**Role:** PHX-MASTER  
**Scope:** `coordination/phoenix/` only  
**Master branch at audit start:** `phoenix/master-coordination@15653103e01bd34239fe0134b801826d2db0c9e7`  
**Parent:** `0f533470087aaa69d8d0cec9f879576cf74d7030`  
**Experiments main:** `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`  
**Development:** `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`  
**Active v0.6 audit branch:** `2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**COE main:** `a6513ab4412b4c014eee2863e45cbe32d06cb243`  
**COE integration PR #26:** `b382d233ff06c8791b1028bed3c617cc7b670d12`

## Executive disposition

- Master PR #288 is OPEN / DRAFT / UNMERGED at the audit-start SHA. Its 249 existing changed paths are all under `coordination/phoenix/`.
- The ownership manifest remains `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER target remains null.
- COE #26 remains frozen. No source/destination copy, move, overwrite, cherry-pick, staging, route promotion or merge was performed.
- P0 #177 remains OPEN. Active v0.6 source still polls synchronously before the first coin sample on both boards.
- Production remains NO-GO. No subsystem source, firmware, payment system, signer, secret, release artifact or physical device was touched.

## 1. HARDWARE exact-head reconciliation

### PR #357 — current docs-sync head is not the restack commit

Live PR metadata reports:

- Branch: `phoenix/hw-runtime-pin-config-guard-20261127-utc04`
- Current PR head: `2476b2cdf820c57ac6d97e5c81abc6292836c609`
- Base branch: `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`
- Exact base SHA / current #355 head: `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`

The #357 body has conflicting head fields: its opening line still calls restack commit `69ef1b4905a1adefdb74b69d701057d6d331540f` the current branch HEAD, while its later docs-sync line and live PR metadata identify `2476b2cdf820c57ac6d97e5c81abc6292836c609`. HARDWARE owns the PR description/handover refresh; MASTER did not edit it.

Current exact-head Actions at `2476b2cdf820c57ac6d97e5c81abc6292836c609`:

| Workflow | Run | Result |
|---|---:|---|
| Full BlazePwifi build | [#45958868784](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958868784) | FAIL — validation / Controller protocol parity |
| Native synthetic journal | [#45958868726](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958868726) | FAIL — PAY-0745 |
| ESP32 Mbed TLS 3/4 | [#45958868755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958868755) | PASS |
| Poll intake deny | [#45958868771](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958868771) | PASS |

The Full run's Android, ESP8266, ESP32 and all 11 OpenWrt firmware-target jobs passed; the validation job failed at Controller protocol parity. The Native log ends at the QA-owned syntactic assertion:

`assert "clearPending(true)" in text and "clearPending(false)" in text`

The preceding signed synthetic journal, CGI envelope, read-only migration preflight, maintenance-freeze and frozen-state checks passed. Do not add a pending-clear call merely to satisfy a string-presence assertion. CORE owns authenticated receipt/disposition semantics; QA owns independent semantic regressions; HARDWARE owns firmware/GPIO implementation; MASTER owns the cross-role contract.

### PR #355 and #356

| PR | Exact head | Exact-head evidence |
|---|---|---|
| #355 | `9f7a8ecb915cf199a82c0b4d37c56c40d722037b` | Poll [#45948626013](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45948626013) PASS; Mbed [#45948625942](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45948625942) PASS; Full [#45948625969](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45948625969) FAIL; Native [#45948626003](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45948626003) FAIL. |
| #356 | `0ea32d31ed5c902b2187d98c181aab14bc9fdeae` (source/test `414048cdc390c7ade2207661ca7e5009c413389e`) | Preflight [#45940999149](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45940999149), Mbed [#45940999085](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45940999085), Native [#45940999113](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45940999113), Full [#45940999134](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45940999134) all PASS. |

#356 is CI VERIFIED / SIMULATED only. It is not physical storage, power-cut, electrical or device acceptance. #355's ledger-prefix restoration remains a separate branch-local result and does not close its Full/Native QA contract failures.

## 2. P0 #177 — active v0.6 source re-read

Issue #177 is OPEN. Its body still cites source SHA `9df0a7e7...`; the actual active branch ref is `2fbd2475e9f54878c316fa7cea2f228386b0e859`.

Exact current blobs and lines:

| Board | Blob | Blocking poll | First coin sample | Timeout |
|---|---|---:|---:|---:|
| ESP8266 | `12c4bb82b6fddafe813674a0b5f692c1d3634073` | 354 | 357 | 3,500 ms (line 263) |
| ESP32 | `29f1125d52ff474a0d028ad41f7af201be1f0f9d` | 314 | 318 | 3,500 ms (line 230) |

The blocking `post("poll")` still precedes the first `digitalRead(runCoinPin)` on both boards. This source-order inspection is not a physical coin-slot test. HARDWARE must provide local intake inhibition or nonblocking pulse capture; CORE must define authenticated receipt/disposition and durable authority; QA must independently test the same source SHA. No unsigned enable or unsafe pending clear is authorized.

## 3. COE #26 — exact intake branch drift

All recursive Git trees used below were complete and non-truncated.

### Distinct source/destination refs

| Object | Exact ref |
|---|---|
| Pinned source commit in intake | Experiments `6d4c9b487af4d768c4d7627654d119417fcc6e00` |
| Current intake destination branch | COE `feature/pisowifi-cleanup-stabilization@331e14bc63e163148f09813da0fdbf4d13581a19` |
| Live integration PR #26 | COE `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12` |
| PR #26 base | COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243` |

The candidate PR does not use the same destination tree as the current intake branch. Within `Pisowifi/`, feature branch has 91 entries and PR #26 has 95; 18 shared paths have different blobs, five paths exist only in PR #26 and one only in the feature branch.

### SOURCE_INTAKE exact comparison

The current feature branch contains newer `SOURCE_INTAKE.json` blob `fdd9c1e3668272576174238b82c19368226685f7`:

- 61 runtime rows: 54 byte-identical / 7 derived.
- 11 derived tests, all `NOT_RUN`.
- 3 unchanged original tests.

PR #26 still contains older `SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`:

- 61 runtime rows: exact tree comparison gives 46 byte-identical / 15 derived.
- Its declared summary says 47 identical / 14 derived — a one-row discrepancy.
- 15 derived tests: 11 `NOT_RUN`, four `PENDING_CI_RUN`.
- 2 unchanged original tests.

For both refs, the 61 source pins resolve to the pinned source tree and the recorded destination blob IDs resolve to that ref's own destination tree. The problem is not a missing row in the old PR snapshot; it is that PR #26 still carries the older intake/migration snapshot while the named feature branch has newer, materially different destination blobs and a revised intake summary.

### Test identity at the pinned source commit

| Comparison | Source tests | Destination tests | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| Feature branch `331e14bc` | 149 | 16 | 3 | 1 | 145 | 12 |
| PR #26 `b382d233` | 149 | 19 | 2 | 2 | 145 | 15 |

These are blob/path comparisons, not execution results. The 11/15 derived test status entries remain unverified as described above.

### Licensing and NOTICE

Within the pinned PisoWiFi project root, source has nine LICENSE/NOTICE paths; each destination ref has four, with four exact path+blob counterparts and five source paths without exact destination counterparts:

- `android/BlazeRentalLauncher/LICENSE`
- `android/BlazeRentalLauncher/assets/license.html`
- `tests/vendor/jsqr-1.4.0/LICENSE`
- `ui/vendor/qrcode/LICENSE`
- `ui/vendor/tabler/LICENSE`

The repository-root Experiments `NOTICE.md` is also absent from the COE candidate root. The PR #26 description's claim that the licensing/privacy conflict is resolved is not supported by this exact path review; obtain owner/legal reconciliation before staging.

### Current #355 source vs COE #26 Hardware/test routes

At current Hardware #355 head `9f7a8ecb` vs PR #26 `b382d233`:

| Route | Source blobs | Destination blobs | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 4 | 1 | 0 | 1 | 3 | 0 |
| ESP8266 | 13 | 1 | 0 | 1 | 12 | 0 |
| PisoWiFi tests | 151 | 19 | 2 | 2 | 147 | 15 |

Both destination firmware sketches differ from current source. This comparison is separate from the historical 61-row intake pinned to `6d4c9b48`.

### Candidate CI and hold

COE #26's five workflows are terminal **CANCELLED**, with zero check-runs/statuses:

- [#43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609)
- [#43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632)
- [#43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800)
- [#43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563)
- [#43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557)

No destination staging, copy, move, overwrite, cherry-pick or promotion is authorized.

## 4. Other role exact-head CI

| Owner / PR | Exact head | Current PR-triggered evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS (scoped only). CORE source remains reserved to the separate production-continuation owner; MASTER made no CORE changes. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | Build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL; API21/23 [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth/installer [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), APK identity [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340) PASS. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM physical acceptance NOT TESTED. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows synthetic [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered workflow run returned. Its base is stale Master `b1ca02e2`; QA must revalidate against current Master before acceptance. |
| RELEASE #242 / #291 | `36c0d0bb...` / `bf339a76...` | No PR-triggered runs returned for either exact head. No signing/publishing gate is accepted. |
| COE RELEASE #35 | `bc57ba8ecc5245ce538c6770a45bb25e2b8b5ef3` | Case [#45897198239](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198239) PASS; sandbox [#45897198204](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198204) FAIL; shared Hardware [#45897198326](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198326) FAIL. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; synthetic only. |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared Hardware [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL. |

## 5. Governance, tool and test limits

- Cleanup issue #266 remains OPEN; all seven role checklist items are unchecked (0/7).
- `OWNERSHIP_ROUTES.json` remains unchanged: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found in the Library title search. No Google Drive connector action is exposed in this runtime; older registry snapshots were not substituted and no private IDs/content were published.
- GitHub API reads were available, but local Git access failed: `git ls-remote` could not resolve `github.com`. Therefore Master Python suite and `verify_coordination.py` were NOT RUN; no Master Actions run was created or claimed.
- No automation inventory read was available in this tool surface. The user-designated separate CORE owner was respected: no CORE branch, source or duplicate CORE task was touched.

## 6. Required next owner actions

1. HARDWARE refreshes #357's conflicting head fields and canonical handover with terminal exact-head CI at `2476b2cdf820c57ac6d97e5c81abc6292836c609`; keep PR draft/unmerged.
2. CORE publishes the authenticated receipt/disposition schema and golden vectors; QA replaces literal callsite assertions with exact-SHA semantic state/replay/failure tests; HARDWARE preserves deny-only firmware behavior.
3. HARDWARE resolves P0 #177 with local intake protection or nonblocking pulse capture; QA independently verifies both boards at the same source SHA.
4. COE integration owner reconciles PR #26 against the newer feature-branch intake/map, the 18 changed shared paths, test identity and missing licensing/NOTICE paths; then restores runnable exact-head CI. Keep #26 frozen until this is complete.
5. Registry custodian restores authorized private Drive access to v11 and newer corrections.
6. MASTER runs the coordination suite once an authenticated local checkout or Master CI execution path is available.

**Final:** PR #288 remains draft/unmerged; COE #26 remains frozen; production remains **NO-GO**. No merge, release, signer operation, secret provisioning, flash, physical test, payment operation, migration or customer cutover occurred.


---

## Post-audit Hardware #357 refresh — 2026-11-27T08:00:27Z

The earlier UTC07 audit captured #357 at docs-sync head `2476b2cdf820c57ac6d97e5c81abc6292836c609`. HARDWARE subsequently published a new exact-head handover and CI refresh. This addendum supersedes the #357 head/CI fields above; it does not alter the earlier timestamped tree and intake comparisons.

**Current live PR #357:**
- PR/docs HEAD: `2b5130d5cba54acf354ffdbdbe04127d6a61113f`
- Source/test SHA: `7ee0bc955cdf67763d032f81e488141e4a270a88`
- Base #355: `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`
- PR remains OPEN / DRAFT / UNMERGED.
- The previous conflicting restack/docs-sync head fields are now reconciled in the live Hardware PR body.

### New Hardware source improvement

The Hardware-owned ESP8266 `validRuntimePins()` now rejects GPIO0, GPIO2 and GPIO15 for coin, relay and LED runtime roles because the ESP8266 ROM samples these strap pins at reset. Defaults coin GPIO4 / LED GPIO14 / relay GPIO5 remain valid. Invalid stored tuples retain the existing default-fallback behavior; this change does not add positive coin/relay admission.

Exact source/test blobs:
- ESP8266 sketch: `96fa83d9ae5404eefbad425e5b032db962fa45a4`
- Source-extracted lab: `9728fd0a1d9044fbb5188959d73c0ae20e1bc0dc`
- Handover: `eea8a9781065e0bed4590230dfaa95e4cc3a0d47`

The lab covers all three strap pins in all three runtime roles and rejects a mutation that removes the strap guard. The handover reports 14/14 injected regressions rejected and `CHANGE_LEDGER_APPEND_ONLY_PASS`. These are source-extracted/host-simulated checks, not electrical or board acceptance.

### Terminal exact-head CI at 2b5130d5

| Workflow | Run | Result |
|---|---:|---|
| Focused Poll Intake Deny | [#45961809870](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961809870) | PASS |
| Focused push | [#45961801597](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961801597) | PASS |
| ESP32 Mbed TLS 3/4 | [#45961809743](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961809743) | 3/3 PASS |
| Full | [#45961809866](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961809866) | FAIL — QA-owned `tests/controllers.sh:21` requires `config_revision` in both sketches; all 13 firmware-target jobs and Android pass; production import/signing/publication and candidate simulations skipped |
| Native | [#45961809750](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961809750) | FAIL — QA-owned PAY-0745 literal `clearPending(true/false)` assertion; preceding Vendo pending-sequence shell contract passes |

The new GPIO source guard is a useful Hardware improvement, but #357 remains Full/Native FAIL. Do not add unsafe pending-clear calls to satisfy a string-presence assertion. QA owns semantic contract repair; CORE owns authenticated receipt/disposition; HARDWARE owns firmware; MASTER owns cross-role coordination.

**Physical boundary unchanged:** GPIO strap levels, external pulls, relay contacts, coin pulses, brownout, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
