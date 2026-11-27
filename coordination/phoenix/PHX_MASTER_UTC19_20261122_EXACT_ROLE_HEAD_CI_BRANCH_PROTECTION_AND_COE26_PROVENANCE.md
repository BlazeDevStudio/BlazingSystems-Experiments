# PHX-MASTER UTC19 — exact role heads, CI, branch protection and COE #26 provenance

**Audit window:** 2026-11-22 UTC19  
**Role:** PHX-MASTER — master auditor / integration coordinator  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Master parent at audit start:** `f6fc375e02d63afd34f00bad3cbbb989d1474c18`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**PR #288:** OPEN / DRAFT / UNMERGED; 173 paths before this audit, all under `coordination/phoenix/`.

This is an append-only coordination/provenance record. It does not authorize subsystem source edits, integration staging, merge, release, signing, flashing, payment operations or physical testing.

## 1. Live control-plane and branch identities

| Ref | Exact HEAD |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Active development `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master `phoenix/master-coordination` | `f6fc375e02d63afd34f00bad3cbbb989d1474c18` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

- Control plane [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) was re-read; latest observed issue update: 2026-11-22T19:13:27Z.
- Cleanup gate [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN; seven tracks remain 0/7 complete. MASTER's broad duplicate/dead-file inventory is still incomplete.
- Current [Master PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) head matched the branch HEAD at audit start.
- Ownership manifest blob `e4db324315a1b3543fec17a148fbf960170fcb29`: `DRAFT_REVIEW_ONLY`, 11 routes, source ref Experiments main `f4e8a891...`, destination candidate PR #26 at `b382d233...`. PHX-MASTER is `coordination-only`, with `target: null`. Manifest was not changed.
- GitHub branch API returned `protected=false` and `protection.enabled=false` for Experiments `main`, active development, Master coordination, and COE `main`; required status-check enforcement was off. No repository settings were changed. Repository administrators must establish protected rulesets/branch protection and required review/status gates.
- Experiments root `AGENTS.md` was read at blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`. COE root `AGENTS.md` returned 404; no replacement guidance was assumed.

## 2. Exact owner PR and CI reconciliation

All refs below are live PR heads read during this activation. A green focused workflow is not a full integration or production pass.

| Owner / PR | Exact head | Exact-head CI observation |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) BUILD SUCCESS; CORE remains separately owned. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) APK identity PASS; [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) API21/API23 PASS; [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) BUILD FAIL. ESP32 compile log reports `mbedtls/sha256.h: No such file or directory`. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) Windows release workflow SUCCESS; native COM/device acceptance remains unverified. |
| HARDWARE #327 | `fadac4ed3bc837cf729753264b9427fa3fd312b9` | [#45029851960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851960) quarantine PASS; [#45029852010](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029852010) relay polarity PASS; [#45029851959](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851959) full build FAIL. |
| HARDWARE #342 | `e7815297b1a8780b7868bc9b28f45011ec419dce` | [#45043657779](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45043657779) quarantine PASS; [#45043657792](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45043657792) full build FAIL. |
| HARDWARE #343 | `19550979b788c3d9be9571db3685a89ad944d617` | [#45055311907](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45055311907) quarantine PASS; [#45055311979](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45055311979) relay PASS; [#45055311858](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45055311858) full build FAIL at validation job `137309124802`: `Missing poll signature check`. All 14 target/platform jobs plus Android completed successfully; downstream simulation/sign/candidate/publication jobs were skipped. #343 changes six Hardware-owned paths only. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) Windows workflow SUCCESS; this is not independent poll-contract acceptance. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered workflow runs returned. |
| RELEASE #291 | `8ffe39276b955aae8e97352a3b7532c53035609a` | [#45059662097](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45059662097) Windows handover gate FAIL; [#45059662114](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45059662114) Full run FAIL at CI-0701 docs-only handover regression (4 tests fail); [#45059662069](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45059662069) ESP32 compatibility was IN_PROGRESS at last read. Windows log identifies the CORE-owned `PROJECT_HANDOVER.md` freshness gate; RELEASE's own docs tests report missing/stale current refs and the transposed source SHA. |
| COE RELEASE #35 | `edb4eb482dfa94bbad2dcf29b90b8463a2165fa5` | [#45054914784](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45054914784) case-collision PASS; [#45054914749](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45054914749) 37 sandbox tests PASS, then Bubblewrap missing (exit 125); [#45054914752](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45054914752) all ten appliance profiles fail closed without approved site-scoped ULA /48 authority. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) Pisowifi suite PASS; [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) case-collision PASS. |
| COE Stage 5.1 #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) Stage 5.1 suite PASS; [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) case-collision PASS; [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) shared hardware/contract workflow FAIL. This is a separate bridge candidate, not a replacement for #26. |

### Ownership collision and cross-role caution

RELEASE #291 contains 27 changed paths: 22 RELEASE-owned, 3 CORE-owned handover files, and 2 PISONET-owned release-signing test files. Its mixed-owner scope is not an ownership transfer. MASTER did not edit those paths. CORE's separate automation owns CORE source/handover work; no parallel CORE implementation was started. The named separate CORE automation was not independently surfaced in this runtime's automation listing, so no claim is made about its latest execution state.

## 3. COE #26 exact migration provenance — FROZEN

Exact refs read:

