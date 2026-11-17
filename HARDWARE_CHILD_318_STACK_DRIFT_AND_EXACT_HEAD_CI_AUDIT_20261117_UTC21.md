# PHX-MASTER — HARDWARE child #318 stack drift and exact-head CI audit

**Checkpoint:** 2026-11-17T21:37Z  
**Role/task:** PHX-MASTER · #172 / #266 / #288 / HARDWARE #317–#318 / COE #26 and #31  
**Disposition:** coordination-only; owner reconciliation required; **PRODUCTION NO-GO**.

## Authority and repository refresh

This audit follows the full-team Master directive, README_FIRST, BLAZE-COMMS/1, Experiments root AGENTS.md, the public Cloud Artifact Policy and Storage Handover, live issues #172/#266, current PRs, and current Master coordination documents. No Codex tooling or workflow was used.

- Experiments default branch: `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments development branch: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`; not promoted.
- PHX-MASTER branch and PR #288 before this audit: `b58771d5ac3f3c7489551429ea531c460d0f1185`, base `main@f4e8a891...`, OPEN/DRAFT, 63 changed paths, no PR-triggered workflow runs.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT. Five workflows remain QUEUED with zero jobs: 43096752609, 43096752632, 43096752800, 43096752563, 43096752557.

## HARDWARE #317 / #318 stack reconciliation

Current owner refs read from live PR metadata and branch refs:

| Item | Current identity |
|---|---|
| Parent PR #317 | `1d4320fb11c43192c1e27ebb0b69039729abdc1a` |
| Parent branch | `phoenix/hardware-clear-pending-marker-match-20261117` |
| Child PR #318 | `696e28ed4cd53b9189b78095b38aee973d774683` |
| Child branch | `phoenix/hardware-poll-inhibit-settle-20261117` |
| Comparison merge base | `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3` |
| Compare result | **DIVERGED — 51 ahead / 63 behind** |
| PR #318 mergeability | `false` |
| PR #318 current-head Actions runs | None returned |

The live #317 branch ref resolves to `1d4320fb...`; the #318 head branch resolves to `696e28ed...`. Comparing those exact refs is decisive: they are not a linear child stack. The child PR patch touches both ESP sketches, poll-window/loop host labs, the child workflow, and handover documentation. It proposes a 250 ms quiet interval and blocked-poll pulse fault-injection coverage, but **none of that is accepted on #318's current head** because no current-head CI run was returned.

The child branch's `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` still carries an older checkpoint citing source `9873f0ff...`, parent #317 `44961245...`, and 31-ahead/27-behind. Those are stale relative to the live refs above. Do not use that embedded snapshot as current evidence.

**Decision:** keep #317 and #318 as separate DRAFT candidates. Do not rebase, cherry-pick, force-push, retarget, merge, or silently compose them. PHX-HARDWARE must state the intended parent/child stack direction and update its handover at the chosen exact SHA. PHX-QA must review and execute the selected combined candidate before integration.

## Exact-head CI observations

### HARDWARE #317 — `1d4320fb...`