- Historical source pin from `Pisowifi/SOURCE_INTAKE.json`: Experiments commit `6d4c9b487af4d768c4d7627654d119417fcc6e00`, rootfs tree `f4a923aaacf1374e90c7bab5f335efe6c6ec55cf`, tests tree `7e3b16f2a981c1c8ecab3b1da0d34a82b4e44f17`.
- Current Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Current Hardware source candidate: #343 `19550979b788c3d9be9571db3685a89ad944d617`.
- COE #26 destination: `b382d233ff06c8791b1028bed3c617cc7b670d12`.

All recursive trees were non-truncated: source candidate 2,481 entries, current Experiments main 2,340 entries, COE #26 286 entries.

### 61-row PisoWiFi map

- All 61 map source blob identities match the historical pinned rootfs tree (61/61).
- All 61 destination blob identities match the destination tree at COE #26 (61/61).
- The actual map computes **46 byte-identical / 15 divergent** rows.
- `SOURCE_INTAKE.json` summary says **47 byte-identical / 14 locally derived**. This is an off-by-one discrepancy; the existing Master synthetic test `test_observed_61_row_off_by_one_is_reported` covers this failure class, but the full Master suite was not executed in this activation.
- Comparing the same 61 paths with current Experiments main gives **33 unchanged / 20 changed / 8 absent** relative to the old source pins. The old snapshot match does not establish current-source equivalence.

### Hardware, test, licensing and import completeness

| Item | Current source | COE #26 destination | Result |
|---|---|---|---|
| ESP32 sketch | `9011029ea05bb6160bc326598e6d25cbe953c4c2` (#343) | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Divergent |
| ESP8266 sketch | `01fe33404d51653515e64833038d23d080ff80b2` (#343) | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Divergent |
| Firmware hardening test | `41211b2c110ab409f6d9d1812ef12fda73b13211` (#343 source) | `f921c56cecc19cab1989507b9b4ade1f45dac54e` | Different test identity |

Both hardening-test blobs contain legacy positive `response_sig`, `|register|` and `|poll|` assertions; the current source test has no deny-only markers. This aligns with the current HARDWARE Full validation failure but does not justify changing firmware to satisfy the legacy assertion. CORE owns the producer contract; QA owns the assertion and independent negative/default-deny tests; HARDWARE owns firmware consumers.

- Current #343 source tree contains 34 ESP32/ESP8266 board-local Python helpers; COE #26 has zero `Hardware/*.py` files. This is an incomplete lab/helper import, not a claim that every helper is production firmware.
- Source and destination PisoWiFi LICENSE blobs are byte-identical: `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Experiments root `NOTICE.md` exists at blob `f6d92cd21465312be5993631fe26977219be0fb9`; COE #26 has no root NOTICE. Its only NOTICE is the TailAdmin vendor notice. COE Hardware-local LICENSE/NOTICE files are absent. Scope and attribution need owner/legal review; do not auto-copy.
- COE #26 has five workflow runs queued at this exact head: [case-collision #43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [Pisonet #43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632), [Hardware/shared #43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [Rental #43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), and [Pisowifi #43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557). Each returned zero jobs; none is a pass.

**Decision:** COE #26 remains FROZEN. No destination staging, copy, move, overwrite, cherry-pick, rebase or edit. Before any proposal, COE integration owner must reconcile source pin/current-main drift, 47/14 versus 46/15, all divergent/absent rows, helper imports, firmware/test identities, NOTICE/licensing, and terminal exact-head CI. MASTER route remains `target: null`.

## 4. Verification boundary, registry and next actions

- Source/tree inspections and in-memory provenance comparisons were executed; they are not repository unit tests.
- Master PR #288 has no workflow runs returned. Full `coordination/phoenix` unittest discovery and `verify_coordination.py` were NOT RUN because this activation had no authenticated local checkout/test workspace. Do not report them as passing.
- Canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were searched by exact filename in the authorized Library surface; only older v3–v7 snapshots/checkpoints surfaced. No Google Drive connector was exposed in this runtime. No older registry was substituted, and no private registry contents or identifiers were copied into GitHub.
- No merge, release, signing, secret provisioning, firmware flash, real-payment operation, financial migration, physical test, or production gate approval occurred.

### Exact next owner actions

1. **Repository administrators:** enable effective protected branch/ruleset enforcement on Experiments main, active development and Master coordination, plus COE main; require reviewed PRs and relevant status checks.
2. **PHX-QA:** reconcile the positive poll-signature fixture with the current CORE producer contract and add independent negative/default-deny behavior tests; do not weaken firmware fail-closed behavior.
3. **PHX-CORE:** continue producer/handover ownership under the separate CORE runner; no parallel Master implementation.
4. **PHX-RENTAL:** resolve ESP32 Mbed TLS header availability and keep handover freshness current.
5. **PHX-RELEASE:** correct its own #291 handover-current-ref regression and mixed-owner review; obtain the CORE-owned handover refresh from CORE rather than editing it.
6. **COE integration owner:** keep #26 frozen and reconcile every discrepancy above before proposing per-file staging.
7. **Registry custodian:** restore authorized access to canonical Drive v11 and newer corrections.
8. **Human runner / repository admin:** provide an authenticated local checkout or Master CI runner, then execute the full Master test suite.

**Disposition: PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