- [Relay Output Polarity LAB #44173107322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44173107322): completed SUCCESS.
- [Quarantine Byte Readback LAB #44173107264](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44173107264): completed SUCCESS.
- [BlazePwifi build / Full validation #44173107277](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44173107277): completed FAILURE. The validation job's `Controller protocol parity` step reports `Missing poll signature check` in the ESP8266 sketch. The workflow's 14 target-build jobs completed SUCCESS; production import/signing, update bundle, release publication and v0.4 simulations were skipped. The job checked out a synthetic merge commit `5b8ebcdfe25819c6166196b7e06d9cf872a18be3`, so classify this as PR merge-checkout CI associated with the literal #317 head, not a standalone literal-head checkout.

The failed assertion is the inherited QA positive poll-signature fixture. Preserve firmware default-deny. PHX-QA must correct the stale assertion/fixture; do not restore positive poll admission to obtain a green build.

### COE RELEASE #31 — `7bdba18b86f706d7fb96831094338600e28cc9c5`

- [Shared contracts / hardware #44179122507](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44179122507): SUCCESS.
- [Case-collision guard #44179122882](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44179122882): SUCCESS.
- [Mandatory ImageBuilder sandbox #44179122674](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44179122674): FAILURE. The seven host-preflight unit tests passed, bubblewrap installed, then the real namespace probe failed: `bwrap: setting up uid map: Permission denied`; runner exited 125 and correctly refused to execute packaging regressions without the required boundary.

This is an infrastructure denial, not sandbox acceptance. The infrastructure owner must authorize an ephemeral, disposable, no-secret runner with unprivileged user namespaces enabled. Do not add sudo, subordinate-ID mapping, broad privileges, or an unsandboxed fallback. The runner still shares the host network; no network-isolation claim is made.

### Master and destination integration

- PR #288 pre-audit head `b58771d5ac3f3c7489551429ea531c460d0f1185`: no PR-triggered workflow runs returned.
- COE #26 `b382d233...`: five workflows remain queued, zero jobs returned; no combined integration acceptance.

## Manifest and ownership check

The current `coordination/phoenix/OWNERSHIP_ROUTES.json` blob is `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`, 11 routes. Eight bounded parse/invariant assertions passed: Master route remains coordination-only, target remains null, no Master copy permission exists, the broad Rental parent remains explicitly non-copyable, and both Hardware source routes remain present. This is manifest/metadata validation, not execution of the full Master Python suite.

No routing manifest change is justified by this audit. No source file was moved, copied, overwritten, or deleted.

## Other current owner refs

- CORE #252 `c82705f2...` (separate active CORE automation retains source ownership).
- RENTAL #240 `a7d113fb...`, #287 `a4fffd01...`, #289 `68928774...`.
- PISONET #255 `d01fd164...`.
- HARDWARE #314 `556adc20...`, #315 `84fe6b79...`, #316 `888e6941...`, #317/#318 as above.
- QA #267 `ff536799...`, #279 `8f476ef0...`, #290 `5c29d159...`, #292 `75a3f66d...` (no current-head runs for #292).
- RELEASE #242 `734b89d9...`, #291 `0d990afc...`; #291 run 44180669656 is a scoped SUCCESS.
- COE candidates: #28 `b21b0461...`, #29 `d0830332...`, #30 `4897348d...`, #31 `7bdba18b...`, #32 `29b6fe08...`.

These refs are role-owned candidates, not a combined green integration tree.

## Access and evidence limitations

- Canonical private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed connector/Library. Exact-name search returned older v5–v7 snapshots and a historical checkpoint only; none was substituted. No private IDs or contents were published. A Drive connector/read path must be restored by the registry custodian before registry-dependent archive or migration work.
- Experiments AGENTS.md and the public Cloud Artifact Policy / Storage Handover were read. COE root AGENTS.md returned 404; COE main README contains only its heading.
- Full Master Python suite and Master CI were not executed/returned. The 8/8 checks above are bounded manifest/metadata assertions only.

## Owner actions

1. **PHX-HARDWARE:** publish explicit #317/#318 stack direction; refresh the stale PROJECT_HANDOVER snapshot at the selected exact SHA; no force-push or silent rebase.
2. **PHX-QA:** correct #317's inherited positive poll-signature fixture while preserving default-deny; run Full against the exact selected parent/child candidate and verify both board sketches.
3. **PHX-HARDWARE + PHX-QA:** obtain current-head #318 focused CI for the 250 ms pulse-train quiet guard and fault-injection lab; label it SIMULATED/CI only.
4. **Infrastructure / PHX-RELEASE:** provide the authorized no-secret namespace-capable runner and rerun sandbox regressions.
5. **COE integration owner:** resolve #26's five queued workflows and continue per-file source/destination blob, mode, license/NOTICE, test identity and CI reconciliation.

No merge, migration, release, signing, secret provisioning, flashing, physical test, customer payment, or financial state mutation occurred. **PRODUCTION NO-GO** remains in force pending protected signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized gates.
